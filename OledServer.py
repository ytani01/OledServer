#!/usr/bin/env python3
#
# (c) 2018 Yoichi Tanibayashi
#
import sys
import time
import threading
import queue
import socketserver
import click
from OledText import OledText
from ipaddr import ipaddr

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
    datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False
def init_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l

#
# ワーカースレッド
#
#   ハンドラースレッドからのメッセージを受信して、処理を実行する。
#   メッセージ受信はキューを介して行うため、非同期実行可能。
#
#   msg = {'type':'...', 'content':'...'}
#
class OledWorker(threading.Thread):
    CMD_PREFIX = '@@@'
    
    def __init__(self, device='ssd1306', header=0, footer=0, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('device = %s', device)
        self.logger.debug('header = %d', header)
        self.logger.debug('footer = %d', footer)

        self.device = device
        
        self.msgq = queue.Queue()

        self.ot = OledText(self.device, headerlines=header, footerlines=footer,
                           debug=debug)
        if not self.ot.enable:
            self.logger.error('OledText is not available')
            raise RuntimeError
        
        self.zenkakuflag = False
        self.logger.debug('self.zenkakuflag = %s', self.zenkakuflag)
        super().__init__()

    def set_zenkaku(self, flag):
        self.ot.set_zenkaku(flag)
        
    def send(self, msg_type, msg_text):
        msg = {'type': msg_type, 'content': msg_text}
        self.msgq.put(msg)
        
    def send_msg(self, msg_text):
        self.send('', msg_text)
        
    def send_cmd(self, msg_text):
        self.send('cmd', msg_text)

    def recv(self):
        msg = self.msgq.get()
        self.logger.debug('msg = %s', msg)
        return msg['type'], msg['content']
        
    def msg_empty(self):
        return self.msgq.empty()

    def end(self):
        self.logger.debug('')
        self.send_cmd('end')
        self.logger.debug('send cmd \'end\'')
        self.join()
        self.logger.debug('join(): done')

    def run(self):
        while True:
            if self.msg_empty():
                self.ot._display(True)
                self.logger.debug('wait msg ..')

            msg_type, msg_content = self.recv()

            if msg_type == 'cmd' and msg_content == 'end':
                self.logger.debug('recv (%s:%s)', msg_type, msg_content)
                break

            #
            # main work
            #
            args = msg_content.split()
            if len(args) > 0:
                if args.pop(0) == __class__.CMD_PREFIX:
                    cmd = args.pop(0)
                    self.logger.debug('recv special command: %s %s', cmd, args)
                    if cmd == 'zenkaku':
                        self.ot.set_zenkaku(True)
                        if len(args) > 0:
                            if args[0] == 'False':
                                self.ot.set_zenkaku(False)
                        continue
                    if cmd == 'crlf':
                        self.ot.set_crlf(True)
                        if len(args) > 0:
                            if args[0] == 'False':
                                self.ot.set_crlf(False)
                        continue
                    if cmd == 'row':
                        if len(args) > 0:
                            self.ot.set_row(int(args[0]))
                            continue
                    if cmd == 'body':
                        self.ot.set_part(cmd)
                        continue
                    if cmd == 'header':
                        self.ot.set_part(cmd)
                        continue
                    if cmd == 'footer':
                        self.ot.set_part(cmd)
                        continue
                    if cmd == 'clear':
                        self.ot.clear(display_now=False)
                        continue
                
            # server side variable
            msg_content = msg_content.replace('@DATE@',
                                              time.strftime('%Y/%m/%d(%a)'))
            msg_content = msg_content.replace('@TIME@',
                                              time.strftime('%H:%M:%S'))
            msg_content = msg_content.replace('@IFNAME@', ipaddr().if_name())
            msg_content = msg_content.replace('@IPADDR@', ipaddr().ip_addr())
            for ch in 'YmdaHMS':
                msg_content = msg_content.replace('@' + ch + '@',
                                                  time.strftime('%' + ch))

            self.ot.print(msg_content, display_now=False)

            time.sleep(0.01)
            
#
# ハンドラー
#
#  ネットワークが接続されると、handle()関数が呼び出される。
#  ネットワークからメッセージを受信して、ワーカースレッドにメッセージを送る。
#  メッセージの送信はキューを介して行われるため、非同期実行可能。
#
#  XXX なぜか特定のTELNET制御コードを変換しなければならない
#  XXX 変換しきれない…TBD
#
class OledHandler(socketserver.StreamRequestHandler):
    ACK = 'ACK\r\n'.encode('utf-8')

    def setup(self):
        self.logger = init_logger(__class__.__name__, self.server.debug)
        super().setup()
        
    def write(self, msg):
        try:
            self.wfile.write(msg)
        except:
            self.logger.error('write(): Error !')

    def send_ack(self):
        self.write(__class__.ACK)

    def getline(self, byte_data):
        TELNET_TO_BYTE = {
            b'\xff\xed\xff\xfd\x06': b'\x9a',
            b'\xff\xf3\xff\xfd\x06': b'\x9c',
            b'\xff\xf4\xff\xfd\x06': b'\x83',
            b'\xff\xf5\xff\xfd\x06': b'\x8f',
            b'\x01': b'',
            b'\x02': b'',
            b'\x03': b'',
            b'\x04': b''
        }

        line = ''

        # XXX なぜか特定のTELNET制御コードを変換しなければならない
        f = False
        for b in byte_data:
            if int(b) == 0xff:
                f = True
            if f:
                self.logger.debug('TELNET code: %02X', int(b))
                if int(b) == 0x06:
                    f = False
        
        byte_data0 = byte_data
        for code in TELNET_TO_BYTE.keys():
            byte_data = byte_data.replace(code,
                                          TELNET_TO_BYTE[code])
        if byte_data != byte_data0:
            self.logger.debug('byte_data0: \n%s', byte_data0)
            self.logger.debug('byte_data: \n%s',  byte_data)

        try:
            line = byte_data.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            ### XXX デコードエラーへの対応: TBD ###
            self.logger.error('UnicodeDecodeError ignored: %s', byte_data)

        return line.rstrip()

    def handle(self):
        global continueToServe
        
        self.send_ack()
        self.logger.info('Connected')

        while True:
            #
            # receive message from client
            #
            try:
                #net_data = self.request.recv(512)
                net_data = self.rfile.readline()

            except ConnectionResetError:
                self.logger.error('ConnectionResetError')
                break
            except KeyboardInterrupt:
                self.logger.warn('KeyboardInterrupt')
                continueToServe = False
                break

            #logger.debug('%s> net_data: \n%s', __class__.__name__, net_data)
            
            if len(net_data) == 0:
                self.logger.info('Connection closed')
                break

            if not self.server.worker.is_alive():
                self.logger.debug('worker is dead')
                continueToServe = False
                break

            # decode and something to do
            line = self.getline(net_data)
            self.logger.debug('line=\'%s\'', line)
            
            # send message to worker
            self.server.worker.send_msg(line)

            # replay ack
            self.send_ack()
            self.logger.debug('replay ACK')

        self.logger.debug('done')
            
#
# サーバークラス
#
#   サーバーのメインループ
#   初期化時にハンドラークラスを登録する
#   main関数の server.serve_forever() でメインループを開始する
#
class OledServer(socketserver.TCPServer):
    DEF_PORT = 12345
    allow_reuse_address = True

    def __init__(self, device='ssd1306', header=0, footer=0, port=DEF_PORT,
                 handler=OledHandler, worker=OledWorker, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('device = %s', device)
        self.logger.debug('hader  = %d', header)
        self.logger.debug('footer = %d', footer)
        self.logger.debug('port   = %d', port)

        self.device     = device
        self.debug      = debug
        
        self.worker	= worker(self.device, header, footer, debug=debug)
        self.logger.debug('self.worker = %s', self.worker)
        self.worker.start()
        
        self.port	= port
        self.logger.info('self.port = %d', self.port)

        self.logger.debug('handler = %s', handler)
        return super().__init__(('', self.port), handler)

    def __del__(self):
        global continueToServe

        self.logger.debug('')
        continueToServer = False
        if hasattr(self, 'worker'):
            self.worker.end()

#####
#CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(help='OLED display server')
@click.argument('device', type=str, nargs=1)
@click.option('--port',   '-p', 'port',   type=int, default=12345,
              help='port number')
@click.option('--header', '-h', 'header', type=int, default=0,
              help='header lines')
@click.option('--footer', '-f', 'footer', type=int, default=0,
              help='footer lines')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(device, port, header, footer, debug):
    global continueToServe
    continueToServe = True

    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    try:
        logger.debug('port=%d', port)
        server = OledServer(device, header, footer, port,
                            OledHandler, OledWorker, debug=debug)

    except Exception as e:
        logger.error('Exception %s %s', type(e), e)
        continueToServe = False

    try:
        while continueToServe:
            server.handle_request()
            logger.debug('handle_request() done')

    except KeyboardInterrupt:
        logger.warn('== Interrupted ==')

    return

#####
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warn('== Interrupted ==')
    finally:
        logger.warn('== End ==')

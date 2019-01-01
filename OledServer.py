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
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

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
    
    def __init__(self, header=0, footer=0):
        self.msgq = queue.Queue()

        self.ot = OledText(headerlines=header, footerlines=footer)
        self.zenkakuflag = False
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
        logger.debug('%s> msg = %s' , __class__.__name__, msg)
        return msg['type'], msg['content']
        
    def msg_empty(self):
        return self.msgq.empty()

    def end(self):
        self.send_cmd('end')
        self.join()

    def run(self):
        while True:
            if self.msg_empty():
                logger.debug('%s> wait msg ..', __class__.__name__)

            msg_type, msg_content = self.recv()

            if msg_type == 'cmd' and msg_content == 'end':
                logger.debug('%s> recv end cmd', __class__.__name__)
                break

            #
            # main work
            #
            args = msg_content.split()
            if len(args) > 0:
                if args.pop(0) == __class__.CMD_PREFIX:
                    cmd = args.pop(0)
                    logger.debug('%s> recv special command: %s %s', __class__.__name__,
                                 cmd, args)
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
                        self.ot.clear()
                        continue
                
            # server variable
            msg_content = msg_content.replace('@DATE@', time.strftime('%Y/%m/%d(%a)'))
            msg_content = msg_content.replace('@TIME@', time.strftime('%H:%M:%S'))
            msg_content = msg_content.replace('@IFNAME@', ipaddr().if_name())
            msg_content = msg_content.replace('@IPADDR@', ipaddr().ip_addr())

            self.ot.print(msg_content)

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

    def write(self, msg):
        try:
            self.wfile.write(msg)
        except:
            logger.error('%s> write(): Error !', __class__.__name__)

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
                logger.debug('TELNET code: %02X', int(b))
                if int(b) == 0x06:
                    f = False
        
        byte_data0 = byte_data
        for code in TELNET_TO_BYTE.keys():
            byte_data = byte_data.replace(code,
                                          TELNET_TO_BYTE[code])
        if byte_data != byte_data0:
            logger.debug('%s>%s> byte_data0: \n%s',
                         __class__.__name__, 'getline', byte_data0)
            logger.debug('%s>%s> byte_data: \n%s',
                         __class__.__name__, 'getline', byte_data)

        try:
            line = byte_data.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            ### XXX デコードエラーへの対応: TBD ###
            logger.error('%s>%s> UnicodeDecodeError ignored: %s',
                         __class__.__name__, 'getline', byte_data)

        return line.rstrip()

    def handle(self):
        global continueToServe
        
        self.send_ack()
        logger.info('%s> Connected', __class__.__name__)

        while True:
            #
            # receive message from client
            #
            try:
                #net_data = self.request.recv(512)
                net_data = self.rfile.readline()

            except ConnectionResetError:
                logger.error('%s> ConnectionResetError', __class__.__name__)
                break
            except KeyboardInterrupt:
                logger.warn('%s> KeyboardInterrupt', __class__.__name__)
                continueToServe = False
                break

            #logger.debug('%s> net_data: \n%s', __class__.__name__, net_data)
            
            if len(net_data) == 0:
                logger.info('%s> Connection closed', __class__.__name__)
                break

            if not self.server.worker.is_alive():
                logger.debug('%s> worker is dead', __class__.__name__)
                continueToServe = False
                break

            # decode and something to do
            line = self.getline(net_data)
            logger.debug('%s> line=\'%s\'', __class__.__name__, line)
            
            # send message to worker
            self.server.worker.send_msg(line)

            # replay ack
            self.send_ack()
            logger.debug('%s> replay ACK', __class__.__name__)

        logger.debug('%s> handle() done', __class__.__name__)
            
#
# サーバークラス
#
#   サーバーのメインループ
#   初期化時にハンドラークラスを登録する
#   main関数の server.serve_forever() でメインループを開始する
#
class OledServer(socketserver.TCPServer):
    DEF_PORT_NUM = 12345
    allow_reuse_address = True

    def __init__(self, handler, worker, port_num=0, header=0, footer=0):
        self.worker	= worker(header, footer)
        self.worker.start()
        logger.debug('%s> worker:%s', __class__.__name__, worker.__name__)
        
        self.port_num	= port_num
        if self.port_num == 0:
            self.port_num = __class__.DEF_PORT_NUM
        logger.info('%s> port=%d', __class__.__name__, self.port_num)

        logger.debug('%s> handler:%s', __class__.__name__, handler.__name__)
        return super().__init__(('', self.port_num), handler)

    def __del__(self):
        global continueToServe
        continueToServer = False
        logger.debug('%s>', __class__.__name__)

#####
@click.command(help='OLED display server')
@click.option('--port',   '-p', 'port',   type=int, default=0,
              help='port number')
@click.option('--header', '-h', 'header', type=int, default=0,
              help='header lines')
@click.option('--footer', '-f', 'footer', type=int, default=0,
              help='footer lines')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(port, header, footer, debug):
    global continueToServe
    continueToServe = True

    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    try:
        logger.debug('port=%d', port)
        server = OledServer(OledHandler, OledWorker, port, header, footer)

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

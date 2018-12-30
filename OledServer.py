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
from MisakiFont import MisakiFont

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
#handler_fmt = Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
handler_fmt = Formatter('[%(levelname)s] %(message)s')
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
    CMD_PREFIX = '$$$'
    
    def __init__(self):
        self.msgq = queue.Queue()

        self.misakifont = MisakiFont()
        self.zenkakuflag = False
        super().__init__()

    def set_zenkaku(self, flag):
        self.misakifont.set_zenkaku_flag(flag)
        
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
            cmd_list = msg_content.split()
            if len(cmd_list) > 0:
                if cmd_list.pop(0) == __class__.CMD_PREFIX:
                    logger.debug('%s> recv special command: %s',
                                 __class__.__name__, cmd_list)
                    for cmd in cmd_list:
                        if cmd == 'zenkaku_on':
                            self.misakifont.set_zenkaku_flag(True)
                            continue
                        if cmd == 'zenkaku_off':
                            self.misakifont.set_zenkaku_flag(False)
                            continue
                        if cmd == 'clear':
                            self.misakifont.clear()
                            continue
                    continue
                
            self.misakifont.println(msg_content)

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
    def write(self, msg):
        try:
            self.wfile.write(msg)
        except:
            logger.error('%s> write(): Error !', __class__.__name__)

    def getline(self, byte_data):
        TELNET_TO_BYTE = {
            b'\xff\xed\xff\xfd\x06': b'\x9a',
            b'\xff\xf3\xff\xfd\x06': b'\x9c',
            b'\xff\xf4\xff\xfd\x06': b'\x83',
            b'\xff\xf5\xff\xfd\x06': b'\x8f'
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
        
        for code in TELNET_TO_BYTE.keys():
            byte_data = byte_data.replace(code,
                                          TELNET_TO_BYTE[code])
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
        
        self.write('[Connected]\r\n'.encode('utf-8'))
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
                logger.error('%s> KeyboardInterrupt', __class__.__name__)
                continueToServe = False
                break

            logger.debug('%s> net_data: \n%s', __class__.__name__, net_data)
            
            if len(net_data) == 0:
                logger.debug('%s> Connection closed', __class__.__name__)
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

    def __init__(self, worker, port_num=0):
        self.worker	= worker

        self.port_num	= port_num
        if self.port_num == 0:
            self.port_num = __class__.DEF_PORT_NUM
        logger.info('%s> port=%d', __class__.__name__, self.port_num)
        
        return super().__init__(('', self.port_num), OledHandler)

    def __del__(self):
        global continueToServe
        continueToServer = False
        logger.debug('%s> __del__()', __class__.__name__)

#####
@click.command(help='OLED display server')
@click.option('--port', '-p', type=int, default=0,
              help='port number')
def main(port):
    global continueToServe
    continueToServe = True

    worker = OledWorker()
    worker.start()
    logger.debug('main> worker started: port=%d', port)

    try:
        logger.debug('main> port=%d', port)
        server = OledServer(worker, port)

    except Exception as e:
        logger.error('main> Exception %s %s', type(e), e)
        continueToServe = False

    try:
        while continueToServe:
            server.handle_request()
            logger.debug('main> handle_request() done')

    except KeyboardInterrupt:
        logger.warn('main> == Interrupted ==')

    if worker.is_alive():
        worker.end()
    return

#####
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warn('== Interrupted ==')
    finally:
        logger.warn('== End ==')

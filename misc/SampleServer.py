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
class SampleWorker(threading.Thread):
    def __init__(self):
        self.msgq = queue.Queue()
        super().__init__()

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
            for w in msg_content.split():
                print('%s> [%s]' % (__class__.__name__, w))
                time.sleep(1)

            time.sleep(0.01)
            
#
# ハンドラー
#
#  ネットワークが接続されると、handle()関数が呼び出される。
#  ネットワークからメッセージを受信して、ワーカースレッドにメッセージを送る。
#  メッセージの送信はキューを介して行われるため、非同期実行可能。
#
class SampleHandler(socketserver.StreamRequestHandler):
    def write(self, msg):
        try:
            self.wfile.write(msg)
        except:
            logger.error('%s> write(): Error !', __class__.__name__)

    def handle(self):
        global continueToServe
        
        self.write('[Connected]\r\n'.encode('utf-8'))
        logger.info('%s> Connected', __class__.__name__)

        while True:
            try:
                net_data = self.request.recv(512)

            except ConnectionResetError:
                logger.error('%s> ConnectionResetError', __class__.__name__)
                break

            except KeyboardInterrupt:
                logger.error('%s> KeyboardInterrupt', __class__.__name__)
                continueToServe = False
                break

            logger.debug('%s> net_data: %s', __class__.__name__, net_data)
            
            if len(net_data) == 0:
                logger.debug('%s> Connection closed', __class__.__name__)
                break

            if not self.server.worker.is_alive():
                logger.debug('%s> worker is dead', __class__.__name__)
                continueToServe = False
                break

            try:
                self.server.worker.send_msg(net_data.decode('utf-8').strip())

            except UnicodeDecodeError:
                pass

        logger.debug('%s> handle() done', __class__.__name__)
            
#
# サーバークラス
#
#   サーバーのメインループ
#   初期化時にハンドラークラスを登録する
#   main関数の server.serve_forever() でメインループを開始する
#
class SampleServer(socketserver.TCPServer):
    DEF_PORT_NUM = 12345
    allow_reuse_address = True

    def __init__(self, worker, port_num=0):
        self.worker	= worker

        self.port_num	= port_num
        if self.port_num == 0:
            self.port_num = __class__.DEF_PORT_NUM
            
        return super().__init__(('', self.port_num), SampleHandler)

    def __del__(self):
        global continueToServe
        continueToServer = False
        logger.debug('%s> __del__()', __class__.__name__)

#####
@click.command(help='Sample Telnet server')
@click.option('--port', '-p', type=int, default=0,
              help='port number')
def main(port):
    global continueToServe
    continueToServe = True
    
    worker = SampleWorker()
    worker.start()
    logger.info('main> worker started')

    try:
        server = SampleServer(worker, port)

    except Exception as e:
        logger.error('main> Exception %s %s', type(e), e)
        continueToServe = False

    try:
        while continueToServe:
            server.handle_request()
            logger.info('main> handle_request() done')

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

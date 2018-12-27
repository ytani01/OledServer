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

#
# ワーカースレッド
#
#   ハンドラースレッドからのメッセージを受信して、処理を実行する。
#   メッセージ受信はキューを介して行うため、非同期実行可能。
#
class SampleThread(threading.Thread):
    # msg = {'type':'...', 'content':'...'}
    MSG_TYPE = ('cmd', 'msg')
    
    def __init__(self):
        self.msgq = queue.Queue()
        super().__init__()

    def send_msg(self, text):
        msg = {}
        msg['type'] = ''
        msg['content'] = text
        self.msgq.put(msg)
        
    def send_cmd(self, text):
        msg = {}
        msg['type'] = 'cmd'
        msg['content'] = text
        self.msgq.put(msg)
        
    def recv_msg(self):
        msg = self.msgq.get()
        print('%s> msg = ' % __class__.__name__, msg)
        return  msg

    def msg_empty(self):
        return self.msgq.empty()

    def end(self):
        self.send_cmd('end')
        
    def run(self):
        while True:
            if self.msg_empty():
                print('%s> wait msg ..' % __class__.__name__)
            msg = self.recv_msg()

            if msg['type'] == 'cmd':
                if msg['content'] == 'end':
                    break
            else:
                #
                # main work
                #
                print('%s> %s' % (__class__.__name__, msg['content']))
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
    def __init__(self, request, client_address, server):
        self.worker = server.worker
        
        return super().__init__(request, client_address, server)

    def net_write(self, msg):
        try:
            self.wfile.write(msg)
        except:
            print('%s> net_write(): Error !' % __class__.__name__)

    def handle(self):
        # Telnet Protocol
        #
        # mode character
        #  0xff IAC .. Interpret as Command
        #  0xfd DO
        #  0x22 LINEMODE
        self.net_write(b'\xff\xfd\x22')

        self.net_write('OK> \r\n'.encode('utf-8'))

        flag_continue = True
        while flag_continue:
            try:
                net_data = self.request.recv(512)
            except ConnectionResetError:
                print('%s> ConnectionResetError' % __class__.__name__)
                return

            print('%s> net_data:' % __class__.__name__, net_data)
            if len(net_data) == 0:
                print('%s> Connection closed' % __class__.__name__)
                break

            msg = {'type':'', 'content':''}
            try:
                self.worker.send_msg(net_data.decode('utf-8'))
            except UnicodeDecodeError:
                pass
            
#
# サーバークラス
#
#   サーバーのメインループ
#   初期化時にハンドラークラスを登録する
#   main関数の server.serve_forever() でメインループを開始する
#
class SampleServer(socketserver.TCPServer):
    DEF_PORT_NUM = 12345

    def __init__(self, worker, port_num=0):
        self.port_num = port_num
        if self.port_num == 0:
            self.port_num = __class__.DEF_PORT_NUM

        self.worker = worker
        if not self.worker.is_alive():
            self.worker.start()

        return super().__init__(('', self.port_num), SampleHandler)

    def __del__(self):
        self.worker.end()
        self.worker.join()

#####
@click.command(help='Sample Telnet server')
@click.option('--port', '-p', type=int, default=0,
              help='port number')
def main(port):
    worker_th = SampleThread()
    worker_th.start()

    server = SampleServer(worker_th, port)
    server.serve_forever()

if __name__ == '__main__':
    try:
        main()
    except(KeyboardInterrupt):
        print('== Interrupted ==')
    finally:
        print('== End ==')

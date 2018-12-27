#!/usr/bin/env python3
#
# (c) 2018 Yoichi Tanibayashi
#
import sys
import threading
import queue
import socketserver

class PrintThread(threading.Thread):
    # msg = {'type':'...', 'content':'...'}
    MSG_TYPE = ('cmd', 'msg')
    
    def __init__(self):
        self.msgq = queue.Queue()

    def send_msg(self, text):
        msg['type'] = ''
        msg['content'] = text
        self.msgq.put(msg)
        
    def send_cmd(self, text):
        msg['type'] = 'cmd'
        msg['content'] = text
        self.msgq.put(msg)
        
    def recv_msg(self):
        msg = self.msgq.get()
        print('msg =', msg)
        return  msg

    def msg_empty(self):
        return self.msgq.empty()

    def end(self):
        self.send_cmd('end')
        
    def run(self):
        while True:
            print('wait msg ..')
            msg = self.recv_msg()

            if msg['type'] == 'cmd':
                if msg['content'] == 'end':
                    break
            else:
                #
                # main work
                #
                print(msg['content'])
                time.sleep(1)

            time.sleep(0.01)
            
class PrintHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.woker = server.worker
        
        return supser().__init__(request, client_address, server)

    def net_write(self, msg):
        try:
            self.wfile.write(msg)

    def handle(self):
        # Telnet Protocol
        #
        # mode character
        #  0xff IAC .. Interpret as Command
        #  0xfd DO  .. 相手に要求
        #  0x22 LINEMODE .. テキストライン編集後、ライン毎に送信
        self.net_write(b'\xff\xfd\x22')

        self.net_write('OK> \r\n'.encode('utf-8'))

        flag_continue = True:
        while flag_continue:
            try:
                net_data = self.request.recv(512)
            except ConectionResetError:
                return

            print('net_data:', net_data)
            if len(net_data) == 0:
                break

            msg = {'type':'', 'content':''}
            try:
                worker.send_msg(net_data.decode('utf-8'))
            except UnicodeDecodeError:
                pass
            
#
# 
#
class PrintServer(socketserver.TCPServer):
    DEF_PORT_NUM = 12345

    def __init__(self, worker, port_num=0):
        self.port_num = port_num
        if self.port_num == 0:
            self.port_num = __class__.DEF_PORT_NUM

        self.worker = worker
        if not self.worker.is_alive():
            self.worker.start()

        return super().__init__(('', self.port_num), PrintHandler)

    def __del__(self):
        self.worker.end()
        self.worker.join()
        return super().__del__()


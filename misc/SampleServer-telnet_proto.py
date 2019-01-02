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

###
TELNET_CMD_Fx = [ ['SE',	'Sub-negotiation End'],
	          ['NOP',	'No Operation'],	
                  ['DM',	'Data Mark'],
                  ['BRK',	'Break'],
                  ['IP',	'Interrupt Process'],
                  ['AO',	'About Output'],
                  ['AYT',	'Are You There'],
                  ['EC',	'Erase Character'],
                  ['EL',	'Erase Line'],
                  ['GA',	'Go Ahead'],
                  ['SB',	'Sub-negotiation Begin'],
                  ['WILL',	'Will'],
                  ['WONT',	'Won\'t'],
                  ['DO',	'Do'],
                  ['DONT',	'Don\'t'],
                  ['IAC',	'Interpret as Command']	]

TELNET_OPT = { 0x00:	'Binary Transmission',
               0x01:	'Echo',
               0x03:	'Suppress Go Ahead',
               0x05:	'Status',
               0x06:	'Timing Mark',
               0x18:	'Terminal Type',
               0x19:	'End of Record',
               0x22:	'Linemode',
               0x23:	'X Display Location',
               0xff:	'Extended Option List'	}

#
def parse_telnet_cmd(data):
    out = []
    stat = ''
    for d in data:
        code = int(d)
        cmd_idx = code - 0xf0
        cmd = ''
        if cmd_idx >= 0 and cmd_idx <= 0xf:
            cmd = TELNET_CMD_Fx[cmd_idx][0]
        if stat != 'SB' and cmd == 'IAC':
            out.append('[%s]' % cmd)
            stat = 'IAC'
            continue
        if stat == 'IAC':
            out.append('[%s]' % cmd)
            if cmd in ['WILL', 'WONT', 'DO', 'DONT']:
                stat = 'OPT'
            if cmd == 'SB':
                stat = 'SB'
            continue
        if stat == 'OPT':
            opt = TELNET_OPT[code]
            out.append('[%s]' % opt)
        if stat == 'SB':
            opt = '%02X' % code
            if cmd == 'SE':
                stat = ''
                opt = cmd
            out.append('[%s]' % opt)
    return out

#
# ワーカースレッド
#
#   ハンドラースレッドからのメッセージを受信して、処理を実行する。
#   メッセージ受信はキューを介して行うため、非同期実行可能。
#
class SampleWorker(threading.Thread):
    # msg = {'type':'...', 'content':'...'}
    MSG_TYPE = ('cmd', 'msg')
    
    def __init__(self):
        self.msgq = queue.Queue()
        super().__init__()

    def send(self, msg_type, msg_text):
        msg = {}
        msg['type'] = msg_type
        msg['content'] = msg_text
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
        logger.debug('%s> join()', __class__.__name__)
        self.join()
        logger.debug('%s> join() done', __class__.__name__)

    def run(self):
        while True:
            if self.msg_empty():
                logger.debug('%s> wait msg ..', __class__.__name__)
            msg_type, msg_content = self.recv()

            if msg_type == 'cmd' and msg_content == 'end':
                logger.debug('%s> recv end cmd', __class__.__name__)
                break
            else:
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
    def __init__(self, request, client_address, server):
        self.worker = server.worker
        
        return super().__init__(request, client_address, server)

    def write(self, msg):
        try:
            self.wfile.write(msg)

            telnet_cmd = parse_telnet_cmd(msg)
            if len(telnet_cmd) > 0:
                logger.debug('write> (TELNET) %s' % telnet_cmd)
        except:
            logger.error('%s> write(): Error !', __class__.__name__)

    def handle(self):
        global continueToServe
        
        # Telnet Protocol
        #
        # mode character
        #  0xff IAC .. Interpret as Command
        #  0xfb WILL
        #  0xfc WON'T
        #  0xfd DO
        #  0xfe DON'T
        #
        #  0x01 ECHO
        #  0x22 LINEMODE
        #
        # 以下、一見逆に思えるが…
        #self.write(b'\xff\xfd\x22')	# 1文字ずつ
        self.write(b'\xff\xfc\x22')	# 1行ずつ

        self.write('[Connected]\r\n'.encode('utf-8'))

        while True:
            msg = {'type':'', 'content':''}
            try:
                net_data = self.request.recv(512)
            except ConnectionResetError:
                logger.error('%s> ConnectionResetError', __class__.__name__)
                break
            except KeyboardInterrupt:
                logger.error('%s> KeyboardInterrupt', __class__.__name__)
                continueToServe = False
                break

            telnet_cmd =  parse_telnet_cmd(net_data)
            if telnet_cmd != []:
                logger.debug('(TELNET) %s', telnet_cmd)
                
            net_data = net_data[len(telnet_cmd):]
            logger.debug('%s> net_data: %s', __class__.__name__, net_data)
            
            if len(net_data) + len(telnet_cmd) == 0:
                logger.debug('%s> Connection closed', __class__.__name__)
                break

            if len(net_data) == 0:
                continue

            if not self.worker.is_alive():
                logger.debug('%s> worker is dead', __class__.__name__)
                continueToServe = False
                break

            try:
                self.worker.send_msg(net_data.decode('utf-8').strip())
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

    def __init__(self, worker, port_num=0):
        self.port_num = port_num
        if self.port_num == 0:
            self.port_num = __class__.DEF_PORT_NUM

        self.worker = worker
        if self.worker and not self.worker.is_alive():
            self.worker.start()
            logger.debug('%s > worker started', __class__.__name__)

        return super().__init__(('', self.port_num), SampleHandler)

    def __del__(self):
        global continueToServe
        
        logger.debug('%s> __del__()', __class__.__name__)
        continueToServer = False

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
            logger.warn('main> handle_request() done')
    except KeyboardInterrupt:
        logger.warn('== Interrupted ==')

    if worker.is_alive():
        worker.end()
    return


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warn('== Interrupted ==')
    finally:
        logger.warn('== End ==')

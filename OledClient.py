#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
import telnetlib
import sys
import time
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

#####
class OledClient:
    DEF_HOST = 'localhost'
    DEF_PORT = 12345

    CMD_PREFIX = '@@@'
    ACK = 'ACK\r\n'.encode('utf-8')

    def __init__(self, host='', port=0):
        logger.debug('host=%s, port=%d', host, port)
        self.host = host
        self.port = port

    def __del__(self):
        logger.debug('__del__')

    # for 'with' statement
    def __enter__(self):
        logger.debug('__enter__')
        self.open()
        return self
    
    # for 'with' statement
    def __exit__(self, ex_type, ex_value, trace):
        logger.debug('__exit__(%s,%s,%s)', ex_type, ex_value, trace)
        self.close()

    def open(self):
        logger.debug('open> begin')
        try:
            self.tn = telnetlib.Telnet(self.host, self.port)
            logger.debug('open> Telnet %s', self.tn)
            self.wait_ack()
        except Exception as e:
            self.tn = None
            logger.error('open> %s, %s', type(e), e)
            raise(e)

    def close(self):
        logger.debug('close()')
        if self.tn:
            self.tn.close()
        self.tn = None
        
    def send(self, text):
        try:
            self.tn.write((text + '\r\n').encode('utf-8'))
            logger.debug('send> %s', text)
            if not self.wait_ack():
                return False
        except Exception as e:
            logger.error('send> %s:%s', type(e), e)
            return False
        return True

    def wait_ack(self, timeout=2):
        ret = self.tn.read_until(__class__.ACK, timeout)
        logger.debug('wait_ack> %s', ret)
        if ret == b'':
            logger.error('wait_ack> timeout')
            return False
        logger.debug('wait_ack> done')
        return True

    def println(self, text):
        return self.send(text)

    def clear(self):
        return self.send('%s clear' % __class__.CMD_PREFIX)

    def zenkaku(self, flag):
        if flag:
            return self.send('%s zenkaku_on' % __class__.CMD_PREFIX)
        else:
            return self.send('%s zenkaku_off' % __class__.CMD_PREFIX)

#####
@click.command(help='OLED client')
@click.argument('text', type=str, nargs=-1)
@click.option('--host', '-h', type=str, default=OledClient.DEF_HOST,
              help='hostname or IP address')
@click.option('--port', '-p', type=int, default=OledClient.DEF_PORT,
              help='port number')
def main(text, host, port):
    logger.debug('text=%s', text)

    if len(text) > 0:
        with OledClient(host, port) as cl:
            t = ' '.join(text)
            print(t)
            cl.println(t)
        return

    ### open/close
    cl = OledClient(host, port)
    cl.open()
    cl.clear()
    cl.zenkaku(False)
    cl.println('Hellow world 1')
    cl.zenkaku(True)
    cl.println('Hellow world 1')
    time.sleep(2)
    cl.clear()
    cl.println('Hellow world 2')
    cl.zenkaku(False)
    cl.println('Hellow world 2')
    cl.close()

    time.sleep(3)

    ### with .. as ..
    with OledClient(host, port) as cl:
        cl.clear()
        cl.zenkaku(False)
        cl.println('Hellow world 3')
        cl.zenkaku(True)
        cl.println('Hellow world 3')
        time.sleep(2)
        cl.clear()
        cl.println('Hellow world 4 ')
        cl.zenkaku(False)
        cl.println('Hellow world 4')

if __name__ == '__main__':
    main()

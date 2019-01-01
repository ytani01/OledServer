#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
import telnetlib
import sys
import time
import click
from ipaddr import ipaddr

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(DEBUG)
console_handler = StreamHandler()
console_handler.setLevel(DEBUG)
#handler_fmt = Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
console_handler.setFormatter(handler_fmt)
logger.addHandler(console_handler)
logger.propagate = False

#####
class OledClient:
    DEF_HOST = 'localhost'
    DEF_PORT = 12345

    CMD_PREFIX = '@@@'
    ACK = 'ACK\r\n'.encode('utf-8')

    def __init__(self, host='', port=0):
        self.host, self.port = __class__.DEF_HOST, __class__.DEF_PORT
        if host != '':
            self.host = host
        if port != 0:
            self.port = port

        logger.debug('(\'%s\',%d): self.host=\'%s\', self.port=%d',
                     host, port, self.host, self.port)

    def __del__(self):
        logger.debug('()')

    # for 'with' statement
    def __enter__(self):
        logger.debug('()')
        self.open()
        logger.debug('done')
        return self
    
    # for 'with' statement
    def __exit__(self, ex_type, ex_value, trace):
        logger.debug('(%s,%s,%s)', ex_type, ex_value, trace)
        self.close()
        logger.debug('(%s,%s,%s):done', ex_type, ex_value, trace)

    def open(self, host='', port=0):
        if host != '':
            self.host = host
        if port != 0:
            self.port = port
            
        logger.debug('(\'%s\',%d): self.host=\'%s\', self.port=%d',
                     host, port, self.host, self.port)
        try:
            self.tn = telnetlib.Telnet(self.host, self.port)
            ack = self.wait_ack()
            logger.debug('tn=%s, wait_ack():%s', self.tn, ack)
        except Exception as e:
            self.tn = None
            logger.error('%s, %s', type(e), e)
            raise(e)

    def close(self):
        logger.debug('()')
        if self.tn:
            self.tn.close()
        self.tn = None
        
    def send(self, text):
        try:
            self.tn.write((text + '\r\n').encode('utf-8'))
            logger.debug('\'%s\'', text)
            if not self.wait_ack():
                return False
        except Exception as e:
            logger.error('send> %s:%s', type(e), e)
            return False
        return True

    def wait_ack(self, timeout=2):
        ret = self.tn.read_until(__class__.ACK, timeout)
        logger.debug('%s', ret)
        if ret == b'':
            logger.error('timeout')
            return False
        return True

    def print(self, text):
        return self.send(text)

    def clear(self):
        return self.send('%s clear' % __class__.CMD_PREFIX)

    def zenkaku(self, flag=True):
        return self.send('%s zenkaku %s' % (__class__.CMD_PREFIX, flag))

    def set_part(self, part='body'):
        return self.send('%s %s' % (__class__.CMD_PREFIX, part))

    def set_row(self, row=0):
        return self.send('%s row %d' % (__class__.CMD_PREFIX, row))

    def set_crlf(self, flag=True):
        return self.send('%s crlf %s' % (__class__.CMD_PREFIX, flag))

#####
@click.command(help='OLED client')
@click.argument('text', type=str, default='')
@click.option('--host', '-h', type=str, default=OledClient.DEF_HOST,
              help='hostname or IP address')
@click.option('--port', '-p', type=int, default=OledClient.DEF_PORT,
              help='port number')
@click.option('--debug', '-d', is_flag=True, default=False,
              help='debug flag')
def main(text, host, port, debug):
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    if text == '':
        text = 'Hello, world !'
    logger.debug('text=%s', text)
        
    ### open/close
    cl = OledClient()
    cl.open(host, port)
    cl.set_part('body')
    cl.clear()
    cl.set_row(1)
    cl.zenkaku(False)
    cl.print(text)
    cl.zenkaku(True)
    cl.print(text)
    cl.close()

    #time.sleep(2)
    
    ### with .. as ..
    ip = ipaddr().ip_addr()
    with OledClient(host, port) as cl:
        #cl.set_part('body')
        #cl.clear()

        cl.set_part('header')
        cl.set_row(0)
        cl.set_crlf(True)
        cl.zenkaku(True)
        cl.print('@DATE@')
        cl.zenkaku(True)
        cl.print('@TIME@')
        #cl.print('@IFNAME@ @IPADDR@')

        cl.set_part('footer')
        cl.set_row(0)
        cl.set_crlf(False)
        cl.zenkaku(True)
        cl.print('@IPADDR@')

        cl.set_part('body')
        cl.set_crlf(True)
        for i in range(3):
            cl.clear()
            cl.zenkaku(False)
            cl.print('ABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞ')
            cl.zenkaku(True)
            cl.print(ip)
        
if __name__ == '__main__':
    main()

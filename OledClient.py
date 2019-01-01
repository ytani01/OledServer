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
def time_mode(host, port, sec):
    count = 0
    while True:
        count += 1
        print('count=%d' % count)
        with OledClient(host, port) as oc:
            oc.set_part('header')
            oc.set_row(0)
            oc.set_crlf(True)
            oc.zenkaku(True)
            oc.print('@DATE@')
            oc.print('%s [%d]' % ('@TIME@', count))

        time.sleep(sec)

#####
@click.command(help='OLED client')
@click.argument('text', type=str, default='')
@click.option('--host', '-h', 'host', type=str, default=OledClient.DEF_HOST,
              help='hostname or IP address')
@click.option('--port', '-p', 'port', type=int, default=OledClient.DEF_PORT,
              help='port number')
@click.option('--timemode', '-t', 'timemode', type=int, default=0,
              help='time client mode')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(text, host, port, timemode, debug):
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    if timemode > 0:
        time_mode(host, port, timemode)
        sys.exit(0)
        
    if text == '':
        text = 'Hello, world !'
    logger.debug('text=%s', text)
        
    ### open/close
    oc = OledClient()
    oc.open(host, port)
    oc.set_part('body')
    oc.clear()
    oc.set_row(1)
    oc.zenkaku(False)
    oc.print(text)
    oc.zenkaku(True)
    oc.print(text)
    oc.close()

    #time.sleep(2)
    
    ### with .. as ..
    ip = ipaddr().ip_addr()
    with OledClient(host, port) as oc:
        #oc.set_part('body')
        #oc.clear()

        oc.set_part('header')
        oc.set_row(0)
        oc.set_crlf(True)
        oc.zenkaku(True)
        oc.print('@DATE@')
        oc.zenkaku(True)
        oc.print('@TIME@')
        #oc.print('@IFNAME@ @IPADDR@')

        oc.set_part('footer')
        oc.set_row(0)
        oc.set_crlf(False)
        oc.zenkaku(True)
        oc.print('@IPADDR@')

        oc.set_part('body')
        oc.set_crlf(True)
        for i in range(3):
            oc.clear()
            oc.zenkaku(False)
            oc.print('ABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞ')
            oc.zenkaku(True)
            oc.print(ip)
        
if __name__ == '__main__':
    main()

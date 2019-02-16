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
logger.setLevel(INFO)
console_handler = StreamHandler()
console_handler.setLevel(DEBUG)
#handler_fmt = Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
handler_fmt = Formatter('%(asctime)s %(levelname)s %(name)s:%(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
console_handler.setFormatter(handler_fmt)
logger.addHandler(console_handler)
logger.propagate = False
def get_logger(name, debug=False):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)

    return l


#####
class OledClient:
    DEF_HOST = 'localhost'
    DEF_PORT = 12345

    CMD_PREFIX = '@@@'
    ACK = 'ACK\r\n'.encode('utf-8')

    def __init__(self, host=DEF_HOST, port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('host=%s, port=%d', host, port)
        
        self.host = __class__.DEF_HOST
        self.port = __class__.DEF_PORT
        if host != '':
            self.host = host
        if port != 0:
            self.port = port

        self.logger.debug('(\'%s\',%d): self.host=\'%s\', self.port=%d',
                          host, port, self.host, self.port)

    # for 'with' statement
    def __enter__(self):
        self.logger.debug('')
        self.open()
        self.logger.debug('done')
        return self
    
    # for 'with' statement
    def __exit__(self, ex_type, ex_value, trace):
        self.logger.debug('(%s,%s,%s)', ex_type, ex_value, trace)
        self.close()
        self.logger.debug('(%s,%s,%s):done', ex_type, ex_value, trace)

    def open(self, host='', port=0):
        
        if host != '':
            self.host = host
        if port != 0:
            self.port = port
            
        self.logger.debug('(\'%s\',%d): self.host=\'%s\', self.port=%d',
                          host, port, self.host, self.port)
        try:
            self.tn = telnetlib.Telnet(self.host, self.port)
            ack = self.wait_ack()
            self.logger.debug('tn=%s, wait_ack():%s', self.tn, ack)
        except Exception as e:
            self.tn = None
            self.logger.error('%s, %s', type(e), e)
            raise(e)

    def close(self):
        self.logger.debug('()')
        if self.tn:
            self.tn.close()
        self.tn = None
        
    def send(self, text):
        try:
            self.tn.write((text + '\r\n').encode('utf-8'))
            self.logger.debug('\'%s\'', text)
            if not self.wait_ack():
                return False
        except Exception as e:
            self.logger.error('send> %s:%s', type(e), e)
            return False
        return True

    def wait_ack(self, timeout=2):
        ret = self.tn.read_until(__class__.ACK, timeout)
        self.logger.debug('%s', ret)
        if ret == b'':
            self.logger.error('timeout')
            return False
        return True

    def clear(self):
        return self.send('%s clear' % __class__.CMD_PREFIX)

    def zenkaku(self, flag=True):
        return self.send('%s zenkaku %s' % (__class__.CMD_PREFIX, flag))

    def part(self, part='body'):
        return self.send('%s %s' % (__class__.CMD_PREFIX, part))

    def row(self, row=0):
        return self.send('%s row %d' % (__class__.CMD_PREFIX, row))

    def crlf(self, flag=True):
        return self.send('%s crlf %s' % (__class__.CMD_PREFIX, flag))

#####
def clock_mode(host, port, myip, mode=1, sec=2):
    prev_str_time = ''
    while True:
        str_time = time.strftime('%H:%M')
        logger.debug('%s', time.strftime('%H:%M:%S'))

        if str_time != prev_str_time:
            logger.info('update server time: %s', str_time)

            with OledClient(host, port) as oc:
                # header
                oc.part('header')
                oc.clear()
                oc.crlf(False)
                oc.zenkaku(False)
                oc.row(0)
                oc.send('@DATE@  @H@:@M@ ')
                if mode == 1:
                    oc.zenkaku(True)
                    oc.row(1)
                    oc.send(myip)

                # footer
                if mode == 2:
                    oc.part('footer')
                    oc.clear()
                    oc.crlf(False)
                    oc.zenkaku(True)
                    oc.row(0)
                    oc.send(myip)

                # body
                oc.part('body')
                oc.crlf(True)

            prev_str_time = str_time

        time.sleep(sec)

#####
@click.command(help='OLED client')
@click.argument('text', type=str, default='')
@click.option('--host', '-h', 'host', type=str, default=OledClient.DEF_HOST,
              help='hostname or IP address')
@click.option('--port', '-p', 'port', type=int, default=OledClient.DEF_PORT,
              help='port number')
@click.option('--clockmode', '-c', 'clockmode', type=int, default=0,
              help='clock client mode (0:off)')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(text, host, port, clockmode, debug):
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    myip = ipaddr().ip_addr()
    logger.debug('myip = %s', myip)

    if clockmode > 0:
        try:
            clock_mode(host, port, myip, clockmode)
        except Exception as e:
            logger.error(e)
            logger.warn('exit(0)')
            sys.exit(0)

    if text != '':
        with OledClient(host, port) as oc:
            oc.send(text)

        sys.exit(0)
        
    text = 'Hello, world !'
    logger.debug('text=%s', text)
        
    ### open/close
    oc = OledClient()
    oc.open(host, port)
    oc.part('body')
    oc.clear()
    oc.row(1)
    oc.zenkaku(False)
    oc.send(text)
    oc.zenkaku(True)
    oc.send(text)
    oc.close()

    time.sleep(2)
    
    ### with .. as ..
    with OledClient(host, port) as oc:
        #oc.part('body')
        #oc.clear()

        oc.part('footer')
        oc.row(0)
        oc.crlf(False)
        oc.zenkaku(True)
        oc.send('@IPADDR@')

        oc.part('body')
        oc.crlf(True)
        oc.clear()
        for i in range(3):
            oc.zenkaku(False)
            oc.send('ABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞ')
            oc.zenkaku(True)
            oc.send(myip)
            time.sleep(2)
            oc.send('---')
            time.sleep(2)
        
if __name__ == '__main__':
    main()

#!/usr/bin/env python3
#
import time
import click

import RPi.GPIO as GPIO
from OledClient import OledClient
from RotaryEncoder import RotaryKey

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
class Demo:
    def __init__(self, host, port, pin_rot, pin_sw, debug=False):
        self.host = host
        self.port = port
        self.pin_rot = pin_rot
        self.pin_sw = pin_sw

        self.rk = RotaryKey(self.pin_rot, pin_sw, self.rk_callback,
                            debug=True)

        self.oc = OledClient(self.host, self.port)
        self.oc.open()
        self.oc.part('body')
        self.oc.clear()
        self.oc.row(0)
        self.oc.zenkaku(True)
        self.oc.crlf(False)
        #self.oc.send('%s[%s]' % (self.rk.get_text(), self.rk.get_ch()))
        self.oc.close()

        self.text = ''

    def oled_out(self, text, ch, enter=False):
        self.oc.open()
        self.oc.part('body')
        self.oc.zenkaku(True)
        
        if enter:
            self.oc.crlf(True)
            self.oc.send(text)
            self.oc.close()
            return()
            
        if ch == RotaryKey.CH_BS:
            ch = '≪'
        if ch == RotaryKey.CH_ENT:
            ch = '◎'
        
        self.oc.crlf(False)
        self.oc.send('%s[%s]' % (text, ch))
        self.oc.close()

    def rk_callback(self, out_ch, cur_ch):
        logger.debug('out_ch=%s, cur_ch=%s', out_ch, cur_ch)

        if out_ch == RotaryKey.CH_BS:
            pass
        if out_ch == RotaryKey.CH_ENT:
            pass
        if out_ch != '':
            self.text += out_ch
            
        self.oled_out(self.text, cur_ch, False)        

#####
@click.command(help='demo program')
@click.option('--server', '-s', 'server_host', type=str, default='localhost',
              help='server host')
@click.option('--port', '-p', 'server_port', type=int, default=12345,
              help='port')
@click.option('--pin1', '-p1', 'pin1', type=int, default=27,
              help='rotary encoder pin1')
@click.option('--pin2', '-p2', 'pin2', type=int, default=22,
              help='rotary encoder pin2')
@click.option('--pinsw', '-ps', 'pin_sw', type=int, default=17,
              help='switch pin')
def main(server_host, server_port, pin1, pin2, pin_sw):
    logger.debug('%s, %d, %d', server_host, server_port, pin1)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    demo = Demo(server_host, server_port, [pin1, pin2], pin_sw)

    while True:
        time.sleep(.1)

if __name__ == '__main__':
    main()

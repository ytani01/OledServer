#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import time
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, ssd1327
from PIL import Image, ImageDraw, ImageFont

import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
    datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False
def init_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l

#####
class Oled:
    I2C_ADDR = 0x3C
    
    def __init__(self, display_name='ssd1306', i2c_bus=1, i2c_addr=I2C_ADDR,
                 debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('')
        self.debug = debug

        self.display_name  = display_name
        self.i2c_bus  = i2c_bus
        self.i2c_addr = i2c_addr

        self.enable = True

    def __enter__(self):
        self.logger.debug('enter \'with\' block')
        return self.open()

    def __exit__(self, ex_type, ex_value, trace):
        self.logger.debug('(%s,%s,%s)', ex_type, ex_value, trace)
        self.close()
        self.logger.debug('exit \'with\' block')

    def open(self):
        self.logger.debug('')
        self.i2c = i2c(port=self.i2c_bus, address=self.i2c_addr)

        self.disp = None
        if self.display_name == 'ssd1306':
            self.disp = ssd1306(self.i2c)
            self.mode = '1'
        if self.display_name == 'ssd1327':
            #self.disp = ssd1327(self.i2c, framebuffer='diff_to_previous')
            self.disp = ssd1327(self.i2c)
            self.mode = 'RGB'
        if self.disp == None:
            self.logger.error('invalid display_name:%s', self.display_name)
            self.enable = False
            return None
        #self.disp.persist = True

        self.logger.debug('self.disp')
        for x in dir(self.disp):
            self.logger.debug('  %s', x)

        self.width  = self.disp.width
        self.height = self.disp.height

        self.logger.debug('w=%d, h=%d', self.disp.width, self.disp.height)
        
        self.image = Image.new(self.mode, self.disp.size)
        self.draw  = ImageDraw.Draw(self.image)
        self.image2 = Image.new(self.mode, self.disp.size)
        self.draw2  = ImageDraw.Draw(self.image2)

        self.logger.debug('self.draw')
        for x in dir(self.draw):
            self.logger.debug('  %s', x)

        self.display()

        return self

    def close(self):
        self.logger.debug('')
        self.disp.cleanup()

    def display(self):
        self.logger.debug('')
        self.disp.display(self.image)

##### sample application
class Sample:
    def __init__(self, display, i2c_bus, i2c_addr, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.debug = debug
        self.logger.debug('display  = %s',   display)
        self.logger.debug('i2c_bus  = %d',   i2c_bus)
        self.logger.debug('i2c_addr = 0x%X', i2c_addr)

        self.display  = display
        self.i2c_bus  = i2c_bus
        self.i2c_addr = i2c_addr

    def main(self):
        with Oled(self.display, self.i2c_bus, self.i2c_addr,
                  debug=self.debug) as ol:
            while True:
                ol.draw.rectangle([(0, 0),(ol.width - 1, ol.height - 1)],
                                   outline=255, width=10, fill=64)
                ol.display()
                
                time.sleep(2)
                
                ol.draw.rectangle([(20, 20),(ol.width - 21, ol.height - 21)],
                                  outline=255, width=10, fill=128)
                ol.display()
                
                time.sleep(2)
            
    def finish(self):
        self.logger.debug('')


#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('display', type=str, default='ssd1306', nargs=1)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(display, debug):
    logger = init_logger('', debug)
    logger.debug('display  = %s', display)
    logger.debug('debug    = %s', debug)

    try:
        obj = Sample(display, 1, 0x3C, debug=debug)
        obj.main()
    finally:
        obj.finish()

if __name__ == '__main__':
    main()

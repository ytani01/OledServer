#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import time
import threading
import RPi.GPIO as GPIO
from luma.core.interface.serial import i2c, spi
from luma.oled.device import ssd1306, ssd1327, ssd1331
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
    
    def __init__(self, display_name='ssd1331', param1=0, param2=I2C_ADDR,
                 debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('display_name = %s',   display_name)
        self.logger.debug('param1       = %d',   param1)
        self.logger.debug('param2       = 0x%X', param2)
        self.debug = debug

        self.display_name  = display_name
        self.param1 = param1
        self.param2 = param2

        self.enable = True
        if self.open() == self:
            self.enable = True

    def __enter__(self):
        self.logger.debug('enter \'with\' block')

        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.logger.debug('(%s,%s,%s)', ex_type, ex_value, trace)

        self.cleanup()
        self.logger.debug('exit \'with\' block')

    def open(self):
        self.logger.debug('')

        GPIO.setwarnings(False)
        
        self.disp = None
        if self.display_name == 'ssd1306':
            self.serial = i2c(port=self.param1, address=self.param2)
            self.disp = ssd1306(self.serial)
            self.mode = '1'
        if self.display_name == 'ssd1327':
            self.serial = i2c(port=self.param1, address=self.param2)
            #self.disp = ssd1327(self.i2c, framebuffer='diff_to_previous')
            self.disp = ssd1327(self.serial)
            self.mode = 'RGB'
        if self.display_name == 'ssd1331':
            self.serial = spi(device=self.param1, port=self.param2)
            self.disp = ssd1331(self.serial)
            self.mode = 'RGB'
        if self.disp == None:
            self.logger.error('invalid display_name:%s', self.display_name)
            self.enable = False
            return None
        self.disp.persist = True

        self.image = Image.new(self.mode, self.disp.size)
        self.draw  = ImageDraw.Draw(self.image)

        self.clear()
        
        return self

    def available(self):
        if self.enable:
            self.logger.debug('OK')
            return True

        self.logger.error('NG')
        return False

    def cleanup(self):
        if not self.available():
            self.logger.debug('OLED is not available')
            return

        self.logger.debug('self.disp.cleanup()')
        self.disp.cleanup()

    def clear(self, display_now=False):
        self.logger.debug('display_now = %s', display_now)
        if not self.available():
            self.logger.debug('OLED is not available')
            return
        
        xy = [(0, 0), (self.disp.width - 1, self.disp.height - 1)]
        self.draw.rectangle(xy, outline=0, fill=0)

        if display_now:
            self.display()

    def display(self):
        self.logger.debug('')
        if not self.available():
            return
        
        self.disp.display(self.image)

##### sample application
class BG:
    def __init__(self, ol, w, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.debug = debug
        self.logger.debug('w = %d', w)

        self.ol = ol
        self.w  = w

        (self.x1, self.y1) = (0, 0)
        (self.x2, self.y2) = (self.ol.disp.width - 1, self.ol.disp.height - 1)

    def draw(self):
        xy = [(self.x1, self.y1), (self.x2, self.y2)]
        self.ol.draw.rectangle(xy, outline=255, width=self.w, fill=0)
        
class Ball:
    def __init__(self, ol, color, xy, r, vxy=(0, 0), debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.debug = debug
        self.logger.debug('color = %d', color)
        self.logger.debug('xy    = %s', xy)
        self.logger.debug('r     = %d', r)
        self.logger.debug('vxy   = %s', vxy)

        self.ol = ol
        self.color = color
        (self.x, self.y) = xy
        self.r = r
        (self.vx, self.vy) = vxy

        self.lock = threading.Lock()

    def move(self):
        self.lock.acquire()
        self.logger.debug('')

        self.x += self.vx
        self.y += self.vy

        if self.x <= 0:
            self.x = 0
            self.vx = -self.vx
        if self.x >= self.ol.disp.width - 1:
            self.x = self.ol.disp.width - 1
            self.vx = -self.vx
        if self.y <= 0:
            self.y = 0
            self.vy = -self.vy
        if self.y >= self.ol.disp.height - 1:
            self.y = self.ol.disp.height - 1
            self.vy = -self.vy

        self.lock.release()

    def draw(self):
        self.lock.acquire()
        self.logger.debug('')
        
        x1 = round(self.x - self.r / 2)
        y1 = round(self.y - self.r / 2)
        x2 = x1 + self.r
        y2 = y1 + self.r

        self.ol.draw.rectangle([(x1, y1), (x2, y2)],
                               outline=self.color, fill=self.color)
        
        self.lock.release()

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

        self.ol = Oled(self.display, self.i2c_bus, self.i2c_addr,
                       debug=self.debug)

        self.bg   = BG(self.ol, 2, debug=debug)
        self.ball = []
        self.ball.append(Ball(self.ol, 255, (5, 10), 5, (2, -1), debug=debug))
        self.ball.append(Ball(self.ol, 128, (10, 5), 5, (1, -2), debug=debug))

        self.bg.draw()
        for i in range(len(self.ball)):
            self.ball[i].draw()
        self.ol.display()

    def disp_bg(self):
        self.ol.draw.rectangle([(0, 0), (self.x_max, self.y_max)],
                               outline=1, width=self.border_w, fill=0)

    def move(self):
        while True:
            for i in range(len(self.ball)):
                self.ball[i].move()
            time.sleep(0.1)

    def draw(self):
        self.bg.draw()
        for i in range(len(self.ball)):
            self.ball[i].draw()

    def main(self):
        disp_th = threading.Thread(target=self.move, daemon=True)
        disp_th.start()

        while True:
            #self.ball.move()

            self.draw()
                
            self.ol.display()
            time.sleep(0.01)
                
    def finish(self):
        self.logger.debug('')
        self.ol.cleanup()

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
        #obj = Sample(display, 1, 0x3C, debug=debug)
        obj = Sample(display, 0, 0, debug=debug)
        obj.main()
    finally:
        obj.finish()

if __name__ == '__main__':
    main()

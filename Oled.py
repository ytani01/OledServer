#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import time
import threading
import RPi.GPIO as GPIO
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.core import error
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
    '''
OLED

SPI pins

| SSD1331      |  0.95'  | 96x64    | 64K color   |
|-------------:|:-------:|:--------:|:------------|
| VCC(3.3v)    | VCC     | DC       | BCM 24      |
| BCM 10(MOSI) | D1(SDA) | GND      | GND         |
| BCM 9(MISO)  | -       | RST(RES) | BCM 25      |
| BCM 11(SCLK) | D0(SCL) | CS       | BCM 8 (CE0) |
    '''

    DEF_I2C_ADDR = 0x3C
    I2C_DEV = ['ssd1306', 'ssd1327']
    SPI_DEV = ['ssd1331']
    
    def __init__(self, dev, param1=-1, param2=-1, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('dev    = %s',   dev)
        self.logger.debug('param1 = %d',   param1)
        self.logger.debug('param2 = %d(0x%X)', param2, param2)
        self.debug = debug

        self.dev  = dev
        self.param1 = param1
        self.param2 = param2

        self.enable = False
        
        if param1 < 0:
            if dev in self.I2C_DEV:
                self.param1 = 1
            elif dev in self.SPI_DEV:
                self.param1 = 0
            else:
                logger.error('invalic device: %s', dev)
                raise RuntimeError('invalid device: %s' % dev)

        if param2 < 0:
            if dev in self.I2C_DEV:
                self.param2 = self.DEF_I2C_ADDR
            elif dev in self.SPI_DEV:
                self.param2 = 0
            else:
                logger.error('invalic device: %s', dev)
                raise RuntimeError('invalid device: %s' % dev)
                
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
        self.mode = ''
        if self.dev == 'ssd1306':
            if self.param2 == 0:
                self.param2 = self.I2C_ADDR
            self.serial = i2c(port=self.param1, address=self.param2)
            self.disp   = ssd1306(self.serial)
            self.mode   = '1'

        if self.dev == 'ssd1327':
            if self.param2 == 0:
                self.param2 = self.I2C_ADDR
            self.serial = i2c(port=self.param1, address=self.param2)
            self.disp   = ssd1327(self.serial)
            self.mode   = 'RGB'

        if self.dev == 'ssd1331':
            self.serial = spi(device=self.param1, port=self.param2)
            self.disp   = ssd1331(self.serial)
            self.mode   = 'RGB'
            
        if self.mode == '':
            self.logger.error('invalid device: %s', self.dev)
            raise RuntimeError('invalid device: %s' % self.dev)
        
        self.disp.persist = True

        self.image = Image.new(self.mode, self.disp.size)
        self.draw  = ImageDraw.Draw(self.image)

        #self.clear()
        
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

        self.disp.cleanup()
        self.logger.debug('done')

    def clear(self, display_now=False):
        self.logger.debug('display_now = %s', display_now)
        
        xy = [(0, 0), (self.disp.width - 1, self.disp.height - 1)]
        self.draw.rectangle(xy, outline=0, fill=0)

        if display_now:
            self.display()

    def display(self, img=None):
        self.logger.debug('')

        if img == None:
            img = self.image

        while True:
            try:
                self.disp.display(img)
                break
            except (OSError, error.DeviceNotFoundError) as e:
                self.logger.error('%s:%s', type(e), e)
                time.sleep(0.1)

    def loadImagefile(self, imgfile, display_now=False, clear_flag=False):
        self.logger.debug('imgfile = %s', imgfile)

        im = Image.open(imgfile)

        w = im.width
        h = im.height
        if w > self.disp.width or h > self.disp.height:
            a1 = w / self.disp.width
            a2 = h / self.disp.height

            if a1 > a2:
                w = self.disp.width
                h = int(h / a1)
            else:
                w = int(w / a2)
                h = self.disp.height
        self.logger.debug('(w, h) = (%d, %d)', w, h)

        x = int((self.disp.width - w) / 2)
        y = int((self.disp.height - h) / 2)
        self.logger.debug('(x, y) = (%d, %d)', x, y)
        
        if clear_flag:
            self.clear(display_now=False)
            
        im2 = im.resize((w, h), Image.BICUBIC)

        self.image.paste(im2, (x, y))
        if display_now:
            self.display()

##### sample application
class BG:
    def __init__(self, ol, color, w, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.debug = debug
        self.logger.debug('color = %s', color)
        self.logger.debug('w     = %d', w)

        self.ol    = ol
        self.color = color
        self.w     = w

        (self.x1, self.y1) = (0, 0)
        (self.x2, self.y2) = (self.ol.disp.width - 1, self.ol.disp.height - 1)

    def draw(self):
        xy = [(self.x1, self.y1), (self.x2, self.y2)]
        #self.ol.draw.rectangle(xy, outline=self.color, width=self.w, fill=0)
        self.ol.draw.rectangle(xy, outline=self.color, fill=0)
        
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
    def __init__(self, dev, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.debug = debug
        self.logger.debug('dev  = %s',   dev)

        self.dev  = dev

        self.ol = Oled(self.dev, debug=self.debug)

        self.col = {}
        self.col['bg'] = 255
        self.col['ball'] = [255, 128]
        if dev in Oled.SPI_DEV:
            self.col['bg'] = 0x00ff00 # 'green'
            self.col['ball'] = ['red', 'blue']
            
        self.bg   = BG(self.ol, self.col['bg'], 2, debug=debug)
        self.ball = []
        self.ball.append(Ball(self.ol, self.col['ball'][0],
                              (5, 10), 5, (2, -1),
                              debug=debug))
        self.ball.append(Ball(self.ol, self.col['ball'][1],
                              (10, 5), 5, (1, -2),
                              debug=debug))

        self.bg.draw()
        for i in range(len(self.ball)):
            self.ball[i].draw()
        self.ol.display()

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
            self.draw()
            self.ol.display()
            #time.sleep(0.01)
                
    def finish(self):
        self.logger.debug('')
        self.ol.cleanup()

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('dev', type=str, metavar='<ssd1306|ssd1327|ssd1331>', nargs=1)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(dev, debug):
    logger = init_logger('', debug)
    logger.debug('dev   = %s', dev)
    logger.debug('debug = %s', debug)

    obj = Sample(dev, debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.finish()

if __name__ == '__main__':
    main()

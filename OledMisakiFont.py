#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
#import textwrap
import mojimoji
import unicodedata
import time

from ipaddr import ipaddr

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

# $ wget http://www.geocities.jp/littlimi/arc/misaki/misaki_ttf_2015-04-10.zip
FONT_PATH = '/home/pi/font/misakifont/misaki_gothic.ttf'

class OledMisakiFont:
    def __init__(self, headerlines=0, footerlines=0, zenkaku=False, fontsize=8, rst=24):
        self.enable = True
        self.lines = {
            'header':	headerlines,
            'body':	0,
            'footer':	footerlines	}
        self.zenkaku_flag = zenkaku
        self.fontsize = fontsize
        self.rst = rst

        self.cur_part = 'body'
        self.char_width, self.char_height = self.fontsize, self.fontsize

        # initialize display
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=self.rst)
        #self.disp = Adafruit_SSD1306.SSD1306_96_16(rst=self.rst)
        try:
            self.disp.begin()
        except:
            self.enable = False
            return None
        self.disp.clear()
        self.disp.display()

        # load font
        self.font = ImageFont.truetype(FONT_PATH, self.fontsize, encoding='unic')
        (self.char_width, self.char_height) = self.font.getsize('８')
        self.char_height += 1
        
        # cols and rows
        self.cols = int(self.disp.width / self.char_width)
        self.rows = int(self.disp.height / self.char_height)

        self.lines['body'] = self.rows - self.lines['header'] - self.lines['footer']
        if self.lines['body'] < 0 or \
           self.lines['header'] + self.lines['footer'] > self.rows:
            self.enable = False
            return None
        logger.debug('lines = %s', self.lines)

        self.startline = {
            'header':	0,
            'body':	self.lines['header'],
            'footer':	self.lines['header'] + self.lines['body'] }
        logger.debug('startline = %s', self.startline)

        self.text = {}
        self.cur_row = {'header': 0, 'body': 0, 'footer': 0}
        for part in ['header', 'body', 'footer']:
            self.text[part] = [''] * self.lines[part]

        logger.debug('text = %s', self.text)
        logger.debug('cur_row = %s', self.cur_row)

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.image = Image.new('1', (self.disp.width, self.disp.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)
 

    def clear(self, part=''):
        if not self.enable:
            return

        if part == '':
            part = self.cur_part

        self.draw.rectangle((0,0,self.disp.width,self.disp.height), outline=0, fill=0)
        self.disp.image(self.image)
        self.disp.display()
        
        self.cur_row['body'] = 0
        for i in range(self.rows):
            self.text[i] = ''

    def set_zenkaku_flag(self, value):
        if not self.enable:
            return

        if value:
            self.zenkaku_flag = True
        else:
            self.zenkaku_flag = False

    def set_part(self, part):
        if not self.enable:
            return

        if part in self.lines.keys():
            self.cur_part = part
        
    def _draw_1line(self, col, row, text):
        x = col * self.char_width
        y = row * self.char_height
        logger.debug('(%d, %d)', x, y)
        self.draw.text((x,y), text, font=self.font, fill=255)

    def _draw_lines(self, part=''):
        if part == '':
            part = self.cur_part

        x1 = 0
        y1 = self.char_height * self.startline[part]
        x2 = self.disp.width - 1 
        y2 = self.char_height * self.lines[part] + y1 - 1
        self.draw.rectangle([(x1, y1), (x2, y2)], outline=0, fill=0)
        logger.debug('(%d,%d),(%d,%d)', x1, y1, x2, y2)
        
        row = self.startline[part]
        for t in self.text[part]:
            self._draw_1line(0, row, t)
            row += 1

    def _draw_alllines(self):
        self.draw.rectangle((0,0,self.disp.width,self.disp.height), outline=0, fill=0)

        row = 0
        for part in ['header', 'body', 'footer']:
            if self.lines[part] <= 0:
                continue
            for t in self.text[part]:
                self._draw_1line(0, row, t)
                row += 1

    def _print1line(self, text, part=''):
        if not self.enable:
            return

        logger.debug('part=%-6s text=\'%s\'', part, text)
        if part == '':
            part = self.cur_part
            
        self.text[part][self.cur_row[part]] = text
        #self._draw_alllines()
        self._draw_lines(part)

        self.cur_row[part] += 1
        if self.cur_row[part] > self.lines[part] - 1:
            self.cur_row[part] = self.lines[part] - 1
            self.text[part].pop(0)
            self.text[part].append('')

    # 長い行を折り返して、出力する
    def println(self, s, part=''):
        if not self.enable:
            return

        if part == '':
            part = self.cur_part

        if len(s) == 0:
            self._print1line('', part=part)
            return

        if self.zenkaku_flag:
            s = mojimoji.han_to_zen(s)

        line = ''
        prev_len = 0
        cur_len = 0
        for ch in s:
            prev_len = cur_len
            if unicodedata.east_asian_width(ch) in 'FWA':
                cur_len += 1
            else:
                cur_len += 0.5
                
            if cur_len <= self.cols:
                line += ch
            else:
                self._print1line(line, part=part)
                line = ch
                cur_len -= prev_len
        if cur_len > 0:
            self._print1line(line, part=part)

        # display OLED display
        self.disp.image(self.image)
        self.disp.display()
        
#####
def main():
    mf = OledMisakiFont(3,2)
    logger.info('font:   %d', mf.fontsize)
    logger.info('char:   %d x %d', mf.char_width, mf.char_height)
    logger.info('disp:   %d x %d', mf.cols, mf.rows)
    ip = ipaddr().ip_addr()
    logger.info('ipaddr: %s', ip)

    mf.set_zenkaku_flag(True)
    mf.set_part('header')
    mf.println(time.strftime('%Y/%m/%d(%a)'))
    mf.println(time.strftime('%H:%M:%S'))
    mf.println('----------------')
    mf.set_part('footer')
    mf.println('----------------')
    mf.println(ip, part='footer')
    mf.set_part('body')
    mf.set_zenkaku_flag(False)
    mf.println('ABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞ')
    mf.println('font: %d = %d x %d pixels' % (mf.fontsize,
                                              mf.char_width, mf.char_height))
    mf.println('%d cols x %d rows' % (mf.cols, mf.rows))

if __name__ == '__main__':
    main()

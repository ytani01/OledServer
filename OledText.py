#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
#import textwrap
import mojimoji
import unicodedata
import time
import click

from ipaddr import ipaddr

## logging
from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

# $ wget http://www.geocities.jp/littlimi/arc/misaki/misaki_ttf_2015-04-10.zip
FONT_DIR	= '/home/pi/font/misakifont'
FONT_NAME	= 'misaki_gothic.ttf'
FONT_PATH	= FONT_DIR + '/' + FONT_NAME

#
#
#
class OledText:
    def __init__(self, headerlines=0, footerlines=0, zenkaku=False, fontsize=8, rst=24):
        self.enable = True
        self.zenkaku_flag = zenkaku
        self.fontsize = fontsize
        self.rst = rst

        self.crlf = True

        # initialize display
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=self.rst)
        try:
            self.disp.begin()
        except:
            self.enable = False
            return None

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.image = Image.new('1', (self.disp.width, self.disp.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # clear display
        self.disp.clear()

        # load font
        self.font = ImageFont.truetype(FONT_PATH, self.fontsize, encoding='unic')
        (self.char_width, self.char_height) = self.font.getsize('８')
        self.char_height += 1

        
        # physical cols and rows
        self.disp_cols = int(self.disp.width  / self.char_width)
        self.disp_rows = int(self.disp.height / self.char_height)

        # setup header, footer and body
        self.cur_part = 'body'
        if not self.set_layout(headerlines, footerlines):
            self.enable = False
            return None

    # output physical display
    def _display(self):
        self.disp.image(self.image)
        self.disp.display()

    # clear display
    def clear(self, part='', display=True):
        if not self.enable:
            return

        if part == '':
            part = self.cur_part

        # clear text
        for i in range(self.rows[part]):
            self.text[part][i] = ''
        #self.cur_row[part] = 0

        # clear image
        x1, y1 = 0, self.char_height * self.start_row[part]
        x2, y2 = self.disp.width - 1, self.char_height * self.rows[part] + y1 - 1
        self.draw.rectangle([(x1, y1), (x2, y2)], outline=0, fill=0)
        logger.debug('clear(%d,%d),(%d,%d)', x1, y1, x2, y2)
        
        # display
        if display:
            self._display()

    # draw border
    def _draw_border(self, width=2, display=False):
        x1 = 0
        x2 = self.disp.width - 1
        if self.rows['header'] > 0:
            y1 = self.char_height * (self.rows['header'] + 0.5) - 1
            y2 = y1
            self.draw.line([(x1, y1), (x2, y2)], fill=255, width=width)

        if self.rows['footer'] > 0:
            y1 = self.disp.height - self.char_height * (self.rows['footer'] + 0.5) - 1
            y2 = y1
            self.draw.line([(x1, y1), (x2, y2)], fill=255, width=width)

        if display:
            self._display()

    # set header and footer
    def set_layout(self, headerlines=0, footerlines=0, display=True):
        if headerlines + footerlines + 2 > self.disp_rows:
            return False

        self.rows = {
            'header':	headerlines,
            'body':	self.disp_rows - headerlines - footerlines,
            'footer':	footerlines	}
        for part in ['header', 'footer']:
            if self.rows[part] > 0:
                self.rows['body'] -=  1
        logger.debug('rows = %s', self.rows)

        self.start_row = {
            'header':	0,
            'body':	self.rows['header'],
            'footer':	self.disp_rows - self.rows['footer'] }
        if self.rows['header'] > 0:
            self.start_row['body'] += 1
        logger.debug('start_row = %s', self.start_row)

        self.cur_row = {'header': 0, 'body': 0, 'footer': 0}
        logger.debug('cur_row = %s', self.cur_row)

        self.text = {}
        for part in ['header', 'body', 'footer']:
            self.text[part] = [''] * self.rows[part]
        logger.debug('text = %s', self.text)

        # display
        self._draw_border()
        for part in ['header', 'body', 'footer']:
            self.clear(part, display=False)

        if display:
            self._display()
            
        return True

    # selct current part
    def set_part(self, part, row=-1, zenkaku=None, crlf=None):
        if not self.enable:
            return

        if part in self.rows.keys():
            self.cur_part = part

        if row >= 0:
            self.set_row(row)

        if zenkaku != None:
            self.zenkaku(zenkaku)

        if crlf != None:
            self.set_crlf(crlf)
        
    # set part and row
    def set_row(self, row=255, part=''):
        if part == '':
            part = self.cur_part

        self.set_part(part)
        self.cur_row[part] = row
    
    # set zenkaku_flag
    def set_zenkaku(self, value, part=''):
        if not self.enable:
            return

        if part == '':
            part = self.cur_part

        if value:
            self.zenkaku_flag = True
        else:
            self.zenkaku_flag = False

    # 改行設定
    def set_crlf(self, crlf=None):
        if not self.enable:
            return
        if crlf == None:
            return

        self.crlf=crlf

    def _draw_1line(self, ph_row, text):
        x1, y1 = 0, ph_row * self.char_height
        self.draw.text((x1,y1), text, font=self.font, fill=255)
        logger.debug('draw.text(%d, %d)', x1, y1)

    def _clear_1line(self, ph_row):
        x1, y1 = 0, ph_row * self.char_height
        x2, y2 = self.disp.width - 1, y1 + self.char_height - 1
        self.draw.rectangle([(x1, y1), (x2, y2)], outline=0, fill=0)
        logger.debug('clear rectangle (%d,%d),(%d,%d)', x1, y1, x2, y2)
        
    def _draw_part(self, part=''):
        if part == '':
            part = self.cur_part

        # clear part area
        x1, y1 = 0, self.char_height * self.start_row[part]
        x2, y2 = self.disp.width - 1, y1 + self.char_height * self.rows[part] - 1
        self.draw.rectangle([(x1, y1), (x2, y2)], outline=0, fill=0)
        logger.debug('clear rectangle (%d,%d),(%d,%d)', x1, y1, x2, y2)

        # draw lines in current part
        ph_row = self.start_row[part]
        for t in self.text[part]:
            self._draw_1line(ph_row, t)
            ph_row += 1

    # 1行分出力し、crlfフラグに応じてスクロール処理も行う
    def _print_1line(self, text, part='', crlf=None):
        if not self.enable:
            return

        logger.debug('part=%-6s crlf=%s text=\'%s\'', part, crlf, text)
        if part == '':
            part = self.cur_part
            logger.debug('part=%-6s', part)
        if self.rows[part] < 1:
            return

        if crlf == None:
            crlf = self.crlf
            logger.debug('crlf=%s', crlf)

        # 事前に、必要に応じてスクロール処理
        if self.cur_row[part] > self.rows[part] - 1:
            if crlf:
                self.cur_row[part] = self.rows[part] - 1
                self.text[part].pop(0)
                self.text[part].append('')
            else:
                return

        # 1行分出力
        self.text[part][self.cur_row[part]] = text

        # draw part
        # (text[]上での操作を self.drawに反映)
        self._draw_part(part)

        # crlfフラグに応じて改行
        if crlf:
            self.cur_row[part] += 1

    # 長い行を折り返して出力する。必要に応じてスクロールも行う。
    def print(self, text, part='', crlf=None):
        if not self.enable:
            return

        logger.debug('part=%-6s crlf=%s text=\'%s\'', part, crlf, text)
        if part == '':
            part = self.cur_part
            logger.debug('part=%-6s', part)
        if crlf == None:
            crlf = self.crlf
            logger.debug('crlf=%s', crlf)

        if len(text) == 0:
            # clear one line
            self._print_1line('', part=part, crlf=crlf)
            return

        if self.zenkaku_flag:
            text = mojimoji.han_to_zen(text)

        # 長い行は折り返し
        # crlfがFalseの場合は、最初の1行だけ出力
        line = ''
        zenkaku_len = 0
        for ch in text:
            if unicodedata.east_asian_width(ch) in 'FWA':
                ch_len = 1
            else:
                ch_len = 0.5

            if zenkaku_len + ch_len > self.disp_cols:
                logger.debug('line=%s zenkaku_len=%.1f ch_len=%.1f',
                             line, zenkaku_len, ch_len)
                self._print_1line(line, part=part, crlf=crlf)

                line = ''
                zenkaku_len = 0
                
                if not crlf:
                    break
                
            line += ch
            zenkaku_len += ch_len

        if zenkaku_len > 0:
            self._print_1line(line, part=part, crlf=crlf)
        
        # display OLED
        self._display()
        
#####
@click.command(help='OLED Text library')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main():
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    ot = OledText(2,1)
    logger.info('font:   %d', ot.fontsize)
    logger.info('char:   %d x %d', ot.char_width, ot.char_height)
    logger.info('disp:   %d x %d', ot.disp_cols, ot.disp_rows)
    ip = ipaddr().ip_addr()
    logger.info('ipaddr: %s', ip)

    ot.set_part('header')
    ot.set_zenkaku(True)
    ot.print(time.strftime('%Y/%m/%d(%a)'))
    ot.print(time.strftime('%H:%M:%S'))
    time.sleep(2)
    ot.set_part('footer')
    ot.print(ip, part='footer')
    time.sleep(2)
    ot.set_part('body')
    ot.set_zenkaku(False)
    ot.print('ABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞABCあいうえお0123456789ガギグゲゴｶﾞｷﾞｸﾞｹﾞｺﾞ')
    ot.print('font: %d = %d x %d pixels' % (ot.fontsize,
                                              ot.char_width, ot.char_height))
    ot.print('%d cols x %d rows' % (ot.disp_cols, ot.disp_rows))
    time.sleep(2)
    ot.set_row(1, 'header')
    ot.set_zenkaku(True)
    ot.print(time.strftime('%H:%M:%S'))
    time.sleep(1)
    ot.set_row(1)
    ot.print(time.strftime('%H:%M:%S'))
    time.sleep(1)
    ot.set_row(1)
    ot.print(time.strftime('%H:%M:%S'))
    time.sleep(2)
    ot.clear('footer')
    time.sleep(2)
    ot.clear('body')

if __name__ == '__main__':
    main()

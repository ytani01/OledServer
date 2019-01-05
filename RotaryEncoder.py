#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#

import RPi.GPIO as GPIO
import time
import click

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

#
# Rotary Keyboard Class
#
class RotaryKey:
    CH_BS = '\b'
    CH_ENTER = '\n'
    CH_LIST = ' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' \
              + CH_ENTER + CH_BS
    
    def __init__(self, pin_rot, rk_rot_callback, pin_sw, rk_sw_callback):
        self.pin_rot		= pin_rot
        self.pin_sw		= pin_sw
        self.rk_rot_callback	= rk_rot_callback
        self.rk_sw_callback	= rk_sw_callback

        self.ch_list = __class__.CH_LIST
        self.idx = 0
        self.text = ''

        self.re = RotaryEncoder(pin_rot, self.rot_callback, pin_sw, self.sw_callback)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()
        logger.debug('%s, %s, %s', ex_type, ex_value, trace)        

    def open(self):
        self.re.open()
    
    def close(self):
        self.re.close()

    def rot_callback(self, v):
        self.idx = (self.idx + v) % len(self.ch_list)
        ch = self.get_ch()
        ch1 = ch
        if ch == __class__.CH_ENTER:
            ch1 = '<ENTER>'
        if ch == __class__.CH_BS:
            ch1 = '<BS>'
        logger.debug('\'%s[%s]\'', self.text, ch1)
        self.rk_rot_callback(self.text, ch)

    def get_ch(self):
        return self.ch_list[self.idx]

    def get_text(self):
        return self.text

    def sw_callback(self):
        ch = self.get_ch()
        if ch == __class__.CH_ENTER:
            logger.debug('\'%s\' -> callback', self.text)
            self.rk_sw_callback(self.text)
            self.text = ''
            self.idx = 0
            self.rk_rot_callback(self.text, ch)
            return

        if ch == __class__.CH_BS:
            if len(self.text) > 0:
                self.text = self.text[:-1]
                logger.debug('\'%s\'', self.text)
        else:
            self.text += ch
            logger.debug('\'%s\'', self.text)
        self.rk_rot_callback(self.text, ch)

#
# Rotary Encoder Class
#
class RotaryEncoder:
    ROT_BOUNCE_MSEC = 10
    SW_BOUNCE_MSEC = 300
    
    def __init__(self, pin_rot, rot_callback, pin_sw=0, sw_callback=None):
        self.pin_rot = pin_rot	# list [pin0, pin1]
        self.rot_callback = rot_callback
        self.pin_sw = pin_sw
        self.sw_callback = sw_callback

        self.rot_stat = [-1, -1]

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()
        logger.debug('%s, %s, %s', ex_type, ex_value, trace)

    def open(self):
        GPIO.setmode(GPIO.BCM)
        for p in self.pin_rot:
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(p, GPIO.BOTH,
                                  callback=self.pin_handler,
                                  bouncetime=__class__.ROT_BOUNCE_MSEC)
        if self.pin_sw != 0:
            GPIO.setup(self.pin_sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin_sw, GPIO.FALLING,
                                  callback=self.sw_handler,
                                  bouncetime=__class__.SW_BOUNCE_MSEC)
            
        self.rot_stat = self.getall()['rot']
        logger.debug('rot_stat=%s', self.rot_stat)
        self.v = 0

    def close(self):
        for p in self.pin_rot:
            GPIO.remove_event_detect(p)
        GPIO.remove_event_detect(self.pin_sw)
        GPIO.cleanup()

    def pin_handler(self, pin):
        #logger.debug('%d', pin)
        val = GPIO.input(pin)
        for i in [0, 1]:
            if pin == self.pin_rot[i]:
                chg_i = i
                
        if self.rot_stat[0] != self.rot_stat[1]:
            if chg_i == 0:
                self.v = -1
            else:
                self.v = 1
        '''
        else:
            if chg_i == 0:
                self.v = 1
            else:
                self.v = -1
        '''
        self.rot_stat[chg_i] = val
                
        #logger.debug('rot_stat=%s, v = %d', self.rot_stat, self.v)

        if self.rot_stat[0] == self.rot_stat[1]:
            self.rot_callback(self.v)

    def sw_handler(self, pin):
        if pin != self.pin_sw:
            return

        self.sw_callback()

    def getall(self):
        ret = {'rot': [GPIO.input(self.pin_rot[i]) for i in [0, 1]],
               'sw': GPIO.input(self.pin_sw)}
        #logger.debug('%s', ret)
        return ret

#####
InText = ''
Val = 0
EndFlag = False

def rk_rot_callback(text, ch):
    if ch == RotaryKey.CH_BS:
        ch = '[BS]'
    if ch == RotaryKey.CH_ENTER:
        ch = '[ENTER]'
    print('%s%s' % (text, ch))

def rk_sw_callback(text):
    global InText

    InText = text
    print('>>> %s <<<' % InText)

def rot_callback(v):
    global Val
    
    #logger.debug('=== %d ===', v)
    Val += v
    print('=== %d ===' % Val)

def sw_callback():
    global Val
    global EndFlag
    
    print('>>> %d <<<' % Val)

    if Val == 0:
        EndFlag = True
    
@click.command(help='Rotary Encoder Class')
@click.argument('pin1', type=int, default=27)
@click.argument('pin2', type=int, default=22)
@click.argument('pin_sw', type=int, default=23)
def main(pin1, pin2, pin_sw):
    global InText
    global Val
    global EndFlag
    
    logger.debug('%d %d %d', pin1, pin2, pin_sw)

    with RotaryEncoder([pin1, pin2], rot_callback, pin_sw, sw_callback) as re:
        while True:
            if EndFlag:
                break
            time.sleep(1)
            print('%s' % re.getall())

    with RotaryKey([pin1, pin2], rk_rot_callback, pin_sw, rk_sw_callback) as rk:
        while True:
            if InText == '0000':
                break
            time.sleep(0.1)

#####
if __name__ == '__main__':
    main()

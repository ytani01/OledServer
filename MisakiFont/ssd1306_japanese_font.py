# -*- coding: utf-8 -*-

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Raspberry Pi pin configuration
RST = 24

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()
 
# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
 
# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Misaki Font, awesome 8x8 pixel Japanese font, can be downloaded from the following URL.
# $ wget http://www.geocities.jp/littlimi/arc/misaki/misaki_ttf_2015-04-10.zip
font = ImageFont.truetype('/home/pi/font/misakifont/misaki_gothic.ttf', 8, encoding='unic')

# Un-comment out the following line if you want to use the default font instead of Misaki Font
# font = ImageFont.load_default()

# Write two lines of text.
x=0
y=0
for str in [ u'最近の研究から、地球上のカミナ', u'リ雲でも電子が高いエネルギーに', u'まで「加速」されている証拠が見', u'つかってきました。加速された電', u'子が大気分子と衝突することで生', u'じるガンマ線がカミナリ雲からビ', u'ーム状に放出されていることがわ', u'かったのです！  →   thdr.info' ]:
    draw.text((x,y), str, font=font, fill=255)
    y+=8

disp.image(image)
disp.display()

#
import pigpio
import _LCD_I2C
from PIL import Image
from PIL import ImageDraw
import time

###
SETCONTRAST = 0x81
DISPLAYALLON_RESUME = 0xA4
DISPLAYALLON = 0xA5
NORMALDISPLAY = 0xA6
INVERTDISPLAY = 0xA7
DISPLAYOFF = 0xAE
DISPLAYON = 0xAF
SETDISPLAYOFFSET = 0xD3
SETCOMPINS = 0xDA
SETVCOMDETECT = 0xDB
SETDISPLAYCLOCKDIV = 0xD5
SETPRECHARGE = 0xD9
SETMULTIPLEX = 0xA8
SETLOWCOLUMN = 0x00
SETHIGHCOLUMN = 0x10
SETSTARTLINE = 0x40
MEMORYMODE = 0x20
COLUMNADDR = 0x21
PAGEADDR = 0x22
COMSCANINC = 0xC0
COMSCANDEC = 0xC8
SEGREMAP = 0xA0
CHARGEPUMP = 0x8D
EXTERNALVCC = 0x1
SWITCHCAPVCC = 0x2

# Scrolling constants
ACTIVATE_SCROLL = 0x2F
DEACTIVATE_SCROLL = 0x2E
SET_VERTICAL_SCROLL_AREA = 0xA3
RIGHT_HORIZONTAL_SCROLL = 0x26
LEFT_HORIZONTAL_SCROLL = 0x27
VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL = 0x29
VERTICAL_AND_LEFT_HORIZONTAL_SCROLL = 0x2A


###
WIDTH      = 128
HEIGHT     = 64

COLOR_MODE = '1'
I2C_ADDR   = '0x3c'

class SSD1306(_LCD_I2C._LCD_I2C):
    def __init__(self, pi, i2c_bus, i2c_addr=I2C_ADDR):
        self.pi       = pi
        self.i2c_bus  = i2c_bus
        self.i2c_addr = i2c_addr

        self.width      = WIDTH
        self.height     = HEIGHT
        self.size       = (self.width, self.height)
        self.pages      = self.height//8
        self.mask       = [1 << (i // self.width) % 8 for i in range(self.width * self.height)]
        self.offsets    = [(self.width * (i // (self.width * 8))) for i in range(self.width * self.height)]
        self.color_mode = COLOR_MODE

        super().__init__(self.pi, self.color_mode, self.i2c_bus, self.i2c_addr)
    
    def reset(self):
        return

    def _init(self):
        self.command(DISPLAYOFF)
        self.command(SETDISPLAYCLOCKDIV)
        self.command(0x80)
        self.command(SETMULTIPLEX)
        self.command(0x3F)
        self.command(SETDISPLAYOFFSET)
        self.command(0x00)
        self.command(SETSTARTLINE | 0x00)
        self.command(CHARGEPUMP)
        self.command(0x14)
        self.command(MEMORYMODE)
        self.command(0x00)
        self.command(SEGREMAP | 0x01)
        self.command(COMSCANDEC)
        self.command(SETCOMPINS)
        self.command(0x12)
        self.command(SETCONTRAST)
        self.command(0xCF)
        self.command(SETPRECHARGE)
        self.command(0xF1)
        self.command(SETVCOMDETECT)
        self.command(0x40)
        self.command(DISPLAYALLON_RESUME)
        self.command(NORMALDISPLAY)

    def display(self, image=None):
        if image is None:
            image = self.buffer
            
        self.command(COLUMNADDR)
        self.command(0)
        self.command(self.width-1)
        self.command(PAGEADDR)
        self.command(0)
        self.command(self.pages-1)

        buf = bytearray(self.width * self.pages)
        idx = 0
        for pix in image.getdata():
            if pix > 0:
                buf[self.offsets[idx]] |= self.mask[idx]
            idx += 1

        reg = 0x40
        for i in range(0, len(buf), 16):
            self.pi.i2c_write_i2c_block_data(self.i2c, reg, buf[i:i+16])

    def clear(self):
        pass
    

import pigpio
from _LCD_SPI import _LCD_SPI
from PIL import Image
from PIL import ImageDraw
import time

SPI_CLOCK_HZ = 8000000 # 8 MHz

WIDTH    = 96
HEIGHT   = 64

NOP         = 0x00
SETCA       = 0x15 # Set Column Address
SETRA       = 0x75 # Set Row Address
SETCCA      = 0x81 # Set Contrast for Color A
SETCCB      = 0x82 # Set Contrast for Color B
SETCCC      = 0x83 # Set Contrast for Color C
MCCTL       = 0x87 # Master Current Control
SETSPSCA    = 0x8A # Set Second Pre-charge Speed for Color A
SETSPSCB    = 0x8B # Set Second Pre-charge Speed for Color B
SETSPSCC    = 0x8C # Set Second Pre-charge Speed for Color C
SETRDF      = 0xA0 # Set Remap & Data Format
SETDSL      = 0xA1 # Set Display Start Line
SETDO       = 0xA2 # Set Display Offset
SETNORMDISP = 0xA4 # Set Display Mode: Normal Display
SETEDISPON  = 0xA5 # Set Display Mode: Set Entire Display ON
SETEDISPOFF = 0xA6 # Set Display Mode: Set Entire Display OFF
SETINVDISP  = 0xA7 # Set Display Mode: Inverse Display
SETMR       = 0xA8 # Set Multiplex Ratio
DIMMODSET   = 0xAB # Dim mode setting
SETMCONF    = 0xAD # Set Master Configuration
DMDISPON    = 0xAC # Dim Mode Display ON
DISPOFF     = 0xAE # Display OFF
NBDISPON    = 0xAF # Normal Brightness Display ON
PWSAVE      = 0xB0 # Power Save Mode
PPADJ       = 0xB1 # Phase 1 and 2 Period Adjustment
SETDISPCLK  = 0xB3 # Set Display Clock Divide Ratio/ Oscillator Frequency
SETGSTBL    = 0xB8 # Set Gray Scale Table
ELGSTBL     = 0xB9 # Enable Linear Gray Scale Table
SETPCV      = 0xBB # Set Pre-charge voltage
NOP_BC      = 0xBC # NOP
NOP_BD      = 0xBD # NOP
SETVCOMHV   = 0xBE # Set V(COMH) Voltage
NOP_E3      = 0xE3 # NOP
SETCMDLCK   = 0xFD # Set Command Lock

# Colours for convenience
BLACK       = 0x0000 # 0b 00000 000000 00000
BLUE        = 0x001F # 0b 00000 000000 11111
GREEN       = 0x07E0 # 0b 00000 111111 00000
RED         = 0xF800 # 0b 11111 000000 00000
CYAN        = 0x07FF # 0b 00000 111111 11111
MAGENTA     = 0xF81F # 0b 11111 000000 11111
YELLOW      = 0xFFE0 # 0b 11111 111111 00000
WHITE       = 0xFFFF # 0b 11111 111111 11111


class SSD1331(_LCD_SPI):
    """Representation of an ST7789 IPS LCD."""

    def __init__(self, pi, mode=3, rst=25, dc=24, led=0):
        self.pi = pi
        self.mode = mode
        self.rst = rst
        self.dc  = dc
        self.led = led

        self.width = WIDTH
        self.height = HEIGHT
        self.size = (self.width, self.height)
        
        self.pi.set_mode(self.dc, pigpio.OUTPUT)

        super().__init__(self.pi, 0, SPI_CLOCK_HZ, self.mode, self.rst, self.dc)

    def reset(self):
        if self.rst is not None:
            self.pi.write(self.rst, 1)
            time.sleep(0.100)
            self.pi.write(self.rst, 0)
            time.sleep(0.100)
            self.pi.write(self.rst, 1)
            time.sleep(0.100)

    def _init(self):
        time.sleep(0.010)
        self.command(0xAE)  # Display Off
        self.command([0xA0, 0x72])  # Seg remoap
        self.command([0xA1, 0x00])  #  Set Display start line
        self.command([0xA2, 0x00])  # Set display Offset
        self.command(0xA4)  # Normal display
        self.command([0xA8, 0x3F])  # Set multiplex
        self.command([0xAD, 0x8E])  # Master configure
        self.command([0xB0, 0x0B])  # Power save mode
        self.command([0xB1, 0x74])  # Phase 12 period
        self.command([0xB3, 0xD0])  # Clock divider
        self.command([0x8A, 0x80])  # Set precharge speed A
        self.command([0x8B, 0x80])  # Set precharge speed B
        self.command([0x8C, 0x80])  # Set precharge speed C
        self.command([0xBB, 0x3E])  # Set pre-charge voltage
        self.command([0xBE, 0x3E])  # Set voltage
        self.command([0x87, 0x0F])  # Master current control
        time.sleep(0.100) # 100 ms

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.command([0x15, x0, x1])       # Column addr set
        self.command([0x75, y0, y1])       # Row addr set

    def set_contrast(self, level):
        self.command([0x81, level])
        self.command([0x82, level])
        self.command([0x83, level])

    def display(self, image=None, x0=0, y0=0, x1=None, y1=None):
        if image is None:
            image = self.buffer

        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.set_window(x0, y0, x1, y1)

        pixelbytes = list(self.image_to_data(image))
        self.data(pixelbytes)

    def clear(self, color=(0,0,0)):
        width, height = self.buffer.size
        self.buffer.putdata([color]*(width*height))

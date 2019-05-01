# ST7789 IPS LCD (240x240) driver
import pigpio
from LCD_SPI import LCD_SPI
from PIL import Image
from PIL import ImageDraw
import time

SPI_CLOCK_HZ = 40000000 # 40 MHz

# Constants for interacting with display registers.
WIDTH    = 240
HEIGHT   = 240

NOP         = 0x00
SWRESET     = 0x01
RDDID       = 0x04
RDDST       = 0x09
RDDPM       = 0x0A
RDDMADCTL   = 0x0B
RDDCOLMOD   = 0x0C
RDDIM       = 0x0D
RDDSM       = 0x0E
RDDSDR      = 0x0F

SLPIN       = 0x10
SLPOUT      = 0x11
PTLON       = 0x12
NORON       = 0x13

INVOFF      = 0x20
INVON       = 0x21
GAMSET      = 0x26
DISPOFF     = 0x28
DISPON      = 0x29
CASET       = 0x2A
RASET       = 0x2B
RAMWR       = 0x2C
RAMRD       = 0x2E

PTLAR       = 0x30
VSCRDEF     = 0x33
TEOFF       = 0x34
TEON        = 0x35
MADCTL      = 0x36
VSCRSADD    = 0x37
IDMOFF      = 0x38
IDMON       = 0x39
COLMOD      = 0x3A
RAMWRC      = 0x3C
RAMRDC      = 0x3E

TESCAN      = 0x44
RDTESCAN    = 0x45

WRDISBV     = 0x51
RDDISBV     = 0x52
WRCTRLD     = 0x53
RDCTRLD     = 0x54
WRCACE      = 0x55
RDCABC      = 0x56
WRCABCMB    = 0x5E
RDCABCMB    = 0x5F

RDABCSDR    = 0x68

RDID1       = 0xDA
RDID2       = 0xDB
RDID3       = 0xDC

RAMCTRL     = 0xB0
RGBCTRL     = 0xB1
PORCTRL     = 0xB2
FRCTRL1     = 0xB3

GCTRL       = 0xB7
DGMEN       = 0xBA
VCOMS       = 0xBB

LCMCTRL     = 0xC0
IDSET       = 0xC1
VDVVRHEN    = 0xC2

VRHS        = 0xC3
VDVSET      = 0xC4
VCMOFSET    = 0xC5
FRCTR2      = 0xC6
CABCCTRL    = 0xC7
REGSEL1     = 0xC8
REGSEL2     = 0xCA
PWMFRSEL    = 0xCC

PWCTRL1     = 0xD0
VAPVANEN    = 0xD2
CMD2EN      = 0xDF5A6902
PVGAMCTRL   = 0xE0
NVGAMCTRL   = 0xE1
DGMLUTR     = 0xE2
DGMLUTB     = 0xE3
GATECTRL    = 0xE4
PWCTRL2     = 0xE8
EQCTRL      = 0xE9
PROMCTRL    = 0xEC
PROMEN      = 0xFA
NVMSET      = 0xFC
PROMACT     = 0xFE

# Colours for convenience
BLACK       = 0x0000 # 0b 00000 000000 00000
BLUE        = 0x001F # 0b 00000 000000 11111
GREEN       = 0x07E0 # 0b 00000 111111 00000
RED         = 0xF800 # 0b 11111 000000 00000
CYAN        = 0x07FF # 0b 00000 111111 11111
MAGENTA     = 0xF81F # 0b 11111 000000 11111
YELLOW      = 0xFFE0 # 0b 11111 111111 00000
WHITE       = 0xFFFF # 0b 11111 111111 11111


class ST7789(LCD_SPI):
    """Representation of an ST7789 IPS LCD."""

    def __init__(self, pi, mode=3, rst=25, dc=24, led=8):
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
        """Reset the display, if reset pin is connected."""
        if self.rst is not None:
            self.pi.write(self.rst, 1)
            time.sleep(0.100)
            self.pi.write(self.rst, 0)
            time.sleep(0.100)
            self.pi.write(self.rst, 1)
            time.sleep(0.100)

    def _init(self):
        # Initialize the display.  Broken out as a separate function so it can
        # be overridden by other displays in the future.

        time.sleep(0.010)
        self.command(SLPOUT)
        time.sleep(0.150)

        self.command(MADCTL)
        self.data(0x00)

        self.command(COLMOD)
        self.data(0x05)

        self.command(PORCTRL)
        self.data(0x0C)
        self.data(0x0C)

        self.command(GCTRL)
        self.data(0x35)

        self.command(VCOMS)
        self.data(0x1A)

        self.command(LCMCTRL)
        self.data(0x2C)

        self.command(VDVVRHEN)
        self.data(0x01)

        self.command(VRHS)
        self.data(0x0B)

        self.command(VDVSET)
        self.data(0x20)

        self.command(FRCTR2)
        self.data(0x0F)

        self.command(PWCTRL1)
        self.data(0xA4)
        self.data(0xA1)

        self.command(INVON)

        self.command(PVGAMCTRL)
        self.data(0x00)
        self.data(0x19)
        self.data(0x1E)
        self.data(0x0A)
        self.data(0x09)
        self.data(0x15)
        self.data(0x3D)
        self.data(0x44)
        self.data(0x51)
        self.data(0x12)
        self.data(0x03)
        self.data(0x00)
        self.data(0x3F)
        self.data(0x3F)

        self.command(NVGAMCTRL)
        self.data(0x00)
        self.data(0x18)
        self.data(0x1E)
        self.data(0x0A)
        self.data(0x09)
        self.data(0x25)
        self.data(0x3F)
        self.data(0x43)
        self.data(0x52)
        self.data(0x33)
        self.data(0x03)
        self.data(0x00)
        self.data(0x3F)
        self.data(0x3F)
        self.command(DISPON)

        time.sleep(0.100) # 100 ms

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        """Set the pixel address window for proceeding drawing commands. x0 and
        x1 should define the minimum and maximum x pixel bounds.  y0 and y1
        should define the minimum and maximum y pixel bound.  If no parameters
        are specified the default will be to update the entire display from 0,0
        to width-1,height-1.
        """
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.command(CASET)       # Column addr set
        self.data(x0 >> 8)
        self.data(x0)                    # XSTART
        self.data(x1 >> 8)
        self.data(x1)                    # XEND
        self.command(RASET)       # Row addr set
        self.data(y0 >> 8)
        self.data(y0)                    # YSTART
        self.data(y1 >> 8)
        self.data(y1)                    # YEND
        self.command(RAMWR)       # write to RAM

    #def display(self, image=None):
    def display(self, image=None, x0=0, y0=0, x1=None, y1=None):
        """Write the display buffer or provided image to the hardware.  If no
        image parameter is provided the display buffer will be written to the
        hardware.  If an image is provided, it should be RGB format and the
        same dimensions as the display hardware.
        """
        # By default write the internal buffer to the display.
        if image is None:
            image = self.buffer

        # Set address bounds to entire display.
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.set_window(x0, y0, x1, y1)
        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        pixelbytes = list(self.image_to_data(image))
        # Write data to hardware.
        self.data(pixelbytes)

    def clear(self, color=(0,0,0)):
        """Clear the image buffer to the specified RGB color (default black)."""
        width, height = self.buffer.size
        self.buffer.putdata([color]*(width*height))

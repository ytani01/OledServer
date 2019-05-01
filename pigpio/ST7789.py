# ST7789 IPS LCD (240x240) driver
import pigpio
import _LCD_SPI
from PIL import Image
from PIL import ImageDraw
import time

SPI_CLOCK_HZ = 40000000 # 40 MHz

# Constants for interacting with display registers.
WIDTH    = 240
HEIGHT   = 240

NOP         = 0x00
SWRESET     = 0x01 # Sofware Reset
RDDID       = 0x04 # Read Display ID
RDDST       = 0x09 # Read Display Status
RDDPM       = 0x0A # Read Display Power Mode
RDDMADCTL   = 0x0B # Read Display MADCTL
RDDCOLMOD   = 0x0C # Read Display Pixel Format
RDDIM       = 0x0D # Read Display Image Mode
RDDSM       = 0x0E # Read Display Signal Mode
RDDSDR      = 0x0F # Read Display Self-Diagnostic Result

SLPIN       = 0x10 # Sleep in
SLPOUT      = 0x11 # Sleep Out
PTLON       = 0x12 # Partial Display Mode On
NORON       = 0x13 # Normal Display Mode On

INVOFF      = 0x20 # Display Inversion Off
INVON       = 0x21 # Display Inversion On
GAMSET      = 0x26 # Gamma Set
DISPOFF     = 0x28 # Display Off
DISPON      = 0x29 # Display On
CASET       = 0x2A # Column Address Set
RASET       = 0x2B # Row Address Set
RAMWR       = 0x2C # Memory Write
RAMRD       = 0x2E # Memory Read

PTLAR       = 0x30 # Partial Area
VSCRDEF     = 0x33 # Vertical Scrolling Definition
TEOFF       = 0x34 # Tearing Effect Line OFF
TEON        = 0x35 # Tearing Effect Line ON
MADCTL      = 0x36 # Memory Data Access Control
VSCRSADD    = 0x37 # Vertical Scroll Start Address of RAM
IDMOFF      = 0x38 # Idle Mode Off
IDMON       = 0x39 # Idle Mode On
COLMOD      = 0x3A # Interface Pixel Format
RAMWRC      = 0x3C # Write Memory Continue
RAMRDC      = 0x3E # Read Memory Continue

TESCAN      = 0x44 # Set Tear Scanline
GSCAN       = 0x45 # Get Scanline

WRDISBV     = 0x51 # Write Display Brightness
RDDISBV     = 0x52 # Read Display Brightness Value
WRCTRLD     = 0x53 # Write CTRL Display
RDCTRLD     = 0x54 # Read CTRL Display
WRCACE      = 0x55 # Write Content Adaptive Brightness Control and Color Enhancement
RDCABC      = 0x56 # Read Content Adaptive Brightness Control
WRCABCMB    = 0x5E # Write CABC Minimum Brightness
RDCABCMB    = 0x5F # Read CABC Minimum Brightness

RDABCSDR    = 0x68 # Read Automatic Brightness Control Self-Diagnostic Result

RDID1       = 0xDA # Read ID1
RDID2       = 0xDB # Read ID2
RDID3       = 0xDC # Read ID3

RAMCTRL     = 0xB0 # RAM Contrl
RGBCTRL     = 0xB1 # RGB Interface Control
PORCTRL     = 0xB2 # Porch Setting
FRCTRL1     = 0xB3 # Frame Rate Control 1 (In partial mode/idle colors)
PARCTL      = 0xB5 # Partial Control
GCTRL       = 0xB7 # Gate Control
GTADJ       = 0xB8 # Gate On Timing Adjustment
DGMEN       = 0xBA # Digital Gamma Enable
VCOMS       = 0xBB # VCOM Setting
POWSAVE     = 0xBC # Power Saving Mode
DLPOFFSAVE  = 0xBD # Display off power save

LCMCTRL     = 0xC0 # LCM Control
IDSET       = 0xC1 # ID Code Setting
VDVVRHEN    = 0xC2 # VDV and VRH Command Enable

VRHS        = 0xC3 # VRH Set
VDVSET      = 0xC4 # VDV Set
VCMOFSET    = 0xC5 # VCOM Offset Set
FRCTR2      = 0xC6 # Frame Rate Control in Normal Mode
CABCCTRL    = 0xC7 # CABC Control
REGSEL1     = 0xC8 # Register Value Selection 1
REGSEL2     = 0xCA # Register Value Selection 2
PWMFRSEL    = 0xCC # PWM Frequency Selection

PWCTRL1     = 0xD0 # Power Control 1
VAPVANEN    = 0xD2 # Enable VAP/VAN signal output
CMD2EN      = 0xDF # Command 2 Enable
PVGAMCTRL   = 0xE0 # Positive Voltage Gamma Control
NVGAMCTRL   = 0xE1 # Negative Voltage Gamma Control
DGMLUTR     = 0xE2 # Digital Gamma Look-up Table for Red
DGMLUTB     = 0xE3 # Digital Gamma Look-up Table for Blue
GATECTRL    = 0xE4 # Gate Control
SPI2EN      = 0xE7 # SPI2 Enable
PWCTRL2     = 0xE8 # Power Control 2
EQCTRL      = 0xE9 # Equalize time control
PROMCTRL    = 0xEC # Program Mode Control
PROMEN      = 0xFA # Program Mode Enable
NVMSET      = 0xFC # NVM Setting
PROMACT     = 0xFE # Program action

# Colours for convenience
BLACK       = 0x0000 # 0b 00000 000000 00000
BLUE        = 0x001F # 0b 00000 000000 11111
GREEN       = 0x07E0 # 0b 00000 111111 00000
RED         = 0xF800 # 0b 11111 000000 00000
CYAN        = 0x07FF # 0b 00000 111111 11111
MAGENTA     = 0xF81F # 0b 11111 000000 11111
YELLOW      = 0xFFE0 # 0b 11111 111111 00000
WHITE       = 0xFFFF # 0b 11111 111111 11111

COLOR_MODE = 'RGB'

class ST7789(_LCD_SPI._LCD_SPI):

    def __init__(self, pi, spi_mode=3, spi_rst=25, spi_dc=24, led=8):
        self.pi       = pi
        self.spi_mode = spi_mode
        self.spi_rst  = spi_rst
        self.spi_dc   = spi_dc
        self.led      = led

        self.width      = WIDTH
        self.height     = HEIGHT
        self.size       = (self.width, self.height)
        self.color_mode = COLOR_MODE

        self.pi.set_mode(self.spi_dc, pigpio.OUTPUT)

        super().__init__(self.pi, self.color_mode,
                         0, SPI_CLOCK_HZ, self.spi_mode,
                         self.spi_rst, self.spi_dc)

    def reset(self):
        if self.spi_rst is not None:
            self.pi.write(self.spi_rst, 1)
            time.sleep(0.100)
            self.pi.write(self.spi_rst, 0)
            time.sleep(0.100)
            self.pi.write(self.spi_rst, 1)
            time.sleep(0.100)

    def _init(self):
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

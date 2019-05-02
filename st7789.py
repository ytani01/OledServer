#
from luma.core.device import device
from luma.oled.device.color import color_device
import luma.core.error
import luma.core.framebuffer
import luma.oled.const
import time

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

class st7789(color_device):
    def __init__(self, serial_interface=None, width=240, height=240, rotate=0,
                 framebuffer="diff_to_previous", **kwargs):
        super(st7789, self).__init__(serial_interface, width, height, rotate,
                                     framebuffer, **kwargs)

    def _supported_dimensions(self):
        return [(240, 240)]

    def _init_sequence(self):
        time.sleep(0.150)
        self.command(SLPOUT)
        time.sleep(0.150)

        self.command(MADCTL, 0x00)
        self.command(COLMOD, 0x05)
        self.command(PORCTRL, 0x0C, 0x0C)
        self.command(GCTRL, 0x35)
        self.command(VCOMS, 0x1A)
        self.command(LCMCTRL, 0x2C)
        self.command(VDVVRHEN, 0x01)
        self.command(VRHS, 0x0B)
        self.command(VDVSET, 0x20)
        self.command(FRCTR2, 0x0F)
        self.command(PWCTRL1, 0xA4, 0xA1)
        self.command(INVON)
        self.command(PVGAMCTRL, 0x00, 0x19, 0x1E,0x0A, 0x09, 0x15, 0x3D, 0x44,
                     0x51, 0x12, 0x03, 0x00, 0x3F, 0x3F)

        self.command(NVGAMCTRL, 0x00, 0x18, 0x1E, 0x0A, 0x09, 0x25, 0x3F, 0x43,
                     0x52, 0x33, 0x03, 0x00, 0x3F, 0x3F)
        self.command(DISPON)

        time.sleep(0.100) # 100 ms

    def _set_position(self, top, right, bottom, left):
        self.command(CASET, 0, left, 0, right - 1)
        self.command(RASET, 0, top,  0, bottom - 1)
        self.command(RAMWR)

    def contrast(self, level):
        assert(0 <= level <= 255)
        return
    '''
        self.command(0x81, level,
                     0x82, level,
                     0x83, level)
    '''

#
import pigpio
import _LCD

MODE_CMD  = 0x00
MODE_DATA = 0x40

class _LCD_I2C(_LCD._LCD):
    def __init__(self, pi, color_mode, i2c_bus, i2c_addr):
        self.pi         = pi
        self.color_mode = color_mode
        self.i2c_bus    = i2c_bus
        self.i2c_addr   = i2c_addr

        self.i2c = self.pi.i2c_open(self.i2c_bus, self.i2c_addr)

        super().__init__(self.pi, self.color_mode)

    def command(self, *val):
        self.pi.i2c_write_i2c_block_data(self.i2c, MODE_CMD, list(val))

    def data(self, *val):
        self.pi.i2c_write_i2c_block_data(self.i2c, MODE_DATA, list(val))

    def cleanup(self):
        print('%s.cleanup()' % __class__.__name__)
        super().cleanup()
        self.pi.i2c_close(self.i2c)

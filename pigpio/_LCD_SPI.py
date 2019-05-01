#
import pigpio
import _LCD
import numbers

class _LCD_SPI(_LCD._LCD):
    def __init__(self, pi, color_mode,
                 spi_ch, spi_baud, spi_flags, spi_rst=25, spi_dc=24):
        self.pi         = pi
        self.color_mode = color_mode
        self.spi_ch     = spi_ch
        self.spi_baud   = spi_baud
        self.spi_flags  = spi_flags
        self.spi_rst    = spi_rst
        self.spi_dc     = spi_dc
        
        self.spi = self.pi.spi_open(self.spi_ch, self.spi_baud, self.spi_flags)

        super().__init__(self.pi, self.color_mode)

    def send(self, data, is_data=True, chunk_size=4096):
        # Set DC low for command, high for data.
        self.pi.write(self.spi_dc, is_data)
        # Convert scalar argument to list so either can be passed as parameter.
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]
        # Write data a chunk at a time.
        for start in range(0, len(data), chunk_size):
            end = min(start+chunk_size, len(data))
            self.pi.spi_write(self.spi, data[start:end])

    def command(self, data):
        """Write a byte or array of bytes to the display as command data."""
        self.send(data, False)

    def data(self, data):
        self.send(data, True)

    def cleanup(self):
        print('%s.cleanup()' % __class__.__name__)
        super().cleanup()
        self.pi.spi_close(self.spi)

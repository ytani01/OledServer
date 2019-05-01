#
import pigpio
from LCD import LCD
import numbers

class LCD_SPI(LCD):
    def __init__(self, pi, ch, baud, flags, rst=25, dc=24):
        self.pi    = pi
        self.ch    = ch
        self.baud  = baud
        self.flags = flags
        self.rst   = rst
        self.dc    = dc
        
        self.spi = pi.spi_open(self.ch, self.baud, self.flags)
        super().__init__(self.pi)

    def send(self, data, is_data=True, chunk_size=4096):
        """Write a byte or array of bytes to the display. Is_data parameter
        controls if byte should be interpreted as display data (True) or command
        data (False).  Chunk_size is an optional size of bytes to write in a
        single SPI transaction, with a default of 4096.
        """
        # Set DC low for command, high for data.
        self.pi.write(self.dc, is_data)
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
        """Write a byte or array of bytes to the display as display data."""
        self.send(data, True)

    def cleanup(self):
        print('%s.cleanup()' % __class__.__name__)
        self.pi.spi_close(self.spi)
        super().cleanup()

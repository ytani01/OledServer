# OLED Server and Library
----

* Oled(dev='ssd1331', param1=-1, param2=-1, debug=False)

* OledText(dev='ssd1306, headerlines=0, footerlines=0)

* OledServer(device='ssd1306', header=0, footer=0, port=DEF_PORT, handler=OledHandler, worker=OledWorker, debug=False)

* OledClient(host='localhost', port=DEF_PORT)

## Install

TBD

## SPI pins

| SSD1331      |  0.95'  | 96x64    | 64K color   |
|-------------:|:-------:|:--------:|:------------|
| VCC(3.3v)    | VCC     | DC       | BCM 24      |
| BCM 10(MOSI) | D1(SDA) | GND      | GND         |
| BCM 9(MISO)  | -       | RST(RES) | BCM 25      |
| BCM 11(SCLK) | D0(SCL) | CS       | BCM 8 (CE0) |

ST7789: LED=BCM8

## Reference

* Luma.OLED
https://luma-oled.readthedocs.io/
* Luma.OLED github
https://github.com/rm-hull/luma.oled/
* I2C vs. SPI
https://luma-oled.readthedocs.io/en/latest/hardware.html#i2c-vs-spi

* Python_ST7789
https://github.com/solinnovay/Python_ST7789

# OLED: 美咲フォント

## パーツ
* [0.96インチ 128x64ドット 有機ELディスプレイ(OLED) I2C](http://akizukidenshi.com/catalog/g/gP-12031/)

## 参考

* [Raspberry PiでI2C接続の128×64 OLEDに日本語を表示(美咲フォント)](http://ytkyk.info/blog/2016/06/19/raspberry-pi%E3%81%A7128x64%E3%81%AEoled%E3%81%AB%E6%97%A5%E6%9C%AC%E8%AA%9E%E3%82%92%E8%A1%A8%E7%A4%BA%E7%BE%8E%E5%92%B2%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88/)

## How to use

* Install

```bash
git clone https://github.com/ytani01/OLED.git
cd ~/OLED/SSD1306/MisakiFont
./install.sh
crontab -e  # see crontab.sample
```

* run demo

```bash
MisakiFont.py
```

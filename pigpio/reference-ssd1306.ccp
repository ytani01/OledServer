write(0b10000000); //control byte, Co bit = 1, D/C# = 0 (command)
write(0xAE); //display off

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0xA8); //Set Multiplex Ratio  0xA8, 0x3F
write(0b00111111); //64MUX

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0xD3); //Set Display Offset 0xD3, 0x00
write(0x00);

write(0b10000000); //control byte, Co bit = 1, D/C# = 0 (command)
write(0x40); //Set Display Start Line 0x40

write(0b10000000); //control byte, Co bit = 1, D/C# = 0 (command)
write(0xA0); //Set Segment re-map 0xA0/0xA1

write(0b10000000); //control byte, Co bit = 1, D/C# = 0 (command)
write(0xC0); //Set COM Output Scan Direction 0xC0,/0xC8

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0xDA); //Set COM Pins hardware configuration 0xDA, 0x02
write(0b00010010);

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0x81); //Set Contrast Control 0x81, default=0x7F
write(255); //0-255

write(0b10000000); //control byte, Co bit = 1, D/C# = 0 (command)
write(0xA4); //Disable Entire Display On

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0xA6); //Set Normal Display 0xA6, Inverse display 0xA7

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0xD5); //Set Display Clock Divide Ratio/Oscillator Frequency 0xD5, 0x80
write(0b10000000);

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0x20); //Set Memory Addressing Mode
write(0x10); //Page addressing mode

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0x22); //Set Page Address
write(0); //Start page set
write(7); //End page set

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0x21); //set Column Address
write(0); //Column Start Address
write(127); //Column Stop Address

write(0b00000000); //control byte, Co bit = 0, D/C# = 0 (command)
write(0x8D); //Set Enable charge pump regulator 0x8D, 0x14
write(0x14);

write(0b10000000); //control byte, Co bit = 1, D/C# = 0 (command)
write(0xAF); //Display On 0xAF

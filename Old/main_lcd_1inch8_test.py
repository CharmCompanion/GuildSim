from machine import Pin, PWM
from st7735_1inch8 import LCD_1inch8
from lcd_color_profile import map_rgb

# Backlight
bl = PWM(Pin(13))
bl.freq(1000)
bl.duty_u16(42000)

lcd = LCD_1inch8()

# Warm high-contrast palette preview (calibrated MODE 1).
black = map_rgb(0, 0, 0)
white = map_rgb(255, 255, 255)
brown = map_rgb(95, 55, 28)
tan = map_rgb(196, 160, 120)
gold = map_rgb(245, 195, 35)

lcd.fill(black)
lcd.text("Guildmaster", 18, 8, white)
lcd.text("Open VPet", 34, 24, gold)
lcd.rect(8, 40, 144, 70, gold)
lcd.text("STATUS: ONLINE", 16, 52, white)
lcd.text("BROWN  TAN  GOLD", 12, 68, white)
lcd.fill_rect(8, 92, 44, 24, brown)
lcd.fill_rect(56, 92, 44, 24, tan)
lcd.fill_rect(104, 92, 44, 24, gold)
lcd.show()

print("LCD 1.8 test frame rendered")

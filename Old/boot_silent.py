# Boot-time display quieting for Waveshare ST7735 on Pico.
# Goal: suppress power-on snow by keeping panel in reset and backlight off
# until main.py initializes and draws first frame.

from machine import Pin, PWM

# Hold panel reset low during early boot.
rst = Pin(12, Pin.OUT)
rst.value(0)

# Keep chip-select inactive.
cs = Pin(9, Pin.OUT)
cs.value(1)

# Backlight off during boot phase.
bl = PWM(Pin(13))
bl.freq(1000)
bl.duty_u16(0)

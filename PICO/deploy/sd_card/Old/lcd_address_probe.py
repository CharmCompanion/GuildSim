from machine import Pin, PWM
import time
import lcd


def draw_probe(display):
    black = 0x0000
    white = 0xFFFF
    red = 0xF800
    green = 0x07E0
    blue = 0x001F

    display.fill(black)

    # Border
    display.rect(0, 0, display.width, display.height, white)

    # Horizontal and vertical guide lines every 16 px.
    for x in range(0, display.width, 16):
        display.vline(x, 0, display.height, blue)
    for y in range(0, display.height, 16):
        display.hline(0, y, display.width, green)

    # Corner markers to detect wrap/stride errors quickly.
    display.fill_rect(0, 0, 10, 10, red)
    display.fill_rect(display.width - 10, 0, 10, 10, green)
    display.fill_rect(0, display.height - 10, 10, 10, blue)
    display.fill_rect(display.width - 10, display.height - 10, 10, 10, white)

    display.text("X=160 Y=128", 18, 8, white)
    display.text("Grid 16px", 18, 24, white)
    display.show()


if __name__ == "__main__":
    bl = PWM(Pin(13))
    bl.freq(1000)
    bl.duty_u16(52000)

    d = lcd.LCD_1inch8()
    draw_probe(d)
    print("LCD address probe rendered")
    time.sleep(0.5)

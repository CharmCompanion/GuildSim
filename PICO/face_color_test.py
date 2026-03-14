from machine import Pin, PWM
import time
import lcd


def draw_color_bars(d):
	bars = [
		(0, 0xF800, "R"),
		(1, 0x07E0, "G"),
		(2, 0x001F, "B"),
		(3, 0xFFE0, "Y"),
		(4, 0xF81F, "M"),
		(5, 0x07FF, "C"),
		(6, 0xFFFF, "W"),
		(7, 0x0000, "K"),
	]
	w = 20
	for i, color, label in bars:
		x = i * w
		d.fill_rect(x, 0, w, 22, color)
		text_color = 0x0000 if color == 0xFFFF else 0xFFFF
		d.text(label, x + 7, 7, text_color)


def draw_face(d):
	# Background should look neutral gray, not lavender.
	d.fill_rect(0, 22, 160, 106, 0xC618)

	# Hair
	d.fill_rect(40, 34, 80, 38, 0x3146)
	# Face skin tone
	d.fill_rect(50, 44, 60, 56, 0xDBB1)
	# Eyes
	d.fill_rect(62, 64, 8, 5, 0x0000)
	d.fill_rect(90, 64, 8, 5, 0x0000)
	# Mouth
	d.fill_rect(72, 84, 16, 3, 0xA145)

	# UI swatches close to your menu palette.
	d.fill_rect(5, 104, 58, 18, 0x39E7)   # cool blue panel
	d.fill_rect(66, 104, 58, 18, 0x7AEF)  # neutral slot
	d.fill_rect(127, 104, 28, 18, 0x07E0) # selection green

	d.text("FACE", 8, 108, 0xFFFF)
	d.text("SLOT", 69, 108, 0x0000)
	d.text("SEL", 130, 108, 0x0000)


def main():
	bl = PWM(Pin(13))
	bl.freq(1000)
	bl.duty_u16(52000)

	d = lcd.LCD_1inch8()

	while True:
		d.fill(0x0000)
		draw_color_bars(d)
		draw_face(d)
		d.text("COLOR CHECK", 28, 26, 0xFFFF)
		d.show()
		time.sleep(1)


if __name__ == "__main__":
	main()

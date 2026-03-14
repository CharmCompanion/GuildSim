from PIL import Image

def convert_png_to_rgb565_array(png_path, var_name, out_path):
    img = Image.open(png_path).convert('RGB').resize((128, 160))
    with open(out_path, 'w') as f:
        f.write(f'#include <stdint.h>\n')
        f.write(f'const uint16_t {var_name}[128*160] = {{\n')
        for y in range(160):
            for x in range(128):
                r, g, b = img.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                f.write(f'0x{rgb565:04X},')
            f.write('\n')
        f.write('};\n')

convert_png_to_rgb565_array('GuildBG.png', 'guildBG_128x160', 'GuildBG_128x160.c')
convert_png_to_rgb565_array('GuildFG.png', 'guildFG_128x160', 'GuildFG_128x160.c')

cd "c:\Users\RY0M\Desktop\Guildmaster  V-Pet\GuildSim\assets\scenes\Guild"
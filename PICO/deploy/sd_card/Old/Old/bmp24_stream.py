"""Low-memory 24-bit BMP reader for MicroPython/Pico.

This module reads BMP rows directly from a file handle so callers can render
images without loading full frames into RAM.
"""


def _u16_le(buf, offset):
    return buf[offset] | (buf[offset + 1] << 8)


def _u32_le(buf, offset):
    return (
        buf[offset]
        | (buf[offset + 1] << 8)
        | (buf[offset + 2] << 16)
        | (buf[offset + 3] << 24)
    )


def _i32_le(buf, offset):
    value = _u32_le(buf, offset)
    if value & 0x80000000:
        return -((~value + 1) & 0xFFFFFFFF)
    return value


def rgb565(r, g, b):
    """Pack 24-bit RGB into standard RGB565."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def bgr565(r, g, b):
    """Alternative packing used by some display paths with swapped channels."""
    return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)


class BMP24Reader:
    """Row-streaming BMP parser for uncompressed 24-bit BMP files."""

    def __init__(self, file_handle):
        self._fh = file_handle
        self._read_header()

    def _read_header(self):
        self._fh.seek(0)
        header = self._fh.read(54)
        if len(header) < 54:
            raise ValueError("BMP header too small")

        if header[0] != 0x42 or header[1] != 0x4D:
            raise ValueError("Not a BMP file")

        self.pixel_data_offset = _u32_le(header, 10)
        dib_size = _u32_le(header, 14)
        if dib_size < 40:
            raise ValueError("Unsupported BMP DIB header")

        width = _i32_le(header, 18)
        height = _i32_le(header, 22)
        planes = _u16_le(header, 26)
        bits_per_pixel = _u16_le(header, 28)
        compression = _u32_le(header, 30)

        if planes != 1:
            raise ValueError("Invalid BMP planes")
        if bits_per_pixel != 24:
            raise ValueError("Only 24-bit BMP is supported")
        if compression != 0:
            raise ValueError("Compressed BMP not supported")

        if width <= 0 or height == 0:
            raise ValueError("Invalid BMP dimensions")

        self.width = width
        self.top_down = height < 0
        self.height = -height if height < 0 else height

        # 3 bytes/pixel with 4-byte row alignment padding.
        self.row_stride = ((self.width * 3) + 3) & ~3

    def get_row_bgr(self, row_index):
        """Return row bytes in BMP BGR order for one logical row index (top=0)."""
        if row_index < 0 or row_index >= self.height:
            raise IndexError("Row out of range")

        if self.top_down:
            bmp_row = row_index
        else:
            bmp_row = self.height - 1 - row_index

        row_offset = self.pixel_data_offset + (bmp_row * self.row_stride)
        self._fh.seek(row_offset)
        row = self._fh.read(self.row_stride)
        if len(row) < self.row_stride:
            raise ValueError("Unexpected EOF while reading BMP row")
        return row

    def iter_pixels(self, row_index):
        """Yield (r, g, b) tuples for one row."""
        row = self.get_row_bgr(row_index)
        pixel_bytes = self.width * 3
        for i in range(0, pixel_bytes, 3):
            b = row[i]
            g = row[i + 1]
            r = row[i + 2]
            yield (r, g, b)

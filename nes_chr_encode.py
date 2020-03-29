"""Convert a PNG image into an NES CHR data file."""

import argparse
import os
import sys
import png  # PyPNG

def parse_arguments():
    """Parse and validate command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Convert a PNG image into an NES CHR (graphics) data file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="PNG palette (which colors correspond to CHR colors 0-3). Four 6-digit hexadecimal "
        "RRGGBB color codes (\"000000\"-\"ffffff\") separated by spaces. Must be all distinct."
    )
    parser.add_argument(
        "input_file",
        help="The PNG image to read. The width must be 128 pixels. The height must be a multiple "
        "of 8 pixels. There must be four unique colors or less. --palette must contain all the "
        "colors in the image, but the image need not contain all the colors in --palette."
    )
    parser.add_argument(
        "output_file",
        help="The NES CHR data file to write. The size will be a multiple of 256 bytes."
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")
    if len(set(args.palette)) < 4:
        sys.exit("All colors in --palette must be distinct.")

    return args

def decode_color_code(color):
    """Decode a 6-digit hexadecimal color code. Return (R, G, B)."""

    try:
        if len(color) != 6:
            raise ValueError
        color = int(color, 16)
    except ValueError:
        sys.exit("Invalid command line color argument.")
    return (color >> 16, (color >> 8) & 0xff, color & 0xff)

def palettize_pixel_rows(RGBRows, palette):
    """In: RGB pixel rows (each RGBRGB...), yield: one indexed pixel row per call"""

    RGBToIndex = dict((RGB, i) for (i, RGB) in enumerate(palette))
    indexedRow = []
    for RGBRow in RGBRows:
        indexedRow.clear()
        for pos in range(0, len(RGBRow), 3):
            RGB = tuple(RGBRow[pos:pos+3])
            try:
                indexedRow.append(RGBToIndex[RGB])
            except KeyError:
                sys.exit("Color in PNG not specified by --palette: {:02x}{:02x}{:02x}".format(*RGB))
        yield indexedRow

def encode_character_slice(indexes):
    """Encode 8*1 pixels of one character.
    In: 8 two-bit ints (indexed pixels), return: (int with the LSBs, int with the MSBs)"""

    LSBs = sum((indexes[i] & 1) << (7 - i) for i in range(8))
    MSBs = sum((indexes[i] >> 1) << (7 - i) for i in range(8))
    return (LSBs, MSBs)

def encode_pixel_rows(RGBPixelRows, palette):
    """in: pixel rows (128*1 px each, 8-bit RGBRGB... values)
    yield: one NES character data row from every 8 pixel rows (16*1 characters, 128*8 px, 256
    bytes)"""

    charData = bytearray(256)
    for (pxY, indexedPixelRow) in enumerate(palettize_pixel_rows(RGBPixelRows, palette)):
        for charX in range(16):
            charSlice = indexedPixelRow[charX*8:(charX+1)*8]
            i = charX * 16 + pxY % 8
            (charData[i], charData[i+8]) = encode_character_slice(charSlice)
        if pxY % 8 == 7:
            yield charData

def encode_file(source, target, palette):
    """Convert a PNG file to an NES CHR data file."""

    source.seek(0)
    (width, height, RGBPixelRows) = png.Reader(source).asRGB8()[:3]
    if width != 128:  # 16 NES characters
        sys.exit("Invalid PNG width.")
    (charRowCount, remainder) = divmod(height, 8)
    if charRowCount == 0 or remainder:
        sys.exit("Invalid PNG height.")

    target.seek(0)
    for chrDataRow in encode_pixel_rows(RGBPixelRows, palette):
        target.write(chrDataRow)

def main():
    """The main function."""

    settings = parse_arguments()
    palette = tuple(decode_color_code(color) for color in settings.palette)
    try:
        with open(settings.input_file, "rb") as source, open(settings.output_file, "wb") as target:
            encode_file(source, target, palette)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

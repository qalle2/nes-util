"""Convert an NES CHR data file to/from a PNG file."""

import argparse
import os
import sys
import png  # PyPNG

# UI section ---------------------------------------------------------------------------------------

def parse_arguments():
    """Parse and validate command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Convert an NES CHR (graphics) data file to a PNG file or vice versa. File "
        "restrictions (input&output): PNG: width 128 pixels, height a multiple of 8 pixels, 4 "
        "unique colors or less, all colors specified by --palette; CHR: file size a multiple of "
        "256 bytes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="PNG palette (which colors correspond to CHR colors 0-3). Four 6-digit hexadecimal "
        "RRGGBB color codes (\"000000\"-\"ffffff\") separated by spaces. Must be all distinct when "
        "encoding (reading a PNG)."
    )
    parser.add_argument(
        "operation", choices=("e", "d"),
        help="What to do: e=encode (PNG to CHR), d=decode (CHR to PNG)."
    )
    parser.add_argument("input_file", help="The file to read (PNG if encoding, CHR if decoding).")
    parser.add_argument("output_file", help="The file to write (CHR if encoding, PNG if decoding).")

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")
    if args.operation == "e" and len(set(args.palette)) < 4:
        sys.exit("All colors in --palette must be distinct when encoding.")

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

# encode section -----------------------------------------------------------------------------------

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

# decode section -----------------------------------------------------------------------------------

def read_character_data_rows(source):
    """in: NES character data file
    yield: one character data row per call (16*1 characters, 128*8 px, 256 bytes)"""

    fileSize = source.seek(0, 2)
    source.seek(0)
    while source.tell() < fileSize:
        yield source.read(256)

def decode_character_slice(LSBs, MSBs):
    """Decode 8*1 pixels of one character.
    LSBs: integer with 8 less significant bits
    MSBs: integer with 8 more significant bits
    return: iterable with 8 2-bit big-endian integers"""

    MSBs <<= 1
    return (((LSBs >> shift) & 1) | ((MSBs >> shift) & 2) for shift in range(7, -1, -1))

def decode_pixel_rows(source):
    """in: NES character data file
    yield: one pixel row per call (128*1 px, 2-bit values)"""

    indexedPixelRow = []
    for charDataRow in read_character_data_rows(source):
        for pxY in range(8):
            indexedPixelRow.clear()
            for charX in range(16):
                i = charX * 16 + pxY
                indexedPixelRow.extend(decode_character_slice(charDataRow[i], charDataRow[i+8]))
            yield indexedPixelRow

def decode_file(source, target, palette):
    """Convert an NES CHR data file to a PNG file."""

    fileSize = source.seek(0, 2)
    (charRowCount, remainder) = divmod(fileSize, 256)  # 16 NES characters/row
    if charRowCount == 0 or remainder:
        sys.exit("Invalid input file size.")

    source.seek(0)
    target.seek(0)
    targetImage = png.Writer(
        width=128,  # 16 NES characters
        height=charRowCount * 8,
        bitdepth=2,  # 4 colors
        palette=palette,
    )
    targetImage.write(target, decode_pixel_rows(source))

def main():
    """The main function."""

    settings = parse_arguments()
    palette = tuple(decode_color_code(color) for color in settings.palette)
    try:
        with open(settings.input_file, "rb") as source, open(settings.output_file, "wb") as target:
            function = encode_file if settings.operation == "e" else decode_file
            function(source, target, palette)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

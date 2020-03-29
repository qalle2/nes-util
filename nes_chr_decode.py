"""Convert an NES CHR data file to a PNG file."""

import argparse
import os
import sys
import png  # PyPNG

# UI section ---------------------------------------------------------------------------------------

def parse_arguments():
    """Parse and validate command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Convert an NES CHR (graphics) data file into a PNG file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Output palette (which colors correspond to CHR colors 0-3). Four 6-digit hexadecimal "
        "RRGGBB color codes (\"000000\"-\"ffffff\") separated by spaces."
    )
    parser.add_argument(
        "input_file",
        help="The NES CHR data file to read. The size must be a multiple of 256 bytes."
    )
    parser.add_argument(
        "output_file",
        help="The PNG image file to write. Its width will be 128 pixels, height a multiple of 8 "
        "pixels. It will have 1-4 unique colors."
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

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
            decode_file(source, target, palette)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

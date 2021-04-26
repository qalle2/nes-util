"""Convert NES CHR data into a PNG file."""

import argparse, itertools, os, sys
from PIL import Image  # Pillow, https://python-pillow.org
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
    # parse command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Convert NES CHR (graphics) data into a PNG file."
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Output palette (which image colors correspond to CHR colors 0...3). Four hexadecimal "
        "RRGGBB color codes separated by spaces. Default: 000000 555555 aaaaaa ffffff"
    )
    parser.add_argument(
        "input_file",
        help="File to read. An iNES ROM file (.nes) or raw CHR data (the size must be a multiple "
        "of 256 bytes)."
    )
    parser.add_argument(
        "output_file", help="PNG file to write. Always 128 pixels (16 tiles) wide."
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def decode_color_code(color):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)

    if len(color) != 6:
        sys.exit("Each color code must be 6 hexadecimal digits.")

    try:
        color = int(color, 16)
    except ValueError:
        sys.exit("Color codes must be hexadecimal.")

    return (color >> 16, (color >> 8) & 0xff, color & 0xff)

def get_chr_addr_and_size(handle):
    # detect file type and get (address, size) of CHR ROM data

    fileInfo = qneslib.ines_header_decode(handle)
    if fileInfo is not None:
        # iNES ROM file
        if fileInfo["chrSize"] == 0:
            sys.exit("The input file is an iNES ROM file but has no CHR ROM.")
        return (fileInfo["chrStart"], fileInfo["chrSize"])
    else:
        fileSize = handle.seek(0, 2)
        if fileSize == 0 or fileSize % 256:
            sys.exit("The input file is neither an iNES ROM file nor a raw CHR data file.")
        # raw CHR data file
        return (0, fileSize)

def decode_pixel_rows(handle, charRowCount):
    # generate one pixel row (128 two-bit values) per call from NES CHR data

    pixelRow = []
    for i in range(charRowCount):
        # read 16*1 characters (16 bytes or 8*8 pixels each)
        charRow = handle.read(256)
        for pixY in range(8):
            pixelRow.clear()
            for charX in range(16):
                # decode two bytes (bitplanes) into eight pixels
                loPos = (charX << 4) | pixY
                hiPos = (charX << 4) | 8 | pixY
                pixelRow.extend(qneslib.tile_slice_decode(charRow[loPos], charRow[hiPos]))
            yield pixelRow

def chr_data_to_png(handle, palette):
    # convert CHR data into a PNG image using Pillow

    (chrAddr, chrSize) = get_chr_addr_and_size(handle)
    charRowCount = chrSize // 256

    image = Image.new("P", (16 * 8, charRowCount * 8))
    image.putpalette(itertools.chain.from_iterable(palette))

    handle.seek(chrAddr)
    for (y, pixelRow) in enumerate(decode_pixel_rows(handle, charRowCount)):
        for (x, value) in enumerate(pixelRow):
            image.putpixel((x, y), value)

    return image

args = parse_arguments()
palette = tuple(decode_color_code(color) for color in args.palette)

# convert CHR data into an image
try:
    with open(args.input_file, "rb") as handle:
        image = chr_data_to_png(handle, palette)
except OSError:
    sys.exit("Error reading input file.")

# save image
try:
    with open(args.output_file, "wb") as handle:
        handle.seek(0)
        image.save(handle, "png")
except OSError:
    sys.exit("Error writing output file.")

"""Convert an image file into an NES CHR data file."""

import argparse
import os
import sys
from PIL import Image  # Pillow

def reorder_palette(img, mapping):
    """Return image with reordered palette. mapping: from command line arguments"""

    palette = img.getpalette()
    palette = [tuple(palette[i*3:i*3+3]) for i in range(256)]  # RGB

    mapping = [decode_color_code(c) for c in mapping]  # RGB

    undefinedColors = set(palette[c[1]] for c in img.getcolors()) - set(mapping)  # RGB
    if undefinedColors:
        sys.exit("Image contains colors not defined by --palette: " + ", ".join(
            "".join(f"{c:02x}" for c in rgb) for rgb in sorted(undefinedColors)
        ))

    # map new indexes 0...3 to colors in the command line argument
    return img.remap_palette(palette.index(c) for c in mapping)

def encode_image(img):
    """Generate 256 bytes (16*1 tiles) of NES CHR data for every 128*8 pixels in a Pillow
    image."""

    data = bytearray(256)

    for y in range(img.height):
        for x in range(0, 128, 8):
            # read 8*1 pixels (2 bits each); convert into two bitplanes (8 bits each)
            loByte = hiByte = 0
            for pixel in (img.getpixel((x2, y)) for x2 in range(x, x + 8)):
                loByte = (loByte << 1) | (pixel &  1)
                hiByte = (hiByte << 1) | (pixel >> 1)
            # store bitplanes (tile = 16 bytes; first low bitplane, then high)
            loPos = (x << 1) | (y & 7)
            hiPos = (x << 1) | 8 | (y & 7)
            (data[loPos], data[hiPos]) = (loByte, hiByte)
        if y & 7 == 7:
            yield data

def image_to_chr(source, target, args):
    # open image
    source.seek(0)
    img = Image.open(source)

    # validate image
    if img.width != 128:
        sys.exit("Image must be 128 pixels wide.")
    if img.height == 0 or img.height % 8:
        sys.exit("Image height must be a multiple of 8 pixels.")
    if img.mode not in ("P", "L", "RGB"):
        sys.exit("Image format must be indexed, grayscale or RGB.")
    if img.getcolors(4) is None:
        sys.exit("Image must have four unique colors or less.")

    # convert into indexed color
    if img.mode in ("L", "RGB"):
        img = img.convert("P", dither=Image.NONE, palette=Image.ADAPTIVE)

    img = reorder_palette(img, args.palette)

    # encode into CHR data
    target.seek(0)
    for dataRow in encode_image(img):
        target.write(dataRow)

# --- main, argument parsing ----------------------------------------------------------------------

def parse_arguments():
    """Parse and validate command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Convert an image file into an NES CHR (graphics) data file.",
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="PNG palette (which colors correspond to CHR colors 0...3). Four color codes "
        "(hexadecimal RGB or RRGGBB) separated by spaces. Must be all distinct. Default: "
        "'000000 555555 aaaaaa ffffff'"
    )
    parser.add_argument(
        "input_file",
        help="The image file to read (e.g. PNG). The width must be 128 pixels. The height must be "
        "a multiple of 8 pixels. There must be four unique colors or less. --palette must contain "
        "all the colors in the image, but the image need not contain all the colors in --palette."
    )
    parser.add_argument(
        "output_file",
        help="The NES CHR data file to write. The size will be a multiple of 256 bytes."
    )

    args = parser.parse_args()

    if len(set(decode_color_code(c) for c in args.palette)) < 4:
        sys.exit("All colors in --palette must be distinct.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def decode_color_code(color):
    """Decode a color code (hexadecimal RGB/RRGGBB). Return (red, green, blue),
    each 0...255."""

    # based on bits per component, get constants for separating them
    if len(color) == 3:
        mask = 0xf
        multiplier = 0x11
        shift = 4
    elif len(color) == 6:
        mask = 0xff
        multiplier = 1
        shift = 8
    else:
        sys.exit("Color code must be 3 or 6 hexadecimal digits.")

    try:
        color = int(color, 16)
    except ValueError:
        sys.exit("Color code must be hexadecimal.")

    # separate components, scale them to 0...255
    components = []
    for i in range(3):
        components.append((color & mask) * multiplier)
        color >>= shift
    return tuple(components[::-1])

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as source, \
        open(args.output_file, "wb") as target:
            image_to_chr(source, target, args)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

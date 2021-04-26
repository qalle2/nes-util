"""Convert an image file into an NES CHR data file."""

import argparse, os, sys
from PIL import Image  # Pillow, https://python-pillow.org

def decode_color_code(color):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)

    if len(color) != 6:
        sys.exit("Each color code must be 6 hexadecimal digits.")

    try:
        color = int(color, 16)
    except ValueError:
        sys.exit("Color codes must be hexadecimal.")

    return (color >> 16, (color >> 8) & 0xff, color & 0xff)

def parse_arguments():
    # parse and validate command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Convert an image file into an NES CHR (graphics) data file.",
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Input palette (which image colors correspond to CHR colors 0...3). Four hexadecimal "
        "RRGGBB color codes separated by spaces. Must be all distinct and include every unique "
        "color in the input file. May contain colors not present in the input file. Default: "
        "000000 555555 aaaaaa ffffff"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print more info."
    )
    parser.add_argument(
        "input_file",
        help="Image file to read. Width must be 128 pixels (16 tiles). Height must be a multiple "
        "of 8 pixels (1 tile). There must be four unique colors or less. See also --palette."
    )
    parser.add_argument(
        "output_file",
        help="NES CHR data file to write. The size will be a multiple of 256 bytes (16 tiles)."
    )

    args = parser.parse_args()

    if len(set(decode_color_code(c) for c in args.palette)) < 4:
        sys.exit("All colors in --palette must be distinct.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def get_image_palette(img):
    # get palette from Pillow image as [(R, G, B), ...]
    palette = img.getpalette()  # [R, G, B, ...]
    return [tuple(palette[i*3:(i+1)*3]) for i in range(256)]

def reorder_palette(img, args):
    # reorder palette of indexed image

    palette = get_image_palette(img)
    mapping = [decode_color_code(c) for c in args.palette]

    usedColors = set(palette[c[1]] for c in img.getcolors())  # {(R, G, B), ...}
    undefinedColors = usedColors - set(mapping)
    if undefinedColors:
        sys.exit(
            "Error: the image contains colors not specified by --palette: "
            + ", ".join(bytes(c).hex() for c in sorted(undefinedColors))
        )

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

args = parse_arguments()

if args.verbose:
    print("Color settings (RGB -> CHR index): " + ", ".join(
        f"{bytes(decode_color_code(c)).hex()} -> {i}" for (i, c) in enumerate(args.palette)
    ))

try:
    with open(args.input_file, "rb") as source, open(args.output_file, "wb") as target:
        # open image
        source.seek(0)
        img = Image.open(source)

        # validate image
        if img.width != 128:
            sys.exit("The image must be 128 pixels wide.")
        if img.height == 0 or img.height % 8:
            sys.exit("Image height must be a multiple of 8 pixels.")
        if img.mode not in ("P", "L", "RGB"):
            sys.exit("Image format must be indexed, grayscale or RGB.")
        if img.getcolors(4) is None:
            sys.exit("The image must have four unique colors or less.")

        # convert into indexed color
        if img.mode in ("L", "RGB"):
            img = img.convert("P", dither=Image.NONE, palette=Image.ADAPTIVE)

        img = reorder_palette(img, args)
        if args.verbose:
            print("Reordered image palette (index -> RGB): " + ", ".join(
                f"{i} -> {bytes(c).hex()}" for (i, c) in enumerate(get_image_palette(img)[:4])
            ))

        # encode into CHR data
        target.seek(0)
        for dataRow in encode_image(img):
            target.write(dataRow)
except OSError:
    sys.exit("Error reading/writing files.")

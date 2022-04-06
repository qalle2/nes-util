import argparse, os, sys
from PIL import Image  # Pillow, https://python-pillow.org
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

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
    parser = argparse.ArgumentParser(
        description="Convert an image file into an NES CHR (graphics) data file.",
    )
    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Input palette (which image colors correspond to CHR colors 0-3). Four hexadecimal "
        "RRGGBB color codes separated by spaces. Must be all distinct. Must include every unique "
        "color in input file. May contain colors not present in input file. Default: 000000 "
        "555555 aaaaaa ffffff"
    )
    parser.add_argument(
        "input_file",
        help="Image file to read. Width must be 128 pixels (16 tiles). Height must be a multiple "
        "of 8 pixels (1 tile). No more than 4 unique colors."
    )
    parser.add_argument(
        "output_file",
        help="NES CHR data file to write. The size will be a multiple of 256 bytes (16 tiles)."
    )
    args = parser.parse_args()

    if len(set(decode_color_code(c) for c in args.palette)) < 4:
        sys.exit("All colors in --palette argument must be distinct.")
    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def reorder_palette(img, args):
    # map indexes 0-3 of an indexed image to colors in the command line argument

    palette = img.getpalette()  # [R, G, B, ...]
    palette = [tuple(palette[i*3:(i+1)*3]) for i in range(256)]  # [(R, G, B), ...]
    mapping = [decode_color_code(c) for c in args.palette]

    usedColors = {palette[c[1]] for c in img.getcolors()}  # {(R, G, B), ...}
    undefinedColors = usedColors - set(mapping)
    if undefinedColors:
        sys.exit(
            "Image contains colors not specified by --palette argument: "
            + ", ".join(bytes(c).hex() for c in sorted(undefinedColors))
        )

    return img.remap_palette(palette.index(c) for c in mapping)

def encode_image(img):
    # generate NES CHR data from a Pillow image (256 bytes for every 128*8 pixels or 16*1 tiles);
    # note: a tile is 8*8 pixels and 2 bitplanes, or 16 bytes; first low bitplane from top to
    # bottom, then high bitplane from top to bottom; 1 byte is 8*1 pixels of one bitplane

    data = bytearray(256)
    for y in range(img.height):
        for x in range(0, 128, 8):
            # read 8*1 pixels, convert into 2 bytes, store 8 bytes apart
            (data[x*2+y%8], data[x*2+y%8+8]) \
            = qneslib.tile_slice_encode(img.getpixel((x2, y)) for x2 in range(x, x + 8))
        if y % 8 == 7:
            yield data

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as source:
            # open image
            source.seek(0)
            img = Image.open(source)
            # validate
            if img.width != 128:
                sys.exit("Image width must be 128.")
            if img.height == 0 or img.height % 8:
                sys.exit("Image height must be a multiple of 8.")
            if img.getcolors(4) is None:
                sys.exit("Image must have 4 unique colors or less.")
            # convert into indexed color
            if img.mode != "P":
                img = img.convert("P", dither=Image.NONE, palette=Image.ADAPTIVE)
            # reorder palette
            img = reorder_palette(img, args)
            # encode into CHR data
            with open(args.output_file, "wb") as target:
                target.seek(0)
                for dataRow in encode_image(img):
                    target.write(dataRow)
    except OSError:
        sys.exit("Error reading/writing files.")

main()

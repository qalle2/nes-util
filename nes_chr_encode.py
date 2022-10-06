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
    parser = argparse.ArgumentParser(
        description="Convert an image file into an NES CHR (graphics) data "
        "file."
    )
    parser.add_argument(
        "-p", "--palette", nargs=4,
        default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Input palette (which image colors correspond to CHR colors "
        "0-3). Four hexadecimal RRGGBB color codes separated by spaces. Must "
        "be all distinct. Must include every unique color in input file. May "
        "contain colors not present in input file. Default: 000000 555555 "
        "aaaaaa ffffff"
    )
    parser.add_argument(
        "input_file",
        help="Image file to read. Width must be 128 pixels (16 tiles). Height "
        "must be a multiple of 8 pixels (1 tile). No more than 4 unique "
        "colors."
    )
    parser.add_argument(
        "output_file",
        help="NES CHR data file to write. The size will be a multiple of 256 "
        "bytes (16 tiles)."
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
    # map indexes 0-3 of an indexed image to colors in the command line arg

    palette = img.getpalette()  # [R, G, B, ...]
    palette = [tuple(palette[i*3:(i+1)*3]) for i in range(256)]  #[(R,G,B),...]
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
    # generate NES CHR data from a Pillow image: 8 bytes for each bitplane of
    # each tile (each tile is 8*8 pixels and 2 bitplanes; less significant
    # bitplane comes first; each byte is 8*1 pixels of one bitplane)

    for ty in range(0, img.height, 8):  # tile Y
        for tx in range(0, 128, 8):  # tile X
            tile = list(img.crop((tx, ty, tx + 8, ty + 8)).getdata())
            for bp in range(2):  # bitplane
                yield bytes(
                    sum(((tile[py+x] >> bp) & 1) << (7 - x) for x in range(8))
                    for py in range(0, 64, 8)
                )

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
                img = img.convert(
                    "P", dither=Image.NONE, palette=Image.ADAPTIVE
                )
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

# encode NES CHR data

# NES CHR data format:
# - byte = 1 bitplane of 8*1 pixels (most significant bit = leftmost pixel)
# - tile = 2 bitplanes of 8*8 pixels (first low bitplane top to bottom, then
#   high bitplane top to bottom)
# - pattern table = 256 tiles
# - maximum CHR data without bankswitching = 2 pattern tables

import os, sys
try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow module required. See https://python-pillow.org")

DEFAULT_PALETTE = "000000,555555,aaaaaa,ffffff"

HELP_TEXT = f"""\
Convert an image file into an NES CHR (graphics) data file.
Arguments: IN OUT PALETTE (PALETTE is optional)
    IN: Image file to read (e.g. PNG).
        Width must be 128 pixels (16 tiles).
        Height must be a multiple of 8 pixels (1 tile).
        No more than 4 unique colors.
    OUT: NES CHR data file to write.
         The size will be a multiple of 256 bytes (16 tiles).
    PALETTE: Input palette (which image colors correspond to CHR colors 0-3).
             Four hexadecimal RRGGBB color codes (000000-ffffff) separated by
             commas.
             All colors must be distinct.
             Palette may contain colors not present in input file.
             Palette must include every unique color in input file.
             Default: {DEFAULT_PALETTE}\
"""

def decode_color(color):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)

    try:
        color = int(color, 16)
        if not 0 <= color <= 0xffffff:
            raise ValueError
    except ValueError:
        sys.exit("Unrecognized color code.")
    return (color >> 16, (color >> 8) & 0xff, color & 0xff)

def parse_arguments():
    if not 3 <= len(sys.argv) <= 4:
        sys.exit(HELP_TEXT)

    (inputFile, outputFile) = sys.argv[1:3]

    palette = sys.argv[3] if len(sys.argv) == 4 else DEFAULT_PALETTE
    palette = tuple(decode_color(c) for c in palette.split(","))
    if len(palette) != 4:
        sys.exit("Incorrect number of colors in palette argument.")
    if len(set(palette)) < 4:
        sys.exit("All colors in palette argument must be distinct.")

    if not os.path.isfile(inputFile):
        sys.exit("Input file not found.")
    if os.path.exists(outputFile):
        sys.exit("Output file already exists.")

    return {
        "inputFile": inputFile,
        "outputFile": outputFile,
        "palette": palette,
    }

def get_color_conv_table(image, targetPal):
    # get a tuple that converts original color indexes into those specified by
    # the command line argument
    # (note: reordering the image palette with remap_palette() used to work;
    # now doesn't with the 2-color test image)

    origPal = image.getpalette()  # [R, G, B, ...]
    origPal = [
        tuple(origPal[i*3:(i+1)*3]) for i in range(len(origPal) // 3)
    ]  # [(R, G, B), ...]

    usedColors = {origPal[c[1]] for c in image.getcolors()}  # {(R, G, B), ...}
    undefinedColors = usedColors - set(targetPal)
    if undefinedColors:
        sys.exit(
            "Image contains colors not specified by palette argument: "
            + ", ".join(bytes(c).hex() for c in sorted(undefinedColors))
        )

    return tuple(targetPal.index(c) for c in origPal)

def generate_tiles(image):
    # generate tiles (64 2-bit integers each) from image
    for y in range(0, image.height, 8):
        for x in range(0, 128, 8):
            yield image.crop((x, y, x + 8, y + 8)).getdata()

def encode_image(image, colorConvTable):
    # generate NES CHR data from image (1 bitplane of 1 tile per call)
    # colorConvTable: a tuple that converts color indexes

    for tile in generate_tiles(image):
        tile = tuple(colorConvTable[c] for c in tile)
        for bp in range(2):
            yield bytes(
                sum(((tile[y+x] >> bp) & 1) << (7 - x) for x in range(8))
                for y in range(0, 64, 8)
            )

def convert_image(source, target, palette):
    # source, target: handles; palette: from command line argument

    source.seek(0)
    image = Image.open(source)

    # validate
    if image.width != 128:
        sys.exit("Incorrect image width.")
    if image.height == 0 or image.height % 8:
        sys.exit("Incorrect image height.")
    if image.getcolors(4) is None:
        sys.exit("Too many colors in image.")
    # convert into indexed color
    if image.mode != "P":
        image = image.convert(
            "P", dither=Image.Dither.NONE, palette=Image.Palette.ADAPTIVE
        )
    # create palette conversion table
    colorConvTable = get_color_conv_table(image, palette)

    # write output file
    target.seek(0)
    for dataRow in encode_image(image, colorConvTable):
        target.write(dataRow)

def main():
    args = parse_arguments()

    try:
        with open(args["inputFile"], "rb") as source, \
        open(args["outputFile"], "wb") as target:
            convert_image(source, target, args["palette"])
    except OSError:
        sys.exit("File read/write error.")

main()

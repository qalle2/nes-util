# convert an image into NES CHR data

import os, sys
try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow module required. See https://python-pillow.org")

TILES_PER_ROW = 16  # output image width in tiles
TILE_WIDTH    = 8   # in pixels
TILE_HEIGHT   = 8   # in pixels

BYTES_PER_TILE = TILE_WIDTH * TILE_HEIGHT * 2 // 8  # 2 bits/pixel

DEFAULT_PALETTE = "000000,555555,aaaaaa,ffffff"

HELP_TEXT = f"""\
Convert an image file into an NES CHR (graphics) data file.
Arguments: inputFile outputFile palette
    inputFile: Image file to read (e.g. PNG). Width must be
        {TILES_PER_ROW*TILE_WIDTH} pixels ({TILES_PER_ROW} tiles). Height must
        be a multiple of {TILE_HEIGHT} pixels (1 tile). No more than 4 unique
        colors.
    outputFile: NES CHR data file to write. The size will be a multiple of
        {TILES_PER_ROW*BYTES_PER_TILE} bytes ({TILES_PER_ROW} tiles).
    palette: Optional. Input palette (which image colors correspond to CHR
        colors 0-3). Four hexadecimal RRGGBB color codes (000000-ffffff)
        separated by commas. All colors must be distinct. Palette must include
        every unique color in input file. Palette may contain colors not
        present in input file.
        Default: {DEFAULT_PALETTE}\
"""

def decode_color_code(colorStr):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)
    try:
        color = int(colorStr, 16)
        if not 0 <= color <= 0xffffff:
            raise ValueError
    except ValueError:
        sys.exit("Unrecognized color code: " + colorStr)
    return tuple((color >> s) & 0xff for s in (16, 8, 0))

def parse_arguments():
    # return: (inputFile, outputFile, palette)

    if not 3 <= len(sys.argv) <= 4:
        sys.exit(HELP_TEXT)

    (inputFile, outputFile) = sys.argv[1:3]

    palette = sys.argv[3] if len(sys.argv) == 4 else DEFAULT_PALETTE
    palette = tuple(decode_color_code(c) for c in palette.split(","))
    if len(palette) != 4:
        sys.exit("Incorrect number of colors in palette argument.")
    if len(set(palette)) < 4:
        sys.exit("All colors in palette argument must be distinct.")

    if not os.path.isfile(inputFile):
        sys.exit("Input file not found.")
    if os.path.exists(outputFile):
        sys.exit("Output file already exists.")

    return (inputFile, outputFile, palette)

def validate_and_prepare_image(image):
    if image.width != TILES_PER_ROW * TILE_WIDTH:
        sys.exit(f"Image width must be {TILES_PER_ROW*TILE_WIDTH} pixels.")
    if image.height == 0 or image.height % TILE_HEIGHT:
        sys.exit(f"Image height must be a multiple of {TILE_HEIGHT} pixels.")
    if image.getcolors(4) is None:
        sys.exit("Too many colors in image.")

    # convert into indexed color
    if image.mode != "P":
        image = image.convert(
            "P", dither=Image.Dither.NONE, palette=Image.Palette.ADAPTIVE
        )

    return image

def get_color_conv_table(image, targetPal):
    # get a tuple that converts original color indexes into those specified by
    # the command line argument
    # (note: reordering the image palette with remap_palette() used to work;
    # now doesn't with the 2-color test image)

    origPal = image.getpalette()  # [R, G, B, ...]
    # [(R, G, B), ...]
    origPal = [tuple(origPal[i*3:(i+1)*3]) for i in range(len(origPal) // 3)]

    usedColors = set(origPal[c[1]] for c in image.getcolors())  # {(R,G,B),...}
    undefinedColors = usedColors - set(targetPal)
    if undefinedColors:
        sys.exit(
            "Image contains colors not specified by palette argument: "
            + ", ".join(bytes(c).hex() for c in sorted(undefinedColors))
        )

    return tuple(targetPal.index(c) for c in origPal)

def generate_tiles(image):
    # generate tiles (64 2-bit integers each) from image
    for y in range(0, image.height, TILE_HEIGHT):
        for x in range(0, TILES_PER_ROW * TILE_WIDTH, TILE_WIDTH):
            yield image.crop((x, y, x + TILE_WIDTH, y + TILE_HEIGHT)).getdata()

def encode_image(image, palette):
    # generate NES CHR data from image (1 byte per call);
    # palette: a tuple of four (red, green, blue) tuples;
    # CHR data format:
    #     - tile = 16 bytes = 2 bitplanes (first low, then high)
    #     - bitplane = 8 bytes (first = topmost)
    #     - byte = 8*1 pixels of 1 bitplane (MSB = leftmost pixel)

    image = validate_and_prepare_image(image)
    colorConvTable = get_color_conv_table(image, palette)

    for tile in generate_tiles(image):
        tile = tuple(colorConvTable[c] for c in tile)
        for bitplane in range(2):
            for y in range(0, TILE_HEIGHT * TILE_WIDTH, TILE_WIDTH):
                yield sum(
                    ((tile[y+x] >> bitplane) & 1) << (7 - x)
                    for x in range(TILE_WIDTH)
                )

def main():
    (inputFile, outputFile, palette) = parse_arguments()

    # read and convert data
    try:
        with open(inputFile, "rb") as handle:
            handle.seek(0)
            image = Image.open(handle)
            chrData = bytes(encode_image(image, palette))
    except OSError:
        sys.exit("Error reading input file.")

    # write data
    try:
        with open(outputFile, "wb") as handle:
            handle.seek(0)
            handle.write(chrData)
    except OSError:
        sys.exit("Error writing output file.")

main()

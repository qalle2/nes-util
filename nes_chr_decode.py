# decode NES CHR data

# NES CHR data format:
# - byte = 1 bitplane of 8*1 pixels (most significant bit = leftmost pixel)
# - tile = 2 bitplanes of 8*8 pixels (first low bitplane top to bottom, then
#   high bitplane top to bottom)
# - pattern table = 256 tiles
# - maximum CHR data without bankswitching = 2 pattern tables

import itertools, os, struct, sys
try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow module required. See https://python-pillow.org")

DEFAULT_PALETTE = "000000,555555,aaaaaa,ffffff"

HELP_TEXT = f"""\
Convert NES CHR (graphics) data into a PNG file.
Arguments: IN OUT PALETTE (PALETTE is optional)
    IN:
        File to read. An iNES ROM (.nes) or raw CHR data.
        Size of raw CHR data must be a multiple of 256 bytes (16 tiles).
    OUT:
        PNG file to write. 128 pixels (16 tiles) wide.
    PALETTE:
        Output palette (which image colors correspond to CHR colors 0-3).
        Four hexadecimal RRGGBB codes (000000-ffffff) separated by commas.
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

    if not os.path.isfile(inputFile):
        sys.exit("Input file not found.")
    if os.path.exists(outputFile):
        sys.exit("Output file already exists.")

    return {
        "inputFile": inputFile,
        "outputFile": outputFile,
        "palette": palette,
    }

def decode_ines_header(handle):
    # parse iNES ROM header
    # (doesn't support VS System or PlayChoice-10 flags or NES 2.0 header)
    # return: None on error, otherwise (CHR ROM start address, CHR ROM size)
    # see https://www.nesdev.org/wiki/INES

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    handle.seek(0)
    (id_, prgSize, chrSize, flags6) = struct.unpack("4s3B", handle.read(7))

    prgSize *= 16 * 1024
    chrSize *= 8 * 1024
    trainerSize = bool(flags6 & 0b0000_0100) * 512

    if id_ != b"NES\x1a" or fileSize < 16 + trainerSize + prgSize + chrSize:
        return None

    return (16 + trainerSize + prgSize, chrSize)

def get_chr_info(handle):
    # detect file type and get (address, size) of CHR ROM data

    # try as iNES ROM
    chrInfo = decode_ines_header(handle)
    if chrInfo is not None:
        if chrInfo[1] == 0:
            sys.exit("iNES ROM file has no CHR ROM.")
        return chrInfo

    # try as raw CHR data
    fileSize = handle.seek(0, 2)
    if fileSize == 0 or fileSize % 256:
        sys.exit("Unrecognized input file format.")
    return (0, fileSize)

def generate_tiles(handle):
    # read NES CHR data, generate tiles (tuples of 64 2-bit ints)

    (chrAddr, chrSize) = get_chr_info(handle)
    tileCount = chrSize // 16  # 16 bytes/tile
    handle.seek(chrAddr)

    decodedTile = []
    for i in range(tileCount):
        tile = handle.read(16)
        decodedTile.clear()
        for y in range(8):
            lowBits = tile[y]
            highBits = tile[y+8] << 1
            decodedTile.extend(
                ((lowBits >> s) & 1) | ((highBits >> s) & 2)
                for s in range(7, -1, -1)
            )
        yield tuple(decodedTile)

def create_image(handle, palette):
    # read CHR data from file, return image

    (chrAddr, chrSize) = get_chr_info(handle)

    # chrSize // 16 bytes/tile // 16 tiles/row * 8 px/row
    imageHeight = chrSize // 32

    # create image with palette from command line argument
    image = Image.new("P", (16 * 8, imageHeight))
    image.putpalette(itertools.chain.from_iterable(palette))

    # convert CHR data into image data
    tileImage = Image.new("P", (8, 8))
    for (i, tile) in enumerate(generate_tiles(handle)):
        tileImage.putdata(tile)
        (y, x) = divmod(i, 16)
        image.paste(tileImage, (x * 8, y * 8))

    return image

def main():
    args = parse_arguments()

    try:
        with open(args["inputFile"], "rb") as handle:
            image = create_image(handle, args["palette"])
        with open(args["outputFile"], "wb") as handle:
            handle.seek(0)
            image.save(handle, "png")
    except OSError:
        sys.exit("File read/write error.")

main()

# convert NES CHR data into an image

import itertools, os, struct, sys
try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow module required. See https://python-pillow.org")

TILES_PER_ROW = 16  # output image width in tiles
TILE_WIDTH    = 8   # in pixels; don't change
TILE_HEIGHT   = 8   # in pixels; don't change
BITS_PER_BYTE = 8   # don't change

BYTES_PER_TILE = TILE_WIDTH * TILE_HEIGHT * 2 // BITS_PER_BYTE  # 2 bits/pixel

DEFAULT_PALETTE = "000000,555555,aaaaaa,ffffff"

HELP_TEXT = f"""\
Convert NES CHR (graphics) data into a PNG file.
Arguments: inputFile outputFile palette
    inputFile: File to read. An iNES ROM (.nes) or raw CHR data. Size of raw
        CHR data must be a multiple of {TILES_PER_ROW*BYTES_PER_TILE} bytes.
    outputFile: PNG file to write. {TILES_PER_ROW} tiles wide.
    palette: Optional. Output palette or which colors will correspond to CHR
        colors 0-3. Four hexadecimal RRGGBB codes (000000-ffffff) separated by
        commas. Default: {DEFAULT_PALETTE}\
"""

def decode_color(colorStr):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)

    try:
        color = int(colorStr, 16)
        if not 0 <= color <= 0xffffff:
            raise ValueError
    except ValueError:
        sys.exit("Unrecognized color code: " + colorStr)
    return tuple((color >> s) & 0xff for s in (16, 8, 0))

def parse_arguments():
    # return (inputFile, outputFile, palette)

    if not 3 <= len(sys.argv) <= 4:
        sys.exit(HELP_TEXT)

    (inputFile, outputFile) = sys.argv[1:3]

    palette = sys.argv[3] if len(sys.argv) == 4 else DEFAULT_PALETTE
    palette = tuple(decode_color(c) for c in palette.split(","))
    if len(palette) != 4:
        sys.exit("Incorrect number of colors in palette argument.")

    if not os.path.isfile(inputFile):
        sys.exit("Input file not found.")
    if os.path.exists(outputFile):
        sys.exit("Output file already exists.")

    return (inputFile, outputFile, palette)

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
    if fileSize == 0 or fileSize % (TILES_PER_ROW * BYTES_PER_TILE):
        sys.exit("Unrecognized input file format.")
    return (0, fileSize)

def generate_tiles(handle):
    # read NES CHR data, generate tiles (tuples of 64 2-bit ints);
    # CHR data format:
    #     - tile = 16 bytes = 2 bitplanes (first low, then high)
    #     - bitplane = 8 bytes (first = topmost)
    #     - byte = 8*1 pixels of 1 bitplane (MSB = leftmost pixel)

    bytesPerBitplane = TILE_WIDTH * TILE_HEIGHT // BITS_PER_BYTE
    (chrAddr, chrSize) = get_chr_info(handle)
    tileCount = chrSize // BYTES_PER_TILE
    handle.seek(chrAddr)

    decodedTile = []
    for i in range(tileCount):
        tile = handle.read(BYTES_PER_TILE)
        decodedTile.clear()
        for y in range(TILE_HEIGHT):
            lowBits = tile[y]
            highBits = tile[bytesPerBitplane+y] << 1
            decodedTile.extend(
                ((lowBits >> s) & 1) | ((highBits >> s) & 2)
                for s in range(TILE_WIDTH - 1, -1, -1)
            )
        yield tuple(decodedTile)

def create_image(handle, palette):
    # read CHR data from file, return image

    # get height of output image
    (chrAddr, chrSize) = get_chr_info(handle)
    imageHeight = chrSize // (TILES_PER_ROW * BYTES_PER_TILE) * TILE_HEIGHT

    # create image
    image = Image.new("P", (TILES_PER_ROW * TILE_WIDTH, imageHeight))
    image.putpalette(itertools.chain.from_iterable(palette))

    # decode CHR data and copy it to the image, one tile at a time
    tileImage = Image.new("P", (TILE_WIDTH, TILE_HEIGHT))
    for (i, tile) in enumerate(generate_tiles(handle)):
        tileImage.putdata(tile)
        (y, x) = divmod(i, TILES_PER_ROW)
        image.paste(tileImage, (x * TILE_WIDTH, y * TILE_HEIGHT))

    return image

def main():
    (inputFile, outputFile, palette) = parse_arguments()

    try:
        with open(inputFile, "rb") as handle:
            image = create_image(handle, palette)
    except OSError:
        sys.exit("Error reading input file.")

    try:
        with open(outputFile, "wb") as handle:
            handle.seek(0)
            image.save(handle, "png")
    except OSError:
        sys.exit("Error writing output file.")

main()

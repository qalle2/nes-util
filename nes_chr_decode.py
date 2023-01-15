# decode NES CHR data

# NES CHR data format:
# - byte = 1 bitplane of 8*1 pixels (most significant bit = leftmost pixel)
# - tile = 2 bitplanes of 8*8 pixels (first low bitplane top to bottom, then
#   high bitplane top to bottom)
# - pattern table = 256 tiles
# - maximum CHR data without bankswitching = 2 pattern tables

import argparse, itertools, os, struct, sys
from PIL import Image  # Pillow, https://python-pillow.org

def decode_color(color):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)

    try:
        color = int(color, 16)
        if not 0 <= color <= 0xffffff:
            raise ValueError
    except ValueError:
        sys.exit("Each color code must be 6 hexadecimal digits.")
    return (color >> 16, (color >> 8) & 0xff, color & 0xff)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert NES CHR (graphics) data into a PNG file."
    )
    parser.add_argument(
        "-p", "--palette", nargs=4,
        default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Output palette (which image colors correspond to CHR colors "
        "0-3). Four hexadecimal RRGGBB codes separated by spaces. Default: "
        "000000 555555 aaaaaa ffffff"
    )
    parser.add_argument(
        "input_file",
        help="File to read. An iNES ROM (.nes) or raw CHR data. Size of raw "
        "CHR data must be a multiple of 256 bytes (16 tiles)."
    )
    parser.add_argument(
        "output_file", help="PNG file to write. 128 pixels (16 tiles) wide."
    )
    args = parser.parse_args()

    [decode_color(c) for c in args.palette]  # validate
    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def decode_ines_header(handle):
    # parse iNES ROM header
    # (doesn't support VS System or PlayChoice-10 flags or NES 2.0 header)
    # return: None on error, otherwise (CHR ROM start address, CHR ROM size)
    # see https://www.nesdev.org/wiki/INES

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    handle.seek(0)
    (id_, prgSize, chrSize, flags6) = struct.unpack("4s3B9x", handle.read(16))

    prgSize = (prgSize if prgSize else 256) * 16 * 1024  # 0 = 256
    chrSize *= 8 * 1024
    trainerSize = bool(flags6 & 0b00000100) * 512

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
        sys.exit("Not an iNES ROM and invalid size for raw CHR data.")
    return (0, fileSize)

def generate_tiles(handle, tileCount):
    # read NES CHR data, generate tiles (tuples of 64 2-bit ints)

    decodedTile = []
    for i in range(tileCount):
        tile = handle.read(16)
        decodedTile.clear()
        for y in range(8):
            decodedTile.extend(
                ((tile[y] >> s) & 1) | (((tile[y+8] >> s) & 1) << 1)
                for s in range(7, -1, -1)
            )
        yield tuple(decodedTile)

def create_image(handle, args):
    # read CHR data from file, return image

    (chrAddr, chrSize) = get_chr_info(handle)
    tileCount = chrSize // 16  # 16 bytes/tile
    imgHeight = tileCount // 2  # 16 tiles/row, height 8 pixels/tile

    # create indexed image; get palette from command line argument
    image = Image.new("P", (16 * 8, imgHeight))
    image.putpalette(itertools.chain.from_iterable(
        decode_color(c) for c in args.palette
    ))

    # convert CHR data into image data
    handle.seek(chrAddr)
    tileImg = Image.new("P", (8, 8))
    for (i, tile) in enumerate(generate_tiles(handle, tileCount)):
        tileImg.putdata(tile)
        image.paste(tileImg, (i % 16 * 8, i // 16 * 8))

    return image

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as handle:
            image = create_image(handle, args)
    except OSError:
        sys.exit("File read error.")

    try:
        with open(args.output_file, "wb") as handle:
            handle.seek(0)
            image.save(handle, "png")
    except OSError:
        sys.exit("File write error.")

main()

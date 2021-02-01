"""Convert NES CHR data into a PNG file."""

import argparse
import itertools
import os
import struct
import sys
from PIL import Image  # Pillow

def get_ines_chr_info(handle):
    """Get (CHR_ROM_address, CHR_ROM_size) of an iNES ROM file.
    On error, return None."""

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    # extract fields from header
    handle.seek(0)
    (fileId, prgSize, chrSize, flags6, flags7) = struct.unpack("4s4B8x", handle.read(16))

    # get size of PRG ROM, CHR ROM and trainer in bytes
    prgSize = (prgSize if prgSize else 256) * 16 * 1024
    chrSize = chrSize * 8 * 1024
    trainerSize = bool(flags6 & 0x04) * 512

    # validate id and file size
    if fileId != b"NES\x1a" or fileSize < 16 + trainerSize + prgSize + chrSize:
        return None

    return (16 + trainerSize + prgSize, chrSize)

def get_chr_addr_and_size(handle):
    """Get (address, size) of CHR ROM data in file."""

    if handle.name.lower().endswith(".nes"):
        # iNES ROM
        chrInfo = get_ines_chr_info(handle)
        if chrInfo is None:
            sys.exit("Not a valid iNES ROM file.")
        if chrInfo[1] == 0:
            sys.exit("iNES ROM file has no CHR ROM.")
        return chrInfo

    # raw CHR data
    fileSize = handle.seek(0, 2)
    if fileSize == 0 or fileSize % 256:
        sys.exit("Raw CHR data file must be a multiple of 256 bytes.")
    return (0, fileSize)

def decode_tile_slice(lo, hi):
    """Decode 8*1 pixels of one tile.
    lo, hi: low/high bitplane (eight bits each)
    return: eight two-bit big-endian ints"""

    pixels = []
    for i in range(8):
        pixels.append((lo & 1) | ((hi & 1) << 1))
        lo >>= 1
        hi >>= 1
    return pixels[::-1]

def decode_pixel_rows(handle, charRowCount):
    """Generate one pixel row (128 two-bit values) per call from NES CHR data."""

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
                pixelRow.extend(decode_tile_slice(charRow[loPos], charRow[hiPos]))
            yield pixelRow

def chr_data_to_png(handle, palette):
    """Convert CHR data into a PNG image using Pillow."""

    (chrAddr, chrSize) = get_chr_addr_and_size(handle)
    charRowCount = chrSize // 256

    image = Image.new("P", (16 * 8, charRowCount * 8))
    image.putpalette(itertools.chain.from_iterable(palette))

    handle.seek(chrAddr)
    for (y, pixelRow) in enumerate(decode_pixel_rows(handle, charRowCount)):
        for (x, value) in enumerate(pixelRow):
            image.putpixel((x, y), value)

    return image

# --- main, argument parsing ----------------------------------------------------------------------

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Convert NES CHR (graphics) data into a PNG file."
    )

    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000", "555", "aaa", "fff"),
        help="Output palette (which colors correspond to CHR colors 0...3). Four color codes "
        "(hexadecimal RGB or RRGGBB) separated by spaces. Default: '000 555 aaa fff'"
    )
    parser.add_argument(
        "input_file",
        help="File to read. An iNES ROM file (extension '.nes') or raw CHR data (any other "
        "extension; size must be a multiple of 256 bytes)."
    )
    parser.add_argument(
        "output_file",
        help="PNG file to write. Always 128 pixels (16 tiles) wide."
    )

    args = parser.parse_args()

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
    return components[::-1]

def main():
    """The main function."""

    args = parse_arguments()
    palette = tuple(decode_color_code(color) for color in args.palette)

    # convert into image
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

if __name__ == "__main__":
    main()

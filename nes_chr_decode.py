"""Convert NES CHR data into a PNG file or a raw RGB data file."""

import argparse
import itertools
import os
import struct
import sys

# try to import Pillow (for PNG support)
try:
    from PIL import Image
    PILLOW_LOADED = True
except ImportError:
    PILLOW_LOADED = False

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

def chr_data_to_raw_rgb_data(source, palette, target):
    """Convert CHR data into a raw RGB data file."""

    (chrAddr, chrSize) = get_chr_addr_and_size(source)
    charRowCount = chrSize // 256

    palette = [bytes(color) for color in palette]

    source.seek(chrAddr)
    target.seek(0)
    for pixelRow in decode_pixel_rows(source, charRowCount):
        target.write(b"".join(palette[value] for value in pixelRow))

# --- main, argument parsing ----------------------------------------------------------------------

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Convert NES CHR (graphics) data into a PNG file or a raw RGB data file. PNG "
        "output requires the Pillow module. Raw RGB data files (extension '.data', three bytes "
        "per pixel) can be opened with GIMP."
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
        help="Image file to write. Always 128 pixels (16 tiles) wide. Extension must be '.png' "
        "or '.data'."
    )

    args = parser.parse_args()

    outExtension = os.path.splitext(args.output_file)[1].lower()
    if PILLOW_LOADED:
        if outExtension not in (".png", ".data"):
            sys.exit("Output file extension must be '.png' or '.data'")
    else:
        if outExtension != ".data":
            sys.exit("Pillow module not installed; output file extension must be '.data'")

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

    try:
        if args.output_file.lower().endswith(".png"):
            # convert into PNG
            with open(args.input_file, "rb") as handle:
                image = chr_data_to_png(handle, palette)
            with open(args.output_file, "wb") as handle:
                handle.seek(0)
                image.save(handle, "png")
        else:
            # convert into raw RGB data
            with open(args.input_file, "rb") as source, \
            open(args.output_file, "wb") as target:
                chr_data_to_raw_rgb_data(source, palette, target)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

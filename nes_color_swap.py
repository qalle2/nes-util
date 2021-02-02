"""Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes)."""

import argparse
import os
import sys
import struct

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes)."
    )

    parser.add_argument(
        "-c", "--colors", nargs=4, type=int, choices=range(4), default=(0, 2, 3, 1),
        help="Change original colors 0...3 to these colors. Four colors (each 0...3) "
        "separated by spaces. Default: 0 2 3 1"
    )
    parser.add_argument(
        "-f", "--first-tile", type=int, default=0,
        help="First tile to change (0 or greater, default=0)."
    )
    parser.add_argument(
        "-n", "--tile-count", type=int, default=0,
        help="Number of tiles to change. 0 (default) = all starting from --first-tile."
    )
    parser.add_argument(
        "input_file",
        help="iNES ROM file (.nes) to read."
    )
    parser.add_argument(
        "output_file",
        help="iNES ROM file (.nes) to write."
    )

    args = parser.parse_args()

    if args.first_tile < 0:
        sys.exit("--first-tile must be 0 or greater.")
    if args.tile_count < 0:
        sys.exit("--tile-count must be 0 or greater.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Target file already exists.")

    return args

def get_ines_chr_address(handle):
    """Parse an iNES header. Return CHR data address or None on error."""

    fileSize = handle.seek(0, 2)

    if fileSize < 16:
        return None

    # get fields from header
    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) = struct.unpack("4s4B8x", handle.read(16))

    # get sizes in bytes
    prgSize = (prgSize if prgSize else 256) * 16 * 1024
    chrSize = chrSize * 8 * 1024
    trainerSize = bool(flags6 & 0x04) * 512

    # validate id and file size
    if id_ != b"NES\x1a" or fileSize < 16 + trainerSize + prgSize + chrSize:
        return None

    return 16 + trainerSize + prgSize

def read_file_slice(handle, bytesLeft):
    """Generate bytesLeft bytes from file in chunks."""

    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        yield handle.read(chunkSize)
        bytesLeft -= chunkSize

def decode_tile_slice(loByte, hiByte):
    """Decode 8*1 pixels of one tile.
    loByte, hiByte: low/high bitplane (8 bits each)
    return: eight 2-bit big-endian ints"""

    pixels = []
    for i in range(8):
        pixels.append((loByte & 1) | ((hiByte & 1) << 1))
        loByte >>= 1
        hiByte >>= 1
    return pixels[::-1]

def encode_tile_slice(pixels):
    """Encode 8*1 pixels of one tile.
    pixels: eight 2-bit big-endian ints
    return: 8-bit ints: (low_bitplane, high_bitplane)"""

    loByte = hiByte = 0
    for pixel in pixels:
        loByte = (loByte << 1) | (pixel &  1)
        hiByte = (hiByte << 1) | (pixel >> 1)
    return (loByte, hiByte)

def swap_colors(chunk, colors):
    """Replace colors 0...3 in NES CHR data chunk with new colors."""

    chunk = bytearray(chunk)

    for charPos in range(0, len(chunk), 16):
        for y in range(8):
            # process 8*1 pixels of one tile
            # position of low/high bitplane (byte)
            loPos = charPos + y
            hiPos = charPos + 8 + y
            # decode pixels, replace colors, reencode pixels
            (chunk[loPos], chunk[hiPos]) = encode_tile_slice(
                colors[color] for color
                in decode_tile_slice(chunk[loPos], chunk[hiPos])
            )

    return chunk

def create_output_data(source, chrAddr, args):
    """Read input file, modify specified tiles, generate output data as chunks."""

    fileSize = source.seek(0, 2)

    # length of address range to modify and ranges before/after it
    beforeLen = chrAddr + args.first_tile * 16
    if args.tile_count:
        modifyLen = args.tile_count * 16
    else:
        modifyLen = fileSize - beforeLen
    afterLen = fileSize - beforeLen - modifyLen

    source.seek(0)

    # data before tiles to modify
    yield from read_file_slice(source, beforeLen)
    # tiles to modify
    for chunk in read_file_slice(source, modifyLen):
        yield swap_colors(chunk, args.colors)
    # data after tiles to modify
    yield from read_file_slice(source, afterLen)

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as source:
            chrAddr = get_ines_chr_address(source)
            if chrAddr is None:
                sys.exit("Invalid iNES ROM file.")

            chrSize = source.seek(0, 2) - chrAddr
            if chrSize == 0:
                sys.exit("Input file has no CHR ROM.")
            if args.first_tile * 16 >= chrSize:
                sys.exit("--first-tile is too large.")
            if args.tile_count and (args.first_tile + args.tile_count) * 16 > chrSize:
                sys.exit("Sum of --first-tile and --tile-count is too large.")

            # copy input file to output file
            try:
                with open(args.output_file, "wb") as target:
                    target.seek(0)
                    for chunk in create_output_data(source, chrAddr, args):
                        target.write(chunk)
            except OSError:
                sys.exit("Error copying data.")
    except OSError:
        sys.exit("Error reading input file.")

if __name__ == "__main__":
    main()

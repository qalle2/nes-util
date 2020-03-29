"""Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes)."""

import argparse
import os
import sys
import ineslib

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-l", "--colors", nargs=4, type=int, choices=range(4), default=(0, 2, 3, 1),
        help="Change original colors 0-3 to these colors."
    )
    parser.add_argument(
        "-f", "--first-tile", type=int, default=0, help="The first tile to change (0 or greater)."
    )
    parser.add_argument(
        "-c", "--tile-count", type=int, default=0,
        help="The number of tiles to change (0 = all starting from --first-tile)."
    )
    parser.add_argument("input_file", help="The iNES ROM file (.nes) to read.")
    parser.add_argument("output_file", help="The iNES ROM file (.nes) to write.")

    args = parser.parse_args()

    if args.first_tile < 0:
        sys.exit("The first tile to change must be 0 or greater.")
    if args.tile_count < 0:
        sys.exit("The number of tiles to change must be 0 or greater.")
    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Target file already exists.")

    return args

def read_file(source, bytesLeft):
    """Read a part of a file starting from current position. Yield one chunk per call."""

    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        yield source.read(chunkSize)
        bytesLeft -= chunkSize

def decode_character_slice(LSBs, MSBs):
    """Decode 8*1 pixels of one character.
    LSBs: integer with 8 less significant bits
    MSBs: integer with 8 more significant bits
    return: iterable of 8 2-bit big-endian integers"""

    MSBs <<= 1
    return (((LSBs >> shift) & 1) | ((MSBs >> shift) & 2) for shift in range(7, -1, -1))

def encode_character_slice(indexedPixels):
    """Encode 8*1 pixels of one character.
    in: iterable of 8 2-bit integers
    return: (integer with 8 less significant bits, integer with 8 more significant bits)"""

    LSBs = sum((indexedPixels[i] & 1) << (7 - i) for i in range(8))
    MSBs = sum((indexedPixels[i] >> 1) << (7 - i) for i in range(8))
    return (LSBs, MSBs)

def swap_colors(chunk, outputColors):
    """Replace colors 0-3 in NES CHR data chunk with outputColors."""

    chunk = bytearray(chunk)
    # process one slice (8*1 pixels of one character) at a time
    for charPos in range(0, len(chunk), 16):
        for pixelY in range(8):
            # position of less/more significant bitplane (byte)
            LSBytePos = charPos + pixelY
            MSBytePos = charPos + 8 + pixelY
            # decode pixels into 2-bit integers, replace colors, reencode
            slice_ = decode_character_slice(chunk[LSBytePos], chunk[MSBytePos])
            slice_ = tuple(outputColors[color] for color in slice_)
            (chunk[LSBytePos], chunk[MSBytePos]) = encode_character_slice(slice_)
    return chunk

def process_file(source, target, args):
    """Make a copy of an iNES ROM file with modified CHR data."""

    inputFileSize = source.seek(0, 2)
    if inputFileSize < 16:
        sys.exit("The input file is smaller than an iNES header.")

    try:
        fileInfo = ineslib.parse_iNES_header(source)
    except Exception as e:
        sys.exit("Error: " + str(e))
    (PRGSize, CHRSize) = (fileInfo["PRGSize"], fileInfo["CHRSize"])

    if CHRSize == 0:
        sys.exit("The input file has no CHR ROM.")

    # validate the range of tiles to modify
    totalTileCount = CHRSize // 16
    if args.first_tile > totalTileCount - 1:
        sys.exit('The "first tile" argument is too large.')
    if args.tile_count == 0:
        tileCount = totalTileCount - args.first_tile
    else:
        tileCount = args.tile_count
        if args.first_tile + tileCount > totalTileCount:
            sys.exit('The sum of "first tile" and "tile count" arguments is too large.')

    # copy header, PRG ROM and possibly start of CHR ROM verbatim
    source.seek(0)
    target.seek(0)
    for chunk in read_file(source, 16 + PRGSize + args.first_tile * 16):
        target.write(chunk)
    # copy and modify some or all of CHR ROM data
    for chunk in read_file(source, tileCount * 16):
        target.write(swap_colors(chunk, args.colors))
    # possibly copy the rest of CHR ROM verbatim
    for chunk in read_file(source, (totalTileCount - args.first_tile - tileCount) * 16):
        target.write(chunk)

def main():
    """The main function."""

    if sys.version_info[0] != 3:
        print("Warning: possibly incompatible Python version.", file=sys.stderr)

    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as source, open(args.output_file, "wb") as target:
            process_file(source, target, args)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

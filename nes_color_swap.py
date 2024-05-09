import argparse, os, struct, sys

def parse_arguments():
    # parse command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Swap colors in the graphics data (CHR ROM) of an iNES "
        "ROM file (.nes)."
    )
    parser.add_argument(
        "-c", "--colors", nargs=4, type=int, choices=range(4),
        default=(0, 2, 3, 1),
        help="Change original colors 0...3 to these colors. Four colors "
        "(each 0...3) separated by spaces. Default: 0 2 3 1"
    )
    parser.add_argument(
        "-f", "--first-tile", type=int, default=0,
        help="First tile to change (0 or greater, default=0)."
    )
    parser.add_argument(
        "-n", "--tile-count", type=int, default=0,
        help="Number of tiles to change. 0 (default) = all starting from "
        "--first-tile."
    )
    parser.add_argument(
        "input_file", help="iNES ROM file (.nes) to read."
    )
    parser.add_argument(
        "output_file", help="iNES ROM file (.nes) to write."
    )
    args = parser.parse_args()

    if args.first_tile < 0:
        sys.exit("--first-tile must be 0 or greater.")
    if args.tile_count < 0:
        sys.exit("--tile-count must be 0 or greater.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def ines_header_decode(handle):
    # Parse the header of an iNES ROM file.
    # See https://www.nesdev.org/wiki/INES
    # Note: doesn't support VS System or PlayChoice-10 flags or NES 2.0 header.
    # handle: iNES ROM file
    # return: tuple: (CHR_ROM_address, CHR_ROM_size)

    fileSize = handle.seek(0, 2)

    if fileSize < 16:
        sys.exit("Not an iNES ROM file.")

    # get fields from header
    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) = struct.unpack(
        "4s4B8x", handle.read(16)
    )

    if id_ != b"NES\x1a":
        sys.exit("Not an iNES ROM file.")

    # PRG ROM / CHR ROM / trainer size in bytes (PRG ROM size 0 -> 256)
    prgSize = (prgSize if prgSize else 256) * 16 * 1024
    chrSize = chrSize * 8 * 1024
    trainerSize = bool(flags6 & 0b00000100) * 512

    # validate id and file size (accept files that are too large)
    if fileSize < 16 + trainerSize + prgSize + chrSize:
        sys.exit("Unexpected end of iNES ROM file.")

    chrStart = 16 + trainerSize + prgSize
    return (chrStart, chrSize)

def read_file_slice(handle, bytesLeft):
    # generate bytesLeft bytes from file
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        yield handle.read(chunkSize)
        bytesLeft -= chunkSize

def tile_slice_decode(loByte, hiByte):
    # decode 8*1 pixels of one tile of CHR data;
    # loByte, hiByte: low/high bitplane (both 8-bit ints);
    # return: eight 2-bit ints
    pixels = []
    for i in range(8):
        pixels.append((loByte & 1) | ((hiByte & 1) << 1))
        loByte >>= 1
        hiByte >>= 1
    return pixels[::-1]

def tile_slice_encode(pixels):
    # encode 8*1 pixels of one tile of CHR data;
    # pixels: eight 2-bit ints
    # return: (low_bitplane, high_bitplane); both 8-bit ints
    loByte = hiByte = 0
    for pixel in pixels:
        loByte = (loByte << 1) | (pixel &  1)
        hiByte = (hiByte << 1) | (pixel >> 1)
    return (loByte, hiByte)

def swap_colors(chunk, colors):
    # replace colors 0-3 in CHR data chunk (16n bytes) with new colors (4 ints)

    chunk = bytearray(chunk)

    for charPos in range(0, len(chunk), 16):
        for pixelY in range(8):
            # process 8*1 pixels of one tile
            # position of low/high bitplane (byte)
            loPos = charPos + pixelY
            hiPos = charPos + 8 + pixelY
            # decode pixels, replace colors, reencode pixels
            (chunk[loPos], chunk[hiPos]) = tile_slice_encode(
                colors[color] for color
                in tile_slice_decode(chunk[loPos], chunk[hiPos])
            )

    return chunk

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as source:
            # get file info
            (chrStart, chrSize) = ines_header_decode(source)
            if chrSize == 0:
                sys.exit("Input file has no CHR ROM.")

            # length of CHR data before the tiles to modify
            beforeLen = args.first_tile * 16
            if beforeLen >= chrSize:
                sys.exit("--first-tile is too large.")

            # length of CHR data at/after the tiles to modify
            if args.tile_count:
                modifyLen = args.tile_count * 16
                afterLen = chrSize - beforeLen - modifyLen
                if afterLen < 0:
                    sys.exit(
                        "Sum of --first-tile and --tile-count is too large."
                    )
            else:
                afterLen = 0
                modifyLen = chrSize - beforeLen - afterLen

            # copy input file to output file
            source.seek(0)
            with open(args.output_file, "wb") as target:
                target.seek(0)
                # copy data before/at/after the tiles to be modified
                for chunk in read_file_slice(
                    source, chrStart + beforeLen
                ):
                    target.write(chunk)
                for chunk in read_file_slice(source, modifyLen):
                    target.write(swap_colors(chunk, args.colors))
                for chunk in read_file_slice(source, afterLen):
                    target.write(chunk)
    except OSError:
        sys.exit("Error reading/writing files.")

main()

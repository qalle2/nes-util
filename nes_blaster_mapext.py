"""Extract world maps from Blaster Master ROM to PNGs.
Source: http://bck.sourceforge.net/blastermaster.txt
(I actually figured out most of the info myself before I found that document.)
TODO: clean up (pylint complains)
Note: tank view of world 4 is different between US/JP versions (ultra-subblocks seem identical,
but subblocks, blocks and map differ).
"""

import argparse
import itertools
import os
import sys
from PIL import Image
import ineslib
import neslib

# addresses of maps: (16-KiB PRG ROM bank, pointer address within PRG ROM bank, 4-KiB CHR ROM bank)
# note: JP version uses PRG bank 4 instead of 2
MAP_DATA_ADDRESSES = {
    0: (0, 0 * 4, 8),
    1: (0, 1 * 4, 9),
    2: (0, 2 * 4, 10),
    3: (0, 3 * 4, 11),
    4: (0, 4 * 4, 12),
    5: (1, 0 * 4, 13),
    6: (1, 1 * 4, 14),
    7: (1, 2 * 4, 15),
    8: (1, 3 * 4, 17),
    9: (2, 1 * 4, 19),
    10: (1, 4 * 4, 18),
    11: (2, 4 * 4, 20),
    12: (2, 0 * 4, 18),
    13: (2, 2 * 4, 19),
    14: (2, 5 * 4, 20),
    15: (2, 3 * 4, 17),
}

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Extract world maps from NES Blaster Master to PNG files."
    )

    parser.add_argument(
        "-j", "--japan", action="store_true",
        help="Input file is Japanese version (Chou-Wakusei Senki - MetaFight)."
    )
    parser.add_argument(
        "-m", "--map", type=int, default=0,
        help="Map to extract: 0-7=tank view of area 1-8, 8-15=overhead view of area 1-8. Default=0."
    )
    parser.add_argument("--usb", help="Save ultra-subblocks as PNG file (256*256 px).")
    parser.add_argument("--sb", help="Save subblocks as PNG file (512*512 px).")
    parser.add_argument("--blocks", help="Save blocks as PNG file (1024*1024 px).")
    parser.add_argument(
        "input_file",
        help="Blaster Master ROM file in iNES format (.nes, US/US prototype/EUR/JP; see also "
        "--japan)."
    )
    parser.add_argument("output_file", help="The PNG image file to write.")

    args = parser.parse_args()

    if not 0 <= args.map <= 15:
        sys.exit("Invalid map number.")
    if args.usb is not None and os.path.exists(args.usb):
        sys.exit("USB output file already exists.")
    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

# --------------------------------------------------------------------------------------------------

def is_blaster_master(fileInfo):
    """Is the file likely Blaster Master? (Don't validate too accurately because the file may be
    a hack.)
    fileInfo: from ineslib.parse_iNES_header()"""

    return (
        fileInfo["PRGSize"] == 128 * 1024
        and fileInfo["CHRSize"] == 128 * 1024
        and fileInfo["mapper"] == 1
    )

def decode_offset(bytes_):
    """Decode address, convert into offset within bank."""

    addr = bytes_[0] | bytes_[1] << 8  # decode little-endian unsigned short
    assert 0x8000 <= addr <= 0xbfff
    return addr & 0x3fff  # convert into offset

# --- image creation - ultra-subblocks -------------------------------------------------------------

def create_image_palette(image, NESColors):
    """Add NES colors to Pillow Image palette.
    return: table for converting NESColors index into image palette index"""

    RGBPalette = sorted(set(neslib.PALETTE[color] for color in NESColors))
    image.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...
    return tuple(RGBPalette.index(neslib.PALETTE[color]) for color in NESColors)

def get_pixel_coords(USBIndex, tileIndex, pixelIndex):
    """Get target coordinates for pixel in ultra-subblock image."""

    x = USBIndex << 4 & 0xf0 | tileIndex << 3 & 0x08 | pixelIndex & 0x07
    y = USBIndex & 0xf0 | tileIndex << 2 & 0x08 | pixelIndex >> 3
    return (x, y)

def create_ultra_subblock_image(USBData, USBAttrData, tileData, worldPalette):
    """Create Pillow Image with 16 * 16 ultra-subblocks, each 16 * 16 pixels."""

    image = Image.new("P", (16 * 16, 16 * 16), 0)  # indexed color
    worldPalToImgPal = create_image_palette(image, worldPalette)

    # for each USB, draw 2 * 2 tiles with correct palette
    for (USBIndex, USBTiles) in enumerate(USBData):
        paletteMask = USBAttrData[USBIndex] << 2 & 0x0c  # 2 LSBs in attrs = subpalette
        for (tileIndex, tile) in enumerate(USBTiles):
            for (pixelIndex, pixel) in enumerate(tileData[tile]):
                color = worldPalToImgPal[paletteMask | pixel]
                image.putpixel(get_pixel_coords(USBIndex, tileIndex, pixelIndex), color)
    return image

# --- image creation - subblocks, blocks, map ------------------------------------------------------

def set_image_palette(image, NESColors):
    """Add NES colors to Pillow Image palette."""

    RGBPalette = sorted(set(neslib.PALETTE[color] for color in NESColors))
    image.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...

def get_ultra_subblock_image_coords(USB):
    """Get source coordinates for ultra-subblock in ultra-subblock image."""

    x = USB << 4 & 0xf0
    y = USB & 0xf0
    return (x, y, x + 16, y + 16)

def get_subblock_image_coords(SBIndex, USBIndex):
    """Get target coordinates for ultra-subblock in subblock image."""

    x = SBIndex << 5 & 0x1e0 | USBIndex << 4 & 0x10
    y = SBIndex << 1 & 0x1e0 | USBIndex << 3 & 0x10
    return (x, y)

def create_subblock_image(SBData, USBImg, worldPalette):
    """Create Pillow Image with 16 * 16 subblocks, each 32 * 32 pixels."""

    outImg = Image.new("P", (16 * 32, 16 * 32), 0)  # indexed color
    set_image_palette(outImg, worldPalette)

    for (SBIndex, USBs) in enumerate(SBData):
        for (USBIndex, USB) in enumerate(USBs):
            # copy USB from another image
            inImg = USBImg.crop(get_ultra_subblock_image_coords(USB))
            outImg.paste(inImg, get_subblock_image_coords(SBIndex, USBIndex))
    return outImg

def get_block_image_coords(blockIndex, SBIndex, USBIndex):
    """Get target coordinates for ultra-subblock in block image."""

    x = blockIndex << 6 & 0x3c0 | SBIndex << 5 & 0x20 | USBIndex << 4 & 0x10
    y = blockIndex << 2 & 0x3c0 | SBIndex << 4 & 0x20 | USBIndex << 3 & 0x10
    return (x, y)

def create_block_image(blockData, SBData, USBImg, worldPalette):
    """Create Pillow Image with 16 * 16 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (16 * 64, 16 * 64), 0)  # indexed color
    set_image_palette(outImg, worldPalette)

    for (blockIndex, SBs) in enumerate(blockData):
        for (SBIndex, SB) in enumerate(SBs):
            for (USBIndex, USB) in enumerate(SBData[SB]):
                # copy USB from another image
                inImg = USBImg.crop(get_ultra_subblock_image_coords(USB))
                outImg.paste(inImg, get_block_image_coords(blockIndex, SBIndex, USBIndex))
    return outImg

def get_map_image_coords(blockIndex, SBIndex, USBIndex):
    """Get target coordinates for ultra-subblock in map image."""

    x = blockIndex << 6 & 0x7c0 | SBIndex << 5 & 0x20 | USBIndex << 4 & 0x10
    y = blockIndex << 1 & 0x7c0 | SBIndex << 4 & 0x20 | USBIndex << 3 & 0x10
    return (x, y)

def create_map_image(mapData, blockData, SBData, USBImg, worldPalette):
    """Create Pillow Image of entire map with 32 * 32 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (32 * 64, len(mapData) * 2), 0)  # indexed color
    set_image_palette(outImg, worldPalette)

    # world = 32*? blocks, block = 2*2 subblocks, subblock = 2*2 ultra-subblocks,
    # ultra-subblock = 2*2 tiles, tile = 8*8 pixels
    for (blockIndex, block) in enumerate(mapData):
        for (SBIndex, SB) in enumerate(blockData[block]):
            for (USBIndex, USB) in enumerate(SBData[SB]):
                # copy USB from another image
                inImg = USBImg.crop(get_ultra_subblock_image_coords(USB))
                outImg.paste(inImg, get_map_image_coords(blockIndex, SBIndex, USBIndex))
    return outImg

# --------------------------------------------------------------------------------------------------

def convert_map(sourceHnd, args):
    """Convert one map into PNG."""

    # parse iNES header
    try:
        fileInfo = ineslib.parse_iNES_header(sourceHnd)
    except ineslib.iNESError as error:
        sys.exit("iNES error: " + str(error))

    if not is_blaster_master(fileInfo):
        sys.exit("The file doesn't look like Blaster Master.")

    (PRGBank, worldPtr, CHRBank) = MAP_DATA_ADDRESSES[args.map]
    PRGBank = 4 if PRGBank == 2 and args.japan else PRGBank  # the only version difference
    scrollPtr = worldPtr + 2

    print(f"Map: {args.map:d}")
    print(f"Banks: PRG (16 KiB) = {PRGBank:d}, CHR (4 KiB) = {CHRBank:d}")
    print(f"Pointer offsets within PRG bank: world=0x{worldPtr:04x}, scroll=0x{scrollPtr:04x}")

    # read PRG bank data
    sourceHnd.seek(16 + fileInfo["trainerSize"] + PRGBank * 16 * 1024)
    PRGBankData = sourceHnd.read(16 * 1024)

    # After the pointers, the order of data sections varies.
    # The first ones are always: palette, ultra-subblocks, subblocks, blocks, map.
    # The last two are USB attributes and scroll, in either order.

    worldAddr = decode_offset(PRGBankData[worldPtr:worldPtr+2])
    scrollAddr = decode_offset(PRGBankData[scrollPtr:scrollPtr+2])
    print(f"Data offsets within PRG ROM bank: world=0x{worldAddr:04x}, scroll=0x{scrollAddr:04x}")

    palAddr = decode_offset(PRGBankData[worldAddr+0:worldAddr+0+2])
    USBAttrAddr = decode_offset(PRGBankData[worldAddr+2:worldAddr+2+2])
    USBAddr = decode_offset(PRGBankData[worldAddr+4:worldAddr+4+2])
    SBAddr = decode_offset(PRGBankData[worldAddr+6:worldAddr+6+2])
    blockAddr = decode_offset(PRGBankData[worldAddr+8:worldAddr+8+2])
    mapAddr = decode_offset(PRGBankData[worldAddr+10:worldAddr+10+2])

    print(
        "World data section offsets within PRG bank: "
        f"palette=0x{palAddr:04x}, "
        f"ultra-subblocks=0x{USBAddr:04x}, "
        f"subblocks=0x{SBAddr:04x}, "
        f"blocks=0x{blockAddr:04x}, "
        f"map=0x{mapAddr:04x}, "
        f"ultra-subblock attributes = 0x{USBAttrAddr:04x}"
    )

    # read this world's palette (always 4*4 bytes, contains duplicate NES colors)
    worldPalette = PRGBankData[palAddr:palAddr+16]

    # read ultra-subblock data
    assert SBAddr - USBAddr in range(4, 256 * 4, 4)
    USBData = tuple(PRGBankData[i:i+4] for i in range(USBAddr, SBAddr, 4))

    # read subblock data
    assert blockAddr - SBAddr in range(4, 256 * 4, 4)
    SBData = tuple(PRGBankData[i:i+4] for i in range(SBAddr, blockAddr, 4))
    assert max(itertools.chain.from_iterable(SBData)) < len(USBData)

    # read block data
    assert mapAddr - blockAddr in range(4, 256 * 4, 4)
    blockData = tuple(PRGBankData[i:i+4] for i in range(blockAddr, mapAddr, 4))
    assert max(itertools.chain.from_iterable(blockData)) < len(SBData)

    # read map data
    mapEnd = min(USBAttrAddr, scrollAddr)
    assert mapEnd - mapAddr in range(32, 32 * 32 + 1, 32)
    mapData = PRGBankData[mapAddr:mapEnd]
    assert max(set(mapData)) < len(blockData)

    # read ultra-subblock attribute data (1 byte/ultra-subblock)
    if USBAttrAddr <= scrollAddr < USBAttrAddr + len(USBData):
        # map 3 of JP version
        print("Warning: scroll data overlaps with ultra-subblock attribute data.", file=sys.stderr)
    USBAttrData = PRGBankData[USBAttrAddr:USBAttrAddr+len(USBData)]

    # read and decode tile data
    sourceHnd.seek(16 + fileInfo["trainerSize"] + fileInfo["PRGSize"] + CHRBank * 4 * 1024)
    CHRBankData = sourceHnd.read(4 * 1024)
    tileData = tuple(neslib.decode_tile(CHRBankData[i*16:(i+1)*16]) for i in range(256))

    # create image with ultra-subblocks, optionally save
    USBImg = create_ultra_subblock_image(USBData, USBAttrData, tileData, worldPalette)
    if args.usb is not None:
        with open(args.usb, "wb") as target:
            USBImg.save(target)

    # optionally create and save image with subblocks
    if args.sb is not None:
        SBImg = create_subblock_image(SBData, USBImg, worldPalette)
        with open(args.sb, "wb") as target:
            SBImg.save(target)

    # optionally create and save image with blocks
    if args.blocks is not None:
        blockImg = create_block_image(blockData, SBData, USBImg, worldPalette)
        with open(args.blocks, "wb") as target:
            blockImg.save(target)

    # create main output image and save it
    mapImg = create_map_image(mapData, blockData, SBData, USBImg, worldPalette)
    with open(args.output_file, "wb") as target:
        target.seek(0)
        mapImg.save(target)

# --------------------------------------------------------------------------------------------------

def main():
    """The main function."""

    args = parse_arguments()
    try:
        with open(args.input_file, "rb") as sourceHnd:
            convert_map(sourceHnd, args)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()

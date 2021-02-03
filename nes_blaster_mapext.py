"""Extract world maps from Blaster Master ROM to PNGs.
Source: http://bck.sourceforge.net/blastermaster.txt
(I actually figured out most of the info myself before I found that document.)
Note: tank view of world 4 is different between US/JP versions (ultra-subblocks seem identical,
but subblocks, blocks and map differ).
"""

import argparse
import itertools
import os
import sys
from PIL import Image  # Pillow, https://python-pillow.org
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

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
    fileInfo: from qneslib.ines_header_decode()"""

    return (
        fileInfo["prgSize"] == 128 * 1024
        and fileInfo["chrSize"] == 128 * 1024
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

def get_pixel_coords(usbIndex, tileIndex, pixelIndex):
    """Get target coordinates for pixel in ultra-subblock image."""

    x = usbIndex << 4 & 0xf0 | tileIndex << 3 & 0x08 | pixelIndex & 0x07
    y = usbIndex & 0xf0 | tileIndex << 2 & 0x08 | pixelIndex >> 3
    return (x, y)

def create_ultra_subblock_image(usbData, usbAttrData, tileData, worldPalette):
    """Create Pillow Image with 16 * 16 ultra-subblocks, each 16 * 16 pixels."""

    image = Image.new("P", (16 * 16, 16 * 16), 0)  # indexed color
    worldPalToImgPal = create_image_palette(image, worldPalette)

    # for each USB, draw 2 * 2 tiles with correct palette
    for (usbIndex, usbTiles) in enumerate(usbData):
        paletteMask = usbAttrData[usbIndex] << 2 & 0x0c  # 2 LSBs in attrs = subpalette
        for (tileIndex, tile) in enumerate(usbTiles):
            for (pixelIndex, pixel) in enumerate(tileData[tile]):
                color = worldPalToImgPal[paletteMask | pixel]
                image.putpixel(get_pixel_coords(usbIndex, tileIndex, pixelIndex), color)
    return image

# --- image creation - subblocks, blocks, map ------------------------------------------------------

def set_image_palette(image, NESColors):
    """Add NES colors to Pillow Image palette."""

    RGBPalette = sorted(set(neslib.PALETTE[color] for color in NESColors))
    image.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...

def get_ultra_subblock_image_coords(usb):
    """Get source coordinates for ultra-subblock in ultra-subblock image."""

    x = usb << 4 & 0xf0
    y = usb & 0xf0
    return (x, y, x + 16, y + 16)

def get_subblock_image_coords(sbIndex, usbIndex):
    """Get target coordinates for ultra-subblock in subblock image."""

    x = sbIndex << 5 & 0x1e0 | usbIndex << 4 & 0x10
    y = sbIndex << 1 & 0x1e0 | usbIndex << 3 & 0x10
    return (x, y)

def create_subblock_image(sbData, usbImg, worldPalette):
    """Create Pillow Image with 16 * 16 subblocks, each 32 * 32 pixels."""

    outImg = Image.new("P", (16 * 32, 16 * 32), 0)  # indexed color
    set_image_palette(outImg, worldPalette)

    for (sbIndex, usbs) in enumerate(sbData):
        for (usbIndex, usb) in enumerate(usbs):
            # copy USB from another image
            inImg = usbImg.crop(get_ultra_subblock_image_coords(usb))
            outImg.paste(inImg, get_subblock_image_coords(sbIndex, usbIndex))
    return outImg

def get_block_image_coords(blockIndex, sbIndex, usbIndex):
    """Get target coordinates for ultra-subblock in block image."""

    x = blockIndex << 6 & 0x3c0 | sbIndex << 5 & 0x20 | usbIndex << 4 & 0x10
    y = blockIndex << 2 & 0x3c0 | sbIndex << 4 & 0x20 | usbIndex << 3 & 0x10
    return (x, y)

def create_block_image(blockData, sbData, usbImg, worldPalette):
    """Create Pillow Image with 16 * 16 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (16 * 64, 16 * 64), 0)  # indexed color
    set_image_palette(outImg, worldPalette)

    for (blockIndex, sbs) in enumerate(blockData):
        for (sbIndex, sb) in enumerate(sbs):
            for (usbIndex, usb) in enumerate(sbData[sb]):
                # copy USB from another image
                inImg = usbImg.crop(get_ultra_subblock_image_coords(usb))
                outImg.paste(inImg, get_block_image_coords(blockIndex, sbIndex, usbIndex))
    return outImg

def get_map_image_coords(blockIndex, sbIndex, usbIndex):
    """Get target coordinates for ultra-subblock in map image."""

    x = blockIndex << 6 & 0x7c0 | sbIndex << 5 & 0x20 | usbIndex << 4 & 0x10
    y = blockIndex << 1 & 0x7c0 | sbIndex << 4 & 0x20 | usbIndex << 3 & 0x10
    return (x, y)

def create_map_image(mapData, blockData, sbData, usbImg, worldPalette):
    """Create Pillow Image of entire map with 32 * 32 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (32 * 64, len(mapData) * 2), 0)  # indexed color
    set_image_palette(outImg, worldPalette)

    # world = 32*? blocks, block = 2*2 subblocks, subblock = 2*2 ultra-subblocks,
    # ultra-subblock = 2*2 tiles, tile = 8*8 pixels
    for (blockIndex, block) in enumerate(mapData):
        for (sbIndex, sb) in enumerate(blockData[block]):
            for (usbIndex, usb) in enumerate(sbData[sb]):
                # copy USB from another image
                inImg = usbImg.crop(get_ultra_subblock_image_coords(usb))
                outImg.paste(inImg, get_map_image_coords(blockIndex, sbIndex, usbIndex))
    return outImg

# --------------------------------------------------------------------------------------------------

def decode_tile(data):
    """Decode an NES tile.
    data: 16 bytes
    return: 64 2-bit big-endian integers"""

    data = []
    for (loByte, hiByte) in zip(data[0:8], data[8:16]):
        data.extend(tile_slice_decode(loByte, hiByte))
    return tuple(data)

def convert_map(sourceHnd, args):
    """Convert one map into PNG."""

    # parse iNES header
    try:
        fileInfo = qneslib.parse_ines_header(sourceHnd)
    except ineslib.iNESError as error:
        sys.exit("iNES error: " + str(error))

    if not is_blaster_master(fileInfo):
        sys.exit("The file doesn't look like Blaster Master.")

    (prgBank, worldPtr, chrBank) = MAP_DATA_ADDRESSES[args.map]
    prgBank = 4 if prgBank == 2 and args.japan else prgBank  # the only version difference
    scrollPtr = worldPtr + 2

    print(f"Map: {args.map:d}")
    print(f"Banks: PRG (16 KiB) = {prgBank:d}, CHR (4 KiB) = {chrBank:d}")
    print(f"Pointer offsets within PRG bank: world=0x{worldPtr:04x}, scroll=0x{scrollPtr:04x}")

    # read PRG bank data
    sourceHnd.seek(fileInfo["prgStart"] + prgBank * 16 * 1024)
    prgBankData = sourceHnd.read(16 * 1024)

    # After the pointers, the order of data sections varies.
    # The first ones are always: palette, ultra-subblocks, subblocks, blocks, map.
    # The last two are USB attributes and scroll, in either order.

    worldAddr = decode_offset(prgBankData[worldPtr:worldPtr+2])
    scrollAddr = decode_offset(prgBankData[scrollPtr:scrollPtr+2])
    print(f"Data offsets within PRG ROM bank: world=0x{worldAddr:04x}, scroll=0x{scrollAddr:04x}")

    palAddr = decode_offset(prgBankData[worldAddr+0:worldAddr+0+2])
    usbAttrAddr = decode_offset(prgBankData[worldAddr+2:worldAddr+2+2])
    usbAddr = decode_offset(prgBankData[worldAddr+4:worldAddr+4+2])
    sbAddr = decode_offset(prgBankData[worldAddr+6:worldAddr+6+2])
    blockAddr = decode_offset(prgBankData[worldAddr+8:worldAddr+8+2])
    mapAddr = decode_offset(prgBankData[worldAddr+10:worldAddr+10+2])

    print(
        "World data section offsets within PRG bank: "
        f"palette=0x{palAddr:04x}, "
        f"ultra-subblocks=0x{usbAddr:04x}, "
        f"subblocks=0x{sbAddr:04x}, "
        f"blocks=0x{blockAddr:04x}, "
        f"map=0x{mapAddr:04x}, "
        f"ultra-subblock attributes = 0x{usbAttrAddr:04x}"
    )

    # read this world's palette (always 4*4 bytes, contains duplicate NES colors)
    worldPalette = prgBankData[palAddr:palAddr+16]

    # read ultra-subblock data
    assert sbAddr - usbAddr in range(4, 256 * 4, 4)
    usbData = tuple(prgBankData[i:i+4] for i in range(usbAddr, sbAddr, 4))

    # read subblock data
    assert blockAddr - sbAddr in range(4, 256 * 4, 4)
    sbData = tuple(prgBankData[i:i+4] for i in range(sbAddr, blockAddr, 4))
    assert max(itertools.chain.from_iterable(sbData)) < len(usbData)

    # read block data
    assert mapAddr - blockAddr in range(4, 256 * 4, 4)
    blockData = tuple(prgBankData[i:i+4] for i in range(blockAddr, mapAddr, 4))
    assert max(itertools.chain.from_iterable(blockData)) < len(sbData)

    # read map data
    mapEnd = min(usbAttrAddr, scrollAddr)
    assert mapEnd - mapAddr in range(32, 32 * 32 + 1, 32)
    mapData = prgBankData[mapAddr:mapEnd]
    assert max(set(mapData)) < len(blockData)

    # read ultra-subblock attribute data (1 byte/ultra-subblock)
    if usbAttrAddr <= scrollAddr < usbAttrAddr + len(usbData):
        # map 3 of JP version
        print("Warning: scroll data overlaps with ultra-subblock attribute data.", file=sys.stderr)
    usbAttrData = prgBankData[usbAttrAddr:usbAttrAddr+len(usbData)]

    # read and decode tile data
    sourceHnd.seek(fileInfo["chrStart"] + chrBank * 4 * 1024)
    chrBankData = sourceHnd.read(4 * 1024)
    tileData = tuple(decode_tile(chrBankData[i*16:(i+1)*16]) for i in range(256))

    # create image with ultra-subblocks, optionally save
    usbImg = create_ultra_subblock_image(usbData, usbAttrData, tileData, worldPalette)
    if args.usb is not None:
        with open(args.usb, "wb") as target:
            usbImg.save(target)

    # optionally create and save image with subblocks
    if args.sb is not None:
        sbImg = create_subblock_image(sbData, usbImg, worldPalette)
        with open(args.sb, "wb") as target:
            sbImg.save(target)

    # optionally create and save image with blocks
    if args.blocks is not None:
        blockImg = create_block_image(blockData, sbData, usbImg, worldPalette)
        with open(args.blocks, "wb") as target:
            blockImg.save(target)

    # create main output image and save it
    mapImg = create_map_image(mapData, blockData, sbData, usbImg, worldPalette)
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

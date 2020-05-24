"""Extract world maps from Blaster Master US ROM to PNGs.
Source: http://bck.sourceforge.net/blastermaster.txt
(I actually figured out most of the info myself before I found that document.)
TODO: clean up (pylint complains)"""

import argparse
import itertools
import os
import sys
from PIL import Image
import ineslib
import neslib

# addresses of maps: (16-KiB PRG ROM bank, pointer offset within PRG ROM bank, 4-KiB CHR ROM bank)
MAP_DATA_ADDRESSES = (
    # area 1-8 side view
    (0, 0 * 4, 8),
    (0, 1 * 4, 9),
    (0, 2 * 4, 10),
    (0, 3 * 4, 11),
    (0, 4 * 4, 12),
    (1, 0 * 4, 13),
    (1, 1 * 4, 14),
    (1, 2 * 4, 15),
    # area 1-8 top view
    (1, 3 * 4, 17),
    (2, 1 * 4, 19),
    (1, 4 * 4, 18),
    (2, 4 * 4, 20),
    (2, 0 * 4, 18),
    (2, 2 * 4, 19),
    (2, 5 * 4, 20),
    (2, 3 * 4, 17),
)

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Extract world maps from NES Blaster Master to PNG files."
    )

    parser.add_argument(
        "-m", "--map", type=int, default=0,
        help="Map to extract: 0-7=side view of area 1-8, 8-15=top view of area 1-8. Default=0."
    )
    parser.add_argument("--usb", help="Save ultra-subblocks as a PNG file (256*256 px).")
    parser.add_argument("--sb", help="Save subblocks as a PNG file (512*512 px).")
    parser.add_argument("--blocks", help="Save blocks as a PNG file (1024*1024 px).")
    parser.add_argument(
        "input_file", help="The Blaster Master ROM file in iNES format (.nes, US version)."
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

def is_blaster_master(fileInfo):
    """Is the file likely Blaster Master (US)?
    fileInfo: from ineslib.parse_iNES_header()"""

    return (
        fileInfo["PRGSize"] == 128 * 1024
        and fileInfo["CHRSize"] == 128 * 1024
        and fileInfo["mapper"] == 1
        and fileInfo["mirroring"] == "horizontal"
        and not fileInfo["saveRAM"]
    )

def decode_offset(bytes_):
    """Decode address, convert into offset within bank."""

    addr = bytes_[0] + bytes_[1] * 0x100  # decode little-endian unsigned short
    if not 0x8000 <= addr <= 0xbfff:
        sys.exit("Invalid address.")
    return addr & 0x3fff  # convert into offset

def find_ranges(values):
    """Generate ranges from values. E.g. [0, 1, 5] -> range(0, 2), range(5, 6)."""

    rangeStart = None

    for value in sorted(values):
        if rangeStart is None or value > prevValue + 1:
            if rangeStart is not None:
                yield range(rangeStart, prevValue + 1)
            rangeStart = value
        prevValue = value

    if rangeStart is not None:
        yield range(rangeStart, prevValue + 1)

def format_range(range_):
    """Convert range into hexadecimal representation.
    E.g. range(0, 2) -> '0x00-0x01', range(5, 6) -> '0x05'."""

    end = range_.stop - 1
    return f"0x{range_.start:02x}" + (f"-0x{end:02x}" if end > range_.start else "")

def read_block_data(addr, length, PRGBankData, maxValue=255):
    """Read ultra-subblock, subblock or block data from PRG ROM data. Return tuple."""

    if not 4 <= length <= 256 * 4 or length % 4:
        sys.exit(f"Invalid data size.")
    data = tuple(PRGBankData[i:i+4] for i in range(addr, addr + length, 4))
    valuesUsed = set(itertools.chain.from_iterable(data))
    print("Entries defined: {:d} (0x00-0x{:02x})".format(len(data), len(data) - 1))
    print("Unique values used by entries: {:d} ({:s})".format(
        len(valuesUsed), ", ".join(format_range(r) for r in find_ranges(valuesUsed))
    ))
    if max(valuesUsed) > maxValue:
        sys.exit("Invalid value in data.")
    return data

def read_map_data(addr, length, PRGBankData, maxValue=255):
    """Read map data from PRG ROM data (up to 32 * 32 blocks). Return tuple."""

    if not 32 <= length <= 32 * 32 or length % 32:
        sys.exit("Invalid data size.")
    data = PRGBankData[addr:addr+length]
    valuesUsed = set(data)
    print("Blocks: {:d}".format(len(data)))
    print("Unique blocks: {:d} ({:s})".format(
        len(valuesUsed), ", ".join(format_range(r) for r in find_ranges(valuesUsed))
    ))
    if max(valuesUsed) > maxValue:
        sys.exit("Invalid block index in map data.")
    return data

def create_USB_image(USBData, USBAttrData, tileData, worldPalette):
    """Return a Pillow Image with 16 * 16 ultra-subblocks, each 16 * 16 pixels."""

    image = Image.new("P", (16 * 16, 16 * 16), 0)  # indexed color
    RGBPalette = sorted(set(neslib.PALETTE[color] for color in worldPalette))
    image.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...
    worldPalToImgPal = tuple(RGBPalette.index(neslib.PALETTE[color]) for color in worldPalette)

    # for each USB, draw 2 * 2 tiles with correct palette
    for (USBIndex, USBTiles) in enumerate(USBData):  # index bits: UUUU_uuuu
        worldSubPal = USBAttrData[USBIndex] & 3
        for (tileIndex, tile) in enumerate(USBTiles):  # index bits: Tt
            for pixel in range(8 * 8):  # bits: PP_Pppp
                targetY = USBIndex & 0xf0 | tileIndex << 2 & 0x08 | pixel >> 3         # UUUU_TPPP
                targetX = USBIndex << 4 & 0xf0 | tileIndex << 3 & 0x08 | pixel & 0x07  # uuuu_tppp
                worldPalColor = worldSubPal << 2 | tileData[tile][pixel]
                image.putpixel((targetX, targetY), worldPalToImgPal[worldPalColor])
    return image

def get_USB_image_coords(USB):
    """Get source coordinates for ultra-subblock in ultra-subblock image.
    return: (x1, y1, x2, y2)"""

    # bits:
    # USB = TTTT_tttt
    # x   = tttt_0000
    # y   = TTTT_0000

    x = USB << 4 & 0xf0
    y = USB & 0xf0
    return (x, y, x + 16, y + 16)

def get_SB_image_coords(SB, USB):
    """Get target coordinates for ultra-subblock in subblock image.
    SB/USB: subblock/ultra-subblock index
    return: (x, y)"""

    # bits:
    # SB  =   SSSS_ssss
    # USB =          Uu
    # x   = S_SSSU_0000
    # y   = s_sssu_0000

    x = SB << 5 & 0x1e0 | USB << 4 & 0x10
    y = SB << 1 & 0x1e0 | USB << 3 & 0x10
    return (x, y)

def create_SB_image(SBData, USBImg, worldPalette):
    """Return a Pillow Image with 16 * 16 subblocks, each 32 * 32 pixels."""

    outImg = Image.new("P", (16 * 32, 16 * 32), 0)  # indexed color
    RGBPalette = sorted(set(neslib.PALETTE[color] for color in worldPalette))
    outImg.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...

    for (SBIndex, SB) in enumerate(SBData):
        for (USBIndex, USB) in enumerate(SB):
            # copy USB from one image to another
            inImg = USBImg.crop(get_USB_image_coords(USB))
            outImg.paste(inImg, get_SB_image_coords(SBIndex, USBIndex))
    return outImg

def get_block_image_coords(block, SB, USB):
    """Get target coordinates for ultra-subblock in block image.
    block/SB/USB: block/subblock/ultra-subblock index
    return: (x, y)"""

    # bits:
    # block =    BBBB_bbbb
    # SB    =           Ss
    # USB   =           Uu
    # x     = bb_bbsu_0000
    # y     = BB_BBSU_0000

    x = block << 6 & 0x3c0 | SB << 5 & 0x20 | USB << 4 & 0x10
    y = block << 2 & 0x3c0 | SB << 4 & 0x20 | USB << 3 & 0x10
    return (x, y)

def create_block_image(blockData, SBData, USBImg, worldPalette):
    """Return a Pillow Image with 16 * 16 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (16 * 64, 16 * 64), 0)  # indexed color
    RGBPalette = sorted(set(neslib.PALETTE[color] for color in worldPalette))
    outImg.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...

    # TODO: finish
                #outImg.paste(inImg, get_block_image_coords(blockIndex, SBIndex, USBIndex))
    return outImg

def get_map_image_coords(block, SB, USB):
    """Get target coordinates for ultra-subblock in map image.
    block/SB/USB: block/subblock/ultra-subblock index
    return: (x, y)"""

    # bits:
    # block =  BB_BBBb_bbbb
    # SB    =            Ss
    # USB   =            Uu
    # x     = bbb_bbsu_0000
    # y     = BBB_BBSU_0000

    x = block << 6 & 0x7c0 | SB << 5 & 0x20 | USB << 4 & 0x10
    y = block << 1 & 0x7c0 | SB << 4 & 0x20 | USB << 3 & 0x10
    return (x, y)

def create_map_image(mapData, blockData, SBData, USBImg, worldPalette):
    """Return Pillow Image of entire map with 32 * 32 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (2048, len(mapData) * 2), 0)  # indexed color
    RGBPalette = sorted(set(neslib.PALETTE[color] for color in worldPalette))
    outImg.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...

    # world = 32*? blocks, block = 2*2 subblocks, subblock = 2*2 ultra-subblocks,
    # ultra-subblock = 2*2 tiles, tile = 8*8 pixels
    for (blockIndex, block) in enumerate(mapData):
        for (SBIndex, SB) in enumerate(blockData[block]):
            for (USBIndex, USB) in enumerate(SBData[SB]):
                # copy USB from image to another
                inImg = USBImg.crop(get_USB_image_coords(USB))
                outImg.paste(inImg, get_map_image_coords(blockIndex, SBIndex, USBIndex))
    return outImg

def convert_map(sourceHnd, args):
    """Convert one map into PNG."""

    # parse iNES header
    try:
        fileInfo = ineslib.parse_iNES_header(sourceHnd)
    except ineslib.iNESError as error:
        sys.exit("iNES error: " + str(error))

    if not is_blaster_master(fileInfo):
        sys.exit("The file doesn't seem like Blaster Master.")

    (PRGBank, worldPtr, CHRBank) = MAP_DATA_ADDRESSES[args.map]
    scrollPtr = worldPtr + 2

    print(f"Banks: PRG (16 KiB) = {PRGBank:d}, CHR (4 KiB) = {CHRBank:d}")
    print(f"Pointer offsets within PRG bank: world=0x{worldPtr:04x}, scroll=0x{scrollPtr:04x}")

    # read PRG bank data
    sourceHnd.seek(16 + fileInfo["trainerSize"] + PRGBank * 16 * 1024)
    PRGBankData = sourceHnd.read(16 * 1024)

    # After the pointers, the order of data sections varies.
    # The first ones are always: palette, USBs, subblocks, blocks, map.
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

    # TODO: rip unused USBs/SBs/blocks, add to TCRF

    print("Reading ultra-subblock data...")
    USBData = read_block_data(USBAddr, SBAddr - USBAddr, PRGBankData)

    print("Reading subblock data...")
    SBData = read_block_data(SBAddr, blockAddr - SBAddr, PRGBankData, len(USBData) - 1)

    print("Reading block data...")
    blockData = read_block_data(blockAddr, mapAddr - blockAddr, PRGBankData, len(SBData) - 1)

    print("Reading map data...")
    mapData = read_map_data(
        mapAddr, min(USBAttrAddr, scrollAddr) - mapAddr, PRGBankData, len(blockData) - 1
    )

    # read ultra-subblock attribute data (1 byte/ultra-subblock)
    if not (scrollAddr < USBAttrAddr or scrollAddr == USBAttrAddr + len(USBData)):
        sys.exit("Invalid ultra-subblock attribute or scroll data address.")
    USBAttrData = PRGBankData[USBAttrAddr:USBAttrAddr+len(USBData)]

    # read and decode tile data
    sourceHnd.seek(16 + fileInfo["trainerSize"] + fileInfo["PRGSize"] + CHRBank * 4 * 1024)
    CHRBankData = sourceHnd.read(4 * 1024)
    tileData = tuple(neslib.decode_tile(CHRBankData[i*16:(i+1)*16]) for i in range(256))

    # create image with ultra-subblocks, optionally save
    USBImg = create_USB_image(USBData, USBAttrData, tileData, worldPalette)
    if args.usb is not None:
        with open(args.usb, "wb") as target:
            USBImg.save(target)

    # optionally create and save image with subblocks
    if args.sb is not None:
        SBImg = create_SB_image(SBData, USBImg, worldPalette)
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

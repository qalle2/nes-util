# source: "Blaster Master Format Specification", http://bck.sourceforge.net/blastermaster.txt
# (I actually figured out most of the info myself before I found that document.)

import argparse, itertools, os, struct, sys
from PIL import Image  # Pillow, https://python-pillow.org
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# addresses of maps: (16-KiB PRG ROM bank, pointer address within PRG ROM bank, 4-KiB CHR ROM bank)
# note: JP version uses PRG bank 4 instead of 2
MAP_DATA_ADDRESSES = {
    0:  (0, 0 * 4,  8),
    1:  (0, 1 * 4,  9),
    2:  (0, 2 * 4, 10),
    3:  (0, 3 * 4, 11),
    4:  (0, 4 * 4, 12),
    5:  (1, 0 * 4, 13),
    6:  (1, 1 * 4, 14),
    7:  (1, 2 * 4, 15),
    8:  (1, 3 * 4, 17),
    9:  (2, 1 * 4, 19),
    10: (1, 4 * 4, 18),
    11: (2, 4 * 4, 20),
    12: (2, 0 * 4, 18),
    13: (2, 2 * 4, 19),
    14: (2, 5 * 4, 20),
    15: (2, 3 * 4, 17),
}

def parse_arguments():
    # parse command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Extract world maps from NES Blaster Master to PNG files."
    )

    parser.add_argument(
        "-j", "--japan", action="store_true", help="Input file is Japanese version (Chou-Wakusei "
        "Senki - MetaFight)."
    )
    parser.add_argument(
        "-n", "--map-number", type=int, default=0, help="Map to extract: 0...7 = side view of "
        "area 1...8, 8...15 = overhead view of area 1...8. Default=0."
    )
    parser.add_argument(
        "-u", "--ultra-subblock-image", help="Save ultra-subblocks as PNG file (256*256 px)."
    )
    parser.add_argument(
        "-s", "--subblock-image", help="Save subblocks as PNG file (512*512 px)."
    )
    parser.add_argument(
        "-b", "--block-image", help="Save blocks as PNG file (1024*1024 px)."
    )
    parser.add_argument(
        "-m", "--map-image", help="Save map as PNG file (up to 2048*2048 px)."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print more information. Note: all addresses "
        "are hexadecimal."
    )

    parser.add_argument(
        "input_file", help="Blaster Master ROM file in iNES format (.nes, US/US prototype/EUR/JP; "
        "see also --japan)."
    )

    args = parser.parse_args()

    if not 0 <= args.map_number <= 15:
        sys.exit("Invalid map number.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")

    outputFiles = (
        args.ultra_subblock_image, args.subblock_image, args.block_image, args.map_image
    )
    if all(file_ is None for file_ in outputFiles):
        print("Warning: you didn't specify any output files.", file=sys.stderr)
    if any(file_ is not None and os.path.exists(file_) for file_ in outputFiles):
        sys.exit("Some of the output files already exist.")

    return args

def is_blaster_master(fileInfo):
    # is the file likely Blaster Master? don't validate too accurately because the file may be
    # a hack; fileInfo: from qneslib.ines_header_decode()
    return (
        fileInfo["prgSize"]     == 128 * 1024
        and fileInfo["chrSize"] == 128 * 1024
        and fileInfo["mapper"]  == 1
    )

def decode_offset(bytes_):
    # decode address, convert into offset within bank
    addr = struct.unpack("<H", bytes_)[0]  # little-endian unsigned short
    assert 0x8000 <= addr <= 0xbfff
    return addr & 0x3fff

def get_tile_data(handle):
    # read a bank of CHR data; generate one tile (64 2-bit big-endian integers) per call
    chrData = handle.read(4 * 1024)
    pixels = []
    for pos in range(0, 4096, 16):
        pixels.clear()
        for bitplanes in zip(chrData[pos:pos+8], chrData[pos+8:pos+16]):
            pixels.extend(qneslib.tile_slice_decode(*bitplanes))
        yield tuple(pixels)

def create_ultra_subblock_image(usbData, usbAttrData, tileData, worldPal):
    # create Pillow image with 16 * 16 ultra-subblocks, each 16 * 16 pixels; worldPal: world palette
    # (16 NES colors)

    image = Image.new("P", (16 * 16, 16 * 16), 0)  # indexed color

    # convert world palette into RGB
    worldPal = [qneslib.PALETTE[color] for color in worldPal]
    # set image palette, create palette conversion table
    imgPal = sorted(set(worldPal))
    image.putpalette(itertools.chain.from_iterable(imgPal))
    worldPalToImgPal = tuple(imgPal.index(color) for color in worldPal)

    # for each USB, draw 2*2 tiles with correct palette
    for (usbIndex, usb) in enumerate(usbData):
        palMask = (usbAttrData[usbIndex] & 3) << 2  # subpalette
        for (tileIndex, tile) in enumerate(usb):
            for (pixelIndex, pixel) in enumerate(tileData[tile]):
                # bits: usbIndex = UUUUuuuu, tileIndex = Tt, pixelIndex = PPPppp
                # -> y = UUUUTPPP, x = uuuutppp
                y = usbIndex & 0xf0       | (tileIndex & 2) << 2 | pixelIndex >> 3
                x = (usbIndex & 0xf) << 4 | (tileIndex & 1) << 3 | pixelIndex & 7
                image.putpixel((x, y), worldPalToImgPal[palMask|pixel])
    return image

def world_palette_into_image_palette(worldPal):
    # 16 NES colors -> generate sorted unique colors as R,G,B,R,G,B,...
    yield from itertools.chain.from_iterable(
        sorted(set(qneslib.PALETTE[color] for color in worldPal))
    )

def create_subblock_image(sbData, usbImg, worldPal):
    # create Pillow image with 16 * 16 subblocks, each 32 * 32 pixels

    outImg = Image.new("P", (16 * 32, 16 * 32), 0)  # indexed color
    outImg.putpalette(world_palette_into_image_palette(worldPal))

    for (sbIndex, usbs) in enumerate(sbData):
        for (usbIndex, usb) in enumerate(usbs):
            # copy USB from source image
            # bits: usb = UUUUuuuu -> y = UUUU0000, x = uuuu0000
            y = usb & 0xf0
            x = (usb & 0x0f) << 4
            inImg = usbImg.crop((x, y, x + 16, y + 16))
            # paste USB into target image
            # bits: sbIndex = SSSSssss, usbIndex = Uu
            # -> y = SSSSU0000, x = ssssu0000
            y = (sbIndex & 0xf0) << 1 | (usbIndex & 2) << 3
            x = (sbIndex & 0xf)  << 5 | (usbIndex & 1) << 4
            outImg.paste(inImg, (x, y))
    return outImg

def create_block_image(blockData, sbData, usbImg, worldPal):
    # create Pillow Image with 16 * 16 blocks, each 64 * 64 pixels

    outImg = Image.new("P", (16 * 64, 16 * 64), 0)  # indexed color
    outImg.putpalette(world_palette_into_image_palette(worldPal))

    for (blockIndex, block) in enumerate(blockData):
        for (sbIndex, sb) in enumerate(block):
            for (usbIndex, usb) in enumerate(sbData[sb]):
                # copy USB from source image
                # bits: usb = UUUUuuuu -> y = UUUU0000, x = uuuu0000
                y = usb & 0xf0
                x = (usb & 0x0f) << 4
                inImg = usbImg.crop((x, y, x + 16, y + 16))
                # paste USB into target image
                # bits: blockIndex = BBBBbbbb, sbIndex = Ss, usbIndex = Uu
                # -> y = BBBBSU0000, x = bbbbsu0000
                y = (blockIndex & 0xf0) << 2 | (sbIndex & 2) << 4 | (usbIndex & 2) << 3
                x = (blockIndex & 0xf)  << 6 | (sbIndex & 1) << 5 | (usbIndex & 1) << 4
                outImg.paste(inImg, (x, y))
    return outImg

def create_map_image(mapData, blockData, sbData, usbImg, worldPal):
    # create Pillow Image of entire map with 32 * 32 blocks, each 64 * 64 pixels

    outImg = Image.new("P", (32 * 64, len(mapData) * 2), 0)  # indexed color
    outImg.putpalette(world_palette_into_image_palette(worldPal))

    # world = 32*? blocks, block = 2*2 subblocks, subblock = 2*2 ultra-subblocks,
    # ultra-subblock = 2*2 tiles, tile = 8*8 pixels
    for (blockIndex, block) in enumerate(mapData):
        for (sbIndex, sb) in enumerate(blockData[block]):
            for (usbIndex, usb) in enumerate(sbData[sb]):
                # copy USB from source image
                # bits: usb = UUUUuuuu -> y = UUUU0000, x = uuuu0000
                y = usb & 0xf0
                x = (usb & 0x0f) << 4
                inImg = usbImg.crop((x, y, x + 16, y + 16))
                # paste USB into target image
                # bits: blockIndex = BBBBBbbbbb, sbIndex = Ss, usbIndex = Uu
                # -> y = BBBBBSU0000, x = bbbbbsu0000
                y = (blockIndex & 0x3e0) << 1 | (sbIndex & 2) << 4 | (usbIndex & 2) << 3
                x = (blockIndex & 0x1f)  << 6 | (sbIndex & 1) << 5 | (usbIndex & 1) << 4
                outImg.paste(inImg, (x, y))
    return outImg

args = parse_arguments()

try:
    with open(args.input_file, "rb") as sourceHnd:
        # parse iNES header
        fileInfo = qneslib.ines_header_decode(sourceHnd)
        if fileInfo is None:
            sys.exit("Not a valid iNES ROM file.")

        if not is_blaster_master(fileInfo):
            sys.exit("The file doesn't look like Blaster Master.")

        (prgBank, worldPtr, chrBank) = MAP_DATA_ADDRESSES[args.map_number]
        prgBank = 4 if prgBank == 2 and args.japan else prgBank  # the only version difference
        scrollPtr = worldPtr + 2

        # read PRG bank
        sourceHnd.seek(fileInfo["prgStart"] + prgBank * 16 * 1024)
        prgBankData = sourceHnd.read(16 * 1024)

        worldAddr  = decode_offset(prgBankData[worldPtr :worldPtr +2])
        scrollAddr = decode_offset(prgBankData[scrollPtr:scrollPtr+2])

        if args.verbose:
            print(f"Map: {args.map_number:d}, PRG bank: {prgBank}, CHR bank: {chrBank}")
            print(f"World data at {worldAddr:04x}, scroll data at {scrollAddr:04x}")

        # The first data sections are always: palette, ultra-subblocks, subblocks, blocks, map.
        # The last two are USB attributes and scroll, in either order.

        (palAddr, usbAttrAddr, usbAddr, sbAddr, blockAddr, mapAddr) = (
            decode_offset(prgBankData[pos:pos+2])
            for pos in range(worldAddr, worldAddr + 12, 2)
        )

        if args.verbose:
            print(
                "Section addresses: "
                f"palette: {palAddr:04x}, "
                f"USBs: {usbAddr:04x}, "
                f"SBs: {sbAddr:04x}, "
                f"blocks: {blockAddr:04x}, "
                f"map: {mapAddr:04x}, "
                f"USB attributes: {usbAttrAddr:04x}"
            )

        # read this world's palette (always 4*4 bytes, contains duplicate NES colors)
        worldPalette = prgBankData[palAddr:palAddr+16]
        assert max(worldPalette) <= 0x3f

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
            print(
                "Warning: scroll data overlaps with ultra-subblock attribute data. "
                "(This is expected for map 3 of Japanese version.)",
                file=sys.stderr
            )
        usbAttrData = prgBankData[usbAttrAddr:usbAttrAddr+len(usbData)]

        # read and decode tile data
        sourceHnd.seek(fileInfo["chrStart"] + chrBank * 4 * 1024)
        tileData = list(get_tile_data(sourceHnd))

        # create ultra-subblock image (needed for creating all other images)
        usbImg = create_ultra_subblock_image(usbData, usbAttrData, tileData, worldPalette)
        if args.ultra_subblock_image is not None:
            # save ultra-subblock image
            with open(args.ultra_subblock_image, "wb") as target:
                usbImg.save(target)

        if args.subblock_image is not None:
            # create and save subblock image
            sbImg = create_subblock_image(sbData, usbImg, worldPalette)
            with open(args.subblock_image, "wb") as target:
                sbImg.save(target)

        if args.block_image is not None:
            # create and save block image
            blockImg = create_block_image(blockData, sbData, usbImg, worldPalette)
            with open(args.block_image, "wb") as target:
                blockImg.save(target)

        if args.map_image is not None:
            # create and save map image
            mapImg = create_map_image(mapData, blockData, sbData, usbImg, worldPalette)
            with open(args.map_image, "wb") as target:
                target.seek(0)
                mapImg.save(target)
except OSError:
    sys.exit("Error reading/writing files.")

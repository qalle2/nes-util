# extract map data from NES Super Mario Bros. by Nintendo;
# under construction

# tile = 8*8 pixels with 2 bitplanes
# metatile = 2*2 tiles with 1 of 4 palettes
# screen = 16*13 metatiles (area objects can't be placed on bottom row)
# area = 1-32 screens horizontally (ground area 9 is 1 screen, ground area 16
#        is 24 screens)
# level = 1 or more areas, connected by pipes/vines/falling/other?
# "doppelganger's" = doppelganger's SMB disassembly

# for area/enemy data, see
# https://www.youtube.com/watch?v=1ysdUajrhL8
# (5:50-18:20 for area data, 18:20-22:00 for enemy data)

import itertools, os, struct, sys
from PIL import Image  # Pillow, https://python-pillow.org

HELP_TEXT = """\
Extract map data (excluding enemies) from NES Super Mario Bros. by Nintendo.
Argument syntax:
    Short summary of all areas:
        INPUTFILE
    All data and image of one area:
        INPUTFILE OUTPUTFILE AREATYPE AREA
Arguments:
    INPUTFILE: iNES format, US version.
    OUTPUTFILE: PNG, will be overwritten!
    AREATYPE: 0=water, 1=ground, 2=underground, 3=castle.
    AREA: 0 or greater; max. value depends on AREATYPE.
E.g. AREATYPE 1, AREA 5 = above-ground part of level 1-1.
Note: looping castle areas look totally wrong; all other areas look more or
less wrong too.\
"""

AREA_TYPES = ("water", "ground", "underground", "castle")

# PRG ROM addresses (not CPU or .nes file addresses)
BACKGROUND_COLORS      = 0x05cf  # "BackgroundColors"     in doppelganger's
METATILE_DATA          = 0x0b08  # "MetatileGraphics_Low" in doppelganger's
PALETTE_DATA           = 0x0ca4  # "WaterPaletteData"     in doppelganger's
FLOOR_METATILES        = 0x13d8  # "TerrainMetatiles"     in doppelganger's
FLOOR_PATTERNS         = 0x13dc  # "TerrainRenderBits"    in doppelganger's
CASTLE_METATILES       = 0x17cf  # "CastleMetatiles"      in doppelganger's
AREA_DATA_OFFSETS      = 0x1d28  # "AreaDataHOffsets"     in doppelganger's
AREA_DATA_ADDRESSES_LO = 0x1d2c  # "AreaDataAddrLow"      in doppelganger's
AREA_DATA_ADDRESSES_HI = 0x1d4e  # "AreaDataAddrHigh"     in doppelganger's

# enumerate types of area data blocks
(
    AB_Y_NO_SIZE,      # object with Y but no size (e.g. "?" with power-up)
    AB_Y_SIZE,         # object with both Y and size (e.g. brick row)
    AB_SIZE_NO_Y,      # object with size but no Y (e.g. castle)
    AB_NO_Y_NO_SIZE,   # object without Y or size (e.g. axe)
    AB_SCREEN,         # skip to screen
    AB_BACKGROUND,     # switch background
    AB_SCENERY_FLOOR,  # switch scenery & floor pattern
) = range(7)

# NES master palette;
# key=index, value=(red, green, blue); source: FCEUX (fceux.pal)
NES_COLORS = {
    0x00: (0x74, 0x74, 0x74),
    0x01: (0x24, 0x18, 0x8c),
    0x02: (0x00, 0x00, 0xa8),
    0x03: (0x44, 0x00, 0x9c),
    0x04: (0x8c, 0x00, 0x74),
    0x05: (0xa8, 0x00, 0x10),
    0x06: (0xa4, 0x00, 0x00),
    0x07: (0x7c, 0x08, 0x00),
    0x08: (0x40, 0x2c, 0x00),
    0x09: (0x00, 0x44, 0x00),
    0x0a: (0x00, 0x50, 0x00),
    0x0b: (0x00, 0x3c, 0x14),
    0x0c: (0x18, 0x3c, 0x5c),
    0x0d: (0x00, 0x00, 0x00),
    0x0e: (0x00, 0x00, 0x00),
    0x0f: (0x00, 0x00, 0x00),
    0x10: (0xbc, 0xbc, 0xbc),
    0x11: (0x00, 0x70, 0xec),
    0x12: (0x20, 0x38, 0xec),
    0x13: (0x80, 0x00, 0xf0),
    0x14: (0xbc, 0x00, 0xbc),
    0x15: (0xe4, 0x00, 0x58),
    0x16: (0xd8, 0x28, 0x00),
    0x17: (0xc8, 0x4c, 0x0c),
    0x18: (0x88, 0x70, 0x00),
    0x19: (0x00, 0x94, 0x00),
    0x1a: (0x00, 0xa8, 0x00),
    0x1b: (0x00, 0x90, 0x38),
    0x1c: (0x00, 0x80, 0x88),
    0x1d: (0x00, 0x00, 0x00),
    0x1e: (0x00, 0x00, 0x00),
    0x1f: (0x00, 0x00, 0x00),
    0x20: (0xfc, 0xfc, 0xfc),
    0x21: (0x3c, 0xbc, 0xfc),
    0x22: (0x5c, 0x94, 0xfc),
    0x23: (0xcc, 0x88, 0xfc),
    0x24: (0xf4, 0x78, 0xfc),
    0x25: (0xfc, 0x74, 0xb4),
    0x26: (0xfc, 0x74, 0x60),
    0x27: (0xfc, 0x98, 0x38),
    0x28: (0xf0, 0xbc, 0x3c),
    0x29: (0x80, 0xd0, 0x10),
    0x2a: (0x4c, 0xdc, 0x48),
    0x2b: (0x58, 0xf8, 0x98),
    0x2c: (0x00, 0xe8, 0xd8),
    0x2d: (0x78, 0x78, 0x78),
    0x2e: (0x00, 0x00, 0x00),
    0x2f: (0x00, 0x00, 0x00),
    0x30: (0xfc, 0xfc, 0xfc),
    0x31: (0xa8, 0xe4, 0xfc),
    0x32: (0xc4, 0xd4, 0xfc),
    0x33: (0xd4, 0xc8, 0xfc),
    0x34: (0xfc, 0xc4, 0xfc),
    0x35: (0xfc, 0xc4, 0xd8),
    0x36: (0xfc, 0xbc, 0xb0),
    0x37: (0xfc, 0xd8, 0xa8),
    0x38: (0xfc, 0xe4, 0xa0),
    0x39: (0xe0, 0xfc, 0xa0),
    0x3a: (0xa8, 0xf0, 0xbc),
    0x3b: (0xb0, 0xfc, 0xcc),
    0x3c: (0x9c, 0xfc, 0xf0),
    0x3d: (0xc4, 0xc4, 0xc4),
    0x3e: (0x00, 0x00, 0x00),
    0x3f: (0x00, 0x00, 0x00),
}

# --- used by print_summary() and possibly extract_map() ----------------------

def generate_area_blocks(areaDataAddr, prgData):
    # generate blocks (2 bytes each) from area data (excluding header and
    # terminator)

    for i in range(0, 0x100, 2):
        block = prgData[areaDataAddr+i+2:areaDataAddr+i+4]
        if block[0] == 0xfd:  # terminator
            break
        yield block

def get_area_block_type(block):
    # block: 2 bytes; return an AB_... constant (see definitions)

    y = block[0] & 0b1111

    if y < 12:
        return AB_Y_SIZE if block[1] & 0b1110000 else AB_Y_NO_SIZE
    if y == 12 or y == 15:
        return AB_SIZE_NO_Y
    if y == 13:
        return AB_NO_Y_NO_SIZE if block[1] & 0b1000000 else AB_SCREEN
    # Y = 14
    return AB_BACKGROUND if block[1] & 0b1000000 else AB_SCENERY_FLOOR

def get_area_width(areaDataAddr, prgData):
    # get area width in screens (1-32)

    screen = maxScreen = 0
    for block in generate_area_blocks(areaDataAddr, prgData):
        maxScreen = max(screen, maxScreen)
        if get_area_block_type(block) == AB_SCREEN:
            screen = block[1] & 0b11111
        elif block[1] >> 7:
            screen += 1
    return maxScreen + 1

def parse_area_header(areaDataAddr, prgData):
    # parse area data header (2 bytes, bits TTMMMBBB PPSSFFFF)

    header = prgData[areaDataAddr:areaDataAddr+2]

    return {
        "timeLimit":       header[0] >> 6,
        "startHeight":     (header[0] >> 3) & 0b111,
        "background":      header[0] & 0b111,         # initial
        "specialPlatform": header[1] >> 6,
        "scenery":         (header[1] >> 4) & 0b11,   # initial
        "floorPattern":    header[1] & 0b1111,        # initial
    }

def get_area_count(areaType, prgData):
    # get number of areas for area type

    # get area data offsets
    offsets = prgData[AREA_DATA_OFFSETS:AREA_DATA_OFFSETS+4]

    if areaType < 3:
        return offsets[areaType+1] - offsets[areaType]
    return AREA_DATA_ADDRESSES_HI \
    - (AREA_DATA_ADDRESSES_LO + offsets[areaType])

def get_area_data_addr(areaType, area, prgData):
    # get PRG ROM address of area data

    offset = prgData[AREA_DATA_OFFSETS+areaType] + area

    lowByte = prgData[AREA_DATA_ADDRESSES_LO+offset]
    highByte = prgData[AREA_DATA_ADDRESSES_HI+offset]

    return (lowByte + highByte * 0x100) & 0x7fff

def print_summary(prgData):
    # print a summary of all areas

    print("Floor patterns (*=brick, .=blank):")
    patterns = get_floor_patterns(prgData)
    print(" ".join(f"{x:2}" for x in range(16)))
    print(" ".join("--" for x in range(16)))
    for y in range(13):
        print(" ".join(" " + (".", "*")[patterns[x][y]] for x in range(16)))
    print()

    print(
        "AT = area type, A# = area number, Addr = PRG address, Wi = width in "
        "screens, AOb = number of area objects, TL = time limit, SH = start "
        "height, SP = special platform type, BkGnd = backgrounds, Scenrs = "
        "sceneries, Floors = floor patterns"
    )
    print()
    print("AT A#  Addr Wi AOb TL SH SP BkGnd   Scenrs  Floors")
    print("-- -- ----- -- --- -- -- -- -----   ------  ------")
    for areaType in range(4):
        areaCount = get_area_count(areaType, prgData)
        for area in range(areaCount):
            dataAddr = get_area_data_addr(areaType, area, prgData)
            hdrInfo = parse_area_header(dataAddr, prgData)
            width = get_area_width(dataAddr, prgData)
            blockCnt = sum(
                1 for i in generate_area_blocks(dataAddr, prgData)
            )

            backgrounds = {hdrInfo["background"]} | set(
                b[1] & 0b111 for b in generate_area_blocks(dataAddr, prgData)
                if get_area_block_type(b) == AB_BACKGROUND
            )
            backgrounds = "/".join(str(b) for b in sorted(backgrounds))

            sceneries = {hdrInfo["scenery"]} | set(
                (b[1] >> 4) & 0b11
                for b in generate_area_blocks(dataAddr, prgData)
                if get_area_block_type(b) == AB_SCENERY_FLOOR
            )
            sceneries = "/".join(str(b) for b in sorted(sceneries))

            floorPatterns = {hdrInfo["floorPattern"]} | set(
                b[1] & 0b1111 for b in generate_area_blocks(dataAddr, prgData)
                if get_area_block_type(b) == AB_SCENERY_FLOOR
            )
            floorPatterns = "/".join(str(b) for b in sorted(floorPatterns))

            print(
                "{:2} {:2} ${:04x} {:2} {:3} {:2} {:2} {:2} {:7} {:7} {}"
                .format(
                    areaType, area, dataAddr,
                    width, blockCnt,
                    hdrInfo["timeLimit"], hdrInfo["startHeight"],
                    hdrInfo["specialPlatform"],
                    backgrounds, sceneries, floorPatterns
                )
            )

# --- used by extract_map() but not print_summary() ---------------------------

def create_mtile_image(bgTileImage, prgData):
    # create image with 16*16 metatiles (256*256 px) from PRG ROM data and
    # tile image; top 16*4 metatiles are for palette 0, etc.
    # note: there's garbage at the end

    # get PRG addresses of metatile data of each palette
    pointers = prgData[METATILE_DATA:METATILE_DATA+2*4]
    pointers = [
        (pointers[i] + pointers[i+4] * 0x100) & 0x7fff for i in range(4)
    ]

    mtileImage = Image.new("P", (16 * 16, 16 * 16))
    mtileImage.putpalette((0,0,0, 85,85,85, 170,170,170, 255,255,255))

    for palette in range(4):
        # get tile data
        if palette < 3:
            dataEnd = pointers[palette+1]
        else:
            dataEnd = pointers[palette] + 256
        tileData = prgData[pointers[palette]:dataEnd]

        for mti in range(len(tileData) // 4):  # metatile index
            for ti in range(4):  # tile index within metatile
                # get tile
                (y, x) = divmod(tileData[mti*4+ti], 16)
                tempImage = bgTileImage.crop((
                    x * 8, y * 8, (x + 1) * 8, (y + 1) * 8
                ))
                # paste tile
                y = (palette * 4 + mti // 16) * 16 + ti % 2 * 8
                x = mti % 16 * 16 + ti // 2 * 8
                mtileImage.paste(tempImage, (x, y))

    return mtileImage

def get_mtile_from_image(i, mtileImage):
    # get metatile from image
    (y, x) = divmod(i, 16)
    return mtileImage.crop((x * 16, y * 16, (x + 1) * 16, (y + 1) * 16))

def get_floor_patterns(prgData):
    # return floor patterns as 16 tuples of 13 ints (0=blank, 1=brick; top to
    # bottom)

    patterns = prgData[FLOOR_PATTERNS:FLOOR_PATTERNS+16*2]
    patternsList = []
    for i in range(0, 16 * 2, 2):
        # interpret 2 bytes as unsigned little endian
        pattern = patterns[i] + patterns[i+1] * 0x100
        # convert bottom 13 bits into a tuple, low bit first
        patternList = []
        for j in range(13):
            patternList.append(pattern & 1)
            pattern >>= 1
        patternsList.append(tuple(patternList))
    return patternsList

def draw_floor_patterns(areaImage, areaType, area, mtileImage, prgData):
    # draw floor patterns on area image

    areaDataAddr = get_area_data_addr(areaType, area, prgData)
    areaWidth = get_area_width(areaDataAddr, prgData)
    floorPatterns = get_floor_patterns(prgData)

    # get metatile
    mti = prgData[FLOOR_METATILES+areaType]
    mtile = get_mtile_from_image(mti, mtileImage)

    # find out where floor pattern changes
    patternChanges = {}  # key = screen * 16 + X, value = pattern
    screen = 0
    for block in generate_area_blocks(areaDataAddr, prgData):
        if block[1] >> 7:
            screen += 1
        if get_area_block_type(block) == AB_SCENERY_FLOOR:
            x = block[0] >> 4
            pattern = block[1] & 0b1111
            patternChanges[screen*16+x] = pattern

    # get initial floor pattern
    pattern = parse_area_header(areaDataAddr, prgData)["floorPattern"]

    # draw columns
    for x in range(areaWidth * 16):
        for (y, isFilled) in enumerate(floorPatterns[pattern]):
            if isFilled:
                areaImage.paste(mtile, (x * 16, y * 16))
        pattern = patternChanges.get(x, pattern)
    return areaImage

AREA_BLK_TYPES_Y_SIZE = {
    1: "special platform",
    2: "brick row",
    3: "3D block row",
    4: "coin row",
    5: "brick column",
    6: "3D block column",
    7: "vertical pipe",
}
METATILES_TYPE_Y_SIZE = {
    1: 0x16,  # special platform
    2: 0x47,  # brick
    5: 0x47,  # brick
    3: 0x61,  # 3D block
    6: 0x61,  # 3D block
    4: 0xc2,  # coin
}

AREA_BLK_TYPES_Y_NO_SIZE = {
    0:  "question block with power-up",
    1:  "question block with coin",
    2:  "hidden coin",
    3:  "hidden 1-up",
    4:  "brick with power-up",
    5:  "brick with vine",
    6:  "brick with star",
    7:  "brick with multiple coins",
    8:  "brick with 1-up",
    9:  "used question block",
    10: "horizontal end of pipe",  # also firebar block?
    11: "jumpspring",
    12: "pipe left & up (variant 1?)",
    13: "flagpole 1",
}
METATILES_TYPE_Y_NO_SIZE = {
    0:  0xc0,  # question block
    1:  0xc0,  # question block
    2:  0xc4,  # used question block
    3:  0xc4,  # used question block
    4:  0x47,  # brick
    5:  0x47,  # brick
    6:  0x47,  # brick
    7:  0x47,  # brick
    8:  0x47,  # brick
    9:  0xc4,  # used question block
    10: 0xc4,  # used question block
    13: 0x24,  # flagpole ball
}

AREA_BLK_TYPES_SIZE_NO_Y = {
    0:  "hole in ground",
    1:  "pulley rope top",
    2:  "bridge at Y=7",
    3:  "bridge at Y=8",
    4:  "bridge at Y=10",
    5:  "water/lava hole in ground",
    6:  "question block row at Y=3",
    7:  "question block row at Y=7",
    8:  "vertical pulley rope 1",
    9:  "vertical pulley rope 2",
    10: "castle",
    11: "ascending staircase",
    12: "pipe left & long up",
}
METATILES_TYPE_SIZE_NO_Y = {
    0:  0x00,  # solid black
    5:  0x00,  # solid black
    6:  0xc0,  # question block
    7:  0xc0,  # question block
    8:  0x25,  # vertical pulley rope
    9:  0x25,  # vertical pulley rope
    11: 0x61,  # 3D block
}

AREA_BLK_TYPES_NO_Y_NO_SIZE = {
    0:  "pipe left & up (variant 2?)",
    1:  "flagpole 2",  # e.g. 1-1
    2:  "axe",
    3:  "diagonal chain",
    4:  "Bowser's bridge",
    5:  "warp zone",
    6:  "scroll stop 1",
    7:  "scroll stop 2",
    8:  "generator - red Cheep Cheep",
    9:  "generator - bullet or gray Cheep Cheep",
    10: "generator - stop",
    11: "loop command",
}
METATILES_TYPE_NO_Y_NO_SIZE = {
    1: 0x24,  # flagpole ball
    2: 0xc5,  # axe
    3: 0x0c,  # diagonal chain
    4: 0x89,  # Bowser's bridge
}

REPL_MTILE = 0x88  # replacement metatile (smiling cloud)

def parse_area_block(block, screen, areaImage, mtileImage, prgData):
    # parse area data block (object) except terminator
    # (2 bytes, bits XXXXYYYY NTTTSSSS)
    # screen: current screen
    # areaImage: image to draw to
    # mtileImage: 16*16 metatiles
    # return: (current screen, areaImage)

    blockType = get_area_block_type(block)

    blkX = block[0] >> 4
    blkY = block[0] & 0b1111  # only meaningful for AB_Y_SIZE, AB_Y_NO_SIZE
    nextScreen = block[1] >> 7

    # get type of object, if any
    if blockType == AB_Y_NO_SIZE:
        objType = block[1] & 0b1111
    elif blockType == AB_Y_SIZE:
        objType = (block[1] >> 4) & 0b111
    elif blockType == AB_SIZE_NO_Y:
        objType = ((block[1] >> 4) & 0b111) + (8 if blkY == 15 else 0)
    elif blockType == AB_NO_Y_NO_SIZE:
        objType = block[1] & 0b111111

    # get other properties of object, if any
    if blockType == AB_Y_SIZE and objType == 7:  # vertical pipe
        enterable = (block[1] >> 3) & 0b1
        size = (block[1] & 0b111) + 1
    elif blockType in (AB_Y_SIZE, AB_SIZE_NO_Y):
        size = (block[1] & 0b1111) + 1

    if nextScreen:
        screen += 1

    print(f"screen={screen:2}, X={blkX:2}: ", end="")
    imageX = (screen * 16 + blkX) * 16

    if blockType == AB_Y_NO_SIZE:
        print(f"{AREA_BLK_TYPES_Y_NO_SIZE[objType]}, Y={blkY}")
        mtile = get_mtile_from_image(
            METATILES_TYPE_Y_NO_SIZE.get(objType, REPL_MTILE), mtileImage
        )
        areaImage.paste(mtile, (imageX, blkY * 16))

    elif blockType == AB_Y_SIZE:
        if objType == 7:
            # vertical pipe
            print(
                f"{AREA_BLK_TYPES_Y_SIZE[objType]}, Y={blkY}, {enterable=}, "
                f"{size=}"
            )
            for x in range(2):
                for y in range(size):
                    mti = 0x10 + x + (0 if y == 0 else 4)
                    mtile = get_mtile_from_image(mti, mtileImage)
                    areaImage.paste(mtile, (imageX + x * 16, (blkY + y) * 16))
        else:
            print(f"{AREA_BLK_TYPES_Y_SIZE[objType]}, Y={blkY}, {size=}")
            mtile = get_mtile_from_image(
                METATILES_TYPE_Y_SIZE[objType], mtileImage
            )
            if objType <= 4:
                # row
                for x in range(size):
                    areaImage.paste(mtile, (imageX + x * 16, blkY * 16))
            else:
                # column
                for y in range(size):
                    areaImage.paste(mtile, (imageX, (blkY + y) * 16))

    elif blockType == AB_SIZE_NO_Y:
        print(f"{AREA_BLK_TYPES_SIZE_NO_Y[objType]}, {size=}")
        mtile = get_mtile_from_image(
            METATILES_TYPE_SIZE_NO_Y.get(objType, REPL_MTILE), mtileImage
        )
        if objType == 0:
            # hole in ground
            for x in range(size):
                for y in range(8, 12 + 1):
                    areaImage.paste(mtile, (imageX + x * 16, y * 16))
        elif objType == 5:
            # water/lava hole in ground
            for x in range(size):
                for y in range(8, 9 + 1):
                    areaImage.paste(mtile, (imageX + x * 16, y * 16))
            mtile = get_mtile_from_image(0x86, mtileImage)  # water/lava
            for x in range(size):
                for y in range(10, 12 + 1):
                    areaImage.paste(mtile, (imageX + x * 16, y * 16))
        elif objType == 10:
            # castle (looks wrong)
            for x in range(5):
                for y in range(size):
                    mti = prgData[CASTLE_METATILES+y*5+x]
                    mtile = get_mtile_from_image(mti, mtileImage)
                    areaImage.paste(mtile, (imageX + x * 16, (y + 4) * 16))
        elif objType == 11:
            # ascending staircase
            for x in range(size):
                for y in range(max(10 - x, 3), 10 + 1):
                    areaImage.paste(mtile, (imageX + x * 16, y * 16))
        elif objType in (6, 7):
            # question block row at Y=3/7
            y = 3 + (objType - 6) * 4
            for x in range(size):
                areaImage.paste(mtile, (imageX + x * 16, y * 16))
        else:
            for x in range(size):
                for y in range(13):
                    areaImage.paste(mtile, (imageX + x * 16, y * 16))

    elif blockType == AB_NO_Y_NO_SIZE:
        print(f"{AREA_BLK_TYPES_NO_Y_NO_SIZE[objType]}")
        mtile = get_mtile_from_image(
            METATILES_TYPE_NO_Y_NO_SIZE.get(objType, REPL_MTILE), mtileImage
        )
        if objType == 1:
            # flagpole
            areaImage.paste(mtile, (imageX, 0 * 16))
            mtile = get_mtile_from_image(0x25, mtileImage)  # shaft
            for y in range(1, 9 + 1):
                areaImage.paste(mtile, (imageX, y * 16))
            mtile = get_mtile_from_image(0x61, mtileImage)  # base
            areaImage.paste(mtile, (imageX, 10 * 16))
        elif objType == 2:
            # axe
            areaImage.paste(mtile, (imageX, 6 * 16))
        elif objType == 3:
            # diagonal chain
            areaImage.paste(mtile, (imageX, 7 * 16))
        elif objType == 4:
            # Bowser's bridge
            for x in range(13):
                areaImage.paste(mtile, (imageX + x * 16, 8 * 16))
            mtile = get_mtile_from_image(0x86, mtileImage)  # lava
            for x in range(13):
                for y in range(11, 12 + 1):
                    areaImage.paste(mtile, (imageX + x * 16, y * 16))
        else:
            for y in range(13):
                areaImage.paste(mtile, (imageX, y * 16))

    elif blockType == AB_SCREEN:
        screen = block[1] & 0b11111
        print(f"skip to screen {screen}")

    elif blockType == AB_BACKGROUND:
        bg = block[1] & 0b111
        print(f"use background {bg}")

    elif blockType == AB_SCENERY_FLOOR:
        scenery = (block[1] >> 4) & 0b11
        floor = block[1] & 0b1111
        print(f"use scenery {scenery}, floor pattern {floor}")

    else:
        sys.exit("Error: this should never happen.")

    return (screen, areaImage)

def extract_map(areaType, area, prgData, bgTileImage):
    # return area image, print info

    # create image of metatiles (16*16 metatiles, 256*256 px)
    mtileImage = create_mtile_image(bgTileImage, prgData)

    # check maximum area number for area type
    areaCount = get_area_count(areaType, prgData)
    if area >= areaCount:
        sys.exit(f"AREA must be 0-{areaCount-1} for this AREATYPE.")

    print(f"area type: {areaType} ({AREA_TYPES[areaType]})")
    print(f"area # within area type: {area}")

    areaDataAddr = get_area_data_addr(areaType, area, prgData)
    print(f"area data PRG address: ${areaDataAddr:04x}")

    hdrInfo = parse_area_header(areaDataAddr, prgData)
    print(
        "header - area-wide values: "
        "time limit", hdrInfo["timeLimit"],
        ", start height", hdrInfo["startHeight"],
        ", special platform", hdrInfo["specialPlatform"],
    )
    print(
        "header - initial values: "
        "background", hdrInfo["background"],
        ", scenery", hdrInfo["scenery"],
        ", floor pattern", hdrInfo["floorPattern"],
    )

    areaWidth = get_area_width(areaDataAddr, prgData)
    print("area width in screens:", areaWidth)

    # background/foreground colors
    bgColor = prgData[BACKGROUND_COLORS+areaType]
    subpal = (1, 3, 1, 0)[areaType]  # temporary hack
    fgColorAddr = PALETTE_DATA + areaType * 36 + subpal * 4 + 4
    fgColors = prgData[fgColorAddr:fgColorAddr+3]

    # create indexed image
    areaImage = Image.new("P", (areaWidth * 16 * 16, 13 * 16))
    palette = [NES_COLORS[c] for c in (bgColor, *fgColors)]
    areaImage.putpalette(itertools.chain.from_iterable(palette))

    # draw floor patterns
    areaImage = draw_floor_patterns(
        areaImage, areaType, area, mtileImage, prgData
    )

    # print and draw area data blocks
    print("area data:")
    screen = 0
    for block in generate_area_blocks(areaDataAddr, prgData):
        (screen, areaImage) \
        = parse_area_block(block, screen, areaImage, mtileImage, prgData)

    return areaImage

# --- not used by extract_map() or print_summary() ----------------------------

def decode_ines_header(fileData):
    # parse iNES ROM header; return dict or None on error;
    # does not support VS System, PlayChoice-10 or trainer flags or NES 2.0
    # header; see https://www.nesdev.org/wiki/INES

    if len(fileData) < 16:
        return None

    (id_, prgSize, chrSize, flags6, flags7) \
    = struct.unpack("4s4B", fileData[:8])

    prgSize *= 16 * 1024
    chrSize *= 8 * 1024

    if id_ != b"NES\x1a" or len(fileData) < 16 + prgSize + chrSize:
        return None

    return {
        "prgStart": 16,
        "prgSize":  prgSize,
        "chrStart": 16 + prgSize,
        "chrSize":  chrSize,
        "mapper":   (flags7 & 0b11110000) | (flags6 >> 4),
    }

def decode_pt(chrData):
    # read one pattern table (256 tiles) of CHR data;
    # generate tiles (tuples of 64 2-bit ints)
    pixels = []
    for ti in range(256):
        tile = chrData[(0x100+ti)*16:(0x101+ti)*16]
        pixels.clear()
        for y in range(8):
            pixels.extend(
                ((tile[y] >> s) & 1) | (((tile[y+8] >> s) & 1) << 1)
                for s in range(7, -1, -1)
            )
        yield tuple(pixels)

def pt_to_image(chrData):
    # create image with 16*16 tiles (128*128 px) from background pattern table
    # data
    image = Image.new("P", (16 * 8, 16 * 8))
    image.putpalette((0,0,0, 85,85,85, 170,170,170, 255,255,255))
    for (ti, tile) in enumerate(decode_pt(chrData)):
        for (pi, pixel) in enumerate(tile):
            (ty, tx) = divmod(ti, 16)
            (py, px) = divmod(pi, 8)
            image.putpixel((tx * 8 + px, ty * 8 + py), pixel)
    return image

def main():
    if len(sys.argv) not in (2, 5):
        sys.exit(HELP_TEXT)

    inputFile = sys.argv[1]

    if len(sys.argv) == 5:
        summary = False
        (outputFile, areaType, area) = sys.argv[2:5]
        try:
            areaType = int(areaType, 10)
            area = int(area, 10)
        except ValueError:
            sys.exit("AREATYPE and AREA must be integers.")
        if not 0 <= areaType <= 3:
            sys.exit("AREATYPE must be 0-3.")
        if area < 0:
            sys.exit("AREA must be 0 or greater.")
    else:
        summary = True

    if not os.path.isfile(inputFile):
        sys.exit("Input file not found.")

    # read input file
    try:
        with open(inputFile, "rb") as handle:
            handle.seek(0)
            fileData = handle.read()
    except OSError:
        sys.exit("File read error.")

    # read iNES header
    fileInfo = decode_ines_header(fileData)
    if fileInfo is None:
        sys.exit("Not a valid iNES ROM file.")
    if fileInfo["prgSize"] < 32 * 1024 \
    or fileInfo["chrSize"] < 8 * 1024:
        sys.exit("The file doesn't look like Super Mario Bros.")

    # read PRG & CHR ROM
    prgData = fileData[
        fileInfo["prgStart"]:fileInfo["prgStart"]+fileInfo["prgSize"]
    ]
    chrData = fileData[
        fileInfo["chrStart"]:fileInfo["chrStart"]+fileInfo["chrSize"]
    ]
    del fileData

    # create image of background pattern table (16*16 tiles, 128*128 px)
    bgTileImage = pt_to_image(chrData)
    del chrData

    if summary:
        print_summary(prgData)
    else:
        areaImage = extract_map(areaType, area, prgData, bgTileImage)
        with open(outputFile, "wb") as handle:
            handle.seek(0)
            areaImage.save(handle, "png")

main()

# extract map data from NES Super Mario Bros.

import argparse, os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

AREA_TYPES = ("water", "ground", "underground", "castle")
WORLD_CNT = 8
AREA_CNT1 = 36
AREA_CNT2 = 34

# PRG ROM addresses of labels (label name in doppelganger's disassembly in "quotes")
WORLD_ADDRESSES   = 0x1cb4  # "WorldAddrOffsets"
AREA_ADDRESSES    = 0x1cbc  # "AreaAddrOffsets"
ENEMY_ADDRESSES   = 0x1ce0  # "EnemyAddrHOffsets"
ENEMY_ADDR_LO     = 0x1ce4  # "EnemyDataAddrLow"
ENEMY_ADDR_HI     = 0x1d06  # "EnemyDataAddrHigh"
TERRAIN_ADDRESSES = 0x1d28  # "AreaDataHOffsets"
TERRAIN_ADDR_LO   = 0x1d2c  # "AreaDataAddrLow"
TERRAIN_ADDR_HI   = 0x1d4e  # "AreaDataAddrHigh"

def parse_arguments():
    # parse command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Extract maps from NES Super Mario Bros. to PNG files."
    )
    parser.add_argument(
        "input_file", help="Super Mario Bros. ROM file in iNES format (.nes, US version)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")

    return args

def is_super_mario_bros(fileInfo):
    # is the file likely Super Mario Bros.? don't validate too accurately because the file may be
    # a hack; fileInfo: from qneslib.ines_header_decode()
    return (
        fileInfo["prgSize"]     == 32 * 1024
        and fileInfo["chrSize"] == 8 * 1024
        and fileInfo["mapper"]  == 0
    )

def extract_map(sourceHnd, args):
    # parse iNES header
    fileInfo = qneslib.ines_header_decode(sourceHnd)
    if fileInfo is None:
        sys.exit("Not a valid iNES ROM file.")

    if not is_super_mario_bros(fileInfo):
        sys.exit("The file doesn't look like Super Mario Bros.")

    # read PRG ROM
    sourceHnd.seek(fileInfo["prgStart"])
    prgData = sourceHnd.read(fileInfo["prgSize"])

    world = 0  # 0-7
    area = 0  # 0-4

    # get area type and offset (done by "LoadAreaPointer" subroutine)
    areaPointer = prgData[AREA_ADDRESSES + prgData[WORLD_ADDRESSES+world] + area]
    areaType = (areaPointer & 0x60) >> 5  # 0=water, 1=ground, 2=underground, 3=castle
    areaOffset = areaPointer & 0x1f
    print(f"Area: {AREA_TYPES[areaType]} #{areaOffset}")

    # get enemy data address (done by "GetAreaDataAddrs" subroutine)
    enemyOffset = prgData[ENEMY_ADDRESSES+areaType] + areaOffset
    enemyAddr = prgData[ENEMY_ADDR_LO+enemyOffset] + prgData[ENEMY_ADDR_HI+enemyOffset] * 256 - 0x8000
    assert enemyAddr >= 0

    # get terrain data address (also done by "GetAreaDataAddrs" subroutine)
    terrainOffset = prgData[TERRAIN_ADDRESSES+areaType] + areaOffset
    terrainAddr = prgData[TERRAIN_ADDR_LO+terrainOffset] \
    + prgData[TERRAIN_ADDR_HI+terrainOffset] * 256 - 0x8000
    assert terrainAddr >= 0

    # read enemy data
    enemyData = bytearray()
    for byte in prgData[enemyAddr:]:
        if byte == 0xff:
            break
        enemyData.append(byte)
    assert len(enemyData) <= 256
    print(f"Enemy data (@ {enemyAddr:04x}):", " ".join(f"{b:02x}" for b in enemyData))

    # read terrain data
    terrainData = bytearray()
    for byte in prgData[terrainAddr:]:
        if byte == 0xfd:
            break
        terrainData.append(byte)
    assert 2 <= len(terrainData) <= 256
    print(f"Terrain header (@ {terrainAddr:04x}):", " ".join(f"{b:02x}" for b in terrainData[:2]))
    print(f"Terrain data (@ {terrainAddr+2:04x}):", " ".join(f"{b:02x}" for b in terrainData[2:]))

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as handle:
            extract_map(handle, args)
    except OSError:
        sys.exit("File read error.")

if __name__ == "__main__":
    main()

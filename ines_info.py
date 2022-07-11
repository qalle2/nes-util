import os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# parse command line arguments
if len(sys.argv) != 2:
    sys.exit("Print information of an iNES ROM file (.nes).")
inputFile = sys.argv[1]
if not os.path.isfile(inputFile):
    sys.exit("File not found.")

# get info
try:
    with open(inputFile, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
except OSError:
    sys.exit("Error reading the file.")
if fileInfo is None:
    sys.exit("Invalid iNES ROM file.")

# print info
print("trainer size:", fileInfo["trainerSize"])
print("PRG ROM size:", fileInfo["prgSize"])
print("CHR ROM size:", fileInfo["chrSize"])
print("iNES mapper number:", fileInfo["mapper"])
print("Mapper name:", qneslib.mapper_name(fileInfo["mapper"]))
print(
    "name table mirroring:",
    {"h": "horizontal", "v": "vertical", "f": "four-screen"}[fileInfo["mirroring"]]
)
print("has extra RAM:", ["no", "yes"][fileInfo["extraRam"]])

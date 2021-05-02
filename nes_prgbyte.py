import os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# read args
if len(sys.argv) != 3:
    sys.exit(
        "Get byte value at specified PRG ROM address in an iNES ROM file (.nes). Args: file "
        "address_in_hexadecimal"
    )
(filename, prgAddr) = sys.argv[1:]

# parse address (continue validation later)
try:
    prgAddr = int(prgAddr, 16)
except ValueError:
    sys.exit("Invalid PRG ROM address.")

# read byte from file
if not os.path.isfile(filename):
    sys.exit("File not found.")
try:
    with open(filename, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")
        if not 0 <= prgAddr < fileInfo["prgSize"]:
            sys.exit("Invalid PRG ROM address.")
        handle.seek(fileInfo["prgStart"] + prgAddr)
        value = handle.read(1)[0]
except OSError:
    sys.exit("Error reading the file.")

print(f"0x{value:02x}")

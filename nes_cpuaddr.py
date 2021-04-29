import os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# read args
if len(sys.argv) != 3:
    sys.exit(
        "Convert an NES PRG ROM address into possible CPU addresses using the iNES ROM file "
        "(.nes). Args: file PRG_ROM_address_in_hexadecimal"
    )
(filename, prgAddr) = sys.argv[1:]

# validate file
if not os.path.isfile(filename):
    sys.exit("File not found.")
try:
    with open(filename, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")
except OSError:
    sys.exit("Error reading the file.")

if not qneslib.is_mapper_known(fileInfo["mapper"]):
    print(
        f"Warning: unknown mapper {fileInfo['mapper']}; assuming 8-KiB PRG ROM banks.",
        file=sys.stderr
    )

# parse and validate address
try:
    prgAddr = int(prgAddr, 16)
    if not 0 <= prgAddr < fileInfo["prgSize"]:
        raise ValueError
except ValueError:
    sys.exit("Invalid PRG ROM address.")

prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
cpuAddresses = qneslib.address_prg_to_cpu(prgAddr, prgBankSize)
print("Possible CPU addresses:", ", ".join(f"0x{addr:04x}" for addr in sorted(cpuAddresses)))

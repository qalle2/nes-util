import os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# read args
if len(sys.argv) != 3:
    sys.exit(
        "Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM file (.nes). "
        "Args: file code"
    )
(filename, code) = sys.argv[1:]

if not os.path.isfile(filename):
    sys.exit("File not found.")

# decode the code
values = qneslib.game_genie_decode(code)
if values is None:
    sys.exit("Invalid code.")
(cpuAddr, compareValue) = (values[0], values[2])

try:
    with open(filename, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")

        # get PRG ROM addresses
        prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
        prgAddrGen = qneslib.address_cpu_to_prg(cpuAddr, prgBankSize, fileInfo["prgSize"])
        if compareValue is None:
            # 6-letter code
            prgAddresses = list(prgAddrGen)
        else:
            # 8-letter code
            prgAddresses = []
            for prgAddr in prgAddrGen:
                handle.seek(fileInfo["prgStart"] + prgAddr)
                if handle.read(1)[0] == compareValue:
                    prgAddresses.append(prgAddr)
except OSError:
    sys.exit("Error reading the file.")

if not qneslib.is_mapper_known(fileInfo["mapper"]):
    print(f"Warning: unknown mapper {fileInfo['mapper']}.", file=sys.stderr)

print(", ".join(f"0x{a:04x}" for a in prgAddresses))

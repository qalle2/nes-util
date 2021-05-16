import os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# read args
if len(sys.argv) != 3:
    sys.exit(
        "Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM file (.nes). "
        "Args: file code"
    )
(filename, code) = sys.argv[1:]

# decode the code
values = qneslib.game_genie_decode(code)
if values is None:
    sys.exit("Invalid code.")
(cpuAddr, replaceValue, compareValue) = values

if not os.path.isfile(filename):
    sys.exit("File not found.")

try:
    with open(filename, "rb") as handle:
        # get file info
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")
        # get PRG ROM addresses
        prgAddresses = []
        if compareValue is None or compareValue != replaceValue:
            if compareValue is None:
                # 6-letter code (old value must not equal replace value)
                validValues = set(range(0x100)) - {replaceValue,}  # 6-letter code
            else:
                # 8-letter code (old value must equal compare value)
                validValues = {compareValue,}
            prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
            for prgAddr in qneslib.address_cpu_to_prg(cpuAddr, prgBankSize, fileInfo["prgSize"]):
                handle.seek(fileInfo["prgStart"] + prgAddr)
                if handle.read(1)[0] in validValues:
                    prgAddresses.append(prgAddr)
except OSError:
    sys.exit("Error reading the file.")

if not qneslib.is_mapper_known(fileInfo["mapper"]):
    print(f"Warning: unknown mapper {fileInfo['mapper']}.", file=sys.stderr)

print(", ".join(f"0x{a:04x}" for a in prgAddresses))

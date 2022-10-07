import os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# read args
if len(sys.argv) != 3:
    sys.exit(
        "Convert a 6-letter NES Game Genie code into 8 letters using the "
        "iNES ROM file (.nes). Can be useful if the 6-letter code has "
        "unintended side effects. Args: file code"
    )
(filename, code) = sys.argv[1:]

# validate code; get CPU address and replace value
decoded = qneslib.game_genie_decode(code)
if decoded is None or decoded[2] is not None:
    sys.exit("Not a valid 6-letter Game Genie code.")
(cpuAddr, repl) = (decoded[0], decoded[1])

if not os.path.isfile(filename):
    sys.exit("File not found.")

try:
    with open(filename, "rb") as handle:
        # get file info
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")
        if not qneslib.is_prg_bankswitched(
            fileInfo["prgSize"], fileInfo["mapper"]
        ):
            print(
                "Note: the game does not use PRG ROM bankswitching, so there "
                "is no reason to use eight-letter codes.", file=sys.stderr
            )
        # get compare values (bytes corresponding to specified CPU address
        # in each PRG ROM bank)
        prgBankSize = qneslib.min_prg_bank_size(
            fileInfo["prgSize"], fileInfo["mapper"]
        )
        compValues = set()
        for prgAddr in qneslib.address_cpu_to_prg(
            cpuAddr, prgBankSize, fileInfo["prgSize"]
        ):
            handle.seek(fileInfo["prgStart"] + prgAddr)
            compValues.add(handle.read(1)[0])
except OSError:
    sys.exit("Error reading the file.")

# ignore a compare value that equals the replace value
compValues.discard(repl)

if not qneslib.is_mapper_known(fileInfo["mapper"]):
    print(f"Warning: unknown mapper {fileInfo['mapper']}.", file=sys.stderr)

print(", ".join(sorted(
    qneslib.game_genie_encode(cpuAddr, repl, c) for c in compValues
)))

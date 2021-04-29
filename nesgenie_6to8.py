import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

# read args
if len(sys.argv) != 3:
    sys.exit(
        "Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). "
        "Args: file code"
    )
(filename, code) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

# validate code; get CPU address and replace value
decoded = qneslib.game_genie_decode(code)
if decoded is None:
    sys.exit("Invalid Game Genie code.")
if decoded[2] is not None:
    sys.exit("The code must be six letters.")
(cpuAddr, repl) = (decoded[0], decoded[1])

try:
    with open(filename, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")
        if not qneslib.is_prg_bankswitched(fileInfo["prgSize"], fileInfo["mapper"]):
            sys.exit("There is no reason to use eight-letter codes with this game.")

        # get compare values (bytes corresponding to specified CPU address in each PRG ROM bank)
        prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
        compValues = set()
        for prgAddr in qneslib.address_cpu_to_prg(cpuAddr, prgBankSize, fileInfo["prgSize"]):
            handle.seek(fileInfo["prgStart"] + prgAddr)
            compValues.add(handle.read(1)[0])
except OSError:
    sys.exit("Error reading the file.")

# ignore a compare value that equals the replace value
compValues.discard(repl)

if not qneslib.is_mapper_known(fileInfo["mapper"]):
    print(f"Warning: unknown mapper {fileInfo['mapper']}.", file=sys.stderr)

print(", ".join(sorted(qneslib.game_genie_encode(cpuAddr, repl, comp) for comp in compValues)))

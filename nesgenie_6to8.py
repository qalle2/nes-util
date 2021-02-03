"""Converts a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes)."""

import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def get_compare_values(handle, cpuAddr):
    """For each PRG ROM bank, yield the byte corresponding to the specified CPU address."""

    fileInfo = qneslib.ines_header_decode(handle)

    for prgAddr in qneslib.cpu_address_to_prg_addresses(handle, cpuAddr):
        handle.seek(fileInfo["prgStart"] + prgAddr)
        yield handle.read(1)[0]

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). "
            "Args: file code"
        )
    (file, code) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    # validate code; get CPU address and replace value
    decoded = qneslib.game_genie_decode(code)
    if decoded is None:
        sys.exit("Invalid Game Genie code.")
    if decoded[2] is not None:
        sys.exit("The code must be six letters.")
    (cpuAddr, repl) = (decoded[0], decoded[1])

    try:
        with open(file, "rb") as handle:
            fileInfo = qneslib.ines_header_decode(handle)
            if fileInfo is None:
                sys.exit("Invalid iNES ROM file.")

            if not qneslib.is_prg_bankswitched(fileInfo["prgSize"], fileInfo["mapper"]):
                sys.exit("There is no reason to use eight-letter codes with this game.")

            compValues = set(get_compare_values(handle, cpuAddr))
    except OSError:
        sys.exit("Error reading the file.")

    # ignore a compare value that equals the replace value
    compValues.discard(repl)

    print(", ".join(sorted(
        qneslib.game_genie_encode(cpuAddr, repl, comp) for comp in compValues
    )))

if __name__ == "__main__":
    main()

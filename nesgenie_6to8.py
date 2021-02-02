"""Converts a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes)."""

import sys
import ineslib
import nesgenielib
import neslib

def get_compare_values(handle, CPUAddr):
    """For each PRG ROM bank, yield the byte corresponding to the specified CPU address."""

    fileInfo = ineslib.parse_iNES_header(handle)

    for PRGAddr in neslib.CPU_address_to_PRG_addresses(handle, CPUAddr):
        handle.seek(16 + fileInfo["trainerSize"] + PRGAddr)
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
    decoded = nesgenielib.decode_code(code)
    if decoded is None:
        sys.exit("Invalid Game Genie code.")
    if decoded[2] is not None:
        sys.exit("The code must be six letters.")
    (CPUAddr, repl) = (decoded[0], decoded[1])

    try:
        with open(file, "rb") as handle:
            # read iNES header
            try:
                fileInfo = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as error:
                sys.exit("Error: " + str(error))

            if not ineslib.is_PRG_bankswitched(fileInfo):
                sys.exit("There is no reason to use eight-letter codes with this game.")

            compValues = set(get_compare_values(handle, CPUAddr))
    except OSError:
        sys.exit("Error reading the file.")

    # ignore a compare value that equals the replace value
    compValues.discard(repl)

    print(", ".join(sorted(nesgenielib.encode_code(CPUAddr, repl, comp) for comp in compValues)))

if __name__ == "__main__":
    main()

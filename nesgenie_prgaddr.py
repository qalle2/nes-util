"""Find the PRG ROM addresses affected by an NES Game Genie code."""

import os
import sys
import ineslib
import nesgenielib
import neslib

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM file "
            "(.nes). Args: file code"
        )
    (file, code) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    if not os.path.isfile(file):
        sys.exit("File not found.")

    # decode the code
    try:
        (CPUAddr, replaceValue, compareValue) = nesgenielib.decode_code(code)
    except nesgenielib.NESGenieError:
        sys.exit("Invalid NES Game Genie code.")

    try:
        with open(file, "rb") as handle:
            # validate file
            try:
                ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as error:
                sys.exit("Error: " + str(error))

            # get PRG addresses
            print(", ".join(
                f"0x{PRGAddr:04x}" for PRGAddr
                in neslib.CPU_address_to_PRG_addresses(handle, CPUAddr, compareValue)
            ))
    except OSError:
        sys.exit("Error reading the file.")

if __name__ == "__main__":
    main()

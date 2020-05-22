"""Convert an NES PRG ROM address into possible CPU addresses for the Game Genie."""

import os
import sys
import ineslib

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Convert an NES PRG ROM address into possible CPU addresses for the Game Genie, using "
            "the iNES ROM file (.nes). Args: file address_in_hexadecimal"
        )
    (file, PRGAddr) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    try:
        PRGAddr = int(PRGAddr, 16)
    except ValueError:
        sys.exit("The PRG ROM address is not a valid hexadecimal integer.")

    if not os.path.isfile(file):
        sys.exit("File not found.")

    try:
        with open(file, "rb") as handle:
            # parse iNES header
            try:
                fileInfo = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as error:
                sys.exit("Error: " + str(error))
    except OSError:
        sys.exit("Error reading the file.")

    if not 0 <= PRGAddr < fileInfo["PRGSize"]:
        sys.exit("PRG ROM address out of range.")

    bankSize = ineslib.get_PRG_bank_size(fileInfo)
    print("PRG ROM bank size: {:d} KiB".format(bankSize // 1024))

    CPUAddresses = ineslib.PRG_address_to_CPU_addresses(PRGAddr, bankSize)
    print("Possible CPU addresses:", " ".join(f"0x{addr:04x}" for addr in sorted(CPUAddresses)))

if __name__ == "__main__":
    main()

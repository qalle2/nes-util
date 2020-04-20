"""Find the PRG ROM addresses affected by an NES Game Genie code."""

import os
import sys
import ineslib
import nesgenielib

def get_PRG_addresses(handle, fileInfo, CPUAddress, compareValue):
    """Generate PRG ROM addresses that contain compareValue at CPUAddress.
    fileInfo: from ineslib.parse_iNES_header()
    CPUAddress: NES CPU address (0x8000-0xffff)
    compareValue: 0x00-0xff or None"""

    PRGStart = 16 + fileInfo["trainerSize"]
    PRGBankSize = min(ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"]), fileInfo["PRGSize"])

    # get offset within each bank by ignoring the most significant bits of the address
    offset = CPUAddress & (PRGBankSize - 1)

    # for each bank, read the byte at that offset
    for PRGPos in range(offset, fileInfo["PRGSize"], PRGBankSize):
        handle.seek(PRGStart + PRGPos)
        if compareValue is None or handle.read(1)[0] == compareValue:
            yield PRGPos

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

    # validate and decode the code
    decoded = nesgenielib.decode_code(code)
    if decoded is None:
        sys.exit("Invalid NES Game Genie code.")
    CPUAddress = decoded[0]
    compareValue = decoded[2] if len(decoded) == 3 else None

    try:
        with open(file, "rb") as handle:
            # parse iNES header
            try:
                fileInfo = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error: " + str(e))
            # get PRG addresses corresponding to CPU address
            for PRGAddr in get_PRG_addresses(handle, fileInfo, CPUAddress, compareValue):
                print(f"0x{PRGAddr:04x}")
    except OSError:
        sys.exit("Error reading the file.")

if __name__ == "__main__":
    main()

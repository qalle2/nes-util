"""Convert an eight-letter NES Game Genie code from one version of a game to another using both
iNES ROM files (.nes).
TODO:
    - try to match slices only partially
    - handle addresses near the start/end of PRG ROM correctly
    - support six-letter codes
    - make pylint happy
"""

import os
import sys
import ineslib
import nesgenielib

SLICE_LEN = 2  # length of slice before and after the address

def get_PRG_addresses(CPUAddress, compareValue, handle, fileInfo):
    """Generate PRG ROM addresses that match the CPU address and the compare value in the file."""

    # get offset within each bank by ignoring the most significant bits of the CPU address
    PRGBankSize = min(ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"]), fileInfo["PRGSize"])
    offset = CPUAddress & (PRGBankSize - 1)
    # for each bank, if that offset matches the compare value, yield the PRG ROM address
    for PRGPos in range(offset, fileInfo["PRGSize"], PRGBankSize):
        handle.seek(16 + fileInfo["trainerSize"] + PRGPos)
        byte = handle.read(1)[0]
        if byte == compareValue:
            yield PRGPos

def filter_PRG_addresses(addresses, PRGSize):
    """Return PRG ROM addresses that aren't too close to the start or the end of the PRG ROM."""

    filtered = []
    maxAddr = PRGSize - 1 - SLICE_LEN
    for addr in addresses:
        if SLICE_LEN <= addr <= maxAddr:
            filtered.append(addr)
        else:
            print(
                "Warning: skipping a PRG ROM address that's too close to the start or the "
                "end of the PRG ROM (because this program is too stupid to handle that).",
                file=sys.stderr
            )
    return filtered

def get_PRG_slice(PRGAddr, PRGStart, handle):
    """Get a slice of 2 * SLICE_LEN + 1 bytes from the PRG ROM. The addresses must not be too close
    to the start or the end of the PRG ROM."""

    handle.seek(PRGStart + PRGAddr - SLICE_LEN)
    return handle.read(2 * SLICE_LEN + 1)

def find_slices_in_PRG(slices, PRGStart, PRGSize, handle):
    """Try to find each slice (bytes) in the PRG data. Yield one result per call."""

    # read PRG ROM data
    handle.seek(PRGStart)
    PRGData = handle.read(PRGSize)
    # for each slice, find all occurrences and yield corresponding PRG ROM addresses
    for slice_ in slices:
        searchStart = 0
        while True:
            try:
                pos = PRGData.index(slice_, searchStart)
            except ValueError:
                break
            yield pos + SLICE_LEN
            searchStart = pos + SLICE_LEN + 1

def PRG_addresses_to_CPU_addresses(PRGAddresses, fileInfo):
    """Convert PRG ROM addresses into CPU ROM addresses. Yield one address per call."""

    PRGBankSize = min(ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"]), fileInfo["PRGSize"])
    for addr in PRGAddresses:
        # assuming 32-KiB banks
        offset32k = addr & (32 * 1024 - 1)
        yield 0x8000 + offset32k
        # assuming 16-KiB banks
        if PRGBankSize <= 16 * 1024:
            offset16k = addr & (16 * 1024 - 1)
            yield 0x8000 + offset16k
            yield 0x8000 + 16 * 1024 + offset16k
            if PRGBankSize == 8 * 1024:
                # assuming 8-KiB banks
                offset8k = addr & (8 * 1024 - 1)
                yield 0x8000 + offset8k
                yield 0x8000 + 8 * 1024 + offset8k
                yield 0x8000 + 16 * 1024 + offset8k
                yield 0x8000 + 24 * 1024 + offset8k

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 4:
        sys.exit(
            "Convert an eight-letter NES Game Genie code from one version of a game to another "
            "using both iNES ROM files (.nes). Args: code_for_file1 file1 file2"
        )
    (code, file1, file2) = (sys.argv[1], sys.argv[2], sys.argv[3])

    # validate and decode the code
    decoded = nesgenielib.decode_code(code)
    if decoded is None:
        sys.exit("Invalid Game Genie code.")
    if len(decoded) == 2:
        sys.exit("Only eight-letter codes are supported for now.")
    canonicalCode = nesgenielib.encode_code(*decoded)
    print(canonicalCode, "=", nesgenielib.stringify_values(*decoded))

    (address, replaceValue, compareValue) = (decoded[0], decoded[1], decoded[2])

    if not os.path.isfile(file1):
        sys.exit("file1 not found.")
    if not os.path.isfile(file2):
        sys.exit("file2 not found.")

    try:
        with open(file1, "rb") as handle:
            try:
                fileInfo1 = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error in file1: " + str(e))
            PRGAddresses1 = list(get_PRG_addresses(address, compareValue, handle, fileInfo1))
            PRGAddresses1 = filter_PRG_addresses(PRGAddresses1, fileInfo1["PRGSize"])
            if not PRGAddresses1:
                sys.exit("No possible PRG ROM addresses found in file1.")
            print(
                "Corresponding PRG ROM address(es) in file1:",
                " ".join("0x{:04x}".format(addr) for addr in PRGAddresses1)
            )
            slices1 = set(
                get_PRG_slice(addr, 16 + fileInfo1["trainerSize"], handle) for addr in PRGAddresses1
            )
    except OSError:
        sys.exit("Error reading file1.")

    print(
        "Unique slices centered at those addresses in file1 (hexadecimal):",
        " ".join(
            "".join(format(byte, "02x") for byte in slice_) for slice_ in sorted(slices1)
        )
    )

    try:
        with open(file2, "rb") as handle:
            try:
                fileInfo2 = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error in file2: " + str(e))
            PRGAddresses2 = set(find_slices_in_PRG(
                slices1, 16 + fileInfo2["trainerSize"], fileInfo2["PRGSize"], handle
            ))
    except OSError:
        sys.exit("Error reading file2.")

    if not PRGAddresses2:
        sys.exit("No possible PRG ROM addresses found in file2.")
    print(
        "PRG ROM addresses containing one of those slices in file2:",
        " ".join("0x{:04x}".format(addr) for addr in sorted(PRGAddresses2))
    )

    CPUAddresses = set(PRG_addresses_to_CPU_addresses(PRGAddresses2, fileInfo2))
    print(
        "Corresponding CPU ROM addresses:",
        " ".join("0x{:04x}".format(addr) for addr in sorted(CPUAddresses))
    )
    print("Corresponding Game Genie codes:", " ".join(sorted(
        nesgenielib.encode_code(addr, replaceValue, compareValue) for addr in CPUAddresses
    )))

if __name__ == "__main__":
    main()

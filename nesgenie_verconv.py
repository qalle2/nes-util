"""Convert an eight-letter NES Game Genie code from one version of a game to another using both
iNES ROM files (.nes).
TODO:
    - handle addresses near the start/end of PRG ROM correctly
    - support six-letter codes
"""

import argparse
import os
import sys
import ineslib
import nesgenielib

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Read two versions (e.g. Japanese and US) of the same NES game in iNES format "
        "(.nes) and a Game Genie code for one of the versions. Output the equivalent code for the "
        "other version of the game."
    )

    parser.add_argument(
        "-s", "--slice-length", type=int, default=4,
        help="Length of PRG ROM slices to compare, before and after the relevant byte (so the "
        "actual length is twice this value plus one). 1 or greater, default=4. Decrease to get "
        "more results."
    )
    parser.add_argument(
        "-d", "--max-different-bytes", type=int, default=1,
        help="Maximum number of non-matching bytes allowed in each pair of PRG ROM slices to "
        "compare. (The relevant byte in the middle of the slice must always match.) 0 or greater, "
        "default=1. Increase to get more results."
    )
    parser.add_argument(
        "code", help="An eight-letter NES Game Genie code that is known to work with file1."
    )
    parser.add_argument(
        "file1", help="An iNES ROM file (.nes) to read. The game your code is known to work with."
    )
    parser.add_argument(
        "file2", help="Another iNES ROM file (.nes) to read. The equivalent code for this game "
        "will be searched for."
    )

    args = parser.parse_args()

    if args.slice_length < 1:
        sys.exit("Invalid slice length.")
    if args.max_different_bytes < 0:
        sys.exit("Invalid maximum number of non-matching bytes.")
    if not os.path.isfile(args.file1):
        sys.exit("file1 not found.")
    if not os.path.isfile(args.file2):
        sys.exit("file2 not found.")

    return args

def decode_code(code):
    """Parse a Game Genie code from the command line arguments.
    return: (CPU address, replace value, compare value)"""

    decoded = nesgenielib.decode_code(code)
    if decoded is None:
        sys.exit("Invalid Game Genie code.")
    if len(decoded) == 2:
        sys.exit("Only eight-letter codes are supported for now.")
    return decoded

def get_PRG_addresses(CPUAddress, compareValue, handle, fileInfo):
    """Generate PRG ROM addresses that match the CPU address and the compare value in the file."""

    # get offset within each bank by ignoring the most significant bits of the CPU address
    PRGBankSize = min(ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"]), fileInfo["PRGSize"])
    offset = CPUAddress & (PRGBankSize - 1)

    # for each bank, if that offset matches the compare value, yield the PRG ROM address
    PRGStart = 16 + fileInfo["trainerSize"]
    for PRGPos in range(offset, fileInfo["PRGSize"], PRGBankSize):
        handle.seek(PRGStart + PRGPos)
        byte = handle.read(1)[0]
        if byte == compareValue:
            yield PRGPos

def get_slices_from_PRG(handle, address, compareValue, sliceLen):
    """Generate the PRG ROM slices the address and compareValue may refer to."""

    try:
        fileInfo = ineslib.parse_iNES_header(handle)
    except ineslib.iNESError as e:
        sys.exit("Error in file1: " + str(e))

    # get PRG addresses; delete those too close to the start or the end of the PRG ROM (this
    # program is too stupid to handle those)
    PRGAddresses = get_PRG_addresses(address, compareValue, handle, fileInfo)
    maxPRGAddr = fileInfo["PRGSize"] - 1 - sliceLen
    PRGAddresses = [addr for addr in PRGAddresses if sliceLen <= addr <= maxPRGAddr]
    if not PRGAddresses:
        sys.exit("No possible PRG ROM addresses found in file1.")

    print("Corresponding PRG ROM addresses in file1:")
    for addr in PRGAddresses:
        print("  0x{:04x}".format(addr))

    PRGStart = 16 + fileInfo["trainerSize"]
    for addr in PRGAddresses:
        handle.seek(PRGStart + addr - sliceLen)
        yield handle.read(2 * sliceLen + 1)

def find_slices_in_PRG(handle, fileInfo, slices, args):
    """Try to find each slice (bytes) in the PRG data. Yield one result per call."""

    # read PRG ROM data
    handle.seek(16 + fileInfo["trainerSize"])
    PRGData = handle.read(fileInfo["PRGSize"])

    # for each slice, find all occurrences similar enough and yield corresponding PRG ROM addresses
    for pos in range(fileInfo["PRGSize"] - 2 * args.slice_length):
        for slice_ in slices:
            if slice_[args.slice_length] == PRGData[pos+args.slice_length]:
                commonByteCnt = sum(
                    1 for (byte1, byte2) in zip(slice_, PRGData[pos:pos+2*args.slice_length+1])
                    if byte1 == byte2
                )
                if commonByteCnt >= args.slice_length * 2 + 1 - args.max_different_bytes:
                    yield pos + args.slice_length

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

    args = parse_arguments()

    (address, replaceValue, compareValue) = decode_code(args.code)
    print(
        f"Decoded code: address=0x{address:04x}, replace=0x{replaceValue:02x}, "
        f"compare=0x{compareValue:02x}"
    )

    try:
        with open(args.file1, "rb") as handle:
            slices1 = set(get_slices_from_PRG(handle, address, compareValue, args.slice_length))
    except OSError:
        sys.exit("Error reading file1.")

    print("Unique slices centered at those addresses in file1:")
    for slice_ in sorted(slices1):
        print("  " + " ".join(f"0x{byte:02x}" for byte in slice_))

    try:
        with open(args.file2, "rb") as handle:
            try:
                fileInfo2 = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error in file2: " + str(e))
            PRGAddresses2 = set(find_slices_in_PRG(handle, fileInfo2, slices1, args))
    except OSError:
        sys.exit("Error reading file2.")

    if not PRGAddresses2:
        sys.exit("No possible PRG ROM addresses found in file2.")
    print("PRG ROM addresses containing one of those slices in file2:")
    for addr in sorted(PRGAddresses2):
        print(f"  0x{addr:04x}")

    CPUAddresses = set(PRG_addresses_to_CPU_addresses(PRGAddresses2, fileInfo2))
    print("Game Genie codes:")
    for addr in sorted(CPUAddresses):
        print("  address=0x{:04x}, replace=0x{:02x}, compare=0x{:02x}: {:s}{:s}".format(
            addr, replaceValue, compareValue,
            nesgenielib.encode_code(addr, replaceValue, compareValue),
            " (likely)" if abs(addr - address) <= 256 else ""
        ))

if __name__ == "__main__":
    main()

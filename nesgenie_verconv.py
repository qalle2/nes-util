"""Convert an eight-letter NES Game Genie code from one version of a game to another using both
iNES ROM files (.nes).
TODO: make pylint happy"""

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
        "-s", "--slice-length", type=int, default=9,
        help="Length of PRG ROM slices to compare. (Each slice will be equally distributed before "
        "and after its relevant byte if possible.) Minimum=1, default=9. Decrease to get more "
        "results."
    )
    parser.add_argument(
        "-d", "--max-different-bytes", type=int, default=1,
        help="Maximum number of non-matching bytes allowed in each pair of PRG ROM slices to "
        "compare. (The relevant byte, usually in the middle of the slice, must always match.) "
        "Minimum=0, default=1. Increase to get more results."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print technical information."
    )
    parser.add_argument(
        "code",
        help="An NES Game Genie code that is known to work with file1. Six-letter codes are not "
        "allowed if file1 uses PRG ROM bankswitching."
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

def is_PRG_ROM_bankswitched(fileInfo):
    """Is the PRG ROM of an NES game bankswitched? (May give false positives.)
    fileInfo: from ineslib.parse_iNES_header()"""

    return fileInfo["PRGSize"] > ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"])

def get_banked_PRG_addresses(handle, fileInfo, CPUAddress, compareValue):
    """Generate PRG ROM addresses that match the CPU address and the compare value in the file.
    (The file may use PRG ROM bankswitching.)"""

    # get offset within each bank by ignoring the most significant bits of the CPU address
    PRGBankSize = min(ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"]), fileInfo["PRGSize"])
    offset = CPUAddress & (PRGBankSize - 1)

    # for each bank, if that offset matches the compare value, yield the PRG ROM address
    PRGStart = 16 + fileInfo["trainerSize"]
    for PRGPos in range(offset, fileInfo["PRGSize"], PRGBankSize):
        handle.seek(PRGStart + PRGPos)
        if handle.read(1)[0] == compareValue:
            yield PRGPos

def get_PRG_slices(handle, PRGAddresses, sliceLen, fileInfo):
    """Generate the slice surrounding each PRG ROM address."""

    PRGStart = 16 + fileInfo["trainerSize"]

    for PRGAddr in PRGAddresses:
        # get length of slice before/after the relevant byte
        lenBefore = min(sliceLen // 2, PRGAddr)
        lenAfter = min(sliceLen - lenBefore - 1, fileInfo["PRGSize"] - PRGAddr - 1)
        # read slice
        handle.seek(PRGStart + PRGAddr - lenBefore)
        slice_ = handle.read(lenBefore + 1 + lenAfter)
        # yield bytes before and after the relevant byte
        yield (slice_[:lenBefore], slice_[lenBefore+1:])

def find_slices_in_PRG(handle, slices, compareValue, fileInfo, args):
    """Generate PRG addresses of each slice."""

    # read PRG ROM data
    handle.seek(16 + fileInfo["trainerSize"])
    PRGData = handle.read(fileInfo["PRGSize"])

    for (before, after) in slices:
        slice_ = before + bytes((compareValue,)) + after
        for PRGAddr in range(fileInfo["PRGSize"] - args.slice_length + 1):
            # the relevant byte must always match
            if PRGData[PRGAddr+len(before)] == compareValue:
                # if not too many different bytes, yield PRG address of relevant byte
                differentByteCnt = sum(
                    1 for (byte1, byte2) in zip(slice_, PRGData[PRGAddr:PRGAddr+args.slice_length])
                    if byte1 != byte2
                )
                if differentByteCnt <= args.max_different_bytes:
                    yield PRGAddr + len(before)

def PRG_addresses_to_CPU_addresses(PRGAddresses, fileInfo):
    """Generate CPU addresses from PRG addresses."""

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

    decoded = nesgenielib.decode_code(args.code)
    if decoded is None:
        sys.exit("Invalid Game Genie code.")
    (address, replaceValue, compareValue) \
    = (decoded[0], decoded[1], decoded[2] if len(decoded) == 3 else None)

    if args.verbose:
        print("Decoded code: address=0x{:04x}, replace=0x{:02x}, compare={:s}".format(
            address, replaceValue, "none" if compareValue is None else f"0x{compareValue:02x}"
        ))

    # read file1
    try:
        with open(args.file1, "rb") as handle:
            # get info from iNES header
            try:
                fileInfo1 = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error in file1: " + str(e))

            # get PRG addresses
            if compareValue is None:
                # using a six-letter code
                if is_PRG_ROM_bankswitched(fileInfo1):
                    sys.exit(
                        "file1 seems to use PRG ROM bankswitching, so six-letter codes are not "
                        "allowed."
                    )
                PRGAddresses1 = [address & (fileInfo1["PRGSize"] - 1)]
                # also get a fake compare value
                handle.seek(16 + fileInfo1["trainerSize"] + PRGAddresses1[0])
                compareValue = handle.read(1)[0]
            else:
                # using an eight-letter code
                PRGAddresses1 = get_banked_PRG_addresses(handle, fileInfo1, address, compareValue)
            PRGAddresses1 = list(PRGAddresses1)

            # get bytestrings surrounding the addresses
            slices = set(get_PRG_slices(handle, PRGAddresses1, args.slice_length, fileInfo1))
    except OSError:
        sys.exit("Error reading file1.")

    if args.verbose:
        print("Corresponding PRG ROM addresses in file1:")
        for addr in PRGAddresses1:
            print(f"  0x{addr:04x}")
        print("Unique bytestrings around those addresses in file1 (exact byte in <brackets>):")
        for (before, after) in sorted(slices):
            print("  {:s} <0x{:02x}> {:s}".format(
                " ".join(f"0x{byte:02x}" for byte in before),
                compareValue,
                " ".join(f"0x{byte:02x}" for byte in after)
            ))

    # read file2
    try:
        with open(args.file2, "rb") as handle:
            # get info from iNES header
            try:
                fileInfo2 = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error in file2: " + str(e))
            # find possible addresses for all slices in PRG ROM
            PRGAddresses2 = set(find_slices_in_PRG(handle, slices, compareValue, fileInfo2, args))
    except OSError:
        sys.exit("Error reading file2.")

    # ignore compare value to output six-letter codes if target game is not bankswitched
    compareValue = compareValue if is_PRG_ROM_bankswitched(fileInfo2) else None

    if args.verbose:
        print("PRG ROM addresses in file2 matching one of those bytestrings:")
        for addr in sorted(PRGAddresses2):
            print(f"  0x{addr:04x}")
        if compareValue is None:
            print("file2 does not seem to use PRG ROM bankswitching.")
        else:
            print("file2 seems to use PRG ROM bankswitching.")

    print(f"Game Genie codes for file2 (try the first ones first):")
    CPUAddresses = sorted(set(PRG_addresses_to_CPU_addresses(PRGAddresses2, fileInfo2)))
    CPUAddresses.sort(key=lambda addr: abs(addr - address))
    for addr in CPUAddresses:
        print("  {:s} (address=0x{:04x})".format(
            nesgenielib.encode_code(addr, replaceValue, compareValue), addr
        ))

if __name__ == "__main__":
    main()

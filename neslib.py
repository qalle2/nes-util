"""A library for miscellaneous NES (Nintendo Entertainment System) stuff."""

import ineslib

def PRG_address_to_CPU_addresses(fileInfo, PRGAddr):
    """Generate CPU ROM addresses (0x8000-0xffff) from the PRG ROM address.
    fileInfo: from ineslib.parse_iNES_header()
    handle: handle of an iNES file (.nes)
    bankSize: PRG ROM bank size in bytes"""

    PRGBankSize = ineslib.get_PRG_bank_size(fileInfo)
    offset = PRGAddr & (PRGBankSize - 1)  # address within each bank

    for origin in range(0x8000, 0x10000, PRGBankSize):
        yield origin | offset

def CPU_address_to_PRG_addresses(handle, CPUAddr, compareValue=None):
    """Generate PRG ROM addresses that may correspond to the CPU address.
    handle: handle of an iNES file (.nes)
    CPUAddr: CPU ROM address (0x8000-0xffff)
    compareValue: 0x00-0xff or None"""

    fileInfo = ineslib.parse_iNES_header(handle)
    PRGBankSize = ineslib.get_PRG_bank_size(fileInfo)
    offset = CPUAddr & (PRGBankSize - 1)  # address within each bank

    PRGAddrRange = range(offset, fileInfo["PRGSize"], PRGBankSize)

    if compareValue is None:
        for PRGAddr in PRGAddrRange:
            yield PRGAddr

    # only generate addresses matching the compare value
    for PRGAddr in PRGAddrRange:
        handle.seek(16 + fileInfo["trainerSize"] + PRGAddr)
        if handle.read(1)[0] == compareValue:
            yield PRGAddr

def decode_character_slice(LSBs, MSBs):
    """Decode 8*1 pixels of one character (planar to interleaved).
    LSBs: the least significant bits (8-bit int)
    MSBs: the most significant bits (8-bit int)
    return: pixels (iterable, 8 2-bit big-endian ints)"""

    pixels = 8 * [0]
    for i in range(7, -1, -1):
        pixels[i] = (LSBs & 1) | ((MSBs & 1) << 1)
        LSBs >>= 1
        MSBs >>= 1

    return pixels

def encode_character_slice(charSlice):
    """Encode 8*1 pixels of one character (interleaved to planar).
    charSlice: pixels (8 2-bit big-endian ints)
    return: (8-bit int least_significant_bits, 8-bit int most_significant_bits)"""

    LSBs = MSBs = 0
    for pixel in charSlice:
        LSBs = (LSBs << 1) | (pixel & 1)
        MSBs = (MSBs << 1) | (pixel >> 1)

    return (LSBs, MSBs)

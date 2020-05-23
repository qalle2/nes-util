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

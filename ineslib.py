"""A library for parsing/encoding iNES ROM files (.nes).
See http://wiki.nesdev.com/w/index.php/INES"""

_INES_ID = b"NES\x1a"

def parse_iNES_header(handle):
    """Parse an iNES header. Return a dict. On error, raise an exception with an error message."""

    if handle.seek(0, 2) < 16:
        raise Exception("file_smaller_than_ines_header")

    # read the header, extract fields
    handle.seek(0)
    header = handle.read(16)
    (id_, PRGSize16KiB, CHRSize8KiB, flags6, flags7) \
    = (header[0:4], header[4], header[5], header[6], header[7])

    # validate id
    if id_ != _INES_ID:
        raise Exception("invalid_id")

    # get the size of PRG ROM, CHR ROM and trainer
    PRGSize = (PRGSize16KiB if PRGSize16KiB else 256) * 16 * 1024
    CHRSize = CHRSize8KiB * 8 * 1024
    trainerSize = bool(flags6 & 0x04) * 512

    # validate file size
    if handle.seek(0, 2) < 16 + trainerSize + PRGSize + CHRSize:
        raise Exception("file_too_small")

    # get type of name table mirroring
    if flags6 & 0x08:
        mirroring = "four-screen"
    elif flags6 & 0x01:
        mirroring = "vertical"
    else:
        mirroring = "horizontal"

    return {
        "PRGSize": PRGSize,
        "CHRSize": CHRSize,
        "mapper": (flags7 & 0xf0) | (flags6 >> 4),
        "mirroring": mirroring,
        "trainerSize": trainerSize,
        "saveRAM": bool(flags6 & 0x02),
    }

def create_iNES_header(PRGSize, CHRSize, mapper=0, mirroring="h", saveRAM=False):
    """Return a 16-byte iNES header as bytes. On error, raise an exception with an error message.
    PRGSize: PRG ROM size (16 * 1024 to 4096 * 1024 and a multiple of 16 * 1024)
    CHRSize: CHR ROM size (0 to 2040 * 1024 and a multiple of 8 * 1024)
    mapper: mapper number (0-255)
    mirroring: name table mirroring ('h'=horizontal, 'v'=vertical, 'f'=four-screen)
    saveRAM: does the game have save RAM"""

    # get PRG ROM size in 16-KiB units; encode 256 as 0
    (PRGSize16KiB, remainder) = divmod(PRGSize, 16 * 1024)
    if not 1 <= PRGSize16KiB <= 256 or remainder:
        raise Exception("invalid_prg_rom_size")
    PRGSize16KiB %= 256

    # get CHR ROM size in 8-KiB units
    (CHRSize8KiB, remainder) = divmod(CHRSize, 8 * 1024)
    if not 0 <= CHRSize8KiB <= 255 or remainder:
        raise Exception("invalid_chr_rom_size")

    # encode flags
    flags6 = (mapper & 0x0f) << 4
    if mirroring == "v":
        flags6 |= 0x01
    elif mirroring == "f":
        flags6 |= 0x08
    elif mirroring != "h":
        raise Exception("invalid_mirroring_type")
    if saveRAM:
        flags6 |= 0x02
    flags7 = mapper & 0xf0

    return _INES_ID + bytes((PRGSize16KiB, CHRSize8KiB, flags6, flags7)) + 8 * b"\x00"

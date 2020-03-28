"""A library for parsing iNES ROM files (.nes)."""

def parse_iNES_header(handle):
    """Parse an iNES header. See http://wiki.nesdev.com/w/index.php/INES
    Raise an exception on error."""

    if handle.seek(0, 2) < 16:
        raise Exception("file_smaller_than_ines_header")

    # read the header, extract fields
    handle.seek(0)
    header = handle.read(16)
    (id_, PRGSize16KiB, CHRSize8KiB, flags6, flags7) \
    = (header[0:4], header[4], header[5], header[6], header[7])

    # validate id
    if id_ != b"NES\x1a":
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

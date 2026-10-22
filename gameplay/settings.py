"""Audited settings journal space in the two original USA flash-save banks."""
import hashlib
import struct
from .patches import PatchMismatch

JOURNAL_OFFSETS = (0x3F000, 0x7F000)
JOURNAL_SIZE = 256


def audit_save_layout(rom):
    if rom.arm9RamAddress != 0x02000000:
        raise PatchMismatch('Settings storage requires the audited USA ARM9 layout.')
    arm = bytes(rom.arm9)
    table = arm[0xF6464:0xF6464 + 96]
    if hashlib.sha256(table).hexdigest() != '43bcc55f61ac7b092f0d77dc77006e913984ef1d2215f69216a2e6a7a2ad1808':
        raise PatchMismatch('Native extra-save allocation table differs from the audit.')
    expected = [(0, 35, 0x0202E0DD, 0x2AB0), (1, 38, 0x020312A5, 0xBA0),
                (2, 39, 0x0202FBCD, 0x1D50), (3, 41, 0x0202FBCD, 0x1D50),
                (4, 43, 0x0202FBCD, 0x1D50), (5, 45, 0x0202FBCD, 0x1D50)]
    spans = []
    for index, sector, function, size in expected:
        actual = struct.unpack_from('<4I', table, index * 16)
        if actual[:3] != (index, sector, function):
            raise PatchMismatch('Native extra-save chunk allocation changed.')
        spans.append((sector * 0x1000, sector * 0x1000 + size + 16))
    for address, size, digest in SAVE_FUNCTIONS:
        data = arm[address - rom.arm9RamAddress:address - rom.arm9RamAddress + size]
        if hashlib.sha256(data).hexdigest() != digest:
            raise PatchMismatch(f'Native save routine changed at {address:#x}.')
    native_end = max(end for start, end in spans)
    for bank in (0, 0x40000):
        offset = JOURNAL_OFFSETS[bank // 0x40000]
        if offset < bank + native_end or offset + JOURNAL_SIZE > bank + 0x40000:
            raise PatchMismatch('Settings record overlaps native save data.')
    return {'bank_size': 0x40000, 'native_main_limit': 35 * 0x1000,
            'native_extra_spans': spans, 'native_data_end_per_bank': native_end,
            'journal_offsets': list(JOURNAL_OFFSETS), 'journal_record_bytes': JOURNAL_SIZE,
            'journal_version': 1, 'checksum': 'CRC-32', 'ownership': 'native full trainer ID'}


SAVE_FUNCTIONS = [
    (0x0202E0DC, 16, '151dc348a3f8fe957e5e1d2d9a1a1ff574b13167452718828a62af62861ce58f'),
    (0x020312A4, 16, '89835c28ae45ca3076cfc7f362e33e68b3334e6cb1e6f2f646f775101b53b3b3'),
    (0x0202FBCC, 16, '3d6c209ece058fbf7732eed59439617e31c4626a5a7afa560242de91a8e43952'),
    (0x02028758, 144, '626ca6932525ed8111d9e5abadd162c47235a12ddb43211678ecd32a89799e17'),
]

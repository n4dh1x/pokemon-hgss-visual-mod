"""Checked field hooks; only overlays 1/2 and listed ARM9 sites may change."""
from dataclasses import dataclass
import hashlib
import struct

import ndspy.code

from .native import Payload, thumb_veneer
from .patches import PatchMismatch, PatchResult


@dataclass(frozen=True)
class OverlayPatch:
    overlay: int
    file_id: int
    patch: PatchResult


@dataclass(frozen=True)
class FilePatch:
    file_id: int
    feature: str
    before_sha256: str
    after_sha256: str
    data: bytes
    behavior: str

    def summary(self):
        return {name: getattr(self, name) for name in
                ('file_id', 'feature', 'before_sha256', 'after_sha256', 'behavior')}


def thumb_call(address: int, destination: int) -> bytes:
    if address & 1 or not destination & 1:
        raise PatchMismatch('Thumb BL requires an aligned site and Thumb destination.')
    delta = (destination & ~1) - address - 4
    if delta % 2 or not -0x400000 <= delta < 0x400000:
        raise PatchMismatch('Thumb BL destination is out of range.')
    return struct.pack('<HH', 0xF000 | ((delta >> 12) & 0x7FF),
                       0xF800 | ((delta >> 1) & 0x7FF))


def fingerprint(data, base, address, size, digest):
    offset = address - base
    if offset < 0 or hashlib.sha256(data[offset:offset + size]).hexdigest() != digest:
        raise PatchMismatch(f'Field context differs at {address:#010x}.')


def replace(data, base, address, before, after, behavior):
    offset = address - base
    if offset < 0 or bytes(data[offset:offset + len(before)]) != before or len(before) != len(after):
        raise PatchMismatch(f'Field hook differs at {address:#010x}.')
    data[offset:offset + len(before)] = after
    return PatchResult('visible_encounters', address, before.hex(), after.hex(), behavior)


def install_field(rom, payload: Payload) -> tuple[list[PatchResult], list[OverlayPatch]]:
    arm = bytearray(rom.arm9)
    base = rom.arm9RamAddress
    fingerprint(arm, base, 0x0202D9C4, 12, '101aa1751b7950e918a3160614f091f0894f68d2d9db003d6ba062121e5cff4d')
    fingerprint(arm, base, 0x0202DB08, 16, 'e8868befa007c2e6c1c512dd52795fe0c486af30b4c5341222860326d2b1075b')
    fingerprint(arm, base, 0x0203E15C, 0x198, '652e669711e0f8af6e082cad86640e34db51b0229ece1b731001b3f19bc49f16')
    fingerprint(arm, base, 0x0205E5EC, 0x5C, 'd1e26d932f67ffa9f3172f1a2b8965b464f434e2ecc03a824159c97a29b29ea6')
    fingerprint(arm, base, 0x0205E0E8, 0x1C, '4f992d38cdf5fefd9739bbd4160ca005475856b601d1fb6f2fd744050496ebc5')
    main = []
    for site, original, symbol in (
        (0x0203E0D0, 0x0203E15D, 'EnhancedFieldControl'),
        (0x0203E270, 0x021E6AF5, 'EnhancedFieldInput'),
        (0x0205E604, 0x0205EEF5, 'EnhancedSaveIterator'),
        (0x0205E62A, 0x0205EEF5, 'EnhancedSaveIterator'),
    ):
        main.append(replace(arm, base, site, thumb_call(site, original),
                            thumb_call(site, payload.symbols[symbol]), symbol))
    main.append(replace(arm, base, 0x0205E0E8,
                        bytes(arm[0x0205E0E8 - base:0x0205E0F8 - base]),
                        thumb_veneer(payload.symbols['EnhancedManagerDelete']),
                        'Forget transient ownership before original manager allocations are freed'))
    overlays = ndspy.code.loadOverlayTable(rom.arm9OverlayTable,
                                           lambda oid, fid: rom.files[fid], {1, 2})
    context = {
        1: [(0x021E6AF4, 0x2D0, '0b22495d52b5131c68a2b20749a33064d7af8589aa5c25211b53d58371e041a7'),
            (0x021E7114, 0x84, '71e23a58ecd82a89f42f2e87edc9f504a579fbe1beae6e5e0bfb93d3bb016970')],
        2: [(0x02246C8C, 0x2E0, '2774f4f3deddfce2d71849c774885c82017a033979d9e2c39512802e0d6aba18')],
    }
    calls = {
        1: [(0x021E6C6C, 0x0203FE75, 'EnhancedStartScript'),
            (0x021E6C78, 0x0203FE75, 'EnhancedStartScript'),
            (0x021E7180, 0x02246C8D, 'EnhancedStepEncounter')],
        2: [(0x02246D5E, 0x02247569, 'EnhancedEncounterRoll'),
            (0x02246D92, 0x02248361, 'EnhancedRoamerCheck'),
            (0x02246F2E, 0x02050B09, 'EnhancedCaptureEncounter')],
    }
    records = []
    table = bytearray(rom.arm9OverlayTable)
    for oid, overlay in overlays.items():
        for address, size, digest in context[oid]:
            fingerprint(overlay.data, overlay.ramAddress, address, size, digest)
        for site, original, symbol in calls[oid]:
            patch = replace(overlay.data, overlay.ramAddress, site,
                            thumb_call(site, original), thumb_call(site, payload.symbols[symbol]), symbol)
            records.append(OverlayPatch(oid, overlay.fileID, patch))
        rom.files[overlay.fileID] = overlay.save(compress=False)
        # Preserve all untouched overlay descriptors exactly.
        for offset in range(0, len(table), 32):
            if struct.unpack_from('<I', table, offset)[0] == oid:
                table[offset:offset + 32] = ndspy.code.saveOverlayTable({oid: overlay})
                break
        else:
            raise PatchMismatch(f'Overlay {oid} descriptor is missing.')
    rom.arm9 = bytes(arm)
    rom.arm9OverlayTable = bytes(table)
    return main, records


def verify_field_files(original, patched, records: list[OverlayPatch], file_patches=()):
    ids = {r.overlay for r in records}
    overlays = ndspy.code.loadOverlayTable(original.arm9OverlayTable,
                                           lambda oid, fid: original.files[fid], ids)
    expected_files = list(original.files)
    expected_table = bytearray(original.arm9OverlayTable)
    for oid, overlay in overlays.items():
        for record in (r for r in records if r.overlay == oid):
            if record.file_id != overlay.fileID:
                raise PatchMismatch('Recorded overlay file ID changed.')
            change = record.patch
            replace(overlay.data, overlay.ramAddress, change.address,
                    bytes.fromhex(change.before), bytes.fromhex(change.after), change.behavior)
        expected_files[overlay.fileID] = overlay.save(compress=False)
        for offset in range(0, len(expected_table), 32):
            if struct.unpack_from('<I', expected_table, offset)[0] == oid:
                expected_table[offset:offset + 32] = ndspy.code.saveOverlayTable({oid: overlay})
                break
    seen = {r.file_id for r in records}
    for record in file_patches:
        if record.file_id in seen or not 0 <= record.file_id < len(expected_files):
            raise PatchMismatch('Duplicate or invalid recorded data file ID.')
        if hashlib.sha256(original.files[record.file_id]).hexdigest() != record.before_sha256 or \
                hashlib.sha256(record.data).hexdigest() != record.after_sha256:
            raise PatchMismatch('Recorded data file checksum mismatch.')
        seen.add(record.file_id)
        expected_files[record.file_id] = record.data
    if expected_files != patched.files or bytes(expected_table) != patched.arm9OverlayTable:
        raise PatchMismatch('Unrecorded NitroFS or overlay descriptor changes.')

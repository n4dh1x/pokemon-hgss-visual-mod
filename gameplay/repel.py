"""Guarded native Repel use/expiry hooks and the audited last-type save byte."""
import dataclasses
import struct
import ndspy.code

from .field import OverlayPatch, fingerprint, replace, thumb_call


def install_repel(rom, payload):
    arm, base = bytes(rom.arm9), rom.arm9RamAddress
    fingerprint(arm, base, 0x0203BE60, 108, '01963235000bfc1f4d6335710f19371f6eb737d5bccc199ea3c92984fd3e3d42')
    fingerprint(arm, base, 0x02067584, 24, '115ff6a1e4290537c1927454f1fb2b16745a39c209b9354b4858427d7c827e1f')
    fingerprint(arm, base, 0x02066860, 80, 'd4fd6001ba8341768e5d3ad2a53c5c4825b86137ae217e875a70daca19b5a8fe')
    fingerprint(arm, base, 0x0202D968, 0x1D0, 'a151f809088a85ee2658965f03be1d008b3fe63135a1547d067b32dadef5e9d6')
    fingerprint(arm, base, 0x02078434, 144, '5981cc0c9f3602f243f69062b35afa3dddff822f5b9c9b852d1d536cb89d250f')
    fingerprint(arm, base, 0x0207879C, 12, '2c3a66435ca1a6b52f5ed6f5f3cc32b67436f1e94b09a09c5b0076f6be1743ae')
    fingerprint(arm, base, 0x0200604C, 32, '450aa068194ad9eb69d59218414b67d48aa21f6d96fc11a3c7e06bda9301675b')
    overlays = ndspy.code.loadOverlayTable(rom.arm9OverlayTable,
        lambda oid, fid: rom.files[fid], {2, 15})
    fingerprint(overlays[2].data, overlays[2].ramAddress, 0x0224BAE4, 52,
                'd532a46d70de71aa034f322249d6b9efbd2568ed39173917582835e3e2d9213d')
    fingerprint(overlays[15].data, overlays[15].ramAddress, 0x021FBA9C, 92,
                'df8e10e2834e8d1c97f19fdb31f6a34b3bc40731c8e418792144683b0f2007b4')
    records, table = [], bytearray(rom.arm9OverlayTable)
    for oid, site, original, symbol in (
        (2, 0x0224BB06, 0x0203FE75, 'EnhancedRepelWoreOff'),
        (15, 0x021FBACA, 0x02077D89, 'EnhancedRepelGetSteps'),
    ):
        overlay = overlays[oid]
        change = replace(overlay.data, overlay.ramAddress, site, thumb_call(site, original),
                         thumb_call(site, payload.symbols[symbol]), symbol)
        change = dataclasses.replace(change, feature='repel_prompt')
        records.append(OverlayPatch(oid, overlay.fileID, change))
        rom.files[overlay.fileID] = overlay.save(compress=False)
        for offset in range(0, len(table), 32):
            if struct.unpack_from('<I', table, offset)[0] == oid:
                table[offset:offset+32] = ndspy.code.saveOverlayTable({oid: overlay})
                break
    rom.arm9OverlayTable = bytes(table)
    return records, {'native_chunk': 'SAVE_ROAMER', 'native_chunk_bytes': 0x68,
        'last_type_offset': 0x66, 'allowed_values': [0, 76, 77, 79],
        'unexpected_byte_policy': 'Preserve unknown data and use native wear-off message',
        'persistence': 'Original game save and checksum, coupled to Repel step count',
        'audit': 'Pinned roamer.c/h, all Roamers_Get callers, and guarded USA native routines'}

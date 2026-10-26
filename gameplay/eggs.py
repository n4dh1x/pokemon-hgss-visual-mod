"""Guarded native daycare step trigger; original hatch queue stays intact."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import fingerprint, replace, thumb_call, OverlayPatch

# Independently checked against both USA Visual+ baselines. These full native
# bodies retain breeding, valid-egg selection, calendar/ability cycle behavior
# and the original hatch application handoff.
MAIN_CONTEXTS = (
    (0x0206CD1C, 0x128, '65033b13d1f61e3419e90a8b335b8138dbf180338ceb8b123e7e7a3998f6156e'),
    (0x0206CE44, 0x50, '70c25f0a92ba7e578bd16e71f3a9a9c54e3f46a982a7c5cc44949ddea3e471c0'),
    (0x0206CB34, 0x54, 'ed17a4dd0cd123c7a7d35941e515d96b10db3192bfa044be29601885d31dfcae'),
    (0x0206CCD8, 0x44, 'a81aea1dde1826d97519cf8f2ce73834b10990cd39cb7f7f8922d750ab2884e3'),
    (0x0203F9F4, 0x44, '064044215a2cde379fe837f6ebc3fa5ec64843426c43d9c53ad7fad8febc8514'),
    (0x020292DC, 0x68, '4ff132462526036b5b7cda6ea9d1ca4a187c9325943b11a8333e1389f53a4489'),
)


def install_eggs(rom, payload):
    for address, size, digest in MAIN_CONTEXTS:
        fingerprint(rom.arm9, rom.arm9RamAddress, address, size, digest)
    overlay = ndspy.code.loadOverlayTable(
        rom.arm9OverlayTable, lambda oid, fid: rom.files[fid], {1})[1]
    fingerprint(overlay.data, overlay.ramAddress, 0x021E788C, 0x4C,
                'd9f8d1e4e163f10e089d52f4d599cca28a05870c8560feabbc3f745a3f8a9950')
    site = 0x021E78A2
    patch = rename(replace(overlay.data, overlay.ramAddress, site,
        thumb_call(site, 0x0206CD1D),
        thumb_call(site, payload.symbols['EnhancedDaycareStep']),
        'Optional five-step valid egg trigger; native daycare and hatch handoff'),
        feature='fast_eggs')
    rom.files[overlay.fileID] = overlay.save(compress=False)
    table = bytearray(rom.arm9OverlayTable)
    for offset in range(0, len(table), 32):
        if struct.unpack_from('<I', table, offset)[0] == 1:
            table[offset:offset + 32] = ndspy.code.saveOverlayTable({1: overlay})
            break
    else:
        raise ValueError('Native field overlay descriptor is missing.')
    rom.arm9OverlayTable = bytes(table)
    return [OverlayPatch(1, overlay.fileID, patch)]

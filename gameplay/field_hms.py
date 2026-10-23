"""Guard native contextual HM checks without changing badges or Pokemon moves."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import OverlayPatch, fingerprint, replace, thumb_call


def install_field_hms(rom, payload):
    arm = bytearray(rom.arm9)
    for address, size, digest in (
        (0x0204D3CC,192,'1597d3de4e072fde476b78638022c712007a3ac3fa76f5b9a07d37d0b4436550'),
        (0x020542E8,136,'99ac4ddfeed7b6104727505c8075fb6f5a0acae64fd379a9860e331b88402546'),
        (0x0207224C,136,'cc0d81e61066d361b4ebbecddf20e4566a1681b82043549db7a47c9b345ef67e'),
        (0x020FAF00,96,'87d1fe8e5b1ddc8fe27aa8f5389431755d45b8b840559229d219403bcc00a3be'),
        (0x0203FE2C,24,'c5d49b18f38dbe417a8bbc6ac7e8d6503b0373a83a4524d0ce99aac92852d3fd'),
        (0x020403AC,40,'0aa8159965069e90b3ccb64652ea59d13836245d1d2c13f4bcc13330f56f08a8'),
    ): fingerprint(arm,rom.arm9RamAddress,address,size,digest)
    patch = replace(arm,rom.arm9RamAddress,0x020FAF34,
        struct.pack('<I',0x0204D3CD),struct.pack('<I',payload.symbols['EnhancedPartySlotWithMove']),
        'Contextual HM users follow saved field-HM option; native badge/story scripts retained')
    main = [rename(patch,feature='field_hms')]
    overlay = ndspy.code.loadOverlayTable(rom.arm9OverlayTable,
        lambda oid,fid: rom.files[fid],{1})[1]
    records = []
    for start, site, digest in (
        (0x021E6BB6,0x021E6BBE,'f5e82c68c18e953c7263dfb0a5c25a7f2bc32b2ffb57d2593369041b9c70b95f'),
        (0x021E753C,0x021E7544,'2e00486ad0dde3fdfbcbeed080a9fa9eef38c056887a685c9536291a21084b9e'),
    ):
        fingerprint(overlay.data,overlay.ramAddress,start,20,digest)
        change = replace(overlay.data,overlay.ramAddress,site,
            thumb_call(site,0x020542E9),thumb_call(site,payload.symbols['EnhancedFirstPartyMove']),
            'Native Surf/Waterfall input eligibility uses the same HM fallback; other gates retained')
        records.append(OverlayPatch(1,overlay.fileID,rename(change,feature='field_hms')))
    rom.arm9 = bytes(arm)
    rom.files[overlay.fileID] = overlay.save(compress=False)
    table = bytearray(rom.arm9OverlayTable)
    for offset in range(0,len(table),32):
        if struct.unpack_from('<I',table,offset)[0] == 1:
            table[offset:offset+32] = ndspy.code.saveOverlayTable({1:overlay})
            break
    rom.arm9OverlayTable = bytes(table)
    return main, records

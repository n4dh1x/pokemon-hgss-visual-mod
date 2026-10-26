"""Checked field-camera deletion forwarding and native camera function guards."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import fingerprint, replace, thumb_call, OverlayPatch
MAIN_CONTEXTS = (
    (0x020233D8, 0xC0, '54bff3c6510e727676d3c5b8355f791847d4b05c02f257302c4f015712b1494b'),
    (0x02022D74, 0xE0, '10a50f14135dd24779c81181c9210ba1f916bc4113f2d5c1efe7ede6f397d4c3'),
    (0x02023120, 0x8, 'df5277dbd8d95a7ae061b511ad12ba6efd5b819260e384fbe76a33bfdc3008cb'),
    (0x0202313C, 0xC, '11a69ab47adf27841dd30176f4aafd82a31957091bfd8ce948ffe3537e04ec35'),
    (0x02023558, 0x24, '8d14b4a51c4eae60ba8ebe8aebcc2103453d1651b6797f4324a60c5c00865572'),
    (0x020235D4, 0xC, 'cab4817e2a3580d056a85ad1e541157ae4da623d70086a12704ee9bedc105e72'),
)
def install_camera(rom, payload):
    for a,n,d in MAIN_CONTEXTS: fingerprint(rom.arm9,rom.arm9RamAddress,a,n,d)
    overlay=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{1})[1]
    fingerprint(overlay.data,overlay.ramAddress,0x021EAC30,0x1C,'3a06f267b48b45e4f4769d4411b60de198818e46e5e50cc171335025fb8e884d')
    fingerprint(overlay.data,overlay.ramAddress,0x021EABA8,0x88,'91130bf479ac964ecda7ee34d55341b74cdd92b586724cb4b1727363f22f32da')
    fingerprint(overlay.data,overlay.ramAddress,0x021EAC6C,0x50,'71dc01ecda0b3c1dec420a1f3e1e3ed1770fb66fd0f893bb75225fd6eb905571')
    fingerprint(overlay.data,overlay.ramAddress,0x021EAD8C,0xC4,'bfe9dc00350f36ab217d7edf84d9bf5ec68f667b39355df3bbcba0ae72b49595')
    site=0x021EAC46
    patch=rename(replace(overlay.data,overlay.ramAddress,site,thumb_call(site,0x02023121),
        thumb_call(site,payload.symbols['EnhancedCameraDelete']),
        'Forget owned camera before original native deletion'),feature='camera_controls')
    rom.files[overlay.fileID]=overlay.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for at in range(0,len(table),32):
        if struct.unpack_from('<I',table,at)[0]==1:
            table[at:at+32]=ndspy.code.saveOverlayTable({1:overlay});break
    else:raise ValueError('Native field camera overlay descriptor is missing.')
    rom.arm9OverlayTable=bytes(table)
    return [OverlayPatch(1,overlay.fileID,patch)]

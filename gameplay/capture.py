"""Guarded native capture callback integration; retain the native EXP task."""
import struct
import ndspy.code
from .field import OverlayPatch, fingerprint, replace

def install_capture(rom, payload):
    overlay = ndspy.code.loadOverlayTable(rom.arm9OverlayTable,
        lambda oid, fid: rom.files[fid], {12})[12]
    for address,size,digest in [
        (0x0223E6A0,380,'e34511fdf98dd6f68a1756c9a8691a07a6626e1eb9bd31cd4144e1fe23c5cf6e'),
        (0x0223EB88,92,'3fd1db77fa1c0c891387c6ba03725daf1df08a7e1255132c82ec1ddfa961df95'),
        (0x02245898,2896,'a2bd10b089685b468573bdb5799af0998b25ee4a200f05a0c1f8d882767de550'),
        (0x022465A8,3188,{'IPKE':'4c9bc8130f1d0b104edbb315cbb26f89f3501c3160a4d62182e0eccf8411e91b',
                         'IPGE':'1fa5951673d394ee52ab84407fabffe63ee08e5a5c22b67ad8b89f8afcd45973'}[rom.idCode.decode()]),
    ]: fingerprint(overlay.data,overlay.ramAddress,address,size,digest)
    from dataclasses import replace as replace_record
    patch=replace(overlay.data,overlay.ramAddress,0x0223EBE0,struct.pack('<I',0x022465A9),
                  struct.pack('<I',payload.symbols['EnhancedCaptureTask']),'Capture callback runs the native EXP task before Dex/nickname/storage')
    patch=replace_record(patch,feature='capture_exp')
    rom.files[overlay.fileID]=overlay.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for offset in range(0,len(table),32):
        if struct.unpack_from('<I',table,offset)[0]==12:
            table[offset:offset+32]=ndspy.code.saveOverlayTable({12:overlay});break
    rom.arm9OverlayTable=bytes(table)
    return [OverlayPatch(12,overlay.fileID,patch)]

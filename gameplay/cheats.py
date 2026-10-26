"""Guarded native ball-shake RNG override; retain original catch bookkeeping."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import fingerprint, replace, thumb_call, OverlayPatch
CONTEXTS = {
    'IPKE': (
        (0x02247228, 0x440, 'ee1e72cfd2b7849e9cde81fd30eaa5d9c9e8b2a91d23aaeefb006baa3dd5bc8a'),
        (0x0223BD98, 0x2C, '29e88b6c3903a8d41c8471aebff5a8ae313f9a36682b73e57d04ddf085267cd8'),
        (0x0223A7E0, 0x8, '93784878d166cc5ea86f97ad5f63d8720bc0fef0415880c370c5cbdb251b58f1'),
        (0x02246740, 0x3C, '8392ec9080a98d3bef0a0b18d60747bf6d0df8844f1b3b4f55e8147ecc0c49d9'),
        (0x022466FC, 0x44, '63447652614afe842d3a5bb054175b24e6c750459112e06fde90d43043ee1506'),
    ),
    'IPGE': (
        (0x02247228, 0x440, 'ee1e72cfd2b7849e9cde81fd30eaa5d9c9e8b2a91d23aaeefb006baa3dd5bc8a'),
        (0x0223BD98, 0x2C, '29e88b6c3903a8d41c8471aebff5a8ae313f9a36682b73e57d04ddf085267cd8'),
        (0x0223A7E0, 0x8, '93784878d166cc5ea86f97ad5f63d8720bc0fef0415880c370c5cbdb251b58f1'),
        (0x02246740, 0x3C, '8392ec9080a98d3bef0a0b18d60747bf6d0df8844f1b3b4f55e8147ecc0c49d9'),
        (0x022466FC, 0x44, '63447652614afe842d3a5bb054175b24e6c750459112e06fde90d43043ee1506'),
    ),
}
def install_cheats(rom,payload):
    overlay=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{12})[12]
    for a,n,h in CONTEXTS[rom.idCode.decode()]:fingerprint(overlay.data,overlay.ramAddress,a,n,h)
    site=0x022475FE
    patch=rename(replace(overlay.data,overlay.ramAddress,site,thumb_call(site,0x0223BD99),
        thumb_call(site,payload.symbols['EnhancedCatchRoll']),
        'Optional owned wild guarantee at native ball-shake roll'),feature='always_catch')
    rom.files[overlay.fileID]=overlay.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for at in range(0,len(table),32):
        if struct.unpack_from('<I',table,at)[0]==12:
            table[at:at+32]=ndspy.code.saveOverlayTable({12:overlay});break
    else:raise ValueError('Native battle overlay descriptor is missing.')
    rom.arm9OverlayTable=bytes(table)
    return [OverlayPatch(12,overlay.fileID,patch)]

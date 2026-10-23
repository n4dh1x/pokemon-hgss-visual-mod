"""Guard the native Bag field-action hook and real start-menu use callback."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import OverlayPatch, fingerprint, replace, thumb_call


def install_field_hm_bag(rom, payload):
    arm = bytearray(rom.arm9)
    for address, size, digest in (
        (0x02067DF4,3028,'5babd2e7a552a0dd5f857f2d0c4015df41521c4223974d33b08a30c669a82005'),
        (0x020FE7BC,112,'592022fd5d6b1097d1d7b81f76cc9815b2e1a311c6d15bc9a840dd81a9feb05b'),
        (0x02064E18,160,'fe2b9762999e0858db7518f4a598058f0cf6c1c72399e2ef38cd88634c4b45ec'),
        (0x020FE264,96,'22bf6c360eef42ad875b6c3d9643eb08919779aac7bcedf77cb2f2ae576e20d7'),
        (0x0203CFC0,544,'9f914659f5baec3df8684cc7224cb982dce0d5040a071ccc8ba433ef7ed1a263'),
        (0x0203D758,192,'27619e12cf1ed7a02c991d2de153599db110783ecded2e04306a27f50f96ebfb'),
        (0x0203E3FC,100,'eff3f3e3fe7b0abbccc2ef4aa467a18ad6a50df416d15381f60573308e470143'),
    ): fingerprint(arm,rom.arm9RamAddress,address,size,digest)
    main = [rename(replace(arm,rom.arm9RamAddress,0x020FE2AC,
        struct.pack('<I',0x02064E19),struct.pack('<I',payload.symbols['EnhancedItemUseTMHM']),
        'Confirmed Bag field-use intent calls native Fly/Flash with the actual start-menu environment; ordinary teaching preserved'),feature='field_hms')]
    overlay = ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{15})[15]
    for address,size,digest in (
        (0x021FB14C,564,'fcb496e2719e76a75d9bce279d8254a1648520d7827789cbac7384fa1dc7729a'),
        (0x021FB604,124,'6d9950b6711eb2b15edac4ad5f45976c8836bb28f5775589e878eb706e289a6c'),
        (0x021FB680,128,'68d9ecff4281355bec1b6ad12cc014a6e998f57d63eb3d241c6b85efce3658c6'),
        (0x021FF004,100,'4af0e5617ef534c8e02b84735463fe2509d4fd9cfe1ef72f6b5b7dfa24e8d19e'),
        (0x021FEB84,96,'82e1ac3b61a0492e276b577a377cdbc51a75c4f32c3edefc5800fd7a7e88ebb3'),
        (0x021FEF48,188,'dbcbf599711354f7bb869d30a83110cf10f896a693ff7ef36c24b2e152b0b440'),
    ): fingerprint(overlay.data,overlay.ramAddress,address,size,digest)
    site=0x021FB35A
    change=rename(replace(overlay.data,overlay.ramAddress,site,thumb_call(site,0x021FEB85),
        thumb_call(site,payload.symbols['EnhancedBagDrawContext']),
        'Add bounded USE NOW action for owned HM02/TM70; preserve native teaching and Bag context'),feature='field_hms')
    rom.arm9=bytes(arm);rom.files[overlay.fileID]=overlay.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for offset in range(0,len(table),32):
        if struct.unpack_from('<I',table,offset)[0]==15:
            table[offset:offset+32]=ndspy.code.saveOverlayTable({15:overlay});break
    rom.arm9OverlayTable=bytes(table)
    return main,[OverlayPatch(15,overlay.fileID,change)]

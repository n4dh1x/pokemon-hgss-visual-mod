"""Guarded native selection handoff for optional opponent fainting."""
from dataclasses import replace as rename
import struct,hashlib
import ndspy.code,ndspy.narc
from .field import fingerprint,replace,OverlayPatch
from .patches import PatchMismatch
CONTEXTS = {
    'IPKE': (
        (0x02237ED0, 0x48, 'd2f2ff4733dadca6f56516505ca11cd3447a7b05672d0a408355da2bad2c76a9'),
        (0x022486B0, 0x4C, 'b782ed1a74790c2fe9068460774da2e1b73ed5d4881cf424407d3c3bfe2b1637'),
        (0x0226CA90, 0xB8, '76d2a529ba3726fce5f866c101792f8293d44da86373807b4e119df5bb90676d'),
        (0x0224873C, 0x44, '691c9064c0e18d2181f66902da2663ae34116ef0174c5b5c1aa81c9a0519facb'),
        (0x022487FC, 0x4C, '0cb2283a8bd3b154b28346ffbb8ba8c54c7694bc303d24ca71903399dda9b075'),
        (0x02248848, 0x948, '43d5edeeee2edf52f68b49bf60da55659a27684d5a9c9cbcb21b197b3fec43de'),
        (0x0224A958, 0x58, 'e0deeeeea6b985b476dbe9d9a8e91f45df175a685caa0a35d418babf0ecaa7be'),
        (0x0223B514, 0xC, '13a7bdc65451e82d0e88641335bc3e9225315ba07cbc25ce3fcd91ddd65df617'),
        (0x0223A7E0, 0x14, '4b83013f71b57b8ef5e09003af65d8050f119e9743aa908dffe6de2599f03a97'),
        (0x0223AB1C, 0x18, '9a635733300868eb20c446907bcb6551b9731003a4a80904591c1fd0ca40ba7b'),
        (0x0223BD14, 0xC, 'acfd520b4350b0489e0c41dd8bb740501c56883e2e7aafa6f6a8e1f4c0466f45'),
        (0x0224EB9C, 0x40, 'bb1e73a56cec539e4431ee6ccced5476c1721f27b8a1e2f87dda09e8e81f28b1'),
        (0x0224DC74, 0xA4, 'c0acd9a0a49ee5d23ff408e73ef1c389bdf78a0805ad2b86cf887aab89857a00'),
        (0x0224DD18, 0x5C, 'cd7d390dfa853a382fb90b229f7f4904ded4564360a477b8f685df2787e69af7'),
        (0x0224D7EC, 0x378, '7814a0310e3ccb2f872b6ba7511427c4f24923fec64258e6d216ca15f4400e91'),
        (0x0224D540, 0x2AC, 'e58b9f7c81a48d76788fe84fc4371ba8a42e0f6224732d6e6e2c0a21b5713d3e'),
        (0x02250F44, 0xF4, '5691ad9d19cd638e138fc3843d5695dde3e51ebf419c2b9832fa1c527f6b3512'),
        (0x02251710, 0xDC, '297124d0f086304ab23268d73a998db226d337a1954b49bc602794d5980f0162'),
    ),
    'IPGE': (
        (0x02237ED0, 0x48, 'd2f2ff4733dadca6f56516505ca11cd3447a7b05672d0a408355da2bad2c76a9'),
        (0x022486B0, 0x4C, 'b782ed1a74790c2fe9068460774da2e1b73ed5d4881cf424407d3c3bfe2b1637'),
        (0x0226CA90, 0xB8, '76d2a529ba3726fce5f866c101792f8293d44da86373807b4e119df5bb90676d'),
        (0x0224873C, 0x44, '691c9064c0e18d2181f66902da2663ae34116ef0174c5b5c1aa81c9a0519facb'),
        (0x022487FC, 0x4C, '0cb2283a8bd3b154b28346ffbb8ba8c54c7694bc303d24ca71903399dda9b075'),
        (0x02248848, 0x948, '43d5edeeee2edf52f68b49bf60da55659a27684d5a9c9cbcb21b197b3fec43de'),
        (0x0224A958, 0x58, 'e0deeeeea6b985b476dbe9d9a8e91f45df175a685caa0a35d418babf0ecaa7be'),
        (0x0223B514, 0xC, '13a7bdc65451e82d0e88641335bc3e9225315ba07cbc25ce3fcd91ddd65df617'),
        (0x0223A7E0, 0x14, '4b83013f71b57b8ef5e09003af65d8050f119e9743aa908dffe6de2599f03a97'),
        (0x0223AB1C, 0x18, '9a635733300868eb20c446907bcb6551b9731003a4a80904591c1fd0ca40ba7b'),
        (0x0223BD14, 0xC, 'acfd520b4350b0489e0c41dd8bb740501c56883e2e7aafa6f6a8e1f4c0466f45'),
        (0x0224EB9C, 0x40, 'bb1e73a56cec539e4431ee6ccced5476c1721f27b8a1e2f87dda09e8e81f28b1'),
        (0x0224DC74, 0xA4, 'c0acd9a0a49ee5d23ff408e73ef1c389bdf78a0805ad2b86cf887aab89857a00'),
        (0x0224DD18, 0x5C, 'cd7d390dfa853a382fb90b229f7f4904ded4564360a477b8f685df2787e69af7'),
        (0x0224D7EC, 0x378, '7814a0310e3ccb2f872b6ba7511427c4f24923fec64258e6d216ca15f4400e91'),
        (0x0224D540, 0x2AC, 'e58b9f7c81a48d76788fe84fc4371ba8a42e0f6224732d6e6e2c0a21b5713d3e'),
        (0x02250F44, 0xF4, '5691ad9d19cd638e138fc3843d5695dde3e51ebf419c2b9832fa1c527f6b3512'),
        (0x02251710, 0xDC, '297124d0f086304ab23268d73a998db226d337a1954b49bc602794d5980f0162'),
    ),
}
SCRIPTS = {
    'IPKE': {
        2: 'bf7ad08c8f82d1b33126bf3b11cddcf34f4e7fbd49beb2fe45d90b9f65bafe70',
        6: 'f6fbadfb588c3e78ba801edff49ce5d5a166ea77480b6f8f5e63dfc344f29654',
        231: '793ad17b62b8cf5eb9974101299690a48c93b75bcdeaa00d5c4ecdd7cd5c87f2',
        276: '1a1de3be58ae616377add078cd2f27d1216af520bfe0c4d201b952cc4c9e1e1b',
    },
    'IPGE': {
        2: 'bf7ad08c8f82d1b33126bf3b11cddcf34f4e7fbd49beb2fe45d90b9f65bafe70',
        6: 'f6fbadfb588c3e78ba801edff49ce5d5a166ea77480b6f8f5e63dfc344f29654',
        231: '793ad17b62b8cf5eb9974101299690a48c93b75bcdeaa00d5c4ecdd7cd5c87f2',
        276: '1a1de3be58ae616377add078cd2f27d1216af520bfe0c4d201b952cc4c9e1e1b',
    },
}

def install_victory(rom,payload):
    code=rom.idCode.decode()
    overlay=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{12})[12]
    for address,length,digest in CONTEXTS[code]:fingerprint(overlay.data,overlay.ramAddress,address,length,digest)
    narc=ndspy.narc.NARC(rom.getFileByName('a/0/0/1'))
    for index,digest in SCRIPTS[code].items():
        if hashlib.sha256(narc.files[index]).hexdigest()!=digest:raise PatchMismatch(f'Native battle subscript {index} differs from the baseline.')
    changes=[]
    for index,old,symbol in [(0,0x224873D,'EnhancedVictoryGetBattleMon'),(5,0x2248849,'EnhancedVictorySelection')]:
        site=0x226CA90+4*index
        change=rename(replace(overlay.data,overlay.ramAddress,site,struct.pack('<I',old),struct.pack('<I',payload.symbols[symbol]),'Native selection/faint reward handoff'),feature='instant_victory')
        changes.append(OverlayPatch(12,overlay.fileID,change))
    rom.files[overlay.fileID]=overlay.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for at in range(0,len(table),32):
        if struct.unpack_from('<I',table,at)[0]==12:
            table[at:at+32]=ndspy.code.saveOverlayTable({12:overlay});break
    else:raise ValueError('Native battle overlay descriptor is missing.')
    rom.arm9OverlayTable=bytes(table)
    return changes

"""Guard the native quick-throw UI/response/consumption handoffs in both games."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import fingerprint, replace, thumb_call, OverlayPatch
from .items import audit_items
from .patches import PatchMismatch

# Independently compared with both clean USA Visual+ full baselines. This covers
# native menu callbacks/ownership, item response ABI and original bag restrictions.
CONTEXTS = (
    (0,0x02025224,0x2C,'94b53981f7cf0eddb11d9828783b24f6488651e10db1811329676338410ca268'),
    (0,0x020270D8,0xC,'f14c50093643ed9f9fb033d431a1060b573ed1531dab9dd33bacdafc5af57b34'),
    (12,0x02266B78,0xEC,'35622a0f3d62801c5b3d5beb52911f8f6569f6090472eea5268fc16056b84dc9'),
    (12,0x02269A24,0x78,'0105013d9feadd8aad53e2176bded25b7ef812a29a1299bbf11553c85aaffe49'),
    (12,0x02268550,0x134,'501a477ed528e4081b9695ddec4d0860f46595702229dd23cf39ba525d739362'),
    (12,0x02268684,0x38,'c79a7a741159b83b7d277cd50d6bc812951d35cd6411792e1af3d16f5afeebf7'),
    (12,0x02263138,0x188,'1740f08b9915ee2e75dd2614c02224103ceb0ce847758e350a56d3e9bfd14234'),
    (12,0x022632C0,0x18,'451de636f454572840d3d5971219646c96872684e26e7f63848f751100824962'),
    (12,0x0224EDC0,0x20,'491c53453911776cf209b2435f677658a32f4e5245041117e10c47626b1467ee'),
    (12,0x0224AAF0,0x160,'cbd00ce92b0c2f3e3a1a8086eb40b6ab04e13b52f3539ef3136c09d937c34140'),
    (12,0x0223A7D4,0x58,'19ac89329766695560ba38a656ccc73140fbfa135eb4b85b753f9bac080b94ae'),
    (12,0x0223AA80,0xC0,'dfa48ea9d3539c458d43250bf366c47e271c3e912c970c4626649a259991d326'),
    (12,0x02262240,0xA0,'0dcc731cf74e415d87d93b30d04209aef1e032886b7eef415de2414b0406b531'),
    (8,0x02222B8C,0x1EC,'678be9997e51c99db1298c83213c7eafc0751e5e341855b48780f2650ce406e9'),
    (0,0x02073D54,0x38,'78a384154aa6933a73176ad53a470a2d760cfc57afa345b725a370143886acba'),
    (0,0x02013660,0x54,'6027d00a30c00b3212962d7ae1434642f7a406fe2035153032526bcfbc3d8611'),
    (0,0x02021B5C,0x60,'e296afc0728be392e2593831fe7f0899ff59b983fc2adf6cf24166d029809d04'),
)
SITES = (
    (0x02266BD0,0x02025225,'EnhancedQuickTouchRect'),
    (0x02266BE0,0x02269A25,'EnhancedQuickCursor'),
    (0x02248DFA,0x02263139,'EnhancedQuickShowBag'),
    (0x0224ABF0,0x02078435,'EnhancedQuickTakeBall'),
)


def install_quick_ball(rom, payload):
    if rom.idCode not in (b'IPKE',b'IPGE'):
        raise PatchMismatch('Quick ball supports audited USA HG/SS only.')
    audit_items(rom)
    overlays=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{8,12})
    for oid,address,size,digest in CONTEXTS:
        code=overlays[oid].data if oid else rom.arm9
        base=overlays[oid].ramAddress if oid else rom.arm9RamAddress
        fingerprint(code,base,address,size,digest)
    overlay=overlays[12];changes=[]
    for site,old,symbol in SITES:
        patch=replace(overlay.data,overlay.ramAddress,site,thumb_call(site,old),
            thumb_call(site,payload.symbols[symbol]),'Native quick-ball menu feedback, item response and one native consumption')
        changes.append(OverlayPatch(12,overlay.fileID,rename(patch,feature='quick_ball')))
    rom.files[overlay.fileID]=overlay.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for at in range(0,len(table),32):
        if struct.unpack_from('<I',table,at)[0]==12:
            table[at:at+32]=ndspy.code.saveOverlayTable({12:overlay});break
    else:raise PatchMismatch('Battle overlay descriptor is missing.')
    rom.arm9OverlayTable=bytes(table)
    return changes

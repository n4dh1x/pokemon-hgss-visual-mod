"""Audit unchanged native Bag/item APIs and item-name/data resources."""
import hashlib
import ndspy.narc
from .field import fingerprint
from .patches import PatchMismatch
MAIN_CONTEXTS = (
    (0x02100194,537*8,'f6b48e235564bda6f687610bd6551fbda44ebcae2eec15527a57c597e5e0f54f'),
    (0x02077CE8,0x1A0,'cd1762c9d922998e31801d3e106ed234c447c0d15cd458cc6887616e1e5f2aa8'),
    (0x02078240,0x568,'c00318ebb03f609ca4fe668c2a1bd06659ff635cb45d43396074812b0883b0ea'),
)
ITEM_DATA_SHA = '577631590698709a75a7142da8a037e1641b8c41ac4cf9dd481de3f3d4e3a29c'
ITEM_NAMES_SHA = 'e6c79808dacc5a3196acd2735ac831bc53cff0154e48b2b3aa4bc214afeeeede'
def audit_items(rom):
    for address,size,digest in MAIN_CONTEXTS:
        fingerprint(rom.arm9,rom.arm9RamAddress,address,size,digest)
    if hashlib.sha256(rom.getFileByName('a/0/1/7')).hexdigest()!=ITEM_DATA_SHA:
        raise PatchMismatch('Native item attributes changed.')
    names=ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[222]
    if hashlib.sha256(names).hexdigest()!=ITEM_NAMES_SHA:
        raise PatchMismatch('Native item-name bank changed.')


def item_pocket_table(rom):
    """Derive a compact lookup from the audited ROM; never commit game assets."""
    import struct
    audit_items(rom)
    data=ndspy.narc.NARC(rom.getFileByName('a/0/1/7'))
    table=bytearray(b'\xff'*269)
    for item in range(1,537):
        member=struct.unpack_from('<H',rom.arm9,0x100194+item*8)[0]
        if not member:continue
        if member>=len(data.files) or len(data.files[member])<10:
            raise PatchMismatch('Native item parameter mapping is out of bounds.')
        pocket=(struct.unpack_from('<H',data.files[member],8)[0]>>7)&15
        if pocket>7:raise PatchMismatch('Native item pocket is outside HGSS pockets.')
        shift=(item&1)*4
        table[item//2]=(table[item//2]&~(15<<shift))|(pocket<<shift)
    return bytes(table)

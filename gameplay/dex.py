"""Audit unchanged native Dex APIs and exact HGSS regional membership."""
import hashlib
from .field import fingerprint
from .patches import PatchMismatch
MAIN_CONTEXTS = (
    (0x02029408, 0x1238, 'fdf2c5c835afd1b0fe3364cccf98a5e42d7ce0015d7b091d1b1f04b430ec7c1c'),
    (0x02028E9C, 0xC, '474f4bdec75f4cdaa5a88d8eb2d14834ba0fff4b1253d3e5fb52694fc08cdfe7'),
    (0x02029088, 0x2C, '4b815d7e4b2bb4cd4ee361f3ea4422af44456da0cc4f0c96184461e548f0dd37'),
    (0x0207187C, 0x10, '0b60c97ef5ef0e89f2c4f7e5e3a3dbe875135c00a5f3c3b46e017f909a133606'),
    (0x0206DE38, 0x2A0, '44b644c22769bf26c50390f0d9d78d2d892fa4ad63ed7e476c1c121affa694b5'),
)
JOHTO_SHA = '370ebe8f4afad6bf7d4720f0e23177611209eabd08647c194c952340fd102381'
def audit_dex(rom):
    for address, size, digest in MAIN_CONTEXTS:
        fingerprint(rom.arm9, rom.arm9RamAddress, address, size, digest)
    if hashlib.sha256(rom.getFileByName('a/1/3/8')).hexdigest() != JOHTO_SHA:
        raise PatchMismatch('Native Johto Dex membership table changed.')

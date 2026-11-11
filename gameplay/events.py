"""Audit native HGSS gift delivery, metadata and mutation APIs before building."""
from .field import fingerprint
MAIN_CONTEXTS=(
 # Original game message table allocation, read and release.
 (0x0200BAF8,0x98,'d5cc4b3f130c353c8818d66c76787db963ed3fff6f25e9e2853beaf520c34041'),
 (0x020270E4,0x14,'1160f272691f8801862ad25b7d081cd608533af8536d7a219eaef4b2d9311fbd'),
 (0x0202DB40,0x4C0,'768c367cd0c66481b01ba9dee40e65c1c1ce9aab230b9254088d0faa477c9b9e'),
 (0x0206DE38,0x150,'1357f441d544bf799c13a3a26532fcd97f5d711703c064932366c0aaf70990ae'),
 (0x0206EC40,0x168,'76580b6fec419e2a3e8dbb4aa181c7339dc8496b167f17424a83518512946ec6'),
 (0x02028900,0x88,'c04366c867f073a1d8540cb5caef800ec4bd96f7e6ae7a800445ae388c98942b'),
 # Save_Pokewalker_Get and the course-ownership reader establish save slot 39 and offset 0x130.
 (0x020325EC,0x38,'26ce648084b659135c52d60d16756c46a3f62c1deb5dd3ade00962bb4234203f'),
 (0x02032730,0x14,'a18ff2d7d37fc956d0c34c9ef78ba0ebe975836314e69b80020b6802b3e0f57f'),
 (0x020714E8,0x38,'97d3e3c59df30fccfd7cea0c1414e3d4f1a501b764e92572bcf29192aa36c091'),
)
def audit_events(rom):
    for address,size,digest in MAIN_CONTEXTS:
        fingerprint(rom.arm9,rom.arm9RamAddress,address,size,digest)

"""Guarded shared entry veneers retaining both original wallet API bodies."""
from dataclasses import replace as rename
import struct
from .field import fingerprint, replace

MAIN_CONTEXTS = (
    (0x02029024, 0x64, '6f7e1376f9ad3146c7000557d967b710cc8bdbc5750f02da8699884e8949e9b8'),
    (0x02028E9C, 0xC, '474f4bdec75f4cdaa5a88d8eb2d14834ba0fff4b1253d3e5fb52694fc08cdfe7'),
    (0x02028F84, 0x8, '63105a15c78ee375f53c7c202b509220cacb2e0fbea7ac383a7884aff5b6d70e'),
    (0x0205230C, 0x90, '71fa15550738ed375b5f2870b2b8f35a7840e8b1fe3054446de8e4a4e45ccb9d'),
)


def install_money(rom, payload):
    arm = bytearray(rom.arm9)
    for address, size, digest in MAIN_CONTEXTS:
        fingerprint(arm, rom.arm9RamAddress, address, size, digest)
    # GetMoney is only four bytes. Its adjacent setter is relocated byte for
    # byte, so both four-byte entry points can share a literal pool in the old
    # setter body. Neither entry overwrites another live function. R3 is an
    # AAPCS caller-saved register; SP/LR and all argument registers are retained.
    reader = payload.symbols['EnhancedMoneyRead']
    setter = payload.symbols['OriginalMoneySet']
    if not reader & 1 or not setter & 1:
        raise ValueError('Money entry veneers require Thumb destinations.')
    original = bytes.fromhex('40697047034a914200d9111c4161081c7047c046')
    branch = bytes.fromhex('024b1847024b1847') + bytes(4) + struct.pack('<2I', reader, setter)
    result = rename(replace(arm, rom.arm9RamAddress, 0x02029024, original,
        branch, 'Owned wallet refill and exact relocated original capped setter'),
        feature='infinite_money')
    rom.arm9 = bytes(arm)
    return [result]

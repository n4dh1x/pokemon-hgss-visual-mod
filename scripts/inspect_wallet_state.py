#!/usr/bin/env python3
"""Read native wallet, bank, currencies and inventory on a private RAM copy.

The wallet getter is intentionally not called: its optional refill is a game
mutation. The stored wallet field is read from the audited original profile
layout; original native APIs locate the profile and read separate currencies.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inspect_wallet(run: Path, report_path: Path, rom_path: Path) -> dict:
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
    from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
                                   UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)
    from inspect_visible_state import inspect_run
    diag = inspect_run(run, report_path)
    report = json.loads(report_path.read_text())
    raw = rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != report['output_sha256']:
        raise ValueError('ROM differs from the candidate report.')
    rom = ndspy.rom.NintendoDSRom(raw)
    ram = (run / 'main-ram.bin').read_bytes()
    for address, size in ((0x02028E9C, 0x40), (0x02029024, 0x64),
                          (0x0207879C, 0xC), (0x02078724, 0x78),
                          (0x0202ED88, 0xC), (0x0202F14C, 0x4C),
                          (0x0202D918, 0xC), (0x0202D3F8, 0x58),
                          (0x020503D0, 0xC), (0x02066794, 0x14)):
        at = address - 0x02000000
        if ram[at:at + size] != rom.arm9[at:at + size]:
            raise ValueError(f'Native currency reader differs at {address:#x}.')
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(0x02000000, ram)

    def read(address, size):
        if not 0x02000000 <= address <= 0x02400000 - size:
            raise ValueError('Native currency or bag pointer is outside main RAM.')
        return bytes(uc.mem_read(address, size))

    def call(fn, a=0, b=0, c=0):
        uc.reg_write(UC_ARM_REG_SP, 0x023FF000)
        uc.reg_write(UC_ARM_REG_LR, 0x023FEF01)
        for reg, value in ((UC_ARM_REG_R0, a), (UC_ARM_REG_R1, b), (UC_ARM_REG_R2, c)):
            uc.reg_write(reg, value)
        uc.emu_start(fn, 0x023FEF00, count=1000000)
        if uc.reg_read(UC_ARM_REG_PC) != 0x023FEF00 or uc.reg_read(UC_ARM_REG_SP) != 0x023FF000:
            raise ValueError('Native currency reader did not return within its bound.')
        return uc.reg_read(UC_ARM_REG_R0)

    field = struct.unpack('<I', read(0x021D4158, 4))[0]
    save = struct.unpack('<I', read(field + 12, 4))[0]
    profile = call(0x02028E9D, save)
    profile_before = read(profile, 64)
    wallet = struct.unpack('<I', read(profile + 20, 4))[0]
    coins = struct.unpack('<H', read(profile + 32, 2))[0]
    phone = call(0x0202ED89, save)
    bank_before = read(phone + 0x140, 4)
    bank = call(0x0202F14D, phone, 0, 0)
    if bank != struct.unpack('<I', bank_before)[0]:
        raise ValueError('Native bank reader disagrees with its stored balance.')
    frontier = call(0x0202D919, save)
    frontier_before = read(frontier, 2)
    bp = call(0x0202D3F9, frontier, 0, 0)
    flags = call(0x020503D1, save)
    mom_enabled = bool(call(0x02066795, flags))
    bag = call(0x0207879D, save)
    bag_before = read(bag, 0x79C)
    contents = {}
    for pocket, name, count in ((0, 'items', 165), (1, 'medicine', 40),
                                 (2, 'balls', 24), (3, 'machines', 101),
                                 (4, 'berries', 64), (5, 'mail', 12),
                                 (6, 'battle_items', 30), (7, 'key_items', 50)):
        slots = []
        for slot in range(count):
            address = call(0x02078725, bag, pocket, slot)
            item, quantity = struct.unpack('<HH', read(address, 4))
            if item or quantity:
                if not 1 <= item <= 536 or not 1 <= quantity <= 999:
                    raise ValueError('Native inventory slot contains invalid data.')
                slots.append({'slot': slot, 'item': item, 'quantity': quantity})
        contents[name] = slots
    if (read(profile, 64) != profile_before or read(bag, 0x79C) != bag_before or
            read(frontier, 2) != frontier_before or
            read(phone + 0x140, 4) != bank_before):
        raise ValueError('Native private readers changed profile, bag, bank or Battle Points.')
    return {'candidate_sha256': report['output_sha256'], 'stored_wallet': wallet,
            'coins': coins, 'battle_points': bp, 'mom_savings': bank,
            'mom_savings_enabled': mom_enabled,
            'native_profile_sha256': hashlib.sha256(profile_before[:32]).hexdigest(),
            'native_bag_sha256': hashlib.sha256(bag_before).hexdigest(),
            'inventory': contents, 'money_diagnostics': diag.get('money'),
            'private_readers_preserve_profile_bag_bank_and_BP_bytes': True,
            'wallet_refill_getter_not_executed_by_inspection': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_wallet(args.run, args.report, args.rom), indent=2))

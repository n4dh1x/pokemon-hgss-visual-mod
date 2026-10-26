#!/usr/bin/env python3
"""Read party egg identity and hatch counters using original native getters.

Runs only on a private copy of a ROM-matched, settled field checkpoint. It does
not modify the emulator, input RAM, cartridge save or Pokemon data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inspect_eggs(run: Path, report_path: Path, rom_path: Path) -> dict:
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
    from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
                                   UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)
    from inspect_visible_state import inspect_run

    diag = inspect_run(run, report_path)
    if diag.get('native_battle') or not diag.get('enhancement_menu', {}).get('active'):
        raise ValueError('Freeze the settled field with SELECT before reading eggs.')
    report = json.loads(report_path.read_text())
    raw = rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != report['output_sha256']:
        raise ValueError('ROM differs from the matched candidate report.')
    rom = ndspy.rom.NintendoDSRom(raw)
    ram = (run / 'main-ram.bin').read_bytes()
    for address, size in ((0x0206E540, 32), (0x02074904, 12),
                          (0x02074640, 24), (0x0207003C, 0x94),
                          (0x0202CF54, 0xC), (0x0202CF60, 0x29C)):
        at = address - 0x02000000
        if ram[at:at + size] != rom.arm9[at:at + size]:
            raise ValueError(f'Native reader instructions differ at {address:#x}.')
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(0x02000000, ram)

    def read(address, size):
        if not 0x02000000 <= address <= 0x02400000 - size:
            raise ValueError('Native party/stat pointer is outside main RAM.')
        return bytes(uc.mem_read(address, size))

    def call(fn, a=0, b=0, c=0):
        uc.reg_write(UC_ARM_REG_SP, 0x023FF000)
        uc.reg_write(UC_ARM_REG_LR, 0x023FEF01)
        for reg, value in ((UC_ARM_REG_R0, a), (UC_ARM_REG_R1, b), (UC_ARM_REG_R2, c)):
            uc.reg_write(reg, value)
        uc.emu_start(fn, 0x023FEF00, count=1000000)
        if uc.reg_read(UC_ARM_REG_PC) != 0x023FEF00 or uc.reg_read(UC_ARM_REG_SP) != 0x023FF000:
            raise ValueError('Native reader did not return within its bound.')
        return uc.reg_read(UC_ARM_REG_R0)

    field = struct.unpack('<I', read(0x021D4158, 4))[0]
    save = struct.unpack('<I', read(field + 12, 4))[0]
    party = call(0x02074905, save)
    count = call(0x02074641, party)
    if not 0 <= count <= 6:
        raise ValueError('Invalid native party count.')
    result = {'candidate_sha256': report['output_sha256'], 'party': []}
    for slot in range(count):
        mon = call(0x02074645, party, slot)
        before = read(mon, 236)
        get = lambda attr: call(0x0206E541, mon, attr)
        entry = {'slot': slot, 'pokemon_sha256': hashlib.sha256(before).hexdigest()}
        for code, name in ((0, 'pid'), (3, 'checksum_failed'), (5, 'species'),
                           (7, 'ot_id'), (8, 'experience'), (9, 'cycles_or_friendship'),
                           (10, 'ability'), (76, 'is_egg'), (77, 'has_nickname'), (112, 'form'),
                           (146, 'egg_year'), (147, 'egg_month'), (148, 'egg_day'),
                           (149, 'met_year'), (150, 'met_month'), (151, 'met_day'),
                           (152, 'egg_location'), (153, 'met_location'),
                           (155, 'pokeball'), (156, 'met_level'),
                           (160, 'status'), (161, 'level'), (163, 'hp'), (164, 'max_hp')):
            entry[name] = get(code)
        for label, codes in (('ivs', (70, 71, 72, 74, 75, 73)),
                             ('evs', range(13, 19)), ('moves', range(54, 58)),
                             ('pp', range(58, 62))):
            entry[label] = [get(code) for code in codes]
        nickname = 0x02380000
        uc.mem_write(nickname, bytes(32))
        call(0x0206E541, mon, 117, nickname)
        codes = list(struct.unpack('<11H', read(nickname, 22)))
        if 0xFFFF not in codes:
            raise ValueError('Native nickname is missing its terminator.')
        entry['nickname_codes'] = codes[:codes.index(0xFFFF)]
        entry['native_shiny'] = bool(call(0x0207003D, mon))
        if read(mon, 236) != before:
            raise ValueError('Native private getters modified Pokemon bytes.')
        entry['private_getters_preserve_all_bytes'] = True
        result['party'].append(entry)
    stats = call(0x0202CF55, save)
    before = read(stats, 0x1C0)
    result['eggs_hatched'] = call(0x0202D18D, stats, 12)
    result['trainer_score'] = call(0x0202D18D, stats, 2)
    if read(stats, 0x1C0) != before:
        raise ValueError('Native private readers modified saved game statistics.')
    result['private_stat_readers_preserve_all_bytes'] = True
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_eggs(args.run, args.report, args.rom), indent=2))

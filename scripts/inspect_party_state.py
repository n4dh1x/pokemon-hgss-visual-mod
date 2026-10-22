#!/usr/bin/env python3
"""Read native saved-party EXP/EV fields on a private copy of a test RAM dump.

Requires the exact candidate and its matching state report. No input state/save is
edited. Native USA getter instructions run in Unicorn; no Pokemon layout or crypto
is reimplemented here. In-battle party copies are intentionally not interpreted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inspect_party(run: Path, report_path: Path, rom_path: Path) -> list[dict]:
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
    from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
        UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)
    import ndspy.rom
    from inspect_visible_state import inspect_run
    inspect_run(run, report_path)
    report = json.loads(report_path.read_text())
    raw = rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != report['output_sha256']:
        raise ValueError('Candidate ROM differs from the verified run report.')
    rom = ndspy.rom.NintendoDSRom(raw)
    ram = (run / 'main-ram.bin').read_bytes()
    # All executed main ARM9 code must match this exact candidate. Exclude the
    # loader's writable/BSS region by comparing the narrow getter entry points.
    for address, size in ((0x0206E540, 32), (0x02074904, 12),
                          (0x02074640, 4), (0x02074644, 20)):
        offset = address - 0x02000000
        if ram[offset:offset + size] != rom.arm9[offset:offset + size]:
            raise ValueError(f'Native getter instructions differ at {address:#x}.')
    def word(address):
        if not 0x02000000 <= address <= 0x023FFFFC:
            raise ValueError('Party diagnostic pointer outside main RAM.')
        return struct.unpack_from('<I', ram, address - 0x02000000)[0]
    field = word(0x021D4158)
    save = word(field + 12)
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(0x02000000, ram)
    def call(address, a=0, b=0, c=0):
        uc.reg_write(UC_ARM_REG_SP, 0x023FF000)
        uc.reg_write(UC_ARM_REG_LR, 0x023FEF01)
        for reg, value in ((UC_ARM_REG_R0,a), (UC_ARM_REG_R1,b), (UC_ARM_REG_R2,c)):
            uc.reg_write(reg,value)
        uc.emu_start(address, 0x023FEF00, count=1000000)
        if uc.reg_read(UC_ARM_REG_PC) != 0x023FEF00 or uc.reg_read(UC_ARM_REG_SP) != 0x023FF000:
            raise ValueError('Native getter did not return within its execution bound.')
        return uc.reg_read(UC_ARM_REG_R0)
    party = call(0x02074905, save)
    count = call(0x02074641, party)
    if not 0 <= count <= 6:
        raise ValueError('Native party count outside bounds.')
    result = []
    for index in range(count):
        mon = call(0x02074645,party,index)
        if not 0x02000000 <= mon <= 0x02400000 - 236:
            raise ValueError('Native party Pokemon pointer outside main RAM.')
        entry = {'slot':index}
        for code, label in ((5,'species'),(8,'experience'),(161,'level'),(163,'hp'),
                (13,'hp_ev'),(14,'attack_ev'),(15,'defense_ev'),(16,'speed_ev'),
                (17,'spatk_ev'),(18,'spdef_ev')):
            entry[label] = call(0x0206E541,mon,code)
        result.append(entry)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--rom',type=Path,required=True)
    a = p.parse_args()
    print(json.dumps(inspect_party(a.run,a.report,a.rom),indent=2))

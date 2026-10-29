#!/usr/bin/env python3
"""Read original Dex entries and unchanged-story evidence from a private RAM copy."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inspect_dex(run, report_path, rom_path):
    import ndspy.rom
    import ndspy.narc
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
    from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
                                   UC_ARM_REG_R0, UC_ARM_REG_R1)
    from inspect_visible_state import inspect_run
    diag = inspect_run(run, report_path)
    report = json.loads(report_path.read_text())
    raw = rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != report['output_sha256']:
        raise ValueError('ROM differs from the matched report.')
    rom = ndspy.rom.NintendoDSRom(raw)
    ram = (run / 'main-ram.bin').read_bytes()
    for address, size in ((0x02029408, 0x1238), (0x02028E9C, 0xC),
                          (0x020503D0, 0xC), (0x0201FD2C, 0x3C)):
        at = address - 0x02000000
        if ram[at:at+size] != rom.arm9[at:at+size]:
            raise ValueError(f'Native Dex reader differs at {address:#x}.')
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(0x02000000, ram)
    def read(address, size):
        if not 0x02000000 <= address <= 0x02400000-size:
            raise ValueError('Native Dex or save pointer is outside RAM.')
        return bytes(uc.mem_read(address,size))
    def call(fn,a=0,b=0):
        uc.reg_write(UC_ARM_REG_SP,0x023FF000);uc.reg_write(UC_ARM_REG_LR,0x023FEF01)
        uc.reg_write(UC_ARM_REG_R0,a);uc.reg_write(UC_ARM_REG_R1,b)
        uc.emu_start(fn,0x023FEF00,count=1000000)
        if uc.reg_read(UC_ARM_REG_PC)!=0x023FEF00 or uc.reg_read(UC_ARM_REG_SP)!=0x023FF000:
            raise ValueError('Native Dex reader did not return within its bound.')
        return uc.reg_read(UC_ARM_REG_R0)
    field=struct.unpack('<I',read(0x021D4158,4))[0]
    save=struct.unpack('<I',read(field+12,4))[0]
    dex=call(0x0202A635,save);profile=call(0x02028E9D,save);flags=call(0x020503D1,save)
    before=read(dex,0x340);profile_before=read(profile,32);flags_before=read(flags,0x44C)
    if struct.unpack_from('<I',before)[0]!=0xBEEFCAFE:raise ValueError('Invalid native Dex magic.')
    seen=[i for i in range(1,494) if before[0x44+(i-1)//8]&(1<<((i-1)%8))]
    caught=[i for i in range(1,494) if before[4+(i-1)//8]&(1<<((i-1)%8))]
    if call(0x02029E0D,dex)!=len(caught) or call(0x02029E49,dex)!=len(seen):
        raise ValueError('Native Dex counters disagree with stored flags.')
    lut=struct.unpack('<494H',ndspy.narc.NARC(rom.getFileByName('a/1/3/8')).files[0])
    if read(dex,0x340)!=before or read(profile,32)!=profile_before or read(flags,0x44C)!=flags_before:
        raise ValueError('Private native readers modified game progress.')
    return {'candidate_sha256':report['output_sha256'], 'seen':seen,'caught':caught,
            'national_seen':len(seen),'national_caught':len(caught),
            'johto_seen':sum(bool(lut[i]) for i in seen),'johto_caught':sum(bool(lut[i]) for i in caught),
            'dex_enabled':before[0x336],'national_enabled':before[0x337],
            'profile_national_enabled':bool(profile_before[29]&2),
            'dex_sha256':hashlib.sha256(before).hexdigest(),'dex_bytes':before.hex(),
            'profile_sha256':hashlib.sha256(profile_before).hexdigest(),'profile_bytes':profile_before.hex(),
            'story_vars_flags_sha256':hashlib.sha256(flags_before).hexdigest(),
            'lc_rng_seed':struct.unpack('<I',read(0x021D15A8,4))[0],
            'private_native_readers_preserve_dex_profile_and_story_bytes':True,
            'action':diag.get('pokedex_action'),'ui':diag.get('pokedex_ui')}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('run','report','rom'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect_dex(a.run,a.report,a.rom),indent=2))

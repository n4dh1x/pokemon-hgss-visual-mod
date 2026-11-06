#!/usr/bin/env python3
"""Read native PC-box identity/capture metadata from a private RAM copy."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from inspect_visible_state import inspect_run


def inspect_storage(run, report_path, rom_path):
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
    from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
    diag=inspect_run(run,report_path)
    if diag.get('native_battle') or not diag.get('enhancement_menu',{}).get('active'):
        raise ValueError('Freeze a settled field with the enhancement shortcut first.')
    report=json.loads(report_path.read_text());raw=rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['output_sha256']:
        raise ValueError('ROM differs from its matched report.')
    rom=ndspy.rom.NintendoDSRom(raw);ram=(run/'main-ram.bin').read_bytes()
    for address,size in ((0x020270D8,12),(0x0206E640,32)):
        at=address-0x02000000
        if ram[at:at+size]!=rom.arm9[at:at+size]:raise ValueError('Native PC/getter entry differs from ROM.')
    uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x02000000,0x400000);uc.mem_write(0x02000000,ram)
    def read(address,size):
        if not 0x02000000<=address<=0x02400000-size:raise ValueError('PC pointer exceeds main RAM.')
        return bytes(uc.mem_read(address,size))
    def call(fn,a=0,b=0,c=0):
        uc.reg_write(UC_ARM_REG_SP,0x023FF000);uc.reg_write(UC_ARM_REG_LR,0x023FEF01)
        for reg,value in ((UC_ARM_REG_R0,a),(UC_ARM_REG_R1,b),(UC_ARM_REG_R2,c)):uc.reg_write(reg,value)
        uc.emu_start(fn,0x023FEF00,count=1000000)
        if uc.reg_read(UC_ARM_REG_PC)!=0x023FEF00 or uc.reg_read(UC_ARM_REG_SP)!=0x023FF000:
            raise ValueError('Native getter exceeded its execution bound.')
        return uc.reg_read(UC_ARM_REG_R0)
    field=struct.unpack('<I',read(0x021D4158,4))[0];save=struct.unpack('<I',read(field+12,4))[0]
    pc=call(0x020270D9,save);before=read(pc,0x12300)
    # Pinned native pokemon_storage_system.h: 18 PC_BOX records of 0x1000;
    # each contains 30 136-byte BoxPokemon followed by 16 native padding bytes.
    records=[];hashes=[]
    for box in range(18):
        for slot in range(30):
            mon=pc+box*0x1000+slot*136;data=read(mon,136)
            hashes.append(hashlib.sha256(data).hexdigest())
            if data==bytes(136):continue
            get=lambda attr:call(0x0206E641,mon,attr)
            species=get(5)
            if not species:continue
            if not 1<=species<=493 or get(3):raise ValueError('Invalid native boxed Pokemon/checksum.')
            entry={'box':box,'slot':slot,'species':species,'box_pokemon_sha256':hashes[-1]}
            for attr,name in ((0,'pid'),(7,'ot_id'),(8,'experience'),(9,'friendship'),(10,'ability'),(76,'is_egg'),(112,'form'),(155,'pokeball'),(156,'met_level')):
                entry[name]=get(attr)
            for name,attrs in (('ivs',(70,71,72,74,75,73)),('moves',range(54,58)),('pp',range(58,62))):entry[name]=[get(a) for a in attrs]
            if read(mon,136)!=data:raise ValueError('Native private getters changed a boxed record.')
            records.append(entry)
    if read(pc,0x12300)!=before:raise ValueError('Native private inspection changed PC bytes.')
    return {'candidate_sha256':report['output_sha256'],'records':records,'slot_sha256':hashes,
        'storage_sha256':hashlib.sha256(before).hexdigest(),'active_box':struct.unpack_from('<I',before,0x12000)[0],
        'native_layout':'18 x 0x1000 PC_BOX; 30 x 136-byte BoxPokemon plus 16 padding bytes',
        'private_getters_preserve_all_storage_bytes':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','report','rom'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();print(json.dumps(inspect_storage(a.run,a.report,a.rom),indent=2))

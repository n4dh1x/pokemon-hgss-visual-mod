#!/usr/bin/env python3
"""Compare an active IV/EV view with native getters on a private RAM copy."""
import argparse,hashlib,json,struct
from pathlib import Path

def inspect_summary(run: Path, report_path: Path, rom_path: Path) -> dict:
    import ndspy.rom
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
    from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2
    from inspect_visible_state import inspect_run
    diagnostics=inspect_run(run,report_path)
    view=diagnostics.get('summary_view',{})
    if view.get('mode') not in (1,2):raise ValueError('Capture an active EV or IV view before reading summary data.')
    report=json.loads(report_path.read_text());raw=rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['output_sha256']:raise ValueError('Candidate ROM differs from the run report.')
    rom=ndspy.rom.NintendoDSRom(raw);ram=(run/'main-ram.bin').read_bytes()
    for address,size in ((0x0208A520,68),(0x0206E540,32),(0x0206E640,32),(0x02070D90,8)):
        offset=address-0x02000000
        if ram[offset:offset+size]!=rom.arm9[offset:offset+size]:raise ValueError(f'Native getter bytes differ at {address:#x}.')
    def read(address,size):
        offset=address-0x02000000
        if offset<0 or offset+size>len(ram):raise ValueError('Summary pointer is outside main RAM.')
        return ram[offset:offset+size]
    def word(address):return struct.unpack('<I',read(address,4))[0]
    summary=view['summary'];base=word(summary+0x22C);kind=read(base+0x11,1)[0]
    if kind>2 or read(summary+0x7BC,1)!=b'\x01' or not 8<=word(summary+0x228)<=32:raise ValueError('Summary is not on its valid native skills page.')
    uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x02000000,0x400000);uc.mem_write(0x02000000,ram)
    def call(address,a=0,b=0,c=0):
        uc.reg_write(UC_ARM_REG_SP,0x023FF000);uc.reg_write(UC_ARM_REG_LR,0x023FEF01)
        for reg,value in ((UC_ARM_REG_R0,a),(UC_ARM_REG_R1,b),(UC_ARM_REG_R2,c)):uc.reg_write(reg,value)
        uc.emu_start(address,0x023FEF00,count=1000000)
        if uc.reg_read(UC_ARM_REG_PC)!=0x023FEF00 or uc.reg_read(UC_ARM_REG_SP)!=0x023FF000:raise ValueError('Native getter did not return within its execution bound.')
        return uc.reg_read(UC_ARM_REG_R0)
    mon=call(0x0208A521,summary)
    if mon!=view['pokemon']:raise ValueError('Recorded view and native summary getter identify different Pokemon.')
    length=136 if kind==2 else 236;before=read(mon,length)
    getter=0x0206E641 if kind==2 else 0x0206E541
    order=(0,1,2,4,5,3)
    ivs=[call(getter,mon,70+i) for i in order];evs=[call(getter,mon,13+i) for i in order]
    species=call(getter,mon,5)
    expected=evs if view['mode']==1 else ivs
    if expected!=view['values']:raise ValueError('Displayed numbers do not match the native getter values.')
    after=bytes(uc.mem_read(mon,length))
    if before!=after:raise ValueError('Private native getter calls changed Pokemon data.')
    return {'candidate_sha256':report['output_sha256'],'mode':'EVs' if view['mode']==1 else 'IVs','data_type':kind,
        'pokemon_pointer':hex(mon),'species':species,'stat_order':['HP','Attack','Defense','Sp.Atk','Sp.Def','Speed'],
        'ivs':ivs,'evs':evs,'displayed_values':view['values'],'matches_native_getters':True,
        'pokemon_sha256_before':hashlib.sha256(before).hexdigest(),'pokemon_sha256_after':hashlib.sha256(after).hexdigest(),
        'cached_normal_stats':list(struct.unpack('<7H',read(summary+0x254,14))),
        'scope':'Read-only interpretation of this bounded, ROM-matched active summary checkpoint.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--rom',type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect_summary(a.run,a.report,a.rom),indent=2))
if __name__=='__main__':main()

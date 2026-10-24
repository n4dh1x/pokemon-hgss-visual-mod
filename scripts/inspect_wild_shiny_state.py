#!/usr/bin/env python3
"""Read retained wild/battle identities with original native getters on a copy."""
import argparse,hashlib,json,struct
from pathlib import Path

def inspect_wilds(run:Path,report_path:Path,rom_path:Path):
    import ndspy.rom
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
    from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2
    from inspect_visible_state import inspect_run
    diag=inspect_run(run,report_path);report=json.loads(report_path.read_text());raw=rom_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['output_sha256']:raise ValueError('ROM differs from the candidate report.')
    rom=ndspy.rom.NintendoDSRom(raw);ram=(run/'main-ram.bin').read_bytes();state=(run/'state.bin').read_bytes()
    for address,size in ((0x0206E540,32),(0x0206E640,32),(0x0207003C,0x94),(0x0202D9C4,12),(0x020403AC,20)):
        offset=address-0x02000000
        if ram[offset:offset+size]!=rom.arm9[offset:offset+size]:raise ValueError('Native getter/check bytes differ from the ROM.')
    uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x02000000,0x400000);uc.mem_write(0x02000000,ram)
    def call(fn,a=0,b=0,c=0):
        uc.reg_write(UC_ARM_REG_SP,0x023FF000);uc.reg_write(UC_ARM_REG_LR,0x023FEF01)
        for reg,value in ((UC_ARM_REG_R0,a),(UC_ARM_REG_R1,b),(UC_ARM_REG_R2,c)):uc.reg_write(reg,value)
        uc.emu_start(fn,0x023FEF00,count=1000000)
        if uc.reg_read(UC_ARM_REG_PC)!=0x023FEF00 or uc.reg_read(UC_ARM_REG_SP)!=0x023FF000:raise ValueError('Native getter did not return within its bound.')
        return uc.reg_read(UC_ARM_REG_R0)
    def pokemon(data):
        if len(data)!=236:raise ValueError('Expected a whole party Pokemon.')
        at=0x02380000;uc.mem_write(at,data)
        get=lambda attr:call(0x0206E541,at,attr)
        pid=get(0);owner=get(7);native_shiny=bool(call(0x0207003D,at))
        xor=(pid&65535)^(pid>>16)^(owner&65535)^(owner>>16)
        result={'species':get(5),'pid':pid,'ot_id':owner,'native_shiny':native_shiny,'shiny_xor':xor,
                'level':get(161),'hp':get(163),'max_hp':get(164),'status':get(160),'nature':pid%25,'form':get(112),'ability':get(10),
                'ivs':[get(i) for i in (70,71,72,74,75,73)],'moves':[get(i) for i in range(54,58)],
                'pokemon_sha256':hashlib.sha256(data).hexdigest()}
        if native_shiny!=(xor<8):raise ValueError('Native shininess differs from the unmodified Gen IV rule.')
        if bytes(uc.mem_read(at,236))!=data:raise ValueError('Private getter calls modified Pokemon data.')
        result['private_getters_preserve_all_bytes']=True
        return result
    marker=struct.pack('<2I',0x48534745,1)
    base=state.index(marker);symbols=report['resident_payload']['symbols'];payload=report['resident_payload']
    start=base+symbols['gVisibleState']-payload['address']
    if start<base or start+1592>base+payload['size']:raise ValueError('Retained slots exceed the payload.')
    result={'candidate_sha256':report['output_sha256'],'retained':[],'native_battle':None}
    for slot in diag['slots']:
        if not slot['species']:continue
        offset=start+32+slot['index']*260+12
        mon=pokemon(state[offset:offset+236])
        if mon['pid']!=slot['personality'] or mon['species']!=slot['species']:raise ValueError('Retained diagnostics disagree with native data.')
        entry={'index':slot['index'],'owned_active':slot['owned_active'],**mon}
        if slot['owned_active']:
            at=int(slot['object'],16)+0x38-0x02000000
            if at<0 or at+12>len(ram):raise ValueError('Object parameters exceed main RAM.')
            entry['native_object_params']=list(struct.unpack_from('<3I',ram,at))
            entry['native_object_shiny_bit']=bool(entry['native_object_params'][2]&1)
        result['retained'].append(entry)
    if 'native_battle' in diag:
        at=int(diag['native_battle']['enemy_party'],16)+8-0x02000000
        if at<0 or at+236>len(ram):raise ValueError('Battle Pokemon exceeds main RAM.')
        result['native_battle']=pokemon(ram[at:at+236])
        result['native_battle']['identical_retained_slots']=diag['native_battle']['identical_retained_slots']
    field=struct.unpack_from('<I',ram,0x021D4158-0x02000000)[0]
    if 0x02000000<=field<0x02400000-16:
        save=struct.unpack_from('<I',ram,field+12-0x02000000)[0]
        party=call(0x02074905,save);count=call(0x02074641,party)
        if not 0<=count<=6:raise ValueError('Invalid native saved-party count.')
        bag=call(0x0207879D,save);ball=bag+0x6C0-0x02000000
        if ball<0 or ball+4>len(ram):raise ValueError('Native balls slot exceeds main RAM.')
        result['native_ball_slot']=list(struct.unpack_from('<2H',ram,ball))
        # Original save/variable getters on this private snapshot. Preserve the
        # whole native 104-byte roaming block while reading capture flags.
        roamer_base=call(0x0202D9C5,save);roamer_at=roamer_base-0x02000000
        if roamer_at<0 or roamer_at+104>len(ram):raise ValueError('Native roamer save exceeds main RAM.')
        roaming=ram[roamer_at:roamer_at+104]
        result['native_roamers']={'records':[list(struct.unpack_from('<5I',roaming,16+20*i)) for i in range(4)],
            'locations':list(roaming[96:100]),
            'captured_flags':[call(0x020403AD,field,0x4045+i) for i in range(4)]}
        if bytes(uc.mem_read(roamer_base,104))!=roaming:raise ValueError('Private roaming getters modified saved data.')
        result['native_roamers']['private_getters_preserve_all_bytes']=True
        result['party']=[]
        for slot in range(count):
            at=call(0x02074645,party,slot)-0x02000000
            if at<0 or at+236>len(ram):raise ValueError('Party Pokemon exceeds main RAM.')
            result['party'].append({'slot':slot,**pokemon(ram[at:at+236])})
    result['scope']='Read-only native getters and shiny rule on this ROM-matched snapshot; no live RAM or save writes.'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True,type=Path);p.add_argument('--report',required=True,type=Path);p.add_argument('--rom',required=True,type=Path)
    a=p.parse_args();print(json.dumps(inspect_wilds(a.run,a.report,a.rom),indent=2))

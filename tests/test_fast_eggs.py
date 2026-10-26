"""Five actual steps, native daycare cycles and original valid-egg selection."""
from pathlib import Path
import unittest
import test_settings as api
from gameplay.eggs import install_eggs, MAIN_CONTEXTS
from gameplay.field import verify_field_files
ROOT = Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE, 'Install native ARM dependencies.')
class TestFastEggs(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.payload=api.build_payload()
    def setUp(self):
        owner=self;self.original=False;self.native_ready=0;self.events=[];self.mons=[]
        self.parents=[0,0];self.parent_steps=[0,0];self.pending=0;self.cycle=0;self.compat=70;self.random=0;self.month=1;self.day=1;self.penalty=0
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if owner.original and (0x206CD1C<=address<0x206CE94 or 0x206CB34<=address<0x206CB88 or 0x206CCD8<=address<0x206CD1C):return
                args=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)];a,b,c,d=args
                result=0
                if address==0x206CD1C:
                    owner.events.append(('native',a,b,c));result=owner.native_ready
                elif address==0x2074640: result=len(owner.mons)
                elif address==0x2074644:
                    owner.assertLess(b,len(owner.mons));result=owner.party+0x100+0x100*b
                elif address==0x206E540:
                    slot=(a-owner.party-0x100)//0x100;owner.assertIn(slot,range(len(owner.mons)));result=owner.mons[slot].get(b,0)
                elif address==0x206EC40:
                    slot=(a-owner.party-0x100)//0x100;owner.assertEqual(b,9);value=f.get(c);owner.mons[slot][b]=value;owner.events.append(('cycles',slot,value))
                elif address==0x206C1C8:
                    f.put(b,owner.daycare+0x100);f.put(b+4,owner.daycare+0x200)
                elif address==0x206E640:
                    owner.assertEqual(b,172);result=owner.parents[(a-owner.daycare)//0x100-1]
                elif address==0x20292DC: result=owner.daycare+0x100*(b+1)
                elif address==0x2029324: owner.parent_steps[(a-owner.daycare)//0x100-1]+=b
                elif address==0x20292EC: result=owner.parent_steps[(a-owner.daycare)//0x100-1]
                elif address==0x20292F8: result=owner.pending
                elif address==0x206CCC4: result=owner.compat
                elif address==0x201FD44: result=owner.random
                elif address==0x206C274: owner.pending=1;owner.events.append(('bred',))
                elif address==0x209316C: owner.events.append(('phone',a))
                elif address==0x2029314: result=owner.cycle
                elif address==0x202933C: owner.cycle=b&255
                elif address==0x205560C: result=owner.day
                elif address==0x2055600: result=owner.month
                elif address==0x2055670: result=owner.penalty
                else:return super().hook(uc,address,size,context)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        self.party=0x02280000;self.daycare=0x02290000;self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gFastEggState'];self.f.put(self.extra+48,1)
    def step(self):return self.f.execute('EnhancedDaycareStep',self.daycare,self.party,self.f.field)
    def egg(self,cycles=20,bad=False):return {3:int(bad),76:1,173:1,9:cycles,10:0}
    def native(self):
        rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds');self.f.uc.mem_write(0x02000000,bytes(rom.arm9));self.original=True
        self.payload.symbols['OriginalEggSelector']=0x0206CE45
    def test_exactly_five_calls_only_first_valid_egg_cycles_change(self):
        self.mons=[self.egg(0,True),{9:99},self.egg(20),self.egg(30)]
        before=[dict(m) for m in self.mons]
        for i in range(4):self.assertEqual(self.step(),0);self.assertEqual(self.mons,before);self.assertEqual(self.f.get(self.state+8),i+1)
        self.assertEqual(self.step(),1);before[2][9]=0;self.assertEqual(self.mons,before);self.assertEqual(self.f.get(self.state+8),0);self.assertEqual(self.f.get(self.state+16),1)
        self.assertEqual([e[0] for e in self.events],['native']*5+['cycles'])
    def test_off_wrong_owner_unloaded_or_different_save_and_empty_party_reset_progress(self):
        for mode in ('off','wrong-owner','unloaded','different-save','empty','bad-only'):
            self.f.put(self.extra+48,1);self.f.owner=0x12345678;self.f.put(self.f.state+8,1);self.f.put(self.f.field+12,self.f.save);self.mons=[self.egg()]
            for _ in range(4):self.step()
            if mode=='off':self.f.put(self.extra+48,0)
            elif mode=='wrong-owner':self.f.owner^=1
            elif mode=='unloaded':self.f.put(self.f.state+8,0)
            elif mode=='different-save':self.f.put(self.f.field+12,self.f.save+4)
            elif mode=='empty':self.mons=[]
            else:self.mons=[self.egg(0,True)]
            self.native_ready=1;self.assertEqual(self.step(),1);self.assertEqual(self.f.get(self.state+8),0);self.assertFalse(any(e[0]=='cycles' for e in self.events));self.events=[];self.native_ready=0
    def test_party_reordering_keeps_steps_and_each_next_egg_requires_five_steps(self):
        self.mons=[self.egg(20),self.egg(30)]
        for _ in range(4):self.step()
        self.mons.reverse();self.assertEqual(self.step(),1);self.assertEqual([m[9] for m in self.mons],[0,20]);self.mons[0][76]=self.mons[0][173]=0
        for _ in range(4):self.assertEqual(self.step(),0)
        self.assertEqual(self.step(),1);self.assertEqual(self.mons[1][9],0);self.assertEqual(self.f.get(self.state+16),2)
    def test_owner_change_starts_new_counter_and_native_ready_return_is_preserved(self):
        self.mons=[self.egg()]
        for _ in range(4):self.step()
        self.f.owner=0x87654321;self.f.put(self.f.state+4,self.f.owner);self.native_ready=1
        self.assertEqual(self.step(),1);self.assertEqual(self.f.get(self.state+8),1);self.assertEqual(self.mons[0][9],20)
    def test_original_calendar_cycles_and_flame_body_magma_armor_still_run(self):
        self.native();self.f.put(self.extra+48,0)
        for ability in (0,40,49):
            for special in (False,True):
                self.month,self.day=(1,12) if special else (1,1);self.penalty=0
                self.mons=[{10:ability},self.egg(3),self.egg(1),self.egg(0,True)];self.cycle=(230 if special else 255)-1
                self.assertEqual(self.step(),0);self.assertEqual(self.cycle,0);self.assertEqual([m.get(9) for m in self.mons[1:]],[1 if ability else 2,0,0])
                self.cycle=(230 if special else 255)-1;self.assertEqual(self.step(),1)
        self.month,self.day=1,12;self.penalty=1;self.cycle=229;self.mons=[self.egg(3)]
        self.assertEqual(self.step(),0);self.assertEqual(self.cycle,230);self.assertEqual(self.mons[0][9],3)
        self.cycle=254;self.assertEqual(self.step(),0);self.assertEqual(self.mons[0][9],2)
    def test_original_parent_exp_breeding_roll_notification_and_native_ready_hatch_are_preserved(self):
        self.native();self.parents=[1,1];self.parent_steps=[254,254];self.cycle=254;self.mons=[self.egg(0)]
        self.assertEqual(self.step(),1);self.assertEqual(self.parent_steps,[255,255]);self.assertEqual(self.pending,1);self.assertIn(('phone',self.f.field),self.events);self.assertEqual(self.cycle,0);self.assertEqual(self.f.get(self.state+20),1)
        self.parents=[1,1];self.parent_steps=[254,254];self.pending=0;self.random=65535;self.mons=[self.egg(20)];self.events=[]
        self.assertEqual(self.step(),0);self.assertEqual(self.parent_steps,[255,255]);self.assertEqual(self.pending,0);self.assertNotIn(('phone',self.f.field),self.events)
        self.parents=[1,0];self.parent_steps=[1,9];self.step();self.assertEqual(self.parent_steps,[2,9])
    def test_original_selector_skips_bad_eggs_and_matches_first_ready_valid_egg(self):
        self.native();self.mons=[self.egg(0,True),{9:0},self.egg(20),self.egg(30)]
        for _ in range(5):self.step()
        self.assertEqual(self.f.execute('OriginalEggSelector',self.party),self.party+0x300)
        self.mons[2][76]=self.mons[2][173]=0
        self.assertEqual(self.f.execute('OriginalEggSelector',self.party),0)
        self.mons[3][9]=0;self.assertEqual(self.f.execute('OriginalEggSelector',self.party),self.party+0x400)
    def test_both_baselines_only_change_guarded_native_step_call_and_reject_context_mutation(self):
        for game in ('heartgold','soulsilver'):
            original=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds');rom=api.ndspy.rom.NintendoDSRom(original.save());changes=install_eggs(rom,self.payload)
            self.assertEqual(len(changes),1);self.assertEqual(rom.arm9,original.arm9);verify_field_files(original,rom,changes)
            for address,size,digest in MAIN_CONTEXTS:
                rom=api.ndspy.rom.NintendoDSRom(original.save());arm=bytearray(rom.arm9);arm[address-rom.arm9RamAddress]^=1;rom.arm9=bytes(arm)
                with self.assertRaises(api.PatchMismatch):install_eggs(rom,self.payload)
            rom=api.ndspy.rom.NintendoDSRom(original.save());o=rom.loadArm9Overlays([1])[1];o.data[0x21e78a6-o.ramAddress]^=1;rom.files[o.fileID]=o.save(compress=False)
            with self.assertRaises(api.PatchMismatch):install_eggs(rom,self.payload)

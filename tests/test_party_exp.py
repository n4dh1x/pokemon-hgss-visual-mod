"""Execute party EXP recipient ownership and appended-message preservation."""
from pathlib import Path
import hashlib, struct, sys, unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import test_settings as api

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestPartyExperience(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.payload=api.build_payload()
    def setUp(self):
        parent=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if any(lo<=address<hi for lo,hi in f.native_ranges):return
                handlers={0x02245898,0x0223E6A0,0x0223A7E0,0x0223A7E8,0x0223A7F4,
                          0x02074640,0x02074644,0x0206E540,0x0206FBE8,0x020F2BA4,
                          0x022454E8,0x02245508,0x0223C494,0x0223A930,0x0223A834,
                          0x0223A880,0x02077D88,0x020726C0,0x022568B0,0x020F2BA4,
                          0x0206FCDC,0x0206EC40,0x022463E8,0x0223B718}
                if address not in handlers:return super().hook(uc,address,size,context)
                a,b,c,d=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                f.calls.append((address,a,b,c,d));result=0
                if address==0x02245898:
                    slot=f.get(b+0x48);side=(f.get(parent.ctx+0x74)>>1)&1
                    if slot>=len(f.mons):f.put(parent.ctx+0x178,0);f.finished.append((a,b))
                    elif f.get(b+0x28)==0:
                        f.awards.append((slot,f.get(parent.ctx+0x9C),f.get(parent.ctx+0xA0),f.get(parent.ctx+0xA4+4*side)))
                        f.put(b+0x28,37)
                    else:f.put(b+0x48,slot+1);f.put(b+0x28,0)
                elif address==0x0223E6A0:f.original_calcs+=1;result=17
                elif address==0x0223A7E0:result=f.battle_type
                elif address==0x0223A7E8:result=parent.opponent
                elif address==0x0223A7F4:result=parent.party
                elif address==0x02074640:result=len(f.mons)
                elif address==0x02074644:result=parent.party+0x100+b*236
                elif address==0x0206E540:result=f.mons[(a-parent.party-0x100)//236].get(b,0)
                elif address==0x0206FBE8:parent.assertEqual((a,b),(19,9));result=f.base_exp
                elif address==0x020F2BA4:result=a//b
                elif address==0x02245508:f.increments.append(b)
                elif address==0x022454E8:result=23
                elif address==0x0223C494:f.messages.append(bytes(uc.mem_read(c,36)));result=3
                elif address==0x0223A930:result=0x02230000
                elif address==0x0223A834:result=len(f.mons)
                elif address==0x0223A880:result=parent.party+0x100+c*236
                elif address==0x02077D88:result=f.effects.get(a,0)
                elif address==0x020726C0:result=1<<a
                elif address==0x022568B0:result=f.original_trainer
                elif address==0x0206FCDC:result=0
                elif address==0x0206EC40:
                    parent.assertEqual(b,8);f.mons[(a-parent.party-0x100)//236][8]=f.get(c)
                elif address==0x022463E8:f.ev_calls.append((a,b,c,d))
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture(methodName='runTest');f=self.f;f.native_ranges=[];f.setUp()
        self.work,self.ctx,self.battle,self.party,self.opponent=0x02220000,0x02221000,0x02226000,0x02227000,0x02229000
        self.state=self.payload.symbols['gPartyExperience']
        f.battle_type=0;f.base_exp=57;f.original_calcs=0
        f.mons=[{5:152,76:0,163:20},{5:19,76:0,163:12},{5:163,76:0,163:15}]
        f.awards=[];f.finished=[];f.messages=[];f.increments=[]
        f.effects={216:51,231:66};f.original_trainer=1;f.ev_calls=[]
        f.put(self.work,self.battle);f.put(self.work+4,self.ctx);f.put(self.ctx+0x178,self.work)
        f.put(self.ctx+0x74,1);f.put(self.ctx+0x9C,17);f.put(self.ctx+0xA0,8);f.put(self.ctx+0xA4,1)
        f.uc.mem_write(self.opponent+0x195,b'\x01')
        f.uc.mem_write(self.ctx+0x2D40+192,struct.pack('<H',19));f.uc.mem_write(self.ctx+0x2D74+192,b'\x02')
    def test_full_for_each_participant_half_for_each_bench_and_pointer_reuse(self):
        f=self.f;f.put(self.ctx+0xA4,5)
        for _ in range(7):f.execute('EnhancedPartyExperienceTask',1,self.work)
        self.assertEqual(f.awards,[(0,17,0,1),(1,8,0,2),(2,17,0,4)])
        self.assertEqual(f.finished,[(1,self.work)])
        self.assertEqual(f.get(self.ctx+0xA4),0);self.assertEqual(f.get(self.ctx+0x9C),17);self.assertEqual(f.get(self.ctx+0xA0),8)
        self.assertEqual(f.get(self.state+8),0);self.assertEqual(f.get(self.state+60),3)
        f.put(self.work+0x48,0);f.put(self.work+0x28,0);f.put(self.ctx+0x178,self.work);f.put(self.ctx+0xA4,2)
        f.execute('EnhancedPartyExperienceTask',1,self.work)
        self.assertEqual(f.awards[-1],(0,8,0,1));self.assertEqual(f.get(self.state+44),2)
    def test_skip_fainted_eggs_empty_slots_and_independent_double_side(self):
        f=self.f;f.mons=[{5:152,163:0},{5:175,76:1,163:20},{5:0,163:20},{5:19,163:10}]
        f.put(self.ctx+0x74,3);f.put(self.ctx+0xA8,8);f.put(self.ctx+0xA4,0x31)
        for _ in range(3):f.execute('EnhancedPartyExperienceTask',1,self.work)
        self.assertEqual(f.awards,[(3,17,0,8)]);self.assertEqual(f.get(self.ctx+0xA4),0x31);self.assertEqual(f.get(self.ctx+0xA8),0)
    def test_capture_child_awards_party_then_restores_capture_parent_once(self):
        f=self.f;capture=self.payload.symbols['gCaptureExperience'];parent=0x02231000
        # The capture task already owns this parent and records its context
        # before scheduling the independent EXP child allocation.
        for offset,value in ((0,parent),(4,self.ctx),(8,1),(16,0),(20,99),(24,45),(28,5),(32,8)):
            f.put(capture+offset,value)
        for _ in range(7):f.execute('EnhancedCaptureExperienceChild',2,self.work)
        self.assertEqual(f.awards,[(0,17,0,1),(1,8,0,2),(2,8,0,4)])
        self.assertEqual(f.finished,[(2,self.work)])
        self.assertEqual(f.get(capture+40),1);self.assertEqual(f.get(capture+8),2)
        self.assertEqual(f.get(self.ctx+0x178),parent)
        self.assertEqual([f.get(self.ctx+n) for n in (0x74,0x9C,0xA0,0xA4,0xA8)],[0,99,45,5,8])
        self.assertEqual(f.get(self.state+48),1)
    def test_disabled_calls_originals_without_changing_native_distribution(self):
        f=self.f;f.put(api.PAYLOAD_BASE+28,0)
        self.assertEqual(f.execute('EnhancedCalcExperience',self.battle,self.ctx),17)
        self.assertEqual(f.original_calcs,1)
        f.execute('EnhancedPartyExperienceTask',1,self.work)
        self.assertEqual(f.awards,[(0,17,8,1)]);self.assertEqual(f.get(self.state+44),0)
    def test_base_formula_minimum_and_script_skip_for_restricted_contexts(self):
        f=self.f;f.execute('EnhancedCalcExperience',self.battle,self.ctx)
        self.assertEqual((f.get(self.ctx+0x9C),f.get(self.ctx+0xA0)),(16,8));self.assertEqual(f.increments,[1])
        f.base_exp=1;f.execute('EnhancedCalcExperience',self.battle,self.ctx)
        self.assertEqual((f.get(self.ctx+0x9C),f.get(self.ctx+0xA0)),(1,1))
        for typ in (4,32,128,512):
            f.battle_type=typ;f.increments=[];f.put(self.ctx+0x9C,99)
            f.execute('EnhancedCalcExperience',self.battle,self.ctx)
            self.assertEqual(f.get(self.ctx+0x9C),99);self.assertEqual(f.increments,[1,23])
        f.battle_type=0;f.uc.mem_write(self.opponent+0x195,b'\x00');f.increments=[]
        f.execute('EnhancedCalcExperience',self.battle,self.ctx);self.assertEqual(f.increments,[1,23])
    def test_one_collective_message_preserves_other_messages_and_printer_handle(self):
        f=self.f;message=0x02230000;f.uc.mem_write(message,struct.pack('<9I',0x10001,*([0]*8)))
        f.put(self.state+8,1);f.put(self.state+32,1)
        for _ in range(3):self.assertEqual(f.execute('EnhancedExperienceMessage',self.battle,2,message,1),3)
        self.assertEqual(len(f.messages),1);self.assertEqual(struct.unpack_from('<H',f.messages[0],2)[0],1276)
        self.assertEqual(f.messages[0][1],0);self.assertEqual(f.get(self.state+52),1);self.assertEqual(f.get(self.state+56),2)
        f.put(self.state+32,0);f.execute('EnhancedExperienceMessage',self.battle,2,message,1)
        self.assertEqual(f.messages[-1],bytes(f.uc.mem_read(message,36)))
    def test_actual_native_reward_code_preserves_held_item_trainer_trade_and_level100_rules(self):
        for game in ('heartgold','soulsilver'):
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():self.skipTest('Build local baselines first.')
            rom=api.ndspy.rom.NintendoDSRom.fromFile(path);ov=rom.loadArm9Overlays([12])[12]
            # Execute the original reward task, with bounded external APIs. This
            # checks native modifiers and EXP writes, rather than recreating them.
            for held,typ,ot,language,level,expected in (
                (0,0,1,2,5,8),(216,0,1,2,5,8),(231,0,1,2,5,12),
                (0,1,1,2,5,12),(0,1,0,2,5,18),(0,1,0,3,5,20),
                (0,0,1,2,100,0)):
                self.setUp();f=self.f;f.uc.mem_write(ov.ramAddress,bytes(ov.data))
                f.native_ranges=[(0x02245898,0x022463E8)];f.battle_type=typ;f.original_trainer=ot
                # gGameLanguage is a literal in the guarded native reward body.
                lang_at=struct.unpack_from('<I',ov.data,0x02245C44-ov.ramAddress)[0]
                f.uc.mem_write(lang_at,b'\x02')
                f.put(self.ctx+0x3144,1);f.put(self.work+0x48,1)
                f.mons[1].update({6:held,8:100,12:language,161:level})
                f.execute('EnhancedPartyExperienceTask',1,self.work)
                self.assertEqual(f.mons[1][8],100+expected,(game,held,typ,ot,language,level))
                self.assertEqual(len(f.ev_calls),int(level!=100))
                if expected:self.assertEqual(struct.unpack_from('<I',f.messages[-1],8)[0],expected)
                self.assertEqual(f.get(self.ctx+0xA4),1)
    def test_arm_sdk_division_interworks_with_thumb_and_matches_integer_quotients(self):
        path=ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds'
        if not path.exists():self.skipTest('Build local baseline first.')
        rom=api.ndspy.rom.NintendoDSRom.fromFile(path);f=self.f
        lo,hi=0x020F2BA4,0x020F2E00
        f.uc.mem_write(lo,bytes(rom.arm9[lo-rom.arm9RamAddress:hi-rom.arm9RamAddress]))
        f.native_ranges=[(lo,hi)]
        for numerator,denominator in ((114,7),(1,7),(0,7),(999999,7),(0xFFFFFFFF,7),(100,100)):
            self.assertEqual(f.execute('EnhancedUnsignedDivide',numerator,denominator),numerator//denominator)
    def test_both_roms_append_one_message_and_guard_all_changed_files(self):
        import ndspy.narc
        from gameplay.party_exp import install_party_exp
        from gameplay.field import verify_field_files
        from gameplay.messages import entries
        from gameplay.patches import PatchMismatch
        for game in ('heartgold','soulsilver'):
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():self.skipTest('Build local baselines first.')
            original=api.ndspy.rom.NintendoDSRom.fromFile(path);patched=api.ndspy.rom.NintendoDSRom.fromFile(path)
            changes,assets=install_party_exp(patched,self.payload);verify_field_files(original,patched,changes,assets)
            old=ndspy.narc.NARC(original.files[assets[0].file_id]);new=ndspy.narc.NARC(patched.files[assets[0].file_id])
            self.assertEqual(len(old.files),len(new.files))
            for i,(a,b) in enumerate(zip(old.files,new.files)):
                if i!=197:self.assertEqual(a,b)
            _,before=entries(old.files[197]);_,after=entries(new.files[197]);self.assertEqual(len(after),1277)
            for (a,n),(b,m) in zip(before,after):self.assertEqual(n,m);self.assertEqual(old.files[197][a:a+2*n],new.files[197][b:b+2*m])
            with self.assertRaises((ValueError,PatchMismatch)):verify_field_files(original,patched,changes)
            patched.files[assets[0].file_id]=original.files[assets[0].file_id]
            with self.assertRaises((ValueError,PatchMismatch)):verify_field_files(original,patched,changes,assets)

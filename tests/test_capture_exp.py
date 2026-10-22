"""Execute capture task ownership and guarded native EXP completion."""
from pathlib import Path
import struct,sys,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import test_settings as api

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestCaptureExperience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.payload=api.build_payload()
    def setUp(self):
        parent=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if any(lo<=address<hi for lo,hi in f.native_ranges):return
                handlers={0x022465A8,0x02245898,0x0223E6A0,0x0223A7E0,0x0223A7F4,
                          0x02074640,0x02074644,0x0206E540,0x0201AA8C,0x0201AB0C,
                          0x0200E320,0x0200E390,0x02232F60,0x0223A930,0x0223A834}
                if address not in handlers:return super().hook(uc,address,size,context)
                a,b,c,d=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                f.calls.append((address,a,b,c,d));result=0
                if address==0x022465A8:f.parent_calls.append((a,b))
                elif address==0x02245898:
                    if f.get(b+0x28):f.put(parent.ctx+0x178,0);f.freed.append(b);f.destroyed.append(a)
                    else:f.put(b+0x28,1)
                elif address==0x0223E6A0:
                    parent.assertEqual(f.get(b+0xB4),0);f.calculated_enemy=f.get(b+0x74)
                    f.put(b+0x9C,123);f.put(b+0xA0,45);f.put(b+0xB4,2)
                elif address==0x0223A7E0:result=f.battle_type
                elif address==0x0223A7F4:result=parent.party
                elif address in (0x02074640,0x0223A834):result=len(f.mons)
                elif address==0x02074644:result=parent.party+0x100+b*236
                elif address==0x0206E540:result=f.mons[(a-parent.party-0x100)//236].get(b,0)
                elif address==0x0201AA8C:
                    parent.assertEqual((a,b),(5,0x58));result=0 if f.fail_alloc else parent.exp
                elif address==0x0201AB0C:f.freed.append(a)
                elif address==0x0200E390:f.destroyed.append(a)
                elif address==0x0200E320:
                    parent.assertEqual((a,b,c),(parent.payload.symbols['EnhancedCaptureExperienceChild'],parent.exp,0))
                    result=0 if f.fail_task else parent.child
                elif address==0x02232F60:result=f.ball_active
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture(methodName='runTest');f=self.f
        f.native_ranges=[];f.setUp()
        self.work,self.ctx,self.battle,self.party,self.exp,self.child=0x02220000,0x02221000,0x02225000,0x02226000,0x02228000,0x02229000
        f.parent_calls=[];f.freed=[];f.destroyed=[];f.battle_type=0;f.mons=[{5:152,76:0,163:20}]
        f.fail_alloc=f.fail_task=f.ball_active=False
        f.put(self.work,self.battle);f.put(self.work+4,self.ctx);f.put(self.work+8,0x02229100)
        f.put(self.ctx+0x178,self.work);f.put(self.ctx+0x74,0);f.put(self.ctx+0x9C,999);f.put(self.ctx+0xA0,777)
        f.put(self.ctx+0xA4,1);f.put(self.ctx+0xA8,1);f.put(self.ctx+0xB4,37)
        self.state=self.payload.symbols['gCaptureExperience']
        f.execute('EnhancedCaptureTask',0x02229200,self.work)
        f.parent_calls.clear();f.put(self.work+0x28,10);f.put(self.work+0x34,1)
    def test_parent_waits_for_separate_native_exp_and_restores_context(self):
        f=self.f;f.execute('EnhancedCaptureTask',0x02229200,self.work)
        self.assertEqual(f.calculated_enemy,1);self.assertEqual(f.parent_calls,[])
        self.assertEqual(f.get(self.ctx+0x178),self.exp);self.assertEqual(f.get(self.ctx+0xB4),37)
        f.execute('EnhancedCaptureTask',0x02229200,self.work);self.assertEqual(f.parent_calls,[])
        f.execute('EnhancedCaptureExperienceChild',self.child,self.exp)
        f.execute('EnhancedCaptureExperienceChild',self.child,self.exp)
        self.assertEqual(f.get(self.state+40),1);self.assertEqual(f.freed,[self.exp]);self.assertEqual(f.destroyed,[self.child])
        self.assertEqual(f.get(self.ctx+0x178),self.work)
        self.assertEqual([f.get(self.ctx+n) for n in (0x74,0x9C,0xA0,0xA4,0xA8,0xB4)],[0,999,777,1,1,37])
        f.execute('EnhancedCaptureTask',0x02229200,self.work)
        self.assertEqual(f.parent_calls,[(0x02229200,self.work)]);self.assertEqual(f.get(self.state+36),1)
    def test_special_battles_disabled_eggs_fainted_and_missing_participants_skip(self):
        for typ in [1,4,8,16,32,64,128,512,1024,2048,4096,8192]:
            self.setUp();self.f.battle_type=typ;self.f.execute('EnhancedCaptureTask',1,self.work)
            self.assertEqual(self.f.get(self.state+36),0);self.assertEqual(len(self.f.parent_calls),1)
        for change in ['off','egg','fainted','empty','mask']:
            self.setUp();f=self.f
            if change=='off':f.put(api.PAYLOAD_BASE+24,0)
            elif change=='egg':f.mons[0][76]=1
            elif change=='fainted':f.mons[0][163]=0
            elif change=='empty':f.mons=[]
            else:f.put(self.ctx+0xA4,0)
            f.execute('EnhancedCaptureTask',1,self.work);self.assertEqual(f.get(self.state+36),0)
    def test_failed_alloc_or_task_creation_preserves_capture(self):
        for fail in ['fail_alloc','fail_task']:
            self.setUp();f=self.f;setattr(f,fail,True);f.execute('EnhancedCaptureTask',1,self.work)
            self.assertEqual(f.get(self.state+44),1);self.assertEqual(f.get(self.ctx+0x178),self.work)
            self.assertEqual(f.get(self.ctx+0x74),0);self.assertEqual(len(f.parent_calls),1)
            self.assertEqual(f.freed,[self.exp] if fail=='fail_task' else [])
    def test_double_right_enemy_and_success_delay(self):
        f=self.f;f.battle_type=2;f.uc.mem_write(self.ctx+0x3108,b'\x02')
        f.put(self.work+0x34,2);f.execute('EnhancedCaptureTask',1,self.work);self.assertEqual(f.get(self.state+36),0)
        f.put(self.work+0x34,1);f.ball_active=True;f.execute('EnhancedCaptureTask',1,self.work);self.assertEqual(f.get(self.state+36),0)
        f.ball_active=False;f.execute('EnhancedCaptureTask',1,self.work);self.assertEqual(f.calculated_enemy,3)
    def test_both_native_completion_paths_destroy_only_child(self):
        for game in ['heartgold','soulsilver']:
            self.setUp();f=self.f;path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():self.skipTest('Build both local baselines first.')
            rom=api.ndspy.rom.NintendoDSRom.fromFile(path);ov=rom.loadArm9Overlays([12])[12]
            f.uc.mem_write(ov.ramAddress,bytes(ov.data));f.execute('EnhancedCaptureTask',1,self.work)
            f.native_ranges=[(0x02245898,0x022463E8)];f.mons=[]
            f.execute('EnhancedCaptureExperienceChild',self.child,self.exp)
            self.assertEqual(f.freed,[self.exp]);self.assertEqual(f.destroyed,[self.child])
            self.assertEqual(f.get(self.ctx+0x178),self.work);self.assertEqual(f.get(self.state+40),1)
    def test_both_guarded_callback_patches_preserve_other_files(self):
        from gameplay.capture import install_capture
        from gameplay.field import verify_field_files
        from gameplay.patches import PatchMismatch
        for game in ['heartgold','soulsilver']:
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():self.skipTest('Build both local baselines first.')
            original=api.ndspy.rom.NintendoDSRom.fromFile(path);patched=api.ndspy.rom.NintendoDSRom.fromFile(path)
            changes=install_capture(patched,self.payload);verify_field_files(original,patched,changes)
            self.assertEqual(changes[0].patch.address,0x0223EBE0)
            ov=original.loadArm9Overlays([12])[12];ov.data[0x02245898-ov.ramAddress]^=1
            original.files[ov.fileID]=ov.save(compress=False)
            with self.assertRaises(PatchMismatch):install_capture(original,self.payload)

"""Exercise actual compiled prompt/use hooks and native step/bag instructions."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import test_settings


@unittest.skipUnless(test_settings.AVAILABLE, 'Install native ARM test dependencies.')
class TestRepelPrompt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = test_settings.build_payload()

    def setUp(self):
        parent = self
        class Fixture(test_settings.TestSettings):
            def hook(f, uc, address, size, context):
                if any(lo <= address < hi for lo,hi in f.native_ranges):
                    return
                api = {0x0202D9C4,0x0202DB04,0x0202DB08,0x0207879C,0x020784B0,0x02078434,
                       0x02077D88,0x0200604C,0x0203FE74,0x020504F0,
                       0x021F992C,0x021F993C,0x0200BBA0,
                       0x020503D0,0x02066860,0x02066870,0x020668A0,0x02067584,0x0203BE60,
                       0x02066974,0x0206695C,0x02066980,0x02066968,0x0203B5D8}
                if address not in api:
                    return super().hook(uc,address,size,context)
                a,b,c,d = [uc.reg_read(r) for r in (test_settings.UC_ARM_REG_R0,test_settings.UC_ARM_REG_R1,test_settings.UC_ARM_REG_R2,test_settings.UC_ARM_REG_R3)]
                f.calls.append((address,a,b,c,d)); result=0
                if address==0x020503D0:result=f.save+0x100
                elif address in (0x02066860,0x02066870,0x020668A0,0x02067584):result=int(address in f.restrictions)
                elif address==0x0203BE60:result=f.menu_inhibit
                elif address==0x02066980:result=int(f.bag_unlocked)
                elif address==0x0203B5D8:result=int(f.amity)
                elif address in (0x02066974,0x0206695C,0x02066968):result=1
                elif address in (0x0202D9C4,0x021F992C): result=f.roamers
                elif address==0x0202DB04: result=f.roamers+0x65
                elif address==0x0202DB08: result=int(bytes(uc.mem_read(f.roamers+0x65,1))==b'\x00')
                elif address==0x0207879C: result=f.bag
                elif address==0x020784B0:
                    parent.assertEqual((a,c,d),(f.bag,1,11));result=int(f.quantities.get(b,0)>=c)
                elif address==0x02078434:
                    parent.assertEqual((a,c,d),(f.bag,1,11))
                    result=int(f.quantities.get(b,0)>=c)
                    if result:f.quantities[b]-=c
                elif address==0x02077D88: result={76:200,77:250,79:100}.get(a,0)
                elif address==0x0203FE74:f.fallback.append((a,b,c))
                elif address==0x020504F0:
                    parent.assertEqual((a,b),(f.field,parent.payload.symbols['EnhancedRepelPromptTask']))
                    result=0x02213200;f.put(f.field+0x10,result)
                elif address==0x021F993C:uc.mem_write(f.roamers+0x65,bytes([b]))
                elif address==0x0200BBA0:result=0x02213300
                uc.reg_write(test_settings.UC_ARM_REG_R0,result)
                uc.reg_write(test_settings.UC_ARM_REG_PC,uc.reg_read(test_settings.UC_ARM_REG_LR))
        Fixture.payload=self.payload
        self.f=Fixture(methodName='runTest');self.f.setUp()
        self.f.roamers,self.f.bag=0x02230000,0x02231000
        self.f.quantities,self.f.fallback={},[]
        self.f.native_ranges=[]
        self.f.restrictions=set();self.f.menu_inhibit=0
        self.f.bag_unlocked=True;self.f.amity=False
        self.f.reload()
        self.dialog=self.payload.symbols['gEnhancedRepelDialog']

    def begin(self,item=79,count=2):
        f=self.f;f.uc.mem_write(f.roamers+0x66,bytes([item]));f.quantities[item]=count
        f.execute('EnhancedRepelWoreOff',f.field,2022,0)
        self.assertEqual(f.get(self.dialog+24),1)
        f.execute('EnhancedRepelPromptTask',0)

    def keys(self,keys):
        self.f.put(0x021D1154,keys)
        return self.f.execute('EnhancedRepelPromptTask',0)

    def test_use_records_exact_type_but_preserves_unknown_save_byte(self):
        f=self.f
        for item,steps in ((79,100),(76,200),(77,250)):
            self.assertEqual(f.execute('EnhancedRepelGetSteps',item,2,6),steps)
            self.assertEqual(bytes(f.uc.mem_read(f.roamers+0x66,1)),bytes([item]))
        f.uc.mem_write(f.roamers+0x66,b'\x09')
        f.execute('EnhancedRepelGetSteps',79,2,6)
        self.assertEqual(bytes(f.uc.mem_read(f.roamers+0x66,1)),b'\x09')

    def test_disabled_unknown_or_missing_same_type_uses_native_message(self):
        f=self.f
        for item,enabled,quantities in ((0,1,{79:2}),(9,1,{79:2}),(79,0,{79:2}),(79,1,{77:3})):
            f.uc.mem_write(f.roamers+0x66,bytes([item]));f.put(test_settings.PAYLOAD_BASE+20,enabled);f.quantities=quantities
            f.execute('EnhancedRepelWoreOff',f.field,2022,0)
            self.assertEqual(f.get(self.dialog+24),0)
        self.assertEqual(len(f.fallback),4)

    def test_yes_uses_last_type_not_best_and_restores_original_npc_pause(self):
        self.begin();f=self.f;f.quantities[77]=5
        self.keys(1)
        self.assertEqual(f.quantities,{79:1,77:5})
        self.assertEqual(bytes(f.uc.mem_read(f.roamers+0x65,2)),b'\x64\x4f')
        self.assertEqual(f.get(self.dialog+52),1)
        self.assertEqual(self.keys(0),0)
        self.assertEqual(self.keys(2),1)
        self.assertEqual(f.get(f.objects),65)
        self.assertEqual(f.get(f.objects+0x12C),1)

    def test_super_and_max_repel_restore_native_durations(self):
        for item,steps in ((76,200),(77,250)):
            self.setUp();self.begin(item);self.keys(1)
            self.assertEqual(bytes(self.f.uc.mem_read(self.f.roamers+0x65,1)),bytes([steps]))
            self.assertEqual(self.f.quantities[item],1)

    def test_no_and_b_never_consume_or_restart_steps(self):
        for cancel in (True,False):
            self.setUp();self.begin()
            if not cancel:self.keys(0x10)
            self.assertEqual(self.keys(2 if cancel else 1),1)
            self.assertEqual(self.f.quantities[79],2)
            self.assertEqual(bytes(self.f.uc.mem_read(self.f.roamers+0x65,1)),b'\x00')
            self.assertEqual(self.f.get(self.dialog+56),1)

    def test_inventory_rechecked_at_acceptance(self):
        self.begin();self.f.quantities[79]=0;self.keys(1)
        self.assertEqual(self.f.get(self.dialog+60),1)
        self.assertEqual(bytes(self.f.uc.mem_read(self.f.roamers+0x65,1)),b'\x00')

    def test_special_area_and_locked_bag_fall_back_without_consumption(self):
        for restrictions,inhibit,allowed in (({0x02066870},0,False),({0x020668A0},0,False),
                ({0x02067584},0,False),(set(),4,False),(set(),0x90,True),
                ({0x02066860},4,True)):
            self.setUp();f=self.f;f.restrictions=restrictions;f.menu_inhibit=inhibit
            f.uc.mem_write(f.roamers+0x66,b'\x4f');f.quantities={79:2}
            f.execute('EnhancedRepelWoreOff',f.field,2022,0)
            self.assertEqual(bool(f.get(self.dialog+24)),allowed)
            self.assertEqual(len(f.fallback),int(not allowed));self.assertEqual(f.quantities,{79:2})

    def test_context_rechecked_before_accepting(self):
        self.begin();self.f.restrictions={0x02066870};self.keys(1)
        self.assertEqual(self.f.quantities,{79:2})
        self.assertEqual(self.f.get(self.dialog+60),1)
        self.assertEqual(bytes(self.f.uc.mem_read(self.f.roamers+0x65,1)),b'\x00')

    def test_both_native_normal_bag_and_tower_restrictions(self):
        for game in ('heartgold','soulsilver'):
            self.setUp();f=self.f;r=self.rom(game);f.uc.mem_write(0x02000000,bytes(r.arm9))
            f.native_ranges=[(0x0203BE60,0x0203BECA),(0x02067584,0x0206759C)]
            location=0x02233000;f.put(f.field+0x20,location);f.put(location,33)
            self.assertEqual(f.execute('EnhancedRepelCanUse',f.field),1)
            f.bag_unlocked=False
            self.assertEqual(f.execute('EnhancedRepelCanUse',f.field),0)
            f.bag_unlocked=True;f.amity=True
            self.assertEqual(f.execute('EnhancedRepelCanUse',f.field),0)
            f.amity=False;f.put(location,struct.unpack_from('<I',r.arm9,0x67598)[0])
            self.assertEqual(f.execute('EnhancedRepelCanUse',f.field),0)

    def rom(self,game):
        path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
        if not path.exists():self.skipTest('Build both local baselines first.')
        return test_settings.ndspy.rom.NintendoDSRom.fromFile(path)

    def test_both_rom_hooks_allow_only_recorded_files_and_reject_layout_change(self):
        from gameplay.field import install_field,verify_field_files
        from gameplay.repel import install_repel
        from gameplay.patches import PatchMismatch
        for game in ('heartgold','soulsilver'):
            original=self.rom(game);patched=self.rom(game)
            _,records=install_field(patched,self.payload);repel,layout=install_repel(patched,self.payload)
            self.assertEqual(len(repel),2);self.assertEqual(layout['last_type_offset'],0x66)
            verify_field_files(original,patched,records+repel)
            bad=self.rom(game);code=bytearray(bad.arm9);code[0x2D994]^=1;bad.arm9=code
            before=list(bad.files)
            with self.assertRaises(PatchMismatch):install_repel(bad,self.payload)
            self.assertEqual(bad.files,before)

    def test_native_step_decrements_and_opens_prompt_only_at_zero(self):
        from gameplay.repel import install_repel
        rom=self.rom('heartgold');install_repel(rom,self.payload);ov=rom.loadArm9Overlays([2])[2]
        self.f.uc.mem_write(ov.ramAddress,bytes(ov.data))
        self.f.native_ranges=[(0x0224BAE4,0x0224BB18)]
        self.payload.symbols['NativeRepelDecrement']=0x0224BAE5
        f=self.f;f.uc.mem_write(f.roamers+0x65,b'\x02\x4f');f.quantities[79]=2
        self.assertEqual(f.execute('NativeRepelDecrement',f.save,f.field),0)
        self.assertEqual(f.get(self.dialog+48),0)
        self.assertEqual(f.execute('NativeRepelDecrement',f.save,f.field),1)
        self.assertEqual(f.get(self.dialog+48),1)
        self.assertEqual(f.execute('NativeRepelDecrement',f.save,f.field),0)

    def test_native_bag_records_only_successful_repel_use(self):
        from gameplay.repel import install_repel
        rom=self.rom('heartgold');install_repel(rom,self.payload);ov=rom.loadArm9Overlays([15])[15]
        self.f.uc.mem_write(ov.ramAddress,bytes(ov.data));self.payload.symbols['NativeBagRepel']=0x021FBA9D
        self.f.native_ranges=[(0x021FBA9C,0x021FBAF8)]
        app=0x02232000;f=self.f
        f.execute('NativeBagRepel',app,76)
        self.assertEqual(bytes(f.uc.mem_read(f.roamers+0x65,2)),b'\xc8\x4c')
        self.assertEqual(struct.unpack('<H',f.uc.mem_read(app+0x680,2))[0],1)
        f.execute('NativeBagRepel',app,77)
        self.assertEqual(bytes(f.uc.mem_read(f.roamers+0x65,2)),b'\xc8\x4c')
        self.assertEqual(struct.unpack('<H',f.uc.mem_read(app+0x680,2))[0],0)

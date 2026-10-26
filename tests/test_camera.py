"""Native camera geometry, ownership handoff and both-ROM hook guards."""
from pathlib import Path
import struct,sys,unittest
import test_settings as api
from gameplay.camera import install_camera
from gameplay.field import verify_field_files
ROOT=Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE,'Install native ARM dependencies.')
class TestCamera(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=api.build_payload()
        cls.rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds')
    def setUp(self):
        self.allowed=True;self.flags=385;self.deleted=[];self.tasks=[];self.native=True;self.projections=[]
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,ctx):
                if address in (0x0203E13C,0x0203BE60,0x02023120,0x020504C0,0x021EAC64,0x020230F8,0x020CCBA0,0x020CC998):
                    a,b,c=[uc.reg_read(r) for r in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2)]
                    result=0
                    if address==0x0203E13C:result=int(owner.allowed)
                    elif address==0x0203BE60:result=owner.flags
                    elif address==0x020CCBA0:
                        signed=lambda x:x if x<0x80000000 else x-0x100000000
                        result=(signed(a)<<12)//signed(b)
                    elif address==0x020CC998:
                        d=uc.reg_read(api.UC_ARM_REG_R3)
                        signed=lambda x:x if x<0x80000000 else x-0x100000000
                        owner.projections.append(tuple(map(signed,(a,b,c,d))))
                    elif address==0x02023120:
                        owner.assertEqual(f.get(owner.state+8),0);owner.deleted.append(a)
                    elif address==0x020504C0:
                        owner.assertEqual(owner.params(),owner.base);owner.tasks.append((a,b,c));result=0x02213200
                    uc.reg_write(api.UC_ARM_REG_R0,result&0xffffffff);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                if address in (0x02028E9C,0x02028F84,0x0202877C,0x02028758,0x020F2BA4,0x0201A4BC,0x0201A4CC,0x02300000) or address<0x02000000:
                    return super().hook(uc,address,size,ctx)
                # Execute the original native geometry/math functions and overlay
                # deletion body. Save/profile/task/heap services remain controlled.
                if 0x02000000<=address<0x021D0000 or 0x021EAC30<=address<0x021EAC4C or address==0x02023148:return
                return super().hook(uc,address,size,ctx)
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        self.f.uc.mem_write(0x02000000,bytes(self.rom.arm9))
        self.camera=0x02231000;self.controller=0x02232000;self.state=self.payload.symbols['gCameraState'];self.extra=self.payload.symbols['gEnhancedExtraOptions']
        for off,value in ((0x24,self.camera),(0x28,self.controller),(0x44,0x02233000)):self.f.put(self.f.field+off,value)
        self.f.put(self.controller,self.camera);self.f.put(0x021D2204,self.camera)
        self.f.uc.mem_write(self.camera,struct.pack('<5i',1062,3956,5461,614400,3686400))
        self.f.put(self.camera+56,1464748);self.f.uc.mem_write(self.camera+60,struct.pack('<4H',58147,180,250,0))
        self.f.uc.mem_write(self.camera+32,struct.pack('<6i',100000,0,200000,0,4096,0))
        self.f.put(self.camera+84,0x02234000)
        self.base=self.params();self.unchanged=bytes(self.f.uc.mem_read(self.camera+32,24))+bytes(self.f.uc.mem_read(self.camera+68,36))
    def params(self):return (struct.unpack('<4H',self.f.uc.mem_read(self.camera+60,8)),self.f.get(self.camera+56))
    def execute(self,name,*args):return self.f.execute(name,*args)
    def update(self,pitch=None,zoom=None):
        if pitch is not None:self.f.put(self.extra+32,pitch)
        if zoom is not None:self.f.put(self.extra+36,zoom)
        self.execute('EnhancedCameraUpdate',self.f.field)
    def test_default_visual_camera_is_byte_identical_and_invalid_choices_do_not_apply(self):
        before=bytes(self.f.uc.mem_read(self.camera,104));self.update()
        self.assertEqual(bytes(self.f.uc.mem_read(self.camera,104)),before)
        self.assertEqual(self.f.get(self.state+36),0)
        self.update(6,1);self.update(0,4);self.assertEqual(self.params(),self.base)
    def test_all_pitches_and_zooms_execute_native_geometry_without_target_or_tracking_changes(self):
        for pitch,degrees in enumerate((None,34,37,40,43,46)):
            for zoom,percent in enumerate((90,100,110,120)):
                self.update(pitch,zoom)
                expected=self.base[0][0] if degrees is None else (-((degrees*65536+180)//360))&65535
                self.assertEqual(self.params(),((expected,*self.base[0][1:]),self.base[1]*100//percent))
                data=bytes(self.f.uc.mem_read(self.camera+32,24))+bytes(self.f.uc.mem_read(self.camera+68,36))
                self.assertEqual(data,self.unchanged)
        self.update(0,1);self.assertEqual(self.params(),self.base)
    def test_orthographic_zoom_rebuilds_native_projection_and_defers_foreign_camera_graphics(self):
        self.f.uc.mem_write(self.camera+68,b'\1')
        uc=self.f.uc
        for reg,value in ((api.UC_ARM_REG_R0,1),(api.UC_ARM_REG_R1,self.camera),(api.UC_ARM_REG_SP,0x023FF000),(api.UC_ARM_REG_LR,0x02300001)):uc.reg_write(reg,value)
        uc.emu_start(0x020233D9,0x02300000,count=200000)
        baseline=self.projections[-1]
        self.update(0,3);self.assertEqual(len(self.projections),2)
        self.assertTrue(0<self.projections[-1][0]<baseline[0])
        self.assertEqual(self.projections[-1][0],-self.projections[-1][1])
        self.assertEqual(self.projections[-1][2],-self.projections[-1][3])
        self.f.put(0x021D2204,0);self.update()
        self.assertEqual(self.params(),self.base);self.assertEqual(len(self.projections),2)
        self.assertEqual(self.f.get(self.state+56),1)
        self.f.put(self.extra+36,1);self.f.put(0x021D2204,self.camera);self.update()
        self.assertEqual(self.projections[-1],baseline);self.assertEqual(self.f.get(self.state+56),0)

    def test_repeated_idle_updates_do_not_accumulate_zoom_or_reallocate(self):
        self.update(2,3);before=self.params();count=self.f.get(self.state+40)
        for _ in range(80):self.update()
        self.assertEqual(self.params(),before);self.assertEqual(self.f.get(self.state+40),count)
        self.assertEqual(self.f.get(self.state+36),1)
    def test_native_task_constructor_receives_restored_base_before_any_script_runs(self):
        self.update(1,3);self.execute('EnhancedClockCreateTask',self.f.field,0x02123457,0x02233000)
        self.assertEqual(self.tasks,[(self.f.field,0x02123457,0x02233000)])
        self.assertEqual(self.f.get(self.f.field+0x10),0x02213200);self.assertEqual(self.f.get(self.state+36),0)
        self.f.put(self.f.field+0x10,0);self.update();self.assertEqual(self.f.get(self.state+36),1)
    def test_native_controller_busy_and_script_edits_rebase_without_overwriting_external_angles(self):
        self.update(1,3);self.f.put(self.controller+0x28,1);self.update();self.assertEqual(self.params(),self.base)
        new=(57000,900,600,0);self.f.uc.mem_write(self.camera+60,struct.pack('<4H',*new));self.f.put(self.camera+56,1700000)
        self.update();self.assertEqual(self.params(),(new,1700000))
        self.f.put(self.controller+0x28,0);self.update()
        self.assertEqual(self.params(),((59346,*new[1:]),1700000*100//120))
        self.update(0,1);self.assertEqual(self.params(),(new,1700000))
    def test_external_distance_change_restores_owned_angle_then_uses_new_native_base(self):
        self.update(5,2);self.f.put(self.camera+56,1600000);self.update()
        self.assertEqual(self.f.get(self.state+52),1);self.assertEqual(self.f.get(self.state+28),1600000)
        self.update(0,1);self.assertEqual(self.params(),(self.base[0],1600000))
    def test_field_guards_and_trainer_change_restore_owned_view(self):
        for condition in ('task','movement','inhibit','static','owner','renderer'):
            self.update(3,3)
            if condition=='task':self.f.put(self.f.field+0x10,1)
            elif condition=='movement':self.allowed=False
            elif condition=='inhibit':self.flags=4
            elif condition=='static':self.f.put(0x021D2204,0)
            elif condition=='owner':self.f.owner^=1
            else:self.f.put(self.f.field+0x44,0)
            self.update();self.assertEqual(self.params(),self.base,condition)
            self.f.put(self.f.field+0x10,0);self.allowed=True;self.flags=385;self.f.put(0x021D2204,self.camera);self.f.owner=0x12345678;self.f.put(self.f.field+0x44,0x02233000)
    def test_guarded_native_field_deletion_forgets_before_forwarding_original_delete(self):
        r=api.ndspy.rom.NintendoDSRom(self.rom.save());changes=install_camera(r,self.payload)
        import ndspy.code
        ov=ndspy.code.loadOverlayTable(r.arm9OverlayTable,lambda oid,fid:r.files[fid],{1})[1]
        self.f.uc.mem_write(0x021EAC30,bytes(ov.data[0x021EAC30-ov.ramAddress:0x021EAC4C-ov.ramAddress]))
        self.update(4,0)
        uc=self.f.uc;uc.reg_write(api.UC_ARM_REG_R0,self.f.field);uc.reg_write(api.UC_ARM_REG_SP,0x023FF000);uc.reg_write(api.UC_ARM_REG_LR,0x02300001)
        uc.emu_start(0x021EAC31,0x02300000,count=200000)
        self.assertEqual(uc.reg_read(api.UC_ARM_REG_SP),0x023FF000);self.assertEqual(self.deleted,[self.camera]);self.assertEqual(self.f.get(self.state+36),0)
    def test_both_roms_guard_native_geometry_and_only_patch_one_recorded_overlay_call(self):
        for g in ('heartgold','soulsilver'):
            original=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{g}-visual-plus-full-baseline.nds');r=api.ndspy.rom.NintendoDSRom(original.save())
            changes=install_camera(r,self.payload);self.assertEqual(len(changes),1);self.assertEqual(r.arm9,original.arm9);verify_field_files(original,r,changes)
            raw=bytearray(original.arm9);raw[0x23558]^=1;r=api.ndspy.rom.NintendoDSRom(original.save());r.arm9=bytes(raw)
            with self.assertRaises(api.PatchMismatch):install_camera(r,self.payload)

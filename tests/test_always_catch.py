"""Original native shake calculation, RNG progression and Friend Ball effects."""
from pathlib import Path
import struct,sys,math,unittest
import test_settings as api
from gameplay.cheats import install_cheats
from gameplay.field import verify_field_files
ROOT=Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE,'Install native ARM dependencies.')
class TestAlwaysCatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.payload=api.build_payload()
    def setUp(self):
        self.friendship=[];self.rate=3;self.types=[];owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,ctx):
                if address in (0x0206FBE8,0x0224EDE0,0x0223A880,0x0206EC40):
                    a,b,c=[uc.reg_read(r) for r in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2)];result=0
                    if address==0x0206FBE8:owner.assertEqual((a,b),(243,8));result=owner.rate
                    elif address==0x0224EDE0:owner.assertIn(c,(27,28));owner.types.append(c)
                    elif address==0x0223A880:owner.assertEqual((a,b,c),(owner.battle,1,0));result=owner.mon
                    else:
                        owner.assertEqual((a,b),(owner.mon,9));value=bytes(uc.mem_read(c,1))[0];owner.friendship.append(value)
                    uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                if 0x02247228<=address<0x02247668 or 0x0223BD98<=address<0x0223BDC4 or 0x0223A7E0<=address<0x0223A7E4 or 0x020F0000<=address<0x02100000:return
                return super().hook(uc,address,size,ctx)
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        self.battle,self.ctx,self.mon=0x02201000,0x02208000,0x02221000
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gAlwaysCatchState']
        self.f.uc.mem_map(0x04000000,0x10000)
        from unicorn import UC_HOOK_MEM_WRITE
        def hardware(uc,access,address,size,value,ctx):
            if address==0x040002B8:uc.mem_write(0x040002B4,struct.pack('<I',math.isqrt(value&0xffffffff)))
        self.f.uc.hook_add(UC_HOOK_MEM_WRITE,hardware)
        self.load_game('heartgold');self.prepare()
    def load_game(self,g):
        self.rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{g}-visual-plus-full-baseline.nds');self.patched=api.ndspy.rom.NintendoDSRom(self.rom.save());install_cheats(self.patched,self.payload)
        self.f.uc.mem_write(0x02000000,bytes(self.rom.arm9));ov=self.patched.loadArm9Overlays([12])[12];self.f.uc.mem_write(ov.ramAddress,bytes(ov.data))
    def prepare(self,item=497,typ=0,hp=30,status=0,seed=1):
        f=self.f;f.put(self.ctx+0x6C,1);f.put(self.ctx+0x128,item)
        f.uc.mem_write(self.ctx+0x2D40+0xC0,struct.pack('<H',243))
        f.put(self.ctx+0x2D90+0xC0,30);f.put(self.ctx+0x2D8C+0xC0,hp);f.put(self.ctx+0x2DAC+0xC0,status)
        f.put(self.battle+0x2C,typ);f.put(self.battle+0x2448,seed)
        f.uc.mem_write(self.state,bytes(20));self.friendship=[];self.types=[]
    def calculate(self):
        uc=self.f.uc;uc.reg_write(api.UC_ARM_REG_R0,self.battle);uc.reg_write(api.UC_ARM_REG_R1,self.ctx)
        uc.reg_write(api.UC_ARM_REG_SP,0x023FF000);uc.reg_write(api.UC_ARM_REG_LR,0x02300001)
        uc.emu_start(0x02247229,0x02300000,count=200000)
        self.assertEqual(uc.reg_read(api.UC_ARM_REG_PC),0x02300000);self.assertEqual(uc.reg_read(api.UC_ARM_REG_SP),0x023FF000)
        return uc.reg_read(api.UC_ARM_REG_R0)
    def test_off_and_unowned_rolls_preserve_original_native_rng_value_and_progress(self):
        for seed in (0,1,0x12345678,0xffffffff):
            for mode in ('off','unowned','not-loaded'):
                self.f.owner=0x12345678;self.f.put(self.f.state+8,1);self.prepare(seed=seed)
                self.f.put(self.extra+40,int(mode!='off'))
                if mode=='unowned':self.f.owner^=1
                elif mode=='not-loaded':self.f.put(self.f.state+8,0)
                result=self.f.execute('EnhancedCatchRoll',self.battle);next_seed=(seed*0x41C64E6D+0x6073)&0xffffffff
                self.assertEqual(result,next_seed>>16);self.assertEqual(self.f.get(self.battle+0x2448),next_seed)
                self.assertEqual(self.f.get(self.state+4),0)
    def test_all_supported_wild_flag_combinations_force_only_shake_rolls(self):
        self.f.put(self.extra+40,1);bits=[2,8,16,32,64,256,4096]
        for m in range(128):
            typ=sum(b for i,b in enumerate(bits) if m&(1<<i));self.prepare(typ=typ)
            self.assertEqual(self.f.execute('EnhancedCatchRoll',self.battle),0);self.assertEqual(self.f.get(self.state+4),1)
            for forbidden in (1,4,128,512,1024,2048,8192,0x80000000):
                self.prepare(typ=typ|forbidden)
                self.assertEqual(self.f.execute('EnhancedCatchRoll',self.battle),0x41C6)
                self.assertEqual((self.f.get(self.state+4),self.f.get(self.state+16)),(0,1))
    def test_both_original_calculators_fail_off_then_force_four_shakes_and_friendship_on(self):
        for g in ('heartgold','soulsilver'):
            self.load_game(g);self.prepare();self.f.put(self.extra+40,0)
            self.assertEqual(self.calculate(),0);self.assertEqual(self.friendship,[])
            self.assertEqual(self.f.get(self.state),1);self.assertEqual(self.f.get(self.battle+0x2448),0x41C6AEE0)
            self.prepare();self.f.put(self.extra+40,1)
            self.assertEqual(self.calculate(),4);self.assertEqual(self.friendship,[200])
            self.assertEqual((self.f.get(self.state),self.f.get(self.state+4)),(4,4))
            seed=1
            for _ in range(4):seed=(seed*0x41C64E6D+0x6073)&0xffffffff
            self.assertEqual(self.f.get(self.battle+0x2448),seed)
    def test_original_hardware_division_zero_boundary_status_and_ball_math_still_guarantee(self):
        self.f.put(self.extra+40,1)
        # Rate zero/one also exercises the original SDK's divisor-zero return,
        # rather than replacing native math with a Python catch formula.
        for rate in (0,1,3,45,255):
            self.rate=rate
            for hp in (1,15,30):
                for status in (0,7,32,64,128):
                    self.prepare(hp=hp,status=status);self.assertEqual(self.calculate(),4,(rate,hp,status))
                    self.assertEqual(self.friendship,[200])
    def test_native_immediate_success_masterball_tutorial_and_palpark_keep_original_rules(self):
        self.rate=255;self.f.put(self.extra+40,0);self.prepare(hp=1,status=7)
        self.assertEqual(self.calculate(),4);self.assertEqual(self.friendship,[200]);self.assertEqual(self.f.get(self.state),0)
        self.rate=3
        for typ in (512,1024):
            self.prepare(typ=typ);self.f.put(self.extra+40,1)
            self.assertEqual(self.calculate(),4);self.assertEqual(self.f.get(self.state),0);self.assertEqual(self.friendship,[])
        self.prepare(item=1);self.f.put(self.extra+40,0)
        self.assertEqual(self.calculate(),4);self.assertEqual(self.friendship,[])
    def test_excluded_trainer_link_frontier_and_unknown_paths_retain_native_failed_roll(self):
        self.f.put(self.extra+40,1)
        for typ in (1,4,128,2048,8192,0x80000000):
            self.prepare(typ=typ);self.assertEqual(self.calculate(),0)
            self.assertEqual(self.friendship,[]);self.assertEqual(self.f.get(self.state+4),0)
    def test_both_guarded_installations_only_change_one_native_roll_call_and_reject_mutation(self):
        for g in ('heartgold','soulsilver'):
            self.load_game(g);r=api.ndspy.rom.NintendoDSRom(self.rom.save());changes=install_cheats(r,self.payload)
            self.assertEqual(len(changes),1);self.assertEqual(r.arm9,self.rom.arm9);verify_field_files(self.rom,r,changes)
            # Native trainer deflection and caller state machine stay identical.
            a=self.rom.loadArm9Overlays([12])[12];b=r.loadArm9Overlays([12])[12]
            for start,end in ((0x022466FC,0x02246740),(0x0223BD98,0x0223BDC4)):
                self.assertEqual(a.data[start-a.ramAddress:end-a.ramAddress],b.data[start-b.ramAddress:end-b.ramAddress])
            bad=bytearray(a.data);bad[0x02247602-a.ramAddress]^=1;r.files[a.fileID]=bytes(bad)
            with self.assertRaises(api.PatchMismatch):install_cheats(r,self.payload)

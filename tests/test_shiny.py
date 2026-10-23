"""Execute shiny selection and actual native creation callers with guarded hooks."""
from pathlib import Path
import struct,sys,unittest
import test_settings as api
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from gameplay.shiny import install_shiny
from gameplay.field import thumb_call

def shiny(pid,owner):return ((pid&65535)^(pid>>16)^(owner&65535)^(owner>>16))<8
def letter(pid):return (((pid>>18)&192)|((pid>>12)&48)|((pid>>6)&12)|(pid&3))%28
def gender(pid,ratio):return 0 if ratio==0 else 1 if ratio==254 else 2 if ratio==255 else int((pid&255)<ratio)

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestShiny(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=api.build_payload();cls.roms=[]
        for game in ('heartgold','soulsilver'):
            p=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not p.exists():raise unittest.SkipTest('Build both local baselines first.')
            cls.roms.append(api.ndspy.rom.NintendoDSRom(p.read_bytes()))
    def setUp(self):
        self.randoms=None;self.seed=0x12345678;self.rng_calls=0;self.ratio=127;self.created=[]
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,ctx):
                if 0x0206FE2C<=address<0x0206FE3A or 0x0206E108<=address<0x0206E21C:return
                a,b,c,d=[uc.reg_read(r) for r in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                if address==0x020F2BA4:
                    uc.reg_write(api.UC_ARM_REG_R0,a//b);uc.reg_write(api.UC_ARM_REG_R1,a%b)
                    uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                if address==0x0201FD44:
                    owner.rng_calls+=1
                    if owner.randoms is not None:
                        owner.assertTrue(owner.randoms,'Unexpected extra random draw.');result=owner.randoms.pop(0)
                    else:owner.seed=(owner.seed*0x41C64E6D+0x6073)&0xFFFFFFFF;result=owner.seed>>16
                elif address==0x0206FBE8:
                    owner.assertEqual(b,18);result=owner.ratio
                elif address==0x0206DE38:
                    sp=uc.reg_read(api.UC_ARM_REG_SP)
                    owner.created.append((a,b,c,d,*struct.unpack('<4I',uc.mem_read(sp,16))));result=0
                else:return super().hook(uc,address,size,ctx)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gShinyState']
        rom=api.ndspy.rom.NintendoDSRom(self.roms[0].save());install_shiny(rom,self.payload)
        self.f.uc.mem_write(0x0206FE2C,bytes(rom.arm9[0x6FE2C:0x6FE3A]))
        self.f.uc.mem_write(0x0206E108,bytes(rom.arm9[0x6E108:0x6E21C]))
    def execute(self,symbol,*args):
        f=self.f
        for r,v in zip((api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3),(*args,0,0,0,0)):f.uc.reg_write(r,v)
        f.uc.mem_write(0x023FF000,struct.pack('<8I',*args[4:],*([0]*(8-len(args[4:])))))
        f.uc.reg_write(api.UC_ARM_REG_SP,0x023FF000);f.uc.reg_write(api.UC_ARM_REG_LR,0x02300001)
        address=self.payload.symbols[symbol] if isinstance(symbol,str) else symbol
        f.uc.emu_start(address,0x02300000,count=5000000)
        self.assertEqual(f.uc.reg_read(api.UC_ARM_REG_PC),0x02300000)
        self.assertEqual(f.uc.reg_read(api.UC_ARM_REG_SP),0x023FF000)
        return f.uc.reg_read(api.UC_ARM_REG_R0)
    def test_normal_invalid_and_already_shiny_keep_pid_without_extra_rng(self):
        original=12345
        for setting in (0,6,0xFFFFFFFF):
            self.f.put(self.extra+16,setting)
            self.assertEqual(self.execute('EnhancedShinySelect',original,self.f.owner,163,1),original)
        self.f.put(self.extra+16,5);pid=(self.f.owner&65535)^((self.f.owner>>16)&65535)
        self.assertTrue(shiny(pid,self.f.owner))
        self.assertEqual(self.execute('EnhancedShinySelect',pid,self.f.owner,163,1),pid)
        self.assertEqual(self.rng_calls,0)
    def test_each_boost_has_exact_roll_budget_and_stops_on_first_shiny(self):
        for setting,rolls in ((1,2),(2,8),(3,32),(4,128)):
            self.f.put(self.extra+16,setting);self.f.put(self.state+4,0);self.f.put(self.state+8,0)
            self.randoms=[0x1111,0x2222]*(rolls-1)
            self.assertFalse(shiny(0x22221111,self.f.owner))
            result=self.execute('EnhancedShinySelect',12345,self.f.owner,163,0)
            self.assertEqual(result,0x22221111);self.assertEqual(self.randoms,[])
            self.assertEqual(self.f.get(self.state+4),rolls);self.assertEqual(self.f.get(self.state+8),rolls-1)
        self.f.put(self.extra+16,4);self.f.put(self.state+4,0)
        lo=37;hi=lo^(self.f.owner&65535)^(self.f.owner>>16)
        self.randoms=[0x1111,0x2222,lo,hi]
        self.assertTrue(shiny(self.execute('EnhancedShinySelect',12345,self.f.owner,163,0),self.f.owner))
        self.assertEqual(self.f.get(self.state+4),3);self.assertEqual(self.randoms,[])
    def test_boosted_nature_and_gender_constraints_use_real_native_nature_accessor(self):
        self.f.put(self.extra+16,4)
        for kind,ratio in ((1,127),(2,31),(2,127),(2,191),(2,0),(2,254),(2,255)):
            self.ratio=ratio;original=0x12345679
            result=self.execute('EnhancedShinySelect',original,self.f.owner,163,kind)
            self.assertEqual(result%25,original%25)
            if kind==2:self.assertEqual(gender(result,ratio),gender(original,ratio))
    def test_always_is_shiny_and_keeps_every_nature_and_gender_class(self):
        self.f.put(self.extra+16,5)
        for nature in range(25):
            original=1000000+nature;self.assertEqual(original%25,nature)
            result=self.execute('EnhancedShinySelect',original,self.f.owner,163,1)
            self.assertTrue(shiny(result,self.f.owner));self.assertEqual(result%25,nature)
        for ratio in (0,1,31,63,127,191,254,255):
            for original in (0x12340000,0x123400FF):
                self.ratio=ratio;result=self.execute('EnhancedShinySelect',original,self.f.owner,163,2)
                self.assertTrue(shiny(result,self.f.owner));self.assertEqual(result%25,original%25)
                self.assertEqual(gender(result,ratio),gender(original,ratio))
        self.assertEqual(self.f.get(self.state+16),0)
    def test_always_preserves_all_unown_letters_and_terminates_with_stuck_rng(self):
        self.f.put(self.extra+16,5);self.ratio=255
        for form in range(28):
            original=((form&48)<<12)|((form&12)<<6)|(form&3)
            if shiny(original,self.f.owner):original^=1<<20
            self.assertEqual(letter(original),form)
            self.randoms=[0,0]
            result=self.execute('EnhancedShinySelect',original,self.f.owner,201,2)
            self.assertTrue(shiny(result,self.f.owner));self.assertEqual(result%25,original%25)
            self.assertEqual(letter(result),form);self.assertEqual(self.randoms,[])
        self.assertEqual(self.f.get(self.state+16),0)
    def test_wrappers_initialize_once_forward_all_arguments_and_do_not_edit_existing_memory(self):
        mon=0x02230000;before=bytes(range(236));self.f.uc.mem_write(mon,before)
        self.f.put(self.extra+16,5)
        for name,fixed,pid in (('EnhancedPlayerCreateMon',0,0),('EnhancedNatureCreateMon',1,12345),('EnhancedGenderCreateMon',1,12345)):
            self.created=[];self.execute(name,mon,163,7,32,fixed,pid,0,0)
            self.assertEqual(len(self.created),1);args=self.created[0]
            self.assertEqual(args[:5],(mon,163,7,32,1));self.assertEqual(args[6:],(0,0))
            self.assertTrue(shiny(args[5],self.f.owner))
            if name!='EnhancedPlayerCreateMon':self.assertEqual(args[5]%25,pid%25)
            self.assertEqual(bytes(self.f.uc.mem_read(mon,236)),before)
    def test_default_fixed_trainer_preset_and_invalid_owner_forward_original_identity(self):
        mon=0x02230000
        for setting,fixed,ot in ((0,0,0),(6,0,0),(5,1,0),(5,0,1),(5,0,2)):
            self.f.put(self.extra+16,setting);self.created=[]
            self.execute('EnhancedPlayerCreateMon',mon,163,7,32,fixed,12345,ot,9876)
            self.assertEqual(self.created,[(mon,163,7,32,fixed,12345,ot,9876)])
        self.f.put(self.extra+16,5);self.f.put(self.f.state+4,self.f.owner^1)
        self.execute('EnhancedNatureCreateMon',mon,163,7,32,1,12345,0,0)
        self.assertEqual(self.created[-1][5],12345)
        self.f.put(self.f.state+8,0)
        self.execute('EnhancedPlayerCreateMon',mon,163,7,32,0,12345,0,0)
        self.assertEqual(self.created[-1][4:6],(0,12345));self.assertEqual(self.rng_calls,0)
    def test_actual_native_nature_and_cute_charm_callers_reach_wrapper_once(self):
        for original in self.roms:
            rom=api.ndspy.rom.NintendoDSRom(original.save());install_shiny(rom,self.payload)
            self.f.uc.mem_write(0x0206E108,bytes(rom.arm9[0x6E108:0x6E21C]))
            for setting in (0,5):
                self.f.put(self.extra+16,setting);self.created=[];self.randoms=[1,0] if setting==0 else [1,0,0,0]
                self.execute(0x0206E109,0x02230000,163,7,32,1)
                self.assertEqual(len(self.created),1);pid=self.created[0][5]
                self.assertEqual(pid%25,1)
                self.assertEqual(shiny(pid,self.f.owner),setting==5);self.assertEqual(self.randoms,[])
            self.created=[];self.ratio=127;self.f.put(self.extra+16,5);self.randoms=[0,0]
            self.execute(0x0206E14D,0x02230000,163,7,32,1,13,0)
            pid=self.created[0][5];self.assertTrue(shiny(pid,self.f.owner));self.assertEqual(pid%25,13)
            self.assertEqual(gender(pid,127),1);self.assertEqual(len(self.created),1)
    def test_only_four_audited_creation_calls_change_and_native_checks_and_other_callers_stay(self):
        wanted={0x02054216,0x020960E6,0x0206E142,0x0206E1E4}
        for original in self.roms:
            rom=api.ndspy.rom.NintendoDSRom(original.save());changes=install_shiny(rom,self.payload)
            self.assertEqual({c.address for c in changes},wanted)
            for offset in range(0,len(original.arm9)-4,2):
                at=0x02000000+offset
                if at not in wanted and original.arm9[offset:offset+4]==thumb_call(at,0x0206DE39):
                    self.assertEqual(rom.arm9[offset:offset+4],original.arm9[offset:offset+4])
            for at,size in ((0x0206DE38,0x2D0),(0x0207003C,0x50)):
                self.assertEqual(rom.arm9[at-0x02000000:at-0x02000000+size],original.arm9[at-0x02000000:at-0x02000000+size])
            damaged=api.ndspy.rom.NintendoDSRom(original.save());data=bytearray(damaged.arm9);data[0x6E108]^=1;damaged.arm9=bytes(data)
            with self.assertRaises(ValueError):install_shiny(damaged,self.payload)

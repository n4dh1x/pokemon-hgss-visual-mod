"""Execute native HM user checks and guard both USA patch sites."""
from pathlib import Path
import struct,sys,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import test_settings as api

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestFieldHms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.payload=api.build_payload()
    def setUp(self):
        import ndspy.narc
        parent=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if address==0x0207224C:f.compat.append(uc.reg_read(api.UC_ARM_REG_R1))
                if any(lo<=address<hi for lo,hi in f.native_ranges):return
                if address not in {0x02040374,0x020403AC,0x02074904,0x02074640,
                                   0x02074644,0x0206E540,0x0206E640,0x0206FBC4}:
                    return super().hook(uc,address,size,context)
                a,b,c=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2)]
                result=0
                if address==0x02040374:
                    parent.assertEqual((a,b),(f.field,0x800C));result=parent.result
                elif address==0x020403AC:result=f.variables.get(b,b)
                elif address==0x02074904:parent.assertEqual(a,f.save);result=parent.party
                elif address==0x02074640:result=len(f.mons)
                elif address==0x02074644:result=parent.party+0x100+b*236
                elif address in (0x0206E540,0x0206E640):
                    mon=f.mons[(a-parent.party-0x100)//236]
                    result=(494 if mon.get(76,0) else mon.get(5,0)) if b==174 else mon.get(b,0)
                elif address==0x0206FBC4:
                    parent.assertEqual(b,0);parent.assertIn(c,range(29,33))
                    result=struct.unpack_from('<I',f.personal[a],28+(c-29)*4)[0]
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture(methodName='runTest');f=self.f;f.setUp()
        path=ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds'
        if not path.exists():self.skipTest('Build local USA baselines first.')
        self.rom=api.ndspy.rom.NintendoDSRom.fromFile(path);f.uc.mem_write(self.rom.arm9RamAddress,bytes(self.rom.arm9))
        f.personal=ndspy.narc.NARC(self.rom.files[self.rom.filenames.idOf('a/0/0/2')]).files
        f.native_ranges=[(0x020542E8,0x02054358),(0x0204D3CC,0x0204D48C),
                         (0x0203FE2C,0x0203FE44),(0x0207224C,0x020722D4)]
        self.ctx,self.program,self.result,self.party=0x02220000,0x02221000,0x02222000,0x02228000
        f.put(self.ctx+0x80,f.field);f.mons=[{5:129},{5:151}];f.variables={};f.compat=[]
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];f.put(self.extra,1)
    def command(self,move,symbol='EnhancedPartySlotWithMove'):
        f=self.f;f.put(self.ctx+8,self.program);f.put(self.result,0xABCD0006)
        f.uc.mem_write(self.program,struct.pack('<HH',0x800C,move))
        self.assertEqual(f.execute(symbol,self.ctx),0)
        self.assertEqual(f.get(self.ctx+8),self.program+4)
        self.assertEqual(f.get(self.result)>>16,0xABCD)
        return f.get(self.result)&0xFFFF
    def test_all_eight_native_hm_compatibility_indices_prefer_real_compatible_species(self):
        # Original compatibility instructions read actual, unchanged personal
        # data from the local ROM. Magikarp has no HMs; Mew has all eight.
        for move,index in ((15,92),(19,93),(57,94),(70,95),(250,96),(249,97),(127,98),(431,99)):
            self.f.compat=[];self.assertEqual(self.command(move),1)
            self.assertEqual(self.f.compat,[index,index])
    def test_known_user_kept_before_fallback_and_non_hm_moves_are_native(self):
        f=self.f;f.mons=[{5:129,54:15},{5:151}]
        self.assertEqual(self.command(15),0);self.assertEqual(f.compat,[])
        for move in (148,100,91,29,57):
            f.mons=[{5:129,54:move},{5:151}]
            self.assertEqual(self.command(move),0)
        for move in (148,100,91,29):
            f.mons=[{5:129},{5:151}];self.assertEqual(self.command(move),6)
    def test_first_non_egg_fallback_eggs_empty_and_fainted_behavior(self):
        f=self.f;f.mons=[{5:151,76:1},{5:129,163:0}]
        self.assertEqual(self.command(15),1,'Field HM users may be fainted, as in native field use.')
        f.mons=[{5:151,76:1}];self.assertEqual(self.command(15),6)
        f.mons=[];self.assertEqual(self.command(15),6)
        f.mons=[{5:0},{5:129}];self.assertEqual(self.command(15),1)
    def test_disabled_executes_original_command_and_resolves_variable_move_operand(self):
        f=self.f;f.put(self.extra,0);f.mons=[{5:129},{5:151,55:57}]
        f.variables[0x4000]=57;self.assertEqual(self.command(0x4000),1)
        self.assertEqual(self.command(15),6);self.assertEqual(f.compat,[])
        f.put(self.extra,1);self.assertEqual(self.command(0x4000),1)
    def test_both_original_usa_command_paths_and_output_conventions(self):
        for game in ('heartgold','soulsilver'):
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():self.skipTest('Build both local USA baselines first.')
            rom=api.ndspy.rom.NintendoDSRom.fromFile(path);self.f.uc.mem_write(rom.arm9RamAddress,bytes(rom.arm9))
            self.f.personal=api.ndspy.narc.NARC(rom.files[rom.filenames.idOf('a/0/0/2')]).files
            self.f.uc.mem_write(api.PAYLOAD_BASE,self.payload.data)
            for enabled in (0,1):
                self.f.put(self.extra,enabled)
                self.f.mons=[{5:129},{5:151}]
                self.assertEqual(self.command(15),1 if enabled else 6)
    def test_bag_flash_uses_real_tm70_compatibility_without_changing_contextual_flash(self):
        f=self.f
        self.assertEqual(f.execute('EnhancedBagFieldUser',self.party,148),1)
        self.assertEqual(f.compat,[69,69])
        self.assertEqual(f.execute('EnhancedFirstPartyMove',self.party,148),255)
        f.put(self.extra,0)
        self.assertEqual(f.execute('EnhancedBagFieldUser',self.party,148),255)

    def test_direct_surf_waterfall_helper_preserves_native_255_convention(self):
        f=self.f
        self.assertEqual(f.execute('EnhancedFirstPartyMove',self.party,57),1)
        f.put(self.extra,0);self.assertEqual(f.execute('EnhancedFirstPartyMove',self.party,57),255)
        f.put(self.extra,1);f.mons=[{5:151,76:1}]
        self.assertEqual(f.execute('EnhancedFirstPartyMove',self.party,127),255)
    def test_repeated_field_checks_cache_compatibility_but_not_current_party_or_moves(self):
        f=self.f;self.assertEqual(self.command(15),1);self.assertEqual(len(f.compat),2)
        f.compat=[]
        for _ in range(20):self.assertEqual(self.command(15),1)
        self.assertEqual(f.compat,[])
        f.mons[1][5]=129
        self.assertEqual(self.command(15),0,'A species change must not reuse a cached party slot.')
        f.mons[0][76]=1;self.assertEqual(self.command(15),1)
        f.mons[0][76]=0;f.mons[0][54]=15
        self.assertEqual(self.command(15),0,'Real learned moves must still take priority.')

    def test_both_guarded_installations_keep_all_unrecorded_components_unchanged(self):
        from gameplay.field_hms import install_field_hms
        from gameplay.field import install_field,verify_field_files
        from gameplay.native import verify_arm9_changes
        from gameplay.patches import PatchMismatch
        for game in ('heartgold','soulsilver'):
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():self.skipTest('Build both local USA baselines first.')
            original=api.ndspy.rom.NintendoDSRom.fromFile(path);patched=api.ndspy.rom.NintendoDSRom.fromFile(path)
            main,overlays=install_field(patched,self.payload)
            hm_main,hm_overlays=install_field_hms(patched,self.payload)
            verify_field_files(original,patched,overlays+hm_overlays)
            self.assertEqual(hm_main[0].address,0x020FAF34)
            self.assertEqual([r.patch.address for r in hm_overlays],[0x021E6BBE,0x021E7544])
            bad=api.ndspy.rom.NintendoDSRom.fromFile(path);data=bytearray(bad.arm9);data[0x4D3CC]^=1;bad.arm9=bytes(data)
            with self.assertRaises(PatchMismatch):install_field_hms(bad,self.payload)

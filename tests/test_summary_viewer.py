"""Read real native Pokemon data and exercise the optional summary views."""
from pathlib import Path
import struct,sys,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import test_settings as api

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestSummaryViewer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.payload=api.build_payload()
    def setUp(self):
        run=ROOT/'local_data/verification/hg14a-summary-native'
        if not (run/'main-ram.bin').exists():self.skipTest('Local native summary checkpoint required.')
        self.ram=(run/'main-ram.bin').read_bytes()
        pattern=struct.pack('<7H',14,22,9,12,13,13,11)
        candidates=[];at=0
        while (at:=self.ram.find(pattern,at))>=0:
            if at>=0x254 and self.ram[at-0x254+0x7BC]==1:candidates.append(0x2000000+at-0x254)
            at+=1
        self.assertEqual(len(candidates),1);self.summary=candidates[0]
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if address==0x02300000:uc.emu_stop();return
                if address not in owner.apis:return
                a,b,c,d=[uc.reg_read(r) for r in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                owner.calls.append((address,a,b,c,d));result=0
                if address==0x02088B40:result=owner.native_result
                elif address==0x0208C87C:owner.numbers.append((b,c,d))
                elif address==0x0208C778:owner.prints.append((b,c,d))
                elif address==0x020269A0:
                    codes=[]
                    for i in range(64):
                        v=struct.unpack('<H',uc.mem_read(b+2*i,2))[0]
                        if v==0xFFFF:break
                        codes.append(v)
                    owner.texts.append(codes)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        self.apis={0x02088B40,0x0208D178,0x0208C87C,0x0208C778,0x020269A0,0x0201D978,0x0201D578,0x0200604C}
        Fixture.payload=self.payload;self.f=Fixture('runTest');f=self.f;f.setUp()
        f.uc.mem_write(0x2000000,self.ram)
        self.calls=[];self.numbers=[];self.prints=[];self.texts=[];self.native_result=2
        self.base=f.get(self.summary+0x22C);self.windows=f.get(self.summary+0x224)
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gSummaryViewState']
        f.put(self.extra+8,1);f.put(0x021D1154,0);f.put(0x021D1158,0)
        f.uc.mem_write(0x021D1170,bytes(2))
        self.mon=f.execute('NativeSummaryMon',self.summary)
        self.mon_before=bytes(f.uc.mem_read(self.mon,236));self.cache_before=bytes(f.uc.mem_read(self.summary+0x230,0x64))
        self.expected={}
        for mode,start in ((1,13),(2,70)):
            self.expected[mode]=[f.execute('GetMonData',self.mon,start+i,0) for i in (0,1,2,4,5,3)]
    def input(self,key,repeat=0):
        self.f.put(0x021D1154,key);self.f.put(0x021D1158,repeat)
        return self.f.execute('EnhancedSummaryInput',self.summary)
    def count(self,address):return len([c for c in self.calls if c[0]==address])
    def test_native_party_raw_and_pc_box_access_reads_exact_values_without_mutation(self):
        f=self.f;out=0x02390000
        for type in (1,0,2):
            clone=0x02380000
            f.uc.mem_write(clone,self.mon_before[:136] if type==2 else self.mon_before)
            f.uc.mem_write(self.base+0x11,bytes([type]));f.uc.mem_write(self.base+0x14,b'\0')
            f.put(self.base,self.f.get(self.base) if type==1 else clone)
            for mode in (1,2):
                self.assertEqual(f.execute('EnhancedSummaryReadValues',self.summary,mode,out),1)
                self.assertEqual(list(struct.unpack('<6I',f.uc.mem_read(out,24))),self.expected[mode])
            self.assertEqual(bytes(f.uc.mem_read(clone,136 if type==2 else 236)),self.mon_before[:136] if type==2 else self.mon_before)
        self.assertEqual(bytes(f.uc.mem_read(self.mon,236)),self.mon_before)
        self.assertEqual(bytes(f.uc.mem_read(self.summary+0x230,0x64)),self.cache_before)
    def test_invalid_view_or_native_source_type_is_rejected_before_reading(self):
        f=self.f;out=0x02390000;before=b'\xAB'*24;f.uc.mem_write(out,before)
        for mode in (0,3,0xFFFFFFFF):self.assertEqual(f.execute('EnhancedSummaryReadValues',self.summary,mode,out),0)
        f.uc.mem_write(self.base+0x11,b'\x03')
        self.assertEqual(f.execute('EnhancedSummaryReadValues',self.summary,1,out),0)
        self.assertEqual(bytes(f.uc.mem_read(out,24)),before)
    def test_l_evs_r_ivs_draw_correct_native_numbers_and_two_letter_label(self):
        f=self.f
        for key,mode,chars in ((0x200,1,[303,320]),(0x100,2,[307,320])):
            # HGSS font codes: E=303, I=307, V=320.
            self.numbers=[];self.texts=[];self.prints=[]
            self.assertEqual(self.input(key),2);self.assertEqual(f.get(self.state+8),mode)
            self.assertEqual([n[1] for n in self.numbers],self.expected[mode])
            self.assertTrue(all(n[0]==119 and n[2]==3 for n in self.numbers))
            self.assertEqual(self.texts[0],chars);self.assertIn(0xE000,self.texts[1])
            self.assertEqual([p[0] for p in self.prints[:6]],[self.windows+i*16 for i in range(6)])
            self.assertEqual([p[2] for p in self.prints[:6]],[2,1,1,1,1,1])
        self.assertEqual(bytes(f.uc.mem_read(self.mon,236)),self.mon_before)
        self.assertEqual(bytes(f.uc.mem_read(self.summary+0x230,0x64)),self.cache_before)
    def test_y_cycles_every_view_and_keeps_native_mapped_a_action_available(self):
        f=self.f;f.put(0x021D1140,3)  # Native L=A input mode.
        for mode in (2,1,0):
            self.assertEqual(self.input(0x800),2);self.assertEqual(f.get(self.state+8),mode)
        before=self.count(0x02088B40);self.native_result=3
        f.put(0x021D1148,0x200)  # Physical L is mapped to A by the native reader.
        self.assertEqual(self.input(1),3);self.assertEqual(self.count(0x02088B40),before+1)
        self.assertEqual(f.get(self.state+8),0)
        self.assertEqual(bytes(f.uc.mem_read(self.mon,236)),self.mon_before)

    def test_select_restores_original_draw_and_hp_label_without_editing_data(self):
        self.input(0x100);self.texts=[];before=self.count(0x0208D178)
        self.assertEqual(self.input(4),2);self.assertEqual(self.f.get(self.state+8),0)
        self.assertEqual(self.count(0x0208D178),before+1);self.assertEqual(self.texts[-1],[306,314])
        self.assertEqual(bytes(self.f.uc.mem_read(self.mon,236)),self.mon_before)
    def test_disabled_other_pages_and_native_closing_modes_preserve_original_input(self):
        f=self.f;f.put(self.extra+8,0)
        self.assertEqual(self.input(0x100),2);self.assertEqual(self.numbers,[]);self.assertEqual(self.count(0x02088B40),1)
        f.put(self.extra+8,1)
        for offset,value in ((0x7BC,0),(0x7BF,16)):
            f.uc.mem_write(self.summary+0x7BC,b'\x01');f.uc.mem_write(self.summary+0x7BF,b'\0')
            f.uc.mem_write(self.summary+offset,bytes([value]));self.assertEqual(self.input(0x200),2)
        self.assertEqual(self.numbers,[])
    def test_navigation_and_modal_keys_take_priority_and_restore_normal_stats(self):
        self.input(0x200);before=self.count(0x0208D178);self.native_result=19
        self.assertEqual(self.input(0x100,0x20),19);self.assertEqual(self.f.get(self.state+8),0)
        self.assertEqual(self.count(0x0208D178),before+1)
        self.native_result=2;self.input(0x100);before=self.count(0x0208D178)
        self.assertEqual(self.input(2),2);self.assertEqual(self.count(0x0208D178),before+1)
    def test_touch_navigation_restores_normal_stats_before_original_input(self):
        f=self.f;self.input(0x100);before=self.count(0x0208D178)
        f.uc.mem_write(0x021D1170,b'\x01\x00');self.native_result=19
        self.assertEqual(self.input(0),19);self.assertEqual(f.get(self.state+8),0)
        self.assertEqual(self.count(0x0208D178),before+1);self.assertEqual(self.texts[-1],[306,314])
        f.uc.mem_write(self.base+0x14,b'\x01');self.texts=[]
        f.execute('EnhancedSummaryDraw',self.summary)
        self.assertEqual(self.texts[-1],[306,314],'Every native refresh must replace a prior custom label.')
    def test_pokemon_change_and_page_refresh_reset_the_view(self):
        f=self.f;self.input(0x200)
        f.uc.mem_write(self.base+0x14,b'\x01');self.input(0)
        self.assertEqual(f.get(self.state+8),0);self.assertNotEqual(f.get(self.state+4),self.mon)
        self.input(0x100);self.assertEqual(f.get(self.state+8),2)
        f.execute('EnhancedSummaryDraw',self.summary);self.assertEqual(f.get(self.state+8),0)
    def test_guarded_hooks_and_recorded_arm_changes_for_both_roms(self):
        from gameplay.summary_viewer import install_summary_viewer
        from gameplay.native import inject_evolution,verify_arm9_changes
        from gameplay.patches import PatchMismatch
        for game in ('heartgold','soulsilver'):
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            original=api.ndspy.rom.NintendoDSRom.fromFile(path);patched=api.ndspy.rom.NintendoDSRom.fromFile(path)
            changes=install_summary_viewer(patched,self.payload);self.assertEqual([c.address for c in changes],[0x02088494,0x0208CC5A])
            injection=inject_evolution(patched.arm9,patched.arm9RamAddress,self.payload)
            verify_arm9_changes(original.arm9,injection.image,original.arm9RamAddress,changes+injection.changes,self.payload)
            self.assertEqual(original.files,patched.files);self.assertEqual(original.arm9OverlayTable,patched.arm9OverlayTable)
            bad=api.ndspy.rom.NintendoDSRom.fromFile(path);arm=bytearray(bad.arm9);arm[0x88B40]^=1;bad.arm9=bytes(arm)
            with self.assertRaises(PatchMismatch):install_summary_viewer(bad,self.payload)

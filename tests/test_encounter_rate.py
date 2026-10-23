"""Execute the original HGSS rate and legendary routines under the new wrapper."""
from pathlib import Path
import sys,unittest
import test_visible_field as api
ROOT=Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestNativeEncounterRate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ndspy.code
        cls.payload=api.build_payload();cls.images=[]
        for game in ('heartgold','soulsilver'):
            p=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not p.exists():raise unittest.SkipTest('Build both local baselines first.')
            rom=api.ndspy.rom.NintendoDSRom.fromFile(p)
            o=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{2})[2]
            cls.images.append((rom,o))
    def fixture(self,image):
        owner=self
        class Fixture(api.TestVisibleField):
            def hook(f,uc,address,size,ctx):
                if 0x02247568<=address<0x02247690 or 0x02248360<=address<0x02248418:return
                a=uc.reg_read(api.UC_ARM_REG_R0);b=uc.reg_read(api.UC_ARM_REG_R1)
                result=None
                if address in (0x0205C700,0x0205DE98,0x0205B6F4,0x022522B4):result=0
                elif address==0x0201FD44:
                    owner.assertTrue(owner.randoms,'Unexpected extra native RNG consumption.')
                    result=owner.randoms.pop(0)
                elif address==0x020F2998:
                    uc.reg_write(api.UC_ARM_REG_R0,a//b);uc.reg_write(api.UC_ARM_REG_R1,a%b)
                    uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                elif address==0x0202D9F8:result=b
                elif address==0x02067698:result=33 if a==0 else 0
                elif address==0x0202DA28:result=int(owner.active and b==0)
                elif address==0x0202DA54:result=f.save+0x300
                if result is None:return super().hook(uc,address,size,ctx)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;f=Fixture('runTest');f.setUp();rom,o=image
        for address,length in ((0x02247568,0x128),(0x02248360,0xB8)):
            f.uc.mem_write(address,bytes(o.data[address-o.ramAddress:address-o.ramAddress+length]))
        return f
    def test_actual_native_thresholds_for_all_multipliers_and_clamp(self):
        for image in self.images:
            for mode,rate,threshold in ((2,20,5),(3,20,10),(4,20,40),(4,200,100)):
                for roll,want in ((threshold-1,1),(threshold,0)):
                    if roll==100:continue  # Native LCRandRange(100) cannot produce 100.
                    self.active=False;f=self.fixture(image);f.put(self.payload.symbols['gEnhancedExtraOptions']+12,mode)
                    self.randoms=[99,0,roll]  # Native-rate fail, then scaled first/second rolls.
                    self.assertEqual(f.execute('EnhancedEncounterRoll',f.field,rate,2),want)
                    self.assertEqual(self.randoms,[])
                    if want:self.assertEqual(f.execute('EnhancedRoamerCheck',f.field,f.input+0x40),0)
                    self.assertEqual(bytes(f.uc.mem_read(f.mon,236)),f.native_mon)
    def test_actual_native_roamer_selection_keeps_normal_roll_and_identity_even_when_off(self):
        for image in self.images:
            self.active=True;f=self.fixture(image);f.put(self.payload.symbols['gEnhancedExtraOptions']+12,1)
            self.randoms=[0,19,1]  # Original two rate gates, original 50% legendary gate.
            self.assertEqual(f.execute('EnhancedEncounterRoll',f.field,20,2),1)
            self.assertEqual(self.randoms,[])
            out=f.input+0x40;self.assertEqual(f.execute('EnhancedRoamerCheck',f.field,out),1)
            self.assertEqual(f.get(out),f.save+0x300);self.assertEqual(self.randoms,[])
            self.active=False;self.randoms=[0,19]
            self.assertEqual(f.execute('EnhancedEncounterRoll',f.field,20,2),0)
            self.assertEqual(self.randoms,[])
    def test_both_native_routine_fingerprints_reject_changes(self):
        import ndspy.code
        for original,o in self.images:
            for address in (0x02247568,0x02248360):
                rom=api.ndspy.rom.NintendoDSRom(original.save())
                overlay=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{2})[2]
                overlay.data[address-overlay.ramAddress]^=1
                rom.files[overlay.fileID]=overlay.save(compress=False)
                with self.assertRaises(api.PatchMismatch):api.install_field(rom,self.payload)

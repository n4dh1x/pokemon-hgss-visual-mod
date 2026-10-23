"""Run the audited original native parameter/selector instructions on both ROMs."""
from pathlib import Path
import struct,unittest
import test_visible_field as api

@unittest.skipUnless(api.AVAILABLE, 'Install ARM test dependencies.')
class TestNativeFieldPalette(unittest.TestCase):
    def fixture(self, game):
        class Fixture(api.TestVisibleField):
            def hook(f, uc, address, size, context):
                if any(a <= address < b for a,b in ((0x02069EE8,0x02069F0C),
                    (0x0206A080,0x0206A0A4),(0x0206A0E0,0x0206A128),
                    (0x0206A304,0x0206A32E),(0x0205F2D0,0x0205F314),
                    (0x0220553C,0x02205564),(0x0205B994,0x0205B9A8),
                    (0x0205B778,0x0205B78C))): return
                if address == 0x02007508:
                    self.assertEqual(uc.reg_read(api.UC_ARM_REG_R1),141)
                    uc.mem_write(uc.reg_read(api.UC_ARM_REG_R0),bytes([0,1,0x23,0]))
                    uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                if address == 0x0201AB0C:
                    uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                return super().hook(uc,address,size,context)
        Fixture.payload=api.build_payload(); f=Fixture();f.setUp()
        path=api.ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
        if not path.exists(): self.skipTest('Build both local baselines first.')
        rom=api.ndspy.rom.NintendoDSRom(path.read_bytes())
        f.uc.mem_write(rom.arm9RamAddress,bytes(rom.arm9))
        import ndspy.code
        overlay=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda a,b:rom.files[b],{1})[1]
        f.uc.mem_write(0x0220553C,bytes(overlay.data[0x0220553C-overlay.ramAddress:0x02205564-overlay.ramAddress]))
        f.uc.mem_write(0x02205540,api.thumb_call(0x02205540,f.payload.symbols['EnhancedPaletteObjectId']))
        f.uc.mem_write(0x02232000,bytes([0,1,0x23,0]))
        return f

    def test_native_parameter_helper_stays_inside_scratch_and_selector_preserves_npcs(self):
        for game in ('heartgold','soulsilver'):
            with self.subTest(game=game):
                f=self.fixture(game);scratch=0x02233010
                f.payload.symbols['NativeParams']=0x02069EE9
                f.payload.symbols['NativeSelector']=0x0220553D
                for shiny in (0,1):
                    f.uc.mem_write(scratch-16,b'\xA5'*100)
                    f.put(scratch+0x38,0);f.put(scratch+0x3C,0);f.put(scratch+0x40,0)
                    before=bytes(f.uc.mem_read(scratch-16,100))
                    f.execute('NativeParams',scratch,163,0,shiny)
                    after=bytes(f.uc.mem_read(scratch-16,100))
                    self.assertEqual(before[:72],after[:72]);self.assertEqual(before[84:],after[84:])
                    self.assertEqual([f.get(scratch+x) for x in (0x38,0x3C,0x40)],[163,0x123,shiny])
                f.shiny=True;f.make_spawn()
                self.assertEqual(f.execute('NativeSelector',f.created),1)
                f.put(f.created+0x40,0)
                self.assertEqual(f.execute('NativeSelector',f.created),0)
                for npc in (0xFD,0xFA,0xFB,0xFF,42):
                    f.put(f.player+8,npc);f.put(f.player+0x40,1)
                    self.assertEqual(f.execute('NativeSelector',f.player),int(npc in (0xFD,0xFA,0xFB)))

    def test_habitat_classifier_uses_actual_native_tile_flags(self):
        for game in ('heartgold','soulsilver'):
            f=self.fixture(game)
            for tile in (2,3):self.assertEqual(f.execute('EnhancedTileHabitat',tile),1)
            for tile in (5,8,11,37):self.assertEqual(f.execute('EnhancedTileHabitat',tile),2)
            for tile in (16,18,21,42):self.assertEqual(f.execute('EnhancedTileHabitat',tile),3)
            for tile in (0,6,17,19,20,22,23,25,32,56,60,75,80,81):
                self.assertEqual(f.execute('EnhancedTileHabitat',tile),0)

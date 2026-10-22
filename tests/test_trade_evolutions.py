"""Exercise the hooked USA evolution code and native item-completion path."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import ndspy.code
    import ndspy.narc
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
    from gameplay.native import build_payload, inject_evolution, EVOLUTION_ADDRESS, PAYLOAD_BASE
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'Install requirements-dev.txt for ARM evolution tests.')
class TestTradeEvolutions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build_payload()
        cls.games = {}
        for game in ('heartgold', 'soulsilver'):
            path = ROOT / f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():
                raise unittest.SkipTest('Build both local Visual+ baselines first.')
            rom = ndspy.rom.NintendoDSRom.fromFile(path)
            injected = inject_evolution(rom.arm9, rom.arm9RamAddress, cls.payload)
            cls.games[game] = (bytes(rom.arm9), injected.image,
                               ndspy.narc.NARC(rom.getFileByName('a/0/3/4')).files)

    def execute(self, game, species, level, held=0, context=0, item=0,
                enhanced=True, enabled=True, egg=False, everstone=False,
                null_method=False, completion=False, completion_method=6):
        original, modified, tables = self.games[game]
        image = modified if enhanced else original
        emu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        emu.mem_map(0x02000000, 0x400000)
        emu.mem_map(0x01FF8000, 0x8000)
        emu.mem_map(0x027E0000, 0x4000)
        for section in ndspy.code.MainCodeFile(image, 0x02000000).sections:
            emu.mem_write(section.ramAddress, bytes(section.data))
        if enhanced:
            emu.mem_write(PAYLOAD_BASE + 8, struct.pack('<I', int(enabled)))
        mon, method_pointer, heap, task = 0x02182000, 0x02188000, 0x02190000, 0x021A0000
        stack, stop = 0x023FF000, 0x02300000
        emu.mem_write(method_pointer, struct.pack('<I', 0xF00D))
        emu.mem_write(stack, struct.pack('<I', 0 if null_method else method_pointer))
        writes = []
        current_held = held

        def hook(uc, address, size, _):
            nonlocal current_held
            if address == stop:
                uc.emu_stop()
                return
            r0, r1, r2, r3 = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            if address == 0x0206E540:  # GetMonData
                self.assertEqual(r0, mon)
                value = {0: 0x12345678, 5: species, 6: current_held, 9: 0,
                         20: 0, 76: int(egg), 112: 0, 161: level}.get(r1, 0)
                uc.reg_write(UC_ARM_REG_R0, value)
            elif address == 0x02077D88:  # GetItemAttr
                uc.reg_write(UC_ARM_REG_R0, 0x40 if everstone else 0)
            elif address == 0x0201AA8C:  # Heap_Alloc
                uc.reg_write(UC_ARM_REG_R0, heap)
            elif address == 0x020725C8:  # LoadMonEvolutionTable
                uc.mem_write(r1, bytes(tables[r0][:42]))
            elif address == 0x0201AB0C:  # Heap_Free
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif address == 0x020F2998:  # native division helper (ARM state)
                self.assertNotEqual(r1, 0)
                uc.reg_write(UC_ARM_REG_R0, r0 // r1)
                uc.reg_write(UC_ARM_REG_R1, r0 % r1)
            elif address in (0x02014804, 0x02071754):  # IsNighttime / MonHasMove
                uc.reg_write(UC_ARM_REG_R0, 0)
            elif address == 0x0206EC40:  # SetMonData (completion only)
                value = struct.unpack('<I', uc.mem_read(r2, 4))[0]
                writes.append((r0, r1, value))
                if r1 == 6:
                    current_held = value
                uc.reg_write(UC_ARM_REG_R0, 1)
            else:
                return
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        emu.hook_add(UC_HOOK_CODE, hook)
        if completion:
            emu.mem_write(task + 0x28, struct.pack('<I', mon))
            emu.mem_write(task + 0x78, struct.pack('<I', completion_method))
            arguments = (task, 0, 0, 0)
            start = 0x02076C90
        else:
            arguments = (0, mon, context, item)
            start = EVOLUTION_ADDRESS
        for register, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), arguments):
            emu.reg_write(register, value)
        emu.reg_write(UC_ARM_REG_SP, stack)
        emu.reg_write(UC_ARM_REG_LR, stop | 1)
        emu.emu_start(start | 1, stop, count=10000)
        self.assertEqual(emu.reg_read(UC_ARM_REG_PC), stop, 'Evolution routine did not return.')
        self.assertEqual(emu.reg_read(UC_ARM_REG_SP), stack, 'Evolution hook changed stack balance.')
        return (emu.reg_read(UC_ARM_REG_R0),
                struct.unpack('<I', emu.mem_read(method_pointer, 4))[0], current_held, writes)

    def trade_entries(self, game):
        tables = self.games[game][2]
        for species in range(1, 494):
            for offset in range(0, 42, 6):
                method, parameter, target = struct.unpack_from('<HHH', tables[species], offset)
                if method in (5, 6):
                    yield species, method, parameter, target

    def test_every_native_trade_evolution_has_the_level_40_alternative(self):
        for game in self.games:
            for species, method, parameter, target in self.trade_entries(game):
                held = parameter if method == 6 else 0
                for level in (39, 40, 100):
                    with self.subTest(game=game, species=species, method=method, level=level):
                        result, actual_method, retained, writes = self.execute(game, species, level, held)
                        baseline = self.execute(game, species, level, held, enhanced=False)
                        self.assertEqual(result, target if level >= 40 else baseline[0])
                        if result and level >= 40:
                            self.assertEqual(actual_method, method)
                        self.assertEqual(retained, held)
                        self.assertEqual(writes, [], 'Eligibility checks must never consume an item.')

    def test_missing_or_wrong_trade_items_preserve_native_evolutions(self):
        for game in self.games:
            for species, method, parameter, target in self.trade_entries(game):
                if method != 6:
                    continue
                valid_items = {p for s, m, p, t in self.trade_entries(game) if s == species}
                wrong = next(i for i in range(1, 1000) if i not in valid_items)
                for held in (0, wrong):
                    with self.subTest(game=game, species=species, held=held):
                        self.assertEqual(self.execute(game, species, 40, held),
                                         self.execute(game, species, 40, held, enhanced=False))

    def test_slowpoke_held_item_selects_slowking_only_from_level_40(self):
        for game in self.games:
            self.assertEqual(self.execute(game, 79, 39, 221)[0], 80)
            self.assertEqual(self.execute(game, 79, 40, 221)[0:2], (199, 6))
            self.assertEqual(self.execute(game, 79, 40, 0)[0], 80)

    def test_normal_trading_preserved_below_level_40_and_with_option_off(self):
        for game in self.games:
            for species, method, parameter, target in self.trade_entries(game):
                held = parameter if method == 6 else 0
                expected = self.execute(game, species, 1, held, context=1, enhanced=False)
                for enabled in (False, True):
                    self.assertEqual(self.execute(game, species, 1, held, context=1, enabled=enabled), expected)

    def test_option_off_does_not_add_level_evolutions(self):
        for game in self.games:
            for species, method, parameter, target in self.trade_entries(game):
                self.assertEqual(self.execute(game, species, 100, parameter, enabled=False),
                                 self.execute(game, species, 100, parameter, enhanced=False))

    def test_everstone_kadabra_exception_and_eggs(self):
        for game in self.games:
            self.assertEqual(self.execute(game, 67, 40, 1, everstone=True)[0], 0)
            self.assertEqual(self.execute(game, 64, 40, 1, everstone=True)[0], 65)
            self.assertEqual(self.execute(game, 67, 40, egg=True)[0], 0)
            self.assertEqual(self.execute(game, 67, 40, null_method=True)[0], 68)

    def test_non_trade_species_keep_native_level_evolution_behavior(self):
        for game in self.games:
            traded = {s for s, m, p, t in self.trade_entries(game)}
            for species in range(1, 494):
                if species in traded:
                    continue
                with self.subTest(game=game, species=species):
                    self.assertEqual(self.execute(game, species, 40),
                                     self.execute(game, species, 40, enhanced=False))

    def test_stone_item_argument_survives_hook_and_trampoline(self):
        for game in self.games:
            table = self.games[game][2][133]  # Eevee's native stone conditions.
            for offset in range(0, 42, 6):
                method, stone, target = struct.unpack_from('<HHH', table, offset)
                if method != 7:
                    continue
                for context in (2, 3):
                    with self.subTest(game=game, stone=stone, context=context):
                        actual = self.execute(game, 133, 40, context=context, item=stone)
                        self.assertEqual(actual[0], target)
                        self.assertEqual(actual, self.execute(game, 133, 40, context=context, item=stone, enhanced=False))

    def test_native_completion_removes_trade_item_only_after_eligibility(self):
        for game in self.games:
            eligibility = self.execute(game, 95, 40, 233)
            self.assertEqual(eligibility[0], 208)
            self.assertEqual(eligibility[2:], (233, []))
            completed = self.execute(game, 95, 40, 233, completion=True)
            self.assertEqual(completed[2], 0)
            self.assertEqual(completed[3], [(0x02182000, 6, 0)])
            plain_trade = self.execute(game, 67, 40, 1, completion=True, completion_method=5)
            self.assertEqual(plain_trade[2:], (1, []))


if __name__ == '__main__':
    unittest.main()

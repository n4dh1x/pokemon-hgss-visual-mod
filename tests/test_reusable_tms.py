"""Execute the original and patched Thumb teaching function in an ARM emulator.

External game calls are observed/stubbed. This tests the actual instructions
and call flow, not a Python reproduction of the intended item-use condition.
Interactive melonDS verification remains required for the full user flow.
"""
import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gameplay.patches import reusable_tms, PatchMismatch, LEARN_MOVE_ADDRESS, TAKE_TM_ADDRESS

try:
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_SP
    HAS_ARM_TOOLS = True
except ImportError:
    HAS_ARM_TOOLS = False


@unittest.skipUnless(HAS_ARM_TOOLS, 'Install requirements-dev.txt for ARM instruction tests.')
class TestReusableTMs(unittest.TestCase):
    def run_teaching(self, code, item, move, slot=2):
        emu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        emu.mem_map(0x02000000, 0x400000)
        emu.mem_write(0x02000000, bytes(code))
        menu, args, mon, bag = 0x02180000, 0x02181000, 0x02182000, 0x02183000
        stop = 0x02300000
        emu.mem_write(menu + 0x654, struct.pack('<I', args))
        emu.mem_write(args + 4, struct.pack('<I', bag))
        emu.mem_write(args + 0x28, struct.pack('<HH', item, move))
        events = []
        registers = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
        services = {0x0206EC40: 'set_mon_data', 0x0207332C: 'max_pp',
                    0x02078024: 'is_hm', 0x02078434: 'take_item',
                    0x020828EC: 'map_section', 0x0206FE90: 'friendship',
                    0x02097F0C: 'mood'}

        def hook(uc, address, size, _):
            if address == stop:
                uc.emu_stop()
                return
            if address not in services:
                return
            name = services[address]
            r = tuple(uc.reg_read(reg) for reg in registers)
            if name == 'set_mon_data':
                events.append((name, r[0], r[1], struct.unpack('<I', uc.mem_read(r[2], 4))[0]))
            else:
                events.append((name, *r[:3]))
            if name == 'is_hm':
                uc.reg_write(UC_ARM_REG_R0, int(r[0] in (15, 19, 57, 70, 127, 249, 250, 431)))
            elif name == 'max_pp':
                uc.reg_write(UC_ARM_REG_R0, 20)
            elif name == 'map_section':
                uc.reg_write(UC_ARM_REG_R0, 7)
            else:
                uc.reg_write(UC_ARM_REG_R0, 1)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        emu.hook_add(UC_HOOK_CODE, hook)
        for reg, value in ((UC_ARM_REG_R0, menu), (UC_ARM_REG_R1, mon),
                           (UC_ARM_REG_R2, slot), (UC_ARM_REG_SP, 0x023FF000),
                           (UC_ARM_REG_LR, stop | 1)):
            emu.reg_write(reg, value)
        emu.emu_start(LEARN_MOVE_ADDRESS | 1, stop, count=1000)
        self.assertEqual(emu.reg_read(UC_ARM_REG_PC), stop)
        self.assertEqual(emu.reg_read(UC_ARM_REG_SP), 0x023FF000)
        return events

    def get_arm9(self, game):
        path = ROOT / f'build/baseline/{game}-visual-plus-full-baseline.nds'
        if not path.exists():
            self.skipTest('Build the local Visual+ baselines to execute the ROM instruction tests.')
        return bytearray(ndspy.rom.NintendoDSRom.fromFile(path).arm9)

    def test_teaching_keeps_tm_and_preserves_all_other_calls(self):
        for game in ('heartgold', 'soulsilver'):
            original = self.get_arm9(game)
            patched = bytearray(original)
            reusable_tms(patched, 0x02000000)
            for slot in range(4):
                with self.subTest(game=game, slot=slot):
                    before = self.run_teaching(original, 328, 264, slot)
                    after = self.run_teaching(patched, 328, 264, slot)
                    self.assertEqual(sum(e[0] == 'take_item' for e in before), 1)
                    self.assertEqual(sum(e[0] == 'take_item' for e in after), 0)
                    self.assertEqual([e for e in before if e[0] != 'take_item'], after)
                    self.assertEqual([e[2:] for e in after if e[0] == 'set_mon_data'],
                                     [(0x36 + slot, 264), (0x3E + slot, 0), (0x3A + slot, 20)])

    def test_hm_and_itemless_teaching_unchanged(self):
        for game in ('heartgold', 'soulsilver'):
            original = self.get_arm9(game)
            patched = bytearray(original)
            reusable_tms(patched, 0x02000000)
            for item, move in ((420, 15), (0, 264)):
                with self.subTest(game=game, item=item, move=move):
                    self.assertEqual(self.run_teaching(original, item, move),
                                     self.run_teaching(patched, item, move))

    def test_different_code_rejected_without_mutation(self):
        code = self.get_arm9('heartgold')
        code[0x82550] ^= 1
        before = hashlib.sha256(code).digest()
        with self.assertRaises(PatchMismatch):
            reusable_tms(code, 0x02000000)
        self.assertEqual(hashlib.sha256(code).digest(), before)

    def test_out_of_range_and_already_patched_rejected(self):
        with self.assertRaises(PatchMismatch):
            reusable_tms(bytearray(64), 0x02000000)
        code = self.get_arm9('heartgold')
        reusable_tms(code, 0x02000000)
        before = bytes(code)
        with self.assertRaises(PatchMismatch):
            reusable_tms(code, 0x02000000)
        self.assertEqual(bytes(code), before)


if __name__ == '__main__':
    unittest.main()

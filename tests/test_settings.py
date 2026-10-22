"""Execute settings journal/menu code with a flash fixture and native APIs."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
    from gameplay.native import build_payload, PAYLOAD_BASE
    from gameplay.settings import audit_save_layout, JOURNAL_OFFSETS
    from gameplay.patches import PatchMismatch
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def record(owner, sequence, values=(1, 1, 1), version=1):
    body = struct.pack('<63I', 0x53454748, version, sequence, owner, 48,
                       *values, *([0] * (48 - len(values))), *([0] * 10))
    return body + struct.pack('<I', zlib.crc32(body) & 0xFFFFFFFF)


@unittest.skipUnless(AVAILABLE, 'Install requirements-dev.txt for native settings tests.')
class TestSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build_payload()

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_map(0x01FF8000, 0x8000)
        self.uc.mem_write(PAYLOAD_BASE, self.payload.data)
        self.field, self.save, self.profile = 0x02210000, 0x02211000, 0x02212000
        self.manager, self.objects = 0x02214000, 0x02215000
        self.put(self.field + 12, self.save)
        self.put(self.field + 0x3C, self.manager)
        self.put(self.field + 4, 0x02213000)
        self.put(0x02213008, 0x02213100)
        self.put(self.manager + 4, 2)
        self.put(self.manager + 0x124, self.objects)
        self.put(self.objects, 1 | 64)
        self.put(self.objects + 0x12C, 1)
        self.owner = 0x12345678
        self.flash = bytearray(b'\xFF' * 0x80000)
        self.writes, self.reads, self.calls, self.draws = [], [], [], []
        self.fail_write = False
        self.state = self.payload.symbols['gSettingsState']
        self.menu = self.payload.symbols['gEnhancedMenu']
        self.uc.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value & 0xFFFFFFFF))

    def get(self, address):
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def install(self, slot, data):
        offset = JOURNAL_OFFSETS[slot]
        self.flash[offset:offset + 256] = data

    def hook(self, uc, address, size, _):
        if address < 0x02000000:
            return
        if address == 0x02300000:
            uc.emu_stop()
            return
        a, b, c, d = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        self.calls.append((address, a, b, c, d))
        result = 0
        if address == 0x02028E9C:
            self.assertEqual(a, self.save)
            result = self.profile
        elif address == 0x02028F84:
            self.assertEqual(a, self.profile)
            result = self.owner
        elif address == 0x0202877C:
            self.assertIn(a, JOURNAL_OFFSETS)
            self.assertEqual(c, 256)
            self.reads.append((a, c))
            uc.mem_write(b, bytes(self.flash[a:a + c]))
            result = 1
        elif address == 0x02028758:
            self.assertIn(a, JOURNAL_OFFSETS)
            self.assertEqual(c, 256)
            data = bytes(uc.mem_read(b, c))
            self.writes.append((a, data))
            self.flash[a:a + (128 if self.fail_write else c)] = data[:128 if self.fail_write else c]
            result = int(not self.fail_write)
        elif address in (0x0201A4BC, 0x0201A4CC):
            self.assertEqual(a, 1)
        elif address == 0x02078434:
            result = 0xABCD
        elif address == 0x020504F0:
            self.assertEqual(a, self.field)
            self.assertEqual(b, self.payload.symbols['EnhancedMenuTask'])
            self.put(self.field + 0x10, 0x02213200)
            result = 0x02213200
        elif address == 0x02026354:
            result = 0x02213300
        elif address == 0x020269A0:
            codes = []
            for i in range(64):
                code = struct.unpack('<H', uc.mem_read(b + 2 * i, 2))[0]
                if code == 0xFFFF: break
                codes.append(code)
            self.draws.append(codes)
        elif address in (0x021EFACC, 0x0201D40C, 0x0200E3DC, 0x0200E580,
                         0x0201D978, 0x020200FC, 0x0201D578, 0x0200E5D4,
                         0x0201D520, 0x02026380):
            pass
        else:
            self.fail(f'Unexpected native settings API: {address:#x}')
        uc.reg_write(UC_ARM_REG_R0, result)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def execute(self, symbol, *args):
        for r, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), (*args, 0, 0, 0, 0)):
            self.uc.reg_write(r, value)
        self.uc.reg_write(UC_ARM_REG_SP, 0x023FF000)
        self.uc.reg_write(UC_ARM_REG_LR, 0x02300001)
        self.uc.emu_start(self.payload.symbols[symbol], 0x02300000, count=200000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), 0x02300000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), 0x023FF000)
        return self.uc.reg_read(UC_ARM_REG_R0)

    def values(self):
        return struct.unpack('<3I', self.uc.mem_read(PAYLOAD_BASE + 8, 12))

    def reload(self):
        self.put(self.state + 8, 0)
        self.execute('EnhancedSettingsEnsure', self.field)

    def test_crc_matches_standard_and_checks_all_record_bytes(self):
        data = record(self.owner, 3)
        at = 0x02220000
        self.uc.mem_write(at, data)
        self.assertEqual(self.execute('EnhancedSettingsCRC', at, 252), zlib.crc32(data[:252]) & 0xFFFFFFFF)
        self.assertEqual(self.execute('EnhancedSettingsValid', at, self.owner), 1)
        for offset in (0, 8, 12, 20, 120, 251, 255):
            damaged = bytearray(data); damaged[offset] ^= 1
            self.uc.mem_write(at, bytes(damaged))
            self.assertEqual(self.execute('EnhancedSettingsValid', at, self.owner), 0, offset)

    def test_alternating_writes_preserve_all_native_bytes_and_reload(self):
        self.flash[0:0x3F000] = bytes((i * 37) & 255 for i in range(0x3F000))
        self.flash[0x40000:0x7F000] = bytes((i * 53) & 255 for i in range(0x3F000))
        before = bytes(self.flash)
        self.reload()
        self.assertEqual(self.values(), (1, 1, 1))
        self.assertEqual(self.execute('EnhancedSettingsStore', 0, 0, 3), 1)
        self.assertEqual(self.execute('EnhancedSettingsStore', 1, 0, 2), 1)
        self.assertEqual([x[0] for x in self.writes], list(JOURNAL_OFFSETS))
        for lo, hi in ((0, 0x3F000), (0x3F100, 0x7F000), (0x7F100, 0x80000)):
            self.assertEqual(bytes(self.flash[lo:hi]), before[lo:hi])
        self.reload()
        self.assertEqual(self.values(), (1, 0, 2))

    def test_corrupt_newer_record_falls_back_to_older_valid_copy(self):
        self.install(0, record(self.owner, 6, (0, 1, 2)))
        damaged = bytearray(record(self.owner, 7, (1, 0, 3))); damaged[-1] ^= 1
        self.install(1, damaged)
        self.reload()
        self.assertEqual(self.values(), (0, 1, 2))

    def test_zero_initialized_unused_pages_accept_first_write(self):
        self.flash[:] = bytes(len(self.flash))
        self.reload()
        self.assertEqual(self.execute('EnhancedSettingsStore', 0, 0, 3), 1)
        self.reload()
        self.assertEqual(self.values(), (0, 0, 3))

    def test_unknown_first_page_uses_other_blank_page_without_overwriting(self):
        unknown = record(self.owner, 8, (0, 0, 3), version=2)
        self.install(0, unknown)
        self.reload()
        self.assertEqual(self.execute('EnhancedSettingsStore', 1, 0, 2), 1)
        self.assertEqual(self.flash[JOURNAL_OFFSETS[0]:JOURNAL_OFFSETS[0] + 256], unknown)
        self.assertEqual(self.writes[0][0], JOURNAL_OFFSETS[1])
        self.reload()
        self.assertEqual(self.values(), (1, 0, 2))

    def test_wrong_owner_and_future_format_are_not_loaded_or_overwritten(self):
        self.install(0, record(self.owner + 1, 8, (0, 0, 3), version=2))
        self.install(1, record(self.owner + 1, 9, (0, 0, 2), version=2))
        original = bytes(self.flash)
        self.reload()
        self.assertEqual(self.values(), (1, 1, 1))
        self.assertEqual(self.execute('EnhancedSettingsStore', 0, 0, 3), 0)
        self.assertEqual(bytes(self.flash), original)

    def test_sequence_wrap_and_invalid_option_values(self):
        self.install(0, record(self.owner, 0xFFFFFFFF, (1, 0, 1)))
        self.install(1, record(self.owner, 0, (0, 1, 2)))
        self.reload()
        self.assertEqual(self.values(), (0, 1, 2))
        self.assertEqual(self.execute('EnhancedSettingsStore', 2, 0, 1), 0)
        self.assertEqual(self.execute('EnhancedSettingsStore', 1, 1, 4), 0)
        self.assertEqual(self.writes, [])

    def test_interrupted_write_keeps_previous_valid_journal(self):
        self.install(0, record(self.owner, 12, (0, 1, 2)))
        self.reload()
        self.fail_write = True
        self.assertEqual(self.execute('EnhancedSettingsStore', 1, 0, 3), 0)
        self.assertEqual(self.values(), (0, 1, 2))
        self.reload()
        self.assertEqual(self.values(), (0, 1, 2))

    def test_tm_toggle_returns_success_or_original_consumption(self):
        self.put(PAYLOAD_BASE + 12, 1)
        self.assertEqual(self.execute('EnhancedTakeTm', 0x02230000, 328, 1, 12), 1)
        self.assertFalse(any(c[0] == 0x02078434 for c in self.calls))
        self.put(PAYLOAD_BASE + 12, 0)
        self.assertEqual(self.execute('EnhancedTakeTm', 0x02230000, 328, 1, 12), 0xABCD)
        self.assertEqual(self.calls[-1][1:], (0x02230000, 328, 1, 12))

    def test_menu_cancel_restores_npc_pause_and_does_not_apply_or_write(self):
        self.assertEqual(self.execute('EnhancedMenuOpen', self.field), 1)
        self.execute('EnhancedMenuTask', 0)
        self.put(0x021D1154, 0x10)
        self.execute('EnhancedMenuTask', 0)
        self.assertEqual(self.get(self.menu + 44), 2)
        self.assertEqual(self.values(), (1, 1, 1))
        self.put(0x021D1154, 2)
        self.assertEqual(self.execute('EnhancedMenuTask', 0), 1)
        self.assertEqual(self.writes, [])
        self.assertEqual(self.get(self.objects), 65)
        self.assertEqual(self.get(self.objects + 0x12C), 1)

    def test_menu_apply_writes_on_later_task_tick_then_closes(self):
        self.execute('EnhancedMenuOpen', self.field)
        self.execute('EnhancedMenuTask', 0)
        self.put(self.menu + 44, 3)
        self.put(self.menu + 32, 4)
        self.put(0x021D1154, 1)
        self.assertEqual(self.execute('EnhancedMenuTask', 0), 0)
        self.assertEqual(self.writes, [])
        self.put(0x021D1154, 0)
        self.assertEqual(self.execute('EnhancedMenuTask', 0), 1)
        self.assertEqual(self.values(), (1, 1, 3))
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.get(self.menu + 24), 0)

    def test_legacy_journal_defaults_new_repel_option_on_then_preserves_explicit_off(self):
        self.install(0, record(self.owner, 8, (0, 1, 3)))
        self.reload()
        self.assertEqual(self.get(PAYLOAD_BASE + 20), 1)
        self.assertEqual(self.execute('EnhancedSettingsStore', 0, 1, 3, 0), 1)
        self.reload()
        self.assertEqual(self.values(), (0, 1, 3))
        self.assertEqual(self.get(PAYLOAD_BASE + 20), 0)
        self.assertEqual(self.execute('EnhancedSettingsStore', 0, 1, 3, 2), 0)


@unittest.skipUnless(AVAILABLE, 'Install requirements-dev.txt for save layout audit.')
class TestSaveLayout(unittest.TestCase):
    def test_both_native_layouts_reserve_journal_pages_and_reject_table_edits(self):
        for game in ('heartgold', 'soulsilver'):
            path = ROOT / f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists(): self.skipTest('Build both local Visual+ baselines first.')
            rom = ndspy.rom.NintendoDSRom.fromFile(path)
            layout = audit_save_layout(rom)
            self.assertEqual(layout['native_data_end_per_bank'], 0x2ED60)
            self.assertEqual(layout['journal_offsets'], [0x3F000, 0x7F000])
            data = bytearray(rom.arm9); data[0xF6468] ^= 1; rom.arm9 = data
            with self.assertRaises(PatchMismatch): audit_save_layout(rom)


if __name__ == '__main__':
    unittest.main()

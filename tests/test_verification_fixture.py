"""Guard exact-checkpoint fixture writes before touching emulator memory."""
import copy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.smoke_libretro import apply_ram_fixture


class TestVerificationFixture(unittest.TestCase):
    def setUp(self):
        self.ram = bytes(0x400000)
        self.fixture = {'kind': 'hgss-verification-ram-fixture', 'rom_sha256': 'abc',
            'source_ram_sha256': hashlib.sha256(self.ram).hexdigest(),
            'changes': [{'address': 0x02000010, 'before': '00000000', 'after': '4f000200',
                         'reason': 'Seed two Repels in a separate test checkpoint'}]}

    def test_only_declared_bytes_change_and_input_is_immutable(self):
        after = apply_ram_fixture(self.ram, self.fixture, 'abc')
        self.assertEqual(after[:16], self.ram[:16])
        self.assertEqual(after[16:20], bytes.fromhex('4f000200'))
        self.assertEqual(after[20:], self.ram[20:])
        self.assertEqual(self.ram, bytes(len(self.ram)))

    def test_wrong_rom_checkpoint_or_late_expected_byte_mismatch_rejected(self):
        for problem in ('rom', 'checkpoint', 'late_change'):
            fixture = copy.deepcopy(self.fixture)
            if problem == 'rom': fixture['rom_sha256'] = 'other'
            if problem == 'checkpoint': fixture['source_ram_sha256'] = 'other'
            if problem == 'late_change':
                fixture['changes'].append({'address': 0x02000020, 'before': '01', 'after': '02', 'reason': 'Mismatch'})
            with self.subTest(problem=problem), self.assertRaises(ValueError):
                apply_ram_fixture(self.ram, fixture, 'abc')
        self.assertEqual(self.ram, bytes(len(self.ram)))

    def test_out_of_bounds_overlap_and_oversized_change_rejected(self):
        for problem in ('bounds', 'overlap', 'size'):
            fixture = copy.deepcopy(self.fixture)
            if problem == 'bounds': fixture['changes'][0]['address'] = 0x02400000
            if problem == 'overlap': fixture['changes'].append(fixture['changes'][0].copy())
            if problem == 'size':
                fixture['changes'][0].update(before='00'*257, after='01'*257)
            with self.subTest(problem=problem), self.assertRaises(ValueError):
                apply_ram_fixture(self.ram, fixture, 'abc')

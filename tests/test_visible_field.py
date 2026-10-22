"""Execute resident field code with controlled native APIs, plus ROM hook checks."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
    from gameplay.native import build_payload, PAYLOAD_BASE
    from gameplay.field import install_field, verify_field_files, thumb_call
    from gameplay.patches import PatchMismatch
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'Install requirements-dev.txt for ARM field tests.')
class TestVisibleField(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build_payload()

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_map(0x01FF8000, 0x8000)
        self.uc.mem_write(PAYLOAD_BASE, self.payload.data)
        self.state = self.payload.symbols['gVisibleState']
        self.field, self.manager, self.objects = 0x02210000, 0x02211000, 0x02212000
        self.avatar, self.location, self.save = 0x02218000, 0x02219000, 0x0221A000
        self.party, self.mon, self.setup, self.enemy_party = 0x0221B000, 0x0221C000, 0x0221D000, 0x0221E000
        self.input = 0x0221F000
        self.player = self.objects
        self.created = self.objects + 0x12C
        for offset, value in ((0xC, self.save), (0x20, self.location), (0x3C, self.manager), (0x40, self.avatar)):
            self.put(self.field + offset, value)
        self.put(self.location, 33)
        self.put(self.manager + 4, 64)
        self.put(self.manager + 0x124, self.objects)
        self.put(self.avatar + 0x30, self.player)
        self.put(self.player, 1)
        for offset, value in ((8, 255), (0x28, 1), (0x64, 658), (0x68, 2), (0x6C, 401), (0xB4, self.manager)):
            self.put(self.player + offset, value)
        words = [0x12345678, 163, 3, 0, 12, 0, 1] + [0xA5A50000 + i for i in range(52)]
        self.native_mon = struct.pack('<59I', *words)
        self.uc.mem_write(self.mon, self.native_mon)
        self.put(self.setup + 8, self.enemy_party)
        self.tile, self.map_wild, self.special, self.hp = 2, True, False, 12
        self.original_result = 0
        self.allowed, self.movement_busy, self.blocked, self.occupied = True, False, False, False
        self.moves = []
        self.roamer_result = False
        self.calls, self.freed, self.removed, self.script_calls = [], [], [], []
        self.battle_mon = None
        self.iterator = []
        self.uc.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value & 0xFFFFFFFF))

    def get(self, address):
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def hook(self, uc, address, size, _):
        if address < 0x02000000:
            return
        if address == 0x02300000:
            uc.emu_stop()
            return
        a, b, c, d = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        self.calls.append((address, a, b, c, d))
        result = 0
        if address == 0x021E6AF4:
            result = self.original_result
        elif address == 0x0203E13C:
            result = int(self.allowed)
        elif address == 0x0203E15C:
            result = 0
        elif address == 0x0203B324:
            result = int(self.map_wild)
        elif address == 0x020503D0:
            result = self.save + 0x100
        elif address in (0x02066644, 0x02066860, 0x02066870, 0x020668A0):
            result = int(self.special)
        elif address == 0x02074904:
            result = self.party
        elif address == 0x02074640:
            result = 1
        elif address == 0x02074644:
            result = self.mon
        elif address == 0x0206E540:
            field = {0: 0, 5: 1, 161: 2, 76: 3, 163: 4, 112: 5, 111: 6}[b]
            result = self.get(a + field * 4)
            if a == self.mon and b == 163:
                result = self.hp
        elif address == 0x02054918:
            result = self.tile
        elif address in (0x020548C0, 0x020549F4):
            result = int(self.blocked)
        elif address == 0x02060BFC:
            result = int(self.occupied)
        elif address == 0x02062198:
            result = int(not self.movement_busy)
        elif address == 0x020621C0:
            result = 1
        elif address == 0x0206214C:
            self.moves.append((a, b))
        elif address == 0x0201FD44:
            result = 0  # chooses a known unoccupied tile, x/z -3
        elif address == 0x02246C8C:
            if self.get(self.state + 4):
                self.put(self.state + 8, self.setup)
            elif self.get(self.state + 1624) and not self.roamer_result:
                self.put(self.state + 1628, 1)
            result = 1
        elif address in (0x02247568, 0x02248360):
            result = 7
        elif address == 0x02051BF8:
            self.assertEqual(a, self.setup)
            self.freed.append(a)
        elif address == 0x02069D70:
            result = 0x251
        elif address == 0x0207003C:
            result = 0
        elif address == 0x0205E1D0:
            event = bytes(uc.mem_read(b, 32))
            values = struct.unpack('<12H2Hi', event)
            self.put(self.created, 1)
            for offset, value in ((8, values[0]), (0xC, c), (0x10, values[1]),
                                  (0x4C, values[12]), (0x54, values[13]),
                                  (0x64, values[12]), (0x68, 2), (0x6C, values[13]), (0xB4, self.manager)):
                self.put(self.created + offset, value)
            result = self.created
        elif address == 0x02069EE8:
            self.assertEqual((a, b), (self.created, 163))
        elif address == 0x02069DC8:
            self.assertEqual(b, 0, 'Native TRUE hides Pokemon models.')
        elif address == 0x020518D8:
            self.assertEqual((a, b), (11, 0))
            result = self.setup
        elif address == 0x02051F00:
            self.assertEqual((a, b), (self.setup, self.field))
        elif address == 0x02051C9C:
            self.battle_mon = bytes(uc.mem_read(b, 236))
            self.assertEqual(c, 1)
        elif address == 0x0205E3CC:
            self.removed.append(a)
            self.put(a, 0)
        elif address == 0x02050B08:
            self.assertEqual((a, b), (self.field, self.setup))
        elif address == 0x0203FE74:
            self.script_calls.append((a, b, c))
        elif address == 0x0205EEF4:
            index = self.get(c)
            if index < len(self.iterator):
                self.put(b, self.iterator[index])
                self.put(c, index + 1)
                result = 1
        elif address == 0x0201AB80:
            self.freed.append((a, b))
        else:
            self.fail(f'Unexpected native API at {address:#x}')
        uc.reg_write(UC_ARM_REG_R0, result)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def execute(self, name, *args):
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), (*args, 0, 0, 0, 0)):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(UC_ARM_REG_SP, 0x023FF000)
        self.uc.reg_write(UC_ARM_REG_LR, 0x02300001)
        self.uc.emu_start(self.payload.symbols[name], 0x02300000, count=100000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), 0x02300000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), 0x023FF000)
        return self.uc.reg_read(UC_ARM_REG_R0)

    def make_spawn(self):
        self.put(self.state, self.manager)
        self.put(self.state + 12, 59)
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertEqual(self.get(self.state + 16), 1)

    def test_spawn_keeps_exact_pokemon_and_contact_refreshes_battle(self):
        self.make_spawn()
        slot = self.state + 32
        self.assertEqual(self.get(slot), self.created)
        self.assertEqual(bytes(self.uc.mem_read(slot + 12, 236)), self.native_mon)
        self.assertEqual(self.get(slot + 248), 163)
        self.assertEqual(self.get(slot + 252), 3)
        self.assertEqual(self.get(slot + 256), 0x12345678)
        self.execute('EnhancedStartScript', self.field, 0, self.created)
        self.assertEqual(self.battle_mon, self.native_mon)
        self.assertEqual(self.removed, [self.created])
        self.assertEqual(self.get(slot), 0)
        self.assertEqual(self.get(self.state + 20), 1)
        self.assertEqual(len([c for c in self.calls if c[0] == 0x02051F00]), 1)
        self.assertEqual(self.script_calls, [])

    def test_save_iterator_excludes_only_owned_objects(self):
        self.make_spawn()
        other = self.objects + 0x258
        self.put(other, 1)
        self.put(other + 8, 0xE0)
        self.put(other + 0xB4, self.manager)
        self.iterator = [self.player, self.created, other]
        out, index = 0x02220000, 0x02220004
        actual = []
        while self.execute('EnhancedSaveIterator', self.manager, out, index, 1):
            actual.append(self.get(out))
        self.assertEqual(actual, [self.player, other])
        self.assertEqual(self.get(self.state + 24), 1)

    def test_many_suppresses_only_regular_grass_step_encounters(self):
        for mode in (0, 1, 2, 3):
            self.put(PAYLOAD_BASE + 16, mode)
            self.assertEqual(self.execute('EnhancedStepEncounter', self.field), 0 if mode == 3 else 1)
        self.special = True
        self.assertEqual(self.execute('EnhancedStepEncounter', self.field), 1)
        self.special = False
        self.tile = 16
        self.assertEqual(self.execute('EnhancedStepEncounter', self.field), 1)
        self.tile = 2
        self.hp = 0
        self.assertEqual(self.execute('EnhancedStepEncounter', self.field), 1)
        self.hp = 12
        self.roamer_result = True
        self.assertEqual(self.execute('EnhancedStepEncounter', self.field), 1,
                         'Many mode must retain the native roamer path.')

    def test_scripts_and_ineligible_fields_never_generate(self):
        self.put(self.state, self.manager)
        self.put(self.state + 12, 59)
        self.original_result = 2
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 2)
        self.original_result = 0
        self.map_wild = False
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.map_wild = True
        self.hp = 0
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertEqual(self.get(self.state + 16), 0)

    def test_generation_intercepts_leave_normal_calls_unchanged(self):
        self.assertEqual(self.execute('EnhancedEncounterRoll', self.field, 20, 2), 7)
        self.assertEqual(self.execute('EnhancedRoamerCheck', self.field, 0), 7)
        self.put(self.state + 4, 1)
        self.assertEqual(self.execute('EnhancedEncounterRoll', self.field, 20, 2), 1)
        self.assertEqual(self.execute('EnhancedRoamerCheck', self.field, 0), 0)
        self.execute('EnhancedCaptureEncounter', self.field, self.setup)
        self.assertEqual(self.get(self.state + 8), self.setup)
        self.assertEqual(len([c for c in self.calls if c[0] == 0x02050B08]), 0)

    def test_manager_deletion_drops_ownership_before_free(self):
        self.make_spawn()
        self.execute('EnhancedManagerDelete', self.manager)
        self.assertEqual(self.get(self.state), 0)
        self.assertEqual(self.get(self.state + 32), 0)
        self.assertEqual(self.freed[-2:], [(11, self.objects), (11, self.manager)])

    def test_roaming_uses_native_walk_and_respects_terrain_and_occupancy(self):
        self.make_spawn()
        self.put(self.state + 1592, 0)
        position = bytes(self.uc.mem_read(self.created + 0x64, 12))
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertEqual(self.moves, [(self.created, 12)])
        self.assertEqual(bytes(self.uc.mem_read(self.created + 0x64, 12)), position,
                         'Resident code must schedule interpolation, not teleport.')
        for reason in ('terrain', 'occupied', 'busy', 'not_grass'):
            self.blocked, self.occupied, self.movement_busy, self.tile = False, False, False, 2
            if reason == 'terrain': self.blocked = True
            if reason == 'occupied': self.occupied = True
            if reason == 'busy': self.movement_busy = True
            if reason == 'not_grass': self.tile = 16
            self.put(self.state + 1592, 0)
            self.execute('EnhancedFieldInput', self.input, self.field)
            self.assertEqual(len(self.moves), 1, reason)

    def test_menu_script_freeze_and_resume_owned_wilds_only(self):
        self.make_spawn()
        self.allowed = False
        self.execute('EnhancedFieldControl', self.field)
        self.assertEqual(self.get(self.created) & 2, 2)
        self.assertEqual(self.get(self.player) & 2, 0)
        self.assertEqual(self.get(self.state + 1620), 1)
        self.allowed = True
        self.execute('EnhancedFieldControl', self.field)
        self.assertEqual(self.get(self.created) & 2, 0)
        self.assertEqual(self.get(self.state + 1620), 0)

    def test_roaming_into_stationary_player_starts_retained_battle(self):
        self.make_spawn()
        self.put(self.player + 0x64, self.get(self.created + 0x64))
        self.put(self.player + 0x6C, self.get(self.created + 0x6C) - 1)
        self.put(self.state + 1592, 0)
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 1)
        self.assertEqual(self.get(self.state + 20), 1)
        self.assertEqual(self.battle_mon, self.native_mon)
        self.assertEqual(self.moves, [])

    def test_many_discards_ordinary_setup_without_launching_it(self):
        self.put(self.state + 1624, 1)
        self.execute('EnhancedCaptureEncounter', self.field, self.setup)
        self.assertEqual(self.get(self.state + 1628), 1)
        self.assertEqual(self.freed, [self.setup])
        self.assertFalse(any(c[0] == 0x02050B08 for c in self.calls))


@unittest.skipUnless(AVAILABLE, 'Install requirements-dev.txt for ROM field hooks.')
class TestFieldHooks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build_payload()

    def test_both_games_allow_only_recorded_field_mutations(self):
        for game in ('heartgold', 'soulsilver'):
            path = ROOT / f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if not path.exists():
                self.skipTest('Build both local Visual+ baselines first.')
            original = ndspy.rom.NintendoDSRom.fromFile(path)
            patched = ndspy.rom.NintendoDSRom.fromFile(path)
            main, overlays = install_field(patched, self.payload)
            self.assertEqual((len(main), len(overlays)), (5, 6))
            verify_field_files(original, patched, overlays)
            patched.files[-1] = bytes(patched.files[-1]) + b'changed'
            with self.assertRaises(PatchMismatch):
                verify_field_files(original, patched, overlays)

    def test_branch_rejects_wrong_state_and_range(self):
        with self.assertRaises(PatchMismatch):
            thumb_call(0x02000001, 0x02000101)
        with self.assertRaises(PatchMismatch):
            thumb_call(0x02000000, 0x02000100)
        with self.assertRaises(PatchMismatch):
            thumb_call(0x02000000, 0x03000001)


if __name__ == '__main__':
    unittest.main()

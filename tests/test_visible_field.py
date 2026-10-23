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
        settings = self.payload.symbols['gSettingsState']
        self.put(settings, self.save)
        self.put(settings + 4, 0x1234)
        self.put(settings + 8, 1)
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
        self.tiles = {}
        self.tile, self.map_wild, self.special, self.hp = 2, True, False, 12
        self.original_result = 0
        self.allowed, self.movement_busy, self.blocked, self.occupied = True, False, False, False
        self.moves = []
        self.shiny = False
        self.sparkle_result = 0x02230000
        self.put(self.field+0x44, 0x02231000)
        self.roamer_result = False
        self.native_roll_results = []
        self.native_roamer_gate = 7
        self.repel = False
        self.party_mons = [self.mon]
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
        elif address == 0x02028E9C:
            result = self.save + 0x100
        elif address == 0x02028F84:
            result = 0x1234
        elif address == 0x0203B324:
            result = int(self.map_wild)
        elif address == 0x020503D0:
            result = self.save + 0x100
        elif address in (0x02066644, 0x02066860, 0x02066870, 0x020668A0):
            result = int(self.special)
        elif address == 0x02074904:
            result = self.party
        elif address == 0x02074640:
            result = len(self.party_mons) if a == self.party else 1
        elif address == 0x02074644:
            result = self.party_mons[b] if a == self.party else self.mon
        elif address == 0x0202D9C4:
            self.assertEqual(a, self.save)
            result = self.save + 0x200
        elif address == 0x0202DB08:
            self.assertEqual(a, self.save + 0x200)
            result = int(not self.repel)
        elif address == 0x0206E540:
            field = {0: 0, 5: 1, 161: 2, 76: 3, 163: 4, 112: 5, 111: 6}[b]
            result = self.get(a + field * 4)
            if a == self.mon and b == 163:
                result = self.hp
        elif address == 0x02054918:
            result = self.tiles.get((b,c), self.tile)
        elif address == 0x0205B994:
            result = int(a in (2,3,5,8,11,16,18,21,37,42))
        elif address == 0x0205B778:
            result = int(a in (16,17,18,19,20,21,25,42,80,81,82,83))
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
        elif address == 0x02247568:
            result = self.native_roll_results.pop(0) if self.native_roll_results else 7
        elif address == 0x02248360:
            result = self.native_roamer_gate
            if result and b:self.put(b,self.save+0x300)
        elif address == 0x02051BF8:
            self.assertEqual(a, self.setup)
            self.freed.append(a)
        elif address == 0x02069D70:
            result = 0x251
        elif address == 0x021FE66C:
            self.assertEqual(a, self.created)
            result = self.sparkle_result
        elif address == 0x0200604C:
            self.assertEqual(a, 2340)
            result = 1
        elif address == 0x0207003C:
            result = int(self.shiny)
        elif address == 0x0205E1D0:
            event = bytes(uc.mem_read(b, 32))
            values = struct.unpack('<12H2Hi', event)
            self.put(self.created, 1)
            for offset, value in ((8, values[0]), (0xC, c), (0x10, values[1]),
                                  (0x4C, values[12]), (0x54, values[13]),
                                  (0x64, values[12]), (0x68, 2), (0x6C, values[13]), (0xB4, self.manager)):
                self.put(self.created + offset, value)
            self.put(self.created+0x38,values[7]);self.put(self.created+0x3C,values[8]);self.put(self.created+0x40,values[9])
            result = self.created
        elif address == 0x02069EE8:
            self.assertEqual(b, 163)
            self.put(a+0x38,b);self.put(a+0x3C,0x123);self.put(a+0x40,int(self.shiny))
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
        elif address == 0x0205F24C:
            result = self.get(a+8)
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

    def test_shiny_glints_repeat_silently_and_normal_spawns_are_silent(self):
        self.shiny = True
        self.make_spawn()
        visual = self.payload.symbols['gVisibleVisualState']
        self.assertEqual(self.get(visual+20), 1)
        self.assertEqual(self.get(visual+52), 1)
        self.assertEqual(self.get(visual+28), 120)
        self.put(visual+28, 0)
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertEqual(self.get(visual+20), 2)
        self.assertEqual(self.get(visual+52), 1)
        self.assertEqual(len([c for c in self.calls if c[0]==0x0200604C]), 1)
        self.execute('EnhancedStartScript', self.field, 0, self.created)
        self.assertEqual(self.get(visual+28), 0)
        self.assertEqual(self.battle_mon, self.native_mon)

    def test_sparkle_failure_keeps_shiny_spawn_and_one_chime(self):
        self.shiny = True
        self.sparkle_result = 0
        self.make_spawn()
        visual = self.payload.symbols['gVisibleVisualState']
        self.assertEqual(self.get(visual+24), 1)
        self.assertEqual(self.get(visual+52), 1)
        self.assertEqual(self.get(self.state+32), self.created)

    def test_normal_spawn_has_no_shiny_effect_or_sound(self):
        self.make_spawn()
        for _ in range(3):
            self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertFalse(any(c[0] in (0x021FE66C,0x0200604C) for c in self.calls))

    def test_cave_and_surf_spawns_keep_native_pokemon_and_surface(self):
        for tile, habitat, surfing in ((8,2,False),(16,3,True)):
            self.setUp();self.tile=tile
            self.put(self.avatar+0x18,2 if surfing else 0)
            self.make_spawn()
            hs=self.payload.symbols['gVisibleHabitatState']
            self.assertEqual(self.get(hs),habitat)
            self.assertEqual(self.get(hs+24+habitat*4),1)
            self.execute('EnhancedStartScript',self.field,0,self.created)
            self.assertEqual(self.battle_mon,self.native_mon)
            self.assertEqual(self.get(hs),0)

    def test_water_requires_surf_and_water_wild_is_cleared_after_dismount(self):
        self.tile=16;self.put(self.state,self.manager);self.put(self.state+12,59)
        self.execute('EnhancedFieldInput',self.input,self.field)
        self.assertEqual(self.get(self.state+16),0)
        self.put(self.avatar+0x18,2);self.make_spawn()
        self.put(self.avatar+0x18,0)
        self.execute('EnhancedStartScript',self.field,0,self.created)
        self.assertIsNone(self.battle_mon)
        self.assertEqual(self.removed,[self.created])

    def test_cave_wilds_cannot_step_on_warps_or_water(self):
        self.tile=8;self.make_spawn()
        x=self.get(self.created+0x64);z=self.get(self.created+0x6C)
        for bad_tile in (0,16,60):
            self.tiles[(x,z-1)]=bad_tile
            self.put(self.state+1592,0)
            self.execute('EnhancedFieldInput',self.input,self.field)
            self.assertEqual(self.moves,[])
        self.tiles[(x,z-1)]=8;self.put(self.state+1592,0)
        self.execute('EnhancedFieldInput',self.input,self.field)
        self.assertEqual(self.moves,[(self.created,12)])

    def test_surf_wilds_cannot_step_onto_shore_and_release_on_surface_change(self):
        self.tile=16;self.put(self.avatar+0x18,2);self.make_spawn()
        x=self.get(self.created+0x64);z=self.get(self.created+0x6C)
        self.tiles[(x,z-1)]=8;self.put(self.state+1592,0)
        self.execute('EnhancedFieldInput',self.input,self.field)
        self.assertEqual(self.moves,[])
        self.tiles[(x,z)]=0
        self.execute('EnhancedFieldInput',self.input,self.field)
        self.assertEqual(self.removed,[self.created])
        self.assertEqual(self.get(self.payload.symbols['gVisibleHabitatState']+40),1)

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

    def test_grass_contact_only_is_optional_and_applies_to_every_visible_mode(self):
        extra=self.payload.symbols['gEnhancedExtraOptions']
        for mode in (0,1,2,3):
            self.put(PAYLOAD_BASE+16,mode)
            self.assertEqual(self.execute('EnhancedStepEncounter',self.field),1)
        self.put(extra+4,1)
        for mode in (0,1,2,3):
            self.put(PAYLOAD_BASE+16,mode);self.calls=[]
            self.assertEqual(self.execute('EnhancedStepEncounter',self.field),1 if mode==0 else 0)
            self.assertEqual(any(c[0]==0x02246C8C for c in self.calls),mode==0)
        self.roamer_result=True;self.calls=[]
        self.assertEqual(self.execute('EnhancedStepEncounter',self.field),0)
        self.assertFalse(any(c[0]==0x02246C8C for c in self.calls),
                         'No hidden native roamer branch may start a grass battle in contact-only mode.')

    def test_contact_only_keeps_water_caves_special_contexts_and_no_live_party_native(self):
        self.put(self.payload.symbols['gEnhancedExtraOptions']+4,1)
        for tile in (0,16):
            self.tile=tile;self.assertEqual(self.execute('EnhancedStepEncounter',self.field),1)
        self.tile=2;self.special=True;self.assertEqual(self.execute('EnhancedStepEncounter',self.field),1)
        self.special=False;self.hp=0;self.assertEqual(self.execute('EnhancedStepEncounter',self.field),1)

    def test_contact_only_still_generates_and_launches_the_exact_roaming_pokemon(self):
        self.put(self.payload.symbols['gEnhancedExtraOptions']+4,1)
        self.assertEqual(self.execute('EnhancedStepEncounter',self.field),0)
        self.make_spawn();self.position_for_unsolicited_contact()
        self.assertEqual(self.execute('EnhancedFieldInput',self.input,self.field),1)
        self.assertEqual(self.battle_mon,self.native_mon)
        self.assertEqual(self.get(self.state+1640),1)

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

    def test_normal_mode_launches_ordinary_setup_without_discarding_it(self):
        self.put(self.state+1624,1)  # Obsolete implicit-Many flag must not leak.
        self.execute('EnhancedCaptureEncounter',self.field,self.setup)
        self.assertEqual(self.freed,[])
        self.assertTrue(any(c[0]==0x02050B08 for c in self.calls))

    def position_for_unsolicited_contact(self):
        self.put(self.player + 0x64, self.get(self.created + 0x64))
        self.put(self.player + 0x6C, self.get(self.created + 0x6C) - 1)
        self.put(self.state + 1592, 0)

    def test_repel_used_after_spawn_blocks_wild_contact_until_it_expires(self):
        self.put(self.payload.symbols['gEnhancedExtraOptions']+4,1)
        self.make_spawn()
        self.put(self.mon + 8, 10)
        self.repel = True
        self.position_for_unsolicited_contact()
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 0)
        self.assertEqual(self.get(self.state + 20), 0)
        self.assertEqual(self.get(self.state + 1632), 1)
        self.assertEqual(self.get(self.state + 32), self.created)
        self.assertEqual(self.removed, [])
        self.assertEqual(self.moves, [])
        self.repel = False
        self.position_for_unsolicited_contact()
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 1)
        self.assertEqual(self.battle_mon, self.native_mon)

    def test_repel_uses_current_first_alive_member_and_allows_equal_level(self):
        self.make_spawn()
        self.repel = True
        egg, fainted = 0x02230000, 0x02231000
        for address in (egg, fainted): self.uc.mem_write(address, self.native_mon)
        self.put(egg + 12, 1)
        self.put(egg + 8, 50)
        self.put(fainted + 16, 0)
        self.put(fainted + 8, 40)
        self.party_mons = [egg, fainted, self.mon]
        self.put(self.mon + 8, 4)
        self.position_for_unsolicited_contact()
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 0)
        self.put(self.mon + 8, 3)
        self.position_for_unsolicited_contact()
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 1)
        self.assertEqual(self.battle_mon, self.native_mon)

    def test_player_can_deliberately_interact_with_repellable_wild(self):
        self.make_spawn()
        self.put(self.mon + 8, 50)
        self.repel = True
        self.execute('EnhancedStartScript', self.field, 0, self.created)
        self.assertEqual(self.battle_mon, self.native_mon)

    def test_connected_map_change_releases_old_wild_before_contact(self):
        self.make_spawn()
        self.position_for_unsolicited_contact()
        self.put(self.location, 34)
        self.assertEqual(self.execute('EnhancedFieldInput', self.input, self.field), 0)
        self.assertEqual(self.removed, [self.created])
        self.assertEqual(self.get(self.state + 32), 0)
        self.assertEqual(self.get(self.state + 1636), 1)
        self.assertIsNone(self.battle_mon)

    def test_reused_object_on_new_map_is_not_owned_or_removed(self):
        self.make_spawn()
        self.put(self.created + 0x0C, 34)
        self.put(self.location, 34)
        self.put(self.state + 12, 0)
        self.iterator = [self.created]
        out, index = 0x02220000, 0x02220004
        self.assertEqual(self.execute('EnhancedSaveIterator', self.manager, out, index, 1), 1)
        self.assertEqual(self.get(out), self.created)
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertEqual(self.removed, [])
        self.assertEqual(self.get(self.state + 32), 0)

    def test_early_a_interaction_on_changed_map_discards_before_battle(self):
        self.make_spawn()
        self.put(self.location, 34)
        self.execute('EnhancedStartScript', self.field, 0, self.created)
        self.assertEqual(self.removed, [self.created])
        self.assertEqual(self.get(self.state + 1636), 1)
        self.assertEqual(self.get(self.state + 20), 0)
        self.assertIsNone(self.battle_mon)
        self.assertEqual(self.script_calls, [])

    def test_early_a_interaction_after_mode_off_does_not_launch(self):
        self.make_spawn()
        self.put(PAYLOAD_BASE + 16, 0)
        self.execute('EnhancedStartScript', self.field, 0, self.created)
        self.assertEqual(self.removed, [self.created])
        self.assertIsNone(self.battle_mon)

    def test_existing_wild_is_removed_when_special_context_starts(self):
        self.make_spawn()
        self.special = True
        self.position_for_unsolicited_contact()
        self.execute('EnhancedFieldInput', self.input, self.field)
        self.assertEqual(self.removed, [self.created])
        self.assertIsNone(self.battle_mon)

    def test_early_a_interaction_in_special_context_does_not_launch(self):
        self.make_spawn()
        self.special = True
        self.execute('EnhancedStartScript', self.field, 0, self.created)
        self.assertEqual(self.removed, [self.created])
        self.assertIsNone(self.battle_mon)

    def test_encounter_rate_scales_native_rate_clamps_and_keeps_normal_calls_exact(self):
        extra=self.payload.symbols['gEnhancedExtraOptions']
        for mode,rate,want in ((0,20,20),(2,20,5),(3,20,10),(4,20,40),(4,200,100),(2,3,0),(99,20,20)):
            self.put(extra+12,mode);self.native_roamer_gate=0;self.native_roll_results=[0,1]
            self.calls=[];self.execute('EnhancedEncounterRoll',self.field,rate,2)
            rolls=[c for c in self.calls if c[0]==0x02247568]
            self.assertEqual(rolls[-1][2:4],(want,2))
            self.assertEqual(len(rolls),1 if mode in (0,99) else 2)
            self.assertEqual(self.native_mon,bytes(self.uc.mem_read(self.mon,236)))

    def test_encounter_rate_off_blocks_ordinary_but_preserves_cached_native_roamer(self):
        extra=self.payload.symbols['gEnhancedExtraOptions'];state=self.payload.symbols['gEncounterRateState'];out=self.input+0x40
        self.put(extra+12,1);self.native_roamer_gate=0;self.native_roll_results=[1]
        self.assertEqual(self.execute('EnhancedEncounterRoll',self.field,20,2),0)
        self.assertEqual(self.get(state+24),1)
        self.native_roamer_gate=1;self.native_roll_results=[1];self.calls=[]
        self.assertEqual(self.execute('EnhancedEncounterRoll',self.field,20,2),1)
        self.assertEqual(self.execute('EnhancedRoamerCheck',self.field,out),1)
        self.assertEqual(self.get(out),self.save+0x300);self.assertEqual(self.get(state+8),0)
        self.assertEqual(len([c for c in self.calls if c[0]==0x02248360]),1)
        self.assertEqual(self.get(state+20),1)

    def test_double_rate_cannot_create_a_roamer_after_failed_native_roll(self):
        self.put(self.payload.symbols['gEnhancedExtraOptions']+12,4)
        self.native_roll_results=[0,1];self.native_roamer_gate=1;self.calls=[];out=self.input+0x40
        self.assertEqual(self.execute('EnhancedEncounterRoll',self.field,20,2),1)
        self.assertEqual(self.execute('EnhancedRoamerCheck',self.field,out),0)
        self.assertEqual(self.get(out),0)
        self.assertEqual([c for c in self.calls if c[0]==0x02248360],[])
        self.assertEqual(self.execute('EnhancedRoamerCheck',self.field,out),1)
        self.assertEqual(len([c for c in self.calls if c[0]==0x02248360]),1,'Cache must be consumed exactly once.')

    def test_rate_capture_bypasses_multiplier_but_native_special_contexts_do_not_change(self):
        extra=self.payload.symbols['gEnhancedExtraOptions'];state=self.payload.symbols['gEncounterRateState']
        for mode in range(5):
            self.put(extra+12,mode);self.put(self.state+4,1);self.calls=[]
            self.assertEqual(self.execute('EnhancedEncounterRoll',self.field,20,2),1)
            self.assertEqual(self.execute('EnhancedRoamerCheck',self.field,self.input+0x40),0)
            self.assertEqual(self.calls,[])
        self.put(self.state+4,0);self.special=True;self.put(extra+12,1);self.calls=[]
        self.assertEqual(self.execute('EnhancedEncounterRoll',self.field,20,2),7)
        self.assertEqual(self.get(state+12),0)

    def test_visible_spawn_cadence_scales_without_altering_density_or_identity(self):
        extra=self.payload.symbols['gEnhancedExtraOptions']
        for mode,interval in ((0,60),(2,240),(3,120),(4,30),(99,60)):
            self.put(extra+12,mode);self.assertEqual(self.execute('EnhancedSpawnInterval'),interval)
            self.put(self.state,self.manager);self.put(self.state+12,interval-2)
            self.put(self.state+32,0);self.put(self.created,0);self.put(self.state+16,0)
            self.execute('EnhancedFieldInput',self.input,self.field);self.assertEqual(self.get(self.state+16),0)
            self.execute('EnhancedFieldInput',self.input,self.field);self.assertEqual(self.get(self.state+16),1)
            self.assertEqual(bytes(self.uc.mem_read(self.state+44,236)),self.native_mon)

    def test_rate_off_clears_visible_wilds_and_blocks_stale_a_contact(self):
        self.make_spawn();extra=self.payload.symbols['gEnhancedExtraOptions'];self.put(extra+12,1)
        self.execute('EnhancedStartScript',self.field,0,self.created)
        self.assertEqual(self.removed,[self.created]);self.assertIsNone(self.battle_mon)
        self.put(self.state+12,999);self.execute('EnhancedFieldInput',self.input,self.field)
        self.assertEqual(self.get(self.state+12),0);self.assertEqual(self.get(self.state+16),1)
        self.assertEqual(self.execute('EnhancedSpawnInterval'),0)


    def test_palette_identity_is_local_to_owned_objects_and_preserves_real_ids(self):
        self.shiny=True;self.make_spawn()
        self.assertEqual(self.get(self.created+0x38),163)
        self.assertEqual(self.get(self.created+0x3C),0x123)
        self.assertEqual(self.get(self.created+0x40)&1,1)
        before=bytes(self.uc.mem_read(self.created,0x12C));mon=bytes(self.uc.mem_read(self.state+44,236))
        self.assertEqual(self.execute('EnhancedPaletteObjectId',self.created),0xFD)
        self.assertEqual(bytes(self.uc.mem_read(self.created,0x12C)),before)
        self.assertEqual(bytes(self.uc.mem_read(self.state+44,236)),mon)
        self.assertEqual(self.execute('EnhancedPaletteObjectId',self.player),255)
        self.put(self.created+0x0C,34)
        self.assertEqual(self.execute('EnhancedPaletteObjectId',self.created),0xE0)
        self.assertEqual(self.get(self.created+8),0xE0)

    def test_palette_pending_requires_exact_manager_map_sprite_species_and_active_object(self):
        self.shiny=True;self.make_spawn();visual=self.payload.symbols['gVisibleVisualState']
        self.put(self.state+32,0);self.put(visual,1);self.put(visual+4,self.get(self.created+0x10))
        self.assertEqual(self.execute('EnhancedPaletteObjectId',self.created),0xFD)
        for offset in (0,8,0x0C,0x10,0x38,0xB4):
            before=self.get(self.created+offset);self.put(self.created+offset,before^1)
            self.assertNotEqual(self.execute('EnhancedPaletteObjectId',self.created),0xFD)
            self.put(self.created+offset,before)
        self.put(visual,0)
        self.assertEqual(self.execute('EnhancedPaletteObjectId',self.created),0xE0)
        self.assertEqual(self.get(visual+12),1)


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
            self.assertEqual((len(main), len(overlays)), (5, 8))
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

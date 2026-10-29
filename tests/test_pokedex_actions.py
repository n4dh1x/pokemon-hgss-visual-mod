"""Execute native HGSS Dex bookkeeping with bounded Pokemon/heap services."""
from pathlib import Path
import hashlib
import struct
import unittest
import ndspy.narc
import test_settings as api
from gameplay.dex import audit_dex, MAIN_CONTEXTS
ROOT = Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE, 'Install native ARM dependencies.')
class TestPokedexActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = api.build_payload()
        cls.payload.symbols['NativeDexNationalCount'] = 0x02029E0D
        cls.rom = api.ndspy.rom.NintendoDSRom.fromFile(ROOT / 'build/baseline/heartgold-visual-plus-full-baseline.nds')
        cls.table = bytes(ndspy.narc.NARC(cls.rom.getFileByName('a/1/3/8')).files[0])
        cls.members = {i for i, n in enumerate(struct.unpack('<494H', cls.table)) if n}

    def setUp(self):
        owner = self
        self.events = []; self.alloc_fail = self.list_fail = False
        self.species = 1; self.language = 2; self.pid = 1; self.gender = 0; self.form = 0
        self.dex, self.mon, self.lut = 0x02220000, 0x02221000, 0x02222000
        class Fixture(api.TestSettings):
            def hook(f, uc, address, size, context):
                if 0x02029408 <= address < 0x0202A634 or 0x020290A8 <= address < 0x020290B2:
                    return  # Execute original native Dex routines and profile bit setter.
                a,b,c,d = [uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                result = 0
                if address == 0x0202A634:
                    owner.assertEqual(a, f.save); result = owner.dex
                elif address == 0x0201AA8C:
                    owner.assertEqual((a,b),(4,236)); owner.events.append(('alloc',b))
                    result = 0 if owner.alloc_fail else owner.mon
                elif address == 0x0207187C:
                    owner.events.append(('johto',)); result = 0 if owner.list_fail else owner.lut
                elif address == 0x0201AB0C:
                    owner.assertIn(a,(owner.mon,owner.lut)); owner.events.append(('free',a))
                elif address == 0x0206DE38:
                    owner.assertEqual((a,c,d),(owner.mon,1,0))
                    sp = uc.reg_read(api.UC_ARM_REG_SP)
                    tail = struct.unpack('<4I', uc.mem_read(sp,16))
                    owner.assertEqual(tail,(1,1,1,f.owner))
                    owner.species = b; owner.events.append(('create',b))
                elif address == 0x0206E540:
                    owner.assertEqual(a,owner.mon)
                    owner.assertIn(b,(0,5,12,112))
                    result = {0:owner.pid,5:owner.species,12:owner.language,112:owner.form}[b]
                elif address == 0x0206FF88: result = owner.gender
                elif address == 0x02070D98: result = 0
                elif address == 0x02091278:
                    result = [1,2,3,4,5,7].index(a) if a in (1,2,3,4,5,7) else 6
                elif address == 0x0200604C: owner.events.append(('sound',a))
                else: return super().hook(uc,address,size,context)
                uc.reg_write(api.UC_ARM_REG_R0,result)
                uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        self.f = Fixture(); self.f.payload = self.payload; self.f.setUp()
        self.f.uc.mem_write(0x02000000,bytes(self.rom.arm9))
        self.f.uc.mem_write(self.lut,self.table)
        self.f.uc.mem_write(self.dex,b'\0'*0x340)
        self.f.put(self.dex,0xBEEFCAFE)
        for at,n in [(0x108,4),(0x10C,56),(0x338,4),(0x33C,3)]:self.f.uc.mem_write(self.dex+at,b'\xFF'*n)
        self.f.put(self.dex+0x40,0xFF000000);self.f.put(self.dex+0x80,0xFF000000)
        self.f.execute('EnhancedSettingsEnsure',self.f.field)
        self.state=self.payload.symbols['gDexAction']
        self.f.put(self.f.profile+28,0xA1) # Game-clear bit and unrelated bytes retained.

    def flags(self, offset):
        raw=bytes(self.f.uc.mem_read(self.dex+offset,64))
        return {i for i in range(1,494) if raw[(i-1)//8] & (1<<((i-1)%8))}

    def complete(self, action):
        self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,action),1)
        for count in range(495):
            result=self.f.execute('EnhancedDexStep')
            if result: self.assertEqual(result,1);return count
        self.fail('Dex action did not complete within species bound.')

    def test_native_regional_membership_includes_exactly_256_species_and_preserves_other_entries(self):
        self.assertEqual(len(self.members),256)
        self.species=493;self.f.execute('NativeDexCaught',self.dex,self.mon)
        self.complete(0)
        self.assertEqual(self.flags(4),self.members|{493});self.assertEqual(self.flags(0x44),self.members|{493})
        self.assertEqual([x[1] for x in self.events if x[0]=='create'],sorted(self.members))
        self.assertEqual(self.f.get(self.state+32),256)
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex+0x336,2)),b'\0\0')
        self.assertEqual(self.f.get(self.f.profile+28),0xA1)
        self.assertEqual(self.events.count(('free',self.mon)),1);self.assertEqual(self.events.count(('free',self.lut)),1)
        self.assertEqual(self.f.writes,[])

    def test_native_national_upgrade_sets_only_both_original_flags_without_caught_entries_or_story_flags(self):
        before=bytes(self.f.uc.mem_read(self.dex,0x340));self.complete(1)
        after=bytes(self.f.uc.mem_read(self.dex,0x340))
        expected=bytearray(before);expected[0x337]=1
        self.assertEqual(after,bytes(expected));self.assertEqual(self.f.get(self.f.profile+28),0x2A1)
        self.assertFalse(any(x[0]=='create' or x[0]=='alloc' for x in self.events));self.assertEqual(self.f.writes,[])

    def test_native_full_national_records_seen_caught_english_and_forms_without_replacing_existing_metadata(self):
        # Preserve existing seen Spinda PID and previously registered Shellos form.
        self.species=327;self.pid=0x12345678;self.f.execute('NativeDexCaught',self.dex,self.mon)
        self.species=422;self.form=1;self.f.execute('NativeDexCaught',self.dex,self.mon)
        self.pid=1;self.form=0
        self.complete(2)
        self.assertEqual(self.flags(4),set(range(1,494)));self.assertEqual(self.flags(0x44),set(range(1,494)))
        self.assertEqual(self.f.get(self.dex+0x104),0x12345678)
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex+0x144+1,493)),bytes([2])*493)
        self.assertEqual(self.f.get(self.state+32),493)
        self.assertEqual(self.f.execute('NativeDexNationalCount',self.dex),493)
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex+0x108,1))[0]&3,1)
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex+0x336,2)),b'\0\1')
        self.assertEqual(self.f.get(self.f.profile+28),0x2A1)
        self.assertEqual(self.f.writes,[])

    def test_allocation_failure_never_applies_national_upgrade_and_frees_any_allocated_memory(self):
        for mode in ('mon','lut'):
            self.alloc_fail=mode=='mon';self.list_fail=mode=='lut'
            before=bytes(self.f.uc.mem_read(self.dex,0x340))
            self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,0),0)
            self.assertEqual(bytes(self.f.uc.mem_read(self.dex,0x340)),before)
        self.assertIn(('free',self.lut),self.events);self.assertIn(('free',self.mon),self.events)
        self.alloc_fail=True
        self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,2),0)
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex+0x337,1)),b'\0')

    def test_invalid_context_and_owner_change_deny_or_stop_without_writing_another_save(self):
        self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,3),0)
        self.f.put(self.dex,0);self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,0),0)
        self.f.put(self.dex,0xBEEFCAFE)
        self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,0),1)
        self.assertEqual(self.f.execute('EnhancedDexBegin',self.f.field,2),0)
        self.f.owner^=1
        self.assertEqual(self.f.execute('EnhancedDexStep'),0xFFFFFFFF)
        self.assertEqual(self.flags(4),set());self.assertIn(('free',self.mon),self.events)

    def key(self,value):
        self.f.put(0x021D1154,value);return self.f.execute('EnhancedMenuTask',0)

    def open_actions(self):
        self.f.execute('EnhancedMenuOpen',self.f.field);self.key(0);self.key(0x200)
        for _ in range(4):self.key(0x80)
        self.assertEqual(self.f.get(self.f.menu+32),4)
        before=self.f.get(self.payload.symbols['gEnhancedExtraOptions']+52)
        self.key(0x10);self.assertEqual(self.f.get(self.payload.symbols['gEnhancedExtraOptions']+52),before)
        self.key(1);self.assertEqual(self.f.get(self.f.menu+28),3)

    def test_actions_default_No_and_B_back_preserve_all_progress_and_staged_settings(self):
        self.open_actions();before=bytes(self.f.uc.mem_read(self.dex,0x340))
        self.key(1);self.key(1) # Default No.
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex,0x340)),before)
        self.key(1);self.key(2) # Confirmation B.
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex,0x340)),before)
        self.key(2);self.assertEqual(self.f.get(self.f.menu+28),1)
        self.assertEqual(self.f.get(self.f.menu+32),4);self.assertEqual(self.f.writes,[])

    def test_UI_confirmed_upgrade_completes_and_returns_without_saving_unrelated_settings(self):
        self.open_actions();self.key(0x80);self.key(1);self.key(0x40);self.key(1);self.key(0)
        self.assertEqual(bytes(self.f.uc.mem_read(self.dex+0x337,1)),b'\1')
        self.key(1);self.key(2)
        self.assertEqual(self.f.get(self.f.menu+28),1);self.assertEqual(self.f.writes,[])

    def test_both_baselines_guard_all_native_routines_and_regional_table_without_mutating_ROM(self):
        for game in ('heartgold','soulsilver'):
            original=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds')
            before=hashlib.sha256(original.save()).digest();audit_dex(original)
            self.assertEqual(hashlib.sha256(original.save()).digest(),before)
            for address,size,digest in MAIN_CONTEXTS:
                bad=api.ndspy.rom.NintendoDSRom(original.save());arm=bytearray(bad.arm9);arm[address-bad.arm9RamAddress]^=1;bad.arm9=bytes(arm)
                with self.assertRaises(api.PatchMismatch):audit_dex(bad)
            bad=api.ndspy.rom.NintendoDSRom(original.save());data=bytearray(bad.getFileByName('a/1/3/8'));data[-1]^=1;bad.setFileByName('a/1/3/8',bytes(data))
            with self.assertRaises(api.PatchMismatch):audit_dex(bad)

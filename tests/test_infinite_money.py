"""Native wallet entry veneers, original setters and Mom's reward bookkeeping."""
from pathlib import Path
import struct
import unittest
import test_settings as api
from gameplay.money import install_money, MAIN_CONTEXTS
ROOT = Path(__file__).resolve().parent.parent
MAX_MONEY = 999999

@unittest.skipUnless(api.AVAILABLE, 'Install native ARM dependencies.')
class TestInfiniteMoney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = api.build_payload()
        cls.payload.symbols.update(NativeMoneyGet=0x02029025, NativeMoneySet=0x02029029,
                                   NativeMoneyAdd=0x02029045, NativeMoneySub=0x02029069,
                                   NativeMomReward=0x0205230D)

    def setUp(self):
        owner = self
        self.mom_enabled, self.mom_balance, self.gifts = 1, 0, []
        class Fixture(api.TestSettings):
            def hook(f, uc, address, size, context):
                if (0x02029024 <= address < 0x02029088 or
                        0x0205230C <= address < 0x0205239C):
                    return
                a, b, c = [uc.reg_read(reg) for reg in
                           (api.UC_ARM_REG_R0, api.UC_ARM_REG_R1, api.UC_ARM_REG_R2)]
                if address == 0x020503D0:
                    result = 0x02230000
                elif address == 0x0202ED88:
                    result = 0x02231000
                elif address == 0x02066794:
                    result = owner.mom_enabled
                elif address == 0x0202F14C:
                    owner.assertEqual(a, 0x02231000)
                    if b == 2:
                        owner.mom_balance = min(MAX_MONEY, owner.mom_balance + c)
                    else:
                        owner.assertEqual(b, 0)
                    result = owner.mom_balance
                elif address == 0x0209322C:
                    owner.gifts.append((a, b, c))
                    result = 0
                else:
                    return super().hook(uc, address, size, context)
                uc.reg_write(api.UC_ARM_REG_R0, result)
                uc.reg_write(api.UC_ARM_REG_PC, uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload = self.payload
        self.f = Fixture('runTest')
        self.f.setUp()
        self.f.reload()
        original = api.ndspy.rom.NintendoDSRom.fromFile(
            ROOT / 'build/baseline/heartgold-visual-plus-full-baseline.nds')
        patched = api.ndspy.rom.NintendoDSRom(original.save())
        install_money(patched, self.payload)
        self.f.uc.mem_write(0x02000000, bytes(patched.arm9))
        self.extra = self.payload.symbols['gEnhancedExtraOptions']
        self.state = self.payload.symbols['gMoneyState']
        self.copy = 0x02222000
        self.f.put(self.f.profile + 20, 3064)
        self.f.put(self.copy + 20, 3128)

    def call(self, name, profile=None, amount=None):
        args = [self.f.profile if profile is None else profile]
        if amount is not None:
            args.append(amount)
        return self.f.execute(name, *args)

    def test_original_relocated_bodies_match_bytes_and_preserve_native_bounds(self):
        for name, expected in (('OriginalMoneyRead', '40697047'),
                               ('OriginalMoneySet', '034a914200d9111c4161081c7047c0463f420f00')):
            address = self.payload.symbols[name] & ~1
            self.assertEqual(address % 4, 0)
            self.assertEqual(bytes(self.f.uc.mem_read(address, len(expected)//2)), bytes.fromhex(expected))
        for value in (0, 1, MAX_MONEY-1, MAX_MONEY, 0xFFFFFFFF):
            self.f.put(self.f.profile+20, value)
            before = bytes(self.f.uc.mem_read(self.f.profile, 64))
            self.assertEqual(self.call('NativeMoneyGet'), value)
            self.assertEqual(bytes(self.f.uc.mem_read(self.f.profile, 64)), before)
            self.assertEqual(self.call('NativeMoneySet', amount=value), min(value, MAX_MONEY))
            self.assertEqual(self.f.get(self.f.profile+20), min(value, MAX_MONEY))

    def test_owned_reads_refill_real_wallet_after_native_spending_and_do_not_touch_neighbors(self):
        self.f.put(self.extra+52, 1)
        self.f.uc.mem_write(self.f.profile, bytes(range(32)))
        self.f.put(self.f.profile+20, 3064)
        before = bytes(self.f.uc.mem_read(self.f.profile, 64))
        for cost in (300, 0, MAX_MONEY, MAX_MONEY+1):
            self.assertEqual(self.call('NativeMoneyGet'), MAX_MONEY)
            self.assertEqual(self.call('NativeMoneySub', amount=cost), max(0, MAX_MONEY-cost))
            self.assertEqual(self.call('NativeMoneyGet'), MAX_MONEY)
        after = bytes(self.f.uc.mem_read(self.f.profile, 64))
        self.assertEqual(after[:20]+after[24:], before[:20]+before[24:])
        self.assertGreater(self.f.get(self.state+4), 0)
        self.assertEqual(self.call('NativeMoneySet', amount=0), 0)
        self.assertEqual(self.f.get(self.f.profile+20), 0)
        self.assertEqual(self.call('NativeMoneyGet'), MAX_MONEY)
        self.assertEqual(self.call('NativeMoneyAdd', amount=MAX_MONEY+1), MAX_MONEY)
        self.f.put(self.extra+52, 0)
        self.assertEqual(self.call('NativeMoneySub', amount=300), MAX_MONEY-300)
        self.assertEqual(self.call('NativeMoneyGet'), MAX_MONEY-300)
        self.assertEqual(self.f.get(self.f.profile+20), MAX_MONEY-300)

    def test_unloaded_wrong_owner_copied_or_opponent_profiles_never_refill(self):
        for mode in ('off', 'unloaded', 'wrong-owner', 'copied', 'opponent', 'invalid-setting'):
            self.f.put(self.extra+52, 1)
            self.f.put(self.f.state+8, 1)
            self.f.owner = 0x12345678
            profile = self.f.profile
            if mode == 'off': self.f.put(self.extra+52, 0)
            elif mode == 'unloaded': self.f.put(self.f.state+8, 0)
            elif mode == 'wrong-owner': self.f.owner ^= 1
            elif mode in ('copied', 'opponent'): profile = self.copy
            elif mode == 'invalid-setting': self.f.put(self.extra+52, 2)
            self.f.put(profile+20, 3064)
            before = bytes(self.f.uc.mem_read(profile, 32))
            self.assertEqual(self.call('NativeMoneyGet', profile), 3064)
            self.assertEqual(bytes(self.f.uc.mem_read(profile, 32)), before)

    def test_original_mom_reward_delta_and_capped_savings_are_identical_on_and_off(self):
        for on in (0, 1):
            for savings in (0, MAX_MONEY-9, MAX_MONEY):
                self.f.put(self.extra+52, on)
                self.f.put(self.f.profile+20, 3064)
                self.f.put(self.copy+20, 3128)
                self.mom_balance, self.gifts = savings, []
                self.f.execute('NativeMomReward', self.f.field, self.f.profile, self.copy)
                deposit = min(16, MAX_MONEY-savings)
                self.assertEqual(self.mom_balance, savings+deposit)
                self.assertEqual(self.f.get(self.copy+20), 3128-deposit)
                self.assertEqual(self.f.get(self.f.profile+20), 3064)
                self.assertEqual(self.gifts, [(0x02231000, savings+deposit, savings)])
                self.assertEqual(self.call('NativeMoneyGet'), MAX_MONEY if on else 3064)
        self.assertEqual(self.f.get(self.state+16), 6)

    def test_native_mom_no_reward_loss_and_disabled_savings_stay_unchanged(self):
        self.f.put(self.extra+52, 1)
        for before, after in ((MAX_MONEY, MAX_MONEY), (3064, 3000), (0, 0)):
            self.f.put(self.f.profile+20, before)
            self.f.put(self.copy+20, after)
            self.mom_balance = 100
            self.f.execute('NativeMomReward', self.f.field, self.f.profile, self.copy)
            self.assertEqual(self.mom_balance, 100)
            self.assertEqual(self.f.get(self.copy+20), after)
            self.assertEqual(self.f.get(self.f.profile+20), before)
        self.mom_enabled = 0
        calls = self.f.get(self.state)
        self.f.execute('NativeMomReward', self.f.field, self.f.profile, self.copy)
        self.assertEqual(self.f.get(self.state), calls)

    def test_shared_entry_tail_branches_preserve_stack_and_callee_saved_registers(self):
        from unicorn.arm_const import (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
            UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        registers = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                     UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        self.f.put(self.extra+52, 1)
        for i, reg in enumerate(registers): self.f.uc.reg_write(reg, 0x12340000+i)
        for name, amount in (('NativeMoneyGet', None), ('NativeMoneySet', 3000),
                             ('NativeMoneyAdd', 64), ('NativeMoneySub', 300)):
            self.call(name, amount=amount)
            self.assertEqual([self.f.uc.reg_read(reg) for reg in registers],
                             [0x12340000+i for i in range(8)])

    def test_both_baselines_only_change_twenty_entry_bytes_and_reject_context_mutations(self):
        for game in ('heartgold', 'soulsilver'):
            original = api.ndspy.rom.NintendoDSRom.fromFile(
                ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds')
            patched = api.ndspy.rom.NintendoDSRom(original.save())
            changes = install_money(patched, self.payload)
            self.assertEqual(len(changes), 1)
            a, b = bytes(original.arm9), bytes(patched.arm9)
            self.assertEqual(a[:0x29024]+a[0x29038:], b[:0x29024]+b[0x29038:])
            self.assertEqual(original.files, patched.files)
            for address, size, digest in MAIN_CONTEXTS:
                bad = api.ndspy.rom.NintendoDSRom(original.save())
                arm = bytearray(bad.arm9); arm[address-bad.arm9RamAddress] ^= 1
                bad.arm9 = bytes(arm)
                with self.assertRaises(api.PatchMismatch): install_money(bad, self.payload)

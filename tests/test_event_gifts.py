"""Exercise the compiled event catalogue against bounded native API fixtures."""
import struct
import unittest

import test_settings as settings


@unittest.skipUnless(settings.AVAILABLE, 'Install requirements-dev.txt for ARM tests.')
class TestEventGifts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = settings.build_payload()

    def setUp(self):
        test = self

        class FieldFixture(settings.TestSettings):
            def hook(self, uc, address, size, data):
                if address < 0x02000000 or address == 0x02300000:
                    return super().hook(uc, address, size, data)
                name = test.apis.get(address)
                if name is None:
                    return super().hook(uc, address, size, data)
                args = [uc.reg_read(register) for register in (
                    settings.UC_ARM_REG_R0, settings.UC_ARM_REG_R1,
                    settings.UC_ARM_REG_R2, settings.UC_ARM_REG_R3)]
                result = getattr(test, name)(*args)
                uc.reg_write(settings.UC_ARM_REG_R0, result or 0)
                uc.reg_write(settings.UC_ARM_REG_PC, uc.reg_read(settings.UC_ARM_REG_LR))

        self.apis = {self.payload.symbols[name] & ~1: name for name in (
            'NativeMysteryGift', 'NativeInsertGift', 'NativeGiftFlagSet',
            'NativeCreateMon', 'NativeGiftMove', 'SetMonData', 'Heap_Alloc', 'Heap_Free',
            'Save_VarsFlags_Get', 'CheckSafari', 'CheckContest', 'CheckPalPark',
            'FieldSystem_MapIsBattleTowerMultiPartnerSelectRoom', 'NativeNormalMenuInhibitFlags',
            'FieldSystem_VarGet', 'Save_Bag_Get', 'Bag_HasItem')}
        self.vm = FieldFixture(methodName='runTest')
        self.vm.payload = self.payload
        self.vm.setUp()
        self.vm.reload()
        self.block = 0x02222000
        self.allocation = 0x02224000
        self.frame = 0
        self.deliveries = []
        self.fail_insert = False
        self.story_progress = 0
        self.existing_stone = False
        self.bag_blocked = False
        self.allocations = 0

    def NativeMysteryGift(self, save, *_):
        self.assertEqual(save, self.vm.save)
        return self.block

    def NativeGiftFlagSet(self, block, flag, *_):
        self.assertEqual(block, self.block)
        address = block + flag // 8
        byte = self.vm.uc.mem_read(address, 1)[0]
        self.vm.uc.mem_write(address, bytes([byte | 1 << (flag % 8)]))

    def NativeInsertGift(self, block, source, card, _):
        self.assertEqual((block, source, card), (self.block, self.allocation, 3))
        if self.fail_insert:
            return 0
        record = bytes(self.vm.uc.mem_read(source, 260))
        for slot in range(8):
            pointer = block + 256 + 260 * slot
            if self.vm.get(pointer) == 0:
                self.vm.uc.mem_write(pointer, record)
                self.deliveries.append(record)
                return 1
        self.fail('Attempted to overwrite a full native queue')

    def NativeCreateMon(self, mon, species, level, ivs):
        self.assertEqual((mon, ivs), (self.allocation + 8, 32))
        stack = self.vm.uc.reg_read(settings.UC_ARM_REG_SP)
        fixed, pid, ot_kind, owner = struct.unpack('<4I', self.vm.uc.mem_read(stack, 16))
        self.assertEqual((fixed, ot_kind, owner), (1, 1, self.vm.owner))
        self.vm.uc.mem_write(mon, struct.pack('<4I', species, level, pid, owner))

    def SetMonData(self, mon, attribute, value, _):
        self.assertIn(attribute, (110, 155))
        self.vm.put(mon + (16 if attribute == 110 else 20), self.vm.get(value))

    def NativeGiftMove(self, mon, move, slot, _):
        self.vm.put(mon + 24 + slot * 4, move)

    def Heap_Alloc(self, heap, size, *_):
        self.assertEqual((heap, size), (4, 260))
        self.allocations += 1
        return self.allocation

    def Heap_Free(self, pointer, *_):
        self.assertEqual(pointer, self.allocation)
        self.allocations -= 1

    def Save_VarsFlags_Get(self, save, *_):
        self.assertEqual(save, self.vm.save)
        return 0x02226000

    def CheckSafari(self, *_):
        return 0

    CheckContest = CheckPalPark = FieldSystem_MapIsBattleTowerMultiPartnerSelectRoom = CheckSafari

    def NativeNormalMenuInhibitFlags(self, *_):
        return 4 if self.bag_blocked else 0

    def FieldSystem_VarGet(self, field, var, *_):
        self.assertEqual((field, var), (self.vm.field, 0x4083))
        return self.story_progress

    def Save_Bag_Get(self, save, *_):
        self.assertEqual(save, self.vm.save)
        return 0x02227000

    def Bag_HasItem(self, bag, item, count, heap):
        self.assertEqual((bag, item, count, heap), (0x02227000, 536, 1, 4))
        return int(self.existing_stone)

    def enable(self):
        return self.vm.execute('EnhancedEventsEnable', self.vm.field)

    def tick(self):
        self.frame += 60
        self.vm.put(0x021D1138, self.frame)
        self.vm.execute('EnhancedEventsTick', self.vm.field)
        self.assertEqual(self.allocations, 0)

    def empty_queue(self):
        # Model completed native receipts without clearing received flags.
        self.vm.uc.mem_write(self.block + 256, bytes(8 * 260))

    def test_full_catalogue_refills_without_duplicates_and_keeps_wonder_cards(self):
        sentinel = b'active Wonder Card'
        self.vm.uc.mem_write(self.block + 0x920, sentinel)
        self.tick()
        self.assertEqual(self.deliveries, [])
        self.assertEqual(self.enable(), 1)
        self.tick()
        self.assertEqual(len(self.deliveries), 8)
        self.tick()
        self.assertEqual(len(self.deliveries), 8)
        for _ in range(4):
            self.empty_queue()
            self.tick()
        tags = [struct.unpack_from('<I', row)[0] for row in self.deliveries]
        self.assertEqual(len(tags), 28)
        self.assertEqual(tags.count(7), 1)
        self.assertEqual([struct.unpack_from('<I', row, 4)[0] for row, tag in zip(self.deliveries, tags) if tag == 14], list(range(21, 27)))
        self.assertEqual([struct.unpack_from('<I', row, 4)[0] for row, tag in zip(self.deliveries, tags) if tag == 3], [536])
        pokemon = [struct.unpack_from('<6I', row, 8) for row, tag in zip(self.deliveries, tags) if tag == 1]
        self.assertTrue({151, 251, 385, 386, 489, 491, 492, 493}.issubset({mon[0] for mon in pokemon}))
        self.assertEqual(len({mon[2] for mon in pokemon}), len(pokemon))
        for species, _, pid, owner, fateful, ball in pokemon:
            self.assertEqual((fateful, ball), (1, 16))
            shiny = ((pid ^ (pid >> 16) ^ owner ^ (owner >> 16)) & 0xFFFF) < 8
            self.assertEqual(shiny, species in {172, 243, 244, 245, 133, 350})
        self.assertEqual(bytes(self.vm.uc.mem_read(self.block + 0x920, len(sentinel))), sentinel)
        self.assertEqual(self.vm.writes, [])

    def test_unsafe_or_conflicting_activation_keeps_native_bytes(self):
        self.bag_blocked = True
        self.assertEqual(self.enable(), 0)
        self.bag_blocked = False
        self.vm.put(self.block + 248, 1)
        before = bytes(self.vm.uc.mem_read(self.block, 0x1680))
        self.assertEqual(self.enable(), 0)
        self.tick()
        self.assertEqual(bytes(self.vm.uc.mem_read(self.block, 0x1680)), before)

    def test_insert_failure_retries_and_existing_stone_progress_is_preserved(self):
        self.assertEqual(self.enable(), 1)
        self.fail_insert = True
        self.tick()
        self.assertEqual(self.vm.get(self.block + 248), 0)
        self.fail_insert = False
        self.story_progress = 3
        for _ in range(4):
            self.empty_queue()
            self.tick()
        self.assertEqual(len(self.deliveries), 27)
        self.assertEqual(self.vm.get(self.block + 248) & 0x0FFFFFFF, 0x0FFFFFFF)
        self.assertNotIn(3, [struct.unpack_from('<I', row)[0] for row in self.deliveries])

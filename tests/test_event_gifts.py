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
            'FieldSystem_VarGet', 'Save_Bag_Get', 'Bag_HasItem', 'NativeSavePokewalker')}
        self.vm = FieldFixture(methodName='runTest')
        self.vm.payload = self.payload
        self.vm.setUp()
        self.vm.reload()
        self.block = 0x02222000
        self.allocation = 0x02224000
        self.pokewalker = 0x02228000
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

    def NativeSavePokewalker(self, save, *_):
        self.assertEqual(save, self.vm.save)
        return self.pokewalker

    def queue(self, index):
        result = self.vm.execute('EnhancedQueueEvent', self.vm.field, index)
        self.assertEqual(self.allocations, 0)
        return result

    def empty_queue(self):
        # Model completed native receipts without clearing received flags.
        self.vm.uc.mem_write(self.block + 256, bytes(8 * 260))

    def test_every_gift_can_be_selected_and_wonder_cards_are_preserved(self):
        sentinel = b'active Wonder Card'
        self.vm.uc.mem_write(self.block + 0x920, sentinel)
        for index in range(28):
            if index and index % 8 == 0:
                self.assertEqual(self.queue(index), 3)
                self.assertEqual(self.vm.get(self.block + 248), (1 << index) - 1)
                self.empty_queue()
            self.assertEqual(self.queue(index), 1)
            self.assertEqual(self.queue(index), 2)
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

    def test_selection_is_independent_and_respects_existing_save_flags(self):
        # Keep a save previously enabled by the bulk queue.
        self.vm.put(self.block + 252, 0xec350000)
        self.vm.put(self.block + 248, 1)
        self.assertEqual(self.queue(0), 2)
        self.assertEqual(self.queue(8), 1)
        self.assertEqual(self.vm.get(self.block + 248), 0x101)
        self.assertEqual(len(self.deliveries), 1)
        self.assertEqual(struct.unpack_from('<I', self.deliveries[0], 8)[0], 493)

    def test_unsafe_or_conflicting_selection_keeps_native_bytes(self):
        self.bag_blocked = True
        self.assertEqual(self.queue(1), 4)
        self.bag_blocked = False
        self.vm.put(self.block + 248, 1)
        before = bytes(self.vm.uc.mem_read(self.block, 0x1680))
        self.assertEqual(self.queue(1), 4)
        self.assertEqual(self.queue(28), 4)
        self.assertEqual(bytes(self.vm.uc.mem_read(self.block, 0x1680)), before)

    def test_insert_failure_can_retry_and_keeps_enigma_stone_progress(self):
        self.fail_insert = True
        self.assertEqual(self.queue(0), 4)
        self.assertEqual(self.vm.get(self.block + 248), 0)
        self.assertEqual(self.vm.get(self.block + 252), 0)
        self.fail_insert = False
        self.assertEqual(self.queue(0), 1)
        self.story_progress = 3
        self.assertEqual(self.queue(21), 2)
        self.story_progress = 0
        self.existing_stone = True
        self.assertEqual(self.queue(21), 2)
        self.assertEqual(len(self.deliveries), 1)

    def test_owned_and_pending_courses_do_not_block_other_selections(self):
        self.vm.put(self.pokewalker + 0x130, 1 << 21 | 1 << 25)
        # Only the first byte of the retail course payload holds its ID.
        original = struct.pack('<HHBBBB', 14, 1, 22, 0xa5, 0x72, 0x31) + bytes(252)
        self.vm.uc.mem_write(self.block + 256, original)
        for index in (22, 23, 26):
            self.assertEqual(self.queue(index), 2)
        for index in (24, 25, 27):
            self.assertEqual(self.queue(index), 1)
        self.assertEqual([row[4] for row in self.deliveries], [23, 24, 26])
        self.assertEqual(bytes(self.vm.uc.mem_read(self.block + 256, 260)), original)
        self.assertEqual(self.vm.get(self.pokewalker + 0x130), 1 << 21 | 1 << 25)

"""Resident loader checks, including rejecting unrecorded ARM9 edits."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
HAS_TOOLS = all(importlib.util.find_spec(name) for name in ('ndspy', 'elftools', 'unicorn'))
if HAS_TOOLS:
    import ndspy.code
    import ndspy.rom
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
    from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_SP
    from gameplay.native import (build_payload, inject_evolution, verify_arm9_changes,
                                 thumb_veneer, PAYLOAD_BASE, COLD_BASE, ITCM_ARENA_LITERAL, validate_payload_layout)
    from gameplay.patches import PatchMismatch, reusable_tms


@unittest.skipUnless(HAS_TOOLS, 'Install requirements-dev.txt for native loader tests.')
class TestNativeLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'build/baseline/heartgold-visual-plus-full-baseline.nds'
        if not path.exists():
            raise unittest.SkipTest('Build the local HeartGold Visual+ baseline first.')
        cls.rom = ndspy.rom.NintendoDSRom.fromFile(path)
        cls.payload = build_payload()

    def test_section_roundtrip_and_recorded_operations(self):
        original = bytes(self.rom.arm9)
        arm = bytearray(original)
        tm = reusable_tms(arm, self.rom.arm9RamAddress)
        injection = inject_evolution(bytes(arm), self.rom.arm9RamAddress, self.payload)
        verify_arm9_changes(original, injection.image, self.rom.arm9RamAddress,
                            [tm, *injection.changes], self.payload)
        parsed = ndspy.code.MainCodeFile(injection.image, self.rom.arm9RamAddress)
        self.assertEqual(len(parsed.sections),5)
        for actual, expected in zip(parsed.sections[1:3],ndspy.code.MainCodeFile(original,self.rom.arm9RamAddress).sections[1:]):
            self.assertEqual((actual.ramAddress,actual.bssSize,bytes(actual.data)),(expected.ramAddress,expected.bssSize,bytes(expected.data)))
        self.assertEqual(parsed.sections[3].ramAddress,COLD_BASE)
        self.assertEqual(parsed.sections[3].bssSize,0)
        self.assertEqual(bytes(parsed.sections[3].data),self.payload.cold_data)
        self.assertEqual(parsed.sections[-1].ramAddress, PAYLOAD_BASE)
        self.assertEqual(bytes(parsed.sections[-1].data), self.payload.data)
        end = struct.unpack_from('<I', parsed.sections[0].data,
                                 ITCM_ARENA_LITERAL - self.rom.arm9RamAddress)[0]
        self.assertEqual(end, PAYLOAD_BASE + len(self.payload.data))

    def test_unrecorded_arm9_change_is_rejected(self):
        injection = inject_evolution(self.rom.arm9, self.rom.arm9RamAddress, self.payload)
        changed = bytearray(injection.image)
        changed[0x1000] ^= 1
        with self.assertRaises(PatchMismatch):
            verify_arm9_changes(self.rom.arm9, changed, self.rom.arm9RamAddress,
                                injection.changes, self.payload)

    def test_modified_sdk_arena_is_rejected(self):
        arm = bytearray(self.rom.arm9)
        struct.pack_into('<I', arm, ITCM_ARENA_LITERAL - self.rom.arm9RamAddress, 0x01FF9000)
        with self.assertRaises(PatchMismatch):
            inject_evolution(bytes(arm), self.rom.arm9RamAddress, self.payload)

    def test_repeated_injection_and_wrong_base_are_rejected(self):
        injection = inject_evolution(self.rom.arm9, self.rom.arm9RamAddress, self.payload)
        with self.assertRaises(PatchMismatch):
            inject_evolution(injection.image, self.rom.arm9RamAddress, self.payload)
        with self.assertRaises(PatchMismatch):
            inject_evolution(self.rom.arm9, 0x02000004, self.payload)

    def test_both_USA_images_load_exact_nonoverlapping_segments_without_touching_original_ITCM_DTCM(self):
        for game in ('heartgold','soulsilver'):
            rom=ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds')
            injection=inject_evolution(rom.arm9,rom.arm9RamAddress,self.payload)
            verify_arm9_changes(rom.arm9,injection.image,rom.arm9RamAddress,injection.changes,self.payload)
            parsed=ndspy.code.MainCodeFile(injection.image,rom.arm9RamAddress)
            spans=[(s.ramAddress,s.ramAddress+len(s.data)+s.bssSize) for s in parsed.sections[1:]]
            for i,(start,end) in enumerate(spans):
                for a,b in spans[i+1:]:self.assertTrue(end<=a or b<=start)
            self.assertEqual(COLD_BASE,0x01FF8000+0x620)
            self.assertLessEqual(COLD_BASE+len(self.payload.cold_data),PAYLOAD_BASE)
            self.assertEqual(self.payload.total_size,len(self.payload.data)+len(self.payload.cold_data))

    def test_malformed_split_payload_is_rejected_before_injection(self):
        for cold in (b'',self.payload.cold_data+b'X',self.payload.cold_data+bytes(4)):
            symbols=dict(self.payload.symbols);symbols['__enhanced_cold_end']=COLD_BASE+len(cold)
            bad=replace(self.payload,cold_data=cold,symbols=symbols)
            with self.assertRaises(PatchMismatch):inject_evolution(self.rom.arm9,self.rom.arm9RamAddress,bad)
        for name,value in (('__enhanced_cold_end',PAYLOAD_BASE+4),('__enhanced_end',0x02000004)):
            symbols=dict(self.payload.symbols);symbols[name]=value
            with self.assertRaises(PatchMismatch):validate_payload_layout(replace(self.payload,symbols=symbols))

    def test_corrupted_misplaced_or_extra_BSS_segments_are_rejected(self):
        injection=inject_evolution(self.rom.arm9,self.rom.arm9RamAddress,self.payload)
        for mode in ('cold-bytes','cold-base','cold-bss','hot-bytes','extra-section','native-ITCM'):
            code=ndspy.code.MainCodeFile(injection.image,self.rom.arm9RamAddress)
            if mode=='cold-bytes':code.sections[3].data[0]^=1
            elif mode=='cold-base':code.sections[3].ramAddress-=4
            elif mode=='cold-bss':code.sections[3].bssSize=4
            elif mode=='hot-bytes':code.sections[4].data[-1]^=1
            elif mode=='extra-section':code.sections.append(ndspy.code.MainCodeFile.Section(bytes(4),0x023F0000,0))
            else:code.sections[1].data[0]^=1
            with self.assertRaises(PatchMismatch):verify_arm9_changes(self.rom.arm9,bytes(code.save(compress=False)),self.rom.arm9RamAddress,injection.changes,self.payload)

    def test_instruction_loader_installs_both_segments_preserves_native_prefix_and_bounds_reads(self):
        uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x01FF8000,0x8000)
        uc.mem_write(0x01FF8000,b'\xa5'*0x620)
        self.payload.install_into(uc)
        self.assertEqual(bytes(uc.mem_read(0x01FF8000,0x620)),b'\xa5'*0x620)
        for address,data in self.payload.segments:
            self.assertEqual(bytes(uc.mem_read(address,len(data))),data)
            self.assertEqual(self.payload.read(address,len(data)),data)
        for address,size in ((COLD_BASE-1,1),(0x02000000,4),(PAYLOAD_BASE-2,4),(COLD_BASE,-1)):
            with self.assertRaises(PatchMismatch):self.payload.read(address,size)
        for name,address in self.payload.symbols.items():
            if name.startswith('g') and name!='gItemPocketTable':
                self.assertGreaterEqual(address,PAYLOAD_BASE,name)
        self.assertLess(self.payload.symbols['gItemPocketTable'],PAYLOAD_BASE)

    def test_thumb_veneer_preserves_arguments_and_call_frame(self):
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x01FF8000, 0x8000)
        source, target, stop, stack = 0x02080000, 0x01FF9040, 0x02300000, 0x023FF000
        uc.mem_write(source, thumb_veneer(target | 1))
        uc.mem_write(target, bytes.fromhex('7047'))  # bx lr
        registers = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
        arguments = (0x11223344, 0x55667788, 0x99887766, 0xAABBCCDD)
        for register, value in zip(registers, arguments):
            uc.reg_write(register, value)
        uc.reg_write(UC_ARM_REG_SP, stack)
        uc.reg_write(UC_ARM_REG_LR, stop | 1)
        uc.emu_start(source | 1, stop, count=32)
        self.assertEqual(tuple(uc.reg_read(r) for r in registers), arguments)
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP), stack)
        self.assertEqual(uc.reg_read(UC_ARM_REG_LR), stop | 1)
        with self.assertRaises(PatchMismatch):
            thumb_veneer(target)


if __name__ == '__main__':
    unittest.main()

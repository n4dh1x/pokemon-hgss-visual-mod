"""Build and install a resident enhancement payload in reserved ARM9 ITCM.

The original image already autoloads 0x620 bytes at 0x01ff8000. The SDK's
ITCM arena starts immediately after that image. We add a distinct autoload
read-only section in the audited 0x01ff8620..0x01ff9000 gap and a code/state
section at 0x01ff9000, moving the arena start past the new code. Main-memory
heaps, existing overlays and the Visual+ code cave are left in place.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

import ndspy.code
from elftools.elf.elffile import ELFFile

from .patches import PatchMismatch, PatchResult

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD_BASE = 0x01FF9000
ITCM_END = 0x02000000
EVOLUTION_ADDRESS = 0x02070E34
EVOLUTION_CONTEXT_LENGTH = 0x41C
EVOLUTION_SHA256 = 'f71fa4e8a0f05b359f7642e33f42cb8a0efc81c73a703971cca6eeccfe626d48'
ITCM_ARENA_LITERAL = 0x020D2C68
ORIGINAL_ITCM_END = 0x01FF8620
COLD_BASE = ORIGINAL_ITCM_END


@dataclass
class Payload:
    data: bytes
    symbols: dict[str, int]
    compiler: str
    linker: str
    cold_data: bytes = b''

    @property
    def segments(self):
        return ((COLD_BASE, self.cold_data), (PAYLOAD_BASE, self.data))

    @property
    def total_size(self):
        return len(self.cold_data) + len(self.data)

    def read(self, address: int, size: int) -> bytes:
        for base, data in self.segments:
            if size >= 0 and base <= address <= base + len(data) - size:
                return data[address-base:address-base+size]
        raise PatchMismatch('Resident read crosses a payload boundary.')

    def install_into(self, emulator):
        validate_payload_layout(self)
        for base, data in self.segments:
            if data:
                emulator.mem_write(base, data)


@dataclass
class Injection:
    image: bytes
    changes: list[PatchResult]
    payload: Payload


def find_linker() -> str:
    explicit = os.environ.get('HGSS_LLD') or shutil.which('ld.lld') or shutil.which('rust-lld')
    if explicit:
        return explicit
    rustc = shutil.which('rustc')
    if rustc:
        sysroot = Path(subprocess.check_output([rustc, '--print', 'sysroot'], text=True).strip())
        for p in sorted((sysroot / 'lib/rustlib').glob('*/bin/rust-lld')):
            if p.is_file():
                return str(p)
    raise FileNotFoundError('Install LLD or set HGSS_LLD to an ARM-capable ld.lld/rust-lld.')


def build_payload(item_pockets: bytes | None = None) -> Payload:
    clang = os.environ.get('HGSS_CLANG') or shutil.which('clang')
    if not clang:
        raise FileNotFoundError('Install clang or set HGSS_CLANG.')
    linker = find_linker()
    linker_command = [linker, '-flavor', 'gnu'] if Path(linker).name in ('lld', 'rust-lld') else [linker]
    output = ROOT / 'build/native'
    output.mkdir(parents=True, exist_ok=True)
    if item_pockets is None:
        # Standalone instruction tests can compile without proprietary data.
        # Real ROM builds always supply their independently audited table.
        item_pockets = bytes([255])*269
        for game in ('heartgold', 'soulsilver'):
            baseline = ROOT / f'build/baseline/{game}-visual-plus-full-baseline.nds'
            if baseline.is_file():
                import ndspy.rom
                from .items import item_pocket_table
                item_pockets = item_pocket_table(ndspy.rom.NintendoDSRom.fromFile(baseline))
                break
    if len(item_pockets) != 269:
        raise PatchMismatch('Item pocket lookup must contain exactly 269 bytes.')
    flags = ['--target=arm-none-eabi', '-mcpu=arm946e-s', '-mthumb']
    with tempfile.TemporaryDirectory(prefix='.compile-', dir=output) as temporary:
        temp = Path(temporary)
        (temp / 'item_pockets.bin').write_bytes(item_pockets)
        objects = []
        for filename in ('evolution.c', 'evolution_trampoline.S', 'field.c', 'settings.c', 'ui.c', 'menu.c', 'repel.c', 'capture.c', 'party_exp.c', 'party_exp_divide.S', 'field_hms.c', 'field_hm_bag.c', 'summary_viewer.c', 'shiny.c', 'follower.c', 'clock.c', 'clock_hud.c', 'camera.c', 'cheats.c', 'victory.c', 'eggs.c', 'money.c', 'money_original.S', 'dex.c', 'dex_ui.c', 'items.c', 'items_data.S', 'quick_ball.c', 'events.c', 'overview.c'):
            target = temp / (filename + '.o')
            args = [clang, *flags, '-I', str(temp)]
            if filename.endswith('.c'):
                args += ['-ffreestanding', '-fno-builtin', '-fno-unwind-tables',
                         '-fno-asynchronous-unwind-tables', '-fno-stack-protector',
                         '-Oz', '-Wall', '-Wextra', '-Werror']
            subprocess.run([*args, '-c', str(ROOT / 'native' / filename), '-o', str(target)], check=True)
            objects.append(str(target))
        elf = temp / 'payload.elf'
        subprocess.run([*linker_command, '-T', str(ROOT / 'native/payload.ld'),
                        *objects, '-Map='+str(output/'payload.map'), '-o', str(elf)], check=True)
        with elf.open('rb') as source:
            parsed = ELFFile(source)
            if parsed['e_machine'] != 'EM_ARM':
                raise PatchMismatch('Compiler produced a non-ARM payload.')
            symbols = {s.name: int(s['st_value']) for s in parsed.get_section_by_name('.symtab').iter_symbols()}
            end = symbols['__enhanced_end']
            if not PAYLOAD_BASE < end <= ITCM_END or end % 4:
                raise PatchMismatch('Payload does not fit its reserved ITCM region.')
            cold_end = symbols['__enhanced_cold_end']
            if not COLD_BASE < cold_end <= PAYLOAD_BASE or cold_end % 4:
                raise PatchMismatch('Read-only payload exceeds the audited ITCM gap.')
            data = bytearray(end - PAYLOAD_BASE)
            cold_data = bytearray(cold_end - COLD_BASE)
            for section in parsed.iter_sections():
                if not section['sh_flags'] & 2 or not section['sh_size']:
                    continue
                address, size = section['sh_addr'], section['sh_size']
                if COLD_BASE <= address and address+size <= cold_end:
                    if section['sh_flags'] & 1 or section['sh_type'] == 'SHT_NOBITS':
                        raise PatchMismatch('Only immutable initialized data belongs in the ITCM gap.')
                    target, offset = cold_data, address-COLD_BASE
                elif PAYLOAD_BASE <= address and address+size <= end:
                    target, offset = data, address-PAYLOAD_BASE
                else:
                    raise PatchMismatch('Allocated ELF section falls outside the payload segments.')
                if section['sh_type'] != 'SHT_NOBITS':
                    target[offset:offset+size] = section.data()
        shutil.copy2(elf, output / 'payload.elf')
    if data[:16] != struct.pack('<4I', 0x48534745, 1, 1, 1):
        raise PatchMismatch('Resident options ABI does not match the injector.')
    if symbols['OriginalEvolution'] != 0x01FF9021:
        raise PatchMismatch('Original evolution trampoline moved.')
    if data[0x20:0x30] != bytes.fromhex('f0b591b00f1c009001920026381c0521'):
        raise PatchMismatch('Relocated evolution prologue differs from the original.')
    for name, expected in (('OriginalMoneyRead', '40697047'),
                           ('OriginalMoneySet', '034a914200d9111c4161081c7047c0463f420f00')):
        address = symbols[name] & ~1
        start = address - PAYLOAD_BASE
        if address % 4 or data[start:start + len(expected) // 2] != bytes.fromhex(expected):
            raise PatchMismatch('Original money routine relocation changed: ' + name)
    payload = Payload(bytes(data), symbols,
                      subprocess.check_output([clang, '--version'], text=True).splitlines()[0],
                      subprocess.check_output([*linker_command, '--version'], text=True).splitlines()[0],
                      bytes(cold_data))
    if payload.read(symbols['gItemPocketTable'],269) != item_pockets:
        raise PatchMismatch('Resident item pocket lookup differs from the audited ROM.')
    (output / 'payload.bin').write_bytes(data)
    (output / 'cold-rodata.bin').write_bytes(cold_data)
    return payload


def thumb_veneer(destination: int) -> bytes:
    """Absolute Thumb-1 tail branch preserving r0-r3, SP and LR."""
    if not destination & 1:
        raise PatchMismatch('The resident function must be a Thumb entry point.')
    return bytes.fromhex('08b4024b9c4608bc6047c046') + struct.pack('<I', destination)



def validate_payload_layout(payload: Payload) -> None:
    if (not payload.cold_data or len(payload.cold_data) % 4 or
            COLD_BASE + len(payload.cold_data) > PAYLOAD_BASE or
            payload.symbols.get('__enhanced_cold_end') != COLD_BASE + len(payload.cold_data)):
        raise PatchMismatch('Read-only payload is outside the audited ITCM gap.')
    if (not payload.data or len(payload.data) % 4 or
            PAYLOAD_BASE + len(payload.data) > ITCM_END or
            payload.symbols.get('__enhanced_end') != PAYLOAD_BASE + len(payload.data)):
        raise PatchMismatch('Mutable/code payload is outside the reserved ITCM region.')


def inject_evolution(arm9: bytes, ram_address: int, payload: Payload) -> Injection:
    validate_payload_layout(payload)
    code = ndspy.code.MainCodeFile(arm9, ram_address)
    if ram_address != 0x02000000 or code.codeSettingsOffs != 0xBA0 or len(code.sections) != 3:
        raise PatchMismatch('Unexpected USA ARM9/autoload layout.')
    first = code.sections[0]
    offset = EVOLUTION_ADDRESS - ram_address
    if hashlib.sha256(first.data[offset:offset + EVOLUTION_CONTEXT_LENGTH]).hexdigest() != EVOLUTION_SHA256:
        raise PatchMismatch('GetMonEvolution differs from the audited code.')
    arena_offset = ITCM_ARENA_LITERAL - ram_address
    if struct.unpack_from('<I', first.data, arena_offset)[0] != ORIGINAL_ITCM_END:
        raise PatchMismatch('SDK ITCM arena start differs from the audited value.')
    if [(s.ramAddress, len(s.data), s.bssSize) for s in code.sections[1:]] != [
            (0x01FF8000, 0x620, 0), (0x027E0000, 0x60, 0x20)]:
        raise PatchMismatch('Existing resident sections differ from the audited layout.')
    end = PAYLOAD_BASE + len(payload.data)
    if not PAYLOAD_BASE < end <= ITCM_END or end % 4:
        raise PatchMismatch('Invalid resident payload size.')
    veneer = thumb_veneer(payload.symbols['EnhancedEvolution'])
    prologue = bytes(first.data[offset:offset + 16])
    first.data[offset:offset + 16] = veneer
    struct.pack_into('<I', first.data, arena_offset, end)
    for address, data in payload.segments:
        code.sections.append(ndspy.code.MainCodeFile.Section(data, address, 0))
    image = bytes(code.save(compress=False))
    check = ndspy.code.MainCodeFile(image, ram_address)
    if len(check.sections) != 5:
        raise PatchMismatch('Resident section count did not survive serialization.')
    for section, (address, data) in zip(check.sections[3:], payload.segments):
        if section.ramAddress != address or section.bssSize or bytes(section.data) != data:
            raise PatchMismatch('Resident segment did not survive serialization.')
    for old, new in zip(code.sections[1:3], check.sections[1:3]):
        if old.ramAddress != new.ramAddress or old.bssSize != new.bssSize or old.data != new.data:
            raise PatchMismatch('An existing resident section changed during injection.')
    return Injection(image, [
        PatchResult('trade_evo', EVOLUTION_ADDRESS, prologue.hex(), veneer.hex(),
                    'Optional level-40 trade alternatives; native trading and completion retained'),
        PatchResult('resident_code_reservation', ITCM_ARENA_LITERAL,
                    struct.pack('<I', ORIGINAL_ITCM_END).hex(), struct.pack('<I', end).hex(),
                    'Reserve enhancement code outside the SDK ITCM arena')], payload)


def verify_arm9_changes(original_image: bytes, patched_image: bytes, ram_address: int,
                       changes: list[PatchResult], payload: Payload) -> None:
    validate_payload_layout(payload)
    before = ndspy.code.MainCodeFile(original_image, ram_address)
    after = ndspy.code.MainCodeFile(patched_image, ram_address)
    if len(before.sections) != 3 or len(after.sections) != 5:
        raise PatchMismatch('Unexpected section count after gameplay patching.')
    expected = bytearray(before.sections[0].data)
    for change in changes:
        start = change.address - ram_address
        old, new = bytes.fromhex(change.before), bytes.fromhex(change.after)
        if start < 0 or expected[start:start + len(old)] != old or len(old) != len(new):
            raise PatchMismatch('The recorded patch operations do not match the baseline.')
        expected[start:start + len(old)] = new
    table = ram_address + len(expected) + sum(len(s.data) for s in after.sections[1:])
    struct.pack_into('<3I', expected, before.codeSettingsOffs,
                     table, table + 12 * (len(after.sections) - 1), ram_address + len(expected))
    if bytes(expected) != bytes(after.sections[0].data):
        raise PatchMismatch('Unrecorded changes in the original ARM9 section.')
    for old, new in zip(before.sections[1:], after.sections[1:3]):
        if (old.ramAddress, old.bssSize, old.data) != (new.ramAddress, new.bssSize, new.data):
            raise PatchMismatch('Original ITCM/DTCM sections changed.')
    for resident, (address, data) in zip(after.sections[3:], payload.segments):
        if resident.ramAddress != address or resident.bssSize or bytes(resident.data) != data:
            raise PatchMismatch('Enhanced resident segment differs from its compiled payload.')

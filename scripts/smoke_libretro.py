#!/usr/bin/env python3
"""Run the user's local melonDS libretro core in an isolated software test host.

Captures DS video and a machine-readable run record. A successful run is a
boot/smoke check, not verification of every gameplay mechanic. Firmware, saves,
states and screenshots stay in ignored local_data/verification/ directories.
"""
from __future__ import annotations

import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import struct
import time
import zlib

ROOT = Path(__file__).resolve().parent.parent
BUTTONS = {'B': 0, 'Y': 1, 'SELECT': 2, 'START': 3, 'UP': 4, 'DOWN': 5,
           'LEFT': 6, 'RIGHT': 7, 'A': 8, 'X': 9, 'L': 10, 'R': 11}


class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]


class SystemInfo(C.Structure):
    _fields_ = [('library_name', C.c_char_p), ('library_version', C.c_char_p),
                ('valid_extensions', C.c_char_p), ('need_fullpath', C.c_bool),
                ('block_extract', C.c_bool)]


class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]


def png(path: Path, width: int, height: int, pitch: int, pixels: bytes, format: int):
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0)
        row = pixels[y * pitch:(y + 1) * pitch]
        for x in range(width):
            if format == 1:  # XRGB8888
                b, g, r = row[x * 4:x * 4 + 3]
            else:
                value = struct.unpack_from('<H', row, x * 2)[0]
                if format == 2:  # RGB565
                    r, g, b = ((value >> 11) & 31) * 255 // 31, ((value >> 5) & 63) * 255 // 63, (value & 31) * 255 // 31
                else:  # 0RGB1555
                    r, g, b = ((value >> 10) & 31) * 255 // 31, ((value >> 5) & 31) * 255 // 31, (value & 31) * 255 // 31
            scanlines.extend((r, g, b))

    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xFFFFFFFF)

    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b''))


def run(core_path: Path, rom: Path, output: Path, frames: int, presses: list[tuple], captures: set[int], load_state: Path | None = None):
    core_path, rom, output = core_path.resolve(), rom.resolve(), output.resolve()
    load_state = load_state.resolve() if load_state else None
    output.mkdir(parents=True, exist_ok=True)
    for name in ('system', 'save'):
        (output / name).mkdir(exist_ok=True)
    core = C.CDLL(str(core_path))
    held = []
    defaults, choices, unknown = {}, {}, set()
    overrides = {'melonds_render_mode': 'software', 'melonds_console_mode': 'ds',
                 'melonds_boot_mode': 'direct', 'melonds_sysfile_mode': 'builtin',
                 'melonds_jit_enable': 'disabled', 'melonds_network_mode': 'disabled',
                 'melonds_start_time_mode': 'absolute'}
    frame, video_format, last_video, audio_samples = 0, 0, None, 0
    errors = []

    def set_string(data, value):
        buffer = C.create_string_buffer(os.fsencode(value))
        held.append(buffer)
        C.cast(data, C.POINTER(C.c_char_p))[0] = C.cast(buffer, C.c_char_p)

    @C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
    def environment(command, data):
        nonlocal video_format
        try:
            if command in (9, 30, 31):
                set_string(data, output / ('system' if command == 9 else 'save'))
                return True
            if command == 10:
                video_format = C.cast(data, C.POINTER(C.c_int))[0]
                return video_format in (0, 1, 2)
            if command == 16:
                entries = C.cast(data, C.POINTER(Variable))
                for i in range(512):
                    if not entries[i].key:
                        break
                    key = entries[i].key.decode()
                    description = entries[i].value.decode()
                    values = description.split(';', 1)[1].strip().split('|')
                    defaults[key], choices[key] = values[0], values
                return True
            if command == 15:
                var = C.cast(data, C.POINTER(Variable))
                key = var[0].key.decode()
                value = overrides.get(key, defaults.get(key))
                if key in choices and value not in choices[key]:
                    value = defaults[key]
                if value is None:
                    return False
                buffer = C.create_string_buffer(value.encode())
                held.append(buffer)
                var[0].value = C.cast(buffer, C.c_char_p)
                return True
            if command in (3, 17, 50 | 0x10000):
                C.cast(data, C.POINTER(C.c_bool))[0] = command != 17
                return True
            if command in (39, 52, 59):
                C.cast(data, C.POINTER(C.c_uint))[0] = 0
                return True
            if command == (47 | 0x10000):
                C.cast(data, C.POINTER(C.c_int))[0] = 3
                return True
            if command == (51 | 0x10000):
                return True
            if command in (1, 6, 8, 11, 12, 18, 35, 36, 37, 44, 45, 62, 64):
                return True
            if command == 38:
                set_string(data, 'HGSS TEST')
                return True
            unknown.add(command)
            return False
        except Exception as exc:
            errors.append(str(exc))
            return False

    @C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    def video(data, width, height, pitch):
        nonlocal last_video
        if data and data != C.c_void_p(-1).value and (frame in captures or frame == frames):
            last_video = (width, height, pitch, C.string_at(data, pitch * height))
            png(output / f'frame-{frame:06d}.png', width, height, pitch, last_video[3], video_format)

    @C.CFUNCTYPE(None, C.c_int16, C.c_int16)
    def audio_sample(left, right):
        pass

    @C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
    def audio_batch(data, count):
        nonlocal audio_samples
        audio_samples += count
        return count

    @C.CFUNCTYPE(None)
    def poll():
        pass

    @C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
    def input_state(port, device, index, id):
        if port or device != 1:
            return 0
        down = {BUTTONS[button] for button, start, end in presses if start <= frame < end}
        if id == 256:
            return sum(1 << bit for bit in down)
        return int(id in down)

    for name, callback in [('environment', environment), ('video_refresh', video),
                            ('audio_sample', audio_sample), ('audio_sample_batch', audio_batch),
                            ('input_poll', poll), ('input_state', input_state)]:
        function = getattr(core, 'retro_set_' + name)
        function.argtypes = [type(callback)]
        function(callback)
    core.retro_get_system_info.argtypes = [C.POINTER(SystemInfo)]
    info = SystemInfo()
    core.retro_get_system_info(C.byref(info))
    core.retro_load_game.argtypes = [C.POINTER(GameInfo)]
    core.retro_load_game.restype = C.c_bool
    core.retro_get_memory_size.argtypes = [C.c_uint]
    core.retro_get_memory_size.restype = C.c_size_t
    core.retro_get_memory_data.argtypes = [C.c_uint]
    core.retro_get_memory_data.restype = C.c_void_p
    core.retro_serialize_size.restype = C.c_size_t
    core.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]
    core.retro_serialize.restype = C.c_bool
    core.retro_unserialize.argtypes = [C.c_void_p, C.c_size_t]
    core.retro_unserialize.restype = C.c_bool
    path = os.fsencode(rom)
    data = None if info.need_fullpath else C.create_string_buffer(rom.read_bytes())
    game = GameInfo(path, C.cast(data, C.c_void_p) if data is not None else None,
                    len(data) - 1 if data is not None else 0, None)
    started = time.monotonic()
    old_cwd = Path.cwd()
    loaded = False
    try:
        os.chdir(output)
        core.retro_init()
        if not core.retro_load_game(C.byref(game)):
            raise RuntimeError(f'melonDS could not load the ROM; options: {defaults}')
        loaded = True
        (output / 'core-options.json').write_text(json.dumps({'defaults': defaults, 'choices': choices}, indent=2))
        rom_sha = hashlib.sha256(rom.read_bytes()).hexdigest()
        if load_state:
            load_state = load_state.resolve()
            metadata = json.loads(load_state.with_suffix('.json').read_text())
            if metadata['rom_sha256'] != rom_sha:
                raise RuntimeError('Refusing to load a savestate from a different ROM.')
            state = C.create_string_buffer(load_state.read_bytes())
            if not core.retro_unserialize(state, len(state) - 1):
                raise RuntimeError('melonDS rejected the supplied savestate.')
        for frame in range(1, frames + 1):
            core.retro_run()
        ram_size = core.retro_get_memory_size(2)
        ram = core.retro_get_memory_data(2)
        if ram and ram_size:
            (output / 'main-ram.bin').write_bytes(C.string_at(ram, ram_size))
        if errors:
            raise RuntimeError('; '.join(errors))
        if last_video is None:
            raise RuntimeError('No software video frame was captured.')
        state_size = core.retro_serialize_size()
        if state_size:
            state = C.create_string_buffer(state_size)
            if core.retro_serialize(state, state_size):
                (output / 'state.bin').write_bytes(state.raw)
                (output / 'state.json').write_text(json.dumps({'rom_sha256': rom_sha,
                                                             'core_version': info.library_version.decode()}))
        report = {'core': info.library_name.decode(), 'version': info.library_version.decode(),
                  'rom': rom.name, 'frames': frames, 'audio_samples': audio_samples,
                  'elapsed_seconds': round(time.monotonic() - started, 2),
                  'video_format': video_format, 'last_frame_dimensions': list(last_video[:2]),
                  'last_frame_sha256': hashlib.sha256(last_video[3]).hexdigest(),
                  'effective_options': {k: overrides.get(k, v) if overrides.get(k, v) in choices[k] else v for k, v in defaults.items()},
                  'unsupported_environment_commands': sorted(unknown),
                  'scope': 'Boot/smoke check only; not full gameplay verification.'}
        (output / 'smoke-report.json').write_text(json.dumps(report, indent=2) + '\n')
        return report
    finally:
        if loaded:
            core.retro_unload_game()
        core.retro_deinit()
        os.chdir(old_cwd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, default=Path.home() / 'Library/Application Support/RetroArch/cores/melondsds_libretro.dylib')
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, default=600)
    parser.add_argument('--capture', type=int, action='append', default=[])
    parser.add_argument('--load-state', type=Path)
    parser.add_argument('--press', action='append', default=[], help='BUTTON:START_FRAME:END_FRAME')
    args = parser.parse_args()
    if args.frames < 1:
        parser.error('--frames must be positive')
    presses = []
    for event in args.press:
        button, start, end = event.split(':')
        if button not in BUTTONS or int(start) < 1 or int(end) <= int(start):
            parser.error(f'Invalid button interval: {event}')
        presses.append((button, int(start), int(end)))
    print(json.dumps(run(args.core, args.rom, args.output, args.frames, presses,
                         set(args.capture) | {args.frames}, args.load_state), indent=2))


if __name__ == '__main__':
    main()

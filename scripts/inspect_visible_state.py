#!/usr/bin/env python3
"""Read bounded visible-encounter diagnostics from a local melonDS test run.

This inspects saved data, not a running emulator. ROM hash, resident config
uniqueness and pointer bounds are checked before interpreting memory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inspect_run(run: Path, report_path: Path) -> dict:
    report = json.loads(report_path.read_text())
    metadata = json.loads((run / 'state.json').read_text())
    if metadata['rom_sha256'] != report['output_sha256']:
        raise ValueError('Savestate and candidate report name different ROM hashes.')
    ram = (run / 'main-ram.bin').read_bytes()
    state = (run / 'state.bin').read_bytes()
    if len(ram) != 0x400000 or state[:4] != b'MELN':
        raise ValueError('Expected a 4 MiB main RAM dump and MELN savestate.')
    config = struct.pack('<2I', 0x48534745, 1)
    if state.count(config) != 1:
        raise ValueError('Resident config does not have a unique state location.')
    base = state.index(config)
    symbols = report['resident_payload']['symbols']
    payload_address = report['resident_payload']['address']
    start = base + symbols['gVisibleState'] - payload_address
    if start < base or start + 1592 > base + report['resident_payload']['size']:
        raise ValueError('Visible state lies outside the recorded resident section.')
    header = struct.unpack_from('<8I', state, start)

    def read(address, size):
        offset = address - 0x02000000
        if offset < 0 or offset + size > len(ram):
            raise ValueError(f'RAM pointer outside main memory: {address:#x}.')
        return ram[offset:offset + size]

    def word(address):
        return struct.unpack('<I', read(address, 4))[0]

    result = {'candidate_sha256': report['output_sha256'],
              'visible_mode': struct.unpack_from('<I', state, base + 16)[0],
              'manager': hex(header[0]), 'capture_active': bool(header[1]),
              'tick': header[3], 'generated': header[4], 'launched': header[5],
              'save_filtered': header[6], 'allocation_failures': header[7], 'slots': []}
    retained = []
    for index in range(6):
        offset = start + 32 + 260 * index
        address, id, map_id = struct.unpack_from('<3I', state, offset)
        mon = state[offset + 12:offset + 248]
        species, level, pid = struct.unpack_from('<3I', state, offset + 248)
        retained.append(mon)
        entry = {'index': index, 'object': hex(address), 'id': id, 'map': map_id,
                 'species': species, 'level': level, 'personality': pid,
                 'pokemon_sha256': hashlib.sha256(mon).hexdigest(), 'owned_active': False}
        if address:
            flags = word(address)
            entry['owned_active'] = bool(flags & 1 and word(address + 8) == id and word(address + 0xB4) == header[0])
            entry['flags'] = hex(flags)
            entry['position'] = list(struct.unpack('<3i', read(address + 0x64, 12)))
            entry['vector'] = list(struct.unpack('<3i', read(address + 0x70, 12)))
            entry['movement'] = list(struct.unpack('<2I', read(address + 0xA4, 8)))
        result['slots'].append(entry)
    if 'EnhancedFieldControl' in symbols:
        if start + 1624 > base + report['resident_payload']['size']:
            raise ValueError('Roaming state lies outside the resident payload.')
        result['walk_commands'], result['paused_mask'] = struct.unpack_from('<2I', state, start + 1616)
    # Audited USA sFieldSysPtr. The field task chain identifies an actual native
    # battle setup, avoiding a broad memory-pattern match as identity evidence.
    field = word(0x021D4158)
    if field:
        avatar = word(field + 0x40)
        if avatar:
            player = word(avatar + 0x30)
            if player:
                result['player_position'] = list(struct.unpack('<3i', read(player + 0x64, 12)))
        task = word(field + 0x10)
        visited = set()
        while task and task not in visited and len(visited) < 16:
            visited.add(task)
            previous, function, phase, environment = struct.unpack('<4I', read(task, 16))
            if function == 0x02050661:  # Task_StartBattle's environment is BattleSetup
                party = word(environment + 8)
                count = word(party + 4)
                if not 1 <= count <= 6:
                    raise ValueError('Battle enemy party has an invalid count.')
                mon = read(party + 8, 236)
                result['native_battle'] = {'setup': hex(environment), 'enemy_party': hex(party),
                    'pokemon_sha256': hashlib.sha256(mon).hexdigest(),
                    'identical_retained_slots': [i for i, candidate in enumerate(retained) if candidate == mon]}
                break
            task = previous
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_run(args.run, args.report), indent=2))


if __name__ == '__main__':
    main()

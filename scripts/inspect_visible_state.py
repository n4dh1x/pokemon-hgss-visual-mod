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
    def resident_words(name, count):
        offset = base + symbols[name] - payload_address
        if offset < base or offset + count * 4 > base + report['resident_payload']['size']:
            raise ValueError(f'{name} lies outside the recorded resident section.')
        return struct.unpack_from(f'<{count}I', state, offset)

    if 'gSettingsState' in symbols:
        settings = resident_words('gSettingsState', 9)
        result['settings'] = {'loaded': bool(settings[2]), 'sequence': settings[3],
            'last_slot': settings[4] if settings[4] < 2 else -1,
            'writable_slots': [bool(v) for v in settings[5:7]],
            'successful_writes': settings[7], 'status': settings[8],
            'trade_evolutions': struct.unpack_from('<I', state, base + 8)[0],
            'reusable_tms': struct.unpack_from('<I', state, base + 12)[0]}
    if 'gEnhancedMenu' in symbols:
        menu_size = report.get('diagnostics', {}).get('menu_state_bytes', 60)
        extended_menu = menu_size >= 64
        menu = resident_words('gEnhancedMenu', menu_size // 4)
        result['enhancement_menu'] = {'active': bool(menu[6]), 'phase': menu[7],
            'row': menu[8], 'staged_trade': menu[9], 'staged_tms': menu[10],
            'staged_visible': menu[11], 'error': menu[(menu_size // 4) - 3]}
        if extended_menu:
            result['enhancement_menu']['staged_repel_prompt'] = menu[12]
            result['settings']['repel_prompt'] = struct.unpack_from('<I', state, base + 20)[0]
    if 'gCaptureExperience' in symbols:
        result['enhancement_menu']['staged_capture_exp'] = menu[13]
        result['settings']['capture_exp'] = struct.unpack_from('<I', state, base + 24)[0]
        capture = resident_words('gCaptureExperience', 14)
        result['capture_exp'] = dict(zip(('parent','context','phase','completed_once','saved_fainted','saved_gained','saved_shared','saved_earn0','saved_earn1','started','completed','failures','skipped','last_enemy'), capture))
    if 'gPartyExperience' in symbols:
        result['enhancement_menu']['staged_party_exp'] = menu[14]
        result['settings']['party_exp'] = struct.unpack_from('<I', state, base + 28)[0]
        party = resident_words('gPartyExperience', 17)
        result['party_exp'] = dict(zip(('work','context','active','participants','full','half','side','slot','bench','shown','printer','started','completed','groups','suppressed','recipients','calculations'), party))
    if 'gEnhancedExtraOptions' in symbols:
        extra_count = report.get('diagnostics', {}).get('extra_options_bytes', 12 if menu_size >= 88 else 8) // 4
        extra = resident_words('gEnhancedExtraOptions', extra_count)
        result['settings']['field_hms'] = extra[0]
        result['settings']['roaming_only_grass'] = extra[1]
        result['enhancement_menu']['staged_field_hms'] = menu[15]
        result['enhancement_menu']['staged_roaming_only_grass'] = menu[16]
        result['enhancement_menu']['page'] = menu[15 + extra_count]
        if menu_size >= 88:
            result['settings']['iv_ev_viewer'] = extra[2]
            result['enhancement_menu']['staged_iv_ev_viewer'] = menu[17]
        hm = resident_words('gFieldHmState', 9)
        result['field_hms'] = dict(zip(('scripts','checks','fallbacks','no_user','last_move','last_slot','compatible','disabled','cache_hits'), hm))
    if 'gEncounterRateState' in symbols:
        result['settings']['encounter_rate'] = extra[3]
        result['enhancement_menu']['staged_encounter_rate'] = menu[18]
        result['encounter_rate'] = dict(zip(('field','roamer','cached','native_rolls','scaled_rolls','roamer_preserved','off_blocks'), resident_words('gEncounterRateState', 7)))
    if 'gVisibleVisualState' in symbols:
        values = resident_words('gVisibleVisualState', 14 if report['diagnostics']['visible_visual_state_bytes'] == 56 else 13)
        result['visible_visuals'] = dict(zip(('pending_slot','pending_sprite','owned_lookups','construction_lookups','native_lookups','sparkles','sparkle_failures'), values[:7]))
        result['visible_visuals']['sparkle_ticks'] = list(values[7:13])
        result['visible_visuals']['chimes'] = values[13] if len(values) > 13 else 0
    if 'gVisibleHabitatState' in symbols:
        habitats = resident_words('gVisibleHabitatState', 11)
        result['habitats'] = {'slots': list(habitats[:6]), 'spawned': list(habitats[6:10]), 'surface_releases': habitats[10]}
    if 'gVisibleRoamerState' in symbols:
        r = resident_words('gVisibleRoamerState', 48)
        result['visible_roamers'] = dict(zip(('capture_slot','candidate','selected','duplicates','stale','launched'),r[:6]))
        result['visible_roamers']['slots'] = []
        for i in range(6):
            at=6+i*7
            result['visible_roamers']['slots'].append({'identity':r[at],'record':list(r[at+1:at+6]),'battle_type':r[at+6]})
    if 'gFollowerState' in symbols:
        result['follower'] = dict(zip(('field','manager','known','hidden','removed','restored','blocked'),resident_words('gFollowerState',7)))
        result['settings']['hide_follower'] = extra[5]
        result['enhancement_menu']['staged_hide_follower'] = menu[20]
    if 'gShinyState' in symbols:
        result['settings']['shiny_odds'] = extra[4]
        result['enhancement_menu']['staged_shiny_odds'] = menu[19]
        result['shiny'] = dict(zip(('calls','rolls','candidates','changes','failures','original_pid','selected_pid','owner','species','kind'), resident_words('gShinyState', 10)))
    if 'gSummaryViewState' in symbols:
        summary = resident_words('gSummaryViewState', 13)
        result['summary_view'] = dict(zip(('summary','pokemon','mode','draws','switches','data_type','reads'), summary[:7]))
        result['summary_view']['values'] = list(summary[7:])
    if 'gFieldBagState' in symbols:
        result['field_bag'] = dict(zip(('field','save','item','active','slot','offered','accepted','cancelled','blocked','launched','response'), resident_words('gFieldBagState', 11)))
    if 'gEnhancedRepelDialog' in symbols:
        dialog = resident_words('gEnhancedRepelDialog', 17)
        result['repel_dialog'] = {'active': bool(dialog[6]), 'phase': dialog[7],
            'choice': dialog[8], 'item': dialog[9], 'offered': dialog[12],
            'accepted': dialog[13], 'declined': dialog[14], 'failures': dialog[15],
            'remembered': dialog[16]}
    if 'follower' in result:
        field = word(0x021D4158)
        if 0x02000000 <= field <= 0x023FFF00:
            native = read(field + 0xE4, 28)
            follower = result['follower']
            follower['native_active'] = bool(native[0x16])
            follower['native_pending'] = native[0x15]
            follower['species'] = struct.unpack_from('<I', native, 0x10)[0]
            follower['gender'] = native[0x14]
            follower['shiny'] = bool(native[0x17])
            follower['form'] = struct.unpack_from('<H', native, 0x18)[0]
            address = struct.unpack_from('<I', native)[0]
            follower['native_object'] = hex(address)
            if follower['native_active'] and 0x02000000 <= address <= 0x023FFED4:
                follower['object'] = {'flags': word(address), 'id': word(address + 8),
                    'sprite': word(address + 0x10), 'manager': hex(word(address + 0xB4)),
                    'position': list(struct.unpack('<3i', read(address + 0x64, 12))),
                    'parameters': list(struct.unpack('<3I', read(address + 0x38, 12)))}
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
            entry['object_map'] = word(address + 0x0C)
            entry['owned_active'] = bool(flags & 1 and word(address + 8) == id and word(address + 0xB4) == header[0] and entry['object_map'] == map_id)
            entry['flags'] = hex(flags)
            entry['position'] = list(struct.unpack('<3i', read(address + 0x64, 12)))
            entry['vector'] = list(struct.unpack('<3i', read(address + 0x70, 12)))
            entry['movement'] = list(struct.unpack('<2I', read(address + 0xA4, 8)))
        result['slots'].append(entry)
    if 'EnhancedFieldControl' in symbols:
        if start + 1632 > base + report['resident_payload']['size']:
            raise ValueError('Roaming state lies outside the resident payload.')
        result['walk_commands'], result['paused_mask'] = struct.unpack_from('<2I', state, start + 1616)
        result['discarded_ordinary'] = struct.unpack_from('<I', state, start + 1628)[0]
    if report.get('diagnostics', {}).get('visible_state_bytes') >= 1640:
        if start + 1640 > base + report['resident_payload']['size']:
            raise ValueError('Contact diagnostics lie outside the resident payload.')
        result['repelled_contacts'], result['map_releases'] = struct.unpack_from('<2I', state, start + 1632)
    if report.get('diagnostics', {}).get('visible_state_bytes', 0) >= 1644:
        if start + 1644 > base + report['resident_payload']['size']:
            raise ValueError('Grass diagnostics lie outside the resident payload.')
        result['blocked_grass_steps'] = struct.unpack_from('<I', state, start + 1640)[0]
    # Audited USA sFieldSysPtr. The field task chain identifies an actual native
    # battle setup, avoiding a broad memory-pattern match as identity evidence.
    field = word(0x021D4158)
    if field:
        location = word(field + 0x20)
        if location:
            result['current_map'] = word(location)
        avatar = word(field + 0x40)
        if avatar:
            result['avatar_state'] = word(avatar + 0x18)
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
                result['native_battle'] = {'setup': hex(environment), 'battle_type': word(environment), 'enemy_party': hex(party),
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

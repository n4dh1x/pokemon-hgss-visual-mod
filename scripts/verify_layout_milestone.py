#!/usr/bin/env python3
"""Assert milestone-29 split-loader acceptance from immutable local runs.

Reads ROM-matched snapshots and invokes bounded original getters on private RAM
copies. No emulator, cartridge save or accepted checkpoint is modified.
"""
from pathlib import Path
import hashlib
import json
import struct

import ndspy.code
import ndspy.rom
from inspect_visible_state import inspect_run
from inspect_wallet_state import inspect_wallet
from inspect_egg_state import inspect_eggs
from inspect_dex_state import inspect_dex

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / 'local_data/verification'
C = ROOT / 'build/candidates'
E = ROOT / 'build/experiments/layout-29a'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def asset(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def decoded(party):
    return [{k: v for k, v in mon.items() if k != 'pokemon_sha256'} for mon in party['party']]


def verify():
    logs = {}
    for name, count in [('full', 298), ('loader', 9), ('items', 12), ('settings', 47)]:
        path = ROOT / f'local_data/milestone-29-{name}-tests.log'
        body = path.read_text()
        assert f'Ran {count} tests' in body and body.rstrip().endswith('OK'), name
        logs[name] = {'passed': count, 'log': asset(path)}
    path = ROOT / 'local_data/milestone-29-inventory-audit.log'
    assert 'OK: 59 feature rows; 41 option keys covered.' in path.read_text()
    logs['inventory'] = {'rows': 59, 'emerald_keys': 41, 'log': asset(path)}
    output = {'kind': 'bounded-local-gameplay-verification', 'milestone': 29,
              'verified_on': '2026-11-06', 'final_release': False,
              'scope': 'Split immutable-table/code loader: exact original ITCM/DTCM, live immutable bytes and arena reservation; previous native saves, all saved preferences, item lookup/giving/duplicate keys, normal Save/cold, camera/clock options, visible contact identity and native victory/party rewards/save/cold in both games.',
              'regression': logs, 'candidates': {}, 'games': {}}
    for tag, game in [('hg', 'heartgold'), ('ss', 'soulsilver')]:
        stem = f'{game}-visual-plus-gameplay-milestone-29'
        report_path = C / (stem + '.json')
        report = load(report_path)
        rom_path = report_path.with_suffix('.nds')
        for ext in ('.nds', '.xdelta'):
            assert (C / (stem + ext)).read_bytes() == (E / (stem + ext)).read_bytes()
        assert sha(rom_path) == report['output_sha256']
        assert sha(report_path.with_suffix('.xdelta')) == report['patch_sha256']
        payload = report['resident_payload']
        assert (payload['address'], payload['size'], payload['total_size']) == (0x01FF9000, 25484, 28012)
        assert (payload['immutable_data']['address'], payload['immutable_data']['size']) == (0x01FF8620, 2528)
        end = payload['symbols']['__enhanced_end']
        assert end == 0x01FFF38C and 0x02000000-end == 3188
        rom = ndspy.rom.NintendoDSRom.fromFile(rom_path)
        baseline = ndspy.rom.NintendoDSRom.fromFile(ROOT / f'build/baseline/{game}-visual-plus-full-baseline.nds')
        sections = ndspy.code.MainCodeFile(rom.arm9, rom.arm9RamAddress).sections
        originals = ndspy.code.MainCodeFile(baseline.arm9, baseline.arm9RamAddress).sections
        assert len(sections) == 5 and len(originals) == 3
        for before, after in zip(originals[1:], sections[1:3]):
            assert (before.ramAddress, before.bssSize, bytes(before.data)) == (after.ramAddress, after.bssSize, bytes(after.data))
        for section, metadata in zip(sections[3:], (payload['immutable_data'], payload)):
            assert section.ramAddress == metadata['address'] and not section.bssSize
            assert len(section.data) == metadata['size']
            assert hashlib.sha256(section.data).hexdigest() == metadata['sha256']
        output['candidates'][game] = {'local_rom': str(rom_path.relative_to(ROOT)),
            'output_sha256': sha(rom_path), 'patch_sha256': report['patch_sha256'], 'report': asset(report_path),
            'payload': {k: payload[k] for k in ('address', 'size', 'total_size', 'immutable_data')},
            'payload_end': hex(end), 'remaining_ITCM_bytes': 3188, 'additional_code_capacity_bytes': 2528,
            'original_resident_sections_unchanged': True, 'reproduced_tested_experiment': True,
            'checks': report['checks']}
        parents = {'field': None, 'picker': 'field', 'duplicate': 'picker', 'give': 'duplicate',
            'prefs-save': 'give', 'native-save': 'prefs-save', 'cold': None, 'view': 'field',
            'route': 'field', 'grass': 'route', 'reward': 'battle' if tag == 'hg' else 'grass',
            'reward-save': 'reward', 'reward-cold': None}
        if tag == 'hg':
            parents['battle'] = 'grass'
        cases, diagnostics, wallets, parties, dexes = {}, {}, {}, {}, {}
        for name, parent in parents.items():
            path = V / (tag + '29a-' + name)
            smoke = load(path / 'smoke-report.json')
            assert smoke['developer_ram_fixture'] is None
            log = ROOT / f'local_data/{tag}29a-{name}.log'
            text = log.read_text().lower()
            assert 'data abort' not in text and 'prefetch abort' not in text
            state, ram = (path / 'state.bin').read_bytes(), (path / 'main-ram.bin').read_bytes()
            config = struct.pack('<2I', 0x48534745, 1)
            assert state.count(config) == 1
            base = state.index(config)
            cold_at = base + 0x01FF8620 - 0x01FF9000
            assert state[cold_at:base] == bytes(sections[3].data)
            assert state[base-0x1000:base-0x1000+0x620] == bytes(originals[1].data)
            assert struct.unpack_from('<I', ram, 0x3FFDAC)[0] == end
            d = inspect_run(path, report_path)
            diagnostics[name] = d
            case = {'local_run': str(path.relative_to(ROOT)), 'state': asset(path / 'state.bin'),
                'main_ram': asset(path / 'main-ram.bin'), 'smoke_report': asset(path / 'smoke-report.json'),
                'core_log': asset(log), 'frames': smoke['frames'], 'inputs': smoke['inputs'],
                'developer_ram_fixture': None, 'original_ITCM_and_immutable_data_exact_in_state': True,
                'runtime_ITCM_arena_low': hex(end), 'settings': d['settings'], 'menu': d['enhancement_menu'],
                'item_giver': d['item_giver']}
            if parent:
                case['loaded_state'] = asset(V / (tag + '29a-' + parent) / 'state.bin')
            else:
                src = V / (tag + ('28b-used-save' if name == 'field' else '29a-' + ('native-save' if name == 'cold' else 'reward-save'))) / 'cartridge.sav'
                assert smoke['save_import_sha256'] == sha(src)
                case['loaded_native_save'] = asset(src)
            if d['enhancement_menu']['active'] and not d.get('native_battle'):
                w = inspect_wallet(path, report_path, rom_path)
                p = inspect_eggs(path, report_path, rom_path)
                x = inspect_dex(path, report_path, rom_path)
                wallets[name], parties[name], dexes[name] = w, p, x
                case.update(wallet_and_inventory=w, party=p,
                    dex_and_story={k: x[k] for k in ('national_seen', 'national_caught', 'dex_sha256', 'profile_sha256', 'story_vars_flags_sha256')})
            if d.get('native_battle'):
                assert d['native_battle']['identical_retained_slots']
                case['native_battle'] = d['native_battle']
                case['visible_slots'] = d['slots']
            if name in ('reward', 'reward-save', 'reward-cold'):
                case.update(instant_victory=d['instant_victory'], party_exp=d['party_exp'])
            if name == 'view':
                case.update(camera=d['camera'], clock=d['clock'], clock_hud=d['clock_hud'])
            cases[name] = case
        old_report = ROOT / 'build/candidates' / f'{game}-visual-plus-gameplay-milestone-28.json'
        old_run = V / (tag + '28b-used-save')
        old = inspect_run(old_run, old_report)
        metadata = {'loaded', 'sequence', 'last_slot', 'writable_slots', 'successful_writes', 'status'}
        prefs = ('give_pocket', 'give_item', 'give_count')
        for key, value in old['settings'].items():
            if key not in metadata:
                assert diagnostics['field']['settings'][key] == value, key
        assert diagnostics['field']['visible_mode'] == old['visible_mode']
        old_party = inspect_eggs(old_run, old_report, old_report.with_suffix('.nds'))
        assert decoded(parties['field']) == decoded(old_party)
        assert [diagnostics['field']['settings'][k] for k in prefs] == [7, 429, 4]
        for name in ('picker', 'duplicate', 'give'):
            assert parties[name] == parties['field']
            assert dexes[name] == dexes['field']
            assert (V / (tag + '29a-' + name) / 'cartridge.sav').read_bytes() == (V / (tag + '29a-field') / 'cartridge.sav').read_bytes()
        assert wallets['duplicate'] == wallets['field']
        expected = json.loads(json.dumps(wallets['field']['inventory']))
        assert expected['battle_items'] == [{'slot': 0, 'item': 55, 'quantity': 99}]
        expected['battle_items'][0]['quantity'] = 100
        assert diagnostics['duplicate']['item_giver']['result'] == 3
        assert diagnostics['duplicate']['item_giver']['gives'] == 0
        giver = diagnostics['give']['item_giver']
        assert (giver['result'], giver['gives'], giver['denied'], giver['last_item'], giver['last_quantity']) == (1, 1, 1, 55, 1)
        for name in ('give', 'prefs-save', 'native-save', 'cold'):
            assert wallets[name]['inventory'] == expected
            for key in ('stored_wallet', 'mom_savings', 'coins', 'battle_points'):
                assert wallets[name][key] == wallets['field'][key]
            assert decoded(parties[name]) == decoded(parties['field'])
            for key in ('dex_bytes', 'profile_bytes', 'story_vars_flags_sha256'):
                assert dexes[name][key] == dexes['field'][key]
        for name in ('prefs-save', 'native-save', 'cold'):
            assert [diagnostics[name]['settings'][k] for k in prefs] == [6, 55, 0]
            for key, value in diagnostics['field']['settings'].items():
                if key not in metadata and key not in prefs:
                    assert diagnostics[name]['settings'][key] == value
        view = diagnostics['view']
        assert [view['settings'][k] for k in ('clock_speed', 'clock_hud', 'camera_pitch', 'camera_zoom')] == [1, 1, 1, 2]
        assert view['camera']['updates'] >= 1 and view['camera']['restored'] >= 1
        assert view['clock_hud']['opens'] >= 1
        assert diagnostics['route']['current_map'] == 33
        battle = diagnostics['battle' if tag == 'hg' else 'grass']['native_battle']
        assert battle['identical_retained_slots'] == ([1] if tag == 'hg' else [5])
        reward = diagnostics['reward']
        assert not reward.get('native_battle') and reward['enhancement_menu']['active']
        assert reward['instant_victory']['completed'] == reward['party_exp']['completed'] == 1
        assert reward['party_exp']['recipients'] == 6
        for before, after, gain in zip(parties['field']['party'], parties['reward']['party'], (24, 12, 12, 12, 12, 12)):
            assert after['experience'] == before['experience'] + gain
            for key in ('pid', 'species', 'ot_id', 'ivs', 'ability', 'moves', 'pp', 'nickname_codes', 'is_egg', 'form'):
                if key in before:
                    assert after[key] == before[key], key
        assert decoded(parties['reward-cold']) == decoded(parties['reward'])
        assert wallets['reward-cold']['inventory'] == wallets['field']['inventory']
        output['games'][game] = {'cases': cases, 'previous_milestone_native_save_loaded': True,
            'item_stack_99_to_100_and_duplicate_key_rejected': True,
            'item_and_preferences_saved_and_cold_reloaded': True,
            'camera_clock_options_rendered_and_owned_camera_restored': True,
            'contact_identity_and_six_native_EXP_recipients_verified': True,
            'native_rewards_saved_and_cold_reloaded': True}
    output['limitations'] = [
        'This memory-layout milestone adds capacity; quick-ball gameplay is still pending.',
        'Acceptance uses the declared HG-derived project save lineage in both ROMs, not a fresh SoulSilver story or universal save interchange.',
        'No RAM fixtures were applied in these accepted runs; earlier lineage fixtures remain declared in prior milestone evidence.',
        'Prior feature-specific milestones remain bounded evidence; these representative controls do not repeat every species, map, quest or long-play flow.',
        'No physical DS/3DS verification; remaining audited enhancements and broader acceptance are still required before a final release.']
    return output


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))

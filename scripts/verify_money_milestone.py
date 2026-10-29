#!/usr/bin/env python3
"""Assert milestone-26 acceptance against immutable local melonDS evidence.

Run from the project root. No emulator state, ROM or cartridge save is changed.
The generated report includes hashes and exact fixture/input scope; local assets
are intentionally excluded from Git.
"""
from pathlib import Path
import hashlib
import json
import struct

from inspect_visible_state import inspect_run
from inspect_wallet_state import inspect_wallet
from inspect_egg_state import inspect_eggs

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / 'local_data/verification'
C = ROOT / 'build/candidates'
E = ROOT / 'build/experiments/money-26a'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def asset(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def potion(wallet):
    return sum(x['quantity'] for x in wallet['inventory']['medicine'] if x['item'] == 17)


def verify():
    logs = {}
    for tag, count in [('full', 256), ('money', 7), ('settings', 45)]:
        path = ROOT / f'local_data/milestone-26-{tag}-tests.log'
        body = path.read_text()
        assert f'Ran {count} tests' in body and body.rstrip().endswith('OK')
        logs[tag] = {'passed': count, 'log': asset(path)}
    audit_log = ROOT / 'local_data/milestone-26-inventory-audit.log'
    assert 'OK: 59 feature rows; 41 option keys covered.' in audit_log.read_text()
    logs['inventory'] = {'rows': 59, 'emerald_keys': 41, 'log': asset(audit_log)}
    output = {'kind': 'bounded-local-gameplay-verification', 'milestone': 26,
              'verified_on': '2026-10-29', 'final_release': False,
              'scope': 'Saved default-Off wallet refill on read, original capped money APIs, native buy/sell/Cancel/quantity controls, native Mom trainer ledger, Trainer Card, native save/cold, legacy options and settings Cancel.',
              'regression': logs, 'candidates': {}, 'games': {}}
    for tag, game in [('hg', 'heartgold'), ('ss', 'soulsilver')]:
        stem = f'{game}-visual-plus-gameplay-milestone-26'
        report_path = C / (stem + '.json')
        report = load(report_path)
        rom = report_path.with_suffix('.nds')
        for ext in ('.nds', '.xdelta'):
            assert (C / (stem + ext)).read_bytes() == (E / (stem + ext)).read_bytes()
        assert sha(rom) == report['output_sha256']
        output['candidates'][game] = {
            'local_rom': str(rom.relative_to(ROOT)), 'output_sha256': sha(rom),
            'patch_sha256': sha(C / (stem + '.xdelta')), 'report_sha256': sha(report_path),
            'payload_bytes': report['resident_payload']['size'],
            'payload_end': hex(report['resident_payload']['symbols']['__enhanced_end']),
            'remaining_ITCM_bytes': 0x02000000 - report['resident_payload']['symbols']['__enhanced_end'],
            'reproduced_tested_experiment': True, 'checks': report['checks']}
        parents = {'field': None}
        for mode in ('on', 'off'):
            def chain(source, phases):
                for phase in phases:
                    name = mode + '-' + phase
                    parents[name] = source
                    source = name
            parents[mode] = 'field'
            chain(mode, ['talk', 'buy-start', 'buy-open', 'buy-quantity', 'buy-confirm',
                         'bought', 'purchased', 'buy-return', 'buy-field', 'sale-talk',
                         'sale-start', 'sale-open', 'sale-pocket', 'sale-quantity',
                         'sale-confirm', 'sold', 'sale-field', 'sale-save'])
            chain(mode + '-buy-quantity', ['max-quantity', 'quantity-cancel'])
            parents[mode + '-sale-cancel'] = mode + '-sale-confirm'
            chain(mode + '-talk', ['mom-start', 'mom-field', 'mom-save'])
            for kind in ('sale', 'mom'):
                parents[mode + '-' + kind + '-cold'] = None
            parents[mode + '-cancel'] = mode + '-sale-cold'
            parents[mode + '-card'] = mode + '-mom-cold'
        cases, diagnostics, wallets, parties = {}, {}, {}, {}
        for name, parent in parents.items():
            actual_name = name + '2' if tag == 'ss' and name.endswith('-card') else name
            path = V / (tag + '26a-' + actual_name)
            smoke = load(path / 'smoke-report.json')
            d = inspect_run(path, report_path)
            w = inspect_wallet(path, report_path, rom)
            diagnostics[name], wallets[name] = d, w
            assert w['coins'] == w['battle_points'] == 0
            assert w['private_readers_preserve_profile_bag_bank_and_BP_bytes']
            assert w['wallet_refill_getter_not_executed_by_inspection']
            log = ROOT / f'local_data/{tag}26a-{actual_name}.log'
            body = log.read_text().lower()
            assert 'data abort' not in body and 'prefetch abort' not in body
            case = {'local_run': str(path.relative_to(ROOT)),
                    'state_sha256': sha(path / 'state.bin'), 'ram_sha256': sha(path / 'main-ram.bin'),
                    'smoke_report_sha256': sha(path / 'smoke-report.json'), 'core_log': asset(log),
                    'frames': smoke['frames'], 'inputs': smoke['inputs'],
                    'developer_ram_fixture': smoke['developer_ram_fixture'],
                    'settings': d['settings'], 'menu': d['enhancement_menu'],
                    'money': d['money'], 'wallet_and_inventory': w}
            if parent:
                case['loaded_state'] = asset(V / (tag + '26a-' + parent) / 'state.bin')
            else:
                old = tag + '25a-on-named-save' if name == 'field' else tag + '26a-' + name.replace('cold', 'save')
                source = V / old / 'cartridge.sav'
                assert smoke['save_import_sha256'] == sha(source)
                case['loaded_native_save'] = asset(source)
            fixture_kind = next((kind for kind in ('buy', 'sale', 'mom') if name.endswith('-' + kind + '-start')), None)
            if fixture_kind:
                mode = name.split('-')[0]
                fixture_path = ROOT / f'local_data/{tag}26a-{mode}-{fixture_kind}-fixture.json'
                f = load(fixture_path)
                assert f['rom_sha256'] == report['output_sha256']
                assert f['source_ram_sha256'] == sha(V / (tag + '26a-' + parent) / 'main-ram.bin')
                assert smoke['developer_ram_fixture']['fixture_sha256'] == sha(fixture_path)
                assert smoke['developer_ram_fixture']['changes'] == f['changes']
                size, prefix = {'buy': (10, struct.pack('<2H', 275, 0)),
                                'sale': (8, struct.pack('<H', 782)),
                                'mom': (18, struct.pack('<4H', 30, 0x986, 213, 47))}[fixture_kind]
                assert len(f['changes']) == 2
                assert [len(bytes.fromhex(x['after'])) for x in f['changes']] == [size, 4]
                assert f['changes'][0]['before'] == '00' * size
                assert bytes.fromhex(f['changes'][0]['after']).startswith(prefix)
                case['fixture_definition'] = {**asset(fixture_path), 'changes': f['changes']}
            else:
                assert smoke['developer_ram_fixture'] is None
            if d['enhancement_menu']['active']:
                e = inspect_eggs(path, report_path, rom)
                parties[name] = e
                case['native_party_and_hatch_stats'] = e
            cases[name] = case
        # Earlier nineteen-option journals retain every known choice; Money defaults Off.
        old = inspect_run(V / (tag + '25a-on-named-save'), C / f'{game}-visual-plus-gameplay-milestone-25.json')
        metadata_keys = {'loaded', 'sequence', 'last_slot', 'writable_slots', 'successful_writes', 'status'}
        for key, value in old['settings'].items():
            if key not in metadata_keys:
                assert diagnostics['field']['settings'][key] == value, (game, key)
        assert diagnostics['field']['settings']['infinite_money'] == 0
        assert wallets['field']['stored_wallet'] == 3064
        assert diagnostics['field']['money']['calls'] == 0
        for mode, enabled in [('on', 1), ('off', 0)]:
            names = [n for n in parents if n == mode or n.startswith(mode + '-')]
            assert all(diagnostics[n]['settings']['infinite_money'] == enabled for n in names)
            base = 999999 if enabled else 3064
            for phase in ('buy-open', 'buy-quantity', 'buy-confirm', 'bought', 'max-quantity', 'quantity-cancel'):
                w = wallets[mode + '-' + phase]
                assert w['stored_wallet'] == base and potion(w) == 5
            paid = wallets[mode + '-purchased']
            assert paid['stored_wallet'] == base - 300 and potion(paid) == 6
            returned = wallets[mode + '-buy-return']
            assert returned['stored_wallet'] == (999999 if enabled else 2764) and potion(returned) == 6
            if enabled:
                assert diagnostics[mode + '-buy-open']['money']['refills'] == 1
                assert diagnostics[mode + '-buy-return']['money']['refills'] == 2
            assert potion(wallets[mode + '-sale-cancel']) == 6
            assert wallets[mode + '-sale-cancel']['stored_wallet'] == returned['stored_wallet']
            sold = wallets[mode + '-sold']
            assert potion(sold) == 5 and sold['stored_wallet'] == (999999 if enabled else 2914)
            for n in names:
                w = wallets[n]
                assert w['inventory']['items'] == wallets['field']['inventory']['items']
                for pocket in ('balls', 'machines', 'berries', 'mail', 'battle_items', 'key_items'):
                    assert w['inventory'][pocket] == wallets['field']['inventory'][pocket]
                assert w['mom_savings'] == (16 if ('-mom-' in n and not n.endswith('-start')) or n.endswith('-card') else 0)
            mom = wallets[mode + '-mom-field']
            assert mom['stored_wallet'] == 3112 and mom['mom_savings'] == 16 and mom['mom_savings_enabled']
            dm = diagnostics[mode + '-mom-field']
            assert dm['money']['calls'] == 2 and dm['money']['refills'] == 0
            assert dm['money']['bookkeeping'] == 2 * enabled
            assert dm['instant_victory']['completed'] == 2 and dm['party_exp']['completed'] == 2
            before = parties['field']['party']
            after = parties[mode + '-mom-field']['party']
            assert [b['experience'] - a['experience'] for a, b in zip(before, after)] == [70, 34, 34, 34, 34, 34]
            for a, b in zip(before, after):
                for key in ('pid', 'ot_id', 'species', 'ivs', 'ability', 'native_shiny', 'nickname_codes'):
                    assert a[key] == b[key]
                assert b['checksum_failed'] == 0
            assert after[5]['level'] == 3 and after[5]['nickname_codes'] == [317, 314, 299, 316, 309]
            for kind in ('sale', 'mom'):
                expected = wallets[mode + '-' + kind + '-field']
                for phase in ('save', 'cold'):
                    name = mode + '-' + kind + '-' + phase
                    w = wallets[name]
                    for key in ('stored_wallet', 'mom_savings', 'coins', 'battle_points', 'inventory'):
                        assert w[key] == expected[key]
                    for a, b in zip(parties[name]['party'], parties[mode + '-' + kind + '-field']['party']):
                        assert {k: v for k, v in a.items() if k != 'pokemon_sha256'} == {k: v for k, v in b.items() if k != 'pokemon_sha256'}
                assert diagnostics[mode + '-' + kind + '-cold']['money']['calls'] == 0
            cancelled = mode + '-cancel'
            source = mode + '-sale-cold'
            assert (V / (tag + '26a-' + cancelled) / 'cartridge.sav').read_bytes() == (V / (tag + '26a-' + source) / 'cartridge.sav').read_bytes()
            assert diagnostics[cancelled]['enhancement_menu']['staged_infinite_money'] == enabled
            card = wallets[mode + '-card']
            assert card['stored_wallet'] == (999999 if enabled else 3112) and card['mom_savings'] == 16
            assert diagnostics[mode + '-card']['money']['refills'] == enabled
            assert diagnostics[mode + '-card']['money']['caller'] == 0x02069038
        screenshots = []
        for mode in ('on', 'off'):
            for phase, frame in [('max-quantity', 400), ('card', 900), ('sale-cold', 3300), ('mom-cold', 3300), ('cancel', 800)]:
                actual_phase = 'card2' if tag == 'ss' and phase == 'card' else phase
                if actual_phase == 'card2':
                    frame = 1200
                path = V / f'{tag}26a-{mode}-{actual_phase}' / f'frame-{frame:06d}.png'
                if not path.exists():
                    # Select a real captured frame; never invent screenshot paths.
                    path = sorted(path.parent.glob('frame-*.png'))[-1]
                screenshots.append(asset(path))
        output['games'][game] = {'cases': cases, 'checks': {
            'legacy_19_options_retained_and_money_defaults_Off': True,
            'native_purchase_300_and_sale_150_change_inventory_exactly_once': True,
            'money_refills_on_read_not_periodically': True,
            'quantity_and_sale_Cancel_preserve_inventory_and_balance': True,
            'native_Mom_prize_64_deposit_16_wallet_48_retained': True,
            'both_native_opponents_complete_and_party_rewards_preserved': True,
            'Trainer_Card_refills_owned_wallet_and_leaves_bank_16': True,
            'coins_BP_and_other_inventory_unchanged': True,
            'native_save_cold_preserves_actual_balance_inventory_and_choice': True,
            'settings_Cancel_preserves_entire_cartridge_save': True,
            'accepted_logs_no_data_or_prefetch_abort': True},
            'visually_checked_quantity_limits': {'on': 99, 'off': 10, 'price_each': 300},
            'screenshots': screenshots}
    output['limits'] = [
        'Mac melonDS DS1.3.1 software renderer/builtin BIOS; isolated HG-derived project lineage, not fresh HG/SS stories or universal save interchange.',
        'Buy/sale fixtures change 10/8 unused native script-stack bytes plus a four-byte pointer. Mom fixture changes 18 stack bytes plus a pointer: native SetFlag(0x986) then TrainerBattle(Mikey47). No wallet, bank, coins, BP, inventory, Pokemon, battle data or coordinates are injected.',
        'Original follower continuation and native tasks handle app/trainer behavior. Source saves retain explicitly declared earlier legendary-release/location/ball-fixture ancestry.',
        'Original Mom helper executes in native instruction tests with controlled external services for additional ledger/cap cases; actual native trainer controls prove a 64 prize, 16 deposit and 48 wallet delta in both games.',
        'Private currency/party readers preserve all inspected bytes and never execute the refill getter; inspection does not change emulator state or cartridge saves.',
        'Further shop categories, full bag/insufficient funds UI, losses/blackouts, Mom purchases and wider story/link/Frontier acceptance remain pending; instruction tests cover ownership, copied profiles, caps and original add/sub/set behavior.',
        'First SoulSilver card attempts remained in the enhancement menu because of one-frame input; excluded from acceptance. Corrected card2 runs use multi-frame input and the actual native Card getter.',
        'HG lead Pokemon raw storage changes on native cold boot, while all inspected identity/battle/memo/name fields remain equal. This report does not assert byte-identical party storage across cold boot.',
        'Other enhancements and wider acceptance remain in the full goal; these are experimental candidates, not final releases.']
    destination = ROOT / 'enhancements/milestone-26-verification.json'
    destination.write_text(json.dumps(output, indent=2) + '\n')
    print('PASS: both exact candidates satisfy native buy/sale/Mom/Card/save/cold/Cancel/legacy assertions.')


if __name__ == '__main__':
    verify()

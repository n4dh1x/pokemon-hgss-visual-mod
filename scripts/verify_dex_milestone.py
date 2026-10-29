#!/usr/bin/env python3
"""Assert milestone-27 acceptance against immutable local native test evidence."""
from pathlib import Path
import hashlib
import json
import struct

from inspect_visible_state import inspect_run
from inspect_dex_state import inspect_dex
from inspect_wallet_state import inspect_wallet
from inspect_egg_state import inspect_eggs

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / 'local_data/verification'
C = ROOT / 'build/candidates'
E = ROOT / 'build/experiments/dex-27a'


def load(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def asset(path): return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
def decoded_party(party):
    return [{k:v for k,v in p.items() if k != 'pokemon_sha256'} for p in party]
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def verify():
    logs = {}
    for name,count in [('full',280),('dex',8),('settings',45)]:
        path = ROOT / f'local_data/milestone-27-{name}-tests.log'
        body=path.read_text();assert f'Ran {count} tests' in body and body.rstrip().endswith('OK')
        logs[name]={'passed':count,'log':asset(path)}
    audit=ROOT/'local_data/milestone-27-inventory-audit.log'
    assert 'OK: 59 feature rows; 41 option keys covered.' in audit.read_text()
    logs['inventory']={'rows':59,'emerald_keys':41,'log':asset(audit)}
    out={'kind':'bounded-local-gameplay-verification','milestone':27,'verified_on':'2026-10-29',
         'final_release':False,'scope':'Confirmed native Johto/National actions, exact regional membership, normal original form/language bookkeeping, untouched story/party/economy/RNG controls, No/B cancellation, native save/cold and declared original-app ownership fixtures.',
         'regression':logs,'candidates':{},'games':{}}
    for tag,game in [('hg','heartgold'),('ss','soulsilver')]:
        stem=game+'-visual-plus-gameplay-milestone-27';report_path=C/(stem+'.json');rom=report_path.with_suffix('.nds');report=load(report_path)
        for ext in ('.nds','.xdelta'):assert (C/(stem+ext)).read_bytes()==(E/(stem+ext)).read_bytes()
        assert sha(rom)==report['output_sha256']
        out['candidates'][game]={'local_rom':str(rom.relative_to(ROOT)),'output_sha256':sha(rom),
            'patch_sha256':sha(C/(stem+'.xdelta')),'report_sha256':sha(report_path),
            'payload_bytes':report['resident_payload']['size'],
            'payload_end':hex(report['resident_payload']['symbols']['__enhanced_end']),
            'remaining_ITCM_bytes':0x02000000-report['resident_payload']['symbols']['__enhanced_end'],
            'reproduced_tested_experiment':True,'checks':report['checks']}
        parents={'field':None,'actions':'field','cancel':'actions'}
        for kind in ('johto','unlock','national'):
            parents[kind]='actions';parents[kind+'-save']=kind;parents[kind+'-cold']=None
            if kind!='unlock':
                last=kind+'-cold'
                for phase in ('talk','owned','dex','entry','return'):
                    name=kind+'-'+phase;parents[name]=last;last=name
        cases={};ds={};ws={};ps={};diags={}
        for name,parent in parents.items():
            run=V/(tag+'27a-'+name);sm=load(run/'smoke-report.json')
            d=inspect_dex(run,report_path,rom);ds[name]=d
            diag=inspect_run(run,report_path);diags[name]=diag
            w=inspect_wallet(run,report_path,rom);ws[name]=w
            log=ROOT/f'local_data/{tag}27a-{name}.log';body=log.read_text().lower()
            assert 'data abort' not in body and 'prefetch abort' not in body
            case={'local_run':str(run.relative_to(ROOT)), 'state_sha256':sha(run/'state.bin'),
                'ram_sha256':sha(run/'main-ram.bin'),'smoke_report_sha256':sha(run/'smoke-report.json'),
                'core_log':asset(log),'frames':sm['frames'],'inputs':sm['inputs'],
                'developer_ram_fixture':sm['developer_ram_fixture'],'native_dex':d,
                'settings':diag['settings'],'menu':diag['enhancement_menu'],
                'wallet_and_inventory':w}
            if parent:case['loaded_state']=asset(V/(tag+'27a-'+parent)/'state.bin')
            else:
                source=V/(tag+'26a-off-mom-save' if name=='field' else tag+'27a-'+name.replace('cold','save'))/'cartridge.sav'
                assert sm['save_import_sha256']==sha(source);case['loaded_native_save']=asset(source)
            if name.endswith('-owned'):
                kind=name.split('-')[0];fp=ROOT/f'local_data/{tag}27a-{kind}-ownership-fixture.json';f=load(fp)
                assert f['rom_sha256']==report['output_sha256'] and f['source_ram_sha256']==sha(V/(tag+'27a-'+parent)/'main-ram.bin')
                assert sm['developer_ram_fixture']['fixture_sha256']==sha(fp)
                assert sm['developer_ram_fixture']['changes']==f['changes']
                assert len(f['changes'])==2 and [len(bytes.fromhex(x['after'])) for x in f['changes']]==[12,4]
                assert bytes.fromhex(f['changes'][0]['after'])[:6]==struct.pack('<3H',291,30,0x6B)
                case['fixture_definition']={**asset(fp),'changes':f['changes'],'native_commands':['GivePokedex','SetFlag(FLAG_GOT_POKEDEX0x6B)','GoToOriginalFollowerContinuation']}
            else:assert sm['developer_ram_fixture'] is None
            if diag['enhancement_menu']['active']:
                p=inspect_eggs(run,report_path,rom);ps[name]=p
                case['native_decoded_party_sha256']=digest(decoded_party(p['party']))
                case['native_raw_party_sha256']=[m['pokemon_sha256'] for m in p['party']]
                case['native_eggs_hatched']=p['eggs_hatched'];case['native_trainer_score']=p['trainer_score']
            cases[name]=case
        # Load the earlier twenty-option save without replacing its journal.
        old=inspect_run(V/(tag+'26a-off-mom-save'),C/f'{game}-visual-plus-gameplay-milestone-26.json')
        meta={'loaded','sequence','last_slot','writable_slots','successful_writes','status'}
        for key,value in old['settings'].items():
            if key not in meta:assert diags['field']['settings'][key]==value
        assert diags['field']['enhancement_menu']['staged_visible']==old['enhancement_menu']['staged_visible']
        field=ds['field'];assert (field['national_seen'],field['national_caught'])==(6,5)
        assert field['dex_enabled']==field['national_enabled']==0 and not field['profile_national_enabled']
        # All action branches are real inputs only: no entry/flag/Pokemon injection.
        for name in ('actions','cancel','johto','unlock','national'):
            d=ds[name];assert d['story_vars_flags_sha256']==field['story_vars_flags_sha256']
            assert d['lc_rng_seed']==field['lc_rng_seed'];assert d['dex_enabled']==0
            for key in ('stored_wallet','mom_savings','coins','battle_points','inventory'):
                assert ws[name][key]==ws['field'][key]
            assert ps[name]['party']==ps['field']['party']
            assert ps[name]['eggs_hatched']==ps['field']['eggs_hatched']
            assert ps[name]['trainer_score']==ps['field']['trainer_score']
            assert (V/(tag+'27a-'+name)/'cartridge.sav').read_bytes()==(V/(tag+'27a-field')/'cartridge.sav').read_bytes()
        for name in ('actions','cancel'):
            assert ds[name]['dex_sha256']==field['dex_sha256'] and ds[name]['profile_sha256']==field['profile_sha256']
        assert ds['johto']['johto_seen']==ds['johto']['johto_caught']==256
        assert ds['johto']['national_seen']==ds['johto']['national_caught']==256
        assert ds['johto']['national_enabled']==0 and ds['johto']['profile_sha256']==field['profile_sha256']
        # Native table contains the five Gen-IV additions, beyond species1..251.
        import ndspy.rom,ndspy.narc
        rr=ndspy.rom.NintendoDSRom(rom.read_bytes());lut=struct.unpack('<494H',ndspy.narc.NARC(rr.getFileByName('a/1/3/8')).files[0])
        regional={i for i in range(1,494) if lut[i]};assert len(regional)==256
        assert set(ds['johto']['seen'])==set(ds['johto']['caught'])==regional
        for name in ('unlock','national'):
            d=ds[name];assert d['national_enabled']==1 and d['profile_national_enabled']
            expected=bytearray.fromhex(field['profile_bytes']);expected[29]|=2
            assert bytes.fromhex(d['profile_bytes'])==bytes(expected)
        expected=bytearray.fromhex(field['dex_bytes']);expected[0x337]=1
        assert bytes.fromhex(ds['unlock']['dex_bytes'])==bytes(expected)
        assert set(ds['national']['seen'])==set(ds['national']['caught'])==set(range(1,494))
        for kind,count in [('johto',256),('unlock',0),('national',493)]:
            action=ds[kind]['action'];assert action['status']==2 and action['registered']==count
            assert action['mon']==action['johto']==0
            for suffix in ('-save','-cold'):
                name=kind+suffix;d=ds[name]
                for key in ('dex_bytes','profile_bytes','story_vars_flags_sha256'):
                    assert d[key]==ds[kind][key]
                for key in ('stored_wallet','mom_savings','coins','battle_points','inventory'):
                    assert ws[name][key]==ws[kind][key]
                assert decoded_party(ps[name]['party'])==decoded_party(ps[kind]['party'])
                assert diags[name]['enhancement_menu']['staged_visible']==diags[kind]['enhancement_menu']['staged_visible']
                for key,value in diags[kind]['settings'].items():
                    if key not in meta:assert diags[name]['settings'][key]==value
            assert ds[kind+'-cold']['action']['status']==0
        for kind in ('johto','national'):
            before=ds[kind+'-talk'];owned=ds[kind+'-owned']
            expected=bytearray.fromhex(before['dex_bytes']);expected[0x336]=1
            assert bytes.fromhex(owned['dex_bytes'])==bytes(expected)
            assert owned['profile_bytes']==before['profile_bytes']
            for phase in ('dex','entry','return'):
                name=kind+'-'+phase;assert ds[name]['dex_bytes']==owned['dex_bytes']
                assert ds[name]['profile_bytes']==owned['profile_bytes']
                assert ds[name]['story_vars_flags_sha256']==owned['story_vars_flags_sha256']
            assert diags[kind+'-return']['enhancement_menu']['active']
        images=[]
        for name,frame in [('actions',400),('cancel',800),('unlock',250),('johto-cold',3300),('national-cold',3300),('johto-dex',1200),('national-dex',1200),('johto-entry',1400),('national-entry',1400),('national-return',2100)]:
            images.append(asset(V/(tag+'27a-'+name)/f'frame-{frame:06d}.png'))
        out['games'][game]={'cases':cases,'starting_native_party':ps['field'],
            'checks':{'all_20_old_choices_retained':True,'default_No_and_B_Cancel_preserve_progress_and_entire_cartridge_save':True,
                'Johto_exact_native_256_members_seen_and_caught_no_National_upgrade':True,
                'National_unlock_changes_only_both_original_flags':True,
                'National_full_493_seen_caught_and_both_original_flags':True,
                'actions_preserve_all_party_bytes_stats_economy_story_vars_flags_and_gameplay_RNG':True,
                'actions_do_not_write_cartridge_save_or_settings':True,
                'completed_actions_free_all_owned_allocations':True,
                'native_save_cold_preserves_Dex_profile_story_and_decoded_party':True,
                'original_Dex_UI_totals_entries_and_field_return':True,
                'accepted_logs_no_data_or_prefetch_abort':True},'screenshots':images}
    out['limits']=[
        'Mac melonDS DS1.3.1 software renderer/builtin BIOS; isolated declared HG-derived project lineage, not fresh HG/SS story or universal save interchange.',
        'The three actions and cancellation/native save controls use real menu inputs only, with no RAM fixtures. They do not grant the Pokedex story ownership flag or owned-Dex byte. Normal story acquisition remains necessary to open the app.',
        'Separate app-UI controls explicitly insert GivePokedex291 and SetFlag30(FLAG_GOT_POKEDEX0x6B) plus original follower continuation: 12 unused script-stack bytes and a four-byte pointer. This verification fixture supplies ownership missing in the source lineage; the feature never does so. No entries, Pokemon, currencies, inventory or coordinates are injected.',
        'Original caught API applies normal form/gender/language bookkeeping from deterministic private native-created Pokemon; it does not fill every alternate form or every language. Existing Spinda personality and form-history preservation are also checked with native instructions and bounded external metadata services.',
        'Native field/follower continuation after app-UI fixture can apply ordinary dialogue/walking effects. Strict untouched party/economy/story/RNG assertions cover the direct action controls; they do not mask the declared ownership-fixture differences.',
        'HG lead raw Pokemon storage changes across cold boot while all inspected decoded identity/battle/memo/name fields remain equal. Byte-identical party storage is asserted only for direct menu actions, not all native reloads.',
        'Wider alternate forms/languages, repeated native acquisition, fresh stories, long play and other enhancements remain pending. These are experimental candidates, not final releases.']
    (ROOT/'enhancements/milestone-27-verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: both candidates satisfy native Dex membership/actions/Cancel/save/cold/UI/return and unchanged progress assertions.')

if __name__=='__main__':verify()

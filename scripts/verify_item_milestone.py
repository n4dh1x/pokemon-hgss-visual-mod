#!/usr/bin/env python3
"""Assert milestone-28 all-pocket giving against immutable local native runs."""
from pathlib import Path
import hashlib
import json
import struct
from inspect_visible_state import inspect_run
from inspect_wallet_state import inspect_wallet
from inspect_dex_state import inspect_dex
from inspect_egg_state import inspect_eggs

ROOT=Path(__file__).resolve().parent.parent
V=ROOT/'local_data/verification';C=ROOT/'build/candidates';E=ROOT/'build/experiments/items-28b'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def asset(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def party(p):return [{k:v for k,v in x.items() if k!='pokemon_sha256'} for x in p['party']]
def quantity(w,pocket,item):return sum(x['quantity'] for x in w['inventory'][pocket] if x['item']==item)


def verify():
    logs={}
    for name,count in [('full',294),('items',12),('settings',47)]:
        p=ROOT/f'local_data/milestone-28-{name}-tests.log';s=p.read_text()
        assert f'Ran {count} tests' in s and s.rstrip().endswith('OK')
        logs[name]={'passed':count,'log':asset(p)}
    p=ROOT/'local_data/milestone-28-inventory-audit.log';assert 'OK: 59 feature rows; 41 option keys covered.' in p.read_text()
    logs['inventory']={'rows':59,'emerald_keys':41,'log':asset(p)}
    out={'kind':'bounded-local-gameplay-verification','milestone':28,'verified_on':'2026-10-30','final_release':False,
        'scope':'Native all-eight-pocket item giving with five quantities, stack caps, unique keys, ROM-derived responsive lookup, staged picker preferences, Cancel, ordinary game Save/cold, original Bag and Potion-use/save controls. No RAM fixtures in accepted cases.',
        'regression':logs,'candidates':{},'games':{}}
    for tag,game in [('hg','heartgold'),('ss','soulsilver')]:
        stem=game+'-visual-plus-gameplay-milestone-28';r=C/(stem+'.json');rom=r.with_suffix('.nds');report=load(r)
        for ext in ('.nds','.xdelta'):assert (C/(stem+ext)).read_bytes()==(E/(stem+ext)).read_bytes()
        assert sha(rom)==report['output_sha256']
        assert report['item_giver']['pocket_lookup']['bytes']==269
        assert report['item_giver']['pocket_lookup']['sha256']=='4afd61ba0281d972fe2e8d74466378aa0e3de6247136177323b97081b777f8e1'
        out['candidates'][game]={'local_rom':str(rom.relative_to(ROOT)),'output_sha256':sha(rom),'patch_sha256':sha(C/(stem+'.xdelta')),'report_sha256':sha(r),
            'payload_bytes':report['resident_payload']['size'],'payload_end':hex(report['resident_payload']['symbols']['__enhanced_end']),
            'remaining_ITCM_bytes':0x02000000-report['resident_payload']['symbols']['__enhanced_end'],
            'reproduced_tested_experiment':True,'pocket_lookup':report['item_giver']['pocket_lookup'],'checks':report['checks']}
        parents={'field':None,'picker':'field'}
        for i in range(8):parents['pocket'+str(i)]='picker' if not i else 'pocket'+str(i-1)
        parents.update({'prefs-save':'pocket7','machine-cap':'picker','medicine-cap':'picker','cancel':'picker','give-then-cancel':'pocket0',
            'prefs-only-cold':None,'all-save':'prefs-save','all-cold':None,'bag':'all-cold','bag-medicine':'bag','potion-context':'bag-medicine',
            'potion-party':'potion-context','potion-healed':'potion-party','potion-field':'potion-healed','used-save':'potion-field','used-cold':None})
        cases={};diags={};wallets={};dexes={};parties={}
        for name,parent in parents.items():
            p=V/(tag+'28b-'+name);sm=load(p/'smoke-report.json');d=inspect_run(p,r);w=inspect_wallet(p,r,rom);x=inspect_dex(p,r,rom)
            diags[name]=d;wallets[name]=w;dexes[name]=x
            assert sm['developer_ram_fixture'] is None
            log=ROOT/f'local_data/{tag}28b-{name}.log';body=log.read_text().lower()
            assert 'data abort' not in body and 'prefetch abort' not in body
            case={'local_run':str(p.relative_to(ROOT)),'state_sha256':sha(p/'state.bin'),'ram_sha256':sha(p/'main-ram.bin'),
                'smoke_report_sha256':sha(p/'smoke-report.json'),'core_log':asset(log),'frames':sm['frames'],'inputs':sm['inputs'],
                'developer_ram_fixture':None,'settings':d['settings'],'menu':d['enhancement_menu'],'item_giver':d['item_giver'],
                'wallet_and_inventory':w,'dex_and_story':{k:v for k,v in x.items() if k not in ('seen','caught','dex_bytes','profile_bytes')}}
            if parent:case['loaded_state']=asset(V/(tag+'28b-'+parent)/'state.bin')
            else:
                if name=='field':src=V/(tag+'27a-national-save')/'cartridge.sav'
                elif name=='prefs-only-cold':src=V/(tag+'28b-prefs-save')/'cartridge.sav'
                else:src=V/(tag+'28b-'+name.replace('cold','save'))/'cartridge.sav'
                assert sm['save_import_sha256']==sha(src);case['loaded_native_save']=asset(src)
            if d['enhancement_menu']['active']:
                e=inspect_eggs(p,r,rom);parties[name]=e
                case['decoded_party_sha256']=digest(party(e));case['raw_pokemon_sha256']=[m['pokemon_sha256'] for m in e['party']]
                case['eggs_hatched']=e['eggs_hatched'];case['trainer_score']=e['trainer_score']
            cases[name]=case
        old=inspect_run(V/(tag+'27a-national-save'),C/f'{game}-visual-plus-gameplay-milestone-27.json')
        meta={'loaded','sequence','last_slot','writable_slots','successful_writes','status'}
        pref=('give_pocket','give_item','give_count')
        for key,value in old['settings'].items():
            if key not in meta:assert diags['field']['settings'][key]==value
        assert diags['field']['enhancement_menu']['staged_visible']==old['enhancement_menu']['staged_visible']
        assert [diags['field']['settings'][k] for k in pref]==[0,0,0]
        base=wallets['field'];assert (base['stored_wallet'],base['mom_savings'],base['coins'],base['battle_points'])==(3112,16,0,0)
        expected=json.loads(json.dumps(base['inventory']))
        additions=[('items',68,1),('medicine',17,5),('balls',1,10),('machines',328,50),('berries',149,99),('mail',137,1),('battle_items',55,99),('key_items',429,1)]
        strict=['picker','prefs-save','machine-cap','medicine-cap']+['pocket'+str(i) for i in range(8)]
        for name in strict:
            w=wallets[name];x=dexes[name];e=parties[name]
            for key in ('stored_wallet','mom_savings','coins','battle_points'):assert w[key]==base[key]
            for key in ('dex_bytes','profile_bytes','story_vars_flags_sha256'):assert x[key]==dexes['field'][key]
            if name!='prefs-save':assert x['lc_rng_seed']==dexes['field']['lc_rng_seed']
            assert e['party']==parties['field']['party']
            assert (e['eggs_hatched'],e['trainer_score'])==(parties['field']['eggs_hatched'],parties['field']['trainer_score'])
        for i,(pocket,item,amount) in enumerate(additions):
            existing=next((z for z in expected[pocket] if z['item']==item),None)
            if existing:existing['quantity']+=amount
            else:expected[pocket].append({'slot':len(expected[pocket]),'item':item,'quantity':amount})
            name='pocket'+str(i);assert wallets[name]['inventory']==expected
            a=diags[name]['item_giver'];assert a['gives']==i+1 and a['last_item']==item and a['last_quantity']==amount
            assert a['denied']==(1 if i==7 else 0) and a['result']==(3 if i==7 else 1)
            assert [diags[name]['settings'][k] for k in pref]==[0,0,0]
            assert (V/(tag+'28b-'+name)/'cartridge.sav').read_bytes()==(V/(tag+'28b-field')/'cartridge.sav').read_bytes()
        assert diags['pocket7']['enhancement_menu']['staged_give_count']==4
        assert wallets['prefs-save']['inventory']==expected
        assert [diags['prefs-save']['settings'][k] for k in pref]==[7,429,4]
        assert (V/(tag+'28b-prefs-save')/'cartridge.sav').read_bytes()!=(V/(tag+'28b-field')/'cartridge.sav').read_bytes()
        # Settings persistence deliberately does not replace the original game save.
        assert wallets['prefs-only-cold']['inventory']==base['inventory']
        assert [diags['prefs-only-cold']['settings'][k] for k in pref]==[7,429,4]
        assert wallets['cancel']['inventory']==base['inventory']
        assert [diags['cancel']['settings'][k] for k in pref]==[0,0,0]
        assert (V/(tag+'28b-cancel')/'cartridge.sav').read_bytes()==(V/(tag+'28b-field')/'cartridge.sav').read_bytes()
        assert quantity(wallets['give-then-cancel'],'items',68)==1
        assert [diags['give-then-cancel']['settings'][k] for k in pref]==[0,0,0]
        assert (V/(tag+'28b-give-then-cancel')/'cartridge.sav').read_bytes()==(V/(tag+'28b-field')/'cartridge.sav').read_bytes()
        assert quantity(wallets['medicine-cap'],'medicine',17)==999
        assert diags['medicine-cap']['item_giver']['gives']==14 and diags['medicine-cap']['item_giver']['denied']==1
        assert diags['medicine-cap']['item_giver']['result']==4
        assert quantity(wallets['machine-cap'],'machines',328)==99
        assert diags['machine-cap']['item_giver']['gives']==diags['machine-cap']['item_giver']['denied']==1
        assert diags['machine-cap']['item_giver']['result']==4
        for name in ('all-save','all-cold'):
            assert wallets[name]['inventory']==expected
            for key in ('stored_wallet','mom_savings','coins','battle_points'):assert wallets[name][key]==base[key]
            for key in ('dex_bytes','profile_bytes','story_vars_flags_sha256'):assert dexes[name][key]==dexes['prefs-save'][key]
            assert party(parties[name])==party(parties['prefs-save'])
            assert [diags[name]['settings'][k] for k in pref]==[7,429,4]
            for key,value in diags['field']['settings'].items():
                if key not in meta and key not in pref:assert diags[name]['settings'][key]==value
        assert diags['all-cold']['item_giver']['gives']==0
        for name in ('bag','bag-medicine','potion-context','potion-party'):
            assert wallets[name]['inventory']==expected
        for name in ('potion-healed','potion-field','used-save','used-cold'):
            assert quantity(wallets[name],'medicine',17)==9
            inventory=json.loads(json.dumps(expected));inventory['medicine'][0]['quantity']=9
            assert wallets[name]['inventory']==inventory
            for key in ('stored_wallet','mom_savings','coins','battle_points'):assert wallets[name][key]==base[key]
        before=parties['all-cold']['party']
        assert (before[0]['hp'],before[0]['max_hp'])==(28,36)
        for name in ('potion-field','used-save','used-cold'):
            after=parties[name]['party'];assert (after[0]['hp'],after[0]['max_hp'])==(36,36)
            for a,b in zip(before,after):
                for key in ('pid','ot_id','species','ivs','ability','native_shiny','nickname_codes','experience','moves','pp'):
                    assert a[key]==b[key]
                assert b['checksum_failed']==0
        screenshots=[]
        for name,frame in [('picker',500),('pocket3',550),('pocket7',550),('medicine-cap',1100),('machine-cap',900),('prefs-only-cold',3500),('all-cold',3500),('bag-medicine',400),('potion-party',900),('potion-healed',1200),('used-cold',3300)]:
            if tag=='ss' and name=='medicine-cap':frame=1200
            screenshots.append(asset(V/(tag+'28b-'+name)/f'frame-{frame:06d}.png'))
        out['games'][game]={'cases':cases,'starting_native_party':parties['field'],'checks':{
            'legacy_20_choices_retained_and_picker_defaults_zero':True,
            'all_eight_pockets_and_five_quantities_follow_exact_native_inventory_deltas':True,
            'keys_force_quantity_one_and_duplicate_is_rejected':True,
            'actual_native_999_general_and_99_machine_caps_reject_further_gives':True,
            'direct_giving_preserves_all_party_bytes_hatch_score_dex_profile_story_currencies_and_RNG':True,
            'direct_giving_does_not_write_cartridge_or_apply_staged_preferences':True,
            'main_Cancel_discards_picker_preferences_without_undoing_given_items':True,
            'settings_Save_and_normal_game_Save_have_separate_verified_effects':True,
            'normal_Save_cold_retains_all_given_items_preferences_and_prior_choices':True,
            'given_Potion_native_Bag_use_consumes_one_and_heals_28_to_36_HP':True,
            'used_item_and_healed_identity_survive_normal_Save_cold':True,
            'accepted_cases_use_no_RAM_fixtures_and_have_no_data_or_prefetch_abort':True},'screenshots':screenshots}
    out['limits']=[
        'Mac melonDS DS1.3.1 software renderer/builtin BIOS; isolated HG-derived project lineage, not fresh HG/SS stories or universal save interchange.',
        'All accepted 28b cases use real inputs without RAM fixtures. Source saves retain declared earlier legendary-release/location/ball-fixture ancestry and milestone27 native Dex actions; no new economic/Pokemon/story data is injected.',
        'Earlier 28a file-scanning picker missed rapid input and is excluded from acceptance. Its partial regression run was stopped143 before the performance fix. Only the fixed 28b builds and complete fresh294 suite support this milestone.',
        'A269-byte pocket lookup is derived from audited native mapping/data at build time and checked in the payload. It skips23 unused mappings; native names still reject placeholders. Generated item metadata binaries stay private/ignored and are not committed.',
        'All eight native pockets are adapted, including named special/legacy records; availability in the giver does not grant associated quest flags or make every item usable in every story/context. Native item-use restrictions remain.',
        'Original Bag instruction tests cover legal full-pockets, sorting, ownership and native Bag permissions with controlled metadata/flag services. Actual full-pocket saturation and restricted-map UI coverage remain wider acceptance work.',
        'Strict untouched party/RNG assertions cover direct giving while the enhancement menu pauses the field. Native app/field-return/reload can change normal runtime/storage bytes. HG lead raw storage changes on cold boot while inspected decoded fields remain equal.',
        'Normal Potion use is verified; broader item types/effects, key quest interactions, native TM teaching and other gameplay enhancements remain pending. These are experimental candidates, not final releases.']
    (ROOT/'enhancements/milestone-28-verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: both exact candidates satisfy all-pocket native giving/caps/key/prefs/Cancel/save/cold/Bag/use assertions.')

if __name__=='__main__':verify()

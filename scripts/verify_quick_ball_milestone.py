#!/usr/bin/env python3
"""Recheck milestone 30 from ROM-matched native snapshots without mutations."""
from pathlib import Path
import hashlib,json
from inspect_visible_state import inspect_run
from inspect_storage_state import inspect_storage
from inspect_wallet_state import inspect_wallet
from inspect_egg_state import inspect_eggs
ROOT=Path(__file__).resolve().parent.parent
V=ROOT/'local_data/verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def asset(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def verify():
    out={'milestone':30,'verified_on':'2026-11-06','final_release':False,
         'scope':'Native quick-ball keyboard/touch selection, throw, native Bag tracking, failed throw, capture rewards and native save/cold reload; SELECT+L shortcut.',
         'regression':{},'games':{},'limitations':['Mac melonDS DS1.3.1 software renderer and builtin BIOS; no physical hardware test.',
         'Existing HG-derived progress used in SS, not a fresh SS story playthrough or general HG/SS save interchange.',
         'No RAM fixtures in accepted 30h runs. Earlier test-save lineage and milestone-29 preparation remain documented.',
         'Special-format/storage-full/failed-save restrictions have compiled ARM tests; broader native gameplay acceptance remains.']}
    for name,count in [('full',314),('h-quick',13),('c-settings',50)]:
        p=ROOT/'local_data'/({'full':'milestone-30-full-tests.log','h-quick':'milestone-30h-quick-tests.log','c-settings':'milestone-30c-settings-tests.log'}[name])
        body=p.read_text();assert f'Ran {count} tests' in body and body.rstrip().endswith('OK'),name
        out['regression'][name]={'passed':count,'log':asset(p)}
    for tag,game in [('hg','heartgold'),('ss','soulsilver')]:
        stem=f'{game}-visual-plus-gameplay-milestone-30'
        report=ROOT/f'build/candidates/{stem}.json';rom=report.with_suffix('.nds');meta=json.loads(report.read_text())
        for ext in ('.nds','.xdelta'):
            assert (ROOT/f'build/experiments/quick-30h/{stem}{ext}').read_bytes()==report.with_suffix(ext).read_bytes()
        assert sha(rom)==meta['output_sha256'] and sha(report.with_suffix('.xdelta'))==meta['patch_sha256']
        names=['field','grass','battle','native-save','saved-cold']
        names+=['poke-control','late-touch-cycles','touch-ultra-throw','escaped-field'] if tag=='hg' else ['key-cycles','key-ultra-throw','ultra-field','bag-open','bag-balls','bag-great-selected','bag-great-throw']
        ds={};cases={}
        for name in names:
            run=V/f'{tag}30h-{name}';smoke=json.loads((run/'smoke-report.json').read_text())
            assert smoke['developer_ram_fixture'] is None
            d=inspect_run(run,report);ds[name]=d
            cases[name]={'run':str(run.relative_to(ROOT)),'state':asset(run/'state.bin'),'ram':asset(run/'main-ram.bin'),
                'smoke_report':asset(run/'smoke-report.json'),'inputs':smoke['inputs'],'frames':smoke['frames'],
                'quick_ball':d['quick_ball'],'enhancement_menu':d['enhancement_menu'],'settings':d['settings']}
            log=ROOT/f'local_data/{tag}30h-{name}.log';body=log.read_text().lower()
            assert 'data abort' not in body and 'prefetch abort' not in body
            cases[name]['log']=asset(log)
        cold=ds['saved-cold']['quick_ball'];saved=ds['native-save']['quick_ball']
        assert (cold['last'],cold['saved'],cold['dirty'])==(2,2,0)
        assert (saved['last'],saved['saved'],saved['dirty'],saved['saves'])==(2,2,0,1)
        assert ds['saved-cold']['enhancement_menu']['active'] and not ds['saved-cold'].get('native_battle')
        skip={'loaded','sequence','last_slot','writable_slots','successful_writes','status'}
        assert {k:v for k,v in ds['field']['settings'].items() if k not in skip}=={k:v for k,v in ds['saved-cold']['settings'].items() if k not in skip}
        assert ds['field']['quick_ball']['last']==0
        base_run=V/f'{tag}30h-field';cold_run=V/f'{tag}30h-saved-cold'
        before_pc=inspect_storage(base_run,report,rom);after_pc=inspect_storage(cold_run,report,rom)
        assert before_pc['records']==[] and len(after_pc['records'])==1
        caught=after_pc['records'][0];assert caught['species']==161 and caught['pokeball']==2
        assert caught['pid']==(3346388842 if tag=='hg' else 394594202)
        wallet0=inspect_wallet(base_run,report,rom);wallet1=inspect_wallet(cold_run,report,rom)
        b0={x['item']:x['quantity'] for x in wallet0['inventory']['balls']};b1={x['item']:x['quantity'] for x in wallet1['inventory']['balls']}
        assert b0=={1:10,2:10,3:10,4:10}
        assert b1=={1:10,2:9,3:10,4:9 if tag=='hg' else 10}
        for key in ('stored_wallet','mom_savings','coins','battle_points'):assert wallet0[key]==wallet1[key]
        party0=inspect_eggs(base_run,report,rom);party1=inspect_eggs(cold_run,report,rom)
        assert len(party0['party'])==len(party1['party'])==6
        for a,b in zip(party0['party'],party1['party']):assert a['pid']==b['pid']
        assert party1['party'][0]['experience']>party0['party'][0]['experience']
        if tag=='hg':
            failed=ds['poke-control'];q=failed['quick_ball']
            assert (q['last'],q['throws'],q['ui_ball'],q['ui_quantity'])==(4,1,4,9)
            assert failed['capture_exp']['completed_once']==0 and all(q[f'text{i}'] for i in range(4))
            assert (ds['late-touch-cycles']['quick_ball']['cycles'],ds['late-touch-cycles']['quick_ball']['ui_ball'])==(5,2)
            assert ds['touch-ultra-throw']['quick_ball']['throws']==2
        else:
            assert (ds['key-cycles']['quick_ball']['cycles'],ds['key-cycles']['quick_ball']['ui_ball'])==(7,2)
            manual=ds['bag-great-throw']['quick_ball'];assert (manual['last'],manual['throws'],manual['requests'])==(3,1,0)
            assert inspect_storage(V/f'{tag}30h-ultra-field',report,rom)['records']==after_pc['records']
        out['games'][game]={'rom_sha256':sha(rom),'patch_sha256':sha(report.with_suffix('.xdelta')),'report':asset(report),
            'reproduces_native_tested_experiment':True,'cases':cases,'storage_before':before_pc,'storage_after_cold':after_pc,
            'wallet_before':wallet0,'wallet_after_cold':wallet1,'party_before':party0,'party_after_cold':party1}
    return out
if __name__=='__main__':print(json.dumps(verify(),indent=2))

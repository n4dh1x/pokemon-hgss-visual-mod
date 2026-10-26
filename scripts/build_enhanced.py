#!/usr/bin/env python3
"""Build an experimental, checked gameplay milestone over Visual+.

The feature list in the output report is authoritative. This is not yet the
final Emerald-parity release. ROMs and candidate patches stay in ignored build/.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import ndspy.rom
import ndspy.fnt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gameplay.patches import reusable_tms
from gameplay.native import build_payload, inject_evolution, verify_arm9_changes, PAYLOAD_BASE
from gameplay.field import install_field, verify_field_files
from gameplay.settings import audit_save_layout
from gameplay.repel import install_repel
from gameplay.capture import install_capture
from gameplay.party_exp import install_party_exp
from gameplay.field_hms import install_field_hms
from gameplay.field_hm_bag import install_field_hm_bag
from gameplay.summary_viewer import install_summary_viewer
from gameplay.shiny import install_shiny
from gameplay.follower import install_follower
from gameplay.clock import install_clock
from gameplay.camera import install_camera
from build_baseline import build_baseline, read_rom, sha256


def verify_unchanged_data(original, patched, overlay_changes, file_changes=()) -> None:
    for name in ('name', 'idCode', 'arm9RamAddress', 'arm9EntryAddress',
                 'arm7', 'arm7RamAddress', 'arm7EntryAddress',
                 'arm7OverlayTable', 'iconBanner'):
        if getattr(original, name) != getattr(patched, name):
            raise ValueError(f'Unexpected change outside gameplay code: {name}')
    if ndspy.fnt.save(original.filenames) != ndspy.fnt.save(patched.filenames):
        raise ValueError('Unexpected NitroFS filename change.')
    verify_field_files(original, patched, overlay_changes, file_changes)


def build(source: Path, decoder: str, output_dir: Path) -> dict:
    baseline_dir = ROOT / 'build/baseline'
    info = build_baseline(source, 'full', decoder, baseline_dir)
    baseline = baseline_dir / info['output']
    original = ndspy.rom.NintendoDSRom.fromFile(baseline)
    arm9 = bytearray(original.arm9)
    settings_storage = audit_save_layout(original)
    payload = build_payload()
    results = [reusable_tms(arm9, original.arm9RamAddress, payload.symbols['EnhancedTakeTm'])]
    patched = ndspy.rom.NintendoDSRom.fromFile(baseline)
    patched.arm9 = bytes(arm9)
    field_changes, overlay_changes = install_field(patched, payload)
    results.extend(field_changes)
    repel_changes, repel_storage = install_repel(patched, payload)
    overlay_changes.extend(repel_changes)
    capture_changes = install_capture(patched, payload)
    overlay_changes.extend(capture_changes)
    party_changes, file_changes = install_party_exp(patched, payload)
    overlay_changes.extend(party_changes)
    hm_main, hm_overlays = install_field_hms(patched, payload)
    results.extend(hm_main)
    overlay_changes.extend(hm_overlays)
    bag_main, bag_overlays = install_field_hm_bag(patched, payload)
    results.extend(bag_main)
    overlay_changes.extend(bag_overlays)
    results.extend(install_summary_viewer(patched, payload))
    results.extend(install_shiny(patched, payload))
    follower_main,follower_overlays = install_follower(patched,payload)
    results.extend(follower_main)
    overlay_changes.extend(follower_overlays)
    injection = inject_evolution(patched.arm9, original.arm9RamAddress, payload)
    results.extend(injection.changes)
    patched.arm9 = injection.image
    clock_main,clock_overlays = install_clock(patched,payload)
    results.extend(clock_main)
    overlay_changes.extend(clock_overlays)
    overlay_changes.extend(install_camera(patched,payload))
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f'{info["game"]}-visual-plus-gameplay-milestone-22'
    output = output_dir / (name + '.nds')
    patch_output = output_dir / (name + '.xdelta')
    report_output = output_dir / (name + '.json')
    encoded = patched.save()
    parsed = ndspy.rom.NintendoDSRom(encoded)
    verify_unchanged_data(original, parsed, overlay_changes, file_changes)
    verify_arm9_changes(original.arm9, parsed.arm9, original.arm9RamAddress, results, payload)
    with tempfile.TemporaryDirectory(prefix='.gameplay-', dir=output_dir) as workdir:
        work = Path(workdir)
        clean, candidate, delta, restored = [work / n for n in ('clean.nds', 'candidate.nds', 'candidate.xdelta', 'restored.nds')]
        clean.write_bytes(read_rom(source))
        candidate.write_bytes(encoded)
        subprocess.run([decoder, '-e', '-s', str(clean), str(candidate), str(delta)], check=True)
        subprocess.run([decoder, '-d', '-s', str(clean), str(delta), str(restored)], check=True)
        if sha256(restored.read_bytes()) != sha256(encoded):
            raise ValueError('Candidate patch did not reproduce the enhanced ROM.')
        for source_file, destination in ((candidate, output), (delta, patch_output)):
            if destination.exists() and sha256(destination.read_bytes()) != sha256(source_file.read_bytes()):
                raise ValueError(f'Refusing to overwrite a different candidate: {destination}')
        os.replace(candidate, output)
        os.replace(delta, patch_output)
    report = {
        'kind': 'experimental-gameplay-milestone', 'final_release': False,
        'game': info['game'], 'visual_plus_variant': 'full',
        'source_rom_sha256': info['source_rom_sha256'],
        'baseline_sha256': info['output_sha256'],
        'output_sha256': sha256(encoded),
        'patch_sha256': sha256(patch_output.read_bytes()),
        'features': [dataclasses.asdict(r) for r in results if r.feature != 'resident_code_reservation'] +
                    [dataclasses.asdict(r.patch) for r in overlay_changes],
        'code_changes': [dataclasses.asdict(r) for r in results],
        'overlay_changes': [dataclasses.asdict(r) for r in overlay_changes],
        'file_changes': [r.summary() for r in file_changes],
        'settings_storage': settings_storage,
        'repel_storage': repel_storage,
        'enhancement_menu': {'open_button': 'SELECT',
            'options': ['visible_wild', 'trade_evo', 'infinite_tms', 'repel_prompt', 'capture_exp', 'party_exp', 'field_hms', 'roaming_only_grass', 'ivs_evs', 'encounter_rate', 'shiny_odds', 'follower', 'clock_speed', 'clock_hud', 'camera_pitch', 'camera_zoom'],
            'apply': 'Save and close', 'cancel': 'B or Cancel', 'page': 'X or L/R'},
        'party_follower': {'choices': ['On', 'Off'], 'default': 'On',
                           'scope': 'Native party follower only; native map/form/shiny/party rules retained; roaming wilds independent'},
        'camera_controls': {'pitch_choices': ['Visual+', 34, 37, 40, 43, 46],
                            'pitch_default': 'Visual+', 'zoom_percentages': [90, 100, 110, 120],
                            'zoom_default': 100, 'scope': 'Native free-field perspective and orthographic views',
                            'native_tasks': 'Restore still-owned base parameters before task creation; defer native interpolation and foreign cameras',
                            'preserved': 'Native target/up/history/tracking, map base, frustum and camera renderer'},
        'world_clock': {'rates': [1, 6, 12, 24, 60, 120], 'default': 1,
                        'hud_default': 'Off', 'hud_screen': 'top field screen',
                        'scope': 'World lighting, daypart, time-dependent encounters/evolution and active-session extra Berry Pots growth',
                        'calendar': 'Native RTC/calendar, daily events and Pokegear clock retained',
                        'offline': 'Shifted world time resumes at 1x; no accelerated offline Berry growth',
                        'planting': 'Settle existing-plant bonus before native seed creation'},
        'summary_viewer': {'default': 'On', 'page': 'Skills', 'controls': {'Y':'Cycle stats/IVs/EVs','L':'EVs','R':'IVs','SELECT':'Normal stats'},
                           'data': 'Native party/raw/PC-box getters; no Pokemon or cached-stat mutation'},
        'shiny_odds': {'choices': ['1/8192', '1/4096', '1/1024', '1/256', '1/64', 'Always'], 'default': '1/8192',
                       'rolls': [1, 2, 8, 32, 128, 0], 'scope': 'New eligible wild/starters/gifts/native roamer releases; eggs/trades/fixed personalities and existing Pokemon unchanged'},
        'encounter_rate': {'choices': ['Normal', 'Off', '1/4', '1/2', '2x'], 'default': 'Normal',
                           'scope': 'Ordinary walking/surfing and visible spawn cadence; native legendary roamer decisions, fishing, scripted and special-area encounters retained',
                           'visible_spawn_interval_field_updates': [60, 0, 240, 120, 30]},
        'grass_battles': {'choices': ['Normal', 'Roaming only'], 'default': 'Normal',
                          'scope': 'Regular grass while visible wilds are enabled; other contexts remain native'},
        'diagnostics': {'visible_state_bytes': 1644, 'settings_state_bytes': 1060,
                        'menu_state_bytes': 116, 'repel_dialog_bytes': 68, 'capture_exp_state_bytes': 56, 'party_exp_state_bytes': 68, 'field_hm_state_bytes': 36, 'extra_options_bytes': 40, 'shiny_state_bytes': 40, 'visible_visual_state_bytes': 56, 'visible_habitat_state_bytes': 44, 'visible_roamer_state_bytes': 192, 'follower_state_bytes': 28, 'camera_state_bytes': 60, 'clock_state_bytes': 60, 'clock_hud_state_bytes': 48, 'encounter_rate_state_bytes': 28, 'summary_view_state_bytes': 52, 'field_bag_state_bytes': 44},
        'resident_payload': {'address': PAYLOAD_BASE, 'size': len(payload.data),
                             'sha256': sha256(payload.data),
                             'symbols': {name: value for name, value in payload.symbols.items()
                                         if name.startswith('Enhanced') or name in ('OriginalEvolution', 'gEnhancedOptions', 'gVisibleState', 'gSettingsState', 'gEnhancedMenu', 'gEnhancedRepelDialog', 'gCaptureExperience', 'gPartyExperience', 'gEnhancedExtraOptions', 'gFieldHmState', 'gFieldBagState', 'gSummaryViewState', 'gEncounterRateState', 'gShinyState', 'gVisibleVisualState', 'gVisibleHabitatState', 'gVisibleRoamerState', 'gFollowerState', 'gClockState', 'gClockHudState', 'gCameraState', '__enhanced_end')},
                             'compiler': payload.compiler, 'linker': payload.linker},
        'checks': ['baseline checksum', 'patch-site fingerprints', 'recorded ARM9 edits only',
                   'original ITCM/DTCM sections unchanged', 'resident code section round-trip',
                   'recorded overlay 1/2/12/15/17/101 changes only', 'audited native flash allocation',
                   'one guarded appended battle message; other NitroFS/ARM7/banner unchanged', 'xdelta round-trip'],
        'runtime_gameplay_tested': False,
        'limitations': ['Shiny odds cover new wild/starters/script gifts and native roamer release; existing stored identities are unchanged. Wider gift/starter/egg/trade/roamer-species acceptance remains pending.',
                       'Shiny visible wilds use native alternate palettes and brief native glints; one chime plays per new shiny spawn. Full species/form acceptance remains pending.',
                       'The enhancement menu currently exposes sixteen integrated gameplay options across three pages.',
                       'Field HMs include contextual fallback and native Bag Use Now actions for HM02/TM70; full per-move acceptance remains pending.',
                       'Roaming only suppresses hidden grass battles; active native legendary roamers can appear visibly with their saved identity and native battle bookkeeping.',
                       'Full in-game TM teaching and evolution/cancellation flows still need verification.',
                       'Bag TM quantity labels retain their original presentation.',
                       'Visible encounters cover native grass, cave/land encounter floors and surfing water; full acceptance cases remain pending.',
                       'Visible mode defaults to Few when no valid owned settings journal exists.',
                       'General spawn effects, wider roamer-species and full transition/capacity verification remain pending.',
                       'Camera view acceptance is bounded; wider map/culling/cutscene/long-play checks remain pending.',
                       'Other new Emerald enhancements remain pending.'],
    }
    report_output.write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--xdelta', default=str(ROOT / 'local_data/tools/xdelta3-3.2.2-macos-arm64/xdelta3'))
    parser.add_argument('--output', type=Path, default=ROOT / 'build/candidates')
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.rom, args.xdelta, args.output), indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Build failed: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

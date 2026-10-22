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
from build_baseline import build_baseline, read_rom, sha256


def verify_unchanged_data(original, patched, overlay_changes) -> None:
    for name in ('name', 'idCode', 'arm9RamAddress', 'arm9EntryAddress',
                 'arm7', 'arm7RamAddress', 'arm7EntryAddress',
                 'arm7OverlayTable', 'iconBanner'):
        if getattr(original, name) != getattr(patched, name):
            raise ValueError(f'Unexpected change outside gameplay code: {name}')
    if ndspy.fnt.save(original.filenames) != ndspy.fnt.save(patched.filenames):
        raise ValueError('Unexpected NitroFS filename change.')
    verify_field_files(original, patched, overlay_changes)


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
    injection = inject_evolution(patched.arm9, original.arm9RamAddress, payload)
    results.extend(injection.changes)
    patched.arm9 = injection.image
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f'{info["game"]}-visual-plus-gameplay-milestone-08'
    output = output_dir / (name + '.nds')
    patch_output = output_dir / (name + '.xdelta')
    report_output = output_dir / (name + '.json')
    encoded = patched.save()
    parsed = ndspy.rom.NintendoDSRom(encoded)
    verify_unchanged_data(original, parsed, overlay_changes)
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
                    [dataclasses.asdict(r.patch) for r in repel_changes + capture_changes],
        'code_changes': [dataclasses.asdict(r) for r in results],
        'overlay_changes': [dataclasses.asdict(r) for r in overlay_changes],
        'settings_storage': settings_storage,
        'repel_storage': repel_storage,
        'enhancement_menu': {'open_button': 'SELECT',
            'options': ['visible_wild', 'trade_evo', 'infinite_tms', 'repel_prompt', 'capture_exp'],
            'apply': 'Save and close', 'cancel': 'B or Cancel'},
        'diagnostics': {'visible_state_bytes': 1640, 'settings_state_bytes': 1060,
                        'menu_state_bytes': 68, 'repel_dialog_bytes': 68, 'capture_exp_state_bytes': 56},
        'resident_payload': {'address': PAYLOAD_BASE, 'size': len(payload.data),
                             'sha256': sha256(payload.data),
                             'symbols': {name: value for name, value in payload.symbols.items()
                                         if name.startswith('Enhanced') or name in ('OriginalEvolution', 'gEnhancedOptions', 'gVisibleState', 'gSettingsState', 'gEnhancedMenu', 'gEnhancedRepelDialog', 'gCaptureExperience', '__enhanced_end')},
                             'compiler': payload.compiler, 'linker': payload.linker},
        'checks': ['baseline checksum', 'patch-site fingerprints', 'recorded ARM9 edits only',
                   'original ITCM/DTCM sections unchanged', 'resident code section round-trip',
                   'recorded overlay 1/2/12/15 changes only', 'audited native flash allocation',
                   'other NitroFS/ARM7/banner unchanged', 'xdelta round-trip'],
        'runtime_gameplay_tested': False,
        'limitations': ['The enhancement menu currently exposes five integrated gameplay options.',
                       'Full in-game TM teaching and evolution/cancellation flows still need verification.',
                       'Bag TM quantity labels retain their original presentation.',
                       'Visible encounters are an experimental grass integration; full acceptance cases remain pending.',
                       'Visible mode defaults to Few when no valid owned settings journal exists.',
                       'Cave/water encounters, spawn effects, sparkle and full transition/capacity verification remain pending.',
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

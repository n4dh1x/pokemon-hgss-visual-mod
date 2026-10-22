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
from build_baseline import build_baseline, read_rom, sha256


def verify_unchanged_data(original, patched) -> None:
    for name in ('name', 'idCode', 'arm9RamAddress', 'arm9EntryAddress',
                 'arm7', 'arm7RamAddress', 'arm7EntryAddress',
                 'arm9OverlayTable', 'arm7OverlayTable', 'iconBanner'):
        if getattr(original, name) != getattr(patched, name):
            raise ValueError(f'Unexpected change outside gameplay code: {name}')
    if original.files != patched.files or ndspy.fnt.save(original.filenames) != ndspy.fnt.save(patched.filenames):
        raise ValueError('Unexpected NitroFS file or filename change.')


def build(source: Path, decoder: str, output_dir: Path) -> dict:
    baseline_dir = ROOT / 'build/baseline'
    info = build_baseline(source, 'full', decoder, baseline_dir)
    baseline = baseline_dir / info['output']
    original = ndspy.rom.NintendoDSRom.fromFile(baseline)
    arm9 = bytearray(original.arm9)
    results = [reusable_tms(arm9, original.arm9RamAddress)]
    payload = build_payload()
    injection = inject_evolution(bytes(arm9), original.arm9RamAddress, payload)
    results.extend(injection.changes)
    patched = ndspy.rom.NintendoDSRom.fromFile(baseline)
    patched.arm9 = injection.image
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f'{info["game"]}-visual-plus-gameplay-milestone-02'
    output = output_dir / (name + '.nds')
    patch_output = output_dir / (name + '.xdelta')
    report_output = output_dir / (name + '.json')
    encoded = patched.save()
    parsed = ndspy.rom.NintendoDSRom(encoded)
    verify_unchanged_data(original, parsed)
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
        'features': [dataclasses.asdict(r) for r in results if r.feature != 'resident_code_reservation'],
        'code_changes': [dataclasses.asdict(r) for r in results],
        'resident_payload': {'address': PAYLOAD_BASE, 'size': len(payload.data),
                             'sha256': sha256(payload.data),
                             'symbols': {name: value for name, value in payload.symbols.items()
                                         if name in ('EnhancedEvolution', 'OriginalEvolution', 'gEnhancedOptions', '__enhanced_end')},
                             'compiler': payload.compiler, 'linker': payload.linker},
        'checks': ['baseline checksum', 'patch-site fingerprints', 'recorded ARM9 edits only',
                   'original ITCM/DTCM sections unchanged', 'resident code section round-trip',
                   'NitroFS/overlays/ARM7/banner unchanged', 'xdelta round-trip'],
        'runtime_gameplay_tested': False,
        'limitations': ['Reusable TMs currently enabled at build time; runtime UI pending.',
                       'Trade evolution option is enabled in resident config; runtime UI pending.',
                       'Full in-game TM teaching and evolution/cancellation flows still need verification.',
                       'Bag TM quantity labels retain their original presentation.',
                       'All other new Emerald enhancements remain pending.'],
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

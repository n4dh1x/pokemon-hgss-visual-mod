#!/usr/bin/env python3
"""Build and verify an unchanged upstream Visual+ reference from a local USA ROM.

This command does not add the planned Emerald gameplay enhancements. It accepts
the user's NDS file or a ZIP holding one NDS file and never modifies the input.
It uses shipped USA xdelta patches; no Korean donor ROM is needed for this step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_rom(path: Path) -> bytes:
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            candidates = [i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith('.nds')]
            if len(candidates) != 1:
                raise ValueError('The ZIP must contain exactly one NDS ROM.')
            if candidates[0].file_size != 128 * 1024 * 1024:
                raise ValueError('Expected a full 128 MiB USA HGSS ROM.')
            return archive.read(candidates[0])
    if path.stat().st_size != 128 * 1024 * 1024:
        raise ValueError('Expected a full 128 MiB USA HGSS ROM.')
    return path.read_bytes()


def select_build(rom: bytes, variant: str, manifest: dict) -> dict:
    digest = sha256(rom)
    for build in manifest['builds']:
        if build['variant'] == variant and build['source_rom_sha256'] == digest:
            code = {'heartgold': b'IPKE', 'soulsilver': b'IPGE'}[build['game']]
            if rom[12:16] != code:
                raise ValueError('ROM game code disagrees with its recorded checksum.')
            return build
    raise ValueError('ROM checksum is not a supported clean USA HeartGold/SoulSilver dump.')


def build_baseline(source: Path, variant: str, decoder: str, output_dir: Path) -> dict:
    rom = read_rom(source)
    manifest = json.loads((ROOT / 'release/release_manifest.json').read_text())
    build = select_build(rom, variant, manifest)
    patch = ROOT / build['patch']
    if sha256(patch.read_bytes()) != build['patch_sha256']:
        raise ValueError(f'Release patch checksum mismatch: {patch.name}')
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f'{build["game"]}-visual-plus-{variant}-baseline.nds'
    if output.resolve() == source.resolve():
        raise ValueError('The output must not replace the source ROM.')
    if output.exists():
        if sha256(output.read_bytes()) != build['patched_rom_sha256']:
            raise ValueError(f'Refusing to replace a different existing output: {output}')
    else:
        with tempfile.TemporaryDirectory(prefix='.visual-baseline-', dir=output_dir) as work:
            work = Path(work)
            clean, patched = work / 'clean.nds', work / 'patched.nds'
            clean.write_bytes(rom)
            subprocess.run([decoder, '-d', '-s', str(clean), str(patch), str(patched)], check=True)
            if sha256(patched.read_bytes()) != build['patched_rom_sha256']:
                raise ValueError('Patched ROM does not match the upstream reference checksum.')
            os.replace(patched, output)
    result = {
        'kind': 'upstream-visual-plus-reference-only',
        'new_emerald_gameplay_features': False,
        'game': build['game'], 'variant': variant,
        'source_rom_sha256': sha256(rom),
        'patch_sha256': build['patch_sha256'],
        'output_sha256': build['patched_rom_sha256'],
        'output': output.name,
    }
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--variant', choices=['full', 'conservative-camera', 'safe', 'visual-only'], default='full')
    local_decoder = ROOT / 'local_data/tools/xdelta3-3.2.2-macos-arm64/xdelta3'
    parser.add_argument('--xdelta', default=shutil.which('xdelta3') or str(local_decoder))
    parser.add_argument('--output', type=Path, default=ROOT / 'build/baseline')
    args = parser.parse_args()
    try:
        result = build_baseline(args.rom, args.variant, args.xdelta, args.output)
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Build failed: {exc}\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

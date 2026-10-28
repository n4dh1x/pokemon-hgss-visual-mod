#!/usr/bin/env python3
"""Reclaim generated storage while keeping builds reproducible and evidence intact.

Preview is the CLI default. Old generated ROMs are removed only after their
retained patch actually reconstructs the exact bytes. macOS filesystem
compression keeps snapshot paths and byte contents unchanged.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
STEM = re.compile(r'^(heartgold|soulsilver)-visual-plus-gameplay-milestone-(\d+)$')
DIGEST = re.compile(r'^[0-9a-f]{64}$')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.cleanup-', delete=False) as out:
        temporary = Path(out.name)
        out.write((json.dumps(value, indent=2) + '\n').encode())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def input_bytes(path):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            files = [f for f in archive.infolist() if not f.is_dir() and f.filename.lower().endswith('.nds')]
            if len(files) != 1:
                raise ValueError('Input ZIP must contain exactly one NDS ROM.')
            return archive.read(files[0])
    return path.read_bytes()


def within_regular(path, boundary):
    return (not path.is_symlink() and path.is_file() and
            path.resolve().is_relative_to(boundary.resolve()))


def has_companion_save(rom):
    for directory in (rom.parent, rom.parent / 'save', rom.parent / 'saves'):
        for suffix in ('.sav', '.dsv', '.srm', '.state'):
            if any(directory.glob(rom.stem + suffix + '*')):
                return True
    return False


def artifacts(root):
    build = root / 'build'
    reports = list((build / 'candidates').glob('*.json'))
    reports += list((build / 'experiments').glob('*/*.json'))
    result = []
    for report in sorted(reports):
        match = STEM.fullmatch(report.stem)
        if not match or not within_regular(report, build):
            continue
        try:
            data = json.loads(report.read_text())
        except (ValueError, OSError):
            continue
        if (data.get('kind') != 'experimental-gameplay-milestone' or
                data.get('game') != match[1] or
                not all(DIGEST.fullmatch(str(data.get(key, ''))) for key in
                        ('output_sha256', 'patch_sha256', 'source_rom_sha256'))):
            continue
        result.append((int(match[2]), report, data))
    return result


def retained_milestones(root, records):
    keep = set(sorted({number for number, _, _ in records})[-2:])
    verified = []
    for path in (root / 'enhancements').glob('milestone-*-verification.json'):
        try:
            data = json.loads(path.read_text())
            if data.get('kind') == 'bounded-local-gameplay-verification' and isinstance(data.get('milestone'), int):
                verified.append(data['milestone'])
        except (ValueError, OSError):
            continue
    if verified:
        keep.add(max(verified))
    return keep


def live_verification():
    """Conservatively skip snapshot maintenance if process inventory is unavailable."""
    import shlex
    try:
        lines = subprocess.check_output(['/bin/ps', '-axo', 'command='], text=True).splitlines()
        for line in lines:
            try:
                words = shlex.split(line)
            except ValueError:
                continue
            if words and Path(words[0]).name.startswith('python'):
                if any(Path(word).name == 'smoke_libretro.py' for word in words[1:4]):
                    return True
        return False
    except (OSError, subprocess.CalledProcessError):
        return True


def compress_copy(path, directory):
    """Replace only a verified, unchanged original with a smaller transparent copy."""
    before = path.stat()
    if getattr(before, 'st_flags', 0) & getattr(stat, 'UF_COMPRESSED', 32):
        return 0
    if before.st_size < 65536:
        return 0
    digest = sha(path)
    with tempfile.TemporaryDirectory(prefix='.compress-', dir=directory) as work:
        compressed = Path(work) / path.name
        subprocess.run(['/usr/bin/ditto', '--hfsCompression', '--noclone', str(path), str(compressed)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        current = path.stat()
        identity = lambda value: (value.st_ino, value.st_size, value.st_mtime_ns)
        if identity(before) != identity(current):
            raise ValueError(f'File changed during cleanup; left untouched: {path}')
        after = compressed.stat()
        if after.st_size != before.st_size or sha(compressed) != digest:
            raise ValueError(f'Compression did not preserve bytes; left untouched: {path}')
        saved = before.st_blocks * 512 - after.st_blocks * 512
        if not getattr(after, 'st_flags', 0) & getattr(stat, 'UF_COMPRESSED', 32) or saved <= 0:
            return 0
        os.replace(compressed, path)
        return saved


def cleanup(root=ROOT, *, sources=(), decoder=None, apply=False, compress=True):
    root = Path(root).resolve()
    if not (root / 'native/config.h').is_file():
        raise ValueError('Cleanup requires the HGSS project root.')
    build = root / 'build'
    for directory in (build, root / 'local_data'):
        if directory.is_symlink() or not directory.resolve().is_relative_to(root):
            raise ValueError('Cleanup refuses redirected generated directories.')
    records = artifacts(root)
    keep = retained_milestones(root, records)
    registry_path = root / 'local_data/cleanup/inputs.json'
    try:
        registry = json.loads(registry_path.read_text())
    except (OSError, ValueError):
        registry = {}
    known = dict(registry.get('sources', {}))
    for source in sources:
        source = Path(source).resolve()
        known[hashlib.sha256(input_bytes(source)).hexdigest()] = str(source)
    decoder = decoder or shutil.which('xdelta3') or str(root / 'local_data/tools/xdelta3-3.2.2-macos-arm64/xdelta3')
    summary = {'kept_milestones': sorted(keep), 'removed_roms': [], 'removed_temporary_files': [],
               'compressed_snapshots': 0, 'reclaimed_bytes': 0, 'deferred': []}
    protected = {Path(value).resolve() for value in known.values()}
    busy = apply and live_verification()
    cache = {}
    work_parent = root / 'local_data/cleanup'
    if apply:
        work_parent.mkdir(parents=True, exist_ok=True)
        atomic_json(registry_path, {'sources': known})
    for number, report, data in records:
        rom, patch = report.with_suffix('.nds'), report.with_suffix('.xdelta')
        if number in keep or not within_regular(rom, build):
            continue
        if busy or rom.resolve() in protected or has_companion_save(rom):
            summary['deferred'].append(str(rom.relative_to(root)))
            continue
        if not within_regular(patch, build) or sha(rom) != data['output_sha256'] or sha(patch) != data['patch_sha256']:
            summary['deferred'].append(str(rom.relative_to(root)))
            continue
        source = known.get(data['source_rom_sha256'])
        if not source or not Path(source).is_file():
            summary['deferred'].append(str(rom.relative_to(root)))
            continue
        if not apply:
            summary['removed_roms'].append(str(rom.relative_to(root)))
            continue
        digest = data['source_rom_sha256']
        if digest not in cache:
            cache[digest] = input_bytes(source)
            if hashlib.sha256(cache[digest]).hexdigest() != digest:
                raise ValueError(f'Original ROM changed; cleanup refused: {source}')
        with tempfile.TemporaryDirectory(prefix='.restore-check-', dir=work_parent) as work:
            clean, restored = Path(work)/'clean.nds', Path(work)/'restored.nds'
            clean.write_bytes(cache[digest])
            subprocess.run([decoder, '-d', '-s', str(clean), str(patch), str(restored)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if sha(restored) != data['output_sha256']:
                raise ValueError(f'Patch could not reproduce old ROM; left untouched: {rom}')
        # Revalidate the exact old file before deleting it. Patches/reports stay.
        if sha(rom) != data['output_sha256']:
            raise ValueError(f'Old ROM changed during cleanup; left untouched: {rom}')
        summary['reclaimed_bytes'] += rom.stat().st_blocks * 512
        rom.unlink()
        summary['removed_roms'].append(str(rom.relative_to(root)))
        if len(summary['removed_roms']) % 10 == 0:
            print(f"Cleanup: verified/pruned {len(summary['removed_roms'])} reproducible ROMs", file=sys.stderr, flush=True)
    garbage = list((build / 'native').glob('*.o'))
    for base in (build, root / 'local_data'):
        garbage += list(base.rglob('.DS_Store'))
    for path in garbage:
        if not within_regular(path, root):
            continue
        summary['removed_temporary_files'].append(str(path.relative_to(root)))
        if apply:
            summary['reclaimed_bytes'] += path.stat().st_blocks * 512
            path.unlink()
    if compress and sys.platform == 'darwin' and apply:
        if busy:
            summary['deferred'].append('Snapshot compression: active verification or process inventory unavailable.')
        else:
            for run in sorted((root / 'local_data/verification').glob('*')):
                if run.is_symlink() or not run.is_dir() or not (run / 'state.json').is_file():
                    continue
                for name in ('state.bin', 'main-ram.bin'):
                    path = run / name
                    if within_regular(path, root / 'local_data/verification'):
                        saved = compress_copy(path, work_parent)
                        if saved:
                            summary['compressed_snapshots'] += 1
                            summary['reclaimed_bytes'] += saved
                            if summary['compressed_snapshots'] % 100 == 0:
                                print(f"Cleanup: compressed {summary['compressed_snapshots']} snapshots", file=sys.stderr, flush=True)
    if apply:
        atomic_json(root / 'local_data/cleanup/last-run.json', summary)
    return summary


@contextmanager
def after_build(source, decoder=None):
    try:
        yield
    finally:
        failure = sys.exc_info()[0] is not None
        try:
            result = cleanup(sources=[source], decoder=decoder, apply=True)
            print(f"Build cleanup: reclaimed {result['reclaimed_bytes']/1024**3:.2f} GiB; "
                  f"kept milestones {result['kept_milestones']}.", file=sys.stderr)
        except Exception as exc:
            if not failure:
                raise
            print(f'Build cleanup also failed: {exc}', file=sys.stderr)


def restore_rom(report, root=ROOT, *, sources=(), decoder=None):
    root, report = Path(root).resolve(), Path(report).resolve()
    matches = [(path, data) for _, path, data in artifacts(root) if path.resolve() == report]
    if len(matches) != 1:
        raise ValueError('Restore requires a recognized generated build report.')
    report, data = matches[0]
    target, patch = report.with_suffix('.nds'), report.with_suffix('.xdelta')
    if target.exists():
        if target.is_symlink() or sha(target) != data['output_sha256']:
            raise ValueError('Restore refuses to replace a different existing ROM.')
        return {'restored': str(target), 'sha256': data['output_sha256']}
    if not within_regular(patch, root / 'build') or sha(patch) != data['patch_sha256']:
        raise ValueError('Restore patch is missing or changed.')
    registry_path = root / 'local_data/cleanup/inputs.json'
    try:
        known = json.loads(registry_path.read_text()).get('sources', {})
    except (OSError, ValueError):
        known = {}
    for source in sources:
        known[hashlib.sha256(input_bytes(source)).hexdigest()] = str(Path(source).resolve())
    source = known.get(data['source_rom_sha256'])
    if not source or not Path(source).is_file():
        raise ValueError('Original ROM unavailable; supply it using --rom.')
    original = input_bytes(source)
    if hashlib.sha256(original).hexdigest() != data['source_rom_sha256']:
        raise ValueError('Original ROM checksum changed; restore refused.')
    decoder = decoder or shutil.which('xdelta3') or str(root / 'local_data/tools/xdelta3-3.2.2-macos-arm64/xdelta3')
    with tempfile.TemporaryDirectory(prefix='.restore-', dir=target.parent) as work:
        clean, restored = Path(work) / 'clean.nds', Path(work) / 'restored.nds'
        clean.write_bytes(original)
        subprocess.run([decoder, '-d', '-s', str(clean), str(patch), str(restored)], check=True)
        if sha(restored) != data['output_sha256']:
            raise ValueError('Restored ROM checksum differs; output refused.')
        os.replace(restored, target)
    return {'restored': str(target), 'sha256': data['output_sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply cleanup; without this flag only preview ROM pruning.')
    parser.add_argument('--rom', type=Path, action='append', default=[], help='Original clean NDS or ZIP; never modified.')
    parser.add_argument('--xdelta', help='Path to xdelta3.')
    parser.add_argument('--no-compress', action='store_true')
    parser.add_argument('--restore-rom', type=Path, help='Recreate an older ROM from its retained JSON report and patch.')
    args = parser.parse_args()
    if args.restore_rom:
        result = restore_rom(args.restore_rom, sources=args.rom, decoder=args.xdelta)
    else:
        result = cleanup(sources=args.rom, decoder=args.xdelta, apply=args.apply,
                         compress=not args.no_compress)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

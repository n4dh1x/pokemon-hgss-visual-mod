#!/usr/bin/env python3
"""Validate the HGSS inventory against the actual Emerald option definitions."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def emerald_keys(root: Path) -> set[str]:
    extras = (root / '3ds_port/src/3ds_extras.c').read_text()
    keys = set()
    for line in extras.splitlines():
        if line.strip().startswith('{CTR_EXTRAS'):
            match = re.search(r'CTR_TEXT\(.*?\),\s*"([a-z0-9_]+)"', line)
            if match is None:
                raise ValueError(f'Unparsed option definition: {line.strip()}')
            keys.add(match[1])
    settings = (root / '3ds_port/src/3ds_settings.c').read_text()
    start = settings.index('void CtrSettings_ApplyLine(')
    end = settings.index('void CtrSettings_Load(', start)
    keys.update(re.findall(r'"([a-z0-9_]+)=(?:%d)?"', settings[start:end]))
    return keys


def validate_inventory(data: dict, expected_keys: set[str] | None = None) -> list[str]:
    errors = []
    features = data['features']
    ids = Counter(row['id'] for row in features)
    assigned = Counter(key for row in features for key in row['emerald_keys'])
    for key, count in ids.items():
        if count != 1:
            errors.append(f'Duplicate feature ID: {key}')
    for key, count in assigned.items():
        if count != 1:
            errors.append(f'Option assigned more than once: {key}')
    for row in features:
        if row['category'] not in data['categories']:
            errors.append(f'Unknown category for {row["id"]}')
        for field in ('base_heartgold', 'visual_plus', 'required_work', 'evidence'):
            if not row[field]:
                errors.append(f'Missing {field}: {row["id"]}')
        allowed = {'existing', 'not_integrated', 'integrated_untested', 'verified'}
        if row['implementation'] not in allowed:
            errors.append(f'Unknown implementation state: {row["id"]}')
    if expected_keys is not None:
        errors.extend(f'Missing Emerald option: {k}' for k in sorted(expected_keys - assigned.keys()))
        errors.extend(f'Unknown Emerald option: {k}' for k in sorted(assigned.keys() - expected_keys))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=ROOT / 'enhancements/inventory.json')
    parser.add_argument('--emerald-source', type=Path)
    args = parser.parse_args()
    data = json.loads(args.inventory.read_text())
    expected = emerald_keys(args.emerald_source) if args.emerald_source else None
    errors = validate_inventory(data, expected)
    if args.emerald_source:
        for name, digest in data['sources']['emerald']['files'].items():
            if hashlib.sha256((args.emerald_source / name).read_bytes()).hexdigest() != digest:
                errors.append(f'Pinned Emerald source changed: {name}')
    if errors:
        print('\n'.join(errors))
        return 1
    assigned = {key for row in data['features'] for key in row['emerald_keys']}
    print(f'OK: {len(data["features"])} feature rows; {len(assigned)} option keys covered.')
    for category, count in sorted(Counter(r['category'] for r in data['features']).items()):
        print(f'  {data["categories"][category]}: {count}')
    print('Coverage validation does not prove gameplay integration.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

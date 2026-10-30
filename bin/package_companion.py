#!/usr/bin/env python3
"""Package only the optional companion's public files, deterministically."""
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = ('main.js', 'styles.css', 'manifest.json', 'README.md', 'LICENSE')

def package(root=ROOT):
    metadata = json.loads((root / 'companion/manifest.json').read_text())
    plugin_id, version = metadata['id'], metadata['version']
    if not re.fullmatch(r'[a-z0-9-]+', plugin_id) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('unsafe package id/version')
    out = root / 'dist' / f'{plugin_id}-{version}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out, 'w') as archive:
        for name in PUBLIC_FILES:
            source = root / 'LICENSE' if name == 'LICENSE' else root / 'companion' / name
            entry = ZipInfo(f'{plugin_id}/{name}', (2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, source.read_bytes())
    return out

if __name__ == '__main__':
    print(package())

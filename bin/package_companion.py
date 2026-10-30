#!/usr/bin/env python3
"""Package only the optional companion's public files, deterministically."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
ROOT = Path(__file__).resolve().parent.parent
out = ROOT / 'dist/omarchy-writing-0.1.0.zip'
out.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(out, 'w') as archive:
    for name in ('main.js', 'styles.css', 'manifest.json', 'README.md', 'LICENSE'):
        source = ROOT / 'LICENSE' if name == 'LICENSE' else ROOT / 'companion' / name
        entry = ZipInfo('omarchy-writing/' + name, (2026, 1, 1, 0, 0, 0))
        entry.compress_type = ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, source.read_bytes())
print(out)

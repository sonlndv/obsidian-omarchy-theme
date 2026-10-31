#!/usr/bin/env python3
"""Create the explicitly installed Mounty distribution from reviewed root files."""
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = ('theme.css', 'manifest.json', 'OFL-Geist.txt', 'OFL-SpaceMono.txt', 'LICENSE')
NAME = 'Mounty'

def package(root=ROOT):
    metadata = json.loads((root/'manifest.json').read_text())
    if metadata['name'] != 'Omarchy' or not re.fullmatch(r'\d+\.\d+\.\d+', metadata['version']):
        raise ValueError('expected the compatible Omarchy updater manifest')
    metadata['name'] = NAME
    contents = {name: (root/name).read_bytes() for name in PUBLIC_FILES}
    contents['manifest.json'] = (json.dumps(metadata, indent=2)+'\n').encode()
    directory = root/'dist'/NAME
    directory.mkdir(parents=True, exist_ok=True)
    out = root/'dist'/f'{NAME}-{metadata["version"]}.zip'
    with ZipFile(out, 'w') as archive:
        for name in PUBLIC_FILES:
            (directory/name).write_bytes(contents[name])
            entry = ZipInfo(f'{NAME}/{name}', (2026,1,1,0,0,0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, contents[name])
    return out

if __name__ == '__main__':
    print(package())

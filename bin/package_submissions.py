#!/usr/bin/env python3
"""Export two standalone, root-ready public source archives; never install."""
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
THEME_FILES = {
    'manifest.json': 'manifest.json',
    'README.md': 'docs/submissions/Mounty-README.md',
    'LICENSE': 'LICENSE',
    'theme.css': 'theme.css',
    'screenshot.png': 'docs/images/mounty-dark.png',
    'OFL-Geist.txt': 'OFL-Geist.txt',
    'OFL-SpaceMono.txt': 'OFL-SpaceMono.txt',
    'docs/images/mounty-light.png': 'docs/images/mounty-light.png',
    'docs/GRAPH-COLOURS.md': 'docs/GRAPH-COLOURS.md',
    'docs/MIGRATING-TO-MOUNTY.md': 'docs/MIGRATING-TO-MOUNTY.md',
    'docs/COMMUNITY-LISTINGS.md': 'docs/COMMUNITY-LISTINGS.md',
}
PLUGIN_FILES = {
    'manifest.json': 'companion/manifest.json',
    'README.md': 'docs/submissions/Mounty-Zen-README.md',
    'LICENSE': 'LICENSE',
    'main.js': 'companion/main.js',
    'styles.css': 'companion/styles.css',
    'docs/images/mounty-writing-tools.png': 'docs/images/mounty-writing-tools.png',
    'docs/images/mounty-zen.png': 'docs/images/mounty-zen.png',
    'docs/MIGRATING-TO-MOUNTY.md': 'docs/MIGRATING-TO-MOUNTY.md',
    'docs/COMMUNITY-LISTINGS.md': 'docs/COMMUNITY-LISTINGS.md',
}

def _version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('unsafe manifest version')
    return value


def _write(root, filename, files, manifest):
    contents = {destination: (root/source).read_bytes() for destination, source in files.items()}
    contents['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output = root/'dist'/filename
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w') as archive:
        for name, data in contents.items():
            entry = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return output


def package(root=ROOT):
    theme = json.loads((root/'manifest.json').read_text())
    plugin = json.loads((root/'companion/manifest.json').read_text())
    if theme.get('name') != 'Omarchy':
        raise ValueError('expected the supported Omarchy updater root')
    if (plugin.get('name'), plugin.get('id')) != ('Mounty Zen', 'omarchy-writing'):
        raise ValueError('expected Mounty Zen with the stable plugin ID')
    theme_version = _version(theme['version'])
    plugin_version = _version(plugin['version'])
    theme['name'] = 'Mounty'
    return (
        _write(root, f'Mounty-{theme_version}-submission-source.zip', THEME_FILES, theme),
        _write(root, f'Mounty-Zen-{plugin_version}-submission-source.zip', PLUGIN_FILES, plugin),
    )

if __name__ == '__main__':
    for path in package():
        print(path)

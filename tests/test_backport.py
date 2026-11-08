"""Source parity and pure synthetic palette regressions; no host/installer calls."""
import hashlib
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from test_build import ROOT, build, variables


class BackportTest(unittest.TestCase):
    def test_normal_hash_and_authored_layer_without_external_reads(self):
        read_text = pathlib.Path.read_text

        def source_read(path, *args, **kwargs):
            self.assertTrue(path.resolve().is_relative_to(ROOT), str(path))
            return read_text(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(pathlib.Path, 'read_text', source_read):
                _, body = build.build(tmp)
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),
                             '1fd377383c95caf51c276da198a1f72d08870861daebb8526392007427083f88')
            part = (ROOT / 'src/parts/emphasis.css').read_text()
            self.assertTrue(body.endswith(part))
            self.assertEqual(body.count(part), 1)
            self.assertNotIn(str(ROOT.parent), body)
            self.assertEqual((pathlib.Path(tmp) / 'manifest.json').read_text(),
                             build.manifest('Omarchy'))

    def test_accepted_roles(self):
        body = build.sonwork_css()
        for scheme, bold, italic, mint, unresolved in (
                ('dark', '#f5a67d', '#c4b5fd', '#83d5b4', '#c7bca4'),
                ('light', '#96502a', '#6c4b99', '#22684e', '#6e6044')):
            v = variables(body, scheme)
            for role, value in {'bold-color': bold, 'inline-code-color': bold,
                                'italic-color': italic, 'h4-color': mint,
                                'underline-color': mint, 'graph-node-focused': bold,
                                'graph-node-tag': mint, 'graph-node-attachment': italic,
                                'graph-node-unresolved': unresolved,
                                'graph-node': v['text-accent'],
                                'strikethrough-color': v['text-faint'],
                                'blockquote-border-color': v['text-accent']}.items():
                self.assertEqual(v[role], value, (scheme, role))
            self.assertEqual(v['blockquote-background-color'],
                             f"rgba({build.rgb(v['text-accent'])}, {0.05 if scheme == 'dark' else 0.04})")

    def test_generic_palette_values_and_local_consumers(self):
        additions = {'inline-code-color', 'underline-color', 'strikethrough-color',
                     'blockquote-background-color'}
        for scheme, path, expected, count in (
                ('dark', build.COLORS, '118b898ee46122dd9da41fa76211bd26559f762cc247fc1c15312f322d3ca44d', 69),
                ('light', build.LIGHT_COLORS, '7d13e81cc5e76ab3f047f46853c1a432dde9fb7f0ffc34ba9d568953c8094cbb', 71)):
            palette = build.read_colors(path)
            v = variables(build.css(palette, scheme), scheme)
            original = {k: value for k, value in v.items() if k not in additions}
            self.assertEqual(len(original), count)
            # Frozen digest of every pre-backport generic declaration, not CSS bytes.
            self.assertEqual(hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(), expected)
            self.assertEqual(v['underline-color'], palette['green'])
            self.assertEqual(v['h4-color'], palette['green'])
            self.assertEqual(v['inline-code-color'], palette['foreground'])
            self.assertEqual(v['strikethrough-color'], palette['dark_foreground'])
            self.assertEqual(v['blockquote-border-color'], palette['accent'])
            for name in additions:
                self.assertNotIn('var(', v[name])
            typography = (ROOT / 'src/sonwork/typography.css').read_text()
            local = re.search(r'\.markdown-preview-view,\s*\.markdown-source-view\.mod-cm6\s*\{([^}]+)\}', typography).group(1)
            self.assertIn('--h4-color: var(--underline-color);', local)
            self.assertIn('--blockquote-border-color: var(--text-accent);', local)
            # Note-local H4 resolves its literal inherited underline first. Heading
            # overrides then inherit resolved H4, so underline -> H4 is not cyclic.
            resolved_h4 = v['underline-color']
            self.assertRegex(resolved_h4, r'^#[0-9a-f]{6}$')
            part = (ROOT / 'src/parts/emphasis.css').read_text()
            for level in range(1, 7):
                heading = re.search(r'\.HyperMD-header-' + str(level) + r'\s*\{([^}]+)\}', part).group(1)
                for role in ('bold', 'italic', 'inline-code', 'underline', 'strikethrough'):
                    self.assertIn(f'--{role}-color: var(--h{level}-color);', heading)

    def test_synthetic_both_schemes_roundtrip_and_identity(self):
        originals = {name: (ROOT / name).read_bytes() for name in ('theme.css', 'manifest.json')}
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _, normal = build.build(root / 'normal')
            for scheme, source in (('dark', build.COLORS), ('light', build.LIGHT_COLORS)):
                path = root / f'{scheme}.toml'
                path.write_text(source.read_text().replace(build.read_colors(source)['accent'], '#123456'))
                _, first = build.build(root / 'first', path)
                _, second = build.build(root / 'second', path)
                self.assertEqual(first, second)
                other = 'light' if scheme == 'dark' else 'dark'
                block = lambda text: re.search(r'\.theme-' + other + r'\s*\{[^}]*\}', text).group()
                self.assertEqual(block(first), block(normal))
                self.assertEqual(variables(first, scheme)['text-accent'], '#123456')
                for name in ('underline-color', 'inline-code-color', 'strikethrough-color', 'blockquote-background-color'):
                    self.assertNotIn('var(', variables(first, scheme)[name])
                self.assertEqual((root / 'first/manifest.json').read_bytes(), originals['manifest.json'])
                _, restored = build.build(root / 'restored')
                self.assertEqual(restored, normal)
        for name, content in originals.items():
            self.assertEqual((ROOT / name).read_bytes(), content)

    def test_all_heading_weights_and_scoped_formatted_children(self):
        typography = (ROOT / 'src/sonwork/typography.css').read_text()
        for level in range(1, 7):
            self.assertIn(f'--h{level}-weight: 700;', typography)
            self.assertIn(f'.HyperMD-header-{level}', typography)
        self.assertIn('--bold-weight: 600;', typography)
        scope = typography.split('/* Heading emphasis follows')[1]
        self.assertIn('.markdown-rendered :is(h1, h2, h3, h4, h5, h6) *', scope)
        self.assertIn('font-weight: 700;', scope)
        self.assertIn('--bold-weight: 700;', scope)
        self.assertNotIn('!important', scope)
        self.assertNotIn('font-family:', scope)
        self.assertNotIn('color:', scope)

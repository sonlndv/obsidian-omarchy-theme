"""Candidate contracts; the legacy suite remains unchanged."""
import base64
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from test_build import build, contrast, variables

ROOT = pathlib.Path(__file__).resolve().parent.parent


class SonworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = build.sonwork_css()
        cls.palette = json.loads((ROOT / 'src/sonwork/palette.json').read_text())

    def test_semantic_palettes_and_neutral_headings(self):
        roles = {'background-primary': 'void', 'background-secondary': 'ground',
                 'code-background': 'raise', 'text-normal': 'ink',
                 'text-muted': 'ink-2', 'text-faint': 'ink-3',
                 'link-color': 'lume', 'interactive-accent': 'lume',
                 'caret-color': 'lume', 'text-on-accent': 'lume-ink',
                 'callout-warning': 'human', 'callout-note': 'lume'}
        expected = {
            'dark': ('#02050d', '#050b16', '#0c1621', '#f0f4f7', '#abb2ba', '#8a939e', '#39d0fc'),
            'light': ('#f8fafd', '#eef3f8', '#e4eaf1', '#0b1421', '#333e4c', '#515c68', '#006cac'),
        }
        for scheme in ('dark', 'light'):
            c = {k: v['hex'] for k, v in self.palette['modes'][scheme].items()}
            self.assertEqual(tuple(c[k] for k in ('void', 'ground', 'raise', 'ink', 'ink-2', 'ink-3', 'lume')), expected[scheme])
            values = variables(self.css, scheme)
            for role, token in roles.items():
                self.assertEqual(values[role], c[token], (scheme, role))
            for level in range(1, 7):
                self.assertEqual(values[f'h{level}-color'], c['ink'])
            self.assertIn('rgba(', values['text-selection'])
            self.assertIn('outline: 2px solid var(--interactive-accent)', self.css)

    def test_small_text_and_action_contrast(self):
        for scheme in ('dark', 'light'):
            v = variables(self.css, scheme)
            for surface in ('background-primary', 'background-secondary', 'code-background'):
                for name in ('text-normal', 'text-muted', 'text-faint', 'link-color',
                             'code-comment', 'h4-color', 'h5-color', 'h6-color', 'callout-warning'):
                    self.assertGreaterEqual(contrast(v[name], v[surface]), 4.5, (scheme, name, surface))
            self.assertGreaterEqual(contrast(v['text-on-accent'], v['interactive-accent']), 4.5)
            for name, opacity in (('text-selection', .18), ('text-highlight-bg', .14)):
                for surface in ('background-primary', 'background-secondary'):
                    composite = build.mix_hex(v[surface], v['interactive-accent'], opacity)
                    self.assertGreaterEqual(contrast(v['text-normal'], composite), 4.5)

    def test_original_fonts_and_licenses_embedded(self):
        faces = re.findall(r'@font-face\s*\{([^}]+)\}', self.css)
        self.assertEqual(len(faces), 8)
        for face in faces:
            family = 'geist' if "'Geist Sonwork'" in face else 'space-mono'
            weight = re.search(r'font-weight: (\d+)', face).group(1)
            subset = 'vietnamese' if 'U+1EA0-1EF9' in face else 'latin'
            data = re.search(r'base64,([^)]*)', face).group(1)
            self.assertEqual(base64.b64decode(data),
                             (ROOT / f'src/sonwork/fonts/{family}-{subset}-{weight}-normal.woff2').read_bytes())
            if subset == 'vietnamese':
                for span in ('U+0102-0103', 'U+0110-0111', 'U+01A0-01A1', 'U+01AF-01B0', 'U+1EA0-1EF9'):
                    self.assertIn(span, face)
        for name in ('OFL-Geist.txt', 'OFL-SpaceMono.txt'):
            self.assertIn((ROOT / 'src/sonwork/fonts' / name).read_text(), self.css)

    def test_scaling_native_layout_and_font_roles(self):
        self.assertNotRegex(self.css, r'--font-(?:text|preferred)-size\s*:')
        reading_rule = re.search(
            r'\.markdown-preview-view,\s*'
            r'\.markdown-source-view\.mod-cm6 \.cm-scroller\s*\{([^}]+)\}',
            self.css)
        self.assertIsNotNone(reading_rule)
        self.assertIn(
            'font-size: var(--font-preferred-size, var(--font-text-size, 1rem));',
            reading_rule.group(1))
        self.assertIn('--file-line-width: 68ch', self.css)
        self.assertIn('--line-height-normal: 1.7', self.css)
        self.assertIn("--font-text-theme: 'Geist Sonwork'", self.css)
        self.assertIn('--h6-font: var(--font-monospace-theme)', self.css)
        self.assertIn('width: 100%', self.css)
        self.assertIn('safe-area-inset-left', self.css)
        self.assertIn('overflow-x: auto', self.css)
        self.assertIn('white-space: pre', self.css)
        self.assertNotRegex(self.css, r'font-size:\s*(16|17)px')
        self.assertNotIn('focus-mode', self.css)
        self.assertNotIn('!important', self.css)
        self.assertTrue(self.css.endswith((ROOT / 'src/parts/geometry.css').read_text() + '\n'))

    def test_selectable_deterministic_output_and_default_preservation(self):
        originals = {name: (ROOT / name).read_bytes() for name in ('theme.css', 'manifest.json')}
        with tempfile.TemporaryDirectory() as tmp:
            outroot = pathlib.Path(tmp)
            (outroot / 'src').symlink_to(ROOT / 'src', target_is_directory=True)
            (outroot / 'LICENSE').symlink_to(ROOT / 'LICENSE')
            with mock.patch.object(build, 'ROOT', outroot), mock.patch.object(build, 'install') as install:
                build.main(['--preset', 'sonwork'])
                out = outroot / 'dist/sonwork'
                first = {p.name: p.read_bytes() for p in out.iterdir()}
                build.main(['--preset', 'sonwork'])
                self.assertEqual(first, {p.name: p.read_bytes() for p in out.iterdir()})
                install.assert_not_called()
                self.assertEqual(json.loads(first['manifest.json'])['name'], 'Omarchy Sonwork')
                self.assertEqual(first['theme.css'].decode(), self.css)
                for name in ('OFL-Geist.txt', 'OFL-SpaceMono.txt'):
                    self.assertEqual(first[name], (ROOT / 'src/sonwork/fonts' / name).read_bytes())
        for name, content in originals.items():
            self.assertEqual((ROOT / name).read_bytes(), content)
        with tempfile.TemporaryDirectory() as tmp:
            build.build(tmp)
            for name, content in originals.items():
                self.assertEqual((pathlib.Path(tmp) / name).read_bytes(), content)

    def test_reject_live_and_install_before_writing(self):
        for flags in (['--live'], ['--install'], ['--live', '--install']):
            with mock.patch.object(build, 'build_sonwork') as candidate, mock.patch.object(build, 'install') as install:
                with self.assertRaises(SystemExit) as error:
                    build.main(['--preset', 'sonwork', *flags])
                self.assertEqual(error.exception.code, 2)
                candidate.assert_not_called()
                install.assert_not_called()

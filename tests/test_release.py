import json
import pathlib
import tempfile
import subprocess
import unittest
from unittest import mock
from test_build import build, variables

class ReleaseTest(unittest.TestCase):
    def test_normal_release_and_compat(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, css = build.build(tmp)
            self.assertEqual(json.loads((pathlib.Path(tmp)/'manifest.json').read_text())['version'], '1.6.2')
            for scheme in ('dark', 'light'):
                self.assertEqual(variables(css, scheme), variables(build.sonwork_css(), scheme))
            compat = (build.PARTS/'plugin-compat.css').read_text()
            self.assertIn(compat, css)
            for selector in ('.bases-map-container', '.cg-note-toolbar-container', '.omnisearch-modal', '.quickAddModal', '.tasknotes-plugin'):
                self.assertIn(selector, compat)
            self.assertIn('--bases-map-marker-icon-color: var(--text-on-accent)', compat)
            self.assertNotIn('display:', compat)
            self.assertNotIn('--tn-color-', compat)
            self.assertIn("'Geist Sonwork'", css)
            for name in ('OFL-Geist.txt', 'OFL-SpaceMono.txt'):
                self.assertEqual((pathlib.Path(tmp)/name).read_bytes(), (build.PARTS.parent/'sonwork/fonts'/name).read_bytes())

    def test_unreadable_or_nonobject_preferences_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            ap = vault/'.obsidian/appearance.json'; ap.parent.mkdir()
            for content in ('{broken', '', '[]', 'null'):
                ap.write_text(content)
                with self.assertRaises((ValueError, TypeError)):
                    build.select_theme(vault, 'Omarchy')
                self.assertEqual(ap.read_text(), content)

    def test_selection_preserves_other_preferences(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp); ap = vault/'.obsidian/appearance.json'; ap.parent.mkdir()
            ap.write_text(json.dumps({'fontSize':22, 'enabledCssSnippets':['mine','omarchy-theme'], 'other':{'keep':True}}))
            build.select_theme(vault, 'Omarchy')
            result = json.loads(ap.read_text())
            self.assertEqual(result, {'fontSize':22, 'enabledCssSnippets':['mine'], 'other':{'keep':True}, 'cssTheme':'Omarchy'})

    def test_companion_aggregate(self):
        root = build.PARTS.parent.parent
        subprocess.run(['node', '--check', str(root/'companion/main.js')], check=True)
        subprocess.run(['node', '--test', str(root/'tests/test_companion.cjs')], check=True)

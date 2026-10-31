import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock
from test_build import build, variables

class HookPolicyTest(unittest.TestCase):
    def fixture(self, root):
        policy=root/'policy'; other=root/'other'
        for v in (policy,other): v.mkdir()
        registry=root/'registry.json';registry.write_text(json.dumps({'vaults':{'p':{'path':str(policy)},'o':{'path':str(other)}}}))
        pref=policy/'.obsidian/plugins/omarchy-writing/data.json';pref.parent.mkdir(parents=True)
        return policy,other,registry,pref

    def snapshot(self, root):
        return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def test_off_on_off_two_vault_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
            pref.write_text('{"followOmarchyColors":false,"private":"fixture"}')
            before=self.snapshot(policy)
            with mock.patch.object(build,'VAULTS',registry):
                build.install('live one',policy)
                self.assertEqual(self.snapshot(policy),before)
                self.assertEqual((other/'.obsidian/themes/Omarchy/theme.css').read_text(),'live one')
                pref.write_text('{"followOmarchyColors":true}')
                build.install('live two',policy)
                self.assertEqual((policy/'.obsidian/themes/Omarchy/theme.css').read_text(),'live two')
                self.assertEqual(json.loads((policy/'.obsidian/appearance.json').read_text())['cssTheme'],'Omarchy')
                pref.write_text('{"followOmarchyColors":false}')
                before=self.snapshot(policy);build.install('live three',policy)
                self.assertEqual(self.snapshot(policy),before)
                self.assertEqual((other/'.obsidian/themes/Omarchy/theme.css').read_text(),'live three')

    def test_missing_invalid_nonboolean_and_escape_deny(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
            with mock.patch.object(build,'VAULTS',registry):
                for value in (None,'{bad','[]','null','{}','{"followOmarchyColors":"true"}','{"followOmarchyColors":1}'):
                    if value is None:
                        if pref.exists(): pref.unlink()
                    else: pref.write_text(value)
                    before=self.snapshot(policy);build.install('sentinel',policy)
                    self.assertEqual(self.snapshot(policy),before)
                    self.assertFalse((policy/'.obsidian/themes').exists())
                outside=root/'outside.json';outside.write_text('{"followOmarchyColors":true}')
                pref.unlink();pref.symlink_to(outside)
                self.assertFalse(build.policy_allows(policy))
                before=self.snapshot(policy);build.install('denied',policy);self.assertEqual(self.snapshot(policy),before)
                with self.assertRaises(ValueError): build.install('bad',root/'unregistered')

    def test_policy_flip_during_assembly_and_cli_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
            pref.write_text('{"followOmarchyColors":true}')
            original=build.build
            def assemble_then_flip(*args):
                result=original(*args)
                pref.write_text('{"followOmarchyColors":false}')
                return result
            with mock.patch.object(build,'VAULTS',registry), mock.patch.object(build,'LIVE_COLORS',build.COLORS), mock.patch.object(build,'build',side_effect=assemble_then_flip):
                build.main(['--live','--install','--policy-vault',str(policy)])
            self.assertFalse((policy/'.obsidian/themes').exists())
            _,expected=original(root/'expected',build.COLORS)
            self.assertEqual((other/'.obsidian/themes/Omarchy/theme.css').read_text(),expected)
            for flags in ([],['--live'],['--install']):
                with self.assertRaises(SystemExit): build.main([*flags,'--policy-vault',str(policy)])

    def test_marker_and_fixed_palette_contract(self):
        root=build.PARTS.parent.parent
        companion=(root/'companion/styles.css').read_text()
        for scheme in ('dark','light'):
            block=re.search(r'body\.theme-'+scheme+r'\[data-ow-palette="sonwork"\]\s*\{([^}]+)\}',companion)
            self.assertIsNotNone(block)
            fixed=dict(re.findall(r'--([\w-]+):\s*([^;]+);',block.group(1)))
            self.assertEqual(fixed,variables(build.sonwork_css(),scheme))
            self.assertNotIn('font-text-size',fixed)
        for source in (None,build.COLORS,build.LIGHT_COLORS):
            with tempfile.TemporaryDirectory() as tmp:
                _,css=build.build(tmp,source)
                self.assertIn(':root { --ow-theme-id: omarchy; }',css)
                for scheme in ('dark','light'):
                    self.assertNotIn('ow-theme-id',variables(css,scheme))

    def test_opted_in_cli_installs_exact_live_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
            pref.write_text('{"followOmarchyColors":true,"unrelated":"fixture only"}')
            pref_before=pref.read_bytes()
            _,expected=build.build(root/'expected',build.LIGHT_COLORS)
            with mock.patch.object(build,'VAULTS',registry), mock.patch.object(build,'LIVE_COLORS',build.LIGHT_COLORS):
                build.main(['--live','--install','--policy-vault',str(policy)])
            for vault in (policy,other):
                self.assertEqual((vault/'.obsidian/themes/Omarchy/theme.css').read_text(),expected)
                self.assertEqual(json.loads((vault/'.obsidian/themes/Omarchy/manifest.json').read_text())['version'],'1.6.2')
            self.assertEqual(pref.read_bytes(),pref_before)

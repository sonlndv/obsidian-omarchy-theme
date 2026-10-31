import hashlib
import importlib.util
import json
import pathlib
import re
import tempfile
import subprocess
import unittest
import zipfile
from unittest import mock
from test_build import build, variables, contrast
import test_hook_policy

ROOT=pathlib.Path(__file__).resolve().parent.parent

class MountyTest(unittest.TestCase):
    def test_exact_emphasis_and_graph_values_in_both_consumers(self):
        expected={
            'dark': ('#f5a67d','#c4b5fd','#83d5b4','#8a939e','#39d0fc','#c7bca4'),
            'light': ('#96502a','#6c4b99','#22684e','#515c68','#006cac','#6e6044')}
        companion=(ROOT/'companion/styles.css').read_text()
        for scheme,(peach,lilac,mint,slate,cyan,stone) in expected.items():
            v=variables(build.sonwork_css(),scheme)
            roles={'bold-color':peach,'inline-code-color':peach,'italic-color':lilac,
                   'underline-color':mint,'strikethrough-color':slate,'link-color':cyan,
                   'graph-node':cyan,'graph-node-tag':mint,'graph-node-attachment':lilac,
                   'graph-node-focused':peach,'graph-node-unresolved':stone}
            for name,color in roles.items():
                self.assertEqual(v[name],color)
            fixed=re.search(r'body\.theme-'+scheme+r'\[data-ow-palette="sonwork"\]\s*\{([^}]+)\}',companion)
            self.assertEqual(dict(re.findall(r'--([\w-]+):\s*([^;]+);',fixed.group(1))),v)
            for color in (peach,lilac,mint,slate,cyan):
                self.assertGreaterEqual(contrast(color,v['background-primary']),4.5)
            graph=(ROOT/'src/parts/graph.css').read_text()
            unresolved=re.search(r'body \.graph-view\.color-fill-unresolved\s*\{([^}]+)\}',graph)
            self.assertIn('opacity: 0.8;',unresolved.group(1))
            composite=build.mix_hex(v['background-primary'],stone,.8)
            self.assertGreaterEqual(contrast(composite,v['background-primary']),3)
            self.assertNotRegex(graph,r'color-fill-\d')

    def test_emphasis_selectors_fenced_code_heading_and_link_scopes(self):
        css=(ROOT/'src/parts/emphasis.css').read_text()
        rules={selector.strip():body for selectors,body in re.findall(r'([^{}]+)\{([^{}]*)\}',re.sub(r'/\*.*?\*/','',css,flags=re.S)) for selector in selectors.split(',\n')}
        expected={'.markdown-rendered :is(strong, b)':'--bold-color',
                  '.markdown-rendered :is(em, i)':'--italic-color',
                  '.markdown-rendered u':'--underline-color',
                  '.markdown-source-view.mod-cm6 u':'--underline-color',
                  '.markdown-source-view.mod-cm6 .cm-em.cm-strong':'--italic-color',
                  '.markdown-source-view.mod-cm6 .cm-underline':'--underline-color',
                  '.markdown-rendered :is(s, del)':'--strikethrough-color',
                  '.markdown-source-view.mod-cm6 .cm-strikethrough':'--strikethrough-color',
                  '.markdown-rendered :not(pre) > code':'--inline-code-color',
                  '.markdown-source-view.mod-cm6 .cm-line:not(.HyperMD-codeblock) .cm-inline-code':'--inline-code-color'}
        for selector,token in expected.items():
            self.assertIn('color: var('+token,rules[selector])
        for level in range(1,7):
            for selector in (f'.markdown-rendered h{level}',f'.markdown-source-view.mod-cm6 .HyperMD-header-{level}'):
                for role in ('bold','italic','inline-code','underline','strikethrough'):
                    self.assertIn(f'--{role}-color: var(--h{level}-color)',rules[selector])
        for selector in ('.markdown-rendered a','.markdown-source-view.mod-cm6 a','.markdown-source-view.mod-cm6 :is(.cm-link, .cm-hmd-internal-link, .cm-url)'):
            self.assertIn('--bold-color: var(--link-color)',rules[selector])
            self.assertIn('--italic-color: var(--link-color)',rules[selector])
        self.assertNotIn('font-size:',css)
        self.assertNotIn('font-family:',css)
        self.assertNotIn('font-weight:',css) # nested strong/em keep native weight/style
        scoped=re.sub(r'(?m)^(\.markdown-[^\n]*)',r'body[data-ow-palette="sonwork"] \1',css)
        self.assertIn(scoped,(ROOT/'companion/styles.css').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            _,normal=build.build(tmp)
            self.assertIn(css,normal)
            self.assertEqual(variables(normal,'dark')['code-normal'],'#f0f4f7')

    def test_native_probe_syntax_and_identity_gates(self):
        subprocess.run(['node','--check',str(ROOT/'tests/native_formatting_probe.cjs')],check=True)
        subprocess.run(['node','--test',str(ROOT/'tests/test_native_probe.cjs')],check=True)

    def test_theme_package_name_css_allowlist_and_determinism(self):
        spec=importlib.util.spec_from_file_location('theme_pack',ROOT/'bin/package_theme.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            build.build(root);(root/'LICENSE').write_bytes((ROOT/'LICENSE').read_bytes())
            (root/'private-fixture.json').write_text('must not ship')
            out=module.package(root);original=out.read_bytes()
            self.assertEqual(out.name,'Mounty-1.7.0.zip')
            self.assertEqual(module.package(root).read_bytes(),original)
            self.assertEqual(json.loads((root/'manifest.json').read_text())['name'],'Omarchy')
            with zipfile.ZipFile(out) as archive:
                self.assertEqual(set(archive.namelist()),{f'Mounty/{name}' for name in module.PUBLIC_FILES})
                data=json.loads(archive.read('Mounty/manifest.json'))
                self.assertEqual(data['name'],'Mounty');self.assertEqual(data['version'],'1.7.0')
                self.assertEqual(archive.read('Mounty/theme.css'),(root/'theme.css').read_bytes())
                for entry in archive.infolist(): self.assertEqual(entry.date_time,(2026,1,1,0,0,0))
        manifest=json.loads((ROOT/'companion/manifest.json').read_text())
        self.assertEqual((manifest['id'],manifest['name'],manifest['version']),('omarchy-writing','Mounty Writing','0.4.0'))
        self.assertEqual(hashlib.sha256((ROOT/'hooks/50-obsidian-theme').read_bytes()).hexdigest(),'5ef59f05962d7ec09e12ecc707550732be917dba998c038785cd7375681fdb4c')

class MountyPolicyTest(unittest.TestCase):
    fixture=test_hook_policy.HookPolicyTest.fixture
    snapshot=test_hook_policy.HookPolicyTest.destination_state

    def test_selected_mounty_on_off_and_other_vault_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
            appearance=policy/'.obsidian/appearance.json';appearance.write_text('{"cssTheme":"Mounty","fontSize":23}')
            pref.write_text('{"followOmarchyColors":false}')
            before=self.snapshot(policy)
            with mock.patch.object(build,'VAULTS',registry):
                build.install('live one',policy);self.assertEqual(self.snapshot(policy),before)
                pref.write_text('{"followOmarchyColors":true}')
                build.install('live two',policy)
                folder=policy/'.obsidian/themes/Mounty'
                self.assertEqual((folder/'theme.css').read_text(),'live two')
                self.assertEqual(json.loads((folder/'manifest.json').read_text())['name'],folder.name)
                self.assertEqual(json.loads(appearance.read_text())['cssTheme'],'Mounty')
                self.assertEqual(json.loads(appearance.read_text())['fontSize'],23)
                self.assertFalse((policy/'.obsidian/themes/Omarchy').exists())
                self.assertEqual((other/'.obsidian/themes/Omarchy/theme.css').read_text(),'live two')
                pref.write_text('{"followOmarchyColors":false}');before=self.snapshot(policy)
                build.install('live three',policy);self.assertEqual(self.snapshot(policy),before)

    def test_malformed_unknown_selection_and_mounty_symlinks_deny(self):
        for value in ('{bad','[]','null','{"cssTheme":"../note"}','{"cssTheme":"Other"}','{"cssTheme":null}','{"cssTheme":{}}'):
            with self.subTest(appearance=value), tempfile.TemporaryDirectory() as tmp:
                root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
                pref.write_text('{"followOmarchyColors":true}')
                (policy/'.obsidian/appearance.json').write_text(value)
                before=self.snapshot(policy)
                with mock.patch.object(build,'VAULTS',registry): build.install('denied',policy)
                self.assertEqual(self.snapshot(policy),before)
        for leaf in ('theme.css','manifest.json'):
            for inside in (True,False):
                with self.subTest(leaf=leaf,inside=inside), tempfile.TemporaryDirectory() as tmp:
                    root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
                    pref.write_text('{"followOmarchyColors":true}')
                    (policy/'.obsidian/appearance.json').write_text('{"cssTheme":"Mounty"}')
                    folder=policy/'.obsidian/themes/Mounty';folder.mkdir(parents=True)
                    target=(policy if inside else root)/'sentinel';target.write_text('untouched')
                    (folder/leaf).symlink_to(target);before=self.snapshot(policy)
                    with mock.patch.object(build,'VAULTS',registry): build.install('denied',policy)
                    self.assertEqual(target.read_text(),'untouched');self.assertEqual(self.snapshot(policy),before)

    def test_selected_mounty_directory_symlinks_deny(self):
        for inside in (True,False):
            with self.subTest(inside=inside), tempfile.TemporaryDirectory() as tmp:
                root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
                pref.write_text('{"followOmarchyColors":true}')
                (policy/'.obsidian/appearance.json').write_text('{"cssTheme":"Mounty"}')
                parent=policy/'.obsidian/themes';parent.mkdir()
                target=(policy if inside else root)/'redirect';target.mkdir()
                (parent/'Mounty').symlink_to(target,target_is_directory=True)
                before=self.snapshot(policy)
                with mock.patch.object(build,'VAULTS',registry): build.install('denied',policy)
                self.assertEqual(self.snapshot(policy),before);self.assertEqual(list(target.iterdir()),[])

    def test_selected_theme_is_rechecked_after_assembly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);policy,other,registry,pref=self.fixture(root)
            pref.write_text('{"followOmarchyColors":true}')
            appearance=policy/'.obsidian/appearance.json';appearance.write_text('{"cssTheme":"Omarchy"}')
            original=build.build
            def assemble_and_change_selection(*args):
                result=original(*args);appearance.write_text('{"cssTheme":"Mounty"}');return result
            with mock.patch.object(build,'VAULTS',registry), mock.patch.object(build,'LIVE_COLORS',build.COLORS), mock.patch.object(build,'build',side_effect=assemble_and_change_selection):
                build.main(['--live','--install','--policy-vault',str(policy)])
            self.assertTrue((policy/'.obsidian/themes/Mounty/theme.css').is_file())
            self.assertFalse((policy/'.obsidian/themes/Omarchy').exists())

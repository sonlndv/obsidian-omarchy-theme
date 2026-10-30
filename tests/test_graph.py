import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile
from test_build import build, contrast, variables

ROOT = pathlib.Path(__file__).resolve().parent.parent

class GraphTest(unittest.TestCase):
    def test_derived_headings_and_graph_contrast(self):
        css = build.sonwork_css()
        for scheme, heading in (('dark', '#82defa'), ('light', '#044974')):
            v = variables(css, scheme)
            self.assertEqual(v['h2-color'], heading)
            self.assertEqual(v['h3-color'], heading)
            for level in range(1, 7):
                self.assertGreaterEqual(contrast(v[f'h{level}-color'], v['background-primary']), 4.5)
            for name in ('graph-node','graph-node-focused','graph-node-tag','graph-node-attachment'):
                self.assertGreaterEqual(contrast(v[name],v['background-primary']),3)
            composite = build.mix_hex(v['background-primary'],v['graph-node-unresolved'], .8)
            self.assertGreaterEqual(contrast(composite,v['background-primary']),3)
            self.assertGreaterEqual(contrast(v['graph-text'],v['background-primary']),4.5)
            self.assertEqual(len({v[name] for name in ('graph-node','graph-node-tag','graph-node-attachment','graph-node-unresolved','graph-node-focused')}),5)

    def test_direct_body_probes_and_live_fallbacks(self):
        graph = (build.PARTS/'graph.css').read_text()
        for name in ('fill','fill-focused','fill-tag','fill-attachment','fill-unresolved','line','text','fill-highlight','line-highlight'):
            self.assertIn(f'body .graph-view.color-{name}',graph)
        self.assertIn('opacity: 0.8',graph)
        self.assertNotIn('workspace',graph)
        self.assertNotIn('color-fill-1',graph)
        self.assertIn('var(--graph-node-unresolved, var(--text-muted))',graph)
        self.assertIn('var(--graph-text, var(--text-normal))',graph)
        for source in (build.COLORS,build.LIGHT_COLORS):
            with tempfile.TemporaryDirectory() as tmp:
                _,css=build.build(tmp,source)
                self.assertIn(graph,css)
                self.assertEqual(variables(css,build.read_colors(source)['mode'])['graph-node'],build.read_colors(source)['foreground'])
        sidebar=(build.PARTS/'sidebar.css').read_text()
        self.assertIn('[data-type="file-explorer"]',sidebar)
        self.assertIn('[data-type="outline"]',sidebar)
        self.assertIn('inset 1px',sidebar)

    def test_version_derived_deterministic_allowlisted_package(self):
        spec=importlib.util.spec_from_file_location('pack',ROOT/'bin/package_companion.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/'companion').mkdir()
            for name in module.PUBLIC_FILES:
                source=ROOT/'LICENSE' if name=='LICENSE' else ROOT/'companion'/name
                target=root/'LICENSE' if name=='LICENSE' else root/'companion'/name
                target.write_bytes(source.read_bytes())
            metadata=json.loads((root/'companion/manifest.json').read_text());metadata['version']='9.8.7'
            (root/'companion/manifest.json').write_text(json.dumps(metadata))
            (root/'companion/data.json').write_text('private fixture sentinel')
            path=module.package(root);before=path.read_bytes()
            self.assertEqual(path.name,'omarchy-writing-9.8.7.zip')
            self.assertEqual(module.package(root).read_bytes(),before)
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(set(archive.namelist()),{f'omarchy-writing/{name}' for name in module.PUBLIC_FILES})
                for entry in archive.infolist():
                    self.assertEqual(entry.date_time,(2026,1,1,0,0,0))

    def test_accepted_fonts_notices_palette_and_layers_unchanged(self):
        expected = {'src/sonwork/fonts/OFL-Geist.txt': '71609cbb5c78b5870d712eab73a31d76622635c6ed034ab5cee3b9ecbda8685f', 'src/sonwork/fonts/OFL-SpaceMono.txt': '761663b7fb7667764f42243f9b1b2bcfccf41b158a7ab508bed4961dcf377eab', 'src/sonwork/fonts/geist-latin-400-normal.woff2': 'ead637fd0b6b887d829b3ce3f25fdc242b1de0cfb69c0d97987933675d1315ba', 'src/sonwork/fonts/geist-latin-600-normal.woff2': 'edde7cc4e2719898f981a6d970a756030fff75a8ed36dd6a457a60181b889ebf', 'src/sonwork/fonts/geist-vietnamese-400-normal.woff2': '27b07da23b7642200561395e748f40e2675e91306e8544c66ec087607c6a990b', 'src/sonwork/fonts/geist-vietnamese-600-normal.woff2': 'cd6e1b9ef0dbeb78753dd294cf803cc78cb6393d9fe09fc7be5c8b4d79cd8c2c', 'src/sonwork/fonts/space-mono-latin-400-normal.woff2': 'fb4a81a2d0a893e5c38c394a7e716a1cef0b24610a0af49c96f6d529bd66bf2b', 'src/sonwork/fonts/space-mono-latin-700-normal.woff2': '2d46bd159b53f55c41167a4f1540a074649464194fd1e416f5b4694a6c0f282c', 'src/sonwork/fonts/space-mono-vietnamese-400-normal.woff2': 'a748973d5d192a27d69862f5af5f9182d4420d3a924e7b992ae82182e9b12cd8', 'src/sonwork/fonts/space-mono-vietnamese-700-normal.woff2': '97f6df0559c6393b851812484ae859b7c539815d5fcdab7d17234492480fa16c', 'src/sonwork/palette.json': '8dfc9c33f8dfe932c161606a016c91fe170374ab9385c648e7b31fb876a38afb', 'src/sonwork/typography.css': 'ba1b7f0b541357d14f950a170d20d5c352fc3e270b48ca696e3a54c48ed14c7d', 'src/parts/geometry.css': '3694ee834430e0ee3b41c7aa88aee9bf68682f5eb08cb541cf5cc4fc2cfa74a6', 'src/parts/plugin-compat.css': 'd86235d172bdbe2611ccc77368fe7816a85f6219382dc486610c2458a72a3d21'}
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest, name)

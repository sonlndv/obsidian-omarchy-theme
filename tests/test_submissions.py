import hashlib
import importlib.util
import json
import pathlib
import posixpath
import re
import tempfile
import unittest
import zipfile
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('submissions', ROOT/'bin/package_submissions.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

THEME_ALLOWLIST = {'manifest.json','README.md','LICENSE','theme.css','screenshot.png',
    'OFL-Geist.txt','OFL-SpaceMono.txt','docs/images/mounty-light.png',
    'docs/GRAPH-COLOURS.md','docs/MIGRATING-TO-MOUNTY.md','docs/COMMUNITY-LISTINGS.md'}
PLUGIN_ALLOWLIST = {'manifest.json','README.md','LICENSE','main.js','styles.css',
    'docs/images/mounty-writing-tools.png','docs/images/mounty-zen.png',
    'docs/MIGRATING-TO-MOUNTY.md','docs/COMMUNITY-LISTINGS.md'}

class SubmissionTest(unittest.TestCase):
    def prepare(self, root):
        for relative in set(exporter.THEME_FILES.values()) | set(exporter.PLUGIN_FILES.values()):
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((ROOT/relative).read_bytes())
        for relative in ('.task-tmp/secret.txt','.git/config','companion/data.json','dist/private.log','vault/Note.md'):
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('PRIVATE_SENTINEL_DO_NOT_SHIP')

    def check_local_references(self, archive):
        links=0;images=0
        for name in archive.namelist():
            if not name.endswith('.md'):continue
            text=archive.read(name).decode()
            for match in re.finditer(r'(!?)\[[^\]]+\]\(([^\s)]+)\)',text):
                target=urlsplit(match.group(2))
                if target.scheme or target.netloc:continue
                path=unquote(target.path)
                if not path:continue
                resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),path))
                self.assertFalse(resolved.startswith(('../','/')), (name,path))
                self.assertIn(resolved,archive.namelist(),(name,path))
                links+=1;images+=bool(match.group(1))
        self.assertGreaterEqual(links,3)
        self.assertGreaterEqual(images,2)

    def test_root_ready_manifests_runtime_links_allowlists_and_determinism(self):
        self.assertEqual(set(exporter.THEME_FILES),THEME_ALLOWLIST)
        self.assertEqual(set(exporter.PLUGIN_FILES),PLUGIN_ALLOWLIST)
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);self.prepare(root)
            before={name:(root/name).read_bytes() for name in ('manifest.json','companion/manifest.json','theme.css','companion/main.js','companion/styles.css')}
            theme,plugin=exporter.package(root)
            self.assertEqual(theme.name,'Mounty-1.7.1-submission-source.zip')
            self.assertEqual(plugin.name,'Mounty-Zen-0.4.1-submission-source.zip')
            first=[p.read_bytes() for p in (theme,plugin)]
            self.assertEqual([p.read_bytes() for p in exporter.package(root)],first)
            for path,allowlist,title in ((theme,THEME_ALLOWLIST,'Mounty'),(plugin,PLUGIN_ALLOWLIST,'Mounty Zen')):
                with zipfile.ZipFile(path) as archive:
                    self.assertEqual(set(archive.namelist()),allowlist)
                    self.assertIn('manifest.json',archive.namelist()) # no enclosing product folder
                    self.assertTrue(archive.read('README.md').decode().startswith('# '+title+'\n'))
                    self.check_local_references(archive)
                    for entry in archive.infolist():
                        self.assertEqual(entry.date_time,(2026,1,1,0,0,0))
                        self.assertNotIn(b'PRIVATE_SENTINEL_DO_NOT_SHIP',archive.read(entry))
                        self.assertNotIn('..',pathlib.PurePosixPath(entry.filename).parts)
            with zipfile.ZipFile(theme) as archive:
                manifest=json.loads(archive.read('manifest.json'))
                self.assertEqual((manifest['name'],manifest['version']),('Mounty','1.7.1'))
                self.assertNotIn('id',manifest)
                self.assertEqual(archive.read('theme.css'),(ROOT/'theme.css').read_bytes())
                self.assertEqual(archive.read('screenshot.png'),(ROOT/'docs/images/mounty-dark.png').read_bytes())
                for name in ('OFL-Geist.txt','OFL-SpaceMono.txt','LICENSE'):
                    self.assertEqual(archive.read(name),(ROOT/name).read_bytes())
            with zipfile.ZipFile(plugin) as archive:
                manifest=json.loads(archive.read('manifest.json'))
                self.assertEqual((manifest['name'],manifest['id'],manifest['version']),('Mounty Zen','omarchy-writing','0.4.1'))
                for name in ('main.js','styles.css','manifest.json'):
                    self.assertEqual(archive.read(name),(ROOT/'companion'/name).read_bytes())
            for name,content in before.items():self.assertEqual((root/name).read_bytes(),content)

    def test_equal_distributions_and_metadata_description_contract(self):
        package_spec=importlib.util.spec_from_file_location('mounty_package',ROOT/'bin/package_theme.py')
        module=importlib.util.module_from_spec(package_spec);package_spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);self.prepare(root)
            manual=module.package(root);submission,_=exporter.package(root)
            with zipfile.ZipFile(manual) as m,zipfile.ZipFile(submission) as s:
                self.assertEqual(m.read('Mounty/theme.css'),s.read('theme.css'))
                self.assertEqual(m.read('Mounty/theme.css'),(ROOT/'theme.css').read_bytes())
                self.assertEqual(m.read('Mounty/manifest.json'),s.read('manifest.json'))
        updater=json.loads((ROOT/'manifest.json').read_text())
        self.assertEqual((updater['name'],updater['version']),('Omarchy','1.7.1'))
        plugin=json.loads((ROOT/'companion/manifest.json').read_text())
        self.assertEqual(plugin['name'],'Mounty Zen')
        self.assertEqual(plugin['id'],'omarchy-writing')
        self.assertEqual(plugin['minAppVersion'],'1.5.0')
        description=plugin['description']
        self.assertLessEqual(len(description),250)
        self.assertTrue(description.isascii());self.assertTrue(description.endswith('.'))
        self.assertTrue(description.startswith('Focus '))
        self.assertIn(description,(ROOT/'docs/COMMUNITY-LISTINGS.md').read_text())
        listing=(ROOT/'docs/COMMUNITY-LISTINGS.md').read_text()
        for name in ('Mounty','Mounty Zen','Omarchy'):
            self.assertIn('### '+name,listing)
        self.assertIn('planned, not submitted',(ROOT/'docs/submissions/Mounty-README.md').read_text())

    def test_runtime_source_hook_identity_is_unchanged(self):
        names=sorted(str(p.relative_to(ROOT)) for directory in ('src','hooks') for p in (ROOT/directory).rglob('*') if p.is_file())+['companion/main.js','companion/styles.css','theme.css']
        digest=hashlib.sha256()
        for name in names:digest.update(name.encode()+b'\0'+hashlib.sha256((ROOT/name).read_bytes()).digest())
        self.assertEqual(digest.hexdigest(), '9c48e1c44be5d50314a796559468fbae22ed2fbf0f4079d4fc34a2a0f158db78')
        # Unchanged runtime retains stable own settings and commands; no rebranding ID fork.
        source=(ROOT/'companion/main.js').read_text()
        for key in ('followOmarchyColors','typewriter','width','hideInlineTitle'):
            self.assertIn(key,source)
        for command in ("id: 'toggle-zen'","id: 'toggle-typewriter'","id: 'open-writing-tools'"):
            self.assertIn(command,source)

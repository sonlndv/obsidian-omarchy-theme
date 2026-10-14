import importlib.util
import json
import pathlib
import re
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build", ROOT / "bin" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = pathlib.Path(cls.tmp.name)
        build.build(cls.out)
        cls.css = (cls.out / "theme.css").read_text()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_content_container_full_width(self):
        m = re.search(r"\.markdown-source-view\.mod-cm6 \.cm-contentContainer\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(m)
        self.assertIn("width: 100%", m.group(1))

    def test_mobile_safe_area(self):
        self.assertIn(".is-mobile", self.css)
        self.assertIn("safe-area-inset", self.css)

    def test_last_text_font_preserves_embedded_fallback(self):
        declarations = re.findall(r"--font-text-theme\s*:\s*([^;]+);", self.css)
        self.assertTrue(declarations)
        self.assertIn("IBM Plex Mono Embedded", declarations[-1])

    def test_dark_colour_block(self):
        m = re.search(r"\.theme-dark\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(m)
        self.assertIn("--background-primary", m.group(1))

    def test_manifest(self):
        data = json.loads((self.out / "manifest.json").read_text())
        for key in ("name", "version", "minAppVersion", "author"):
            self.assertTrue(data.get(key), key)

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build.build(other)
            for name in ("theme.css", "manifest.json"):
                self.assertEqual((self.out / name).read_bytes(),
                                 (pathlib.Path(other) / name).read_bytes())


if __name__ == "__main__":
    unittest.main()

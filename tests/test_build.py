import importlib.util
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build", ROOT / "bin" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def contrast(first, second):
    def luminance(color):
        channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                  for c in channels]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def variables(css, scheme):
    block = re.search(r"\.theme-" + scheme + r"\s*\{([^}]*)\}", css)
    if block is None:
        raise AssertionError(f"missing {scheme} block")
    return dict(re.findall(r"--([\w-]+):\s*([^;]+);", block.group(1)))


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

    def test_platform_radius_overrides(self):
        css = re.sub(r"/\*.*?\*/", "", self.css, flags=re.DOTALL)
        mobile_rules = [body for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
                        if any(part.strip() == "body.is-mobile" for part in selector.split(","))]
        self.assertTrue(mobile_rules)
        radii = (
            "clickable-icon-radius",
            "input-radius",
            "modal-radius",
            "nav-item-radius",
            "navbar-radius",
            "toggle-radius",
            "toggle-thumb-radius",
            "setting-items-radius",
            "search-input-radius",
            "view-header-action-radius",
            "embed-action-radius",
            "embed-actions-radius",
            "swatch-radius",
            "canvas-controls-radius",
            "radius-xl",
            "touch-radius-xxs",
            "touch-radius-xs",
            "touch-radius-s",
            "touch-radius-m",
            "touch-radius-l",
            "touch-radius-xl",
            "metadata-property-radius",
            "metadata-property-radius-hover",
            "metadata-property-radius-focus",
            "hotkey-radius",
            "table-selection-border-radius",
            "tab-switcher-preview-radius",
        )
        for name in (*radii, "mobile-sidebar-radius"):
            with self.subTest(variable=name):
                value = "0" if name == "mobile-sidebar-radius" else "var(--sharp-radius)"
                declaration = rf"--{re.escape(name)}\s*:\s*{re.escape(value)}\s*;"
                self.assertTrue(any(re.search(declaration, body) for body in mobile_rules), name)

    def test_last_text_font_preserves_embedded_fallback(self):
        declarations = re.findall(r"--font-text-theme\s*:\s*([^;]+);", self.css)
        self.assertTrue(declarations)
        self.assertIn("IBM Plex Mono Embedded", declarations[-1])

    def test_dark_colour_block(self):
        m = re.search(r"\.theme-dark\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(m)
        self.assertIn("--background-primary", m.group(1))

    def test_both_schemes_and_contrast(self):
        for scheme in ("dark", "light"):
            values = variables(self.css, scheme)
            for name in ("text-normal", "text-muted", "text-accent", "link-color",
                         "h3-color", "code-normal", "code-string", "code-keyword"):
                with self.subTest(scheme=scheme, variable=name):
                    self.assertGreaterEqual(contrast(values[name], values["background-primary"]), 4.5)
            self.assertGreaterEqual(contrast(values["text-faint"], values["background-primary"]), 3)

    def test_palette_keys_match(self):
        self.assertEqual(build.read_colors().keys(), build.read_colors(build.LIGHT_COLORS).keys())
        self.assertEqual(build.read_colors(build.LIGHT_COLORS)["mode"], "light")

    def test_live_replaces_only_matching_scheme(self):
        for scheme, source in (("dark", build.COLORS), ("light", build.LIGHT_COLORS)):
            with self.subTest(scheme=scheme), tempfile.TemporaryDirectory() as tmp:
                path = pathlib.Path(tmp) / "live.toml"
                path.write_text(source.read_text().replace(
                    build.read_colors(source)["accent"], "#123456"))
                _, css = build.build(pathlib.Path(tmp) / "out", path)
                self.assertEqual(variables(css, scheme)["text-accent"], "#123456")
                other = "light" if scheme == "dark" else "dark"
                self.assertEqual(variables(css, other), variables(self.css, other))

    def test_no_important(self):
        self.assertNotIn("!important", self.css)
        self.assertNotIn("!important", (ROOT / "theme.css").read_text())

    def test_live_install_preserves_repo_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "repo"
            root.mkdir()
            originals = {"theme.css": b"committed css\n",
                         "manifest.json": b"committed manifest\n"}
            for name, content in originals.items():
                (root / name).write_bytes(content)
            live = pathlib.Path(tmp) / "live.toml"
            live.write_text(build.LIGHT_COLORS.read_text().replace(
                build.read_colors(build.LIGHT_COLORS)["accent"], "#123456"))
            vault = pathlib.Path(tmp) / "vault"
            vault.mkdir()
            vaults = pathlib.Path(tmp) / "obsidian.json"
            vaults.write_text(json.dumps({"vaults": {"test": {"path": str(vault)}}}))
            with mock.patch.multiple(build, ROOT=root, LIVE_COLORS=live, VAULTS=vaults):
                build.main(["--live", "--install"])
            for name, content in originals.items():
                self.assertEqual((root / name).read_bytes(), content)
            installed = vault / ".obsidian" / "themes" / build.THEME
            css = (installed / "theme.css").read_text()
            self.assertIn(".theme-dark", css)
            self.assertIn(".theme-light", css)
            self.assertEqual(variables(css, "light")["text-accent"], "#123456")
            self.assertEqual(json.loads((installed / "manifest.json").read_text())["name"],
                             build.THEME)

    def test_manifest(self):
        data = json.loads((self.out / "manifest.json").read_text())
        self.assertNotIn("description", data)
        self.assertEqual(data["version"], "1.3.0")
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

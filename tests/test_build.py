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
        channels = ([int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
                    if isinstance(color, str) else [c / 255 for c in color])
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
        # Preserve the legacy palette/IBM fallback fixture contracts explicitly;
        # the normal 1.6.0 artifact is covered by test_sonwork/test_release.
        cls.css = build.assemble({"dark": build.read_colors(build.COLORS),
                                  "light": build.read_colors(build.LIGHT_COLORS)})

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
                value = "0" if name == "mobile-sidebar-radius" else "var(--corner-radius)"
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
                         "h2-color", "h3-color", "h4-color", "h5-color", "code-normal", "code-string", "code-keyword"):
                with self.subTest(scheme=scheme, variable=name):
                    self.assertGreaterEqual(contrast(values[name], values["background-primary"]), 4.5)
            self.assertGreaterEqual(contrast(values["text-faint"], values["background-primary"]), 3)

    def test_base_colours_and_callouts(self):
        for scheme, path in (("dark", build.COLORS), ("light", build.LIGHT_COLORS)):
            palette = build.read_colors(path)
            values = variables(self.css, scheme)
            with self.subTest(scheme=scheme):
                self.assertRegex(values["color-blue-rgb"], r"^\d{1,3}, \d{1,3}, \d{1,3}$")
                self.assertNotIn("8, 109, 221", self.css)
                for name, key in (("red", "red"), ("orange", "orange"),
                                  ("yellow", "yellow"), ("green", "green"),
                                  ("cyan", "cyan"), ("blue", "blue"),
                                  ("purple", "magenta"), ("pink", "bright_magenta")):
                    expected = ", ".join(str(int(palette[key][i:i + 2], 16))
                                         for i in (1, 3, 5))
                    self.assertEqual(values[f"color-{name}"], palette[key])
                    self.assertEqual(values[f"color-{name}-rgb"], expected)
                for name in ("default", "info", "note"):
                    value = values[f"callout-{name}"]
                    self.assertRegex(value, r"^#[0-9a-fA-F]{6}$")
                    self.assertNotRegex(value, r"^\d+,\s*\d+,\s*\d+$")
                    self.assertEqual(value, palette["blue"])

    def test_surface_colours_and_highlight_contrast(self):
        for scheme, path in (("dark", build.COLORS), ("light", build.LIGHT_COLORS)):
            palette = build.read_colors(path)
            values = variables(self.css, scheme)
            with self.subTest(scheme=scheme):
                if scheme == "light":
                    self.assertEqual(values["text-highlight-bg"], palette["selection"])
                    highlight = palette["selection"]
                else:
                    self.assertEqual(values["text-highlight-bg"],
                                     f"rgba({build.rgb(palette['yellow'])}, 0.25)")
                    highlight = build.mix_hex(palette["background"], palette["yellow"], 0.25)
                self.assertGreaterEqual(contrast(values["text-normal"], highlight), 4.5)
                self.assertEqual(values["tag-background"],
                                 f"rgba({build.rgb(palette['accent'])}, {0.12 if scheme == 'light' else 0.1})")
                self.assertEqual(values["tag-border-color"],
                                 f"rgba({build.rgb(palette['accent'])}, {0.4 if scheme == 'light' else 0.35})")
                self.assertEqual(values["tag-border-width"], "1px")
                self.assertNotEqual(values["tag-background"], values["text-highlight-bg"])
                self.assertEqual(values["nav-item-background-active"],
                                 (build.mix_hex(palette["dark_background"], palette["foreground"], 0.07)
                                  if scheme == "light" else
                                  build.mix_hex(palette["selection"], palette["muted"], 0.25)))
                self.assertNotEqual(values["nav-item-background-active"],
                                    values["background-secondary"])
                self.assertEqual(values["table-border-color"],
                                 f"rgba({build.rgb(palette['muted'])}, {0.45 if scheme == 'light' else 0.6})")
                self.assertEqual(values["code-background"], palette["lighter_background"])
                self.assertNotEqual(values["code-background"], palette["background"])
                self.assertEqual(values["code-normal"], palette["foreground"])

    def test_light_tag_composite_contrast(self):
        values = variables(self.css, "light")
        palette = build.read_colors(build.LIGHT_COLORS)
        self.assertEqual(values["tag-color"], palette["bright_yellow"])
        fill = re.fullmatch(r"rgba\((\d+), (\d+), (\d+), ([\d.]+)\)",
                            values["tag-background"])
        self.assertIsNotNone(fill)
        red, green, blue, alpha = map(float, fill.groups())
        for surface in ("background-primary", "background-secondary"):
            with self.subTest(surface=surface):
                background = [int(values[surface][i:i + 2], 16) for i in (1, 3, 5)]
                composite = [fg * alpha + bg * (1 - alpha)
                             for fg, bg in zip((red, green, blue), background)]
                self.assertGreaterEqual(contrast(values["tag-color"], composite), 4.5)

    def test_light_active_row_and_warning(self):
        values = variables(self.css, "light")
        palette = build.read_colors(build.LIGHT_COLORS)
        self.assertGreaterEqual(contrast(values["nav-item-color-active"],
                                         values["nav-item-background-active"]), 4.5)
        self.assertEqual(values["callout-warning"], palette["orange"])
        for surface in ("background-primary", "background-secondary"):
            self.assertGreaterEqual(contrast(values["callout-warning"], values[surface]), 4.5)
        self.assertIn(".theme-light .tree-item-self.is-active {\n"
                      "  box-shadow: inset 2px 0 0 var(--interactive-accent);\n}", self.css)

    def test_heading_sizes(self):
        rules = re.findall(r"([^{}]+)\{([^{}]*)\}",
                           (ROOT / "src/parts/typography.css").read_text())
        for level, size in ((1, "2em"), (2, "1.45em")):
            selectors = [f".markdown-preview-view h{level}",
                         f".markdown-source-view .HyperMD-header-{level}",
                         f".markdown-source-view .cm-header-{level}"]
            if level == 1:
                selectors.append(".inline-title")
            for selector in selectors:
                with self.subTest(selector=selector):
                    self.assertTrue(any(
                        selector in [part.strip() for part in group.split(",")]
                        and re.search(r"font-size:\s*" + re.escape(size) + r"\s*;", body)
                        for group, body in rules))

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
                self.assertEqual(variables(css, other), variables(build.sonwork_css(), other))

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
        self.assertEqual(data["version"], "1.7.1")
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

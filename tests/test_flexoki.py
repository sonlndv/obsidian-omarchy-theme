"""Opt-in Mounty · Flexoki palette: provenance, scoping, precedence and contrast."""
import hashlib
import json
import pathlib
import re
import tempfile
import unittest

from test_build import ROOT, build, contrast, variables

SCHEMES = ("dark", "light")
FLEXOKI = ROOT / "src" / "flexoki"
COMPANION = ROOT / "companion" / "styles.css"


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def comments(css):
    return "\n".join(re.findall(r"/\*.*?\*/", css, flags=re.DOTALL))


def rules(css):
    """Top-level rules as (selectors, custom-property declarations, raw body)."""
    found = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", strip_comments(css)):
        selectors = tuple(part.strip() for part in selector.split(","))
        found.append((selectors, dict(re.findall(r"--([\w-]+):\s*([^;]+);", body)), body))
    return found


def specificity(selector):
    classes = len(re.findall(r"\[[^\]]*\]", selector))
    selector = re.sub(r"\[[^\]]*\]", "", selector)
    ids = selector.count("#")
    classes += len(re.findall(r"\.[\w-]+", selector)) + len(re.findall(r":[\w-]+", selector))
    types = len(re.findall(r"(?:^|[\s>+~])([a-zA-Z][\w-]*)", selector))
    return (ids, classes, types)


def values(scheme):
    return build.flexoki_values(scheme)


def companion_selector(scheme):
    return f'body.theme-{scheme}[data-ow-palette="sonwork"]'


def companion_roles(scheme):
    text = COMPANION.read_text()
    blocks = re.findall(re.escape(companion_selector(scheme)) + r"\s*\{([^}]*)\}", text)
    names = set()
    for block in blocks:
        names.update(re.findall(r"--([\w-]+):", block))
    return names


class FlexokiTest(unittest.TestCase):
    def test_provenance_hashes_licence_and_class(self):
        roles = json.loads((FLEXOKI / "roles.json").read_text())
        source = roles["source"]
        self.assertEqual(hashlib.sha256((FLEXOKI / "flexoki-obsidian.css").read_bytes()).hexdigest(),
                         source["sha256"])
        self.assertEqual(hashlib.sha256((FLEXOKI / "LICENSE").read_bytes()).hexdigest(),
                         source["license_sha256"])
        licence = (FLEXOKI / "LICENSE").read_text()
        self.assertIn("MIT License", licence)
        self.assertIn("Copyright (c) 2023 Steph Ango", licence)
        self.assertIn("https://stephango.com/flexoki",
                      (FLEXOKI / "flexoki-obsidian.css").read_text())
        self.assertEqual(roles["class"], "mounty-flexoki")

    def test_generated_files_are_current_and_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            build.build(first)
            build.build(second)
            first, second = pathlib.Path(first), pathlib.Path(second)
            self.assertEqual((first / "theme.css").read_bytes(), (ROOT / "theme.css").read_bytes())
            self.assertEqual((first / "snippets/mounty-flexoki.css").read_bytes(),
                             (ROOT / "snippets/mounty-flexoki.css").read_bytes())
            self.assertEqual((first / "snippets/mounty-flexoki.css").read_text(),
                             build.flexoki_snippet())
            for name in ("theme.css", "snippets/mounty-flexoki.css"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_layer_is_appended_once_after_untouched_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, body = build.build(tmp)
        layer = "\n" + build.flexoki_css()
        self.assertTrue(body.endswith(layer))
        self.assertEqual(body.count(layer), 1)
        default = build.sonwork_css()
        for scheme in SCHEMES:
            with self.subTest(scheme=scheme):
                self.assertEqual(variables(body, scheme), variables(default, scheme))
        self.assertNotIn("mounty-flexoki", default)

    def test_live_builds_keep_the_layer(self):
        layer = "\n" + build.flexoki_css()
        for source in (build.COLORS, build.LIGHT_COLORS):
            with self.subTest(source=source.name), tempfile.TemporaryDirectory() as tmp:
                _, body = build.build(tmp, source)
                self.assertTrue(body.endswith(layer))

    def test_scoping_of_layer_and_snippet(self):
        layer = rules(build.flexoki_css())
        self.assertEqual(len(layer), 2)
        for (selectors, _, _), scheme in zip(layer, SCHEMES):
            with self.subTest(layer=scheme):
                plain = f"body.theme-{scheme}.mounty-flexoki"
                self.assertEqual(selectors, (plain, plain + "[data-ow-palette]"))
                for selector in selectors:
                    self.assertIn(".mounty-flexoki", selector)
                    self.assertTrue(selector.startswith(f"body.theme-{scheme}"))
        snippet = rules(build.flexoki_snippet())
        self.assertEqual(len(snippet), 2)
        for (selectors, _, _), scheme in zip(snippet, SCHEMES):
            with self.subTest(snippet=scheme):
                plain = f":root body.theme-{scheme}"
                self.assertEqual(selectors, (plain, plain + "[data-ow-palette]"))
                for selector in selectors:
                    self.assertTrue(selector.startswith(":root body.theme-"))

    def test_style_settings_block(self):
        parser = re.compile(r"/\*!?\s*@settings[\r\n]+?([\s\S]+?)\*/")
        layer = build.flexoki_css()
        found = parser.findall(layer)
        self.assertEqual(len(found), 1)
        lines = [line.strip() for line in found[0].splitlines()]
        for expected in ("name: Mounty", "id: mounty", "id: mounty-flexoki",
                         "type: class-toggle", "default: false", "addCommand: true",
                         "title: Mounty · Flexoki palette"):
            self.assertIn(expected, lines)
        with tempfile.TemporaryDirectory() as tmp:
            _, body = build.build(tmp)
        self.assertEqual(body.count("@settings"), 1)
        self.assertNotIn("@settings", build.flexoki_snippet())

    def test_colour_only_declarations(self):
        allowed = (set(variables(build.sonwork_css(), "dark"))
                   | set(build.flexoki_upstream()["dark"]))
        patterns = (r"^#[0-9a-f]{6}$",
                    r"^rgba\(\d{1,3}, \d{1,3}, \d{1,3}, (?:0?\.\d+|1|0)\)$",
                    r"^\d{1,3}, \d{1,3}, \d{1,3}$")
        for label, css in (("layer", build.flexoki_css()), ("snippet", build.flexoki_snippet())):
            for selectors, declarations, raw in rules(css):
                with self.subTest(css=label, selector=selectors[0]):
                    self.assertEqual(re.sub(r"--[\w-]+:\s*[^;]+;", "", raw).strip(), "")
                    self.assertLessEqual(set(declarations), allowed)
                    for name, value in declarations.items():
                        if name in ("accent-h", "accent-s", "accent-l"):
                            self.assertRegex(value, r"^\d+%?$", name)
                        else:
                            self.assertTrue(any(re.match(p, value) for p in patterns),
                                            (name, value))
            bare = strip_comments(css)
            for forbidden in ("font", "@font-face", "!important", "radius", "width", "size",
                              "display", "padding", "margin"):
                self.assertNotIn(forbidden, bare, (label, forbidden))

    def test_values_come_from_kepano_flexoki(self):
        pins = {
            "dark": {"background-primary": "#100f0f", "background-secondary": "#1c1b1a",
                     "text-normal": "#cecdc3", "text-muted": "#878580",
                     "link-color": "#3aa99f", "bold-color": "#da702c",
                     "italic-color": "#8b7ec8", "h4-color": "#879a39",
                     "graph-line": "#575653"},
            "light": {"background-primary": "#fffcf0", "background-secondary": "#f2f0e5",
                      "text-normal": "#100f0f", "text-muted": "#6f6e69",
                      "link-color": "#24837b", "bold-color": "#bc5215",
                      "italic-color": "#5e409d", "h4-color": "#66800b",
                      "graph-line": "#b7b5ac"},
        }
        mapping = build.flexoki_roles()["tokens"]
        css_rules = rules(build.flexoki_css())
        snippet_rules = rules(build.flexoki_snippet())
        for index, scheme in enumerate(SCHEMES):
            with self.subTest(scheme=scheme):
                v = values(scheme)
                upstream = build.flexoki_upstream()[scheme]
                normalised = {name: value.lower() if value.startswith("#") else value
                              for name, value in upstream.items()}
                for name, value in normalised.items():
                    self.assertEqual(v[name], value, name)
                hexes = {value for value in normalised.values() if value.startswith("#")}
                ink, lume = normalised[mapping["ink"]], normalised[mapping["lume"]]
                mixed = build.mix_hex(ink, lume, 0.6)
                for name, value in v.items():
                    if re.match(r"^#[0-9a-f]{6}$", value):
                        if name in ("h2-color", "h3-color"):
                            self.assertEqual(value, mixed, name)
                        else:
                            self.assertIn(value, hexes, name)
                    if value.startswith("rgba("):
                        self.assertIn(f"rgba({build.rgb(lume)},", value, name)
                self.assertEqual(v["interactive-accent-rgb"], build.rgb(lume))
                for name, expected in pins[scheme].items():
                    self.assertEqual(v[name], expected, name)
                self.assertEqual(css_rules[index][1], v)
                self.assertEqual(snippet_rules[index][1], v)

    def test_every_default_and_companion_role_is_covered(self):
        default = build.sonwork_css()
        for scheme in SCHEMES:
            with self.subTest(scheme=scheme):
                declared = set(values(scheme))
                self.assertLessEqual(set(variables(default, scheme)), declared)
                protected = companion_roles(scheme)
                self.assertTrue(protected)
                self.assertLessEqual(protected, declared)

    def test_precedence_over_companion_and_base_overrides(self):
        floor = (specificity(".is-mobile.theme-dark"), specificity(".theme-dark"))
        for label, css in (("layer", build.flexoki_css()), ("snippet", build.flexoki_snippet())):
            for (selectors, _, _), scheme in zip(rules(css), SCHEMES):
                with self.subTest(css=label, scheme=scheme):
                    companion = specificity(companion_selector(scheme))
                    self.assertIn(companion_selector(scheme), COMPANION.read_text())
                    plain, variant = selectors
                    self.assertTrue(variant.endswith("[data-ow-palette]"))
                    self.assertGreater(specificity(variant), companion)
                    for selector in selectors:
                        for base in floor:
                            self.assertGreater(specificity(selector), base)

    def test_contrast_floors(self):
        for scheme in SCHEMES:
            with self.subTest(scheme=scheme):
                v = values(scheme)
                bg = v["background-primary"]
                for name in ("text-normal", "text-muted", "h1-color", "h2-color", "h3-color",
                             "h5-color", "h6-color", "bold-color", "italic-color",
                             "inline-code-color", "code-normal", "callout-warning",
                             "graph-text"):
                    self.assertGreaterEqual(contrast(v[name], bg), 4.5, name)
                # Flexoki's own light cyan-600 and green-600 sit just under 4.5:1 on paper.
                for name in ("link-color", "text-accent", "h4-color", "underline-color"):
                    self.assertGreaterEqual(contrast(v[name], bg), 4.3, name)
                    if scheme == "dark":
                        self.assertGreaterEqual(contrast(v[name], bg), 4.5, name)
                for name in ("text-faint", "code-comment", "strikethrough-color"):
                    self.assertGreaterEqual(contrast(v[name], bg), 3.5, name)
                self.assertGreaterEqual(contrast(v["text-on-accent"], v["interactive-accent"]), 4.3)
                nodes = ("graph-node", "graph-node-focused", "graph-node-tag",
                         "graph-node-attachment")
                for name in nodes:
                    self.assertGreaterEqual(contrast(v[name], bg), 3, name)
                unresolved = build.mix_hex(bg, v["graph-node-unresolved"], 0.8)
                self.assertGreaterEqual(contrast(unresolved, bg), 3)
                self.assertEqual(len({v[name] for name in nodes + ("graph-node-unresolved",)}), 5)
                for surface in ("background-primary", "background-secondary"):
                    for opacity in (0.18, 0.14):
                        fill = build.mix_hex(v[surface], v["interactive-accent"], opacity)
                        self.assertGreaterEqual(contrast(v["text-normal"], fill), 4.5,
                                                (surface, opacity))

    def test_attribution_in_layer_and_snippet(self):
        notice = build.flexoki_notice()
        for label, css in (("layer", build.flexoki_css()), ("snippet", build.flexoki_snippet())):
            with self.subTest(css=label):
                text = comments(css)
                self.assertIn(notice, text)
                self.assertIn("https://stephango.com/flexoki", text)
                self.assertIn("kepano/flexoki-obsidian", text)


if __name__ == "__main__":
    unittest.main()

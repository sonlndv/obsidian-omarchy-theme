#!/usr/bin/env python3
"""Build the Omarchy Obsidian theme.

By default uses the accepted Sonwork dark/light palette and typography and
writes both schemes to theme.css plus manifest.json in the repository root.
Pass --live to replace the matching scheme with current Omarchy colours from
~/.local/state/omarchy/current/theme/colors.toml; the other stays bundled. Pass --install to
also copy the result into .obsidian/themes/Omarchy of every vault listed in
~/.config/obsidian/obsidian.json and select it in appearance.json. With both
--live and --install, only vault copies are updated; repository files are untouched.

The theme is assembled from src/parts/: the generated colour block plus the
static font, typography and geometry layers.

An opt-in "Mounty · Flexoki" colour layer (Style Settings class `mounty-flexoki`,
from src/flexoki/) is appended after everything else, so the default palette is
unchanged while it is off. The build also writes the same colours as the
standalone snippet snippets/mounty-flexoki.css for vaults without Style Settings.
"""
import argparse
import base64
import json
import os
import pathlib
import re
import stat
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
COLORS = ROOT / "src" / "colors.toml"
LIGHT_COLORS = ROOT / "src" / "colors-light.toml"
LIVE_COLORS = pathlib.Path.home() / ".local/state/omarchy/current/theme/colors.toml"
VAULTS = pathlib.Path.home() / ".config/obsidian/obsidian.json"
THEME = "Omarchy"
PARTS = ROOT / "src" / "parts"
FLEXOKI = ROOT / "src" / "flexoki"
SNIPPET = pathlib.Path("snippets") / "mounty-flexoki.css"


def read_colors(path=COLORS):
    if not path.exists():
        sys.exit(f"no colors at {path}")
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([a-z_]+)\s*=\s*"([^"]+)"\s*$', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def rgb(color):
    """Return bare channels for the --color-*-rgb companion variables."""
    return ", ".join(str(int(color[i:i + 2], 16)) for i in (1, 3, 5))


def mix_hex(first, second, weight):
    """Mix hex colours, with weight specifying the share of second."""
    channels = (round(int(first[i:i + 2], 16) * (1 - weight)
                      + int(second[i:i + 2], 16) * weight) for i in (1, 3, 5))
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def css(c, scheme):
    def alpha(key, opacity):
        return f"rgba({rgb(c[key])}, {opacity})"

    values = {}
    for name, key in (("red", "red"), ("orange", "orange"), ("yellow", "yellow"),
                      ("green", "green"), ("cyan", "cyan"), ("blue", "blue"),
                      ("purple", "magenta"), ("pink", "bright_magenta")):
        values[f"color-{name}"] = c[key]
        values[f"color-{name}-rgb"] = rgb(c[key])
    for name in ("default", "info", "note"):
        values[f"callout-{name}"] = c["blue"]
    mapping = {
        "background-primary": "background",
        "background-primary-alt": "background",
        "background-secondary": "dark_background",
        "background-secondary-alt": "darker_background",
        "ribbon-background": "darker_background",
        "ribbon-background-collapsed": "darker_background",
        "titlebar-background": "darker_background",
        "titlebar-background-focused": "darker_background",
        "background-modifier-hover": "lighter_background",
        "nav-item-background-hover": "selection",
        "text-normal": "foreground",
        "text-muted": "dark_foreground",
        "text-faint": "muted",
        "text-accent": "accent",
        "text-accent-hover": "bright_blue",
        "text-selection": "selection",
        "text-error": "red",
        "text-success": "green",
        "interactive-accent": "accent",
        "interactive-accent-hover": "bright_blue",
        "link-color": "accent",
        "link-color-hover": "bright_blue",
        "tag-color": "accent",
        "bold-color": "bright_foreground",
        "italic-color": "foreground",
        "inline-code-color": "foreground",
        "underline-color": "green",
        "strikethrough-color": "dark_foreground",
        "h1-color": "bright_foreground",
        "h2-color": "accent",
        "h3-color": "cyan",
        "h4-color": "green",
        "h5-color": "magenta",
        "h6-color": "muted",
        "code-background": "lighter_background",
        "code-normal": "foreground",
        "code-string": "yellow",
        "code-keyword": "magenta",
        "table-header-background": "lighter_background",
        "hr-color": "muted",
        "blockquote-border-color": "accent",
        "graph-node": "foreground",
        "graph-node-focused": "accent",
        "graph-line": "muted",
        "graph-node-tag": "orange",
        "graph-node-attachment": "green",
    }
    values.update((name, c[key]) for name, key in mapping.items())
    values.update({
        "background-modifier-border": alpha("muted", 0.35),
        "text-highlight-bg": c["selection"] if scheme == "light" else alpha("yellow", 0.25),
        "nav-item-background-active": mix_hex(c["selection"], c["muted"], 0.25),
        "blockquote-background-color": alpha("accent", 0.04 if scheme == "light" else 0.05),
        "tag-background": alpha("accent", 0.10),
        "tag-border-color": alpha("accent", 0.35),
        "tag-border-width": "1px",
        "table-border-color": alpha("muted", 0.60),
    })
    if scheme == "light":
        values.update({
            "background-modifier-border": alpha("muted", 0.25),
            "table-border-color": alpha("muted", 0.45),
            "nav-item-background-active": mix_hex(c["dark_background"], c["foreground"], 0.07),
            "nav-item-color-active": c["foreground"],
            "tag-color": c["bright_yellow"],
            "tag-background": alpha("accent", 0.12),
            "tag-border-color": alpha("accent", 0.4),
            "callout-warning": c["orange"],
        })
    light_rules = ("\n.theme-light .tree-item-self.is-active {\n"
                   "  box-shadow: inset 2px 0 0 var(--interactive-accent);\n}\n"
                   if scheme == "light" else "")
    declarations = "\n".join(f"  --{name}: {value};" for name, value in values.items())
    return ("/* Omarchy theme -> Obsidian. Generated by bin/build.py.\n"
            "   Do not edit by hand; edit src/ and rebuild. */\n\n"
            f".theme-{scheme} {{\n{declarations}\n}}\n" + light_rules)


def vault_paths():
    if not VAULTS.exists():
        return []
    data = json.loads(VAULTS.read_text())
    return [pathlib.Path(v["path"]) for v in data.get("vaults", {}).values()]


def select_theme(vault, name):
    """Point appearance.json at the theme and clear our old snippet entries."""
    ap = vault / ".obsidian" / "appearance.json"
    cfg = {}
    if ap.exists():
        cfg = json.loads(ap.read_text())
        if not isinstance(cfg, dict):
            raise ValueError("appearance.json must contain an object; refusing to reset settings")
    cfg["cssTheme"] = name
    # These used to be shipped as snippets; the theme supersedes them and
    # leaving both enabled double-applies the rules.
    stale = {"omarchy-theme", "longform-writing", "sh" + "arp-edges", "plex-font"}
    cfg["enabledCssSnippets"] = [s for s in (cfg.get("enabledCssSnippets") or [])
                                 if s not in stale]
    ap.parent.mkdir(parents=True, exist_ok=True)
    ap.write_text(json.dumps(cfg, indent=2))


def manifest(name):
    return json.dumps({
        "name": name,
        "version": "1.6.2",
        "minAppVersion": "1.0.0",
        "author": "Le Son",
    }, indent=2) + "\n"


def assemble(palettes):
    """Both colour blocks first, then the static layers in load order."""
    chunks = [
        "/* Omarchy theme for Obsidian — GENERATED by bin/build.py.\n"
        "   Edits here are overwritten; edit src/ and rebuild.\n"
        "   Static layers live in src/parts/. */\n",
        *(css(palettes[scheme], scheme) for scheme in ("dark", "light")),
    ]
    for part in ("font.css", "typography.css", "geometry.css"):
        f = PARTS / part
        if f.exists():
            chunks.append(f"\n/* ===== {part} ===== */\n")
            chunks.append(f.read_text())
    return "\n".join(chunks)


def build(out_dir, colors_path=None):
    """Write theme.css and manifest.json into out_dir; return (colors, css)."""
    body = sonwork_css()
    colors = {"mode": "dark", "accent": "#39d0fc", "background": "#02050d"}
    if colors_path is not None:
        colors = read_colors(colors_path)
        scheme = colors.get("mode", "dark")
        if scheme not in ("dark", "light"):
            raise ValueError(f"unsupported colour mode: {scheme}")
        body = re.sub(r"\.theme-" + scheme + r"\s*\{[^}]*\}",
                      lambda _: css(colors, scheme), body, count=1)
    body += "\n:root { --ow-theme-id: omarchy; }\n"
    body += "\n" + (PARTS / "plugin-compat.css").read_text()
    body += "\n" + (PARTS / "graph.css").read_text()
    body += "\n" + (PARTS / "sidebar.css").read_text()
    body += "\n" + (PARTS / "emphasis.css").read_text()
    body += "\n" + flexoki_css()
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "theme.css").write_text(body)
    (out / SNIPPET).parent.mkdir(parents=True, exist_ok=True)
    (out / SNIPPET).write_text(flexoki_snippet())
    (out / "manifest.json").write_text(manifest(THEME))
    for name in ("OFL-Geist.txt", "OFL-SpaceMono.txt"):
        (out / name).write_bytes((PARTS.parent / "sonwork/fonts" / name).read_bytes())
    return colors, body


def policy_destinations_safe(vault):
    """Validate every existing component of the three authorized write paths.

    Reject even in-vault links: a linked note is not a theme/settings destination.
    This preflight does not eliminate concurrent filesystem replacement races.
    """
    if vault.is_symlink():
        return False
    for relative in (pathlib.Path(".obsidian/themes") / THEME / "theme.css",
                     pathlib.Path(".obsidian/themes") / THEME / "manifest.json",
                     pathlib.Path(".obsidian/appearance.json")):
        current = vault
        for index, component in enumerate(relative.parts):
            current = current / component
            try:
                mode = current.lstat().st_mode
            except FileNotFoundError:
                continue
            is_leaf = index == len(relative.parts) - 1
            if not (stat.S_ISREG(mode) if is_leaf else stat.S_ISDIR(mode)):
                return False
    return True


def policy_allows(vault):
    """Read only this companion's boolean opt-in; all unsafe inputs deny."""
    try:
        root = vault.resolve(strict=True)
        target = vault / ".obsidian/plugins/omarchy-writing/data.json"
        if not target.is_file() or not target.resolve(strict=True).is_relative_to(root):
            return False
        if not policy_destinations_safe(vault):
            return False
        data = json.loads(target.read_text())
        return isinstance(data, dict) and data.get("followOmarchyColors") is True
    except (OSError, ValueError, RuntimeError):
        return False


def registered_policy(vaults, policy_vault):
    if policy_vault is None:
        return None
    policy = pathlib.Path(policy_vault).resolve()
    if policy not in [v.resolve() for v in vaults]:
        raise ValueError("policy vault must be explicitly registered")
    return policy


def install(body, policy_vault=None):
    vaults = vault_paths()
    policy = registered_policy(vaults, policy_vault)
    if not vaults:
        sys.exit("no Obsidian vaults found in obsidian.json")
    for v in vaults:
        if not v.exists():
            print(f"skip (missing): {v}")
            continue
        # Re-read immediately before this vault's first mutation, after assembly.
        if policy is not None and v.resolve() == policy and not policy_allows(v):
            print("skip (policy off or unavailable)")
            continue
        d = v / ".obsidian" / "themes" / THEME
        d.mkdir(parents=True, exist_ok=True)
        (d / "theme.css").write_text(body)
        (d / "manifest.json").write_text(manifest(THEME))
        select_theme(v, THEME)
        print(f"themed: {v}")


SONWORK_DERIVED = {
    "dark": {"emphasis": "#f5a67d", "violet": "#c4b5fd", "mint": "#83d5b4",
             "unresolved": "#c7bca4", "graph-line": "#3c5c70"},
    "light": {"emphasis": "#96502a", "violet": "#6c4b99", "mint": "#22684e",
              "unresolved": "#6e6044", "graph-line": "#a1b3c2"},
}


def semantic_roles(c, scheme):
    """Return the ordered Obsidian colour properties (without --) for tokens c.

    c holds void, ground, raise, line, ink, ink-2, ink-3, lume, lume-ink, human,
    emphasis, violet, mint, unresolved and graph-line as hex colours.
    """
    roles = {
        "background-primary": "void", "background-primary-alt": "ground",
        "background-secondary": "ground", "background-secondary-alt": "raise",
        "ribbon-background": "ground", "ribbon-background-collapsed": "ground",
        "titlebar-background": "ground", "titlebar-background-focused": "ground",
        "background-modifier-hover": "raise", "background-modifier-border": "line",
        "background-modifier-border-hover": "ink-3",
        "background-modifier-border-focus": "lume",
        "text-normal": "ink", "text-muted": "ink-2", "text-faint": "ink-3",
        "text-accent": "lume", "text-accent-hover": "lume",
        "interactive-normal": "ground", "interactive-hover": "raise",
        "interactive-accent": "lume", "interactive-accent-hover": "lume",
        "color-accent": "lume", "color-accent-1": "lume", "color-accent-2": "lume",
        "inline-title-color": "ink",
        "text-on-accent": "lume-ink", "text-on-accent-inverted": "lume-ink",
        "link-color": "lume", "link-color-hover": "lume",
        "link-external-color": "lume", "link-external-color-hover": "lume",
        "text-warning": "human", "callout-warning": "human",
        "text-error": "human", "callout-error": "human",
        "callout-default": "lume", "callout-info": "lume", "callout-note": "lume",
        "bold-color": "emphasis", "italic-color": "violet",
        "code-background": "raise", "code-normal": "ink",
        "code-comment": "ink-3", "code-string": "ink-2", "code-keyword": "ink",
        "code-function": "ink", "code-property": "ink-2",
        "code-operator": "ink-2", "code-punctuation": "ink-2",
        "code-tag": "ink", "code-value": "ink-2", "code-important": "ink",
        "table-header-background": "raise", "table-border-color": "line",
        "hr-color": "line", "blockquote-border-color": "lume",
        "nav-item-color": "ink-2", "nav-item-color-hover": "ink",
        "nav-item-color-active": "ink", "nav-item-background-active": "raise",
        "nav-item-background-hover": "raise", "tab-text-color": "ink-2",
        "tab-text-color-active": "ink", "tag-color": "lume",
        "caret-color": "lume", "checkbox-color": "lume",
        "checkbox-color-hover": "lume", "checkbox-marker-color": "lume-ink",
    }
    roles.update({f"h{level}-color": "ink" for level in range(1, 7)})
    values = {name: c[key] for name, key in roles.items()}
    # Insert the quote fill directly after its border for frozen serialization.
    border = list(values).index("blockquote-border-color") + 1
    entries = list(values.items())
    entries.insert(border, ("blockquote-background-color",
                           f"rgba({rgb(c['lume'])}, {0.05 if scheme == 'dark' else 0.04})"))
    values = dict(entries)
    # Derived roles, never changes to the measured source tokens.
    values.update({"h2-color": mix_hex(c["ink"], c["lume"], 0.6),
                   "h3-color": mix_hex(c["ink"], c["lume"], 0.6),
                   "h4-color": c["mint"],
                   "inline-code-color": c["emphasis"],
                   "underline-color": c["mint"],
                   "strikethrough-color": c["ink-3"]})
    graph = (c["lume"], c["emphasis"], c["mint"], c["violet"], c["unresolved"], c["graph-line"])
    values.update(zip(("graph-node", "graph-node-focused", "graph-node-tag",
                       "graph-node-attachment", "graph-node-unresolved", "graph-line"), graph))
    values["graph-text"] = c["ink-2"]
    values.update({
        "interactive-accent-rgb": rgb(c["lume"]),
        "text-selection": f"rgba({rgb(c['lume'])}, 0.18)",
        "text-highlight-bg": f"rgba({rgb(c['lume'])}, 0.14)",
        "background-modifier-active-hover": f"rgba({rgb(c['lume'])}, 0.12)",
        "tag-background": f"rgba({rgb(c['lume'])}, 0.08)",
    })
    return values


def sonwork_css():
    """Fixed, measured Sonwork colours; independent of the live Omarchy hook."""
    source = PARTS.parent / "sonwork"
    data = json.loads((source / "palette.json").read_text())
    chunks = ["/* Mounty — compatible Omarchy distribution. Generated by bin/build.py. */"]
    for scheme, tokens in data["modes"].items():
        c = {name: token["hex"] for name, token in tokens.items()}
        # Accepted semantic colours are derived roles, not reference palette facts.
        c.update(SONWORK_DERIVED[scheme])
        values = semantic_roles(c, scheme)
        chunks.append(f".theme-{scheme} {{\n" + "\n".join(
            f"  --{name}: {value};" for name, value in values.items()) + "\n}")
    # Preserve original font bytes and full notices, even when CSS is copied alone.
    fonts = source / "fonts"
    ranges = {
        "vietnamese": "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB",
        "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20A0-20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
    }
    for filename in ("OFL-Geist.txt", "OFL-SpaceMono.txt"):
        chunks.append("/*\n" + (fonts / filename).read_text() + "\n*/")
    for slug, family, weights in (("geist", "Geist Sonwork", (400, 600)),
                                  ("space-mono", "Space Mono Sonwork", (400, 700))):
        for weight in weights:
            for subset, unicode_range in ranges.items():
                font = fonts / f"{slug}-{subset}-{weight}-normal.woff2"
                encoded = base64.b64encode(font.read_bytes()).decode("ascii")
                chunks.append(f"@font-face {{\n  font-family: '{family}';\n"
                              f"  font-style: normal;\n  font-weight: {weight};\n"
                              f"  font-display: swap;\n  src: url(data:font/woff2;base64,{encoded}) format('woff2');\n"
                              f"  unicode-range: {unicode_range};\n}}")
    chunks.extend([(source / "typography.css").read_text(),
                   (PARTS / "geometry.css").read_text()])
    return "\n\n".join(chunks) + "\n"


def build_sonwork():
    """Preview only: a fixed destination, with no vault discovery or activation."""
    out = ROOT / "dist" / "sonwork"
    body = sonwork_css()
    out.mkdir(parents=True, exist_ok=True)
    (out / "theme.css").write_text(body)
    data = json.loads(manifest("Omarchy Sonwork"))
    data["version"] = "0.1.0"
    (out / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")
    for filename in ("OFL-Geist.txt", "OFL-SpaceMono.txt"):
        (out / filename).write_bytes((ROOT / "src/sonwork/fonts" / filename).read_bytes())
    (out / "LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())
    return out


FLEXOKI_SETTINGS = """/* @settings

name: Mounty
id: mounty
settings:
    -
        id: mounty-flexoki
        title: Mounty · Flexoki palette
        description: "Opt-in Flexoki colours for dark and light modes; layout and fonts stay Mounty. Flexoki by Steph Ango, MIT, stephango.com/flexoki"
        type: class-toggle
        default: false
        addCommand: true

*/"""


def flexoki_upstream():
    """Parse the vendored kepano/flexoki-obsidian dark and light variable blocks."""
    text = (FLEXOKI / "flexoki-obsidian.css").read_text()
    out = {}
    for scheme in ("dark", "light"):
        block = re.search(r"\.theme-" + scheme + r"\s*\{([^}]*)\}", text)
        if block is None:
            raise ValueError(f"missing .theme-{scheme} block in vendored Flexoki CSS")
        out[scheme] = {name: value.strip()
                       for name, value in re.findall(r"--([\w-]+):\s*([^;]+);", block.group(1))}
    return out


def flexoki_roles():
    """Return the Mounty role -> Flexoki variable mapping from roles.json."""
    return json.loads((FLEXOKI / "roles.json").read_text())


def flexoki_values(scheme):
    """Return every upstream declaration plus the shared Mounty role table."""
    upstream = flexoki_upstream()[scheme]

    def normalise(value):
        return value.lower() if value.startswith("#") else value

    values = {name: normalise(value) for name, value in upstream.items()}
    tokens = {token: normalise(upstream[variable])
              for token, variable in flexoki_roles()["tokens"].items()}
    values.update(semantic_roles(tokens, scheme))
    return values


def flexoki_block(selectors, scheme):
    """Serialize one scheme's Flexoki declarations under the given selectors."""
    return (",\n".join(selectors) + " {\n"
            + "\n".join(f"  --{name}: {value};" for name, value in flexoki_values(scheme).items())
            + "\n}")


def flexoki_notice():
    """The upstream MIT licence text embedded in both generated outputs."""
    return (FLEXOKI / "LICENSE").read_text().rstrip("\n")


def flexoki_css():
    """The opt-in theme layer appended to theme.css, scoped to body.mounty-flexoki."""
    attribution_comment = (
        "/* Mounty · Flexoki: opt-in palette. GENERATED by bin/build.py from\n"
        "   src/flexoki/ (do not edit by hand). The Style Settings toggle above adds\n"
        "   body.mounty-flexoki; with it off the default Mounty palette is unchanged.\n"
        "   Only colour variables change; layout and fonts stay Mounty.\n"
        "   Colour values: kepano/flexoki-obsidian theme.css at commit 527685bc,\n"
        "   vendored as src/flexoki/flexoki-obsidian.css. https://stephango.com/flexoki\n"
        "\n" + flexoki_notice() + "\n*/")
    blocks = [flexoki_block((f"body.theme-{scheme}.mounty-flexoki",
                             f"body.theme-{scheme}.mounty-flexoki[data-ow-palette]"), scheme)
              for scheme in ("dark", "light")]
    return "\n\n".join([FLEXOKI_SETTINGS, attribution_comment, *blocks]) + "\n"


def flexoki_snippet():
    """The same colours as a standalone CSS snippet for vaults without Style Settings."""
    snippet_header = (
        "/* Mounty · Flexoki: optional CSS snippet. GENERATED by bin/build.py from\n"
        "   src/flexoki/ (do not edit by hand).\n"
        "   For Mounty/Omarchy without the Style Settings plugin: copy this file to\n"
        "   <vault>/.obsidian/snippets/ and enable \"mounty-flexoki\" under\n"
        "   Settings > Appearance > CSS snippets. It applies the same colours as the\n"
        "   theme's \"Mounty · Flexoki palette\" toggle; turn it off before switching to\n"
        "   another theme. Only colour variables change.\n"
        "   Colour values: kepano/flexoki-obsidian theme.css at commit 527685bc,\n"
        "   vendored as src/flexoki/flexoki-obsidian.css. https://stephango.com/flexoki\n"
        "\n" + flexoki_notice() + "\n*/")
    blocks = [flexoki_block((f":root body.theme-{scheme}",
                             f":root body.theme-{scheme}[data-ow-palette]"), scheme)
              for scheme in ("dark", "light")]
    return "\n\n".join([snippet_header, *blocks]) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--preset", choices=("omarchy", "sonwork"), default="omarchy",
                    help="theme variant (Sonwork is a fixed local preview)")
    ap.add_argument("--live", action="store_true",
                    help="read colours from the current Omarchy theme")
    ap.add_argument("--install", action="store_true",
                    help="also install into every Obsidian vault")
    ap.add_argument("--policy-vault", type=pathlib.Path,
                    help="require this registered vault's explicit companion live-colour opt-in")
    args = ap.parse_args(argv)
    if args.policy_vault is not None:
        if not (args.live and args.install and args.preset == "omarchy"):
            ap.error("--policy-vault requires --live --install with the normal preset")
        registered_policy(vault_paths(), args.policy_vault)
    if args.preset == "sonwork":
        if args.live or args.install:
            ap.error("Sonwork is preview-only; --live and --install are not supported")
        print(f"wrote preview to {build_sonwork()}")
        return
    colors_path = LIVE_COLORS if args.live else None
    if args.live and args.install:
        with tempfile.TemporaryDirectory() as tmp:
            colors, body = build(tmp, colors_path)
    else:
        colors, body = build(ROOT, colors_path)
        print(f"wrote {ROOT / 'theme.css'}, manifest.json and {SNIPPET}")
    print(f"accent {colors.get('accent')}  bg {colors.get('background')}  mode {colors.get('mode')}")
    if args.install:
        install(body, args.policy_vault)


if __name__ == "__main__":
    main()

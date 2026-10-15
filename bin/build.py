#!/usr/bin/env python3
"""Build the Omarchy Obsidian theme.

By default reads src/colors.toml (dark) and src/colors-light.toml (light) and
writes both schemes to theme.css plus manifest.json in the repository root.
Pass --live to replace the matching scheme with current Omarchy colours from
~/.local/state/omarchy/current/theme/colors.toml; the other stays bundled. Pass --install to
also copy the result into .obsidian/themes/Omarchy of every vault listed in
~/.config/obsidian/obsidian.json and select it in appearance.json. With both
--live and --install, only vault copies are updated; repository files are untouched.

The theme is assembled from src/parts/: the generated colour block plus the
static font, typography and geometry layers.
"""
import argparse
import json
import os
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
COLORS = ROOT / "src" / "colors.toml"
LIGHT_COLORS = ROOT / "src" / "colors-light.toml"
LIVE_COLORS = pathlib.Path.home() / ".local/state/omarchy/current/theme/colors.toml"
VAULTS = pathlib.Path.home() / ".config/obsidian/obsidian.json"
THEME = "Omarchy"
PARTS = ROOT / "src" / "parts"


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
    if ap.exists() and ap.read_text().strip():
        try:
            cfg = json.loads(ap.read_text())
        except json.JSONDecodeError:
            cfg = {}
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
        "version": "1.5.2",
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


def build(out_dir, colors_path=COLORS):
    """Write theme.css and manifest.json into out_dir; return (colors, css)."""
    colors = read_colors(colors_path)
    palettes = {"dark": read_colors(COLORS), "light": read_colors(LIGHT_COLORS)}
    scheme = colors.get("mode", "dark")
    if scheme not in palettes:
        raise ValueError(f"unsupported colour mode: {scheme}")
    palettes[scheme] = colors
    body = assemble(palettes)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "theme.css").write_text(body)
    (out / "manifest.json").write_text(manifest(THEME))
    return colors, body


def install(body):
    vaults = vault_paths()
    if not vaults:
        sys.exit("no Obsidian vaults found in obsidian.json")
    for v in vaults:
        if not v.exists():
            print(f"skip (missing): {v}")
            continue
        d = v / ".obsidian" / "themes" / THEME
        d.mkdir(parents=True, exist_ok=True)
        (d / "theme.css").write_text(body)
        (d / "manifest.json").write_text(manifest(THEME))
        select_theme(v, THEME)
        print(f"themed: {v}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--live", action="store_true",
                    help="read colours from the current Omarchy theme")
    ap.add_argument("--install", action="store_true",
                    help="also install into every Obsidian vault")
    args = ap.parse_args(argv)
    colors_path = LIVE_COLORS if args.live else COLORS
    if args.live and args.install:
        with tempfile.TemporaryDirectory() as tmp:
            colors, body = build(tmp, colors_path)
    else:
        colors, body = build(ROOT, colors_path)
        print(f"wrote {ROOT / 'theme.css'} and manifest.json")
    print(f"accent {colors.get('accent')}  bg {colors.get('background')}  mode {colors.get('mode')}")
    if args.install:
        install(body)


if __name__ == "__main__":
    main()

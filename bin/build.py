#!/usr/bin/env python3
"""Build Mounty with the compatible Omarchy updater identity.

By default uses the accepted Sonwork dark/light palette and typography and
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
        "version": "1.7.0",
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
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "theme.css").write_text(body)
    (out / "manifest.json").write_text(manifest(THEME))
    for name in ("OFL-Geist.txt", "OFL-SpaceMono.txt"):
        (out / name).write_bytes((PARTS.parent / "sonwork/fonts" / name).read_bytes())
    return colors, body


def policy_paths_safe(vault, relatives):
    """Validate every existing component of the three authorized write paths.

    Reject even in-vault links: a linked note is not a theme/settings destination.
    This preflight does not eliminate concurrent filesystem replacement races.
    """
    if vault.is_symlink():
        return False
    for relative in relatives:
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


def policy_destinations_safe(vault, theme=THEME):
    if theme not in (THEME, "Mounty"):
        return False
    return policy_paths_safe(vault, (
        pathlib.Path(".obsidian/themes") / theme / "theme.css",
        pathlib.Path(".obsidian/themes") / theme / "manifest.json",
        pathlib.Path(".obsidian/appearance.json")))


def policy_theme(vault):
    """Return only a recognized opted-in destination, or deny without writes."""
    try:
        root = vault.resolve(strict=True)
        target = vault / ".obsidian/plugins/omarchy-writing/data.json"
        if not target.is_file() or not target.resolve(strict=True).is_relative_to(root):
            return None
        data = json.loads(target.read_text())
        if not isinstance(data, dict) or data.get("followOmarchyColors") is not True:
            return None
        appearance = vault / ".obsidian/appearance.json"
        if not policy_paths_safe(vault, (pathlib.Path(".obsidian/appearance.json"),)):
            return None
        selected = THEME
        if appearance.exists():
            cfg = json.loads(appearance.read_text())
            if not isinstance(cfg, dict):
                return None
            selected = cfg.get("cssTheme", THEME)
        if selected not in (THEME, "Mounty") or not policy_destinations_safe(vault, selected):
            return None
        return selected
    except (OSError, ValueError, RuntimeError):
        return None


def policy_allows(vault):
    return policy_theme(vault) is not None


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
        # Re-read preference, selection and actual paths after assembly.
        name = THEME
        if policy is not None and v.resolve() == policy:
            name = policy_theme(v)
            if name is None:
                print("skip (policy off or unavailable)")
                continue
        d = v / ".obsidian" / "themes" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "theme.css").write_text(body)
        (d / "manifest.json").write_text(manifest(name))
        select_theme(v, name)
        print(f"themed: {v}")


def sonwork_css():
    """Fixed, measured Sonwork colours; independent of the live Omarchy hook."""
    source = PARTS.parent / "sonwork"
    data = json.loads((source / "palette.json").read_text())
    chunks = ["/* Mounty — compatible Omarchy distribution. Generated by bin/build.py. */"]
    for scheme, tokens in data["modes"].items():
        c = {name: token["hex"] for name, token in tokens.items()}
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
            "bold-color": "ink", "italic-color": "ink",
            "code-background": "raise", "code-normal": "ink",
            "code-comment": "ink-3", "code-string": "ink-2", "code-keyword": "ink",
            "code-function": "ink", "code-property": "ink-2",
            "code-operator": "ink-2", "code-punctuation": "ink-2",
            "code-tag": "ink", "code-value": "ink-2", "code-important": "ink",
            "table-header-background": "raise", "table-border-color": "line",
            "hr-color": "line", "blockquote-border-color": "line",
            "nav-item-color": "ink-2", "nav-item-color-hover": "ink",
            "nav-item-color-active": "ink", "nav-item-background-active": "raise",
            "nav-item-background-hover": "raise", "tab-text-color": "ink-2",
            "tab-text-color-active": "ink", "tag-color": "lume",
            "caret-color": "lume", "checkbox-color": "lume",
            "checkbox-color-hover": "lume", "checkbox-marker-color": "lume-ink",
        }
        roles.update({f"h{level}-color": "ink" for level in range(1, 7)})
        values = {name: c[key] for name, key in roles.items()}
        # Derived roles, never changes to the measured source tokens.
        values.update({"h2-color": mix_hex(c["ink"], c["lume"], 0.6),
                       "h3-color": mix_hex(c["ink"], c["lume"], 0.6)})
        accents = {
            "dark": ("#f5a67d", "#c4b5fd", "#83d5b4", "#8a939e", "#c7bca4"),
            "light": ("#96502a", "#6c4b99", "#22684e", "#515c68", "#6e6044"),
        }
        peach, lilac, mint, slate, stone = accents[scheme]
        values.update({"bold-color": peach, "italic-color": lilac,
                       "inline-code-color": peach, "underline-color": mint,
                       "strikethrough-color": slate})
        graph = {
            "dark": (c["lume"], peach, mint, lilac, stone, "#3c5c70"),
            "light": (c["lume"], peach, mint, lilac, stone, "#a1b3c2"),
        }
        values.update(zip(("graph-node", "graph-node-focused", "graph-node-tag",
                           "graph-node-attachment", "graph-node-unresolved", "graph-line"), graph[scheme]))
        values["graph-text"] = c["ink-2"]
        values.update({
            "interactive-accent-rgb": rgb(c["lume"]),
            "text-selection": f"rgba({rgb(c['lume'])}, 0.18)",
            "text-highlight-bg": f"rgba({rgb(c['lume'])}, 0.14)",
            "background-modifier-active-hover": f"rgba({rgb(c['lume'])}, 0.12)",
            "tag-background": f"rgba({rgb(c['lume'])}, 0.08)",
        })
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
        print(f"wrote {ROOT / 'theme.css'} and manifest.json")
    print(f"accent {colors.get('accent')}  bg {colors.get('background')}  mode {colors.get('mode')}")
    if args.install:
        install(body, args.policy_vault)


if __name__ == "__main__":
    main()

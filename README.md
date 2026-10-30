# Omarchy for Obsidian

**Omarchy 1.6.1** keeps the accepted cool dark/light surfaces, Geist prose and
interface text, Space Mono headings/code and soft native controls. H2/H3 have a
restrained cyan/ink blend; other headings stay ink. Original licensed Latin and
Vietnamese subsets are embedded for offline use. Names, repository/community
entry and plugin IDs are unchanged: **Omarchy** and **Omarchy Writing**.

## Install or update the theme

- **Existing community installation:** open Settings → Appearance → Themes,
  check for updates and update **Omarchy**. Keep Omarchy selected. This updates
  the theme only; it never installs or updates the companion.
- **New community installation:** Settings → Appearance → Manage, search for
  **Omarchy**, install it, then select it. Choose Light, Dark or Adapt to system.
- **Manual ZIP:** download the source ZIP for the desired tagged release from
  this repository's Releases page and extract it. Copy only root `theme.css`,
  `manifest.json`, `OFL-Geist.txt`, `OFL-SpaceMono.txt` and `LICENSE` into
  `<vault>/.obsidian/themes/Omarchy/` (create that folder if needed). The files
  belong directly in `Omarchy/`, without an extra extracted repository folder.
  Select Omarchy in Appearance; reselect it or reload Obsidian after replacement.

No local build or font installation is needed for those installation routes.
Use only reviewed/published release files; this author pass does not certify
publication. For removal, choose another theme before removing its theme folder.

## Graph and side tools

Ordinary graph notes are cool blue/cyan, tags mint, attachments violet,
unresolved notes quieter blue, and focused/hover nodes peach/ochre. Links stay
restrained and labels use readable secondary ink. The theme uses supported graph
colour probes, including the native unresolved alpha; it does not change sizes,
physics, zoom, graph data or animation behavior.

For varied **cluster** colours, open the native graph settings and add manual
**Groups** with your own search queries and colours. Native Groups override the
per-node theme colours. **Show tags** and **Attachments** are optional native
filters; enable them yourself if useful. CSS neither assigns clusters nor
changes those settings. File explorer and Outline active/focused rows gain a
restrained 1px cyan indicator, without changing panel layout or plugin icons.

Optional **Omarchy Writing 0.2.0** adds a pen ribbon button and **Open writing
tools** command: toggle Zen/typewriter or explicitly open native Outline and
Backlinks. No extra community plugins are needed for those panes. Enable the
corresponding Obsidian core plugin yourself if its menu action is unavailable.
The companion never enables plugins. See [companion/README.md](companion/README.md)
for clean installation, same-folder upgrades retaining `data.json`, hotkeys,
comfort settings and removal. Normal works without the companion.

## Text and palette preferences

The theme follows native preferred text sizing with about 68ch readable line
length and 1.7 leading; enable Obsidian's readable-line-length setting. Explicit
user interface/text/monospace font overrides take precedence. Mobile safe areas
and native long code/table scrolling remain. Companion width/title preferences
are opt-in presentation changes, not note edits.

The measured public [Sonwork](https://sonwork.org/) palette facts remain in
`src/sonwork/palette.json`; the current heading/graph roles are derived theme
choices, not edits to that reference. Sonwork is provenance, not a new product
name. `--preset sonwork` remains a legacy development preview option with its
existing paths/name and rejection of `--live`/`--install`; ordinary users should
install **Omarchy**.

`python3 -B bin/build.py --live` deliberately replaces the matching scheme from
`~/.local/state/omarchy/current/theme/colors.toml`, retaining the other scheme,
fonts and compatibility layers. This explicitly overrides the fixed palette,
including heading/graph roles; missing graph roles have native semantic fallbacks.
The existing `--live --install` interface updates configured vault copies only,
leaving root artifacts untouched. `--install` selects Omarchy in all configured
vaults and is not needed for preview. Unreadable appearance JSON fails closed.
No hook or live installer was executed during this author pass.

## Build and checks

```sh
python3 -B bin/build.py
python3 -B -m unittest discover -s tests -v
node --check companion/main.js
node --test tests/test_companion.cjs
python3 -B bin/package_companion.py
```

Default output is reproducible root `theme.css`, `manifest.json` and OFL notices.
Python discovery is the aggregate: it includes Node syntax/companion checks and
package/version/allowlist tests. CI runs it, rebuilds and checks generated diffs.
Original font bytes/notices and plugin compatibility are retained. MIT license:
[LICENSE](LICENSE); embedded fonts retain their full OFL notices, also in CSS.

## Limits and rollback

Native graph, menu, ribbon, core-pane actions and visual acceptance for this
refinement remain parent QA work; passing source tests is not native acceptance
or publication. Companion behavior targets the main window, not detached editor
windows. Narrow desktop testing is not physical iPhone/mobile IME certification.
See [COMPATIBILITY.md](COMPATIBILITY.md) and [CHANGELOG.md](CHANGELOG.md).

To roll back, disable Omarchy Writing, then replace only the Omarchy theme files
with the retained **1.6.0** release files and reselect the theme/reload. To roll
back the companion, replace its three runtime files with the retained **0.1.0**
files in the same `omarchy-writing` folder while disabled, retaining `data.json`.
Never reset notes, graph settings, hotkeys or other plugin settings. Publication
and any upstream corrective patch remain separate reviewed actions.

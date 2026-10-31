# Omarchy for Obsidian

**Omarchy 1.6.2** keeps the accepted cool dark/light surfaces, Geist prose and
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
Use the reviewed files from the chosen published release. For removal, choose
another theme before removing its theme folder.

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

Optional **Omarchy Writing 0.3.0** adds a pen ribbon button and **Open writing
tools** command: toggle Zen/typewriter or explicitly open native Outline and
Backlinks. No extra community plugins are needed for those panes. Enable the
corresponding Obsidian core plugin yourself if its menu action is unavailable.
The companion never enables plugins. See [companion/README.md](companion/README.md)
for clean installation, same-folder upgrades retaining `data.json`, hotkeys,
comfort settings and removal. Normal works without the companion.

## Follow Omarchy colours — optional, initially OFF

With **Omarchy Writing 0.3.0 enabled**, open Settings → Omarchy Writing →
**Follow Omarchy colours**. Missing/older settings default to OFF. OFF immediately
protects the fixed Sonwork colour roles, including headings and graph, even if
the loaded Omarchy CSS was previously generated from a live desktop palette.
The companion checks a computed Omarchy identity marker; another selected theme
is not recoloured. Fonts, native text sizing, geometry and Graph Groups stay
unchanged. This is presentation, not a rewrite of the installed CSS.

ON permits the **next desktop Omarchy theme application** to supply live colours.
It does not switch the OS theme, immediately rebuild CSS or promise that a phone
has synced theme/plugin/settings files. External changes reload only this
companion's preferences without saving them back. Native CSS-change notifications
reconcile theme switches and refresh graph colours with a recursion guard.

The optional hook policy is explicit and scoped to one registered vault:

```sh
python3 -B bin/build.py --live --install --policy-vault /path/to/chosen-vault
```

With that flag, only literal boolean `true` for `followOmarchyColors` in that
vault's `.obsidian/plugins/omarchy-writing/data.json` permits its writes. Missing,
invalid, non-boolean or escaping symlink targets fail closed: no theme/manifest/
appearance writes or directory creation there. Policy is re-read after assembly
immediately before the target's mutations. Other registered vaults keep existing
behavior. No flag preserves the legacy bulk-install behavior; it does not enforce
this opt-in. The companion itself does not execute this command or read vault
paths. Use fixtures for testing, not a real registry.

`hooks/50-obsidian-theme` is a reviewable host-wrapper **template only**. Admin
owns its exact scoped installation after release/review/backups; this source does
not modify the shared host hook. The runner executes regular files (except
`*.sample`), so changing executable bits or adding `.disabled` is not the toggle.
No other OS/app hook is changed. Keep owned hook/runtime/preference backups and
stop on concurrent edits before deployment. No live deployment or activation is
implied by these source files. Existing 0.2 runtime files may be staged without
being enabled; Zen requires explicitly enabling the companion.

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

Verified in isolated Obsidian 1.14.5 with synthetic notes: both graph palettes,
real node hover, painted heading/prose fonts, ribbon/command menus, native
Outline/Backlinks, keyboard Zen and Exit, real cursor centering, menu guards and
active-Zen unload cleanup. The command menu explicitly targets the main document
even after Graph used an iframe. Standard SDK ribbon metadata and explicit pane
actions remain native; Zen does not rewrite pane arrangements. Companion
behavior targets the main window, not detached editors. The 390px/200% preferred-
size probe is desktop evidence, not physical iPhone/mobile IME certification.
See [COMPATIBILITY.md](COMPATIBILITY.md) and [CHANGELOG.md](CHANGELOG.md).

To roll back, disable Omarchy Writing, then replace only the Omarchy theme files
with the retained **1.6.0** release files and reselect the theme/reload. To roll
back the companion, replace its three runtime files with the retained **0.1.0**
files in the same `omarchy-writing` folder while disabled, retaining `data.json`.
Never reset notes, graph settings, hotkeys or other plugin settings. Publication
and any upstream corrective patch remain separate reviewed actions.

For a failed follow-colours rollout, disable the companion and have Admin restore
only the reviewed hook backup; restore the backed-up owned theme/runtime files
without resetting `data.json`, Graph Groups, notes or other preferences. Older
companions ignore this new key, and an older hook does not enforce the policy:
verify the complete rollback combination before allowing desktop theme writes.
The native CLI's missing filesystem endpoint remains a separate capability gate;
this update does not repair it or bypass activation/native verification.

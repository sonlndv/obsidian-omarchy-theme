# Omarchy theme for Obsidian

Omarchy 1.6.0 brings the accepted Sonwork dark/light palette to the normal
community theme: Geist prose and interface text, Space Mono headings/code,
cyan actions, native Obsidian layout and the existing soft corners. Original
licensed Latin and Vietnamese font subsets are embedded for offline/mobile use.
Full font notices are included in CSS and the adjacent OFL files.

## Build and verify

```sh
python3 -B bin/build.py
python3 -B -m unittest discover -s tests -v
node --check companion/main.js
node --test tests/test_companion.cjs
```

The default build writes reproducible root `theme.css`, `manifest.json` and
font licenses for **Omarchy 1.6.0**. Python discovery also runs the companion
syntax and Node built-in tests, so it is the aggregate check. CI runs these
checks and rebuilds the root artifacts before checking for generated diffs.

The measured public [Sonwork](https://sonwork.org/) palette is recorded in
`src/sonwork/palette.json`. The theme keeps preferred-first native text scaling,
about 68ch readable line length and 1.7 leading. Choose Obsidian's readable-line
length setting and Light/Dark/Adapt to system under Appearance. Long code and
tables retain native scrolling. No artwork, website navigation or scripts ship.

## Update or install the theme

Existing users can update **Omarchy** through its current community-theme entry.
For manual installation, copy root `theme.css`, `manifest.json`, `OFL-Geist.txt`
and `OFL-SpaceMono.txt` into `<vault>/.obsidian/themes/Omarchy/`, then select
Omarchy under Appearance. A theme update does **not** install or enable the
optional companion. Normal works independently of any plugin.

`python3 -B bin/build.py --preset sonwork` retains the separately named fixed
**Omarchy Sonwork** preview in `dist/sonwork/`. It rejects `--live`/`--install`.
Remove a manual preview by selecting another theme and deleting only its theme
folder. Do not delete notes or appearance settings.

## Deliberately follow Omarchy colours

`python3 -B bin/build.py --live` replaces the matching light/dark colour block
from `~/.local/state/omarchy/current/theme/colors.toml`, retaining the other
Sonwork scheme and the new fonts/compatibility layer. This is a deliberate
palette override; it can change heading and accent colours from the fixed look.
The existing `--live --install` hook interface remains available and updates
only configured vault copies, leaving root artifacts untouched. `--install`
selects Omarchy in all configured vaults; it is never needed for preview and
has not been executed against live vaults in this author pass. Unreadable
appearance JSON now fails closed rather than replacing preferences.

## Optional writing companion

See [companion/README.md](companion/README.md) for manual installation, Zen,
optional typewriter, width/title settings, removal and packaging. The companion
has no dependencies or prebound hotkeys. Zen always starts off.

See [COMPATIBILITY.md](COMPATIBILITY.md) for scoped plugin contracts and limits,
and [CHANGELOG.md](CHANGELOG.md) for changes. Native app/plugin acceptance is a
separate parent QA step; no physical iPhone certification is claimed.

MIT theme/companion license: [LICENSE](LICENSE). Fonts retain their full OFL
copyright and license notices.

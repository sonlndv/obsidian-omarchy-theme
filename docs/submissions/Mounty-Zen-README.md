# Mounty Zen

Optional Zen, typewriter editing and Markdown width/title controls for **Mounty
and Omarchy equally**. This is Mounty Zen **0.4.1**, stable ID/folder
**omarchy-writing**. The plugin's new listing is planned, not submitted or
approved; the theme works without it and never auto-installs it.

![The retained synthetic desktop native writing-tools menu.](docs/images/mounty-writing-tools.png)

![Synthetic writing content with a visible Exit Zen control.](docs/images/mounty-zen.png)

These real retained synthetic captures illustrate unchanged behavior, not fresh
native validation of this display-name/metadata patch.

## Install or update

For a reviewed clean manual install, copy main.js, styles.css and manifest.json
into `<vault>/.obsidian/plugins/omarchy-writing/`, then explicitly enable
**Mounty Zen** in Community plugins. For an existing manual companion, disable
it first, replace those three runtime files in the SAME folder and **preserve
data.json**, then re-enable it. Do not create a mounty-zen ID, enable both names
as separate plugins or edit a manifest to fake a directory migration.

An official install/upgrade route is conditional on actual directory availability;
verify ID omarchy-writing and the intended version before relying on it. No new
listing/repository URL or release upload is claimed. A staged file/source export
is not live activation. See [optional migration](docs/MIGRATING-TO-MOUNTY.md).

## Controls and conservative defaults

Use the pen ribbon or **Mounty Zen: Open writing tools**. The native menu offers
Zen, optional typewriter, Outline and Backlinks. No pane opens at startup; core
commands unavailable in the app are disabled, not enabled automatically.

Stable assignable commands, with no prebound hotkeys:

- `omarchy-writing:open-writing-tools`
- `omarchy-writing:toggle-zen`
- `omarchy-writing:toggle-typewriter`

Zen always starts OFF and provides a visible Exit Zen button. Typewriter is OFF;
when opted in, it centers only a focused, unselected cursor in Zen source editing,
with native-menu/IME/selection/manual-scroll guards and no idle loop. Width starts
standard and hiding the filename title starts OFF. Follow Omarchy colours starts
OFF, protecting the fixed palette for recognized Omarchy/Mounty CSS. ON permits
the next desktop Omarchy application via a separately reviewed scoped hook; it
does not execute shell, install hooks, switch OS theme or confirm phone sync.
Legacy bulk hooks may reselect Omarchy, an equal supported theme route.

Only explicit own settings changes are saved; note content, Graph Groups, other
plugin settings, hotkeys and layout are not rewritten. Unload removes owned
presentation/listeners/menu/button/padding and restores owned body state.

## Privacy, limits and rollback

Runtime is offline and needs no account, telemetry, network, shell, dependency
installer or external library. Obsidian supplies its SDK; main.js is directly
loadable CommonJS source with styles.css. There is no build/transpiler step.
The owner's Obsidian/GitHub account linking is required for submission, not use.

Behavior targets the main window. Retained native QA used Obsidian 1.14.5;
minAppVersion 1.5.0 is inherited metadata, not freshly certified. Physical phone,
detached editor, IME/mobile keyboard and remote sync are not certified. Disable
before restoring a backed-up runtime in the same folder; keep data.json and
owned theme/hook backups. Never reset notes, Groups or other settings. Older
hook/plugin combinations may not enforce opt-in; verify before desktop writes.

## Source, attribution and release preparation

This standalone source ZIP extracts directly to a repository ROOT, not an
installer. main.js and styles.css retain the reviewed runtime bytes. The maintained
generator/exporter and original source live at
https://github.com/sonlndv/obsidian-omarchy-theme in `bin/` and `companion/`.
Preserve original author Le Son and the [MIT LICENSE](LICENSE).

After review, the owner prepares independent public plugin source and tags
exactly **0.4.1**, uploading main.js, manifest.json and styles.css to that release.
The default branch must carry this plugin manifest, README and LICENSE, not the
theme/Omarchy monorepo root. See [submission preparation](docs/COMMUNITY-LISTINGS.md)
for official paths and pending status. No source export establishes account
access, listing submission, approval, publication or activation.

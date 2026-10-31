# Mounty Zen 0.4.1

Optional writing controls for **Mounty and Omarchy equally**: Zen, optional typewriter scrolling,
Markdown width/title preferences, and a small native writing-tools menu. The
theme works without this companion. It uses only Obsidian's provided SDK
and browser APIs, without external dependencies, network or shell execution.

## Install or update

The product/display name is **Mounty Zen**. Its new official listing is planned,
not submitted or approved; no live listing URL or new repository is claimed. The stable plugin ID and folder
remain **omarchy-writing**; command IDs and `data.json` preferences are preserved.
The theme updater does not install or update this optional manual companion.

- **Clean install:** extract `omarchy-writing-0.4.1.zip`, place its
  `omarchy-writing/` folder under one chosen vault's `.obsidian/plugins/`, then
  explicitly enable Mounty Zen in Community plugins. Runtime files must sit
  directly in that folder, without another nested archive directory.
- **Upgrade:** disable the existing Omarchy/Mounty Writing companion, replace
  only `main.js`, `styles.css`, `manifest.json` and documentation in the SAME
  folder, retain **data.json**, then re-enable it. Do not create a new plugin ID
  or discard settings. Minimum declared Obsidian version remains 1.5.0.

A staged runtime or release ZIP is not activation: explicitly enable the companion
and verify it in the chosen vault after updating.

## Writing tools

Click the pen ribbon, or use **Mounty Zen: Open writing tools** in the command
palette. The native menu offers Zen, typewriter, Outline and Backlinks. Opening
a pane is explicit and exits Zen first; no pane opens at startup. Unavailable
core commands are disabled and rechecked on invocation. Enable Obsidian's own
Outline/Backlinks core plugins yourself if wanted; no extra community plugins
are needed. Native command menus explicitly use the main document.

Stable assignable commands (no default hotkeys):

- `omarchy-writing:open-writing-tools`
- `omarchy-writing:toggle-zen`
- `omarchy-writing:toggle-typewriter`

Zen always starts OFF. It hides surrounding native navigation with CSS, without
collapsing panels or persisting layout. Plugin content/toolbars, menus and
modals remain. **Exit Zen** is visible and keyboard/touch accessible; the command
also exits when the ribbon is hidden. No Escape handler hijacks IME, Vim,
suggestions, menus or native dialogs. Unload restores owned body attributes and
removes the button, listeners, frame and editor-padding class; the SDK cleans
the ribbon and the owned menu is closed.

## Conservative preferences

- **Typewriter OFF:** when explicitly enabled, only Zen source editing centers
  a focused unselected cursor after input/keyboard movement via public
  `Editor.scrollIntoView(range, true)`. No idle loop or reading-mode scrolling.
  Selection, composition, modals/suggestions and visible menus suppress it;
  hidden menu remnants do not. Manual wheel/touch/pointer interaction pauses it.
- **Width standard:** narrow/standard/wide are 56/68/82ch in Markdown only.
  Enable Obsidian's native readable-line-length setting. Other plugin views stay
  native and preferred text sizing is unchanged.
- **Hide filename title OFF:** opt in to hide Markdown's filename inline title
  while keeping your own H1. Notes are never scanned or rewritten.
- **Follow Omarchy colours OFF:** immediately protects Mounty's fixed semantic
  palette when the loaded theme carries the retained Omarchy identity marker,
  including emphasis, heading and graph roles. Another theme is not recoloured.
  New roles match the theme source; original fonts/geometry stay unchanged.

Only explicit preference/command changes save this plugin's settings. Zen state
is not persisted. External preference changes reload only this plugin's data
without saving back. CSS changes reconcile the palette with one guarded native
notification per attribute transition. The stable internal marker/attribute and
`followOmarchyColors` key remain compatible with 0.3; update both distributions
for the new protected emphasis colours.

ON permits the **next normal desktop Omarchy theme application** to supply live
colours through a separately reviewed scoped hook. It does not switch OS theme,
execute a command, rebuild immediately or promise phone sync. For a policy vault
selected as Mounty, the hook updates Mounty's matching folder/manifest; Omarchy
still works. OFF also protects already-live CSS locally. The hook separately
blocks future policy-vault writes when OFF/missing/invalid. Without the policy
flag, legacy bulk behavior remains. See the [root guide](../README.md) for deliberate
exact-vault setup, backups outside the executable hook directory and native Groups.

## Limits, removal and rollback

Behavior targets the main window, not detached/pop-out editors. The 1.7.0/0.4.0
formatting, palette, menu/Exit and cleanup checks use an isolated synthetic desktop
vault; they are not physical iPhone, mobile keyboard/touch/IME, remote-sync or full
accessibility certification. Older SDK command/notification limits remain. A
published package is not proof that a particular vault has loaded it.

Disable the companion to restore presentation. For removal, delete only its
plugin folder after disabling it; retain `data.json` if returning later. For
rollback, restore the backed-up runtime in the same folder while disabled and
keep preferences; restore/select the retained Omarchy theme as needed. Restore
any owned hook backup through its normal maintainer. Older hook/companion pairs may not enforce follow-colours;
verify before allowing desktop writes. Never reset notes, groups or other
settings. This companion does not read/write note content, graph configuration,
other plugin settings, hotkeys or layout.

## Package and verify

```sh
python3 -B bin/package_companion.py
node --check companion/main.js
node --test tests/test_companion.cjs
```

The ZIP derives ID/version from its manifest, uses deterministic metadata, and
contains exactly the three runtime files, this README and MIT LICENSE under
`omarchy-writing/`. No `data.json`, private fixture, log or third-party package
is included. Python aggregate discovery also runs the companion contract tests;
these do not replace native acceptance or activation evidence.

## Community submission and optional migration

The runtime needs no account, network, shell, telemetry or dependency installer.
Son needs an Obsidian account and GitHub linking to submit/claim directory entries;
those are owner actions, not plugin-runtime requirements. The inherited minimum
1.5.0 is declared, not freshly certified; retained native QA used Obsidian 1.14.5.

Once an official entry actually exists, verify its ID **omarchy-writing** and
available version before choosing that upgrade route. Do not enable a second
plugin or edit a manifest to fake migration. See the [migration guide](../docs/MIGRATING-TO-MOUNTY.md)
and [submission/source guide](../docs/COMMUNITY-LISTINGS.md). Ordinary Omarchy
users already get the same theme and may keep their current name/selection.
JavaScript and CSS runtime behavior are unchanged in this naming patch; the
manifest updates the display name, description and version.

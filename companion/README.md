# Omarchy Writing 0.2.0

Optional CommonJS Obsidian companion, ID `omarchy-writing`. Uses only Obsidian's
provided SDK and browser APIs. No network, note-content reads/writes, editor text
writes, automated workspace-layout rewrite, other plugin configuration changes
or default hotkeys. Obsidian manages normal ribbon metadata and remembers panes
opened through explicit native actions; Zen itself does not collapse/rewrite them.

## Install or upgrade

For a clean optional install, extract the companion release ZIP and copy its
`omarchy-writing/` folder into one chosen vault's `.obsidian/plugins/`. Its
`main.js`, `styles.css` and `manifest.json` must sit directly in that folder.
Enable **Omarchy Writing** explicitly in Community plugins. Minimum Obsidian
version is 1.5.0. This is a manual companion, not a community-plugin listing.
The Omarchy theme updater cannot install/update it; Normal needs no companion.

To upgrade an existing installation, disable the companion first, then replace
only `main.js`, `styles.css`, `manifest.json` (and documentation) in the SAME
`.obsidian/plugins/omarchy-writing/` folder. **Keep `data.json`** to retain your
settings. Do not delete/recreate the folder or rename the ID. Re-enable the
companion and check that **Open writing tools** is available. Zen still starts
off. Obsidian 1.14.5 can cache the old manifest version while the app stays open;
if its label is stale, check again after your next normal app opening with work
saved. Do not reset the vault or force a reload just to refresh that label.

## Open writing tools

Click the pen ribbon button, or run **Omarchy Writing: Open writing tools** in
the command palette. In Zen, the ribbon is hidden; the command remains usable.
Assign a shortcut under Settings → Hotkeys if desired; no hotkey is prebound.
The small native menu offers Zen, typewriter, Outline and Backlinks. Opening a
pane explicitly exits Zen first so the pane can be seen. Unavailable native
commands are disabled and rechecked on invocation. Enable Outline/Backlinks in
Obsidian Core plugins yourself if wanted; no extra community plugin is needed.
Nothing opens/rearranges panes or enables plugins at startup.

Stable commands:

- `omarchy-writing:open-writing-tools`: open the native tools menu.
- `omarchy-writing:toggle-zen`: enter/exit Zen. Zen always starts off. A visible
  keyboard/touch **Exit Zen** button also exits.
- `omarchy-writing:toggle-typewriter`: change the optional typewriter setting,
  persisting only this companion's preference; this does not enter Zen.

Zen hides desktop side navigation/ribbons, tab headers and status chrome using
scoped CSS. Native view headers, plugin content, toolbars, menus, suggestions
and modals remain available. It never collapses a sidebar or rewrites layout.
Exit/unload removes the temporary button, listeners, queued frame and editor
padding class and restores owned body attributes. Escape is deliberately never
bound: IME, Vim, modal and suggestion handling keep their own keys. Mobile shell
variants may expose additional navigation; native runtime review is required.

Settings are conservative: typewriter **off**, width **standard**, hide filename
inline title **off**. Narrow/standard/wide set Markdown readable-line width to
56/68/82ch (including Normal); enable Obsidian's readable-line-length option.
Other plugin views are untouched. Hide filename title hides only Markdown's
inline filename presentation; your own H1 stays. No notes are inspected to
choose this preference. Native text-size controls are never overridden.

With typewriter enabled, only Zen source editing centers the focused,
unselected cursor after user input or keyboard movement using public
`Editor.scrollIntoView(range, true)`. Bottom space is scoped to that editor.
There is no idle loop or read-mode scrolling. Wheel/touch/pointer interaction
pauses centering briefly; selections, composition, visible native menus, modals/suggestions, Escape
and unrelated inputs do not trigger it. Exact centering depends on Obsidian's editor API and viewport.
Hidden/disconnected menu elements do not permanently block typewriter. Owned
menus close on unload; Obsidian's SDK owns ribbon cleanup. No Escape handler is
installed, and existing IME/selection/manual-scroll guards remain.

## Known limits

Zen/typewriter/menu actions target the main Obsidian window. Detached/pop-out
editors are not supported. Native 0.2.0 checks in isolated Obsidian 1.14.5 covered
the pen ribbon, main-document command menu after Graph, all four menu actions,
keyboard selection/Zen, cursor centering, menu/Escape guards and unload cleanup.
A 390px desktop viewport at a directly probed 200% preferred text size retained a
hit-testable 44px Exit button and keyboard exit. These checks do not certify
physical iPhone/touch/mobile-keyboard/IME operation or older SDK versions. The native
command registry is feature-checked; unavailable Outline/Backlinks actions are
disabled rather than enabling core plugins or inventing pane APIs.

Only explicit settings/command changes call this plugin's `saveData`. Zen state
is not persisted. Disable the companion to restore presentation; to remove it,
disable it first and delete only its plugin folder. Notes and other settings
are left intact. This plugin is opt-in/manual, not a community plugin listing.

Packaging from the repository root (no dependency installation):

```sh
python3 -B bin/package_companion.py
```

Produces `dist/omarchy-writing-0.2.0.zip` with an `omarchy-writing/` directory,
the three runtime files, this README and the repository MIT license. Do not add
`data.json`, private fixture notes, logs or third-party packages to the archive.
Test with `node --test tests/test_companion.cjs` (Node built-in runner). These
are SDK/DOM contract tests, not native-plugin or physical iPhone certification.

For rollback, disable this companion and restore the three 0.1.0 runtime files
in the same folder, preserving `data.json`, then re-enable it. Disable it before
rolling back the Omarchy theme to 1.6.0; no note/layout reset is needed.

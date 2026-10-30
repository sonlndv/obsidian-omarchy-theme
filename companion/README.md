# Omarchy Writing 0.1.0

Optional CommonJS Obsidian companion, ID `omarchy-writing`. Uses only Obsidian's
provided SDK and browser APIs. No network, note reads/writes, editor text writes,
layout persistence, other plugin configuration changes or default hotkeys.

Copy `main.js`, `styles.css`, `manifest.json` and this README into one chosen
vault's `.obsidian/plugins/omarchy-writing/`, then explicitly enable **Omarchy
Writing** in Community plugins. The theme updater cannot install it. The Normal
theme is fully usable without this companion. Minimum Obsidian version: 1.5.0.

Commands (assign shortcuts in Settings → Hotkeys):

- `omarchy-writing:toggle-zen`: enter/exit Zen. Zen always starts off, including
  after restart. A visible keyboard/touch **Exit Zen** button also exits.
- `omarchy-writing:toggle-typewriter`: change the optional typewriter setting.
  This persists only this companion's preference; it does not enter Zen.

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
pauses centering briefly; selections, composition, modals/suggestions, Escape
and unrelated inputs do not trigger it. Exact centering depends on Obsidian's
editor API and viewport. In isolated Obsidian 1.14.5, native keyboard movement
centered the cursor, manual scrolling paused it, and selections, composition
and an open command palette suppressed it. Escape closed the native palette
without leaving Zen. Composition-event checks are not physical IME certification.

## Known limits

Zen/typewriter are main-window features in 0.1.0; use the commands in the main
Obsidian window, and do not expect them to follow a detached/pop-out editor.
A 390×844 desktop viewport with 200% preferred editor text was checked, but this
is not an iPhone, mobile-keyboard or physical touch test. Native keyboard Enter
and pointer activation of Exit Zen were checked. Exit and active-Zen unload
restored layout/presentation without changing the synthetic notes or existing
core preferences.

Only explicit settings/command changes call this plugin's `saveData`. Zen state
is not persisted. Disable the companion to restore presentation; to remove it,
disable it first and delete only its plugin folder. Notes and other settings
are left intact. This plugin is opt-in/manual, not a community plugin listing.

Packaging from the repository root (no dependency installation):

```sh
python3 -B bin/package_companion.py
```

Produces `dist/omarchy-writing-0.1.0.zip` with an `omarchy-writing/` directory,
the three runtime files, this README and the repository MIT license. Do not add
`data.json`, private fixture notes, logs or third-party packages to the archive.
Test with `node --test tests/test_companion.cjs` (Node built-in runner). These
are SDK/DOM contract tests, not native-plugin or physical iPhone certification.

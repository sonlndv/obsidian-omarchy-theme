# Plugin compatibility

The normal theme always includes `src/parts/plugin-compat.css`, independently
of the companion. The following exact installed packages were exercised in
isolated Obsidian 1.14.5 using synthetic notes, not the user's vault or plugin
configuration. Third-party packages/configurations are not shipped.

Native checks covered real Omnisearch results and Escape, QuickAdd prompt entry
and submission, TaskNotes form input and creation of a synthetic task, and Note
Toolbar's settings/new-item UI plus frontmatter-bound toolbar container. The
Maps canvas, view controls and native marker-colour aliases were checked with
public example coordinates and network tiles blocked. These representative
checks are not certification of every plugin feature: custom toolbar actions,
Maps tiles/marker popups, authentication, sync and physical-device behavior were
not exhaustively tested. TaskNotes fixture input used a synthetic input event
before native Save activation; no real task was created.

| Plugin | Version | Theme integration |
| --- | --- | --- |
| Maps | 0.2.2 | `.bases-map-container` aliases marker background to accent and icon to `--text-on-accent`, avoiding white on cyan. Tiles, popups and marker source data remain native. |
| Note Toolbar | 1.35.22 | `.cg-note-toolbar-container`/`.cg-note-toolbar-callout` use surface, border and text aliases. Toolbar placement/actions remain owned by the plugin. |
| Omnisearch | 1.32.0 | `.omnisearch-modal` highlight background/text aliases use native highlight and ink. Search behavior and icons remain native. |
| QuickAdd | 2.33.1 | `.quickAddModal` ordinary text inherits native ink; existing native colour/focus/control tokens remain authoritative. |
| TaskNotes | 4.14.0 | `.tasknotes-plugin` ordinary text/border/action aliases follow the theme. Status, priority, calendar and semantic colour tokens are preserved. |

No blanket SVG recolouring, geometry overrides, tile filters or hidden plugin
toolbars are included. Later plugin versions may change selector/token contracts.
The companion limits width/title controls to Markdown and leaves plugin views
alone. Desktop/narrow synthetic QA and physical mobile testing are distinct;
no physical iPhone certification is claimed by this release candidate.

## 1.6.1 graph and writing-tools refinement

Obsidian 1.14.5 reads graph colours from temporary `.graph-view.color-*` probes
inserted directly under body. The global graph layer therefore uses those
supported probes, including focused/hover classes. Unresolved opacity is scoped
to its probe at 0.8 and tested after compositing. Native Groups stay authoritative;
no per-group fill-N override, graph settings write, sizing or physics change ships.
Only native File explorer/Outline row selection/focus gains a 1px indicator;
`plugin-compat.css` and plugin geometry remain unchanged.

Omarchy Writing 0.2.0 uses the SDK Menu/ribbon and feature-checks the native
command registry for `outline:open`/`backlink:open`; it does not enable plugins.
The original toggle IDs and settings schema remain compatible with 0.1.0.
Visible menus block typewriter; hidden remnants do not. Main-window-only behavior
and physical mobile/IME limits still apply. Fresh native 1.14.5 checks used
synthetic data for both graph palettes/hover, all four menu actions, keyboard
Zen/Exit, real cursor centering, menu guards and active-mode unload. Command
menus explicitly bind the main document rather than a previously active Graph
iframe. The third-party workflow checks above are retained 1.6.0 evidence; their
compatibility layer is byte-unchanged, not newly recertified exhaustively here.

## 1.6.2 / Writing 0.3.0 follow-colours boundary

Graph CSS is part of the Omarchy theme, not a separate graph plugin. Native Graph
Groups stay authoritative; no cluster allocation, data or physics change ships.
The companion adds only a marker-guarded fixed-role override while follow-colours
is OFF. It uses workspace `css-change` and `onExternalSettingsChange` for actual
paint/settings consumers; external refresh never auto-saves. The three runtime
files remain the complete companion runtime. Zen requires it to be enabled.

The host wrapper is source only and requires Admin review/deployment. Only an
explicitly named registered vault is policy-gated; omitted flags retain legacy
behavior. Parent still owns native OFF/ON/OFF, theme-switch/graph checks and final
activation/review. Source/package creation does not establish activation, phone
sync or physical iPhone/IME support. Main-window and older-SDK limitations remain;
the missing native CLI filesystem endpoint is unchanged.

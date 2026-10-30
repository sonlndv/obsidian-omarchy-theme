# Plugin compatibility

The normal theme always includes `src/parts/plugin-compat.css`, independently
of the companion. Contracts were supplied for the following installed versions;
third-party packages/configurations are not shipped. Native plugin interaction
acceptance remains pending parent QA, rather than being inferred from CSS tests.

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

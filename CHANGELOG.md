# Changelog

## Unreleased

### Opt-in Mounty · Flexoki palette

- Add a colour-only "Mounty · Flexoki" variant for dark and light, using
  kepano/flexoki-obsidian values (commit 527685bc) vendored in `src/flexoki/`
  with the upstream MIT notice retained and embedded in the CSS.
- Two toggles, no file edits: a Style Settings `class-toggle` (`mounty-flexoki`,
  with command) and a generated `snippets/mounty-flexoki.css` fallback.
- While enabled it takes precedence over the companion's fixed-palette
  protection and `--live` colours; the default palette is unchanged when off.
- Mounty's role table is shared (`semantic_roles`) and the default bytes before
  the appended layer are identical. New `tests/test_flexoki.py`; CI also checks
  the generated snippet.

### Emphasis, headings, quotes and graph

- Colour Markdown emphasis from the palette in reading view and Live Preview:
  bold and inline code peach, italic lavender, underline mint, strikethrough
  faint grey (new `src/parts/emphasis.css`). Formatting inside headings and
  links keeps the heading or link colour.
- H4 mint; H4–H6 bold (700), with heading emphasis following heading weight.
  H1–H3 colours, fonts and sizes unchanged.
- Blockquotes get a cyan border and faint cyan tint. Note-level H4 and quote
  border derive locally so companion fixed-palette protection cannot pin the
  older colours.
- Graph nodes use the palette roles: cyan notes, peach focus, mint tags,
  lavender attachments, warm grey unresolved.
- `--live` palettes gain matching underline, inline-code, strikethrough and
  quote-tint roles. Omarchy 1.6.2 manifest and installers unchanged; the CSS
  header now names Mounty as a compatible Omarchy distribution.
- New `tests/test_backport.py` freezes the default build and accepted roles;
  graph, hook-policy and Sonwork tests follow the new roles.

## 1.6.2 / Omarchy Writing 0.3.0

- Add Follow Omarchy colours, default OFF, with marker-guarded fixed-palette
  protection for already-live CSS, including heading and graph roles.
- Reconcile native CSS changes and external own-settings refresh without automatic
  preference writes or recursive notifications; preserve unload state.
- Add explicit registered-vault live/install policy, conservative preference and
  symlink checks, and a reviewable host-hook template; no host deployment.
- Preserve names, fonts, palette, graph, native sizing, geometry and writing tools.

## 1.6.1 / Omarchy Writing 0.2.0

- Keep Omarchy / Omarchy Writing names, IDs, original fonts and palette facts.
- Derive restrained cyan/ink H2/H3 roles; keep other headings ink.
- Add distinct supported graph node colours, readable unresolved nodes and warm
  focus/hover, retaining native Groups/data/physics and restrained links.
- Add 1px native File explorer/Outline selection/focus indicators.
- Add an SDK ribbon and writing-tools menu with explicit native Outline/Backlinks
  actions, unavailable-command guards and menu-aware typewriter suppression.
- Derive deterministic companion package name/version from its manifest; retain
  an explicit public-file allowlist. Clarify theme/companion upgrade and rollback.
- Native rendering/plugin review and publication remain separate parent checks.

## 1.6.0

- Promote the accepted Sonwork dark/light palette and embedded Geist/Space Mono
  Latin/Vietnamese fonts into the normal Omarchy theme; retain native preferred
  sizing, readable layout, soft corners and offline font licenses.
- Add scoped Maps, Note Toolbar, Omnisearch, QuickAdd and TaskNotes colour aliases.
- Keep deliberate `--live` palette substitution and the separate Sonwork preview.
  Fail closed on malformed/non-object appearance JSON during theme selection.
- Add opt-in/manual Omarchy Writing 0.1.0: Zen with visible exit, optional
  typewriter scrolling, Markdown width and explicit filename-title preference.
  Normal requires no companion; theme updates never install it.
- Add Python/Node regression checks and least-privilege reproducibility CI.

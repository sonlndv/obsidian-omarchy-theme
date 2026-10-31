# Native formatting probe — parent execution required

`native_formatting_probe.cjs` exports the synchronous, read-only function
`probeFormatting(options)`. It has no dependencies, starts no app/browser/server,
performs no note reads/writes and never inserts a CSS mock or sample DOM. Run it
in the parent's **already-owned main-window synthetic Obsidian fixture**, using
its existing CommonJS loader or evaluating the exported function in that owned
renderer context. This author pass does not execute it against an app.

Required contract:

```js
const { probeFormatting } = require('/absolute/repository/tests/native_formatting_probe.cjs');
const result = probeFormatting({
  app,
  document,
  expectedVaultPath: '/absolute/explicit/synthetic-vault',
  expectedFile: 'Formatting checks.md',
  mode: 'source',             // 'source' (Live Preview) or 'preview' (reading)
  scheme: 'dark',             // 'dark' or 'light'
  layer: 'theme-only',        // or 'protected' with companion OFF palette active
  samples: {
    bold: 'Bold sample',
    italic: 'Italic sample',
    underline: 'Underline sample',
    strike: 'Strike sample',
    inlineCode: 'inline_sample',
    fencedCode: 'const fenced = 1;',
    formattedLink: 'Underlined link',
    heading: 'Heading sample',
    combinedBoldOuter: 'Bold outside italic inside',
    combinedItalicOuter: 'Italic outside bold inside'
  }
});
if (!result.ok) throw new Error(JSON.stringify(result));
```

The sample strings are **exact visible token text**, supplied explicitly by the
parent to match its synthetic fixture, not instructions to inspect/write a real
note. Except fencedCode (contained text), matching is exact after trim. Prepare
or choose all ten examples in that fixture using the parent's existing workflow:
ordinary bold/italic/native `<u>`/strike/inline code, a fenced code line, an
underlined formatted link, a bold span within a heading, and two **distinct**
combined-emphasis samples with bold-outer/italic-inner and italic-outer/bold-inner
source order. The probe does not read Markdown to infer the lost order: the
parent supplies those two separately labelled strings. Keep the compact examples
in the settled CM viewport so native virtualization does not omit them.

The underline check requires an actual native **u element** in the active source
view; checking only `.cm-underline` cannot pass it. The formatted source-link
check requires `.cm-underline` inside an actual native link class/element. The
heading check requires an actual strong token inside a native heading level.
Ordinary samples exclude headings/links. Combined samples require both >=600
weight and italic/oblique style: source expects lilac in both flat-token orders;
reading expects lilac for `strong em` and peach for `em strong`. Fenced-code text
must have nonzero text samples and at least one computed colour other than peach.

Before any DOM/style inspection, the function requires an absolute expected
vault path matching `app.vault.adapter.getBasePath()`, the exact expected file
`Formatting checks.md`, active Markdown view and expected native mode. It then
requires the active main document, connected view, scheme, theme marker and
expected palette layer. Identity/configuration errors throw with a stable error
`code`; it never falls back to another app/vault/file. Missing DOM samples are
**failures**, not skipped checks. This is a formatting probe, not a font-size or
full plugin/typewriter/graph-layout certification.

Return: `{ok, mode, scheme, layer, file, checks}`. Each check reports `name`,
`count > 0`, `pass` and observed/expected computed colours, weights/styles (or
fenced colours). No note contents or actual vault path are returned. The parent
must preserve results for the eight combinations: two modes × two schemes ×
theme-only/protected companion, and run native graph contrast/Groups checks
separately. Parent-owned setup/navigation is outside the probe.

Normal Python discovery checks source/cascade parity and runs `node --check` on
this file plus the Node identity-gate regression. Those tests deliberately fail
on unrelated identities before any DOM access. They **do not** claim native
colour execution. Native execution and screenshot acceptance remain separate
required parent gates after the revised source is frozen.

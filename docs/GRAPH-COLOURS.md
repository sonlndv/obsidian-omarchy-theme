# Graph colours: meaning before decoration

Mounty does not require a rainbow graph. Colour is a small vocabulary for navigating notes, not a different paint for every folder. The full palette is available; it is not a requirement to use every accent together.

## User-chosen categories with Mounty-tool

The optional [Mounty-tool plugin](https://github.com/sonlndv/Mounty-tool) can define meaningful categories and dark/light colours, then manually assign **one** category to an explicitly chosen note using the portable `mounty-graph` property. For example:

```yaml
mounty-graph: restaurant
```

`note` uses cyan by default; `restaurant` can use a colour you choose. Choose one useful axis (for example note kind) and keep each colour's meaning consistent. There is no hard category-count cap: start with a restrained palette and add only distinctions you use. No automatic classification, tags or bulk migration are needed.

The tool previews native global Graph rules before explicit Apply, placing category rules ahead of overlapping older Groups while preserving all other rules/order and forces/zoom. Property values match whole categories, not partial words. Choose/apply the appropriate scheme after a dark/light change. Removing a category does not bulk-rewrite notes. See the tool's current README for exact UI, compatibility checks and removal behavior; the CSS theme does none of these writes.

## Optional manual workflow-role example

Without the tool, you may still use a simple native-Group recipe. This example uses **the note's role in your workflow**, not a mandatory taxonomy. Start with no custom Groups; add a colour only when it answers a useful question.

| Meaning | Rule in the optional example | Dark | Light |
| --- | --- | --- | --- |
| Ordinary thinking/writing notes | No more specific Group matches | cyan `#39d0fc` | cyan `#006cac` |
| Active work requiring attention | Deliberate `tag:#active` Group | peach `#f5a67d` | peach `#96502a` |
| Sources/reference material | Deliberate `tag:#reference` Group | mint `#83d5b4` | mint `#22684e` |

For this small workflow example, keep **three simultaneous note-group colours**, including the default. This is a recommended starting palette, not a limit on user-defined categories. More colours need another real distinction, not another available swatch. A folder name by itself is not a reason for a new colour. Completed work does not remain peach merely because it lives in a Projects folder.

### Rules and precedence

1. Use the same colour for the same meaning throughout the vault. Do not mix topic, folder, importance and status into one unlabelled colour scheme.
2. Native Graph Groups use the **first matching rule**. The example's order is **active → reference → ordinary**: put the active rule before reference so an actively used reference is peach. A deliberately overlapping synthetic note was checked in both orders; reversing the Groups changes its colour as expected.
3. Use real native search queries. These two tags are examples, not claims about your existing vault and not tags created by the theme. If your own system uses other metadata, choose deliberate matching queries instead.
4. Keep a short legend beside the graph or in its guide. Labels, tags/search and note text carry meaning too; colour must not be the only signal.
5. Dark and light use the paired swatches above for the same meanings. Native custom Group colours are user settings, not automatically remapped by the theme when Appearance changes; choose the suitable pair deliberately.
6. Prefer search/filtering to another category colour. Hide irrelevant types before adding more hue.

## Native graph states are separate

Without custom Groups, the theme follows native object/state roles: ordinary notes are cyan, focused/highlighted objects use peach, tags use mint, attachments use lilac, and unresolved links use quieter stone. Tags and attachments need only be shown when useful. Hover/focus is temporary emphasis, not a saved active-work classification. Native Groups can override per-note colour, so a custom Group's meaning must be documented.

Lilac and stone are **not** extra arbitrary topic colours in the three-colour note example. They remain available for their native attachment/unresolved meanings. Do not infer that every lilac object is an idea or that every stone object is an archived note.

## What Mounty never does automatically

The CSS theme never creates taxonomy, classifies notes, writes tags/properties, changes `graph.json`, adds Groups or alters graph physics/zoom. The historical writing-only0.4.1 companion also does none of those writes. Mounty-tool is different: only explicit assign/clear changes the chosen note property, and only confirmed Apply/removal changes its managed native rules. It does not automatically classify or bulk-edit notes, and it preserves unrelated Groups/physics/zoom. The retained theme screenshots show manually prepared synthetic example Groups, not automatic classification.

A smaller palette is deliberate: each additional colour must earn a clear, stable meaning.

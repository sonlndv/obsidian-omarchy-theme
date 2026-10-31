'use strict';
/* Read-only native DOM probe. No SDK dependency, app launch, note reads or writes.
   Run in the parent's already-owned main-window synthetic Obsidian context. */
function probeFormatting({ app, document: doc, expectedVaultPath, expectedFile,
  mode, scheme, layer, samples }) {
  const fail = code => { const error = new Error(code); error.code = code; throw error; };
  // All identity gates precede DOM/style inspection. Never fall back to another vault.
  if (typeof expectedVaultPath !== 'string' || !expectedVaultPath.startsWith('/') ||
      expectedFile !== 'Formatting checks.md' || !['source', 'preview'].includes(mode) ||
      !['dark', 'light'].includes(scheme) || !['theme-only', 'protected'].includes(layer)) fail('INVALID_CONTRACT');
  if (typeof app?.vault?.adapter?.getBasePath !== 'function' ||
      app.vault.adapter.getBasePath().replace(/\/$/, '') !== expectedVaultPath.replace(/\/$/, '')) fail('VAULT_MISMATCH');
  const view = app.workspace?.activeLeaf?.view;
  if (view?.getViewType?.() !== 'markdown' || view.file?.path !== expectedFile || view.getMode?.() !== mode) fail('FILE_OR_MODE_MISMATCH');
  const root = view.containerEl;
  if (!doc || root?.ownerDocument !== doc || !root.isConnected) fail('DOCUMENT_MISMATCH');
  const names = ['bold', 'italic', 'underline', 'strike', 'inlineCode', 'fencedCode',
    'formattedLink', 'heading', 'combinedBoldOuter', 'combinedItalicOuter'];
  if (!samples || names.some(name => typeof samples[name] !== 'string' || !samples[name].trim()) ||
      samples.combinedBoldOuter === samples.combinedItalicOuter) fail('MISSING_DISTINCT_SAMPLES');
  const style = el => doc.defaultView.getComputedStyle(el);
  if (!doc.body.classList.contains('theme-' + scheme) ||
      style(doc.body).getPropertyValue('--ow-theme-id').trim() !== 'omarchy' ||
      doc.body.getAttribute('data-ow-palette') !== (layer === 'protected' ? 'sonwork' : null)) fail('SCHEME_OR_LAYER_MISMATCH');
  const palette = scheme === 'dark'
    ? {peach:'#f5a67d', lilac:'#c4b5fd', mint:'#83d5b4', slate:'#8a939e', cyan:'#39d0fc', ink:'#f0f4f7', heading:'#82defa'}
    : {peach:'#96502a', lilac:'#6c4b99', mint:'#22684e', slate:'#515c68', cyan:'#006cac', ink:'#0b1421', heading:'#044974'};
  const rgb = hex => 'rgb(' + [1,3,5].map(i => parseInt(hex.slice(i,i+2),16)).join(', ') + ')';
  const source = mode === 'source';
  const scope = source ? '.markdown-source-view.mod-cm6 ' : '.markdown-rendered ';
  const link = el => el.closest('a, .cm-link, .cm-hmd-internal-link, .cm-url');
  function headingLevel(el) {
    for (let n = el; n && root.contains(n); n = n.parentElement) {
      const rendered = /^H([1-6])$/.exec(n.tagName || '');
      const cm = /(?:HyperMD-header-|cm-header-)([1-6])(?:\s|$)/.exec(n.className || '');
      if (rendered || cm) return Number((rendered || cm)[1]);
    }
    return 0;
  }
  const checks = [];
  function check(name, selectors, expected, extra = () => true, ordinary = true) {
    const elements = [...root.querySelectorAll(selectors)].filter(el =>
      el.isConnected && el.getClientRects().length && el.textContent.trim() === samples[name] &&
      (!ordinary || (!link(el) && !headingLevel(el))));
    const observations = elements.map(el => {
      const s = style(el);
      const wanted = typeof expected === 'function' ? expected(el) : expected;
      return {color:s.color, expected:rgb(wanted), fontWeight:s.fontWeight, fontStyle:s.fontStyle,
        pass:s.color === rgb(wanted) && extra(s,el)};
    });
    checks.push({name, count:elements.length, pass:elements.length > 0 && observations.every(o => o.pass), observations});
  }
  const cm = selector => scope + selector + ':not(.cm-formatting)';
  const bold = s => Number(s.fontWeight) >= 600;
  const italic = s => ['italic','oblique'].includes(s.fontStyle);
  check('bold', source ? cm('.cm-strong') : scope+'strong, '+scope+'b', palette.peach, bold);
  check('italic', source ? cm('.cm-em') : scope+'em, '+scope+'i', palette.lilac, italic);
  // Actual native editor <u>, not just the assumed .cm-underline inventory.
  check('underline', scope+'u', palette.mint);
  check('strike', source ? cm('.cm-strikethrough') : scope+'s, '+scope+'del', palette.slate);
  check('inlineCode', source ? scope+'.cm-line:not(.HyperMD-codeblock) .cm-inline-code:not(.cm-formatting)' : scope+':not(pre) > code', palette.peach);
  check('formattedLink', source ? scope+'.cm-underline' : scope+'a u', palette.cyan,
    (_s,el) => !!link(el), false);
  check('heading', source ? cm('.cm-strong') : scope+'h1 strong, '+scope+'h2 strong, '+scope+'h3 strong, '+scope+'h4 strong, '+scope+'h5 strong, '+scope+'h6 strong',
    el => [2,3].includes(headingLevel(el)) ? palette.heading : palette.ink,
    (s,el) => headingLevel(el) > 0 && bold(s), false);
  const both = s => bold(s) && italic(s);
  check('combinedBoldOuter', source ? cm('.cm-em.cm-strong') : scope+'strong em', palette.lilac, both);
  check('combinedItalicOuter', source ? cm('.cm-em.cm-strong') : scope+'em strong', source ? palette.lilac : palette.peach, both);
  const fences = [...root.querySelectorAll(source ? scope+'.HyperMD-codeblock' : scope+'pre code')]
    .filter(el => el.textContent.includes(samples.fencedCode) && el.isConnected && el.getClientRects().length);
  const colours = [];
  function visit(node) {
    if (node.nodeType === 3 && node.textContent.trim()) colours.push(style(node.parentElement).color);
    else for (const child of node.childNodes) visit(child);
  }
  fences.forEach(visit);
  checks.push({name:'fencedCode', count:fences.length, pass:fences.length > 0 && colours.length > 0 && colours.some(c => c !== rgb(palette.peach)), colours});
  return {ok:checks.every(c => c.pass), mode, scheme, layer, file:expectedFile, checks};
}
module.exports = { probeFormatting };

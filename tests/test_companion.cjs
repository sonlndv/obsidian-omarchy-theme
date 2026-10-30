'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const Module = require('node:module');
class Element {
  constructor() { this.attrs = new Map(); this.children = []; this.listeners = new Map(); this.classes = new Set(); this.classList = {add: x => this.classes.add(x), remove: x => this.classes.delete(x)}; }
  getAttribute(k) { return this.attrs.has(k) ? this.attrs.get(k) : null; }
  setAttribute(k,v) { this.attrs.set(k,v); }
  removeAttribute(k) { this.attrs.delete(k); }
  appendChild(e) { this.children.push(e); e.parent = this; }
  remove() { this.parent.children = this.parent.children.filter(x => x !== this); }
  addEventListener(e,f) { if (!this.listeners.has(e)) this.listeners.set(e,new Set()); this.listeners.get(e).add(f); }
  removeEventListener(e,f) { this.listeners.get(e).delete(f); }
  fire(e, data = {}) { for (const f of this.listeners.get(e) || []) f(data); }
  contains(e) { return e === this || this.children.includes(e); }
  closest(s) { return s === '.cm-editor' ? this : null; }
}
class Plugin {
  async loadData() { return this.data; }
  async saveData(data) { this.saved = structuredClone(data); this.saves = (this.saves || 0)+1; }
  addCommand(c) { this.commands.push(c); }
  addSettingTab() {}
  addRibbonIcon(icon, label, callback) { this.ribbon = {icon, label, callback}; }
}
class Menu {
  constructor() { this.items=[]; }
  addItem(fn) {
    const item = {};
    for (const key of ['Title','Icon','Checked','Disabled']) item['set'+key] = value => { item[key.toLowerCase()]=value; return item; };
    item.onClick = fn => { item.callback=fn; return item; };
    fn(item); this.items.push(item); return this;
  }
  addSeparator() {}
  onHide(fn) { this.onhide=fn; return this; }
  hide() { this.hidden=true; this.onhide?.(); }
  showAtMouseEvent(event) { this.position=event; }
  showAtPosition(position) { this.position=position; }
}
const original = Module._load;
Module._load = function(id,...args) { return id === 'obsidian' ? {Plugin, PluginSettingTab: class {}, Setting: class {}, MarkdownView: class {}, Menu} : original.call(this,id,...args); };
const Writing = require('../companion/main.js');
Module._load = original;
function setup(data) {
  global.document = new Element(); document.body = new Element(); document.createElement = () => new Element();
  document.querySelector = () => null; document.querySelectorAll = () => [];
  global.window = {innerWidth: 800}; global.getComputedStyle = el => ({visibility: el.visibility || 'visible'});
  let next = 0; const frames = new Map();
  global.requestAnimationFrame = f => { frames.set(++next,f); return next; };
  global.cancelAnimationFrame = id => frames.delete(id);
  const el = new Element(); const input = new Element(); el.appendChild(input); document.activeElement = input;
  const calls = []; let mode = 'source', selected = false, focus = true;
  const editor = {hasFocus: () => focus, somethingSelected: () => selected,
    getCursor: () => ({line: 12,ch: 3}), scrollIntoView: (...args) => calls.push(args)};
  const view = {containerEl: el, editor, getMode: () => mode};
  const refs = new Set();
  const p = new Writing(); p.commands=[]; p.data=data;
  p.app={workspace:{getActiveViewOfType: () => view, on: (event,fn) => { const ref={event,fn}; refs.add(ref); return ref; }, offref: ref => refs.delete(ref)}};
  return {p, calls, el, refs, frames, setMode: v => mode=v, setSelected: v => selected=v, setFocus: v => focus=v,
    flush: () => { for (const [id,f] of [...frames]) {frames.delete(id);f();} }};
}
test('conservative normalization, startup and assignable commands', async () => {
  assert.deepEqual(Writing.normalize({zen:true, width:'bad',typewriter:1,hideInlineTitle:'yes'}),Writing.DEFAULTS);
  const {p} = setup(); await p.onload();
  assert.equal(p.zen,false); assert.equal(p.saves,undefined);
  assert.deepEqual(p.commands.map(c => c.id),['toggle-zen','toggle-typewriter','open-writing-tools']);
  assert.ok(p.commands.every(c => !c.hotkeys)); p.onunload();
});
test('enter/exit/unload restore owned presentation without app/note/settings mutations', async () => {
  const {p,refs,el,frames} = setup({typewriter:true});
  document.body.setAttribute('data-ow-width','prior');
  const untouched = JSON.stringify(p.app); await p.onload(); p.setZen(true);
  assert.equal(p.button.textContent,'Exit Zen'); assert.equal(p.button.getAttribute('aria-label'),'Exit Zen');
  assert.ok(el.classes.has('ow-typewriter')); assert.equal(refs.size,2);
  document.fire('keyup',{key:'a'}); assert.equal(frames.size,1);
  p.button.fire('click'); assert.equal(p.zen,false); assert.equal(frames.size,0);
  assert.equal(el.classes.size,0); assert.equal(refs.size,0); assert.equal(document.body.children.length,0);
  assert.ok([...document.listeners.values()].every(s => s.size===0));
  assert.equal(p.saves,undefined); assert.equal(JSON.stringify(p.app),untouched);
  p.setZen(true); p.onunload(); assert.equal(document.body.getAttribute('data-ow-width'),'prior');
  assert.equal(document.body.getAttribute('data-ow-zen'),null); assert.equal(document.body.getAttribute('data-ow-hide-title'),null);
});
test('typewriter centers real cursor range only for focused unselected source editing in Zen', async () => {
  const {p,calls,flush,setMode,setSelected,setFocus,frames} = setup(); await p.onload();
  p.setZen(true); document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,0);
  await p.change('typewriter',true); assert.equal(p.saves,1);
  document.fire('keyup',{key:'a'}); document.fire('keyup',{key:'ArrowDown'}); assert.equal(frames.size,1); flush();
  assert.deepEqual(calls,[[{from:{line:12,ch:3},to:{line:12,ch:3}},true]]);
  for (const key of ['Escape']) { document.fire('keyup',{key}); flush(); }
  document.fire('compositionstart'); document.fire('keyup',{key:'a'}); flush();
  document.fire('compositionend'); setSelected(true); document.fire('keyup',{key:'a'}); flush(); setSelected(false);
  setMode('preview'); document.fire('keyup',{key:'a'}); flush(); setMode('source');
  setFocus(false); document.fire('keyup',{key:'a'}); flush(); setFocus(true);
  document.querySelector=()=>({}); document.fire('keyup',{key:'a'}); flush(); document.querySelector=()=>null;
  document.fire('wheel'); document.fire('keyup',{key:'a'}); flush();
  assert.equal(calls.length,1);
  p.pausedUntil=0; document.fire('keyup',{key:'a'}); await p.change('typewriter',false);
  assert.equal(frames.size,0); assert.equal(p.padded,null); p.onunload();
});

test('native writing tools are explicit, disabled safely, exit Zen before opening panes, close on unload', async () => {
  const {p} = setup(); const actions=[];
  let available=['outline:open','backlink:open'];
  p.app.commands={listCommands:()=>available.map(id=>({id})),executeCommandById:id=>actions.push([id,p.zen])};
  await p.onload(); assert.deepEqual(actions,[]); assert.equal(p.menu,undefined); assert.equal(p.saves,undefined);
  assert.equal(p.ribbon.icon,'pen-tool');
  p.ribbon.callback({clientX:10,clientY:10}); assert.equal(p.menu.items.length,4);
  await p.menu.items[1].callback(); assert.equal(p.settings.typewriter,true); assert.equal(p.saves,1);
  p.menu.items[0].callback(); assert.equal(p.zen,true);
  p.menu.items[2].callback(); assert.deepEqual(actions,[['outline:open',false]]);
  p.setZen(true); p.menu.items[3].callback(); assert.deepEqual(actions[1],['backlink:open',false]);
  const old=p.menu; available=[];
  p.commands.find(c=>c.id==='open-writing-tools').callback(); assert.equal(old.hidden,true);
  assert.equal(p.menu.items[2].disabled,true); assert.equal(p.menu.items[3].disabled,true);
  p.setZen(true); p.menu.items[2].callback(); assert.equal(p.zen,true); assert.equal(actions.length,2);
  const owned=p.menu; p.onunload(); assert.equal(owned.hidden,true); assert.equal(p.menu,null);
  assert.equal(require('../companion/manifest.json').id,'omarchy-writing');
  assert.equal(require('../companion/manifest.json').version,'0.2.0');
});
test('visible native/owned menus suppress pending typewriter; hidden/disconnected menus do not', async () => {
  const {p,calls,flush} = setup({typewriter:true}); await p.onload(); p.setZen(true);
  const native={isConnected:true,getClientRects:()=>[{}],visibility:'visible'};
  document.querySelectorAll=()=>[native]; document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,0);
  native.getClientRects=()=>[]; document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,1);
  native.getClientRects=()=>[{}]; native.visibility='hidden'; document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,2);
  native.visibility='visible'; native.isConnected=false; document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,3);
  p.openTools(); document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,3);
  p.menu.hide(); document.fire('keyup',{key:'a'}); flush(); assert.equal(calls.length,4); p.onunload();
});

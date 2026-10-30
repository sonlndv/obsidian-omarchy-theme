'use strict';
const { Plugin, PluginSettingTab, Setting, MarkdownView, Menu } = require('obsidian');
const DEFAULTS = Object.freeze({ typewriter: false, width: 'standard', hideInlineTitle: false });
function normalize(data) {
  data = data && typeof data === 'object' ? data : {};
  return { typewriter: data.typewriter === true,
    width: ['narrow', 'standard', 'wide'].includes(data.width) ? data.width : 'standard',
    hideInlineTitle: data.hideInlineTitle === true };
}
class WritingSettings extends PluginSettingTab {
  display() {
    this.containerEl.empty();
    new Setting(this.containerEl).setName('Typewriter during Zen editing')
      .setDesc('Keep the cursor near the center after typing or keyboard movement. Off by default.')
      .addToggle(c => c.setValue(this.plugin.settings.typewriter).onChange(v => this.plugin.change('typewriter', v)));
    new Setting(this.containerEl).setName('Markdown reading width')
      .setDesc('Uses native readable-line length. Does not change other plugin views.')
      .addDropdown(c => c.addOptions({ narrow: 'Narrow', standard: 'Standard', wide: 'Wide' })
        .setValue(this.plugin.settings.width).onChange(v => this.plugin.change('width', v)));
    new Setting(this.containerEl).setName('Hide filename title')
      .setDesc('Hide only Markdown inline filename titles; keep your own H1. Off by default.')
      .addToggle(c => c.setValue(this.plugin.settings.hideInlineTitle).onChange(v => this.plugin.change('hideInlineTitle', v)));
  }
}
class OmarchyWriting extends Plugin {
  async onload() {
    this.settings = normalize(await this.loadData());
    this.zen = false; this.frame = null; this.cleanups = []; this.composing = false;
    this.body = document.body;
    this.previous = new Map(['data-ow-width', 'data-ow-hide-title', 'data-ow-zen'].map(k => [k, this.body.getAttribute(k)]));
    this.applySettings();
    this.addCommand({ id: 'toggle-zen', name: 'Toggle Zen', callback: () => this.setZen(!this.zen) });
    this.addCommand({ id: 'toggle-typewriter', name: 'Toggle typewriter', callback: () => this.change('typewriter', !this.settings.typewriter) });
    this.addCommand({ id: 'open-writing-tools', name: 'Open writing tools', callback: () => this.openTools() });
    this.addRibbonIcon('pen-tool', 'Open writing tools', event => this.openTools(event));
    this.addSettingTab(new WritingSettings(this.app, this));
  }
  availableCommand(id) {
    const commands = this.app.commands;
    return !!(commands && typeof commands.listCommands === 'function' &&
      typeof commands.executeCommandById === 'function' &&
      commands.listCommands().some(command => command.id === id));
  }
  openPane(id) {
    // Recheck at invocation: a core plugin may have been disabled since opening.
    if (!this.availableCommand(id)) return;
    this.setZen(false);
    this.app.commands.executeCommandById(id);
  }
  openTools(event) {
    if (this.menu) this.menu.hide();
    this.cancel();
    const menu = new Menu();
    this.menu = menu;
    menu.onHide(() => { if (this.menu === menu) this.menu = null; });
    menu.addItem(item => item.setTitle(this.zen ? 'Exit Zen' : 'Enter Zen')
      .setIcon('focus').onClick(() => this.setZen(!this.zen)));
    menu.addItem(item => item.setTitle('Typewriter').setChecked(this.settings.typewriter)
      .onClick(() => this.change('typewriter', !this.settings.typewriter)));
    menu.addSeparator();
    for (const [title, id, icon] of [['Open Outline', 'outline:open', 'list'], ['Open Backlinks', 'backlink:open', 'links-coming-in']]) {
      menu.addItem(item => item.setTitle(title).setIcon(icon).setDisabled(!this.availableCommand(id))
        .onClick(() => this.openPane(id)));
    }
    if (event) menu.showAtMouseEvent(event);
    else menu.showAtPosition({ x: Math.max(0, window.innerWidth - 240), y: 64 });
  }
  visibleMenu() {
    // Native menus can leave hidden DOM behind; only visible menus suppress input.
    return !!this.menu || [...document.querySelectorAll('.menu')].some(el =>
      el.isConnected && el.getClientRects().length > 0 &&
      getComputedStyle(el).visibility !== 'hidden');
  }
  async change(key, value) {
    this.settings = normalize({ ...this.settings, [key]: value });
    this.applySettings();
    this.syncEditor();
    await this.saveData(this.settings);
  }
  applySettings() {
    this.body.setAttribute('data-ow-width', this.settings.width);
    this.body.setAttribute('data-ow-hide-title', String(this.settings.hideInlineTitle));
  }
  activeView() { return this.app.workspace.getActiveViewOfType(MarkdownView); }
  cancel() {
    if (this.frame !== null) cancelAnimationFrame(this.frame);
    this.frame = null;
  }
  syncEditor() {
    this.cancel();
    if (this.padded) this.padded.classList.remove('ow-typewriter');
    this.padded = null;
    const view = this.activeView();
    if (this.zen && this.settings.typewriter && view && view.getMode() === 'source') {
      this.padded = view.containerEl;
      this.padded.classList.add('ow-typewriter');
    }
  }
  eligible(view) {
    return this.zen && this.settings.typewriter && !this.composing && !this.visibleMenu() &&
      Date.now() >= this.pausedUntil && view && view === this.activeView() &&
      view.getMode() === 'source' && view.editor.hasFocus() && !view.editor.somethingSelected() &&
      view.containerEl.contains(document.activeElement) &&
      !!document.activeElement.closest('.cm-editor') &&
      !document.querySelector('.modal-container, .suggestion-container');
  }
  schedule() {
    const view = this.activeView();
    if (!this.eligible(view)) return;
    this.cancel();
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      if (!this.eligible(view)) return;
      this.syncEditor();
      const cursor = view.editor.getCursor();
      view.editor.scrollIntoView({ from: cursor, to: cursor }, true);
    });
  }
  listen(target, event, fn, options) {
    target.addEventListener(event, fn, options);
    this.cleanups.push(() => target.removeEventListener(event, fn, options));
  }
  setZen(value) {
    if (this.zen === value) return;
    this.zen = value;
    if (!value) {
      this.cancel();
      for (const cleanup of this.cleanups.splice(0)) cleanup();
      if (this.button) this.button.remove();
      this.button = null;
      this.restore('data-ow-zen');
      this.composing = false;
      this.syncEditor();
      return;
    }
    this.pausedUntil = 0;
    this.body.setAttribute('data-ow-zen', 'true');
    this.button = document.createElement('button');
    this.button.className = 'ow-exit-zen'; this.button.textContent = 'Exit Zen';
    this.button.setAttribute('aria-label', 'Exit Zen');
    this.body.appendChild(this.button);
    this.listen(this.button, 'click', () => this.setZen(false));
    // Never bind Escape: Vim, IME, search, suggestions and modals own it.
    this.listen(document, 'compositionstart', () => { this.composing = true; this.cancel(); });
    this.listen(document, 'compositionend', () => { this.composing = false; });
    const manual = () => { this.pausedUntil = Date.now() + 800; this.cancel(); };
    for (const event of ['wheel', 'touchstart', 'pointerdown']) this.listen(document, event, manual, { passive: true, capture: true });
    this.listen(document, 'keyup', e => {
      if (!e.isComposing && !e.ctrlKey && !e.metaKey && !e.altKey &&
          e.key !== 'Escape' && e.key !== 'Shift' && !e.shiftKey) this.schedule();
    });
    this.listen(document, 'input', e => {
      const view = this.activeView();
      if (view && view.containerEl.contains(e.target) && e.target.closest('.cm-editor')) this.schedule();
    });
    for (const event of ['active-leaf-change', 'layout-change']) {
      const ref = this.app.workspace.on(event, () => this.syncEditor());
      this.cleanups.push(() => this.app.workspace.offref(ref));
    }
    this.syncEditor();
  }
  restore(key) {
    const old = this.previous.get(key);
    if (old === null) this.body.removeAttribute(key); else this.body.setAttribute(key, old);
  }
  onunload() {
    if (this.menu) this.menu.hide();
    this.menu = null;
    this.setZen(false); this.cancel();
    for (const key of this.previous.keys()) this.restore(key);
  }
}
module.exports = OmarchyWriting;
module.exports.normalize = normalize;
module.exports.DEFAULTS = DEFAULTS;

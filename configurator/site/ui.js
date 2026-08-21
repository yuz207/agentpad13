/**
 * ui.js — the control rail and the build sheet, in DOM.
 *
 * House rules, enforced by reading this file: the only strings that reach the
 * page are (a) single-word group labels, (b) option VALUES — a segmented cell,
 * a colour NAME in the dropdown, a checkbox's own word — and (c) build-sheet
 * content. No eyebrows, no subtitles, no helper copy, no icons, no badges.
 * Anything explanatory that a control needs lives in an aria-label or a title
 * attribute, which are for assistive tech and hover, not for the layout.
 *
 * THREE control shapes, and only three:
 *   .seg    pick one of N values   (segmented cells)
 *   .pick   pick one colour        (chip + name, opens a GRID of swatches)
 *   .checks booleans               (a list of identical [ ] checkboxes)
 * Every boolean in the page is a .check row — same box, same size, same
 * spacing — whether it is a Show toggle, a translucency checkbox or the LED.
 */

import { at } from './rules.js';

/**
 * Swatch columns in an open colour panel. Round 4, verbatim: "for the color
 * picker, why not drop down a grid of swatches? Then you can have more colors."
 * ONE number, because both the CSS grid and the arrow-key walk have to agree on
 * it — styles.css `.menu[data-grid]` repeats this many columns, and Up/Down
 * moves by exactly this many cells. Changing it here means changing it there.
 */
const SWATCH_COLS = 8;

const el = (tag, attrs = {}, kids = []) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'text') n.textContent = v;
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of [].concat(kids)) if (kid) n.append(kid);
  return n;
};

/* ------------------------------------------------------- open dropdown */

/* At most one colour list is open at a time, and it closes on Escape or on a
   press anywhere outside it. Module scope, not per-rail, so the listeners are
   registered once no matter how often the rail is rebuilt. */
let closeOpenMenu = null;
const closeMenu = () => { if (closeOpenMenu) { const fn = closeOpenMenu; closeOpenMenu = null; fn(); } };

document.addEventListener('pointerdown', (e) => {
  if (!closeOpenMenu) return;
  const t = e.target;
  if (!(t instanceof Element) || !t.closest('.pick')) closeMenu();
}, true);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });

/* ------------------------------------------------------------------ rail */

export function buildRail(root, data, store) {
  const { catalog, finishes } = data;
  const syncs = [];
  root.replaceChildren();

  /** A labelled group. `when` decides whether it is in the page at all. */
  function group(label, controls, when) {
    const node = el('div', { class: 'group' }, [el('div', { class: 'label', text: label })]);
    for (const c of controls) node.append(c.node);
    root.append(node);
    syncs.push((state, derived) => {
      if (when) node.hidden = !when(state, derived);
      for (const c of controls) c.sync(state, derived);
    });
  }

  /** Segmented control. options: [{value, label}] */
  function segmented(path, options, { label, when } = {}) {
    const track = el('div', { class: 'seg', role: 'radiogroup', 'aria-label': label });
    const buttons = options.map((o) => {
      const b = el('button', { type: 'button', role: 'radio', 'aria-checked': 'false', text: o.label });
      b.addEventListener('click', () => store.set(path, o.value));
      track.append(b);
      return [b, o.value];
    });
    return {
      node: track,
      sync(state, derived) {
        if (when) track.hidden = !when(state, derived);
        const current = at(state, path);
        for (const [b, v] of buttons) b.setAttribute('aria-checked', String(v === current));
      },
    };
  }

  /**
   * A list of identical checkboxes — Show, transparency, the LED. One box, one
   * word, one row each; no chips, no pills, no per-item sizing. Real
   * <input type="checkbox"> so the keyboard and every screen reader already
   * know what it is; the box itself is drawn in CSS.
   *
   * items: [{path, label, when?, suggest?}] — `suggest` names a derived hint
   * that rings the box while the box is still off (rules.json led_on_band_suggest).
   */
  function checks(items, { label, when } = {}) {
    const box = el('div', { class: 'checks', role: 'group', 'aria-label': label });
    const rows = items.map((it) => {
      const input = el('input', { type: 'checkbox' });
      const row = el('label', { class: 'check' }, [input, el('span', { text: it.label })]);
      input.addEventListener('change', () => store.set(it.path, input.checked));
      box.append(row);
      return { row, input, it };
    });
    return {
      node: box,
      sync(state, derived) {
        if (when) box.hidden = !when(state, derived);
        for (const { row, input, it } of rows) {
          if (it.when) row.hidden = !it.when(state, derived);
          input.checked = at(state, it.path) === true;
          const hint = it.suggest && derived.suggest[it.suggest] === true && !input.checked;
          if (hint) row.setAttribute('data-suggest', ''); else row.removeAttribute('data-suggest');
        }
      },
    };
  }

  /**
   * The colour control: the CURRENT colour as a chip plus its name, and a
   * click drops a GRID of swatches. One shared palette, so every colourable
   * part — and the LED lighting — gets this identical control.
   *
   * CLOSED is unchanged from round 3 (chip + name + caret), because that is
   * the part that has to read at a glance in a 320 px rail. OPEN is a grid:
   * a swatch carries its colour and nothing else, its NAME lives in `title`
   * and `aria-label` (hover + assistive tech, never layout), and the grid is
   * what makes a 56-colour palette fit in the same 340 px panel a 31-row list
   * used to overflow.
   *
   * list: [{id, name, hex, css?}] — the finish palette, the soldermask list,
   * or the lighting list whose first entry (Rainbow) carries a `css` gradient
   * instead of a flat hex.
   */
  function picker(path, list, { label, when } = {}) {
    const byId = new Map(list.map((f) => [f.id, f]));
    const wrap = el('div', { class: 'pick', 'data-open': 'false' });
    const chip = el('span', { class: 'chip' });
    const name = el('span', { class: 'pick-name' });
    const btn = el('button', {
      type: 'button', class: 'pick-btn', 'aria-haspopup': 'listbox',
      'aria-expanded': 'false', 'aria-label': label,
    }, [chip, name]);
    const menu = el('div', {
      class: 'menu', role: 'listbox', 'aria-label': label,
      'data-grid': String(SWATCH_COLS), hidden: true,
    });
    wrap.append(btn, menu);

    const rows = list.map((f) => {
      /* The swatch IS the option: no text node, so a 56-colour grid adds
         nothing to the page's rendered copy (site_text_audit.mjs). */
      const row = el('div', {
        class: 'swatch', role: 'option', tabindex: '-1', 'aria-selected': 'false',
        title: f.name, 'aria-label': f.name, 'data-css': f.css ? '' : null,
      });
      row.style.background = f.css || f.hex;
      row.addEventListener('click', () => { store.set(path, f.id); close(); btn.focus(); });
      menu.append(row);
      return [row, f];
    });

    function close() {
      if (menu.hidden) return;
      menu.hidden = true;
      wrap.dataset.open = 'false';
      btn.setAttribute('aria-expanded', 'false');
      if (closeOpenMenu === close) closeOpenMenu = null;
    }

    function open() {
      closeMenu();                                   // one list at a time
      menu.hidden = false;
      wrap.dataset.open = 'true';
      btn.setAttribute('aria-expanded', 'true');
      /* The rail scrolls and clips, so a list opened near its foot drops
         UPWARD instead of pushing the rail's scroll height out. */
      const r = btn.getBoundingClientRect();
      wrap.dataset.drop = window.innerHeight - r.bottom < menu.offsetHeight + 12 ? 'up' : 'down';
      closeOpenMenu = close;
      (menu.querySelector('[aria-selected="true"]') || menu.firstElementChild).focus();
    }

    btn.addEventListener('click', () => (menu.hidden ? open() : close()));
    btn.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (menu.hidden) open(); }
    });
    /* Arrow keys walk the GRID, not a list: Left/Right step one swatch,
       Up/Down step a whole row. Both clamp at the ends rather than wrapping,
       so the first and last colours are reachable and nothing jumps. */
    menu.addEventListener('keydown', (e) => {
      const opts = [...menu.children];
      const i = opts.indexOf(document.activeElement);
      const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: SWATCH_COLS, ArrowUp: -SWATCH_COLS }[e.key];
      if (step !== undefined) {
        e.preventDefault();
        opts[Math.min(opts.length - 1, Math.max(0, (i < 0 ? 0 : i) + step))].focus();
      } else if (e.key === 'Home' || e.key === 'End') {
        e.preventDefault();
        opts[e.key === 'Home' ? 0 : opts.length - 1].focus();
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (i > -1) opts[i].click();
      } else if (e.key === 'Escape' || e.key === 'Tab') {
        close();
        // this Escape was for the list: do not let it reach the build sheet too
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); btn.focus(); }
      }
    });

    return {
      node: wrap,
      sync(state, derived) {
        if (when) wrap.hidden = !when(state, derived);
        if (wrap.hidden) close();
        const current = at(state, path);
        const f = byId.get(current) || list[0];
        chip.style.background = f.css || f.hex;
        name.textContent = f.name;
        for (const [row, r] of rows) row.setAttribute('aria-selected', String(r.id === current));
      },
    };
  }

  const YESNO = [{ value: 'no', label: 'no' }, { value: 'yes', label: 'yes' }];
  const finishList = finishes.finishes;
  const maskList = finishes.masks;

  /* The lighting palette is the SHARED one with Rainbow bolted on the front —
     "whose first option is Rainbow followed by the shared colors". Rainbow is
     not a finish (you cannot print in it), so it lives here rather than in
     finishes.json, and it carries a `css` conic gradient so the swatch and the
     closed chip both show what it is instead of a flat colour. */
  const RAINBOW = {
    id: 'rainbow',
    name: 'Rainbow',
    hex: '#FFFFFF',
    css: 'conic-gradient(from 0.25turn, #FF3B30, #FF9500, #FFD60A, #34C759, #32D0D0, #0A84FF, #5E5CE6, #BF5AF2, #FF375F, #FF3B30)',
  };
  const lightingList = [RAINBOW].concat(finishList);

  /** Colour + its own translucency checkbox: the two independent axes every
   *  colourable part gets, in the same order every time. */
  const colour = (part, label, opts = {}) => [
    picker(`${part}.finish`, finishList, { label: `${label} colour`, when: opts.when }),
    checks([{ path: `${part}.translucent`, label: 'translucent', suggest: opts.suggest }],
      { label: `${label} translucency`, when: opts.when }),
  ];

  /* Option labels are VALUES, derived from catalog data — never hand-typed
     copy. A rung id is "5p8" -> 5.8; a topper id is "knurled_cup" -> knurled;
     a plate variant is "tented_ring" -> tented ring. */
  const rungLabel = (id) => String(id).replace('p', '.');
  const styleLabel = (id) => String(id).split('_')[0];
  /* ...with ONE override, and it is a manufacturing fact rather than a
     rename for taste. Owner ruling, round 4: "call standard something else b/c
     that matters for the manufacturing process (not leaded!)". The `standard`
     variant is the one that OPENS THE MASK over the touch pad, so the pad is
     bare copper under your finger and the board has to be ordered ENIG
     (lead-free gold), never leaded HASL. Naming the value after what it is —
     an exposed pad — is what makes that choice legible. The catalog id stays
     `standard`: it is pipeline data and nothing here may edit it. */
  const VARIANT_LABEL = { standard: 'exposed pad' };
  const variantLabel = (id) => VARIANT_LABEL[id] || String(id).replace(/_/g, ' ');
  const makeLabel = (id) => (id === 'fr4' ? 'FR4' : String(id).replace(/_/g, ' '));
  const wallLabel = (w) => (w.wall_mm != null ? w.wall_mm.toFixed(1) : rungLabel(w.id.replace(/^w/, '')));
  const capWidthLabel = (w) => {
    const f = catalog.keycaps.files.find((x) => x.width === w);
    return f && f.width_mm != null ? f.width_mm.toFixed(1) : w;
  };

  /* LED band: yes/no is the BOARD you order, and nothing else. */
  group('LED band', [segmented('led', YESNO, { label: 'LED band' })]);

  /* Lighting is its OWN section now ("Maybe lighting becomes its own
     section"), and it is offered whatever the LED band toggle says: the
     per-key LEDs under the switches are on every board — only the perimeter
     band ribbon depends on `led`. Both controls are VIEW ONLY: state.lighting
     reaches no rule and no build sheet. */
  group('Lighting', [
    checks([{ path: 'lighting.on', label: 'lit' }], { label: 'Light the LEDs on the render' }),
    picker('lighting.color', lightingList, { label: 'LED colour' }),
  ]);

  group('Board', [picker('board_mask', maskList, { label: 'Board soldermask' })],
    (state, derived) => derived.show.board_mask === true);

  /* Plate: procurement first, because it decides what the rest of the group
     even is. FR4 keeps the touch-face variant and the fab mask list — that is
     manufacturing reality, not taste. Printed gets the same palette, and the
     same transparency checkbox, as every other printed part. */
  const printedPlate = (s, d) => d.show.plate_finish === true;
  group('Plate', [
    segmented('plate.make', [{ value: 'fr4', label: makeLabel('fr4') }, { value: 'printed', label: makeLabel('printed') }],
      { label: 'Plate procurement' }),
    segmented('plate.variant', catalog.plate.variants.map((v) => ({ value: v.id, label: variantLabel(v.id) })),
      { label: 'Plate variant', when: (s, d) => d.show.plate_variant === true }),
    picker('plate.mask', maskList, { label: 'Plate soldermask', when: (s, d) => d.show.plate_mask === true }),
    ...colour('plate', 'Plate', { when: printedPlate }),
  ]);

  group('Band', [
    segmented('band.width', catalog.band.widths.map((w) => ({ value: w.id, label: wallLabel(w) })), { label: 'Band width' }),
    ...colour('band', 'Band', { suggest: 'band_transparent' }),
  ]);

  group('Tray', colour('tray', 'Tray'));

  /* No peg control: the fit is measured with the printed gauge, not chosen
     from a menu, so the manifest ships the gauge and all four rungs. */
  group('Base', [
    segmented('base.variant', [{ value: 'none', label: 'none' }].concat(
      catalog.bases.items.map((b) => ({ value: b.id, label: variantLabel(b.id) }))), { label: 'Base' }),
  ]);

  /* Show: what is on the render. Six of these are view-only; caps is the one
     that also decides what you print (see state.js). Seven identical boxes.
     MODULE then TOPPER, twice over — encoder/knob and joystick/stick — because
     that is the stack: untick the topper and the bare hardware is what is
     left standing. */
  group('Show', [checks([
    { path: 'view.caps', label: 'caps' },
    { path: 'view.switches', label: 'switches' },
    { path: 'view.encoder', label: 'encoder' },
    { path: 'view.knob', label: 'knob' },
    { path: 'view.joystick', label: 'joystick' },
    { path: 'view.stick', label: 'stick' },
    { path: 'view.stabilizer', label: 'stabilizer' },
  ], { label: 'Show on the render' })]);

  group('Caps', [
    segmented('caps.profile', catalog.keycaps.profiles.map((p) => ({ value: p, label: p })),
      { label: 'Keycap profile' }),
    segmented('caps.width', catalog.keycaps.widths.map((w) => ({ value: w, label: capWidthLabel(w) })),
      { label: 'Keycap width' }),
    ...colour('caps', 'Keycap'),
  ], (state, derived) => derived.show.caps_detail === true);

  group('Switches', colour('switches', 'Switch'));

  group('Toppers', [
    segmented('toppers.knob', [{ value: 'none', label: 'none' }].concat(
      catalog.toppers.knobs.map((k) => ({ value: k.id, label: styleLabel(k.id) }))), { label: 'Encoder knob' }),
    segmented('toppers.stick', [{ value: 'none', label: 'none' }].concat(
      catalog.toppers.stick_caps.map((s) => ({ value: s.id, label: styleLabel(s.id) }))), { label: 'Stick cap' }),
    ...colour('toppers', 'Topper'),
  ]);

  return { sync: (state, derived) => syncs.forEach((fn) => fn(state, derived)) };
}

/* ----------------------------------------------------------------- sheet */

function money(price) {
  if (!price) return null;
  const { amount, currency } = price;
  if (amount == null) return null;
  return currency === 'USD' ? `$${amount.toFixed(2)}` : `${amount.toFixed(2)} ${currency || ''}`.trim();
}

function entryNode(e, releaseBase) {
  const li = el('li', { class: e.kind === 'note' ? 'note' : null });
  if (e.count) li.append(el('span', { class: 'n', text: `${e.count} ×` }));
  if (e.kind === 'file') {
    li.append(el('a', { href: releaseBase + e.path, target: '_blank', rel: 'noopener', text: e.text }));
  } else if (e.kind === 'value') {
    li.append(el('span', { class: 'k', text: e.label }), el('span', { text: e.value }));
  } else {
    li.append(el('span', { text: e.text }));
  }
  const p = money(e.price);
  if (p) li.append(el('span', { class: 'price', text: p }));
  return li;
}

export function renderSheet(root, sheet, releaseBase) {
  const grid = el('div', { class: 'sheet-grid' });
  for (const section of sheet.sections) {
    grid.append(el('section', {}, [
      el('h2', { text: section.title }),
      el('ul', {}, section.entries.map((e) => entryNode(e, releaseBase))),
    ]));
  }
  const f = sheet.footer;
  const foot = el('div', { class: 'sheet-foot' }, [
    el('a', { href: releaseBase + f.uf2.path, target: '_blank', rel: 'noopener', text: f.uf2.text }),
    el('span', { class: 'cmd', text: f.flash }),
    ...f.links.map((l) => el('a', { href: releaseBase + l.path, target: '_blank', rel: 'noopener', text: l.text })),
  ]);
  /* One caveat for the whole sheet, and only when there are prices to caveat —
     sheet.js already returns null when costs.json has no `updated` date. */
  const nodes = [grid];
  if (sheet.costs_label) nodes.push(el('div', { class: 'sheet-costs', text: sheet.costs_label }));
  nodes.push(foot);
  root.replaceChildren(...nodes);
}

/* ------------------------------------------------------------ sheet open */

export function wireSheet(sheet, handle) {
  const set = (open) => {
    sheet.dataset.open = String(open);
    handle.setAttribute('aria-expanded', String(open));
  };
  handle.addEventListener('click', () => set(sheet.dataset.open !== 'true'));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') set(false); });
  return { set };
}

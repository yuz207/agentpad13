/**
 * site_sheet.test.mjs — build-sheet assembly from fixed config snapshots,
 * the costs-null behaviour, board-mask visibility, and link integrity.
 */

import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { suite, ok, eq, deep, loadData, REPO } from './site_harness.mjs';
import { buildSheet, sheetPaths } from '../site/sheet.js';
import { derive } from '../site/rules.js';
import { initialState, withPath } from '../site/state.js';

const data = loadData();
const S = suite('site_sheet');
const base = () => initialState(data);
const sec = (sheet, id) => sheet.sections.find((s) => s.id === id);
const ids = (sheet, id) => sec(sheet, id).entries.map((e) => e.id);

/* --- the three sections and the fixed footer ------------------------ */

S.test('sheet has exactly the three spec sections, in order', () => {
  const sheet = buildSheet(base(), data);
  deep(sheet.sections.map((s) => s.id), ['pcbway', 'selfbuy', 'print']);
  deep(sheet.sections.map((s) => s.title), ['PCBWay', 'Self-buy', 'Print']);
});

S.test('fixed config snapshot -> exact PCBWay package', () => {
  /* OWNER RULING, round 4: "default should tented ring, not standard". The
     default order is therefore the RING gerbers on the ordinary lead-free
     HASL — no exposed copper, no ENIG requirement. This snapshot has flipped
     once before; it is pinned by ruling now, so a change here needs a new one. */
  let s = base();
  const sheet = buildSheet(s, data);
  deep(ids(sheet, 'pcbway'), ['fabpack', 'plate_gerbers', 'board_mask', 'plate_mask', 'plate_finish', 'assembly']);
  const e = sec(sheet, 'pcbway').entries;
  eq(e[0].text, 'fabpack_translucent.zip');
  eq(e[1].text, 'plate_v5_ring_gerbers.zip');
  eq(e[2].value, 'Black');
  eq(e[4].value, 'HASL-LF');
  ok(e[5].text.includes('factory-populated'), 'assembly note must state the v5.8 population boundary');
  ok(e[5].text.includes('TP5'), 'assembly note must identify the optional user-soldered contact');
});

S.test('the exposed-pad plate is the ONE that must be ordered lead-free gold', () => {
  /* Owner: "call standard something else b/c that matters for the
     manufacturing process (not leaded!)". The `standard` variant opens the
     mask over TP5, so the pad is bare copper under a finger: ENIG, and the
     sheet has to say lead-free in as many words. Every other path is HASL-LF,
     which already carries it. One value each, no prose. */
  let s = withPath(base(), 'led', 'no');
  s = withPath(s, 'plate.variant', 'standard');
  const sheet = buildSheet(s, data);
  eq(sec(sheet, 'pcbway').entries[0].text, 'fabpack_opaque.zip');
  eq(sec(sheet, 'pcbway').entries[1].text, 'plate_v5_gerbers.zip');
  eq(sec(sheet, 'pcbway').entries[4].value, 'ENIG (lead-free)');
  for (const [variant, finish] of [['tented_ring', 'HASL-LF'], ['blank', 'HASL-LF']]) {
    const f = sec(buildSheet(withPath(base(), 'plate.variant', variant), data), 'pcbway')
      .entries.find((x) => x.id === 'plate_finish');
    eq(f.value, finish, `${variant}: no exposed copper, so no ENIG`);
  }
  for (const v of data.catalog.plate.variants) {
    const f = sec(buildSheet(withPath(base(), 'plate.variant', v.id), data), 'pcbway')
      .entries.find((x) => x.id === 'plate_finish');
    ok(/lead-free|LF/.test(f.value), `${v.id}: the finish line must be unambiguous about lead`);
    ok(!/\s(and|the|order|use)\s/i.test(f.value), `${v.id}: a finish is a VALUE, not prose`);
  }
});

S.test('blank plate variant links the blank gerbers', () => {
  const sheet = buildSheet(withPath(base(), 'plate.variant', 'blank'), data);
  eq(sec(sheet, 'pcbway').entries[1].text, 'plate_v5_blank_gerbers.zip');
});

/* --- the plate procurement fork (spec §2 "Plate") -------------------- */

S.test('printed plate -> the plate leaves the fab order entirely', () => {
  const sheet = buildSheet(withPath(base(), 'plate.make', 'printed'), data);
  deep(ids(sheet, 'pcbway'), ['fabpack', 'board_mask', 'assembly']);
  ok(!ids(sheet, 'pcbway').includes('plate_gerbers'), 'no gerbers on the printed path');
  ok(!ids(sheet, 'pcbway').includes('plate_mask'), 'no fab mask on the printed path');
  ok(!ids(sheet, 'pcbway').includes('plate_finish'), 'no fab finish on the printed path');
});

S.test('printed plate -> STL moves into the print manifest, with the touch note', () => {
  const sheet = buildSheet(withPath(base(), 'plate.make', 'printed'), data);
  const print = sec(sheet, 'print').entries;
  eq(print.find((e) => e.id === 'plate_stl').text, 'agentpad13_v2_plate.stl');
  ok(print.some((e) => e.id === 'plate_printed_touch' && e.kind === 'note'), 'the touch note is required');
});

S.test('FR4 plate -> no plate STL in the print manifest', () => {
  const list = ids(buildSheet(withPath(base(), 'plate.make', 'fr4'), data), 'print');
  ok(!list.includes('plate_stl'), 'the fab plate is not printed');
});

S.test('footer is the single UF2, the flash line and the two docs', () => {
  const sheet = buildSheet(base(), data);
  eq(sheet.footer.uf2.text, 'agentpad13.uf2');
  eq(sheet.footer.flash, 'dd if=firmware/prebuilt/agentpad13.uf2 of=/Volumes/RPI-RP2/fw.uf2 bs=1m');
  deep(sheet.footer.links.map((l) => l.text), ['BRING-UP.md', 'POLARITY-NOTE.md']);
});

/* --- board mask visibility ------------------------------------------ */

S.test('solid case -> sheet states mask: black even if state says green', () => {
  let s = withPath(base(), 'board_mask', 'green');
  s = withPath(s, 'band.translucent', false);
  s = withPath(s, 'tray.translucent', false);
  const sheet = buildSheet(s, data);
  eq(sheet.board_mask, 'black');
  eq(sec(sheet, 'pcbway').entries[2].value, 'Black');
});

S.test('translucent band -> the chosen board mask reaches the sheet', () => {
  let s = withPath(base(), 'board_mask', 'green');
  s = withPath(s, 'band.translucent', true);
  s = withPath(s, 'tray.translucent', false);
  const sheet = buildSheet(s, data);
  eq(sheet.board_mask, 'green');
  eq(sec(sheet, 'pcbway').entries[2].value, 'Green');
});

S.test('a translucent TRAY reveals the mask just as the band does', () => {
  let s = withPath(base(), 'board_mask', 'blue');
  s = withPath(s, 'band.translucent', false);
  s = withPath(s, 'tray.translucent', true);
  eq(sec(buildSheet(s, data), 'pcbway').entries[2].value, 'Blue');
});

S.test('the sheet carries the case colour AND its translucency, as two axes', () => {
  let s = withPath(base(), 'band.finish', 'neon_pink');
  s = withPath(s, 'band.translucent', true);
  s = withPath(s, 'tray.finish', 'olive');
  s = withPath(s, 'tray.translucent', false);
  const sheet = buildSheet(s, data);
  deep(sheet.finish_names, { band: 'Neon pink', tray: 'Olive' });
  deep(sheet.translucent, { band: true, tray: false });
});

/* --- print manifest -------------------------------------------------- */

S.test('default print manifest: band + tray + the band-pocket note only', () => {
  const sheet = buildSheet(base(), data);
  deep(ids(sheet, 'print'), ['band', 'tray', 'knob', 'stick_cap', 'band_pocket']);
  eq(sec(sheet, 'print').entries[0].text, 'agentpad13_v2_band_1.6mm_w5.4.stl');
});

S.test('band width picks the matching STL', () => {
  for (const [id, file] of [['w3.0', 'agentpad13_v2_band_1.6mm_w3.0.stl'],
                            ['w7.4', 'agentpad13_v2_band_1.6mm_w7.4.stl']]) {
    const sheet = buildSheet(withPath(base(), 'band.width', id), data);
    eq(sec(sheet, 'print').entries[0].text, file);
  }
});

S.test('a base ships the gauge and ALL FOUR rungs — the fit is measured, not chosen', () => {
  for (const v of ['riser', 'wedge', 'pedestal']) {
    const sheet = buildSheet(withPath(base(), 'base.variant', v), data);
    const list = ids(sheet, 'print');
    ok(list.indexOf('base_gauge') > -1, 'gauge missing');
    for (const rung of data.catalog.bases.peg_rungs) {
      ok(list.includes(`base_peg_${rung}`), `${v} is missing the ${rung} peg`);
      ok(list.indexOf('base_gauge') < list.indexOf(`base_peg_${rung}`), `gauge must precede ${rung} for ${v}`);
    }
    const files = sec(sheet, 'print').entries.filter((e) => e.id.startsWith('base_peg_')).map((e) => e.text);
    deep(files, data.catalog.bases.peg_rungs.map((r) => `base_${v}_peg_${r}.stl`));
  }
});

S.test('the gauge note tells you what to do with the four rungs', () => {
  const notes = sec(buildSheet(withPath(base(), 'base.variant', 'wedge'), data), 'print')
    .entries.filter((e) => e.kind === 'note');
  eq(notes.find((n) => n.id === 'base_gauge_note').text, 'Print the gauge, keep the rung that holds.');
});

S.test('no base -> no gauge, no pegs, no gauge note', () => {
  const list = ids(buildSheet(base(), data), 'print');
  ok(!list.some((i) => i.startsWith('base_')), `unexpected base entries: ${list}`);
});

S.test('keycaps off -> no cap files; on -> the baked-in counts, never chosen', () => {
  ok(!ids(buildSheet(base(), data), 'print').some((i) => i.startsWith('cap_')), 'no caps when off');
  let s = withPath(base(), 'view.caps', true);
  s = withPath(s, 'caps.profile', 'plateau');
  s = withPath(s, 'caps.width', 'std');
  const entries = sec(buildSheet(s, data), 'print').entries.filter((e) => e.id.startsWith('cap_'));
  deep(entries.map((e) => [e.id, e.count, e.text]), [
    ['cap_1u', 12, 'cap_plateau_1u_boxfit.stl'],
    ['cap_2u_stab', 1, 'cap_plateau_2u_stab_boxfit.stl'],
  ]);
});

S.test('17.5 keycap width picks the 17p5 files', () => {
  let s = withPath(base(), 'view.caps', true);
  s = withPath(s, 'caps.width', '17p5');
  const entries = sec(buildSheet(s, data), 'print').entries.filter((e) => e.id.startsWith('cap_'));
  deep(entries.map((e) => e.text), ['cap_dish_1u_17p5_boxfit.stl', 'cap_dish_2u_stab_17p5_boxfit.stl']);
});

S.test('toppers are data-driven: any catalog style resolves to its STL', () => {
  for (const k of data.catalog.toppers.knobs) {
    const sheet = buildSheet(withPath(base(), 'toppers.knob', k.id), data);
    const want = (k.bores && k.bores[data.catalog.toppers.default_knob_bore]) || k.stl;
    eq(sec(sheet, 'print').entries.find((e) => e.id === 'knob').text, want.split('/').pop());
  }
  for (const c of data.catalog.toppers.stick_caps) {
    const sheet = buildSheet(withPath(base(), 'toppers.stick', c.id), data);
    const want = (c.socks && c.socks[data.catalog.toppers.default_stick_sock]) || c.stl;
    eq(sec(sheet, 'print').entries.find((e) => e.id === 'stick_cap').text, want.split('/').pop());
    const files = c.print_files || [{ id: 'stick_cap', stl: want }];
    for (const file of files) {
      eq(sec(sheet, 'print').entries.find((e) => e.id === file.id).text, file.stl.split('/').pop());
    }
    if (!files.some((f) => f.id === 'stick_restrictor')) {
      ok(!sec(sheet, 'print').entries.find((e) => e.id === 'stick_restrictor'),
        `${c.id} must not add a restrictor`);
    }
  }
});

S.test('toppers set to none drop out of the print manifest', () => {
  let s = withPath(base(), 'toppers.knob', 'none');
  s = withPath(s, 'toppers.stick', 'none');
  const list = ids(buildSheet(s, data), 'print');
  ok(!list.includes('knob') && !list.includes('stick_cap') && !list.includes('stick_restrictor'),
    'no topper files expected');
});

S.test('the notes land in the print section, one line each', () => {
  let s = withPath(base(), 'base.variant', 'pedestal');
  const notes = sec(buildSheet(s, data), 'print').entries.filter((e) => e.kind === 'note');
  deep(notes.map((n) => n.id), ['base_gauge_note', 'band_pocket', 'pedestal_solid']);
  const riser = sec(buildSheet(withPath(base(), 'base.variant', 'riser'), data), 'print')
    .entries.filter((e) => e.kind === 'note');
  deep(riser.map((n) => n.id), ['base_gauge_note', 'band_pocket', 'riser_material']);
  const none = sec(buildSheet(base(), data), 'print').entries.filter((e) => e.kind === 'note');
  deep(none.map((n) => n.id), ['band_pocket'], 'no base, no gauge note');
});

/* --- self-buy --------------------------------------------------------- */

S.test('self-buy carries only the spec §3.2 lines', () => {
  /* The four trailing lines are the rest of what you actually have to buy —
     the screws and inserts that hold the stack together (CASE-V2-NOTES §4),
     the touch pillar (§5) and the optional gasket stock (gasket/README.md).
     Each is sourced in its rule's `_` comment in rules.json. */
  let s = withPath(base(), 'view.caps', true);
  deep(ids(buildSheet(s, data), 'selfbuy'),
    ['switches', 'stab', 'screws', 'inserts', 'touch_contact', 'gasket_sheet']);
});

/* --- prices ----------------------------------------------------------- */

S.test('costs.updated == null -> every entry renders no price, and NO label', () => {
  let s = withPath(base(), 'view.caps', true);
  s = withPath(s, 'base.variant', 'wedge');
  const sheet = buildSheet(s, data);
  for (const section of sheet.sections) {
    for (const e of section.entries) eq(e.price, null, `${section.id}/${e.id} must have no price`);
  }
  eq(sheet.costs_label, null, 'nothing price-wise renders, the caveat included');
});

S.test('a dated costs file puts prices on the ids it names, and only those', () => {
  const costs = { updated: '2026-09-01', currency: 'USD', lines: { fabpack: { amount: 41.5, currency: 'USD' } } };
  const sheet = buildSheet(base(), { ...data, costs });
  const pcb = sec(sheet, 'pcbway').entries;
  deep(pcb.find((e) => e.id === 'fabpack').price, { amount: 41.5, currency: 'USD' });
  eq(pcb.find((e) => e.id === 'plate_gerbers').price, null);
});

S.test('a dated costs file also puts ONE estimates caveat on the sheet', () => {
  /* Owner ruling on costs, verbatim: "We should indicate they're all estimates
     and prices may change." One label for the whole sheet — not one per line,
     and not a per-entry field that the DOM would have to de-duplicate. */
  const costs = { updated: '2026-09-01', currency: 'USD', lines: {} };
  const sheet = buildSheet(base(), { ...data, costs });
  eq(sheet.costs_label, 'Estimates — prices change');
  for (const section of sheet.sections) {
    for (const e of section.entries) ok(!('costs_label' in e), `${e.id} must not carry its own caveat`);
  }
});

/* --- link integrity (spec §6) ----------------------------------------- */

S.test('every path the sheet emits exists in the release bundle', () => {
  const seen = new Set();
  const states = [];
  for (const variant of ['none', 'riser', 'wedge', 'pedestal']) {
    states.push(withPath(base(), 'base.variant', variant));   // all four rungs ship with each
  }
  for (const pv of data.catalog.plate.variants) states.push(withPath(base(), 'plate.variant', pv.id));
  for (const make of ['fr4', 'printed']) states.push(withPath(base(), 'plate.make', make));
  for (const w of data.catalog.band.widths) states.push(withPath(base(), 'band.width', w.id));
  for (const profile of data.catalog.keycaps.profiles) {
    for (const width of data.catalog.keycaps.widths) {
      let s = withPath(base(), 'view.caps', true);
      s = withPath(s, 'caps.profile', profile);
      states.push(withPath(s, 'caps.width', width));
    }
  }
  for (const k of data.catalog.toppers.knobs) states.push(withPath(base(), 'toppers.knob', k.id));
  for (const c of data.catalog.toppers.stick_caps) states.push(withPath(base(), 'toppers.stick', c.id));
  for (const led of ['yes', 'no']) states.push(withPath(base(), 'led', led));

  for (const s of states) for (const p of sheetPaths(buildSheet(s, data))) seen.add(p);
  ok(seen.size > 30, `expected a broad path sweep, got ${seen.size}`);
  for (const p of seen) ok(existsSync(join(REPO, p)), `emitted path does not exist: ${p}`);
});

S.test('derive() and buildSheet() agree when derived is passed explicitly', () => {
  const s = base();
  deep(buildSheet(s, data), buildSheet(s, data, derive(s, data)));
});

S.run();

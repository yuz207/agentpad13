/**
 * site_rules.test.mjs — every rule in rules.json as given-config -> expected
 * output, plus the engine's own contracts (purity, determinism, bad input).
 */

import { suite, ok, eq, deep, throws, loadData, freeze } from './site_harness.mjs';
import { derive, evaluate, factsFor, applyOrder } from '../site/rules.js';
import { initialState, withPath } from '../site/state.js';

const data = loadData();
const S = suite('site_rules');
const base = () => initialState(data);
const noteIds = (d) => d.notes.map((n) => n.id);
const lineIds = (d) => d.lines.map((l) => l.id);

/* --- LED master toggle <-> fabpack + band suggestion ---------------- */

S.test('LED band on -> translucent fabpack', () => {
  const d = derive(withPath(base(), 'led', 'yes'), data);
  eq(d.set.fabpack, 'translucent');
  ok(d.fired.includes('led_on_fabpack'), 'led_on_fabpack should fire');
});

S.test('LED band on + a solid band -> the translucency checkbox is hinted', () => {
  let s = withPath(base(), 'led', 'yes');
  s = withPath(s, 'band.translucent', false);
  const d = derive(s, data);
  eq(d.suggest.band_translucent, true);
  ok(d.fired.includes('led_on_band_suggest'), 'led_on_band_suggest should fire');
});

S.test('the hint is silent once the band IS translucent — including by default', () => {
  const d = derive(withPath(base(), 'band.translucent', true), data);
  eq(d.suggest.band_translucent, undefined, 'nothing to suggest: it is already on');
  eq(derive(base(), data).suggest.band_translucent, undefined, 'the default build ships it on');
});

S.test('LED band off -> opaque fabpack, no band hint even with a solid band', () => {
  let s = withPath(base(), 'led', 'no');
  s = withPath(s, 'band.translucent', false);
  const d = derive(s, data);
  eq(d.set.fabpack, 'opaque');
  eq(d.suggest.band_translucent, undefined);
  ok(!d.fired.includes('led_on_fabpack'), 'led_on_fabpack must not fire');
});

/* --- translucency checkbox -> board mask selector + board visible --- */

S.test('solid band + solid tray -> board hidden, mask forced black', () => {
  let s = base();
  s = withPath(s, 'band.translucent', false);
  s = withPath(s, 'tray.translucent', false);
  s = withPath(s, 'board_mask', 'green');           // user picked green earlier
  const d = derive(s, data);
  eq(d.facts.translucent_case, false);
  eq(d.set.board_visible, false);
  eq(d.show.board_mask, false);
  eq(d.set.board_mask, 'black', 'hidden selector must state black');
  ok(d.fired.includes('solid_case_board_hidden'), 'solid_case_board_hidden should fire');
});

S.test('the case colour ALONE never reveals the board mask selector', () => {
  /* Colour and translucency are independent axes now: no finish id, however
     pale, may stand in for the checkbox. */
  let s = withPath(base(), 'band.translucent', false);
  s = withPath(s, 'tray.translucent', false);
  for (const id of ['white', 'silver', 'frost', 'crystal', 'black']) {
    const d = derive(withPath(s, 'band.finish', id), data);
    eq(d.show.board_mask, false, `band colour "${id}" must not reveal the board mask`);
  }
});

S.test('translucent band -> selector shown, board visible, mask = choice', () => {
  let s = withPath(base(), 'band.translucent', true);
  s = withPath(s, 'tray.translucent', false);
  s = withPath(s, 'board_mask', 'green');
  const d = derive(s, data);
  eq(d.set.board_visible, true);
  eq(d.show.board_mask, true);
  eq(d.set.board_mask, 'green');
  ok(d.fired.includes('translucent_case_board_visible'), 'translucent_case_board_visible should fire');
});

S.test('translucent tray -> selector shown too', () => {
  let s = withPath(base(), 'band.translucent', false);
  s = withPath(s, 'tray.translucent', true);
  const d = derive(s, data);
  eq(d.set.board_visible, true);
  eq(d.show.board_mask, true);
});

S.test('translucency on a NON-case part reaches no fact and no rule', () => {
  /* Only the band and the tray decide whether the board is on show. The
     plate, keycaps, switches and toppers each get the same checkbox, and it
     is render-only. */
  let solid = withPath(base(), 'band.translucent', false);
  solid = withPath(solid, 'tray.translucent', false);
  const ref = derive(solid, data);
  for (const part of ['plate', 'caps', 'switches', 'toppers']) {
    for (const v of [true, false]) {
      const d = derive(withPath(solid, `${part}.translucent`, v), data);
      deep(d, ref, `${part}.translucent = ${v} must not change a single derived value`);
    }
  }
});

/* --- the plate procurement fork (spec §2 "Plate") -------------------- */

S.test('FR4 plate -> the touch-face variant and the fab mask are the controls', () => {
  const d = derive(withPath(base(), 'plate.make', 'fr4'), data);
  eq(d.facts.plate_make, 'fr4');
  eq(d.set.plate_procurement, 'fr4');
  eq(d.show.plate_variant, true);
  eq(d.show.plate_mask, true);
  eq(d.show.plate_finish, false, 'no filament colour on a fab-ordered plate');
  ok(!noteIds(d).includes('plate_printed_touch'), 'the touch note is printed-only');
});

S.test('printed plate -> palette colour, no variant, no mask, touch note', () => {
  const d = derive(withPath(base(), 'plate.make', 'printed'), data);
  eq(d.set.plate_procurement, 'printed');
  eq(d.show.plate_variant, false);
  eq(d.show.plate_mask, false);
  eq(d.show.plate_finish, true);
  ok(noteIds(d).includes('plate_printed_touch'), 'printed plate must state the touch behaviour');
  eq(d.notes.find((n) => n.id === 'plate_printed_touch').text,
    'Printed plate has no copper — touch behaves like the blank variant.');
});

/* --- bases: no tolerance control, gauge-first flow ------------------- */

S.test('the peg rung is NOT a control in any base state', () => {
  for (const v of ['none', 'riser', 'wedge', 'pedestal']) {
    const d = derive(withPath(base(), 'base.variant', v), data);
    eq(d.show.base_peg, undefined, `base=${v} must not surface a peg-fit control`);
  }
  ok(!JSON.stringify(data.rules).includes('base_peg"'), 'no rule may show a peg control');
});

S.test('base none -> no gauge note, no ordering constraint', () => {
  const d = derive(withPath(base(), 'base.variant', 'none'), data);
  eq(d.order.length, 0);
  ok(!noteIds(d).includes('base_gauge_note'), 'no gauge note without a base');
});

S.test('base riser -> gauge-first note + gauge-before-pegs + riser note', () => {
  const d = derive(withPath(base(), 'base.variant', 'riser'), data);
  deep(d.order, [{ section: 'print', before: 'base_gauge', after: 'base_peg_5p6', rule: 'base_gauge_flow' }]);
  eq(d.notes.find((n) => n.id === 'base_gauge_note').text, 'Print the gauge, keep the rung that holds.');
  ok(noteIds(d).includes('riser_material'), 'riser note expected');
  ok(!noteIds(d).includes('pedestal_solid'), 'no pedestal note on a riser');
});

S.test('base pedestal -> solid-infill note, no riser note', () => {
  const d = derive(withPath(base(), 'base.variant', 'pedestal'), data);
  ok(noteIds(d).includes('pedestal_solid'), 'pedestal note expected');
  ok(!noteIds(d).includes('riser_material'), 'no riser note on a pedestal');
  eq(d.notes.find((n) => n.id === 'pedestal_solid').text, 'Pedestal prints 100% solid.');
});

S.test('base wedge -> gauge note only, neither base-material note', () => {
  const d = derive(withPath(base(), 'base.variant', 'wedge'), data);
  deep(noteIds(d).sort(), ['band_pocket', 'base_gauge_note']);
});

S.test('applyOrder moves gauge in front of the pegs and is otherwise stable', () => {
  const entries = [{ id: 'band' }, { id: 'tray' }, { id: 'base_peg_5p6' }, { id: 'base_gauge' }, { id: 'knob' }];
  const out = applyOrder(entries, [{ section: 'print', before: 'base_gauge', after: 'base_peg_5p6' }]);
  deep(out.map((e) => e.id), ['band', 'tray', 'base_gauge', 'base_peg_5p6', 'knob']);
});

/* --- the allowed prose notes ---------------------------------------- */

S.test('band-pocket note is present in every base state', () => {
  for (const v of ['none', 'riser', 'wedge', 'pedestal']) {
    const d = derive(withPath(base(), 'base.variant', v), data);
    ok(noteIds(d).includes('band_pocket'), `band_pocket missing for base=${v}`);
  }
});

S.test('every note text in the rule set changes an OUTCOME, and there are five', () => {
  const texts = new Set();
  for (const r of data.rules.rules) for (const n of (r.then.notes || [])) texts.add(n.text);
  deep([...texts].sort(), [
    'Band pocket is deliberately tight — light sand if needed.',
    'Pedestal prints 100% solid.',
    'Print the gauge, keep the rung that holds.',
    'Printed plate has no copper — touch behaves like the blank variant.',
    'Riser in TPU = grip base, rigid = stand.',
  ]);
});

/* --- keycaps -> stabilizer line, and the rest of the self-buy list --- */

S.test('keycaps off -> no stabilizer line', () => {
  const d = derive(withPath(base(), 'view.caps', false), data);
  ok(!lineIds(d).includes('stab'), 'stab line must not appear');
  eq(d.show.caps_detail, undefined);
});

S.test('keycaps on -> stabilizer line + caps detail shown', () => {
  const d = derive(withPath(base(), 'view.caps', true), data);
  ok(lineIds(d).includes('stab'), 'stab line expected');
  eq(d.show.caps_detail, true);
  eq(d.lines.find((l) => l.id === 'stab').text, '1 × 2u plate-mount stabilizer');
});

S.test('the Show toggle for caps IS the caps_on fact — one toggle, both meanings', () => {
  eq(derive(withPath(base(), 'view.caps', true), data).facts.caps_on, true);
  eq(derive(withPath(base(), 'view.caps', false), data).facts.caps_on, false);
});

S.test('the other six view toggles reach NO fact and NO rule', () => {
  const ref = derive(base(), data);
  for (const k of ['switches', 'encoder', 'knob', 'joystick', 'stick', 'stabilizer']) {
    for (const v of [true, false]) {
      const d = derive(withPath(base(), `view.${k}`, v), data);
      deep(d, ref, `view.${k} = ${v} must not change a single derived value`);
    }
  }
});

S.test('the encoder and joystick modules are RENDER, never a config axis', () => {
  /* Round 4 added them because "the configurator still doesn't show the
     encoder or joystick itself, just the toppers" — a rendering complaint. You
     always buy both parts; nothing about showing them changes an order. */
  const src = JSON.stringify(data.rules);
  for (const k of ['view.encoder', 'view.joystick']) {
    ok(!src.includes(k), `no rule may name ${k}`);
  }
  const f = factsFor(base());
  ok(!('encoder_shown' in f) && !('joystick_shown' in f), 'neither may become a fact');
});

S.test('the whole Lighting section is view-only: no fact, no rule, no sheet', () => {
  /* state.led (yes/no) picks the fabpack. state.lighting only lights it — and
     round 4 split it out precisely BECAUSE it is not an order decision. */
  const ref = derive(base(), data);
  for (const v of [true, false]) {
    deep(derive(withPath(base(), 'lighting.on', v), data), ref, `lighting.on = ${v} changed a derived value`);
  }
  for (const c of ['rainbow', 'red', 'neon_pink', 'white']) {
    deep(derive(withPath(base(), 'lighting.color', c), data), ref, `lighting.color = ${c} changed a derived value`);
  }
  // the RULES, not the file: `_not_facts` names lighting precisely to forbid it
  ok(!JSON.stringify(data.rules.rules).includes('lighting'), 'no rule may name lighting');
  ok(JSON.stringify(data.rules._not_facts).includes('lighting'), 'and the file must say why');
  ok(!Object.keys(ref.facts).some((k) => /light|lit|rainbow/.test(k)), 'lighting must not be a fact');
});

S.test('lit is offered on every board: only the BAND half follows led yes/no', () => {
  /* Round 4, verbatim: "lit means the board LEDs under the keys too!" — those
     thirteen are on every board, so nothing about the Lighting section may
     depend on the band you ordered. The band ribbon is a viewer decision. */
  for (const led of ['yes', 'no']) {
    const d = derive(withPath(withPath(base(), 'led', led), 'lighting.on', true), data);
    eq(d.show.lighting, undefined, `led=${led}: no rule may gate the Lighting section`);
    eq(d.set.fabpack, led === 'yes' ? 'translucent' : 'opaque', 'the fabpack still follows the board');
  }
});

S.test('the switch line is unconditional and factory-populated encoder is not self-buy', () => {
  const d = derive(base(), data);
  deep(lineIds(d), ['switches', 'screws', 'inserts', 'touch_contact', 'gasket_sheet']);
  ok(!lineIds(d).includes('encoder'), 'RE1 is in the factory CPL/BOM, not the self-buy list');
});

S.test('the fastener/contact/gasket lines carry the spec their source states', () => {
  /* Each one is sourced in its rule's `_` comment; the numbers here are the
     ones a buyer has to get right, so they are pinned:
       screws + inserts — CASE-V2-NOTES.md §4 "4× M3×8 ISO 7380 button-head;
                          CASE-V2-NOTES.md §33 Voron-style M3×4×5 inserts"
       touch contact    — V5-NOTES.md v5.8 release boundary, optional/user-soldered
       gasket sheet     — gasket/README.md "0.5 mm PORON", adhesive-backed,
                          smallest sheet sold, and OPTIONAL. */
  const t = (id) => derive(base(), data).lines.find((l) => l.id === id).text;
  eq(t('screws'), '4 × M3×8 ISO 7380 button-head screws');
  eq(t('inserts'), '4 × standard Voron-style M3×4×5 heat-set inserts — 4 mm long, nominal 5 mm OD');
  ok(/optional/i.test(t('touch_contact')) && /user-solder/i.test(t('touch_contact')), 'touch contact must state both boundaries');
  ok(/TP5/.test(t('touch_contact')), 'the contact line must name the solder landing');
  ok(/0\.5 mm/.test(t('gasket_sheet')), 'the gasket line must pin 0.5 mm, not 1–2 mm');
  ok(/PORON/.test(t('gasket_sheet')) && /adhesive/.test(t('gasket_sheet')), 'material + backing');
  ok(/optional/i.test(t('gasket_sheet')), 'the gasket kit is optional and must say so');
});

S.test('TP5 contact appears only for an electrode-equipped FR4 plate', () => {
  const idsFor = (s) => lineIds(derive(s, data));
  ok(idsFor(base()).includes('touch_contact'), 'default tented-ring FR4 plate has an electrode');
  ok(idsFor(withPath(base(), 'plate.variant', 'standard')).includes('touch_contact'), 'exposed-pad FR4 plate has an electrode');
  ok(!idsFor(withPath(base(), 'plate.variant', 'blank')).includes('touch_contact'), 'blank FR4 plate has no electrode');
  ok(!idsFor(withPath(base(), 'plate.make', 'printed')).includes('touch_contact'), 'printed plate has no electrode');
});

S.test('no printed knob -> off-the-shelf knob line appears', () => {
  const withKnob = derive(withPath(base(), 'toppers.knob', 'knurled_cup'), data);
  ok(!lineIds(withKnob).includes('knob_cots'), 'printed knob suppresses the COTS line');
  const without = derive(withPath(base(), 'toppers.knob', 'none'), data);
  ok(lineIds(without).includes('knob_cots'), 'COTS knob line expected');
});

S.test('self-buy lines come out in their declared order', () => {
  let s = withPath(base(), 'view.caps', true);
  s = withPath(s, 'toppers.knob', 'none');
  deep(lineIds(derive(s, data)),
    ['switches', 'stab', 'knob_cots', 'screws', 'inserts', 'touch_contact', 'gasket_sheet']);
});

/* --- engine contracts ---------------------------------------------- */

S.test('facts table is fully resolved from state alone', () => {
  let s = withPath(base(), 'band.translucent', true);
  s = withPath(s, 'tray.translucent', false);
  const f = factsFor(s);
  eq(f.band_translucent, true);
  eq(f.tray_translucent, false);
  eq(f.translucent_case, true);
  eq(f.always, true);
  eq(factsFor(withPath(s, 'band.translucent', false)).translucent_case, false);
});

S.test('no fact and no rule may look a colour up any more', () => {
  const f = factsFor(base());
  for (const k of Object.keys(f)) ok(!/kind|finish|colour|color/.test(k), `stale colour fact: ${k}`);
  const src = JSON.stringify(data.rules);
  for (const id of data.finishes.finishes.map((x) => x.id)) {
    ok(!src.includes(`"${id}"`) || id === 'black', `rules.json tests the finish id "${id}"`);
  }
});

S.test('condition combinators: all / any / not', () => {
  const f = { led: 'yes', base: 'wedge' };
  ok(evaluate({ all: [{ fact: 'led', eq: 'yes' }, { fact: 'base', in: ['wedge', 'riser'] }] }, f));
  ok(evaluate({ any: [{ fact: 'led', eq: 'no' }, { fact: 'base', eq: 'wedge' }] }, f));
  ok(evaluate({ not: { fact: 'led', eq: 'no' } }, f));
  ok(!evaluate({ all: [{ fact: 'led', eq: 'yes' }, { fact: 'base', eq: 'none' }] }, f));
});

S.test('a condition with no operator is a hard error, not a silent pass', () => {
  throws(() => evaluate({ fact: 'led' }, { led: 'yes' }));
  throws(() => evaluate({ nonsense: 1 }, {}));
});

S.test('derive is pure: a deep-frozen state survives it', () => {
  const s = freeze(base());
  const a = derive(s, data);
  const b = derive(s, data);
  deep(a, b, 'same input must give the same output');
});

S.test('every rule id is unique and every rule has a condition', () => {
  const ids = data.rules.rules.map((r) => r.id);
  eq(new Set(ids).size, ids.length, 'duplicate rule id');
  for (const r of data.rules.rules) ok(r.when !== undefined, `rule ${r.id} has no when`);
});

S.run();

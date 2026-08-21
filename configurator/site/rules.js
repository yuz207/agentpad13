/**
 * rules.js — the constraint engine. PURE: state in, derived config out.
 *
 * No DOM, no fetch, no globals: `configurator/tests/site_*.test.mjs` imports
 * this file directly under node, the browser imports the same file. Every
 * coupling lives in rules.json (hand-authored per design spec §4); this file
 * only interprets it.
 */

/** Read a dotted path out of an object. */
export function at(obj, path) {
  return String(path).split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

/** Finish record for an id, or undefined. */
export function finishOf(finishes, id) {
  return (finishes.finishes || []).find((f) => f.id === id);
}

/**
 * Resolve the fact table the rules match against. Facts are the ONLY vocabulary
 * rules.json may use, so a new coupling is a data edit until it needs a new fact.
 *
 * Facts come out of STATE alone — the palette is opaque base colours now, so
 * nothing here has to look a colour up. Translucency is the part's own
 * checkbox, and only the two CASE parts carry it into the rules: a see-through
 * band or tray is what puts the board on show.
 */
export function factsFor(state) {
  const bandTranslucent = at(state, 'band.translucent') === true;
  const trayTranslucent = at(state, 'tray.translucent') === true;
  return {
    always: true,
    led: state.led,
    band_translucent: bandTranslucent,
    tray_translucent: trayTranslucent,
    translucent_case: bandTranslucent || trayTranslucent,
    plate_make: at(state, 'plate.make'),
    plate_variant: at(state, 'plate.variant'),
    base: at(state, 'base.variant'),
    // ONE toggle, both meanings — see the state.js header. Every other `view`
    // flag is render-only and deliberately absent from this table, and so is
    // the whole `lighting` block, and so is translucency on any part that is
    // not the band or the tray.
    caps_on: at(state, 'view.caps') === true,
    knob: at(state, 'toppers.knob'),
    stick: at(state, 'toppers.stick'),
  };
}

/** Evaluate one condition node against the fact table. */
export function evaluate(cond, facts) {
  if (cond === true || cond === undefined) return true;
  if (cond === false) return false;
  if (cond.all) return cond.all.every((c) => evaluate(c, facts));
  if (cond.any) return cond.any.some((c) => evaluate(c, facts));
  if (cond.not) return !evaluate(cond.not, facts);
  if (cond.fact !== undefined) {
    const v = facts[cond.fact];
    if ('eq' in cond) return v === cond.eq;
    if ('ne' in cond) return v !== cond.ne;
    if ('in' in cond) return cond.in.includes(v);
    if ('truthy' in cond) return Boolean(v) === Boolean(cond.truthy);
    throw new Error(`rule condition on fact "${cond.fact}" has no operator`);
  }
  throw new Error(`unrecognised rule condition: ${JSON.stringify(cond)}`);
}

/** Resolve a rule value: literals pass through, {"$state":"a.b"} reads state. */
function resolveValue(v, state) {
  if (v && typeof v === 'object' && !Array.isArray(v) && '$state' in v) return at(state, v.$state);
  return v;
}

/**
 * Apply every rule whose condition holds, in file order.
 *
 * @returns {{facts:object, set:object, show:object, suggest:object,
 *            notes:Array, lines:Array, order:Array, fired:string[]}}
 */
export function derive(state, data) {
  const facts = factsFor(state);
  const out = { facts, set: {}, show: {}, suggest: {}, notes: [], lines: [], order: [], fired: [] };
  for (const rule of data.rules.rules) {
    if (!evaluate(rule.when, facts)) continue;
    out.fired.push(rule.id);
    const t = rule.then || {};
    for (const [k, v] of Object.entries(t.set || {})) out.set[k] = resolveValue(v, state);
    for (const [k, v] of Object.entries(t.show || {})) out.show[k] = v;
    for (const [k, v] of Object.entries(t.suggest || {})) out.suggest[k] = resolveValue(v, state);
    for (const n of t.notes || []) out.notes.push({ ...n, rule: rule.id });
    for (const l of t.lines || []) out.lines.push({ ...l, rule: rule.id });
    for (const o of t.order || []) out.order.push({ ...o, rule: rule.id });
  }
  out.lines.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
  return out;
}

/**
 * Apply the engine's ordering constraints to a list of {id} entries.
 * Stable: only the constrained pairs move, and only when out of order.
 */
export function applyOrder(entries, constraints) {
  const list = entries.slice();
  for (const c of constraints) {
    const i = list.findIndex((e) => e.id === c.before);
    const j = list.findIndex((e) => e.id === c.after);
    if (i === -1 || j === -1 || i < j) continue;
    const [moved] = list.splice(i, 1);
    list.splice(list.findIndex((e) => e.id === c.after), 0, moved);
  }
  return list;
}

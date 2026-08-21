/**
 * state.js — the configuration state. Pure data + a 40-line store.
 * No DOM: node tests import initialState() to build fixtures.
 *
 * `view` is the "Show" group: what is ON THE RENDER. Six of the seven are
 * view-only (switches, encoder, knob, joystick, stick, stabilizer) and reach no
 * rule and no build sheet. `view.caps` is the exception and it is deliberate —
 * keycaps are the one thing you can choose to own, so ONE toggle carries both
 * meanings: showing them renders them AND puts their STLs and the stabiliser
 * line on the sheet, exactly as the old `caps.on` did. rules.js reads it as the
 * caps_on fact; nothing else in `view` is a fact.
 *
 * MODULE vs TOPPER — round 4: "the configurator still doesn't show the encoder
 * or joystick itself, just the toppers." `view.encoder` / `view.joystick` are
 * the HARDWARE (the EC11E can and its shaft, the YA13 frame and its blade);
 * `view.knob` / `view.stick` stay what they always were, the printed cap that
 * sits on top. Hiding a topper leaves the bare module standing, which is the
 * whole point of splitting them.
 *
 * `lighting` is its own block because round 4 made it its own rail section:
 * "Maybe lighting becomes its own section." It is {on, color} and it is
 * VIEW-ONLY — no fact, no rule, no sheet line. `led` (yes/no) is still the
 * board variant you ORDER, and it only gates the band ribbon; the per-key LEDs
 * under the switches are on every board, which is why the Lighting section is
 * offered whatever `led` says.
 *
 * COLOUR and TRANSLUCENCY are two independent axes on every colourable part:
 * `<part>.finish` is an id from the one opaque palette, `<part>.translucent`
 * is a boolean. Ticking translucency renders that part's own colour through
 * finishes.translucent — the ONE frosted treatment — so frosted-clear is
 * translucency + a pale colour, and smoke is translucency + a dark one. Only
 * band and tray translucency is a fact (it is what makes the board visible);
 * the rest is render-only.
 */

/** The catalog's own default entry, else the first one. */
const pick = (list) => (list.find((x) => x.default === true) || list[0]).id;

/** The one starting configuration, derived from catalog + finishes defaults. */
export function initialState(data) {
  const { catalog, finishes } = data;
  const d = finishes.defaults;
  const clear = (id) => (d.translucent || {})[id] === true;
  return {
    led: 'yes',
    board_mask: d.board_mask,
    /* plate.variant — OWNER RULING, round 4, verbatim: "default should tented
       ring, not standard". It shipped as tented_ring once, was "corrected" to
       standard, and is now pinned here: the tented variant leaves the touch pad
       under mask and takes the ordinary HASL-LF finish, so it is the default
       order. Do not flip this back without a new ruling. */
    plate: { make: 'fr4', variant: 'tented_ring', mask: d.plate_mask, finish: d.plate, translucent: clear('plate') },
    band: { width: catalog.band.default, finish: d.band, translucent: clear('band') },
    tray: { finish: d.tray, translucent: clear('tray') },
    base: { variant: 'none' },
    view: {
      caps: false, switches: true,
      encoder: true, knob: true, joystick: true, stick: true,
      stabilizer: true,
    },
    /* Rainbow by default: round 4 opened with "Lit looks useless... Make it
       rainbow or whatever so it's obvious I guess." */
    lighting: { on: false, color: d.lighting || 'rainbow' },
    caps: { profile: catalog.keycaps.profiles[0], width: catalog.keycaps.widths[0], finish: d.caps, translucent: clear('caps') },
    switches: { finish: d.switches, translucent: clear('switches') },
    toppers: {
      knob: pick(catalog.toppers.knobs), stick: pick(catalog.toppers.stick_caps),
      finish: d.toppers, translucent: clear('toppers'),
    },
  };
}

/** Immutable-ish set of a dotted path; returns a new state object. */
export function withPath(state, path, value) {
  const keys = String(path).split('.');
  const next = Array.isArray(state) ? state.slice() : { ...state };
  let cur = next;
  for (let i = 0; i < keys.length - 1; i++) {
    cur[keys[i]] = { ...cur[keys[i]] };
    cur = cur[keys[i]];
  }
  cur[keys[keys.length - 1]] = value;
  return next;
}

export function createStore(initial) {
  let state = initial;
  const subs = new Set();
  return {
    get: () => state,
    set(path, value) {
      const next = withPath(state, path, value);
      state = next;
      for (const fn of subs) fn(state, path, value);
    },
    subscribe(fn) { subs.add(fn); return () => subs.delete(fn); },
  };
}

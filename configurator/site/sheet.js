/**
 * sheet.js — build-sheet assembly. PURE: (state, data, derived) -> sheet model.
 *
 * Three sections and a fixed footer, exactly per design spec §3. Every `path`
 * is repo-root-relative and must exist in the release bundle; the DOM layer is
 * the only thing that turns it into an href. Prices come out `null` — i.e.
 * nothing renders at all — until costs.json carries a real `updated` date, and
 * `costs_label` (the one estimates caveat) appears on the same switch.
 */

import { derive, applyOrder, finishOf } from './rules.js';

/** release/firmware/BRING-UP.md step 1 — the command that works on macOS.
 *  Used only when the catalog does not carry firmware.flash itself. */
const FLASH_FALLBACK = 'dd if=firmware/prebuilt/agentpad13.uf2 of=/Volumes/RPI-RP2/fw.uf2 bs=1m';

/**
 * The fab finish per plate variant — release/HOW-TO-ORDER.md card 3, and the
 * one line on this sheet that is a MANUFACTURING instruction rather than a
 * taste. Round 4 owner ruling, verbatim: "call standard something else b/c that
 * matters for the manufacturing process (not leaded!)".
 *
 * The `standard` variant opens the soldermask over TP5, so the touch pad is
 * BARE COPPER you put a finger on: it must be plated ENIG, which is lead-free
 * gold. Ordered as leaded HASL you would be touching a lead-tin alloy, and the
 * disc would not be flat. The tented and blank variants never expose copper, so
 * they take the ordinary lead-free HASL.
 *
 * Both values therefore say lead-free out loud, and each is ONE value — no
 * prose, per the sheet's own style mandate.
 */
const PLATE_FINISH = {
  standard: 'ENIG (lead-free)',
  tented_ring: 'HASL-LF',
  blank: 'HASL-LF',
};

/**
 * The one line that qualifies every price on the sheet. Owner ruling, verbatim:
 * "We should indicate they're all estimates and prices may change."
 *
 * It rides the same switch as the prices themselves — `costs.updated` — so a
 * sheet with no prices carries no label either, and there is exactly one of it
 * for the whole sheet rather than one per line.
 */
const COSTS_LABEL = 'Estimates — prices change';

const base = (p) => (p ? p.split('/').pop() : p);

/** True once costs.json carries a real `updated` date, i.e. once prices show. */
const pricesShown = (costs) => Boolean(costs) && costs.updated != null;

function priceFor(id, costs) {
  if (!pricesShown(costs)) return null;
  const line = (costs.lines || {})[id];
  return line == null ? null : line;
}

const maskName = (data, id) => {
  const m = (data.finishes.masks || []).find((x) => x.id === id);
  return m ? m.name : id;
};

const finishName = (data, id) => {
  const f = finishOf(data.finishes, id);
  return f ? f.name : id;
};

/**
 * @returns {{sections: Array<{id,title,entries:Array}>, footer: object,
 *            fabpack: string, board_mask: string}}
 */
export function buildSheet(state, data, derived = derive(state, data)) {
  const { catalog, costs } = data;
  const fabpack = derived.set.fabpack;
  const boardMask = derived.set.board_mask;
  const plateVariant = catalog.plate.variants.find((v) => v.id === state.plate.variant);
  const bandWidth = catalog.band.widths.find((w) => w.id === state.band.width);
  const baseItem = catalog.bases.items.find((b) => b.id === state.base.variant);
  const capsOn = derived.facts.caps_on;              // state.view.caps, via rules.js

  /* --- 1. PCBWay order package -------------------------------------
     The printed-plate path drops the plate from the fab order entirely
     (spec §2 "Plate"): no gerbers, no plate mask, no plate finish. */
  const fr4Plate = derived.set.plate_procurement !== 'printed';
  const pcbway = [
    { kind: 'file', id: 'fabpack', text: base(catalog.board.fabpacks[fabpack]), path: catalog.board.fabpacks[fabpack] },
  ];
  if (fr4Plate) {
    pcbway.push({ kind: 'file', id: 'plate_gerbers', text: base(plateVariant.gerbers), path: plateVariant.gerbers });
  }
  pcbway.push({ kind: 'value', id: 'board_mask', label: 'board mask', value: maskName(data, boardMask) });
  if (fr4Plate) {
    pcbway.push({ kind: 'value', id: 'plate_mask', label: 'plate mask', value: maskName(data, state.plate.mask) });
    // PLATE_FINISH wins over any catalog value: the wording is a site display
    // decision (owner ruling above), the catalog id stays pipeline data.
    pcbway.push({ kind: 'value', id: 'plate_finish', label: 'plate finish', value: PLATE_FINISH[plateVariant.id] || plateVariant.finish });
  }
  pcbway.push({ kind: 'note', id: 'assembly', text: 'SMD, encoder, and joystick are factory-populated; the afterlist contains only the optional user-soldered TP5 spring or wire contact.' });

  /* --- 2. Self-buy list (rule-driven) ------------------------------- */
  const selfbuy = derived.lines
    .filter((l) => l.section === 'selfbuy')
    .map((l) => ({ kind: 'text', id: l.id, text: l.text }));

  /* --- 3. Print manifest -------------------------------------------- */
  let print = [
    { kind: 'file', id: 'band', text: base(bandWidth.stl), path: bandWidth.stl },
    { kind: 'file', id: 'tray', text: base(catalog.tray.stl), path: catalog.tray.stl },
  ];
  if (!fr4Plate) {
    print.push({ kind: 'file', id: 'plate_stl', text: base(catalog.plate.stl), path: catalog.plate.stl });
  }
  /* Bases: the fit is MEASURED, never chosen. Print the gauge, keep the rung
     that holds — so the manifest carries the gauge and all four rungs, and
     the note (rules.json base_gauge_flow) says what to do with them. */
  if (baseItem) {
    print.push({ kind: 'file', id: 'base_gauge', text: base(catalog.bases.gauge), path: catalog.bases.gauge });
    for (const rung of catalog.bases.peg_rungs) {
      print.push({ kind: 'file', id: `base_peg_${rung}`, text: base(baseItem.pegs[rung]), path: baseItem.pegs[rung] });
    }
  }
  if (capsOn) {
    const useStab = derived.set.keycap_2u_size === '2u_stab';
    const counts = (useStab && catalog.keycaps.counts.with_stabilizer) || catalog.keycaps.counts;
    for (const [size, count] of Object.entries(counts)) {
      if (typeof count !== 'number' || count <= 0) continue;      // skip source/note/with_stabilizer
      const f = catalog.keycaps.files.find(
        (x) => x.profile === state.caps.profile && x.width === state.caps.width && x.size === size,
      );
      if (f) print.push({ kind: 'file', id: `cap_${size}`, count, text: base(f.stl), path: f.stl });
    }
  }
  if (state.toppers.knob !== 'none') {
    const k = catalog.toppers.knobs.find((x) => x.id === state.toppers.knob);
    if (k) {
      const path = (k.bores && k.bores[catalog.toppers.default_knob_bore]) || k.stl;
      print.push({ kind: 'file', id: 'knob', text: base(path), path });
    }
  }
  if (state.toppers.stick !== 'none') {
    const s = catalog.toppers.stick_caps.find((x) => x.id === state.toppers.stick);
    if (s) {
      const path = (s.socks && s.socks[catalog.toppers.default_stick_sock]) || s.stl;
      const files = s.print_files || [{ id: 'stick_cap', role: 'topper', stl: path }];
      for (const file of files) {
        print.push({
          kind: 'file', id: file.id, role: file.role,
          text: base(file.stl), path: file.stl,
        });
      }
    }
  }
  print = applyOrder(print, derived.order.filter((o) => o.section === 'print'));
  for (const n of derived.notes.filter((n) => n.section === 'print')) {
    print.push({ kind: 'note', id: n.id, text: n.text });
  }

  const sections = [
    { id: 'pcbway', title: 'PCBWay', entries: pcbway },
    { id: 'selfbuy', title: 'Self-buy', entries: selfbuy },
    { id: 'print', title: 'Print', entries: print },
  ];

  for (const s of sections) for (const e of s.entries) e.price = priceFor(e.id, costs);

  const footer = {
    uf2: { text: base(catalog.firmware.uf2), path: catalog.firmware.uf2 },
    flash: catalog.firmware.flash || FLASH_FALLBACK,
    links: [
      { text: base(catalog.firmware.flash_doc), path: catalog.firmware.flash_doc },
      { text: base(catalog.firmware.polarity_doc), path: catalog.firmware.polarity_doc },
    ],
  };

  /* The case colours, as the two independent axes the rail offers: an id from
     the opaque palette plus its own translucency checkbox. `translucent` is
     what opened the board-mask line above, so the sheet carries both. */
  return {
    sections, footer, fabpack, board_mask: boardMask,
    costs_label: pricesShown(costs) ? COSTS_LABEL : null,
    finish_names: { band: finishName(data, state.band.finish), tray: finishName(data, state.tray.finish) },
    translucent: { band: state.band.translucent === true, tray: state.tray.translucent === true },
  };
}

/** Every repo-relative path the sheet emits — used by the link-integrity test. */
export function sheetPaths(sheet) {
  const out = [];
  for (const s of sheet.sections) for (const e of s.entries) if (e.path) out.push(e.path);
  out.push(sheet.footer.uf2.path);
  for (const l of sheet.footer.links) out.push(l.path);
  return out;
}

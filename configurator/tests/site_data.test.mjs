/**
 * site_data.test.mjs — the data contract: stub files are marked as stubs and
 * mirror the generated schema, every mesh and every release path resolves, the
 * frame is the documented det -1 board->glTF swap, and the palette is complete.
 */

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { suite, ok, eq, deep, loadData, REPO, SITE } from './site_harness.mjs';
import { initialState } from '../site/state.js';

const data = loadData();
const S = suite('site_data');
const STUB_DIR = join(SITE, 'data-stub');
const GEN_DIR = join(REPO, 'configurator', 'build', 'out');

const collect = (root, key) => {
  const out = [];
  (function walk(o) {
    if (Array.isArray(o)) return o.forEach(walk);
    if (o && typeof o === 'object') {
      for (const [k, v] of Object.entries(o)) {
        if (k === key && typeof v === 'string') out.push(v); else walk(v);
      }
    }
  })(root);
  return out;
};

S.test('every stub data file is marked STUB: true', () => {
  for (const f of ['catalog.json', 'positions.json', 'costs.json']) {
    const j = JSON.parse(readFileSync(join(STUB_DIR, f), 'utf8'));
    eq(j.STUB, true, `${f} must carry "STUB": true`);
  }
});

S.test('stub costs carry no numbers at all', () => {
  eq(data.costs.updated, null);
  deep(data.costs.lines, {});
});

S.test('stub schema ids match the generated contract', () => {
  eq(data.catalog.schema, 'agentpad13-configurator-catalog-v1');
  eq(data.positions.schema, 'agentpad13-configurator-positions-v1');
});

S.test('every mesh the catalog names exists next to the catalog', () => {
  const meshes = collect(data.catalog, 'mesh');
  ok(meshes.length >= 25, `expected the full mesh set, found ${meshes.length}`);
  for (const m of meshes) ok(existsSync(join(STUB_DIR, m)), `missing stub mesh: ${m}`);
});

S.test('the site owns the five stand-ins the release ships no file for', () => {
  /* Round 4 added the two THT modules: "the configurator still doesn't show
     the encoder or joystick itself, just the toppers." Both are self-buy
     parts, so no release artefact exists and the catalog must not claim one. */
  for (const f of ['switch_mx.glb', 'stabilizer_2u.glb', 'screw_m3.glb',
                   'encoder_ec11e.glb', 'joystick_ya13.glb']) {
    ok(existsSync(join(SITE, 'assets', f)), `assets/${f}`);
  }
  const cat = JSON.stringify(data.catalog);
  for (const n of ['switch_mx', 'stabilizer_2u', 'screw_m3', 'encoder_ec11e', 'joystick_ya13']) {
    ok(!cat.includes(n), `the catalog must not claim a ${n} file`);
  }
});

/** Per-part bounding boxes out of a .glb, in glTF space (Y is board z). */
const partBoxes = (rel) => {
  const b = readFileSync(join(SITE, rel));
  const json = JSON.parse(b.subarray(20, 20 + b.readUInt32LE(12)).toString('utf8'));
  const out = {};
  for (const m of json.meshes) {
    const a = json.accessors[m.primitives[0].attributes.POSITION];
    out[m.name] = { min: a.min, max: a.max };
  }
  return out;
};

S.test('the MX stand-in seats the cap ON the stem, not on top of it', () => {
  const p = partBoxes('assets/switch_mx.glb');
  const seat = data.positions.keycap_seat_z;
  // Cherry MX chain, hardware/case/keycaps/keycaps.py:149-165 + :289-291.
  eq(Math.round(p.shoulder.max[1] * 100) / 100, seat, 'the stem shoulder IS the cap seat');
  eq(Math.round(p.housing.max[1] * 100) / 100, 11.01, 'fixed housing top face, h = 6.01');
  eq(Math.round(p.stem.min[1] * 100) / 100, seat, 'the cross starts at the seat');
  eq(Math.round(p.stem.max[1] * 100) / 100, 15.2, 'the cross tops out 3.60 above the seat');
  const overlap = p.stem.max[1] - seat;
  ok(overlap > 3.5, `the stem must stand INSIDE the cap, got ${overlap}`);
  // and the cap it enters is taller than that, so the stem is fully swallowed
  const cap = partBoxes('data-stub/meshes/cap_dish_1u_std.glb').body;
  ok(cap.max[1] - cap.min[1] > overlap, 'the cap must be taller than the exposed cross');
  ok(seat - p.housing.max[1] < 0.7, 'the housing must reach up to just under the cap rim');
});

S.test('the EC11E stand-in keeps the Alps body and the owner-set viewer stem', () => {
  /* research/04-mechanical-case-dossier.md §1C (CONFIRMED against the Alps
     datasheet pp.163-168 / drawing 4-5): "overall to shaft tip 24.5 mm",
     "Shaft ⌀6 mm metal, flat (D-cut) leaves 4.5 mm across the flat", and the
     11.2 mm mounting-tab pattern the sheet's own encoder line names. z = 0 is
     the PCB top face; the deck is +5.0. */
  const p = partBoxes('assets/encoder_ec11e.glb');
  const r2 = (v) => Math.round(v * 100) / 100;
  eq(r2(p.can.max[1] - p.can.min[1]), 4.5, 'body 4.5 tall');
  eq(r2(p.can.min[1]), 0, 'and it stands on the PCB top face');
  eq(r2(p.can.max[0] - p.can.min[0]), 13.4, 'body 13.4 across board x (tabs included)');
  eq(r2(p.can.max[2] - p.can.min[2]), 12.5, 'body 12.5 across board y');
  eq(r2(p.shaft.min[1]), 4.5, 'the bushing starts where the body stops');
  eq(r2(p.shaft.max[1]), 22.0, 'viewer shaft tip is 2.5 mm below the physical +24.5 height');
  eq(r2(p.shaft.max[0] - p.shaft.min[0]), 7.0, 'Ø7.0 threaded bushing is the widest section');
  /* The body is symmetric about RE1's shaft, which is what lets the viewer
     place it with the ordinary bounding-box recentre. */
  for (const b of [p.can, p.shaft]) {
    for (const ax of [0, 2]) eq(r2(b.min[ax] + b.max[ax]), 0, 'the module must be symmetric on the shaft');
  }
  /* Owner ruling 2026-08-21: this is a viewer-only reduction. The physical
     shaft and every fit-critical topper artifact remain unchanged. */
  eq(r2(24.5 - p.shaft.max[1]), 2.5, 'the visible bare stem is shortened exactly 2.5 mm');
});

S.test('the YA13 stand-in carries its rot-180 clocking as geometry', () => {
  /* agentpad13_case_v2.py v2.4 YA13 block: JS_FRAME_HALF 6.5 (13 x 13 frame),
     "F.Fab bbox 9.3" west+north, "F.Fab bbox local -7.4" east+south, body top
     11.1. cpl_translucent.csv JS1 = (69.710, -13.370, 180.0, top), and
     contract_v4.json: "rot180 = 180deg-from-datasheet-datum clocking (pot
     boxes face West+North)". The asymmetry IS the clocking, so it is baked
     into the mesh — which is why the viewer must not bbox-centre this one. */
  const p = partBoxes('assets/joystick_ya13.glb');
  const r2 = (v) => Math.round(v * 100) / 100;
  for (const ax of [0, 2]) {
    eq(r2(p.frame.min[ax]), -9.3, 'pot faces reach 9.3 from the stick');
    eq(r2(p.frame.max[ax]), 7.4, 'the other two faces reach 7.4');
    eq(r2(p.frame.max[ax] - p.frame.min[ax]), 16.7, 'overall 16.7 footprint');
  }
  ok(p.frame.min[0] + p.frame.max[0] < -1, 'the part must NOT be symmetric: 180deg clocking, west+north pots');
  eq(r2(p.frame.min[1]), 0, 'the frame sits on the PCB top face');
  eq(r2(p.frame.max[1]), 11.0, 'body top, dome crown');
  /* The blade is the printed stick cap's mating feature, so it is consumed
     from stick_cap_params, never invented: 1.85 x 1.15, tip +18.4, and the cap
     sockets over it from socket_mouth_z 14.4. */
  eq(r2(p.stick.max[1]), 18.4, 'blade tip = stick_cap_params blade.tip_z');
  const blade = 14.4;                                     // socket_mouth_z
  ok(p.stick.min[1] < blade, 'the shank must emerge below the cap socket mouth');
  ok(p.frame.max[1] < blade, 'and the body must clear it, or no cap would seat');
});

S.test('the modules sit inside the plate openings they come up through', () => {
  /* The fab plate is frozen: encoder opening x 7.025..21.025, y 6.000..19.000;
     joystick opening x 58.91..77.36, y 2.57..21.02 (case script §5 / §14). A
     module that did not fit those would be a modelling error, not a render. */
  const enc = partBoxes('assets/encoder_ec11e.glb');
  const js = partBoxes('assets/joystick_ya13.glb');
  const e = data.positions.encoder, s = data.positions.stick;
  // the bushing and the shaft are what actually pass THROUGH the plate
  ok(e.x + enc.shaft.max[0] < 21.025 && e.x + enc.shaft.min[0] > 7.025, 'encoder bushing inside the opening');
  ok(e.y + enc.shaft.max[2] < 19.0 && e.y + enc.shaft.min[2] > 6.0);
  ok(s.x + js.frame.max[0] < 77.36 && s.x + js.frame.min[0] > 58.91, 'YA13 body inside the opening');
  ok(s.y + js.frame.max[2] < 21.02 && s.y + js.frame.min[2] > 2.57);
});

S.test('the stub board carries NO fake encoder or joystick body any more', () => {
  /* Rounds 1-3 baked two crude blocks into the stub board so the plate
     openings did not read as holes. With real module meshes on Show toggles
     that would mean unticking "encoder" still left an encoder-shaped lump, so
     the board is a bare slab again — which is also what the GENERATED
     board.glb has always been (an F.Cu plot on a slab). */
  const b = partBoxes('data-stub/meshes/board.glb').body;
  eq(Math.round(b.max[1] * 100) / 100, 0, 'the board stops at the PCB top face');
  eq(Math.round(b.min[1] * 100) / 100, data.positions.pcb.z0, 'and starts at its underside');
});

S.test('the stabiliser stand-in is baked on the published slot centres', () => {
  const b = partBoxes('assets/stabilizer_2u.glb').body;
  const st = data.positions.stabilizer;
  const [[x0], [x1]] = st.slot_centers;
  const [slotW] = st.slot_size;
  eq(Math.round((b.min[0] + slotW / 2) * 1000) / 1000, x0, 'left insert on the left slot centre');
  eq(Math.round((b.max[0] - slotW / 2) * 1000) / 1000, x1, 'right insert on the right slot centre');
  eq(Math.round(b.max[1] * 100) / 100, data.positions.keycap_seat_z, 'stems reach the cap seat');
  ok(b.min[1] < data.positions.deck_z, 'the inserts hang below the deck');
});

S.test('the M3 bolt is a button head seated on the deck, proud by 1.8', () => {
  const b = partBoxes('assets/screw_m3.glb').body;
  const s = data.positions.screws;
  eq(Math.round(b.max[1] * 100) / 100, s.z.head_top, 'head top');
  eq(Math.round(b.min[1] * 100) / 100, s.z.tip, 'M3x8 tip');
  eq(Math.round((b.max[0] - b.min[0]) * 100) / 100, s.head_d, 'head diameter');
  eq(Math.round((s.z.head_top - s.z.seat) * 100) / 100, s.head_h, 'the head stands proud of the plate top');
  eq(s.z.seat, data.positions.deck_z, 'the head seats on the deck');
  eq(s.positions.length, 4, 'four screws, one per corner');
});

S.test('every stub mesh is a valid glTF binary marked as a stub', () => {
  for (const f of ['meshes/band_w5.4.glb', 'meshes/tray.glb', 'meshes/plate.glb', 'meshes/board.glb']) {
    const b = readFileSync(join(STUB_DIR, f));
    eq(b.readUInt32LE(0), 0x46546c67, `${f}: glTF magic`);
    eq(b.readUInt32LE(4), 2, `${f}: glTF version`);
    eq(b.readUInt32LE(8), b.length, `${f}: declared length matches the file`);
    const jsonLen = b.readUInt32LE(12);
    const json = JSON.parse(b.subarray(20, 20 + jsonLen).toString('utf8'));
    eq(json.asset.extras.STUB, true, `${f}: asset.extras.STUB`);
    ok(json.nodes.length >= 1, `${f}: at least one node`);
  }
});

S.test('stub meshes sit in glTF Y-up space at the real z stack', () => {
  const bbox = (rel) => {
    const b = readFileSync(join(STUB_DIR, rel));
    const json = JSON.parse(b.subarray(20, 20 + b.readUInt32LE(12)).toString('utf8'));
    const acc = json.accessors.filter((a) => a.min && a.min.length === 3);
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    for (const a of acc) for (let i = 0; i < 3; i++) { min[i] = Math.min(min[i], a.min[i]); max[i] = Math.max(max[i], a.max[i]); }
    return { min, max };
  };
  const band = bbox('meshes/band_w5.4.glb');
  eq(Math.round(band.min[1] * 100) / 100, -7.5, 'band bottom (Y is up in glTF)');
  eq(Math.round(band.max[1] * 100) / 100, 5.0, 'band rim = deck plane');
  eq(Math.round((band.max[0] - band.min[0]) * 10) / 10, 95.6, 'w5.4 outer x');
  eq(Math.round((band.max[2] - band.min[2]) * 10) / 10, 111.4, 'w5.4 outer z (board y)');
  const cap = bbox('meshes/cap_dish_1u_17p5.glb');
  eq(cap.min[1], 0, 'a keycap instance starts at its bottom rim');
  eq(Math.round((cap.max[0] - cap.min[0]) * 10) / 10, 17.5, '17p5 cap footprint');
  const wedge = bbox('meshes/base_wedge.glb');
  eq(Math.round(wedge.max[1] * 100) / 100, -8.1, 'base pegs stop at peg_top_z');
});

/* --- the lean: hinge, desk plane, and the meshes that must meet it ---- */

S.test('a base leans about the NEAR edge, and its tilt IS its desk slope', () => {
  const items = data.positions.bases.items;
  for (const [id, b] of Object.entries(items)) {
    eq(b.hinge.axis, 'x', `${id}: the hinge is the board x axis`);
    eq(b.hinge.y, b.desk_plane.ref_y, `${id}: the hinge sits on the desk-plane reference`);
    eq(b.hinge.z, b.desk_plane.ref_z, `${id}: hinge z is the desk face at that edge`);
    ok(b.hinge.y > 100, `${id}: the hinge must be the NEAR/user edge, not the USB edge`);
    const slopeDeg = Math.atan(b.desk_plane.slope_per_mm) * 180 / Math.PI;
    eq(Math.round(slopeDeg * 100) / 100, b.tilt_deg, `${id}: tilt must equal the desk slope`);
  }
});

S.test('desk_z is the desk plane evaluated across the base plan, both ends', () => {
  const at = (b, y) => b.desk_plane.ref_z - (b.desk_plane.ref_y - y) * b.desk_plane.slope_per_mm;
  for (const [id, b] of Object.entries(data.positions.bases.items)) {
    const [cx, cy] = b.plan.center || [42.1, 50];
    const half = b.plan.shape === 'circle' ? b.plan.d / 2 : b.plan.size[1] / 2;
    const [yMin, yMax] = [cy - half, cy + half];
    eq(Math.round(at(b, yMin) * 1000) / 1000, Math.round(b.desk_z[0] * 1000) / 1000, `${id}: far end`);
    eq(Math.round(at(b, yMax) * 1000) / 1000, Math.round(b.desk_z[1] * 1000) / 1000, `${id}: near end`);
    eq(Math.round((b.mating_plane_z - b.desk_z[0]) * 1000) / 1000,
       Math.round(b.height_mm * 1000) / 1000, `${id}: height is the tray face -> lowest desk point`);
  }
  ok(data.positions.bases.items.pedestal.desk_z[1] < data.positions.bases.items.pedestal.hinge.z,
    'a Ø78 disc never reaches the hinge line, so its near end is BELOW the hinge');
});

S.test('rotating a base about its hinge lands the desk face level and flat', () => {
  /* The viewer rotates the whole assembly about the hinge line. Do the same
     to the stub base mesh here: every point of its desk face must arrive at
     the SAME height, which is what "sits flat on the desk" means. */
  const b = data.positions.bases.items.wedge;
  const t = -b.tilt_deg * Math.PI / 180;                 // board frame: +y is near
  const face = (y) => b.desk_plane.ref_z - (b.desk_plane.ref_y - y) * b.desk_plane.slope_per_mm;
  const spin = (y, z) => {                               // about (hinge.y, hinge.z)
    const dy = y - b.hinge.y, dz = z - b.hinge.z;
    return b.hinge.z + (dy * Math.sin(t) + dz * Math.cos(t));
  };
  const heights = [-3.7, 20, 50, 80, 103.7].map((y) => Math.round(spin(y, face(y)) * 1000) / 1000);
  for (const h of heights) eq(h, Math.round(b.hinge.z * 1000) / 1000, 'the desk face must come out level');
});

S.test('the stub base meshes reach exactly the published desk_z', () => {
  for (const [id, b] of Object.entries(data.positions.bases.items)) {
    const box = partBoxes(`data-stub/meshes/base_${id}.glb`).body;
    eq(Math.round(box.min[1] * 1000) / 1000, Math.round(b.desk_z[0] * 1000) / 1000,
      `base_${id}.glb bottom must be the lowest desk point`);
    eq(Math.round(box.max[1] * 100) / 100, data.positions.base.peg_top_z, `base_${id}.glb peg tops`);
  }
});

/* --- the plate art contract ------------------------------------------ */

S.test('the plate art extent is the plate, and the stub mirrors the contract', () => {
  const om = data.catalog.plate.openings_map;
  const ex = om.extent_mm;
  const [w, h] = data.positions.plate.size;
  const [cx, cy] = data.positions.plate.center;
  eq(Math.round((ex.x1 - ex.x0) * 100) / 100, w, 'texture extent width == the plate');
  eq(Math.round((ex.y1 - ex.y0) * 100) / 100, h, 'texture extent height == the plate');
  eq(Math.round((ex.x0 + ex.x1) / 2 * 100) / 100, cx, 'and it is centred on the plate');
  eq(Math.round((ex.y0 + ex.y1) / 2 * 100) / 100, cy);
  deep(om.size_px, [Math.round(w * om.px_per_mm), Math.round(h * om.px_per_mm)], 'size_px == extent * px_per_mm');
  ok(/row 0 is board y = 0/.test(om.note), 'the row-0 convention must be stated: the viewer flips v to match');
});

S.test('every plate variant declares a marker, and blank is markerless BY DESIGN', () => {
  const byId = Object.fromEntries(data.catalog.plate.variants.map((v) => [v.id, v]));
  eq(byId.standard.marker, 'exposed_pad');
  eq(byId.tented_ring.marker, 'silk_ring');
  eq(byId.blank.marker, 'none');
  eq(byId.blank.decal, null, 'blank has no decal — that is the design, not a missing file');
  const tp = data.positions.touch_pad;
  for (const v of data.catalog.plate.variants) {
    eq(v.marker, tp.variants[v.id].marker, `${v.id}: catalog and positions must agree on the marker`);
  }
  eq(tp.variants.standard.exposed_d, tp.exposed_pad_d);
  eq(tp.variants.tented_ring.ring_d, tp.ring_d);
});

S.test('every release path in the catalog resolves inside the repo', () => {
  const paths = [];
  (function walk(o) {
    if (Array.isArray(o)) return o.forEach(walk);
    if (o && typeof o === 'object') return Object.values(o).forEach(walk);
    if (typeof o === 'string' && /^release\/[^\s:]+$/.test(o)) paths.push(o);
  })(data.catalog);
  ok(paths.length > 60, `expected the full release path set, found ${paths.length}`);
  for (const p of paths) ok(existsSync(join(REPO, p)), `catalog references a missing file: ${p}`);
});

S.test('positions cover all 13 switches on the 19.05 mm grid', () => {
  eq(data.positions.switches.length, 13);
  const row = data.positions.switches.filter((s) => s.y === 31.7).map((s) => s.x);
  deep(row, [13.525, 32.575, 51.625, 70.675]);
  for (let i = 1; i < row.length; i++) {
    eq(Math.round((row[i] - row[i - 1]) * 1000) / 1000, 19.05, 'key pitch must be 19.05');
  }
  eq(data.positions.switches.filter((s) => s.size === '2u').length, 1);
});

S.test('positions carry the whole z stack the viewer stacks against', () => {
  const p = data.positions;
  eq(p.deck_z, 5);
  eq(p.plate.z1, p.deck_z, 'plate top is the deck plane');
  eq(p.band.z1, p.deck_z, 'band rim is flush with the deck');
  eq(p.tray.z0, -9.5);
  eq(p.band.z0, -7.5, 'the band floats on the tray plinth');
  ok(p.tray.z0 < p.band.z0, 'the 2 mm plinth reveal');
  eq(p.base.mating_plane_z, p.tray.z0);
  eq(p.keycap_seat_z, 11.6);
});

S.test('the frame is the documented det -1 board -> glTF swap', () => {
  const f = data.positions.frame;
  eq(f.handedness, 'left');
  deep(f.to_gltf.matrix_column_major, [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1]);
  ok(/MIRROR/i.test(f.to_gltf.note), 'the note must warn about the mirror image');
  const b = data.positions.mesh_placement.baked;
  ok(b.includes('band_*') && b.includes('tray') && b.includes('plate') && b.includes('board'),
    'case parts are baked');
  for (const k of ['cap_*', 'knob_*', 'stick_cap_*']) {
    ok(data.positions.mesh_placement.instance[k], `${k} must be an instance`);
  }
});

S.test('band outer sizes match the shipped w3.0 / w5.4 / w7.4 geometry', () => {
  deep(data.positions.band.widths['w3.0'].outer, [90.8, 106.6]);
  deep(data.positions.band.widths['w5.4'].outer, [95.6, 111.4]);
  deep(data.positions.band.widths['w7.4'].outer, [99.6, 115.4]);
  for (const id of Object.keys(data.positions.band.widths)) {
    ok(data.catalog.band.widths.some((w) => w.id === id), `catalog is missing band width ${id}`);
  }
});

S.test('keycap counts are catalog data and never a user choice', () => {
  const c = data.catalog.keycaps.counts;
  eq(c['1u'], 12);
  eq(c['2u'] + c['2u_stab'], 1, 'exactly one 2U key');
  eq(c.with_stabilizer['1u'], 12);
  eq(c.with_stabilizer['2u_stab'], 1, 'the stabilised build prints the stab cap');
  eq(c.with_stabilizer['2u'], 0);
});

S.test('the palette is opaque base colours ONLY — translucency is not a colour', () => {
  /* Round 3: colour and translucency are independent axes. A finish carries a
     hex and a roughness and nothing else; no entry may smuggle a material
     property back in and become a second, hidden way to ask for glass. */
  for (const f of data.finishes.finishes) {
    ok(/^#[0-9A-Fa-f]{6}$/.test(f.hex), `${f.id}: hex colour`);
    ok(typeof f.roughness === 'number', `${f.id}: roughness`);
    for (const k of ['kind', 'alpha', 'transmission', 'thickness', 'ior']) {
      eq(f[k], undefined, `${f.id} must not carry a material property (${k})`);
    }
    ok(!/trans|clear|crystal|frost|smoke/i.test(f.id), `${f.id} reads as a translucency, not a colour`);
  }
});

S.test('the ONE translucent treatment is FROSTED, not clear acrylic', () => {
  /* Round 4, verbatim: "transparent should be translucent -- and it should be
     more opaque than this. A frosted look is more like what it is", then the
     correction "Not opaque but a little more so." So: still transmits (it is
     not paint), but a step down from the round-3 glass, and ROUGH — roughness
     is the number that scatters the transmitted image, which is both what
     makes it read as printed plastic and what turns the LED ribbon behind it
     into a broad soft wash instead of a readable hard line. */
  const t = data.finishes.translucent;
  ok(t && typeof t === 'object', 'finishes.translucent is the single treatment');
  ok(t.transmission > 0.6 && t.transmission < 0.9,
    `frosted, not clear and not paint: got transmission ${t.transmission}`);
  ok(t.transmission < 0.90, 'it must be MORE opaque than the round-3 glass (0.90)');
  ok(t.roughness >= 0.4, `frost is roughness: got ${t.roughness} (round 3 was 0.16 glass)`);
  ok(t.thickness > 0 && t.ior >= 1, 'thickness and ior are needed for refraction');
  ok((t.clearcoat ?? 0) < 0.5, 'a strong clearcoat would put the acrylic sheen straight back on');
});

S.test('the palette is a filament shelf, not a curated mood board', () => {
  const list = data.finishes.finishes;
  /* Round 4, verbatim: "for the color picker, why not drop down a grid of
     swatches? Then you can have more colors." The grid is 8 wide, so the
     palette is a whole number of rows. */
  ok(list.length >= 48 && list.length <= 60,
    `round 4 asked for ~48-60 opaque base colours, found ${list.length}`);
  eq(list.length % 8, 0, `the grid is 8 wide: ${list.length} leaves a ragged last row`);
  eq(new Set(list.map((f) => f.id)).size, list.length, 'duplicate finish id');
  eq(new Set(list.map((f) => f.name)).size, list.length, 'duplicate finish name');
  eq(new Set(list.map((f) => f.hex.toUpperCase())).size, list.length, 'two entries share a hex');
  /* Every colour the owner named, by id. These are the obvious ones people
     actually buy filament in — a palette that omits any of them is the
     "muted hideous palette no one would ever choose" all over again. The
     translucent and crystal entries of round 2 are gone ON PURPOSE: they are
     the translucency checkbox now, not seven more rows in the list. */
  const required = [
    'white', 'warm_white', 'silver', 'grey', 'space_grey', 'charcoal', 'black',
    'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'forest', 'teal', 'cyan',
    'sky', 'blue', 'navy', 'indigo', 'purple', 'violet', 'magenta', 'pink', 'rose',
    'brown', 'tan', 'olive',
    'neon_green', 'neon_orange', 'neon_pink',
  ];
  /* ...and what round 4 bought with the grid: light and dark steps of the main
     hues, more pastels, more earths, without touching the saturated core. */
  const roundFour = [
    'bone', 'stone', 'slate', 'gunmetal', 'gold', 'copper', 'chocolate',
    'sand', 'terracotta', 'peach', 'coral', 'blush', 'crimson', 'mustard',
    'butter', 'sage', 'mint', 'emerald', 'aqua', 'powder', 'steel',
    'lavender', 'plum', 'neon_yellow', 'neon_blue',
  ];
  const have = new Set(list.map((f) => f.id));
  for (const id of required) ok(have.has(id), `the palette is missing "${id}"`);
  for (const id of roundFour) ok(have.has(id), `round 4 expanded the palette but "${id}" is missing`);
  for (const id of ['frost', 'smoke', 'trans_red', 'trans_amber', 'trans_green', 'trans_blue', 'crystal']) {
    ok(!have.has(id), `"${id}" is a translucency, not a palette entry`);
  }
  /* Rainbow is a LIGHTING option, not a finish: you cannot print in it. */
  ok(!have.has('rainbow'), 'rainbow is a lighting choice, never a filament colour');
});

S.test('saturated colours are actually saturated (no muting)', () => {
  const sat = (hex) => {
    const n = parseInt(hex.slice(1), 16);
    const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    const max = Math.max(...c), min = Math.min(...c);
    return max === 0 ? 0 : (max - min) / max;
  };
  for (const id of ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'magenta', 'neon_green']) {
    const f = data.finishes.finishes.find((x) => x.id === id);
    ok(sat(f.hex) > 0.7, `${id} (${f.hex}) is washed out: saturation ${sat(f.hex).toFixed(2)}`);
  }
});

S.test('ONE palette: every colourable part draws from the same list', () => {
  const d = data.finishes.defaults;
  const ids = new Set(data.finishes.finishes.map((f) => f.id));
  const parts = ['band', 'tray', 'plate', 'caps', 'switches', 'toppers'];
  for (const k of parts) {
    ok(ids.has(d[k]), `default ${k} colour "${d[k]}" is not in the palette`);
  }
  const maskIds = new Set(data.finishes.masks.map((m) => m.id));
  for (const k of ['board_mask', 'plate_mask']) ok(maskIds.has(d[k]), `default ${k} is not a mask`);
  /* ...and every one of them gets the translucency checkbox too, exactly one
     starting value each — no part may be missing from the second axis. */
  deep(Object.keys(d.translucent).sort(), parts.slice().sort(),
    'the translucency defaults must cover the colourable parts, and only those');
  for (const [k, v] of Object.entries(d.translucent)) eq(typeof v, 'boolean', `${k}: not a boolean`);
  eq(d.translucent.band, true, 'the band starts see-through: that is what the LED band is for');
  /* Lighting draws from the same list PLUS rainbow, which is not a finish. */
  ok(d.lighting === 'rainbow' || ids.has(d.lighting), `default lighting "${d.lighting}" is neither rainbow nor a palette id`);
});

S.test('state gives every colourable part BOTH axes, and the LEDs their own block', () => {
  const s = initialState(data);
  const node = { band: s.band, tray: s.tray, plate: s.plate, caps: s.caps, switches: s.switches, toppers: s.toppers };
  for (const [k, v] of Object.entries(node)) {
    ok(typeof v.finish === 'string', `${k}.finish must be a palette id`);
    eq(typeof v.translucent, 'boolean', `${k}.translucent must be its own checkbox`);
    eq(v.transparent, undefined, `${k}: the old "transparent" key must be gone, not shadowed`);
  }
  eq(s.band.translucent, true);
  eq(s.tray.translucent, false);
  /* Round 4 moved the light switch out of Show and into its own section, and
     added the two modules to Show. `led` is no longer a view flag at all. */
  deep(Object.keys(s.view).sort(),
    ['caps', 'encoder', 'joystick', 'knob', 'stabilizer', 'stick', 'switches']);
  for (const v of Object.values(s.view)) eq(typeof v, 'boolean', 'every Show entry is one checkbox');
  eq(s.view.led, undefined, 'the light switch is state.lighting.on now');
  eq(s.view.encoder, true, 'the encoder module ships shown');
  eq(s.view.joystick, true, 'the joystick module ships shown');
});

S.test('lighting is its own block: off to start, rainbow when you turn it on', () => {
  /* Round 4 opened with "Lit looks useless... Make it rainbow or whatever so
     it's obvious I guess", and closed the section with "Maybe lighting becomes
     its own section." Both land here. */
  const s = initialState(data);
  deep(Object.keys(s.lighting).sort(), ['color', 'on']);
  eq(s.lighting.on, false, 'the render starts unlit');
  eq(s.lighting.color, 'rainbow', 'and the first thing you see when you light it is the rainbow');
});

S.test('the default plate is the TENTED RING — owner ruling, round 4', () => {
  /* Verbatim: "default should tented ring, not standard". It was tented_ring
     once, got "corrected" to standard, and is pinned by ruling now. The point
     is manufacturing: `standard` opens the mask over the touch pad, so that
     one has to be ordered ENIG (lead-free gold) and must never be leaded
     HASL — see the sheet test. Do not flip this without a new ruling. */
  eq(initialState(data).plate.variant, 'tented_ring');
  ok(data.catalog.plate.variants.some((v) => v.id === 'tented_ring'), 'and it must exist in the catalog');
  ok(data.catalog.plate.variants.some((v) => v.id === 'standard'),
    'the catalog id stays `standard`: it is pipeline data, only the DISPLAY label changed');
});

S.test('the palette references no release artefact (colour is not a file)', () => {
  ok(!JSON.stringify(data.finishes).includes('release/'), 'finishes.json must stay file-free');
});

S.test('masks include black, and black is the default', () => {
  ok(data.finishes.masks.some((m) => m.id === 'black'));
  eq(data.finishes.defaults.board_mask, 'black');
});

/* --- parity with the generated pipeline, when it is present ---------- */

S.test('stub mirrors the generated catalog shape (skipped if not built yet)', () => {
  const p = join(GEN_DIR, 'catalog.json');
  if (!existsSync(p)) { console.log('        (no configurator/build/out/catalog.json — skipped)'); return; }
  const gen = JSON.parse(readFileSync(p, 'utf8'));
  const keys = (o) => Object.keys(o).filter((k) => k !== 'STUB').sort();
  deep(keys(data.catalog), keys(gen), 'top-level catalog keys drifted from the generated contract');
  for (const k of ['board', 'plate', 'band', 'tray', 'bases', 'keycaps', 'toppers', 'gasket', 'firmware', 'docs']) {
    const extra = keys(gen[k]).filter((x) => !keys(data.catalog[k]).includes(x));
    deep(extra, [], `catalog.${k} is missing generated keys`);
  }
});

S.test('stub mirrors the generated positions shape (skipped if not built yet)', () => {
  const p = join(GEN_DIR, 'positions.json');
  if (!existsSync(p)) { console.log('        (no configurator/build/out/positions.json — skipped)'); return; }
  const gen = JSON.parse(readFileSync(p, 'utf8'));
  const missing = Object.keys(gen).filter((k) => !(k in data.positions));
  deep(missing, [], 'positions is missing generated keys');
  eq(data.positions.frame.handedness, gen.frame.handedness, 'handedness must agree');
  deep(data.positions.frame.to_gltf.matrix_column_major, gen.frame.to_gltf.matrix_column_major);
  eq(data.positions.keycap_seat_z, gen.keycap_seat_z);
  deep(data.positions.switches.map((s) => [s.ref, s.x, s.y, s.size]),
       gen.switches.map((s) => [s.ref, s.x, s.y, s.size]), 'switch table must agree');
});

S.test('every mesh the generated catalog names exists too (skipped if not built)', () => {
  const p = join(GEN_DIR, 'catalog.json');
  if (!existsSync(p)) { console.log('        (not built yet — skipped)'); return; }
  const gen = JSON.parse(readFileSync(p, 'utf8'));
  for (const m of collect(gen, 'mesh')) ok(existsSync(join(GEN_DIR, m)), `generated mesh missing: ${m}`);
  const stubNames = collect(data.catalog, 'mesh').map((m) => m.split('/').pop()).sort();
  const genNames = collect(gen, 'mesh').map((m) => m.split('/').pop()).sort();
  deep(stubNames, genNames, 'stub and generated mesh file names must match one-for-one');
});

S.run();

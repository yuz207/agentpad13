/**
 * make_stub_meshes.mjs — STUB mesh generator for the agentpad13 configurator.
 *
 *   node configurator/site/tools/make_stub_meshes.mjs
 *
 * Writes primitive .glb stand-ins into configurator/site/data-stub/meshes/
 * (plus the five site-owned assets in assets/: the MX switch, the 2u
 * stabiliser, the M3 corner bolt, the EC11E encoder and the YA13 joystick —
 * the last two added in round 4, "the configurator still doesn't show the
 * encoder or joystick itself, just the toppers"). These are NOT the
 * shipping geometry: boxes, rounded prisms, rings, cylinders and slabs at the
 * REAL footprints and the REAL z-stack, so every placement path in viewer.js
 * is exercised before the decimated derivatives of the shipping STLs exist.
 * Every file carries asset.extras.STUB = true, and the filenames, the frame
 * and the baked/instance split match configurator/build/out/meshes/ exactly.
 *
 * Numbers are read off the shipped design sources (nothing is invented):
 *   release/hardware/pcb/harness/contract_v4.json  — outline + refs
 *   release/hardware/case/v2/agentpad13_case_v2.py — z stack + case dims
 *   release/hardware/case/v2/bases/params/agentpad13_base_params.json
 *   release/hardware/case/v2/toppers/params/*.json
 *
 * FRAME — matches positions.json `frame` / `mesh_placement`:
 *   Geometry is authored in the case model's LEFT-handed board frame
 *   (x right, y toward the user, z up, z = 0 at the PCB top face) and emitted
 *   in glTF's Y-up right-handed space by the (X,Y,Z) = (x,z,y) swap. That swap
 *   has determinant -1 — which is exactly what turns the left-handed design
 *   frame into the correctly handed real device — so Tris.tri() also reverses
 *   the winding, keeping every normal pointing out.
 *
 *   baked    (board, plate, band_*, tray, base_*) carry their assembly
 *            position in the vertex data: load and add, no transform.
 *   instance (cap_*, knob_*, stick_cap_*, switch_mx, screw_m3,
 *            encoder_ec11e, joystick_ya13) sit at their own local origin:
 *            caps start at y = 0 (bottom rim) and are placed at the keycap
 *            seat; knobs, stick caps, switches, bolts and the two modules
 *            carry absolute y. joystick_ya13 is the one instance that is NOT
 *            symmetric in x/y — its pot boxes face west and north — so the
 *            viewer places it with recentre:false, on its own origin.
 *            stabilizer_2u is the one BAKED site asset — its wire is
 *            asymmetric, so it carries its absolute board position.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = join(HERE, '..');
const OUT = join(SITE, 'data-stub', 'meshes');
const ASSETS = join(SITE, 'assets');

/* ------------------------------------------------------------------ */
/* geometry accumulator: board frame in, glTF frame out                */
/* ------------------------------------------------------------------ */

const swap = (p) => [p[0], p[2], p[1]];

class Tris {
  constructor() { this.p = []; this.n = []; }
  /** a, b, c CCW in the board frame; emitted swapped and re-wound. */
  tri(a, b, c) {
    const A = swap(a), B = swap(b), C = swap(c);
    const ux = C[0] - A[0], uy = C[1] - A[1], uz = C[2] - A[2];
    const vx = B[0] - A[0], vy = B[1] - A[1], vz = B[2] - A[2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const l = Math.hypot(nx, ny, nz) || 1;
    nx /= l; ny /= l; nz /= l;
    this.p.push(...A, ...C, ...B);
    this.n.push(nx, ny, nz, nx, ny, nz, nx, ny, nz);
  }
  quad(a, b, c, d) { this.tri(a, b, c); this.tri(a, c, d); }
  get count() { return this.p.length / 3; }
}

function roundedRectLoop(cx, cy, w, h, r, seg = 8) {
  const hw = w / 2, hh = h / 2;
  r = Math.max(0, Math.min(r, hw, hh));
  const pts = [];
  const corners = [
    [cx + hw - r, cy + hh - r, 0],
    [cx - hw + r, cy + hh - r, Math.PI / 2],
    [cx - hw + r, cy - hh + r, Math.PI],
    [cx + hw - r, cy - hh + r, -Math.PI / 2],
  ];
  for (const [ox, oy, a0] of corners) {
    for (let i = 0; i <= seg; i++) {
      const a = a0 + (Math.PI / 2) * (i / seg);
      pts.push([ox + r * Math.cos(a), oy + r * Math.sin(a)]);
    }
  }
  return pts;
}

function circleLoop(cx, cy, r, seg = 96) {
  const pts = [];
  for (let i = 0; i < seg; i++) {
    const a = (2 * Math.PI * i) / seg;
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return pts;
}

/** CCW square loop, side `w`, centred on (cx, cy). */
const squareLoop = (cx, cy, w) => {
  const h = w / 2;
  return [[cx - h, cy - h], [cx + h, cy - h], [cx + h, cy + h], [cx - h, cy + h]];
};

/**
 * CCW D-shaft section: a Ø`d` circle with ONE chord cut so the ACROSS-FLAT
 * measurement is `af` — the way a flatted encoder shaft is dimensioned. The
 * flat lands on the +x side; on this part that choice is free, because the
 * printed knob's bore is a PLAIN ROUND bore (encoder_knob_params.json
 * "bore_strategy": "plain round bore + fit ladder (no modeled ribs)"), so
 * nothing keys to it.
 */
function dShaftLoop(cx, cy, d, af, seg = 28) {
  const r = d / 2;
  const xf = af - r;                                 // flat's distance from the axis
  const a0 = Math.acos(Math.max(-1, Math.min(1, xf / r)));
  const pts = [];
  for (let i = 0; i <= seg; i++) {
    const a = a0 + (2 * Math.PI - 2 * a0) * (i / seg);
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return pts;                                        // the wrap edge IS the flat
}

/** CCW regular hexagon by ACROSS-FLATS size (a hex socket is spec'd A/F). */
function hexLoop(cx, cy, af) {
  const r = af / Math.sqrt(3);                      // circumradius from A/F
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 3) * i + Math.PI / 6;
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return pts;
}

/**
 * Loft between two same-length CCW loops at two heights. Winding matches
 * extrudeConvex: side quad = (a@z0, b@z0, b@z1, a@z1), caps fan from the
 * centroid. Used where the plan CHANGES with height (a tapered switch
 * housing, a drafted stem collar, a domed screw head).
 */
function loftLoops(t, lo, z0, hi, z1, { capBottom = false, capTop = false } = {}) {
  const n = lo.length;
  const mid = (l) => [l.reduce((s, p) => s + p[0], 0) / l.length, l.reduce((s, p) => s + p[1], 0) / l.length];
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    t.quad([lo[i][0], lo[i][1], z0], [lo[j][0], lo[j][1], z0], [hi[j][0], hi[j][1], z1], [hi[i][0], hi[i][1], z1]);
  }
  if (capBottom) {
    const [cx, cy] = mid(lo);
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      t.tri([cx, cy, z0], [lo[j][0], lo[j][1], z0], [lo[i][0], lo[i][1], z0]);
    }
  }
  if (capTop) {
    const [cx, cy] = mid(hi);
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      t.tri([cx, cy, z1], [hi[i][0], hi[i][1], z1], [hi[j][0], hi[j][1], z1]);
    }
  }
}

/** A capped round rod between two board-frame points — the stabiliser wire. */
function rod(t, p0, p1, r, seg = 12) {
  const ax = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
  const len = Math.hypot(...ax) || 1;
  const dir = ax.map((v) => v / len);
  const up = Math.abs(dir[2]) > 0.9 ? [1, 0, 0] : [0, 0, 1];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = (v) => { const l = Math.hypot(...v) || 1; return v.map((x) => x / l); };
  const u = norm(cross(dir, up));
  const v = norm(cross(dir, u));
  const ring = (p) => {
    const out = [];
    for (let i = 0; i < seg; i++) {
      const a = (2 * Math.PI * i) / seg;
      out.push([p[0] + r * (u[0] * Math.cos(a) + v[0] * Math.sin(a)),
                p[1] + r * (u[1] * Math.cos(a) + v[1] * Math.sin(a)),
                p[2] + r * (u[2] * Math.cos(a) + v[2] * Math.sin(a))]);
    }
    return out;
  };
  const a = ring(p0), b = ring(p1);
  for (let i = 0; i < seg; i++) {
    const j = (i + 1) % seg;
    t.quad(a[i], a[j], b[j], b[i]);
    t.tri(p0, a[j], a[i]);
    t.tri(p1, b[i], b[j]);
  }
}

/** Extrude a convex CCW loop; z0/z1 may be numbers or f([x,y]) planes. */
function extrudeConvex(t, loop, z0, z1) {
  const zb = typeof z0 === 'function' ? z0 : () => z0;
  const zt = typeof z1 === 'function' ? z1 : () => z1;
  const cx = loop.reduce((s, p) => s + p[0], 0) / loop.length;
  const cy = loop.reduce((s, p) => s + p[1], 0) / loop.length;
  const ctop = [cx, cy, zt([cx, cy])];
  const cbot = [cx, cy, zb([cx, cy])];
  for (let i = 0; i < loop.length; i++) {
    const a = loop[i], b = loop[(i + 1) % loop.length];
    const at = [a[0], a[1], zt(a)], bt = [b[0], b[1], zt(b)];
    const ab = [a[0], a[1], zb(a)], bb = [b[0], b[1], zb(b)];
    t.tri(ctop, at, bt);
    t.tri(cbot, bb, ab);
    t.quad(ab, bb, bt, at);
  }
}

function extrudeRing(t, outer, inner, z0, z1) {
  const n = outer.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const o0 = outer[i], o1 = outer[j], i0 = inner[i], i1 = inner[j];
    t.quad([o0[0], o0[1], z1], [o1[0], o1[1], z1], [i1[0], i1[1], z1], [i0[0], i0[1], z1]);
    t.quad([i0[0], i0[1], z0], [i1[0], i1[1], z0], [o1[0], o1[1], z0], [o0[0], o0[1], z0]);
    t.quad([o0[0], o0[1], z0], [o1[0], o1[1], z0], [o1[0], o1[1], z1], [o0[0], o0[1], z1]);
    t.quad([i0[0], i0[1], z1], [i1[0], i1[1], z1], [i1[0], i1[1], z0], [i0[0], i0[1], z0]);
  }
}

const boxTris = (t, x0, x1, y0, y1, z0, z1) =>
  extrudeConvex(t, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], z0, z1);

/** Axis-aligned rectangle minus axis-aligned holes, by sweep decomposition. */
function rectWithHoles(t, x0, x1, y0, y1, z0, z1, holes) {
  const ys = new Set([y0, y1]);
  for (const h of holes) {
    if (h.y0 > y0 && h.y0 < y1) ys.add(h.y0);
    if (h.y1 > y0 && h.y1 < y1) ys.add(h.y1);
  }
  const yb = [...ys].sort((a, b) => a - b);
  for (let bi = 0; bi < yb.length - 1; bi++) {
    const by0 = yb[bi], by1 = yb[bi + 1], mid = (by0 + by1) / 2;
    const cuts = holes
      .filter((h) => h.y0 < mid && h.y1 > mid)
      .map((h) => [Math.max(h.x0, x0), Math.min(h.x1, x1)])
      .filter(([a, b]) => b > a)
      .sort((a, b) => a[0] - b[0]);
    let x = x0;
    for (const [cx0, cx1] of cuts) {
      if (cx0 > x) boxTris(t, x, cx0, by0, by1, z0, z1);
      x = Math.max(x, cx1);
    }
    if (x < x1) boxTris(t, x, x1, by0, by1, z0, z1);
  }
}

/* ------------------------------------------------------------------ */
/* glb writer (glTF 2.0 binary, one node per named part)               */
/* ------------------------------------------------------------------ */

function writeGlb(file, parts) {
  const json = {
    asset: { version: '2.0', generator: 'agentpad13 configurator stub mesh generator', extras: { STUB: true } },
    scene: 0, scenes: [{ nodes: parts.map((_, i) => i) }],
    nodes: [], meshes: [], accessors: [], bufferViews: [], buffers: [],
  };
  const blobs = [];
  let offset = 0;
  parts.forEach((part, i) => {
    const pos = Float32Array.from(part.t.p);
    const nor = Float32Array.from(part.t.n);
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    for (let k = 0; k < pos.length; k += 3) {
      for (let c = 0; c < 3; c++) {
        if (pos[k + c] < min[c]) min[c] = pos[k + c];
        if (pos[k + c] > max[c]) max[c] = pos[k + c];
      }
    }
    const pv = json.bufferViews.length;
    json.bufferViews.push({ buffer: 0, byteOffset: offset, byteLength: pos.byteLength, target: 34962 });
    blobs.push(Buffer.from(pos.buffer, pos.byteOffset, pos.byteLength));
    offset += pos.byteLength;
    const nv = json.bufferViews.length;
    json.bufferViews.push({ buffer: 0, byteOffset: offset, byteLength: nor.byteLength, target: 34962 });
    blobs.push(Buffer.from(nor.buffer, nor.byteOffset, nor.byteLength));
    offset += nor.byteLength;
    const pa = json.accessors.length;
    json.accessors.push({ bufferView: pv, componentType: 5126, count: pos.length / 3, type: 'VEC3', min, max });
    const na = json.accessors.length;
    json.accessors.push({ bufferView: nv, componentType: 5126, count: nor.length / 3, type: 'VEC3' });
    json.meshes.push({ name: part.name, primitives: [{ attributes: { POSITION: pa, NORMAL: na }, mode: 4 }] });
    json.nodes.push({ name: part.name, mesh: i });
  });
  json.buffers.push({ byteLength: offset });

  let jsonBuf = Buffer.from(JSON.stringify(json), 'utf8');
  while (jsonBuf.length % 4) jsonBuf = Buffer.concat([jsonBuf, Buffer.from(' ')]);
  let binBuf = Buffer.concat(blobs);
  while (binBuf.length % 4) binBuf = Buffer.concat([binBuf, Buffer.alloc(1)]);

  const head = Buffer.alloc(12);
  head.writeUInt32LE(0x46546c67, 0);
  head.writeUInt32LE(2, 4);
  head.writeUInt32LE(12 + 8 + jsonBuf.length + 8 + binBuf.length, 8);
  const jHead = Buffer.alloc(8);
  jHead.writeUInt32LE(jsonBuf.length, 0); jHead.writeUInt32LE(0x4e4f534a, 4);
  const bHead = Buffer.alloc(8);
  bHead.writeUInt32LE(binBuf.length, 0); bHead.writeUInt32LE(0x004e4942, 4);

  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, Buffer.concat([head, jHead, jsonBuf, bHead, binBuf]));
  return { file, tris: parts.reduce((s, p) => s + p.t.count / 3, 0) };
}

/* ------------------------------------------------------------------ */
/* the agentpad13 numbers                                              */
/* ------------------------------------------------------------------ */

const PCB_W = 84.2, PCB_H = 100.0, CX = PCB_W / 2, CY = PCB_H / 2;
const OCTAGON = [[13.2, 0], [69.6, 0], [84.2, 14.6], [84.2, 85.4],
                 [69.6, 100], [14.6, 100], [0, 85.4], [0, 13.2]];
const Z_DECK = 5.0, Z_PLATE_BOT = 3.4, Z_PCB_BOT = -1.6;
const BAND_Z_BOT = -7.5, Z_TRAY_BOT = -9.5, Z_FLOOR_TOP = -5.1;
const PLATE_W = 84.4, PLATE_H = 100.0, PLATE_R = 5.4;
const INNER_W = 84.8, INNER_H = 100.6, INNER_R = 5.6, OUTER_R = 8.0;
const TRAY_W = 84.3, TRAY_H = 100.1, TRAY_R = 5.35;
const FR4_CUTOUT = 14.0;
const SW = {
  SW1: [13.525, 31.7], SW2: [32.575, 31.7], SW3: [51.625, 31.7], SW4: [70.675, 31.7],
  SW5: [13.525, 50.75], SW6: [32.575, 50.75], SW7: [51.625, 50.75], SW8: [70.675, 50.75],
  SW9: [13.525, 69.8], SW10: [32.575, 69.8], SW11: [51.625, 69.8], SW12: [70.675, 69.8],
  SW13: [42.1, 88.85],
};
const ENC_SHAFT = [13.525, 12.5];
const ENC_OPEN = { x0: 7.025, x1: 21.025, y0: 6.0, y1: 19.0 };
const JS_OPEN = { x0: 58.91, x1: 77.36, y0: 2.57, y1: 21.02 };
const STICK = [69.71, 13.37];
const KEYCAP_SEAT_Z = 11.6, CAP_H = 6.0;

/* The YA13's stick blade — the section every printed stick cap sockets onto.
   CONSUMED from release/hardware/case/v2/toppers/params/stick_cap_params.json
   ("blade": {x, y, tip_z}; every variant's sockets.nom is the same 1.85 x 1.15
   and every socket_mouth_z is 14.4). It is not ours to change: the cap files
   were cut against these numbers. */
const STICK_BLADE = { x: 1.85, y: 1.15, tip_z: 18.4 };

/* MX switch stand-in — every number is the Cherry MX chain read off
   hardware/case/keycaps/keycaps.py (see the switch block at the bottom of
   this file for the full citation). z = deck + h, deck = 5.0. */
const SW_BOTTOM_SQ = 13.9;                       // passes the plate's 14.0 cutout
const SW_LIP_SQ = 15.60, SW_LIP_Z0 = 4.65, SW_LIP_Z1 = 5.75;   // :297-298, h -0.35..0.75
const SW_TAPER_Z1 = 10.70;                       // :164  h 5.70, housing 10.12 wide
const SW_HOUSING_TOP_SQ = 9.17, SW_HOUSING_TOP_Z = 11.01;      // :292  h 6.01
const SW_WELL = 6.44, SW_COLLAR_SQ = 5.80;       // :294-296 collar base / :161 top
const SW_SEAT_Z = KEYCAP_SEAT_Z;                 // :289  shoulder h 6.60 == the seat
const SW_CROSS_L = 4.00, SW_CROSS_W_WIDE = 1.30, SW_CROSS_W_NARROW = 1.10;   // :327-329
const SW_STEM_TOP_Z = SW_SEAT_Z + 3.60;          // :290-291 cross 3.60 above the seat

/* 2u plate-mount stabiliser stand-in, from the stabilizer block of
   positions.json (x, slot-centre y, half spacing). View only. */
const STAB_XY = [42.1, 89.47], STAB_HALF = 11.938, STAB_SLOT = [6.65, 12.3];
const STAB_WIRE_REACH = 8.5, STAB_WIRE_Z = 6.2, STAB_WIRE_D = 1.5;

/* M3x8 ISO 7380 button head — four of them, real hardware, always on deck. */
const M3_SHANK_D = 3.0, M3_TIP_Z = -3.0;
const M3_HEAD_D = 5.7, M3_HEAD_H = 1.8, M3_HEX_AF = 2.0, M3_HEX_DEPTH = 0.9;
const BASE_RECT = { x0: -3.7, x1: 87.9, y0: -3.7, y1: 103.7 };
const BASE_PEG_TOP = -8.1, BASE_PEG_D = 5.8, BASE_PITCH = 25.0;
const TILT = 8.0 * Math.PI / 180;

const written = [];
const emit = (dir, name, parts) => written.push(writeGlb(join(dir, name), parts));

/* --- board: the octagonal slab, and nothing else --------------------
   Up to round 3 this mesh also carried two crude THT blocks so the plate's
   encoder and stick openings did not read as holes into an empty case. They
   are GONE: assets/encoder_ec11e.glb and assets/joystick_ya13.glb are the real
   modules now, they are dimensioned rather than blocked in, and they are Show
   toggles — leaving a fake body baked into the board would mean unticking
   "encoder" still left an encoder-shaped lump behind. The generated
   build/out/meshes/board.glb has never carried them (it is the F.Cu plot on a
   slab), so this also brings the stub back in line with it. */
{
  const t = new Tris();
  extrudeConvex(t, OCTAGON, Z_PCB_BOT, 0);
  emit(OUT, 'board.glb', [{ name: 'body', t }]);
}

/* --- plate: one mesh, exactly as the real catalog ships it ---------- */
{
  const holes = [];
  for (const [x, y] of Object.values(SW)) {
    holes.push({ x0: x - FR4_CUTOUT / 2, x1: x + FR4_CUTOUT / 2, y0: y - FR4_CUTOUT / 2, y1: y + FR4_CUTOUT / 2 });
  }
  holes.push(ENC_OPEN, JS_OPEN);
  const t = new Tris();
  const x0 = CX - PLATE_W / 2, x1 = CX + PLATE_W / 2;
  const y0 = CY - PLATE_H / 2, y1 = CY + PLATE_H / 2;
  const outer = roundedRectLoop(CX, CY, PLATE_W, PLATE_H, PLATE_R, 8);
  const inner = roundedRectLoop(CX, CY, PLATE_W - 2 * PLATE_R, PLATE_H - 2 * PLATE_R, 0.001, 8);
  extrudeRing(t, outer, inner, Z_PLATE_BOT, Z_DECK);
  rectWithHoles(t, x0 + PLATE_R, x1 - PLATE_R, y0 + PLATE_R, y1 - PLATE_R, Z_PLATE_BOT, Z_DECK, holes);
  emit(OUT, 'plate.glb', [{ name: 'body', t }]);
}

/* --- band: rounded ring per wall width ------------------------------ */
for (const [id, wall] of [['w3.0', 3.0], ['w5.4', 5.4], ['w7.4', 7.4]]) {
  const t = new Tris();
  const outer = roundedRectLoop(CX, CY, INNER_W + 2 * wall, INNER_H + 2 * wall, OUTER_R, 10);
  const inner = roundedRectLoop(CX, CY, INNER_W, INNER_H, INNER_R, 10);
  extrudeRing(t, outer, inner, BAND_Z_BOT, Z_DECK);
  emit(OUT, `band_${id}.glb`, [{ name: 'body', t }]);
}

/* --- tray: the plinth slab ------------------------------------------ */
{
  const t = new Tris();
  extrudeConvex(t, roundedRectLoop(CX, CY, TRAY_W, TRAY_H, TRAY_R, 8), Z_TRAY_BOT, Z_FLOOR_TOP);
  emit(OUT, 'tray.glb', [{ name: 'body', t }]);
}

/* --- bases: flat top on the mating plane, the tilt lives on the desk
       face; four locating pegs stand proud to the published peg_top_z. */
{
  const pegs = (t) => {
    for (const dx of [-BASE_PITCH / 2, BASE_PITCH / 2]) {
      for (const dy of [-BASE_PITCH / 2, BASE_PITCH / 2]) {
        extrudeConvex(t, circleLoop(CX + dx, CY + dy, BASE_PEG_D / 2, 24), Z_TRAY_BOT, BASE_PEG_TOP);
      }
    }
  };
  const tiltBottom = (p) => Z_TRAY_BOT - (2.4 + (BASE_RECT.y1 - p[1]) * Math.tan(TILT));
  const rect = () => roundedRectLoop((BASE_RECT.x0 + BASE_RECT.x1) / 2, (BASE_RECT.y0 + BASE_RECT.y1) / 2,
    BASE_RECT.x1 - BASE_RECT.x0, BASE_RECT.y1 - BASE_RECT.y0, 8.0, 8);
  {
    const t = new Tris();
    extrudeConvex(t, rect(), Z_TRAY_BOT - 3.0, Z_TRAY_BOT);
    pegs(t);
    emit(OUT, 'base_riser.glb', [{ name: 'body', t }]);
  }
  {
    const t = new Tris();
    extrudeConvex(t, rect(), tiltBottom, Z_TRAY_BOT);
    pegs(t);
    emit(OUT, 'base_wedge.glb', [{ name: 'body', t }]);
  }
  {
    const t = new Tris();
    extrudeConvex(t, circleLoop(CX, CY, 39.0, 96), tiltBottom, Z_TRAY_BOT);
    pegs(t);
    emit(OUT, 'base_pedestal.glb', [{ name: 'body', t }]);
  }
}

/* --- keycaps: instance meshes, local origin = centre of the bottom rim */
{
  const widthMM = { '17p5': 17.5, std: 18.0 };
  const sizeSpan = { '1u': 0, '2u': 19.05, '2u_stab': 19.05 };
  for (const profile of ['dish', 'plateau']) {
    for (const [wid, w] of Object.entries(widthMM)) {
      for (const [size, extra] of Object.entries(sizeSpan)) {
        const t = new Tris();
        const bw = w + extra, bh = w;
        const topInset = profile === 'dish' ? 1.6 : 0.9;
        const loopB = roundedRectLoop(0, 0, bw, bh, 1.6, 6);
        const loopT = roundedRectLoop(0, 0, bw - 2 * topInset, bh - 2 * topInset, 1.6, 6);
        for (let i = 0; i < loopB.length; i++) {
          const j = (i + 1) % loopB.length;
          const a = loopB[i], b = loopB[j], c = loopT[j], d = loopT[i];
          t.quad([a[0], a[1], 0], [b[0], b[1], 0], [c[0], c[1], CAP_H], [d[0], d[1], CAP_H]);
          t.tri([0, 0, 0], [b[0], b[1], 0], [a[0], a[1], 0]);
        }
        const dip = profile === 'dish' ? 0.55 : 0.0;
        for (let i = 0; i < loopT.length; i++) {
          const j = (i + 1) % loopT.length;
          t.tri([0, 0, CAP_H - dip], [loopT[i][0], loopT[i][1], CAP_H], [loopT[j][0], loopT[j][1], CAP_H]);
        }
        emit(OUT, `cap_${profile}_${size}_${wid}.glb`, [{ name: 'body', t }]);
      }
    }
  }
}

/* --- toppers: instance meshes centred on x/y, absolute z ------------- */
{
  /* v2 toppers 2026-08-21: three Ø19 knobs to +27; stubs are plain cylinders */
  const knobs = {
    A: { od: 19.0, z0: 8.0, z1: 27.0, top: 'flat' },
    B2: { od: 19.0, z0: 8.0, z1: 27.0, top: 'flat' },
    C: { od: 19.0, z0: 8.0, z1: 27.0, top: 'flat' },
  };
  for (const [id, k] of Object.entries(knobs)) {
    const t = new Tris();
    const r = k.od / 2;
    if (k.top === 'dome') {
      extrudeConvex(t, circleLoop(0, 0, r, 48), k.z0, k.z1 - 2.0);
      const rings = 6;
      for (let s = 0; s < rings; s++) {
        const a0 = (Math.PI / 2) * (s / rings), a1 = (Math.PI / 2) * ((s + 1) / rings);
        const l0 = circleLoop(0, 0, r * Math.cos(a0), 48), l1 = circleLoop(0, 0, r * Math.cos(a1), 48);
        const h0 = k.z1 - 2.0 + 2.0 * Math.sin(a0), h1 = k.z1 - 2.0 + 2.0 * Math.sin(a1);
        for (let i = 0; i < 48; i++) {
          const j = (i + 1) % 48;
          t.quad([l0[i][0], l0[i][1], h0], [l0[j][0], l0[j][1], h0], [l1[j][0], l1[j][1], h1], [l1[i][0], l1[i][1], h1]);
        }
      }
    } else if (k.top === 'ribbed') {
      extrudeConvex(t, circleLoop(0, 0, r - 0.6, 48), k.z0, k.z1);
      for (let i = 0; i < 16; i++) {
        const a = (2 * Math.PI * i) / 16;
        extrudeConvex(t, circleLoop((r - 0.6) * Math.cos(a), (r - 0.6) * Math.sin(a), 0.75, 8), k.z0, k.z1 - 1.5);
      }
    } else {
      extrudeConvex(t, circleLoop(0, 0, r, 48), k.z0, k.z1);
    }
    emit(OUT, `knob_${id}.glb`, [{ name: 'body', t }]);
  }

  const sticks = { nub_C2: 6.189, puck_TPU: 9.412 }; /* v2: two stick parts */
  for (const [id, od] of Object.entries(sticks)) {
    const t = new Tris();
    const r = od / 2, z0 = 14.4, z1 = 19.6;
    if (id === 'taper') {
      const lo = circleLoop(0, 0, r, 48), hi = circleLoop(0, 0, r * 0.62, 48);
      for (let i = 0; i < 48; i++) {
        const j = (i + 1) % 48;
        t.quad([lo[i][0], lo[i][1], z0], [lo[j][0], lo[j][1], z0], [hi[j][0], hi[j][1], z1], [hi[i][0], hi[i][1], z1]);
        t.tri([0, 0, z0], [lo[j][0], lo[j][1], z0], [lo[i][0], lo[i][1], z0]);
        t.tri([0, 0, z1], [hi[i][0], hi[i][1], z1], [hi[j][0], hi[j][1], z1]);
      }
    } else if (id === 'dish') {
      extrudeConvex(t, circleLoop(0, 0, r, 48), z0, z1);
      const lp = circleLoop(0, 0, r * 0.8, 48);
      for (let i = 0; i < 48; i++) {
        const j = (i + 1) % 48;
        t.tri([0, 0, z1 - 0.9], [lp[j][0], lp[j][1], z1], [lp[i][0], lp[i][1], z1]);
      }
    } else if (id === 'dome') {
      extrudeConvex(t, circleLoop(0, 0, r, 48), z0, z1 - 2.2);
      const rings = 6;
      for (let s = 0; s < rings; s++) {
        const a0 = (Math.PI / 2) * (s / rings), a1 = (Math.PI / 2) * ((s + 1) / rings);
        const l0 = circleLoop(0, 0, r * Math.cos(a0), 48), l1 = circleLoop(0, 0, r * Math.cos(a1), 48);
        const h0 = z1 - 2.2 + 2.2 * Math.sin(a0), h1 = z1 - 2.2 + 2.2 * Math.sin(a1);
        for (let i = 0; i < 48; i++) {
          const j = (i + 1) % 48;
          t.quad([l0[i][0], l0[i][1], h0], [l0[j][0], l0[j][1], h0], [l1[j][0], l1[j][1], h1], [l1[i][0], l1[i][1], h1]);
        }
      }
    } else {
      extrudeConvex(t, circleLoop(0, 0, r, 24), z0, z1);
    }
    emit(OUT, `stick_cap_${id}.glb`, [{ name: 'body', t }]);
  }
}

/* --- site-owned asset 1/3: the MX switch stand-in --------------------
   MX switches are user-supplied, so no release file exists and the catalog
   has no entry. The viewer ships this stand-in so the deck is not bare with
   keycaps off — and so the caps SEAT correctly when they are on.

   PROPORTIONS ARE THE CHERRY MX DATUM CHAIN, not an invention. Source:
   hardware/case/keycaps/keycaps.py — the dimension chain at :149-153
   ("5.0 PCB top -> plate top == our DECK", "11.6 PCB top -> the 11.6 datum",
   "3.6 that datum -> the stem top"), the measured elevation at :160-165, the
   seating fact at :183-190 ("The cap seats with its socket mouth flat on that
   shoulder at h = 6.60, and ABOVE THAT PLANE THE ONLY SWITCH MATERIAL IS THE
   3.60 mm CROSS -- which lives inside the socket"), and the named constants
   at :289-298 / :327-329.

     h above deck   what                          z (deck = 5.0)
     -0.35 .. 0.75  plate-mount lip, 15.60 sq      4.65 .. 5.75
      0.75 .. 5.70  housing tapers 14.24 -> 10.12  5.75 .. 10.70
      5.70 .. 6.01  fixed housing top face, 9.17  10.70 .. 11.01
      6.01 .. 6.60  stem shoulder 6.44 -> 5.80    11.01 .. 11.60  <- CAP SEAT
      6.60 .. 10.20 the exposed 4.00 cross        11.60 .. 15.20

   So the cross stands 3.60 mm ABOVE the cap's bottom rim: the stem is INSIDE
   the cap, overlapping it by 3.60 of the cap's 6.00 mm height, and the fixed
   housing stops 0.59 mm below the rim. The previous stand-in ended a Ø7
   cylinder exactly AT the seat, which is why the caps read as stacked on top.

   Three named parts so the geometry is assertable from the .glb itself.
   Instance mesh, absolute z, symmetric about its local x/y origin. */
{
  const housing = new Tris();
  loftLoops(housing, squareLoop(0, 0, SW_BOTTOM_SQ), 0,
                     squareLoop(0, 0, SW_BOTTOM_SQ), SW_LIP_Z0, { capBottom: true });
  loftLoops(housing, squareLoop(0, 0, SW_LIP_SQ), SW_LIP_Z0,
                     squareLoop(0, 0, SW_LIP_SQ), SW_LIP_Z1);
  loftLoops(housing, squareLoop(0, 0, 14.24), SW_LIP_Z1,
                     squareLoop(0, 0, 10.12), SW_TAPER_Z1);
  loftLoops(housing, squareLoop(0, 0, 10.12), SW_TAPER_Z1,
                     squareLoop(0, 0, SW_HOUSING_TOP_SQ), SW_HOUSING_TOP_Z, { capTop: true });

  const shoulder = new Tris();
  loftLoops(shoulder, squareLoop(0, 0, SW_WELL), SW_HOUSING_TOP_Z,
                      squareLoop(0, 0, SW_COLLAR_SQ), SW_SEAT_Z, { capTop: true });

  const stem = new Tris();
  const hl = SW_CROSS_L / 2;
  boxTris(stem, -hl, hl, -SW_CROSS_W_WIDE / 2, SW_CROSS_W_WIDE / 2, SW_SEAT_Z, SW_STEM_TOP_Z);
  boxTris(stem, -SW_CROSS_W_NARROW / 2, SW_CROSS_W_NARROW / 2, -hl, hl, SW_SEAT_Z, SW_STEM_TOP_Z);

  emit(ASSETS, 'switch_mx.glb', [
    { name: 'housing', t: housing }, { name: 'shoulder', t: shoulder }, { name: 'stem', t: stem },
  ]);
}

/* --- site-owned asset 2/3: the 2u plate-mount stabiliser -------------
   VIEW ONLY. The stabiliser is never a configuration axis — it is one
   self-buy line that follows the keycaps — but with the caps off the 2u key
   looked unsupported, so the "Show" group can put it on the deck.

   BAKED, not an instance: the stabiliser is a fixed pair of inserts either
   side of SW13 and its wire is deliberately NOT symmetric in y, so baking the
   absolute board-frame position (positions.json `stabilizer`: slot centres
   (30.162, 89.47) and (54.038, 89.47) — half spacing 11.938 about x 42.1 —
   and the published plate slot size 6.65 x 12.3) is both simpler and safer
   than relying on a bounding-box recentre. Simplified stand-in: real inserts
   have a wire channel and a return; these are two posts and a wire. */
{
  const t = new Tris();
  const [sx, sy] = STAB_XY;
  const [slotW, slotH] = STAB_SLOT;
  const wireY = sy - STAB_WIRE_REACH;                    // toward the key rows
  for (const dx of [-STAB_HALF, STAB_HALF]) {
    const x = sx + dx;
    const insert = [[x - slotW / 2, sy - slotH / 2], [x + slotW / 2, sy - slotH / 2],
                    [x + slotW / 2, sy + slotH / 2], [x - slotW / 2, sy + slotH / 2]];
    loftLoops(t, insert, 1.2, insert, Z_DECK, { capBottom: true, capTop: true });
    extrudeConvex(t, squareLoop(x, sy, 4.6), Z_DECK, KEYCAP_SEAT_Z);
    rod(t, [x, sy, STAB_WIRE_Z], [x, wireY, STAB_WIRE_Z], STAB_WIRE_D / 2);
  }
  rod(t, [sx - STAB_HALF, wireY, STAB_WIRE_Z], [sx + STAB_HALF, wireY, STAB_WIRE_Z], STAB_WIRE_D / 2);
  emit(ASSETS, 'stabilizer_2u.glb', [{ name: 'body', t }]);
}

/* --- site-owned asset 3/3: the M3 corner bolt ------------------------
   Four of these are REAL and always on the deck — release/HOW-TO-ORDER.md
   parts list: "M3x8 button-head screws (4)", driven last in the stack step.
   ISO 7380 button head, so a low dome with a hex socket, NOT a cap screw:
   head Ø5.70, head height 1.80 seated on the plate top (deck 5.0 -> 6.8),
   hex socket 2.0 across flats. The dome is the sphere R = 3.0 centred at
   z = 4.064 that passes through (r 2.85, z 5.0) and (r 1.21, z 6.8), so the
   crown lands exactly on the published head-top height with material left for
   the socket. Shank Ø3.0 down to the M3x8 tip.

   Instance mesh, absolute z, symmetric: the viewer places it at the plate's
   corner screw positions. */
{
  const t = new Tris();
  extrudeConvex(t, circleLoop(0, 0, M3_SHANK_D / 2, 20), M3_TIP_Z, Z_DECK);
  const R = 3.0, rings = 5;
  const zc = Z_DECK - Math.sqrt(R * R - (M3_HEAD_D / 2) ** 2);      // 4.064
  const rAt = (z) => Math.sqrt(Math.max(R * R - (z - zc) * (z - zc), 0));
  for (let i = 0; i < rings; i++) {
    const z0 = Z_DECK + (M3_HEAD_H * i) / rings, z1 = Z_DECK + (M3_HEAD_H * (i + 1)) / rings;
    loftLoops(t, circleLoop(0, 0, rAt(z0), 24), z0, circleLoop(0, 0, rAt(z1), 24), z1,
      { capBottom: i === 0 });
  }
  /* The crown: a flat annulus from the truncated dome down to the hex mouth,
     then the socket itself. The hexagon is resampled to 24 points so both are
     plain quad strips, and the socket loop is REVERSED so its walls face in
     and its floor faces up — a recess, not a plug. */
  const crownZ = Z_DECK + M3_HEAD_H;
  const corners = hexLoop(0, 0, M3_HEX_AF);
  const hex = [];
  for (let e = 0; e < 6; e++) {
    const a = corners[e], b = corners[(e + 1) % 6];
    for (let k = 0; k < 4; k++) hex.push([a[0] + ((b[0] - a[0]) * k) / 4, a[1] + ((b[1] - a[1]) * k) / 4]);
  }
  const crown = circleLoop(0, 0, rAt(crownZ), 24);
  for (let i = 0; i < 24; i++) {
    const j = (i + 1) % 24;
    t.quad([crown[i][0], crown[i][1], crownZ], [crown[j][0], crown[j][1], crownZ],
           [hex[j][0], hex[j][1], crownZ], [hex[i][0], hex[i][1], crownZ]);
  }
  const socket = hex.slice().reverse();
  loftLoops(t, socket, crownZ - M3_HEX_DEPTH, socket, crownZ, { capBottom: true });
  emit(ASSETS, 'screw_m3.glb', [{ name: 'body', t }]);
}

/* --- site-owned asset 4/5: the Alps EC11E rotary encoder --------------
   Round 4, verbatim: "the configurator still doesn't show the encoder or
   joystick itself, just the toppers." The encoder is a self-buy THT part, so
   the release ships no file for it and the catalog has no entry — the site
   owns the stand-in, exactly as it does for the MX switch.

   THE DIMENSION CHAIN, z = 0 at the PCB top face, deck at +5.0:

     z              what                                        source
     0.00 ..  4.50  body 13.4 (board x) x 12.5 (board y)        [1]
     4.50 .. 11.50  threaded bushing Ø7.0, 7.0 long             [1]
    11.50 .. 14.50  Ø6.0 shaft, full round                      [1][2]
    14.50 .. 22.00  Ø6.0 shaft with the D-flat, across-flat 4.5 [1][2][3][4]

   [1] the Alps EC11E drawing: body 4.5 tall, the bushing 7.0 long above it,
       and the physical shaft tip at +24.5.
   [2] research/04-mechanical-case-dossier.md §1C, CONFIRMED against the Alps
       datasheet pp.163-168 / drawing No. 4-5: "Vertical PCB-mount (EC11E) ...
       overall to shaft tip 24.5 mm (20 mm-class flat shaft)" and "Shaft ⌀6 mm
       metal, flat (D-cut) leaves 4.5 mm across the flat".
   [3] hardware/pcb/.../hand_solder_afterlist.csv: RE1 is
       RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm, Bourns PEC11R-4215F-S0024
       — the H20mm/20mm-class flat shaft this chain is built on.
   [4] viewer-only owner ruling, 2026-08-21: shorten the visible bare stem by
       2.5 mm. The configurator therefore stops at +22.0; this does not alter
       the encoder specification, printed knobs, case CAD, or order sheet.

   Two envelopes in the CASE model differ from the numbers above and that is
   deliberate, not an oversight: agentpad13_case_v2.py carries ENC_BODY_SQ =
   11.7 and ENC_BODY_H = 7.5, which is the metal can plus keep-out margin. This
   mesh is the part as drawn (base plate incl. the ±5.6 mounting tabs, hence
   13.4 across x), so it is wider and shorter than the can-only keep-out. The
   plate opening is x 7.025..21.025 / y 6.000..19.000, so 0.2 mm of the body's
   west edge sits UNDER the plate slab — buried inside opaque material at
   z 3.4..4.5, invisible from every angle this viewer offers.

   This stand-in is intentionally a cosmetic viewer model. The 2.5 mm owner
   adjustment applies only when the knob is hidden and the bare encoder is
   visible; fit-critical knob geometry remains sourced from the real shaft.

   Instance mesh, absolute z, symmetric about RE1's shaft (13.525, 12.5), so
   the viewer's bounding-box recentre lands it correctly. Two named parts, so
   the geometry is assertable straight out of the .glb. */
{
  const ENC_BODY_X = 13.4, ENC_BODY_Y = 12.5, ENC_BODY_Z1 = 4.5;
  const ENC_BUSH_D = 7.0, ENC_BUSH_Z1 = 11.5;
  const ENC_SHAFT_D = 6.0, ENC_SHAFT_TIP = 22.0;
  const ENC_FLAT_AF = 4.5, ENC_FLAT_LEN = 7.5;

  const can = new Tris();
  boxTris(can, -ENC_BODY_X / 2, ENC_BODY_X / 2, -ENC_BODY_Y / 2, ENC_BODY_Y / 2, 0, ENC_BODY_Z1);

  const shaft = new Tris();
  extrudeConvex(shaft, circleLoop(0, 0, ENC_BUSH_D / 2, 32), ENC_BODY_Z1, ENC_BUSH_Z1);
  const flatZ0 = ENC_SHAFT_TIP - ENC_FLAT_LEN;
  extrudeConvex(shaft, circleLoop(0, 0, ENC_SHAFT_D / 2, 32), ENC_BUSH_Z1, flatZ0);
  extrudeConvex(shaft, dShaftLoop(0, 0, ENC_SHAFT_D, ENC_FLAT_AF, 28), flatZ0, ENC_SHAFT_TIP);

  emit(ASSETS, 'encoder_ec11e.glb', [{ name: 'can', t: can }, { name: 'shaft', t: shaft }]);
}

/* --- site-owned asset 5/5: the YTL YA13 thumbstick --------------------
   Same story as the encoder: JS1 is a YTL YA13-FL7.4-B5Ka (LCSC C37323742) THT
   tilt joystick the builder buys, so no release file exists.

   PLAN — every number is agentpad13_case_v2.py's v2.4 YA13 block, which cites
   the v5_6 F.Fab bbox and the height-extraction report:

     JS_FRAME_HALF = 6.5   the 13 x 13 frame
     JS_WN_EXTENT  = 10.5  "F.Fab bbox 9.3 + tab lobes to 10.5"  <- 9.3 here
     JS_ES_EXTENT  = 7.4   "F.Fab bbox local -7.4"
     JS_POT_HALF   = 4.5   pot-box / edge-tab half width
     JS_BODY_Z1    = 11.1  full body/pot-box height above PCB top

   So the part is 16.7 x 16.7 overall (9.3 + 7.4) and ASYMMETRIC about the
   stick: the two potentiometer boxes are on the WEST and NORTH faces. That is
   the CPL's rot 180 —  cpl_translucent.csv row JS1 is
   (69.710, -13.370, 180.0, top), and contract_v4.json records why: "rot180 =
   180deg-from-datasheet-datum clocking (pot boxes face West+North)". The
   clocking is baked into this geometry rather than applied as a transform,
   which is why the viewer places this one part with recentre:false.

   HEIGHTS, z = 0 at the PCB top face:
     0.0 ..  4.5   the 13 x 13 frame, plus four E/S corner retention lugs
     0.0 ..  7.2   the two pot boxes, west and north
     4.5 ..  8.2   the round upper housing Ø11.0
     8.2 .. 11.0   the central dome, crown at the body top
    10.2 .. 13.0   the stick shank emerging through the dome
    13.0 .. 18.4   the BLADE: 1.85 x 1.15 section, tip at +18.4

   The blade section and tip are consumed verbatim from the printed stick cap's
   own params (toppers/params/stick_cap_params.json "blade": {x: 1.85, y: 1.15,
   tip_z: 18.4}, socket_mouth_z 14.4, sockets.nom [1.85, 1.15]) — this IS the
   thing those caps socket onto, so it has to be the same 1.85 x 1.15 and the
   same +18.4, or the cap would not sit where the cap file says it sits. 1.85
   runs along board x, matching the socket, so the 180° clocking leaves it
   unchanged (the section is symmetric under a half turn).

   Baked at its own origin = the stick axis. Two named parts. */
{
  const JS_FRAME_HALF = 6.5, JS_FRAME_Z1 = 4.5;
  const JS_WN = 9.3, JS_ES = 7.4, JS_POT_HALF = 4.5, JS_POT_Z1 = 7.2;
  const JS_HOUSE_D = 11.0, JS_HOUSE_Z1 = 8.2, JS_DOME_Z1 = 11.0, JS_DOME_TOP_D = 4.4;
  const JS_SHANK_Z0 = 10.2, JS_SHANK_Z1 = 13.0, JS_SHANK_D0 = 4.2, JS_SHANK_D1 = 3.4;
  const JS_BLADE_X = STICK_BLADE.x, JS_BLADE_Y = STICK_BLADE.y, JS_BLADE_TIP = STICK_BLADE.tip_z;

  const frame = new Tris();
  boxTris(frame, -JS_FRAME_HALF, JS_FRAME_HALF, -JS_FRAME_HALF, JS_FRAME_HALF, 0, JS_FRAME_Z1);
  // the two pot boxes — WEST (-x) and NORTH (-y), which is the rot-180 clocking
  boxTris(frame, -JS_WN, -JS_FRAME_HALF, -JS_POT_HALF, JS_POT_HALF, 0, JS_POT_Z1);
  boxTris(frame, -JS_POT_HALF, JS_POT_HALF, -JS_WN, -JS_FRAME_HALF, 0, JS_POT_Z1);
  // and the E/S corner retention lugs that carry the bbox out to 7.4
  for (const s of [-1, 1]) {
    boxTris(frame, JS_FRAME_HALF, JS_ES, s * 3.6, s * JS_FRAME_HALF, 0, 1.4);
    boxTris(frame, s * 3.6, s * JS_FRAME_HALF, JS_FRAME_HALF, JS_ES, 0, 1.4);
  }
  extrudeConvex(frame, circleLoop(0, 0, JS_HOUSE_D / 2, 40), JS_FRAME_Z1, JS_HOUSE_Z1);
  // dome: a quarter ellipse from the housing rim to the crown
  {
    const rings = 6;
    const rAt = (f) => JS_DOME_TOP_D / 2 + (JS_HOUSE_D - JS_DOME_TOP_D) / 2 * Math.cos((f * Math.PI) / 2);
    const zAt = (f) => JS_HOUSE_Z1 + (JS_DOME_Z1 - JS_HOUSE_Z1) * Math.sin((f * Math.PI) / 2);
    for (let i = 0; i < rings; i++) {
      const f0 = i / rings, f1 = (i + 1) / rings;
      loftLoops(frame, circleLoop(0, 0, rAt(f0), 40), zAt(f0),
                       circleLoop(0, 0, rAt(f1), 40), zAt(f1), { capTop: i === rings - 1 });
    }
  }

  const stick = new Tris();
  loftLoops(stick, circleLoop(0, 0, JS_SHANK_D0 / 2, 24), JS_SHANK_Z0,
                   circleLoop(0, 0, JS_SHANK_D1 / 2, 24), JS_SHANK_Z1, { capBottom: true });
  boxTris(stick, -JS_BLADE_X / 2, JS_BLADE_X / 2, -JS_BLADE_Y / 2, JS_BLADE_Y / 2,
          JS_SHANK_Z1, JS_BLADE_TIP);

  emit(ASSETS, 'joystick_ya13.glb', [{ name: 'frame', t: frame }, { name: 'stick', t: stick }]);
}

console.log(`wrote ${written.length} stub meshes`);
for (const w of written) console.log(`  ${w.file.split('/site/')[1]}  ${w.tris} tris`);
console.log(`keycap seat z = ${KEYCAP_SEAT_Z} (caps are emitted 0..${CAP_H} and placed at the seat)`);
console.log(`MX stem: shoulder top ${SW_SEAT_Z} == the seat, cross top ${SW_STEM_TOP_Z}` +
  ` -> the stem stands ${(SW_STEM_TOP_Z - KEYCAP_SEAT_Z).toFixed(2)} mm INSIDE a ${CAP_H} mm cap`);
console.log(`EC11E module: instance, symmetric on RE1 shaft (${ENC_SHAFT}); viewer shaft tip +22.0` +
  ` (owner-set cosmetic reduction of 2.5 mm from the physical +24.5)`);
console.log(`YA13 module: instance at JS1 (${STICK}), pot boxes WEST+NORTH = CPL rot 180;` +
  ` 16.7 x 16.7 overall about the stick, blade ${STICK_BLADE.x} x ${STICK_BLADE.y} tip +${STICK_BLADE.tip_z}`);

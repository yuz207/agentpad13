/**
 * viewer.js — the render. three.js assembles board + plate + band + tray +
 * optional base + switches/caps/toppers and swaps material and mesh live on
 * every change.
 *
 * FRAME — this file obeys positions.json `frame` / `mesh_placement` and does
 * not invent a transform of its own:
 *
 *   Meshes are ALREADY in glTF's Y-up right-handed space. A board-frame
 *   position (x, y) with height z becomes (x, z, y) in glTF space — the
 *   determinant -1 swap that positions.json documents as the one that yields
 *   the correctly handed device. Applying a det +1 Z-up->Y-up rotation here
 *   instead would render the MIRROR IMAGE, so there is no rotation here at all.
 *
 *   baked    (board, plate, band_*, tray, base_*) carry their assembly
 *            position: add them untransformed.
 *   instance (cap_*, knob_*, stick_cap_*, the switch, encoder and joystick
 *            stand-ins) sit at their own local origin and are placed from
 *            positions.json.
 *
 * LIT is the one part of this file that is not assembly: see the LIT block for
 * why the LEDs are HDR emitters behind a bloom pass rather than self-lit
 * geometry, and why that is the only way a render reads as light.
 *
 * A tilting base (wedge, pedestal) has a FLAT desk face and a tilted mating
 * face, so the whole assembly — device and base together — rotates about the
 * world X axis until that desk face is level. That is one rotation of one
 * rigid body: nothing is mirrored, nothing is scaled.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { GAIN, BLOOM, BAND_LAMP, emissiveRGB, bandGlow, keyGlow } from './lighting.js';

const DEG = Math.PI / 180;

/** Base tilt, from release/hardware/case/v2/bases/params/agentpad13_base_params.json
 *  variants[].tilt_deg. Used only when positions.json does not carry it. */
const TILT_FALLBACK = { riser: 0, wedge: 8, pedestal: 8 };

/** The hinge a tilting base leans about: the board x axis at the NEAR/user
 *  edge. Fallback only — positions.bases.items[].hinge is authoritative. */
const HINGE_FALLBACK = { y: 103.7, z: -11.9 };

/** Five stand-ins the release does not ship a file for, so the site owns them:
 *  the user-supplied MX switch, the user-supplied 2u stabiliser, the M3 button
 *  head (a fastener, not a part of ours), and — round 4, "the configurator
 *  still doesn't show the encoder or joystick itself, just the toppers" — the
 *  two THT modules the toppers sit on. */
const SWITCH_MESH = 'assets/switch_mx.glb';
const STAB_MESH = 'assets/stabilizer_2u.glb';
const SCREW_MESH = 'assets/screw_m3.glb';
const ENCODER_MESH = 'assets/encoder_ec11e.glb';
const JOYSTICK_MESH = 'assets/joystick_ya13.glb';

/** ISO 7380 M3 button head, Ø5.70. Only used by the screw-position FALLBACK. */
const M3_HEAD_R = 2.85;

export function createViewer({ canvas, data, meshBase }) {
  const { catalog, positions, finishes } = data;
  const [CX, CY] = positions.band?.center || positions.plate?.center || [42.1, 50];

  /* --- renderer / scene ------------------------------------------------ */
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.toneMapping = THREE.NeutralToneMapping ?? THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(32, 1, 1, 4000);
  camera.position.set(120, 140, 210);

  const key = new THREE.DirectionalLight(0xffffff, 1.5);
  key.position.set(120, 230, -90);   // high and slightly behind: the contact shadow spills toward the camera, clear of the body
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.0012;
  const sc = key.shadow.camera;
  sc.left = -140; sc.right = 140; sc.top = 140; sc.bottom = -140; sc.near = 40; sc.far = 600;
  sc.updateProjectionMatrix();                 // the ortho frustum is stale without this
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.35);
  fillLight.position.set(-160, 90, -120);
  scene.add(key, fillLight);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.ShadowMaterial({ opacity: 0.28 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  /* Two groups, one job: `tilt` is the HINGE, `deck` carries the board datum.
     A base leans the whole device about the hinge line — the board x axis at
     the NEAR/user edge (positions.bases.items[].hinge, y = 103.7) — so the
     far/USB edge rises and the near edge stays down on the desk. Rotating
     about the group origin instead would lift the near edge off the desk and
     put the whole assembly at the wrong height. `tilt` is therefore parked ON
     the hinge and `deck` is offset so board coordinates land correctly. */
  const tilt = new THREE.Group();
  const deck = new THREE.Group();
  scene.add(tilt); tilt.add(deck);

  /** Park the pivot on the hinge line: world (Y = hinge z, Z = hinge y - CY). */
  function setHinge(hy, hz) {
    tilt.position.set(0, hz, hy - CY);
    deck.position.set(-CX, -hz, -hy);
  }
  setHinge(CY, 0);                              // no base: pivot is moot, tilt is 0

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.075;
  controls.minDistance = 120;
  controls.maxDistance = 620;
  controls.minPolarAngle = 0.15;
  controls.maxPolarAngle = Math.PI / 2 - 0.04;

  /* --- moving the whole render ------------------------------------------
     Left drag orbits, RIGHT drag pans, two fingers pan (touch), and on a
     trackpad a two-finger drag pans while a pinch zooms. Screen-space panning
     so the device tracks the cursor instead of sliding along the ground.
     Double-click re-centres. Panning is BOUNDED to a radius around the
     assembly, so the device can never be lost off-screen. */
  controls.enablePan = true;
  controls.screenSpacePanning = true;
  controls.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };
  controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
  canvas.addEventListener('contextmenu', (e) => e.preventDefault());

  const home = new THREE.Vector3();
  let panLimit = Infinity;
  const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3();

  /** Screen-space pan by a pixel delta — OrbitControls' own panLeft/panUp
   *  maths, reused because it keeps no public pan() to call. */
  function panByPixels(dx, dy) {
    const dist = _a.copy(camera.position).sub(controls.target).length();
    const h = canvas.clientHeight || canvas.height || 1;
    const k = (2 * dist * Math.tan((camera.fov / 2) * DEG)) / h;
    const move = _b.setFromMatrixColumn(camera.matrix, 0).multiplyScalar(-dx * k)
      .add(_c.setFromMatrixColumn(camera.matrix, 1).multiplyScalar(dy * k));
    camera.position.add(move);
    controls.target.add(move);
    mark();
  }

  /** Pull the view back if a pan has pushed the target past the bound. Camera
   *  and target move together, so the framing is unchanged — it just stops. */
  function clampPan() {
    const off = _a.copy(controls.target).sub(home);
    const r = off.length();
    if (!(r > panLimit)) return;
    off.setLength(r - panLimit);
    controls.target.sub(off);
    camera.position.sub(off);
  }

  /* A mouse wheel is a zoom (OrbitControls' default). A trackpad two-finger
     drag arrives as a wheel event too, so it is separated by signature —
     fractional or small deltas, or any horizontal component — and panned
     instead. A pinch arrives with ctrlKey and always zooms. The listener sits
     on the stage in the CAPTURE phase so it can stop the event reaching the
     controls' own wheel handler on the canvas. */
  const isTrackpadPan = (e) => !e.ctrlKey && !e.metaKey && e.deltaMode === 0
    && (e.deltaX !== 0 || !Number.isInteger(e.deltaY) || Math.abs(e.deltaY) < 40);
  (canvas.parentElement || canvas).addEventListener('wheel', (e) => {
    if (!isTrackpadPan(e)) return;                 // let the controls dolly
    e.preventDefault();
    e.stopPropagation();
    panByPixels(-e.deltaX, e.deltaY);
    clampPan();
  }, { capture: true, passive: false });

  canvas.addEventListener('dblclick', () => {
    const off = _a.copy(camera.position).sub(controls.target);   // keep eye direction + distance
    controls.target.copy(home);
    camera.position.copy(home).add(off);
    controls.update();
    mark();
  });

  /* --- materials, cached per (finish, translucency) ---------------------
   * COLOUR and TRANSLUCENCY are independent axes (finishes.json _palette):
   * every palette entry is an opaque base colour, and a part's own
   * translucency checkbox decides whether that colour is rendered solid or
   * through the ONE frosted treatment finishes.translucent describes.
   * Transmitted light is tinted by the material colour, so the same treatment
   * reads as frosted glass under a pale colour and as smoke under a dark one —
   * which is exactly why the palette needs no translucent entries of its own.
   *
   * Round 4 made that treatment FROSTED rather than glassy ("transparent should
   * be translucent -- and it should be more opaque than this... Not opaque but
   * a little more so"). The number that does the work is ROUGHNESS: three.js
   * blurs the transmitted image by it, so a rough transmissive band scatters
   * the LED ribbon behind it into a broad wash instead of showing it as a
   * readable hard line. All of it is data — finishes.translucent. */
  const matCache = new Map();
  const finishById = new Map((finishes.finishes || []).map((f) => [f.id, f]));
  const maskById = new Map((finishes.masks || []).map((m) => [m.id, m]));

  /** FALLBACK ONLY — finishes.translucent is authoritative. */
  const FROST_FALLBACK = { transmission: 0.78, thickness: 3.2, ior: 1.5, roughness: 0.55, clearcoat: 0.35, clearcoat_roughness: 0.28 };
  const frostSpec = () => finishes.translucent || FROST_FALLBACK;

  /** The frosted translucent treatment as three.js material options. */
  function frostOpts() {
    const t = frostSpec();
    return {
      metalness: 0,
      roughness: t.roughness ?? 0.55,
      transmission: t.transmission ?? 0.78,
      thickness: t.thickness ?? 3.2,
      ior: t.ior ?? 1.5,
      clearcoat: t.clearcoat ?? 0.35,
      clearcoatRoughness: t.clearcoat_roughness ?? 0.28,
    };
  }

  function finishMaterial(id, translucent) {
    const key = `f:${id}:${translucent ? 'frost' : 'solid'}`;
    const cached = matCache.get(key);
    if (cached) return cached;
    const f = finishById.get(id) || { hex: '#888888', roughness: 0.7 };
    const color = new THREE.Color(f.hex);
    const m = translucent
      ? new THREE.MeshPhysicalMaterial({ color, ...frostOpts() })
      : new THREE.MeshStandardMaterial({ color, roughness: f.roughness ?? 0.7, metalness: 0.02 });
    m.userData.transmissive = (m.transmission || 0) > 0.5;
    matCache.set(key, m);
    return m;
  }

  function maskMaterial(id) {
    const cached = matCache.get(`m:${id}`);
    if (cached) return cached;
    const src = maskById.get(id) || { hex: '#16181A' };
    const m = new THREE.MeshStandardMaterial({ color: new THREE.Color(src.hex), roughness: 0.55, metalness: 0.08 });
    matCache.set(`m:${id}`, m);
    return m;
  }

  /** Fasteners are hardware, not a finish: black oxide, always the same. */
  function hardwareMaterial() {
    if (!matCache.has('hw')) {
      matCache.set('hw', new THREE.MeshStandardMaterial({ color: 0x17191B, roughness: 0.36, metalness: 0.82 }));
    }
    return matCache.get('hw');
  }

  /**
   * The THT modules are bought parts, so like the fasteners they get a FIXED
   * look and never a palette colour: you cannot choose the finish of an EC11E.
   * Keyed by the .glb part name, so the mesh itself says which material each
   * piece of it wants.
   *
   *   can      the EC11E's nickel-plated steel body          bright satin steel
   *   shaft    the bushing + the Ø6 D-shaft                  brighter chrome
   *   frame    the YA13 body, pot boxes and dome             dark grey nylon
   *   stick    the YA13 shank and blade                      the same, a shade up
   *
   * The YA13 grey is lifted a little off the true black of the part: against a
   * black soldermask plate a jet-black module simply disappears, and a module
   * you cannot see is the round-4 complaint all over again.
   */
  const MODULE_MATERIALS = {
    can: { color: 0xBFC4C9, roughness: 0.30, metalness: 0.88 },
    shaft: { color: 0xD4D8DC, roughness: 0.18, metalness: 0.94 },
    frame: { color: 0x34383E, roughness: 0.52, metalness: 0.05 },
    stick: { color: 0x42474E, roughness: 0.44, metalness: 0.05 },
  };
  function moduleMaterial(kind) {
    const key = `mod:${kind}`;
    if (!matCache.has(key)) {
      matCache.set(key, new THREE.MeshStandardMaterial(MODULE_MATERIALS[kind] || MODULE_MATERIALS.frame));
    }
    return matCache.get(key);
  }

  /* --- plate art --------------------------------------------------------
   * The plate is the one part with PRINTED DESIGN on it, and the three
   * variants differ only in that art. The pipeline publishes it in LAYERS,
   * and this composites them onto one canvas per (variant, colour):
   *
   *   1. GROUND — ours at runtime, because it is the user's choice: the fab
   *      mask colour on the FR4 path, the palette colour on the printed one.
   *   2. OPENINGS — catalog.plate.openings_map, one shared RGBA that is
   *      opaque where the plate is material and transparent where the fab
   *      routes. Punched into the ground with destination-in and consumed as
   *      alphaTest (not blending), so depth and shadows stay correct.
   *   3. DECAL — the per-variant marker over TP5: standard = the Ø12 exposed
   *      ENIG disc, tented_ring = the Ø16 white silk ring, blank = null,
   *      markerless BY DESIGN (no copper at all), not a missing file.
   *
   * FRAME, per openings_map.note: image ROW 0 is board y = 0, the FAR / USB
   * edge; image COLUMN 0 is board x = extent.x0. ensurePlanarUV() flips v to
   * match, so a texture and a mm coordinate mean the same thing here.
   *
   * Every layer is optional. With no images published, the marker is DRAWN
   * from positions.touch_pad — same geometry, same three variants — so the
   * plate still reads correctly against an older build/out.
   */

  /** FALLBACK ONLY — superseded the moment positions.touch_pad exists. */
  const TOUCH_FALLBACK = {
    x: 13.525, y: 88.85, exposed_pad_d: 12.0, ring_d: 16.0,
    variants: {
      standard: { marker: 'exposed_pad', exposed_d: 12.0 },
      tented_ring: { marker: 'silk_ring', ring_d: 16.0, ring_stroke: 0.2 },
      blank: { marker: 'none' },
    },
  };

  /** Find a published image on a catalog node by CONCEPT, not by a guessed
   *  spelling — key names are the pipeline's to choose, not ours to assume.
   *  A node may also carry it as {path: "..."} alongside its metadata. */
  const imageKey = (obj, re) => {
    if (!obj) return null;
    const isImg = (v) => typeof v === 'string' && /\.(png|webp|jpe?g|avif)$/i.test(v);
    for (const [k, v] of Object.entries(obj)) {
      if (!re.test(k)) continue;
      if (isImg(v)) return v;
      if (v && typeof v === 'object' && isImg(v.path)) return v.path;
    }
    return null;
  };

  const imgCache = new Map();
  function loadImage(rel) {
    const url = meshUrl(rel);
    if (!imgCache.has(url)) {
      imgCache.set(url, new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(url));
        img.src = url;
      }));
    }
    return imgCache.get(url);
  }

  /** The plate's mm rect in the board frame, for both the canvas and the UVs.
   *  The published extent wins — it is what the textures were rendered at. */
  const plateRect = () => {
    const ex = (catalog.plate.openings_map || {}).extent_mm;
    if (ex) return { x0: ex.x0, y0: ex.y0, w: ex.x1 - ex.x0, h: ex.y1 - ex.y0 };
    const pl = positions.plate || {};
    const [w, h] = pl.size || catalog.plate.size_mm || [84.4, 100];
    const [cx, cy] = pl.center || [42.1, 50];
    return { x0: cx - w / 2, y0: cy - h / 2, w, h };
  };

  /** Planar UVs from world x/z — the plate is flat and baked in board coords,
   *  so the projection is exact and works for stub and shipped meshes alike.
   *  v is flipped because flipY puts uv v = 1 on image ROW 0, and row 0 is
   *  board y0 (openings_map.note). */
  function ensurePlanarUV(geometry, rect) {
    if (geometry.getAttribute('uv') || geometry.userData.planarUV) return;
    const pos = geometry.getAttribute('position');
    const uv = new Float32Array(pos.count * 2);
    for (let i = 0; i < pos.count; i++) {
      uv[i * 2] = (pos.getX(i) - rect.x0) / rect.w;
      uv[i * 2 + 1] = 1 - (pos.getZ(i) - rect.y0) / rect.h;   // glTF Z is board y
    }
    geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geometry.userData.planarUV = true;
  }

  /**
   * Composite the plate map. Repaints in place as each published layer
   * arrives; `onOpenings` fires once the routed areas are really cut out.
   */
  function plateCanvas(variant, groundHex, onOpenings) {
    const rect = plateRect();
    const size = (catalog.plate.openings_map || {}).size_px;
    const [W, H] = size || [Math.round((1024 * rect.w) / rect.h), 1024];
    const cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    const tex = new THREE.CanvasTexture(cv);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 4;
    const px = (x, y) => [((x - rect.x0) / rect.w) * W, ((y - rect.y0) / rect.h) * H];
    const perMM = H / rect.h;
    const layer = { openings: null, decal: null };

    const drawMarker = (g) => {
      const tp = positions.touch_pad || TOUCH_FALLBACK;
      const spec = (tp.variants || {})[variant] || { marker: 'none' };
      const [cx, cy] = px(tp.x, tp.y);
      if (spec.marker === 'exposed_pad') {
        const d = spec.exposed_d ?? tp.exposed_pad_d ?? 12;
        g.fillStyle = '#C9A94F';                         // ENIG gold on copper
        g.beginPath(); g.arc(cx, cy, (d / 2) * perMM, 0, Math.PI * 2); g.fill();
      } else if (spec.marker === 'silk_ring') {
        const d = spec.ring_d ?? tp.ring_d ?? 16;
        g.strokeStyle = '#F2F2EE';                       // white silkscreen
        g.lineWidth = Math.max(1.5, (spec.ring_stroke ?? 0.2) * perMM);
        g.beginPath(); g.arc(cx, cy, (d / 2) * perMM, 0, Math.PI * 2); g.stroke();
      }
    };

    const paint = () => {
      const g = cv.getContext('2d');
      g.globalCompositeOperation = 'source-over';
      g.clearRect(0, 0, W, H);
      g.fillStyle = groundHex;
      g.fillRect(0, 0, W, H);
      if (layer.openings) {
        g.globalCompositeOperation = 'destination-in';   // keep material only
        g.drawImage(layer.openings, 0, 0, W, H);
        g.globalCompositeOperation = 'source-over';
      }
      if (layer.decal) g.drawImage(layer.decal, 0, 0, W, H);
      else drawMarker(g);
      tex.needsUpdate = true;
      mark();
    };

    paint();
    const openings = imageKey(catalog.plate, /opening|alpha|cutout/);
    if (openings) {
      loadImage(openings).then((img) => { layer.openings = img; paint(); onOpenings(); }).catch(() => {});
    }
    const vNode = catalog.plate.variants.find((v) => v.id === variant);
    const decal = imageKey(vNode, /decal|art|silk|marker/) || imageKey(catalog.plate, /decal|art|silk/);
    if (decal) loadImage(decal).then((img) => { layer.decal = img; paint(); }).catch(() => {});
    return tex;
  }

  /**
   * The plate material: one canvas map carrying ground colour + openings +
   * art, so a colour change is a repaint and never a second material. A
   * printed plate gets the same transparency checkbox as every other printed
   * part, and that is the only thing that changes the material class here.
   */
  function plateMaterial(variant, src, extra, transparent) {
    const key = `p:${variant}:${src.id}:${transparent ? 'clear' : 'solid'}`;
    if (matCache.has(key)) return matCache.get(key);
    const m = transparent
      ? new THREE.MeshPhysicalMaterial({ color: 0xffffff, ...clearOpts() })
      : new THREE.MeshStandardMaterial({ color: 0xffffff, ...extra });
    m.userData.transmissive = (m.transmission || 0) > 0.5;
    m.map = plateCanvas(variant, src.hex, () => {
      // The openings punched the routed areas out of the map's alpha. Discard
      // them with alphaTest rather than blending: no sort order, no shadow
      // artefacts, and the mesh's own holes stay the silhouette of record.
      m.alphaTest = 0.5;
      m.needsUpdate = true;
      mark();
    });
    matCache.set(key, m);
    return m;
  }

  /**
   * Where the four M3 bolts go. `positions.screws` is authoritative once the
   * pipeline emits it (contract: {..., positions: [[x, y], ...]}).
   *
   * FALLBACK, used until then and clearly marked as such: derive them from
   * the plate's own corner geometry in positions.json — the head is tucked
   * just inside each corner arc, so its centre sits on the corner diagonal at
   * (corner_r - head_r) from the arc centre. On the shipped plate (84.4 x 100,
   * r 5.4) that lands within 0.2 mm of the real hole centres, which is
   * invisible at any framing this viewer offers.
   */
  function screwPositions() {
    const s = positions.screws;
    const listed = s && (s.positions || s.items || (Array.isArray(s) ? s : null));
    if (listed && listed.length) {
      return listed.map((e) => (Array.isArray(e) ? [e[0], e[1]] : [e.x, e.y]));
    }
    const pl = positions.plate || {};
    const [w, h] = pl.size || catalog.plate.size_mm || [84.4, 100];
    const [cx, cy] = pl.center || [42.1, 50];
    const r = pl.corner_r ?? 5.4;
    const d = Math.max(r - M3_HEAD_R, 0) / Math.SQRT2;   // arc centre -> corner
    const out = [];
    for (const sx of [-1, 1]) {
      for (const sy of [-1, 1]) out.push([cx + sx * (w / 2 - r + d), cy + sy * (h / 2 - r + d)]);
    }
    return out;
  }

  /* --- mesh loading, cached per url ------------------------------------ */
  const loader = new GLTFLoader();
  const meshCache = new Map();

  /** Resolve a mesh reference: catalog paths are relative to the catalog. */
  const meshUrl = (rel) => (rel.startsWith('assets/') ? rel : meshBase + rel);

  function loadMesh(rel) {
    const url = meshUrl(rel);
    if (!meshCache.has(url)) {
      meshCache.set(url, new Promise((resolve, reject) => {
        loader.load(url, (gltf) => {
          const parts = [];
          gltf.scene.traverse((o) => {
            if (!o.isMesh) return;
            o.geometry.computeBoundingBox();
            // A named glTF material means the mesh brought its own look (the
            // board's texture); an unnamed default means we own the material.
            parts.push({ mesh: o, name: o.name || '', authored: Boolean(o.material && o.material.name) });
          });
          resolve(parts);
        }, undefined, reject);
      }));
    }
    return meshCache.get(url);
  }

  /* ======================================================================
   * LIT — the LEDs.  Round 4, verbatim: "It's just a hard band which is
   * ridiculous. Should really look like a diffuse glow."
   *
   * The old version put a flat self-lit strip on the board edge and called it
   * a light. It cannot work: a screen pixel stops at white, so a self-lit mesh
   * is always a WHITE SOLID with a hard silhouette, which is exactly what a
   * light does not look like. Light has no edge — it falls off.
   *
   * So this render carries the emitters in HDR (linear values well above 1.0)
   * and gets the falloff from a real BLOOM pass. Everything below exists to
   * serve that: `emissive()` guarantees a hot core clears the bloom threshold
   * whatever hue it is, the curtains carry a vertical brightness gradient so
   * the source itself has no edge, and the additive pieces put the spill where
   * light really escapes this case.
   *
   * TWO LED SETS, and they are not the same product decision:
   *
   *   BAND    ten side-firing SK6812-SIDE parts (LED15-24) on the board's
   *           UNDERSIDE, throwing outward into the band from the gap between
   *           the tray floor and the board. It exists only when you ordered the
   *           LED band AND the wall in front of it can pass light — an OPAQUE
   *           BAND EMITS NOTHING (lighting.js bandGlow, owner rule round 4).
   *   PER-KEY thirteen LEDs under the switches. Round 4: "lit means the board
   *           LEDs under the keys too!" — and they are on EVERY board, so this
   *           half is never gated on the band toggle.
   *
   * All of it is view-only: state.lighting reaches no rule and no build sheet.
   * The ENERGY BUDGET — which rung of the ladder each emitter stands on, and
   * where the bloom threshold sits between them — is lighting.js.
   */

  /* Board-frame z of each emitter, and the gain applied to the chosen colour.
     A gain over the bloom threshold is a light SOURCE; under it, a glow. The
     ribbon's rows are the vertical falloff of the source itself — the reason
     the strip no longer has a top and a bottom edge. */
  const { HOT, WARM, DIM, FAINT } = GAIN;
  const RIBBON_ROWS = [
    [-5.00, FAINT], [-4.40, DIM], [-3.80, WARM], [-3.20, HOT],
    [-2.60, WARM], [-2.00, DIM], [-1.50, FAINT],
  ];
  const RIBBON_OUT = 1.004;         // nudge off the board's own side wall

  /** The band's outer corner radius — case model OUTER_R, one number for all
   *  three wall widths (release/hardware/case/v2/agentpad13_case_v2.py). */
  const BAND_OUTER_R = 8.0;

  const WHITE = new THREE.Color(1, 1, 1);
  const _em = new THREE.Color();
  const _hue = new THREE.Color();

  /** The emitter colour at a rung of the ladder, in linear HDR. The maths is
   *  lighting.js (pure, and tested there); this only boxes it in a Color. */
  function emissive(base, gain) {
    const e = emissiveRGB(base, gain);
    return _em.setRGB(e.r, e.g, e.b);      // already linear: no conversion
  }

  /** The board outline, or the plate rectangle if this build has no octagon. */
  function boardOutline() {
    const poly = positions.pcb && positions.pcb.octagon;
    if (poly && poly.length >= 3) return poly.map(([x, y]) => [x, y]);
    const r = plateRect();
    return [[r.x0, r.y0], [r.x0 + r.w, r.y0], [r.x0 + r.w, r.y0 + r.h], [r.x0, r.y0 + r.h]];
  }

  /** A closed rounded-rect loop in board coords — the plate edge and the band
   *  outer face, which are where the seam light gets out. */
  function roundedLoop(cx, cy, w, h, r, seg = 6) {
    const hw = w / 2, hh = h / 2;
    const rr = Math.max(0, Math.min(r, hw, hh));
    const pts = [];
    for (const [ox, oy, a0] of [[cx + hw - rr, cy + hh - rr, 0], [cx - hw + rr, cy + hh - rr, Math.PI / 2],
                                [cx - hw + rr, cy - hh + rr, Math.PI], [cx + hw - rr, cy - hh + rr, -Math.PI / 2]]) {
      for (let i = 0; i <= seg; i++) {
        const a = a0 + (Math.PI / 2) * (i / seg);
        pts.push([ox + rr * Math.cos(a), oy + rr * Math.sin(a)]);
      }
    }
    return pts;
  }

  /** Resample a closed board-frame polygon to `n` evenly spaced points, so the
   *  rainbow gradient is smooth instead of stepping at the octagon corners. */
  function resample(poly, n) {
    const seg = [];
    let total = 0;
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
      seg.push({ a, b, d, at: total });
      total += d;
    }
    const out = [];
    let s = 0;
    for (let i = 0; i < n; i++) {
      const want = (total * i) / n;
      while (s < seg.length - 1 && seg[s].at + seg[s].d <= want) s++;
      const e = seg[s];
      const f = e.d === 0 ? 0 : (want - e.at) / e.d;
      out.push([e.a[0] + (e.b[0] - e.a[0]) * f, e.a[1] + (e.b[1] - e.a[1]) * f]);
    }
    return out;
  }

  /**
   * A "curtain": a closed vertical band standing on a board-frame loop, with
   * one row of vertices per entry in `rows` ([board z, gain]). Every vertex
   * remembers (its position t around the loop, its row gain) so the colour
   * attribute can be rewritten each frame without touching the positions.
   *
   * @returns {{geometry, tint(fn)}} — tint takes (t) -> THREE.Color.
   */
  function curtain(loop, rows) {
    const n = loop.length, r = rows.length;
    const pos = new Float32Array(n * r * 3);
    const col = new Float32Array(n * r * 3);
    const ts = new Float32Array(n * r);
    const gains = new Float32Array(n * r);
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < r; j++) {
        const k = i * r + j;
        pos[k * 3] = loop[i][0];               // glTF x  = board x
        pos[k * 3 + 1] = rows[j][0];           // glTF y  = board z (height)
        pos[k * 3 + 2] = loop[i][1];           // glTF z  = board y
        ts[k] = i / n;
        gains[k] = rows[j][1];
      }
    }
    const idx = [];
    for (let i = 0; i < n; i++) {
      const i2 = (i + 1) % n;
      for (let j = 0; j < r - 1; j++) {
        const a = i * r + j, b = i * r + j + 1, c = i2 * r + j + 1, d = i2 * r + j;
        idx.push(a, b, c, a, c, d);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeBoundingSphere();
    return {
      geometry: g,
      tint(hueAt) {
        for (let k = 0; k < ts.length; k++) {
          const e = emissive(hueAt(ts[k]), gains[k]);
          col[k * 3] = e.r; col[k * 3 + 1] = e.g; col[k * 3 + 2] = e.b;
        }
        g.getAttribute('color').needsUpdate = true;
      },
    };
  }

  /**
   * A closed horizontal RIBBON between two loops of the same length at one
   * height — the seam annulus at the deck and the pool on the desk. `gains`
   * is [inner, outer], and the outer edge is normally 0: that zero IS the
   * falloff, and it is why the spill has no rim.
   */
  function annulus(inner, outer, y, gains) {
    const n = inner.length;
    const pos = new Float32Array(n * 2 * 3);
    const col = new Float32Array(n * 2 * 3);
    const ts = new Float32Array(n * 2);
    const gs = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) {
      for (const [j, loop] of [[0, inner], [1, outer]]) {
        const k = i * 2 + j;
        pos[k * 3] = loop[i][0]; pos[k * 3 + 1] = y; pos[k * 3 + 2] = loop[i][1];
        ts[k] = i / n;
        gs[k] = gains[j];
      }
    }
    const idx = [];
    for (let i = 0; i < n; i++) {
      const i2 = (i + 1) % n;
      idx.push(i * 2, i * 2 + 1, i2 * 2 + 1, i * 2, i2 * 2 + 1, i2 * 2);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeBoundingSphere();
    return {
      geometry: g,
      tint(hueAt) {
        for (let k = 0; k < ts.length; k++) {
          const e = emissive(hueAt(ts[k]), gs[k]);
          col[k * 3] = e.r; col[k * 3 + 1] = e.g; col[k * 3 + 2] = e.b;
        }
        g.getAttribute('color').needsUpdate = true;
      },
    };
  }

  /**
   * One geometry holding a flat disc at every key position — the per-key LED
   * seen through the switch, through a translucent cap, or through the hole
   * where the switch would be. `t` per key is its place in the rainbow spread,
   * so the grid washes with the ribbon rather than flashing as one block.
   *
   * `rings` is [[radius, gain], ...] from the middle outward. More than two
   * rings buys a CURVED falloff: a two-stop disc is a cone, and a cone has a
   * visible edge where its slope changes — which is how the desk pool first
   * read as a hard oval rather than as light.
   */
  function keyDiscs(keys, y, rings, seg = 20) {
    const nr = rings.length;
    const per = seg * nr;
    const pos = new Float32Array(keys.length * per * 3);
    const col = new Float32Array(keys.length * per * 3);
    const ts = new Float32Array(keys.length * per);
    const gs = new Float32Array(keys.length * per);
    const idx = [];
    keys.forEach((k, ki) => {
      const b = ki * per;
      for (let i = 0; i < seg; i++) {
        const a = (2 * Math.PI * i) / seg;
        for (let j = 0; j < nr; j++) {
          const v = b + i * nr + j;
          pos[v * 3] = k.x + rings[j][0] * Math.cos(a);
          pos[v * 3 + 1] = y;
          pos[v * 3 + 2] = k.y + rings[j][0] * Math.sin(a);
          ts[v] = k.t;
          gs[v] = rings[j][1];
        }
      }
      for (let i = 0; i < seg; i++) {
        const i2 = (i + 1) % seg;
        for (let j = 0; j < nr - 1; j++) {
          const a = b + i * nr + j, c = b + i2 * nr + j;
          idx.push(a, a + 1, c + 1, a, c + 1, c);
        }
      }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeBoundingSphere();
    return {
      geometry: g,
      tint(hueAt) {
        for (let k = 0; k < ts.length; k++) {
          const e = emissive(hueAt(ts[k]), gs[k]);
          col[k * 3] = e.r; col[k * 3 + 1] = e.g; col[k * 3 + 2] = e.b;
        }
        g.getAttribute('color').needsUpdate = true;
      },
    };
  }

  /* Two material classes, and the split is not cosmetic — it is what three.js
     will and will not show through a transmissive surface.

     SOURCE   opaque. Three.js renders the transmission back-buffer from the
              OPAQUE objects only, so ONLY an opaque emitter is visible through
              the frosted band and through a translucent keycap. The ribbon and
              the key discs are therefore opaque, and the band's own roughness
              is what scatters them into a wash.
     SPILL    additive, depth-tested but not depth-writing. Light landing ON a
              surface — the deck seam, the skirt at the tray gap, the pool on
              the desk. Additive never darkens, so it reads as light rather
              than as a decal. */
  const sourceMaterial = () => new THREE.MeshBasicMaterial({
    vertexColors: true, side: THREE.DoubleSide,
  });
  /* The blend is CUSTOM, not THREE.AdditiveBlending, for one reason: this
     canvas is alpha:true and premultiplied, so the page's own ground shows
     through it. Plain additive adds to the ALPHA channel as well as to the
     colour, and a wide dim spill over empty background therefore raised alpha
     while adding almost no colour — which composites as BLACK and drew a dark
     oval on the desk. Adding colour while leaving destination alpha alone
     (blendSrcAlpha Zero, blendDstAlpha One) makes the spill genuinely additive
     over the page in both themes. */
  const spillMaterial = () => new THREE.MeshBasicMaterial({
    vertexColors: true, side: THREE.DoubleSide, transparent: true, depthWrite: false,
    blending: THREE.CustomBlending,
    blendEquation: THREE.AddEquation, blendSrc: THREE.SrcAlphaFactor, blendDst: THREE.OneFactor,
    blendEquationAlpha: THREE.AddEquation, blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneFactor,
  });

  /* --- the lit rig ----------------------------------------------------- */

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const lit = new THREE.Group();          // everything self-lit, inside `deck`
  lit.visible = false;
  deck.add(lit);
  /* No desk pool: owner ruling — reflected light on the desk is invented
     physics ("the reflection of the glow is wack and makes no sense"), and
     with a base the desk is not even the surface under the band. */

  let tinters = [];                       // every piece that follows the colour
  let litSig = '';                        // what the current rig was built for
  let litColor = new THREE.Color('#FFF3E2');
  let rainbow = false, phase = 0;
  let lightsOn = [];
  let animating = false;                  // rainbow needs a frame every frame

  /** Hue at position t (0..1) around the ribbon / across the key grid. */
  function hueAt(t) {
    if (!rainbow) return litColor;
    return _hue.setHSL((t + phase) % 1, 0.95, 0.55, THREE.SRGBColorSpace);
  }

  /** Repaint every emitter from the current colour and phase. */
  function paintLit() {
    for (const fn of tinters) fn(hueAt);
    for (const l of lightsOn) l.color.copy(hueAt(l.userData.t)).lerp(WHITE, 0.35);
  }

  /**
   * Build the rig for one (band glow, keys shown, caps shown, band width)
   * combination. Cheap enough to rebuild on change — a few thousand vertices —
   * and rebuilding is what keeps it honest: the key emitter belongs to the
   * switch when the switch is there and to the bare plate hole when it is not.
   *
   * `bandOn` is lighting.js bandGlow, NOT state.led: an opaque band builds no
   * band emitter at all, so there is nothing to hide and nothing to leak.
   */
  function buildLit(bandOn, switchesOn, capsOn, bandWidthId) {
    while (lit.children.length) lit.remove(lit.children[0]);
    tinters = [];
    lightsOn = [];

    const p = positions;
    const [cx, cy] = p.plate.center || [42.1, 50];
    const keys = p.switches.map((s) => ({
      x: s.x, y: s.y,
      // hue spread runs diagonally across the grid, so the rainbow reads as
      // one wash over the whole deck instead of thirteen unrelated dots
      t: ((s.x - cx) / 84.2 + (s.y - cy) / 100 + 1) / 2,
    }));
    const source = (d) => { lit.add(new THREE.Mesh(d.geometry, sourceMaterial())); tinters.push(d.tint); };
    const spill = (d) => { lit.add(new THREE.Mesh(d.geometry, spillMaterial())); tinters.push(d.tint); };

    /* --- per-key: on every board, band toggle or not -------------------
       Where the emitter goes depends on what is actually stacked over the
       switch, because a light has to be INSIDE the thing it lights: */
    const deckZ = p.deck_z ?? 5;
    const seat = p.keycap_seat_z ?? 11.6;
    if (!switchesOn) {
      // no switch at all: the plate opening itself is what glows
      source(keyDiscs(keys, deckZ + 0.15, [[0, HOT], [4.6, WARM], [6.2, DIM]]));
    } else {
      // out of the switch's own window, in the slot under the cap's rim
      source(keyDiscs(keys, 11.05, [[0, HOT], [2.2, HOT], [3.1, WARM]]));
      if (capsOn) {
        /* ...and a second, wider source INSIDE the cap volume. This is the one
           that matters on a translucent keycap: the frosted treatment scatters
           it through the cap body, which is the lit-keyboard look the owner
           described — a cap glowing from within, not a rim of light under it.
           Under an opaque cap it is simply hidden, which is also correct. */
        source(keyDiscs(keys, seat + 1.3, [[0, WARM * 1.4], [3.4, WARM], [5.2, DIM]]));
      }
    }
    /* ...plus the wash it throws onto the plate around each key. Additive and
       flat on the deck, so it is spill on a surface, never a glowing puck. It
       is also the ONLY thing an opaque keycap shows: a soft rim of light on the
       plate around the cap's footprint, which is what a lit board looks like
       when the cap does not pass any. Kept well under WARM for that reason —
       spill that blooms is a puck again. */
    spill(keyDiscs(keys, deckZ + 0.9, [[7.9, 0.42], [9.6, 0.18], [11.8, 0]]));

    /* --- the band: only when the wall in front of it passes light --------- */
    if (bandOn) {
      const ring = resample(boardOutline().map(([x, y]) =>
        [cx + (x - cx) * RIBBON_OUT, cy + (y - cy) * RIBBON_OUT]), 168);
      const rib = curtain(ring, RIBBON_ROWS);
      lit.add(new THREE.Mesh(rib.geometry, sourceMaterial()));
      tinters.push(rib.tint);

      /* No painted seam/skirt spill: owner ruling — one consistent glow.
         The band is lit by the ribbon inside it seen through the frost, plus
         real lights below; bloom does the diffusion. Nothing painted on. */

      /* Real lights, so the tray, the band and the modules actually respond.
         Unshadowed: this is spill, not a key. */
      const xs = ring.map((v) => v[0]), ys = ring.map((v) => v[1]);
      const [xMin, xMax] = [Math.min(...xs), Math.max(...xs)];
      const [yMin, yMax] = [Math.min(...ys), Math.max(...ys)];
      const h = -3.2;
      const spots = [[cx, yMin + 5, 0.0], [cx, yMax - 5, 0.5], [xMin + 5, cy, 0.25], [xMax - 5, cy, 0.75],
                     [xMin + 8, yMin + 8, 0.12], [xMax - 8, yMax - 8, 0.62]];
      for (const [lx, ly, t] of spots) {
        const l = new THREE.PointLight(0xffffff, BAND_LAMP.intensity, BAND_LAMP.distance, BAND_LAMP.decay);
        l.position.set(lx, h, ly);
        l.userData.t = t;
        lit.add(l);
        lightsOn.push(l);
      }
    }

  }

  /**
   * Switch the LEDs on or off and set their colour.
   * @param on        lighting.js keyGlow — the per-key half, on every board
   * @param colorId   'rainbow' or a palette finish id
   * @param bandOn    lighting.js bandGlow — the perimeter half, which needs the
   *                  LED band ordered AND a band that can pass light
   * @param capsOn    caps on the render: the emitter inside the cap volume only
   *                  exists when there is a cap volume to put it in
   */
  function setLit(on, colorId, bandOn, switchesOn, capsOn, bandWidthId) {
    lit.visible = on;
    if (!on) { animating = false; mark(); return; }
    const sig = `${bandOn}|${switchesOn}|${capsOn}|${bandWidthId}`;
    if (sig !== litSig) { buildLit(bandOn, switchesOn, capsOn, bandWidthId); litSig = sig; }
    rainbow = colorId === 'rainbow';
    const f = finishById.get(colorId);
    litColor = new THREE.Color(f ? f.hex : '#FFF3E2');
    /* Rainbow cycles; a solid colour has nothing to animate. Reduced motion
       freezes the cycle to a STATIC rainbow gradient — the spread along the
       ribbon is the point, the movement is only the garnish. */
    animating = rainbow && !reduceMotion.matches;
    if (!rainbow) phase = 0;
    paintLit();
    mark();
  }
  reduceMotion.addEventListener('change', () => {
    animating = lit.visible && rainbow && !reduceMotion.matches;
    mark();
  });

  /* --- slots ------------------------------------------------------------ */
  const slots = new Map();
  function slot(name) {
    if (!slots.has(name)) { const g = new THREE.Group(); g.name = name; deck.add(g); slots.set(name, g); }
    return slots.get(name);
  }
  function clearSlot(name) {
    const g = slot(name);
    while (g.children.length) g.remove(g.children[0]);
    return g;
  }

  /**
   * Add one loaded part to a slot.
   * @param at  glTF-space position, or null for a baked mesh (no transform)
   * @param tint a THREE.Color multiplied into an authored material
   * @param recentre  true (the default) puts the part's BOUNDING BOX centre on
   *        `at`, which is what a symmetric instance wants. false puts the
   *        part's own ORIGIN there — required by anything asymmetric, i.e. the
   *        YA13 joystick, whose pot boxes reach 9.3 mm to the west and north
   *        and only 7.4 mm the other way: bbox-centring it would slide the
   *        stick 0.95 mm off JS1 in both axes.
   */
  const tinted = new WeakMap();          // authored material -> tint hex -> clone

  /** Tint an authored (glTF-supplied) material without cloning it per frame. */
  function tintedMaterial(src, tint) {
    if (!tinted.has(src)) tinted.set(src, new Map());
    const byTint = tinted.get(src);
    const keyHex = tint ? tint.getHexString() : 'none';
    if (!byTint.has(keyHex)) {
      const m = src.clone();
      if (tint) m.color = tint;
      byTint.set(keyHex, m);
    }
    return byTint.get(keyHex);
  }

  function add(group, part, material, at, tint, recentre = true) {
    const o = part.mesh.clone();
    if (part.authored) {
      o.material = tintedMaterial(part.mesh.material, tint);
    } else if (material) {
      o.material = material;
    }
    o.castShadow = !(o.material.userData && o.material.userData.transmissive);
    o.receiveShadow = true;
    if (at && recentre) {
      const bb = part.mesh.geometry.boundingBox;
      o.position.set(at[0] - (bb.min.x + bb.max.x) / 2, at[1], at[2] - (bb.min.z + bb.max.z) / 2);
    } else if (at) {
      o.position.set(at[0], at[1], at[2]);
    }
    group.add(o);
    return o;
  }

  /* --- the apply pass --------------------------------------------------- */
  let gen = 0, fitted = false, dirty = true;
  const mark = () => { dirty = true; };

  function fill(name, meshRel, build) {
    const myGen = gen;
    loadMesh(meshRel).then((parts) => {
      if (myGen !== gen) return;
      build(clearSlot(name), parts);
      mark();
    }).catch((err) => console.error(`[agentpad13] mesh ${meshRel}`, err));
  }

  function apply(state, derived) {
    gen++;
    const p = positions;

    /* board — always in the stack: you see it through the plate cutouts and
       through a transparent case. Its colour IS the soldermask choice. */
    fill('board', catalog.board.mesh, (g, parts) => {
      const mat = maskMaterial(derived.set.board_mask);
      for (const part of parts) add(g, part, mat, null, mat.color);
    });

    /* plate: one panel. Its colour is the fab mask on the FR4 path and a
       palette colour when it is printed; its ART is the variant. */
    const pv = catalog.plate.variants.find((v) => v.id === state.plate.variant);
    const printedPlate = derived.set.plate_procurement === 'printed';
    const plateSrc = printedPlate
      ? (finishById.get(state.plate.finish) || { id: 'x', hex: '#888888', roughness: 0.7 })
      : (maskById.get(state.plate.mask) || { id: 'black', hex: '#16181A' });
    const plateVariantId = printedPlate ? 'blank' : state.plate.variant;   // no copper => no marker
    fill('plate', (pv && pv.mesh) || catalog.plate.mesh, (g, parts) => {
      const mat = plateMaterial(plateVariantId, plateSrc, printedPlate
        ? { roughness: plateSrc.roughness ?? 0.7, metalness: 0.02 }
        : { roughness: 0.55, metalness: 0.08 },
        printedPlate && state.plate.translucent === true);
      const rect = plateRect();
      for (const part of parts) {
        ensurePlanarUV(part.mesh.geometry, rect);
        add(g, part, mat, null, mat.color);
      }
    });

    /* M3 corner bolts: real hardware — four M3x8 button heads proud on the
       deck — so they are always on the render, never a choice. */
    fill('screws', SCREW_MESH, (g, parts) => {
      const mat = hardwareMaterial();
      for (const [x, y] of screwPositions()) for (const part of parts) add(g, part, mat, [x, 0, y]);
    });

    /* band: the wall width picks the mesh, the colour and its own
       translucency checkbox pick the material */
    const bw = catalog.band.widths.find((w) => w.id === state.band.width);
    fill('band', bw.mesh, (g, parts) => {
      const mat = finishMaterial(state.band.finish, state.band.translucent);
      for (const part of parts) add(g, part, mat);
    });

    /* tray */
    fill('tray', catalog.tray.mesh, (g, parts) => {
      const mat = finishMaterial(state.tray.finish, state.tray.translucent);
      for (const part of parts) add(g, part, mat);
    });

    /* base: swaps the mesh under the tray and leans the whole device */
    const baseItem = catalog.bases.items.find((b) => b.id === state.base.variant);
    if (!baseItem) {
      clearSlot('base');
      tilt.rotation.x = 0;
      setHinge(CY, 0);
      mark();
    } else {
      /* The lean, in preference order: the richer per-variant `bases` block,
         then the flat tilt_deg map, then the params file's own numbers. The
         hinge comes from the same block; without it the pivot stays where a
         zero tilt makes it irrelevant. */
      const rich = p.bases && p.bases.items && p.bases.items[baseItem.id];
      const deg = (rich && rich.tilt_deg)
        ?? (p.base && p.base.tilt_deg && p.base.tilt_deg[baseItem.id])
        ?? TILT_FALLBACK[baseItem.id] ?? 0;
      const hinge = (rich && rich.hinge) || HINGE_FALLBACK;
      setHinge(hinge.y, hinge.z);
      tilt.rotation.x = deg * DEG;
      fill('base', baseItem.mesh, (g, parts) => {
        const mat = finishMaterial(state.tray.finish, state.tray.translucent);
        for (const part of parts) add(g, part, mat);
      });
    }

    /* switches: the stems are what you see with caps off. View toggle only —
       thirteen MX switches are in the build whether or not they are drawn. */
    if (!state.view.switches) { clearSlot('switches'); mark(); }
    else fill('switches', SWITCH_MESH, (g, parts) => {
      const mat = finishMaterial(state.switches.finish, state.switches.translucent);
      for (const sw of p.switches) for (const part of parts) add(g, part, mat, [sw.x, 0, sw.y]);
    });

    /* stabiliser: a site-owned stand-in under the 2u key, baked at its
       absolute board position. View only — it is one self-buy line that
       follows the keycaps, never a configuration axis. */
    if (!state.view.stabilizer) { clearSlot('stab'); mark(); }
    else fill('stab', STAB_MESH, (g, parts) => {
      const mat = hardwareMaterial();
      for (const part of parts) add(g, part, mat);
    });

    /* THE TWO MODULES — round 4: "the configurator still doesn't show the
       encoder or joystick itself, just the toppers." These are the bought THT
       parts the printed toppers push onto, so they carry a fixed hardware look
       (moduleMaterial) and never a palette colour. Their Show rows are
       SEPARATE from the topper rows: hide the knob and the bare EC11E shaft is
       what stands there, which is the whole reason for splitting them. */
    if (!state.view.encoder) { clearSlot('encoder'); mark(); }
    else fill('encoder', ENCODER_MESH, (g, parts) => {
      // symmetric about RE1's shaft, so the default bbox recentre is correct
      for (const part of parts) add(g, part, moduleMaterial(part.name), [p.encoder.x, 0, p.encoder.y]);
    });

    if (!state.view.joystick) { clearSlot('joystick'); mark(); }
    else fill('joystick', JOYSTICK_MESH, (g, parts) => {
      // recentre:false — the YA13 is deliberately asymmetric (see add())
      for (const part of parts) add(g, part, moduleMaterial(part.name), [p.stick.x, 0, p.stick.y], null, false);
    });

    /* keycaps: optional; the size per position comes from positions.json and
       the 2U file follows the stabiliser coupling, never a user choice. */
    if (!derived.facts.caps_on) { clearSlot('caps'); mark(); }
    else {
      const stabSize = derived.set.keycap_2u_size || '2u';
      const wanted = new Map();
      for (const sw of p.switches) {
        const size = sw.size === '2u' ? stabSize : sw.size;
        const f = catalog.keycaps.files.find(
          (x) => x.profile === state.caps.profile && x.width === state.caps.width && x.size === size);
        if (!f) continue;
        if (!wanted.has(f.mesh)) wanted.set(f.mesh, []);
        wanted.get(f.mesh).push(sw);
      }
      clearSlot('caps');
      const myGen = gen;
      const mat = finishMaterial(state.caps.finish, state.caps.translucent);
      for (const [meshRel, list] of wanted) {
        loadMesh(meshRel).then((parts) => {
          if (myGen !== gen) return;
          const g = slot('caps');
          for (const sw of list) for (const part of parts) add(g, part, mat, [sw.x, p.keycap_seat_z, sw.y]);
          mark();
        }).catch((err) => console.error(`[agentpad13] mesh ${meshRel}`, err));
      }
    }

    /* toppers: whatever styles the catalog lists, drawn only when shown */
    const knob = state.view.knob && catalog.toppers.knobs.find((k) => k.id === state.toppers.knob);
    if (!knob) { clearSlot('knob'); mark(); }
    else fill('knob', knob.mesh, (g, parts) => {
      const mat = finishMaterial(state.toppers.finish, state.toppers.translucent);
      for (const part of parts) add(g, part, mat, [p.encoder.x, 0, p.encoder.y]);
    });

    const stick = state.view.stick && catalog.toppers.stick_caps.find((s) => s.id === state.toppers.stick);
    if (!stick) { clearSlot('stick'); mark(); }
    else fill('stick', stick.mesh, (g, parts) => {
      const mat = finishMaterial(state.toppers.finish, state.toppers.translucent);
      const recentre = stick.placement !== 'origin';
      for (const part of parts) add(g, part, mat, [p.stick.x, 0, p.stick.y], null, recentre);
    });

    /* LIT. View only — state.lighting is never a fact (see state.js). The two
       halves have two different gates and lighting.js owns both: the per-key
       LEDs run on any board, and the band half needs the LED band ordered AND a
       band you can see light through. */
    setLit(keyGlow(state), (state.lighting || {}).color, bandGlow(state),
      state.view.switches === true, derived.facts.caps_on === true, state.band.width);

    queueMicrotask(settle);
    setTimeout(settle, 80);
    setTimeout(settle, 400);
  }

  /** Drop the assembly onto the desk plane and frame it the first time.
   *  Also fixes where "centred" is, which is what pan is bounded against and
   *  what a double-click returns to. */
  function settle() {
    const box = new THREE.Box3().setFromObject(tilt);
    if (box.isEmpty()) return;
    ground.position.y = box.min.y - 0.05;
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    home.copy(sphere.center);
    panLimit = sphere.radius * 1.4;        // far enough to compose, never lost
    if (!fitted && slots.get('band') && slots.get('band').children.length) {
      const d = (sphere.radius * 1.06) / Math.sin((camera.fov * DEG) / 2);
      const dir = new THREE.Vector3(0.42, 0.62, 0.66).normalize();
      camera.position.copy(dir.multiplyScalar(d).add(sphere.center));
      controls.target.copy(sphere.center);
      controls.update();
      fitted = true;
    }
    mark();
  }

  /* --- theme: the env light follows the page ground --------------------- */
  function setTheme(darkMode) {
    scene.environmentIntensity = darkMode ? 0.62 : 1.0;
    ground.material.opacity = darkMode ? 0.42 : 0.28;
    key.intensity = darkMode ? 1.1 : 1.5;
    mark();
  }

  /* --- bloom ------------------------------------------------------------
   * The composer is built ONCE, the first time something is lit, and it is
   * used ONLY while something is lit: an unlit render goes straight through
   * renderer.render() and pays nothing for a chain it does not need.
   *
   * Order matters. RenderPass draws into a HalfFloat buffer, and three.js
   * applies tone mapping only when it renders to the CANVAS — so the bloom
   * pass sees raw linear HDR (which is what makes a threshold above 1.0
   * meaningful at all), and OutputPass puts the tone curve and the sRGB
   * transfer back at the very end. */
  let composer = null;
  function ensureComposer() {
    if (composer) return composer;
    const r = canvas.getBoundingClientRect();
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    composer.addPass(new UnrealBloomPass(
      new THREE.Vector2(r.width || 1, r.height || 1),
      BLOOM.strength, BLOOM.radius, BLOOM.threshold,
    ));
    composer.addPass(new OutputPass());
    composer.setSize(r.width || 1, r.height || 1);
    return composer;
  }

  /* --- size + loop ------------------------------------------------------ */
  function resize() {
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    renderer.setSize(r.width, r.height, false);
    if (composer) composer.setSize(r.width, r.height);
    camera.aspect = r.width / r.height;
    camera.updateProjectionMatrix();
    mark();
  }
  new ResizeObserver(resize).observe(canvas);
  resize();

  /** Radians of hue per second in rainbow mode. Slow on purpose: this is a
   *  gentle wash, not a party light. */
  const CYCLE_S = 14;
  let last = 0;

  (function loop(now) {
    requestAnimationFrame(loop);
    const moved = controls.update();
    clampPan();                       // after update(): damping pans too
    if (animating) {
      const dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
      phase = (phase + dt / CYCLE_S) % 1;
      paintLit();
      dirty = true;
    }
    last = now;
    if (!(moved || dirty)) return;
    if (lit.visible) ensureComposer().render(); else renderer.render(scene, camera);
    dirty = false;
  })(0);

  /** Warm the mesh cache in the background so later clicks are instant. */
  function preload(refs) {
    const idle = window.requestIdleCallback || ((fn) => setTimeout(fn, 300));
    let i = 0;
    const step = () => {
      if (i >= refs.length) return;
      loadMesh(refs[i++]).catch(() => {}).finally(() => idle(step));
    };
    idle(step);
  }

  return { apply, setTheme, preload, resize };
}

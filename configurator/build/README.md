# agentpad13 configurator — data pipeline

Generates the four data files and the viewer meshes the site consumes. Every
byte is derived from artifacts that ship in `release/`; nothing is re-run
through CAD and nothing is typed in by hand.

## One command

```sh
python3 configurator/build/build_all.py          # generate + gate + test
python3 configurator/build/build_all.py --no-tests
```

Runs, in order and stopping at the first failure:

| stage | writes | gate |
|---|---|---|
| `gen_catalog.py` | `out/catalog.json` | **manifest gate** — every emitted path must be listed in `release/MANIFEST.md` *and* exist on disk; the flash command is parsed out of `BRING-UP.md` and STOPs if it is not there |
| `gen_positions.py` | `out/positions.json` | every value read from a cited source; STOPs rather than guessing |
| `gen_meshes.py` | `out/meshes/*.glb`, `out/meshes/board_top.png` | inputs must be in the manifest; per-mesh volume/bbox and winding gates; texture **chirality gate** |
| `gen_textures.py` | `out/textures/*.png` | the three plate boards must share one Edge.Cuts profile; **loop census**; **orientation gate**; per-variant marker census |
| `gen_costs.py` | `out/costs.json` | emits `{"updated": null, "lines": {}}` and refuses to clobber owner data |
| `check_links.py` | — | every `release/...` path, every fixed build-sheet link, every `meshes/...` and `textures/...` reference resolves, and every plate variant declares a `decal` key |
| `unittest` | — | the full Python suite in `configurator/tests/` |

Optional, needs `matplotlib` (not required by the build):

```sh
python3 configurator/build/verify_chirality.py out/chirality_check.png
```

## Environment

Create an isolated environment and install the versions used for the committed
assets:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r configurator/build/requirements.txt
python configurator/build/build_all.py
```

The committed build was generated with Python 3.13.7 and the exact direct
dependencies in `requirements.txt`.

| package | used by | why |
|---|---|---|
| `numpy` | everything | mesh arrays |
| `Pillow` | `gen_meshes.py` | crop the board texture |
| `build123d` / `OCP` (7.9.3.1) | `gen_meshes.py` | tessellate the shipped plate STEP |
| `matplotlib` | `verify_chirality.py` only | optional visual check |

No decimation, glTF or DXF library is required — the QEM decimator and the
glTF 2.0 binary writer are in `meshlib.py`, precisely so that the output stays
byte-deterministic under our own control.

`OCP` pins the plate mesh: OCCT tessellation is deterministic for a fixed
version and fixed deflection, but a different OCCT could retessellate. If
`plate.glb` ever changes without the STEP changing, that is why.

## Handedness — read before touching a transform

The case model's board frame is **left-handed**. That is not an opinion;
`release/hardware/case/v2/agentpad13_case_v2.py:1077` says so:

> The design frame is LEFT-handed (x right, y DOWN from raw KiCad board
> coords, z up) while STL/STEP are right-handed, so every solid exported
> through this path is the ENANTIOMORPH of the intended part.

Two consequences, both load-bearing:

1. **Source STLs are in two different frames.** The tray and the bases are
   mirrored at export (`agentpad13_case_v2.py:2483`,
   `bases/agentpad13_base.py:513`, both `Pos(0, PCB_H, 0) * mirror(part,
   about=Plane.XZ)`), so they contain `y_print = 100.0 − y_board`. The bands,
   the plate STEP, the keycaps and the toppers are exported un-mirrored and
   contain board-frame `y` directly. `gen_meshes.py` applies `M_PRINT` to the
   first group and `M_BOARD` to the second.

   *Verified, not assumed.* The tray's corner-boss notch exists at exactly one
   corner — the board's `(0,0)` corner, the only one with a 13.2 mm chamfer leg
   (`contract_v4.json outline.chamfer_vertices`; the other three are 14.6). In
   the shipped tray STL that notch face lies on the plane `x − y = −87.30`,
   i.e. board-frame `x + y = 12.70`, at the STL corner `(0, 100)`. Board `(0,0)`
   → STL `(0,100)` confirms `y_print = 100 − y_board`.

2. **The board→glTF map must have determinant −1.** `(X, Y, Z)_gltf =
   (x, z, y)_board`. This is *not* the usual Z-up→Y-up rotation `(x, z, −y)`;
   that one is determinant +1 and, applied to left-handed numbers, renders the
   mirror image. `meshlib.transform` reverses triangle winding whenever the
   matrix determinant is negative, and `gen_meshes.emit` then asserts the
   transformed solid still has positive signed volume.

`positions.json` publishes numbers in the **board frame** (so `encoder` is
`13.525, 12.5`, exactly as the case model has it) and carries the `frame` block
with the definition, the handedness and the matrix. The meshes are emitted
already in glTF space, so the viewer never applies a mirror itself.

### The visual check, and its result

`verify_chirality.py` composes the emitted meshes using `positions.json` and
renders three orthographic views. Compared by eye against the shipped renders:

| view | expected | observed |
|---|---|---|
| top-down | USB centred on the far edge, encoder TOP-LEFT, stick TOP-RIGHT, 2U key at the near edge | matches the TOP-DOWN panel of `release/renders/v27_turntable.png` |
| 3/4 iso from the user's side | encoder far-LEFT, stick far-RIGHT | matches `release/renders/v27_hero.png` |
| far wall | USB port centred | centred (`USB_X == CX`, `agentpad13_case_v2.py:1111`) |

`gen_meshes.py` additionally gates the texture: the board plot's top outline
edge must span the 13.2 → 69.6 chamfer and the bottom edge 14.6 → 69.6. Those
legs differ, so the check pins image-top to board `y = 0` and a flipped or
mirrored plot fails the build. Measured: top `13.07..69.71`, bottom
`14.49..69.71` (line-width slop; tolerance 0.35 mm) — **PASS**.

## The plate art — layered, never a baked colour

`gen_textures.py` renders the plate's top face from the three ORDERED boards
(`release/hardware/case/v2/fab/agentpad13_v2_plate{,_tented_ring,_blank}_v5.kicad_pcb`)
in pure Python. It emits **23 KiB** total:

| file | what |
|---|---|
| `textures/plate_openings.png` | 844 × 1000 RGBA, 10 px/mm. White + opaque where the plate is material, fully transparent where the fab routes an opening. **Shared by all three variants.** |
| `textures/plate_decal_standard.png` | transparent except the Ø12 exposed ENIG gold disc over TP5 |
| `textures/plate_decal_tented_ring.png` | transparent except the Ø16 white silkscreen ring, 0.2 stroke |
| *(blank)* | none. `catalog.plate.variants[].decal` is `null` — markerless by design, not a missing file |

**No ground colour is baked in.** The configurator lets the owner pick the
plate's colour (soldermask on the FR4 path, filament or resin on the printed
path), so the ground is the viewer's material tint at runtime and the map
carries only coverage. RGB is written at full strength in every pixel,
transparent ones included, so bilinear filtering cannot bleed black into an
antialiased edge.

The frame is board-frame: image row 0 is board `y = 0` (the FAR / USB edge),
column 0 is board `x = −0.1`. `catalog.plate.openings_map` publishes
`px_per_mm`, `size_px` and `extent_mm` so the viewer can map UVs without
guessing.

### Why not `kicad-cli`

Measured on kicad-cli 9.0.9, not assumed:

* its SVG carries a wall-clock timestamp — two runs differ by exactly
  `<title>SVG Image created as X date 2026/08/20 19:20:02 </title>` — so it is
  not byte-stable without post-processing;
* nothing in the build interpreter can rasterise an SVG (no `cairosvg`,
  `svglib`, `cairo`, `skia`, `resvg`; no `rsvg-convert`, no ImageMagick), so a
  second heavy external tool would be needed on top of KiCad itself;
* and it draws the wrong picture. That export — and the shipped
  `agentpad13_v2_plate_v5_top.png`, which **is** that export — is a fab-check
  plot: white page, KiCad theme colours, the mask layer in magenta. The real
  plate is matte black soldermask with an ENIG gold disc.

Filling the Edge.Cuts contours here instead keeps the pipeline hermetic and
byte-deterministic under our own control — the same argument `meshlib.py`
makes for writing its own glTF.

### Its gates

1. **Edge.Cuts identity.** All three variants must carry the same 89-shape
   profile, re-proved from the boards themselves, before one map is shared.
2. **Loop census.** 1 outline (84.4 × 100.0) + 13 MX cutouts (14.0 × 14.0) +
   2 stab slots (6.65 × 12.3) + 1 encoder opening (14.0 × 13.0) + 1 YA13
   opening (18.45 × 18.45) + 1 layer-indicator hole (Ø3.0) + 4 M3 holes
   (Ø3.2) = **23 contours**. A board that lost or gained an opening fails.
3. **Closure.** An open contour is a `GateError`, never a flood fill.
4. **Orientation.** The plate outline is a symmetric rounded rectangle and
   carries no handedness at all. The layer-indicator hole does: LED14 at
   (13.525, 79.35) is open, and **both** of its mirror images — about the x
   centreline and about the y centreline — land on solid plate. Plus the
   encoder opening open and TP5 solid. A mirrored or flipped raster fails at
   least one of the five probes. Measured: `LED14 hole open (alpha 0); LED14
   mirrored in x solid (alpha 255); LED14 mirrored in y solid (alpha 255);
   encoder opening open (alpha 0); TP5 touch pad solid (alpha 255)` — **PASS**.
5. **Marker census.** Each variant must carry exactly the one marker
   `common.PLATE_MARKERS` claims, or the catalog would describe a plate nobody
   can order.

Determinism is by construction: integer supersampled coverage (4 × 4), integer
averaging, `optimize=False` with a fixed `compress_level`, and PIL writes no
`tIME`/`tEXt` chunk. `test_plate_art.py` runs the generator twice into two
fresh directories and compares sha256, and separately asserts the committed
bytes are what the generator produces.

## Mesh weights

28 `.glb` + 1 `.png` = **3.80 MiB** total. One configured scene (tray, one
band, plate, board, one base, 1U + 2U caps, knob, stick cap) = **1.34 MiB**.

Triangle budgets, chosen so any single scene stays near 45k triangles:
tray 12000 · band/base/plate 6000–8000 · keycaps 6000 · toppers 5000.
Only the keycaps (27k–45k source triangles) and three toppers are decimated;
everything else ships at source resolution. Decimation is gated at ≤5 % volume
change and ≤0.25 mm bounding-box drift.

## Board frame at a glance

```
                 y = 0   FAR EDGE — USB (J1 x=42.1), encoder (13.525, 12.5),
                         stick (69.71, 13.37)
   x = 0  +-----------------------------------------+  x = 84.2
   LEFT   |  SW1   SW2   SW3   SW4      y = 31.70   |  RIGHT
          |  SW5   SW6   SW7   SW8      y = 50.75   |
          |  SW9   SW10  SW11  SW12     y = 69.80   |
          |            SW13 (2U)        y = 88.85   |
          +-----------------------------------------+
                 y = 100  NEAR EDGE (toward the user)

   z = 0 at PCB top · PCB −1.6..0 · plate 3.4..5.0 (deck) · keycap seat 11.6
   tray −9.5..  · band −7.5..5.0 · base mating plane −9.5, peg top −8.1
```

## Notes for the site (contract deltas)

The JSON contract is implemented as specified. Everything below is **additive**
— no specified key changed name, type or meaning.

* `catalog.board`: `gerbers`, `assembly.*` (HOW-TO-ORDER §2 uploads the
  gerber zip and the BOM/CPL separately from the fabpack), `outline_mm`,
  `thickness_mm`, `mesh`, `texture`.
* `catalog.plate`: `mesh`, `stl`, `step`, `dxf`, `size_mm`, `thickness_mm`; each
  variant also carries `kicad_pcb`. One mesh serves all three variants — they
  share one Edge.Cuts profile (`CASE-V2-NOTES.md` §14, "ALL GATES PASS (3/3
  variants)").
* `catalog.band`: `default` (`w5.4`, HOW-TO-ORDER §4), per-width
  `step` and `wall_mm`.
* `catalog.bases`: `interface`, `default_peg` (`5p8`, `INTERFACE.md:41`),
  `peg_rungs`.
* `catalog.toppers`: `bores` / `socks` maps (the fit ladders, mirroring how
  `bases.items[].pegs` works) alongside the single `stl`, which points at the
  documented starting rung `nom` (HOW-TO-ORDER §8); `default` flags the
  shipped default parts (`A` knob / `nub_C2`).
* `catalog.keycaps.files[]`: `width_mm`. `catalog.firmware`: `polarity_doc`.
  `catalog.docs`: `how_to_order`, `release_notes`, `base_interface`.
* `positions.json`: `frame`, `mesh_placement`, `pcb`, `stabilizer`, `base`.

### Round 2 (also additive — no round-1 key renamed, retyped or removed)

* `catalog.firmware.flash` — the `dd` command, parsed verbatim out of
  `release/firmware/BRING-UP.md` (Step 1, the "This always works" block), plus
  `flash_source` naming the line. This retires the hardcoded `FLASH_FALLBACK`
  constant in `site/sheet.js`; a test asserts the two agree today and
  `gen_catalog` STOPs rather than falling back if the doc loses the command.
* `catalog.plate.openings_map` and `catalog.plate.variants[].{marker, decal,
  marker_note}` — see "The plate art" above.
* `positions.bases` — per-variant tilt, desk plane, hinge line, plan
  silhouette and mesh. **And** `positions.base.tilt_deg`, the plain
  `{id: degrees}` map `site/viewer.js:255` already reads. Both come from one
  computation, so they cannot disagree.
* `positions.touch_pad` — TP5 centre, the Ø14/Ø14/Ø8 electrode stack, and the
  per-variant marker (Ø12 exposed disc / Ø16 silk ring / none). Every diameter
  is measured off the ordered boards.
* `positions.screws` — the four Ø3.2 corner holes at (3.7, 3.7), (80.5, 3.7),
  (3.7, 96.3), (80.5, 96.3) with the M3×8 **ISO 7380 button head** envelope
  (Ø5.7 × 1.8, proud on the deck — *not* a socket-head cap).
* `positions.stab` — the two slots as rectangles (6.65 × 12.3 at
  (30.162, 89.47) and (54.038, 89.47)). **And** `positions.stabilizer.slot_size`
  / `.slots`, additive inside the round-1 object. One computation again.

**One published parameter disagreement is recorded, not hidden:**

`bases/params/agentpad13_base_params.json` lists `base_height_mm: 17.49`
for the **pedestal**, which is the wedge's full-footprint figure inherited
unchanged. The pedestal's own solid is **15.428** tall below the mating plane,
because its Ø78 plan never reaches the far edge. The geometry-derived value is
published and it matches the shipped STL.

**2U stabilizer rule.** `keycaps.counts` publishes both valid mixes:

* `counts` = 12 × 1U + 1 × 2U without a stabilizer.
* `counts.with_stabilizer` = 12 × 1U + 1 × 2U-stab when the optional 2U
  plate-mount stabilizer is fitted, exactly as HOW-TO-ORDER §7 specifies.

The slots themselves are measured from all three shipped plate boards. Public
`CASE-V2-NOTES.md` §8 item 6 keeps the real-stabilizer coupon fit check open.

## Note for this public tree

The shipped site runs entirely off the committed `build/out/` data. The public
pipeline regenerates it from the shipped release artifacts and public source
files in this repository; it does not call a keycap, case, plate, or board CAD
generator. `gen_meshes.py` only tessellates the shipped plate STEP and converts
the shipped STL files to viewer GLBs. Everything the site serves, links to, or
puts on an order sheet is public and checksummed.

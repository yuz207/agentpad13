# agentpad13 case v2 — plate-as-deck over the v4_r27 octagon

Built 2026-07-18 against the FROZEN board `hardware/pcb/v4/v4_r27.kicad_pcb`
(md5 `af5ad274558fc034d2d098a72d423a25`, verified this session). The board was
not touched. **Gate: PASS — case 62/62 assertions, coupons 15/15, zero
unexplained interferences.**

Owner directives folded in (2026-07-18, this session, verbatim):
- "Let's go ahead with plate as deck concept"
- Plate outline "ROUNDED RECTANGLE (fillet ~R8 …); final radius is an
  owner-sign-off aesthetic"
- Single-PCB alternative **withdrawn**; locked stack: "a screwed-down FR4
  face-plus-skeleton on top, a floating octagonal brain in the middle, a
  printed chassis with the threads and feet on the bottom — three layers,
  four screws"
- "top case should be able to be 3D printed via FDM (same with bottom case),
  or optionally, top case can be clear/frosted ordered via resin printing.
  Bottom case should be FDM always for heat set inserts" — two printed parts
  total, "the top case looks like a band around the side"
- "we absolutely are NOT copying verbatim the silkscreen from the Work Louder
  product!!" — plate ships **BLANK**; "We'll decorate later separately"
- "the top plate should also sit flush with the top of the case … the top
  case should be countersunk so to speak" — the band carries a rabbet ledge
  the plate drops into, flush at the deck plane

## 0. The product (4 parts + hardware)

| # | Part | Made how | File(s) |
|---|------|----------|---------|
| 1 | `fr4_plate` — face + switch skeleton, BLANK | ordered, 1.5 mm FR4 | `fab/agentpad13_v2_plate.kicad_pcb` (+`.dxf`), `step/agentpad13_v2_plate.step` |
| 2 | `band` — top case, the visible side wall | FDM PETG **or** resin (frosted default look) | `stl/ step/ agentpad13_v2_band.*` |
| 3 | PCB v4_r27 — floating, never screwed | already ordered (frozen) | — |
| 4 | `tray` — bottom case, all inserts + pins | FDM PETG **always** | `stl/ step/ agentpad13_v2_tray.*` |

Hardware: 4× M3×8 ISO 7380 button-head; 4× standard Voron-style M3×4×5
heat-set inserts (4 mm long, nominal 5 mm OD, Ø4.7 tray cavity) in the tray
only; 4× 3M SJ61A1 bumpons (Ø7.9×2.2,
clear) on the corner-boss bottom faces; 2 mm PORON around sockets
(unmodeled, v1 §10 carry-over); conductive foam pad pending the touch coupon.

**One screw path** (the whole assembly): M3 head proud on the deck → plate
Ø3.2 → band cap Ø4.4 (z +1.5…+3.5) → tray boss insert (bore Ø4.7,
+1.5…−4.2). Plate, band, and tray clamp as one stack; the PCB floats inside
on three press pins (H5/H6/H7) and support bosses — the owner's "it just
sits in its spot" model, verbatim.

**Why no ears.** v1's blocking defect (CASE-NOTES §v1.1) was that Ø9.5
bosses could not pass the old board's R5 corners inside a clean rectangle —
bbox grew to 89.6×129. The v4 octagon's 14.6 mm chamfers are exactly §v1.1's
lever 1 (a coordinated PCB respin): the bosses now live INSIDE the rounded
rectangle, in the voids the chamfers vacate. Case is 89.6 × 105.4 × R8.

## 1. Z stack (desk → keycap; datum z = 0 at PCB top face)

| z (mm) | Interface | Source |
|---:|---|---|
| +6.8 | screw head top (proud button head) | ISO 7380 env (v1 §4 1.8) |
| **+5.0** | **plate TOP = band rim top (flush deck)** | MX shoulder→PCB 5.0, §1 |
| +3.5 | plate underside = ledge top = cap top | plate 1.5 [D std FR4] |
| +1.5 | cap underside = tray boss top (v1 parting plane) | §3 |
| +0.3 | band ledge underside (floats over the PCB rim) | this doc §3 |
| 0.0 | PCB TOP (datum) | contract |
| −1.51 | PCB bottom (real STEP; design datum −1.6) | [S] |
| −3.45 | hotswap socket bottom | §1 SOCKET_DROP |
| −5.10 | cavity floor = tray floor top | §1 UNDER_PCB_CAVITY 3.5 |
| −5.895 | BOOT/RESET tact bottoms → tray service slots | [S] fresh STEP |
| −7.50 | band bottom (FROZEN — `BAND_Z_BOT`; the band is ordered) | §4 |
| **−9.50** | **tray bottom (v2.11 plinth — NO LONGER flush with the band)** | §4 TRAY_T 4.4 |
| −11.7 | desk (SJ61A1 bumpons on boss bottoms) | 3M catalog |

Stack 14.5 mm (band top +5.0 to tray bottom −9.5; the band itself is
still 12.5) + 2.2 feet. Tact bottoms sit recessed 3.6 above the tray bottom
(5.8 above the desk) inside the slots.

**v2.11 (2026-08-19) — THE TRAY PLINTH.** Through v2.10 the tray bottom and
the band bottom were the same plane (−7.50, flush), and §2's "from the side
only the band is visible" followed from it. Both are now amended. Owner
directive: *"Let's make the tray a little taller. The bases are optional and
there's no reason for the tray to be flush on the bottom, if anything it
might look better with a little bit of height."* and *"I think a more
pronounced gap would be better."*, then, setting the amount: *"Though I
suppose 2mm is fine if the idea is one would also typically use an optional
base?"* — **+2.0 mm adopted** (`TRAY_T` 2.4 → 4.4, tray bottom −7.50 →
−9.50). The band now floats on a 2.0 mm recessed plinth inset
(95.6 − 84.3)/2 = **5.65 mm per side**; the bases stay the styling layer, so
the plinth is a reveal rather than a statement. Nothing above the floor
moved — `Z_FLOOR_TOP` is derived from the PCB side, so the cavity, boss tops,
notch (z ≥ −1.85), retention pins and the 14 supports are untouched, and
khana held 101/101 with the same 8 interference pairs at identical volumes.
The band was protected by a new frozen `BAND_Z_BOT = −7.5`: six band-side
consumers used to read `Z_TRAY_BOT` and would have followed the tray down
(band outer prism, inner cavity, shell clip, boss sockets, bottom EFC
chamfer, and the USB funnel's floor clamp). Band STL md5
`34be6bf79a6bb81995807448639f4822` unchanged. Side effects, both
improvements: base-mount pocket floor 0.8 → **2.8 mm** (retiring the part's
tightest margin), heat-set over-press buffer 3.3 → **5.3 mm**.

## 2. Outline + provenance

- Case outer **89.6 × 105.4, R8.0** (x −2.7…86.9, y −2.7…102.7 in board
  coords). Width = owner's "~89.6"; height derived: PCB 100.0 + 2×0.3 slip +
  2×2.4 wall. R8 = owner sign-off aesthetic (open item).
- Band inner 84.8 × 100.6 R5.6 (PCB + 0.3/side, §4).
- Plate **84.4 × 100.2 R5.4** (inner − 0.2/side). **[Still correct for the CASE
  MODEL — `C.PLATE_H` is deliberately left at 100.2 because it also drives the
  band's plate pocket, which must not move. The EMITTED FAB OUTLINE is
  84.4 × 100.0: `gen_plate_fab.py` applies `PLATE_LONG_TRIM = 0.2` locally at
  emit time. See §19 (2026-07-21 trim).]** The band's plate RECESS is
  cut wider than the inner wall: **85.0 × 100.8 R5.7** = plate + 0.3/side
  (owner 2026-07-18: the plate must drop into a PRINTED band despite typical
  FDM inner-cavity tightening of 0.1–0.3 plus fab routing up to +0.15 on the
  plate). The visible reveal around the flush deck is therefore **0.3 mm
  nominal** (±0.1 centering via the Ø3.2 screw holes → 0.2/0.4 worst case) —
  the CM2-style inset read, width = owner sign-off. The plate seat on the
  rabbet ledge is unaffected (1.0 mm overlap per side).
- Tray floor 84.3 × 100.1 R5.35 (inner − 0.25 slip), nested fully inside the
  band; from the side only the band is visible (owner's "band around the
  side").

Every consumed coordinate is cited in-source (`agentpad13_case_v2.py`
provenance tags): **[C]** contract_v4.json — re-validated this session by
`grade_board.py` against v4_r27 itself: `[PASS] contract: 45/45 refs ok`,
`outline bbox 84.200 x 100.000, chamfer=ok`; **[S]** fresh STEP envelopes
(`pcb_components_data_v2.py`, regenerated this session from a fresh
`kicad-cli pcb export step --subst-models --no-dnp` of v4_r27 — the v1-era
`pcb_components_data.py` was NOT used); **[R]** direct pcbnew read-back of
v4_r27 (H5/H6/H7 = Ø2.2 NPTH; TP5 pad Ø1.5 on F.Cu+F.Mask; TOUCH_PAD zone
14×14 @ (13.525, 88.85), 177.0 mm²; SW14 (64.0, 88.85), SW15 (72.5, 88.3,
90°), J2 (39.0, 41.0, 90°)); **[§n]** v1 CASE-NOTES sections (values
re-derived, never coordinates); **[D]** datasheets/standards.

## 3. Corner joint (the load-bearing derivation)

Boss centers at **(3.7, 3.7)** on each corner diagonal (mirrored: (80.5,
3.7), (3.7, 96.3), (80.5, 96.3)). Machine-verified margins (printed by the
build, gated by khana):

```
pcb_chamfer_slip    = 0.341   (boss to the octagon's 45° chamfer; gate ≥0.3)
band_crescent_wall  = 0.737   (band wall outside the Ø10 socket, at the diagonal)
head_to_plate_edge  = 0.287   (screw head edge inside the plate corner arc)
plate_hole_edge_web = 1.537   (FR4 web, Ø3.2 hole to plate edge)
```

The window for the boss center is [3.00, 3.73]: below 3.50 the Ø5.7 head
overhangs the plate's R5.4 corner; above 3.73 the boss violates 0.3 PCB
slip. 3.7 splits it in favor of PCB slip. The 0.74 crescent is a COSMETIC
shell region (the structural member is the Ø9.5 PETG boss inside it) and is
in-language: the CM2 body deliberately shows its inserts through the frosted
shell. Heads sit nestled in the corners exactly like the reference product.

**Counterbore deviation (owner sign-off).** The original spec said
"counterbored plate holes … for the exposed-head CM2 look". v1's Ø6.2×1.8
counterbore lived in a 3.5 mm printed cap; a 1.5 mm FR4 plate cannot carry a
1.8 mm counterbore. The plate gets plain Ø3.2 holes (ISO 273 CLOSE fit —
owner 2026-07-18, tightened from the Ø3.4 medium fit so the four screws
center the plate to ±0.1 and the 0.2 reveal stays visually even: worst case
0.1/0.3 instead of 0.0/0.4); the button head sits proud on the deck — which
is what the Codex Micro/CM2 renders actually show. Trade-off of the close
fit: the tray print must hold the boss pattern to ~±0.1 over 76.8/92.6 mm
(calibrate slicer XY scale to ≤0.1%); if the screws fight at first
assembly, open the FR4 holes to 3.3/3.4 with a pin vise — FR4 hand-drills
cleanly. Owner-approved: proud heads are fine; only the plate itself must
sit flush with the case top (it does: both at +5.0).
If a recessed head is wanted, the lever is a thicker plate (2.0/2.5 FR4 with
partial-depth counterbore, nonstandard fab op) — flagged, not chosen.

**"Countersunk" band (owner 2026-07-18).** The band carries a 1.2 mm rabbet
ledge (z +0.3…+3.5) the plate drops into: flush deck, perimeter-seated (not
corner-only). The fresh STEP shows no F.Cu solids in the 1.2 mm rim strip;
the ledge floats 0.3 over the PCB rim and the `band/pcb_board ≥ 0.25` gate
covers it. The ledge's 45° under-chamfer was REFUSED by OCCT (all fallback
values) — the ledge underside is square, a 1.2 mm internal overhang ring:
PETG bridges it (non-cosmetic, internal); resin unaffected. Open item if it
prints ugly: revisit the chamfer with a swept-profile cut instead of
`chamfer()`.

## ERRATUM (2026-07-19, independent review — CONFIRMED by pad read-back)

**The RE1 encoder model in every gate run below was positioned at the
footprint ANCHOR, which for the EC11E footprint is PIN A, not the shaft.**
True shaft axis, verified from the frozen board's mounting-tab midpoint and
F.Fab body center: **(21.025, 15.000) = anchor + (7.5, 2.5)**. With the body
at its true position, the plate/body interference is **143.4 mm³**
(independently reproduced) — the "62/62 green" runs below were blind to
this because the same wrong assumption fed both the part model and the
assertion, and the STEP carries no EC11 model to contradict it. v1's case
carries the identical bug (layout_v2 RE1_CENTER = anchor). JS1 is
unaffected (anchor = body center, verified), but its F.Fab body is
**18.72 × 18.72**, larger than the Ø15 modeled envelope — MPN caliper
pending. Resolution in flight: board-side RE1 move (r28 candidate) so the
shaft truly lands at (13.525, 12.5); the ordered plate remains correct for
the DESIGN intent and stays valid. When r28's contract lands (with an
explicit shaft ref), the case script's EC11/knob models switch to
shaft-true positioning so this gate class can never go blind again.

## 4. khana gates (verbatim, final run 2026-07-18)

```
case:    status=ok assertions=62 failed=0
  interferences: [('pcb_components','sockets',1.706), ('pcb_components','leds',2.736),
                  ('sockets','leds',67.326), ('ec11_body','knob_sweep',342.225)]
coupons: status=ok assertions=15 failed=0
  interferences: []
```

- `ec11_body×knob_sweep` 342.225 mm³ is the **asserted-expected** coaxial
  knob-on-shaft overlap (`assert_interference`, v1 pattern — fails loudly if
  it ever vanishes). Identical volume to v1's — the regenerated sweep
  geometry cross-checks.
- The three `sockets/leds/components` overlaps are BOARD-RESIDENT proxy
  pairs: my hand keep-outs for unmodeled parts (Kailh sockets centered
  14.5×5.89, LED envelopes) overlap each other and real neighbors by
  construction. Their mutual geometry is the frozen board designer's solved
  fact — out of case scope, deliberately not asserted (v1 drew the same
  line). Every CASE×CASE and CASE×BOARD pair IS asserted.

Assertion coverage: pairwise no-interference for
{plate, band, tray, retention, screws} × {each other} ∪ {pcb_board,
pcb_components, sockets, leds, ec11_body, js_body, usb_recept}; swept
volumes knob/JS vs plate+band+screw heads; clearances: `band/pcb ≥0.25`
(0.30 built), `sockets/tray ≥1.0` (1.65), `usb_recept/tray ≥0.2` (0.24,
§5), `tray/pcb ≥0.3` (0.341 boss-to-chamfer), `screws/pcb + screws/comps
≥1.0`, `plate/ec11 ≥0.25` (0.298 at the opening's corner diagonal — the
13×13 R1.5 opening vs the square 11.7 body; flats have 0.65), `plate/js
≥0.4` (0.5), `retention/{ec11,js} ≥5.0`. Retention pins Ø2.0 enter the Ø2.2
NPTH [R] and stop at z −0.3 (spec: 0.3 below PCB top) by construction.

### Printability (ADVISORY — mechanism check is the sole hard gate)

```
band: min_wall=0.642 | overhang_area=829.7 max_deg=90
tray: min_wall=0.051 | overhang_area=63.2  max_deg=90
```

- band min_wall 0.64 = the corner crescent at its thinnest azimuth
  (tessellated; analytic 0.737) — cosmetic region, documented above.
- band overhangs = the square ledge underside ring (1.2 mm bridge), the four
  cap undersides bridging their Ø10 sockets, and the USB aperture ceiling
  (10 mm) — all short bridges, printable upright without support; resin N/A.
- tray min_wall 0.051 **[NOT ROOT-CAUSED]** — matches v1's documented
  ray-cast false-positive class (EFC chamfer slivers reported sub-0.1), and
  the fuse seam where the retention bosses meet the floor tangentially is a
  second candidate. Advisory only; verify with a slicer preview before the
  first tray print.
- tray overhang 63 mm² **[NOT ROOT-CAUSED]** — same advisory class; nothing
  in the tray design has an intentional >45° ceiling except the insert-bore
  mouths. Same slicer-preview check.

## 5. The touch key (TP5) — options, physics, coupon plan

Facts ([R] read-back of the frozen board): TOUCH_PAD pour 14×14 mm on F.Cu
at (13.525, 88.85), 177 mm², soldermask-covered — EXCEPT the TP5 test pad
at its exact center: Ø1.5, layers F.Cu + **F.Mask = bare copper exposed**.
The plate underside sits 3.5 mm above the pour; the plate is 1.5 mm FR4
(εr ≈ 4.4 → ≈0.34 mm air-equivalent).

- **(c) through-air (current blank plate):** estimated finger ΔC through
  3.5 air + plate ≈ ε0·(~1 cm²)/3.84 mm ≈ **0.23 pF** [ESTIMATE — parallel-
  plate bound]. RP2040 GPIO charge-cycle sensing resolves ~0.05–0.1 pF with
  averaging [SPECULATIVE — firmware-dependent]. SNR ≈ 2–4×: not dismissible,
  not provable on paper. **The coupon decides.**
- **(b) copper pad on the plate, coupled to TP5:** WITHOUT contact, the
  series air gap (C ≈ 0.50 pF for 14×14 @ 3.5 mm) attenuates about as badly
  as (c) — a stacked pad alone buys nothing. WITH galvanic coupling it
  becomes near-direct sensing (finger through 1.5 FR4 only): a **3.5 mm
  conductive-foam pad** compressed between the exposed Ø1.5 TP5 pad and a
  plate-underside copper pad (via-stitched to a mask-covered top disc —
  still visually blank). Zero board changes needed; needs a plate
  revision (add pad+via) only if chosen.
- **(a) plate cutout + insert window:** a filler plug bridging the 3.5 mm
  gap works electrically but puts a seam in the blank deck and adds a glued
  part. Fallback only.

**RESOLVED (owner 2026-07-18): the pad is baked into the default plate.**
After the full physics pass (finger→1.5 FR4 ≈ 2.5 pF ≈ 10× option (c);
foam-bridge = documented cap-touch app-note pattern; failure modes graceful
— see the analysis above), the owner approved adding the electrode AND the
visible marker: **Ø14 F.Cu pad, Ø12 F.Mask opening = an exposed ENIG gold
disc** (the owner's requested "circle … to indicate there's a touchpad"),
Ø14 B.Cu landing pad with Ø8 B.Mask opening for the conductive-foam pillar,
2 vias at ±6.5 mm — under the masked annulus so the gold face is clean
(render-caught: centered vias read as two dots). Finger lands directly on
gold = the strongest possible signal path. Two plate variants ship:
`agentpad13_v2_plate.kicad_pcb` (pad + gold disc, the default; order ENIG)
and `agentpad13_v2_plate_blank.kicad_pcb` (no copper, for anyone skipping
the pad or the ENIG cost — reverts the touch key to attenuated option (c)).

**Coupon still gates the FOAM decision:** the 20×20 touch chip now carries
the IDENTICAL pad/via/landing construction (no copper-tape mock needed).
Test on the real board with all LEDs animating: (1) chip in the jig, no
foam = does the exposed disc alone sense through the 3.5 mm air gap?
(2) + conductive foam pillar (≈Ø8–10 × 5 mm uncompressed) between the TP5
bare dot and the chip's underside landing = the production-candidate stack.
Ship with foam unless (1) surprises us.

## 6. Fab + print + order guidance

**FR4 order (same cart, e.g. JLCPCB):** `fab/agentpad13_v2_plate.kicad_pcb`
(default: touch pad + gold disc — order **ENIG** finish so the exposed disc
is flat gold, not HASL solder), `fab/agentpad13_v2_coupon_panel.kicad_pcb`,
`fab/agentpad13_v2_touch_chip.kicad_pcb` (same ENIG note). 1.5 mm FR4,
**matte black soldermask both sides**. The blank variant
(`agentpad13_v2_plate_blank.kicad_pcb`) carries no copper — a mask-over-
laminate blank; expect a "no copper" fab query, answer "plate, proceed". Edge.Cuts are centerline-
exact (validated by pcbnew reload: 84.40×100.20 / 80×46 / 20×20; 82/44/8
edge shapes). **[Rev-A figures — the `_v5` plates supersede them: the plate is
84.40×100.00 with 89 edge shapes after the 2026-07-21 long-axis trim, §19. The
coupon panel (80×46) and touch chip (20×20) are unaffected.]** Internal corners get the router's ~R0.5 — MX clips engage on
edge midlines, standard for FR4 plates (ai03 plate guide). The DXF is the
alternative input. Silk: plate NONE (blank by directive); coupon panel
carries functional labels only.

**Band:** default look = **frosted/clear resin** (order SLA; v1 §10 caveats:
translucent-not-clear, UV yellowing, keep out of sun). FDM path: PETG,
upright (bottom on bed), 0.4 nozzle / 0.12–0.16 layers, slicer
elephant-foot comp ON, no supports — bridges: ledge ring 1.2, cap rings
over Ø10, USB ceiling 10 mm. The corner crescents (0.74 min) print as
small local perimeter loops — cosmetic; inspect first article.

**Tray:** PETG always (thermoset resin cannot take heat-set inserts, §4/§10).
Upright, 0.16–0.20. Inserts are standard Voron-style M3×4×5, set from the boss top face
(+1.5), iron ~245 °C, melt 90% then press flat (§4). Slicer preview the two
[NOT ROOT-CAUSED] advisories above before the first print.

**Assembly order:** inserts into tray → PCB onto H5/H6/H7 pins (drops flat
on support bosses) → band down over the bosses (seats on boss shoulders at
+1.5) → switches into the plate cutouts → plate+switches down (switch pins
into hotswap sockets; plate into the band rabbet, flush) → 4× M3×8. USB
plugs into the y=0 wall aperture (metal shell enters, overmold seats
outside, §5 re-verified: receptacle bottom −4.86 vs floor −5.10 = 0.24).

## 7. Drawings + renders + hostile read

`outputs/case/views/{assembly,band,plate,tray}/*.png` (HLR),
`outputs/case/views/plate_render_top.png` (kicad-cli raytrace of the actual
fab file — renders green because the file sets no mask color; the order is
black). GLB/photoreal renders: **not produced** — `gltf-transform` is not
installed (open item; drawings + raytrace + STEPs stand in).

Hostile read log:
- **Caught a real pipeline failure:** the first per-part drawing pass wrote
  stale/overwritten files (suppressed draw errors + shared filenames) — the
  "plate" view was actually the tray. All views regenerated cleanly
  (verified fresh by size/timestamp) before review. Lesson recorded: never
  `>/dev/null` a generator you haven't seen fail loudly once.
- Top views render mirror-Y vs board coords (+Y up on screen, board y down):
  2U/touch row reads at image top. Verified feature-by-feature against
  contract positions after accounting for the flip.
- Plate: 13 cutouts + stab pair + EC11 13×13 + JS Ø16 + LYR Ø3 + 4 corner
  holes, NOTHING else — blank confirmed. Volume 7963 mm³ vs 12684 solid =
  cutouts real.
- Assembly front: USB aperture in the lower wall band, centered; knob/JS
  swept volumes clear the deck plane; screw heads inside the corner arcs.
- Knob Ø18 vs EC11 opening: the opening's corner diagonal reaches 8.57 from
  center vs knob r9 — hidden by 0.43. KEEP knob ⌀ ≥ 18 (v1 open-item #2
  carries).
- Band bottom: 4 cap rings + Ø10 sockets + ledge lines + USB notch — no
  stray geometry.

## 8. Open items (honest list)

1. **R8 corner radius + the 0.3 reveal groove** — owner aesthetic sign-off
   on the built look (drawings/renders in outputs/). Reveal was widened from
   0.2 at the owner's plate-must-fit-the-printed-band direction; shrinking
   it back is safe only for a RESIN band (±0.05–0.1 accuracy).
2. **Proud screw heads** (no counterbore in 1.5 FR4) — owner sign-off; §3.
3. **Touch**: pad + exposed gold-disc marker baked into the default plate
   (owner 2026-07-18); blank variant retained in the kit. The coupon now
   gates only the FOAM decision (with-vs-without), tested with the real
   electrode construction on the chip. §5.
4. **J2 expansion header** — carried from v1: physically DNP (a populated
   vertical header would reach z −10.1, through the tray). The board file
   does not mark it DNP, so the fresh STEP contains it; it is split out in
   `pcb_components_data_v2.J2_HEADER` and excluded from keep-outs. If a
   future SKU populates J2, this case cannot close over it.
5. **JS1 body envelope is LN§3-provisional** (v1 §13.4): freeze JS_BODY_* vs
   the metered part before the resin band order.
6. **2U stab slots** are the plate-spec rectangles (6.65×12.3 @ ±11.938,
   +0.62 south); fab router radius ~R0.5 in the corners is standard but
   verify with the coupon panel's 2U + stab set (v1 §13.5 refinement carry).
7. **Ledge under-chamfer refused by OCCT** — square 1.2 bridge ring; §3.
8. **Tray printability advisories** [NOT ROOT-CAUSED] — slicer-preview gate
   before first print; §4.
9. **Underglow**: v4 populates 10 side-fire LEDs; the frosted/clear band is
   its own diffuser (default). An opaque FDM band has no light channel in
   v2 — option not implemented (owner scope call if an opaque+glow variant
   is wanted).
10. **Weight pocket** shrunk to 60×30 @ (42.1, 58) so the H5 support boss
    keeps solid floor (v1's 60×40 pocket undercut its center boss). 3 mm
    steel still needs local thickening (v1 §13.6 carries).
11. **Renders**: install `gltf-transform` (and/or chitra-cad) for GLB/photo
    renders.
12. **No git action taken** — files staged on disk only; commits are the
    owner's.

## 9. File inventory (hardware/case/v2/)

- `agentpad13_case_v2.py` — parametric source (plate+band+tray+keep-outs+gates)
- `agentpad13_coupons_v2.py` — 6 printed coupons (true-crop corner stack, USB
  chip, insert ladder, touch jig)
- `gen_components_v2.py` → `pcb_components_data_v2.py` — fresh-STEP envelopes
- `gen_plate_fab.py` → `fab/*.kicad_pcb`, `fab/agentpad13_v2_plate.dxf`
- `step_src/agentpad13_v4_r27.step` — fresh component STEP (input artifact)
- `stl/`, `step/` — band, tray(+pins), plate, 6 coupons
- `outputs/case/` — mechanism.json + printability + views/ + plate raytrace
- `outputs/coupons/` — coupon mechanism.json + printability
- `reference/` — Codex Micro / CM2 design-language recon (DESIGN-LANGUAGE.md)
- All python sources: `ruff check` clean.

## 10. v2.1 — PLATE_T 1.5 → 1.6 (fab stock; owner order 2026-07-19)

The fab does not stock 1.5 mm FR4; the plate is ordered at **1.6 mm**. The 2D
fab files (`fab/` — .kicad_pcb + DXF) are thickness-independent and were NOT
touched. Invariant held: **plate TOP stays at +5.0** above PCB top
(`PLATE_TOP_TO_PCB`, MX switch seating). The extra 0.1 mm grows DOWNWARD:
the band's plate seat/rabbet deepens +3.5 → **+3.4** — a 0.1 deeper rabbet,
NOT a taller wall; the band's outer envelope and the −7.5..+5.0 case height
are unchanged (owner sanity frame confirmed by metric diff below).

Source edits (`agentpad13_case_v2.py`):
- `PLATE_T = 1.6` (was 1.5). The seat already derived
  (`Z_PLATE_BOT = Z_PLATE_TOP - PLATE_T`), so the rabbet deepened for free.
- `CAP_Z1` was HARDCODED at 3.5 ("plate seat"); now derived
  `= PLATE_TOP_TO_PCB - PLATE_T` (+3.4) so the corner caps end exactly at
  the plate underside (left at 3.5 they'd poke 0.1 into the plate — the
  one place the seat did not derive from PLATE_T).
- Header docstring Z-stack + 1.5-mm mentions updated to match.
- Band export renamed `agentpad13_v2_band_1.6mm.*` (see below).

Geometry diff vs the v2 build of 2026-07-18 10:26 (mechanism.json parts):
- band: 11851.323 → 11794.717 mm³ (−56.605: the 0.1 seat-annulus layer +
  0.1 off the four cap tops); bbox delta 0.0 on all six extents; 63 faces
  both. Nothing outside the seat region changed.
- fr4_plate: 7969.335 → 8500.624 mm³ (+531.289); bbox min-z 3.5 → 3.4,
  all other extents unchanged; 84 faces both.
- tray / pcb_retention / screws: volumes, bboxes, face counts bit-identical.
- interference list identical (same 4 documented board-proxy/knob entries).

khana v2.1 run (`khana build agentpad13_case_v2.py`, 2026-07-18, verbatim):

    [band] ledge chamfer refused; square ledge underside (1.2 mm overhang ring — PETG bridges it; resin unaffected)
    [corner] pcb_chamfer_slip = 0.341
    [corner] band_crescent_wall = 0.737
    [corner] head_to_plate_edge = 0.287
    [corner] plate_hole_edge_web = 1.537
    [band] ledge chamfer refused; square ledge underside (1.2 mm overhang ring — PETG bridges it; resin unaffected)
    [printability] band: ADVISORY (documented thin zones; see CASE-V2-NOTES) | min_wall=0.6419535201080192 | overhang_area=829.6519185028062 max_deg=90.0
    [printability] tray: ADVISORY (documented thin zones; see CASE-V2-NOTES) | min_wall=0.051463117837141206 | overhang_area=63.180764368446596 max_deg=90.0
    exported band, tray(+pins), plate to stl/ and step/

`mechanism.json`: status **ok**, **62/62 assertions passed**, 0 failed.
Ledge-chamfer refusal and both printability advisories are the §8.7/§8.8
pre-existing items — values bit-identical to the 10:26 build (band 0.642 /
829.7 / 90°; tray 0.051 / 63.2 / 90°).

Re-exported 2026-07-18 21:46:
- `stl/agentpad13_v2_band_1.6mm.stl` — **PCBWay 3D-print upload** (new name)
- `step/agentpad13_v2_band_1.6mm.step`
- (old 1.5-seat `stl/agentpad13_v2_band.stl` + `step/agentpad13_v2_band.step`
  left untouched on disk as the record, per owner — do NOT print those
  against a 1.6 plate: their cap tops sit at +3.5)
- `step/agentpad13_v2_plate.step` — now 1.6 thick, matches the ordered plate
- `stl/agentpad13_v2_tray.stl`, `step/agentpad13_v2_tray.step` — geometry
  unchanged, re-emitted by the build for set consistency
- `outputs/case/` mechanism.json, assembly.stl/.step, band-/tray-
  printability.json — regenerated

Carry item (NOT rebuilt, out of v2.1 scope): `agentpad13_coupons_v2.py`
hardcodes `JIG_GAP = 3.5` as "the production plate-underside gap" — that gap
is now 3.4, and `JIG_WALL_H = JIG_GAP + C.PLATE_T` will pick up 1.6 on the
next coupon rebuild. Revisit before relying on the touch jig's absolute deck
height; the already-exported coupon files still reflect the 1.5 stack.

## 11. Plate fab variants — status of record (coordinator, 2026-07-19)
`fab/` holds three orderable plate variants; only ONE was ordered for Rev A round one:
- `agentpad13_v2_plate.kicad_pcb` (+ `plate_gerbers.zip`) — **ORDERED** 2026-07-19, PCBWay, qty 5, 1.6mm, ENIG 1U" (exposed gold touch disc = the touch marker), owner's mask color per order.
- `agentpad13_v2_plate_tented_ring.kicad_pcb` (+ `plate_ring_gerbers.zip`) — ALTERNATE, built+gerber-proven, NOT ordered. Mask-tented disc (senses through mask, ~90% signal retained) + 16.0mm/0.2 silk ring marker. Purpose: cheap-finish face (HASL-LF class) for future runs; ring outer half-stroke tangentially grazes the 3mm cable cutout rim (unavoidable in range; fabs clip silk at routed edges).
- `agentpad13_v2_plate_blank.kicad_pcb` — ALTERNATE (case session), no copper at all; reverts touch to attenuated air-gap mode.
Band files: `stl/agentpad13_v2_band_1.6mm.stl` = the ordered-geometry band (1.6 plate seat); the un-suffixed band is the superseded 1.5-seat version, kept for record. All variants mirrored in `v4-release-compiled/hardware/case/v2/`.

## 12. v2.2 — board-v5 convergence (2026-07-19, this session)

Built against the ADJUDICATED contract (RE1 anchor 6.025,10.0; corner-(0,0)
chamfer 13.2) + the v5_5 J1-flip ledger. Gate: **PASS — 63/63 assertions
(was 62; +1 = the new band/usb_recept gate), 0 failed, interference list =
exactly the 4 documented proxy/knob entries.** The §ERRATUM resolution
landed: the EC11 body/knob now derive shaft-true from the contract
(anchor + (7.5,2.5) = 13.525,12.5 = the design constant; asserted rot-0),
so board truth and the ordered plate's opening coincide and the gate class
that was blind in v4 is structurally closed.

What changed (all in `agentpad13_case_v2.py`; provenance tag [V5]):

1. **Per-corner chamfer legs.** `CHAMFER_LEG=14.6` (hardcoded) replaced by
   `_corner_leg()` reading the contract octagon (L1 distance corner→nearest
   vertex). The (0,0) corner is 13.2; the other three stay 14.6.
2. **Boss notch (tray).** Any corner boss whose round-profile slip falls
   under 0.3 gets a 45° flat, NOTCH_CLEAR=0.35 back from the chamfer line,
   spanning z −1.85..+1.5 only (full-round below: cross-section only
   shrinks going up — prints clean; EFC untouched). At (3.7,3.7): round
   slip −0.649 → flat at 3.751 from center; **insert-bore wall thins to
   1.40 at one azimuth** after the Voron M3×4×5 cavity update (first-article
   watch: check for bulge at the flat when setting the insert). Other three
   corners keep 0.341 round slip — machine-checked per corner.
3. **USB flip [V5].** `usb_receptacle()` envelope is the flipped J1: x
   37.3..46.9 (9.6 wide, body incl. peg lugs), y −0.49..6.81 — mouth
   0.49 mm PROUD of the y=0 board edge (THE convergence number with the
   board executor's v5_5 ledger), z −4.86..−1.6 (flip-invariant). A sign
   tripwire asserts the face sits outside the board edge: a wrong-direction
   flip would otherwise pass every interference gate VACUOUSLY (the exact
   blindness class that shipped the original backwards connector).
   **Band geometry UNCHANGED** — aperture Ø10.0 z −5.0..−1.4 swallows the
   proud mouth: new load-bearing gate band/usb_recept ≥ 0.1 (measured ~0.2
   x-sides/top, 0.14 aperture-sill); usb_recept/tray 0.24 carries.
   Proof of band invariance: re-exported `stl/agentpad13_v2_band_1.6mm.stl`
   is md5-IDENTICAL to the ordered-geometry file (36980cc2ff011dc32d923f
   b04f7429f7) — the PCBWay band upload stays byte-valid.
4. **JS1 envelope [R].** The hand-made `JS1_PSP_slider` footprint draws BOTH
   an 18.6 sq F.Fab bbox AND a Ø15 F.Fab circle; the hard-gated `js_body`
   is now Ø15 cage (the author's own frame model) + Ø12 nub through the
   Ø16 aperture, both heights [PROVISIONAL]. **v2.2 CATCH (the ERRATUM's
   JS1 warning materialized):** the F.Fab bbox's SE corner overhangs the
   chamfered NE board corner into the screw-stack void — measured overlaps
   tray boss 21.77 mm³ / band cap 16.38 / SCREW SHAFT 4.92 (a screw through
   the module bbox = no case-side fix; the ordered plate's hole pattern
   would be invalid). Advisory probe `[JS-CALIPER-PROBE]` reproduces these
   volumes every build. **Caliper decision rule (gates the band order, §8.5
   verbatim): cage reach from module center toward bearing (80.5,3.7) at
   z ≤ 3.4 must be ≤ 8.1 mm** (boss axis is 13.19 away; Ø15 model = 7.5).
   Beyond 8.1 → STOP: NE screw-stack redesign. Also caliper cage height
   (JS_FRAME_H=3.0 provisional; ≥ 3.15 fails the 0.25 plate gate — escalate,
   do not tune) and nub Ø (12.0 provisional vs Ø16 aperture).
5. **Component envelopes [S] carried, not regenerated.** Between v4_r27 and
   v5 only copper plus the RE1/J1 footprints moved, and NEITHER resolves a
   3D model in the STEP (both are hand keep-outs here) — the module was
   verified to contain no EC11/JS/J1/USB solid. Also hand-verified: no
   bottom-side component bbox intersects the flipped J1 body region
   (x 37.3–46.9, y −0.49–6.81; nearest = U4/SOT-23-6 at y ≥ 7.8, 0.99
   clear). Re-verify by `gen_components_v2.py` regen-diff from the v5_5
   STEP when it banks.

Exports (khana build, this session): `stl/step agentpad13_v2_tray_v5.*`
(NEW — notched; the un-suffixed tray files remain the pre-notch record; do
NOT print those for a v5 board), band re-emitted byte-identical (above),
plate STEP unchanged geometry, outputs/case/ regenerated (mechanism.json
status ok 63/63; printability advisories bit-identical to v2.1: band
0.642/829.7/90°, tray 0.051/63.2/90°).

Fitment renders (Desktop, from the actual part solids): v22_assembled_iso
(full stack + lid-off top-down: red mouth visibly proud at y=0, 13.2 corner
visibly smaller), v22_section_usb (x=42.1: mouth crosses the wall plane
into the aperture), v22_section_encoder (y=12.5: body centered on 13.525),
v22_corner_notch (plan z=−0.75: flat vs chamfer, 0.35 gap). The USB section
+ lid-off view are the case-side member of the "orientation is invisible to
numeric gates" detector class — keep them in every future J1-touching pass.

Open items delta vs §8: #5 (JS1) is now the SHARPENED caliper rule above
and explicitly gates the band order; new watch-item: notch-azimuth insert
wall 1.65 (first-article). Everything else carries.

Variant note (owner question, answered): the translucent/opaque PCB SKUs
differ only in POPULATION (fabpack policy); the case geometry is ONE build
for both. Band material (frosted resin vs opaque FDM) is a print/order-time
choice on the SAME byte-identical geometry — with §8.9's standing caveat
that an opaque band has no underglow light channel.

### 12.1 v2.2.1 — proud 0.49 → 0.60 (authorized v5_5 run, anchor 3.05)

The executor's authorized run landed J1 at anchor y 3.05 (face 0.60 proud,
0.11 more than the §12 plan value). Case-side max-proud audit: the band
aperture is a full through-wall VOID (inner face −0.3 to outer face −2.7)
— no case material in front of the mouth until the outer wall plane, so
0.60 is deep in-range; plug seating IMPROVES (shell bridges 2.10 of wall
vs 2.21). `USB_FACE_PROUD = 0.60` baked; khana re-run **63/63, 0 failed**;
band AND tray_v5 exports byte-identical (md5 36980cc2… / 72f39e25…) — the
change touches only the envelope model and gates, no printed part.
Renders regenerated with the 0.60 annotation. Envelope now y −0.60..6.70
(rear margin to U4 grows 0.99 → 1.10).

## 13. v2.3 — perimeter support rail (owner directive, 2026-07-19)

Owner: the 3-boss floating support is not believable under key presses,
"especially at the top part of the board … use the tray to support at least
some perimeter of the board where there are no populated parts." Agreed —
the band's top-rim ledge already exploits exactly that clear zone; v2.3
mirrors it from below.

**Design.** New assembly part `pcb_rail`: a 1.5 mm-wide rim shelf, outboard
face 0.2 inboard of the octagon edge, rising tray floor (−5.1) → board
underside (−1.51, the SAME plane as the three support bosses). Segmented
around every occupied bottom-side zone, all machine-cut from live data:
STEP component envelopes +0.75, the 10 side-fire underglow LEDs +1.0, the
flipped J1 body +0.75 [V5], RE1's five through-hole solder tails r2.75.
**Coverage: 86 % of the rim ring survives** (1520/1770 mm³) — including
BOTH top chamfer diagonals, so the encoder corner and the JS corner rest
directly on tray material; the top edge is supported everywhere except the
J1 window and the small R/D cluster east of it. Board vertical state is
now: rim + 3 bosses below (0 gap), switches (0) / band ledge (0.3) above.

**Why a separate part** (not `tray`, not `pcb_retention`): the rail touches
`pcb_board` BY DESIGN, so it cannot share tray's ≥0.3 board gate (that gate
is the boss/chamfer spec); and it passes legitimately under the EC11/JS
corners, so it cannot share pcb_retention's ≥5.0 pin stay-away gates. It
gets its own gates (≥0.3 vs pcb_components / leds / usb_recept) plus full
pairwise no-interference membership, and unions into the printed tray at
export. Gate run: **78/78 assertions, 0 failed**, interference list = the 4
documented proxies.

**khana catch during the pass (defense-in-depth receipt):** the first rail
build FAILED — tray×pcb_rail 2.79 mm³. The v2.2 boss notch was deliberately
shallow (z ≥ −1.85, board-passage only), leaving the LOWER boss full-round,
which bulged 0.65 past the chamfer line straight through the rail's corner
segment. Fix: NOTCH_Z0 → full boss height. Cost: the 1.65 insert-wall
azimuth now runs the full insert depth (was its top 3.4 mm) — same PETG
watch-item, first-article check unchanged.

Exports: `stl/step agentpad13_v2_tray_v5.*` REGENERATED (now notch-full +
rail; md5 32401124206819b84a66bf520d133f01 — supersedes the rail-less
72f39e25 build of earlier today; nothing printed yet, no waste). Band
byte-identical still (36980cc2…). New render: `v23_rail_map.png` (plan at
z=−2.5: rail segments + every skip labeled); encoder section updated to
show the rim resting on the rail. Print note: the rail is a 1.5-wide,
3.59-tall perimeter wall on the floor — upright FDM trivial; slicer-preview
the LED-gap ends like the other advisories.

## 14. v5 plate refab — YA13 joystick opening (2026-07-20, this session)

ONE geometry change to the three ORDERABLE plate variants: the v4 Ø16 circular
JS aperture is replaced by an ASYMMETRIC rounded-rect opening for the YTL YA13
joystick. Everything else on the plate is byte-for-byte unchanged. All outputs
are `_v5`-suffixed; **every Rev-A ordered file stays UNTOUCHED on disk**
(timestamps verified still 2026-07-18; same precedent as the `tray_v5` rename).

**The change.** DELETE the JS circle Ø16 @ (70.675, 12.5) (`C.JS1`,
`C.JS_APERTURE`). ADD a rounded rectangle (R1.5, house style = the encoder
opening) because the YA13's full-height body + its West/North-facing pot boxes
+ retention tabs all pass THROUGH the 1.6 mm plate band — a centered circle no
longer clears them (drawing-verified this session).

**Frozen numbers + provenance** (placement study + datasheet height extraction,
this session; all in board coords, y-down):

| edge | value | derivation |
|---|---|---|
| stick anchor (part origin) | (69.71, 13.37) | placement study; pot boxes clock W+N |
| West  x | **58.91** | anchor.x − 10.80 (pot box + tabs 10.5 + 0.25 clr + 0.05 round) |
| North y | **2.57**  | anchor.y − 10.80 (same W/N bias) |
| East  x | **77.36** | anchor.x + 7.65 (body bbox half 7.4 + 0.25 clr) |
| South y | **21.02** | anchor.y + 7.65 |
| corner R | 1.5 | house style (matches encoder opening) |

Opening is 18.45 × 18.45, offset NW of the anchor (the W/N pot-box/tab bias).

**Source of truth.** Edits are confined to `gen_plate_fab.py` (the plate-geom
generator): named constants `JS_OPEN_{W,N,E,S}_X/Y`, `JS_OPEN_R`,
`TENTED_RING_D` with full provenance comments; the Ø16 `circle()` call swapped
for a `rounded_rect()` on those constants; a `silk_ring()` helper + a
`tented_ring` touch mode reproducing the Rev-A cheap-finish variant (tented
disc, no F.Mask opening, + a Ø16/0.2 front-silk ring marker). `__main__` now
emits ONLY the three plate variants, all `_v5`; the coupon/touch-chip/DXF
generators are preserved but not re-run (their Rev-A files are the record).
`agentpad13_case_v2.py` (the 3D/mechanism source) was NOT touched — its
`fr4_plate()` still models the Ø16; the ordered plate is the fab file, and the
next case pass should mirror this opening when the JS envelope is metered
(carries §8.5 + §12.4). `ruff check`: clean.

**Files produced** (`hardware/case/v2/fab/`, all NEW):
- `agentpad13_v2_plate_v5.kicad_pcb` — default (exposed Ø12 gold disc); md5 `9e488bbe3fd839d4f71e66a96ab3d532`
- `agentpad13_v2_plate_tented_ring_v5.kicad_pcb` — tented + Ø16 silk ring; md5 `0a2603c5fe151b845e8ac21a7271c16a`
- `agentpad13_v2_plate_blank_v5.kicad_pcb` — no copper; md5 `d2dbab7b77ac748192141cae6a7b55d5`
- `plate_v5_gerbers.zip` / `plate_v5_ring_gerbers.zip` / `plate_v5_blank_gerbers.zip` — 10 files each (7 gerbers + PTH/NPTH + gbrjob), kicad-cli 9.0.9 defaults (FSLAX46Y46, mm, Protel ext), identical settings + file-set to the Rev-A export; PTH holes 2/2/0 (the TP5 vias; blank has none)
- `agentpad13_v2_plate_v5_top.svg` + `agentpad13_v2_plate_v5_top.png` — default top view (eyeball check: new opening beside the encoder opening)
- `agentpad13_v2_plate_v5.dxf` — Edge.Cuts DXF (kicad-cli, from the v5 board — NOT the stale build123d path)
- `validate_fab_v5.py` — the pcbnew reload gate (reproducible), alongside the generator

The tented_ring_v5 file differs from plate_v5 by EXACTLY one line (F.Mask Ø12
opening → F.SilkS Ø16 ring) — same single-line delta as the Rev-A pair.

**Gates (verbatim, pcbnew 9.0.9 reload — IDENTICAL across all three variants
except the per-variant touch-marker line):**

> **⚠ SUPERSEDED TRANSCRIPT (annotated 2026-08-05, §19).** This block is the
> **PRE-TRIM** run of 2026-07-20 and is kept as the historical record. The
> owner's long-axis fab-cap trim of the NEXT DAY (2026-07-21, §19) moved exactly
> two numbers in it:
>
> - `[bbox] ... 84.400 x 100.200 mm  (x -0.100..84.300, y -0.100..100.100)`
>   → **`84.400 x 100.000 mm  (x -0.100..84.300, y 0.000..100.000)`**
> - `[web] N->plate-top = 2.670   (expect ~2.67)`
>   → **`2.570   (expect ~2.57)`** — the plate's north edge came in 0.1 mm, so
>   the web from it to the frozen JS-opening north edge (y = 2.57) shrinks by
>   the same 0.1.
>
> **Everything else in the block still stands, verbatim and unchanged**, and that
> is the point of the trim: `[count] Edge.Cuts shapes = 89`, the whole
> `[JS opening]` block, `[encoder]`, `[SW13]`, the screw holes, and
> `[web] NE->screw = 1.555` / `S->switch = 3.680` / `nearest feature W = 3.979`.
> The three web numbers are all measured **from the joystick opening**, which the
> trim did not touch — only `N->plate-top` references the moved edge.
> `validate_fab_v5.py` itself was updated with the trim and now asserts
> `PLATE_WH = (84.40, 100.00)` and `near(d_top, 2.57, 0.02)`. See §19 for the
> post-trim gate run.

    [bbox]  Edge.Cuts centerline = 84.400 x 100.200 mm  (x -0.100..84.300, y -0.100..100.100)
    [count] Edge.Cuts shapes = 89                         (was 82: -1 circle +8 rect-opening)
    [JS opening] 4 lines + 4 arcs; extents W=58.910 N=2.570 E=77.360 S=21.020
        edge (58.910,19.520)->(58.910,4.070)   West
        edge (60.410, 2.570)->(75.860, 2.570)  North
        edge (75.860,21.020)->(60.410,21.020)  South
        edge (77.360, 4.070)->(77.360,19.520)  East
    v4 Ø16 circle @ (70.675,12.5) is GONE
    [encoder] center (13.525,12.500) size 13.000x13.000   UNCHANGED
    [SW13]    cutout center (42.100,88.850) size 14.000x14.000 + stab L (30.162,89.47) / R (54.038,89.47) 6.65x12.3  UNCHANGED
    screw holes Ø3.2 @ (3.7,3.7) and (80.5,3.7) present
    [web] N->plate-top       = 2.670   (expect ~2.67)         PASS
    [web] NE->screw(80.5,3.7) = 1.555   (floor 1.5; brief ~1.74) PASS floor
    [web] S->nearest switch   = 3.680 @ SW(70.675,31.7) (floor 2.0) PASS
    [web] nearest feature W   = 3.979 @ SW(51.625,31.7)
    RESULT: ALL GATES PASS   (3/3 variants)

**Note (one soft deviation, flagged — not a stop-condition).** The NE-corner→
(80.5,3.7)-screw web computes **1.555 mm**, not the brief's ≈1.74 estimate. Root
cause: 1.74 corresponds to East x = 77.16 (bbox 7.4 + **0.05** clr), whereas the
frozen East x = 77.36 uses **+0.25** clr; the two brief figures are internally
inconsistent. Implemented the frozen edge (77.36) exactly as directed — it still
clears the hard 1.5 floor (by 0.055). The other webs land clear (N→top exactly
2.67; S→switch 3.68 > the ≈3.0 estimate, floor 2.0). If the 0.055 margin is too
tight for the router near a Ø3.2 hole, the one-line lever is East x → 77.16
(−0.20, recovering ≈1.74) — owner call; the opening would then be 18.25 wide.
No other geometry drifts.

### §14 addendum — coordinator ruling on the East-edge deviation (2026-07-20)
KEEP East x = 77.36 (the honest +0.25 part clearance). The resulting NE->screw
web of 1.555 clears the 1.5 floor AND exceeds the shipped Rev-A precedent
(plate_hole_edge_web = 1.537). The 1.74 expectation in the brief was my
arithmetic slip (+0.05 vs +0.25 clearance), not a geometry problem. No rework.
Carry-forward: agentpad13_case_v2.py fr4_plate() still models the old Ø16 —
the E2E fitment pass MUST mirror the v5 opening (W58.91/N2.57/E77.36/S21.02,
R1.5) before its gates count.

## 15. v2.4 — TRUE E2E fitment (populated hardware, 2026-07-20, this session)

The directive: "do complete fitment ... simulate complete assembly ... make
sure the populated board and switches and everything don't clash with anywhere
on the case." Every past miss (encoder-anchor-as-shaft, the joystick hole, the
slider disc) happened where a model was ASSUMED not DERIVED. v2.4 models the
populated hardware and every envelope cites its source; anything unsourced gets
a loud print, not silence.

**Gate result (verbatim):** `khana` mechanism.json **status=ok, 101
assertions, 101 passed, 0 failed** (was 78 in v2.3; +23 for the new
populated-hardware gates). 20 parts. Interferences list = 9, ALL expected:
the 3 board-resident proxy overlaps (components/sockets/leds, out of case
scope, v1 line), the asserted coaxial `ec11_body×knob_sweep` (342.2), plus
the by-design `js_body×js_sweep` (25.3 stick emerging from body),
`knob_sweep×knob` (2417, the accurate knob inside the swept proxy),
`js_sweep×stick_cap` (549.8, envelope contains the rest pose), and
`switch_bodies×keycaps` (500.3, keycap sits on the switch stem) — none of
those are asserted (they MUST overlap). Ruff clean.

**Changes to `agentpad13_case_v2.py` (v2.4 / [YA13] tags):**
1. **Plate opening mirror.** `fr4_plate()` cuts the YA13 asymmetric rounded
   rect (W58.91/N2.57/E77.36/S21.02 R1.5) from named constants, replacing the
   Ø16 circle. A standalone parse of the ORDERED fab file
   (`fab/agentpad13_v2_plate_v5.kicad_pcb`) confirms the extents match EXACTLY
   (see resweep below). JS1 read from the contract = (69.71,13.37) [C].
2. **Joystick → YA13 (drawing/board-derived, all slider code retired).**
   - `js_body`: faithful CROSS (13x13 frame + W/N pot boxes + E/S corner-tab
     bumps, z 0..11.1), NOT a filled bbox — the pots sit on the W+N faces so
     the bbox corners are void. Reaches W/N 10.5, E/S 7.4 [ext report + F.Fab].
   - `js_pins`: the 10 THT tails, positions+Ø PARSED from the banked v5_6
     (md5-guarded, footprint-pose-guarded), tails to z −3.71.
   - `js_sweep`: the REAL dome-cap swept 30° tilt cone (union of 24 azimuths +
     upright), pivot z 6.1 — replaces the Ø15x8 proxy. South reach 11.279,
     lowest z 10.038 (== stick_cap_params `sweep_lowest_z`).
   - retired: `js_ffab_probe`, the JS-CALIPER-PROBE prints, JS_APERTURE /
     JS_BODY_D / JS_FRAME_H / JS_NUB_D / JS_FFAB_SQ / JS_SWEEP_*.
3. **New populated parts:** `switch_bodies` (13 MX envelopes: lower 13.9 /
   flange 15.8 / upper 14.8 / stem Ø7), `keycaps` (12x 1U 18.0 + 1x 2U 37.1,
   z 10.6..14.6), `knob` (static Ø18 z 8.0..17.5, consumed from
   encoder_knob_params default), `stick_cap` (static dome Ø13 z 14.4..19.6,
   consumed from stick_cap_params default).
4. **Rail change (item 6, empirically required).** `pcb_rail()` now skips the
   YA13 THT pin tails — the de-risk measured **8.03 mm^3** rail overlap at the
   MP2 lug tail near the NE chamfer (JS1 is a hand keep-out, not in the STEP,
   so it was never skipped). Rail rim coverage 86% -> **84%**. Band UNTOUCHED.

**Findings (the E2E payoff — three clash questions, all DERIVED):**
- **(RESOLVED) js_body vs the NE screw boss** — the §12.4/§8.5 caliper item.
  The faithful cross-body clears the Ø9.5 boss (80.5,3.7) by **0.584 mm**.
  The old Ø15-cage gate was BLIND to the square frame's corner (the cage
  r7.5 undershoots the frame corner at 9.19 from center); at the OLD JS1
  (70.675,12.5) the frame NE corner would have sat **0.71 mm INSIDE** the
  boss. The adjudicated SW move of JS1 to (69.71,13.37) is what pulled it
  clear. Caliper watch retired — the hard gate now measures the real corner.
- **(RESOLVED) js_pins vs the perimeter rail** — 8.03 mm^3 overlap at MP2
  without a skip; fixed by the rail skip above; gate now clears **0.750 mm**.
- **(OPEN — owner/topper decision, unfixable case-side) js_sweep vs the SW4
  keycap.** THE joystick-clearance finding the directive named. The dome cap
  at FULL 30° tilt toward SW4 (70.675,31.7) reaches y=24.65 at z≈12.6; the
  SW4 keycap edge is at y=22.7 -> **40.78 mm^3 overlap (~1.95 mm graze)**.
  Modeled from stick_cap_params (pivot 6.1, tilt 30°, dome Ø13) + the
  contract SW4 position + an 18.0 keycap — nothing assumed. This is a REAL
  clash, NOT a modelling artifact; every cap variant (knurl Ø12 / dish Ø14)
  clashes similarly (the cap-cylinder wall at z14.4..17.4 swings into the
  10.6..14.6 keycap band). It is unfixable on the case side (the case
  controls neither the stick tilt nor the keycap). It is therefore NOT gated
  (a hard assert would abort the other 100 gates); it is a loud measured
  advisory (`[v2.4-JS-KEYCAP]` print + `js_sweep×keycaps` in the interference
  list, centroid 69.71/23.31/12.67). **Levers for the owner:** (a) accept the
  light graze — real caps taper/relieve at the edge and full-tilt-into-a-key
  is a corner case; (b) cap the effective stick deflection toward that key;
  (c) a shorter stick cap. All are topper/product calls, not case geometry.

**Hole-vs-copper resweep (item 5 — the SE-lug lesson, independent confirm).**
Standalone parse of v5_6 (md5-guarded): all 10 JS1 THT holes vs ALL foreign-
net copper on both layers (1119 segments + 182 vias + 442 foreign pads,
15842 pairs). **0 pairs below the 0.152 floor; global tightest = 0.2740 mm**
(JS1 pad 2/3 vs an RGB_D16 F.Cu trace at ~0.274; next 0.2783). The board
executor's clearances hold. Same script asserts the fab plate_v5 opening =
58.910/2.570/77.360/21.020 (§14 exact).

**[PROVISIONAL] / assumptions flagged (none block the build):**
- `JS_POT_HALF=4.5` (pot-box / E-S-tab half width) is a CONSERVATIVE envelope
  covering the 3 THT pot pads + margin, not a metered pot-box width; refine
  from the YA13 mechanical drawing before the resin band order. Does not gate
  (the binding faces are the frame + pad-covering arms).
- The **30° tilt** drives the SW4 finding; it is the stick_cap_params [brief]
  value. If the physical YA13 deflects less than ~15.5°, the graze vanishes;
  above that it clashes. Confirm the real mechanical tilt limit.
- Keycaps 18.0 / 37.1 are [CONVENTION] (1U pitch 19.05 − ~1.05; 2U = 1U +
  19.05); MX body dims are [MX]/[D] standard.

**Tightest 5 whole-assembly margins (mm):** band/usb_recept **0.140**
(carried v2.2, aperture sill), usb_recept/tray **0.240** (carried),
js_body/plate-opening **0.250** (NEW — YA13 E/S tabs to the opening edges),
head_to_plate_edge **0.287** (carried corner), band/pcb_board **0.300**
(carried). Next: pcb_chamfer_slip 0.341/0.350, knob-hides-opening +0.430,
js_body/NE-boss 0.584, js_pins/tray 0.718, js_pins/rail 0.750.

**Exports.** Band re-emitted **byte-identical** (md5
`36980cc2ff011dc32d923fb04f7429f7` — the PCBWay upload stays valid; HARD
gate held). `tray_v5` md5 CHANGED `32401124...` -> `d7d16481df24bae4c7769d762
4dfc620` (the JS1 rail skip; nothing printed yet, no waste). Plate STEP
re-emitted with the new opening (record only; the ordered fab .kicad_pcb were
NOT touched). Printability advisories: band 0.642/829.7/90° (bit-identical);
tray 0.051/76.88/90° (overhang area 63.2 -> 76.88, the new rail-skip edges;
min_wall unchanged) — both the §8.7/§8.8 documented classes, slicer-preview
before print.

**Render inventory** (`/Users/yuanz/Desktop/v24_*.png`, extract-tessellate-
render pipeline): `v24_assembled_iso` (full populated stack + lid-off
top-down), `v24_side_elevations` (true ortho front x-z + side y-z of the
complete assembly), `v24_section_controls` (encoder y=12.5 + joystick y=13.37,
x-z), `v24_section_stickcol` (x=69.71 y-z — cap sweep vs SW4 keycap),
`v24_section_usb` (x=42.1), `v24_corner_notch` (plan z=−0.75), `v24_js_zone`
(the zoom: opening edges vs body vs tabs vs cap sweep vs SW4 keycap). All read
and orientation-verified.

**v2.5 — TAPER stick-cap variant (SW4-clearing, lever (c), 2026-07-20).** The
§15 SW4 graze is unfixable case-side but IS fixable topper-side (lever (c), "a
shorter/relieved stick cap"). Added ONE new variant to
`toppers/stick_cap.py` — `taper` — WITHOUT touching the dome/dish/knurl
families or the default (still `dome`; owner picks). The graze binds at the
cap's OUTER WALL, not the rim (a chamfer was proven impotent). Derivation
(reproduced, not trusted): a rest-frame cap point at radius r, cap-frame height
h, rigidly tilted 30° toward SW4 about the pivot (z=6.1) reaches
`world_y = 13.37 + r·cos30 + (h−6.1)·sin30`; the SW4 keycap near edge is
`31.7 − 18.0/2 = 22.7`, so no-touch requires `r·cos30 + (h−6.1)·sin30 ≤ 9.33`,
and `≤ 9.08` gives the +0.25 clearance target. That envelope is LINEAR in h
(slope −tan30) → the clearing wall is a **straight cone at 30° from vertical**
(parallel to the tilt cone). The taper is that +0.25 envelope shrunk 0.05 mm
uniformly in radius: **bottom Ø11.285 @z14.4 → Ø6.667 @z18.4 (dome spring),
then a spherical dome roof to +19.6 (1.2 mm over the blade tip at +18.4)**.
Socket identical to the other variants (mouth +14.4, roof +18.4, 3-rung fit
ladder 1.85×1.15 / +0.05 / +0.10); min socket wall 2.358 (@ the spring).
**Verified through the §15 harness** (the exact `js_sweep` 24-azimuth swept
solid ∩ SW4 keycap box — the same construction that measures 40.784 mm³ for
the dome): **taper swept-solid overlap = 0.0000 mm³, min clearance = +0.293 mm
(uniform along the cone), deck-floor z_low 10.467 (margin +4.867)**. Wall is
inward-going so the outer surface is fully self-supporting on the bed (only the
socket-roof bridge overhangs, as with every family). Exports: 3 taper STLs
(`stick_cap_taper_sock_{nom,p05,p10}.stl`); `stick_cap_params.json` gains the
`taper` variant with its sweep params (default field UNCHANGED). Renders:
`toppers/renders/stick_caps.png` re-rendered with the 4th (taper) row, plus
`/Users/yuanz/Desktop/v25_cap_taper_vs_dome.png` (dome vs taper, side profile +
top, for the owner's look call). Band and all board/plate/fabpack files
UNTOUCHED; the case model still consumes the default dome, so no khana rebuild.

**v2.5 DEFAULT FLIP — dome → taper + case re-gate (2026-07-20, release-packaging
executor).** Coordinator ruling (recorded here per brief): the release DEFAULT
stick cap = **taper** — the only variant satisfying the owner's "make sure it
won't hit a key" (the sole cap whose wall clears the SW4 keycap at full 30°
tilt). dome/dish/knurl SHIP AS ALTERNATES; **dome carries the >15.8°-tilt SW4
graze caveat** (below ~15.5–15.8° tilt the dome clears SW4; above it grazes,
reaching ~1.95 mm overlap at full 30°). One-word flip, fully re-verified.
Changes:
1. `toppers/params/stick_cap_params.json`: `default_variant` "dome" → "taper".
2. `toppers/stick_cap.py`: `DEFAULT_VARIANT` "dome" → "taper" — kept in sync with
   the params JSON so a topper regen cannot silently revert the release default.
   This is a consistency edit BEYOND the coordinator's literal step-1 file list
   (which named only the JSON); ledgered here as a deliberate deviation. No STL
   bytes change (all 4 families × 3 rungs still emitted; only the emitted
   `default_variant` field differs), and stick_cap.py was NOT re-run this session.
3. `agentpad13_case_v2.py` (v2.5): `stick_cap` (rest pose) + `js_sweep` (tilt
   cone) now CONSUME the taper profile — a straight 30°-from-vertical cone,
   bottom Ø11.285 @+14.4 → Ø6.667 @+18.4 (dome spring), then a spherical dome
   roof to +19.6. `_dome_cap` retained as the alternate/fallback; new `_taper_cap`
   + `_cap_solid` dispatch (keyed on the consumed `top_style`) mirror the OUTER
   profile of `toppers/stick_cap.py _taper_body`. `loft` added to imports. The
   v2.4 `[v2.4-JS-KEYCAP]` STOP-CONDITION advisory is replaced by the green
   `[v2.5-JS-KEYCAP]` report; the `keycaps × js_sweep` pair stays NON-asserted
   (an alternate dome/dish/knurl cap would still graze, so gating it would abort
   the other 100 gates).
**Gate (verbatim, `khana build agentpad13_case_v2.py`):** mechanism.json
**status=ok, 101 assertions, 101 passed, 0 failed**; interferences 9 → **8** (the
dome `js_sweep×keycaps` 40.78 mm³ SW4 graze is GONE; the remaining 8 are all the
by-design/board-proxy overlaps — components/sockets/leds, knob_sweep×ec11_body,
js_body×js_sweep, knob_sweep×knob, js_sweep×stick_cap, switch_bodies×keycaps).
`[v2.5-SWEEP] cap sweep south reach from stick = 9.037` (taper; v2.4 dome was
11.279), `lowest z = 10.467` (margin +4.867 vs the 5.6 deck floor).
`[v2.5-JS-KEYCAP] js_sweep x keycaps overlap = 0.00 mm^3 ; taper wall -> SW4
keycap edge (22.7) clearance = +0.293 mm`. These three numbers reproduce the
`toppers/stick_cap.py` taper harness (south reach 9.037, sweep_lowest_z 10.467,
sw4_min_clearance 0.2933) EXACTLY — independent confirmation the case-model taper
solid is geometrically faithful.
**HARD GATES HELD:** band STL md5 **36980cc2ff011dc32d923fb04f7429f7** UNCHANGED
(the PCBWay/resin upload stays valid); tray_v5 STL md5
**d7d16481df24bae4c7769d7624dfc620** UNCHANGED (the cap touches neither export).
Ruff clean. No topper re-run (taper STLs + params already exist from the v2.5
topper add). Band / plate / tray / fabpack all UNTOUCHED. ORDER HOLD STANDS.

---

### §15 addendum — optional PORON ledge-gasket kit (2026-07-20, owner-approved)

A small paper/foam accessory added this session. **NO design geometry change
anywhere** — the band/tray/plate/board `.py`, STEP and STL files are byte-for-
byte untouched. **Band STL md5 RE-VERIFIED this session =
`36980cc2ff011dc32d923fb04f7429f7`** (matches the ordered geometry; the gasket
generator asserts this hash before it emits anything).

**What it is.** The band's rabbet ledge (`band()`: `LEDGE_W = 1.2` wide,
underside at `LEDGE_Z0 = +0.3` above the PCB top rim) gets optional user-cut
`0.5 mm` adhesive PORON segments stuck to its **underside**. `0.5 mm` foam into
the `0.3 mm` gap = `(0.5−0.3)/0.5` = **40 %** compression (PORON's `20–50 %`
sweet spot) → a gentle downward preload on the board rim. The bare `0.3 mm`
ledge is already the backstop, so the kit is purely optional and reversible.

**Derived, not retyped.** `gasket/gen_gasket.py` PARSES `LEDGE_W`, `LEDGE_Z0`,
`PCB_CLEARANCE`, `WALL`, `OUTER_R`, `BOSS_C`, `BOSS_OD`, `SOCKET_SLIP`,
`USB_CUTOUT_W` from `agentpad13_case_v2.py` and `PCB_W/PCB_H/J1.x/octagon` from
`contract_v4.json` (the model's own sources), recomputes the ledge ring with the
module's formulas, and self-checks against the inline comment values. Ledge ring
(board coords, centre 42.1,50.0): OUTER `84.8 × 100.6`, R`5.6` (= band inner wall
`INNER_W/H/R`); INNER `82.4 × 98.2`, R`4.4` (= `INNER_ − 2·LEDGE_W`). The ledge
overhangs the PCB rim by `LEDGE_W − PCB_CLEARANCE = 0.9 mm` (the preload strip).
Empirical cross-check: the band STL was plane-sliced (y=50 / x=25 / x=60) — the
ledge underside is a **flat `z = 0.300` face** the full `1.2 mm` width on all four
sides (the code's inner-edge chamfer was OCCT-refused → left square), so there is
a real flat face to bond to.

**Segments (10):** `~15 × 1.2 mm`, clear of the corner caps
(`BOSS_CENTERS ± SOCKET_D`) and the USB span (`42.1 ± 5`, +1 mm margin):
`W×3` and `E×3` at y = 25/50/75; `N×2` and `S×2` at x = 24.9/59.3 (north's pair
straddles the USB). Total foam ≈ `180 mm²` (a `100 × 100` sheet is many-fold
surplus). Layout asserts (clear-run + strip-containment) all pass.

**Deliverables** (in `hardware/case/v2/gasket/`, copied to
`v5-release-compiled/hardware/case/v2/gasket/`): `gasket_template.svg` (1:1 mm),
`gasket_template.pdf` (1:1 — PyMuPDF re-measured the page box at exactly
`190.000 × 250.000 mm`), `gasket_template.png` (preview), `gasket_segments.dxf`
(10 closed rects, mm, ezdxf-audit-clean), `README.md`, `gen_gasket.py`. Nothing
is fab-ordered; the ORDER HOLD is unaffected.

---

## 16. v2.6 — band sidewall 2.4 → 3.0 + USB port funnel (2026-07-23)

**Trigger.** PCBWay's 3D-print review of the uploaded band
(`agentpad13_v2_band_1.6mm.stl`, order prefix `C-Y15W1075301A_`) flagged the four
corner crescents — the `0.737 mm` zone this ledger has documented as COSMETIC
since §3/§8 — as *"too thin, may break"*. **Owner ruling (2026-07-23):** thicken
the sidewall — *"increase the sidewall thickness by some amount; might even look
better thicker (more visible diffuser)"*.

**GATE RETIREMENT (owner order).** The band **md5-invariance gate**
`36980cc2ff011dc32d923fb04f7429f7` is **RETIRED**. That hash is now the record of
the SUPERSEDED 2.4-wall band; the file stays on disk as the historical artifact
and **must NOT be printed**. Every downstream copy of the gate is updated:
`gasket/gen_gasket.py` §3 no longer asserts hash equality (it re-measures the
ledge from whichever band matches the current `WALL` instead), and this ledger,
`gasket/README.md` and `v5/V5-NOTES.md` carry the retirement note.

### 16.1 The change (one parameter + one freeze)

```
WALL     2.4 -> 3.0     the single owner-tunable sidewall parameter
INNER_R  OUTER_R - WALL  ->  FROZEN 5.6
```

The freeze is **not cosmetic** — it is what makes the wall a safe knob. `INNER_R`
was WALL-derived, and two frozen artifacts hang off it:
`PLATE_R = INNER_R - PLATE_GROOVE = 5.4` (the **ordered** FR4 plate's corner
radius) and `TRAY_R = INNER_R - TRAY_SLIP = 5.35` (the banked `tray_v5` STL,
md5 `d7d16481df24bae4c7769d7624dfc620` — **superseded 2026-08-19 by
`2e4d510381c7a4420d46ce741a22fe22`, v2.8 base pockets; `TRAY_R` itself did not
move, see §21**). Letting `INNER_R` follow WALL to 5.0
would have silently re-cut both and broken this session's own gates. `OUTER_R`
stays 8.0 (owner sign-off "fillet ~R8"), so the inner and outer corner arcs are
no longer concentric: the outer arc centre slides outboard by `WALL - 2.4` per
axis and the corner wall becomes **thicker** than the flat, never thinner
(3.000 on the flats → 3.249 on the diagonal at WALL 3.0).

### 16.2 Derivation chain — every band mating interface (source-read)

| interface | expression in `band()` | depends on | moved? |
|---|---|---|---|
| cavity opening | `_rprism(INNER_W, INNER_H, INNER_R, …)` | `PCB_W/H + 2·PCB_CLEARANCE`, frozen `INNER_R` | **no** |
| 1.2 rabbet ledge | `_rprism(INNER_W-2·LEDGE_W, INNER_H-2·LEDGE_W, INNER_R-LEDGE_W, LEDGE_Z0 … Z_PLATE_BOT)` | same + consts | **no** |
| plate recess | `_rprism(PLATE_W+2·PLATE_FIT, PLATE_H+2·PLATE_FIT, PLATE_R+PLATE_FIT, Z_PLATE_BOT … Z_PLATE_TOP)` | `INNER_*` − `PLATE_GROOVE`, consts | **no** |
| boss sockets | `_z_cyl(SOCKET_D, Z_TRAY_BOT … CAP_Z0)` @ `BOSS_CENTERS` | `BOSS_OD + 2·SOCKET_SLIP`; centres from `PCB_W/H, BOSS_C` | **no** |
| corner caps | `_z_cyl(CAP_D, CAP_Z0, CAP_Z1)`, `CAP_Z1 = PLATE_TOP_TO_PCB − PLATE_T` | consts (the `& outer` clip is a no-op: cap reach 6.56 < R8.0) | **no** |
| screw pass | `_z_cyl(M3_PASS_BAND, CAP_Z0 … CAP_Z1)` | const | **no** |
| tray nesting | tray is `TRAY_W/H/R` = `INNER_* − TRAY_SLIP` | `INNER_*` (frozen R) | **no** |
| USB aperture | `_box(USB_X, −WALL−PCB_CLEARANCE/2, …, 2·(WALL+PCB_CLEARANCE))` | **WALL** — parameterised, cuts fully through at any wall; x/z faces unchanged | **no** (x/z) |
| outer shell | `OUTER_W/H = INNER_* + 2·WALL`, `OUTER_R` 8.0 | **WALL** | **yes, outward only** |

### 16.3 Invariance PROVEN, not asserted (scratchpad `v26_prove.py`, verbatim)

```
P1  band(WALL=2.4) md5 = 36980cc2ff011dc32d923fb04f7429f7
    retired v2.5 band  = 36980cc2ff011dc32d923fb04f7429f7   -> PASS
    (the v2.6 source, re-run at the old wall, reproduces the retired STL byte
     for byte: WALL is the only value that moved)
P2  vol(band_2.4 - band_3.0)              = 0.000000 mm^3   -> nothing removed
P3  vol((band_3.0 - band_2.4) & MATING)   = 0.000000 mm^3   -> nothing added
    into the cavity / ledge / plate recess / boss sockets / screw pass / USB
    aperture  => every mating interface is LITERALLY unmoved, radii included
    vol(usb_funnel & band_2.4)            = 0.000000 mm^3   -> the funnel is
    carved out of the ADDED shell only
    band volume 11794.7 -> 14677.7 mm^3 (+24.4 %)
```

Mating dims re-measured from the rebuilt solid (`v26_prove2.py`):

```
z=-1.00 X cavity below ledge   inner faces  -0.300 ..  +84.500  opening  84.800  OK
z=-1.00 Y cavity below ledge   inner faces  -0.300 .. +100.300  opening 100.600  OK
z=+1.00 X ledge INNER opening  inner faces  +0.900 ..  +83.300  opening  82.400  OK
z=+1.00 Y ledge INNER opening  inner faces  +0.900 ..  +99.100  opening  98.200  OK
z=+2.50 X ledge INNER opening  inner faces  +0.900 ..  +83.300  opening  82.400  OK
z=+4.00 X plate recess         inner faces  -0.400 ..  +84.600  opening  85.000  OK
z=+4.00 Y plate recess         inner faces  -0.400 .. +100.400  opening 100.800  OK
ledge ring width west 1.200 / east 1.200 mm ; underside plane: no material at
z 0.284, material at z 0.300  -> the flat +0.300 underside is intact
```

(The R5.6 / R4.4 inner corner arcs cannot be measured from the solid at all —
the Ø10 socket disc at (3.7,3.7) swallows the whole corner arc below +1.5 and
the Ø8.6 cap fills it above. P2/P3 cover them: zero material moved anywhere.)

### 16.4 Gate results (WALL 3.0, `khana build agentpad13_case_v2.py`)

> **⚠ ERRATUM (2026-07-24, §18.4).** Two `[corner]` lines in the block below are
> REPORTING ARTIFACTS, not real changes: `head_to_plate_edge = 1.136 (was 0.287)`
> and `plate_hole_edge_web = 2.386 (was 1.537)`. Both are PLATE measures and the
> plate is FROZEN + already ordered — v2.6 computed them off the BAND's
> WALL-driven outer arc centre. **The true, WALL-INVARIANT values are 0.287 and
> 1.537** (measured from the built solid at every wall, §18.4). Everything else
> in this block stands. No gate ever read these numbers.

```
mechanism.json status: ok    assertions: 101 passed: 101 failed: 0
interferences: 8  (the documented set, unchanged)
  pcb_components x sockets 1.706   pcb_components x leds 2.736
  sockets x leds 67.326            ec11_body x knob_sweep 342.225
  js_body x js_sweep 7.958         knob_sweep x knob 2417.456
  js_sweep x stick_cap 280.548     switch_bodies x keycaps 500.299
[corner] band_crescent_wall = 1.586      (was 0.737 — THE PCBWay fix)
[corner] head_to_plate_edge = 1.136      (was 0.287)
[corner] plate_hole_edge_web = 2.386     (was 1.537)
[corner] pcb_chamfer_slip[*] = 0.350 / 0.341 / 0.341 / 0.341   (unchanged)
[v2.6-WALL] OUTER 90.8 x 106.6 (R8.0); INNER 84.8 x 100.6 (R5.6 FROZEN)
[v2.6-WALL] visible rim ring = 2.90 mm + the 0.3 nominal reveal per side
[v2.6-FUNNEL] depth 0.60; pocket 13.0 x 7.0 @ y -3.30..-2.70; lead-in 0.60;
              cut bbox x 35.00..49.20 z -6.70..0.90 (band bottom -7.5);
              cut volume 167.5 mm^3
[v2.6-FUNNEL] shell bridge = 2.10 mm — WALL-INVARIANT
band bbox: x -3.300..87.500  y -3.300..103.300  z -7.500..5.000
tray_v5.stl md5 d7d16481df24bae4c7769d7624dfc620  — UNCHANGED (byte-identical)
plate/tray .step differ ONLY in their FILE_NAME timestamp line (git: 1 line each)
```

Printability (ADVISORY — the mechanism check remains the sole hard gate):

```
WALL 2.4 no funnel   min_wall 0.6420   <- the geometry PCBWay rejected
WALL 3.0 no funnel   min_wall 1.5690   <- the crescent fix, +145 %
WALL 3.0 + funnel    min_wall 0.6000   <- see 16.6 (the port step)
overhang area 837.6 -> 837.1 mm^2, max 90° both: the funnel adds NO overhang
   (its 45° lead-in consumes the whole pocket ceiling at WALL 3.0)
```

### 16.5 v2.6b USB PORT FUNNEL (owner directive, same day)

The owner is considering walls up to 7.4 for a "more visible diffuser" look, and
a bare thick wall buries the USB-C receptacle (a plug shell reaches ~6.5 mm past
its overmold face, ~5 mm comfortably). The funnel decouples the two: a
rectangular outer counterbore, centred on the aperture, whose **depth tracks the
wall** (`WALL − USB_FUNNEL_WEB`, i.e. 0 at the stock 2.4 wall) so the pocket's
flat seating face always lands on the ORIGINAL 2.4-wall outer plane `y = −2.70`
and the plug-shell bridge is a **wall-invariant 2.10 mm**
(`2.4 + PCB_CLEARANCE 0.3 − USB_FACE_PROUD 0.60`). **The wall pick is therefore
purely aesthetic.** Pocket `13.0 × 7.0` (USB-IF plug overmold max `12.35 × 6.5`
[D] + clearance), 45° lead-in leg `min(1.0, depth)`, inner aperture (10.0 wide,
z −5.0…−1.4) **UNCHANGED**. It is mid-wall (x 34.6…49.6) — the nearest boss
socket is at x 3.7 / 80.5, >25 mm clear — and the `band × usb_recept ≥ 0.1`
gate measures the same inner geometry as v2.5 (still green). Measured directly:

```
funnel x boss socket/cap overlap    = 0.000000 mm^3
funnel -> boss socket/cap distance  = 27.073 mm   (it can never reach the
                                                   corner screw stack)
funnel x usb_recept overlap         = 0.000000 mm^3
funnel -> usb_recept distance       = 2.100 mm    (== the shell bridge: the
                                                   seating face sits exactly
                                                   2.10 off the mating face)
```

### 16.6 Two measured deviations from the first-cut funnel spec

1. **Bottom lead-in leg clamped to 0** (`USB_FUNNEL_FLOOR_MIN`). A 4-sided
   1.0 mm lead-in put the mouth's bottom edge 0.2 mm *below* the band bottom:
   khana read the band `min_wall = 0.566` — **worse than the 0.737 crescent
   PCBWay rejected** — and OCCT then refused the elephant-foot chamfer
   (`[chamfer] z=-7.5: OCCT refused`). The bottom edge is an upward-facing
   floor: it needs no lead-in for printability and none for insertion. With the
   clamp the mouth is `14.2 × 7.6` at WALL 3.0 and `15.0 × 8.0` at 5.4/7.4 — the
   floor stays at z −6.70 at **every** wall, so nothing ever breaks out.
2. **An 0.8 mm rooted step remains under the pocket**, and it is the GEOMETRIC
   MAXIMUM, not a preference: band bottom `−7.50`; a max-size overmold centred
   on the receptacle (`−3.23`) has its bottom face at `−6.48`, so **no**
   closed-bottom pocket can leave more than `1.02`, and a centred 0.5 mm height
   clearance leaves exactly 0.8. Unlike the retired crescent (a free-standing
   arc shell) this step is bonded to the full wall across its whole `13 × 0.8`
   back face — a step, not a fin. It is what the ray-sampling advisory now
   reports for the funnelled band (0.600). **Lever if it must go:** ramp the
   pocket floor out to the band bottom — no step, at the price of a 13 mm
   scallop in the band's bottom outer edge. NOT taken; owner call.

### 16.7 Wall-comparison constraint table (owner's aesthetic pick)

`INNER_R` frozen ⇒ the crescent formula in `_corner_margins()` is the ARC-region
measure and is only valid while `WALL < OUTER_R − PCB_CLEARANCE − BOSS_C = 4.0`.
Above 4.0 the boss centre leaves the corner-arc quadrant and the true corner wall
is `BOSS_C + WALL + PCB_CLEARANCE − SOCKET_D/2`:

| WALL | outer W×H | corner min wall | visible rim (band material) | funnel depth | USB shell bridge | band volume |
|---|---|---|---|---|---|---|
| 2.4 (retired) | 89.6 × 105.4 | **0.737** (arc) | 2.30 | — | 2.10 | 11.79 cm³ |
| **3.0 (built, gated)** | **90.8 × 106.6** | **1.586** (arc) | **2.90** | **0.60** | **2.10** | **14.68 cm³** |
| 5.4 (+3 look) | 95.6 × 111.4 | 4.400 (flat) | 5.30 | 3.00 | 2.10 | 26.58 cm³ |
| 7.4 (+5 look) | 99.6 × 115.4 | 6.400 (flat) | 7.30 | 5.00 | 2.10 | 36.95 cm³ |

Rim = plate-recess wall → outer face on the flats, `WALL − 0.1`; add the 0.3
nominal reveal per side for the full visual ring. **The USB constraint that used
to bite at 7.4 (a 7.10 mm bare-wall tunnel vs a ~6.5 mm plug shell reach) is
GONE** — with the funnel every wall bridges 2.10 mm. 5.4 and 7.4 are
one-parameter re-runs of this same file (`WALL = …`, `khana build`); only 3.0 is
fully gated here.

### 16.8 Deliverables + status

- Exports: **`stl/agentpad13_v2_band_1.6mm_w3.0.stl`**
  md5 `887b2538619db46d63b07cf044762bab` (STL export is deterministic — the same
  hash on every re-run) and **`step/agentpad13_v2_band_1.6mm_w3.0.step`**
  (`fe952d8cd20cba00c2c2a22f820e3a2a` as of this export; OCCT stamps a wall-clock
  `FILE_NAME` line into every STEP header, so STEP hashes are per-export — hash
  the STL when you need invariance). The export name now carries the
  wall (`_w{WALL}`) so no supersession is ever silent. The 2.4-wall
  `agentpad13_v2_band_1.6mm.*` stay on disk as the superseded record —
  **DO NOT PRINT THEM**.
- Gasket kit: **unchanged-valid**. `gen_gasket.py` re-run against the NEW band
  re-measures the west underside flat run at `x [-0.300, 0.900] @ z 0.3` and the
  ring at `84.8 × 100.6 / 82.4 × 98.2, width 1.2` — the README values exactly.
  `gasket_template.svg` and `.png` regenerate **byte-identical**; `.pdf`/`.dxf`
  differ only in embedded timestamps/GUIDs.
- Renders (Desktop): `v26_wall_compare_topdown.png`, `v26_wall_compare_corner.png`,
  `v26_wall_compare_usb.png`, `v26_corner_detail_w3.0.png`,
  `v26_assembly_iso_w3.0.png`, `v26_assembly_front_w3.0.png`.
- **Release folder / MANIFEST / RELEASE.md / PCBWay drafts NOT finalised** —
  coordinator instruction 2026-07-23: hold until the owner picks the wall. 3.0 is
  banked-ready; 5.4 / 7.4 are one-parameter re-runs.
- `ruff check agentpad13_case_v2.py` clean. No git action taken.

---

## 17. Keycaps — 2026-07-24 revisions (cross-reference)

Two keycap changes landed on 2026-07-24. They touch **only**
`keycaps/keycaps.py` and the twelve `_boxfit`-suffixed STLs; **no case, plate,
band, tray, gasket or fab file is affected**, and the 2026-07-22 unsuffixed
keycap STLs that PCBWay already holds are byte-untouched. Full record, with
arithmetic and as-built measurements, in
[`keycaps/KEYCAP-NOTES.md` §10](keycaps/KEYCAP-NOTES.md).

1. **Boss corner lobes** — the answer to PCBWay's 3D-print review, which
   flagged the cruciform socket wall at 0.628 / 0.648 mm. PCBWay's option (A),
   "thicken to 1.0 mm", is *physically impossible* on a BOX Jade (the moat
   between cross and box wall is 0.90 mm and already fully spent). Replacing
   the round boss OD with `Circle(3.00) & Rectangle(5.5, 5.5)` raises the true
   minimum wall **0.5584 → 0.6500 mm** while spending **zero** clearance —
   boss → bore 0.150 and tab → box 0.319 are unchanged.

2. **The X mating slot became a compliant crush-rib fit.** Owner decision,
   taken with no switches on hand: the wide-arm slot opens **1.25 → 1.42** and
   eight integral **0.07 mm** crush ribs bring the effective opening to
   **1.28**. The Kailh drawing says the male arm is 1.30 ± 0.02; community
   calipers say ~1.39; a dimensional slot has to bet on one of those and the
   losing bet cracks the cap (0.14 mm total interference = 74 % of the
   documented cracking figure). A rib fit covers 1.28 … 1.39+ because the rib
   yields and the 1.42 bore is a hard stop that caps hoop stress. Y slot,
   slot span 4.20, socket depth 3.80 and the corner lobes are **unchanged**.

Verified: as-built ray-cast on the solid *and* on all twelve meshes; min wall
still **0.650** everywhere; meshes watertight/manifold (V − E + F = 2); old↔new
Hausdorff **0.085 mm exactly, confined to the X-slot faces**, < 1e-6 mm
everywhere else; khana GREEN at both size sets; Box-Jade clearances identical.
Printability remains **ADVISORY** for the two pre-existing reasons (0.650 wall
vs the 1.2 gate, 90° cavity ceiling).

**Print-material requirement (hardened):** these caps now **require** a tough /
ABS-like resin. Crush ribs work by yielding; a brittle standard resin shatters
a 0.07 mm rib instead of deforming it.

No git action taken.

## 18. v2.7 — DEFAULT WALL 3.0 → 5.4 (owner decision, 2026-07-24)

**Owner ruling (verbatim).** *"1.6 mm doesn't seem like an especially strong
corner to me"* — the v2.6 3.0-wall band's corner measure (`1.586`, the ARC-region
number). **WALL = 5.4 is now the DEFAULT band.** It is what goes into
`v5-release-compiled/`, what the PCBWay reply offers as the option-A replacement
file, and what the public `agentpad13` repo will carry. **3.0 and 7.4 remain
supported, gated variants** — all three are built, gated and exported under their
own `_w{WALL}` names, so no supersession is ever silent.

Base integrity (protocol §1): the v2.6b source had **no recorded md5**; recorded
here as the base of this session — `agentpad13_case_v2.py` (v2.6b)
`40eed84b1b58744836a0421758679822`. **The v2.7 source that produced every
gate and export below is `f2df0203aa9cd03df0ec48aa0477e049`.**

### 18.1 The change (one literal + one env hook + two PRINT-ONLY fixes)

```
WALL           3.0 -> 5.4          the default; a bare numeric literal
AGENTPAD13_WALL                    NEW optional env override (variant builds)
_corner_margins()                  two REPORTING fixes (see §18.4) — no geometry
```

`WALL` stays a **bare numeric literal on its own line** on purpose:
`gasket/gen_gasket.py` reads it by regex (`^WALL\s*=\s*<number>`) instead of
importing the module, so an expression there would break the gasket kit's
constant parse. The env override is a *second* statement, so the file's declared
default is still what the gasket kit reads. Variant build, no file edit:

```
AGENTPAD13_WALL=7.4 khana build agentpad13_case_v2.py
```

Everything §16.2 listed as WALL-independent still is: `INNER_R` FROZEN at 5.6,
`PLATE_R` 5.4, `TRAY_R` 5.35, ledge, plate recess, boss sockets, caps, screw
pass, USB aperture x/z. Only `OUTER_*` and the funnel depth move.

### 18.2 Invariance PROVEN at 5.4 (scratchpad `v27_prove.py`, verbatim)

```
P1  band(WALL=2.4) md5 = 36980cc2ff011dc32d923fb04f7429f7  -> PASS (retired band)
    band(WALL=3.0) md5 = 887b2538619db46d63b07cf044762bab  -> PASS (v2.6 band)
    (the v2.7 source reproduces BOTH banked bands byte for byte: the edit moved
     WALL and two print-only formulas, and no geometry at all)
P2  vol(band_2.4 - band_5.4) = 0.000000 mm^3   -> nothing removed
    vol(band_3.0 - band_5.4) = 0.000000 mm^3   -> strict superset of v2.6 too
P3  vol((band_5.4 - band_2.4) & MATING) = 0.000000 mm^3 -> nothing added into
    the cavity / ledge / plate recess / boss sockets / screw pass / USB aperture
    vol(usb_funnel_5.4 & band_2.4)      = 0.000000 mm^3 -> the 3.00 mm deep
    funnel is carved out of the ADDED shell only
    band volume 11794.7 -> 14677.7 -> 26580.6 mm^3 (+81.1 % vs the v2.6 default)
P7  plate + tray solids at WALL 2.4 / 3.0 / 5.4 / 7.4: IDENTICAL md5 and volume
    plate 70875386ab732e7eea8ca76e21c80d30  8280.769 mm^3
    tray  d7d16481df24bae4c7769d7624dfc620 19923.440 mm^3  (== the banked STL)
```

Mating dims re-measured from the rebuilt 5.4 solid (`v27_prove.py` P4):

```
z=-1.00 X cavity below ledge  inner faces  -0.300 ..  +84.500  opening  84.800 OK
z=-1.00 Y cavity below ledge  inner faces  -0.300 .. +100.300  opening 100.600 OK
z=+1.00 X ledge INNER opening inner faces  +0.900 ..  +83.300  opening  82.400 OK
z=+1.00 Y ledge INNER opening inner faces  +0.900 ..  +99.100  opening  98.200 OK
z=+2.50 X ledge INNER opening inner faces  +0.900 ..  +83.300  opening  82.400 OK
z=+4.00 X plate recess        inner faces  -0.400 ..  +84.600  opening  85.000 OK
z=+4.00 Y plate recess        inner faces  -0.400 .. +100.400  opening 100.800 OK
ledge ring width west 1.200 / east 1.200 mm ; underside plane: no material at
z 0.284, material at z 0.300  -> the flat +0.300 underside is intact
```

### 18.3 Gate results — ALL THREE WALLS (`khana build agentpad13_case_v2.py`)

Every run: `mechanism.json status ok`, **101 assertions / 101 passed / 0 failed**,
**8 interferences** — the documented set, unchanged
(`pcb_components×sockets 1.706`, `pcb_components×leds 2.736`,
`sockets×leds 67.326`, `ec11_body×knob_sweep 342.225`, `js_body×js_sweep 7.958`,
`knob_sweep×knob 2417.456`, `js_sweep×stick_cap 280.548`,
`switch_bodies×keycaps 500.299`). Tray identical in all three
(19923.4 mm³, STL md5 `d7d16481df24bae4c7769d7624dfc620`).

**WALL 5.4 — THE DEFAULT (verbatim):**

```
[corner] band_crescent_wall = 4.400
[corner] head_to_plate_edge = 0.287
[corner] plate_hole_edge_web = 1.537
[corner] pcb_chamfer_slip[3.7,3.7] = 0.350
[corner] notch_insert_wall[3.7,3.7] = 1.651
[corner] pcb_chamfer_slip[80.5,3.7] = 0.341
[corner] pcb_chamfer_slip[3.7,96.3] = 0.341
[corner] pcb_chamfer_slip[80.5,96.3] = 0.341
[corner] band_crescent_wall class = flat (WALL 5.4 vs the arc/flat transition at 4.0)
[v2.7-WALL] WALL = 5.4 (source: v2.7 file default; v2.7 default 5.4, gated variants 3.0 / 5.4 / 7.4 via AGENTPAD13_WALL)
[v2.6-WALL] WALL = 5.4 -> OUTER 95.6 x 111.4 (R8.0); INNER 84.8 x 100.6 (R5.6 FROZEN -> PLATE_R 5.4, TRAY_R 5.35 unmoved)
[v2.6-WALL] visible rim ring = 5.30 mm + the 0.3 nominal reveal per side; bare-wall USB tunnel would be 5.10 mm
[v2.6-FUNNEL] USB port funnel depth = 3.00 (= WALL - 2.4); pocket 13.0 x 7.0 @ y -5.70..-2.70 (flat bottom); 45° lead-in leg 1.00 (bottom leg 0 by USB_FUNNEL_FLOOR_MIN); cut bbox x 34.60..49.60 z -6.70..1.30 (band bottom -7.5); cut volume 407.2 mm^3
[v2.6-FUNNEL] shell bridge = 2.10 mm — WALL-INVARIANT
[printability] band: ADVISORY | min_wall=0.7333 | overhang_area=896.53 max_deg=90.0
band bbox: x -5.700..89.900  y -5.700..105.700  z -7.500..5.000
```

**WALL 3.0 (variant, re-gated under v2.7):** `band_crescent_wall 1.586` (arc);
OUTER `90.8 × 106.6`; rim `2.90`; funnel depth `0.60`, cut volume `167.5 mm³`;
band `min_wall 0.6000`, overhang `837.1 mm²`; band STL re-exports **byte-identical
to the v2.6 bank**, md5 `887b2538619db46d63b07cf044762bab`.

**WALL 7.4 (variant):** `band_crescent_wall 6.400` (flat); OUTER `99.6 × 115.4`;
rim `7.30`; funnel depth `5.00`, pocket `y -7.70..-2.70`, cut volume `589.2 mm³`;
band `min_wall 0.7333`, overhang `920.1 mm²`; band volume `36947.4 mm³`.

Gasket kit re-run against the 5.4 band (`gen_gasket.py`, exit 0): west ledge
underside flat run `x [-0.300, 0.900] @ z 0.3`, ring `84.8 × 100.6 / 82.4 × 98.2,
width 1.2`, 10 segments, PDF MediaBox `190.000 × 250.000 mm` 1:1 OK.
`gasket_template.svg` + `.png` regenerate **byte-identical**
(`527bba7d1ed7b545caed6f37d2197c02` / `4568f75a886266aef3597a21d1fd54aa`);
`.pdf`/`.dxf` differ only in embedded timestamps/GUIDs. **The kit is INNER-derived
and is therefore the same part at every wall.**

### 18.4 ERRATUM to §16.4 — two REPORTING artifacts, no geometry impact

`_corner_margins()` is printed, never asserted; no gate ever read it. Two of its
closed forms were only valid at the 2.4 wall, and v2.6 published both:

1. **`band_crescent_wall` is arc-only.** It is the ARC-region measure, valid
   while `arc_c = OUTER_R − PCB_CLEARANCE − WALL > BOSS_C`, i.e. `WALL < 4.0`.
   At/above 4.0 the boss centre leaves the corner-arc quadrant and the nearest
   outer surface is a **FLAT**: `BOSS_C + WALL + PCB_CLEARANCE − SOCKET_D/2`.
   §16.7's table already carried the right numbers (4.400 / 6.400 "flat"), but
   the un-branched code would have printed `4.980` / `7.808`. **Fixed** — the
   build now also prints the class (`band_crescent_wall class = flat|arc`).
2. **`head_to_plate_edge` / `plate_hole_edge_web` were measured off the BAND's
   outer arc centre**, which is WALL-driven, although both are **PLATE** measures
   and the plate is FROZEN and ALREADY ORDERED. They agreed at WALL 2.4 only
   because the outer / inner / plate corner arcs were CONCENTRIC there (all at
   (5.3, 5.3)). **§16.4's recorded improvements `head_to_plate_edge = 1.136 (was
   0.287)` and `plate_hole_edge_web = 2.386 (was 1.537)` are therefore WRONG —
   they are reporting artifacts of the 3.0 build, not real changes.** The plate
   never moved (P2/P3 prove zero material moved anywhere; P7 proves the plate
   solid is md5-identical at every wall). **Fixed** — both now key off the
   plate's own arc centre and read `0.287` / `1.537` at every wall, which is what
   §3's original table has said since 2026-07-18.

Both fixes are **verified against the built solids, not re-derived on paper**
(`v27_prove.py` P6 bisects the true breakout radius):

```
band: dist(boss centre -> OUTER surface) - SOCKET_D/2, per wall
  WALL 2.4  mode=arc   dist= 5.737  MEASURED 0.737  v2.7 formula 0.737  PASS
  WALL 3.0  mode=arc   dist= 6.586  MEASURED 1.586  v2.7 formula 1.586  PASS
  WALL 5.4  mode=flat  dist= 9.400  MEASURED 4.400  v2.7 formula 4.400  PASS
            (the v2.6 arc-only form would have said 4.980  <-- WRONG)
  WALL 7.4  mode=flat  dist=11.400  MEASURED 6.400  v2.7 formula 6.400  PASS
            (the v2.6 arc-only form would have said 7.808  <-- WRONG)
  Ø10.0 socket bore verified clear of material at z -3..-1 (both walls)
plate: dist(boss centre -> plate edge), per wall — WALL-INVARIANT
  WALL 2.4 / 3.0 / 5.4 / 7.4  dist = 3.137 at every wall
    -> head_to_plate_edge  MEASURED 0.287 == formula 0.287   PASS
    -> plate_hole_edge_web MEASURED 1.537 == formula 1.537   PASS
```

**Consequence for the record:** the corner-margin *window* argument in §3 (boss
centre in [3.00, 3.73], 3.7 chosen) is unaffected — it was always a plate/PCB
argument, and those numbers are the invariant ones.

### 18.5 Printability at 5.4 (ADVISORY — the mechanism check is the sole gate)

```
WALL 2.4 no funnel   min_wall 0.6420   overhang 829.7 mm^2   <- PCBWay rejected
WALL 3.0 no funnel   min_wall 1.5690   overhang 837.6
WALL 3.0 + funnel    min_wall 0.6000   overhang 837.1
WALL 5.4 no funnel   min_wall 1.9000   overhang 891.3        <- THE DEFAULT
WALL 5.4 + funnel    min_wall 0.7333   overhang 896.5        <- THE DEFAULT
WALL 7.4 no funnel   min_wall 1.9000   overhang 918.1
WALL 7.4 + funnel    min_wall 0.7333   overhang 920.1
```

Both 5.4 numbers were **located**, not guessed (the khana wall sampler shoots an
inward ray per tessellation triangle; the argmin triangles were read back):

- **`1.9000` (funnel-free) is NOT the corner any more.** Its samples sit at
  `z = +3.400` with normal `+Z` — the plate-seat face over the four corner caps —
  and the ray lands on the Ø10 boss-socket ceiling at `z = +1.5`. It is the
  **corner cap slab, `CAP_Z1 − CAP_Z0 = 3.4 − 1.5 = 1.900`**: a WALL-INVARIANT
  feature that has existed since v2.2 and is identical at 7.4. At 3.0 the argmin
  samples were still the four corner diagonals (`1.5690`, normals ±0.71/±0.71 —
  the crescent). **At 5.4 the corner crescent (4.400) is no longer the thinnest
  feature anywhere in the band**, and the funnel-free band CLEARS the 1.0 mm
  advisory floor outright (1.900 ≥ 1.0) — the 2.4-wall band failed it at 0.642.
- **`0.7333` (funnelled) is the §16.6 rooted step under the port, and it
  persists at 5.4 exactly as documented.** Argmin samples sit on the pocket floor
  plane `z = −6.700`, ray down to the band bottom `−7.500` → the step is
  **0.800** nominal; three of the four thinnest samples read exactly `0.8000`.
  The `0.7333` is that same step read where the `EFC_CHAMFER = 0.4` elephant-foot
  chamfer clips the bottom outer edge: the sample at `0.3333` inboard of the
  outer face loses `0.4 − 0.3333 = 0.0667` of floor, i.e. `0.800 − 0.067 =
  0.733`. (At 3.0 the whole 0.6-deep pocket sits inside that chamfer zone, which
  is why it read `0.600`.) **The §16.6 explanation stands verbatim:** the 0.8 mm
  step is the GEOMETRIC MAXIMUM, not a preference — band bottom `−7.50`, a
  max-size overmold centred on the receptacle has its bottom face at `−6.48`, so
  no closed-bottom pocket can leave more than `1.02`, and a centred 0.5 mm height
  clearance leaves exactly 0.8. Unlike the retired 0.737 crescent (a
  free-standing arc shell) this step is **bonded to the full 5.4 mm wall across
  its whole 13 × 0.8 back face — a step, not a fin.** Lever if it must go: ramp
  the pocket floor out to the band bottom (no step; 13 mm scallop in the band's
  bottom outer edge). NOT taken; owner call.

### 18.6 Wall-comparison table (v2.7, corrected + measured)

| WALL | outer W×H | corner min wall | class | visible rim | funnel depth | shell bridge | band volume | band STL md5 |
|---|---|---|---|---|---|---|---|---|
| 2.4 (retired) | 89.6 × 105.4 | 0.737 | arc | 2.30 | — | 2.10 | 11.79 cm³ | `36980cc2…` DO NOT PRINT |
| 3.0 (variant) | 90.8 × 106.6 | 1.586 | arc | 2.90 | 0.60 | 2.10 | 14.68 cm³ | `887b2538…` |
| **5.4 (DEFAULT)** | **95.6 × 111.4** | **4.400** | **flat** | **5.30** | **3.00** | **2.10** | **26.58 cm³** | **`34be6bf7…`** |
| 7.4 (variant) | 99.6 × 115.4 | 6.400 | flat | 7.30 | 5.00 | 2.10 | 36.95 cm³ | `16366996…` |

### 18.7 Deliverables + status

- **DEFAULT export: `stl/agentpad13_v2_band_1.6mm_w5.4.stl`
  md5 `34be6bf79a6bb81995807448639f4822`** (STL export is deterministic — the
  hash reproduced across two independent gated runs) and
  `step/agentpad13_v2_band_1.6mm_w5.4.step` (`964a501ca8d49762c8288ce64bdeb395`
  in the release copy — the STEP hash moved on EVERY re-export this session
  while the STL never did; OCCT stamps a wall-clock `FILE_NAME` line into every STEP
  header, so STEP hashes are per-export — hash the STL when you need invariance).
- Variants: `…_w3.0.stl` `887b2538619db46d63b07cf044762bab` (byte-identical to
  the v2.6 bank), `…_w7.4.stl` `163669962a928793a4e65347a80e4cfe`.
- `stl/agentpad13_v2_band_1.6mm.stl` (`36980cc2…`, the 2.4 wall) stays on disk
  here as the SUPERSEDED record — **DO NOT PRINT IT.** It has been **removed from
  `v5-release-compiled/`** so a do-not-print file cannot ride into the public
  repo; the release now carries `_w5.4` (primary) + `_w3.0` + `_w7.4` only.
- `tray_v5.stl` md5 `d7d16481df24bae4c7769d7624dfc620` — UNCHANGED
  (byte-identical); plate/tray `.step` differ only in their `FILE_NAME` line.
- Renders (Desktop, SHIPPING geometry): `v27_assembly_iso.png`,
  `v27_assembly_front.png` (`khana draw --view iso_ne,front`; the front
  elevation shows the 3.00 mm port funnel mouth). Also copied into
  `v5-release-compiled/renders/`.
- `ruff check agentpad13_case_v2.py` clean. **No git action taken.**

### 18.8 PCBWay reply drafts (order `C-Y15W1075301A_`) — OWNER SENDS, from the portal

Composed from the §16/§18 record. **Not sent by any agent** — no uploads, no
money, no portal action was taken. Paste as-is.

**Q1 — "corner crescents too thin, may break" (the four corners of the band):**

```
Thank you for the review — the flag is correct and we are taking OPTION A
(customer-corrected file).

Please replace the band model with the attached file:

    agentpad13_v2_band_1.6mm_w5.4.stl
    md5 34be6bf79a6bb81995807448639f4822

What changed: the sidewall thickness went from 2.4 mm to 5.4 mm. The corner
regions you flagged were a free-standing arc shell with a minimum of about
0.737 mm. In the new file the minimum material in those same corners is about
4.4 mm, and it is no longer a free arc — it is flat-backed, i.e. the thin
crescent is gone entirely and the corner is now solid wall behind the screw
boss. Overall outside dimensions grow from 89.6 x 105.4 mm to 95.6 x 111.4 mm;
the outer corner radius stays R8.0.

Nothing else moved. Every mating and internal feature is identical to the file
you already reviewed: the inner cavity, the 1.2 mm rabbet ledge, the plate
recess, the four corner screw bosses and their pass-through holes, and the USB
opening are all byte-for-byte unchanged (we verified this by boolean
comparison of the two solids: zero material removed anywhere, and zero material
added inside any mating feature). The wall only grew outward.

One feature worth pointing out so it is not mistaken for a defect: on the USB
port face there is a rectangular relief pocket around the opening, 13.0 x 7.0
mm and 3.0 mm deep. It is intentional — it gives the USB-C plug's overmoulded
body somewhere to sit so the thicker wall does not bury the connector. The
floor of that pocket leaves a 0.8 mm step across the bottom of the opening.
That step is not a fin: it is rooted along its whole 13 mm back face into the
full 5.4 mm wall, so it is supported on the wall behind it and is not a
free-standing thin feature.

Material/finish is unchanged from the original order: clear/transparent resin,
standard unpolished finish (the frosted surface is intentional - please do NOT
polish).

We understand the part volume increases with the thicker wall (about 11.8 cm3
to 26.6 cm3) and that the quote may need to be revised - please send an updated
quotation if so.
```

**Q2 — "the part may deform during transport":**

```
Understood and accepted - please proceed. We accept the risk of minor
deformation in transit and we do not need any additional packaging service
beyond your standard protective packing (though if you can pack it flat rather
than on edge, we would appreciate it).

Two things make this a low-consequence risk for this part:

1. It is not a free-standing frame in service. The band is the middle layer of
   a bolted sandwich: a 2.4 mm printed tray underneath, the PCB, this band, and
   a 1.6 mm FR4 plate that drops into the band's perimeter rabbet on top, all
   clamped by four M3 screws through the corner bosses. The FR4 plate is a
   stiff flat member seated into the recess around the entire perimeter, so
   assembly pulls the band back flat and holds it there. A small bow out of the
   box is taken out by tightening the screws.

2. The replacement file we are sending in the same message is substantially
   stiffer than the one you reviewed. The sidewall goes 2.4 mm to 5.4 mm; the
   out-of-plane bending stiffness of a wall scales with the cube of its
   thickness, so the new wall is on the order of 11x stiffer against exactly
   the kind of bowing you are describing, and part volume roughly doubles
   (11.8 cm3 to 26.6 cm3). If the deformation concern was driven by the thin
   2.4 mm wall, the new part should be much better behaved.

If, after printing, you judge that the part is still likely to arrive
distorted, please tell us before shipping and we will discuss options.
```

**Owner action items in these drafts (flagged, NOT taken by any agent):** attach
`v5-release-compiled/hardware/case/v2/stl/agentpad13_v2_band_1.6mm_w5.4.stl`;
expect a revised quotation (the part volume roughly doubles). Money, uploads and
portal actions are owner-only.

---

## 19. Plate long-axis fab-cap trim — 100.2 → 100.000 mm (owner directive 2026-07-21; §-record written 2026-08-05)

**This change shipped on 2026-07-21 and — until this entry — had NO section of
its own in this ledger.** It was recorded only as a comment block in
`gen_plate_fab.py` and, later, as a hazard note in `v5/V5-NOTES.md` /
`docs/HANDOFF-STATE.md`. §14's gate transcript still printed the pre-trim
`100.200` for two weeks. That gap is closed here; §14's block is annotated in
place (never deleted) and this section is the authority.

### 19.1 What and why

The owner's words, quoted from the directive that produced the change:

> **"Resize the top plates to 100mm. That 0.2 is gonna cost us 25%. Not worth it."**

The plate's long (H) axis was `C.PLATE_H = 100.2 mm` — **0.2 mm over the fab's
100 mm promo-price cap**. PCBWay (and JLCPCB) price a bare board that fits
inside `≤100 × 100 mm` on a promo tier; 100.2 falls out of it and the quote
jumps by roughly the quarter the owner refused to pay. The short (W) axis
(84.4) was already well under and is **untouched**.

### 19.2 How it was implemented — LOCALLY, at emit time

`hardware/case/v2/gen_plate_fab.py`:

```
PLATE_LONG_TRIM = 0.2   # total H-axis reduction: 100.20 -> 100.00 (0.1/edge)

sh = rounded_rect(-0.1, -0.1 + PLATE_LONG_TRIM / 2,
                  C.PLATE_W - 0.1, C.PLATE_H - 0.1 - PLATE_LONG_TRIM / 2,
                  C.PLATE_R)
```

**0.1 mm comes off EACH long edge**, so the outline stays centred on the same
`y = 50.0` axis and **every switch cutout, opening, LED/touch hole and all four
M3 screw holes keep their EXACT absolute position**. Only the two long
Edge.Cuts edges and their four corner arcs move.

**`C.PLATE_H` in `agentpad13_case_v2.py` stays 100.2 ON PURPOSE.** It also
drives the band's plate pocket (`agentpad13_case_v2.py` ~L872,
`_rprism(PLATE_W + 2*PLATE_FIT, PLATE_H + 2*PLATE_FIT, ...)`), which the owner
directed must NOT change. The band pocket therefore stays 100.8 mm and the
long-axis plate-to-lip gap simply **relaxes from 0.30 to 0.40 mm per end** — a
looser, still-valid fit. **No band note, no band reprint, no gasket change.**
(§1's `Plate 84.4 × 100.2 R5.4` line is annotated accordingly: it is the MODEL
dimension, not the fab dimension.)

### 19.3 Resulting exact geometry

| axis | before | after |
|---|---|---|
| W (short) | `84.400` (x −0.100 … 84.300) | **`84.400` (x −0.100 … 84.300) — UNCHANGED** |
| H (long) | `100.200` (y −0.100 … 100.100) | **`100.000` (y 0.000 … 100.000)** |

Corner-arc tangent points followed the edges: `y 5.3 → 5.4` and `y 94.7 → 94.6`
(radius `PLATE_R = 5.4` unchanged). Independent set-difference of the pre-trim
vs post-trim `.kicad_pcb` (UUID-blind, 93 primitives each) returns **exactly 8
primitives changed — the 4 outline lines + 4 corner arcs — and 85 primitives
byte-identical.** The trim moved the outline and nothing else, as designed.

### 19.4 Files the trim regenerated (all `hardware/case/v2/fab/`, 2026-07-21)

All three variants and every downstream artifact:

| file | md5 (post-trim) | bytes |
|---|---|---|
| `agentpad13_v2_plate_v5.kicad_pcb` (disc / ENIG) | `b15a683bf6a1fcede54ee08478080105` | 15328 |
| `agentpad13_v2_plate_tented_ring_v5.kicad_pcb` (ring / any finish) | `7c384ae41dd8e0bd4b8ce22a06776983` | 15330 |
| `agentpad13_v2_plate_blank_v5.kicad_pcb` (blank) | `f1bf659421287aa16bdce5db7fe57a43` | 14437 |
| `plate_v5_gerbers.zip` | `de2f939102c8314cae51a5ca2089308d` | 6072 |
| `plate_v5_ring_gerbers.zip` | `ef58b6c41ca84c1e8d18d0d390f08f6a` | 6378 |
| `plate_v5_blank_gerbers.zip` | `8463dcd7ef6d530f262015ea714d212d` | 5828 |
| `agentpad13_v2_plate_v5.dxf` | `529b60f7e9833683a9f1ec89f1abbf27` | 13017 |
| `agentpad13_v2_plate_v5_top.png` | `c1d1ab21cbc7c67e56114874cfef8551` | 31450 |
| `agentpad13_v2_plate_v5_top.svg` | `668fd03cf4d525b6a154fe8ab83436b7` | 5908 |

The renders carry the change visibly in their page box: the SVG viewBox went
`84.4804 × 100.2792` → **`84.4804 × 100.0760`** mm (the residue over 100.000 is
the 0.1 mm Edge.Cuts stroke), and the PNG is 1000 × **1185** px (was 1187).

`validate_fab_v5.py` was updated in the same pass and now carries
`PLATE_WH = (84.40, 100.00)  # long axis trimmed 100.20->100.00 (fab 100 mm cap)`
plus `ck(near(d_top, 2.57, 0.02), ...)`.

### 19.5 Post-trim gate run — `validate_fab_v5.py` VERBATIM

Re-run 2026-08-05 under the KiCad 9.0.9 bundled Python
(`~/Applications/KiCad.app/.../Versions/3.9/bin/python3.9 validate_fab_v5.py`),
pcbnew reload, all three variants. Absolute paths shortened to `fab/`; the
headless `wxApp` assert line removed. Nothing else altered.

```
========================================================================
FILE: fab/agentpad13_v2_plate_v5.kicad_pcb
VARIANT: disc
[bbox] Edge.Cuts centerline = 84.400 x 100.000 mm  (x -0.100..84.300, y 0.000..100.000)
  PASS bbox 84.40 x 100.00 (got 84.400 x 100.000)
[count] Edge.Cuts shapes = 89
  PASS Edge.Cuts count == 89 (got 89)
[JS opening] 4 lines + 4 arcs; extents W=58.910 N=2.570 E=77.360 S=21.020
    edge (58.910,19.520)->(58.910,4.070)
    edge (60.410,2.570)->(75.860,2.570)
    edge (75.860,21.020)->(60.410,21.020)
    edge (77.360,4.070)->(77.360,19.520)
  PASS opening = 4 lines + 4 arcs
  PASS West x = 58.91 (got 58.910)
  PASS North y = 2.57 (got 2.570)
  PASS East x = 77.36 (got 77.360)
  PASS South y = 21.02 (got 21.020)
  PASS v4 Ø16 circle @ (70.675,12.5) is GONE
[encoder] extents 7.025..20.025 x 6.000..19.000  center (13.525,12.500) size 13.000x13.000
  PASS encoder 13x13 @ (13.525,12.5) unchanged
  PASS screw hole Ø3.2 @ (3.7,3.7) present
  PASS screw hole Ø3.2 @ (80.5,3.7) present
[SW13] cutout center (42.100,88.850) size 14.000x14.000
  PASS SW13 14.0 cutout @ (42.1,88.85) unchanged
  PASS stab L 6.65x12.3 @ (30.162,89.47) unchanged
  PASS stab R 6.65x12.3 @ (54.038,89.47) unchanged
[web] N->plate-top      = 2.570  (expect ~2.57)
[web] NE->screw(80.5,3.7)= 1.555  (floor 1.5; brief ~1.74)
[web] S->nearest switch  = 3.680 @ SW(70.675, 31.7)  (floor 2.0)
[web] nearest feature W  = 3.979 @ SW(51.625, 31.7)
  PASS N->top ~2.57 (got 2.570)
  PASS NE->screw >= 1.5 floor (got 1.555)
  PASS S->switch >= 2.0 floor (got 3.680)
  PASS disc: Ø12 F.Mask gold opening, no silk ring
========================================================================
FILE: fab/agentpad13_v2_plate_tented_ring_v5.kicad_pcb
VARIANT: tented_ring
[bbox] Edge.Cuts centerline = 84.400 x 100.000 mm  (x -0.100..84.300, y 0.000..100.000)
  PASS bbox 84.40 x 100.00 (got 84.400 x 100.000)
[count] Edge.Cuts shapes = 89
  PASS Edge.Cuts count == 89 (got 89)
[JS opening] 4 lines + 4 arcs; extents W=58.910 N=2.570 E=77.360 S=21.020
    edge (58.910,19.520)->(58.910,4.070)
    edge (60.410,2.570)->(75.860,2.570)
    edge (75.860,21.020)->(60.410,21.020)
    edge (77.360,4.070)->(77.360,19.520)
  PASS opening = 4 lines + 4 arcs
  PASS West x = 58.91 (got 58.910)
  PASS North y = 2.57 (got 2.570)
  PASS East x = 77.36 (got 77.360)
  PASS South y = 21.02 (got 21.020)
  PASS v4 Ø16 circle @ (70.675,12.5) is GONE
[encoder] extents 7.025..20.025 x 6.000..19.000  center (13.525,12.500) size 13.000x13.000
  PASS encoder 13x13 @ (13.525,12.5) unchanged
  PASS screw hole Ø3.2 @ (3.7,3.7) present
  PASS screw hole Ø3.2 @ (80.5,3.7) present
[SW13] cutout center (42.100,88.850) size 14.000x14.000
  PASS SW13 14.0 cutout @ (42.1,88.85) unchanged
  PASS stab L 6.65x12.3 @ (30.162,89.47) unchanged
  PASS stab R 6.65x12.3 @ (54.038,89.47) unchanged
[web] N->plate-top      = 2.570  (expect ~2.57)
[web] NE->screw(80.5,3.7)= 1.555  (floor 1.5; brief ~1.74)
[web] S->nearest switch  = 3.680 @ SW(70.675, 31.7)  (floor 2.0)
[web] nearest feature W  = 3.979 @ SW(51.625, 31.7)
  PASS N->top ~2.57 (got 2.570)
  PASS NE->screw >= 1.5 floor (got 1.555)
  PASS S->switch >= 2.0 floor (got 3.680)
  PASS tented_ring: no F.Mask, Ø16 silk ring present
========================================================================
FILE: fab/agentpad13_v2_plate_blank_v5.kicad_pcb
VARIANT: blank
[bbox] Edge.Cuts centerline = 84.400 x 100.000 mm  (x -0.100..84.300, y 0.000..100.000)
  PASS bbox 84.40 x 100.00 (got 84.400 x 100.000)
[count] Edge.Cuts shapes = 89
  PASS Edge.Cuts count == 89 (got 89)
[JS opening] 4 lines + 4 arcs; extents W=58.910 N=2.570 E=77.360 S=21.020
    edge (58.910,19.520)->(58.910,4.070)
    edge (60.410,2.570)->(75.860,2.570)
    edge (75.860,21.020)->(60.410,21.020)
    edge (77.360,4.070)->(77.360,19.520)
  PASS opening = 4 lines + 4 arcs
  PASS West x = 58.91 (got 58.910)
  PASS North y = 2.57 (got 2.570)
  PASS East x = 77.36 (got 77.360)
  PASS South y = 21.02 (got 21.020)
  PASS v4 Ø16 circle @ (70.675,12.5) is GONE
[encoder] extents 7.025..20.025 x 6.000..19.000  center (13.525,12.500) size 13.000x13.000
  PASS encoder 13x13 @ (13.525,12.5) unchanged
  PASS screw hole Ø3.2 @ (3.7,3.7) present
  PASS screw hole Ø3.2 @ (80.5,3.7) present
[SW13] cutout center (42.100,88.850) size 14.000x14.000
  PASS SW13 14.0 cutout @ (42.1,88.85) unchanged
  PASS stab L 6.65x12.3 @ (30.162,89.47) unchanged
  PASS stab R 6.65x12.3 @ (54.038,89.47) unchanged
[web] N->plate-top      = 2.570  (expect ~2.57)
[web] NE->screw(80.5,3.7)= 1.555  (floor 1.5; brief ~1.74)
[web] S->nearest switch  = 3.680 @ SW(70.675, 31.7)  (floor 2.0)
[web] nearest feature W  = 3.979 @ SW(51.625, 31.7)
  PASS N->top ~2.57 (got 2.570)
  PASS NE->screw >= 1.5 floor (got 1.555)
  PASS S->switch >= 2.0 floor (got 3.680)
  PASS blank: no copper / mask / silk at TP5
========================================================================
RESULT: ALL GATES PASS
```

**The one web that moved is `N->plate-top`, 2.670 → 2.570** — exactly the 0.1 mm
the north edge travelled. `NE->screw` is measured from the JOYSTICK OPENING
(frozen) to the screw hole (frozen), so the trim cannot and does not move it off
its **1.555** — the 1.5 floor is still cleared by 0.055, exactly as §14's
addendum ruled. `[count] Edge.Cuts shapes = 89` is likewise unchanged: the trim
moved the 8 outline primitives, it did not add or remove any.

### 19.6 Propagation — where the trimmed files had NOT reached (fixed 2026-08-05)

The trim was applied to the working tree on 2026-07-21 but **never propagated**,
so for two weeks two of the three trees shipped the 100.2 plate:

| tree | before 2026-08-05 | now |
|---|---|---|
| `hardware/case/v2/fab/` (working) | **84.400 × 100.000** ✅ | 84.400 × 100.000 |
| `v5-release-compiled/hardware/case/v2/fab/` | **84.400 × 100.200** ❌ | **84.400 × 100.000** ✅ |
| `agentpad13` public repo, `hardware/case/fab/` | **84.400 × 100.200** ❌ | **84.400 × 100.000** ✅ |

This mattered because the release bundle is meant to be the **self-contained
payload** — anyone who used it as intended would have uploaded the 100.2 mm file
and paid exactly the 25 % the owner refused. `RELEASE.md §(e)` happened to point
at the working-tree path, so the prose was right by luck while the shipped bytes
were wrong. All nine files (3 `.kicad_pcb` + 3 gerber zips + DXF + PNG + SVG) are
now byte-identical across all three trees, and `MANIFEST.md`'s nine plate rows
carry the post-trim md5s.

### 19.7 Unreleased touch-marker style variants on disk (NOT part of any release)

`fab/` also holds four **untracked** files from a 2026-07-21 20:51 experiment,
referenced by no generator path, no doc and no manifest:

- `agentpad13_v2_plate_filled_v5.kicad_pcb` + `plate_filled_100mm.zip`
- `agentpad13_v2_plate_ring_v5.kicad_pcb` + `plate_ring_100mm.zip`

Both are **already at the trimmed 84.400 × 100.000** and differ from their named
siblings by **exactly one primitive** — the TP5 touch marker at (13.525, 88.85):

| file | marker primitive |
|---|---|
| `agentpad13_v2_plate_v5` (SHIPPED) | `F.Mask` circle r 6.0 (Ø12), fill yes — the exposed ENIG gold disc |
| `agentpad13_v2_plate_filled_v5` (experiment) | `F.SilkS` circle r 5.0 (Ø10), **fill yes**, stroke 0.8 — a solid silk disc, no mask opening, so no ENIG requirement |
| `agentpad13_v2_plate_tented_ring_v5` (SHIPPED) | `F.SilkS` circle r 8.0 (Ø16), fill no, stroke 0.2 |
| `agentpad13_v2_plate_ring_v5` (experiment) | `F.SilkS` circle r 5.0 (Ø10), fill no, **stroke 0.8** — a smaller, heavier ring |

Their gerber zips are full 26-file KiCad default exports (every layer incl.
Adhesive/Paste/Courtyard/User_*), not the curated 10-file set the three shipped
variants use. **They supersede nothing.** The release set remains the three
named variants. Also present: `plate_v5_gerbers_100mm.zip`,
`plate_v5_ring_gerbers_100mm.zip`, `plate_v5_blank_gerbers_100mm.zip` — these
are **byte-identical md5 duplicates** of the three shipped zips (re-saved
2026-07-21 20:19 under a name that advertises the 100 mm fact), not new
artifacts. Nothing in `fab/` is stale; the duplicates and experiments are simply
un-adopted.

#### 19.7 addendum (2026-08-19) — the two experiments are DELETED

"Nothing in `fab/` is stale" stopped being true the moment the v2.12 encoder
opening landed (§23). `agentpad13_v2_plate_filled_v5.kicad_pcb`,
`agentpad13_v2_plate_ring_v5.kicad_pcb` and their `plate_filled_100mm.zip` /
`plate_ring_100mm.zip` still carried the superseded **13×13** aperture, and —
unlike every other file in `fab/` — **no generator path emits them**, so they
could not be regenerated with the widened opening. That combination is exactly
the §19.6 failure class: an uploadable zip, sitting in the ordering directory,
carrying geometry the owner has already rejected. All four are **deleted from
the working tree** (git history preserves them; the touch-marker styles they
recorded are fully described in the table above, so nothing is lost but the
hazard). The three `plate_v5_*_gerbers_100mm.zip` duplicates are NOT deleted —
those have a generator path and were re-hashed with the rest of the fab set,
so they remain byte-identical duplicates of the shipped zips.

## 20. PCBWay product-number placement — the v5 plate came back marked on the DECK (2026-08-15)

**The defect, observed on the physical part.** The v5 top plate was ordered from PCBWay and
received; the owner built the macropad from it. PCBWay had printed their product number on the
plate's **top face** — the +Z face, the one the plate exists to be: the visible deck of the
finished product. Nothing in the design asked for that, and nothing in the design asked against
it either, which is the whole problem.

**Why their operator had nothing to go on.** PCBWay's published placement rule is
component-driven, not layer-driven:

> The position where the Product No. is added is not fixed, we will try to put it under the IC
> so that the number will be hidden when soldering.

This plate is a bare decorative panel. It has no ICs, no components of any kind — nothing to hide
a number under. The heuristic degenerates to "somewhere", and "somewhere" came up the deck.

**Silk-layer census, measured this pass** (`fab/`, aperture and draw counts straight out of the
emitted gerbers). An earlier statement of this fact — that *all* silk layers in *all three*
variants are empty — is **wrong, and is corrected here**; the section is worth nothing if the
reasoning does not survive review:

| variant | `-F_Silkscreen.gto` | `-B_Silkscreen.gbo` |
|---|---|---|
| `plate_v5` (disc) | apertures 0, draws 0 | apertures 0, draws 0 |
| `plate_tented_ring_v5` | **apertures 1, draws 2** | apertures 0, draws 0 |
| `plate_blank_v5` | apertures 0, draws 0 | apertures 0, draws 0 |

So **five of the six v5 silk layers are empty, and all three B.SilkS layers are empty** — but the
tented-ring variant's **front** silk is *not*: it carries the Ø16/0.2 touch-marker ring, by design
[`gen_plate_fab.py` `silk_ring()`; §19.7's marker table; `HOW-TO-ORDER.md` Card 2, which sells that
ring as the variant's visible feature]. The Rev-A ring variant behaves identically (1 aperture,
2 draws on F.SilkS).

**Which variant was actually received is UNKNOWN in-repo.** No order record for the v5 plate exists
in this repository at all — the order and the receipt are owner-side facts. The answer changes only
the *rationale* (whether PCBWay had adjacent top-silk content to anchor on, or a blank face
everywhere), **not the instruction**: the number belongs on the bottom face either way. The quick
resolution is to look at the part in hand — if it has a white Ø16 ring around the touch key, it is
the tented-ring variant.

### 20.1 The precedent that should have caught this in July

This is the **second** time the plate's empty silkscreen has cost us something with the same fab.
On the Rev-A plate order, PCBWay put the job on a **silkscreen hold** precisely because the silk
layer was empty. A reply was drafted [`docs/PREORDER-REVIEW-2026-07-19.md:176-179`]:

> PCBWay plate order: silkscreen-hold response drafted separately (empty silkscreen is intentional;
> files present but empty; no fab markings on visible faces).

There is **no record in this repo that it was ever sent**, and — the part that actually mattered —
*the lesson never reached a single reusable ordering document.* "No fab markings on visible faces"
was exactly the right instruction, written down in exactly the place nobody re-reads when placing
the next order. A correct instruction nobody is forced to notice is indistinguishable from no
instruction. Closing that gap is why this section exists and why the instruction now lives in four
places instead of one.

### 20.2 The instruction, and where it now lives

PCBWay's order form carries **`Remove product No.`** under Customized Services, with three options:
`No` / `Yes (extra +$ 1.5)` / `Specify a location`. Their instruction for the third:

> you can specify where to place Product No. for free. Please indicate the location by adding the
> text "WayWayWay" in the silkscreen layer and then select Specify a location. It is important to
> select the option, otherwise, we may not notice that you need to specify the location.

**The paid removal is deliberately NOT used.** Owner ruling, verbatim: *"No, why would we pay when
we can put it on the bottom side that is literally hidden from sight. Seems like an obvious note to
add to the order info."* The number is harmless on a face nobody sees; $1.50/order to delete it is
spend for nothing.

The instruction, as documented: set **`Remove product No.` = `Specify a location`** (free), and
state in the **"Other special request"** remarks box that the product number goes on the **bottom
face — the B.Silkscreen side, tray-facing and hidden once assembled** — and not on the top /
F.Silkscreen face, because the top face is the product's visible deck. TOP/BOTTOM here is the Z
axis: TOP = F.SilkS = the deck you look at; BOTTOM = B.SilkS = the face against the tray.

⚠️ **Honest limit on the token.** PCBWay's wording says *"the silkscreen layer"* — **singular**,
with no top/bottom language anywhere in it. Whether a `WayWayWay` token placed on **B.SilkS**
reliably yields **bottom** placement is therefore **a reasonable inference, not a documented
guarantee.** The load-bearing instruction is the plain-English remark in the "Other special
request" box; the token is belt-and-braces. Do not let a future pass upgrade this to a certainty
without evidence from an actual order.

Documented at, per the owner's directive that this land *"both in the fab pack as well as in
documentation for the GitHub"*:

| file | where |
|---|---|
| `v5-release-compiled/HOW-TO-ORDER.md` | Card 2, after the plate order settings |
| `v5-release-compiled/RELEASE.md` | §(e), Plate block |
| `agentpad13/HOW-TO-ORDER.md` (public mirror) | Card 2, same place |
| `agentpad13/hardware/case/README.md` (public mirror) | after the plate "Order settings" paragraph |
| this section | the why |

### 20.3 Generator support for the token

`gen_plate_fab.py` can now emit the token. `text()` gained a `layer` parameter (it hardcoded
`F.SilkS`), emits `(justify mirror)` for back-layer text — the idiom `v4_r27.kicad_pcb` uses on
every one of its own B.SilkS properties, so the text reads correctly when the physical bottom face
is viewed from below — and floors its stroke at PCBWay's 0.15 mm minimum. That floor is a latent
fix, not cosmetics: the old `thickness = size * 0.15` puts a 1.0 mm character at **exactly** the
0.15 mm minimum with zero margin, and anything smaller would have gone under it silently. At the
only pre-existing call sizes (1.0 and 1.2, in `coupon_shapes()`) the floor is inactive, verified
byte-for-byte, so no existing output moves.

The token itself: `EMIT_PCBWAY_PRODUCT_NO_TOKEN = True`, `"WayWayWay"` at **(42.1, 41.225)** on
**B.SilkS**, size **1.5 mm** (1.88× PCBWay's 0.80 mm minimum character height; stroke 0.225 mm =
1.50× their 0.15 mm minimum width). The location is the full-width clear band between switch row 1
(y 31.7, ends 38.700) and switch row 2 (y 50.75, starts 43.750): nothing lives in it — no cutout,
copper, mask opening or via — and it is horizontally unobstructed across the entire 84.4 mm width,
so a product number *longer* than the token still fits. Measured worst case, using a pessimistic
1.1 × size per-character advance: **1.550 mm** to the four nearest switch cutouts, and it is
nowhere near the TP5 pad/opening at (13.525, 88.85). Emitted line, identical in all three variants:

```
(gr_text "WayWayWay" (at 42.1 41.225 0) (layer "B.SilkS") (uuid "…")
  (effects (font (size 1.5 1.5) (thickness 0.225)) (justify mirror)))
```

Verification run this pass, no artifact written: dry-rendering `plate_shapes()` for all three
variants and diffing UUID-blind against the on-disk boards gives **exactly one added line and zero
removed lines** per variant — the token — and `validate_fab_v5.py`'s touch-marker gate is untouched
by construction (it filters `SHAPE_T_CIRCLE` on the *front* silk at TP5; a `gr_text` on B.SilkS at
mid-board matches nothing, and the `Edge.Cuts count == 89` gate sees no new edge shape). The
`text()` change is byte-inert for every pre-existing caller: at `coupon_shapes()`'s sizes 1.0 and
1.2 the new stroke floor is inactive, verified by re-deriving those five call sites against the old
formula and comparing byte-for-byte.

### 20.4 ⚠️ NAMED DIVERGENCE — the generator no longer reproduces the on-disk fab set

> ## ⚠️ `gen_plate_fab.py` NO LONGER REPRODUCES `fab/*.kicad_pcb` BYTE-FOR-BYTE.
>
> The token was added **without regenerating anything**, deliberately: a change to the encoder plate
> opening is under investigation and will require one regeneration, and doing it twice churns the
> hashes of a verified fab set.
>
> - **The on-disk `fab/` set is still the ordered geometry.** It carries **no** token. Every plate
>   artifact md5 is **unchanged** by the pass that wrote this section — all 15 checked, all
>   identical, including the three gerber zips, the three `_v5` boards, the DXF, the PNG/SVG and the
>   frozen Rev-A set.
> - **The NEXT regeneration introduces the token** into all three plate variants, and only then do
>   the emitted boards and this generator agree again.
> - **Anyone regenerating must re-run `validate_fab_v5.py` and re-hash** the affected rows in
>   `v5-release-compiled/MANIFEST.md`.
>
> **This section is the sole home of this warning.** It was going to be duplicated into
> `docs/HANDOFF-STATE.md`, but that file is being retired, so nothing else in the repo records it.
> Do not remove this box until a regeneration has closed the gap.

### 20.5 Also found, not fixed

`coupon_shapes()` (`gen_plate_fab.py`) references **`C.JS_APERTURE`, which no longer exists** in
`agentpad13_case_v2.py` — it was the v4 Ø16 circular joystick aperture, removed when v5 replaced it
with the asymmetric rounded-rect opening. The function therefore raises `AttributeError` if called.
This is **pre-existing and harmless today**: the v5 pass emits the three plate variants only, and
the module docstring already records that the coupon panel and touch chip *"stay UNTOUCHED on disk
as the record (their generators are preserved below, just not re-run)."* Noted so a future pass
that tries to re-run the coupon panel knows what it will hit first.

---

## 21. v2.8 — MODULAR TRAY BASE interface + base family (2026-08-19)

> ⚠️ **SUPERSEDED THE SAME DAY BY §22.** The four corner-boss pockets
> described here are GONE from `tray()`, and the four base variants below
> no longer exist. Kept as the record of why the corner interface was
> wrong: it did not make large bases wrong, it made them mandatory.
> The magnet arithmetic in §21.2 and §21.5 still stands and is the reason
> magnets remain rejected.

Owner directive (2026-08-18), verbatim:

> "We should think about the tray base as well. Perhaps we can come up with
> variants like angled ones? Or make this modular/stick on in some way so we can
> add bases or grips or whatever. Also low priority."

### 21.1 The change — four pockets, and nothing else

`tray()` gains ONE feature: a blind Ø3.6 × 2.0 locating pocket in each corner-boss
**bottom** face (z −7.5 → −5.5), cut before `_safe_chamfer` (which already
excludes r < BOSS_OD/2 + 2 around every boss centre, so the pocket mouth is
deliberately square — see below). No other geometry in the project moved. The
band, plate, PCB, firmware and every frozen tree are untouched.

New constants (`# --- Tray features ---`): `BASE_PEG_BORE = 3.6`,
`BASE_PEG_DEPTH = 2.0`, `BASE_PEG_ROOF_MIN = 1.2`, derived `Z_BASE_PEG_TOP = −5.5`.

### 21.2 Why this does NOT touch the 1.65 notched-corner watch-item

Two module-scope assertions make it structural, not a claim:

```
assert BASE_PEG_BORE <= M3_INSERT_PILOT              # 3.6 <= 4.7
assert Z_INSERT_BOT - Z_BASE_PEG_TOP >= BASE_PEG_ROOF_MIN   # 1.300 >= 1.2
```

The (0,0) boss is notched to a standoff of **3.7512** from its centre. The M3
insert bore (Ø4.7) therefore sets this part's current minimum wall at
**1.4012** over z −4.2 … +1.5. Because the pocket is *narrower* than the insert
bore, its wall on the same azimuth is **1.9512** — looser by +0.3000. And the
two thin bands occupy **different z ranges** (pocket −7.5 … −5.5; insert bore
−4.2 … +1.5), separated by 1.3 mm of full-section boss, so they can never stack
into one tall thin wall. **The tray's current minimum wall is 1.4012 mm.**
The pocket mouth is left un-chamfered on purpose: a 0.5 × 45° lead-in would
neck that azimuth to 1.451 at the bottom face for no functional gain, so the
lead-in chamfer lives on the *peg* instead.

Measured cost: **81.43 mm³** removed (0.45 % of the tray) and, *if* a bumpon is
still stuck directly on a boss bottom with no base fitted, **21 %** of its
Ø7.9 contact area. The base family carries its own feet, so that case is the
no-base fallback, not the intent.

### 21.3 Gate — `khana check agentpad13_case_v2.py`, verbatim deltas

```
status ok | assertions 101 | passed 101
interferences 8
    pcb_components x sockets      1.70565
    pcb_components x leds         2.736188
    sockets x leds               67.3259
    ec11_body x knob_sweep      342.225
    js_body x js_sweep            7.957625
    knob_sweep x knob          2417.455547
    js_sweep x stick_cap        280.547585
    switch_bodies x keycaps     500.29863
assertions added: []   removed: []   failed: []
interference pairs added: []   removed: []
part volume deltas vs the v2.7 banked mechanism.json:
    tray: -81.4301 mm^3      (all 19 other parts: 0.0000; no bbox moved)
```

The 8 interference volumes are **bit-identical** to the banked baseline. Only
the tray changed, and only by the four pockets.

Printability (ADVISORY, as always): tray `min_wall` **0.050741 → 0.050741,
unchanged**; overhang area 76.88 → 117.44 mm² = +40.56, which is exactly the
four Ø3.6 pocket roofs (4 × 10.18 = 40.72 nominal). Those are Ø3.6 bridges —
the tray already bridges its insert bores. Band printability byte-identical.

### 21.4 Artifacts

| file | md5 |
|---|---|
| `stl/agentpad13_v2_tray_v5.stl` | `d7d16481df24bae4c7769d7624dfc620` → **`2e4d510381c7a4420d46ce741a22fe22`** |
| `step/agentpad13_v2_tray_v5.step` | `476744d315b8fe6211e206dbf723e924` → `90fcee9c6cb29b735a9cb4915f1775a8` |
| `stl/agentpad13_v2_band_1.6mm_w5.4.stl` | `34be6bf79a6bb81995807448639f4822` — **UNCHANGED** |
| `step/agentpad13_v2_band_1.6mm_w5.4.step` | `1178b0fa5206eed273a2f817eff5da85` — **UNCHANGED** |
| `step/agentpad13_v2_plate.step` | `97df78de2c5c6f633ff92ee071a26dc0` — **UNCHANGED** |

⚠️ The band and plate **STEP** files re-export with a fresh
`FILE_NAME(...,'<timestamp>')` header line, so a plain re-run shows them as
"changed" while the geometry bodies are byte-identical. They were restored from
the pre-run copies after this session's gate run so the tree carries no churn
on parts that did not move. Any future `khana check`/`build` of the case script
will dirty them again the same way — check the body, not the md5.

⚠️ `v5-release-compiled/` still holds the **pre-v2.8** tray (md5
`d7d16481…`) and a copy of this file citing it. That bundle is a release
snapshot; it needs the coordinator's usual re-sync, not an in-place edit.

### 21.5 The base family — `bases/agentpad13_base.py`

New sibling of `toppers/`, same shape: one parameterised generator emitting a
variant × fit-rung STL matrix, a params JSON, and per-part printability. It
**imports `agentpad13_case_v2`** (CONSUME, never modify) and reads
`BOSS_CENTERS`, `Z_TRAY_BOT`, `BASE_PEG_BORE`, `OUTER_*`, `_TACTS`, so the
interface cannot drift from the tray and the outline tracks `WALL`
automatically.

4 variants × 3 peg rungs = 12 STL. Peg ladder **3.25 / 3.35 / 3.45** into the
Ø3.6 pocket — the knob-bore / stick-cap doctrine, because a nominal FDM hole
prints ~0.15 under and a nominal peg ~0.10 over, so CAD-equal would be a
0.25 mm interference. Print the three, keep the rung that holds.

| variant | tilt | thickness near → far | feet | print height | volume |
|---|---|---|---|---|---|
| `flat` | 0° | 2.40 → 2.40 | 4 | 4.00 mm | 22.9 cm³ |
| `grip` | 0° | 2.40 → 2.40 | 8 | 4.00 mm | 22.7 cm³ |
| `tilt_3p5` | 3.5° | 2.40 → 8.97 | 4 | 10.18 mm | 54.9 cm³ |
| `tilt_6p5` | 6.5° | 2.40 → 14.64 | 4 | 15.44 mm | 82.5 cm³ |

Every variant: outline 91.6 × 107.4 R6.0 (band outer − 2.0/side), mating plane
z = −7.5, **desk face on the bed, no support**. Feet are 3M SJ61A1 — the
bumpon already in the BOM — in Ø8.3 × 1.0 recesses concentric with the pegs,
i.e. at today's bumpon positions, so the support polygon does not regress and
every control (RE1 shaft, JS1, SW13, TP5) stays inside it.

Per-variant hard gate (`bases/outputs/<variant>/mechanism.json`): 5/5, `ok`,
including a positive `assert_interference("base", "tray_boss_pockets")` that
fires if anyone deletes the pockets from `tray()`.

### 21.6 Watch items this pass did NOT resolve

- The tray's advisory `min_wall` of **0.0507** is pre-existing and untouched.
  It is two tessellation-thin zones: perimeter-rail slivers around
  (73.6, 6.0) where two skip-cuts nearly meet, and the point at **x = 69.0**
  where the two service slots are *exactly tangent* (slot A starts where slot B
  ends), leaving a knife-edge web. Neither is caused by v2.8; the slot tangency
  in particular is worth a deliberate decision — merge the two slots or space
  them — rather than leaving a zero-width web in the model.
- Heat-set over-press buffer at the boss is now 1.3 mm rather than 3.3 mm. The
  insert has no hard stop; it is set by feel from the cavity side. First-article
  watch-item alongside the 1.6512 notch wall.

---

## 22. v2.9 — the CENTRAL MOUNT contract (2026-08-19). SUPERSEDES §21.

Owner directives, verbatim, the same day §21 was written:

> "No magnets, either just alternative trays or notches in the tray where bases
> can insert, whether TPU or hard filaments."

> "I'm just saying why is the base so big? Why don't we have the notche closer
> to the middle to enable a variety of styles perhaps even a circular pedestal
> like the actual Codex Micro."

> "A full footprint variety is fine too. Just saying regardless, we should have
> more flexibility in the bases this way esp if this is open source people can
> make their own."

**§21 is superseded, not amended.** Its four corner-boss pockets are removed
from `tray()`. The defect was not that v2.8's bases were large — it was that
putting the only attachment points 76.8 × 92.6 mm apart made large *mandatory*.
Every v2.8 variant was 91.6 × 107.4 by geometry, not by choice.

### 22.1 THE CONTRACT — publishable, and the actual deliverable

This is a spec sheet. Someone who has never opened `agentpad13_case_v2.py`
should be able to design a base from it. Machine-readable copy:
`bases/params/agentpad13_base_params.json` → `contract`.

| item | value |
|---|---|
| **datum** | centre of the case outline in plan = `(CX, CY)` = (42.1, 50.0) |
| how to find it | the band outer (95.6 × 111.4) **and** the tray outline (84.3 × 100.1) are *both* centred on it — measure the finished case with a ruler, no source read |
| **mating plane** | z = −7.5, the flat tray bottom = band bottom (coplanar). All base material at or below it. |
| **features** | 4 blind flat-bottomed cylindrical pockets, axes vertical, in the tray bottom face |
| pocket Ø | **6.0** (CAD nominal, no allowance) |
| pocket depth | **1.6** (z −7.5 → −5.9); 0.8 mm of floor left above |
| positions | **(±12.5, ±12.5)** from the datum — a 25.0 mm square; bolt circle Ø35.36 |
| mouth chamfer | **0.2 × 45°** — MEASURED, see §22.6 |
| **peg** | Ø from the ladder, **1.4** long, **0.4** tip chamfer, 0.2 seat gap |
| **fit ladder** | **5.60 / 5.70 / 5.80 / 5.90** — CAD diametral clearance 0.40…0.10 |
| default | 5.80 rigid filament, **5.90 TPU** (TPU compresses, so it takes the *tight* rung) |
| how to pick | print `bases/stl/base_fit_gauge.stl`, push each peg into any pocket, keep the rung that holds. Marks are raised dots: n dots = rung n, smallest first. |
| **orientation** | y = 0 is FAR (USB / control band, away from the user); y = 100 is NEAR (2U key). Landmark: **the USB port is on the far edge.** |
| **symmetry** | 4-fold — a base mounts in any of four 90° orientations, so one printed wedge tilts four ways |
| **load path** | vertical load goes through the FLAT MATING PLANE, never through the pegs. Pegs locate and take shear. |
| peg bearing area | 8.4 mm² each; at even 30 MPa that is ~250 N/peg against single-digit-newton service loads — engagement depth is *not* the limiting factor, location is the job |
| smallest base carrying the whole pattern | **Ø47.4** (bolt circle + peg Ø + 3 mm wall) |

**Keep-outs a base must respect**

| keep-out | extent | rule |
|---|---|---|
| BOOT/RESET service slots | x 59.0…76.0, y 83.3…93.3 (two rects) | any base covering this **must** carry a through window. Nearest slot corner is **39.182 mm** from the datum → a base staying inside **Ø78.36** never reaches it. |
| bumpon lands | the four Ø9.5 boss bottoms at (3.7, 3.7) (80.5, 3.7) (3.7, 96.3) (80.5, 96.3) | a base either provides its own feet or clears these |
| USB face | far edge, above the mating plane | a wedge that raises the far edge cuts plug-to-desk clearance |

**Why four plain round pockets and nothing cleverer.** The deciding criterion is
a stranger's *first* print on an unknown machine. A blind round hole and a round
peg are the one pair every FDM printer makes predictably, and the error is a
single number a builder can measure with calipers and correct by picking a rung.
A keyed recess, a dovetail ring, or a bolt circle with a spigot each add a
second dimension that has to land at the same time, and none of them buys
anything: the base is *located* by the pegs and *loaded* through the plane.
Ø6.0 over v2.8's Ø3.6 because press-fit hoop strain goes as (interference / D),
so for a given absolute print error the **larger** bore is the more forgiving
one — and it doubles the bearing area.

**Magnets stay rejected**, on §21's arithmetic, not revisited: a Ø6 pocket necks
the notched (0,0) boss wall to 0.651 mm against a 1.6512 minimum that is already
a first-article watch-item.

### 22.2 Three rulings

**(a) The v2.8 corner-boss pockets are RETIRED — not kept alongside.** A
full-footprint base does not need them: its own footprint already exceeds the
centre-of-pressure excursion of any credible press (§22.3), so the pegs never
see tension, and vertical load rides the mating plane. Keeping both would be two
interfaces to document, two to hold tolerance on, and two for a third party to
get wrong. **Retiring them also closes a §21.6 watch-item**: the heat-set
over-press buffer below each M3 insert goes back from 1.3 mm to **3.3 mm**, and
an SJ61A1 lands on a full Ø9.5 boss bottom again instead of losing 21 % of its
contact area.

**(b) The weight pocket is RETIRED.** It occupied x 12.1…72.1, y 43…73 — exactly
the centre of the floor — so it was the single obstruction to a central
interface. It was never ordered ("washers/bar stock + epoxy", no laser order),
never gated, referenced only by narrative docs, and flagged in its own comment
as *"3 mm steel = open item"*: at 1.6 mm deep it never fit the steel it was
drawn for. Capacity was 2.88 cm³ = **22.6 g** of solid steel, against the
research dossier's own +80–150 g target — it could not have hit its brief with
any filler. Retiring it restores 2880 mm³ of floor and takes the tray's 0.8 mm
region from **1800 mm² down to 113 mm²**. Ballast moves to the base, where it is
~10× larger, reversible, and below the desk plane instead of 6 mm above it.

**(c) Modular bases beat alternative trays, but not by much, and not always.**
The owner's alternative — *"just alternative trays"* — is genuinely competitive:

| | alternative tray | modular base |
|---|---|---|
| parts | 1 | 2 |
| interface, fit ladder, tolerance stack | none | yes — the whole of §22.1 |
| reprint cost to change angle | the **whole tray**: 21 cm³, 4 heat-set inserts, full disassembly | the base only; case never opened |
| can a third party contribute? | only by forking the case script | yes — print against a published spec |
| height added | none (integral) | base thickness |
| stiffness | one solid part | two parts on a plane + 4 pegs |
| desk-clearance at the USB port | designer controls it | base designer must not break it |

An alternative tray wins on part count, stiffness, and having no tolerance
problem at all. It loses on *everything the owner asked for*: swapping requires
pulling four screws, lifting the plate/PCB sandwich, and re-seating heat-set
inserts in a fresh print, and a third party cannot contribute an angle without
forking the generator. **Ruling: modular base.** The tray stays one part with
one published interface; angle, grip, height, and mount style all live in
reprintable bases. The honest caveat: for a *single* fixed angle the owner
personally wants forever, an alternative tray is the better engineering, and
nothing here forecloses it — `tray()` is still one parametric function.

### 22.3 Stability — the engineering that sizes a small base

A base narrower than the footprint makes the device **cantilever**. Two load
cases, and they respond to mass in *opposite* ways. Implementation and all
numbers: `bases/agentpad13_base.py` §4, recomputed on every run.

**(A) Vertical press**, force `F` at plan point `p`, weight `W` at plan `g`:
the ground reaction resultant sits at `CoP(F) = g + t·(p − g)`, `t = F/(W+F)`.
CoP walks the segment `g → p` and can never pass `p`, so **a press at a point
inside the support polygon cannot tip the device at any force.** If `p` is
outside and `t_e` is where the segment crosses the boundary,
`F_tip = W·t_e/(1 − t_e)`. Mass helps, linearly.

**(B) Horizontal push**, force `F` at height `h` above the desk: reaction offset
`d = F·h/W`; `F_tip = W·b/h` (`b` = boundary distance from the CG that way) and
`F_slide = μ·W`. It tips before it slides iff **`b < μ·h` — mass cancels**. Mass
cannot buy you out of a too-small base under a hard shove; only diameter can.
The CG's *height* appears in neither case, so where ballast sits vertically is
mechanically irrelevant — the pedestal's cavity is placed for printability.

**Assembled pad: 158.7 g**, plan CG **(41.56, 49.32)** — i.e. **0.54 mm left and
0.68 mm far of the datum.** The pad's own centre of mass lands within a
millimetre of the case-outline centre. That is *why* that centre is the datum,
and it is a measured result, not a convenience. Full per-part mass model with
provenance: `bases/params/agentpad13_base_params.json` → `stability.mass_model`.

**The governing case is not the farthest key.** It is a firm press on the
**encoder knob edge**, 56.1 mm from the datum — farther out than SW13 (38.9 mm),
and an EC11 push is a 2–4 N part against a keyswitch's ~1.5 N.

Minimum base mass for a circular pedestal, by diameter:

| Ø | for margin ≥1.5 at the 3 N design press | for margin ≥1.0 at the 5 N abuse press |
|---|---|---|
| 50 | 417 g | 480 g |
| 60 | 245 g | 289 g |
| 65 | 178 g | 215 g |
| **70** | **121 g** | **152 g** |
| 74 | 82 g | 108 g |
| 80 | 29 g | 50 g |

**A free-standing pedestal REQUIRES added mass — that is a result, not a
preference.** A Ø70 pedestal must weigh ≥152 g; printed solid in PLA its shell
is **67 g**. No infill setting closes that gap. Hence the ballast cavity.

Ø70 is not a styling pick either: it is set by the **service slots**. The
nearest slot corner is 39.182 mm from the datum, so a windowless circular base
caps at Ø78.36; Ø70 clears by 4.18 mm and keeps the pedestal free of a window.

**Baseline for comparison — the bare tray on its four bumpons cannot be tipped
by pressing anything.** Every control lies inside the 76.8 × 92.6 bumpon
rectangle; only the extreme edge of the 2U keycap is outside, and that tips at
42.8 N. Laterally it slides at 1.11 N before it could tip at 1.94 N. Any base
must be judged against *that*, not against zero.

### 22.4 The base family — `bases/agentpad13_base.py`

Two bases chosen to be **as different as possible**, to prove the interface is
style-agnostic. Same four pegs, same ladder, no special-casing.

| variant | outline | mass | ballast | worst margin | note |
|---|---|---|---|---|---|
| `pedestal` | **Ø70 × 20 circular** | 67 g shell + ballast | **required** | 1.16 | 20 % of the pad's plan area |
| `mat` | **91.6 × 107.4 full-footprint** TPU | 27 g | **none** | cannot tip | every control inside the support polygon |
| `wedge` | 91.6 × 107.4, 6.5° back-raised | 43 g | none | 19.93 | honours the 2026-08-18 "angled" directive |

`pedestal`: ballast cavity Ø48 × 15 opening **downward**, crossed by 2 rib bars
(4 arms) so the roof never bridges more than a quarter sector and the arms
divide the washer stack. Capacity **135 g** of steel at 70 % packing against a
**85 g** floor — 1.58×. Spec says **fill it**: at the floor the horizontal-shove
margin is only ~1.45, and filling lifts it to 1.69. Unballasted the pedestal is
67 g and **not stable**. Feet on a Ø59 bolt circle: solved, not chosen — it is
the only radius leaving ≥1.2 mm to both the cavity and the rim.

Every variant: **desk face on the bed, no support**, 4 ladder rungs each, plus
`base_fit_gauge.stl`. Per-variant hard gate `bases/outputs/<v>/mechanism.json`,
3/3 `ok`, including a positive `assert_interference("base","pocket_witness")`
that fires if anyone deletes the pockets from `tray()`.

### 22.5 Gate — `khana check agentpad13_case_v2.py`, verbatim

```
status ok | assertions 101 | passed 101
interferences 8
    pcb_components x sockets      1.70564999999999
    pcb_components x leds         2.7361875000000015
    sockets x leds               67.32590000000002
    ec11_body x knob_sweep      342.22499999999997
    js_body x js_sweep            7.957625486011078
    knob_sweep x knob          2417.4555469373463
    js_sweep x stick_cap        280.5475845757973
    switch_bodies x keycaps     500.29863008417453
assertions added: []   removed: []   failed: []
interference pairs added: []   removed: []
interference volumes vs banked baseline: ALL BIT-IDENTICAL
part volume delta: tray: +2778.9329 mm^3   bbox moved: False
all other 19 parts: 0.0000 mm^3, bbox unmoved
```

The tray delta decomposes **exactly**, verified by rebuilding at each stage:

```
  v2.8 banked tray                                    18207.7366
  + v2.8 corner pockets restored (4 x Ø3.6 x 2.0)      +  81.4301
  + weight pocket retired (60 x 30 x 1.6)              +2880.0000
  = tray with no base pockets, measured                 21169.1667   delta +0.0000
  - 4 pockets Ø6.0 x 1.6                               - 180.9557
  - 4 mouth chamfers at the REAL 0.2 (Pappus)          -   1.5414
  = 20986.6695 ; measured 20986.6695                    delta +0.0002
```

Printability (ADVISORY as always): tray `min_wall` **0.050741 → 0.050741,
unchanged**; overhang 117.44 → 189.24 mm², which is the four Ø6.0 pocket roofs
(113.1) replacing the four Ø3.6 ones (40.7). Band byte-identical.

| file | md5 |
|---|---|
| `stl/agentpad13_v2_tray_v5.stl` | `2e4d510381c7a4420d46ce741a22fe22` → **`2400881210502e9761e2de601235cd8f`** |
| `stl/agentpad13_v2_band_1.6mm_w5.4.stl` | `34be6bf79a6bb81995807448639f4822` — **UNCHANGED** |
| `step/agentpad13_v2_band_1.6mm_w5.4.step` | `1178b0fa5206eed273a2f817eff5da85` — **restored, unchanged** |
| `step/agentpad13_v2_plate.step` | `97df78de2c5c6f633ff92ee071a26dc0` — **restored, unchanged** |

⚠️ `step/agentpad13_v2_tray_v5.step` md5 is **NOT reproducible** — OCCT stamps
`FILE_NAME(...,'<timestamp>')`, so it differs on every run even when the body is
identical. §21.4 recorded one anyway; treat the **STL** hash as the geometry
gate and ignore the tray STEP hash.

### 22.6 What this pass did NOT resolve

- **`EFC_CHAMFER = 0.4` has never been achieved on the tray bottom.**
  `_safe_chamfer` tries 0.4, then 0.3, then 0.2 and takes the first OCCT
  accepts; on the z = −7.5 face it settles at **0.2**. Verified against the
  committed HEAD build (`9c8ea77`) as well as this one, so it is pre-existing
  and the tray's elephant-foot chamfer has always been 0.2, not the 0.4 the
  constant advertises. The base's peg was designed against the measured 0.2;
  designing against 0.4 would have made every ladder rung tighter than
  intended. **The constant should be corrected or the fallback made loud** —
  not touched here because it would move the whole tray outline.
- **3M SJ61A1 is Ø7.92 × 5.08 mm**, per DigiKey and 3M — not the Ø7.9 × 2.2 this
  repo models at `agentpad13_case_v2.py:50`, `CASE-V2-NOTES.md:36` and `:67`.
  Ø7.9 × 2.1 matches **SJ5302** instead. This moves the desk plane from −9.7 to
  ≈−11.6 and means the bumpon does not fit the modelled Ø8.3 × 1.0 recess.
  Unresolved: it is a case-wide datum question, not a base question.
- **The 0.0507 mm tray `min_wall` and the pedestal's 0.0557** are both estimator
  artifacts, not geometry — a *plain* Ø70 disc with a *plain* blind cavity
  (analytic minima 5.0 / 11.0 mm) reads the same 0.056. The pedestal's true
  minimum wall is 1.350 mm, asserted directly.
- **The x = 69.0 service-slot tangency is untouched** (§21.6). The two slots are
  still exactly tangent, leaving a zero-width web.
- **The governing force is an estimate.** EC11 push at 3 N design / 5 N abuse is
  a class figure, not a datasheet value for the fitted part, and Kailh BOX Jade
  mass (1.9 g) has *no* published figure at all. Both propagate into the
  pedestal sizing. Weighing one switch and measuring one encoder's push force
  would firm up the whole table.

## 23. v2.12 — the encoder plate opening, widened +1.0 to the RIGHT (2026-08-19)

**The defect, observed on the physical part.** The owner assembled the v5 top
plate and found the encoder did not sit right. His measurement and directives,
verbatim and in order:

> "1) wider hole (I'll measure to confirm, left side of hole is perfect, right
> side needs more space)"

> "the hole needs to be slightly rectangular, not square"

> "And no, don't widen the hole symmetrically, widen to fit the parts."

> "FYI the top plate hole should be 14mm (encoders were around 13.7mm). Left
> side of the hole is alright good, just expand the width to the right by 1mm."

**Coordinate convention** (agreed with the owner): viewed with USB-C facing UP,
the owner's LEFT is board −x and his RIGHT is board +x (the S1/S2 switch-pin
side).

**The change.** 13.000 × 13.000 → **14.000 × 13.000, R1.5**, centre
(13.525, 12.500) → **(14.025, 12.500)** = shaft + (0.5, 0). Absolute span
x **7.025 .. 21.025** (left edge FROZEN, right edge +1.000), y 6.000 .. 19.000
(unmoved). R stays **1.5** — deliberately NOT enlarged for knob concealment: a
bigger corner radius eats exactly the body-corner clearance the measured
~13.7 mm part needs. Body fit outranks cosmetics.

**Corner reach from the shaft is now asymmetric** (this is what the knob has to
cover):

| corners | arc centres (from shaft) | reach | vs Ø18 knob (r 9.000) |
|---|---|---|---|
| −x (frozen edge) | (−5.0, ±5.0) → 7.0711 | **8.571** | +0.429 hides |
| +x (widened edge) | (+6.0, ±5.0) → 7.8102 | **9.310** | **−0.310 EXPOSED** |

**KNOB RULING (owner-informed).** The Ø18 default no longer fully hides the
opening — a 0.310 mm sliver shows at each of the two +x corners. **Accepted**:
the measured body fit beats concealment. `KNOB_D` stays 18.0 and Ø18 remains
the floor. The escape hatch is the **Ø19 dome_cup (+0.190 hides)**, which is
**PARKED** — no knob STL was regenerated this pass. `toppers/encoder_knob.py`
now carries `HIDE_FLOOR = -0.310` so the script still passes on its own shipped
defaults (house doctrine: no gate may reject its own shipped state) while any
FURTHER regression still fails loudly.

**`ENC_BODY_SQ` stays 11.7** — it is the khana interference proxy. The owner
measured ~13.7 across the pin axis, but the DATUM is unresolved: a
shaft-centred 13.7 is contradicted by his own fit report ("left side perfect,
right side needs more space"), which is what an OFF-centre body does. Project
rule: mechanical claims come from a primary drawing or an owner measurement,
never a guessed datum. The OPENING was sized from the measured fit instead.

**⚠️ Carried open item.** `RELIEF_D = 17.4` (the ribbed_skirt Ø20 variant's body
relief cavity) was sized for the 11.7 ALPS body and is **UNVERIFIED** against
the ~13.7 generic body (half-diagonal ~9.27 → needs Ø18.5+). It would bind.
Only the ribbed_skirt variant is affected. Resizing needs a primary drawing or
a caliper of the body's above-deck profile — not guessed here.

**Measured consequence that did NOT move:** `fr4_plate × ec11_body` clearance
is **0.2979, unchanged** (gate ≥ 0.25). Widening to the right cannot improve it
— the binding corner is on the −x side, which is frozen. The +x corners
improved from 0.298 to ~0.64 and the +x flat from 0.65 to 1.65.

**Regeneration.** `gen_plate_fab.py` re-run: all three `_v5` plate variants
(`plate_v5`, `plate_tented_ring_v5`, `plate_blank_v5` — the blank DOES carry
the encoder opening), their 10-file gerber sets + zips, the Edge.Cuts DXF and
the top-view SVG/PNG. **This regeneration also ships the §20 `WayWayWay`
B.SilkS token for the first time, discharging the §20.4 standing divergence** —
the generator reproduces the on-disk fab set again. Rev-A (non-`_v5`) files,
the coupon panel and the touch chip were NOT re-run and are untouched.
`validate_fab_v5.py` updated to the adjudicated 14×13 @ (14.025,12.5) and
re-run: **ALL GATES PASS** (57 PASS / 0 FAIL). khana: 101/101, same 8
interference pairs at identical volumes; band and tray STL byte-identical.

## 24. v2.13 — the plate pocket was sized around a plate that never shipped (2026-08-19)

**The defect, measured on the assembled unit.** The owner saw a visible gap at
one end of the plate:

> "Is the original board really 100.2? Because the gap is closer to 1mm
> vertically. In our case, we won't reorder it, it's usable. But for future
> builds and public consumption. we should try to eliminate this gap. … This
> isn't about our existing order, it's about the correct moving forward. So no,
> we don't need to keep the ordered files, this is what prototyping is about."

> "The plate is already 100mm. That's already the final. The issue is the
> band's pocket, which you confirmed is 100.8? We should make the pocket 100.2
> then. Perhaps keep the 100.8 after all but that's the low tolerance version
> for people with crappy printers."

### 24.1 Root cause — the 100.2 ghost

The band's plate pocket was `PLATE_H + 2·PLATE_FIT`. `PLATE_H` was
`INNER_H − 2·PLATE_GROOVE` = **100.2**, the PRE-TRIM plate. The 2026-07-21
long-axis trim (owner: *"Resize the top plates to 100mm. That 0.2 is gonna cost
us 25%. Not worth it."*, §19) was applied **only inside `gen_plate_fab.py`**, as
a local subtraction, because the band was frozen at the time and `PLATE_H`
drives the pocket. So the model plate stayed 100.2, the shipped plate became
100.0, and the pocket was cut around a plate **that never existed**. Every
revision since inherited it.

`PLATE_LONG_TRIM` now lives in `agentpad13_case_v2.py`;
`PLATE_H = INNER_H − 2·PLATE_GROOVE − PLATE_LONG_TRIM` = **100.0**, and
`gen_plate_fab.py` consumes `C.PLATE_H` directly instead of re-doing the trim.
**The fab files did not move** — proven by a UUID-blind dry render of all three
plate variants against the on-disk v2.12 set: **zero geometric delta lines**,
nothing overwritten.

### 24.2 The decision trail (it reversed twice — recorded so it stays settled)

1. Pocket → 100.2, legacy 100.8 kept as a low-tolerance variant.
2. Asked whether the WIDTH should tighten too, the owner declined: *"What's the
   current width (in what is now the loose tolerance version?). That's honestly
   fine as is. Small visible gap but tolerable."* → briefly a Y-only change.
3. Withdrawn: *"Nah let's go with the original plan. 84.6 or maybe 84.8. +/-0.2.
   Thoughts?"* → **84.6**, a uniform 0.1/side on both axes and the corner R.
   Rationale for symmetry: one number to reason about and an even 0.1 reveal all
   the way round instead of 0.3 on the sides and 0.1 on the ends.
4. The two-variant plan collapsed to one: *"I'm kind of inclined to make this
   the only version actually. Since even on crappy printers, someone can sand."*
   → **ONE band ships. There is no `_loose` artifact anywhere.**

**Why one version is the safe call:** the two error directions are not
symmetric. Too TIGHT is correctable by anyone in a minute with sandpaper. Too
LOOSE cannot be fixed at all — the plate rattles and the band must be
reprinted. The shipped fit is deliberately the correctable direction.

### 24.3 Geometry and float table

| | pocket | plate | X float | Y float | corner gap |
|---|---|---|---|---|---|
| legacy (shipped through v2.12) | 85.0 × 100.8 R5.7 | 84.4 × 100.0 R5.4 | 0.6 | **0.8** | 0.2 |
| **v2.13 (the only band)** | **84.6 × 100.2 R5.5** | 84.4 × 100.0 R5.4 | **0.2** | **0.2** | **0.1** |

At the tight fit the pocket and plate corner arcs are **exactly concentric**
(both centred ±36.80, ±44.60), so the gap is a uniform **0.100 mm on the flats
AND at the corners** — not merely a flat-face figure. The legacy pocket was
non-concentric in Y (centres ±44.70 vs ±44.60), which is where the 0.8 mm
end-float came from.

Pocket wall vs the inner cavity wall: X **+0.10/side**, Y **+0.20/end** (legacy
was −0.10 on both, i.e. a shallow undercut into the sidewall). Both axes now
present a shallow **lip above the ledge**. This adds no new overhang: the rabbet
ledge below already stands `LEDGE_W` = 1.2 mm inboard, far proud of the lip.
Band printability advisory is **unchanged** (`min_wall` 0.7333333333333292,
overhang 896.53 mm² — identical to v2.12), and band volume rises
**+142.65 mm³**, which matches the closed-form pocket-shrink prediction of
142.65 mm³ exactly.

### 24.4 Tolerance honesty

0.1/side is tight for a printed part. At a worst-case stack (fab routing up to
+0.15 on the plate, plus resin/FDM cavity shrink) the plate may need a **light
sand** to drop in. That is the accepted trade. If a printed pocket comes out
too tight there are two remedies, in order of effort: sand the pocket walls
lightly, or raise **`PLATE_FIT`** in `agentpad13_case_v2.py` and re-export —
**the generator is the loose variant**. 0.3 reproduces the legacy pocket on X
and the corner radius.

**The owner's 2026-07 PCBWay resin band is dimensionally the LEGACY pocket**
(85.0 × 100.8, ~0.8 mm y-float). It is usable and is not recalled — the owner
explicitly kept it: *"In our case, we won't reorder it, it's usable."*

### 24.5 Geometry-neutrality proof (scratch-only)

To prove the `PLATE_H` refactor and the fit restructure changed nothing except
the intended pocket, the band was rebuilt in the scratchpad with the pocket
forced to the legacy geometry and hashed against the ordered file:

```
legacy-pocket band md5 = 34be6bf79a6bb81995807448639f4822
ordered band      md5 = 34be6bf79a6bb81995807448639f4822   BYTE-IDENTICAL
```

**A trap worth recording.** The first attempt at this proof FAILED. Reproducing
the legacy pocket from rounded decimals (`85.0, 100.8, 5.7`) is *not* the same
geometry as the original expressions: the pre-v2.13 chain accumulates float
error — `PLATE_W + 2*0.3` is `84.999999999999986`, not `85.0`. That ~1.4e-14
propagates into the tessellated STL coordinates and changes the file's bytes.
The proof passes only when the ORIGINAL EXPRESSIONS are used. `LEGACY_POCKET`
in the source is therefore labelled **nominal, for documentation only**, with
the reproduction recipe written beside it. No loose artifact was ever written
into the repo.

## 25. v2.14 — is the USB-C aperture in the right place? (2026-08-19)

Owner, after the tray's mirror defect was found:

> "let's ensure the USB-C port cutout is in the right place. There was a good
> chance it was mirrored like the tray as well, but since the port is close to
> center, it wasn't an issue. Let's make sure this is right. Should it just be
> centered? … once [the band] is done, that port should be recalculated and
> repositioned if necessary."

**Answer: it is already exactly centred, and nothing was repositioned.** This
section is verification, asserts and documentation — **no geometry changed**;
every band, tray and plate artifact hash is byte-identical across this pass.

### 25.1 Recalculated from board truth

Derived from the contract, not from the case constants:

| quantity | expression | value |
|---|---|---|
| J1 x | `contract_v4.json refs.J1.x` | **42.100000** |
| board/band x-centre | `CX = PCB_W / 2` = 84.2 / 2 | **42.100000** |
| `USB_X` | `_REFS["J1"][0]` | **42.100000** |
| `USB_X == CX` | exact float equality | **True** (difference `0.0`) |

Built-solid measurements:

| cut | x span | centre | width |
|---|---|---|---|
| band aperture | 37.1000 .. 47.1000 | **42.100000** | 10.0 |
| USB funnel (w5.4) | 34.6000 .. 49.6000 | **42.100000** | 15.0 |
| receptacle envelope | 37.3000 .. 46.9000 | **42.100000** | 9.6 |

Aperture-to-receptacle clearance is **+0.200 mm on the left and +0.200 mm on
the right** — symmetric to the last digit. In z the aperture runs −5.000 ..
−1.400 against a receptacle envelope of −4.860 .. −1.600: clearance **+0.200
top, +0.140 bottom**, i.e. the aperture centre sits **+0.030 mm** above the
envelope centre at the design datum. (Recorded as measured. The z centring is
not what protects the band — the x centring is.)

Confirmed at the shipped-artifact level too: in
`agentpad13_v2_band_1.6mm_w5.4.stl` the aperture edges at both z limits are
x 37.1000 and 47.1000, centre **42.100000**.

### 25.2 Why the band survived the left-handed export, stated properly

The design frame is left-handed (y runs DOWN, from raw KiCad board coords)
while STL/STEP are right-handed, so everything exported through this path is
the **enantiomorph** of the intended part. The tray was visibly wrong and is
mirrored at export (§v2.10). The band is exported **un-mirrored** and is
nevertheless right. The reason is achirality, and it is measurable:

> A solid possessing **any** mirror plane is achiral — its enantiomorph is
> congruent to it by a rigid motion.

CAD booleans on the v2.13 band (`part − mirror` and `mirror − part`):

| part | mirror plane x = 42.1 | mirror plane y = 50.0 |
|---|---|---|
| **band** | **0.000000 / 0.000000 mm³ — EXACT** | 373.57 mm³ (not symmetric) |
| tray (control) | 1034.23 mm³ | 1181.00 mm³ |

The band has an exact mirror plane at x = CX; the tray has none, which is
precisely why one needed the export fix and the other did not. Composing the
export reflection (about XZ, y → −y) with the band's own x-mirror yields
(x, y) → (−x, −y) — a pure **180° rotation about z**. The "wrong-handed" band
is therefore the correct band, merely rotated, and the USB hole is the feature
that tells you which way round it goes. That is the exact sense in which the
owner's intuition ("since the port is close to center, it wasn't an issue")
was right — with the correction that it is not *close to* centre, it is *on*
centre, and only the exact case buys immunity.

Note the band is **not** y-symmetric (373.57 mm³) and does not need to be:
achirality requires only one plane. The USB feature is what breaks y while
being centred in x.

### 25.3 The invariant, and what now protects it

The x mirror plane exists only because every x-asymmetric candidate feature is
centred on x = CX. Today there is exactly one such feature — the USB aperture
and its funnel. Two build-time asserts (plain Python; the khana count stays
101) now pin it:

1. **Constants**, at import: `USB_X == CX`.
2. **Geometry**, inside `band()`: the built aperture and funnel bounding-box
   centres must equal **`CX`** — deliberately *not* `USB_X`. Comparing a cut
   against the constant it was built from is vacuous: it passes by
   construction even with the port moved. That mistake was made and caught by
   a negative control during this pass; pinning to `CX` catches both failure
   routes (a moved `USB_X`, and an offset written into a cut expression) and
   was verified to fire at offsets of ±0.5 and even **+0.001 mm**.

Both assert messages state the consequence in full: *the band is exported
un-mirrored, which is safe only while it is achiral; move the port off centre
(or add any other x-asymmetric band feature — a vent, a logo, a side button)
and the band becomes chiral, so its export must then be mirrored exactly the
way the tray's is.* Doing one without the other ships a wrong-handed band.

**Ruling (coordinator, 2026-08-19): mirror-at-export for the band is DEFERRED**
— it would churn six artifacts for a physically identical part and break the
`34be6bf7…` citation chain, and the right moment to adopt it is when a real
x-asymmetric band feature lands, so the export change and the geometry change
ship together — **and to make that deferral airtight rather than merely
signposted, a third assert now runs on every build**: `_verify_band_achiral()`
tests the FINISHED band solid against its own mirror about x = CX (both
difference volumes must be < 1e-6 mm³), which is feature-agnostic and so
catches the *unknown* asymmetric feature the two per-cut asserts are blind to.
It costs ~0.4 s, runs once per process (the geometry is fixed by import-time
constants), and was negative-controlled with an off-centre vent that the USB
asserts cannot see — caught at 64.8 mm³, and at a 1 × 1 mm nick too.

## 26. v2.16 — the base catalog: riser, wedge, pedestal (2026-08-20)

The v2.15 family (`pedestal` / `mat` / `wedge`) was a demonstration that the
central-mount interface works for wildly different shapes. It is now cut down
to an actual product line. Owner:

> "I only see the need for two official bases to start. A flat one that
> elevates slightly further, and an angled one at some reasonable degree.
> Perhaps a circular angled one if we want to get stylish like Codex Micro."

> "So I think 2 or 3mm is enough for the riser. Maybe it can be printed in TPU
> or something. THw wedge sesems fine. And then the pedestar is the wedge but
> just a circular cutout of it from above. No need for the ballast if the
> diameter is reasonable enough . Keep it fucking ismple. I think 6.5° is too
> low but IDK, you tell me. Base this on real products, maybe it's not too low,
> what is a typical mechanical keyboard pitch?"

Then, on the researched answer: **"Ship it."**

### 26.1 The catalog

| variant | what it is | body | mass | ballast |
|---|---|---|---|---|
| `riser` | 91.6 × 107.4 flat sheet | **3.0 mm** | 33 g TPU | none |
| `wedge` | same plan, back-raised | 2.4 → 17.49 mm | 50 g @20 % | none |
| `pedestal` | Ø78 tilted drum | 2.4 → ~15 mm | **59 g SOLID** | none |

`mat` is **retired** — the riser replaces it (same plan, 2.4 → 3.0 body). Its
files are deleted from the working tree, the bundle and the mirror rather than
kept as a museum piece. `wedge` and `pedestal` keep their names with new
geometry.

### 26.2 The angle: 8.0°, from real products

Owner asked for the typical mechanical-keyboard pitch rather than a guess.
Researched (whatgeek, attackshark): the mainstream standard sits at **7°**, the
comfort band across real boards is **4–8°**, and high-profile customs land
**6–8°**. Adopted **8.0°** — the top of the band, because this deck is a
13-key pad rather than a full-height board, so it needs the steeper end to read
as a typing angle at all. It is ONE constant (`WEDGE_DEG`), shared by the wedge
and the pedestal, so they cannot disagree. Far-edge height derives as
`BASE_T + BASE_H·tan 8°` = 2.4 + 15.09 = **17.49 mm**.

### 26.3 The pedestal, built literally as described

`pedestal = full_base(WEDGE_DEG, windows=False) ∩ vertical cylinder Ø78`. One
boolean, so the angle, mating plane, peg pattern and desk face are all
INHERITED from the wedge. No ballast cavity, no ribs, no service windows. Its
desk face is the tilted plane clipped to the cylinder (an ellipse), so it sits
flush and tilts the device by the same 8°. Because the cylinder is vertical,
its plan silhouette is exactly the circle — which makes the support polygon an
exact r = 39.0, not an approximation.

### 26.4 ⚠️ Ø78 is forced, and it costs the old 2 mm slot margin

This is the one place "safely" bit, and it deserves the full record. A
windowless, unballasted pedestal must satisfy two constraints that **pull in
opposite directions**: clear the BOOT/RESET slots, and carry enough of its own
mass not to tip. Measured across the range, printed solid:

| Ø | slot keep-out | SM design (3 N, bar 1.5) | SM abuse (5 N, bar 1.0) | verdict |
|---|---|---|---|---|
| 70.00 | 4.18 | 1.19 | 0.71 | design FAIL |
| 74.36 | 2.00 | 1.45 | 0.87 | design FAIL |
| 76.00 | 1.18 | 1.56 | 0.94 | abuse FAIL |
| **78.00** | **0.18** | **1.72** | **1.03** | **both OK** |

The largest circle meeting the module's old blanket "2 mm clear of the slots"
rule is Ø74.36, and it reaches only **SM 1.45 against the 1.50 design bar** —
so that rule and the stability bars are mutually exclusive. **Ø78 is not a
preference; it is the only point that clears both without ballast**, which is
exactly what the owner asked for.

The keep-out is therefore re-derived rather than deleted. The 39.182 mm figure
is the slot's *bbox* corner; the tray cuts those slots with `SVC_TOOL_R` corner
radii, so the nearest real material is **39.518 mm** out and the true clearance
at Ø78 is **0.518 mm**, not 0.182. The assert now measures against that real
geometry with a **0.40 mm** print-tolerance floor, plus a hard assert that the
base can never actually reach a slot. A base would have to print ~1 mm oversize
on diameter before it began to overlap, and even then it would encroach on one
rim corner of a 7–10 mm wide slot. **If anyone wants a larger pedestal, the
answer is the symmetric service-window pair (`full_base(..., windows=True)`,
already implemented), not a tighter margin.**

### 26.5 No ballast — infill is now the structural setting

The Ø70 pedestal needed 69–135 g of steel. At Ø78 the printed part carries
itself, **if it is printed solid**:

| effective solidity | mass | worst SM (5 N abuse) |
|---|---|---|
| 1.00 (solid) | 59.1 g | **1.03** ✓ |
| 0.62 (3 walls / 20 % gyroid) | 36.6 g | 0.93 ✗ |

So the docs say it plainly: **print the pedestal solid.** A normal sparse print
clears the 3 N design case (SM 1.56) but *not* the 5 N abuse case. Note the
abuse margin is **1.03 even solid** — this base is at the edge by construction,
because the slot keep-out caps the diameter. That is stated, not smoothed over.
The `riser` and `wedge` span the full footprint and cannot tip in any of the 16
modelled load cases.

### 26.7 ⚠️ CAUGHT IN VERIFICATION — the pedestal shipped with short pegs

Found by the coordinator's independent STL parse, not by any gate here, and
worth recording as a gate-design lesson.

**The defect.** The pedestal's four pegs were **0.4 mm short** and their tip
chamfers were gone — decapitated into flat stubs with no insertion lead-in —
while the riser's and wedge's pegs were correct:

```
riser     z -12.50..-8.10   peg tips -8.10  ✓
wedge     z -26.99..-8.10   peg tips -8.10  ✓
pedestal  z -24.93..-8.50   peg tips -8.50  ✗  0.4 mm short
```

**The cause.** `pedestal()` cut the plan silhouette with a cylinder whose
z-top was hand-written as `MATE_Z + _OVER` = −8.5. Peg tips reach
`MATE_Z + PEG_LEN` = −8.1, so the cut sliced 0.4 mm off every peg — and since
`PEG_TIP_CHAMFER` is exactly 0.4, the removed part was precisely the chamfer.
A silhouette cut is supposed to carry information in its RADIUS only; its
z-bounds should be structurally incapable of touching anything, and a
hand-written constant made them capable.

**Why no gate caught it.** The peg-containment gate asks *"is each peg inside
its pocket?"*, and a peg that is too SHORT passes that test perfectly — it is
contained with room to spare. Containment is blind to length by construction.
Demonstrated on the broken solid: containment reports **0.000000 mm³ outside**
while the part is plainly wrong.

**The fix, and why it makes the class impossible.** The cylinder's z-bounds are
now derived from the solid's own bounding box (`bb.min.Z − _OVER` …
`bb.max.Z + _OVER`), so no hand-written number can ever clip geometry again.
Plus a new per-variant gate, `assert_pegs_intact()`, which takes everything the
built part has above the mating plane — exactly its pegs, since every body tops
out at `MATE_Z` — and requires it to be **geometrically identical** to the
reference `_pegs()` solid, both difference volumes < 1e-6. That catches a
truncated peg, a short peg, a missing peg, a lost tip chamfer and a
mispositioned peg alike. A companion assert pins the tip z to
`MATE_Z + PEG_LEN` exactly. Negative control on the original broken solid:
**caught, 36.710557 mm³ missing** (the four tips).

Only the four pedestal STLs changed; riser, wedge and the fit gauge are
byte-identical across the fix.

### 26.6 Everything else held

x-symmetry design law: exact (0.000000 mm³) on all three, the pedestal
symmetric by construction since the cylinder is centred on the pattern
centreline. Mirror-at-export retained; all four pegs of all three variants
proven CONTAINED in the mirrored tray's pockets (0.000000 mm³ outside), and
both tilted variants verified thick at the exported USB edge. Per-variant khana
gates ok 3/3. Main khana untouched at 101/101/8; tray and all three band STLs
byte-identical.

## 27. v2.17 — the toppers v2 re-point (2026-08-20)

The v2 topper families landed (toppers commit `74a4b07`) and the case was still consuming the
v1 params. This pass re-points it, re-gates it, and retires v1. **No case geometry moved** —
band, tray and plate are byte-identical across the whole pass; only the topper *envelopes*
this file models changed, and with them the interference ledger.

⚠ **This section SUPERSEDES the frozen `101/101/8` gate record** quoted in §22.5, §26.6 and
§23. Section §28 then supersedes this section's flange and oval-puck geometry. The assertion
count remains **104 assertions / 104 passed / 9 interference pairs**.

### 27.1 What re-pointed

`agentpad13_case_v2.py` now loads `toppers/params/stick_topper_v2_params.json` and
`encoder_knob_v2_params.json`. Bare `[]` subscripts throughout — a missing or renamed key
raises `KeyError` at import rather than silently falling back, which is the same fail-loudly
contract v2.4 shipped with. Four schema differences had to be absorbed:

| v1 schema | v2 schema | how the case handles it |
|---|---|---|
| `variants[default_variant]` | no `default_variant` | knob: envelope read from the **top level**, plus a loop asserting all three textures (A/B2/C) share it. Stick: the two shipped parts are named explicitly (`nub_C2`, `puck_TPU`). |
| `opening_corner_reach` scalar + `_min` | one dict `{plus_x, minus_x}` | same two numbers (9.3102 / 8.5711), same meaning; the existing geometry cross-check still passes. |
| `pivot_z`, `tilt_deg` present | **absent** | stated in the case from the YA13 drawing `[D]` (pivot 6.1, full throw 30°) and **cross-checked at import** — see 27.2. |
| `skirt_bottom_z` / `knob_top_z` | `bottom_z` / `top_z` | direct rename. |

Envelope changes that follow:

| | v1 | v2 |
|---|---|---|
| `knob` / `knob_sweep` | Ø18, +8.0..+17.5 (sweep from deck +5.0) | **Ø17.5 grip + low Ø18.8 cover flange, +8.0..+27.0** |
| `stick_cap` / `js_sweep` | `taper` cone, 30° | **`nub_C2`** plain Ø6.189 +14.4..+19.6, 30° |
| — | — | **NEW `js_sweep_puck`** — `puck_TPU` at the full **30°** travel |

`KNOB_D` / `KNOB_H` were hard `[§5]` constants and are now params-wired.

**Why two stick parts.** The v2 family ships two joystick toppers with different outer
profiles. Both preserve the joystick's full 30° mechanical travel, so the case sweeps both
through the same full cone and gates each envelope independently. Neither part contains a
restrictor; both are solid except for the rectangular shaft socket.

### 27.2 pivot / tilt have no home in the v2 params — so they are cross-checked, not trusted

The v2 params publish no `pivot_z` or `tilt_deg`, so those three numbers are stated in the case
from the YA13 drawing. Rather than leave them as bare assertions of fact, each is re-derived
against a number the params *do* publish, and the derivation fails at import if they disagree:

- **nub:** its lowest swept point rides the 0.3 bottom fillet, so the extremum is
  (rotated fillet centre) − 0.3. From pivot 6.1 / 30° / R 3.0945 / fillet 0.3 that is
  **11.8506**; params publish `deck_low_z` **11.851**. This single assert validates pivot,
  tilt *and* the fillet radius simultaneously.
- **puck:** the case consumes the corrected solid outer profile and applies the same 30°
  pivot transform as the nub. No seat, cone-land or stop-angle datum remains in the live
  contract.

Both tolerances are 1e-3 because the params are published to 3 dp.

### 27.3 OCCT containment gate

The corrected puck's case envelope is deliberately simple and conservative: a full-height
9.400 × 6.350 mm oval prism that contains the actual rolled edges, shallow top cup and blind
shaft socket. `_tilt_sweep` still asserts `(south − swept).volume < 1e-3`, because an OCCT
union that silently loses material would make the clearance result optimistic. The due-south
operand is the one carrying the tightest reach toward SW4.

### 27.4 Gate — `khana check agentpad13_case_v2.py`, verbatim

```
status ok | assertions 104 | passed 104
interferences 9
    pcb_components x sockets        1.70564999999999
    pcb_components x leds           2.7361875000000015
    sockets       x leds           67.32590000000002
    ec11_body     x knob_sweep     342.22499999999997
    knob_sweep    x knob           4614.511090465772
    js_sweep      x js_sweep_puck  1238.750478654512
    js_sweep      x stick_cap      156.435095048379
    js_sweep_puck x stick_cap      156.43509504837897
    switch_bodies x keycaps        500.29863008417453
```

**Assertions 101 → 104.** Exactly three added, all `assert_no_interference`, giving the puck
sweep the same case-side gate set the nub sweep has: `js_sweep_puck` × `fr4_plate` / `band` /
`screws`. None removed, none failed.

**Every interference delta, with its cause:**

| pair | v2.16 | v2.17 | cause |
|---|---:|---:|---|
| `pcb_components × sockets` | 1.70565 | 1.70565 | untouched |
| `pcb_components × leds` | 2.73619 | 2.73619 | untouched |
| `sockets × leds` | 67.32590 | 67.32590 | untouched |
| `switch_bodies × keycaps` | 500.29863 | 500.29863 | untouched |
| `ec11_body × knob_sweep` | 342.22500 | current gate | The corrected sweep uses the Ø18.8 low flange plus Ø17.5 grip; see the regenerated mechanism report. |
| `knob_sweep × knob` | 2417.45555 | **4614.51109** | tautological — the sweep contains the static stepped knob: the Ø18.8 flange from +8.0..+9.2 plus the Ø17.5 grip from +9.2..+27.0. |
| `js_sweep × stick_cap` | 280.54758 | **156.43510** | same tautology — = the nub's own volume, π·3.0945²·5.2 = 156.43509504837903. |
| `js_body × js_sweep` | 7.95763 | **REMOVED** | the nub sweep floors at z 11.741, *above* `js_body`'s top at 11.1. The v2.5 taper dipped to 10.467 and clipped the joystick's own pot boxes; the nub does not reach them. |
| `js_body × js_sweep_puck` | — | **none** | The corrected puck envelope floors at z 11.701, above `js_body`'s top at 11.1. |
| `js_sweep × js_sweep_puck` | — | **1238.75048** | **NEW, modelling artifact.** The two sweeps are ALTERNATES — never fitted together. |
| `js_sweep_puck × stick_cap` | — | **156.43510** | **NEW, modelling artifact**, same alternates pairing: the puck sweep fully contains the upright nub, so again = the nub's own volume. |

The three alternate-vs-alternate and by-design pairs are **reported, never asserted** —
gating them would be gating a configuration that cannot physically exist.

Printability (ADVISORY as always) unchanged: band `min_wall` 0.733333, overhang 896.53 mm²;
tray `min_wall` 0.051463, overhang 170.93 mm².

### 27.5 The SW4 advisory was printing a false alarm — fixed

`[v2.5-JS-KEYCAP]` computed `SW4_edge_y − js_sweep.bbox.max.Y`. That was only *accidentally*
meaningful for the v2.5 taper, whose south extreme happened to sit inside the keycap z band.
The nub's south extreme is at z ≈ 16.24, **above** the keycap proxy top (14.6), so that bbox
corner is not a point any keycap can touch. The old formula prints **−0.100 mm** where the
solids are **0.736 mm** apart. A reporting gate that cries wolf is a defect, so the line now
reports the true 3-D `distance_to`, for both toppers:

```
[v2.17-JS-KEYCAP] nub_C2 @30°:     overlap 0.00 mm^3 ; TRUE 3-D min distance = +0.736 mm
[v2.17-JS-KEYCAP] puck_TPU @30°:   overlap 0.00 mm^3 ; TRUE 3-D min distance = +0.655 mm
```

⚠ **MODEL CAVEAT, now printed at every run.** Any SW4-clearance number must name its keycap
model, because the case and the toppers do not use the same one:

| | keycap model |
|---|---|
| **this case** | 18.0 sq × z 10.6..14.6, tagged `[CONVENTION]` — a coarse proxy |
| **the toppers** | the real inserted cap: 17.50 wide, rim +11.6, top +17.6 dish / +18.2 plateau |

The case cap is 0.5 mm **wider** and 3.0–3.6 mm **shorter**. Both parts were sized against the
*toppers'* model: the nub publishes +0.2508 mm and the puck +0.3004 mm at full throw. Those are
the numbers that govern the physical parts. The case's +0.736 / +0.655 are a different
measurement, not a contradiction —
never quote one as "the" SW4 clearance. This discrepancy is **pre-existing**, not introduced
here, and is left as a watch item: the case's keycap proxy is the cruder of the two.

### 27.6 Cover the opening without crowding the key

The plate opening's far +x corners reach 9.3102 mm from the shaft. A uniform Ø18 grip leaves
them exposed; a uniform Ø19 grip crowds the adjacent key. The corrected knob separates those
jobs: a low Ø18.8 flange covers the opening by +0.0898 mm and ends at +9.2, below the keycap
rim at +11.6, while the visible grip is Ø17.5. The case models that stepped envelope rather
than treating either diameter as a full-height cylinder.

### 27.7 Artifacts

| file | md5 | |
|---|---|---|
| `stl/agentpad13_v2_tray_v5.stl` | `8bfd7eafd7608e209b3cd3c1e5a6e2f1` | **UNCHANGED** |
| `stl/agentpad13_v2_band_1.6mm_w5.4.stl` | `60c74d75bfd024696d6d2e261d4f8083` | **UNCHANGED** |

Verified before and after the re-point *and* after the v1 archive move. ⚠ Note that
`khana check` on this script is **not** a dry run — the `__main__` block exports
unconditionally, so every gate run rewrites `stl/` and `step/`. The STLs come back
byte-identical; the three STEPs churn on the OCCT `FILE_NAME` timestamp (§22.5) and were
reverted, so the STL hash remains the geometry gate.

### 27.8 v1 retired to `archive/toppers-v1/`

35 files moved with `git mv` (3 modules, 2 params, 7 printability JSONs, 21 STLs, 2 renders) —
`stick_cap.py`, `encoder_knob.py`, `render_toppers.py` and everything they emitted. A repo-wide
grep confirmed before the move that the only live consumer was this case script; the
`[TOPPER stick_cap.py:92]`-style strings in the v2 modules are provenance citations, not
imports. `hardware/case/toppers/` is now v2-only. See `archive/toppers-v1/README.md` and the
index row in `archive/README.md`.

**Deliberately NOT touched:** `release/hardware/case/v2/toppers/` still carries a copy of the
v1 set. It is a compiled release snapshot, and this repo's archive convention is that an edited
snapshot is no longer a snapshot; the next release recompile carries v2 wholesale.

## 28. Topper geometry correction — remove unrequested features (2026-08-21)

Section §27 introduced two design choices that were not owner requirements: a low encoder-knob
cover flange and an east-west oval joystick puck. Both are removed.

- Every encoder knob is now a straight **Ø17.5 mm** body from +8.0 to +27.0, with no skirt,
  flange or bore lead-in. Plate-opening coverage is not a knob requirement. At the 19.2 mm
  center pitch beside a 17.5 mm keycap, the body leaves a **1.7 mm horizontal gap**.
- The TPU puck is now round **Ø6.350 mm**. Like the nub, it is solid except for the blind
  rectangular shaft socket and retains the joystick's full 30° travel.
- Encoder `clearance_low` follows the conventional nominal push-on D-shaft size:
  Ø6.0 / 4.5 mm across-flat. `clearance_high` is the bounded FDM-compensation
  option, Ø6.3 / 4.8 (0.15 mm radial and flat clearance, the owner-set maximum).
  The rejected Ø6.6 / 5.1 high fit was physically far too loose. The joystick
  pair was tightened after physical testing:
  `clearance_low` is 2.10 × 1.30 mm and `clearance_high` is 2.30 × 1.50 mm
  against the measured 1.70 × 1.00 mm shaft. The rejected 2.50 × 1.80 mm
  socket could rotate fully because its 1.80 mm short side exceeded the
  shaft's 1.70 mm long side; even the current high socket cannot do that.

The knob basis is not a guessed fit table. Alps Alpine EC11E Drawing No.2
publishes the shaft as Ø6 with 4.5 ±0.1 mm across-flat. A commercial Selco
2/08DR200-006 push-on knob is specified for that same 6.0 × 4.5 mm shaft and
uses a compression ring for retention. Our one-piece printed knob has no
unrequested spring, slit, insert, or set screw. Printer/material hole error is
handled by the bounded HIGH file or slicer calibration, not by redefining LOW.

The regenerated case mechanism remains **status ok, 104/104 assertions, 9 reported
interferences**. Its static knob proxy is exactly 17.5 × 17.5 × 19.0 mm
(4570.035563 mm³); the puck case envelope is round and clears the conservative case keycap
proxy by +0.655 mm at full throw. The product-level topper sweep, which uses the actual
17.5 mm inserted-key profile, reports +0.3008 mm for the puck.

## 29. Printable plate artifact (2026-08-22)

The case generator now exports `stl/agentpad13_v2_plate.stl` from the same
`fr4_plate()` solid used for `step/agentpad13_v2_plate.step`. This is the
home-printing file; the STEP remains available for CAD edits and the v5 fab
files remain the manufacturing source for an FR4 plate. No plate geometry
changed: the printed artifact is 84.4 × 100.0 × 1.6 mm with the same
switch, stabilizer, encoder, joystick, indicator and screw openings.

## 30. Base mating-plane wording correction (2026-08-22)

The generated base interface now names the mating plane correctly as the flat
tray bottom at z = −9.5, which is 2.0 mm below the separately frozen band
bottom at z = −7.5. The base geometry already consumed `C.Z_TRAY_BOT` and
was correct; only the generated description had retained the pre-v2.11 claim
that the two bottoms were coplanar.

## 31. TPU joystick socket fit returned to physical qualification (2026-08-22)

Section §28's Ø6.350 puck is also retired: shrinking the puck to approximately
the nub diameter was not an owner requirement. The last owner-final puck
upper envelope is commit `74a4b072d7e42f8f80b459aa600b6a8d18652808`
(`Toppers v2: ... one-piece TPU puck`), whose source, params and exported STL
agree on a round Ø9.4118579 mm exact / Ø9.412 mm published envelope, top
z=19.6, R0.6 rim, 0.55 mm rim land, 0.35/0.55 mm cup and four raised 0.8 mm
X dashes. Those upper and lateral features are restored exactly.

The same historical part's underside cone/restrictor and Ø5.2 hollow bore are
not restored. The owner's later directives explicitly removed the integrated
restrictor and required the bottom to be solid except for the shaft slot. The
live puck therefore keeps the flat, non-restricting bottom at z=14.4 and the
4.00 mm blind rectangular socket. Any throw limit belongs to the separate
cover/insert, not the topper.

The joystick socket dimensions in §28 are no longer production-approved. A
printed `clearance_low` at 2.10 × 1.30 mm spins freely on the measured
1.70 × 1.00 mm shaft; the 2.30 × 1.50 mm `clearance_high` was not physically
qualified. The earlier 1.95 × 1.25 mm print did not seat. The prior rigid
anti-rotation gate proved only that the shaft could not turn a full 90 degrees
inside the nominal rectangle, not that flexible printed walls would retain it
without angular play.

`toppers/stl/stick_socket_fit_coupon_TPU95A_0p4.stl` now brackets that known
transition in 0.05 mm increments using eight numbered, full-factorial cells.
The coupon is an internal process-calibration artifact, not a public family of
topper variants. `toppers/TPU-SOCKET-FIT.md` records the cell map, print
contract and required observations. Production LOW/HIGH remain null in
`toppers/params/stick_topper_v2_fit_selection.json`, and the topper generator
blocks production STL export until physical coupon results select both cells.

## 32. Two-type joystick topper lineup (2026-08-22)

The compact direct-on-shaft family remains exactly two exterior choices: the
existing Ø6.189 seven-dot nub and restored round Ø9.412 puck. Neither exterior
is reopened by the fit correction; both consume the same physically qualified
TPU socket pair after the coupon is graded.

`toppers/restricted_thumb_topper_v1.py` introduces a separate Type 2 source for
one larger conventional round topper used only with the separate YA13
retaining restrictor cap. It is not a nub revision and does not replace or
rename either compact part. The approved body is Ø12.0 with a Ø4.45 straight
neck, z=14.4 mouth, z=14.92 shoulder start, z=15.02 full-body start and z=19.6
top. It is a plain shallow round cup with no lip, ovalization, decoration,
integrated restrictor or plate-coverage objective.

The body gate imports the live cap authority and checks the actual solids
through the 15.5° verified hard maximum at 15° azimuth increments. It records
zero overlap, 0.292 mm minimum cap clearance and 0.331 mm minimum clearance to
the conservative adjacent-key plane. A clearly named no-socket body-reference
STL and render are available for inspection. Production LOW/HIGH socket STLs
remain blocked until the shared eight-cell TPU coupon is physically graded.

## 33. Tray insert cavity changed to Voron M3x4x5 (2026-08-24)

The tray now specifies the standard Voron-style M3x4x5 heat-set insert: M3
internal thread, 4 mm insert length and nominal 5 mm outer diameter. The four
tray cavities widen from Ø4.2 to **Ø4.7 mm**. Their blind depth remains 5.7 mm,
leaving 1.7 mm of relief below the 4 mm insert for the existing M3x8 screw.
No screw clearance hole, pass hole, boss centre, external case dimension or
other mating interface changed.

The regenerated tray loses 79.6865 mm³, exactly the volume of four 5.7 mm-deep
cylinders widened from Ø4.2 to Ø4.7. The assembly gate remains **status ok,
104/104 assertions passed**. The new limiting calculated wall at the notched
(3.7, 3.7) boss is **1.4012 mm**. This CAD result still requires the usual
first-article heat-set test on the target printer and PETG.

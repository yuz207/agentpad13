# agentpad13 case v2.5

Case for the **v5 board** (84.2 × 100 mm octagon). Architecture:
**FR4 plate-as-deck + printed tray** — a screwed-down 1.6 mm FR4 plate on top
(face + switch skeleton), the PCB seated in the middle on locating posts
(never screwed), and a printed tray on the bottom carrying the heat-set
inserts and feet. A printed **band** forms the visible side wall; the plate
drops into a ledge inside the band and sits flush with its rim. Four M3
screws clamp plate + band + tray as one stack. Outer size 89.6 × 105.4 mm,
~12.5 mm tall plus feet.

What changed versus the earlier v2 file set: the plate is **1.6 mm** and
carries the **v5 joystick opening** (the YA13 tilt stick's asymmetric
rounded-rect instead of the old circle), the band seats that 1.6 mm plate
(`band_1.6mm`), the tray matches the v5 board's chamfered corner and joystick
underside (`tray_v5`), and the kit adds **printable toppers** (encoder knobs +
stick caps) and an **optional gasket**.

For the full build path — what to order where, firmware, bring-up — start at
[`HOW-TO-ORDER.md`](../../HOW-TO-ORDER.md) in the repo root.

## Files

### Printed parts (`stl/`, matching STEP in `step/`)

| File | What it is | How to make |
|------|-----------|-------------|
| `agentpad13_v2_band_1.6mm` | Top case — the visible side band, seated for the 1.6 mm plate | Frosted/clear resin (SLA) for the default look, or FDM in a translucent filament |
| `agentpad13_v2_tray_v5` | Bottom case — locating posts, insert bosses, feet; v5-board fit | FDM PETG **always** (resin cannot take heat-set inserts) |

`step/agentpad13_v2_plate.step` is the plate's 3D model — reference geometry
for the FR4 order, and the file you print if you take the plate's home path.

### Plate (`fab/`) — pick ONE variant

All three variants are the same 1.6 mm switch plate/deck; they differ only in
the capacitive-touch key provision at lower-left:

| Variant | Order this zip | What it is |
|---------|----------------|-----------|
| `agentpad13_v2_plate_v5` | `plate_v5_gerbers.zip` | **Exposed touch disc** — Ø12 bare disc over a Ø14 electrode, via-stitched to an underside landing pad. Order **ENIG** finish so the disc is flat gold. |
| `agentpad13_v2_plate_tented_ring_v5` | `plate_v5_ring_gerbers.zip` | **Tented disc + silk ring** — the electrode stays under soldermask, a silkscreen ring marks the key. Cheapest clean face; any finish. |
| `agentpad13_v2_plate_blank_v5` | `plate_v5_blank_gerbers.zip` | **Blank** — no touch-key provision at all. If the fab queries the low copper, answer that it is a mechanical switch plate and to proceed. |

The `.kicad_pcb` files are the sources behind the zips;
`agentpad13_v2_plate_v5.dxf` is an alternative outline input, and
`agentpad13_v2_plate_v5_top.png` / `.svg` are previews.

**Order settings** (any PCB fab, as a bare board): 2 layers · **1.6 mm
thickness** (do not leave a different default!) · single pieces, 1 design ·
soldermask color = the face color of your build. Remarks field: *"Mechanical
switch plate — minimal copper by design; please proceed despite low copper
density."*

**Home path:** print `step/agentpad13_v2_plate.step` (modern slicers open STEP
directly) in PETG or resin, 100% infill. Trade-offs: no copper — the touch key
then senses through-panel (finger on plastic, conductive foam pillar
underneath; tune with the sensitivity-cap pad on the PCB) — and a slightly
softer switch-clip feel.

**Touch-key hardware** (disc variants): one conductive-foam pillar
(EMI-gasket type), ≈Ø8–10 mm × 5 mm uncompressed, placed on the board's bare
center touch pad so it compresses against the plate's underside landing pad.

### Toppers (`toppers/`) — printed caps for the encoder and stick

Renders of every style are in `toppers/renders/`.

- **Encoder knobs** (`knob_*`): 3 styles — `dome_cup`, `knurled_cup`,
  `ribbed_skirt` — each in a 3-bore fit ladder for the EC11 D-shaft:
  **Ø5.9 / 6.0 / 6.1**. Print the 6.0 first; size up if tight, down if loose.
- **Stick caps** (`stick_cap_*`): 4 profiles — **`taper` (default)**, `dome`,
  `dish`, `knurl` — each in a 3-rung socket-fit ladder: **nom / p05 (+0.05) /
  p10 (+0.10)**. Start with nom. The taper profile is the one that clears the
  adjacent 2U keycap at full stick tilt; the dome/dish/knurl alternates can
  graze that keycap at high tilt angles (the dome from roughly 16° of tilt).
- `params/*.json` — the dimensional fit-reference data (socket and bore sizes
  per ladder rung) for both topper families.

### Gasket (`gasket/`) — optional

A user-cut 0.5 mm PORON foam kit that converts the band ledge's 0.3 mm air
gap over the PCB rim into a gentle preload. Entirely optional and reversible —
the bare ledge already works. Print `gasket_template.pdf` **at 100% scale**
(it is verified 1:1 — check the 50 mm scale bar), cut the 10 segments with a
hobby knife, and stick them to the band ledge underside;
`gasket_segments.dxf` is the same shape for craft cutters (Cricut/laser).
Placement, material spec, and the compression math: `gasket/README.md`.

## Print settings

- **Band (resin path, default):** clear/transparent resin, standard finish —
  **do not order polishing** (unpolished prints frosted, which is the desired
  LED-diffusing look). Note resin prints are translucent rather than
  water-clear and can yellow with UV — keep out of prolonged direct sun or
  apply a UV-blocking matte clear coat. An opaque band blocks the underglow.
- **Band (FDM path):** a translucent filament (layered glow), printed upright
  (bottom face on the bed), 0.4 mm nozzle, 0.12–0.16 mm layers, elephant-foot
  compensation ON, no supports (all internal overhangs are short
  self-supporting bridges).
- **Tray:** PETG, printed upright, 0.16–0.20 mm layers. Check the slicer
  preview for thin walls before the first print. The plate's screw holes are
  close-fit (Ø3.2 over M3), which keeps the deck reveal even but asks the
  tray print to hold its 4-boss pattern to roughly ±0.1 mm — calibrate your
  slicer's XY scale if you haven't. If the screws fight at assembly, opening
  the FR4 plate holes to Ø3.3–3.4 with a pin vise is a clean fallback.
- **Toppers:** any rigid filament or resin; small parts, print a few ladder
  rungs in one plate and keep the one that fits.
- The plate drops into the band with 0.3 mm side clearance (the visible
  reveal line around the deck) — sized so a typical FDM band still swallows
  a worst-case fab plate. A resin band has clearance to spare.

## Hardware

- 4 × **M3×8 button-head screws** (ISO 7380). Heads sit proud on the deck by
  design.
- 4 × **M3 heat-set inserts**, Ø4.2 pilot, ~5.7 mm length — tray only. Set
  from the boss top face at ~245 °C; melt most of the way in, then press flat.
- 4 × clear self-adhesive bumpon feet, Ø7.9 × 2.2 mm (e.g. 3M SJ61A1), on
  the tray's corner-boss bottom faces.
- 1 × conductive-foam pillar (touch key, disc plate variants — see above).
- Optional: 0.5 mm adhesive-backed PORON sheet for the gasket kit.

## Assembly order

1. Set the four heat-set inserts into the tray bosses.
2. Drop the PCB onto the tray's locating posts — it sits flat on the support
   bosses, no screws.
3. Place the conductive-foam pillar on the PCB's touch pad; if using the
   gasket, its segments go on the band's ledge underside first.
4. Lower the band over the bosses until it seats.
5. Drop the plate into the band's ledge, flush with the rim, and drive the
   four M3×8 screws into the inserts.
6. Snap the switches into the plate cutouts (support the plate from behind on
   the first insertions), add keycaps, press on an encoder knob and stick cap.
7. USB-C plugs through the aperture in the side wall.

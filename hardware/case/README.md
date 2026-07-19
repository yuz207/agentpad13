# agentpad13 case v2

Case for the **Rev A v4 board** (84.2 × 100 mm octagon). Architecture:
**FR4 plate-as-deck + printed tray** — a screwed-down 1.5 mm FR4 plate on top
(face + switch skeleton), the PCB floating in the middle on three locating
pins (never screwed), and a printed tray on the bottom carrying the heat-set
inserts and feet. A printed **band** forms the visible side wall; the plate
drops into a ledge inside the band and sits flush with its rim. Four M3
screws clamp plate + band + tray as one stack. Outer size 89.6 × 105.4 mm,
~12.5 mm tall plus feet.

## Files

### Printed parts (`stl/`, matching STEP in `step/`)

| File | What it is | How to make |
|------|-----------|-------------|
| `agentpad13_v2_band` | Top case — the visible side band | Frosted/clear resin (SLA) for the default look, or FDM PETG |
| `agentpad13_v2_tray` | Bottom case — locating pins, insert bosses, feet | FDM PETG **always** (resin cannot take heat-set inserts) |

### Ordered FR4 parts (`fab/`)

| File | What it is |
|------|-----------|
| `agentpad13_v2_plate.kicad_pcb` | The plate/deck — 1.5 mm FR4 switch plate, blank (no copper), matte black soldermask both sides. `agentpad13_v2_plate.dxf` is an alternative input. `step/agentpad13_v2_plate.step` is the 3D model. |
| `agentpad13_v2_coupon_panel.kicad_pcb` | FR4 test panel — switch cutouts + 2U stabilizer slots to verify switch/stab fit and the router's corner radius before ordering the full plate |
| `agentpad13_v2_touch_chip.kicad_pcb` | 20 × 20 mm FR4 chip used with the touch jig to test the capacitive-touch key through the plate |

Order all three in one cart at any PCB fab. A standard 2-layer service is
fine; thickness 1.5 mm as set in the plate file. The plate carries no
copper — if the fab queries "no copper on this board?", answer that it is a
switch plate and to proceed.

### Fit-check coupons (`stl/`, `step/`) — print these first

Small test pieces that verify the critical fits before you commit to the
full parts and the plate order:

| File | Verifies |
|------|----------|
| `coupon_corner_tray` + `coupon_corner_band` + `coupon_corner_plate_standin` | One full corner of the stack — screw joint, insert boss, flush deck seating (the plate stand-in is printable so no FR4 is needed for this check) |
| `coupon_insert_ladder` | Heat-set insert pilot-bore sizing in your PETG |
| `coupon_usb_wall_chip` | USB-C wall aperture against your actual cable |
| `coupon_touch_jig` | Holds the FR4 touch chip at exact deck height (3.5 mm) over the board's touch pad, to confirm capacitive-touch sensing through the plate |

## Print settings

- **Band (FDM path):** PETG, printed upright (bottom face on the bed),
  0.4 mm nozzle, 0.12–0.16 mm layers, elephant-foot compensation ON, no
  supports (all internal overhangs are short self-supporting bridges).
- **Band (resin path):** frosted/clear SLA is the intended default look —
  the frosted band is the diffuser for the edge underglow LEDs. Note resin
  prints are translucent rather than water-clear and can yellow with UV
  exposure. An opaque FDM band will block the underglow.
- **Tray:** PETG, printed upright, 0.16–0.20 mm layers. Check the slicer
  preview for thin walls before the first print. The plate's screw holes are
  close-fit (Ø3.2 over M3), which keeps the deck reveal even but asks the
  tray print to hold its 4-boss pattern to roughly ±0.1 mm — calibrate your
  slicer's XY scale if you haven't. If the screws fight at assembly, opening
  the FR4 plate holes to Ø3.3–3.4 with a pin vise is a clean fallback.
- The plate drops into the band with 0.3 mm side clearance (the visible
  reveal line around the deck) — sized so a typical FDM band still swallows
  a worst-case fab plate. A resin band has clearance to spare.

## Hardware

- 4 × **M3×8 button-head screws** (ISO 7380). Heads sit proud on the deck by
  design.
- 4 × **M3 heat-set inserts**, Ø4.2 pilot, ~5.7 mm length (e.g. CNC Kitchen
  standard M3) — tray only. Set from the boss top face at ~245 °C; melt most
  of the way in, then press flat.
- 4 × clear self-adhesive bumpon feet, Ø7.9 × 2.2 mm (e.g. 3M SJ61A1), on
  the tray's corner-boss bottom faces.

## Assembly order

1. Set the four heat-set inserts into the tray bosses.
2. Drop the PCB onto the tray's locating pins — it sits flat on the support
   bosses, no screws.
3. Lower the band over the bosses until it seats.
4. Clip the switches into the plate cutouts, then lower plate + switches
   together — switch pins into the hot-swap sockets, plate into the band's
   ledge, flush with the rim.
5. Drive the four M3×8 screws through the plate corners into the inserts.
6. USB-C plugs through the aperture in the side wall.

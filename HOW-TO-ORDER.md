# HOW TO ORDER — agentpad13 v5

Every part of this device has a fabrication path, and every part except one also has a home path.
The only thing you cannot make at home is the assembled PCB. Pick a build tier, then follow the
cards below — every orderable or printable part of the build appears in exactly one card.

## Build tiers

| Tier | You order | You make at home | Character |
|---|---|---|---|
| **Minimum spend** (~$35–45 + parts) | Assembled PCB only | Plate, band, tray, toppers, gasket | Fully working unit, printed face, touch works through-panel |
| **Standard** | + FR4 plate (tented-ring) | Band, tray, toppers, gasket | Rigid FR4 deck, clean black face |
| **Showcase** | + ENIG plate (gold disc) + SLA frosted band | Tray, toppers, gasket | The full glow build |

Parts shopping list (all tiers): 13× MX-compatible switches (hot-swap, no soldering), keycaps
(12×1U + 1×2U), EC11 encoder + knob hardware if not printing a topper, M3×8 button-head screws (4),
M3 heat-set inserts Ø4.2 pilot (4), conductive foam (touch pillar, ~Ø8–10×5 mm), PORON/EVA sheet
1–2 mm (optional gasket), rubber feet, USB-C cable.

---

## Card 1 — the assembled PCB (mandatory; PCBWay or any turnkey fab)

**Choose your SKU** — want the case edges to glow? → **translucent** (edge LEDs populated).
Opaque top / no underglow → **opaque** (same bare board, 20 fewer parts).

**Files** (`hardware/pcb/`):
- PCB quote: upload **`gerbers.zip`**
- Assembly: upload **`assembly/bom_<sku>.csv`** + **`assembly/cpl_<sku>.csv`**
  (or hand the fab the matching all-in-one `fabpack_<sku>.zip`)

**Form settings:** 2 layers · 84.2 × 100 mm · 1.6 mm FR-4 · qty 5 (promo tier) · single pieces,
1 design · mask color your choice (green cheapest) · finish HASL lead-free (or ENIG) ·
assembly: turnkey, single side (bottom SMD; the joystick is a fab-placed through-hole part).

**Paste into the remarks/notes field:**
> Please plug/fill the via-in-pad locations (two are on LED pads). Please confirm the 0.2 mm via
> drill is standard tier. Board has intentional reverse-mount LED apertures (through-board cutouts).

**What happens:** file review (~1 business day) → parts are priced and added to the quote →
engineer emails any questions → you pay only after review → boards arrive with everything soldered
except the hand-solder afterlist (`hardware/pcb/assembly/hand_solder_afterlist.csv` — the encoder,
plus optional parts you chose to omit).

## Card 2 — the plate (deck + switch plate)

**Fab path** (any PCB fab, as a bare board): pick ONE variant from `hardware/case/fab/` —
the choice is mostly a COST decision, because one of the three requires the ENIG finish upcharge:

| zip | touch pad | what you see | finish required | who it's for |
|---|---|---|---|---|
| `plate_v5_gerbers.zip` | copper electrode, Ø12 mask opening = exposed gold disc (+ bottom landing pad for the foam pillar, 2 vias) | the gold circle itself | **ENIG required** (that's what makes it gold — the upcharge variant) | the premium default |
| `plate_v5_ring_gerbers.zip` | same electrode, fully tented under the soldermask — senses through the mask at ~90% signal | a Ø16 white silkscreen ring | **any finish — HASL-LF fine** (cheapest) | the budget build |
| `plate_v5_blank_gerbers.zip` | no copper at all — plain FR4 skeleton | none | any | skipping the touch feature (it degrades to through-air sensing at best; treat the touch key as absent) |

Settings: 2 layers · **1.6 mm** (do not leave a different default!) · single pieces, 1 design ·
mask color = the face color of your build. Remarks: *"Mechanical switch plate — minimal copper by
design; please proceed despite low copper density."*

**Home path:** print `hardware/case/step/agentpad13_v2_plate.step` (modern slicers open STEP
directly) in PETG or resin, 100% infill. Trade-offs: no copper (the touch key then senses
through-panel — finger on plastic, conductive foam pillar underneath; tune with the sensitivity-cap
pad on the PCB), and slightly softer switch-clip feel.

## Card 3 — the band (the case's translucent middle)

**Fab path:** upload `hardware/case/stl/agentpad13_v2_band_1.6mm.stl` to any SLA resin service
(PCBWay 3D-print works): **clear/transparent resin, standard finish — do NOT order polishing**
(unpolished prints frosted, which is the desired LED-diffusing look). Keep out of prolonged direct
sun or apply a UV-blocking matte clear coat.

**Home path:** same STL — home resin (frosted look) or FDM in a translucent filament
(layered glow; print upright per `hardware/case/README.md` guidance).

## Card 4 — printed at home, always

- **Tray**: `hardware/case/stl/agentpad13_v2_tray_v5.stl` — PETG, upright, 0.16–0.20 mm layers.
- **Toppers**: `hardware/case/toppers/stl/` — pick ONE encoder knob (3 styles × 3 bore fits:
  5.9/6.0/6.1 — print the 6.0 first, size up/down if tight/loose) and ONE stick cap (4 styles ×
  3 socket fits: nom/p05/p10 — start nom). Renders in `hardware/case/toppers/renders/` show the
  styles.
- **Gasket (optional)**: if the assembled stack shows wiggle, cut a PORON/EVA ring using
  `hardware/case/gasket/gasket_template.pdf` — **print at 100% scale** (it is verified 1:1),
  glue-stick it to the sheet, cut with a hobby knife. `gasket_segments.dxf` is the same shape for
  cutting machines (Cricut/laser). See `hardware/case/gasket/README.md` for placement.

## Card 5 — assembly order (when everything arrives)

1. Heat-set the four inserts into the tray posts (~245 °C).
2. Flash firmware over USB (`firmware/prebuilt/*.uf2` — hold BOOTSEL, drag the file on).
3. First-boot config: see `firmware/POLARITY-NOTE.md` — joystick axis inversion + calibration is a
   one-time config edit after you feel the stick.
4. Hand-solder the afterlist (encoder last: seat it flush).
5. Place the conductive foam pillar on the PCB's touch pad; gasket (if using) on the tray ledge.
6. Stack: tray → PCB (seats on posts, no screws) → band → plate; drive the four M3 screws.
7. Snap in switches (support the plate from behind on first insertions), cap everything, done.

Bring-up sanity: every key types, encoder scrolls and clicks, stick moves the pointer in the right
directions (if inverted, that's the POLARITY-NOTE config), touch key responds (add/remove the
sensitivity cap if too numb/twitchy), LEDs animate.

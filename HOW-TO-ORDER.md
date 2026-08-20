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
**0.5 mm** (optional gasket — buy 0.5 mm, not thicker: the kit is sized for ~40 % compression into
the band's 0.3 mm ledge gap, and 1–2 mm stock will not compress into that gap at all), rubber feet,
USB-C cable.

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

Settings: 2 layers · **84.4 × 100.0 mm** (all three variants; deliberately trimmed to land inside
the ≤100 mm promo tier — if the fab's form quotes you a larger size, re-check the upload) ·
**1.6 mm** (do not leave a different default!) · single pieces, 1 design ·
mask color = the face color of your build. Remarks: *"Mechanical switch plate — minimal copper by
design; please proceed despite low copper density."*

**⚠️ Tell the fab where the product number goes — or it lands on the face you look at.**
PCBWay prints a small product number on every board. Their published rule is component-driven:
*"The position where the Product No. is added is not fixed, we will try to put it under the IC so
that the number will be hidden when soldering."* This plate is a bare decorative panel with **no
components at all**, so that heuristic has nothing to aim at — and on our own v5 order the number
came back printed on the **top face, the visible deck**. Two things to do on the order form:

- Under **Customized Services**, set **`Remove product No.` = `Specify a location`**. That option
  is **free**. (`Yes (extra +$1.50)` deletes the number entirely — considered and deliberately
  **not** used: the number is harmless on a face nobody ever sees.)
- In the **"Other special request"** remarks box, say it in plain words:
  > This is a bare decorative panel with **no components**. Its **top face (+Z, the F.Silkscreen
  > side) is the visible deck of the finished product**. Please place the Product No. on the
  > **bottom face — the B.Silkscreen side, which faces the tray and is hidden once the case is
  > assembled**. Please do not place it on the top / F.Silkscreen face.

**The remarks sentence is the load-bearing part.** PCBWay also accept a `WayWayWay` marker placed
in the silkscreen layer to pin the exact spot, and note *"It is important to select the option,
otherwise, we may not notice that you need to specify the location."* **The plate gerbers here
already carry that token on B.Silkscreen** — you do not need to add it. But their instruction says
*"the silkscreen layer"* — singular, with no top/bottom language anywhere — so **a `WayWayWay`
token on B.Silkscreen reliably yielding bottom placement is a reasonable inference, not a
documented guarantee.** Treat the token as belt-and-braces; the plain-English remark is what you
actually rely on.

**Home path:** print `hardware/case/step/agentpad13_v2_plate.step` (modern slicers open STEP
directly) in PETG or resin, 100% infill. Trade-offs: no copper (the touch key then senses
through-panel — finger on plastic, conductive foam pillar underneath; tune with the sensitivity-cap
pad on the PCB), and slightly softer switch-clip feel.

## Card 3 — the band (the case's translucent middle)

**Fab path:** upload `hardware/case/stl/agentpad13_v2_band_1.6mm_w5.4.stl` to any SLA resin service
(PCBWay 3D-print works): **clear/transparent resin, standard finish — do NOT order polishing**
(unpolished prints frosted, which is the desired LED-diffusing look). Keep out of prolonged direct
sun or apply a UV-blocking matte clear coat.

**Which file?** The `_w{N}` suffix is the **sidewall thickness in mm** — the one aesthetic knob on
this part (thicker wall = wider frosted diffuser ring around the plate, and a stronger corner).
**`_w5.4` is the default and the recommended file.** `_w3.0` (slimmer) and `_w7.4` (chunkiest) are
equally valid, equally gated builds — every internal and mating dimension is identical across all
three, including the USB port, which keeps a 2.10 mm plug-shell bridge at any wall thanks to a
relief pocket at the port. **Pick exactly one; do not print
`agentpad13_v2_band_1.6mm.stl`-without-a-suffix if you find it in an old copy** — that is the
retired 2.4 mm-wall geometry whose corners a fab review flagged as too thin.

| file | sidewall | outer size | corner minimum |
|---|---|---|---|
| `…_w3.0.stl` | 3.0 mm | 90.8 × 106.6 mm | 1.59 mm |
| **`…_w5.4.stl` (default)** | **5.4 mm** | **95.6 × 111.4 mm** | **4.40 mm** |
| `…_w7.4.stl` | 7.4 mm | 99.6 × 115.4 mm | 6.40 mm |

**Plate fit — the pocket was re-cut, and it is deliberately tight.** All three bands changed. The
pocket the plate drops into had been sized around a 100.2 mm plate that was never made (the plate
was trimmed to 100.0 mm early on, but only in its own fab generator), so the plate floated
**0.8 mm** along its long axis and showed the whole gap at one end. The pocket is now
**84.6 × 100.2 mm** around the 84.4 × 100.0 mm plate — an even **0.1 mm** reveal all the way round.

There is one band; there is no separate "loose" file. 0.1 mm/side is tight, and at a worst-case
stack (plate routing tolerance plus resin or FDM shrink) **the plate may need a light sand to drop
in.** That is the intended trade: slightly too tight is a minute with sandpaper, too loose cannot be
fixed at all. If yours binds, sand the pocket walls lightly — a few passes with fine paper on the
four inner faces of the recess. (This repo ships the finished STL/STEP, not the parametric case
source, so sanding is the fix here rather than re-exporting at a looser fit.) **A band printed or
ordered before this change is the old loose pocket — still usable, just with the bigger gap.**

**Home path:** same STL — home resin (frosted look) or FDM in a translucent filament
(layered glow; print upright per `hardware/case/README.md` guidance).

## Card 3b — the tray bases (optional, printed at home)

**Tray only, or tray + an insertable base — both are complete products.** The three bases in
`hardware/case/bases/stl/` clip into four Ø6 pockets in the tray's underside: `mat` (full-footprint
TPU sheet, grip), `wedge` (same outline, 6.5° back-raised typing angle) and `pedestal` (Ø70 × 20 mm
circular plinth).

**Print the fit gauge first** — `base_fit_gauge.stl` has all four peg diameters side by side, marked
by a count of raised dots. Keep the rung that holds in a tray pocket, then print the matching
`..._peg_5pN.stl`. Ø5.8 suits most rigid filament; TPU wants Ø5.9.

**The pedestal must be ballasted**: shell ~67 g, physics wants ≥136 g, so load ≥69 g of steel into
its underside cavity — or fill it (~202 g). The other two need nothing.

**Feet are your business**: every underside is flat, and all stated heights exclude feet.

All three print desk-face-down, no support. `bases/INTERFACE.md` is the spec if you would rather
design your own.

## Card 4 — printed at home, always

- **Tray**: `hardware/case/stl/agentpad13_v2_tray_v5.stl` — PETG, upright, 0.16–0.20 mm layers.
- **Keycaps (optional — or buy MX caps)**: `hardware/case/keycaps/` — one universal cap that fits
  Kailh Box / Cherry MX / Gateron KS-9. Pick a top (plateau or dish) and a size (`_17p5` primary,
  no-suffix = 18.0 mm), then print 12 × 1U + one 2U (`_stab` if you fitted stabilizers). Print
  stem-down, no supports. **Material is a requirement, not a preference: use a tough / ABS-like
  resin (elongation at break ≳ 8%) or a rigid filament.** The stem socket grips via 0.07 mm crush
  ribs that must *yield*; in a brittle standard resin they shatter and leave debris in the socket.
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
2. Flash firmware over USB (`firmware/prebuilt/agentpad13.uf2` — hold BOOTSEL, drag the file on).
   - **First power-on: calibrate the joystick — see `firmware/BRING-UP.md`.** Hold **SW14** (the same button in the back) for about a second and follow the 13 key LEDs: white armed, blue bar while it finds the resting position, amber-to-green bar while you roll the stick around its outside edge, green flash when stored. About 15 seconds, and the board remembers it through unplugging and reflashing. **No host software, no daemon, no CLI, no second firmware** — a USB cable is the only tool.
3. First-boot config: see `firmware/POLARITY-NOTE.md` — if an axis reads *backwards* (which way round
   it is, not how far it travels) that is still a one-time config edit after you feel the stick. The
   travel range itself is what step 2's on-board calibration measures and stores.
4. Hand-solder the afterlist (encoder last: seat it flush).
5. Place the conductive foam pillar on the PCB's touch pad; gasket (if using) on the tray ledge.
6. Stack: tray → PCB (seats on posts, no screws) → band → plate; drive the four M3 screws.
7. Snap in switches (support the plate from behind on first insertions), cap everything, done.

Bring-up sanity: every key types, encoder scrolls and clicks, stick moves the pointer in the right
directions (if inverted, that's the POLARITY-NOTE config), touch key responds (add/remove the
sensitivity cap if too numb/twitchy), LEDs animate.

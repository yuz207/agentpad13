# HOW TO ORDER — agentpad13 v5

Every part of this device has a fabrication path, and every part except one also has a home path.
The only thing you cannot make at home is the assembled PCB. Pick a build tier, then follow the
cards below — every file in this bundle appears in exactly one card.

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

**Files** (`hardware/pcb/fabpack_out_v5_7/`):
- PCB quote: upload **`gerbers_v5_7.zip`**
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
except the hand-solder afterlist (`assembly/hand_solder_afterlist.csv` — the encoder, plus optional
parts you chose to omit).

## Card 2 — the plate (deck + switch plate)

**Fab path** (any PCB fab, as a bare board): pick ONE variant from `hardware/case/v2/fab/` —
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
otherwise, we may not notice that you need to specify the location."* **The plate gerbers in this
bundle now carry that token on B.Silkscreen** (added 2026-08-19 with the v2.12 encoder-opening
regeneration) — you do not need to add it. But their instruction says
*"the silkscreen layer"* — singular, with no top/bottom language anywhere — so **a `WayWayWay`
token on B.Silkscreen reliably yielding bottom placement is a reasonable inference, not a
documented guarantee.** Treat the token as belt-and-braces; the plain-English remark is what you
actually rely on.

**Home path:** print `hardware/case/v2/step/agentpad13_v2_plate.step` (modern slicers open STEP
directly) in PETG or resin, 100% infill. Trade-offs: no copper (the touch key then senses
through-panel — finger on plastic, conductive foam pillar underneath; tune with the sensitivity-cap
pad on the PCB), and slightly softer switch-clip feel.

## Card 3 — the band (the case's translucent middle)

**Fab path:** upload `hardware/case/v2/stl/agentpad13_v2_band_1.6mm_w5.4.stl` to any SLA resin
service (PCBWay 3D-print works): **clear/transparent resin, standard finish — do NOT order
polishing** (unpolished prints frosted, which is the desired LED-diffusing look). Keep out of
prolonged direct sun or apply a UV-blocking matte clear coat.

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

**Plate fit — re-cut 2026-08-19, and it is deliberately tight.** All three bands changed on this
date. The plate pocket had been sized around a 100.2 mm plate that never shipped (the fab trim to
100.0 mm lived only in the plate generator), so the plate floated **0.8 mm** along its long axis
and showed the whole gap at one end. The pocket is now **84.6 × 100.2 mm** around the
84.4 × 100.0 mm plate — a uniform **0.1 mm** reveal on the flats and at the corners.

There is **one** band; there is no "loose" file. 0.1 mm/side is genuinely tight, and at a worst-case
stack (fab routing up to +0.15 mm on the plate, plus resin or FDM shrink) **the plate may need a
light sand to drop in.** That is the intended trade: a pocket that is slightly too tight takes a
minute with sandpaper, while one that is too loose cannot be fixed at all. If yours binds, sand the
pocket walls lightly — or raise `PLATE_FIT` in `hardware/case/v2/agentpad13_case_v2.py` (a one-line
edit) and re-export, which reproduces the older loose pocket. **If you already have a band printed
or ordered before this date, it is the old loose pocket: still perfectly usable, just with the
larger gap.**

**Home path:** same STL — home resin (frosted look) or FDM in a translucent filament
(layered glow; print upright per `hardware/case/v2/CASE-V2-NOTES.md` guidance).

## Card 3b — the tray bases (optional, printed at home)

**The offering is: tray only, or tray + one insertable base.** The tray is complete on its own.
Three official bases clip into the same four Ø6 pockets in its underside, so you can print one,
print all three, or design your own against `hardware/case/v2/bases/INTERFACE.md`.

| variant | what it is | print it in | notes |
|---|---|---|---|
| `riser` | 91.6 × 107.4 mm flat sheet, **3.0 mm** | **TPU** for a grip base, **PETG/PLA** for a rigid stand — same file | lifts the pad slightly, no angle |
| `wedge` | same outline, **8° back-raised** | PETG/PLA | far edge 17.5 mm; the typing angle |
| `pedestal` | **Ø78 tilted drum** — the wedge cut to a circle | PETG/PLA, **100 % infill** | same 8° angle, circular look |

**The 8° angle is not arbitrary.** Mainstream mechanical keyboards sit around 7°, the comfortable
band across real boards is 4–8°, and high-profile customs land 6–8°. This deck is a low 13-key pad
rather than a full-height board, so it takes the top of that band to read as a typing angle at all.

**Print the fit gauge first.** `stl/base_fit_gauge.stl` carries all four peg diameters side by side
(Ø5.6 / 5.7 / 5.8 / 5.9), each marked by a count of raised dots. Push each peg into any tray pocket
and keep the rung that holds, then print the matching `..._peg_5pN.stl`. Ø5.8 is the usual answer in
rigid filament; TPU wants Ø5.9 because it compresses.

**⚠️ Print the `pedestal` SOLID — this one is structural, not a speed setting.** It is the only base
smaller than the footprint, so its own printed mass is what stops the pad tipping when you press a
far control. Solid it weighs ~59 g and clears both the 3 N design case and the 5 N abuse case. A
normal 3-wall / 20 % gyroid print is only ~37 g: it still clears the design case, but **not** the
abuse case. There is no ballast cavity to fall back on — the mass has to come from the plastic.
The `riser` and `wedge` span the whole footprint and need nothing at all.

**Feet are your business.** Every base underside is FLAT — no recesses, no bolt circle, no prescribed
part. Stick on whatever you like, wherever you like. Every height and stability figure EXCLUDES
feet, so anything you add is margin on top.

**All three print desk-face-down with no support.**

## Card 4 — printed at home, always

- **Tray**: `hardware/case/v2/stl/agentpad13_v2_tray_v5.stl` — PETG, upright, 0.16–0.20 mm layers.
- **Toppers**: `hardware/case/v2/toppers/stl/` — two picks, not one.
  - **ONE encoder knob** — 3 styles (`A` helical knurl / `B2` deep scoop / `C` cross-hatch,
    all Ø19) × 3 bore fits (`tight` 5.9 / `nom` 6.0 / `loose` 6.1). **Print `nom` first**,
    size up/down if it binds or spins.
  - **ONE stick topper** — these are two different parts, not two styles:
    the **`stick_nub_v2_C2`** dot nub (3 socket fits `nom`/`p05`/`p10` — start `nom`),
    or the **`stick_puck_v2_TPU`** puck (`sock_nom` ships; `sock_m05` is the tight spare).
    **The puck must be printed in TPU ~95A** — it relies on a soft integral stop; printing it
    rigid defeats the part. The nub prints in the same material as everything else.

  Renders in `toppers/renders/` show all of them. Print orientation: knobs `A`/`C` and the
  puck go **top-face-down**; knob `B2` and the nub go **bottom-down**. No supports needed.
- **Gasket (optional)**: if the assembled stack shows wiggle, cut a PORON/EVA ring using
  `hardware/case/v2/gasket/gasket_template.pdf` — **print at 100% scale** (it is verified 1:1),
  glue-stick it to the sheet, cut with a hobby knife. `gasket_segments.dxf` is the same shape for
  cutting machines (Cricut/laser). See `gasket/README.md` for placement.

## Card 5 — assembly order (when everything arrives)

1. Heat-set the four inserts into the tray posts (~245 °C).
2. Flash firmware over USB (`firmware/prebuilt/agentpad13.uf2` — hold BOOTSEL, drag the file on).
   - **First power-on: do the calibration in `firmware/BRING-UP.md`** — hold SW14 (the same back button) for about a second and the 13 key LEDs walk you through it; the board measures its own joystick and stores the result in its own memory. About 15 seconds, no host software, no second firmware, no reflash.
3. First-boot config: see `firmware/POLARITY-NOTE.md` — joystick axis *inversion* (which way round
   an axis reads) is still a one-time config edit after you feel the stick; the axis *range* is what
   Step 2's on-board calibration measures and stores.
4. Hand-solder the afterlist (encoder last: seat it flush).
5. Place the conductive foam pillar on the PCB's touch pad; gasket (if using) on the tray ledge.
6. Stack: tray → PCB (seats on posts, no screws) → band → plate; drive the four M3 screws.
7. Snap in switches (support the plate from behind on first insertions), cap everything, done.

Bring-up sanity: every key types, encoder scrolls and clicks, stick moves the pointer in the right
directions (if inverted, that's the POLARITY-NOTE config), touch key responds (add/remove the
sensitivity cap if too numb/twitchy), LEDs animate.

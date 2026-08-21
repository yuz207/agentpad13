# HOW TO ORDER — agentpad13 v5

**The configurator at <https://yuz207.github.io/agentpad13/configurator/site/> is the primary way
to build one** — pick your options and get an order sheet whose every line links to the file you
upload or print. **This file is its static form:** the same questions in the same order, on paper.

You order the assembled PCB, and optionally the FR4 plate. Everything else you print. Minimum spend
is roughly $35–45 plus parts — **every price here is an estimate and prices change.** What shipped
and why is [`RELEASE.md`](RELEASE.md).

## 1. LED band

**Do you want the case edges to glow?** **yes** → the **translucent** SKU (10 edge-underglow LEDs
populated, and you want a see-through band); **no** → the **opaque** SKU, same bare board, 20 fewer
parts. It picks the fabpack below and nothing else — the 13 per-key LEDs are on both.

## 2. Board — the one part you cannot make at home

Upload to PCBWay (or any turnkey fab), from `hardware/pcb/fabpack_out_v5_7/`: **`gerbers_v5_7.zip`**
for the PCB quote, **`assembly/bom_<sku>.csv`** + **`assembly/cpl_<sku>.csv`** for assembly
(`<sku>` = `translucent` or `opaque`) — or the all-in-one **`fabpack_<sku>.zip`**.

Form: 2 layers · 84.2 × 100 mm · 1.6 mm FR-4 · qty 5 · single pieces, 1 design · HASL lead-free ·
turnkey assembly, single side. Mask colour only shows through a translucent case; green is
cheapest. Remarks box:

> Please plug/fill the via-in-pad locations (two are on LED pads). Please confirm the 0.2 mm via
> drill is standard tier. Board has intentional reverse-mount LED apertures (through-board cutouts).

Boards arrive fully soldered except `assembly/hand_solder_afterlist.csv` — the encoder, plus
anything you omitted.

## 3. Plate — FR4 from a fab, or printed

**Printed:** print `hardware/case/v2/step/agentpad13_v2_plate.step` in PETG or resin at 100 % infill
and skip the rest of this card. No copper, so the touch key senses through the panel.

**FR4:** order ONE of these as a bare board, from `hardware/case/v2/fab/`.

- `plate_v5_gerbers.zip` — Ø12 mask opening, an exposed gold disc you touch. **ENIG (lead-free) is
  required**: that is bare copper under a finger, so not a lead-tin alloy, and HASL is not flat.
  The upcharge variant.
- **`plate_v5_ring_gerbers.zip` — the default.** Same electrode tented under the mask (~90 %
  signal) with a Ø16 silk ring. Any finish; HASL lead-free, and the cheapest.
- `plate_v5_blank_gerbers.zip` — no copper. Any finish; the touch key is absent.

Form: 2 layers · **84.4 × 100.0 mm** (deliberately inside the ≤100 mm promo tier) · **1.6 mm**, do
not leave a different default · mask colour = your build's face colour. Remarks: *"Mechanical switch
plate — minimal copper by design; please proceed despite low copper density."*

**⚠️ Tell the fab where the product number goes, or it lands on the face you look at.** PCBWay hide
it under an IC; this panel has none, so ours came back on the visible deck. Set **Customized
Services → `Remove product No.` = `Specify a location`** (free), and write in "Other special
request":

> This is a bare decorative panel with no components. Its top face (the F.Silkscreen side) is the
> visible deck of the finished product. Please place the Product No. on the bottom face — the
> B.Silkscreen side, which faces the tray and is hidden once the case is assembled.

The gerbers also carry PCBWay's `WayWayWay` marker on B.Silkscreen, but that remark is what you
actually rely on.

## 4. Band — the translucent middle

Pick **one** file from `hardware/case/v2/stl/`. The `_w` suffix is the sidewall in mm, the only
thing that differs — everything inside is identical, USB port included.
**`agentpad13_v2_band_1.6mm_w5.4.stl` is the default**, 95.6 × 111.4 mm outside.
`_w3.0` is 90.8 × 106.6 mm and `_w7.4` is 99.6 × 115.4 mm; both are equally valid.
Order it from any SLA resin service in
**clear resin, standard finish — do NOT order polishing** (unpolished prints frosted, which is the
LED-diffusing look), or print it yourself in resin or translucent FDM, upright. Keep it out of sun.

**⚠️ The plate pocket is deliberately tight** — 84.6 × 100.2 mm around the 84.4 × 100.0 mm plate, a
0.1 mm reveal all round, so at a worst-case tolerance stack **the plate may need a light sand to
drop in.** Sand the pocket walls, not the plate.

## 5. Tray — always printed

`hardware/case/v2/stl/agentpad13_v2_tray_v5.stl` — **PETG**, upright, 0.16–0.20 mm layers. PETG is
not a preference: the tray takes the heat-set inserts, and resin cannot.

## 6. Base — optional

**Tray only, or tray plus one base.** All three clip into the same four Ø6 pockets in the tray
underside and print desk-face-down without supports, from `hardware/case/v2/bases/stl/`.

- `riser` — 3.0 mm flat sheet, no angle. TPU for grip, PETG/PLA for a rigid stand; same file.
- `wedge` — same outline, 8° back-raised. That is the typing angle. PETG/PLA.
- `pedestal` — Ø78 tilted drum, the wedge cut to a circle. PETG/PLA, **100 % infill**.

**Print `base_fit_gauge.stl` first:** four peg diameters side by side (Ø5.6 / 5.7 / 5.8 / 5.9), each
marked by raised dots. Push each into a tray pocket, keep the rung that holds, print the matching
`base_<variant>_peg_5pN.stl`. Ø5.8 is the usual answer; TPU wants Ø5.9.

**⚠️ Print the `pedestal` SOLID — structural, not a speed setting.** It is the only base smaller
than the footprint, so its own printed mass is what stops the pad tipping when you press a far
control. Solid it clears the 5 N abuse case; a 20 % gyroid print does not, and there is no ballast
cavity to fall back on.

Every base underside is flat; feet are your business.

## 7. Caps and switches

13 MX-compatible hot-swap switches, no soldering: 12 × 1U + 1 × 2U. Buy keycaps, or print them from
`hardware/PCBWay_keycaps_boxfit_2026-07-24/` — pick one profile (`dish` or `plateau`) and one width
(standard, or the `_17p5` files at 17.5 mm), then print 12 × the `1u` file and 1 × the `2u`. Fitting
a 2U plate-mount stabilizer? Print `2u_stab` instead.

## 8. Toppers — two picks, not one

From `hardware/case/v2/toppers/stl/`; renders of all of them in `../toppers/renders/`.

- **ONE encoder knob** — `knob_v2_A` (helical knurl), `_B2` (deep scoop) or `_C` (cross hatch), all
  Ø19, each in three bores: `_bore_tight` 5.9 / `_bore_nom` 6.0 / `_bore_loose` 6.1. **Print `nom`
  first**, size up or down if it binds or spins.
- **ONE stick topper** — two different parts, not two styles. `stick_nub_v2_C2_sock_{nom,p05,p10}`
  is the dot nub; start at `nom`. `stick_puck_v2_TPU_sock_{nom,m05}` is the puck, and **it must be
  printed in TPU ~95A** — it works by a soft integral stop, so a rigid print is not the part.

## 9. Self-buy list

None of this is in the bundle, and every price is an estimate that changes.

- 13 × MX switches
- 1 × EC11 encoder — Alps 11.2 mm mounting-tab pattern, flatted D-shaft
- 1 × Ø6 D-shaft knob, if you are not printing one
- 1 × 2u plate-mount stabilizer, if you want one
- 4 × M3×8 ISO 7380 button-head screws
- 4 × M3 heat-set inserts — Ø4.2 pilot, 5.7 mm long
- 1 × conductive foam pillar — ≈Ø8–10 × 5 mm, sits on the TP5 pad
- 1 × 0.5 mm adhesive-backed PORON sheet, smallest sold — the optional gasket. **Buy 0.5 mm, not
  thicker:** it compresses into a 0.3 mm gap, which 1–2 mm stock will not do. Cut it against
  `hardware/case/v2/gasket/gasket_template.pdf` **at 100 % scale**; see that folder's `README.md`.
- rubber feet, and a USB-C cable

## 10. Print notes

The five the configurator prints on your sheet — the ones that change what you do:

- Band pocket is deliberately tight — light sand if needed.
- Print the gauge, keep the rung that holds.
- Riser in TPU = grip base, rigid = stand.
- Pedestal prints 100 % solid.
- Printed plate has no copper — touch behaves like the blank variant.

## 11. Assemble

1. Heat-set the four inserts into the tray posts (~245 °C).
2. Hand-solder the afterlist — encoder last, seated flush.
3. Foam pillar onto the PCB's TP5 pad; gasket, if you cut one, onto the band ledge.
4. Stack tray → PCB (it just sits on the posts, no screws) → band → plate; drive the four M3 screws.
5. Snap in the switches, supporting the plate from behind on the first few, and cap everything.

## Firmware

Flash `firmware/prebuilt/agentpad13.uf2` — hold BOOTSEL while plugging in and the board mounts as a
drive:

```sh
dd if=firmware/prebuilt/agentpad13.uf2 of=/Volumes/RPI-RP2/fw.uf2 bs=1m
```

**Then calibrate the joystick, once, ever:** hold SW14 — the button in the back — for about a second
and follow the 13 key LEDs. ~15 seconds, no host software and no reflash; the board measures its own
stick and remembers it. Full procedure: [`firmware/BRING-UP.md`](firmware/BRING-UP.md). If an axis
reads backwards that is polarity rather than calibration, and a one-line config edit:
[`firmware/POLARITY-NOTE.md`](firmware/POLARITY-NOTE.md).

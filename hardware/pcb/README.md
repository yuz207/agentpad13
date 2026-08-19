# agentpad13 — PCB (v5, complete)

Finished, fabrication-ready 2-layer RP2040 macropad PCB. Designed in **KiCad 9**.

- **Outline:** 84.2 × 100 mm octagon (chamfered), 1.6 mm FR-4, 2 layers.
- **DRC:** clean — **0 violations, 0 unconnected** at a 0.152 mm / 6-mil standard
  fab tier (min via drill 0.20 mm).
- **Function:** 13 hot-swap keys (12×1U + 1×2U), EC11 encoder + push, analog
  2-axis tilt joystick (YTL YA13), TTP223 capacitive touch key, and a 24-LED
  SK6812 chain (14 reverse-mount top LEDs incl. 1 layer indicator + 10
  side/underglow LEDs) level-shifted for a 5 V VBUS rail. All SMD reflow parts
  are on the back (B.Cu); the joystick is a machine-placed through-hole part
  on the front.
- **v5 vs Rev A:** the encoder moved so its shaft centers on the case plate's
  encoder opening, the USB-C receptacle was flipped 180° so its mouth faces the
  case wall aperture, and the hand-solder PSP-slider joystick was replaced by
  the fab-placed YA13 tilt gimbal (LCSC C37323742) with datasheet-verified
  wiring — see `renders/js1_detail.png` and `../../firmware/POLARITY-NOTE.md`
  for the one-time axis/calibration config note.

## Board revision — v5_7 (current)

The published board is **v5_7**. It differs from **v5_6**, the revision the first
units were built from, by **two footprint rotations and nothing else**: the
bottom-edge underglow LEDs **LED20** and **LED21** were rotated 180° so they fire
*into* the board instead of off the edge. Same positions, same layer, same nets, no
part changes — both BOMs and the opaque SKU's pick-and-place file are byte-identical
to v5_6, and the translucent CPL differs in exactly those two rows (`Rot 0 → 180`).

Why they were wrong: the board generator applies each underglow LED's rotation and
*then* flips the part to the back copper, and that flip negates orientation. The two
pairs aimed along Y reversed; the left and right rails, aimed along X, survived. The
result was six of the ten side LEDs firing inward and four firing outward.

**`LED15`/`LED16`, beside the USB connector, still fire outward — that is
deliberate.** They wash the surface behind the pad and are kept that way by choice.
The shipping board is 8 inward / 2 outward.

If you have a board built from v5_6, nothing is broken and nothing needs reworking:
four of the ten underglow LEDs simply throw their light off the edge rather than
under the case.

## Files

```
agentpad13/                 the KiCad 9 project
  agentpad13.kicad_pcb      board
  agentpad13.kicad_sch      schematic
  agentpad13.kicad_pro      project
  fp-lib-table              footprint library table (KIPRJMOD-relative)
lib/                        vendored footprint libraries (see lib/LIBS.md)
BOM.csv                     full bill of materials (MPN / LCSC / DigiKey, pricing)
gerbers.zip                 bare-board manufacturing files (Gerbers + drill)
fabpack_opaque.zip          opaque SKU: gerbers + assembly CSVs + ORDERING.md
fabpack_translucent.zip     translucent SKU: gerbers + assembly CSVs + ORDERING.md
assembly/                   loose per-SKU assembly files
  cpl_opaque.csv            pick-and-place, opaque SKU      (90 placements)
  cpl_translucent.csv       pick-and-place, translucent SKU (110 placements)
  bom_opaque.csv            assembly BOM, opaque SKU
  bom_translucent.csv       assembly BOM, translucent SKU
  hand_solder_afterlist.csv the parts you hand-solder after the boards arrive
renders/                    top.png, bottom.png (v5_7), js1_detail.png (joystick
                            close-up; still the v5_6 plot — the revision changed
                            nothing at that end of the board)
```

## Two SKUs, one bare board

The bare PCB is **identical** for both SKUs — only which parts get placed differs:

| SKU | Top shell | Underglow (LED15-24 + C40-49) |
|---|---|---|
| **opaque** (Rev A default) | solid | not populated (DNP) |
| **translucent** | glowing diffuser | populated |

## Ordering

Upload **`gerbers.zip`** to the bare-board quote and the matching SKU's
`assembly/cpl_<sku>.csv` + `assembly/bom_<sku>.csv` to turnkey (consigned)
assembly — **single side** (bottom SMD; the joystick is a fab-placed
through-hole part). Each `fabpack_*.zip` bundles the Gerbers, that SKU's
assembly CSVs, and a full step-by-step `ORDERING.md` (board options, tier
guidance, DNP handling, pricing ballpark, and pre-order gates). The repo-root
`HOW-TO-ORDER.md` is the condensed walk-through.

**LED cut-outs are intentional:** the Edge.Cuts layer has 14 small internal
rounded-rectangle windows (one per top LED) so the reverse-mounted LEDs shine
through the board — not an outline error.

## Hand-soldered afterlist

The fab places everything else — including the JS1 joystick, a machine-placed
through-hole YA13 (its wiring is datasheet-verified; no metering needed). You
hand-solder (see `assembly/hand_solder_afterlist.csv`):

- **RE1** — EC11 rotary encoder + push (through-hole). Seat it flush.
- Optionally the 13 hot-swap sockets (SW1-13) and 2 tact switches (SW14/15) if you
  opt out of fab assembly for them — they are fab-placed by default.

At first power-on, if the stick drives the cursor opposite to your push, that is
the expected 180°-clocking polarity — a one-line config fix per axis, described
with the calibration note in `../../firmware/POLARITY-NOTE.md`.

## Firmware / GPIO note

The firmware pin map (`firmware/loudest_micro/`) matches the v5 board (identical
to Rev A v4 — the v5 changes needed zero firmware edits) and has been
validated — it boots in an RP2040 emulator and its Raw HID status protocol is
conformance-tested. See `firmware/FIRMWARE-V4-NOTES.md` and `firmware/tests/`.

## License

Hardware (schematic, PCB): **CERN-OHL-W-2.0**. Vendored footprint libraries keep
their upstream licenses (marbastlib: CERN-OHL-P v2; MX_V2: MIT) — see `lib/LIBS.md`.

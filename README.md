# agentpad13

Open-source 13-key macropad for agentic work — in the spirit of the Work Louder
Creator Micro 2 / OpenAI Codex Micro, built from scratch. Bare RP2040, USB-C,
12×1U + 1×2U hot-swap keys, clickable EC11 rotary encoder, analog PSP-slider
joystick, a capacitive-touch key, and a 24-LED RGB chain (per-key + edge
underglow) driven over Raw HID by an open agent-status protocol
(thinking / running / waiting / done, one key per agent).

## Status

- **PCB: Rev A — COMPLETE.** Finished and fabrication-ready (details below).
- **Case: redesign in progress.** The case files under `hardware/case/` target the
  previous board revision and do **not** fit Rev A v4; a redesigned case
  (FR4 plate-as-deck + printed tray) is in progress.
- **Firmware: builds and runs**, pending a pin-map update for the Rev A v4 GPIO
  remap (see note below).

### PCB (complete)

- **Board:** Rev A v4, **84.2 × 100 mm**, **2-layer** RP2040, 1.6 mm FR-4.
- **Features:** 13 hot-swap keys (12×1U + 1×2U) + EC11 encoder + analog PSP
  joystick + capacitive touch + per-key RGB and edge underglow.
- **DRC:** clean (0 violations, 0 unconnected) at a **0.152 mm / 6-mil standard
  fab tier** (verified in KiCad 9).
- **Fab package** (`hardware/pcb/`): Gerbers + drill and per-SKU assembly
  bundles — **opaque** (underglow unpopulated) and **translucent** (underglow
  populated). The bare board is identical for both.
- **Hand-soldered afterlist:** rotary encoder, joystick, hot-swap sockets, and
  tact switches are finished by hand after the assembled boards arrive.

> **Firmware note:** Rev A v4 remapped several RP2040 GPIOs from the pin map
> frozen in the current firmware tree; a firmware update to match the final pinout
> is forthcoming. Re-verify the pin map against the board before relying on it.

> **JS1 joystick:** the JS1 footprint is provisional for the Adafruit 3103 PSP
> slider — **verify the pinout with a multimeter before hand-soldering** (this
> matches the note on the board silkscreen).

## Contents

```
hardware/
  pcb/    KiCad 9 project (agentpad13.kicad_pcb/.kicad_sch/.kicad_pro), vendored
          footprint libs, final BOM, Gerbers, per-SKU assembly bundles, renders.
  case/   Parametric build123d case (unibody shell + plate + bottom lid),
          tolerance coupons, STL/STEP exports. NOTE: targets the previous board
          revision (84.2 × 103.7, round corners) and does NOT fit Rev A v4
          (84.2 × 100, chamfered) — a redesigned case is in progress.
firmware/
  loudest_micro/  vial-qmk keyboard tree (RP2040, direct-pin, ENCODER_MAP,
                  analog joystick modes, Raw HID status protocol).
  prebuilt/       Flashable UF2s (default + vial), built per BUILD.md.
  BUILD.md        Reproducible toolchain + build recipe.
```

## Licensing

- `hardware/` — **CERN-OHL-W-2.0** (schematic, PCB, case CAD).
- `firmware/` — **GPL-2.0-or-later** (QMK/vial-qmk derivative). Corresponding
  source for the prebuilt UF2s = this tree built against
  [vial-qmk](https://github.com/vial-kb/vial-qmk) per `firmware/BUILD.md`.

Vendored footprint libraries under `hardware/pcb/lib/` keep their upstream
licenses (marbastlib: CERN-OHL-P v2; MX_V2: MIT) — see `hardware/pcb/lib/LIBS.md`.

Built from scratch; not affiliated with Work Louder or OpenAI.

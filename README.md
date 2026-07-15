# agentpad13

Hardware and firmware for the **Loudest Micro** — an open-source 13-key macropad for agentic work, in the spirit of the Work Louder Creator Micro 2 / OpenAI Codex Micro. 12×1U + 1×2U hot-swap keys, clickable rotary encoder, planar analog joystick, capacitive touch layer key, 24-LED RGB chain (per-key + underglow) driven by an open Raw HID **agent-status protocol** (thinking / running / waiting / done, one key per agent), bare RP2040, USB-C.

Status: **Rev A design phase** — schematic captured (unrouted), firmware compiling, case printable. Nothing has been fabricated yet.

## Contents

```
hardware/
  pcb/       KiCad 9 schematic (118 components), draft BOM (LCSC#/JLC tiers),
             self-review notes. Footprints unbound; PCB layout not started.
  case/      Parametric build123d case (unibody shell w/ integrated plate +
             bottom lid), 5 tolerance coupons, STL/STEP exports, khana-checked.
firmware/
  loudest_micro/   vial-qmk keyboard tree (RP2040, direct-pin, ENCODER_MAP,
                   analog joystick modes, Raw HID status protocol v0).
  prebuilt/        Flashable UF2s (default + vial), built per BUILD.md.
  BUILD.md         Reproducible toolchain + build recipe.
```

The design docs, research dossiers, and host-side daemon (`loudestd`, MIT) live in the parent project repo; the firmware's Raw HID handler conforms byte-for-byte to that daemon's `protocol.py` (32-byte reports: SET_KEY / SET_LAYER / CLEAR / PING→CAPS).

## Licensing

- `firmware/` — **GPL-2.0-or-later** (QMK/vial-qmk derivative; SPDX headers in sources). Corresponding source for the prebuilt UF2s = this tree built against [vial-qmk](https://github.com/vial-kb/vial-qmk) per `firmware/BUILD.md`.
- `hardware/` — **CERN-OHL-W-2.0** (schematic, PCB, case CAD; SPDX headers where applicable).

No NC restrictions anywhere. Built from scratch; not affiliated with Work Louder or OpenAI.

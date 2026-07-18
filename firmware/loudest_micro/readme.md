# agentpad13

Open-hardware agent macropad (Rev A, RP2040). 13 keys (12x 1U grid + 1x 2U
hero), EC11 encoder with push, planar analog joystick, TTP223 touch pad, and
24 addressable LEDs (13 per-key + 1 layer indicator + 10 underglow) driven as
a live agent-status display over Raw HID.

* Keyboard Maintainer: [yuz207](https://github.com/yuz207)
* Hardware Supported: agentpad13 Rev A PCB (RP2040, board `v4_r27`)
* Hardware Availability: open source (CERN-OHL-W v2), <https://github.com/yuz207/agentpad13>

The QMK keyboard/module name is `loudest_micro` (the project's working name);
the user-visible product name, USB product string, and Vial sidebar name are
**agentpad13**. The directory name is kept because QMK derives build targets,
artifact names, and file names from it, and the Raw HID daemon contract
(`daemon/loudestd/protocol.py`) predates the rename.

Pin map source of truth: `hardware/pcb/v4/ORDER-READINESS.md` (Layer 4 - the
definitive per-GPIO table for board `v4_r27`, extracted twice from the final
copper). `firmware/check_pins_v4.py` asserts this tree against that table.

Make example for this keyboard (after setting up your build environment):

    qmk compile -kb loudest_micro -km default
    qmk compile -kb loudest_micro -km vial

Flashing example for this keyboard:

    qmk flash -kb loudest_micro -km default

To enter the bootloader, hold BOOTSEL while plugging in USB (or double-tap
RESET), then copy the `.uf2` onto the `RPI-RP2` drive.

See the [build environment setup](https://docs.qmk.fm/#/newbs_getting_started) and
the [make instructions](https://docs.qmk.fm/#/getting_started_make_guide) for more
information. Brand new to QMK? Start with our [Complete Newbs
Guide](https://docs.qmk.fm/#/newbs). The exact reproducible toolchain for this
board (vial-qmk fork, patch, versions) is in `firmware/BUILD.md`.

## Layout

```
 [JS]        USB        (ENC)      <- top control band (not in the key matrix)
 +----+----+----+----+
 |SW1 |SW2 |SW3 |SW4 |            row 0
 +----+----+----+----+
 |SW5 |SW6 |SW7 |SW8 |            row 1
 +----+----+----+----+
 |SW9 |SW10|SW11|SW12|            row 2
 +----+----+----+----+
 |TP| |  SW13   | |EP|            row 3: touch [3,2] | SW13 2U [3,0] | encoder push [3,1]
 +--+ +---------+ +--+
```

Direct-pin matrix (Rev A x-monotonic routing remap - logical positions are
unchanged, only the physical GPIOs moved):

| Function | GPIO |
|---|---|
| SW1..SW4 (row 0) | GP12, GP9, GP5, GP2 |
| SW5..SW8 (row 1) | GP11, GP8, GP4, GP1 |
| SW9..SW12 (row 2) | GP10, GP7, GP3, GP0 |
| SW13 (2U hero) | GP6 |
| Encoder A / B / push | GP13 / GP14 / GP15 |
| Touch (TTP223 OUT) | GP16 |
| WS2812 data (via level shifter) | GP17 |
| Joystick X / Y (ADC) | GP26 / GP27 |

## Firmware feature notes

* `ENCODER_MAP` - per-layer encoder actions (volume by default).
* `JOYSTICK` - GP26/GP27 analog axes as a HID gamepad; the `JS_MODE` keycode adds
  custom arrow (8-way) and scroll modes. Calibration is a bring-up placeholder.
* `RAW_ENABLE` - status protocol v0 (`SET_KEY`/`SET_LAYER`/`CLEAR`/`PING`),
  wire contract in `daemon/loudestd/protocol.py`. In the vial build the
  protocol coexists with VIA/Vial through a `via_command_kb()` dispatcher
  (see `firmware/BUILD.md` for the documented edge-case collisions).
* Touch key gated by the `TP_TOG` keycode.

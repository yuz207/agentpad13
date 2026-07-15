# Loudest Micro

![Loudest Micro](https://via.placeholder.com/640x400?text=Loudest+Micro+Rev+A)

Open-hardware agent macropad (CM2-class clone). 13 keys (12x 1U grid + 1x 2U hero),
EC11 encoder with push, planar analog joystick, TTP223 touch pad, 24 addressable
LEDs (13 per-key + 1 layer indicator + 10 underglow) driven as a live agent-status
display over Raw HID.

* Keyboard Maintainer: [work-loudest](https://github.com/work-loudest)
* Hardware Supported: Loudest Micro Rev A PCB (RP2040)
* Hardware Availability: open source (CERN-OHL-W v2)

Pin map and LED chain order are frozen in
`docs/independent-design/phase0-layout-v2-notes.md` (Phase-0 layout v2, D1 top-band).

Make example for this keyboard (after setting up your build environment):

    qmk compile -kb loudest_micro -km default
    qmk compile -kb loudest_micro -km vial

Flashing example for this keyboard:

    qmk flash -kb loudest_micro -km default

To enter the bootloader, hold BOOTSEL while plugging in USB (or double-tap RESET),
then copy the `.uf2` onto the `RPI-RP2` drive.

See the [build environment setup](https://docs.qmk.fm/#/newbs_getting_started) and
the [make instructions](https://docs.qmk.fm/#/getting_started_make_guide) for more
information. Brand new to QMK? Start with our [Complete Newbs
Guide](https://docs.qmk.fm/#/newbs).

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

## Firmware feature notes

* `ENCODER_MAP` — per-layer encoder actions (volume by default).
* `JOYSTICK` — GP26/GP27 analog axes as a HID gamepad; the `JS_MODE` keycode adds
  custom arrow (8-way) and scroll modes. Calibration is a placeholder (Phase-1).
* `RAW_ENABLE` — status protocol v0 (`SET_KEY`/`SET_LAYER`/`CLEAR`/`PING`).
* Touch key gated by the `TP_TOG` keycode (the real CM2 touch has no off switch).

See `firmware/BUILD.md` in the project repo for the exact reproducible toolchain
and the list of Phase-4 follow-ups.

# FIRMWARE POLARITY NOTE — YA13 joystick axis sense (v5)

**TL;DR:** Both joystick axes' *direction sense* are inverted versus the YTL
YA13 datasheet datum because the part is mounted **180° clocked** from the
datasheet datum on the v5 board (pot bodies face West + North instead of the
datasheet's South/East). If, at first power-on, the stick drives the cursor /
arrows / scroll in the **opposite** direction from what you push, invert the
affected axis in the firmware config — **one line per axis, no rebuild is
shipped in this bundle.**

## What is shipped

The prebuilt UF2s in `firmware/prebuilt/` (`loudest_micro_default.uf2`,
`loudest_micro_vial.uf2`) are **unchanged from Rev A** — byte-for-byte identical
to the Rev-A release (md5 `4af788ae…` default / `e5008942…` vial). The v5 board
changes (RE1 move, J1 flip, JS1→YA13) required **zero** firmware changes: the
joystick pin map is untouched — `JOY_X_ADC = GP26/ADC0`, `JOY_Y_ADC = GP27/ADC1`
— and the YA13 wipers land on the same `+3V3 / JOY_X / JOY_Y / GND` nets as the
retired slider. So no rebuilt UF2 is included; this note is the pointer for the
one-line fix if a direction feels reversed.

## Why the sense is inverted (board fact, not a firmware bug)

Board ledger (`hardware/pcb/V5-NOTES.md`, JS1→YA13 rev, datasheet check for
LCSC C37323742): the YA13 datasheet datum has VR1 body **South** and VR2 body
**East**. The v5 placement clocks the part **180° from that datum** — VR1 (the
Y pot) faces **North**, VR2 (the X pot) faces **West** — which was forced by the
placement-study freeze (pot groups exit West + North to clear the neighbors).
The wiper is confirmed to be the **center pin** of each 3-pin group (the hard
requirement — an end-pin wiper would have been a stop; it is not). A 180°
clocking swaps each pot's `+3V3`/`GND` end assignment, which **inverts both
axes' travel direction** relative to the datasheet drawing. This was
pre-flagged in the brief as a firmware-trivial polarity item, not a stop.

## The one-line fix (per axis)

The joystick is QMK's native analog `joystick` feature, configured in
`firmware/loudest_micro/keyboard.json`:

```json
"joystick": {
    "driver": "analog",
    "axes": {
        "x": {"input_pin": "GP26", "low": 0, "rest": 512, "high": 1023},
        "y": {"input_pin": "GP27", "low": 0, "rest": 512, "high": 1023}
    }
}
```

To invert an axis, **swap its `low` and `high`** (one edit per reversed axis),
e.g. to flip X:

```json
"x": {"input_pin": "GP26", "low": 1023, "rest": 512, "high": 0}
```

That flips the QMK HID-gamepad axis. The custom **arrow / scroll** modes
(`JS_MODE` in `loudest_micro/loudest_micro.c`) read the SAME pins directly via
`analogReadPin(GP26/GP27)` and compare against `JS_CENTER ± JS_THRESHOLD`; if
you use those modes, mirror the affected comparison there too (or negate the
reading around center: `v -> (JS_MAX - v)`) so all output paths agree. Rebuild
with the standard QMK/Vial flow in `firmware/BUILD.md`.

## Related watch-item (separate from polarity)

`keyboard.json` still carries the **placeholder calibration** (`low 0 / rest
512 / high 1023`) inherited from the slider era. The real `low / rest / high`
must come from a **bring-up ADC sweep on the actual YA13** at assembly; the
placeholder is a nominal 10-bit span, not metered values. Do the sweep and the
polarity fix together in one firmware pass — both are config-only, one rebuild.

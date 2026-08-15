# FIRMWARE POLARITY NOTE — YA13 joystick axis sense (v5)

**TL;DR:** Both joystick axes' *direction sense* are inverted versus the YTL
YA13 datasheet datum because the part is mounted **180° clocked** from the
datasheet datum on the v5 board (pot bodies face West + North instead of the
datasheet's South/East). If, at first power-on, the stick drives the cursor /
arrows / scroll in the **opposite** direction from what you push, invert the
affected axis in the firmware config — **one line per axis, then rebuild.** (A
polarity flip is compile-time; `firmware/BUILD.md` has the flow. **No axis flip
is pre-applied** in the shipped UF2s.)

## What is shipped

The prebuilt UF2s in `firmware/prebuilt/` were **rebuilt 2026-08-13** to fix the
TTP223 touch-polarity defect — the board straps `AHLB → GND` (active-**high**)
while the firmware had assumed active-low, so matrix `[3,2]` read permanently
pressed and the pad booted into layer 1 — and **rebuilt again 2026-08-15** for
the isotropic RGB layout (finding 7) and the duplicate `housekeeping_task_user()`
call. Details in `firmware/loudest_micro/config.h` and `v5/V5-NOTES.md`.
**Neither rebuild touched the joystick, so everything below still applies
unchanged.** Shipped bytes:

| file | md5 | bytes | replaces |
|---|---|---|---|
| `loudest_micro_default.uf2` | `1c0ff911d545d0943c11a5971279d3ae` | 88576 | `cf5bd628…`, 88576 |
| `loudest_micro_vial.uf2` | `286fb09d0ce1d96c74f2a0baf8348378` | 104448 | `b31673a7…`, 104448 |
| `loudest_micro_calibrate.uf2` | `aabf7954f1e2b46880f298fd620d63ff` | 96768 | `a81ce4a1…`, 96768 |

*(Superseded 2026-08-15, kept for provenance: the 2026-08-13 touch-fix pair was
`loudest_micro_default.uf2` `cf5bd62853ea591b39a1ce7246848229` / 88576 and
`loudest_micro_vial.uf2` `b31673a7ba6a6219a0d5a3b9aee52e42` / 104448, which in
turn replaced the Rev-A binaries `4af788ae…` / 88064 and `e5008942…` / 104448.
The `calibrate` bring-up UF2 was added 2026-08-13 as `a81ce4a1…`. All sizes are
unchanged across the 2026-08-15 rebuild — the changes were a coordinate table
and one removed call.)*

The **default** and **calibrate** builds reproduce byte-for-byte from these
sources (proved again on 2026-08-15: two clean-`.build` rebuilds each, identical
bytes); the **vial** build is non-deterministic run-to-run (LTO/link ordering),
so its md5 records the shipped bytes and is **not** a reproducibility target.

The v5 board changes (RE1 move, J1 flip, JS1→YA13) still required **zero**
joystick firmware changes: the pin map is untouched — `JOY_X_ADC = GP26/ADC0`,
`JOY_Y_ADC = GP27/ADC1` — and the YA13 wipers land on the same
`+3V3 / JOY_X / JOY_Y / GND` nets as the retired slider. This note remains the
pointer for the one-line axis fix if a direction feels reversed.

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

**The sweep now has a mechanism** (added 2026-08-13): flash
`firmware/prebuilt/loudest_micro_calibrate.uf2`, open a text editor, and the
board types its own rest/min/max, per-axis `inverted=YES/NO`, a re-derived
`JS_CENTER`/`JS_THRESHOLD`, and finished copy-pasteable config lines **with the
`low`/`high` swap above already applied** to any inverted axis. Step-by-step
instructions: `firmware/BRING-UP.md` *(moved there 2026-08-15 from
`firmware/BUILD.md` §4a, which now forwards to it, so that the procedure ships
in the release bundle alongside this note)*. Source and reasoning:
`firmware/loudest_micro/keymaps/calibrate/`.

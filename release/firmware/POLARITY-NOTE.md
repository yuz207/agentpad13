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
call, then **rebuilt and renamed a third time later on 2026-08-15** for protocol
v1 and the encoder direction flip. Details in
`firmware/loudest_micro/config.h` and `v5/V5-NOTES.md`.
**None of those rebuilds changed which WAY an axis reads, so everything below
still applies unchanged** — the v1 work added *where the ends are*, not *which
end is which*. Shipped bytes:

| file | built from | md5 | bytes | replaces |
|---|---|---|---|---|
| `agentpad13.uf2` | `-km vial` | `a7b8da85a7d3f0de96b983be8c782ba2` | 109568 | `agentpad13.uf2` `cce79a07…`, 107008 |
| `agentpad13_reference.uf2` | `-km default` | `4caac0bca0cafb1d3ebf7d46dd9e7adb` | 93696 | `agentpad13_reference.uf2` `34fa434b…`, 90624 |

**REBUILT AGAIN 2026-08-15 — on-board (SW14) joystick calibration.** The row
above supersedes the first v1 pair (`cce79a07…` / `34fa434b…`, 107008 / 90624 B).
Calibration no longer needs a host at all: SW14 runs the whole routine on the
board and stores the result itself (`firmware/BRING-UP.md`,
`docs/PROTOCOL-V1-CONTRACT.md`). **This changed nothing about axis DIRECTION
either** — the routine measures where the ends are, exactly as 0x51 does, and
shares its code path byte-for-byte.

**Both artifacts were renamed and rebuilt on 2026-08-15** for protocol v1
(joystick calibration over raw HID, `docs/PROTOCOL-V1-CONTRACT.md`) and for
`ENCODER_DIRECTION_FLIP` (the EC11 A/B landing measured on the assembled board).
The sizes grew by 2560 B (vial) and 2048 B (default) — that is the v1 handlers,
the EEPROM store and the calibration derivation.

*(Superseded, kept for provenance: `loudest_micro_default.uf2` / `loudest_micro_vial.uf2`
were `1c0ff911…` / `286fb09d…` (2026-08-15 isotropic-RGB rebuild), before that
`cf5bd628…` / `b31673a7…` (2026-08-13 touch fix), before that the Rev-A binaries
`4af788ae…` / 88064 and `e5008942…` / 104448. A third artifact,
`loudest_micro_calibrate.uf2` (`a81ce4a1…` then `aabf7954…`, 96768), existed
between 2026-08-13 and 2026-08-15; the separate bring-up firmware it came from
is **deleted** — protocol v1 replaced it with a host-invoked routine that needs
no reflash. See `firmware/BRING-UP.md`.)*

The **reference** build reproduces byte-for-byte from these sources (proved
again on 2026-08-15: two rebuilds from a wiped `.build/`, identical bytes); the
**vial** build is non-deterministic run-to-run (LTO/link ordering), so its md5
records the shipped bytes and is **not** a reproducibility target.

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
512 / high 1023`) inherited from the slider era, and it now stays that way on
purpose: since 2026-08-15 it is the *uncalibrated fallback*, not a value waiting
to be edited.

**The sweep no longer needs a firmware pass at all.** As of 2026-08-15 the board
keeps its own calibration: a 14-byte EEPROM block holds per-axis rest/min/max,
the trigger threshold is derived from it as `floor(60% of the smaller
half-swing)`, and the values are applied to the arrow and scroll modes *and* to
the native HID gamepad. Nothing is rebuilt and nothing is reflashed, and the
calibration **survives a power cycle** — proved, not assumed, by
`firmware/sim/joystick.cjs`, which stores a calibration, restarts the emulated
MCU carrying only the flash image, and reads the values back.

Protocol v1 also exposes that store on the wire for host tooling and diagnostics
(`0x50` read live ADC + stored calibration, `0x51` store, `0x52` wipe —
`docs/PROTOCOL-V1-CONTRACT.md`).

> **The owner-facing procedure is `firmware/BRING-UP.md`** — flash, hold SW14 for
> a second, follow the LEDs. It was rewritten for the on-board routine on
> 2026-08-15; this note's earlier warning that it was stale no longer applies.

*(Superseded 2026-08-13→2026-08-15: the sweep used to mean flashing a separate
`loudest_micro_calibrate.uf2`, opening a text editor and letting the board TYPE
its own rest/min/max plus copy-pasteable config lines, then pasting those back
into two source files and rebuilding. That keymap, its UF2 and its referee
`firmware/sim/calibrate.cjs` are all deleted.)*

**The polarity fix below is still compile-time and still a separate question
from calibration** — `loudest calibrate` records where the stick's ends are, not
which way round they are. If an axis reads reversed, swap its `low`/`high` in
`keyboard.json` and rebuild, exactly as described above.

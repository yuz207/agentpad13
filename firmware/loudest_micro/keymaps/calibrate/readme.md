# `calibrate` — the agentpad13 bring-up keymap

**This is a bring-up tool. It is never the daily firmware.** It replaces every
key with a calibration function and emits no normal keystrokes at all. Flash it
once on the first assembled board, read the numbers it types, then flash
`loudest_micro_default.uf2` (or the Vial build) back.

Step-by-step instructions for a non-EE owner live in **`firmware/BRING-UP.md`**
*(moved there 2026-08-15 from `firmware/BUILD.md` § "4a. Bring-up:
first-power-on calibration", which now forwards to it and keeps only the
maintainer-side build/referee commands)*. This file explains *why it exists* and
*what the numbers mean*.

## Why it exists

Four bring-up items had been written down for months with **no mechanism to
perform them**:

| item | where it was recorded |
|---|---|
| joystick `low` / `rest` / `high` are placeholders (`0/512/1023`) | `keyboard.json`, `BUILD.md` §8, `POLARITY-NOTE.md` |
| `JS_THRESHOLD 300` was never metered against a real YA13 | `v5/V5-NOTES.md` finding 3 |
| JS1 sits 180° from its datasheet datum, so an axis may read reversed | `firmware/POLARITY-NOTE.md` |
| the 2026-08-13 TTP223 touch fix has never been seen on silicon | `docs/HANDOFF-2026-08-06.md` §5 |

Every one of them said "do the bring-up ADC sweep" and none said **how**. There
was no how: raw-HID protocol v0 is LOCKED and carries no ADC readout, and Vial
exposes no raw analog. So the numbers could not be got off the board.

But the board is a keyboard. It can **type its own calibration report** into any
text editor. That is the whole idea.

## Why the joystick item is not cosmetic

`loudest_micro.c` drives the arrow (8-way) and scroll modes from a direct
`analogReadPin()` compared against `JS_CENTER ± JS_THRESHOLD` = `512 ± 300`.
The comparisons are strict, so a direction fires **only below 212 or above 812**.
A gimbal pot at end-of-mechanical-travel commonly covers well under its full
electrical track. If the assembled YA13 only swings, say, 250..780:

* the native HID gamepad still works (at reduced scale), so the stick "works";
* **`JS_MODE_ARROWS` and `JS_MODE_SCROLL` never fire at all** — two of the three
  joystick modes silently dead, with no error anywhere.

That is why step 4 types a per-direction **`fires` / `NEVER FIRES`** verdict
against the shipped constants, not just the endpoints.

## What the derived numbers mean

| line | rule | why that rule |
|---|---|---|
| `inverted=YES` on Y | `y_up > y_rest` | the firmware fires UP on `y < JS_CENTER - JS_THRESHOLD`, so on a correctly-sensed axis pushing up must **decrease** the reading |
| `inverted=YES` on X | `x_right < x_rest` | it fires RIGHT on `x > JS_CENTER + JS_THRESHOLD` |
| `#define JS_CENTER` | `round((x_rest + y_rest) / 2)` | the shipped code uses **one** `JS_CENTER` for both axes; if the two rests differ by more than 30 counts the report prints a WARNING, because a single center is then a compromise |
| `#define JS_THRESHOLD` | `floor(0.60 × smallest half-swing)` | every direction fires with 40 % of its travel still in reserve before the end-stop, so no direction needs the stick jammed against the frame |
| `noise X=+/-n` | largest deviation from the rest average over a 100-sample, ≥500 ms window | a threshold that sits inside the noise floor would self-trigger; the report WARNs if the derived threshold is not more than 3× the noise half-band |
| `low` / `high` in the typed JSON | **already swapped** for any axis marked `inverted=YES` | that swap *is* the documented fix — `POLARITY-NOTE.md` "The one-line fix". The typed lines are final; paste them as they are |

All numbers are in the firmware's 10-bit domain (0..1023) — what
`analogReadPin()` returns on RP2040, and the same domain `keyboard.json`
`low`/`rest`/`high`, `JS_CENTER` and `JS_THRESHOLD` already use.

## What it does NOT change

Nothing outside this directory. It is a keymap: `loudest_micro.c`,
`loudest_micro.h`, `config.h` and `keyboard.json` are untouched by it. The touch
key still arrives at `[3,2]` because `loudest_micro.c`'s `matrix_scan_kb()`
injects it there; this keymap just prints `TOUCH:DOWN` / `TOUCH:UP` instead of
moving a layer.

The one build difference from `keymaps/default` is that
**`ENCODER_MAP_ENABLE` is deliberately not set** — see `rules.mk` for why.

## Referee

`firmware/sim/calibrate.cjs` boots the real `loudest_micro_calibrate.uf2` in
rp2040js, injects ADC values, and asserts the typed report **character for
character** against expectations computed independently in JavaScript. Run it
after any change here:

```bash
node firmware/sim/calibrate.cjs                # must be PASS
node firmware/sim/calibrate.cjs --no-adc-fix   # must FAIL — proves the harness
                                               # is measuring, not agreeing
```

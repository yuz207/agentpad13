# Protocol v1 — joystick calibration commands (CONTRACT, 2026-08-15)

This file is the **single source of truth** both public implementations are written
against: `firmware/loudest_micro/loudest_micro.c` (device) and
`firmware/tests/conformance/protocol_oracle.py` (dependency-free host oracle).
`firmware/tests/conformance/run_conformance.py` asserts the two agree.
If an implementation and this file disagree, STOP — do not "fix" one side silently.

## Why v1 exists

Protocol v0 carried no way to read the joystick, so joystick calibration had no
mechanism except a separate bring-up firmware that TYPED its results. That design is
retired. v1 lets the host read the ADC and store calibration on the board, so
calibration is an ordinary host-invoked routine that needs no mode, no board button,
no separate firmware, and no reflash.

## Version

`LOUDEST_PROTO_VERSION` 0 -> **1**. The CAPS reply (PING 0x04) now reports 1 in byte 4.
v0 clients are unaffected: they never send 0x50-0x52 and the v0 commands are unchanged
byte-for-byte.

## Command IDs — why 0x50-0x52

**Measured from `quantum/via.h` in the pinned vial-qmk tree**: VIA occupies 0x01-0x13,
plus `id_vial_prefix` 0xFE and `id_unhandled` 0xFF. The first-draft IDs 0x05/0x06/0x07
COLLIDE with `id_dynamic_keymap_set_keycode` / `id_dynamic_keymap_reset` /
`id_custom_set_value`. 0x50-0x52 are outside every VIA range, so in the vial build
`via_command_kb()` claims them **unconditionally** — no payload heuristics, unlike the
delicate tail-zero disambiguation that IDs 0x01-0x04 require. Do not move these IDs
into VIA's range.

## Frames

32-byte, report-ID-less, zero-padded (identical framing to v0). All multi-byte values
are **little-endian uint16**. All ADC values are in the firmware's 10-bit domain,
0..1023 (`analogReadPin` on RP2040: `platforms/chibios/drivers/analog.c` returns
`sample >> (12 - ADC_RESOLUTION)`, ADC_RESOLUTION 10).

### 0x50 GET_JOYSTICK — read live ADC + stored calibration

Request: `[0x50, token, 0 x30]`

Reply:

| bytes | field | notes |
|---|---|---|
| 0 | 0x50 | echoes command id |
| 1 | token | echoes request token |
| 2 | 0x4C `'L'` | magic, same as CAPS |
| 3 | 0x44 `'D'` | magic |
| 4:6 | live_x | current GP26/ADC0 reading |
| 6:8 | live_y | current GP27/ADC1 reading |
| 8 | cal_state | 0 = uncalibrated (placeholders in force), 1 = calibrated from EEPROM |
| 9:11 | rest_x | stored, or placeholder 512 when cal_state=0 |
| 11:13 | rest_y | " |
| 13:15 | min_x | stored, or placeholder 0 |
| 15:17 | max_x | stored, or placeholder 1023 |
| 17:19 | min_y | stored, or placeholder 0 |
| 19:21 | max_y | stored, or placeholder 1023 |
| 21:23 | threshold_x | DERIVED, see below |
| 23:25 | threshold_y | DERIVED |
| 25:32 | zero | padding |

### 0x51 SET_CALIBRATION — store calibration, persist to EEPROM

Request: `[0x51, rest_x(2), rest_y(2), min_x(2), max_x(2), min_y(2), max_y(2), 0 x19]`
(fields start at byte 1; total payload 13 bytes)

Reply: `[0x51, status, 0 x30]` — status **0 = accepted and written**, **1 = rejected,
nothing written**.

**Validation (ALL must hold, else reject with status 1 and leave EEPROM untouched):**
- every value <= 1023
- `min_x < rest_x < max_x` and `min_y < rest_y < max_y`
- `rest_x - min_x >= 100`, `max_x - rest_x >= 100`, same for y
  (minimum credible half-swing; below this the stick or ADC is suspect)

Rejection must be **total** — never write a partially-valid struct.

### 0x52 RESET_CALIBRATION — wipe, revert to placeholders

Request: `[0x52, 0 x31]`
Reply: `[0x52, 0x00, 0 x30]`

Clears the EEPROM block (magic invalidated) and reverts live behavior to the shipped
placeholders immediately, without a reboot.

## Derived values (device-side, single definition)

```
center_x    = rest_x                       (per-axis; NOT one shared center)
center_y    = rest_y
threshold_x = 60% of min(rest_x - min_x, max_x - rest_x)
threshold_y = 60% of min(rest_y - min_y, max_y - rest_y)
```

**Rounding is part of the contract:** threshold is the **floor** of 60%, i.e.
`half * 3 / 5` in uint16 integer arithmetic (equivalently `half * 60 // 100`). Never
round-to-nearest. (Added 2026-08-15: the original wording said only "60%" and left this
open. Both implementations independently chose floor and therefore agreed, but that was
luck, not specification — 60% of 101 is 60.6, and a round-to-nearest reading would have
produced a silent one-count divergence that the conformance suite would have caught as
a mystery rather than a spec violation.)

60% means every direction fires with 40% of its half-swing still in reserve before the
end-stop. Per-axis center replaces the old shared `JS_CENTER 512`, which could not
represent a stick whose axes rest at different values.

**Uncalibrated fallback (cal_state = 0):** `center_x = center_y = 512`,
`threshold_x = threshold_y = 300` — i.e. byte-for-byte today's shipped behavior. A
board that is never calibrated behaves exactly as it does now.

## EEPROM

QMK keyboard-level datablock (`EECONFIG_KB_DATA_SIZE` in `config.h`,
`eeconfig_read_kb_datablock` / `eeconfig_update_kb_datablock`, `quantum/eeconfig.h`).

```c
typedef struct {
    uint8_t  magic;    // 0x4A 'J'
    uint8_t  version;  // 1
    uint16_t rest_x, rest_y, min_x, max_x, min_y, max_y;
} loudest_js_cal_t;    // 14 bytes
```

Bad magic or unknown version => treat as uncalibrated, use placeholders, do NOT write.
QMK's own `EECONFIG_KB_DATA_VERSION` handling wipes the block when the declared size or
version changes; our magic/version is a second, independent guard.

**Write policy** ~~writes happen ONLY on an accepted 0x51 and on 0x52~~ —
**AMENDED 2026-08-15**: writes happen ONLY on an accepted 0x51, on 0x52, **and on a
successful SW14-triggered on-board calibration** (below). There is no background or
automatic calibration, so writes are user-initiated and rare — flash endurance is a
non-issue by construction. Do not add periodic or opportunistic writes.

> **Amendment record (2026-08-15).** The original clause admitted only the two
> host-driven writers, because v1 was designed on the assumption that a host would
> always drive calibration. The owner rejected that assumption:
>
> > "Calibration is stored in EEPROM, no daemon needed. You turn on calibration, it
> > fucking calibrates, then it stores. End of story, calibrated usage does not depend
> > on a daemon."
>
> A third writer was therefore added — the on-board routine — and this clause was
> amended rather than silently violated.
>
> **The clause's intent is unchanged and remains binding.** Every write is still
> USER-INITIATED (a deliberate one-second button hold) and RARE. Nothing periodic,
> background, opportunistic or automatic was added, and there is no continuous
> auto-calibration anywhere in the firmware. The owner rejected background learning
> explicitly and **that rejection stands** — do not add it under this amendment.

## On-board routine (SW14) — the primary path, needs no host at all

Added 2026-08-15 under the write-policy amendment above. Triggered by **SW14**, the
button in the back that connects net `BOOTSEL` to `GND` (R6, 1 kΩ, ties `BOOTSEL` to
`QSPI_CS`). Held at power-up that button is the mask-ROM bootloader gesture; pressed
while the firmware is running it starts calibration. The two never collide because
they are separated in time — at power-up our firmware is not executing yet.

Sequence, all bounded, ~15 s total, LEDs are the entire UI:

1. **Arm** — SW14 held ~1 s (SW14 is sampled at 10 Hz, so a brush cannot trigger it).
   The routine additionally refuses to arm until it has observed SW14 *released* at
   least once, which a board running this firmware always has.
2. **Centre, ~2 s** — rest is the mean of a 400 ms window whose peak-to-peak spread is
   ≤ 8 counts on both axes. If no window settles within 4 s the run **fails** and
   writes nothing.
3. **Swing, 10 s** — min/max tracked per axis at 100 Hz, seeded at rest (so a stick
   that never moves yields `min == rest == max` and is correctly rejected).
4. **Validate and store** — the six values go through **the same `js_cal_store()`** the
   0x51 handler calls, so validation, derivation and the stored bytes are identical by
   construction, not by convention. Rejection is total.
5. Return to normal operation.

Pressing SW14 again during the routine aborts it, changing nothing. **The keyboard
keeps working normally throughout** — no keymap change, no layer change, no key made
inert. The arrow/scroll joystick modes are the one exception: they stop *emitting*
while the routine runs, because the joystick is the instrument being measured and ten
seconds of swinging it would otherwise spray input into the focused application.

A calibration produced this way is **byte-identical** to one produced by 0x51 from the
same six measurements; `firmware/sim/joystick.cjs` §10b asserts exactly that by
comparing the two EEPROM images.

## Host routine (`loudestd calibrate`)

All procedure logic lives host-side so it can change without touching firmware:
poll 0x50 at ~50 Hz while the user swings the stick, accumulate min/rest/max, apply the
same validation as the device, show the numbers, then push 0x51 and confirm via the
0x51 reply status plus a follow-up 0x50 read. Keys keep working normally throughout —
nothing is inert, because the host drives the routine, not the keyboard.

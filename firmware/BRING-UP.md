# BRING-UP — first-power-on calibration (`calibrate` keymap)

**Do this once, on the first assembled board, before you trust the joystick.**
You need a USB cable and a text editor. No meter, no scope, no soldering, no
electronics knowledge. The board measures itself and **types the answers**.

Why it is needed: the joystick ships with **placeholder** calibration (`low 0 /
rest 512 / high 1023`) and an unmetered `JS_THRESHOLD 300`. The arrow and scroll
joystick modes only fire below **212** or above **812** on the 0–1023 scale. If
the real stick does not reach that far, the gamepad mode still works and those
two modes are **silently dead**. This step finds out, and hands you the exact
lines to fix it.

> **Where this file lives, and what it needs.** Byte-identical copies ship in
> the working tree (`firmware/BRING-UP.md`) and in the release bundle
> (`v5-release-compiled/firmware/BRING-UP.md`) — the same arrangement as
> `firmware/POLARITY-NOTE.md`. This file is the **single source of truth** for
> the procedure; `firmware/BUILD.md` §4a points here rather than repeating it.
> Steps 0 through 2 and Step 4 need nothing but this page, a USB cable, a text
> editor and the `.uf2` files in `firmware/prebuilt/` — no build toolchain and no
> source checkout. Only the *second* of the two routes in Step 3 needs the source
> repo, and it says so where it matters.

## Step 0 — the ten-second firmware check (do this first)

Plug the board in with the **normal** firmware and look at the layer-indicator
LED (the one below the top-left key).

* **Pure red** → the board is running firmware from 2026-08-13 or later. Good.
* **Orange** → that unit predates the TTP223 touch fix and boots into the wrong
  layer. Reflash `firmware/prebuilt/loudest_micro_default.uf2` before going on.

## Step 1 — flash the calibration firmware

1. Unplug the board.
2. Hold the **BOOTSEL** button (SW14) and plug the USB cable back in. A USB
   drive called **`RPI-RP2`** appears on your computer.
3. Drag **`firmware/prebuilt/loudest_micro_calibrate.uf2`** onto that drive.
   md5 `aabf7954f1e2b46880f298fd620d63ff`. The drive disappears by itself — that
   means it worked.
4. Open a text editor (TextEdit, Notepad, VS Code, anything) and **click into an
   empty document**, so what the board types lands somewhere you can read it.

> **Do not hold SW1 while plugging in.** That is QMK's `Reset EEPROM` gesture.
> And set your OS keyboard layout to **US English** for this step — the board
> types plain US ASCII, and a different layout will garble the punctuation in
> the JSON lines (the numbers themselves are fine either way).

The board types **nothing** at plug-in. That is deliberate: at plug-in you may
not have an editor focused yet. Nothing happens until you press SW1.

## Step 2 — the four presses

`SW1` is the **top-left** key. Between presses, hold the stick where the board
asks and *keep holding it while you press*.

| you do | the board types |
|---|---|
| centre the stick, press **SW1** | `agentpad13 cal v1 \| rest X=… Y=… noise X=+/-… Y=+/-…` then `step 2/4: HOLD stick UP …` |
| hold the stick **UP** (away from you, toward the encoder edge), press **SW1** | `Y up sample: …` then `step 3/4: HOLD stick RIGHT …` |
| hold the stick **RIGHT**, press **SW1** | `X right sample: …` then `step 4/4: slowly roll the stick …` |
| slowly roll the stick around its **full outer edge, twice**, press **SW1** | the full report (below) |

After the first press the board keeps watching the stick continuously — that is
what the roll in step 4 is for: it finds the true end-stops in every direction.
Each press takes a moment before anything appears (the first one measures for
half a second), then the text arrives as if someone were typing it.

**Other keys, usable at any time:**

| key | what it does |
|---|---|
| **SW2** (2nd from left, top row) | start over — types `restarted: center the stick, press SW1` |
| **SW3** (3rd from left, top row) | types one live line, `live X=… Y=…`, as often as you like |
| **touch pad** | types `TOUCH:DOWN` when you touch and `TOUCH:UP` when you lift — **that order is the pass**. Reversed order, or nothing at all, means the touch fix is not on this unit |
| **encoder knob** | types `ENC:CW` / `ENC:CCW` per detent; note which physical direction gives `CW` |
| **encoder push** | types `ENC:PRESS` |
| every other key | does nothing, on purpose |

## Step 3 — what to do with the block it types

The last press prints something like:

```
agentpad13 cal v1 | REPORT
X: min=180 rest=507 max=850  inverted=NO
Y: min=180 rest=514 max=850  inverted=NO
shipped JS_THRESHOLD 300 verdict (fires only below 212 or above 812): X- fires X+ fires Y- fires Y+ fires
--- apply to firmware/loudest_micro/keyboard.json (joystick.axes): ---
"x": {"input_pin": "GP26", "low": 180, "rest": 507, "high": 850},
"y": {"input_pin": "GP27", "low": 180, "rest": 514, "high": 850}
--- apply to firmware/loudest_micro/loudest_micro.c: ---
#define JS_CENTER 511
#define JS_THRESHOLD 196
note: if an axis shows inverted=YES the arrow/scroll comparisons in
loudest_micro.c must be mirrored for that axis too - POLARITY-NOTE.md
```

Save that text. Then either:

* **Easiest — hand it over.** Paste the whole block to the project agent and ask
  it to apply the calibration. Everything needed is in those lines.
* **Or do it yourself.** This route needs the **source repo** and a working build
  toolchain — the two files named below are firmware *sources*; they are not part
  of the release bundle. Two edits, both copy-paste:
  1. In `firmware/loudest_micro/keyboard.json`, replace the two lines inside
     `"joystick": { "axes": { … } }` with the two `"x": …` / `"y": …` lines the
     board typed. **They are already final** — if an axis says `inverted=YES`,
     its `low` and `high` are already swapped for you (that swap *is* the fix
     described in `firmware/POLARITY-NOTE.md`).
  2. In `firmware/loudest_micro/loudest_micro.c`, replace the `#define
     JS_CENTER` and `#define JS_THRESHOLD` lines with the two the board typed.
  3. Rebuild and reflash with the normal flow in `firmware/BUILD.md` — §3
     (Build) and §4 (Flash) — in the source repo.

Any line starting with `WARNING:` is the board telling you something it measured
does not look right — a stick that barely moves, a threshold buried in the noise
floor, or the two axes resting far apart. Report those rather than working
around them.

**If any direction says `NEVER FIRES`,** the shipped `JS_THRESHOLD 300` is too
big for this stick and the arrow/scroll modes would be dead. The typed
`#define JS_THRESHOLD` is the re-derived value that fixes it — this is exactly
the case the whole step exists to catch.

## Step 4 — put the real firmware back

BOOTSEL again, drag `firmware/prebuilt/loudest_micro_default.uf2` (or
`…_vial.uf2`) onto `RPI-RP2`. The calibration keymap has no normal keys, so
**do not leave it on the board.**

---

Axis-direction background (why an axis can read reversed at all, and what the
`low`/`high` swap does): `firmware/POLARITY-NOTE.md`. Build/flash flow, the pin
map and the maintainer-side gates for this keymap: `firmware/BUILD.md` (§3, §4
and the §4a maintainers block).

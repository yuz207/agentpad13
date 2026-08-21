# BRING-UP — first power-on

**Do this once, on each newly assembled board.** It takes about five minutes.
You need a USB cable and nothing else — no meter, no scope, no soldering, no
software to install, and no electronics knowledge. The board calibrates itself
and stores the result in its own memory.

> **Where this file lives.** `firmware/BRING-UP.md` in the working tree is the
> **single source of truth** for this procedure; `firmware/BUILD.md` §4a points
> here rather than repeating it. A copy ships in the release bundle
> (`release/firmware/BRING-UP.md`), refreshed from this one when the
> bundle is rebuilt. Everything below needs only this page, a USB cable, and the
> `.uf2` files in `firmware/prebuilt/` — no build toolchain and no source
> checkout.

---

## Step 1 — flash the firmware

1. Unplug the board.
2. **Hold the BOOTSEL button (SW14, in the back) and plug the USB cable back
   in.** A USB drive called **`RPI-RP2`** appears on your computer.
3. Drag **`firmware/prebuilt/agentpad13.uf2`** onto that drive.
   md5 `a7b8da85a7d3f0de96b983be8c782ba2`.
4. The drive disappears by itself. That means it worked.

> **If dragging the file fails, use the terminal — this is common on macOS.**
> The bootloader drive is not a real disk. It is a small pretend filesystem
> that accepts exactly one file write and then reboots the board. Anything that
> writes more than the plain file — metadata, extended attributes, a
> preallocation — gets rejected, and you see one of these:
>
> | what you did | what you get |
> |---|---|
> | dragged it in Finder | *"there isn't enough space"* (there is; 132 MB free) |
> | `cp file.uf2 /Volumes/RPI-RP2/` | `Invalid argument` |
> | `cp -X file.uf2 /Volumes/RPI-RP2/` | usually `Invalid argument` too |
>
> **This always works:**
>
> ```
> dd if=firmware/prebuilt/agentpad13.uf2 of=/Volumes/RPI-RP2/fw.uf2 bs=1m
> ```
>
> `dd` writes plain sequential blocks — no metadata, no preallocation, nothing
> the bootloader can refuse. The destination filename is irrelevant; the
> bootloader reads the contents, not the name. You should see roughly
> `109568 bytes transferred`, then the drive disappears on its own.
>
> On Linux, plain `cp` to the mount point normally works. On Windows, dragging
> in Explorer normally works. It is macOS that is fussy here.

> **Do not hold SW1 while plugging in.** SW1 is the top-left key, and holding it
> at plug-in is QMK's **Reset EEPROM** gesture — it wipes your saved settings,
> including the joystick calibration you are about to make.

> **The first time you flash this version, your key layout resets — once.**
> This firmware stores the joystick calibration in a small block of the board's
> memory, which shifts where the layout editor keeps its own data by 14 bytes.
> The board notices and starts that area fresh. If you had customised your
> layout in Vial, redo it after this one upgrade. It will not happen again on
> later updates.

## Step 2 — the ten-second check

Look at the **layer-indicator LED** — the small one just below the top-left key.

* **Pure red** → good. Go on to Step 3.
* **Orange** → this unit is running firmware older than 2026-08-13 and boots
  into the wrong layer. Repeat Step 1; the drag did not take.

## Step 3 — calibrate the joystick

The joystick ships with **placeholder** settings, and until you do this the
arrow and scroll modes may be dead or twitchy. The board fixes this itself.

**Press and hold SW14 — the same button in the back you used to flash — for
about one second, then let go and follow the lights.** The 13 key LEDs are the
whole display. The keyboard keeps working normally the entire time; you can
keep typing if you want to.

| the lights do this | you do this |
|---|---|
| **all 13 keys turn white** | let go of SW14 |
| **a blue bar fills across the keys** (about 2 seconds) | **take your hand off the stick.** It is measuring where the stick rests |
| **a bar fills across the keys again** (about 10 seconds), starting **amber** | **slowly roll the stick around its outside edge**, a few full circles, pushing it as far as it will go |
| **that bar turns green** | you have moved it far enough — keep rolling until the bar finishes |
| **all 13 keys flash green** | **done.** Calibration is stored. It survives unplugging, and you never need to do this again |
| **all 13 keys flash red** | it did not work. Nothing was changed. See below |
| **a brief dim white flash** | cancelled — nothing was changed |

**If you get red,** nothing was stored and your previous settings are untouched.
Just do it again. The two usual causes:

* **You did not move the stick far enough.** Push it all the way to the edge and
  roll it right around the rim, twice, slowly.
* **Your hand was on the stick during the blue bar.** That step measures the
  resting position, so the stick has to be sitting still by itself.

**To cancel at any time,** press SW14 again. The lights flash dim white and
nothing is changed.

> **If your LEDs are switched off,** this step has no display — the lights are
> the only thing the board uses to talk to you here. Turn the RGB back on before
> calibrating, then switch it off again afterwards if you prefer it dark.

## Step 4 — check the touch pad and the encoder

Open a text editor and click into an empty document.

* **Touch pad** — rest a finger on it. It should act while your finger is
  **down**, and stop when you lift. If it behaves backwards — acting when you
  *lift* — this unit predates the touch fix; reflash it (Step 1).
* **Encoder knob** — turn it. **Clockwise should turn the volume up.** If it is
  backwards, note which way is which and report it.
* **Encoder push** — press the knob in. It should mute.

That is the whole bring-up. The board is ready to use.

---

### Notes

**Why SW14 does two things.** Held while you plug the board in, it is the
bootloader button that gives you the `RPI-RP2` drive. Pressed while the board is
already running, it starts calibration. The two can never be confused, because
at plug-in time the calibration firmware is not running yet.

**Nothing here needs a daemon or any host software.** The calibration lives in
the board's own memory and is applied by the board itself, to all three joystick
modes and to the plain USB gamepad.

**A brush cannot start calibration.** The button has to be held for a full
second before the white lights appear.

**If an axis reads reversed** — the stick moves right and the pointer goes left
— that is a separate one-line fix, described in `firmware/POLARITY-NOTE.md`.
Calibration does not correct direction, only range.

Build and flash flow, the pin map, and the maintainer-side gates:
`firmware/BUILD.md` (§3, §4 and the §4a maintainers block). The wire protocol
and the exact calibration maths: `docs/PROTOCOL-V1-CONTRACT.md`.

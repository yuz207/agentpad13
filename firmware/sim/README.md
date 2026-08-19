# agentpad13 — pre-hardware behavioral simulation

Boots the **real production `.uf2`** in a headless RP2040 emulator and drives it
the way a user would: presses every switch, turns the encoder, taps the touch
pad, moves the joystick, and paints every LED over raw HID — then checks what
came back out over USB and what landed in the LED chain buffer.

This is the layer above [`firmware/tests/emulator/`](../tests/emulator/), which
proves the binary *boots, muxes its pins correctly, enumerates, and answers one
PING*. This directory answers the four questions you actually care about before
the boards land:

| Question | Answered here? |
|---|---|
| Do presses register? | **Yes** — all 13 switches, each to its own keycode |
| Do the LEDs trigger? | **Yes** — the ws2812 DMA buffer is read back per frame |
| Are they individually addressable? | **Yes** — 24/24 chain positions, byte-exact, in isolation |
| Does the firmware work? | **Now yes — after it found the reason it didn't.** See below. |

> ## ✅ FIXED 2026-08-13 — this harness caught a ships-broken defect, and the fix is in
>
> **As originally written, both shipped `.uf2`s FAILED 4 of 33 checks under the
> default `--touch=board`.** The cause was a real, ships-broken defect: the
> TTP223 touch strap is wired active-**high** and the firmware assumed
> active-**low**. Detail in
> [The defect this harness catches](#the-defect-this-harness-catches).
>
> The **firmware-only** remedy was applied (boards were already fabricated *and
> populated*, so the `R10` rework was not available): `GP16` was removed from
> `matrix_pins.direct` and is polled with its own active-high sense in
> `loudest_micro.c` `matrix_scan_kb()`, injecting the key event at the same
> logical `[3,2]`. **The current `firmware/prebuilt/*.uf2` pass 33/33 under
> `--touch=board`** — see [After the fix](#after-the-fix).
>
> Nothing in `behavior.cjs` was changed to make that happen; the harness that
> passed the fixed binaries was byte-identical to the one that failed the broken
> ones. *(`behavior.cjs` was edited once since, on 2026-08-15, and only to ADD
> the `--encoder=` A/B described below — an extension, not a relaxation: the
> check count is still 33 and the four touch failures under `--touch=firmware`
> are still byte-identical to the ones quoted here. No check was ever adjusted to
> make a failing thing pass.)*

---

## Run it

One-time setup (installs `rp2040js` and fetches the RP2040 B1 bootrom dump into
the *existing* emulator directory — this directory adds no dependencies of its
own):

```bash
cd firmware/tests/emulator
./get-bootrom.sh && npm install
```

Then:

```bash
cd firmware/sim
node behavior.cjs                                # reference build, board truth on both A/Bs
node behavior.cjs ../prebuilt/agentpad13.uf2     # the vial build
node behavior.cjs --touch=firmware               # the polarity config.h used to assume
node behavior.cjs --encoder=firmware             # the A/B landing config.h used to assume

node joystick.cjs                                # protocol-v1 referee (0x50/0x51/0x52 + EEPROM
                                                 #   + the SW14 on-board routine, section 10)
node joystick.cjs --no-eeprom                    # its counterfactual arm; must FAIL
```

or `npm run sim:default` / `sim:vial` / `sim:default:fwpolarity` /
`sim:default:fwencoder` / `joystick:default` / `joystick:vial` from this
directory. `behavior.cjs` takes **~35 s** on an M-series Mac and `joystick.cjs`
**~6 min** (it grew from ~45 s on 2026-08-15: section 10 drives the real
on-board calibration routine, which is ~15 s of *emulated* time per run and is
run three times — there is no way to shorten it without shortening the routine
the owner actually performs). Both exit non-zero on any failure, so they drop
straight into CI. No network, no account, no cloud upload, no browser.

> **Artifact names changed 2026-08-15.** `firmware/prebuilt/` now ships
> `agentpad13.uf2` (the vial build — the one users want) and
> `agentpad13_reference.uf2` (the plain-QMK, byte-reproducible reference). They
> replace `loudest_micro_vial.uf2` and `loudest_micro_default.uf2`, which is why
> older transcripts in this file name the old files.

### `--touch=` — the most important flag

| Mode | GP16 at rest | Meaning |
|---|---|---|
| `board` *(default)* | **LOW** | What the fabricated PCB does. `R10` (0 Ω) ties `TOUCH_AHLB → GND` on `v5_6.kicad_pcb`; on a TTP223, AHLB low selects **active-high** output, so Q idles LOW and drives HIGH while touched. **This is the mode that must pass.** |
| `firmware` | HIGH | The polarity `config.h` *used to* assume — *"idle high, touched low"*. Kept as the counterfactual arm of the A/B; it does **not** describe any board that exists, and since the fix it is the arm that fails. |

Both shipped builds, run four ways — **before** the fix (Rev-A binaries
`4af788ae…` / `e5008942…`) and **after** it (`cf5bd628…` / `b31673a7…`):

> **Hash note, 2026-08-15.** The shipped pair moved again — `1c0ff911…`
> (default) / `286fb09d…` (vial) — for the isotropic RGB layout and the
> `housekeeping_task_user()` de-duplication. Neither touches polarity, and the
> table below re-measures **identically** on the new binaries: 33/33 PASS under
> `--touch=board`, 4 failures under `--touch=firmware`. The `cf5bd628…` /
> `b31673a7…` labels are kept because this table is the record of the *touch
> fix*'s A/B, not a statement about which bytes ship today.

| Build | `--touch=firmware` | `--touch=board` |
|---|---|---|
| `loudest_micro_default.uf2` **before** | 33 checks, **0 failures** — PASS | 33 checks, **4 failures** — FAIL |
| `loudest_micro_vial.uf2` **before** | 33 checks, **0 failures** — PASS | 33 checks, **4 failures** — FAIL |
| `loudest_micro_default.uf2` **after** | 33 checks, **4 failures** — FAIL | 33 checks, **0 failures** — **PASS** |
| `loudest_micro_vial.uf2` **after** | 33 checks, **4 failures** — FAIL | 33 checks, **0 failures** — **PASS** |

That A/B is the whole diagnostic, and it inverted cleanly: **the same binary
passes under one polarity and fails under the other, and the fix moved which one
is which.** The keymap, the LED chain, the USB stack, the encoder and the
joystick were always fine — only the strap sense was wrong, and the four
failures are exactly the four polarity-bearing checks. A post-fix
`--touch=firmware` failure is therefore expected and *correct*: it is the harness
still proving it can tell the two polarities apart. (The DIAGNOSIS prose printed
in that arm was written for the pre-fix direction and now reads backwards; it is
left verbatim because `behavior.cjs` is the referee and was deliberately not
edited as part of the fix.)

### `--encoder=` — the same idea, for the EC11

Added **2026-08-15**, and for the same reason the touch A/B exists: this harness
had a hard-coded belief about the board that turned out to be false.

A quadrature walk on `GP13`/`GP14` has **no intrinsic handedness**. Which of the
two walks is a physically *clockwise* detent depends on which EC11 terminal
landed on `ENC_A` and which on `ENC_B` — a board fact, exactly like the AHLB
strap. `behavior.cjs` used to assert one answer outright: *the forward walk is
clockwise, therefore it must produce `KC_VOLU`.* Nobody had measured that.

**The owner measured it on the assembled board on 2026-08-15: turning the knob
clockwise produced volume-DOWN.** The firmware was corrected
(`config.h`: `#define ENCODER_DIRECTION_FLIP`, which swaps which walk vial-qmk's
`drivers/encoder/encoder_quadrature.c` calls clockwise), and the harness's
falsified assumption was turned into a switch rather than left standing:

| Mode | "Clockwise" is | Meaning |
|---|---|---|
| `board` *(default)* | the **reversed** GP13/GP14 walk | The as-built `v5_6` A/B landing, measured on hardware. **This is the mode that must pass.** |
| `firmware` | the **forward** walk | What this file asserted before 2026-08-15, i.e. the pre-flip assumption. It describes no board that exists; since the flip it is the arm that fails. |

Both modes assert the **same behavior** — CW must give `KC_VOLU`, CCW must give
`KC_VOLD`. Only the walk that stands for "clockwise" moves, which is the one
thing the board decides. No check was relaxed and the count is still 33.

The two switches are independent and compose, which is itself the proof that
each isolates its own fault. Measured on both current builds:

| `--touch=` | `--encoder=` | checks | failures | which |
|---|---|---|---|---|
| `board` | `board` | 33 | **0 — PASS** | the gate |
| `board` | `firmware` | 33 | 2 | both encoder checks, and only those |
| `firmware` | `board` | 33 | 4 | the four touch checks, byte-identical to the 2026-08-13 table above |
| `firmware` | `firmware` | 33 | 6 | 4 + 2, no interaction |

---

## The defect this harness catches

> **Historical record — everything in this section describes the firmware as it
> shipped BEFORE 2026-08-13.** The board facts are still current; the firmware
> quotes are not (both comments were corrected). Kept verbatim so the failure and
> its evidence stay legible. See [After the fix](#after-the-fix).

**Board truth**, confirmed in four independent places:

* `hardware/pcb/v5_6.kicad_pcb` — footprint `R10`, value `0R`, pads
  `1 → TOUCH_AHLB`, `2 → GND`
* `hardware/pcb/SCHEMATIC-REVIEW.md:156` — *"R10 0 Ω strap AHLB→GND
  (active-high); move to +3V3 for active-low"*
* `hardware/pcb/BOM-FINAL.csv:25` — *"AHLB strap (GND=active-high)"*
* the `R10` symbol's own Description property in `loudest-micro.kicad_sch`

On a TTP223, **AHLB tied low selects active-high output**: `Q` idles LOW and
goes HIGH while the pad is touched.

**Firmware assumption**, which is the opposite:

* `firmware/loudest_micro/config.h:21` — *"The PCB straps the AHLB pad
  active-low, so the pad reads like a normal direct pin (idle high, touched
  low)."*
* `firmware/loudest_micro/keyboard.json:32` — *"PCB straps AHLB active-low so it
  reads like a normal direct pin"*

**And nothing reconciles them.** `MATRIX_INPUT_PRESSED_STATE` is never defined
anywhere in the keyboard tree, so QMK's default applies: a direct pin reading
LOW is *pressed*. There is no inversion in `matrix.c`, none in
`loudest_micro.c` (the only touch-related code there is `touch_enabled`, a
TP_TOG gate, not a polarity flip).

### What that does, as the sim demonstrates

GP16 rests LOW → matrix `[3,2]` is **held from power-on**. `[3,2]` is the
layer-cycle key, `TO(L_CTRL)` on layer 0. So:

```
0b. boot layer — the layer indicator must say layer 0 (BASE)
  ..   layer indicator (chain 13) at boot: 31,23,0
  [FAIL] device booted into layer 0 (indicator is pure red, hue 0)  <- 31,23,0

0c. blast radius — SW1 at the as-booted layer must still be KC_F13
  [FAIL] SW1 emits KC_F13 (0x68) from the as-booted layer  <- no keyboard report at all
  !!   The layer-0 keymap is unreachable: every one of the 12 macro keys, and the
  !!   2U hero key, resolves against L_CTRL instead (RGB/media/JS_MODE), and the
  !!   encoder maps to RGB_MOD rather than volume.

0d. touch polarity — the layer must advance ON TOUCH, not on release
  ..   layer indicator: rest 31,23,0 -> touched 31,23,0 -> released 15,31,0
  [FAIL] the layer advances while the pad is TOUCHED  <- still 31,23,0 while touched
  [FAIL] the layer does NOT advance again when the finger LIFTS  <- ... -> released 15,31,0
  !!   DIAGNOSIS: the layer moved on finger LIFT — the inverted-polarity signature.
```

Three separate user-visible symptoms, all from one strap:

1. **The pad boots into layer 1 (CTRL) and can never reach layer 0 (BASE).**
   `F13`–`F24` — the entire product — are unreachable. Indicator hue 32 (orange)
   at power-on instead of hue 0 (red).
2. **Pressing SW1 emits nothing at all**, because layer 1 puts `JS_MODE` there,
   a custom keycode with no USB report. The encoder becomes `RGB_MOD` instead of
   volume.
3. **Touch fires on finger LIFT, not on touch** — every touch action is off by
   one edge.

### How it was fixed — and one trap that was avoided

**⚠ `MATRIX_INPUT_PRESSED_STATE 1` is NOT the fix.** That define is *global*, not
per-pin: QMK's `readMatrixPin()` applies it to every direct pin
([`quantum/matrix.c:97`](https://github.com/qmk/qmk_firmware/blob/master/quantum/matrix.c)),
so setting it to `1` would invert all 13 mechanical switches — which really are
active-low to GND — and trade one broken key for thirteen.

There were two real options, **alternatives, not both**:

* **Hardware.** Move `R10` from `GND` to `+3V3`. AHLB high selects active-low
  output, which is what the firmware already expected — exactly the escape hatch
  `SCHEMATIC-REVIEW.md:156` documents (*"move to +3V3 for active-low"*). **Not
  available:** the boards are already fabricated *and populated*, so this would
  be a per-unit 0402 rework.
* **Firmware (the one taken, 2026-08-13).** `GP16` was dropped from
  `matrix_pins.direct` (`[3][2] → null`) and is polled in `loudest_micro.c`
  `matrix_scan_kb()` — matrix-scan cadence, 5 ms debounce — with its own
  active-high sense, injecting `action_exec(MAKE_KEYEVENT(3, 2, pressed))` so the
  key keeps its logical position, its keycode, its `TO()` layer chain and its
  `TP_TOG` gate. `keyboard_pre_init_kb()` configures the pin (pull-**down**, so a
  high-Z `U6` reads untouched), because `matrix_init_pins()` no longer sees it.
  Cost: Vial's matrix tester cannot display `[3,2]`, since that reads the scanned
  `matrix[]`.

Both comments that asserted the wrong polarity — `config.h:21` and
`keyboard.json:32` — were corrected in the same change.

---

## After the fix

`--touch=board` — the real hardware polarity — **33/33 on both builds**. This is
the acceptance run; the harness was not modified to produce it.

> **This transcript is the 2026-08-13 acceptance run, kept verbatim as the record
> of the touch fix.** It names `loudest_micro_default.uf2`, which no longer
> exists, and it predates the `--encoder=` A/B, so its summary line has no
> encoder model on it. The current gate is
> `node behavior.cjs --touch=board --encoder=board` against
> `agentpad13_reference.uf2` / `agentpad13.uf2`, and it still reads
> **33 checks, 0 failures** on both.

```
agentpad13 behavioral sim — loudest_micro_default.uf2
loaded 173 UF2 blocks
touch model: BOARD TRUTH — TTP223 AHLB->GND (R10) = active-high, GP16 idles LOW

0. boot + USB enumeration
  [ok] USB configured
  ..   interfaces: #0 cls3/proto1 in1  #1 cls3/proto0 in2/out3
  [ok] ws2812 DMA source buffer located
  ..   pixel buffer @ 0x200020c0 (24 x uint32, GRB in bits 31:8)
  [ok] pixel words carry GRB<<8 (low byte always 0)

0b. boot layer — the layer indicator must say layer 0 (BASE)
  ..   layer indicator (chain 13) at boot: 31,0,0
  [ok] device booted into layer 0 (indicator is pure red, hue 0)

0c. blast radius — SW1 at the as-booted layer must still be KC_F13
  [ok] SW1 emits KC_F13 (0x68) from the as-booted layer

0d. touch polarity — the layer must advance ON TOUCH, not on release
  ..   layer indicator: rest 31,0,0 -> touched 31,23,0 -> released 31,23,0
  [ok] the layer advances while the pad is TOUCHED
  [ok] the layer does NOT advance again when the finger LIFTS
  [ok] touch sends no USB key report (TO() is a layer move)

1. LED chain — 24 positions, one unique color each (raw HID SET_KEY)
  [ok] all 24 chain positions independently addressable
  ..   0-12 per-key: 10,100,200  13,98,195  ...  46,76,140
  ..   13 indicator: 49,74,135
  ..   14-23 underglow: 52,72,130  ...  79,54,85
  [ok] repainting LED 9 alone moves only LED 9
  [ok] LED 9 took the exact requested color 254,2,127

2. CLEAR releases the chain back to the on-device animation
  [ok] no LED is still holding its host-set color
  [ok] chain is live (some LED is lit by the local animation)
  ..   layer-0 indicator (chain 13): 31,0,0
  [ok] layer-0 indicator is pure red (hue 0 = layer 0)

3. every switch — GPIO low -> the keycode the default keymap assigns
  [ok] GP12 SW1  [0,0] -> KC_F13 (0x68) then release
  [ok] GP 9 SW2  [0,1] -> KC_F14 (0x69) then release
  [ok] GP 5 SW3  [0,2] -> KC_F15 (0x6a) then release
  [ok] GP 2 SW4  [0,3] -> KC_F16 (0x6b) then release
  [ok] GP11 SW5  [1,0] -> KC_F17 (0x6c) then release
  [ok] GP 8 SW6  [1,1] -> KC_F18 (0x6d) then release
  [ok] GP 4 SW7  [1,2] -> KC_F19 (0x6e) then release
  [ok] GP 1 SW8  [1,3] -> KC_F20 (0x6f) then release
  [ok] GP10 SW9  [2,0] -> KC_F21 (0x70) then release
  [ok] GP 7 SW10 [2,1] -> KC_F22 (0x71) then release
  [ok] GP 3 SW11 [2,2] -> KC_F23 (0x72) then release
  [ok] GP 0 SW12 [2,3] -> KC_F24 (0x73) then release
  [ok] GP 6 SW13 [3,0] 2U hero -> KC_MPLY (consumer 0xcd)
  [ok] GP15 ENC_SW [3,1] push -> KC_MUTE (consumer 0xe2)

4. EC11 encoder — quadrature on GP13/GP14, layer 0 maps to volume
  [ok] rotate CW -> KC_VOLU (consumer 0xe9)
  [ok] rotate CCW -> KC_VOLD (consumer 0xea)

5. analog joystick — ADC injection -> HID gamepad report (report id 0x07)
  ..   rest                   report (none)  axes=n/a
  ..   ADC0 high / ADC1 low   report 071afee801  axes=-486,488
  ..   ADC0 low / ADC1 high   report 07e8011afe  axes=488,-486
  [ok] joystick emits HID gamepad reports at all
  [ok] both axes swing to near full scale on a full ADC sweep
  [ok] the two axes move independently (swapping the ADC inputs flips both signs)
  ..   ADC channels the emulator serviced: [1,0]
  ..   axis IDENTITY (which report slot is X) is NOT decided by this run.

touch model: board   checks: 33   failures: 0
BEHAVIOR SIM: PASS
```

`loudest_micro_vial.uf2` produces the identical 33/33, with the pixel buffer at a
different address — which is exactly why the buffer address is **discovered at
runtime** rather than hardcoded. The default image grew by one 512-byte UF2 block
(172 → 173) for the out-of-matrix touch handling.

The sibling smoke test `firmware/tests/emulator/runner.cjs` carried the same
wrong idle-level assumption (it drove GP16 high with the switch lines and
asserted a pull-up on it) and was corrected to board truth in the same change; it
now fails on the pre-fix binaries and passes on the current ones.

---

## How the LED readback works

QMK's RP2040 `vendor` ws2812 driver hands its pixel array to a DMA channel that
feeds **PIO0's TX FIFO** (`PIO0_BASE + TXF0 = 0x50200010`). The harness watches
every DMA channel start; the lowest read address of whichever channel targets
`TXF0` *is* the pixel buffer, by definition. Nothing is hardcoded, so a rebuild
that moves the buffer does not break the test.

Each entry is one `uint32` carrying **GRB in bits 31:8** — the state machine
runs autopull with `PULL_THRESH = 24`, MSB first, so the low byte is always
zero. The harness asserts that invariant structurally; if a future QMK changes
the packing, the run fails loudly instead of printing plausible nonsense.

So the colors printed above are **the exact words the PIO shifts onto GP17** —
one hop short of the wire.

The chain-index proof is the important part: `SET_KEY(i, r, g, b)` was sent for
every `i` in `0..23` with a distinct color, and every one landed at chain
position `i` with the exact bytes requested. Then LED 9 alone was repainted and
**only** LED 9 moved. That is what "individually addressable" means, and it is
now demonstrated on the shipping binary rather than assumed.

---

## What this cannot tell you

Read this before treating a PASS as permission to skip bring-up.

### Not simulated at all — only real hardware can answer

* **WS2812/SK6812 bit timing on the wire.** The emulator is *not cycle-faithful*
  (the PIO is stepped from the harness loop because `RPPIO.run()` self-schedules
  via `setTimeout`, and its `CLKDIV` is parsed but never used to pace
  execution — [rp2040js PR #117](https://github.com/wokwi/rp2040js/pull/117) was
  closed unmerged). We validate the *data*, never the `T0H`/`T1H` pulse widths.
* **The SN74LVC1T45 level shifter, the 5 V rail, and the LED chain itself.**
  We stop at GP17. Whether LED 7 is physically wired seventh is a hardware fact.
* **Whether the touch pad works as a sensor.** We model GP16's *logic level*
  from the strap. Pad sensitivity through the case, C25 tuning, and false
  triggering are unanswerable without the board.
* **Encoder detent direction — *was* unanswerable here, and it bit us.** This
  bullet used to read *"we prove a CW quadrature walk produces `KC_VOLU`;
  whether turning the physical knob clockwise produces the CW walk depends on
  which way A and B are soldered"* — correctly identifying the gap, while the
  harness went on asserting one side of it anyway. The owner measured the real
  board on **2026-08-15** (clockwise gave volume-DOWN), the firmware got
  `ENCODER_DIRECTION_FLIP`, and the assumption became the `--encoder=` A/B
  above. The emulator still cannot tell you which walk your knob makes; it can
  now tell you which walk this *board* makes, because a human measured it once.
* **Joystick axis direction.** Which way the gimbal drives each wiper is
  mechanical and is still not answerable here — see `firmware/POLARITY-NOTE.md`.
  (Calibration itself is no longer in this list: see the next bullet.)
* **EEPROM / Vial persistence — no longer out of reach.** rp2040js's SSI
  peripheral is a stub and flash writes do not work in stock rp2040js
  ([#157](https://github.com/wokwi/rp2040js/issues/157)), and its `IO_QSPI` is
  an `UnimplementedPeripheral` whose `0xffffffff` reads make QMK's wear-levelling
  driver believe every flash access was aborted — so an EEPROM write used to be
  a silent no-op. `joystick.cjs` attaches a small serial-NOR model to the SSI
  (workaround **(g)** below) and therefore **does** exercise QMK's emulated
  EEPROM: it stores a calibration, restarts the emulated MCU carrying only the
  flash image, and reads the values back. Its `--no-eeprom` arm removes the model
  and must fail on exactly those checks. What is still out of reach is Vial's own
  dynamic-keymap persistence, which nothing here drives.
* **Anything electrical:** USB timing margins, inrush, the 500 mA budget,
  brownout, ESD, thermals.

### Simulated but NOT trustworthy

* **Joystick axis identity.** The run shows ADC0 (GP26, declared `x`) landing in
  the *second* report slot and ADC1 (GP27, declared `y`) in the *first*. **Do
  not read that as an axis swap in the firmware.** rp2040js's round-robin
  channel selector has a real masking bug — `adc.ts` writes
  `(channel & CS_AINSEL_SHIFT)` where `CS_AINSEL_SHIFT` is `12`, when it means
  `(channel & CS_AINSEL_MASK)` with mask `0x7`; that is the root cause of open
  issue [#141](https://github.com/wokwi/rp2040js/issues/141) *("only ADC0 (pin
  26) reads successfully")*. The harness prints the channel order the emulator
  actually serviced so the artifact is visible. The *magnitudes* are sound:
  12-bit `4000` → QMK's 10-bit `1000` → `+488`, and `100` → `25` → `-486`, both
  correct against `rest = 512`.
* **USB config descriptor completeness.** Continuation packets of a multi-packet
  control IN transfer never arrive, so the 91-byte configuration descriptor
  truncates at 64. The boot-keyboard and raw-HID interfaces are complete within
  that first packet; the third (shared: NKRO / consumer / joystick) interface is
  not, so the harness identifies its endpoint from observed traffic instead. A
  descriptor defect in those last 27 bytes would not be caught.
* **Timing-dependent behavior generally** — debounce windows, tap-hold terms,
  `RGB_MATRIX` frame rate. Simulated time is not wall time.

### Emulator workarounds in force

Seven rp2040js fidelity issues are worked around **in the harness, never in the
firmware**, each commented at its site.

**(a)–(e), in both harnesses** (the first four match
`firmware/tests/emulator/runner.cjs`): the ADC `FIFO_REG` interrupt latch,
unimplemented DMA `CHAN_ABORT` reads, DREQ latches that only update on FIFO
transitions, `chan.start()` ignoring an already-asserted DREQ, and the PIO's
`setTimeout` self-scheduling. Pull-ups are also not folded into `inputValue`
([#154](https://github.com/wokwi/rp2040js/issues/154)), so idle-high lines are
driven high explicitly — **and GP16 is driven from the polarity model rather
than assumed, which is precisely what let this harness catch the strap bug.**

**(f) and (g), in `joystick.cjs` only, and both switchable** — a workaround that
cannot be switched off cannot be audited:

* **(f) `ADC.CS.START_ONCE` is self-clearing on silicon and not in rp2040js.**
  ChibiOS's RP ADC LLD sets the channel with a read-modify-write of `CS`, so the
  stale bit is written back and kicks off a second conversion; every
  `adcConvert()` then returns the previous conversion's value. Switch it off
  with `--no-adc-fix` and the board reports `live X=200 Y=800` for an injected
  `800/200` — the swap signature of a strict one-sample lag. **Measured, 2 of 48
  checks fail, and only the live-ADC ones.**
* **(g) flash writes do not work in stock rp2040js.** The SSI peripheral is a
  stub that discards `DR0` writes and always reports `RXFLR = 0`, and `IO_QSPI`
  is an `UnimplementedPeripheral` returning `0xffffffff` — which QMK's
  wear-levelling driver reads as *"flash access aborted"*, so its write loops
  bail out and the EEPROM silently never changes. `joystick.cjs` attaches a
  byte-level serial-NOR model (WREN / page-program / sector- and block-erase /
  read-status) to the SSI and a real register file to `IO_QSPI`, so writes land
  in the same `flash` array the XIP read path already serves. Two things had to
  be measured rather than guessed to make it work: the FIFO must answer even
  while CS is **high** (the bootrom's `flash_exit_xip()` clocks dummy bursts
  through the same loop, and the loop's only other exit was the now-honest abort
  flag — boot hangs in ROM at `0x1784` otherwise), and the FIFO must be cleared
  at **both** CS edges (boot2, re-run from RAM after every program, leaves bytes
  behind; without the clear exactly five EEPROM writes succeed and the sixth
  hangs). Switch it off with `--no-eeprom`: **5 of 48 checks fail, and only the
  persistence ones.**

---

## Why this and not Wokwi

The v4 plan called for "a Wokwi sim of the real UF2". Wokwi **cannot do the
important half of that job**, and this harness can, because it uses Wokwi's own
emulator engine directly instead of Wokwi's product.

Wokwi accepts a pre-built RP2040 `.uf2` and has a real headless CLI, and its
RP2040 model does cover GPIO, PIO, DMA-for-PIO, and ADC on GP26/GP27
([docs.wokwi.com/parts/wokwi-pi-pico](https://docs.wokwi.com/parts/wokwi-pi-pico),
[docs.wokwi.com/vscode/project-config](https://docs.wokwi.com/vscode/project-config)).
But:

* **Its USB is CDC-serial only — HID is not implemented.** The Pico support
  matrix says so, and the request to observe HID traffic
  ([wokwi-features#306](https://github.com/wokwi/wokwi-features/issues/306)) has
  been open with zero votes since February 2022. For a *keyboard*, that removes
  the entire point: no keycodes, no layers, no Raw HID / VIA.
* **No scenario verb sets a GPIO**; each switch must be modelled as a
  `wokwi-pushbutton` part. The rotary encoder part (`wokwi-ky-040`) has **no**
  automation control at all, and **no TTP223 part exists** — so the very defect
  above would have been unreachable.
* **Per-LED colors are only readable as a rendered PNG** (`take-screenshot` on
  the NeoPixel part), not as an RGB array.
* It is **cloud-only** — firmware is uploaded to Wokwi's servers — needs an
  account and a `WOKWI_CLI_TOKEN`, allows 50 simulation-minutes/month on the
  free tier, and its scenario API is self-described as alpha
  ([docs.wokwi.com/wokwi-ci/getting-started](https://docs.wokwi.com/wokwi-ci/getting-started)).

Wokwi's engine is the MIT-licensed [`rp2040js`](https://github.com/wokwi/rp2040js),
which exposes raw USB device hooks (`onEndpointWrite`, `onEndpointRead`,
`sendSetupPacket`) that the Wokwi product does not surface. Using the library
directly gives HID observation, direct GPIO injection, direct ADC injection,
and exact per-LED bytes — offline, free, in ~35 seconds.

**The Wokwi item on the v4 plan should be considered closed by this directory,
not still outstanding.**

---

## Files

| File | What it is |
|---|---|
| `behavior.cjs` | The behavioral harness. Reuses `../tests/emulator/node_modules` + `bootrom.cjs`. Two A/B switches, `--touch=` and `--encoder=`, both defaulting to board truth. |
| `joystick.cjs` | Added 2026-08-15. Referee for the **protocol-v1 calibration commands** on the same shipped `.uf2`s: `0x50` framing and live ADC, `0x51` acceptance with `floor(60%)` threshold derivation and the SRAM gamepad rescale, every `0x51` rejection class (out-of-range, `min ≥ rest`, `rest ≥ max`, the 99-vs-100 half-swing boundary, a truncated frame) each proven to write **nothing**, `0x52`, CAPS reporting version 1, and **EEPROM persistence across a simulated power cycle**. A/B arms `--no-eeprom` and `--no-adc-fix` must FAIL. **Section 10, added later on 2026-08-15, drives the whole SW14 ON-BOARD routine** with no host at all — the button is presented on `qspi[1]`, the stick is swept through the ADC, and the board arms, centres, tracks its envelope, validates, derives and stores entirely by itself; it then asserts the resulting EEPROM image is **byte-identical** to pushing the same six numbers over `0x51`, and that a failed run (half-swing under the contract's minimum) writes **nothing at all**. It also times the interrupts-disabled window inside `sw14_pressed()`. **62 checks.** |
| `package.json` | Convenience scripts only — no dependencies of its own. |

*(`calibrate.cjs` lived here from 2026-08-13 to 2026-08-15. It refereed the
separate bring-up firmware `loudest_micro_calibrate.uf2` by decoding the text
that firmware **typed** over HID. That keymap, its UF2 and this referee are all
deleted; `joystick.cjs` is not its successor in kind — it tests the EEPROM
store and the wire protocol, which is where the calibration actually lives now.)*

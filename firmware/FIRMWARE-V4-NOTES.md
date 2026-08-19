# FIRMWARE-V4-NOTES — agentpad13 Rev A firmware wave (board v4_r27)

Ledger for the firmware wave that brought `firmware/` from the pre-v4 scaffold
pin map to the shipped Rev A board. Every change below cites its authority.
Pin authority throughout: **`hardware/pcb/v4/ORDER-READINESS.md` Layer 4** —
the definitive 30-GPIO table for `hardware/pcb/v4/v4_r27.kicad_pcb`, extracted
twice from the final board (netlist + pcbnew copper read, identical on all 57
U1 pads).

Build inputs for the shipped artifacts: vial-qmk `vial` branch commit
`00fc4627` + `patches/0001-via-command-kb-backport.patch`, Arm GNU Toolchain
15.2.Rel1, QMK CLI 1.2.0 (full recipe: `BUILD.md`).

---

## 1. Pin-map regeneration (old scaffold GPIO → Rev A GPIO)

The scaffold wired SW1–SW13 to GP0–GP12 in order. Rev A routing remapped the
13 switch lines x-monotonically (ORDER-READINESS §4a: ledger cross-check
13/13, "0 surprises"). Logical `[row][col]` positions — and therefore both
keymaps, the Vial layout, bootmagic `[0,0]`, and the LED chain→matrix
associations — are **semantically unchanged**; only `matrix_pins.direct` in
`loudest_micro/keyboard.json` changed.

| Function | Matrix | Old GPIO | New GPIO | Authority (U1 pad → net) |
|---|---|---|---|---|
| SW1 | [0,0] | GP0 | **GP12** | pad 15 → SW1 |
| SW2 | [0,1] | GP1 | **GP9** | pad 12 → SW2 |
| SW3 | [0,2] | GP2 | **GP5** | pad 7 → SW3 |
| SW4 | [0,3] | GP3 | **GP2** | pad 4 → SW4 |
| SW5 | [1,0] | GP4 | **GP11** | pad 14 → SW5 |
| SW6 | [1,1] | GP5 | **GP8** | pad 11 → SW6 |
| SW7 | [1,2] | GP6 | **GP4** | pad 6 → SW7 |
| SW8 | [1,3] | GP7 | **GP1** | pad 3 → SW8 |
| SW9 | [2,0] | GP8 | **GP10** | pad 13 → SW9 |
| SW10 | [2,1] | GP9 | **GP7** | pad 9 → SW10 |
| SW11 | [2,2] | GP10 | **GP3** | pad 5 → SW11 |
| SW12 | [2,3] | GP11 | **GP0** | pad 2 → SW12 |
| SW13 (2U) | [3,0] | GP12 | **GP6** | pad 8 → SW13 |
| Encoder push (ENC_SW) | [3,1] | GP15 | GP15 (unchanged) | pad 18 → ENC_SW |
| Touch (TOUCH_OUT) | [3,2] | GP16 | GP16 (unchanged) | pad 27 → TOUCH_OUT |
| Encoder A / B | — | GP13 / GP14 | GP13 / GP14 (unchanged) | pads 16/17 → ENC_A/ENC_B |
| WS2812 data (RGB_MCU) | — | GP17 | GP17 (unchanged) | pad 28 → RGB_MCU |
| Joystick X / Y | — | GP26 / GP27 | GP26 / GP27 (unchanged) | pads 38/39 → JOY_X_ADC (ADC0) / JOY_Y_ADC (ADC1) |

Net delta: **13 switch pins remapped; every other pin confirmed unchanged.**

Spares deliberately absent from firmware: GP18/GP19 (I2C1 → DNP J2), GP20
(J2.5), GP28 (J2.7, ADC-capable), and the J2 net *named* "GP21" which is
silicon **GPIO24** (ORDER-READINESS Layer 4 call-out: "the J2 spare net names
GP20/GP21/GP28 must not be read as GPIO numbers"). A repo-wide grep confirmed
the firmware tree never referenced GP18–GP25/GP28/GP29 in any form, so the
trap had no firmware footprint; `check_pins_v4.py` now guards it permanently.

### rgb_matrix.layout coordinate regeneration (same file)

The LED chain order was already correct (chain 0–12 = LED1–13 per-key under
SW1–13, 13 = LED14 layer indicator, 14–23 = LED15–24 underglow — matches the
board's verified chain U5.B → RGB_D00 → LED1 … LED14 → RGB_D14 → LED15 …
LED24, ORDER-READINESS Layer 2). The x/y coordinates, however, dated from a
pre-v4 outline (84.2×103.7, underglow "provisional until PCB routing").
`gen_led_layout.py` was rewritten to read the **actual LED centroids and
Edge.Cuts outline from `v4_r27.kicad_pcb`** (84.2×100.0) and emit the QMK
224×64 layout; `keyboard.json` now carries the generated values (cosmetic —
affects RGB animation geometry only, not the protocol's chain indexing).

> **Superseded 2026-08-15 — the transform is now ISOTROPIC** (finding 7 of the
> firmware-verification pass). The mapping described above normalised each axis
> independently to the bbox, i.e. x·224/84.2 = 2.660 units/mm against
> y·64/100.0 = 0.640 units/mm — a 4.16:1 distortion that visibly skews the four
> geometry-bearing animations enabled here. `gen_led_layout.py` now applies
> **one** scale to both axes (`s = 64/bbox_height` = 0.640 u/mm) and centers x
> on **112**, QMK's default effect center (`k_rgb_matrix_center`,
> `quantum/rgb_matrix/rgb_matrix.c:32`), so no `RGB_MATRIX_CENTER` override is
> required. Every `y`, `flags` and `matrix` value is unchanged; only `x` moved,
> on 23 of the 24 entries (LED13 is the bbox center and was already 112). The
> LED cloud now spans x 88–136, y 3–62. Still cosmetic: chain indexing, and
> therefore the protocol, is untouched. Re-run the generator against
> `v5/hardware/pcb/v5_6.kicad_pcb`, not `v4_r27.kicad_pcb`.

### Other keyboard.json changes

* `usb.device_version` 0.0.1 → **1.0.0** (Rev A production build). VID/PID
  unchanged (`0xFEED`/`0x4C4D` — locked with `daemon/loudestd/protocol.py`).
* Provenance comments now cite `hardware/pcb/v4/ORDER-READINESS.md` instead of
  a pre-v4 internal design note.

## 2. Product rebrand → agentpad13

User-visible identity strings renamed to **"agentpad13"** (from the legacy internal project name):
`keyboard_name` (USB product string) and top-level comments in
`keyboard.json`, `name` in `keymaps/vial/vial.json` (Vial sidebar), the
`readme.md` heading and body, `BUILD.md`, and all C file header comments.
`maintainer`/`url` now point at the public repo (`yuz207`,
`github.com/yuz207/agentpad13`).

**Kept (judgment call, per the QMK-churn allowance):** the QMK keyboard/
module name `loudest_micro` — the directory name, `loudest_micro.c/.h`, the
`qmk compile -kb loudest_micro` target, and the derived
`prebuilt/loudest_micro_*.uf2` artifact names. Renaming would churn every QMK
build path and orphan the read-only daemon's references (e.g.
`daemon/loudestd/protocol.py` cites `firmware/loudest_micro/keyboard.json`).
Rationale is stated for strangers in `loudest_micro/readme.md`. Also kept:
`manufacturer: "Open Hardware"` and the `LOUDEST_*`/`loudest_*` C identifiers
(internal API shared with the loudestd contract).

Hygiene sweep on all touched files: no personal paths, no internal repo
name, no internal process/spec references (grep for those literals over
`firmware/` returns zero hits); internal spec-section citations were replaced
with self-contained comments.

## 3. VIA-shadow fix (vial build now runs the full protocol)

**Problem (previously documented as a known issue):** under VIA/Vial,
`quantum/via.c` owns `raw_hid_receive()` and its switch consumes command IDs
0x01–0x04 before the `raw_hid_receive_kb()` fallback — exactly the four
LOCKED protocol IDs — so the vial build only received frames VIA happened to
ignore (CLEAR, and SET_LAYER 0/4–7 via inner-switch defaults).

**Fix, per upstream QMK practice:** upstream QMK's `via_command_kb()`
pre-hook is the official mechanism for keyboard-level raw-HID interception
alongside VIA; the vial-qmk fork at the pinned commit predates it.
`patches/0001-via-command-kb-backport.patch` (23 lines: weak default +
declaration + one pre-hook call in `raw_hid_receive()`, inserted after Vial's
unlock gate to preserve its restricted-command window) backports it, and
`loudest_micro.c` implements the hook as a byte-content dispatcher. The wire
format itself is untouched — `daemon/loudestd/protocol.py` v0 remains the
locked single source of truth and the daemon needs no changes.

**Dispatch rules** were derived from evidence, not guesswork — the Vial GUI
source (`vial-gui` `src/main/python/protocol/keyboard_comm.py` +
`editor/matrix_test.py`, fetched this wave) shows the GUI sends: 0x01 with
all-zero payload (connect handshake), 0x02 only with value ids 0x02
(layout_options, connect) and 0x03 (switch_matrix_state, matrix-tester poll),
0x03 only with nonzero value ids, and **never** per-key 0x04 get_keycode
(keymaps are bulk-read via 0x12). Resulting dispositions for the three
byte-identical collisions (full table in `BUILD.md` §6):

* `01 00…00` → VIA (protects the GUI handshake; costs only "SET_KEY 0 to
  black-solid" in the vial build — CLEAR or rgb≥1 expresses the same intent).
* `02 0n 00…`, n∈{1,2,3} → VIA (protects uptime/layout-options/matrix-tester;
  costs host-side SET_LAYER to layers 1–3 in the vial build only — layers
  0/4–7 work, the default build has the full range, and layers 1–3 remain
  reachable on-device via touch or the Vial GUI).
* `04 nn 00…` → loudest PING (essential for the daemon handshake; costs
  per-key `get_keycode(n,0,0)` for *legacy* VIA clients only — the Vial GUI
  never sends it).

The **default** (non-VIA) build owns `raw_hid_receive()` and is
exception-free, exactly as before.

## 4. Validation

### 4a. Static pin checker (MANDATORY) — PASS, verbatim

`firmware/check_pins_v4.py` embeds the ORDER-READINESS Layer 4 table and
asserts (a) `keyboard.json`, (b) the resolved build config from
`qmk info -kb loudest_micro -f json`, (c) a source-scan for stray/forbidden
GPIOs, and (d) that the vial-qmk tree carries the §3 patch. Output of the
shipping run (51 checks):

```
agentpad13 Rev A pin-map check (authority: hardware/pcb/v4/ORDER-READINESS.md Layer 4, board v4_r27)
-- keyboard.json
  [ok] keyboard.json: matrix is 4 rows x 4 cols
  [ok] keyboard.json: [0,0] SW1 = GP12
  [ok] keyboard.json: [0,1] SW2 = GP9
  [ok] keyboard.json: [0,2] SW3 = GP5
  [ok] keyboard.json: [0,3] SW4 = GP2
  [ok] keyboard.json: [1,0] SW5 = GP11
  [ok] keyboard.json: [1,1] SW6 = GP8
  [ok] keyboard.json: [1,2] SW7 = GP4
  [ok] keyboard.json: [1,3] SW8 = GP1
  [ok] keyboard.json: [2,0] SW9 = GP10
  [ok] keyboard.json: [2,1] SW10 = GP7
  [ok] keyboard.json: [2,2] SW11 = GP3
  [ok] keyboard.json: [2,3] SW12 = GP0
  [ok] keyboard.json: [3,0] SW13 = GP6
  [ok] keyboard.json: [3,1] ENC_SW = GP15
  [ok] keyboard.json: [3,2] TOUCH_OUT = GP16
  [ok] keyboard.json: [3,3] unused = null
  [ok] keyboard.json: encoder pin_a ENC_A = GP13
  [ok] keyboard.json: encoder pin_b ENC_B = GP14
  [ok] keyboard.json: ws2812 pin RGB_MCU = GP17
  [ok] keyboard.json: joystick x JOY_X_ADC = GP26
  [ok] keyboard.json: joystick y JOY_Y_ADC = GP27
  [ok] keyboard.json: no spare/NC GPIO in configuration values (GP18-25/28/29)
-- source scan
  [ok] sources reference only table-assigned pins (['GP16', 'GP26', 'GP27'])
  [ok] sources reference no forbidden pin (incl. the GP21=GPIO24 net-name trap)
-- qmk info (agentpad13_qmk_info.json)
  [ok] qmk info (agentpad13_qmk_info.json): matrix is 4 rows x 4 cols
  [ok] qmk info (agentpad13_qmk_info.json): [0,0] SW1 = GP12
  [ok] qmk info (agentpad13_qmk_info.json): [0,1] SW2 = GP9
  [ok] qmk info (agentpad13_qmk_info.json): [0,2] SW3 = GP5
  [ok] qmk info (agentpad13_qmk_info.json): [0,3] SW4 = GP2
  [ok] qmk info (agentpad13_qmk_info.json): [1,0] SW5 = GP11
  [ok] qmk info (agentpad13_qmk_info.json): [1,1] SW6 = GP8
  [ok] qmk info (agentpad13_qmk_info.json): [1,2] SW7 = GP4
  [ok] qmk info (agentpad13_qmk_info.json): [1,3] SW8 = GP1
  [ok] qmk info (agentpad13_qmk_info.json): [2,0] SW9 = GP10
  [ok] qmk info (agentpad13_qmk_info.json): [2,1] SW10 = GP7
  [ok] qmk info (agentpad13_qmk_info.json): [2,2] SW11 = GP3
  [ok] qmk info (agentpad13_qmk_info.json): [2,3] SW12 = GP0
  [ok] qmk info (agentpad13_qmk_info.json): [3,0] SW13 = GP6
  [ok] qmk info (agentpad13_qmk_info.json): [3,1] ENC_SW = GP15
  [ok] qmk info (agentpad13_qmk_info.json): [3,2] TOUCH_OUT = GP16
  [ok] qmk info (agentpad13_qmk_info.json): [3,3] unused = null
  [ok] qmk info (agentpad13_qmk_info.json): encoder pin_a ENC_A = GP13
  [ok] qmk info (agentpad13_qmk_info.json): encoder pin_b ENC_B = GP14
  [ok] qmk info (agentpad13_qmk_info.json): ws2812 pin RGB_MCU = GP17
  [ok] qmk info (agentpad13_qmk_info.json): joystick x JOY_X_ADC = GP26
  [ok] qmk info (agentpad13_qmk_info.json): joystick y JOY_Y_ADC = GP27
  [ok] qmk info (agentpad13_qmk_info.json): no spare/NC GPIO in configuration values (GP18-25/28/29)
-- resolved build config extras
  [ok] qmk info: WS2812_DI_PIN resolves from ws2812.pin
  [ok] qmk info: processor is RP2040
-- vial-qmk tree
  [ok] vial-qmk quantum/via.c carries the via_command_kb backport (patches/0001-via-command-kb-backport.patch)

PASS: all 51 pin-map checks against the ORDER-READINESS Layer 4 table succeeded
```

(One checker self-fix during development is worth recording: the
forbidden-GPIO sweep initially flagged the *documentation comments* that
explain why the spare pins are unused; the sweep now strips `$`-comment keys
and checks configuration values only — the check's actual intent.)

### 4b. Protocol-v0 conformance — PASS (80/80)

`firmware/tests/conformance/run_conformance.py` compiles the **real**
`loudest_micro.c` on the host (stub QMK headers) in both build flavors and
drives it with frames built by `daemon/loudestd/protocol.py` (the locked
oracle), asserting among others: CAPS replies byte-for-byte equal to
`build_caps()` and parseable by the daemon's own `parse_caps()`; all 24
SET_KEY indices and 3 effects claimed and stored; SET_LAYER dispatch exactly
per §3; every observed VIA/Vial client frame left untouched; malformed frames
rejected. Final line, verbatim:

```
PASS: all 80 protocol-v0 conformance checks passed (firmware C handler vs daemon/loudestd/protocol.py oracle)
```

The daemon's own reference suite was run for cross-evidence:
`daemon/tests/test_protocol.py` → **45 passed**; full daemon suite →
**131 passed** (pytest, plugin autoload disabled to sidestep an unrelated
NumPy-2.0-incompatible host plugin).

### 4c. QMK lint

`qmk lint -kb loudest_micro -km default --strict` → `Lint check passed!`
(`-km vial` trips mainline's "keymap vial should not exist" false positive,
as documented in `BUILD.md` §3.1.)

### 4d. Emulator smoke test of the shipped UF2s (rp2040js) — PASS, both builds

`firmware/tests/emulator/` boots the **production UF2s** headlessly in
[rp2040js] 1.3.3 (`./get-bootrom.sh && npm install && npm run smoke:default
&& npm run smoke:vial`) and asserts, against the ORDER-READINESS table:

1. full USB enumeration (device descriptor shows VID `0xFEED` / PID `0x4C4D`
   / bcdDevice 1.00; interfaces: boot keyboard EP1-IN, raw HID EP2-IN/EP3-OUT);
2. post-boot pin muxing — all 17 matrix/encoder/touch GPIOs on SIO with
   pull-ups, GP17 claimed by PIO (ws2812 vendor driver), GP26/GP27 handed to
   the ADC, and **every spare/NC pin (GP18–25/28/29) untouched**;
3. WS2812 data edges observed on GP17;
4. key scan through real USB: driving **GP12 (SW1) low produces the boot
   keyboard report `0000680000000000` (0x68 = F13, the [0,0] keymap entry)**
   and release produces the empty report — the remapped pin → logical key →
   USB report path proven end-to-end on the shipped binary;
5. raw HID on-target: a PING frame delivered on EP3 returns
   `04424c440018081f00…` on EP2 — **byte-exact vs `protocol.build_caps()`**.

Final lines, verbatim, from the shipped harness location:

```
EMULATOR SMOKE: PASS        (loudest_micro_default.uf2)
EMULATOR SMOKE: PASS        (loudest_micro_vial.uf2)
```

*(Artifact names as of 2026-08-15: `agentpad13_reference.uf2` and
`agentpad13.uf2` respectively — see §5. The expected CAPS literal in
`firmware/tests/emulator/package.json` also moved with protocol v1: byte 4 is
now `01`, so the string is `04424c440118081f00…`, not `…0018081f…` as quoted
just above.)*

The vial-build PASS on check 5 is the artifact-level proof that the §3
`via_command_kb` backport is live in the shipped `.uf2`: an unpatched VIA
would consume the 0x04 frame itself and echo a keycode reply, not the
`'L','D'` CAPS (LTO inlines the handler, so symbol inspection cannot show
this — the behavioral test can).

**Honest scope notes (all workarounds live in the harness, none in the
firmware):** rp2040js is built/tested against the pico-sdk/TinyUSB stack, and
running the ChibiOS/QMK stack surfaced four emulator-fidelity issues that the
harness works around, each documented in `runner.cjs`: (a) ADC `FIFO_REG`
reads never re-evaluate the IRQ line → ADC-FIFO interrupt storm (fix: recheck
interrupts after FIFO reads); (b) DMA `CHAN_ABORT` reads are unimplemented
(return `0xffffffff`) → the ws2812 driver's abort-poll spins forever (fix:
read as 0); (c) DREQ latches only update on FIFO-level *transitions* and
`chan.start()` ignores an already-asserted DREQ → DREQ-paced DMA deadlocks
(fix: initial nudge + start-kick); (d) the PIO run loop self-schedules via
JS `setTimeout`, which never fires inside a synchronous simulation loop
(fix: step the PIO from the harness loop). Additionally the host-side USB
shim paces SET_ADDRESS after bus reset and tolerates a truncated multi-packet
config-descriptor read (the two interfaces under test are fully described in
the first 64-byte packet). Emulator timing is therefore not cycle-faithful —
WS2812 bit timing, ADC readings, and USB timing margins are NOT validated
here; that is what first-power-on hardware bring-up is for.

[rp2040js]: https://github.com/wokwi/rp2040js

## 5. Rebuilt artifacts (firmware/prebuilt/)

| File | built from | SHA-256 |
|---|---|---|
| `agentpad13.uf2` (109568 bytes) | `-km vial` | `fa5b5df04274a389902984a57f8fdad8e5cc66c9f6e142056eedeaa8a2cb68f2` |
| `agentpad13_reference.uf2` (93696 bytes) | `-km default` | `1c8b9d5a716f24373477fd2368df1e41a122242d406c2adb332f4e12cd24a212` |

md5, for the drag-and-drop check: `agentpad13.uf2`
`a7b8da85a7d3f0de96b983be8c782ba2`, `agentpad13_reference.uf2`
`4caac0bca0cafb1d3ebf7d46dd9e7adb`.

**Rebuilt 2026-08-15 for on-board (SW14) joystick calibration**, superseding the
first v1 pair (`agentpad13.uf2` md5 `cce79a07…` / 107008 B,
`agentpad13_reference.uf2` md5 `34fa434b…` / 90624 B). Growth is +2560 B (vial)
and +3072 B (default): the SW14 reader, the calibration state machine and its
LED display. The reproducibility split below was re-confirmed on this pair —
`agentpad13_reference.uf2` rebuilt to `4caac0bc…` identically across repeated
builds including a comment-only source edit, while two consecutive `-km vial`
builds with **no source change at all** produced `8eb56943…` then `a7b8da85…`.

Built from the exact tree in this commit + vial-qmk `00fc4627` + the §3
patch, Arm GNU Toolchain 15.2.Rel1, zero warnings (`-Werror`).
`agentpad13_reference.uf2` reproduced byte-for-byte across **three** clean
builds (`.build/` wiped between each); `agentpad13.uf2` records shipped bytes
only — the vial link is non-deterministic run-to-run.

> **Superseded 2026-08-13 — TTP223 touch-polarity fix.** The table above is the
> current shipped pair. It replaces the Rev-A binaries
> `loudest_micro_default.uf2` (88064 B,
> `49642d69a53aef4308cb03a1d3e1b3c73c18d54946c6350adecfca47202ce39a`, md5
> `4af788ae…`) and `loudest_micro_vial.uf2` (104448 B,
> `5d33fffc57807bfdda263f36f919139e157b6b3cadccc0edc3fb06601f948fd0`, md5
> `e5008942…`), which shipped a permanently-pressed matrix `[3,2]` because the
> board straps the TTP223 `AHLB → GND` (**active-high**) while `config.h` and
> `keyboard.json` asserted active-low. GP16 is now polled outside the direct-pin
> matrix with its own sense (`loudest_micro.c`), so the default image grew by one
> 512-byte UF2 block. Gate: `firmware/sim/behavior.cjs --touch=board` **33/33
> PASS** on both builds (it was 4 failures before). Note the **vial** build is
> non-deterministic run-to-run; only the default UF2 hash is reproducible.

> **Superseded 2026-08-15 — isotropic RGB layout + `housekeeping_task_user()`
> de-duplication.** The table above is the current shipped set. It replaces the
> 2026-08-13 touch-fix binaries `loudest_micro_default.uf2` (88576 B,
> `35f34ea4f229eb65f0b3d9ad8d9cc0444a399af2c5943a25c06131d58b0f2ad3`, md5
> `cf5bd628…`), `loudest_micro_vial.uf2` (104448 B,
> `7056e6ad0ebe9673f077f69fb6d32873fbcf0cdd233e78d163ef940254f814c5`, md5
> `b31673a7…`) and `loudest_micro_calibrate.uf2` (96768 B,
> `7230a4de95851909f78893def51d49bcda68ff34670934495eabf760a31a61e7`, md5
> `a81ce4a1…`). Two changes, both above: (1) `rgb_matrix.layout` regenerated
> under the isotropic transform (finding 7 — see §1's superseded note; `x` only,
> 23 of 24 entries, cosmetic, chain indexing untouched); (2)
> `housekeeping_task_kb()` no longer calls `housekeeping_task_user()`, which
> `quantum/keyboard.c:433-437` already calls itself — the keymap hook had been
> firing **twice** per loop, latent until the `calibrate` keymap implemented it.
> **All three sizes are unchanged.** Gates: `behavior.cjs --touch=board` **33/33
> PASS** on default and vial with `--touch=firmware` still failing 4 (the A/B
> still discriminates); `calibrate.cjs` **37/37 PASS** with `--no-adc-fix` still
> failing 15; 30/30, 56/56, 80/80 unchanged. `default` **and** `calibrate`
> reproduce byte-for-byte (two clean-`.build` rebuilds each); `vial` remains
> non-deterministic.

> **Superseded later on 2026-08-15 — protocol v1, encoder direction flip, and a
> RENAME.** The table above is the current shipped set and there are now **two**
> artifacts, not three. It replaces `loudest_micro_default.uf2` (88576 B, md5
> `1c0ff911…`), `loudest_micro_vial.uf2` (104448 B, md5 `286fb09d…`) and
> `loudest_micro_calibrate.uf2` (96768 B, md5 `aabf7954…`). Three changes:
> (1) **protocol v1** — raw-HID commands `0x50`/`0x51`/`0x52` plus a 14-byte
> keyboard EEPROM datablock holding per-axis joystick rest/min/max, with the
> trigger threshold derived as `floor(60% of the smaller half-swing)` and applied
> to the arrow/scroll modes *and* the native HID gamepad; the CAPS reply's byte 4
> is now `01`. (2) **`ENCODER_DIRECTION_FLIP`** — measured on the owner's
> assembled board, a clockwise turn had been producing volume-DOWN. (3) the
> `calibrate` keymap, its UF2 and its referee `firmware/sim/calibrate.cjs` are
> **deleted** — the calibration lives in EEPROM now instead of being typed into a
> text editor and pasted back into source. Sizes grew by 2048 B (reference) and
> 2560 B (vial) for the v1 handlers and the calibration store. Gates:
> `behavior.cjs --touch=board --encoder=board` **33/33 PASS** on both builds,
> with `--touch=firmware` still failing exactly 4 and the new `--encoder=firmware`
> failing exactly 2 (the A/Bs still discriminate, and they compose to 6);
> `joystick.cjs` **48/48 PASS** on both builds with `--no-eeprom` failing 5 and
> `--no-adc-fix` failing 2; `run_conformance.py` **410/410** (was 80/80);
> 30/30 and 56/56 unchanged.

## 6. Remaining gaps (honest, none hidden)

1. **Joystick calibration** ships as placeholder `0/512/1023`
   (`CALIBRATION-PENDING` markers) — needs the bring-up ADC sweep on the real
   ~~Adafruit 3103 module (which itself must be pinout-metered before
   soldering, per the hardware hand-solder afterlist).~~
   🔻 **CORRECTED 2026-07-19:** JS1 is the YTL **YA13-FL7.4-B5Ka(45-10)-R-Y06**
   (LCSC **C37323742**, footprint `Joystick:YA13-FL7.4-B5Ka_C37323742`) —
   **machine-placed THT**, wiring datasheet-verified. There is **nothing to meter
   and nothing to hand-solder**: JS1 has left the hand-solder afterlist (RE1 is
   the only entry left). The ADC sweep is still needed for real low/rest/high on
   the assembled board; the only other bring-up item is axis direction —
   `firmware/POLARITY-NOTE.md` (in the release), a one-line config flip per
   reversed axis.
2. **Vial-build protocol edge cases** (§3, by design, documented): host-side
   SET_LAYER 1–3 and SET_KEY(0, #000000, solid) route to VIA; during a Vial
   security-unlock sequence the protocol is paused (frames echoed unhandled).
3. **Dispatch evidence horizon:** the "what the Vial GUI actually sends"
   analysis reflects vial-gui `main` as of this wave; a future VIA-protocol
   client that polls uptime or per-key keycodes would hit the documented
   collisions (worst case: a stray CAPS-shaped reply or an ignored layer
   move — never a crash; bounds checks hold).
4. **On-hardware validation** (real board) is inherently pending until Rev A
   arrives: ~~touch AHLB strap polarity~~, encoder detent direction, LED chain on
   real silicon, joystick sweep. The emulator run covers everything software.
   **[2026-08-13 — the AHLB item is CLOSED from the board file, not from
   silicon.]** `R10` (0 Ω) pad 1 → `TOUCH_AHLB`, pad 2 → `GND` on
   `v5_6.kicad_pcb` = **active-HIGH**, and the firmware now matches (see §5's
   superseded-artifacts note). What still needs the real board is whether the pad
   *senses* through the case at all — pad sensitivity, the DNP `C25` tuning, and
   false triggering — not which way the logic runs.
5. `qmk lint` false positive on the vial keymap name (upstream rule; see
   `BUILD.md` §3.1).
6. **No SKU awareness in `LOUDEST_LED_COUNT` / `CAPS.led_count`** (finding 4 of
   the 2026-08-13 firmware-verification pass: both are hard-24 while the opaque
   SKU populates LED1–14, so `loudestd` may address indexes 14–23 to no visible
   effect on an opaque unit).
   🔻 **CLOSED-BY-DECISION 2026-08-15 — stays 24 on both SKUs.** The byte is
   redefined as the **addressable chain length**, which is electrically true on
   both SKUs (on opaque, LED14's DOUT clocks pixels 14–23 into an unpopulated
   pad, so host writes there are harmless no-ops), because that byte is part of
   **LOCKED protocol v0** and forking per-SKU UF2s would multiply the shipped
   artifacts against the drag-and-drop standard for zero visible benefit. No
   code changed; the semantics are now stated at the definition site
   (`loudest_micro.h`).

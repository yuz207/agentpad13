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

### Other keyboard.json changes

* `usb.device_version` 0.0.1 → **1.0.0** (Rev A production build). VID/PID
  unchanged (`0xFEED`/`0x4C4D` — locked with `daemon/loudestd/protocol.py`).
* Provenance comments now cite `hardware/pcb/v4/ORDER-READINESS.md` instead of
  a pre-v4 internal design note.

## 2. Product rebrand → agentpad13

User-visible identity strings renamed "Loudest Micro" → **"agentpad13"**:
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

| File | SHA-256 |
|---|---|
| `loudest_micro_default.uf2` (88064 bytes) | `49642d69a53aef4308cb03a1d3e1b3c73c18d54946c6350adecfca47202ce39a` |
| `loudest_micro_vial.uf2` (104448 bytes) | `5d33fffc57807bfdda263f36f919139e157b6b3cadccc0edc3fb06601f948fd0` |

Built from the exact tree in this commit + vial-qmk `00fc4627` + the §3
patch, Arm GNU Toolchain 15.2.Rel1, zero warnings (`-Werror`).

## 6. Remaining gaps (honest, none hidden)

1. **Joystick calibration** ships as placeholder `0/512/1023`
   (`CALIBRATION-PENDING` markers) — needs the bring-up ADC sweep on the real
   Adafruit 3103 module (which itself must be pinout-metered before
   soldering, per the hardware hand-solder afterlist).
2. **Vial-build protocol edge cases** (§3, by design, documented): host-side
   SET_LAYER 1–3 and SET_KEY(0, #000000, solid) route to VIA; during a Vial
   security-unlock sequence the protocol is paused (frames echoed unhandled).
3. **Dispatch evidence horizon:** the "what the Vial GUI actually sends"
   analysis reflects vial-gui `main` as of this wave; a future VIA-protocol
   client that polls uptime or per-key keycodes would hit the documented
   collisions (worst case: a stray CAPS-shaped reply or an ignored layer
   move — never a crash; bounds checks hold).
4. **On-hardware validation** (real board) is inherently pending until Rev A
   arrives: touch AHLB strap polarity, encoder detent direction, LED chain on
   real silicon, joystick sweep. The emulator run covers everything software.
5. `qmk lint` false positive on the vial keymap name (upstream rule; see
   `BUILD.md` §3.1).

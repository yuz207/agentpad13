# agentpad13 — firmware build guide

Reproducible build of the agentpad13 Rev A firmware (RP2040) against the Vial
fork of QMK. This directory (`firmware/loudest_micro/`) is a **drop-in QMK
keyboard tree** — it is copied into `vial-qmk/keyboards/loudest_micro/` and
compiled there. (`loudest_micro` is the project's QMK keyboard/module name;
the product and all user-visible strings are **agentpad13** — see
`loudest_micro/readme.md` for why the internal name stays.) Only the keyboard
tree, this guide, the core patch in `patches/`, the validation tools
(`check_pins_v4.py`, `tests/conformance/`), and the prebuilt `.uf2`s live in
the repo; the multi-gigabyte vial-qmk checkout does not.

Status: **both keymaps compile to a clean `.uf2` with zero code warnings**
(`-Werror` is on). No features were stubbed — the joystick, RGB status
protocol, touch toggle, encoder map, Vial + VialRGB, and joystick modes are
all real code. The pin map targets the **current public board
`hardware/pcb/agentpad13/agentpad13.kicad_pcb`** (v5_7, md5
`08cf68dae979ab28aadd5e0dda34de01`). The map was re-verified 20/20 GPIO against
v5_6; v5_7 changes only the rotations of underglow LEDs 20 and 21, with zero net
or pin-map changes. `check_pins_v4.py` (below) embeds the definitive table and
asserts this tree against it. Board revision details and the v5_6-to-v5_7 delta
are in `hardware/pcb/README.md` and `release/RELEASE.md` row M.

---

## 1. Toolchain (versions actually used)

| Tool | Version | Notes |
|---|---|---|
| macOS | 15 (Darwin 25.4, arm64) | |
| QMK CLI | 1.2.0 | `pip install --user qmk` |
| Python | 3.12 | |
| vial-qmk | branch `vial`, commit `00fc4627` | + 1 small core patch, see §2 |
| arm-none-eabi-gcc | **Arm GNU Toolchain 15.2.Rel1** (gcc 15.2.1) | official Arm build, self-contained (bundles newlib) |

### 1.1 Toolchain install — and the blocker we hit

`brew install --cask gcc-arm-embedded` and `brew install arm-none-eabi-gcc`
both have pitfalls on a non-interactive machine; here is exactly what happens
and what works:

* **`brew install --cask gcc-arm-embedded` → BLOCKED without a TTY.** The cask
  downloads the official Arm `.pkg` but runs the Apple installer under `sudo`,
  which needs an interactive password (`sudo: a terminal is required…`). The
  download still lands in Homebrew's cache.
* **`brew install arm-none-eabi-gcc` (formula) → COMPILES BUT CANNOT LINK C.**
  The bottled formula (gcc 16.x) installs the compiler **without** the newlib C
  library/headers, so the very first QMK object fails with
  `fatal error: stdint.h: No such file or directory` (a bare `include_next`).
  gcc 16 is also newer than QMK targets.
* **What works (no sudo):** extract the official Arm `.pkg` that the cask
  already cached, into a user directory, and put its `bin/` on `PATH`:

  ```bash
  PKG="$HOME/Library/Caches/Homebrew/downloads/"*arm-gnu-toolchain-15.2*darwin-arm64-arm-none-eabi.pkg
  pkgutil --expand-full $PKG /tmp/armgnu_expand           # no sudo needed
  mv /tmp/armgnu_expand/Payload ~/arm-gnu-toolchain       # any user-writable dir
  export PATH="$HOME/arm-gnu-toolchain/bin:$PATH"
  arm-none-eabi-gcc --version   # -> Arm GNU Toolchain 15.2.Rel1
  ```

  (With a normal desktop session, `brew install --cask gcc-arm-embedded` works
  too — it just prompts for your password once. The extracted tree is the same
  official toolchain, minus the sudo step.)

## 2. Set up the QMK build tree

```bash
pip install --user qmk                          # qmk 1.2.0

# Clone the Vial fork somewhere outside this repo, at the pinned commit:
git clone --branch vial https://github.com/vial-kb/vial-qmk.git
cd vial-qmk
git checkout 00fc4627
qmk config user.qmk_home="$PWD"
qmk git-submodule       # chibios, chibios-contrib, pico-sdk, printf, lufa, ...
                        # (lufa IS required: ChibiOS USB descriptors use its headers)

# Apply the one core patch (see §6 for what it does and why):
git apply /path/to/agentpad13/firmware/patches/0001-via-command-kb-backport.patch

# Drop our keyboard tree in:
cp -R /path/to/agentpad13/firmware/loudest_micro keyboards/loudest_micro
```

> **Do not skip the patch.** Without it the vial build still compiles, but
> VIA silently swallows the agent-status protocol (IDs 0x01–0x04). The
> checker below fails loudly on an unpatched tree.

## 3. Build

```bash
export PATH="$HOME/arm-gnu-toolchain/bin:$HOME/.local/bin:$PATH"

qmk compile -kb loudest_micro -km default       # -> loudest_micro_default.uf2
qmk compile -kb loudest_micro -km vial          # -> loudest_micro_vial.uf2
```

Both drop a `.uf2` in the vial-qmk root. Prebuilt copies live in
`firmware/prebuilt/` (SHA-256 hashes in `firmware/FIRMWARE-V4-NOTES.md`) —
**note the shipped names differ from the build output** *(renamed 2026-08-15)*:

| build | emits | ships as |
|---|---|---|
| `-km vial` | `loudest_micro_vial.uf2` | **`firmware/prebuilt/agentpad13.uf2`** — the one users want |
| `-km default` | `loudest_micro_default.uf2` | **`firmware/prebuilt/agentpad13_reference.uf2`** — the byte-reproducible reference |

### 3.1 Validate

```bash
# 1. Static pin-map check against the board's per-GPIO table (mandatory
#    before flashing anything new). --qmk-info additionally checks the
#    resolved build config; --qmk-home verifies the §2 patch was applied.
qmk info -kb loudest_micro -f json > /tmp/info.json
python3 firmware/check_pins_v4.py --qmk-info /tmp/info.json --qmk-home /path/to/vial-qmk

# 2. Protocol conformance (v0 + v1 since 2026-08-15): compiles the real
#    firmware handler on the host and drives it with frames built by the
#    vendored host wire-format oracle. Contract: docs/PROTOCOL-V1-CONTRACT.md.
python3 firmware/tests/conformance/run_conformance.py

# 3. QMK lint
qmk lint -kb loudest_micro -km default --strict
```

> `qmk lint -km vial` prints **“The keymap vial should not exist!”** — this is
> a mainline-QMK lint rule (`INVALID_KM_NAMES = ['via', 'vial']`) that every
> Vial keyboard trips. It is a false positive here; Vial's own CI uses
> `util/ci_compile_vial_keyboards.py`, not `qmk lint`, for `vial` keymaps. The
> `default` keymap passes `--strict`, and the `vial` keymap compiles cleanly
> (which means `vial.json` was parsed and embedded).

There is also a full-image smoke test that boots the real `.uf2` in the
rp2040js emulator (pin muxing, WS2812 activity, USB enumeration, key scan,
raw HID PING→CAPS):

```bash
cd firmware/tests/emulator
./get-bootrom.sh && npm install
npm run smoke:default && npm run smoke:vial     # -> EMULATOR SMOKE: PASS
```

Recorded results and the emulator-fidelity caveats are in
`firmware/FIRMWARE-V4-NOTES.md` §4d.

## 4. Flash

Enter the RP2040 bootloader (hold BOOTSEL while plugging in USB, or double-tap
RESET) so the `RPI-RP2` mass-storage drive appears, then:

```bash
qmk flash -kb loudest_micro -km default
# or just copy firmware/prebuilt/agentpad13.uf2 (vial) or
# firmware/prebuilt/agentpad13_reference.uf2 (plain QMK) onto RPI-RP2
```

**Never wipes user data:** Vial dynamic keymaps/macros live in emulated EEPROM,
not in the firmware image, so reflashing keeps them. A layout that changes the
matrix or layer count is the only thing that forces a `Reset EEPROM`
(bootmagic: hold SW1/`[0,0]` while plugging in).

---

## 4a. Bring-up: first power-on

**The procedure lives in [`firmware/BRING-UP.md`](BRING-UP.md) — that file is the
single source of truth for it and is not duplicated here.** It was split out of
this section on 2026-08-15 so it can ship in `release/firmware/`
byte-identical (the same arrangement `firmware/POLARITY-NOTE.md` already has):
the audience for bring-up is the owner assembling and powering the first boards,
not a reader of a 400-line toolchain guide. Only the maintainer-side block below
stayed, because its commands need a QMK build tree and repo paths that a bundle
reader does not have.

> **⚠ THE `calibrate` KEYMAP IS DELETED (2026-08-15), AND `BRING-UP.md` HAS NOT
> CAUGHT UP YET.** The separate bring-up firmware — `keymaps/calibrate/`,
> `firmware/prebuilt/loudest_micro_calibrate.uf2`, and its referee
> `firmware/sim/calibrate.cjs` — is gone: the owner flashed it, drove it with
> four `SW1` presses, and it **typed** its measurements into a text editor, and
> the calibration then had to be pasted back into two source files and rebuilt.
> Calibration values now live in the board's own EEPROM (a 14-byte keyboard
> datablock; `config.h`, `docs/PROTOCOL-V1-CONTRACT.md`), survive a power cycle,
> and are applied to all three joystick modes and to the native HID gamepad
> without a rebuild or a reflash.
>
> **RESOLVED later on 2026-08-15 — `BRING-UP.md` has caught up.** That page was
> rewritten around the on-board flow and is followable again end to end: flash
> `agentpad13.uf2`, check the layer LED is pure red, **hold SW14 for a second and
> follow the lights**, then check the touch pad and the encoder. No host, no
> daemon, no CLI, no separate firmware, no reflash — calibration is triggered by
> **SW14 on the board itself** and the board stores its own result.
> (The paragraph this replaces warned that Steps 1–3 could not be followed as
> written, which was true while it stood.) The retired typed-output flow is
> preserved in the release ledger (`release/RELEASE.md`, rows K and L), not
> here. The 0x50/0x51/0x52 commands remain in place
> and working for diagnostics and host tooling; they are simply no longer the
> only path to a calibrated board.

### For maintainers

```bash
qmk compile -kb loudest_micro -km default       # clean under -Werror
qmk compile -kb loudest_micro -km vial          # clean under -Werror (LTO note only)

# Referees for the two shipped artifacts. All four A/B arms are gates:
node firmware/sim/behavior.cjs --touch=board --encoder=board      # 33/33 PASS
node firmware/sim/behavior.cjs --touch=firmware                   # must FAIL (4)
node firmware/sim/behavior.cjs --encoder=firmware                 # must FAIL (2)
node firmware/sim/joystick.cjs                                    # 48/48 PASS
node firmware/sim/joystick.cjs --no-eeprom                        # must FAIL

# Host/device agreement on the wire, no hardware needed:
python3 firmware/tests/conformance/run_conformance.py             # 410/410
```

`joystick.cjs` is the protocol-v1 referee: it boots the real UF2, exercises
0x50/0x51/0x52 and every rejection class, and **proves the calibration survives a
simulated power cycle** rather than assuming it. Its `--no-eeprom` arm removes
the harness's serial-flash model and must fail on exactly the persistence
checks.

---

## 5. Pin map (Rev A — public board `v5_7`; map unchanged from `v5_6`)

Source table: the definitive 30-GPIO table embedded in `check_pins_v4.py`,
originally extracted twice from the final copper and re-verified 20/20 GPIO
against v5_6. The current public board is
`hardware/pcb/agentpad13/agentpad13.kicad_pcb` (v5_7); its only v5_6 delta is
LED20/LED21 orientation, so the GPIO table is unchanged. Direct-pin matrix —
logical `[row][col]` positions unchanged, physical GPIOs follow the board's
x-monotonic routing remap:

| Matrix | Keys | GPIOs |
|---|---|---|
| row 0 | SW1 SW2 SW3 SW4 | GP12 GP9 GP5 GP2 |
| row 1 | SW5 SW6 SW7 SW8 | GP11 GP8 GP4 GP1 |
| row 2 | SW9 SW10 SW11 SW12 | GP10 GP7 GP3 GP0 |
| row 3 | SW13 (2U) · encoder push · touch\* | GP6 · GP15 · *(GP16, see below)* |

\* **GP16 is deliberately NOT in `matrix_pins.direct`** (it is `null` at
`[3][2]`). The board straps the TTP223 **active-HIGH** — `R10` (0 Ω) ties
`TOUCH_AHLB → GND` on the v5 board, so `GP16` idles LOW and drives HIGH while
touched — which is the opposite of the 13 switch-to-GND keys. QMK's only
direct-pin polarity knob, `MATRIX_INPUT_PRESSED_STATE`, is applied **globally**
in `quantum/matrix.c` `readMatrixPin()`, so using it would invert all 13
switches. Instead `loudest_micro.c` configures `GP16` in `keyboard_pre_init_kb()`
(input, pull-**down**) and polls it in `matrix_scan_kb()` with a 5 ms debounce,
injecting `action_exec(MAKE_KEYEVENT(3, 2, pressed))` — so the key keeps its
logical position, keycode, `TO()` layer chain and `TP_TOG` gate. Fixed
2026-08-13; before that the mismatch made `[3,2]` read permanently pressed and
the pad booted into layer 1. Only side effect: Vial's matrix tester cannot show
`[3,2]`, since it reads the scanned `matrix[]`.

Encoder A/B = GP13/GP14 · WS2812 data = GP17 (through the SN74LVC1T45 level
shifter) · joystick X/Y = GP26/GP27 (ADC0/ADC1). GP18/GP19 (I2C1), GP20 and
GP28 go to the DNP J2 expansion header and are unused by firmware. **Trap for
future expansion work:** the J2 net *named* "GP21" is silicon **GPIO24** —
never address it as GPIO21 (`check_pins_v4.py` guards this).

## 6. Raw-HID protocol v0 (LOCKED) and VIA/Vial coexistence

The wire format is LOCKED; the public contract is
`docs/PROTOCOL-V1-CONTRACT.md`. `tests/conformance/protocol_oracle.py` is the
dependency-free host oracle vendored with this tree, and
`tests/conformance/run_conformance.py` asserts the firmware against it
byte-for-byte:

* Descriptor pinned in `config.h`: Usage Page `0xFF60`, Usage `0x61`, VID
  `0xFEED`, PID `0x4C4D`, 32-byte report-ID-less frames.
* `SET_KEY {index,r,g,b,effect}` — `index` is a **raw LED-chain position
  (0–23)**. Because `keyboard.json` authors `rgb_matrix.layout` in chain
  order, chain index == rgb_matrix LED index, so no remap is needed
  (documented in `loudest_micro.h`).
* `SET_LAYER {n}`, `CLEAR`, `PING {token}`.
* CAPS reply: `[0x04, token, 'L'(0x4C), 'D'(0x44), proto=0, led_count=24,
  layer_count=8, features=0x1F]` where features = PER_KEY|UNDERGLOW|
  LAYER_INDICATOR|JOYSTICK|ENCODER. Effects: solid=0, pulse=1, blink=2
  (pulse/blink animated on-device). The host always sends explicit RGB; the
  firmware hardcodes no colors.

### The VIA shadow, and how it is resolved

Under VIA/Vial, `via.c` owns `raw_hid_receive()` and its command switch
consumes IDs 0x01–0x04 (`id_get_protocol_version`,
`id_get/set_keyboard_value`, `id_dynamic_keymap_get_keycode`) before the
`raw_hid_receive_kb()` fallback sees them — which used to shadow the whole
status protocol in the vial build. The fix follows upstream QMK practice: the
`via_command_kb()` pre-hook (present in mainline QMK, missing from the
vial-qmk fork at our pinned commit) is backported by
`patches/0001-via-command-kb-backport.patch` (23 lines, `quantum/via.c` +
`via.h`), and the keyboard implements it as a byte-content dispatcher
(`loudest_micro.c`): frames that are valid v0 protocol commands are handled
and claimed; everything else — including all traffic the Vial GUI actually
sends (verified against vial-gui's `keyboard_comm.py`) — falls through to VIA
untouched.

Three byte patterns are genuinely ambiguous (identical wire bytes, two
meanings). Their dispositions, chosen so both clients stay functional:

| Frame bytes | Could be | Goes to | Cost |
|---|---|---|---|
| `01 00…00` | SET_KEY(0,#000000,solid) / VIA protocol-version handshake | **VIA** | in the vial build, "LED 0 black solid" is expressed via CLEAR or r/g/b ≥ 1 |
| `02 0n 00…` n=1,2,3 | SET_LAYER 1–3 / VIA uptime, layout options, matrix tester | **VIA** | vial build cannot host-switch to layers 1–3 (0 and 4–7 work; the plain-QMK build has the full range; layers remain reachable via touch/Vial GUI) |
| `04 nn 00…` | PING / legacy per-key `get_keycode(n,0,0)` | **loudest** | a legacy VIA client reading key [0,0] would get CAPS bytes; the Vial GUI never sends per-key 0x04 (it bulk-reads via 0x12) |

The **default** (non-VIA) build owns `raw_hid_receive()` outright and runs
the complete protocol with no exceptions. During a Vial security-unlock
sequence (physical key hold) the pre-hook is bypassed and protocol frames are
echoed unhandled — by design, matching Vial's restricted-command window.

---

## 7. Default keymap summary

15 keys, 8 layers. Touch cycles layers via a `TO()` chain (0→1→…→7→0).

* **Layer 0 (BASE):** `F13–F24` on the 4×3 grid; **SW13 (2U hero) = `KC_MPLY`**;
  encoder push = `KC_MUTE`; touch = `TO(1)`.
* **Layer 1 (CTRL):** `JS_MODE`, `TP_TOG`, RGB controls, media transport.
* **Layer 2 (NAV):** arrows / paging / editing.
* **Layers 3–7:** transparent grid (user-customizable), touch keeps the chain alive.
* **Encoder (per-layer map):** volume by default; RGB effect on CTRL; paging on NAV.
* `vial/` keymap = same layers as the compiled-in default, plus `vial.json`
  (15 logical keys, 8 dynamic layers, VialRGB, custom keycodes) and a generated
  `VIAL_KEYBOARD_UID`.

---

## 8. Known follow-ups (no build stubs — these are refinements)

* **Joystick calibration — storage side CLOSED 2026-08-15.** Axes still ship
  with placeholder `0/512/1023` and the 512/300 fallback, but those are now the
  *uncalibrated* case rather than a pending source edit: the board keeps
  per-axis rest/min/max in a 14-byte EEPROM datablock, derives the threshold as
  `floor(60% of the smaller half-swing)`, applies it to the arrow/scroll modes
  and the native gamepad alike, and it survives a power cycle. No source edit,
  no rebuild and no reflash is involved any more. Protocol v1
  (`0x50`/`0x51`/`0x52`, `docs/PROTOCOL-V1-CONTRACT.md`) exposes that store on
  the wire for host tooling and diagnostics. **Still open:** the owner-facing
  way to *start* a calibration, and the `BRING-UP.md` rewrite that goes with it.
  *(This bullet used to say the sweep needed the `calibrate` keymap, which is
  deleted.)* *(This bullet used to say the sweep needed the
  `calibrate` keymap, which is deleted.)*
* **Joystick mode exclusivity.** In arrows/scroll mode the native HID gamepad
  axes keep reporting (QMK's `JOYSTICK_AXIS_IN` task reads every housekeeping
  cycle); the arrow/scroll events are layered on top. To make the modes
  mutually exclusive, switch to virtual axes and drive them manually, or gate
  the joystick task.
* **Persist mode state.** `js_mode` and `touch_enabled` are RAM-only and reset
  on power cycle; persist in EEPROM if desired.
* **Distribution.** Package the status protocol as a QMK Community Module and
  add a VIA V3 JSON for `usevia.app`.

---

## 9. Toolchain gotcha quick-reference

If a fresh build dies with `stdint.h: No such file or directory`, your PATH is
finding the Homebrew `arm-none-eabi-gcc` formula (no newlib) instead of the
official Arm toolchain. Put the extracted `arm-gnu-toolchain/bin` **first** on
PATH.

**Build SERIALLY on macOS.** `qmk compile -j N` adds `--output-sync=target`,
which the GNU Make **3.81** that ships with macOS rejects — the build dies before
compiling anything. The plain `qmk compile` lines in §3 are already serial; do
not add `-j`.

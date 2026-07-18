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
all real code. The pin map targets the shipped Rev A board (`v4_r27`); its
single source of truth is the Layer 4 per-GPIO table in
`hardware/pcb/v4/ORDER-READINESS.md`, and `check_pins_v4.py` (below) asserts
the tree against it.

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
`firmware/prebuilt/` (SHA-256 hashes in `firmware/FIRMWARE-V4-NOTES.md`).

### 3.1 Validate

```bash
# 1. Static pin-map check against the board's per-GPIO table (mandatory
#    before flashing anything new). --qmk-info additionally checks the
#    resolved build config; --qmk-home verifies the §2 patch was applied.
qmk info -kb loudest_micro -f json > /tmp/info.json
python3 firmware/check_pins_v4.py --qmk-info /tmp/info.json --qmk-home /path/to/vial-qmk

# 2. Protocol-v0 conformance: compiles the real firmware handler on the host
#    and drives it with frames built by the daemon's wire-format oracle.
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
# or just copy firmware/prebuilt/loudest_micro_default.uf2 onto RPI-RP2
```

**Never wipes user data:** Vial dynamic keymaps/macros live in emulated EEPROM,
not in the firmware image, so reflashing keeps them. A layout that changes the
matrix or layer count is the only thing that forces a `Reset EEPROM`
(bootmagic: hold SW1/`[0,0]` while plugging in).

---

## 5. Pin map (Rev A, board v4_r27)

Single source of truth: `hardware/pcb/v4/ORDER-READINESS.md` Layer 4 (the
definitive 30-GPIO table, extracted twice from the final copper). Direct-pin
matrix — logical `[row][col]` positions unchanged, physical GPIOs follow the
board's x-monotonic routing remap:

| Matrix | Keys | GPIOs |
|---|---|---|
| row 0 | SW1 SW2 SW3 SW4 | GP12 GP9 GP5 GP2 |
| row 1 | SW5 SW6 SW7 SW8 | GP11 GP8 GP4 GP1 |
| row 2 | SW9 SW10 SW11 SW12 | GP10 GP7 GP3 GP0 |
| row 3 | SW13 (2U) · encoder push · touch | GP6 · GP15 · GP16 |

Encoder A/B = GP13/GP14 · WS2812 data = GP17 (through the SN74LVC1T45 level
shifter) · joystick X/Y = GP26/GP27 (ADC0/ADC1). GP18/GP19 (I2C1), GP20 and
GP28 go to the DNP J2 expansion header and are unused by firmware. **Trap for
future expansion work:** the J2 net *named* "GP21" is silicon **GPIO24** —
never address it as GPIO21 (`check_pins_v4.py` guards this).

## 6. Raw-HID protocol v0 (LOCKED) and VIA/Vial coexistence

The wire format is LOCKED; the single source of truth is
`daemon/loudestd/protocol.py`, and `tests/conformance/run_conformance.py`
asserts the firmware against it byte-for-byte:

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

* **Joystick calibration.** Axes ship with placeholder `0/512/1023`. RP2040
  `analogReadPin` is 10-bit (0–1023) so center ≈512 is structurally right, but
  the real deadzone/curve/rest values come from a bring-up ADC sweep on the
  real module (`config.h`, `keyboard.json`, and `JS_CENTER/JS_THRESHOLD` in
  `loudest_micro.c` are marked `CALIBRATION-PENDING`).
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

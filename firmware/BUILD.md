# Loudest Micro — firmware build guide

Reproducible build of the Loudest Micro Rev A firmware (RP2040) against the Vial
fork of QMK. This directory (`firmware/loudest_micro/`) is a **drop-in QMK keyboard
tree** — it is copied into `vial-qmk/keyboards/loudest_micro/` and compiled there.
Only the keyboard tree, this guide, and the prebuilt `.uf2`s live in the repo; the
multi-gigabyte vial-qmk checkout does not.

Status: **both keymaps compile to a clean `.uf2` with zero code warnings**
(`-Werror` is on). No features were stubbed — the joystick, RGB status protocol,
touch toggle, encoder map, Vial + VialRGB, and joystick modes are all real code.

---

## 1. Toolchain (versions actually used)

| Tool | Version | Notes |
|---|---|---|
| macOS | 15 (Darwin 25.4, arm64) | |
| QMK CLI | 1.2.0 | `pip install --user qmk` |
| Python | 3.12 | |
| vial-qmk | branch `vial`, commit `00fc4627` | shallow clone |
| arm-none-eabi-gcc | **Arm GNU Toolchain 15.2.Rel1** (gcc 15.2.1) | official Arm build, self-contained (bundles newlib) |

### 1.1 Toolchain install — and the blocker we hit

The mission suggested `brew install --cask gcc-arm-embedded` or
`brew install arm-none-eabi-gcc`. Both have pitfalls on a non-interactive machine;
here is exactly what happened and what works:

* **`brew install --cask gcc-arm-embedded` → BLOCKED.** The cask downloads the
  official Arm `.pkg` but runs the Apple installer under `sudo`, which needs an
  interactive TTY/password we do not have (`sudo: a terminal is required…`). The
  download still lands in Homebrew's cache.
* **`brew install arm-none-eabi-gcc` (formula) → COMPILES BUT CANNOT LINK C.**
  The bottled formula (gcc 16.1.0) installs the compiler **without** the newlib C
  library/headers, so the very first QMK object fails with
  `fatal error: stdint.h: No such file or directory` (a bare `include_next`). gcc 16
  is also newer than QMK targets.
* **What works (no sudo):** extract the official Arm `.pkg` that the cask already
  cached, into a user directory, and put its `bin/` on `PATH`:

  ```bash
  PKG="$HOME/Library/Caches/Homebrew/downloads/"*arm-gnu-toolchain-15.2*darwin-arm64-arm-none-eabi.pkg
  pkgutil --expand-full $PKG /tmp/armgnu_expand          # no sudo needed
  mv /tmp/armgnu_expand/Payload /opt/arm-gnu-toolchain    # any user-writable dir
  export PATH="/opt/arm-gnu-toolchain/bin:$PATH"
  arm-none-eabi-gcc --version   # -> Arm GNU Toolchain 15.2.Rel1
  ```

  (If you have a normal desktop session, `brew install --cask gcc-arm-embedded`
  works too — it just needs to prompt for your password once. The extracted tree is
  the same official toolchain, minus the sudo step.)

## 2. Set up the QMK build tree

```bash
pip install --user qmk                          # qmk 1.2.0

# Shallow clone the Vial fork somewhere outside this repo:
git clone --depth 1 --branch vial https://github.com/vial-kb/vial-qmk.git
cd vial-qmk
qmk config user.qmk_home="$PWD"
qmk git-submodule                               # chibios, chibios-contrib, pico-sdk, printf

# Drop our keyboard tree in:
cp -R /path/to/work-loudest/firmware/loudest_micro keyboards/loudest_micro
```

## 3. Build

```bash
export PATH="/opt/arm-gnu-toolchain/bin:$HOME/.local/bin:$PATH"

qmk compile -kb loudest_micro -km default       # -> loudest_micro_default.uf2
qmk compile -kb loudest_micro -km vial          # -> loudest_micro_vial.uf2
```

Both drop a `.uf2` in the vial-qmk root. Prebuilt copies live in
`firmware/prebuilt/`.

### Validate without building

```bash
qmk lint -kb loudest_micro -km default --strict   # PASSES
qmk info -kb loudest_micro                         # dumps parsed config
```

> `qmk lint -km vial` prints **“The keymap vial should not exist!”** — this is a
> mainline-QMK lint rule (`INVALID_KM_NAMES = ['via', 'vial']`) that every Vial
> keyboard trips. It is a false positive here; Vial's own CI uses
> `util/ci_compile_vial_keyboards.py`, not `qmk lint`, for `vial` keymaps. The
> `default` keymap passes `--strict`, and the `vial` keymap compiles cleanly
> (which means `vial.json` was parsed and embedded).

## 4. Flash

Enter the RP2040 bootloader (hold BOOTSEL while plugging in USB, or double-tap
RESET) so the `RPI-RP2` mass-storage drive appears, then:

```bash
qmk flash -kb loudest_micro -km default
# or just copy firmware/prebuilt/loudest_micro_default.uf2 onto RPI-RP2
```

**Never wipes user data:** Vial dynamic keymaps/macros live in emulated EEPROM,
not in the firmware image, so reflashing keeps them (spec 3.9 migration rule). A
layout that changes the matrix or layer count is the only thing that forces a
`Reset EEPROM` (bootmagic: hold SW1/`[0,0]` while plugging in).

---

## 5. What the untested scaffold needed (schema/build fixes)

The scaffold in `firmware/loudest_micro/` was explicitly "not yet compiled." The
real build surfaced these, all now fixed in the tree:

1. **`matrix_pins.direct` empty cell** — scaffold used the string `"NO_PIN"`; the
   keyboard.json schema requires JSON `null`. Fixed → `["GP12","GP15","GP16", null]`.
2. **Illegal `$comment` inside `rgb_matrix`** — nested schema blocks are
   `additionalProperties: false`, so `rgb_matrix.$comment` fails validation. Moved
   all provenance notes to **top-level** `$comment`/`$…_comment` keys (the root
   object does allow extra keys), preserving the layout-v2 comment trail.
3. **Joystick config** — replaced the bare `features.joystick` + hand-rolled
   `config.h` axes with the data-driven block
   `"joystick": {"driver": "analog", "button_count": 0, "axes": {"x": {input_pin GP26…}, "y": {input_pin GP27…}}}`.
   vial-qmk auto-generates `joystick_axes[]` (`JOYSTICK_AXIS_IN(GP26,0,512,1023)`,
   …) and sets `JOYSTICK_AXIS_COUNT=2`, `JOYSTICK_BUTTON_COUNT=0`, and pulls in the
   analog driver (`ANALOG_DRIVER_REQUIRED`). Hand-writing `joystick_axes[]` too
   would double-define it.
4. **`rgb_matrix.layout` was empty** — filled with the 24-LED array from
   `gen_led_layout.py` (13 per-key `flags:4`, 1 indicator `flags:8`, 10 underglow
   `flags:2`). `RGB_MATRIX_LED_COUNT` (24) and `WS2812_DI_PIN` (GP17) are derived.
5. **`RGB_MATRIX_SLEEP`** — moved from a `config.h` `#define` to `rgb_matrix.sleep:
   true` (data-driven) to avoid a duplicate define; added a small `animations` set
   and `center_point`.
6. **Encoder map** — needs `ENCODER_MAP_ENABLE = yes` in each keymap's `rules.mk`
   (it is not a keyboard-level flag); added, plus an 8-layer `encoder_map[]`.
7. **`RAW_ENABLE`** — `features.raw: true` does map to `RAW_ENABLE` (verified via
   `qmk generate-rules-mk`), so the scaffold's intent was fine.
8. **Custom keycodes** — `JS_MODE`/`TP_TOG` defined at keyboard level as
   `QK_KB_0/1` in `loudest_micro.h` so both keymaps and `vial.json` share them.

### Firmware code fixes found by the compiler (`-Werror`)

* `RAW_EPSIZE` is not exposed to keyboard code → used a local `LOUDEST_REPORT_LEN 32`.
* `sin8`/`scale8` (lib8tion) were not in scope → replaced the pulse effect with
  plain integer triangle-wave math (no extra include, fully portable).

---

## 6. Raw-HID protocol v0 conformance (LOCKED)

The `raw_hid_receive` handler conforms **byte-for-byte** to the locked contract in
`daemon/loudestd/protocol.py` (verified against that module's `build_caps` /
`parse_command`):

* Descriptor pinned in `config.h`: Usage Page `0xFF60`, Usage `0x61`, VID `0xFEED`,
  PID `0x4C4D`, 32-byte report-ID-less frames.
* `SET_KEY {index,r,g,b,effect}` — `index` is a **raw LED-chain position (0–23)**.
  Because `keyboard.json` authors `rgb_matrix.layout` in chain order, chain index ==
  rgb_matrix LED index, so no remap is needed (documented in `loudest_micro.h`).
* `SET_LAYER {n}`, `CLEAR`, `PING {token}`.
* CAPS reply: `[0x04, token, 'L'(0x4C), 'D'(0x44), proto=0, led_count=24,
  layer_count=8, features=0x1F]` where features = PER_KEY|UNDERGLOW|LAYER_INDICATOR
  |JOYSTICK|ENCODER. Effects: solid=0, pulse=1, blink=2 (pulse/blink animated
  on-device). The host always sends explicit RGB; the firmware hardcodes no colors.

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

## 8. PHASE1/PHASE4 follow-ups (no build stubs — these are refinements)

* **PHASE1 — joystick calibration.** Axes ship with placeholder `0/512/1023`.
  RP2040 `analogReadPin` is 10-bit (0–1023) so center ≈512 is structurally right,
  but the real deadzone/curve/rest values come from the Phase-1 ADC sweep
  (`config.h`, `keyboard.json`, and `JS_CENTER/JS_THRESHOLD` in `loudest_micro.c`
  are marked `PHASE1-PENDING`).
* **PHASE4 — protocol under Vial.** VIA owns `raw_hid_receive` and claims low
  command IDs, so the **vial** build only receives protocol IDs VIA ignores; the
  low IDs (`0x01–0x04`) are shadowed by VIA. The **default** (non-VIA) build runs
  the full protocol cleanly. Fix: move the status protocol onto a VIA custom
  channel or a dedicated HID interface so it coexists with Vial. (Marked
  `PHASE4-TODO` in `loudest_micro.c`.)
* **PHASE4 — joystick mode exclusivity.** In arrows/scroll mode the native HID
  gamepad axes keep reporting (QMK's `JOYSTICK_AXIS_IN` task reads every
  housekeeping cycle); the arrow/scroll events are layered on top. To make the
  modes mutually exclusive, switch to virtual axes and drive them manually, or gate
  the joystick task.
* **PHASE4 — persist mode state.** `js_mode` and `touch_enabled` are RAM-only and
  reset on power cycle; persist in EEPROM if desired.
* **Distribution (spec 3.9):** package the status protocol as a QMK Community
  Module and add the VIA V3 JSON for `usevia.app`.

---

## 9. Toolchain gotcha quick-reference

If a fresh build dies with `stdint.h: No such file or directory`, your PATH is
finding the Homebrew `arm-none-eabi-gcc` formula (no newlib) instead of the
official Arm toolchain. Put the extracted `arm-gnu-toolchain/bin` **first** on PATH.

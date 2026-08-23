// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 Rev A - keyboard-level configuration.
//
// THE CURRENT PUBLIC BOARD IS release/hardware/pcb/v5_7.kicad_pcb
// (v5_7, md5 08cf68dae979ab28aadd5e0dda34de01). The pin map was re-verified
// 20/20 GPIO against v5_6; v5_7 changes only the rotations of underglow LEDs 20
// and 21, with zero net or pin-map changes. The definitive table is embedded in
// firmware/check_pins_v4.py. See release/hardware/pcb/V5-NOTES.md for the revision delta.
#pragma once

// --- Joystick (analog 2-axis tilt gimbal on ADC) ---
// JS1 = YTL YA13-FL7.4-B5Ka(45-10)-R-Y06, LCSC C37323742, machine-placed THT.
// (Corrected 2026-07-19; this used to read "analog PSP-slider on ADC, planar"
// for the dropped Adafruit 3103 hand-solder part. Electrically identical from
// firmware's side: dual pot, wiper -> ADC. Axis DIRECTION may need inverting --
// see firmware/POLARITY-NOTE.md; it is a one-line edit followed by a rebuild.)
// Axes + placeholder calibration (512 center, 0..1023) live in keyboard.json
// ("joystick": {"driver": "analog", "axes": ...}) which auto-generates
// joystick_axes[]. JOYSTICK_AXIS_COUNT (=2) and JOYSTICK_BUTTON_COUNT (=0) are
// emitted from that block. Those values are only the uncalibrated fallback;
// the SW14 routine measures the real module and stores its values in EEPROM.
// Native QMK output is HID gamepad; the arrow (8-way) and scroll modes are
// custom code in loudest_micro.c reading GP26/GP27 (JS_MODE keycode).

// --- Touch (TTP223 U6 on GP16, injected at matrix [3,2]) ---
// BOARD TRUTH, read off the v5 board: R10 (0R) straps TOUCH_AHLB -> GND. On a
// TTP223, AHLB low selects the ACTIVE-HIGH output, so GP16 idles LOW and drives
// HIGH while the pad is touched -- the OPPOSITE sense of the 13 switch-to-GND
// keys. (CORRECTED 2026-08-13: this comment used to read "the PCB straps the
// AHLB pad active-low ... idle high, touched low". That was wrong about this
// board, and because nothing inverted the read, [3,2] scanned as permanently
// pressed: the pad booted into layer 1, layer 0 was unreachable, and touch fired
// on finger lift. Corroborated directly by R10 on the released v5_7 board:
// pad 1 is TOUCH_AHLB and pad 2 is GND.)
// QMK's only direct-pin polarity knob, MATRIX_INPUT_PRESSED_STATE, is GLOBAL --
// quantum/matrix.c applies it in readMatrixPin() to every direct pin -- so
// setting it would invert the 13 genuinely active-low switches. GP16 is
// therefore NOT a matrix pin (keyboard.json has matrix_pins.direct[3][2] = null)
// and loudest_micro.c polls it with its own active-high sense, injecting the
// press/release at the same logical position [3,2]. Keymaps, LAYOUT, matrix size
// and the rgb_matrix layout are unchanged. TP_TOG (custom keycode) still gates
// this key on/off.

// --- Raw HID status protocol v1 ---
// LOCKED wire format - public contract: docs/PROTOCOL-V1-CONTRACT.md; vendored
// host oracle: firmware/tests/conformance/protocol_oracle.py. Handled in
// loudest_micro.c: 0x01 SET_KEY {chain_idx,r,g,b,effect} | 0x02 SET_LAYER {n} |
// 0x03 CLEAR | 0x04 PING {token} -> CAPS {token,'L','D',ver,led_count,layers,feat}.
// v1 (2026-08-15) ADDS, without touching any v0 frame: 0x50 GET_JOYSTICK |
// 0x51 SET_CALIBRATION | 0x52 RESET_CALIBRATION.
// Pin the QMK Raw HID descriptor to the values a host application opens (already the QMK
// defaults; declared here so the contract is explicit and cannot silently drift).
#define RAW_USAGE_PAGE 0xFF60
#define RAW_USAGE_ID 0x61

// --- SW14: two roles, and why they can never collide ---
// SW14 is the button in the back that connects net BOOTSEL to GND, with R6 (1k)
// tying BOOTSEL to QSPI_CS on the public v5_7 board - the stock Pico
// topology. It does two entirely different jobs:
//   * HELD AT POWER-UP -> the RP2040 MASK ROM samples this line before one
//     instruction of our firmware has run, and enters the UF2 bootloader. This
//     is how the board is flashed (firmware/BUILD.md S4).
//   * PRESSED WHILE RUNNING -> starts the on-board joystick calibration routine
//     (loudest_micro.c, the SW14 + on-board calibration section; user-facing
//     procedure in firmware/BRING-UP.md).
// The two are separated IN TIME, not by any logic: at power-up our code does not
// exist yet, and once our code is running the mask ROM is long gone. A corollary
// the firmware relies on: a board executing this firmware necessarily booted
// with SW14 released.
// SW15 connects RUN to GND. That is a hardware reset - not readable by firmware
// and not touched by any of this.
//
// Keyboard-level EEPROM datablock holding the joystick calibration - exactly
// sizeof(loudest_js_cal_t) in loudest_micro.c, which asserts the two agree at
// compile time.
// WRITE POLICY (AMENDED 2026-08-15; adjudicated in docs/PROTOCOL-V1-CONTRACT.md,
// which is the source of truth): written ONLY on an accepted 0x51, on 0x52, and
// on a SUCCESSFUL SW14-triggered on-board calibration. The third path exists on
// the owner's directive - "You turn on calibration, it fucking calibrates, then
// it stores. End of story, calibrated usage does not depend on a daemon."
// The clause's intent is unchanged and still binding: every write is
// USER-INITIATED and RARE, and there is still no background, periodic,
// opportunistic or automatic calibration anywhere in the firmware.
// NOTE: VIA/Vial's EEPROM region starts at EECONFIG_SIZE (vial-qmk
// quantum/nvm/eeprom/nvm_eeprom_via_internal.h:12), which this block shifts by
// 14 bytes, so the first flash of a v1 build re-initialises Vial's dynamic
// keymap once. Documented consequence, not a defect.
#define EECONFIG_KB_DATA_SIZE 14

// Keep the ADC quiet enough that the placeholder center is stable on a breadboard.
#define JOYSTICK_AXIS_RESOLUTION 10

// --- Encoder direction (EC11 on GP13 = ENC_A / GP14 = ENC_B) ---
// This reflects the AS-BUILT A/B channel landing on v5_6, discovered at bring-up
// 2026-08-15: measured on the owner's assembled board, the pre-flip firmware
// produced volume-DOWN on a CLOCKWISE rotation. ENCODER_DIRECTION_FLIP swaps
// which quadrature walk the driver calls clockwise (vial-qmk
// drivers/encoder/encoder_quadrature.c:65-71), so CW is now volume UP.
// The pin map is NOT touched: pin_a/pin_b stay GP13/GP14 in keyboard.json,
// matching the board netlist and firmware/check_pins_v4.py's assertions -
// swapping the pins there would have flipped direction too but would have made
// the pin-map gate assert a net the board does not have.
#define ENCODER_DIRECTION_FLIP

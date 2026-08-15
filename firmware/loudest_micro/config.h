// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 Rev A - keyboard-level configuration.
//
// THE SHIPPED BOARD IS v5/hardware/pcb/v5_6.kicad_pcb (md5
// 221ebb98fcf44f860ed65f7ed8d1bc45) -- check this tree against THAT file. The
// pin map is UNCHANGED from v4 and was re-verified 20/20 GPIO directly against
// v5_6 on 2026-08-13 (v5/V5-NOTES.md, firmware-verification pass, Task 3), so
// the Layer 4 per-GPIO table in hardware/pcb/v4/ORDER-READINESS.md is where the
// map came from and still describes v5_6 correctly.
// (CORRECTED 2026-08-13: these two lines used to read "Pin map source of truth:
// hardware/pcb/v4/ORDER-READINESS.md (Layer 4 per-GPIO table, board v4_r27)",
// naming a superseded board file as the thing to verify firmware against. The
// values were correct; the citation was not.)
#pragma once

// --- Joystick (analog 2-axis tilt gimbal on ADC) ---
// JS1 = YTL YA13-FL7.4-B5Ka(45-10)-R-Y06, LCSC C37323742, machine-placed THT.
// (Corrected 2026-07-19; this used to read "analog PSP-slider on ADC, planar"
// for the dropped Adafruit 3103 hand-solder part. Electrically identical from
// firmware's side: dual pot, wiper -> ADC. Axis DIRECTION may need inverting --
// see firmware/POLARITY-NOTE.md in the release; one-line flip, no rebuild.)
// Axes + placeholder calibration (512 center, 0..1023) live in keyboard.json
// ("joystick": {"driver": "analog", "axes": ...}) which auto-generates
// joystick_axes[]. JOYSTICK_AXIS_COUNT (=2) and JOYSTICK_BUTTON_COUNT (=0) are
// emitted from that block. Real low/rest/high values are CALIBRATION-PENDING
// (bring-up ADC sweep on the real module). Native QMK output is HID gamepad
// only; the arrow (8-way) and scroll modes are custom code in loudest_micro.c
// reading analogReadPin(GP26/GP27) (JS_MODE keycode).

// --- Touch (TTP223 U6 on GP16, injected at matrix [3,2]) ---
// BOARD TRUTH, read off v5_6.kicad_pcb: R10 (0R) straps TOUCH_AHLB -> GND. On a
// TTP223, AHLB low selects the ACTIVE-HIGH output, so GP16 idles LOW and drives
// HIGH while the pad is touched -- the OPPOSITE sense of the 13 switch-to-GND
// keys. (CORRECTED 2026-08-13: this comment used to read "the PCB straps the
// AHLB pad active-low ... idle high, touched low". That was wrong about this
// board, and because nothing inverted the read, [3,2] scanned as permanently
// pressed: the pad booted into layer 1, layer 0 was unreachable, and touch fired
// on finger lift. Corroborated by hardware/pcb/SCHEMATIC-REVIEW.md:156,
// BOM-FINAL.csv "AHLB strap (GND=active-high)", and the R10 symbol description.)
// QMK's only direct-pin polarity knob, MATRIX_INPUT_PRESSED_STATE, is GLOBAL --
// quantum/matrix.c applies it in readMatrixPin() to every direct pin -- so
// setting it would invert the 13 genuinely active-low switches. GP16 is
// therefore NOT a matrix pin (keyboard.json has matrix_pins.direct[3][2] = null)
// and loudest_micro.c polls it with its own active-high sense, injecting the
// press/release at the same logical position [3,2]. Keymaps, LAYOUT, matrix size
// and the rgb_matrix layout are unchanged. TP_TOG (custom keycode) still gates
// this key on/off.

// --- Raw HID status protocol v0 (device side of loudestd) ---
// LOCKED wire format - counterpart: daemon/loudestd/protocol.py. Handled in
// loudest_micro.c: 0x01 SET_KEY {chain_idx,r,g,b,effect} | 0x02 SET_LAYER {n} |
// 0x03 CLEAR | 0x04 PING {token} -> CAPS {token,'L','D',ver,led_count,layers,feat}.
// Pin the QMK Raw HID descriptor to the values the daemon opens (already the QMK
// defaults; declared here so the contract is explicit and cannot silently drift).
#define RAW_USAGE_PAGE 0xFF60
#define RAW_USAGE_ID 0x61

// Keep the ADC quiet enough that the placeholder center is stable on a breadboard.
#define JOYSTICK_AXIS_RESOLUTION 10

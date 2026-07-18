// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 Rev A - keyboard-level configuration. Pin map source of truth:
// hardware/pcb/v4/ORDER-READINESS.md (Layer 4 per-GPIO table, board v4_r27).
#pragma once

// --- Joystick (analog PSP-slider on ADC, planar) ---
// Axes + placeholder calibration (512 center, 0..1023) live in keyboard.json
// ("joystick": {"driver": "analog", "axes": ...}) which auto-generates
// joystick_axes[]. JOYSTICK_AXIS_COUNT (=2) and JOYSTICK_BUTTON_COUNT (=0) are
// emitted from that block. Real low/rest/high values are CALIBRATION-PENDING
// (bring-up ADC sweep on the real module). Native QMK output is HID gamepad
// only; the arrow (8-way) and scroll modes are custom code in loudest_micro.c
// reading analogReadPin(GP26/GP27) (JS_MODE keycode).

// --- Touch (TTP223 on GP16, matrix row 3, key [3,2]) ---
// The PCB straps the AHLB pad active-low, so the pad reads like a normal direct
// pin (idle high, touched low). If a batch ships without the strap, invert in the
// matrix read. TP_TOG (custom keycode) gates this key on/off.

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

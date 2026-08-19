// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 Rev A - shared keyboard-level definitions.
// (QMK keyboard/module name stays "loudest_micro"; see readme.md.)
#pragma once

#include "quantum.h"

#if defined(RAW_ENABLE) && defined(VIA_ENABLE)
// Pre-VIA raw HID dispatch hook (upstream QMK mechanism; backported into the
// vial-qmk fork by firmware/patches/0001-via-command-kb-backport.patch).
// Returns true when the frame was fully handled, including any reply.
bool via_command_kb(uint8_t *data, uint8_t length);
#endif

// Keyboard-level custom keycodes (shared by the default and vial keymaps).
// QK_KB_0.. is the keyboard custom range; these also appear in vial.json
// customKeycodes as USER00/USER01 so the Vial GUI can bind them.
enum loudest_keycodes {
    JS_MODE = QK_KB_0, // cycle joystick mode: gamepad -> arrows (8-way) -> scroll
    TP_TOG,            // enable/disable the GP16 touch key
};

// ---------------------------------------------------------------------------
// Raw-HID status protocol v1 - LOCKED. Wire counterpart and single source of
// truth: daemon/loudestd/protocol.py, with docs/PROTOCOL-V1-CONTRACT.md as the
// contract both sides are written against. Do NOT change framing/opcodes/CAPS
// layout on one side without updating the other.
// v1 (2026-08-15) added 0x50/0x51/0x52 (joystick calibration) and bumped the
// CAPS protocol_version byte; every v0 frame is unchanged byte-for-byte.
//
// LED addressing is by RAW CHAIN POSITION. Because keyboard.json authors
// rgb_matrix.layout in chain order, the chain index equals the rgb_matrix LED
// index, so no on-device remap is needed:
//   0..12  per-key SW1..SW13 | 13 layer indicator | 14..23 underglow
// ---------------------------------------------------------------------------
// LOUDEST_LED_COUNT is the ADDRESSABLE CHAIN LENGTH, not the populated-LED
// count, and it is 24 on BOTH SKUs. That is electrically true on both: the
// translucent SKU populates LED1-24, and on the opaque SKU (LED1-14 only, per
// the populate-per-variant CPL rows) LED14's DOUT still clocks pixels 14-23 out
// into an unpopulated pad, so host writes to indexes 14-23 are harmless no-ops
// rather than errors. CAPS.led_count therefore reports 24 everywhere.
// (Finding 4 of the 2026-08-13 firmware-verification pass -- "CAPS.led_count =
// 24 misinforms loudestd on opaque units" -- CLOSED-BY-DECISION 2026-08-15:
// this byte is part of LOCKED protocol v0, and forking per-SKU UF2s would
// multiply the shipped artifacts against the drag-and-drop standard for zero
// visible benefit.)
#define LOUDEST_LED_COUNT     24   // addressable chain length (CAPS led_count)
#define LOUDEST_LED_INDICATOR 13   // layer-indicator chain position
#define LOUDEST_PROTO_VERSION 1    // CAPS protocol_version (v1, was 0 before 2026-08-15)
#define LOUDEST_CAPS_MAGIC0   0x4C // 'L'
#define LOUDEST_CAPS_MAGIC1   0x44 // 'D'
// CAPS features bitfield: PER_KEY|UNDERGLOW|LAYER_INDICATOR|JOYSTICK|ENCODER.
#define LOUDEST_CAPS_FEATURES 0x1F

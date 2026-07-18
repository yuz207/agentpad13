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
// Raw-HID status protocol v0 - LOCKED. Wire counterpart and single source of
// truth: daemon/loudestd/protocol.py. Do NOT change framing/opcodes/CAPS layout
// on one side without updating the other.
//
// LED addressing is by RAW CHAIN POSITION. Because keyboard.json authors
// rgb_matrix.layout in chain order, the chain index equals the rgb_matrix LED
// index, so no on-device remap is needed:
//   0..12  per-key SW1..SW13 | 13 layer indicator | 14..23 underglow
// ---------------------------------------------------------------------------
#define LOUDEST_LED_COUNT     24   // addressable LEDs (CAPS led_count)
#define LOUDEST_LED_INDICATOR 13   // layer-indicator chain position
#define LOUDEST_PROTO_VERSION 0    // CAPS protocol_version (v0)
#define LOUDEST_CAPS_MAGIC0   0x4C // 'L'
#define LOUDEST_CAPS_MAGIC1   0x44 // 'D'
// CAPS features bitfield: PER_KEY|UNDERGLOW|LAYER_INDICATOR|JOYSTICK|ENCODER.
#define LOUDEST_CAPS_FEATURES 0x1F

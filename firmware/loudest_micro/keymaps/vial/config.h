// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

// Generated with util/vial_generate_keyboard_uid.py (unique per keyboard model).
#define VIAL_KEYBOARD_UID {0x50, 0x96, 0xBD, 0xC2, 0x2C, 0x90, 0xCD, 0x13}

// Hold SW1 ([0,0]) + SW13 ([3,0]) to unlock Vial security.
#define VIAL_UNLOCK_COMBO_ROWS {0, 3}
#define VIAL_UNLOCK_COMBO_COLS {0, 0}

// >= 8 dynamic layers (spec 3.9). Dynamic keymaps live in emulated EEPROM and
// survive reflash (documented migration rule in BUILD.md).
#define DYNAMIC_KEYMAP_LAYER_COUNT 8

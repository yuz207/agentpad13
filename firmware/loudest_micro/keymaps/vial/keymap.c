// SPDX-License-Identifier: GPL-2.0-or-later
// Loudest Micro Rev A - Vial keymap. These layers are the compiled-in defaults
// loaded into the dynamic keymap on first boot; Vial then owns them in EEPROM.
// Layout + custom keycodes match the default keymap (see that file's header).
#include QMK_KEYBOARD_H

enum loudest_layers {
    L_BASE = 0,
    L_CTRL,
    L_NAV,
    L_U3,
    L_U4,
    L_U5,
    L_U6,
    L_U7,
};

// clang-format off
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [L_BASE] = LAYOUT(
        KC_F13, KC_F14, KC_F15, KC_F16,
        KC_F17, KC_F18, KC_F19, KC_F20,
        KC_F21, KC_F22, KC_F23, KC_F24,
        KC_MPLY,          KC_MUTE,        TO(L_CTRL)
    ),
    [L_CTRL] = LAYOUT(
        JS_MODE,  TP_TOG,   RGB_TOG,  RGB_MOD,
        RGB_HUI,  RGB_SAI,  RGB_VAI,  RGB_SPI,
        KC_MPRV,  KC_MPLY,  KC_MNXT,  KC_MSTP,
        TO(L_BASE),       KC_MUTE,        TO(L_NAV)
    ),
    [L_NAV] = LAYOUT(
        KC_HOME,  KC_UP,    KC_END,   KC_PGUP,
        KC_LEFT,  KC_DOWN,  KC_RGHT,  KC_PGDN,
        KC_DEL,   KC_INS,   KC_PSCR,  KC_APP,
        KC_ENT,           KC_MUTE,        TO(L_U3)
    ),
    [L_U3] = LAYOUT(
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS,          KC_TRNS,        TO(L_U4)
    ),
    [L_U4] = LAYOUT(
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS,          KC_TRNS,        TO(L_U5)
    ),
    [L_U5] = LAYOUT(
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS,          KC_TRNS,        TO(L_U6)
    ),
    [L_U6] = LAYOUT(
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS,          KC_TRNS,        TO(L_U7)
    ),
    [L_U7] = LAYOUT(
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS,          KC_TRNS,        TO(L_BASE)
    ),
};

#if defined(ENCODER_MAP_ENABLE)
const uint16_t PROGMEM encoder_map[][NUM_ENCODERS][NUM_DIRECTIONS] = {
    [L_BASE] = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [L_CTRL] = { ENCODER_CCW_CW(RGB_RMOD, RGB_MOD) },
    [L_NAV]  = { ENCODER_CCW_CW(KC_PGDN, KC_PGUP) },
    [L_U3]   = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [L_U4]   = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [L_U5]   = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [L_U6]   = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [L_U7]   = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
};
#endif
// clang-format on

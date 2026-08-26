// SPDX-License-Identifier: GPL-2.0-or-later
// Direct Codex Desktop OAI keymap for AgentPad13.
//
// The default build exposes CODEX, FN, NAV and MEDIA. Native Codex shortcuts
// are a routing fallback, not hidden layers; TP5 cycles the visible layers.
// Human layer 1 is L_CODEX (QMK index 0), the only layer owned by OAI RPC.
#include QMK_KEYBOARD_H

#include "codex_led.h"
#include "codex_oai.h"
#include "codex_rgb_cap.h"

#ifndef CODEX_EXTRA_LAYERS
#    define CODEX_EXTRA_LAYERS 2
#endif

/* Add user layers by increasing CODEX_EXTRA_LAYERS, adding their LAYOUT rows
 * below, and appending them to codex_layer_order. Two extension layers are
 * shipped; a third transparent custom layer remains available at build time. */
#if CODEX_EXTRA_LAYERS > 3
#    error "CODEX_EXTRA_LAYERS is limited to the three declared extension layers"
#endif
#define CODEX_LAYER_COUNT (2 + CODEX_EXTRA_LAYERS)

enum codex_layers {
    L_CODEX = 0,
    L_FN,
    L_USER2,
    L_USER3,
    L_USER4,
};

#define CODEX_OAI_LAYER L_CODEX

enum codex_oai_keycodes {
    /* QK_KB_0 and QK_KB_0+1 belong to loudest_micro (JS_MODE/TP_TOG). */
    /* Positions 0..12 follow the official Codex action order. Position 13 is
     * encoder click and position 14 remains the legacy protocol slot. */
    OAI_AG00 = QK_KB_0 + 2,
    OAI_AG01,
    OAI_AG02,
    OAI_AG03,
    OAI_AG04,
    OAI_AG05,
    OAI_ACT06,
    OAI_ACT07,
    OAI_ACT08,
    OAI_ACT09,
    OAI_ACT10,
    OAI_ACT11,
    OAI_ACT12,
    OAI_MICROPHONE,
    OAI_ENC,
    CODEX_TOUCH_LAYER,
};

enum codex_native_actions {
    CX_ACTION_PREVIOUS,
    CX_ACTION_NEXT,
    CX_ACTION_NEW,
    CX_ACTION_REVIEW,
    CX_ACTION_PLAN,
    CX_ACTION_IMPLEMENT,
    CX_ACTION_REFACTOR,
    CX_ACTION_TEST,
    CX_ACTION_ABORT,
    CX_ACTION_ACCEPT,
    CX_ACTION_SEND,
    CX_ACTION_TERMINAL,
    CX_ACTION_REASONING_DOWN,
    CX_ACTION_REASONING_UP,
};

#define CX_ACCEPT_TERM 600U
#define CX_NEW_HOLD_TERM TAPPING_TERM
#define CX_SAFE_ARM_TERM TAPPING_TERM
#define CX_WINDOWS_MAGIC 0x57494E31UL

#ifndef CODEX_FN_HERO
#    define CODEX_FN_HERO KC_MPLY
#endif

/* clang-format off */
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [L_CODEX] = LAYOUT(
        OAI_AG00, OAI_AG01, OAI_AG02, OAI_AG03,
        OAI_AG04, OAI_AG05, OAI_ACT06, OAI_ACT07,
        OAI_ACT08, OAI_ACT09, OAI_ACT10, OAI_ACT11,
        OAI_ACT12,       OAI_ENC,   CODEX_TOUCH_LAYER
    ),
    [L_FN] = LAYOUT(
        JS_MODE,  KC_F2,    KC_F3,    KC_F4,
        KC_F5,    KC_F6,    KC_F7,    KC_F8,
        KC_F9,    KC_F10,   KC_F11,   KC_F12,
        CODEX_FN_HERO,       OAI_ENC, CODEX_TOUCH_LAYER
    ),
#if CODEX_EXTRA_LAYERS > 0
    [L_USER2] = LAYOUT(
        KC_ESC,  KC_HOME, KC_UP,   KC_END,
        KC_LEFT, KC_DOWN, KC_RGHT, KC_PGUP,
        KC_PGDN, KC_DEL,  KC_BSPC, TP_TOG,
        KC_TRNS,           OAI_ENC, CODEX_TOUCH_LAYER
    ),
#endif
#if CODEX_EXTRA_LAYERS > 1
    [L_USER3] = LAYOUT(
        KC_MUTE, KC_VOLD, KC_VOLU, KC_MPLY,
        KC_MPRV, KC_MNXT, KC_MSTP, KC_CALC,
        RGB_TOG, RGB_MOD, RGB_HUI, RGB_HUD,
        KC_TRNS,           OAI_ENC, CODEX_TOUCH_LAYER
    ),
#endif
#if CODEX_EXTRA_LAYERS > 2
    [L_USER4] = LAYOUT(
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,
        KC_TRNS, KC_TRNS, KC_TRNS, TP_TOG,
        KC_TRNS,           OAI_ENC, CODEX_TOUCH_LAYER
    ),
#endif
};
/* clang-format on */

static const uint8_t codex_layer_order[CODEX_LAYER_COUNT] = {
    L_CODEX,
    L_FN,
#if CODEX_EXTRA_LAYERS > 0
    L_USER2,
#endif
#if CODEX_EXTRA_LAYERS > 1
    L_USER3,
#endif
#if CODEX_EXTRA_LAYERS > 2
    L_USER4,
#endif
};

static uint32_t accept_timer;
static uint32_t new_timer;
static uint32_t safe_timer;
static bool     safe_pressed;
static bool     codex_armed;
static bool     windows_mode;
static uint8_t  oai_layer;

static uint8_t oai_state_revision;
static uint8_t oai_error_revision;
static uint8_t oai_handshake_revision;
static oai_link_state_t oai_link_state;

static bool task_is_active(const codex_oai_task_t *task) {
    return task->brightness != 0U && task->effect != 0U &&
           (task->red != 0U || task->green != 0U || task->blue != 0U);
}

static void sync_oai_leds(uint32_t now_ms) {
    codex_oai_task_t tasks[OAI_SLOT_COUNT];
    uint8_t active_mask = 0;

    for (uint8_t slot = 0; slot < OAI_SLOT_COUNT; ++slot) {
        (void)codex_oai_task_for_slot(slot, &tasks[slot]);
        if (task_is_active(&tasks[slot])) {
            active_mask |= (uint8_t)(1U << slot);
        }
    }
    codex_led_set_tasks(tasks, active_mask, now_ms);
    oai_link_state = codex_oai_link_state();
    codex_led_set_link(oai_link_state, now_ms);
}

static void tap_codex_primary(uint16_t keycode) {
    tap_code16(windows_mode ? LCTL(keycode) : LGUI(keycode));
}

#ifndef CODEX_TERMINAL_ACTION
#    define CODEX_TERMINAL_ACTION() tap_code16(LCTL(KC_GRV))
#endif

static void native_action(uint8_t action) {
    switch (action) {
        case CX_ACTION_PREVIOUS: tap_codex_primary(LSFT(KC_LBRC)); break;
        case CX_ACTION_NEXT: tap_codex_primary(LSFT(KC_RBRC)); break;
        case CX_ACTION_NEW: tap_codex_primary(KC_N); break;
        case CX_ACTION_REVIEW: tap_code16(LCTL(LSFT(KC_G))); break;
        case CX_ACTION_PLAN: tap_code16(windows_mode ? LSFT(KC_TAB) : LCA(KC_P)); break;
        case CX_ACTION_IMPLEMENT:
            SEND_STRING("Implementa la tarea y verifica el resultado.");
            tap_code(KC_ENT);
            break;
        case CX_ACTION_REFACTOR:
            SEND_STRING("Refactoriza sin cambiar comportamiento.");
            tap_code(KC_ENT);
            break;
        case CX_ACTION_TEST:
            SEND_STRING("Ejecuta las pruebas relevantes.");
            tap_code(KC_ENT);
            break;
        case CX_ACTION_ABORT: tap_code(KC_ESC); break;
        case CX_ACTION_ACCEPT:
        case CX_ACTION_SEND: tap_code(KC_ENT); break;
        case CX_ACTION_TERMINAL: CODEX_TERMINAL_ACTION(); break;
        case CX_ACTION_REASONING_DOWN: tap_code16(windows_mode ? LCA(KC_F23) : LCA(KC_MINS)); break;
        case CX_ACTION_REASONING_UP: tap_code16(windows_mode ? LCA(KC_F24) : LCA(KC_EQL)); break;
    }
}

static void clear_codex_arm(void) {
    safe_pressed = false;
    codex_armed = false;
}

static void select_codex_layer(uint8_t layer) {
    if (layer >= CODEX_LAYER_COUNT) {
        layer = CODEX_OAI_LAYER;
    }
    layer_move(layer);
    oai_layer = layer;
    codex_led_set_layer(layer, timer_read32());
}

static void cycle_codex_layer(void) {
    uint8_t current = get_highest_layer(layer_state | default_layer_state);
    uint8_t selected = 0;

    for (uint8_t index = 0; index < CODEX_LAYER_COUNT; ++index) {
        if (codex_layer_order[index] == current) {
            selected = (uint8_t)((index + 1U) % CODEX_LAYER_COUNT);
            break;
        }
    }
    select_codex_layer(codex_layer_order[selected]);
}

static bool native_control(codex_oai_control_t control, bool pressed) {
    if (!pressed) {
        switch (control) {
            case OAI_CONTROL_AG02:
                if (timer_elapsed32(new_timer) >= CX_NEW_HOLD_TERM) {
                    native_action(CX_ACTION_TERMINAL);
                } else {
                    native_action(CX_ACTION_NEW);
                }
                break;
            case OAI_CONTROL_ACT09:
                clear_codex_arm();
                break;
            default:
                break;
        }
        return false;
    }

    switch (control) {
        case OAI_CONTROL_AG00: native_action(CX_ACTION_PREVIOUS); break;
        case OAI_CONTROL_AG01: native_action(CX_ACTION_NEXT); break;
        case OAI_CONTROL_AG02: new_timer = timer_read32(); break;
        case OAI_CONTROL_AG03: native_action(CX_ACTION_REVIEW); break;
        case OAI_CONTROL_AG04: native_action(CX_ACTION_PLAN); break;
        case OAI_CONTROL_AG05: native_action(CX_ACTION_IMPLEMENT); break;
        case OAI_CONTROL_ACT06: native_action(CX_ACTION_REFACTOR); break;
        case OAI_CONTROL_ACT07: native_action(CX_ACTION_TEST); break;
        case OAI_CONTROL_ACT08: native_action(CX_ACTION_ABORT); break;
        case OAI_CONTROL_ACT09:
            safe_pressed = true;
            codex_armed = false;
            safe_timer = timer_read32();
            break;
        case OAI_CONTROL_ACT10:
            /* ACCEPT is protected and is handled on release below. */
            break;
        case OAI_CONTROL_ACT11:
            /* ACT11 is a second official microphone contact. */
            break;
        case OAI_CONTROL_ACT12:
            native_action(CX_ACTION_SEND);
            break;
        case OAI_CONTROL_ENCODER:
        case OAI_CONTROL_ENCODER_CW:
        case OAI_CONTROL_ENCODER_CCW:
        case OAI_CONTROL_COUNT:
            break;
    }
    return false;
}

static bool notify_or_native(codex_oai_control_t control, bool pressed) {
    if (codex_oai_ready()) {
        return codex_oai_notify(control, pressed);
    }
    return native_control(control, pressed);
}

static bool notify_encoder_press(bool pressed) {
    if (codex_oai_ready()) {
        return codex_oai_notify(OAI_CONTROL_ENCODER, pressed);
    }
    return false;
}

static bool handle_oai_control(codex_oai_control_t control, bool pressed, uint8_t feedback_led) {
    if (feedback_led != 0U) {
        codex_led_note_action(feedback_led, pressed, timer_read32());
    }
    return notify_or_native(control, pressed);
}

static int8_t codex_oai_position_for_keycode(uint16_t keycode, const keyrecord_t *record) {
    uint8_t row = record == NULL ? 0U : record->event.key.row;
    uint8_t col = record == NULL ? 0U : record->event.key.col;
    switch (keycode) {
        case OAI_AG00: return row == 3U && col == 2U ? 14 : 0;
        case OAI_AG01: return 1;
        case OAI_AG02: return 2;
        case OAI_AG03: return 3;
        case OAI_AG04: return 4;
        case OAI_AG05: return 5;
        case OAI_ACT06: return 6;
        case OAI_ACT07: return 7;
        case OAI_ACT08: return 8;
        case OAI_ACT09: return 9;
        case OAI_ACT10: return 10;
        case OAI_ACT11: return 11;
        case OAI_ACT12: return 12;
        case OAI_MICROPHONE: return 12; /* legacy/custom alias */
        case OAI_ENC: return 13;
        default: return -1;
    }
}

static bool codex_oai_control_for_action(uint8_t action, codex_oai_control_t *control) {
    if (control == NULL || action < OAI_KEYMAP_PREVIOUS || action >= OAI_KEYMAP_ACTION_COUNT) {
        return false;
    }
    if (action <= OAI_KEYMAP_ABORT) {
        *control = (codex_oai_control_t)(OAI_CONTROL_AG00 + action - OAI_KEYMAP_PREVIOUS);
    } else if (action == OAI_KEYMAP_SAFE) {
        *control = OAI_CONTROL_ACT09;
    } else if (action == OAI_KEYMAP_ACCEPT) {
        *control = OAI_CONTROL_ACT10;
    } else if (action == OAI_KEYMAP_MICROPHONE) {
        *control = OAI_CONTROL_ACT10;
    } else if (action == OAI_KEYMAP_ACT11) {
        *control = OAI_CONTROL_ACT11;
    } else if (action == OAI_KEYMAP_SEND) {
        *control = OAI_CONTROL_ACT12;
    } else {
        *control = OAI_CONTROL_ENCODER;
    }
    return true;
}

static uint8_t codex_oai_feedback_led(uint8_t position) {
    /* The first six physical keys own task-state LEDs.  Feedback follows the
     * physical function-key positions so custom OAI maps cannot make a task
     * key flash white or leave a function key dark. */
    if (position < CODEX_ACTION_FEEDBACK_FIRST || position > CODEX_ACTION_FEEDBACK_LAST) {
        return 0;
    }
    return position;
}

static bool handle_dynamic_oai_position(uint8_t position, keyrecord_t *record) {
    bool pressed = record->event.pressed;
    uint8_t action = codex_oai_keymap_action_for_position(position);
    codex_oai_control_t control;

    if (action == OAI_KEYMAP_NOOP || !codex_oai_control_for_action(action, &control)) {
        return false;
    }
    if (action == OAI_KEYMAP_ACCEPT) {
        uint8_t feedback_led = codex_oai_feedback_led(position);
        if (pressed) {
            accept_timer = timer_read32();
            if (feedback_led != 0U) {
                codex_led_note_action(feedback_led, true, timer_read32());
            }
            if (codex_oai_ready()) {
                (void)codex_oai_notify(OAI_CONTROL_ACT10, true);
            }
        } else if (codex_oai_ready()) {
            if (feedback_led != 0U) {
                codex_led_note_action(feedback_led, false, timer_read32());
            }
            (void)codex_oai_notify(OAI_CONTROL_ACT10, false);
        } else if (codex_armed || timer_elapsed32(accept_timer) >= CX_ACCEPT_TERM) {
            native_action(CX_ACTION_ACCEPT);
        }
        return false;
    }
    if (action == OAI_KEYMAP_ENCODER) {
        (void)notify_encoder_press(pressed);
        return false;
    }
    if (action == OAI_KEYMAP_SEND && !pressed && !codex_oai_ready()) {
        return false;
    }
    return handle_oai_control(control, pressed, codex_oai_feedback_led(position));
}

void eeconfig_init_user(void) {
    eeconfig_update_user(0);
    codex_oai_reset_keymap();
}

void keyboard_post_init_user(void) {
    windows_mode = eeconfig_read_user() == CX_WINDOWS_MAGIC;
    /* The Codex task/link renderer is the normal RGB owner.  Enable it only
     * in RAM so a previous RGB-off setting cannot hide task LEDs after the
     * startup diagnostic; no EEPROM setting is changed. */
    if (!rgb_matrix_is_enabled()) {
        rgb_matrix_enable_noeeprom();
    }
    codex_oai_init();
    codex_led_init();
    /* Reset both QMK layer-state sources in RAM.  layer_move(0) alone cannot
     * override a previously persisted default layer because consumers use
     * layer_state | default_layer_state to select their active layer. */
    default_layer_set(1UL << CODEX_OAI_LAYER);
    select_codex_layer(CODEX_OAI_LAYER);
    codex_led_startup_begin(timer_read32());
    oai_state_revision = codex_oai_state_revision();
    oai_error_revision = codex_oai_error_revision();
    oai_handshake_revision = codex_oai_handshake_revision();
    oai_link_state = codex_oai_link_state();
    sync_oai_leds(timer_read32());
}

void matrix_scan_user(void) {
    if (!codex_oai_ready() && safe_pressed && !codex_armed && timer_elapsed32(safe_timer) >= CX_SAFE_ARM_TERM) {
        codex_armed = true;
    }
}

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    bool pressed = record->event.pressed;
    int8_t oai_position = codex_oai_position_for_keycode(keycode, record);

    if (oai_position >= 0) {
        return handle_dynamic_oai_position((uint8_t)oai_position, record);
    }

    switch (keycode) {
        case CODEX_TOUCH_LAYER:
            /* The TTP223 can emit one settling edge as USB power rises.  The
             * startup sweep is the deliberate input-free interval, so ignore
             * it rather than letting that edge cycle a fresh CODEX boot to
             * FN. */
            if (pressed && !codex_led_startup_active(timer_read32())) {
                cycle_codex_layer();
            }
            return false;
        default:
            return true;
    }
}

CODEX_OAI_KEEP bool encoder_update_user(uint8_t index, bool clockwise) {
    if (index != 0U) {
        return false;
    }
    switch (get_highest_layer(layer_state | default_layer_state)) {
        case L_FN:
            tap_code16(clockwise ? KC_WH_D : KC_WH_U);
            break;
        case L_USER2:
            tap_code16(clockwise ? KC_PGDN : KC_PGUP);
            break;
        case L_USER3:
            tap_code16(clockwise ? KC_VOLU : KC_VOLD);
            break;
        default:
            if (codex_oai_ready()) {
                (void)codex_oai_notify(clockwise ? OAI_CONTROL_ENCODER_CW : OAI_CONTROL_ENCODER_CCW, true);
            } else {
                native_action(clockwise ? CX_ACTION_REASONING_UP : CX_ACTION_REASONING_DOWN);
            }
            break;
    }
    return false;
}

void housekeeping_task_user(void) {
    uint32_t now_ms = timer_read32();
    uint8_t state_revision = codex_oai_state_revision();
    uint8_t error_revision = codex_oai_error_revision();
    uint8_t handshake_revision = codex_oai_handshake_revision();
    oai_link_state_t link_state = codex_oai_link_state();
    uint8_t active_layer = get_highest_layer(layer_state | default_layer_state);
    bool handshake_changed = handshake_revision != oai_handshake_revision;

    if (active_layer != oai_layer) {
        oai_layer = active_layer;
        codex_led_set_layer(active_layer, now_ms);
    }

    if (handshake_changed) {
        codex_led_reset_tasks(timer_read32());
        oai_handshake_revision = handshake_revision;
    }
    if (state_revision != oai_state_revision || error_revision != oai_error_revision || link_state != oai_link_state || handshake_changed) {
        oai_state_revision = state_revision;
        oai_error_revision = error_revision;
        sync_oai_leds(now_ms);
    }
}

bool rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max) {
    codex_led_rgb_t frame[CODEX_LED_COUNT];
    uint8_t current_value = rgb_matrix_get_val();
    codex_led_render(timer_read32(), frame);

    for (uint8_t led = led_min; led < led_max && led < CODEX_LED_COUNT; ++led) {
        rgb_matrix_set_color(
            led,
            codex_rgb_cap_channel(frame[led].r, current_value, RGB_MATRIX_MAXIMUM_BRIGHTNESS),
            codex_rgb_cap_channel(frame[led].g, current_value, RGB_MATRIX_MAXIMUM_BRIGHTNESS),
            codex_rgb_cap_channel(frame[led].b, current_value, RGB_MATRIX_MAXIMUM_BRIGHTNESS)
        );
    }
    return true;
}

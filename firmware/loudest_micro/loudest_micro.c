// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 Rev A - shared keyboard-level firmware.
//
// Lives at keyboard level (not keymap) so the default and vial keymaps share one
// implementation. The keyboard-level _kb hooks are used (rather than _user
// hooks in each keymap) so both keymaps inherit the behavior. Each _kb hook
// still calls through to its _user counterpart.
#include "loudest_micro.h"
#include "analog.h"
#include <string.h>

#ifdef RAW_ENABLE
#    include "raw_hid.h"
#endif

// ---------------------------------------------------------------------------
// Layer count (bound for SET_LAYER). Vial supplies DYNAMIC_KEYMAP_LAYER_COUNT;
// the plain QMK keymap defines 8 layers in its keymaps[] array.
// ---------------------------------------------------------------------------
#ifdef DYNAMIC_KEYMAP_LAYER_COUNT
#    define LOUDEST_MAX_LAYERS DYNAMIC_KEYMAP_LAYER_COUNT
#else
#    define LOUDEST_MAX_LAYERS 8
#endif

// ---------------------------------------------------------------------------
// Raw-HID status protocol v0 - device side of loudestd. LOCKED wire
// format; the single source of truth is daemon/loudestd/protocol.py. 32-byte
// report-ID-less frames:
//   0x01 SET_KEY   {chain_idx(0..23), r, g, b, effect(0 solid / 1 pulse / 2 blink)}
//   0x02 SET_LAYER {n}
//   0x03 CLEAR
//   0x04 PING      {token} -> CAPS {token, 'L','D', proto_ver, led_count,
//                                   layer_count, features}
// ---------------------------------------------------------------------------
enum loudest_cmd {
    LOUDEST_CMD_SET_KEY   = 0x01,
    LOUDEST_CMD_SET_LAYER = 0x02,
    LOUDEST_CMD_CLEAR     = 0x03,
    LOUDEST_CMD_PING      = 0x04,
};

enum loudest_effect {
    LOUDEST_FX_SOLID = 0,
    LOUDEST_FX_PULSE = 1,
    LOUDEST_FX_BLINK = 2,
};

// Raw-HID report length (matches the 32-byte RAW_EPSIZE endpoint).
#define LOUDEST_REPORT_LEN 32

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t effect;
    bool    active;
} loudest_status_t;

// Status colors pushed from the host, one slot per addressable LED across the
// whole chain (0..23: per-key, layer indicator, underglow). Justified device
// state, not incidental globals: this is the live agent-status display the
// product is built around. SET_KEY.index indexes this array == rgb_matrix LED.
static loudest_status_t loudest_status[LOUDEST_LED_COUNT];

#ifdef RAW_ENABLE
static void loudest_status_handle(uint8_t *data, uint8_t length) {
    if (length < 1) {
        return;
    }
    switch (data[0]) {
        case LOUDEST_CMD_SET_KEY:
            if (length >= 6 && data[1] < LOUDEST_LED_COUNT) {
                loudest_status[data[1]] = (loudest_status_t){
                    .r = data[2], .g = data[3], .b = data[4], .effect = data[5], .active = true};
            }
            break;
        case LOUDEST_CMD_SET_LAYER:
            if (length >= 2 && data[1] < LOUDEST_MAX_LAYERS) {
                layer_move(data[1]);
            }
            break;
        case LOUDEST_CMD_CLEAR:
            memset(loudest_status, 0, sizeof(loudest_status));
            break;
        case LOUDEST_CMD_PING: {
            // CAPS reply, byte-for-byte per daemon/loudestd/protocol.py build_caps():
            // [0x04, token, 'L', 'D', proto_ver, led_count, layer_count, features].
            uint8_t resp[LOUDEST_REPORT_LEN];
            memset(resp, 0, sizeof(resp));
            resp[0] = LOUDEST_CMD_PING;              // echo PING command id
            resp[1] = (length >= 2) ? data[1] : 0;   // echo token
            resp[2] = LOUDEST_CAPS_MAGIC0;           // 'L'
            resp[3] = LOUDEST_CAPS_MAGIC1;           // 'D'
            resp[4] = LOUDEST_PROTO_VERSION;         // 0
            resp[5] = LOUDEST_LED_COUNT;             // 24
            resp[6] = LOUDEST_MAX_LAYERS;            // 8
            resp[7] = LOUDEST_CAPS_FEATURES;         // 0x1F
            raw_hid_send(resp, sizeof(resp));
            break;
        }
        default:
            break;
    }
}

#    ifdef VIA_ENABLE
// --- VIA/Vial coexistence (the "VIA shadow" fix) ---------------------------
// Under VIA/Vial the strong raw_hid_receive() belongs to via.c, whose command
// switch consumes IDs 0x01-0x04 (id_get_protocol_version, id_get/
// id_set_keyboard_value, id_dynamic_keymap_get_keycode) before the
// raw_hid_receive_kb() fallback ever sees them - which used to shadow the
// entire status protocol in the vial build. Fix per upstream QMK practice:
// the via_command_kb() pre-hook (mainline QMK; backported into the vial-qmk
// fork by firmware/patches/0001-via-command-kb-backport.patch) sees every
// frame before VIA parses it and claims only frames that are byte-valid v0
// protocol commands (32-byte zero-padded, per daemon/loudestd/protocol.py).
//
// Dispatch rules, from the observed VIA/Vial client traffic (vial-gui sends
// 0x01 with an all-zero payload at connect, 0x02 only with value ids 0x02
// layout_options / 0x03 switch_matrix_state, 0x03 only with nonzero value
// ids, and never sends per-key 0x04 - it bulk-reads keymaps via 0x12):
//   0x01 SET_KEY   -> ours iff payload is a valid {index<24, r,g,b, fx<=2}
//                     and NOT the all-zero VIA protocol-version handshake.
//   0x02 SET_LAYER -> ours iff layer < LOUDEST_MAX_LAYERS, EXCEPT layers
//                     1/2/3 which are byte-identical to the VIA keyboard
//                     value ids uptime/layout_options/switch_matrix_state
//                     and stay VIA's (documented vial-build limitation;
//                     the plain-QMK build has the full range).
//   0x03 CLEAR     -> ours iff the payload is all zero (VIA set_keyboard_
//                     value ids start at 0x01).
//   0x04 PING      -> ours iff bytes 2.. are zero (vial-gui never sends
//                     per-key get_keycode; a legacy VIA client reading key
//                     [row 0, col 0] would collide - documented).
// Frames we claim are fully handled here (incl. the CAPS reply); VIA never
// sees them and sends no echo, exactly like the plain-QMK build.
static bool loudest_tail_zero(const uint8_t *data, uint8_t from, uint8_t upto) {
    for (uint8_t i = from; i < upto; i++) {
        if (data[i] != 0) {
            return false;
        }
    }
    return true;
}

bool via_command_kb(uint8_t *data, uint8_t length) {
    switch (data[0]) {
        case LOUDEST_CMD_SET_KEY:
            if (length >= 6 && data[1] < LOUDEST_LED_COUNT && data[5] <= LOUDEST_FX_BLINK && loudest_tail_zero(data, 6, length) && !loudest_tail_zero(data, 1, 6)) {
                loudest_status_handle(data, length);
                return true;
            }
            return false; // incl. all-zero payload = VIA get_protocol_version
        case LOUDEST_CMD_SET_LAYER:
            if (length >= 2 && data[1] < LOUDEST_MAX_LAYERS && data[1] != 0x01 && data[1] != 0x02 && data[1] != 0x03 && loudest_tail_zero(data, 2, length)) {
                loudest_status_handle(data, length);
                return true;
            }
            return false; // 0x01-0x03 = VIA uptime/layout_options/matrix_state
        case LOUDEST_CMD_CLEAR:
            if (loudest_tail_zero(data, 1, length)) {
                loudest_status_handle(data, length);
                return true;
            }
            return false; // nonzero value id = VIA set_keyboard_value
        case LOUDEST_CMD_PING:
            if (length >= 2 && loudest_tail_zero(data, 2, length)) {
                loudest_status_handle(data, length);
                return true;
            }
            return false; // nonzero row/col = VIA dynamic_keymap_get_keycode
        default:
            return false; // everything else (incl. 0xFE vial prefix) is VIA's
    }
}

// Fallback for frames VIA's inner switches forward (e.g. a get_keyboard_value
// id VIA does not know). The bounds checks in loudest_status_handle() make
// stray VIA frames harmless here.
void raw_hid_receive_kb(uint8_t *data, uint8_t length) {
    loudest_status_handle(data, length);
}
#    else
// Plain QMK build (no VIA): we own the weak raw_hid_receive() outright.
void raw_hid_receive(uint8_t *data, uint8_t length) {
    loudest_status_handle(data, length);
}
#    endif
#endif // RAW_ENABLE

// ---------------------------------------------------------------------------
// Joystick modes. Native QMK exposes GP26/GP27 as a HID gamepad; the arrow
// (8-way) and scroll modes are custom code reading analogReadPin. JS_MODE
// cycles gamepad -> arrows -> scroll. CALIBRATION-PENDING: real deadzone/curve
// from the bring-up ADC sweep; RP2040 analogReadPin is 10-bit so center ~512
// is the placeholder.
// ---------------------------------------------------------------------------
enum js_mode {
    JS_MODE_GAMEPAD = 0,
    JS_MODE_ARROWS,
    JS_MODE_SCROLL,
    JS_MODE_COUNT,
};

#define JS_CENTER 512
#define JS_THRESHOLD 300         // deflection from center to trigger (placeholder)
#define JS_SCROLL_INTERVAL_MS 120

static uint8_t js_mode = JS_MODE_GAMEPAD;

// arrow order: up, down, left, right
static const uint16_t js_arrow_kc[4] = {KC_UP, KC_DOWN, KC_LEFT, KC_RIGHT};
static bool           js_arrow_held[4];

static void js_release_arrows(void) {
    for (uint8_t i = 0; i < 4; i++) {
        if (js_arrow_held[i]) {
            unregister_code16(js_arrow_kc[i]);
            js_arrow_held[i] = false;
        }
    }
}

static void js_cycle_mode(void) {
    js_release_arrows();
    js_mode = (js_mode + 1) % JS_MODE_COUNT;
}

// ---------------------------------------------------------------------------
// Touch enable/disable. TP_TOG gates the GP16 touch key
// at matrix [3, 2]. Default enabled.
// ---------------------------------------------------------------------------
#define TOUCH_MATRIX_ROW 3
#define TOUCH_MATRIX_COL 2

static bool touch_enabled = true;

bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    // Swallow the touch key entirely (press and release) while touch is disabled.
    if (record->event.key.row == TOUCH_MATRIX_ROW && record->event.key.col == TOUCH_MATRIX_COL && !touch_enabled) {
        return false;
    }

    switch (keycode) {
        case JS_MODE:
            if (record->event.pressed) {
                js_cycle_mode();
            }
            return false;
        case TP_TOG:
            if (record->event.pressed) {
                touch_enabled = !touch_enabled;
            }
            return false;
        default:
            break;
    }
    return process_record_user(keycode, record);
}

void housekeeping_task_kb(void) {
    if (js_mode != JS_MODE_GAMEPAD) {
        int16_t x = analogReadPin(GP26);
        int16_t y = analogReadPin(GP27);

        if (js_mode == JS_MODE_ARROWS) {
            bool want[4];
            want[0] = (y < JS_CENTER - JS_THRESHOLD); // up
            want[1] = (y > JS_CENTER + JS_THRESHOLD); // down
            want[2] = (x < JS_CENTER - JS_THRESHOLD); // left
            want[3] = (x > JS_CENTER + JS_THRESHOLD); // right
            for (uint8_t i = 0; i < 4; i++) {
                if (want[i] && !js_arrow_held[i]) {
                    register_code16(js_arrow_kc[i]);
                    js_arrow_held[i] = true;
                } else if (!want[i] && js_arrow_held[i]) {
                    unregister_code16(js_arrow_kc[i]);
                    js_arrow_held[i] = false;
                }
            }
        } else if (js_mode == JS_MODE_SCROLL) {
            static uint32_t last_scroll = 0;
            if (timer_elapsed32(last_scroll) >= JS_SCROLL_INTERVAL_MS) {
                uint16_t wheel = KC_NO;
                if (y < JS_CENTER - JS_THRESHOLD) {
                    wheel = KC_WH_U;
                } else if (y > JS_CENTER + JS_THRESHOLD) {
                    wheel = KC_WH_D;
                } else if (x < JS_CENTER - JS_THRESHOLD) {
                    wheel = KC_WH_L;
                } else if (x > JS_CENTER + JS_THRESHOLD) {
                    wheel = KC_WH_R;
                }
                if (wheel != KC_NO) {
                    tap_code16(wheel);
                    last_scroll = timer_read32();
                }
            }
        }
    }

    housekeeping_task_user();
}

// ---------------------------------------------------------------------------
// RGB matrix: draw host status colors over per-key LEDs, and color the layer
// indicator LED (chain index 13) by the active layer.
// ---------------------------------------------------------------------------
#ifdef RGB_MATRIX_ENABLE
static void loudest_apply_effect(const loudest_status_t *s, uint8_t *r, uint8_t *g, uint8_t *b) {
    switch (s->effect) {
        case LOUDEST_FX_PULSE: {
            // Triangle-wave breathing over ~1 s, plain integer math (no lib8tion dep).
            uint8_t phase  = (uint8_t)(timer_read() >> 2);
            uint8_t factor = phase < 128 ? (uint8_t)(phase * 2) : (uint8_t)((255 - phase) * 2);
            *r = (uint8_t)((uint16_t)s->r * factor / 255);
            *g = (uint8_t)((uint16_t)s->g * factor / 255);
            *b = (uint8_t)((uint16_t)s->b * factor / 255);
            break;
        }
        case LOUDEST_FX_BLINK: {
            bool on = ((timer_read() / 250) & 1) == 0; // 250 ms on / 250 ms off
            *r = on ? s->r : 0;
            *g = on ? s->g : 0;
            *b = on ? s->b : 0;
            break;
        }
        case LOUDEST_FX_SOLID:
        default:
            *r = s->r;
            *g = s->g;
            *b = s->b;
            break;
    }
}

bool rgb_matrix_indicators_advanced_kb(uint8_t led_min, uint8_t led_max) {
    // Host-driven status colors take over any addressed LED across the chain.
    for (uint8_t i = 0; i < LOUDEST_LED_COUNT; i++) {
        if (!loudest_status[i].active) {
            continue;
        }
        if (i < led_min || i >= led_max) {
            continue;
        }
        uint8_t r, g, b;
        loudest_apply_effect(&loudest_status[i], &r, &g, &b);
        rgb_matrix_set_color(i, r, g, b);
    }

    // Layer indicator: hue by active layer - only when the host hasn't claimed it.
    if (!loudest_status[LOUDEST_LED_INDICATOR].active && LOUDEST_LED_INDICATOR >= led_min && LOUDEST_LED_INDICATOR < led_max) {
        uint8_t layer = get_highest_layer(layer_state | default_layer_state);
        HSV     hsv   = {.h = (uint8_t)(layer * 32), .s = 255, .v = rgb_matrix_get_val()};
        RGB     rgb   = hsv_to_rgb(hsv);
        rgb_matrix_set_color(LOUDEST_LED_INDICATOR, rgb.r, rgb.g, rgb.b);
    }

    return rgb_matrix_indicators_advanced_user(led_min, led_max);
}
#endif // RGB_MATRIX_ENABLE

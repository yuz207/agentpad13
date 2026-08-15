// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 Rev A - shared keyboard-level firmware.
//
// Lives at keyboard level (not keymap) so the default and vial keymaps share one
// implementation. The keyboard-level _kb hooks are used (rather than _user
// hooks in each keymap) so both keymaps inherit the behavior.
//
// Each _kb hook here calls through to its _user counterpart -- EXCEPT
// housekeeping_task_kb(), which must not, because quantum/keyboard.c's
// housekeeping_task() calls _kb and _user itself. The rule is "call _user iff
// the weak _kb default we are overriding was its only caller"; that holds for
// keyboard_pre_init (quantum/keyboard.c:300-302), matrix_scan
// (quantum/matrix_common.c:40-42), process_record (quantum/quantum.c:190-192)
// and rgb_matrix_indicators_advanced (quantum/rgb_matrix/rgb_matrix.c:468-470),
// and does NOT hold for housekeeping_task. All five were re-verified against
// the vial-qmk fork's sources on 2026-08-15.
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
// Capacitive touch (TTP223 U6 -> GP16), presented at matrix [3, 2].
//
// WHY THIS IS NOT A MATRIX PIN. The fabricated board straps the TTP223 for
// ACTIVE-HIGH output: R10 (0R) ties TOUCH_AHLB -> GND on v5_6.kicad_pcb, and on
// a TTP223 an AHLB low selects active-high, so Q idles LOW and drives HIGH while
// the pad is touched. The 13 mechanical switches are the opposite - plain
// switch-to-GND, idle high, pressed low. QMK's direct-pin matrix has exactly one
// polarity knob, MATRIX_INPUT_PRESSED_STATE, and quantum/matrix.c applies it
// inside readMatrixPin() to EVERY direct pin, so using it here would invert all
// 13 switches to fix one input. Instead GP16 is removed from the scanned matrix
// (keyboard.json: matrix_pins.direct[3][2] = null) and polled below with its own
// sense, injecting the key event at the SAME logical position [3, 2].
//
// Nothing else moves: MATRIX_ROWS/COLS stay 4x4, LAYOUT still carries [3,2], and
// both keymaps keep their existing keycode there (the TO() layer chain). TP_TOG
// still gates the key, because process_record_kb() matches on row/col and
// action_exec(MAKE_KEYEVENT(...)) carries row/col unchanged. The one cost is
// that Vial's matrix tester cannot light [3,2] - it reads the scanned matrix[].
//
// (Before this change config.h and keyboard.json both asserted the strap was
// active-LOW while MATRIX_INPUT_PRESSED_STATE was defined nowhere, so QMK's
// default LOW-is-pressed made [3,2] read held from power-on: the pad booted into
// layer 1, layer 0 was unreachable, SW1 emitted nothing, and touch fired on
// finger lift. Fixed 2026-08-13; boards are already fabricated and populated, so
// the R10-to-+3V3 rework alternative is not available.)
// ---------------------------------------------------------------------------
#define TOUCH_MATRIX_ROW 3
#define TOUCH_MATRIX_COL 2
#define TOUCH_PIN GP16
#define TOUCH_PRESSED_STATE 1 // ACTIVE-HIGH per the R10 strap: HIGH == touched
#define TOUCH_DEBOUNCE_MS 5   // same window as QMK's default matrix DEBOUNCE

static bool touch_enabled = true;

void keyboard_pre_init_kb(void) {
    // GP16 is no longer in direct_pins, so matrix_init_pins() never configures
    // it. Pull-DOWN (not the matrix's pull-up): the output is active-high, so an
    // unpopulated or high-Z U6 must read as "not touched".
    gpio_set_pin_input_low(TOUCH_PIN);
    keyboard_pre_init_user();
}

// Runs once per matrix scan (quantum/matrix.c calls matrix_scan_kb() at the end
// of matrix_scan()), i.e. the touch input is sampled at exactly the same cadence
// as the real matrix keys.
void matrix_scan_kb(void) {
    static bool     touch_reported = false; // debounced state already injected
    static bool     touch_sample   = false; // previous raw sample
    static uint16_t touch_since    = 0;     // when the raw sample last changed

    const bool touch_raw = (gpio_read_pin(TOUCH_PIN) == TOUCH_PRESSED_STATE);
    if (touch_raw != touch_sample) {
        touch_sample = touch_raw;
        touch_since  = timer_read();
    } else if (touch_raw != touch_reported && timer_elapsed(touch_since) >= TOUCH_DEBOUNCE_MS) {
        touch_reported = touch_raw;
        action_exec(MAKE_KEYEVENT(TOUCH_MATRIX_ROW, TOUCH_MATRIX_COL, touch_reported));
    }

    matrix_scan_user();
}

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

    // DELIBERATELY NOT calling housekeeping_task_user() here. Unlike every other
    // _kb hook in this file, the weak housekeeping_task_kb() default is NOT the
    // only caller of the _user hook: quantum/keyboard.c:433-437
    //     void housekeeping_task(void) {
    //         housekeeping_task_modules();
    //         housekeeping_task_kb();     // :435 -> this function
    //         housekeeping_task_user();   // :436 -> the keymap's hook, already
    //     }
    // invokes BOTH itself, and the weak _kb default (quantum/keyboard.c:420) is
    // an empty body that calls nothing. Calling _user here as well made the
    // keymap hook run TWICE per loop.
    //
    // (FIXED 2026-08-15. Latent while no keymap defined the hook, but the
    // `calibrate` bring-up keymap now does -- it drains its typing queue there,
    // and only survived the double call because draining a queue is idempotent.
    // Ledgered 2026-08-13 as "a trap for anyone who later implements that hook
    // in a keymap"; this closes the trap.)
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

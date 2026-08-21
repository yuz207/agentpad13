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

// RP2040 hardware access for the SW14 runtime read (see the SW14 section far
// below). This is the SAME include set the in-tree driver that solves the
// identical hazard uses -- platforms/chibios/drivers/wear_leveling/
// wear_leveling_rp2040_flash.c:12-14 -- so it is known to coexist with QMK and
// ChibiOS in this build. __no_inline_not_in_flash_func and the
// IO_QSPI_GPIO_QSPI_SS_CTRL_* register macros arrive transitively through these
// three, exactly as they do there; do not add pico/platform.h or
// hardware/regs/io_qspi.h back, they are redundant.
// Host counterparts for the conformance harness live in
// firmware/tests/conformance/stubs/hardware/, so this file compiles off-target
// UNCONDITIONALLY -- there is no #ifdef splitting the real code from the tested
// code.
#include "hardware/sync.h"
#include "hardware/structs/ioqspi.h"
#include "hardware/structs/sio.h"

#if defined(RAW_ENABLE) && !defined(LOUDEST_CUSTOM_RAW_HID)
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
// Raw-HID status protocol v1 - device side of loudestd. LOCKED wire
// format; the single source of truth is daemon/loudestd/protocol.py, and
// docs/PROTOCOL-V1-CONTRACT.md is the contract both sides are written against.
// 32-byte report-ID-less frames:
//   0x01 SET_KEY   {chain_idx(0..23), r, g, b, effect(0 solid / 1 pulse / 2 blink)}
//   0x02 SET_LAYER {n}
//   0x03 CLEAR
//   0x04 PING      {token} -> CAPS {token, 'L','D', proto_ver, led_count,
//                                   layer_count, features}
// v1 (2026-08-15), joystick calibration - every v0 frame above is unchanged:
//   0x50 GET_JOYSTICK      {token} -> live ADC + stored calibration + thresholds
//   0x51 SET_CALIBRATION   {rest_x,rest_y,min_x,max_x,min_y,max_y} -> {status}
//   0x52 RESET_CALIBRATION -> {0x00}
// ---------------------------------------------------------------------------
#if (defined(RAW_ENABLE) && !defined(LOUDEST_CUSTOM_RAW_HID)) || (defined(RGB_MATRIX_ENABLE) && !defined(LOUDEST_CUSTOM_RGB_STATUS))
enum loudest_cmd {
    LOUDEST_CMD_SET_KEY   = 0x01,
    LOUDEST_CMD_SET_LAYER = 0x02,
    LOUDEST_CMD_CLEAR     = 0x03,
    LOUDEST_CMD_PING      = 0x04,
    // 0x50-0x52 sit outside every VIA range - quantum/via.h:54-79 gives VIA
    // 0x01-0x13 plus id_vial_prefix 0xFE and id_unhandled 0xFF - so in the vial
    // build via_command_kb() claims them unconditionally, with none of the
    // payload heuristics that 0x01-0x04 need. Do not move them into 0x01-0x13.
    LOUDEST_CMD_GET_JOYSTICK      = 0x50,
    LOUDEST_CMD_SET_CALIBRATION   = 0x51,
    LOUDEST_CMD_RESET_CALIBRATION = 0x52,
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
#endif

// ---------------------------------------------------------------------------
// Joystick calibration store (protocol v1). Contract:
// docs/PROTOCOL-V1-CONTRACT.md. All values are in the firmware's 10-bit
// analogReadPin domain, 0..1023 (RP2040 samples 12-bit and returns
// sample >> (12 - ADC_RESOLUTION) with ADC_RESOLUTION 10 --
// platforms/chibios/drivers/analog.c:444-445), the same domain keyboard.json's
// low/rest/high already use.
//
// WRITE POLICY, hard requirement (AMENDED 2026-08-15 -- see
// docs/PROTOCOL-V1-CONTRACT.md, which is the adjudicated source of truth):
// the EEPROM block is written ONLY by an accepted 0x51, by 0x52, and by a
// SUCCESSFUL SW14-triggered on-board calibration. The third path was added on
// the owner's directive: "Calibration is stored in EEPROM, no daemon needed.
// You turn on calibration, it fucking calibrates, then it stores. End of story,
// calibrated usage does not depend on a daemon."
//
// The clause's INTENT is unchanged and still binding: every write is
// USER-INITIATED (a deliberate one-second button hold) and RARE, and there is
// still no background, periodic, opportunistic or automatic calibration
// anywhere in this file. The owner rejected continuous/background learning
// explicitly and that rejection stands -- do not add it.
//
// An UNCALIBRATED board behaves exactly as it did before v1: JS_CENTER /
// JS_THRESHOLD below are the pre-v1 compile-time constants (they used to sit in
// the joystick-mode block further down and moved here because they are now the
// documented fallback), and while cal_state is 0 the native gamepad axes keep
// the low/rest/high keyboard.json generated into joystick_axes[].
// ---------------------------------------------------------------------------
#define JS_CENTER 512        // uncalibrated fallback center, both axes
#define JS_THRESHOLD 300     // uncalibrated fallback deflection to trigger
#define JS_CAL_MAGIC 0x4A    // 'J'
#define JS_CAL_VERSION 1
#define JS_CAL_ADC_MAX 1023  // analogReadPin full scale
#define JS_CAL_MIN_SWING 100 // smallest credible half-swing (contract)

typedef struct {
    uint8_t  magic;
    uint8_t  version;
    uint16_t rest_x, rest_y, min_x, max_x, min_y, max_y;
} loudest_js_cal_t;

_Static_assert(sizeof(loudest_js_cal_t) == EECONFIG_KB_DATA_SIZE, "loudest_js_cal_t must exactly fill the keyboard EEPROM datablock declared in config.h");

static loudest_js_cal_t js_cal;                 // magic stays 0 while uncalibrated
static bool             js_calibrated = false;  // == the wire's cal_state

// Derived ONCE whenever calibration is loaded, accepted or reset - never
// recomputed per scan. center = rest; threshold = 60% of the smaller half-swing.
static int16_t js_center_x    = JS_CENTER;
static int16_t js_center_y    = JS_CENTER;
static int16_t js_threshold_x = JS_THRESHOLD;
static int16_t js_threshold_y = JS_THRESHOLD;

#ifdef JOYSTICK_ENABLE
// keyboard.json's generated low/rest/high, snapshotted before anything here ever
// overwrites them, so 0x52 restores the shipped placeholders without a second
// copy of those numbers living in C.
static joystick_config_t js_axes_shipped[JOYSTICK_AXIS_COUNT];
#endif

// TOTAL validation, per the contract - the same rules are applied to a 0x51
// payload and to whatever the EEPROM hands back, and a rejection writes nothing.
static bool js_cal_valid(const loudest_js_cal_t *c) {
    if (c->magic != JS_CAL_MAGIC || c->version != JS_CAL_VERSION) {
        return false;
    }
    if (c->rest_x > JS_CAL_ADC_MAX || c->rest_y > JS_CAL_ADC_MAX || c->min_x > JS_CAL_ADC_MAX || c->max_x > JS_CAL_ADC_MAX || c->min_y > JS_CAL_ADC_MAX || c->max_y > JS_CAL_ADC_MAX) {
        return false;
    }
    if (c->min_x >= c->rest_x || c->rest_x >= c->max_x || c->min_y >= c->rest_y || c->rest_y >= c->max_y) {
        return false;
    }
    if (c->rest_x - c->min_x < JS_CAL_MIN_SWING || c->max_x - c->rest_x < JS_CAL_MIN_SWING) {
        return false;
    }
    if (c->rest_y - c->min_y < JS_CAL_MIN_SWING || c->max_y - c->rest_y < JS_CAL_MIN_SWING) {
        return false;
    }
    return true;
}

static void js_cal_apply(void) {
    if (js_calibrated) {
        uint16_t lo    = js_cal.rest_x - js_cal.min_x;
        uint16_t hi    = js_cal.max_x - js_cal.rest_x;
        js_center_x    = (int16_t)js_cal.rest_x;
        js_threshold_x = (int16_t)(((lo < hi ? lo : hi) * 3) / 5); // exact floor(60%)
        lo             = js_cal.rest_y - js_cal.min_y;
        hi             = js_cal.max_y - js_cal.rest_y;
        js_center_y    = (int16_t)js_cal.rest_y;
        js_threshold_y = (int16_t)(((lo < hi ? lo : hi) * 3) / 5);
    } else {
        js_center_x    = JS_CENTER;
        js_center_y    = JS_CENTER;
        js_threshold_x = JS_THRESHOLD;
        js_threshold_y = JS_THRESHOLD;
    }
#ifdef JOYSTICK_ENABLE
    // The native HID gamepad axes are RUNTIME-MUTABLE, so one stored calibration
    // drives all three joystick modes instead of only the two custom ones:
    // quantum/joystick.h:81 declares joystick_axes[] extern and non-const, the
    // definition generated from keyboard.json (.build/obj_*/src/*_keyboard.c) is
    // non-const and links into .data in SRAM, and quantum/joystick.c:99-106
    // re-reads min/mid/max_digit on EVERY sample (joystick_task ->
    // joystick_read_axes, joystick.c:162-164), so a write here takes effect on
    // the next axis read with no re-init and no reboot.
    joystick_axes[0].min_digit = js_calibrated ? js_cal.min_x : js_axes_shipped[0].min_digit;
    joystick_axes[0].mid_digit = js_calibrated ? js_cal.rest_x : js_axes_shipped[0].mid_digit;
    joystick_axes[0].max_digit = js_calibrated ? js_cal.max_x : js_axes_shipped[0].max_digit;
    joystick_axes[1].min_digit = js_calibrated ? js_cal.min_y : js_axes_shipped[1].min_digit;
    joystick_axes[1].mid_digit = js_calibrated ? js_cal.rest_y : js_axes_shipped[1].mid_digit;
    joystick_axes[1].max_digit = js_calibrated ? js_cal.max_y : js_axes_shipped[1].max_digit;
#endif
}

// Read-only load at boot. eeconfig_read_kb_datablock() zero-fills when QMK's own
// size/version guard says the block is stale (quantum/nvm/eeprom/nvm_eeconfig.c:
// 225-235), so a stale block arrives as magic 0 and fails js_cal_valid() below;
// our magic/version pair is the second, independent guard the contract asks for.
// Nothing is written on any failure path.
static void js_cal_load(void) {
#ifdef JOYSTICK_ENABLE
    memcpy(js_axes_shipped, joystick_axes, sizeof(js_axes_shipped)); // BEFORE the first apply
#endif
    loudest_js_cal_t stored;
    eeconfig_read_kb_datablock(&stored, 0, sizeof(stored));
    js_calibrated = js_cal_valid(&stored);
    if (js_calibrated) {
        js_cal = stored;
    } else {
        memset(&js_cal, 0, sizeof(js_cal));
    }
    js_cal_apply();
}

// THE single definition of "accept a calibration and make it stick". Both
// writers call this and nothing else writes the block: the 0x51 handler below,
// and the on-board SW14 routine further down. Sharing this function is what
// makes a board-calibrated result BYTE-IDENTICAL to a host-calibrated one for
// the same six measurements -- identical validation, identical derivation
// (js_cal_apply's floor(60%)), identical struct, identical write. It is a
// structural guarantee, not something the tests have to keep rediscovering.
//
// Returns false WITHOUT touching RAM state or EEPROM when the values fail the
// contract's rules. Rejection is TOTAL: a partially-valid struct is never
// written, and a previous good calibration survives a rejected one intact.
static bool js_cal_store(const loudest_js_cal_t *cal) {
    if (!js_cal_valid(cal)) {
        return false;
    }
    js_cal        = *cal;
    js_calibrated = true;
    js_cal_apply(); // derives center/threshold AND rescales joystick_axes[]
    eeconfig_update_kb_datablock(&js_cal, 0, sizeof(js_cal));
    return true;
}

#if defined(RAW_ENABLE) && !defined(LOUDEST_CUSTOM_RAW_HID)
// Little-endian uint16 accessors for the v1 frames. Defined inside RAW_ENABLE
// because the three v1 handlers are their only callers - at file scope they
// would be an unused-static -Werror trip in a hypothetical no-raw build.
static uint16_t js_get16(const uint8_t *data, uint8_t at) {
    return (uint16_t)(data[at] | ((uint16_t)data[at + 1] << 8));
}

static void js_put16(uint8_t *data, uint8_t at, uint16_t value) {
    data[at]     = (uint8_t)(value & 0xFF);
    data[at + 1] = (uint8_t)(value >> 8);
}

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
            resp[4] = LOUDEST_PROTO_VERSION;         // 1 (was 0 before 2026-08-15)
            resp[5] = LOUDEST_LED_COUNT;             // 24
            resp[6] = LOUDEST_MAX_LAYERS;            // 8
            resp[7] = LOUDEST_CAPS_FEATURES;         // 0x1F
            raw_hid_send(resp, sizeof(resp));
            break;
        }
        case LOUDEST_CMD_GET_JOYSTICK: {
            // Safe at any time, including before calibration exists: it reads the
            // ADC and RAM only, never blocks on and never writes the EEPROM.
            uint8_t resp[LOUDEST_REPORT_LEN];
            memset(resp, 0, sizeof(resp));
            resp[0] = LOUDEST_CMD_GET_JOYSTICK;
            resp[1] = (length >= 2) ? data[1] : 0; // echo token
            resp[2] = LOUDEST_CAPS_MAGIC0;         // 'L'
            resp[3] = LOUDEST_CAPS_MAGIC1;         // 'D'
            js_put16(resp, 4, (uint16_t)analogReadPin(GP26));
            js_put16(resp, 6, (uint16_t)analogReadPin(GP27));
            resp[8] = js_calibrated ? 1 : 0; // cal_state
            js_put16(resp, 9, js_calibrated ? js_cal.rest_x : JS_CENTER);
            js_put16(resp, 11, js_calibrated ? js_cal.rest_y : JS_CENTER);
            js_put16(resp, 13, js_calibrated ? js_cal.min_x : 0);
            js_put16(resp, 15, js_calibrated ? js_cal.max_x : JS_CAL_ADC_MAX);
            js_put16(resp, 17, js_calibrated ? js_cal.min_y : 0);
            js_put16(resp, 19, js_calibrated ? js_cal.max_y : JS_CAL_ADC_MAX);
            js_put16(resp, 21, (uint16_t)js_threshold_x);
            js_put16(resp, 23, (uint16_t)js_threshold_y);
            raw_hid_send(resp, sizeof(resp));
            break;
        }
        case LOUDEST_CMD_SET_CALIBRATION: {
            // Fields occupy bytes 1..12, so a frame shorter than 13 is ignored
            // rather than read past, and status stays 1 (rejected, nothing
            // written). status only reaches 0 after the write actually happened.
            uint8_t resp[LOUDEST_REPORT_LEN];
            memset(resp, 0, sizeof(resp));
            resp[0] = LOUDEST_CMD_SET_CALIBRATION;
            resp[1] = 1; // rejected unless every check below passes
            if (length >= 13) {
                loudest_js_cal_t cal = {
                    .magic   = JS_CAL_MAGIC,
                    .version = JS_CAL_VERSION,
                    .rest_x  = js_get16(data, 1),
                    .rest_y  = js_get16(data, 3),
                    .min_x   = js_get16(data, 5),
                    .max_x   = js_get16(data, 7),
                    .min_y   = js_get16(data, 9),
                    .max_y   = js_get16(data, 11),
                };
                if (js_cal_store(&cal)) {
                    resp[1] = 0; // accepted and written
                }
            }
            raw_hid_send(resp, sizeof(resp));
            break;
        }
        case LOUDEST_CMD_RESET_CALIBRATION: {
            uint8_t resp[LOUDEST_REPORT_LEN];
            memset(resp, 0, sizeof(resp));
            resp[0] = LOUDEST_CMD_RESET_CALIBRATION;
            resp[1] = 0x00;
            memset(&js_cal, 0, sizeof(js_cal)); // magic invalidated
            js_calibrated = false;
            js_cal_apply();                                           // placeholders live again, no reboot
            eeconfig_update_kb_datablock(&js_cal, 0, sizeof(js_cal)); // and cleared in EEPROM
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
        case LOUDEST_CMD_GET_JOYSTICK:
        case LOUDEST_CMD_SET_CALIBRATION:
        case LOUDEST_CMD_RESET_CALIBRATION:
            // UNCONDITIONAL, unlike the four above. Verified against the fork's
            // own quantum/via.h: via_command_id occupies 0x01-0x13 with
            // id_vial_prefix 0xFE and id_unhandled 0xFF (:55-79), so 0x50-0x52
            // collide with no VIA command and need no tail-zero disambiguation.
            loudest_status_handle(data, length);
            return true;
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
#endif // RAW_ENABLE && !LOUDEST_CUSTOM_RAW_HID

// ---------------------------------------------------------------------------
// Joystick modes. Native QMK exposes GP26/GP27 as a HID gamepad; the arrow
// (8-way) and scroll modes are custom code reading analogReadPin. JS_MODE
// cycles gamepad -> arrows -> scroll. All three now share ONE calibration
// source: the per-axis js_center_* / js_threshold_* derived above from the
// EEPROM store (protocol v1), which fall back to the 512/300 placeholders on an
// uncalibrated board. (Before 2026-08-15 the arrow/scroll paths used the
// compile-time JS_CENTER/JS_THRESHOLD directly and were marked
// CALIBRATION-PENDING; those two defines are now the fallback and live with the
// calibration store.)
// ---------------------------------------------------------------------------
enum js_mode {
    JS_MODE_GAMEPAD = 0,
    JS_MODE_ARROWS,
    JS_MODE_SCROLL,
    JS_MODE_COUNT,
};

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

// ===========================================================================
// SW14 + on-board joystick calibration.
//
// NAMING, so the two halves are never confused: JS_CAL_* / js_cal_* is the
// EEPROM STORE and its contract-defined validation and derivation (far above).
// SELFCAL_* / selfcal_* is the on-board ROUTINE that measures a stick and fills
// that store. The routine owns no maths of its own -- it hands six numbers to
// js_cal_store() and that is the only way it can change anything.
//
// SW14 HAS TWO ROLES AND THEY CANNOT COLLIDE, because they are separated in
// time, not by any logic in this file:
//   * HELD AT POWER-UP  -> the RP2040 mask ROM samples this same line before a
//                          single instruction of our firmware runs, and enters
//                          the UF2 bootloader. We are not executing; we cannot
//                          be confused.
//   * PRESSED WHILE RUNNING -> calibration, below.
// A corollary this code DEPENDS ON: any board executing this firmware
// necessarily booted with SW14 released, so requiring one observed release
// before the first arming (selfcal_seen_release) costs a real user nothing.
//
// BOARD TRUTH, read off v5/hardware/pcb/v5_6.kicad_pcb: SW14 connects net
// BOOTSEL to GND, and R6 (1k) ties BOOTSEL to QSPI_CS -- the stock Pico
// topology. SW15 connects RUN to GND: that is a hardware reset, invisible to
// firmware, and nothing here touches it.
// ===========================================================================
#define SW14_QSPI_SS_INDEX 1   // QSPI_CS is index 1 in the ioqspi/gpio_hi banks
#define SW14_SETTLE_ITERS  1000 // pico-sdk's field-proven settle spin; see below

// Reads SW14 by briefly turning QSPI_CS into an input and sampling it.
//
// WHY THIS MUST LIVE IN RAM. While OEOVER disables the QSPI_CS output driver,
// the external flash cannot be selected, so XIP is dead: any instruction fetch
// from 0x10xxxxxx would fault or hang. __no_inline_not_in_flash_func places
// this function -- and the literal pool GCC emits alongside it -- in section
// .time_critical.sw14_pressed, which
// platforms/chibios/boards/common/ld/RP2040_rules_data_with_timecrit.ld:26
// links into .data in SRAM (ram0 org 0x20000000). MCU_LDSCRIPT defaults to
// RP2040_FLASH_TIMECRIT for RP2040 (platforms/chibios/mcu_selection.mk:163) and
// nothing in this keyboard overrides it. The build gate that proves it actually
// landed is `arm-none-eabi-nm` showing this symbol at 0x2000xxxx, NOT 0x100xxxx.
//
// WHY INTERRUPTS ARE MASKED. Every ChibiOS RP2040 ISR in this tree executes
// from XIP flash (RP2040_rules_code_with_boot2.ld puts all .text* in flash1),
// so any interrupt taken inside the window would fetch from dead flash.
//
// COST: 14016 cycles == 112.1 us at 125 MHz. That is MEASURED, cycle-exact,
// off this function's own disassembly (window = the OEOVER SET store to the
// OEOVER CLR store), not estimated:
//     post-SET setup                                     5
//     settle spin, 1000 iterations x 14 cycles       14000
//     exit iteration (ldr/cmp/blt not taken)             4
//     SIO sample + CLR-alias prep                        7
//
// DO NOT "OPTIMIZE" THE SPIN. Read this first.
// The body is 14 cycles, not the ~6 an inspection of the C suggests:
//     ldr r3,[sp,#4]   2      ldr r3,[sp,#4]   2
//     cmp r3, r1       1      adds r3,#1       1
//     blt.n  (taken)   3      str r3,[sp,#4]   2
//                             b.n    (taken)   3
// `volatile int i` is what costs the difference: it forces a stack LOAD and a
// stack STORE every single iteration (4 cycles of memory traffic) on top of two
// taken branches (6 cycles). An earlier estimate of this routine modelled it as
// a register loop and came out 1.8x low; that error is recorded here so nobody
// repeats it.
// The iteration count is pico-sdk's get_bootsel_button() value, matched
// DELIBERATELY: the spin exists to let the QSPI_CS line settle after the driver
// is disabled, which is an ELECTRICAL question -- RC on that line through R6
// (1k) plus pad and trace capacitance. pico-sdk chose 1000 against real
// silicon. No emulator models RC at all, so shortening this on simulation
// evidence would be false precision, and dropping the `volatile` would quietly
// shorten the real settling window ~3.5x. Both are wrong. Leave it.
//
// WHY 112 us IS SAFE ANYWAY. Polled at 10 Hz this is a 0.112% duty cycle, and:
//   1. PRECEDENT. wear_leveling_rp2040_flash.c:185-203 already masks interrupts
//      around a flash sector ERASE -- ~50-400 ms -- on every Vial keymap save
//      and on every calibration write below. 112 us is 450-3500x SHORTER than
//      something this firmware already does routinely and survives.
//   2. NO TIME IS LOST. ChibiOS here is TICKLESS (CH_CFG_ST_FREQUENCY 1000000,
//      CH_CFG_ST_TIMEDELTA 20) against the RP2040's free-running 1 MHz hardware
//      timer, so masking DELAYS a pending alarm and cannot DROP a tick.
//      timer_read32() stays truthful across the window.
//   3. USB is a hardware device controller with its own DPRAM buffers; 112 us
//      is 11% of one 1 ms full-speed frame and is absorbed by that buffering.
//   4. EMPIRICAL, not merely argued: firmware/sim/behavior.cjs --touch=board
//      --encoder=board is 33/33 on both builds with this poll running
//      throughout -- USB, HID, RGB, touch and encoder all pass.
//
// Register technique: the atomic SET/CLR aliases touch ONLY the OEOVER field,
// so unlike pico-sdk's read-modify-write hw_write_masked() this needs no read
// and never depends on the current FUNCSEL (which XIP owns and we must not
// disturb). Restoring by clearing both OEOVER bits lands on VALUE_NORMAL (0)
// by construction.
static bool __no_inline_not_in_flash_func(sw14_pressed)(void) {
    uint32_t irq = save_and_disable_interrupts();
    hw_set_bits(&ioqspi_hw->io[SW14_QSPI_SS_INDEX].ctrl, IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_DISABLE << IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB);
    for (volatile int i = 0; i < SW14_SETTLE_ITERS; i++) {
    }
    // Pressed pulls the line to GND through R6, so LOW == pressed.
    const bool pressed = !(sio_hw->gpio_hi_in & (1u << SW14_QSPI_SS_INDEX));
    hw_clear_bits(&ioqspi_hw->io[SW14_QSPI_SS_INDEX].ctrl, IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS);
    restore_interrupts(irq);
    return pressed;
}

// --- the routine's timing, all bounded so it can never hang -----------------
#define SELFCAL_POLL_MS        100   // SW14 sample period (NOT every matrix scan)
#define SELFCAL_ARM_MS         1000  // deliberate hold before anything happens
#define SELFCAL_ARM_SAMPLES    (SELFCAL_ARM_MS / SELFCAL_POLL_MS)
#define SELFCAL_ABORT_SAMPLES  2     // ~200 ms held; one glitch cannot abort
#define SELFCAL_RELEASE_MAX_MS 10000 // stuck button: give up rather than wait
#define SELFCAL_SAMPLE_MS      10    // ADC sample period, both phases (100 Hz)
#define SELFCAL_BLOCK_MS       400   // stability window during centring
#define SELFCAL_CENTER_MS      2000  // nominal "hold still"
#define SELFCAL_CENTER_MAX_MS  4000  // hard timeout if it never settles
#define SELFCAL_SWING_MS       10000 // "roll it round the edge"
#define SELFCAL_RESULT_MS      2000  // success/failure display
#define SELFCAL_ABORT_MS       600   // aborted display
#define SELFCAL_STABLE_BAND    8     // max peak-to-peak, in ADC counts, for a
                                     // 400 ms window to count as "holding still"

enum selfcal_state {
    SELFCAL_IDLE = 0, // normal operation; watching for the arming hold
    SELFCAL_ARMED,    // hold satisfied; waiting for the user to let go
    SELFCAL_CENTER,   // measuring rest
    SELFCAL_SWING,    // tracking the envelope
    SELFCAL_RESULT,   // showing the outcome, then straight back to IDLE
};

enum selfcal_result {
    SELFCAL_RESULT_NONE = 0,
    SELFCAL_RESULT_OK,
    SELFCAL_RESULT_BAD,
    SELFCAL_RESULT_ABORT,
};

// Justified device state, not incidental globals: this is one state machine,
// and the LED painter in the RGB hook is its display, so both halves read it.
static uint8_t  selfcal_state        = SELFCAL_IDLE;
static uint8_t  selfcal_result       = SELFCAL_RESULT_NONE;
static bool     selfcal_seen_release = false; // see the SW14 comment above
static uint8_t  selfcal_press_run    = 0;     // consecutive pressed polls
static uint32_t selfcal_last_poll    = 0;
static uint32_t selfcal_last_sample  = 0;
static uint32_t selfcal_phase_start  = 0;
static uint32_t selfcal_block_start  = 0;
static uint32_t selfcal_sum_x, selfcal_sum_y; // current stability window
static uint16_t selfcal_n;
static uint16_t selfcal_blk_min_x, selfcal_blk_max_x, selfcal_blk_min_y, selfcal_blk_max_y;
static bool     selfcal_have_rest;
static uint16_t selfcal_rest_x, selfcal_rest_y;
static uint16_t selfcal_min_x, selfcal_max_x, selfcal_min_y, selfcal_max_y;
static bool     selfcal_swing_ok; // all four half-swings already credible (LED hint)

static void selfcal_block_reset(uint32_t now) {
    selfcal_block_start = now;
    selfcal_sum_x = selfcal_sum_y = 0;
    selfcal_n                     = 0;
    selfcal_blk_min_x = selfcal_blk_min_y = 0xFFFF;
    selfcal_blk_max_x = selfcal_blk_max_y = 0;
}

static void selfcal_enter(uint8_t state, uint32_t now) {
    selfcal_state       = state;
    selfcal_phase_start = now;
    selfcal_last_sample = now;
}

static void selfcal_finish(uint8_t result, uint32_t now) {
    selfcal_result = result;
    selfcal_enter(SELFCAL_RESULT, now);
    // A fresh run must see the button released again first, so a still-held or
    // stuck SW14 can never re-arm the routine in a loop.
    selfcal_seen_release = false;
}

// Runs from housekeeping_task_kb(). Needs no key input: its only inputs are
// SW14 and the joystick, so no keymap, layer or keycode is involved anywhere.
static void selfcal_task(void) {
    const uint32_t now = timer_read32();

    bool poll    = false;
    bool pressed = false;
    if (timer_elapsed32(selfcal_last_poll) >= SELFCAL_POLL_MS) {
        selfcal_last_poll = now;
        poll              = true;
        pressed           = sw14_pressed();
        if (pressed) {
            if (selfcal_press_run < 0xFF) {
                selfcal_press_run++;
            }
        } else {
            selfcal_press_run    = 0;
            selfcal_seen_release = true;
        }
    }

    switch (selfcal_state) {
        case SELFCAL_IDLE:
            if (poll && selfcal_seen_release && selfcal_press_run >= SELFCAL_ARM_SAMPLES) {
                selfcal_enter(SELFCAL_ARMED, now);
            }
            break;

        case SELFCAL_ARMED:
            // Wait for the user to let go, so the button they are still holding
            // is not immediately re-read as the abort press.
            if (poll && !pressed) {
                js_release_arrows(); // nothing should be stuck down while we measure
                selfcal_have_rest = false;
                selfcal_enter(SELFCAL_CENTER, now);
                selfcal_block_reset(now);
            } else if (timer_elapsed32(selfcal_phase_start) >= SELFCAL_RELEASE_MAX_MS) {
                selfcal_finish(SELFCAL_RESULT_ABORT, now); // stuck button
            }
            break;

        case SELFCAL_CENTER:
            if (poll && selfcal_press_run >= SELFCAL_ABORT_SAMPLES) {
                selfcal_finish(SELFCAL_RESULT_ABORT, now);
                break;
            }
            if (timer_elapsed32(selfcal_last_sample) >= SELFCAL_SAMPLE_MS) {
                selfcal_last_sample   = now;
                const uint16_t x      = (uint16_t)analogReadPin(GP26);
                const uint16_t y      = (uint16_t)analogReadPin(GP27);
                selfcal_sum_x        += x;
                selfcal_sum_y        += y;
                selfcal_n++;
                if (x < selfcal_blk_min_x) selfcal_blk_min_x = x;
                if (x > selfcal_blk_max_x) selfcal_blk_max_x = x;
                if (y < selfcal_blk_min_y) selfcal_blk_min_y = y;
                if (y > selfcal_blk_max_y) selfcal_blk_max_y = y;
            }
            if (timer_elapsed32(selfcal_block_start) >= SELFCAL_BLOCK_MS) {
                // A window counts only if BOTH axes held still across it; rest
                // is then the mean of that window, per the brief.
                if (selfcal_n > 0 && (uint16_t)(selfcal_blk_max_x - selfcal_blk_min_x) <= SELFCAL_STABLE_BAND && (uint16_t)(selfcal_blk_max_y - selfcal_blk_min_y) <= SELFCAL_STABLE_BAND) {
                    selfcal_rest_x    = (uint16_t)(selfcal_sum_x / selfcal_n);
                    selfcal_rest_y    = (uint16_t)(selfcal_sum_y / selfcal_n);
                    selfcal_have_rest = true;
                }
                selfcal_block_reset(now);
            }
            if (selfcal_have_rest && timer_elapsed32(selfcal_phase_start) >= SELFCAL_CENTER_MS) {
                // Seed the envelope AT rest: a user who never moves the stick
                // then ends with min == rest == max, which js_cal_valid()
                // rejects. That is the correct outcome, not a special case.
                selfcal_min_x = selfcal_max_x = selfcal_rest_x;
                selfcal_min_y = selfcal_max_y = selfcal_rest_y;
                selfcal_swing_ok             = false;
                selfcal_enter(SELFCAL_SWING, now);
            } else if (timer_elapsed32(selfcal_phase_start) >= SELFCAL_CENTER_MAX_MS) {
                selfcal_finish(SELFCAL_RESULT_BAD, now); // never settled; write nothing
            }
            break;

        case SELFCAL_SWING:
            if (poll && selfcal_press_run >= SELFCAL_ABORT_SAMPLES) {
                selfcal_finish(SELFCAL_RESULT_ABORT, now);
                break;
            }
            if (timer_elapsed32(selfcal_last_sample) >= SELFCAL_SAMPLE_MS) {
                selfcal_last_sample = now;
                const uint16_t x    = (uint16_t)analogReadPin(GP26);
                const uint16_t y    = (uint16_t)analogReadPin(GP27);
                if (x < selfcal_min_x) selfcal_min_x = x;
                if (x > selfcal_max_x) selfcal_max_x = x;
                if (y < selfcal_min_y) selfcal_min_y = y;
                if (y > selfcal_max_y) selfcal_max_y = y;
                // Purely a display hint (amber -> green); the real verdict is
                // js_cal_valid() inside js_cal_store() at the end of the phase.
                selfcal_swing_ok = (selfcal_rest_x - selfcal_min_x >= JS_CAL_MIN_SWING) && (selfcal_max_x - selfcal_rest_x >= JS_CAL_MIN_SWING) && (selfcal_rest_y - selfcal_min_y >= JS_CAL_MIN_SWING) && (selfcal_max_y - selfcal_rest_y >= JS_CAL_MIN_SWING);
            }
            if (timer_elapsed32(selfcal_phase_start) >= SELFCAL_SWING_MS) {
                const loudest_js_cal_t cal = {
                    .magic   = JS_CAL_MAGIC,
                    .version = JS_CAL_VERSION,
                    .rest_x  = selfcal_rest_x,
                    .rest_y  = selfcal_rest_y,
                    .min_x   = selfcal_min_x,
                    .max_x   = selfcal_max_x,
                    .min_y   = selfcal_min_y,
                    .max_y   = selfcal_max_y,
                };
                // The ONLY place this routine can change anything. On false,
                // nothing was written and any previous calibration is intact.
                selfcal_finish(js_cal_store(&cal) ? SELFCAL_RESULT_OK : SELFCAL_RESULT_BAD, now);
            }
            break;

        case SELFCAL_RESULT:
        default: {
            const uint32_t hold = (selfcal_result == SELFCAL_RESULT_ABORT) ? SELFCAL_ABORT_MS : SELFCAL_RESULT_MS;
            if (timer_elapsed32(selfcal_phase_start) >= hold) {
                selfcal_result = SELFCAL_RESULT_NONE;
                selfcal_state  = SELFCAL_IDLE;
            }
            break;
        }
    }
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

void keyboard_post_init_kb(void) {
    // The EEPROM is live by here and nothing has touched joystick_axes[] yet:
    // quantum/keyboard.c runs eeprom_driver_init() in keyboard_setup() (:367)
    // and calls keyboard_post_init_quantum() LAST in keyboard_init() (:561).
    // The weak keyboard_post_init_kb() (quantum/keyboard.c:331-333) is the only
    // caller of keyboard_post_init_user(), so this override must call it.
    js_cal_load();
    keyboard_post_init_user();
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
    if (record->event.key.row == TOUCH_MATRIX_ROW && record->event.key.col == TOUCH_MATRIX_COL && !touch_enabled && keycode != TP_TOG) {
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
    selfcal_task();

    // While the routine runs, the arrow and scroll modes must NOT also emit
    // input. The joystick is the instrument being measured: ten seconds of
    // deliberately swinging it round the end-stops would otherwise spray arrow
    // keys or wheel events into whatever application happens to be focused.
    // That is a defect, not a feature -- do not "restore" it.
    //
    // Note precisely what this does NOT do: it is not a layer change, not a
    // keymap change, and it makes no key inert. All 13 mechanical keys, the
    // touch pad and the encoder keep working normally for the whole routine,
    // and the native HID gamepad keeps reporting (it is a gamepad; the stick
    // moving is exactly what it is for).
    if (js_mode != JS_MODE_GAMEPAD && selfcal_state == SELFCAL_IDLE) {
        int16_t x = analogReadPin(GP26);
        int16_t y = analogReadPin(GP27);

        if (js_mode == JS_MODE_ARROWS) {
            bool want[4];
            want[0] = (y < js_center_y - js_threshold_y); // up
            want[1] = (y > js_center_y + js_threshold_y); // down
            want[2] = (x < js_center_x - js_threshold_x); // left
            want[3] = (x > js_center_x + js_threshold_x); // right
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
                if (y < js_center_y - js_threshold_y) {
                    wheel = KC_WH_U;
                } else if (y > js_center_y + js_threshold_y) {
                    wheel = KC_WH_D;
                } else if (x < js_center_x - js_threshold_x) {
                    wheel = KC_WH_L;
                } else if (x > js_center_x + js_threshold_x) {
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
#if defined(RGB_MATRIX_ENABLE) && defined(LOUDEST_CUSTOM_RGB_STATUS)
bool rgb_matrix_indicators_advanced_kb(uint8_t led_min, uint8_t led_max) {
    return rgb_matrix_indicators_advanced_user(led_min, led_max);
}
#elif defined(RGB_MATRIX_ENABLE)
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

// --- the on-board calibration routine's entire user interface ---------------
// Per-key LEDs 0..12 ONLY, deliberately:
//   * LED 13 is the layer indicator and keeps doing its job -- BRING-UP.md's
//     first check is "is that LED pure red", and blanking it mid-routine would
//     break the one signal a user is told to trust.
//   * 14..23 are underglow, which the OPAQUE SKU does not populate (see
//     loudest_micro.h). A UI that needed them would be invisible on half the
//     boards shipped.
#define SELFCAL_UI_LEDS   13
#define SELFCAL_HUE_RED   0
#define SELFCAL_HUE_AMBER 30
#define SELFCAL_HUE_GREEN 85
#define SELFCAL_HUE_BLUE  170
// These LEDs ARE the interface, so they get a brightness floor rather than
// inheriting a dimmed-right-down rgb_matrix value. (If the RGB matrix is turned
// OFF entirely this hook never runs at all and the routine has no display --
// documented in firmware/BRING-UP.md. Force-enabling RGB here would be a much
// larger behavior change than the routine is entitled to make.)
#define SELFCAL_MIN_VAL 128

static HSV selfcal_led_hsv(uint8_t index) {
    uint8_t val = rgb_matrix_get_val();
    if (val < SELFCAL_MIN_VAL) {
        val = SELFCAL_MIN_VAL;
    }
    const uint32_t elapsed = timer_elapsed32(selfcal_phase_start);
    const HSV      dark    = {.h = 0, .s = 0, .v = 0};

    switch (selfcal_state) {
        case SELFCAL_ARMED:
            // Steady white on all 13: "that registered -- now let go".
            return (HSV){.h = 0, .s = 0, .v = val};

        case SELFCAL_CENTER: {
            // Blue bar filling over the phase. Cool and static == do not touch it.
            const uint32_t lit = (elapsed * SELFCAL_UI_LEDS) / SELFCAL_CENTER_MS + 1;
            return (index < lit) ? (HSV){.h = SELFCAL_HUE_BLUE, .s = 255, .v = val} : dark;
        }

        case SELFCAL_SWING: {
            // The bar filling shows TIME passing; the colour shows PROGRESS --
            // amber while some half-swing is still short of the credible
            // minimum, green once all four clear it.
            const uint32_t lit = (elapsed * SELFCAL_UI_LEDS) / SELFCAL_SWING_MS + 1;
            const uint8_t  hue = selfcal_swing_ok ? SELFCAL_HUE_GREEN : SELFCAL_HUE_AMBER;
            return (index < lit) ? (HSV){.h = hue, .s = 255, .v = val} : dark;
        }

        case SELFCAL_RESULT:
        default:
            if (selfcal_result == SELFCAL_RESULT_ABORT) {
                // Dim steady white: "nothing happened, nothing changed".
                return (HSV){.h = 0, .s = 0, .v = (uint8_t)(val / 4)};
            }
            {
                const bool on = ((elapsed / 250) & 1) == 0; // 250 ms blink
                return (HSV){.h = (selfcal_result == SELFCAL_RESULT_OK) ? SELFCAL_HUE_GREEN : SELFCAL_HUE_RED, .s = 255, .v = on ? val : 0};
            }
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

    // On-board calibration paints the per-key LEDs while it runs. It does NOT
    // fight the host: an LED the host has claimed above keeps the host's color,
    // which is the same precedence rule that loop already establishes.
    if (selfcal_state != SELFCAL_IDLE) {
        for (uint8_t i = 0; i < SELFCAL_UI_LEDS; i++) {
            if (loudest_status[i].active || i < led_min || i >= led_max) {
                continue;
            }
            const RGB rgb = hsv_to_rgb(selfcal_led_hsv(i));
            rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
        }
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

// Host-side QMK stubs for compiling loudest_micro.c off-target in the
// protocol-conformance harness. Only the symbols that file uses.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// On target the QMK build force-includes the keyboard's config.h into every
// translation unit. Do the same here (it is on the include path as -I KB_DIR),
// or keyboard-level settings such as EECONFIG_KB_DATA_SIZE would be invisible
// to the harness and any firmware code guarded on them would silently vanish
// from the build instead of being tested.
#include "config.h"
// EEPROM datablock API, observed by the harness (see stubs/eeconfig.h).
#include "eeconfig.h"

typedef struct { uint8_t col; uint8_t row; } keypos_t;
typedef struct {
    keypos_t key;
    bool     pressed;
    uint16_t time;
} keyevent_t;
typedef struct {
    keyevent_t event;
} keyrecord_t;

// loudest_micro.c injects the GP16 touch key as a synthetic event at [3,2]
// (the pin is out of the scanned matrix; see that file's touch section).
#define MAKE_KEYEVENT(row_num, col_num, press) \
    ((keyevent_t){.key = {.col = (col_num), .row = (row_num)}, .pressed = (press), .time = 0})

enum { QK_KB_0 = 0x7E00 };

// Keycodes referenced by loudest_micro.c (distinct values, exact ids irrelevant here)
enum {
    KC_NO = 0, KC_UP = 0x52, KC_DOWN = 0x51, KC_LEFT = 0x50, KC_RIGHT = 0x4F,
    KC_WH_U = 0xF1, KC_WH_D = 0xF2, KC_WH_L = 0xF3, KC_WH_R = 0xF4,
};

// Pins
#define GP16 16
#define GP26 26
#define GP27 27

// --- recorded effects (implemented in harness.c) ---
void layer_move(uint8_t layer);

// --- inert stubs ---
static inline bool process_record_user(uint16_t keycode, keyrecord_t *record) { (void)keycode; (void)record; return true; }
static inline void housekeeping_task_user(void) {}
static inline void register_code16(uint16_t kc) { (void)kc; }
static inline void unregister_code16(uint16_t kc) { (void)kc; }
static inline void tap_code16(uint16_t kc) { (void)kc; }
static inline uint32_t timer_read32(void) { return 0; }
static inline uint32_t timer_elapsed32(uint32_t t) { (void)t; return 0; }
static inline uint16_t timer_read(void) { return 0; }
static inline uint16_t timer_elapsed(uint16_t t) { (void)t; return 0; }
static inline void     keyboard_pre_init_user(void) {}
static inline void     keyboard_post_init_user(void) {}
static inline void     matrix_scan_user(void) {}
static inline void     action_exec(keyevent_t event) { (void)event; }
// GP16 touch pin. Off target there is no pad, so it reads its idle level: the
// board straps the TTP223 ACTIVE-HIGH (R10: TOUCH_AHLB->GND), i.e. LOW == not
// touched, so 0 keeps the injected key released through the whole run.
static inline void    gpio_set_pin_input_low(uint8_t pin) { (void)pin; }
static inline uint8_t gpio_read_pin(uint8_t pin) { (void)pin; return 0; }

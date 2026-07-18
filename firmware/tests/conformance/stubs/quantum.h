// Host-side QMK stubs for compiling loudest_micro.c off-target in the
// protocol-conformance harness. Only the symbols that file uses.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

typedef struct {
    struct {
        struct { uint8_t col; uint8_t row; } key;
        bool pressed;
    } event;
} keyrecord_t;

enum { QK_KB_0 = 0x7E00 };

// Keycodes referenced by loudest_micro.c (distinct values, exact ids irrelevant here)
enum {
    KC_NO = 0, KC_UP = 0x52, KC_DOWN = 0x51, KC_LEFT = 0x50, KC_RIGHT = 0x4F,
    KC_WH_U = 0xF1, KC_WH_D = 0xF2, KC_WH_L = 0xF3, KC_WH_R = 0xF4,
};

// Pins
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

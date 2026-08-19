// Host-side stub of QMK's keyboard-level EEPROM datablock API, so the
// conformance harness can observe whether a frame wrote to EEPROM.
//
// The four prototypes are copied from the PINNED vial-qmk tree
// (quantum/eeconfig.h at 00fc4627cd, "Add Vial support for cannonkeys/tmov2"),
// which declares them only when EECONFIG_KB_DATA_SIZE > 0:
//
//   bool     eeconfig_is_kb_datablock_valid(void);
//   uint32_t eeconfig_read_kb_datablock(void *data, uint32_t offset, uint32_t length);
//   uint32_t eeconfig_update_kb_datablock(const void *data, uint32_t offset, uint32_t length);
//   void     eeconfig_init_kb_datablock(void);
//
// They are declared unconditionally here (an unused prototype costs nothing)
// so the harness compiles whether or not the keyboard's config.h has grown its
// EECONFIG_KB_DATA_SIZE yet. The implementations live in harness.c, over a byte
// array it prints after every frame.
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

bool     eeconfig_is_kb_datablock_valid(void);
uint32_t eeconfig_read_kb_datablock(void *data, uint32_t offset, uint32_t length);
uint32_t eeconfig_update_kb_datablock(const void *data, uint32_t offset, uint32_t length);
void     eeconfig_init_kb_datablock(void);

// QMK's convenience macros. Spelled __typeof__ rather than typeof because the
// harness builds with -std=c11 (strict), where the bare GNU keyword is not
// guaranteed; the two are the same operator.
#define eeconfig_read_kb_datablock_field(__object, __field) \
    eeconfig_read_kb_datablock(&(__object.__field), offsetof(__typeof__(__object), __field), sizeof(__object.__field))
#define eeconfig_update_kb_datablock_field(__object, __field) \
    eeconfig_update_kb_datablock(&(__object.__field), offsetof(__typeof__(__object), __field), sizeof(__object.__field))

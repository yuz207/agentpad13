// Host-side stub of the pico-sdk's hardware/sync.h, for the conformance
// harness. loudest_micro.c includes this one directly (the same include the
// in-tree wear_leveling_rp2040_flash.c:13 uses), and reaches
// __no_inline_not_in_flash_func and hw_set_bits/hw_clear_bits through it and
// hardware/structs/ioqspi.h transitively -- so the stubs mirror that chain
// rather than making the firmware name headers it does not name on target.
//
// ON TARGET save_and_disable_interrupts() is mandatory: every ChibiOS RP2040
// interrupt handler in this tree executes from XIP flash, which is inaccessible
// while sw14_pressed() has the QSPI_CS driver overridden.
//
// OFF TARGET the harness is single-threaded with no interrupts at all, so the
// pair is a faithful no-op. The returned cookie is threaded through anyway so
// the firmware's save/restore pairing is still type-checked by the compiler.
#pragma once

#include <stdint.h>

#include "pico/platform.h"
#include "hardware/address_mapped.h"

static inline uint32_t save_and_disable_interrupts(void) {
    return 0;
}

static inline void restore_interrupts(uint32_t status) {
    (void)status;
}

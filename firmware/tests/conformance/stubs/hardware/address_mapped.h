// Host-side stub of the pico-sdk's hardware/address_mapped.h, for the
// conformance harness. Only the register types and the two atomic-alias
// helpers loudest_micro.c uses.
//
// ON TARGET hw_set_bits()/hw_clear_bits() write to the RP2040's atomic SET and
// CLR register aliases (REG_ALIAS_SET_BITS / REG_ALIAS_CLR_BITS), so the
// read-modify-write happens in hardware and no other field of the register can
// be disturbed -- which is exactly why sw14_pressed() uses them instead of
// pico-sdk's read-modify-write hw_write_masked(): it must not touch the FUNCSEL
// field that XIP owns.
//
// OFF TARGET the plain |= and &=~ below are semantically identical (the harness
// is single-threaded and there is no peripheral behind the address), so the
// firmware's register sequence is modelled faithfully and can be inspected.
#pragma once

#include <stdint.h>

typedef volatile uint32_t       io_rw_32;
typedef const volatile uint32_t io_ro_32;

static inline void hw_set_bits(io_rw_32 *addr, uint32_t mask) {
    *addr |= mask;
}

static inline void hw_clear_bits(io_rw_32 *addr, uint32_t mask) {
    *addr &= ~mask;
}

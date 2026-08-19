// Host-side stub of the pico-sdk's hardware/structs/sio.h, for the conformance
// harness. Only gpio_hi_in, the QSPI-bank input register sw14_pressed() samples.
//
// Bit 1 is QSPI_CS. On the board SW14 pulls that line to GND through R6, so
// LOW == pressed and HIGH == released.
//
// The backing variable is defined in harness.c and initialised to all-ones, so
// off target SW14 reads RELEASED -- the state a board is necessarily in when it
// is running this firmware at all (holding SW14 at power-up lands in the mask
// ROM instead). Every pre-existing conformance check therefore sees exactly the
// device it always saw. It is a variable rather than a constant so a future
// check can drive the button without the firmware growing a test seam.
#pragma once

#include <stdint.h>

#include "hardware/address_mapped.h"

typedef struct {
    io_ro_32 gpio_hi_in;
} sio_hw_t;

extern sio_hw_t harness_sio_hw;

#define sio_hw (&harness_sio_hw)

// Host-side stub of the pico-sdk's hardware/structs/ioqspi.h, for the
// conformance harness: the QSPI pad control block, plus the OEOVER field
// macros that arrive with it transitively on target (from
// hardware/regs/io_qspi.h -- loudest_micro.c does not name that header and
// neither does this stub chain).
//
// The three OEOVER values below are copied VERBATIM from the pinned tree,
// lib/pico-sdk/src/rp2040/hardware_regs/include/hardware/regs/io_qspi.h:287-293,
// so a divergence between host and target is a copy error, not a silent
// semantic drift:
//     IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS          0x00003000
//     IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB           12
//     IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_NORMAL  0x0
//     IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_DISABLE 0x2
//
// The struct mirrors the real one field for field (status then ctrl, six pads)
// so io[1].ctrl is the same member path off target as on. The backing storage
// is defined in harness.c; off target writing it does nothing to any flash,
// because there is none.
#pragma once

#include <stdint.h>

#include "hardware/address_mapped.h"

#define IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS          0x00003000u
#define IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB           12u
#define IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_NORMAL  0x0u
#define IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_DISABLE 0x2u

#define NUM_QSPI_GPIOS 6

typedef struct {
    io_ro_32 status;
    io_rw_32 ctrl;
} ioqspi_status_ctrl_hw_t;

typedef struct {
    ioqspi_status_ctrl_hw_t io[NUM_QSPI_GPIOS];
} ioqspi_hw_t;

extern ioqspi_hw_t harness_ioqspi_hw;

#define ioqspi_hw (&harness_ioqspi_hw)

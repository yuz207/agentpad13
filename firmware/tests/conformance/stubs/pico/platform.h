// Host-side stub of the pico-sdk's pico/platform.h, for the conformance
// harness. Only the one macro loudest_micro.c depends on.
//
// ON TARGET this macro is what makes sw14_pressed() safe: it expands to
// __attribute__((section(".time_critical.sw14_pressed"))) plus __noinline
// (pico-sdk platform.h:184,265,298), and
// platforms/chibios/boards/common/ld/RP2040_rules_data_with_timecrit.ld:26
// links .time_critical* into .data in SRAM, so the function does not execute
// from the XIP flash it is busy disabling. That placement is verified on the
// real build by `arm-none-eabi-nm`, not here.
//
// OFF TARGET there is no XIP and no flash, so the section attribute is
// meaningless and would only confuse the host linker. Expanding to the bare
// function name is the honest host model.
#pragma once

#define __no_inline_not_in_flash_func(func_name) func_name

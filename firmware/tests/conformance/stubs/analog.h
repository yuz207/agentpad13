#pragma once
#include <stdint.h>

// The harness drives the two ADC pins separately so a GET_JOYSTICK check can
// tell the axes apart: a firmware that read GP27 into live_x would pass every
// assertion if both pins returned the same number. Defined in harness.c, and
// left at the 10-bit mid-scale 512 unless a test sets them, so every check that
// predates protocol v1 sees exactly what it always saw.
extern int16_t harness_adc_gp26;
extern int16_t harness_adc_gp27;

static inline int16_t analogReadPin(int pin) {
    return (pin == 27) ? harness_adc_gp27 : harness_adc_gp26;
}

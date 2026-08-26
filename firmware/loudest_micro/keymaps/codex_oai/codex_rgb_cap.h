// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <stdint.h>

/* Apply QMK's live value and board maximum only at the physical LED boundary.
 * The OAI renderer and its C/Python oracle intentionally retain logical
 * 0..255 colors. */
static inline uint8_t codex_rgb_cap_channel(
    uint8_t channel,
    uint8_t current_value,
    uint8_t maximum_brightness
) {
    uint8_t scale = current_value < maximum_brightness ? current_value : maximum_brightness;
    return (uint8_t)(((uint16_t)channel * scale) / 255U);
}

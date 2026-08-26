// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "codex_oai.h"

#define CODEX_LED_COUNT 24
#define CODEX_TASK_LED_COUNT 6
#define CODEX_ACTION_FEEDBACK_FIRST CODEX_TASK_LED_COUNT
#define CODEX_ACTION_FEEDBACK_LAST 12U
#define CODEX_ACTION_FEEDBACK_MS 160
#ifndef CODEX_LED_ANIMATION_ENABLE
#    define CODEX_LED_ANIMATION_ENABLE 0
#endif
#define CODEX_STARTUP_STEP_MS 80U
#define CODEX_STARTUP_FLASH_MS 90U
#define CODEX_STARTUP_COMPLETION_MS (CODEX_STARTUP_FLASH_MS * 4U)
#define CODEX_STARTUP_TOTAL_MS ((CODEX_LED_COUNT * CODEX_STARTUP_STEP_MS) + CODEX_STARTUP_COMPLETION_MS)

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} codex_led_rgb_t;

void codex_led_init(void);
void codex_led_startup_begin(uint32_t now_ms);
bool codex_led_startup_active(uint32_t now_ms);
void codex_led_reset_tasks(uint32_t now_ms);
void codex_led_set_tasks(const codex_oai_task_t tasks[OAI_SLOT_COUNT], uint8_t active_mask, uint32_t now_ms);
void codex_led_set_link(oai_link_state_t state, uint32_t now_ms);
void codex_led_set_layer(uint8_t layer, uint32_t now_ms);
void codex_led_note_action(uint8_t led_index, bool pressed, uint32_t now_ms);
CODEX_OAI_KEEP void codex_led_render(uint32_t now_ms, codex_led_rgb_t output[CODEX_LED_COUNT]);

// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if defined(__clang__)
#    define CODEX_OAI_KEEP __attribute__((used, noinline))
#elif defined(__GNUC__)
#    define CODEX_OAI_KEEP __attribute__((used, noinline, externally_visible))
#else
#    define CODEX_OAI_KEEP
#endif

#define OAI_REPORT_SIZE 64
#define OAI_REPORT_ID 6
#define OAI_CHANNEL_DEBUG 1
#define OAI_CHANNEL_RPC 2
#define OAI_MAX_PAYLOAD 61
#define OAI_RX_CAPACITY 512
#define OAI_MAX_JSON_DEPTH 8
#ifndef OAI_SLOT_COUNT
#    define OAI_SLOT_COUNT 6
#endif

#define OAI_KEYMAP_POSITION_COUNT 15
#define OAI_KEYMAP_STORAGE_ADDRESS 64U
#define OAI_KEYMAP_STORE_VERSION 3U
#define OAI_KEYMAP_STORE_MAGIC 0xC7U

typedef enum {
    OAI_KEYMAP_NOOP = 0,
    OAI_KEYMAP_PREVIOUS,
    OAI_KEYMAP_NEXT,
    OAI_KEYMAP_NEW,
    OAI_KEYMAP_REVIEW,
    OAI_KEYMAP_PLAN,
    OAI_KEYMAP_IMPLEMENT,
    OAI_KEYMAP_REFACTOR,
    OAI_KEYMAP_TEST,
    OAI_KEYMAP_ABORT,
    OAI_KEYMAP_SAFE,
    OAI_KEYMAP_ACCEPT,
    OAI_KEYMAP_SEND,
    OAI_KEYMAP_ENCODER,
    OAI_KEYMAP_MICROPHONE,
    OAI_KEYMAP_ACT11,
    OAI_KEYMAP_ACTION_COUNT,
} codex_oai_keymap_action_t;

typedef enum {
    OAI_LINK_WAITING = 0,
    OAI_LINK_READY = 1,
    OAI_LINK_ERROR = 2,
} oai_link_state_t;

typedef enum {
    OAI_CONTROL_AG00,
    OAI_CONTROL_AG01,
    OAI_CONTROL_AG02,
    OAI_CONTROL_AG03,
    OAI_CONTROL_AG04,
    OAI_CONTROL_AG05,
    OAI_CONTROL_ACT06,
    OAI_CONTROL_ACT07,
    OAI_CONTROL_ACT08,
    OAI_CONTROL_ACT09,
    OAI_CONTROL_ACT10,
    OAI_CONTROL_ACT11,
    OAI_CONTROL_ACT12,
    OAI_CONTROL_ENCODER,
    OAI_CONTROL_ENCODER_CW,
    OAI_CONTROL_ENCODER_CCW,
    OAI_CONTROL_COUNT,
} codex_oai_control_t;

typedef struct {
    uint8_t source_slot;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
    uint8_t effect;
    uint8_t brightness;
    uint8_t speed;
    uint8_t flags;
} codex_oai_task_t;

void codex_oai_init(void);
void codex_oai_reset_keymap(void);
bool codex_oai_ready(void);
bool codex_oai_notify(codex_oai_control_t control, bool pressed);
uint8_t codex_oai_state_revision(void);
uint8_t codex_oai_error_revision(void);
/* Incremented only after a valid v.oai.rgbcfg request. */
uint8_t codex_oai_handshake_revision(void);
oai_link_state_t codex_oai_link_state(void);
bool codex_oai_task_state(codex_oai_task_t *output);
bool codex_oai_task_for_slot(uint8_t slot, codex_oai_task_t *output);
uint8_t codex_oai_visible_task_count(void);
bool codex_oai_visible_task(uint8_t rank, codex_oai_task_t *output);
bool codex_oai_keymap_get(uint8_t output[OAI_KEYMAP_POSITION_COUNT]);
bool codex_oai_keymap_set(const uint8_t input[OAI_KEYMAP_POSITION_COUNT]);
bool codex_oai_keymap_get_hex(char output[OAI_KEYMAP_POSITION_COUNT + 1]);
bool codex_oai_keymap_set_hex(const char *input, size_t length);
uint8_t codex_oai_keymap_action_for_position(uint8_t position);
CODEX_OAI_KEEP void raw_hid_receive(uint8_t *data, uint8_t length);

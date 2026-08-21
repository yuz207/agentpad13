// Host harness for the real AgentPad13 RGB renderer.
// Commands: RESET; TASK <slot> <active> <r> <g> <b> <effect> <brightness>
// <speed> <flags> <now>; LINK <state> <now>; LAYER <layer> <now>;
// ACTION <led> <pressed> <now>; RENDER <now>.  A render prints exactly 24
// LED lines followed by ---.
#include <stdio.h>
#include <string.h>

#include "codex_led.h"

static codex_oai_task_t tasks[OAI_SLOT_COUNT];
static uint8_t active_mask;

static void reset(void) {
    memset(tasks, 0, sizeof(tasks));
    for (uint8_t index = 0; index < OAI_SLOT_COUNT; ++index) tasks[index].source_slot = index;
    active_mask = 0;
    codex_led_init();
}

static void render(uint32_t now_ms) {
    codex_led_rgb_t frame[CODEX_LED_COUNT];
    codex_led_render(now_ms, frame);
    for (uint8_t index = 0; index < CODEX_LED_COUNT; ++index) {
        printf("LED %u %u %u %u\n", index, frame[index].r, frame[index].g, frame[index].b);
    }
    printf("---\n");
    fflush(stdout);
}

int main(void) {
    char line[256];
    reset();
    while (fgets(line, sizeof(line), stdin) != NULL) {
        unsigned slot, active, red, green, blue, effect, brightness, speed, flags;
        unsigned led, pressed, state;
        unsigned long now_ms;
        if (strcmp(line, "RESET\n") == 0) {
            reset();
        } else if (sscanf(line, "CLEAR %lu", &now_ms) == 1) {
            codex_led_reset_tasks((uint32_t)now_ms);
        } else if (sscanf(line, "TASK %u %u %u %u %u %u %u %u %u %lu", &slot, &active, &red, &green, &blue, &effect, &brightness, &speed, &flags, &now_ms) == 10 && slot < OAI_SLOT_COUNT) {
            tasks[slot] = (codex_oai_task_t){(uint8_t)slot, (uint8_t)red, (uint8_t)green, (uint8_t)blue, (uint8_t)effect, (uint8_t)brightness, (uint8_t)speed, (uint8_t)flags};
            if (active != 0U) active_mask |= (uint8_t)(1U << slot);
            else active_mask &= (uint8_t)~(1U << slot);
            codex_led_set_tasks(tasks, active_mask, (uint32_t)now_ms);
        } else if (sscanf(line, "LINK %u %lu", &state, &now_ms) == 2 && state <= OAI_LINK_ERROR) {
            codex_led_set_link((oai_link_state_t)state, (uint32_t)now_ms);
        } else if (sscanf(line, "LAYER %u %lu", &state, &now_ms) == 2) {
            codex_led_set_layer((uint8_t)state, (uint32_t)now_ms);
        } else if (sscanf(line, "ACTION %u %u %lu", &led, &pressed, &now_ms) == 3) {
            codex_led_note_action((uint8_t)led, pressed != 0U, (uint32_t)now_ms);
        } else if (sscanf(line, "STARTUP %lu", &now_ms) == 1) {
            codex_led_startup_begin((uint32_t)now_ms);
        } else if (sscanf(line, "RENDER %lu", &now_ms) == 1) {
            render((uint32_t)now_ms);
        }
    }
    return 0;
}

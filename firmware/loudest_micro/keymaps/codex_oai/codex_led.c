// SPDX-License-Identifier: GPL-2.0-or-later

#include "codex_led.h"

#include <string.h>

#ifdef __AVR__
#    include <avr/pgmspace.h>
#    define LED_PROGMEM PROGMEM
#else
#    define LED_PROGMEM
#endif

enum {
    LED_EFFECT_COUNT = 7,
    LED_TAIL_MS = 240,
    LED_CHROMA_ON_MS = 60,
    LED_CHROMA_OFF_MS = 60,
    LED_ANIMATION_SLOW_FACTOR = 4,
    LED_FADE_MIN_LEVEL = 32,
    LED_LINK_FADE_PERIOD_MS = 2400,
    LED_GLOBAL_INDEX = 12,
    /* Chain index 13 is the physical TP5/layer indicator LED.  Its hue always
     * follows the active layer; link waiting/error is a tint or slow pulse so
     * a layer change is still visible before the OAI handshake. */
    LED_LAYER_INDEX = 13,
    LED_UNDERGLOW_FIRST = 14,
    LED_UNDERGLOW_LAST = 23,
};

static const codex_led_rgb_t layer_colors[] = {
    {255, 0, 0},
    {255, 192, 0},
    {0, 255, 0},
    {0, 255, 192},
    {0, 64, 255},
    {128, 0, 255},
    {255, 0, 192},
    {255, 0, 64},
};

#if CODEX_LED_ANIMATION_ENABLE
typedef enum {
    COLOR_OFF,
    COLOR_RED,
    COLOR_YELLOW,
    COLOR_GREEN,
    COLOR_CYAN,
    COLOR_BLUE,
    COLOR_MAGENTA,
    COLOR_NEUTRAL,
} color_family_t;

typedef struct {
    uint8_t numerator;
    uint8_t denominator;
    uint8_t quarters;
} effect_step_t;

typedef struct {
    uint16_t duration_ms;
    uint8_t eighths;
} working_step_t;

/* Legacy Codex OAI effect timing matrix.  The opt-in animation path retains
 * these relative shapes but interpolates between them with a slow fade. */
static const effect_step_t effect_steps[LED_EFFECT_COUNT][6] LED_PROGMEM = {
    {{2, 1, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0}},
    {{3, 1, 4}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0}, {0, 0, 0}},
    {{1, 1, 4}, {1, 1, 0}, {1, 1, 4}, {1, 1, 0}, {0, 0, 0}, {0, 0, 0}},
    {{1, 1, 1}, {1, 1, 2}, {1, 1, 4}, {1, 1, 2}, {1, 1, 1}, {0, 0, 0}},
    {{1, 1, 0}, {1, 1, 1}, {1, 1, 2}, {1, 1, 4}, {1, 1, 2}, {1, 1, 1}},
    {{1, 2, 4}, {1, 2, 0}, {1, 2, 4}, {2, 1, 0}, {0, 0, 0}, {0, 0, 0}},
    {{1, 2, 4}, {1, 2, 0}, {1, 2, 4}, {1, 2, 0}, {2, 1, 4}, {0, 0, 0}},
};

/* Blue working: the legacy flash/wave/gap sequence, rendered as a slow fade. */
static const working_step_t working_steps[] LED_PROGMEM = {
    {80, 8}, {70, 0}, {80, 8}, {70, 0}, {80, 8}, {70, 0},
    {45, 0}, {45, 1}, {45, 3}, {45, 6}, {45, 8}, {45, 6}, {45, 3}, {45, 1}, {45, 0},
    {80, 8}, {70, 0}, {80, 8}, {70, 0}, {80, 8}, {70, 0}, {240, 0},
};
#endif

typedef struct {
    codex_oai_task_t task;
    uint32_t pattern_start_ms;
    bool active;
} task_context_t;

typedef struct {
    uint32_t started_ms;
    bool active;
} feedback_context_t;

static task_context_t tasks_by_led[CODEX_TASK_LED_COUNT];
static feedback_context_t feedback[LED_GLOBAL_INDEX - CODEX_TASK_LED_COUNT + 1];
static oai_link_state_t link_state;
static uint32_t link_started_ms;
static uint8_t layer_index;
static uint32_t startup_started_ms;
static bool startup_running;

#if CODEX_LED_ANIMATION_ENABLE
static uint8_t effect_numerator(uint8_t effect, uint8_t index) {
#ifdef __AVR__
    return pgm_read_byte(&effect_steps[effect][index].numerator);
#else
    return effect_steps[effect][index].numerator;
#endif
}

static uint8_t effect_denominator(uint8_t effect, uint8_t index) {
#ifdef __AVR__
    return pgm_read_byte(&effect_steps[effect][index].denominator);
#else
    return effect_steps[effect][index].denominator;
#endif
}

static uint8_t effect_quarters(uint8_t effect, uint8_t index) {
#ifdef __AVR__
    return pgm_read_byte(&effect_steps[effect][index].quarters);
#else
    return effect_steps[effect][index].quarters;
#endif
}

static uint16_t working_duration(uint8_t index) {
#ifdef __AVR__
    return pgm_read_word(&working_steps[index].duration_ms);
#else
    return working_steps[index].duration_ms;
#endif
}

static uint8_t working_eighths(uint8_t index) {
#ifdef __AVR__
    return pgm_read_byte(&working_steps[index].eighths);
#else
    return working_steps[index].eighths;
#endif
}

static uint8_t maximum3(uint8_t first, uint8_t second, uint8_t third) {
    uint8_t result = first > second ? first : second;
    return result > third ? result : third;
}

static uint8_t minimum3(uint8_t first, uint8_t second, uint8_t third) {
    uint8_t result = first < second ? first : second;
    return result < third ? result : third;
}

static int16_t divide_floor(int16_t numerator, uint8_t denominator) {
    if (numerator < 0) return (int16_t)-(((-numerator) + denominator - 1) / denominator);
    return numerator / denominator;
}

static color_family_t color_family(const codex_oai_task_t *task) {
    uint8_t highest = maximum3(task->red, task->green, task->blue);
    uint8_t lowest = minimum3(task->red, task->green, task->blue);
    uint8_t difference;
    int16_t hue;

    if (highest == 0U) return COLOR_OFF;
    difference = (uint8_t)(highest - lowest);
    if (difference <= highest / 8U) return COLOR_NEUTRAL;
    if (highest == task->red) {
        hue = divide_floor((int16_t)(60 * ((int16_t)task->green - task->blue)), difference);
        hue %= 360;
        if (hue < 0) hue += 360;
    } else if (highest == task->green) {
        hue = (int16_t)(120 + divide_floor((int16_t)(60 * ((int16_t)task->blue - task->red)), difference));
    } else {
        hue = (int16_t)(240 + divide_floor((int16_t)(60 * ((int16_t)task->red - task->green)), difference));
    }
    if (hue < 30 || hue >= 330) return COLOR_RED;
    if (hue < 90) return COLOR_YELLOW;
    if (hue < 150) return COLOR_GREEN;
    if (hue < 210) return COLOR_CYAN;
    if (hue < 270) return COLOR_BLUE;
    return COLOR_MAGENTA;
}

static uint16_t animation_tick_ms(const codex_oai_task_t *task) {
    uint16_t base = (uint16_t)(120U - (((uint16_t)task->speed * 60U + 127U) / 255U));
    return (uint16_t)(base * LED_ANIMATION_SLOW_FACTOR);
}

static uint8_t fraction_level(uint8_t numerator, uint8_t denominator) {
    return (uint8_t)(((uint16_t)255U * numerator + denominator / 2U) / denominator);
}

static uint8_t fade_target(uint8_t level) {
    return level == 0U ? LED_FADE_MIN_LEVEL : level;
}

static uint8_t fade_between(uint8_t from, uint8_t to, uint16_t position, uint16_t duration) {
    if (duration == 0U || position >= duration) return to;
    if (to >= from) {
        return (uint8_t)(from + (((uint32_t)(to - from) * position + duration / 2U) / duration));
    }
    return (uint8_t)(from - (((uint32_t)(from - to) * position + duration / 2U) / duration));
}

static uint8_t fade_level(uint32_t elapsed, uint16_t period) {
    uint16_t half = period / 2U;
    uint16_t phase;
    uint16_t ramp;

    if (half == 0U) return 255U;
    phase = (uint16_t)(elapsed % period);
    ramp = phase < half ? phase : (uint16_t)(period - phase);
    return fade_between(LED_FADE_MIN_LEVEL, 255U, ramp, half);
}
#endif

static bool is_working_task(const codex_oai_task_t *task) {
    return task->red == 48U && task->green == 79U && task->blue == 254U &&
           (task->effect == 1U || task->effect == 4U) && task->brightness != 0U;
}

static bool task_is_visible(const task_context_t *context) {
    const codex_oai_task_t *task = &context->task;
    return context->active && (task->red != 0U || task->green != 0U || task->blue != 0U) &&
           task->brightness != 0U && task->effect != 0U;
}

#if CODEX_LED_ANIMATION_ENABLE
static uint8_t level_from_working(uint32_t elapsed) {
    uint32_t total = 0;
    uint8_t index;
    uint8_t count = (uint8_t)(sizeof(working_steps) / sizeof(working_steps[0]));

    for (index = 0; index < count; ++index) {
        total += (uint32_t)working_duration(index) * LED_ANIMATION_SLOW_FACTOR;
    }
    elapsed %= total;
    for (index = 0; index < count; ++index) {
        uint16_t duration = (uint16_t)(working_duration(index) * LED_ANIMATION_SLOW_FACTOR);
        if (elapsed < duration) {
            uint8_t next = (uint8_t)((index + 1U) % count);
            uint8_t from = fade_target(fraction_level(working_eighths(index), 8U));
            uint8_t to = fade_target(fraction_level(working_eighths(next), 8U));
            return fade_between(from, to, (uint16_t)elapsed, duration);
        }
        elapsed -= duration;
    }
    return LED_FADE_MIN_LEVEL;
}

static uint8_t level_from_standard(uint32_t elapsed, const codex_oai_task_t *task, color_family_t family) {
    uint16_t tick = animation_tick_ms(task);
    uint32_t total = (uint32_t)LED_TAIL_MS * LED_ANIMATION_SLOW_FACTOR;
    uint8_t effect = task->effect < LED_EFFECT_COUNT ? task->effect : 0U;
    uint8_t index;
    uint32_t prelude;

    if (family >= COLOR_RED && family <= COLOR_MAGENTA) {
        prelude = (uint32_t)family * (LED_CHROMA_ON_MS + LED_CHROMA_OFF_MS) * LED_ANIMATION_SLOW_FACTOR;
    } else {
        prelude = 300U * LED_ANIMATION_SLOW_FACTOR;
    }
    total += prelude;
    for (index = 0; index < 6U && effect_numerator(effect, index) != 0U; ++index) {
        total += (uint32_t)effect_numerator(effect, index) * tick / effect_denominator(effect, index);
    }
    elapsed %= total;
    if (elapsed < prelude) {
        return fade_level(elapsed, (uint16_t)prelude);
    }
    elapsed -= prelude;
    for (index = 0; index < 6U && effect_numerator(effect, index) != 0U; ++index) {
        uint16_t duration = (uint16_t)effect_numerator(effect, index) * tick / effect_denominator(effect, index);
        if (elapsed < duration) {
            uint8_t next = (uint8_t)(index + 1U);
            uint8_t from = fade_target(fraction_level(effect_quarters(effect, index), 4U));
            uint8_t to = next >= 6U || effect_numerator(effect, next) == 0U
                             ? LED_FADE_MIN_LEVEL
                             : fade_target(fraction_level(effect_quarters(effect, next), 4U));
            return fade_between(from, to, (uint16_t)elapsed, duration);
        }
        elapsed -= duration;
    }
    return fade_level(elapsed, LED_TAIL_MS * LED_ANIMATION_SLOW_FACTOR);
}
#endif

static uint8_t task_level(const task_context_t *context, uint32_t now_ms) {
#if CODEX_LED_ANIMATION_ENABLE
    color_family_t family;

    if (!task_is_visible(context)) return 0;
    family = color_family(&context->task);
    if (family == COLOR_OFF) return 0;
    if (is_working_task(&context->task)) return level_from_working(now_ms - context->pattern_start_ms);
    return level_from_standard(now_ms - context->pattern_start_ms, &context->task, family);
#else
    (void)now_ms;
    return task_is_visible(context) ? 255U : 0U;
#endif
}

static codex_led_rgb_t scaled_task_rgb(const task_context_t *context, uint32_t now_ms) {
    uint8_t level = task_level(context, now_ms);
    codex_led_rgb_t output = {0, 0, 0};
    const codex_oai_task_t *task = &context->task;

    output.r = (uint8_t)(((uint32_t)task->red * task->brightness * level + 32512U) / 65025U);
    output.g = (uint8_t)(((uint32_t)task->green * task->brightness * level + 32512U) / 65025U);
    output.b = (uint8_t)(((uint32_t)task->blue * task->brightness * level + 32512U) / 65025U);
    return output;
}

static bool tasks_equal(const codex_oai_task_t *first, const codex_oai_task_t *second) {
    return memcmp(first, second, sizeof(*first)) == 0;
}

static bool incoming_task_is_active(
    const codex_oai_task_t tasks[OAI_SLOT_COUNT],
    uint8_t active_mask,
    uint8_t source_slot
) {
    return tasks != NULL && source_slot < OAI_SLOT_COUNT &&
           (active_mask & (uint8_t)(1U << source_slot)) != 0U;
}

static int8_t context_index_for_source(uint8_t source_slot) {
    for (uint8_t index = 0; index < CODEX_TASK_LED_COUNT; ++index) {
        if (tasks_by_led[index].active && tasks_by_led[index].task.source_slot == source_slot) {
            return (int8_t)index;
        }
    }
    return -1;
}

static void clear_task_context(task_context_t *context, uint32_t now_ms) {
    memset(&context->task, 0, sizeof(context->task));
    context->pattern_start_ms = now_ms;
    context->active = false;
}

static void remove_task_context(uint8_t index, uint32_t now_ms) {
    if (index + 1U < CODEX_TASK_LED_COUNT) {
        memmove(
            &tasks_by_led[index],
            &tasks_by_led[index + 1U],
            sizeof(tasks_by_led[0]) * (CODEX_TASK_LED_COUNT - index - 1U)
        );
    }
    clear_task_context(&tasks_by_led[CODEX_TASK_LED_COUNT - 1U], now_ms);
}

static const task_context_t *global_task(void) {
    const task_context_t *selected = NULL;
    for (uint8_t index = 0; index < CODEX_TASK_LED_COUNT; ++index) {
        if (!task_is_visible(&tasks_by_led[index])) continue;
        if (selected == NULL || (is_working_task(&tasks_by_led[index].task) && !is_working_task(&selected->task))) {
            selected = &tasks_by_led[index];
        }
    }
    return selected;
}

static codex_led_rgb_t layer_rgb(void) {
    return layer_colors[layer_index % (sizeof(layer_colors) / sizeof(layer_colors[0]))];
}

static codex_led_rgb_t layer_indicator_rgb(uint32_t now_ms) {
    codex_led_rgb_t output = layer_rgb();

    /* LED 13 is the authoritative layer indicator.  In particular, CODEX
     * must remain red while the direct OAI endpoint is still waiting: tinting
     * it amber made a fresh CODEX boot indistinguishable from the FN layer. */
#if CODEX_LED_ANIMATION_ENABLE
    if (link_state != OAI_LINK_READY) {
        uint8_t level = fade_level(now_ms - link_started_ms, LED_LINK_FADE_PERIOD_MS);
        output.r = (uint8_t)(((uint16_t)output.r * level + 127U) / 255U);
        output.g = (uint8_t)(((uint16_t)output.g * level + 127U) / 255U);
        output.b = (uint8_t)(((uint16_t)output.b * level + 127U) / 255U);
    }
#else
    (void)now_ms;
#endif
    return output;
}

static bool feedback_is_active(uint8_t led_index, uint32_t now_ms) {
    feedback_context_t *context;
    if (led_index < CODEX_TASK_LED_COUNT || led_index > LED_GLOBAL_INDEX) return false;
    context = &feedback[led_index - CODEX_TASK_LED_COUNT];
    if (!context->active) return false;
    if (now_ms - context->started_ms >= CODEX_ACTION_FEEDBACK_MS) {
        context->active = false;
        return false;
    }
    return true;
}

void codex_led_init(void) {
    memset(feedback, 0, sizeof(feedback));
    link_state = OAI_LINK_WAITING;
    link_started_ms = 0;
    layer_index = 0;
    startup_started_ms = 0;
    startup_running = false;
    codex_led_reset_tasks(0);
}

void codex_led_startup_begin(uint32_t now_ms) {
    startup_started_ms = now_ms;
    startup_running = true;
}

bool codex_led_startup_active(uint32_t now_ms) {
    if (!startup_running) return false;
    if ((uint32_t)(now_ms - startup_started_ms) >= CODEX_STARTUP_TOTAL_MS) {
        startup_running = false;
        return false;
    }
    return true;
}

void codex_led_reset_tasks(uint32_t now_ms) {
    for (uint8_t index = 0; index < CODEX_TASK_LED_COUNT; ++index) {
        clear_task_context(&tasks_by_led[index], now_ms);
    }
}

void codex_led_set_tasks(const codex_oai_task_t tasks[OAI_SLOT_COUNT], uint8_t active_mask, uint32_t now_ms) {
    uint8_t index = 0;

    if (tasks == NULL) {
        codex_led_reset_tasks(now_ms);
        return;
    }

    while (index < CODEX_TASK_LED_COUNT) {
        task_context_t *context = &tasks_by_led[index];
        if (!context->active) {
            break;
        }
        if (!incoming_task_is_active(tasks, active_mask, context->task.source_slot)) {
            remove_task_context(index, now_ms);
            continue;
        }
        ++index;
    }

    for (index = 0; index < CODEX_TASK_LED_COUNT; ++index) {
        task_context_t *context = &tasks_by_led[index];
        if (!context->active) continue;
        const codex_oai_task_t *incoming = &tasks[context->task.source_slot];
        if (!tasks_equal(&context->task, incoming)) {
            context->pattern_start_ms = now_ms;
            context->task = *incoming;
        }
    }

    index = 0;
    while (index < CODEX_TASK_LED_COUNT && tasks_by_led[index].active) {
        ++index;
    }
    for (uint8_t source_slot = 0; source_slot < OAI_SLOT_COUNT; ++source_slot) {
        if (!incoming_task_is_active(tasks, active_mask, source_slot) || context_index_for_source(source_slot) >= 0) {
            continue;
        }
        if (index >= CODEX_TASK_LED_COUNT) {
            remove_task_context(0, now_ms);
            index = CODEX_TASK_LED_COUNT - 1U;
        }
        tasks_by_led[index].task = tasks[source_slot];
        tasks_by_led[index].pattern_start_ms = now_ms;
        tasks_by_led[index].active = true;
        ++index;
    }

    while (index < CODEX_TASK_LED_COUNT) {
        clear_task_context(&tasks_by_led[index], now_ms);
        ++index;
    }
}

void codex_led_set_link(oai_link_state_t state, uint32_t now_ms) {
    if (state != link_state) {
        link_state = state;
        link_started_ms = now_ms;
    }
}

void codex_led_set_layer(uint8_t layer, uint32_t now_ms) {
    (void)now_ms;
    layer_index = layer;
}

void codex_led_note_action(uint8_t led_index, bool pressed, uint32_t now_ms) {
    if (pressed && led_index >= CODEX_TASK_LED_COUNT && led_index <= LED_GLOBAL_INDEX) {
        feedback_context_t *context = &feedback[led_index - CODEX_TASK_LED_COUNT];
        context->active = true;
        context->started_ms = now_ms;
    }
}

void codex_led_render(uint32_t now_ms, codex_led_rgb_t output[CODEX_LED_COUNT]) {
    const task_context_t *global;
    codex_led_rgb_t global_rgb = {0, 0, 0};

    if (output == NULL) return;
    memset(output, 0, sizeof(codex_led_rgb_t) * CODEX_LED_COUNT);
    for (uint8_t index = 0; index < CODEX_TASK_LED_COUNT; ++index) {
        output[index] = scaled_task_rgb(&tasks_by_led[index], now_ms);
    }
    global = global_task();
    if (global != NULL) global_rgb = scaled_task_rgb(global, now_ms);
    output[LED_GLOBAL_INDEX] = global_rgb;
    output[LED_LAYER_INDEX] = layer_indicator_rgb(now_ms);
    for (uint8_t index = LED_UNDERGLOW_FIRST; index <= LED_UNDERGLOW_LAST; ++index) {
        output[index].r = global_rgb.r / 2U;
        output[index].g = global_rgb.g / 2U;
        output[index].b = global_rgb.b / 2U;
    }
    for (uint8_t index = CODEX_TASK_LED_COUNT; index <= LED_GLOBAL_INDEX; ++index) {
        if (feedback_is_active(index, now_ms)) {
            output[index].r = 255U;
            output[index].g = 255U;
            output[index].b = 255U;
        }
    }

    if (codex_led_startup_active(now_ms)) {
        uint32_t elapsed = (uint32_t)(now_ms - startup_started_ms);
        memset(output, 0, sizeof(codex_led_rgb_t) * CODEX_LED_COUNT);
        if (elapsed < CODEX_LED_COUNT * CODEX_STARTUP_STEP_MS) {
            uint8_t led = (uint8_t)(elapsed / CODEX_STARTUP_STEP_MS);
            output[led].r = 255U;
            output[led].g = 255U;
            output[led].b = 255U;
        } else if (((elapsed - CODEX_LED_COUNT * CODEX_STARTUP_STEP_MS) / CODEX_STARTUP_FLASH_MS) % 2U == 0U) {
            for (uint8_t led = 0; led < CODEX_LED_COUNT; ++led) {
                output[led].g = 255U;
            }
        }
    }
}

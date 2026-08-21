// Host contract for the shared SW14 calibration overlay under custom RGB ownership.
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    uint8_t h;
    uint8_t s;
    uint8_t v;
} HSV;

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} RGB;

uint8_t rgb_matrix_get_val(void);
RGB     hsv_to_rgb(HSV hsv);
void    rgb_matrix_set_color(uint8_t index, uint8_t r, uint8_t g, uint8_t b);
bool    rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max);

uint32_t layer_state;
uint32_t default_layer_state;
uint8_t  get_highest_layer(uint32_t state);

#include "loudest_micro.c"

#define USER_EVENT 0xFF

static uint8_t events[LOUDEST_LED_COUNT + 1];
static uint8_t red[LOUDEST_LED_COUNT];
static uint8_t green[LOUDEST_LED_COUNT];
static uint8_t blue[LOUDEST_LED_COUNT];
static uint8_t event_count;

int16_t harness_adc_gp26 = 512;
int16_t harness_adc_gp27 = 512;

sio_hw_t    harness_sio_hw    = {.gpio_hi_in = 0xFFFFFFFFu};
ioqspi_hw_t harness_ioqspi_hw = {0};

void raw_hid_send(uint8_t *data, uint8_t length) {
    (void)data;
    (void)length;
}

void layer_move(uint8_t layer) {
    (void)layer;
}

uint8_t get_highest_layer(uint32_t state) {
    (void)state;
    return 0;
}

bool eeconfig_is_kb_datablock_valid(void) {
    return true;
}

uint32_t eeconfig_read_kb_datablock(void *data, uint32_t offset, uint32_t length) {
    (void)offset;
    memset(data, 0, length);
    return length;
}

uint32_t eeconfig_update_kb_datablock(const void *data, uint32_t offset, uint32_t length) {
    (void)data;
    (void)offset;
    return length;
}

void eeconfig_init_kb_datablock(void) {
}

uint8_t rgb_matrix_get_val(void) {
    return 64;
}

RGB hsv_to_rgb(HSV hsv) {
    if (hsv.s == 0) {
        return (RGB){.r = hsv.v, .g = hsv.v, .b = hsv.v};
    }
    return (RGB){.r = hsv.h, .g = hsv.s, .b = hsv.v};
}

void rgb_matrix_set_color(uint8_t index, uint8_t r, uint8_t g, uint8_t b) {
    if (event_count < sizeof(events)) {
        events[event_count++] = index;
    }
    red[index]   = r;
    green[index] = g;
    blue[index]  = b;
}

bool rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max) {
    (void)led_min;
    (void)led_max;
    events[event_count++] = USER_EVENT;
    return false;
}

static void reset_events(void) {
    memset(events, 0, sizeof(events));
    memset(red, 0, sizeof(red));
    memset(green, 0, sizeof(green));
    memset(blue, 0, sizeof(blue));
    event_count = 0;
}

int main(void) {
#if defined(LOUDEST_CUSTOM_RGB_STATUS)
    selfcal_state = SELFCAL_IDLE;
    reset_events();
    if (rgb_matrix_indicators_advanced_kb(0, LOUDEST_LED_COUNT)) {
        return 1;
    }
    if (event_count != 1 || events[0] != USER_EVENT) {
        return 2;
    }

    selfcal_state = SELFCAL_ARMED;
    reset_events();
    if (rgb_matrix_indicators_advanced_kb(0, LOUDEST_LED_COUNT)) {
        return 3;
    }
    if (event_count != 14 || events[0] != USER_EVENT) {
        return 4;
    }
    for (uint8_t index = 0; index < 13; index++) {
        if (events[index + 1] != index) {
            return 5;
        }
        if (red[index] != 128 || green[index] != 128 || blue[index] != 128) {
            return 6;
        }
    }
#else
    loudest_status[0] = (loudest_status_t){
        .r = 1, .g = 2, .b = 3, .effect = LOUDEST_FX_SOLID, .active = true};
    selfcal_state = SELFCAL_ARMED;
    reset_events();
    if (rgb_matrix_indicators_advanced_kb(0, LOUDEST_LED_COUNT)) {
        return 7;
    }
    if (event_count != 15 || events[14] != USER_EVENT) {
        return 8;
    }
    for (uint8_t index = 0; index <= LOUDEST_LED_INDICATOR; index++) {
        if (events[index] != index) {
            return 9;
        }
    }
    if (red[0] != 1 || green[0] != 2 || blue[0] != 3) {
        return 10;
    }
    for (uint8_t index = 1; index < 13; index++) {
        if (red[index] != 128 || green[index] != 128 || blue[index] != 128) {
            return 11;
        }
    }
#endif
    return 0;
}

// Protocol-conformance harness: compiles the REAL firmware source
// (loudest_micro.c) against host stubs and drives its raw HID entry points
// with frames from stdin (one 64-hex-char line per 32-byte frame).
//
// Build modes:
//   default build:  cc -DRAW_ENABLE                        -> raw_hid_receive()
//   vial build:     cc -DRAW_ENABLE -DVIA_ENABLE
//                      -DVIAL_MODE -DDYNAMIC_KEYMAP_LAYER_COUNT=8
//                                                          -> via_command_kb()
//
// Per input frame the harness prints, deterministically:
//   CLAIMED 0|1        (vial mode only: pre-hook verdict)
//   SENT <hex>         for every raw_hid_send() the firmware made
//   LAYER <n>          for every layer_move() the firmware made
//   KEY <i> <r> <g> <b> <fx>   for every active per-chain status slot
//   EEWRITES <n>       EEPROM datablock writes caused by THIS frame
//   EEBLOCK <hex>      the whole simulated EEPROM datablock afterwards
//   ---
//
// Non-frame input lines set device state for the frames that follow:
//   ADC <gp26> <gp27>  what the two joystick pins read (protocol v1 live axes)
//   LEN <n>            the `length` argument handed to the firmware, so a
//                      truncated frame can be tested (default 32)
//   EE <hex>           preload the simulated EEPROM datablock (no write counted)
//   BOOT               run keyboard_post_init_kb(), i.e. the power-on EEPROM load
#include <stdio.h>
#include <string.h>

#include "loudest_micro.c" // the real firmware TU, statics visible

#define MAX_EVENTS 64
static uint8_t sent[MAX_EVENTS][LOUDEST_REPORT_LEN];
static int     sent_n;
static uint8_t layers[MAX_EVENTS];
static int     layers_n;

// Joystick pins, read through stubs/analog.h. 512 is the 10-bit mid-scale every
// pre-v1 check assumed, so leaving them alone changes nothing.
int16_t harness_adc_gp26 = 512;
int16_t harness_adc_gp27 = 512;

// SW14 / QSPI_CS register backing, read through stubs/hardware/structs/*.h, so
// the firmware's on-board calibration routine compiles here as the SAME
// unconditional source that ships -- no #ifdef splits the tested code from the
// shipped code.
//
// gpio_hi_in starts all-ones, i.e. SW14 RELEASED (the line idles high and SW14
// pulls it to GND). Combined with the stubbed timer -- stubs/quantum.h returns
// 0 from timer_elapsed32(), so the routine's 100 ms SW14 poll never comes due
// -- the routine is inert off target and every pre-existing check sees exactly
// the device it always saw. Both facts are load-bearing for the check count.
sio_hw_t    harness_sio_hw    = {.gpio_hi_in = 0xFFFFFFFFu};
ioqspi_hw_t harness_ioqspi_hw = {0};

// Simulated QMK keyboard-level EEPROM datablock. The firmware's calibration
// struct is 14 bytes; 64 leaves room without the harness caring about layout.
#define HARNESS_EE_SIZE 64
static uint8_t ee_block[HARNESS_EE_SIZE];
static bool    ee_valid = true; // QMK marks the block valid on first boot
static int     ee_writes;       // writes caused by the frame being handled

void raw_hid_send(uint8_t *data, uint8_t length) {
    if (length == LOUDEST_REPORT_LEN && sent_n < MAX_EVENTS) {
        memcpy(sent[sent_n++], data, length);
    }
}

void layer_move(uint8_t layer) {
    if (layers_n < MAX_EVENTS) {
        layers[layers_n++] = layer;
    }
}

bool eeconfig_is_kb_datablock_valid(void) {
    return ee_valid;
}

uint32_t eeconfig_read_kb_datablock(void *data, uint32_t offset, uint32_t length) {
    if (offset + length > HARNESS_EE_SIZE) return 0;
    memcpy(data, &ee_block[offset], length);
    return length;
}

uint32_t eeconfig_update_kb_datablock(const void *data, uint32_t offset, uint32_t length) {
    if (offset + length > HARNESS_EE_SIZE) return 0;
    memcpy(&ee_block[offset], data, length);
    ee_valid = true;
    ee_writes++;
    return length;
}

void eeconfig_init_kb_datablock(void) {
    memset(ee_block, 0, sizeof ee_block);
    ee_valid = true;
    ee_writes++;
}

int main(void) {
    char line[256];
    int  frame_len = LOUDEST_REPORT_LEN;
    while (fgets(line, sizeof line, stdin)) {
        int adc_x, adc_y, len;
        if (sscanf(line, "ADC %d %d", &adc_x, &adc_y) == 2) {
            harness_adc_gp26 = (int16_t)adc_x;
            harness_adc_gp27 = (int16_t)adc_y;
            continue;
        }
        if (sscanf(line, "LEN %d", &len) == 1) {
            frame_len = (len < 0) ? 0 : (len > LOUDEST_REPORT_LEN ? LOUDEST_REPORT_LEN : len);
            continue;
        }
        if (!strncmp(line, "EE ", 3)) {
            // Seed the block directly, the way a previously-calibrated (or
            // corrupted) board comes up. Deliberately NOT counted as a write.
            memset(ee_block, 0, sizeof ee_block);
            for (int i = 0; i < HARNESS_EE_SIZE; i++) {
                unsigned v;
                if (sscanf(&line[3 + i * 2], "%2x", &v) != 1) break;
                ee_block[i] = (uint8_t)v;
            }
            continue;
        }
        if (!strncmp(line, "BOOT", 4)) {
            ee_writes = 0;
            keyboard_post_init_kb();
            printf("EEWRITES %d\n", ee_writes);
            printf("---\n");
            fflush(stdout);
            continue;
        }

        uint8_t frame[LOUDEST_REPORT_LEN] = {0};
        int     n = 0;
        for (; n < LOUDEST_REPORT_LEN; n++) {
            unsigned v;
            if (sscanf(&line[n * 2], "%2x", &v) != 1) break;
            frame[n] = (uint8_t)v;
        }
        if (n != LOUDEST_REPORT_LEN) continue; // skip malformed input lines

        sent_n = layers_n = ee_writes = 0;
#ifdef VIAL_MODE
        bool claimed = via_command_kb(frame, (uint8_t)frame_len);
        printf("CLAIMED %d\n", claimed ? 1 : 0);
#else
        raw_hid_receive(frame, (uint8_t)frame_len);
#endif
        for (int i = 0; i < sent_n; i++) {
            printf("SENT ");
            for (int j = 0; j < LOUDEST_REPORT_LEN; j++) printf("%02x", sent[i][j]);
            printf("\n");
        }
        for (int i = 0; i < layers_n; i++) printf("LAYER %d\n", layers[i]);
        for (int i = 0; i < LOUDEST_LED_COUNT; i++) {
            if (loudest_status[i].active) {
                printf("KEY %d %d %d %d %d\n", i, loudest_status[i].r,
                       loudest_status[i].g, loudest_status[i].b,
                       loudest_status[i].effect);
            }
        }
        printf("EEWRITES %d\n", ee_writes);
        printf("EEBLOCK ");
        for (int i = 0; i < HARNESS_EE_SIZE; i++) printf("%02x", ee_block[i]);
        printf("\n");
        printf("---\n");
        fflush(stdout);
    }
    return 0;
}

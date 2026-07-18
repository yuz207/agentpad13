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
//   ---
#include <stdio.h>
#include <string.h>

#include "loudest_micro.c" // the real firmware TU, statics visible

#define MAX_EVENTS 64
static uint8_t sent[MAX_EVENTS][LOUDEST_REPORT_LEN];
static int     sent_n;
static uint8_t layers[MAX_EVENTS];
static int     layers_n;

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

int main(void) {
    char line[256];
    while (fgets(line, sizeof line, stdin)) {
        uint8_t frame[LOUDEST_REPORT_LEN] = {0};
        int     n = 0;
        for (; n < LOUDEST_REPORT_LEN; n++) {
            unsigned v;
            if (sscanf(&line[n * 2], "%2x", &v) != 1) break;
            frame[n] = (uint8_t)v;
        }
        if (n != LOUDEST_REPORT_LEN) continue; // skip malformed input lines

        sent_n = layers_n = 0;
#ifdef VIAL_MODE
        bool claimed = via_command_kb(frame, LOUDEST_REPORT_LEN);
        printf("CLAIMED %d\n", claimed ? 1 : 0);
#else
        raw_hid_receive(frame, LOUDEST_REPORT_LEN);
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
        printf("---\n");
        fflush(stdout);
    }
    return 0;
}

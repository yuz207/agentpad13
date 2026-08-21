// Host harness for the real AgentPad13 OAI firmware engine.
//
// Commands read from stdin:
//   RESET
//   FRAME <128 hex characters>
//   NOTIFY <OAI control name> <0|1>
// Each command emits zero or more SENT reports, the current READY value, and
// a terminating --- line. This keeps the C Raw HID boundary real while
// making the wire contract convenient to assert from Python.
#define RAW_EPSIZE 64
#define RAW_REPORT_ID 6

#include <stdio.h>
#include <string.h>

#include "codex_oai.h"
#include "wear_leveling.h"

static uint8_t wear_store[256];

static void write_keymap(uint8_t version, const uint8_t map[OAI_KEYMAP_POSITION_COUNT]) {
    uint8_t checksum = (uint8_t)(OAI_KEYMAP_STORE_MAGIC ^ version);
    wear_store[OAI_KEYMAP_STORAGE_ADDRESS] = OAI_KEYMAP_STORE_MAGIC;
    wear_store[OAI_KEYMAP_STORAGE_ADDRESS + 1U] = version;
    for (uint8_t index = 0; index < OAI_KEYMAP_POSITION_COUNT; ++index) {
        checksum = (uint8_t)((checksum << 1) ^ (checksum >> 7) ^ map[index]);
        wear_store[OAI_KEYMAP_STORAGE_ADDRESS + 2U + index] = map[index];
    }
    wear_store[OAI_KEYMAP_STORAGE_ADDRESS + 2U + OAI_KEYMAP_POSITION_COUNT] = checksum;
}

static void write_legacy_keymap(const uint8_t map[OAI_KEYMAP_POSITION_COUNT]) {
    write_keymap(1U, map);
}

static void seed_legacy_keymap(void) {
    static const uint8_t legacy_map[OAI_KEYMAP_POSITION_COUNT] = {
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 13, 1,
    };
    write_legacy_keymap(legacy_map);
}

static void seed_current_legacy_keymap(void) {
    static const uint8_t legacy_map[OAI_KEYMAP_POSITION_COUNT] = {
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 13, 1,
    };
    write_keymap(OAI_KEYMAP_STORE_VERSION, legacy_map);
}

static void seed_legacy_custom_keymap(void) {
    static const uint8_t custom_map[OAI_KEYMAP_POSITION_COUNT] = {
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0,
    };
    write_legacy_keymap(custom_map);
}

wear_leveling_status_t wear_leveling_init(void) {
    return WEAR_LEVELING_SUCCESS;
}

wear_leveling_status_t wear_leveling_erase(void) {
    memset(wear_store, 0, sizeof(wear_store));
    return WEAR_LEVELING_SUCCESS;
}

wear_leveling_status_t wear_leveling_write(uint32_t address, const void *value, size_t length) {
    if (value == NULL || address > sizeof(wear_store) || length > sizeof(wear_store) - address) {
        return WEAR_LEVELING_FAILED;
    }
    memcpy(&wear_store[address], value, length);
    return WEAR_LEVELING_SUCCESS;
}

wear_leveling_status_t wear_leveling_read(uint32_t address, void *value, size_t length) {
    if (value == NULL || address > sizeof(wear_store) || length > sizeof(wear_store) - address) {
        return WEAR_LEVELING_FAILED;
    }
    memcpy(value, &wear_store[address], length);
    return WEAR_LEVELING_SUCCESS;
}

static uint8_t sent[64][OAI_REPORT_SIZE];
static uint8_t sent_count;

void raw_hid_send(uint8_t *data, uint8_t length) {
    if (length == OAI_REPORT_SIZE && sent_count < 64) {
        memcpy(sent[sent_count++], data, OAI_REPORT_SIZE);
    }
}

static bool control_from_name(const char *name, codex_oai_control_t *control) {
    static const struct {
        const char          *name;
        codex_oai_control_t control;
    } controls[] = {
        {"AG00", OAI_CONTROL_AG00}, {"AG01", OAI_CONTROL_AG01},
        {"AG02", OAI_CONTROL_AG02}, {"AG03", OAI_CONTROL_AG03},
        {"AG04", OAI_CONTROL_AG04}, {"AG05", OAI_CONTROL_AG05},
        {"ACT06", OAI_CONTROL_ACT06}, {"ACT07", OAI_CONTROL_ACT07},
        {"ACT08", OAI_CONTROL_ACT08}, {"ACT09", OAI_CONTROL_ACT09},
        {"ACT10", OAI_CONTROL_ACT10}, {"ACT11", OAI_CONTROL_ACT11},
        {"ACT12", OAI_CONTROL_ACT12},
        {"ENC", OAI_CONTROL_ENCODER}, {"ENC_CW", OAI_CONTROL_ENCODER_CW},
        {"ENC_CC", OAI_CONTROL_ENCODER_CCW},
    };

    for (size_t index = 0; index < sizeof(controls) / sizeof(controls[0]); ++index) {
        if (strcmp(name, controls[index].name) == 0) {
            *control = controls[index].control;
            return true;
        }
    }
    return false;
}

static bool parse_hex_report(const char *text, uint8_t output[OAI_REPORT_SIZE]) {
    for (uint8_t index = 0; index < OAI_REPORT_SIZE; ++index) {
        unsigned value;
        if (sscanf(text + ((size_t)index * 2), "%2x", &value) != 1) {
            return false;
        }
        output[index] = (uint8_t)value;
    }
    return text[OAI_REPORT_SIZE * 2] == '\0' || text[OAI_REPORT_SIZE * 2] == '\n';
}

static void print_result(void) {
    for (uint8_t report_index = 0; report_index < sent_count; ++report_index) {
        printf("SENT ");
        for (uint8_t byte_index = 0; byte_index < OAI_REPORT_SIZE; ++byte_index) {
            printf("%02x", sent[report_index][byte_index]);
        }
        printf("\n");
    }
    printf("READY %d\n", codex_oai_ready() ? 1 : 0);
    printf("LINK %d\n", codex_oai_link_state());
    printf("REVISION %u\n", codex_oai_state_revision());
    printf("ERROR_REVISION %u\n", codex_oai_error_revision());
    printf("HANDSHAKE_REVISION %u\n", codex_oai_handshake_revision());
    for (uint8_t index = 0; index < OAI_SLOT_COUNT; ++index) {
        codex_oai_task_t task;
        if (codex_oai_task_for_slot(index, &task)) {
            printf(
                "SLOT %u %u %u %u %u %u %u %u\n",
                task.source_slot,
                task.red,
                task.green,
                task.blue,
                task.effect,
                task.brightness,
                task.speed,
                task.flags
            );
        }
    }
    printf("---\n");
    fflush(stdout);
}

int main(void) {
    char line[320];
    codex_oai_init();

    while (fgets(line, sizeof(line), stdin) != NULL) {
        sent_count = 0;
        if (strcmp(line, "RESET\n") == 0) {
            codex_oai_init();
        } else if (strcmp(line, "CORRUPT\n") == 0) {
            wear_store[OAI_KEYMAP_STORAGE_ADDRESS] ^= 0xFFU;
        } else if (strcmp(line, "LEGACY\n") == 0) {
            seed_legacy_keymap();
        } else if (strcmp(line, "CURRENT_LEGACY\n") == 0) {
            seed_current_legacy_keymap();
        } else if (strcmp(line, "LEGACY_CUSTOM\n") == 0) {
            seed_legacy_custom_keymap();
        } else if (strncmp(line, "FRAME ", 6) == 0) {
            uint8_t report[OAI_REPORT_SIZE];
            if (parse_hex_report(line + 6, report)) {
                raw_hid_receive(report, OAI_REPORT_SIZE);
            }
        } else if (strncmp(line, "NOTIFY ", 7) == 0) {
            char name[16];
            int  pressed;
            codex_oai_control_t control;
            if (
                sscanf(line + 7, "%15s %d", name, &pressed) == 2
                && (pressed == 0 || pressed == 1)
                && control_from_name(name, &control)
            ) {
                (void)codex_oai_notify(control, pressed != 0);
            }
        }
        print_result();
    }
    return 0;
}

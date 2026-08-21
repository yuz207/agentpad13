// SPDX-License-Identifier: GPL-2.0-or-later

#include "codex_oai.h"

#include <stddef.h>
#include <string.h>

#include "raw_hid.h"

#if defined(WEAR_LEVELING_ENABLE) || defined(EEPROM_WEAR_LEVELING)
#    define CODEX_OAI_HAS_WEAR_LEVELING
#    include "wear_leveling.h"
#endif

#if !defined(RAW_EPSIZE) || RAW_EPSIZE != OAI_REPORT_SIZE
#    error "The OAI probe requires a 64-byte Raw HID endpoint"
#endif

#if !defined(RAW_REPORT_ID) || RAW_REPORT_ID != OAI_REPORT_ID
#    error "The OAI probe requires HID Report ID 6"
#endif

typedef struct {
    char     method[20];
    uint16_t id;
    size_t   params_start;
    size_t   params_end;
    bool     has_method;
    bool     has_id;
    bool     has_params;
} oai_request_t;

typedef struct {
    uint8_t red;
    uint8_t green;
    uint8_t blue;
    uint8_t effect;
    uint8_t brightness;
    uint8_t speed;
    uint8_t flags;
} oai_slot_t;

typedef struct {
    uint8_t id;
    oai_slot_t value;
    uint8_t fields;
} oai_slot_update_t;

enum {
    SLOT_RED = 1 << 0,
    SLOT_GREEN = 1 << 1,
    SLOT_BLUE = 1 << 2,
    SLOT_EFFECT = 1 << 3,
    SLOT_BRIGHTNESS = 1 << 4,
    SLOT_SPEED = 1 << 5,
    SLOT_SYNC_KEY = 1 << 6,
    SLOT_SYNC_ALL = 1 << 7,
};

static char     rx_buffer[OAI_RX_CAPACITY + 1];
static uint16_t rx_length;
static char     container_stack[OAI_MAX_JSON_DEPTH];
static uint8_t  container_depth;
static bool     collecting;
static bool     in_string;
static bool     escaped;
static bool     invalid_object;
static bool     overflowed;
static bool     saw_rgbcfg;
static bool     saw_thstatus;
static uint8_t  state_revision;
static uint8_t  error_revision;
static uint8_t  handshake_revision;
static bool     last_event_was_error;
static oai_slot_t slots[OAI_SLOT_COUNT];
static uint8_t  oai_keymap[OAI_KEYMAP_POSITION_COUNT];

static const uint8_t default_oai_keymap[OAI_KEYMAP_POSITION_COUNT] = {
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
    OAI_KEYMAP_ACT11,
    OAI_KEYMAP_SEND,
    OAI_KEYMAP_ENCODER,
    OAI_KEYMAP_PREVIOUS,
};

static const uint8_t legacy_default_oai_keymap[OAI_KEYMAP_POSITION_COUNT] = {
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
    OAI_KEYMAP_SEND,
    OAI_KEYMAP_ENCODER,
    OAI_KEYMAP_PREVIOUS,
};

static const uint8_t previous_default_oai_keymap[OAI_KEYMAP_POSITION_COUNT] = {
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
    OAI_KEYMAP_MICROPHONE,
    OAI_KEYMAP_ENCODER,
    OAI_KEYMAP_PREVIOUS,
};

typedef struct {
    uint8_t magic;
    uint8_t version;
    uint8_t map[OAI_KEYMAP_POSITION_COUNT];
    uint8_t checksum;
} oai_keymap_store_t;

static bool is_space(char value) {
    return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

static int8_t hex_digit_value(unsigned char value) {
    if (value >= '0' && value <= '9') return (int8_t)(value - '0');
    if (value >= 'a' && value <= 'f') return (int8_t)(value - 'a' + 10);
    if (value >= 'A' && value <= 'F') return (int8_t)(value - 'A' + 10);
    return -1;
}

static char hex_digit(uint8_t value) {
    return value < 10U ? (char)('0' + value) : (char)('a' + value - 10U);
}

static bool keymap_values_valid(const uint8_t map[OAI_KEYMAP_POSITION_COUNT]) {
    if (map == NULL) {
        return false;
    }
    for (uint8_t position = 0; position < OAI_KEYMAP_POSITION_COUNT; ++position) {
        if (map[position] >= OAI_KEYMAP_ACTION_COUNT) {
            return false;
        }
        if (map[position] == OAI_KEYMAP_ENCODER && position != 13U) {
            return false;
        }
    }
    return true;
}

static uint8_t keymap_checksum(const oai_keymap_store_t *store) {
    uint8_t checksum = (uint8_t)(OAI_KEYMAP_STORE_MAGIC ^ store->version);
    for (uint8_t index = 0; index < OAI_KEYMAP_POSITION_COUNT; ++index) {
        checksum = (uint8_t)((checksum << 1) ^ (checksum >> 7) ^ store->map[index]);
    }
    return checksum;
}

static void keymap_defaults(void) {
    memcpy(oai_keymap, default_oai_keymap, sizeof(oai_keymap));
}

static void keymap_persist(void) {
#if defined(CODEX_OAI_HAS_WEAR_LEVELING)
    oai_keymap_store_t store = {
        .magic = OAI_KEYMAP_STORE_MAGIC,
        .version = OAI_KEYMAP_STORE_VERSION,
    };
    memcpy(store.map, oai_keymap, sizeof(store.map));
    store.checksum = keymap_checksum(&store);
    (void)wear_leveling_write(OAI_KEYMAP_STORAGE_ADDRESS, &store, sizeof(store));
#endif
}

static void keymap_load(void) {
    keymap_defaults();
#if defined(CODEX_OAI_HAS_WEAR_LEVELING)
    oai_keymap_store_t store;
    memset(&store, 0, sizeof(store));
    if (
        wear_leveling_read(OAI_KEYMAP_STORAGE_ADDRESS, &store, sizeof(store)) == WEAR_LEVELING_SUCCESS
        && store.magic == OAI_KEYMAP_STORE_MAGIC
        && store.checksum == keymap_checksum(&store)
        && keymap_values_valid(store.map)
    ) {
        bool factory_map =
            memcmp(store.map, legacy_default_oai_keymap, sizeof(store.map)) == 0
            || memcmp(store.map, previous_default_oai_keymap, sizeof(store.map)) == 0;
        if (store.version == OAI_KEYMAP_STORE_VERSION) {
            if (factory_map) {
                keymap_defaults();
                keymap_persist();
            } else {
                memcpy(oai_keymap, store.map, sizeof(oai_keymap));
            }
            return;
        }
        if (store.version == 1U || store.version == 2U) {
            if (factory_map) {
                keymap_defaults();
            } else {
                memcpy(oai_keymap, store.map, sizeof(oai_keymap));
            }
            keymap_persist();
            return;
        }
    }
    keymap_persist();
#endif
}

static void reset_rx(void) {
    rx_length = 0;
    container_depth = 0;
    collecting = false;
    in_string = false;
    escaped = false;
    invalid_object = false;
    overflowed = false;
}

void codex_oai_init(void) {
    memset(rx_buffer, 0, sizeof(rx_buffer));
    memset(container_stack, 0, sizeof(container_stack));
    memset(slots, 0, sizeof(slots));
    reset_rx();
    saw_rgbcfg = false;
    saw_thstatus = false;
    state_revision = 0;
    error_revision = 0;
    handshake_revision = 0;
    last_event_was_error = false;
    keymap_load();
}

void codex_oai_reset_keymap(void) {
    keymap_defaults();
    keymap_persist();
}

bool codex_oai_keymap_get(uint8_t output[OAI_KEYMAP_POSITION_COUNT]) {
    if (output == NULL) {
        return false;
    }
    memcpy(output, oai_keymap, OAI_KEYMAP_POSITION_COUNT);
    return true;
}

bool codex_oai_keymap_set(const uint8_t input[OAI_KEYMAP_POSITION_COUNT]) {
    if (!keymap_values_valid(input)) {
        return false;
    }
#if defined(CODEX_OAI_HAS_WEAR_LEVELING)
    oai_keymap_store_t store = {
        .magic = OAI_KEYMAP_STORE_MAGIC,
        .version = OAI_KEYMAP_STORE_VERSION,
    };
    memcpy(store.map, input, sizeof(store.map));
    store.checksum = keymap_checksum(&store);
    if (wear_leveling_write(OAI_KEYMAP_STORAGE_ADDRESS, &store, sizeof(store)) == WEAR_LEVELING_FAILED) {
        return false;
    }
#endif
    memcpy(oai_keymap, input, OAI_KEYMAP_POSITION_COUNT);
    return true;
}

bool codex_oai_keymap_get_hex(char output[OAI_KEYMAP_POSITION_COUNT + 1]) {
    if (output == NULL) {
        return false;
    }
    for (uint8_t position = 0; position < OAI_KEYMAP_POSITION_COUNT; ++position) {
        output[position] = hex_digit(oai_keymap[position]);
    }
    output[OAI_KEYMAP_POSITION_COUNT] = '\0';
    return true;
}

bool codex_oai_keymap_set_hex(const char *input, size_t length) {
    if (input == NULL || length != OAI_KEYMAP_POSITION_COUNT) {
        return false;
    }
    uint8_t candidate[OAI_KEYMAP_POSITION_COUNT];
    for (uint8_t position = 0; position < OAI_KEYMAP_POSITION_COUNT; ++position) {
        int8_t value = hex_digit_value((unsigned char)input[position]);
        if (value < 0) {
            return false;
        }
        candidate[position] = (uint8_t)value;
    }
    return codex_oai_keymap_set(candidate);
}

uint8_t codex_oai_keymap_action_for_position(uint8_t position) {
    if (position >= OAI_KEYMAP_POSITION_COUNT) {
        return OAI_KEYMAP_NOOP;
    }
    return oai_keymap[position];
}

bool codex_oai_ready(void) {
    return saw_rgbcfg && saw_thstatus;
}

uint8_t codex_oai_state_revision(void) {
    return state_revision;
}

uint8_t codex_oai_error_revision(void) {
    return error_revision;
}

uint8_t codex_oai_handshake_revision(void) {
    return handshake_revision;
}

oai_link_state_t codex_oai_link_state(void) {
    if (last_event_was_error) {
        return OAI_LINK_ERROR;
    }
    return codex_oai_ready() ? OAI_LINK_READY : OAI_LINK_WAITING;
}

static void note_error(void) {
    ++error_revision;
    last_event_was_error = true;
}

static void note_valid_request(void) {
    last_event_was_error = false;
}

static bool slot_is_visible(const oai_slot_t *slot) {
    return (
        (slot->red != 0 || slot->green != 0 || slot->blue != 0)
        && slot->brightness != 0
        && slot->effect != 0
    );
}

static void copy_task(uint8_t source_slot, const oai_slot_t *slot, codex_oai_task_t *output) {
    output->source_slot = source_slot;
    output->red = slot->red;
    output->green = slot->green;
    output->blue = slot->blue;
    output->effect = slot->effect;
    output->brightness = slot->brightness;
    output->speed = slot->speed;
    output->flags = slot->flags;
}

uint8_t codex_oai_visible_task_count(void) {
    uint8_t count = 0;
    for (uint8_t index = 0; index < OAI_SLOT_COUNT; ++index) {
        if (slot_is_visible(&slots[index])) {
            ++count;
        }
    }
    return count;
}

bool codex_oai_visible_task(uint8_t rank, codex_oai_task_t *output) {
    if (rank >= OAI_SLOT_COUNT || output == NULL) {
        return false;
    }
    uint8_t visible_rank = 0;
    for (uint8_t index = 0; index < OAI_SLOT_COUNT; ++index) {
        if (!slot_is_visible(&slots[index])) {
            continue;
        }
        if (visible_rank == rank) {
            copy_task(index, &slots[index], output);
            return true;
        }
        ++visible_rank;
    }
    return false;
}

bool codex_oai_task_for_slot(uint8_t slot, codex_oai_task_t *output) {
    if (slot >= OAI_SLOT_COUNT || output == NULL) {
        return false;
    }
    copy_task(slot, &slots[slot], output);
    return true;
}

bool codex_oai_task_state(codex_oai_task_t *output) {
    int8_t selected = -1;
    for (uint8_t index = 0; index < OAI_SLOT_COUNT; ++index) {
        const oai_slot_t *slot = &slots[index];
        if (!slot_is_visible(slot)) {
            continue;
        }
        if (selected < 0 || (slot->effect == 4 && slots[(uint8_t)selected].effect != 4)) {
            selected = (int8_t)index;
        }
    }
    if (selected < 0) {
        return false;
    }
    if (output == NULL) {
        return true;
    }
    copy_task((uint8_t)selected, &slots[(uint8_t)selected], output);
    return true;
}

static size_t skip_space(const char *input, size_t length, size_t offset) {
    while (offset < length && is_space(input[offset])) {
        ++offset;
    }
    return offset;
}

static bool parse_plain_string(
    const char *input,
    size_t length,
    size_t *offset,
    char *output,
    size_t output_size
) {
    size_t cursor = *offset;
    size_t written = 0;
    if (cursor >= length || input[cursor] != '"' || output_size == 0) {
        return false;
    }
    ++cursor;
    while (cursor < length && input[cursor] != '"') {
        unsigned char value = (unsigned char)input[cursor];
        if (value == '\\') {
            if (++cursor >= length) return false;
            value = (unsigned char)input[cursor++];
            if (value == 'u') {
                uint16_t codepoint = 0;
                for (uint8_t digit = 0; digit < 4; ++digit) {
                    if (cursor >= length) return false;
                    int8_t hex = hex_digit_value((unsigned char)input[cursor]);
                    if (hex < 0) return false;
                    codepoint = (uint16_t)((codepoint << 4) | (uint8_t)hex);
                    ++cursor;
                }
                if (codepoint > 0x7FU) return false;
                value = (unsigned char)codepoint;
            } else if (!(value == '"' || value == '\\' || value == '/' || value == 'b' || value == 'f' || value == 'n' || value == 'r' || value == 't')) {
                return false;
            } else {
                switch (value) {
                    case 'b': value = '\b'; break;
                    case 'f': value = '\f'; break;
                    case 'n': value = '\n'; break;
                    case 'r': value = '\r'; break;
                    case 't': value = '\t'; break;
                    default: break;
                }
            }
            if (value < 0x20 || value > 0x7E) return false;
        } else {
            if (value < 0x20 || value > 0x7E) return false;
            ++cursor;
        }
        if (written + 1 >= output_size) {
            return false;
        }
        output[written++] = (char)value;
    }
    if (cursor >= length || input[cursor] != '"') {
        return false;
    }
    output[written] = '\0';
    *offset = cursor + 1;
    return true;
}

static bool skip_string(const char *input, size_t length, size_t *offset) {
    size_t cursor = *offset;
    bool escape_next = false;
    uint8_t unicode_digits = 0;
    if (cursor >= length || input[cursor] != '"') {
        return false;
    }
    ++cursor;
    while (cursor < length) {
        unsigned char value = (unsigned char)input[cursor++];
        if (unicode_digits != 0) {
            if (!((value >= '0' && value <= '9') || (value >= 'a' && value <= 'f') || (value >= 'A' && value <= 'F'))) {
                return false;
            }
            --unicode_digits;
        } else if (escape_next) {
            if (value == 'u') {
                unicode_digits = 4;
            } else if (!(value == '"' || value == '\\' || value == '/' || value == 'b' || value == 'f' || value == 'n' || value == 'r' || value == 't')) {
                return false;
            }
            escape_next = false;
        } else if (value == '\\') {
            escape_next = true;
        } else if (value == '"') {
            *offset = cursor;
            return true;
        } else if (value < 0x20) {
            return false;
        }
    }
    return false;
}

static bool matching_container(char open, char close) {
    return (open == '{' && close == '}') || (open == '[' && close == ']');
}

static bool is_json_number_char(char value) {
    return (
        (value >= '0' && value <= '9')
        || value == '-'
        || value == '+'
        || value == '.'
        || value == 'e'
        || value == 'E'
    );
}

static bool skip_primitive(const char *input, size_t length, size_t *offset) {
    size_t cursor = skip_space(input, length, *offset);
    size_t start = cursor;
    while (
        cursor < length
        && input[cursor] != ','
        && input[cursor] != '}'
        && input[cursor] != ']'
    ) {
        ++cursor;
    }
    size_t end = cursor;
    while (end > start && is_space(input[end - 1])) {
        --end;
    }
    if (end == start) {
        return false;
    }
    size_t token_length = end - start;
    if (
        (token_length == 4 && memcmp(&input[start], "true", 4) == 0)
        || (token_length == 5 && memcmp(&input[start], "false", 5) == 0)
        || (token_length == 4 && memcmp(&input[start], "null", 4) == 0)
    ) {
        *offset = end;
        return true;
    }
    if (!is_json_number_char(input[start])) return false;
    cursor = start;
    if (input[cursor] == '-') ++cursor;
    if (cursor >= end) return false;
    if (input[cursor] == '0') {
        ++cursor;
        if (cursor < end && input[cursor] >= '0' && input[cursor] <= '9') return false;
    } else {
        if (input[cursor] < '1' || input[cursor] > '9') return false;
        while (cursor < end && input[cursor] >= '0' && input[cursor] <= '9') ++cursor;
    }
    if (cursor < end && input[cursor] == '.') {
        ++cursor;
        size_t fraction_start = cursor;
        while (cursor < end && input[cursor] >= '0' && input[cursor] <= '9') ++cursor;
        if (cursor == fraction_start) return false;
    }
    if (cursor < end && (input[cursor] == 'e' || input[cursor] == 'E')) {
        ++cursor;
        if (cursor < end && (input[cursor] == '+' || input[cursor] == '-')) ++cursor;
        size_t exponent_start = cursor;
        while (cursor < end && input[cursor] >= '0' && input[cursor] <= '9') ++cursor;
        if (cursor == exponent_start) return false;
    }
    if (cursor != end) return false;
    *offset = end;
    return true;
}

static bool skip_json_value(const char *input, size_t length, size_t *offset, uint8_t depth) {
    size_t cursor = skip_space(input, length, *offset);
    if (cursor >= length) return false;
    if (input[cursor] == '"') {
        if (!skip_string(input, length, &cursor)) return false;
    } else if (input[cursor] == '{' || input[cursor] == '[') {
        if (depth >= OAI_MAX_JSON_DEPTH) return false;
        char opening = input[cursor++];
        char closing = opening == '{' ? '}' : ']';
        bool object = opening == '{';
        cursor = skip_space(input, length, cursor);
        if (cursor < length && input[cursor] == closing) {
            *offset = cursor + 1;
            return true;
        }
        for (;;) {
            if (object) {
                if (!skip_string(input, length, &cursor)) return false;
                cursor = skip_space(input, length, cursor);
                if (cursor >= length || input[cursor++] != ':') return false;
            }
            if (!skip_json_value(input, length, &cursor, (uint8_t)(depth + 1))) return false;
            cursor = skip_space(input, length, cursor);
            if (cursor < length && input[cursor] == ',') {
                ++cursor;
                cursor = skip_space(input, length, cursor);
                if (cursor >= length || input[cursor] == closing) return false;
                continue;
            }
            if (cursor < length && input[cursor] == closing) {
                *offset = cursor + 1;
                return true;
            }
            return false;
        }
    } else {
        if (!skip_primitive(input, length, &cursor)) return false;
    }
    *offset = cursor;
    return true;
}

static bool skip_value(const char *input, size_t length, size_t *offset) {
    return skip_json_value(input, length, offset, 0);
}

static bool parse_id(
    const char *input,
    size_t length,
    size_t *offset,
    uint16_t *id
) {
    size_t cursor = skip_space(input, length, *offset);
    size_t start = cursor;
    uint16_t value = 0;
    size_t digits = 0;
    while (cursor < length && input[cursor] >= '0' && input[cursor] <= '9') {
        value = (uint16_t)(value * 10U + (uint16_t)(input[cursor] - '0'));
        ++cursor;
        ++digits;
        if (digits > 3 || value > 998) {
            return false;
        }
    }
    if (digits == 0 || (digits > 1 && input[start] == '0')) {
        return false;
    }
    *id = value;
    *offset = cursor;
    return true;
}

static bool parse_u32(const char *input, size_t length, size_t *offset, uint32_t *value, uint32_t maximum) {
    size_t cursor = skip_space(input, length, *offset);
    size_t start = cursor;
    uint32_t result = 0;
    size_t digits = 0;
    while (cursor < length && input[cursor] >= '0' && input[cursor] <= '9') {
        uint32_t digit = (uint32_t)(input[cursor] - '0');
        if (result > maximum / 10U || (result == maximum / 10U && digit > maximum % 10U)) {
            return false;
        }
        result = result * 10U + digit;
        ++cursor;
        ++digits;
    }
    if (digits == 0 || (digits > 1 && input[start] == '0')) {
        return false;
    }
    *value = result;
    *offset = cursor;
    return true;
}

static uint32_t scale_fraction_byte(uint32_t fraction, uint32_t denominator) {
    uint32_t quotient = 0;
    uint32_t remainder = 0;
    for (int8_t bit = 7; bit >= 0; --bit) {
        remainder *= 2U;
        quotient *= 2U;
        if ((255U & (1U << bit)) != 0U) {
            remainder += fraction;
        }
        if (remainder >= denominator) {
            remainder -= denominator;
            ++quotient;
        }
    }
    if (remainder * 2U >= denominator) {
        ++quotient;
    }
    return quotient;
}

static bool parse_fraction_byte(const char *input, size_t length, size_t *offset, uint8_t *output) {
    size_t cursor = skip_space(input, length, *offset);
    size_t end = cursor;
    if (!skip_primitive(input, length, &end) || end <= cursor || input[cursor] == '-') {
        return false;
    }
    uint32_t whole = 0;
    while (cursor < end && input[cursor] >= '0' && input[cursor] <= '9') {
        whole = whole * 10U + (uint32_t)(input[cursor] - '0');
        if (whole > 1U) return false;
        ++cursor;
    }
    if (cursor == end) {
        *output = (uint8_t)(whole * 255U);
        *offset = end;
        return true;
    }
    if (input[cursor++] != '.') return false;
    size_t fraction_start = cursor;
    uint32_t fraction = 0;
    uint32_t denominator = 1;
    uint16_t digits = 0;
    uint8_t first_ignored = 0;
    bool ignored_nonzero = false;
    while (cursor < end && input[cursor] >= '0' && input[cursor] <= '9') {
        uint8_t digit = (uint8_t)(input[cursor] - '0');
        if (digits < 9) {
            fraction = fraction * 10U + digit;
            denominator *= 10U;
        } else if (digits == 9) {
            first_ignored = digit;
            ignored_nonzero = digit != 0;
        } else if (digit != 0) {
            ignored_nonzero = true;
        }
        ++digits;
        ++cursor;
    }
    if (cursor != end || cursor == fraction_start || (whole == 1U && (fraction != 0U || ignored_nonzero))) {
        return false;
    }
    if (digits > 9 && first_ignored >= 5U) ++fraction;
    uint32_t scaled_fraction = scale_fraction_byte(fraction, denominator);
    uint32_t scaled = whole * 255U + scaled_fraction;
    *output = (uint8_t)(scaled > 255U ? 255U : scaled);
    *offset = end;
    return true;
}

static bool parse_slot_update(const char *input, size_t length, size_t *offset, oai_slot_update_t *update) {
    size_t cursor = skip_space(input, length, *offset);
    if (cursor >= length || input[cursor++] != '{') {
        return false;
    }
    memset(update, 0, sizeof(*update));
    bool has_id = false;
    for (;;) {
        char key[4];
        cursor = skip_space(input, length, cursor);
        if (cursor < length && input[cursor] == '}') {
            ++cursor;
            break;
        }
        if (!parse_plain_string(input, length, &cursor, key, sizeof(key))) {
            return false;
        }
        cursor = skip_space(input, length, cursor);
        if (cursor >= length || input[cursor++] != ':') {
            return false;
        }
        uint8_t field;
        if (strcmp(key, "id") == 0) {
            field = 0;
            uint32_t id;
            if (has_id || !parse_u32(input, length, &cursor, &id, 5)) {
                return false;
            }
            update->id = (uint8_t)id;
            has_id = true;
        } else if (strcmp(key, "c") == 0) {
            field = SLOT_RED | SLOT_GREEN | SLOT_BLUE;
            uint32_t color;
            if ((update->fields & field) != 0 || !parse_u32(input, length, &cursor, &color, 0xFFFFFFU)) {
                return false;
            }
            update->value.red = (uint8_t)(color >> 16);
            update->value.green = (uint8_t)(color >> 8);
            update->value.blue = (uint8_t)color;
        } else if (strcmp(key, "e") == 0) {
            field = SLOT_EFFECT;
            uint32_t effect;
            if ((update->fields & field) != 0 || !parse_u32(input, length, &cursor, &effect, 6)) {
                return false;
            }
            update->value.effect = (uint8_t)effect;
        } else if (strcmp(key, "b") == 0) {
            field = SLOT_BRIGHTNESS;
            if ((update->fields & field) != 0 || !parse_fraction_byte(input, length, &cursor, &update->value.brightness)) {
                return false;
            }
        } else if (strcmp(key, "s") == 0) {
            field = SLOT_SPEED;
            if ((update->fields & field) != 0 || !parse_fraction_byte(input, length, &cursor, &update->value.speed)) {
                return false;
            }
        } else if (strcmp(key, "sk") == 0 || strcmp(key, "sa") == 0) {
            field = strcmp(key, "sk") == 0 ? SLOT_SYNC_KEY : SLOT_SYNC_ALL;
            uint32_t flag;
            if ((update->fields & field) != 0 || !parse_u32(input, length, &cursor, &flag, 1)) {
                return false;
            }
            if (strcmp(key, "sk") == 0) {
                update->value.flags = (uint8_t)((update->value.flags & 0x02U) | (uint8_t)flag);
            } else {
                update->value.flags = (uint8_t)((update->value.flags & 0x01U) | ((uint8_t)flag << 1));
            }
        } else {
            return false;
        }
        if (field != 0) {
            update->fields |= field;
        }
        cursor = skip_space(input, length, cursor);
        if (cursor < length && input[cursor] == ',') {
            ++cursor;
            continue;
        }
        if (cursor < length && input[cursor] == '}') {
            ++cursor;
            break;
        }
        return false;
    }
    *offset = cursor;
    return has_id;
}

static bool parse_thstatus_params(const char *input, size_t start, size_t end) {
    size_t cursor = skip_space(input, end, start);
    if (cursor >= end || input[cursor++] != '[') {
        return false;
    }
    oai_slot_update_t updates[OAI_SLOT_COUNT];
    uint8_t count = 0;
    bool seen[OAI_SLOT_COUNT] = {false};
    cursor = skip_space(input, end, cursor);
    bool closed = false;
    if (cursor < end && input[cursor] == ']') {
        ++cursor;
        closed = true;
    }
    while (!closed && cursor < end && count < OAI_SLOT_COUNT) {
        if (!parse_slot_update(input, end, &cursor, &updates[count])) {
            return false;
        }
        if (seen[updates[count].id]) {
            return false;
        }
        seen[updates[count].id] = true;
        ++count;
        cursor = skip_space(input, end, cursor);
        if (cursor < end && input[cursor] == ',') {
            ++cursor;
            continue;
        }
        if (cursor < end && input[cursor] == ']') {
            ++cursor;
            closed = true;
            break;
        }
        return false;
    }
    if (!closed || count > OAI_SLOT_COUNT || cursor != skip_space(input, end, cursor) || cursor != end) {
        return false;
    }
    oai_slot_t next[OAI_SLOT_COUNT];
    memcpy(next, slots, sizeof(next));
    for (uint8_t index = 0; index < count; ++index) {
        oai_slot_update_t *update = &updates[index];
        oai_slot_t *slot = &next[update->id];
        if ((update->fields & SLOT_RED) != 0) {
            slot->red = update->value.red;
            slot->green = update->value.green;
            slot->blue = update->value.blue;
        }
        if ((update->fields & SLOT_EFFECT) != 0) slot->effect = update->value.effect;
        if ((update->fields & SLOT_BRIGHTNESS) != 0) slot->brightness = update->value.brightness;
        if ((update->fields & SLOT_SPEED) != 0) slot->speed = update->value.speed;
        if ((update->fields & SLOT_SYNC_KEY) != 0) {
            slot->flags = (uint8_t)((slot->flags & 0x02U) | (update->value.flags & 0x01U));
        }
        if ((update->fields & SLOT_SYNC_ALL) != 0) {
            slot->flags = (uint8_t)((slot->flags & 0x01U) | (update->value.flags & 0x02U));
        }
    }
    if (memcmp(slots, next, sizeof(slots)) != 0) {
        memcpy(slots, next, sizeof(slots));
        ++state_revision;
        if (state_revision == 0) state_revision = 1;
    }
    return true;
}

static bool parse_keymap_params(
    const char *input,
    size_t start,
    size_t end,
    bool require_map,
    uint32_t *layer,
    char map[OAI_KEYMAP_POSITION_COUNT + 1]
) {
    size_t cursor = skip_space(input, end, start);
    if (cursor >= end || input[cursor++] != '{') {
        return false;
    }
    bool has_layer = false;
    bool has_map = false;
    for (;;) {
        char key[2];
        cursor = skip_space(input, end, cursor);
        if (cursor < end && input[cursor] == '}' && (has_layer || has_map)) {
            ++cursor;
            break;
        }
        if (!parse_plain_string(input, end, &cursor, key, sizeof(key))) {
            return false;
        }
        cursor = skip_space(input, end, cursor);
        if (cursor >= end || input[cursor++] != ':') {
            return false;
        }
        if (strcmp(key, "l") == 0) {
            if (has_layer || !parse_u32(input, end, &cursor, layer, 0U)) {
                return false;
            }
            has_layer = true;
        } else if (strcmp(key, "m") == 0) {
            if (has_map || map == NULL || !parse_plain_string(input, end, &cursor, map, OAI_KEYMAP_POSITION_COUNT + 1)) {
                return false;
            }
            if (strlen(map) != OAI_KEYMAP_POSITION_COUNT) {
                return false;
            }
            has_map = true;
        } else {
            return false;
        }
        cursor = skip_space(input, end, cursor);
        if (cursor < end && input[cursor] == ',') {
            ++cursor;
            continue;
        }
        if (cursor < end && input[cursor] == '}') {
            ++cursor;
            break;
        }
        return false;
    }
    cursor = skip_space(input, end, cursor);
    return cursor == end && has_layer && has_map == require_map;
}

static bool parse_request(
    const char *input,
    size_t length,
    oai_request_t *request
) {
    memset(request, 0, sizeof(*request));
    size_t offset = skip_space(input, length, 0);
    if (offset >= length || input[offset++] != '{') {
        return false;
    }

    bool need_member = true;
    for (;;) {
        char key[12];
        offset = skip_space(input, length, offset);
        if (offset < length && input[offset] == '}' && !need_member) {
            ++offset;
            break;
        }
        if (!parse_plain_string(input, length, &offset, key, sizeof(key))) {
            return false;
        }
        offset = skip_space(input, length, offset);
        if (offset >= length || input[offset++] != ':') {
            return false;
        }
        offset = skip_space(input, length, offset);

        if (strcmp(key, "method") == 0) {
            if (
                request->has_method
                || !parse_plain_string(
                    input,
                    length,
                    &offset,
                    request->method,
                    sizeof(request->method)
                )
            ) {
                return false;
            }
            request->has_method = true;
        } else if (strcmp(key, "id") == 0) {
            if (
                request->has_id
                || !parse_id(input, length, &offset, &request->id)
            ) {
                return false;
            }
            request->has_id = true;
        } else if (strcmp(key, "params") == 0) {
            if (request->has_params) {
                return false;
            }
            request->has_params = true;
            request->params_start = offset;
            if (!skip_value(input, length, &offset)) {
                return false;
            }
            request->params_end = offset;
        } else {
            return false;
        }

        need_member = false;
        offset = skip_space(input, length, offset);
        if (offset < length && input[offset] == ',') {
            ++offset;
            need_member = true;
            continue;
        }
        if (offset < length && input[offset] == '}') {
            ++offset;
            break;
        }
        return false;
    }

    offset = skip_space(input, length, offset);
    return (
        offset == length
        && request->has_method
        && request->has_id
        && request->has_params
    );
}

static uint8_t append_text(
    uint8_t report[OAI_REPORT_SIZE],
    uint8_t offset,
    const char *text
) {
    while (*text != '\0' && offset < OAI_REPORT_SIZE) {
        report[offset++] = (uint8_t)*text++;
    }
    return offset;
}

static uint8_t append_id(
    uint8_t report[OAI_REPORT_SIZE],
    uint8_t offset,
    uint16_t id
) {
    if (id >= 100) {
        report[offset++] = (uint8_t)('0' + id / 100);
        id %= 100;
        report[offset++] = (uint8_t)('0' + id / 10);
    } else if (id >= 10) {
        report[offset++] = (uint8_t)('0' + id / 10);
    }
    report[offset++] = (uint8_t)('0' + id % 10);
    return offset;
}

static void send_response(const char *prefix, uint16_t id) {
    uint8_t report[OAI_REPORT_SIZE] = {0};
    uint8_t offset = 3;
    report[0] = OAI_REPORT_ID;
    report[1] = OAI_CHANNEL_RPC;
    offset = append_text(report, offset, prefix);
    offset = append_id(report, offset, id);
    offset = append_text(report, offset, "}\r\n");
    report[2] = (uint8_t)(offset - 3);
    raw_hid_send(report, OAI_REPORT_SIZE);
}

static void send_keymap_get_response(uint16_t id, const char map[OAI_KEYMAP_POSITION_COUNT + 1]) {
    uint8_t report[OAI_REPORT_SIZE] = {0};
    uint8_t offset = 3;
    report[0] = OAI_REPORT_ID;
    report[1] = OAI_CHANNEL_RPC;
    offset = append_text(report, offset, "{\"result\":{\"l\":0,\"m\":\"");
    offset = append_text(report, offset, map);
    offset = append_text(report, offset, "\"},\"id\":");
    offset = append_id(report, offset, id);
    offset = append_text(report, offset, "}\r\n");
    report[2] = (uint8_t)(offset - 3);
    raw_hid_send(report, OAI_REPORT_SIZE);
}

static bool dispatch_request(const char *input, size_t length) {
    oai_request_t request;
    if (!parse_request(input, length, &request)) {
        return false;
    }
    if (strcmp(request.method, "v.oai.rgbcfg") == 0) {
        saw_rgbcfg = true;
        ++handshake_revision;
        if (handshake_revision == 0U) handshake_revision = 1U;
        send_response("{\"result\":true,\"id\":", request.id);
    } else if (strcmp(request.method, "v.oai.thstatus") == 0) {
        bool valid_status = parse_thstatus_params(input, request.params_start, request.params_end);
        if (valid_status) {
            saw_thstatus = true;
            send_response("{\"result\":true,\"id\":", request.id);
        } else {
            return false;
        }
    } else if (strcmp(request.method, "device.status") == 0) {
        send_response("{\"result\":{},\"id\":", request.id);
    } else if (strcmp(request.method, "v.oai.keymap.get") == 0) {
        uint32_t layer = 0;
        char map[OAI_KEYMAP_POSITION_COUNT + 1];
        if (!parse_keymap_params(input, request.params_start, request.params_end, false, &layer, map)) {
            send_response("{\"error\":\"invalid_keymap\",\"id\":", request.id);
            return false;
        }
        (void)layer;
        (void)codex_oai_keymap_get_hex(map);
        send_keymap_get_response(request.id, map);
    } else if (strcmp(request.method, "v.oai.keymap.set") == 0) {
        uint32_t layer = 0;
        char map[OAI_KEYMAP_POSITION_COUNT + 1];
        if (
            !parse_keymap_params(input, request.params_start, request.params_end, true, &layer, map)
            || layer != 0U
            || !codex_oai_keymap_set_hex(map, OAI_KEYMAP_POSITION_COUNT)
        ) {
            send_response("{\"error\":\"invalid_keymap\",\"id\":", request.id);
            return false;
        }
        send_response("{\"result\":true,\"id\":", request.id);
    }
    return true;
}

static void finish_object(void) {
    if (!invalid_object && !overflowed && rx_length <= OAI_RX_CAPACITY) {
        rx_buffer[rx_length] = '\0';
        if (dispatch_request(rx_buffer, rx_length)) {
            note_valid_request();
        } else {
            note_error();
        }
    } else {
        note_error();
    }
    reset_rx();
}

static void feed_rpc_byte(char value) {
    if (!collecting) {
        if (value != '{') {
            return;
        }
        collecting = true;
        container_depth = 1;
        container_stack[0] = '{';
        rx_buffer[0] = '{';
        rx_length = 1;
        return;
    }

    if (rx_length < OAI_RX_CAPACITY) {
        rx_buffer[rx_length++] = value;
    } else {
        overflowed = true;
    }

    if (in_string) {
        if (escaped) {
            escaped = false;
        } else if (value == '\\') {
            escaped = true;
        } else if (value == '"') {
            in_string = false;
        } else if ((unsigned char)value < 0x20) {
            invalid_object = true;
        }
        return;
    }

    if (value == '"') {
        in_string = true;
        return;
    }
    if (value == '{' || value == '[') {
        if (container_depth >= OAI_MAX_JSON_DEPTH) {
            invalid_object = true;
        } else {
            container_stack[container_depth++] = value;
        }
        return;
    }
    if (value == '}' || value == ']') {
        if (
            container_depth == 0
            || !matching_container(
                container_stack[container_depth - 1],
                value
            )
        ) {
            invalid_object = true;
            reset_rx();
            note_error();
            return;
        }
        --container_depth;
        if (container_depth == 0) {
            finish_object();
        }
    }
}

void raw_hid_receive(uint8_t *data, uint8_t length) {
    if (
        data == NULL
        || length != OAI_REPORT_SIZE
        || data[0] != OAI_REPORT_ID
        || data[2] > OAI_MAX_PAYLOAD
    ) {
        note_error();
        return;
    }
    for (uint8_t index = (uint8_t)(3 + data[2]); index < OAI_REPORT_SIZE; ++index) {
        if (data[index] != 0) {
            note_error();
            return;
        }
    }
    if (data[1] == OAI_CHANNEL_DEBUG) {
        return;
    }
    if (data[1] != OAI_CHANNEL_RPC) {
        note_error();
        return;
    }
    for (uint8_t index = 0; index < data[2]; ++index) {
        feed_rpc_byte((char)data[3 + index]);
    }
}

static const char *control_name(codex_oai_control_t control) {
    switch (control) {
        case OAI_CONTROL_AG00:
            return "AG00";
        case OAI_CONTROL_AG01:
            return "AG01";
        case OAI_CONTROL_AG02:
            return "AG02";
        case OAI_CONTROL_AG03:
            return "AG03";
        case OAI_CONTROL_AG04:
            return "AG04";
        case OAI_CONTROL_AG05:
            return "AG05";
        case OAI_CONTROL_ACT06:
            return "ACT06";
        case OAI_CONTROL_ACT07:
            return "ACT07";
        case OAI_CONTROL_ACT08:
            return "ACT08";
        case OAI_CONTROL_ACT09:
            return "ACT09";
        case OAI_CONTROL_ACT10:
            return "ACT10";
        case OAI_CONTROL_ACT11:
            return "ACT11";
        case OAI_CONTROL_ACT12:
            return "ACT12";
        case OAI_CONTROL_ENCODER:
            return "ENC";
        case OAI_CONTROL_ENCODER_CW:
            return "ENC_CW";
        case OAI_CONTROL_ENCODER_CCW:
            return "ENC_CC";
        case OAI_CONTROL_COUNT:
            return NULL;
    }
    return NULL;
}

bool codex_oai_notify(codex_oai_control_t control, bool pressed) {
    if (!codex_oai_ready()) {
        return false;
    }

    const char *name = control_name(control);
    if (name == NULL) {
        return false;
    }
    if (control <= OAI_CONTROL_AG05 && !pressed) {
        return false;
    }

    uint8_t action = pressed ? 1 : 0;
    if (
        control == OAI_CONTROL_ENCODER_CW
        || control == OAI_CONTROL_ENCODER_CCW
    ) {
        action = 2;
    }

    uint8_t report[OAI_REPORT_SIZE] = {0};
    uint8_t offset = 3;
    report[0] = OAI_REPORT_ID;
    report[1] = OAI_CHANNEL_RPC;
    offset = append_text(
        report,
        offset,
        "{\"method\":\"v.oai.hid\",\"params\":{\"k\":\""
    );
    offset = append_text(report, offset, name);
    offset = append_text(report, offset, "\",\"act\":");
    report[offset++] = (uint8_t)('0' + action);
    offset = append_text(report, offset, "}}\r\n");
    report[2] = (uint8_t)(offset - 3);
    raw_hid_send(report, OAI_REPORT_SIZE);
    return true;
}

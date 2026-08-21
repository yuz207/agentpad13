#pragma once

#include <stddef.h>
#include <stdint.h>

typedef enum wear_leveling_status_t {
    WEAR_LEVELING_FAILED,
    WEAR_LEVELING_SUCCESS,
    WEAR_LEVELING_CONSOLIDATED,
} wear_leveling_status_t;

wear_leveling_status_t wear_leveling_init(void);
wear_leveling_status_t wear_leveling_erase(void);
wear_leveling_status_t wear_leveling_write(uint32_t address, const void *value, size_t length);
wear_leveling_status_t wear_leveling_read(uint32_t address, void *value, size_t length);

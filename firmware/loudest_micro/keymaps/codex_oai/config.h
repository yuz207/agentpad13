// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

/* Direct Codex Desktop OAI endpoint.  This target intentionally does not
 * expose the AgentPad13 Vial status protocol. */
#undef VENDOR_ID
#undef PRODUCT_ID
#undef DEVICE_VER
#undef MANUFACTURER
#undef PRODUCT
#undef RAW_USAGE_PAGE
#undef RAW_USAGE_ID
#undef RAW_EPSIZE
#undef RAW_REPORT_ID

#define VENDOR_ID 0x303A
#define PRODUCT_ID 0x8360
#define DEVICE_VER 0x0005
#define MANUFACTURER "hirlu"
#define PRODUCT "Codex Micro Lab OAI LED"

#define RAW_USAGE_PAGE 0xFF00
#define RAW_USAGE_ID 0x61
#define RAW_EPSIZE 64
#define RAW_REPORT_ID 6

/* K00 / physical [0,0] enters the normal QMK bootmagic-lite path. */
#define BOOTMAGIC_LITE_ROW 0
#define BOOTMAGIC_LITE_COLUMN 0

#define LOUDEST_CUSTOM_RAW_HID
#define LOUDEST_CUSTOM_RGB_STATUS

// SPDX-License-Identifier: GPL-2.0-or-later
// agentpad13 - "calibrate" keymap: the first-power-on BRING-UP TOOL.
//
// NOT THE DAILY FIRMWARE. Flash it once, read the numbers it types, flash the
// real firmware back. See keymaps/calibrate/readme.md and firmware/BUILD.md
// ("Bring-up: first-power-on calibration").
//
// WHY THIS EXISTS. Four bring-up items were written down with no mechanism to
// perform them:
//   * keyboard.json ships PLACEHOLDER joystick calibration (low 0 / rest 512 /
//     high 1023) and loudest_micro.c ships JS_THRESHOLD 300, neither metered on
//     a real YA13 (v5/V5-NOTES.md finding 3). If the assembled stick does not
//     reach <212 or >812 on the 0..1023 ADC, JS_MODE_ARROWS and JS_MODE_SCROLL
//     are SILENTLY DEAD while the gamepad mode still "works".
//   * JS1 sits 180 deg from its datasheet datum, so either axis may read
//     reversed (firmware/POLARITY-NOTE.md).
//   * The TTP223 touch fix of 2026-08-13 has never been seen on real silicon.
//   * Encoder direction depends on how A/B landed.
// Protocol v0 is LOCKED and carries no ADC readout, and Vial exposes no raw
// analog, so there was no way to GET the numbers off the board. But the board is
// a keyboard: it can TYPE its own calibration report into any text editor. That
// is all this keymap does.
//
// HOW IT IS WIRED (nothing here touches a shared firmware file):
//   * SW1/SW2/SW3 and the encoder push arrive as ordinary matrix key events;
//     the TTP223 touch arrives at [3,2] because loudest_micro.c's
//     matrix_scan_kb() injects action_exec(MAKE_KEYEVENT(3, 2, pressed)).
//     All of them are matched HERE by row/col in process_record_user(), so
//     every keycode in keymaps[] is KC_NO and this keymap can never type a
//     stray character on its own.
//   * The encoder is read through encoder_update_user(). That callback only
//     runs when ENCODER_MAP_ENABLE is OFF (quantum/encoder.c:35-52 routes to
//     action_exec() instead when the map is enabled), which is why this
//     keymap's rules.mk deliberately does NOT inherit the default keymap's
//     ENCODER_MAP_ENABLE = yes.
//   * Every ADC read and every send_string() happens in housekeeping_task_user()
//     draining a small event queue - never inside the action_exec() that
//     delivered the event, and never inside matrix_scan_kb(). The queue is what
//     decouples "an event arrived" from "type a report", so the typing never
//     runs nested inside key-event dispatch; that is the reason it exists and it
//     is unchanged.
//     housekeeping_task_user() now runs EXACTLY ONCE per loop, from
//     quantum/keyboard.c:436. (CORRECTED 2026-08-15: it used to run TWICE,
//     because loudest_micro.c's housekeeping_task_kb() called it a second time
//     on top of quantum's own call - ledgered 2026-08-13 as a latent trap, and
//     this keymap was the first code to actually implement the hook. It was
//     harmless here only because draining a queue is idempotent. The duplicate
//     call was removed on 2026-08-15; see loudest_micro.c housekeeping_task_kb().)
//
// ALL NUMBERS ARE IN THE FIRMWARE'S 10-BIT DOMAIN (0..1023). That is what
// analogReadPin() returns on RP2040 (platforms/chibios/drivers/analog.c:444-445,
// sample >> (12 - ADC_RESOLUTION), ADC_RESOLUTION 10), and it is the same domain
// as keyboard.json low/rest/high, JS_CENTER and JS_THRESHOLD.
#include QMK_KEYBOARD_H
#include "analog.h"

// ---------------------------------------------------------------------------
// Board bindings. GP26 = JOY_X_ADC (ADC0), GP27 = JOY_Y_ADC (ADC1), re-verified
// 20/20 GPIO against the shipped v5/hardware/pcb/v5_6.kicad_pcb on 2026-08-13
// and asserted statically by firmware/check_pins_v4.py.
// ---------------------------------------------------------------------------
#define CAL_PIN_X GP26
#define CAL_PIN_Y GP27
#define CAL_ADC_MAX 1023

// The constants the SHIPPED firmware actually uses, mirrored from
// loudest_micro.c (JS_CENTER / JS_THRESHOLD). They are #defines local to that
// translation unit, so they cannot be included from here - if they are ever
// changed there, change them here too or the "shipped verdict" below lies.
#define CAL_SHIPPED_CENTER 512
#define CAL_SHIPPED_THRESHOLD 300

// The arrow/scroll comparisons in loudest_micro.c's housekeeping_task_kb() are
// STRICT: want[] = (v < JS_CENTER - JS_THRESHOLD) and (v > JS_CENTER +
// JS_THRESHOLD). So a direction fires only at 211 or below / 813 or above -
// reaching exactly 212 or exactly 812 fires NOTHING. The verdict below uses the
// strict form, i.e. what the code does, not the rounded prose ("<=212 / >=812")
// used in the handoff.
#define CAL_FIRES_LOW(v) ((v) < (CAL_SHIPPED_CENTER - CAL_SHIPPED_THRESHOLD))
#define CAL_FIRES_HIGH(v) ((v) > (CAL_SHIPPED_CENTER + CAL_SHIPPED_THRESHOLD))

// Logical matrix positions (keyboard.json matrix_pins.direct).
#define CAL_SW1_ROW 0
#define CAL_SW1_COL 0 // GP12 - step / capture
#define CAL_SW2_ROW 0
#define CAL_SW2_COL 1 // GP9  - restart
#define CAL_SW3_ROW 0
#define CAL_SW3_COL 2 // GP5  - live reading
#define CAL_ENC_ROW 3
#define CAL_ENC_COL 1 // GP15 - encoder push
#define CAL_TOUCH_ROW 3
#define CAL_TOUCH_COL 2 // GP16 via matrix_scan_kb() injection

// Capture shape. The rest window is CAL_NOISE_SAMPLES readings CAL_NOISE_STEP_MS
// apart (= 500 ms) per axis; the rest AVERAGE is the mean of the first
// CAL_AVG_SAMPLES of that window, so the average is always inside the min..max
// band it is reported with.
#define CAL_AVG_SAMPLES 16
#define CAL_NOISE_SAMPLES 100
#define CAL_NOISE_STEP_MS 5

// Derivation constants (see readme.md for the reasoning behind each).
#define CAL_THRESHOLD_PERCENT 60 // fire with 40% of the half-swing still in reserve
#define CAL_MIN_HALF_SWING 100   // below this the stick/ADC is suspect
#define CAL_NOISE_MARGIN 3       // threshold must clear 3x the rest noise half-band
#define CAL_REST_SKEW_LIMIT 30   // X/Y rest spread that makes ONE JS_CENTER a lie

// Inter-character typing delay. send_char_with_delay() waits this long around
// every keypress (and again around the shift for capitals and symbols), so it is
// cheap insurance against a text editor dropping characters. 0 also works on
// most hosts; do not raise it much or the full report takes minutes.
#define CAL_TYPE_DELAY 2

// ---------------------------------------------------------------------------
// Keymap: every position is KC_NO on purpose. Nothing here can emit a keystroke
// by itself; the only characters this firmware ever sends come from
// send_string() below. process_record_kb() in loudest_micro.c still passes every
// event through to process_record_user(), including [3,2] (quantum/quantum.c:364
// calls process_record_kb() for every keycode, KC_NO included).
// ---------------------------------------------------------------------------
// clang-format off
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO,        KC_NO,        KC_NO
    ),
};
// clang-format on

// ---------------------------------------------------------------------------
// Event queue. Everything below runs in the single QMK keyboard-task thread
// (matrix scan, encoder task and housekeeping are all called from
// keyboard_task()), so no locking is needed - the queue exists to move the slow
// work (ADC windows, typing) OUT of the callbacks that deliver the events.
// ---------------------------------------------------------------------------
enum cal_event {
    CAL_EV_NONE = 0,
    CAL_EV_STEP,       // SW1
    CAL_EV_RESTART,    // SW2
    CAL_EV_LIVE,       // SW3
    CAL_EV_TOUCH_DOWN, // [3,2] make
    CAL_EV_TOUCH_UP,   // [3,2] break
    CAL_EV_ENC_CW,
    CAL_EV_ENC_CCW,
    CAL_EV_ENC_PRESS,
};

#define CAL_QUEUE_LEN 16
static uint8_t cal_queue[CAL_QUEUE_LEN];
static uint8_t cal_q_head = 0;
static uint8_t cal_q_tail = 0;
static bool    cal_q_overflow = false;

static void cal_post(uint8_t ev) {
    uint8_t next = (uint8_t)((cal_q_head + 1u) % CAL_QUEUE_LEN);
    if (next == cal_q_tail) {
        cal_q_overflow = true; // reported, never swallowed
        return;
    }
    cal_queue[cal_q_head] = ev;
    cal_q_head            = next;
}

static uint8_t cal_take(void) {
    if (cal_q_tail == cal_q_head) {
        return CAL_EV_NONE;
    }
    uint8_t ev = cal_queue[cal_q_tail];
    cal_q_tail = (uint8_t)((cal_q_tail + 1u) % CAL_QUEUE_LEN);
    return ev;
}

// ---------------------------------------------------------------------------
// Guided-flow state.
// ---------------------------------------------------------------------------
enum cal_state {
    CAL_ST_IDLE = 0, // nothing captured yet; SW1 -> capture rest
    CAL_ST_UP,       // rest captured; SW1 -> capture Y-up
    CAL_ST_RIGHT,    // Y-up captured; SW1 -> capture X-right
    CAL_ST_ROLL,     // X-right captured; SW1 -> stop tracking, type the report
    CAL_ST_DONE,
};

static uint8_t  cal_state = CAL_ST_IDLE;
static bool     cal_tracking = false; // min/max sweep active (rest -> report)
static uint16_t cal_x_rest, cal_y_rest;
static uint16_t cal_x_noise, cal_y_noise; // half-band around rest
static uint16_t cal_x_min, cal_x_max, cal_y_min, cal_y_max;
static uint16_t cal_y_up, cal_x_right;

// ---------------------------------------------------------------------------
// Typing helpers. cal_u16() renders into one shared buffer, so never call it
// twice in a single expression - always type one number per call.
// ---------------------------------------------------------------------------
static char cal_numbuf[6];

static const char *cal_u16(uint16_t v) {
    char *p = cal_numbuf + sizeof(cal_numbuf) - 1;
    *p      = '\0';
    if (v == 0) {
        *--p = '0';
        return p;
    }
    while (v > 0) {
        *--p = (char)('0' + (v % 10u));
        v /= 10u;
    }
    return p;
}

static void cal_type(const char *s) {
    send_string_with_delay(s, CAL_TYPE_DELAY);
}

static void cal_num(uint16_t v) {
    cal_type(cal_u16(v));
}

static void cal_nl(void) {
    cal_type("\n");
}

// ---------------------------------------------------------------------------
// ADC helpers.
// ---------------------------------------------------------------------------
static uint16_t cal_clamp(int16_t v) {
    if (v < 0) {
        return 0;
    }
    if (v > CAL_ADC_MAX) {
        return CAL_ADC_MAX;
    }
    return (uint16_t)v;
}

static uint16_t cal_read(pin_t pin) {
    return cal_clamp(analogReadPin(pin));
}

static uint16_t cal_avg(pin_t pin) {
    uint32_t sum = 0;
    for (uint8_t i = 0; i < CAL_AVG_SAMPLES; i++) {
        sum += cal_read(pin);
        wait_ms(1);
    }
    return (uint16_t)((sum + (CAL_AVG_SAMPLES / 2u)) / CAL_AVG_SAMPLES);
}

static uint16_t cal_half_band(uint16_t rest, uint16_t lo, uint16_t hi) {
    uint16_t below = (uint16_t)(rest - lo);
    uint16_t above = (uint16_t)(hi - rest);
    return below > above ? below : above;
}

static void cal_fold(uint16_t v, uint16_t *lo, uint16_t *hi) {
    if (v < *lo) {
        *lo = v;
    }
    if (v > *hi) {
        *hi = v;
    }
}

// Rest capture: one CAL_NOISE_SAMPLES window at CAL_NOISE_STEP_MS spacing
// (>= 500 ms) gives BOTH the rest average (first CAL_AVG_SAMPLES) and the rest
// noise band (whole window). The min/max sweep is seeded from that window, so
// min <= rest <= max holds from the first instant and every half-swing below is
// non-negative by construction.
static void cal_capture_rest(void) {
    uint32_t sx = 0, sy = 0;
    uint16_t xlo = CAL_ADC_MAX, xhi = 0, ylo = CAL_ADC_MAX, yhi = 0;

    for (uint16_t i = 0; i < CAL_NOISE_SAMPLES; i++) {
        uint16_t x = cal_read(CAL_PIN_X);
        uint16_t y = cal_read(CAL_PIN_Y);
        if (i < CAL_AVG_SAMPLES) {
            sx += x;
            sy += y;
        }
        cal_fold(x, &xlo, &xhi);
        cal_fold(y, &ylo, &yhi);
        wait_ms(CAL_NOISE_STEP_MS);
    }

    cal_x_rest  = (uint16_t)((sx + (CAL_AVG_SAMPLES / 2u)) / CAL_AVG_SAMPLES);
    cal_y_rest  = (uint16_t)((sy + (CAL_AVG_SAMPLES / 2u)) / CAL_AVG_SAMPLES);
    cal_x_noise = cal_half_band(cal_x_rest, xlo, xhi);
    cal_y_noise = cal_half_band(cal_y_rest, ylo, yhi);
    cal_x_min   = xlo;
    cal_x_max   = xhi;
    cal_y_min   = ylo;
    cal_y_max   = yhi;
}

// ---------------------------------------------------------------------------
// The report.
// ---------------------------------------------------------------------------
static void cal_type_axis(const char *name, uint16_t lo, uint16_t rest, uint16_t hi, bool inverted) {
    cal_type(name);
    cal_type(": min=");
    cal_num(lo);
    cal_type(" rest=");
    cal_num(rest);
    cal_type(" max=");
    cal_num(hi);
    cal_type("  inverted=");
    cal_type(inverted ? "YES" : "NO");
    cal_nl();
}

static void cal_type_verdict_pair(const char *minus, const char *plus, uint16_t lo, uint16_t hi) {
    cal_type(minus);
    cal_type(CAL_FIRES_LOW(lo) ? " fires " : " NEVER FIRES ");
    cal_type(plus);
    cal_type(CAL_FIRES_HIGH(hi) ? " fires" : " NEVER FIRES");
}

static void cal_type_axis_json(const char *key, const char *pin, uint16_t low, uint16_t rest, uint16_t high, bool comma) {
    cal_type("\"");
    cal_type(key);
    cal_type("\": {\"input_pin\": \"");
    cal_type(pin);
    cal_type("\", \"low\": ");
    cal_num(low);
    cal_type(", \"rest\": ");
    cal_num(rest);
    cal_type(", \"high\": ");
    cal_num(high);
    cal_type("}");
    if (comma) {
        cal_type(",");
    }
    cal_nl();
}

static void cal_type_report(void) {
    // Direction sense. loudest_micro.c treats y < JS_CENTER - JS_THRESHOLD as UP
    // and x > JS_CENTER + JS_THRESHOLD as RIGHT, so on a correctly-sensed axis
    // pushing UP must DECREASE Y and pushing RIGHT must INCREASE X.
    const bool inv_y = (cal_y_up > cal_y_rest);
    const bool inv_x = (cal_x_right < cal_x_rest);

    // Half-swings. Non-negative by construction (see cal_capture_rest).
    const uint16_t sxl = (uint16_t)(cal_x_rest - cal_x_min);
    const uint16_t sxh = (uint16_t)(cal_x_max - cal_x_rest);
    const uint16_t syl = (uint16_t)(cal_y_rest - cal_y_min);
    const uint16_t syh = (uint16_t)(cal_y_max - cal_y_rest);

    uint16_t smallest = sxl;
    if (sxh < smallest) smallest = sxh;
    if (syl < smallest) smallest = syl;
    if (syh < smallest) smallest = syh;

    // Derived center: the shipped code shares ONE JS_CENTER across both axes.
    const uint16_t derived_center = (uint16_t)(((uint32_t)cal_x_rest + cal_y_rest + 1u) / 2u);
    // Derived threshold: 60% of the smallest half-swing, so every direction
    // fires with 40% of its travel still in reserve before the end-stop.
    const uint16_t derived_threshold = (uint16_t)(((uint32_t)smallest * CAL_THRESHOLD_PERCENT) / 100u);

    const uint16_t worst_noise = cal_x_noise > cal_y_noise ? cal_x_noise : cal_y_noise;
    const uint16_t rest_skew   = (uint16_t)(cal_x_rest > cal_y_rest ? cal_x_rest - cal_y_rest : cal_y_rest - cal_x_rest);

    cal_type("agentpad13 cal v1 | REPORT");
    cal_nl();
    cal_type_axis("X", cal_x_min, cal_x_rest, cal_x_max, inv_x);
    cal_type_axis("Y", cal_y_min, cal_y_rest, cal_y_max, inv_y);

    if (smallest < CAL_MIN_HALF_SWING) {
        cal_type("WARNING: SWING TOO SMALL - check JS1 / restart with SW2 (smallest half-swing ");
        cal_num(smallest);
        cal_type(", want ");
        cal_num(CAL_MIN_HALF_SWING);
        cal_type("+)");
        cal_nl();
    }
    if (derived_threshold <= (uint16_t)(CAL_NOISE_MARGIN * worst_noise)) {
        cal_type("WARNING: THRESHOLD INSIDE NOISE - derived JS_THRESHOLD ");
        cal_num(derived_threshold);
        cal_type(" is not more than ");
        cal_num(CAL_NOISE_MARGIN);
        cal_type("x the rest noise +/-");
        cal_num(worst_noise);
        cal_nl();
    }
    if (rest_skew > CAL_REST_SKEW_LIMIT) {
        cal_type("WARNING: X and Y rest differ by ");
        cal_num(rest_skew);
        cal_type(" counts (limit ");
        cal_num(CAL_REST_SKEW_LIMIT);
        cal_type(") - loudest_micro.c shares ONE JS_CENTER for both axes");
        cal_nl();
    }

    cal_type("shipped JS_THRESHOLD 300 verdict (fires only below 212 or above 812): ");
    cal_type_verdict_pair("X-", "X+", cal_x_min, cal_x_max);
    cal_type(" ");
    cal_type_verdict_pair("Y-", "Y+", cal_y_min, cal_y_max);
    cal_nl();

    cal_type("--- apply to firmware/loudest_micro/keyboard.json (joystick.axes): ---");
    cal_nl();
    // An inverted axis is fixed by SWAPPING low and high (POLARITY-NOTE.md "The
    // one-line fix"); the swap is already applied here, so these lines are final.
    cal_type_axis_json("x", "GP26", inv_x ? cal_x_max : cal_x_min, cal_x_rest, inv_x ? cal_x_min : cal_x_max, true);
    cal_type_axis_json("y", "GP27", inv_y ? cal_y_max : cal_y_min, cal_y_rest, inv_y ? cal_y_min : cal_y_max, false);

    cal_type("--- apply to firmware/loudest_micro/loudest_micro.c: ---");
    cal_nl();
    cal_type("#define JS_CENTER ");
    cal_num(derived_center);
    cal_nl();
    cal_type("#define JS_THRESHOLD ");
    cal_num(derived_threshold);
    cal_nl();
    cal_type("note: if an axis shows inverted=YES the arrow/scroll comparisons in");
    cal_nl();
    cal_type("loudest_micro.c must be mirrored for that axis too - POLARITY-NOTE.md");
    cal_nl();
}

// ---------------------------------------------------------------------------
// Guided flow.
// ---------------------------------------------------------------------------
static void cal_reset(void) {
    cal_state    = CAL_ST_IDLE;
    cal_tracking = false;
    cal_x_rest = cal_y_rest = 0;
    cal_x_noise = cal_y_noise = 0;
    cal_x_min = cal_y_min = CAL_ADC_MAX;
    cal_x_max = cal_y_max = 0;
    cal_y_up = cal_x_right = 0;
}

static void cal_step(void) {
    switch (cal_state) {
        case CAL_ST_IDLE:
            cal_capture_rest();
            cal_tracking = true;
            cal_state    = CAL_ST_UP;
            cal_type("agentpad13 cal v1 | rest X=");
            cal_num(cal_x_rest);
            cal_type(" Y=");
            cal_num(cal_y_rest);
            cal_type(" noise X=+/-");
            cal_num(cal_x_noise);
            cal_type(" Y=+/-");
            cal_num(cal_y_noise);
            cal_nl();
            cal_type("step 2/4: HOLD stick UP (away from you, toward the encoder edge), then press SW1");
            cal_nl();
            break;

        case CAL_ST_UP:
            cal_y_up = cal_avg(CAL_PIN_Y);
            cal_fold(cal_y_up, &cal_y_min, &cal_y_max);
            cal_state = CAL_ST_RIGHT;
            cal_type("Y up sample: ");
            cal_num(cal_y_up);
            cal_nl();
            cal_type("step 3/4: HOLD stick RIGHT, then press SW1");
            cal_nl();
            break;

        case CAL_ST_RIGHT:
            cal_x_right = cal_avg(CAL_PIN_X);
            cal_fold(cal_x_right, &cal_x_min, &cal_x_max);
            cal_state = CAL_ST_ROLL;
            cal_type("X right sample: ");
            cal_num(cal_x_right);
            cal_nl();
            cal_type("step 4/4: slowly roll the stick around its full outer edge twice, then press SW1");
            cal_nl();
            break;

        case CAL_ST_ROLL:
            cal_tracking = false;
            cal_state    = CAL_ST_DONE;
            cal_type_report();
            break;

        case CAL_ST_DONE:
        default:
            cal_type("already done: press SW2 to restart, SW3 for a live reading");
            cal_nl();
            break;
    }
}

static void cal_live(void) {
    uint16_t x = cal_read(CAL_PIN_X);
    uint16_t y = cal_read(CAL_PIN_Y);
    cal_type("live X=");
    cal_num(x);
    cal_type(" Y=");
    cal_num(y);
    cal_nl();
}

static void cal_handle(uint8_t ev) {
    switch (ev) {
        case CAL_EV_STEP:
            cal_step();
            break;
        case CAL_EV_RESTART:
            cal_reset();
            cal_type("restarted: center the stick, press SW1");
            cal_nl();
            break;
        case CAL_EV_LIVE:
            cal_live();
            break;
        case CAL_EV_TOUCH_DOWN:
            cal_type("TOUCH:DOWN");
            cal_nl();
            break;
        case CAL_EV_TOUCH_UP:
            cal_type("TOUCH:UP");
            cal_nl();
            break;
        case CAL_EV_ENC_CW:
            cal_type("ENC:CW");
            cal_nl();
            break;
        case CAL_EV_ENC_CCW:
            cal_type("ENC:CCW");
            cal_nl();
            break;
        case CAL_EV_ENC_PRESS:
            cal_type("ENC:PRESS");
            cal_nl();
            break;
        default:
            break;
    }
}

// ---------------------------------------------------------------------------
// QMK hooks.
// ---------------------------------------------------------------------------

// Continuous min/max sweep, at exactly the matrix cadence: loudest_micro.c's
// matrix_scan_kb() is the only caller of matrix_scan_user(), once per
// matrix_scan(). Active only between the rest capture (SW1 #1) and the report
// (SW1 #4), so nothing is folded in while the operator's hand is off the stick.
void matrix_scan_user(void) {
    if (!cal_tracking) {
        return;
    }
    cal_fold(cal_read(CAL_PIN_X), &cal_x_min, &cal_x_max);
    cal_fold(cal_read(CAL_PIN_Y), &cal_y_min, &cal_y_max);
}

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    const uint8_t row = record->event.key.row;
    const uint8_t col = record->event.key.col;

    if (row == CAL_TOUCH_ROW && col == CAL_TOUCH_COL) {
        cal_post(record->event.pressed ? CAL_EV_TOUCH_DOWN : CAL_EV_TOUCH_UP);
    } else if (record->event.pressed) {
        if (row == CAL_SW1_ROW && col == CAL_SW1_COL) {
            cal_post(CAL_EV_STEP);
        } else if (row == CAL_SW2_ROW && col == CAL_SW2_COL) {
            cal_post(CAL_EV_RESTART);
        } else if (row == CAL_SW3_ROW && col == CAL_SW3_COL) {
            cal_post(CAL_EV_LIVE);
        } else if (row == CAL_ENC_ROW && col == CAL_ENC_COL) {
            cal_post(CAL_EV_ENC_PRESS);
        }
        // every other switch: deliberate no-op
    }

    (void)keycode; // all positions are KC_NO; dispatch is by row/col only
    return false;  // never let a calibration keypress reach the host
}

bool encoder_update_user(uint8_t index, bool clockwise) {
    if (index == 0) {
        cal_post(clockwise ? CAL_EV_ENC_CW : CAL_EV_ENC_CCW);
    }
    return true;
}

// The only place that reads the ADC in bulk or types. Runs at top level in the
// keyboard task, so no send_string() is ever nested inside the action_exec()
// that delivered the event.
void housekeeping_task_user(void) {
    if (cal_q_overflow) {
        cal_q_overflow = false;
        cal_type("!! some events were dropped (queue overflow) - press SW2 and start over");
        cal_nl();
    }
    for (uint8_t ev = cal_take(); ev != CAL_EV_NONE; ev = cal_take()) {
        cal_handle(ev);
    }
}

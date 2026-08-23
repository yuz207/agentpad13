#!/usr/bin/env python3
"""agentpad13 Rev A firmware pin-map checker.

Asserts every pin in the firmware configuration against the definitive Rev A
per-GPIO table embedded below. The table was extracted twice from the final
board (netlist + pcbnew copper, identical on all 57 U1 pads), re-verified 20/20
against v5_6, and remains unchanged on the current public v5_7 board.

Checks, in order:
  1. keyboard.json matrix_pins.direct == the table, per logical key position.
  1b. TOUCH_OUT (GP16) is deliberately NOT in that matrix (the board straps the
     TTP223 active-HIGH and QMK's polarity knob is global), so instead: it is
     bound and read active-HIGH in loudest_micro.c and injected at [3,2], and
     MATRIX_INPUT_PRESSED_STATE stays undefined.
  2. keyboard.json encoder / ws2812 / joystick pins == the table.
  3. No firmware reference to any spare/NC GPIO (GP18-GP25, GP28, GP29) -
     including the "GP21" J2 net-name trap: that NET is silicon GPIO24 and
     must never appear in firmware as a GPIO number.
  4. Source scan: every GPnn token in the keyboard C sources is one of the
     pins the table assigns to firmware.
  5. (--qmk-info FILE) the same pin assertions against the resolved build
     config emitted by `qmk info -kb loudest_micro -f json`.
  6. (--qmk-home DIR) the vial-qmk tree contains the via_command_kb()
     backport (firmware/patches/0001-via-command-kb-backport.patch), without
     which the vial build silently loses status-protocol commands to VIA.

Exit code 0 with a final "PASS" line only if every assertion holds.

Usage:
    python3 check_pins_v4.py [--qmk-info info.json] [--qmk-home /path/to/vial-qmk]
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYBOARD_DIR = HERE / "loudest_micro"

# --- The authority: definitive GPIO table, verified against the v5 board ---
# function -> GPIO (only the firmware-relevant, assigned pins)
TABLE = {
    "SW1": "GP12",   # U1 pad 15, net SW1
    "SW2": "GP9",    # U1 pad 12, net SW2
    "SW3": "GP5",    # U1 pad 7,  net SW3
    "SW4": "GP2",    # U1 pad 4,  net SW4
    "SW5": "GP11",   # U1 pad 14, net SW5
    "SW6": "GP8",    # U1 pad 11, net SW6
    "SW7": "GP4",    # U1 pad 6,  net SW7
    "SW8": "GP1",    # U1 pad 3,  net SW8
    "SW9": "GP10",   # U1 pad 13, net SW9
    "SW10": "GP7",   # U1 pad 9,  net SW10
    "SW11": "GP3",   # U1 pad 5,  net SW11
    "SW12": "GP0",   # U1 pad 2,  net SW12
    "SW13": "GP6",   # U1 pad 8,  net SW13
    "ENC_A": "GP13",     # U1 pad 16, net ENC_A
    "ENC_B": "GP14",     # U1 pad 17, net ENC_B
    "ENC_SW": "GP15",    # U1 pad 18, net ENC_SW
    "TOUCH_OUT": "GP16", # U1 pad 27, net TOUCH_OUT
    "RGB_MCU": "GP17",   # U1 pad 28, net RGB_MCU (ws2812 data)
    "JOY_X_ADC": "GP26", # U1 pad 38, ADC0, net JOY_X_ADC
    "JOY_Y_ADC": "GP27", # U1 pad 39, ADC1, net JOY_Y_ADC
}

# Logical key grid -> function name. SW1-SW4 = row 0 left-to-right, SW5-SW8 =
# row 1, SW9-SW12 = row 2, SW13 (2U hero) = [3,0], encoder push = [3,1],
# [3,2] = touch (NOT a scanned matrix pin - see below), [3,3] unused.
#
# [3,2] is None ON PURPOSE (2026-08-13). The board straps the TTP223 ACTIVE-HIGH
# (R10 0R: TOUCH_AHLB -> GND on the current v5_7 board), the opposite sense of the 13
# switch-to-GND keys, and QMK's MATRIX_INPUT_PRESSED_STATE is global. So GP16 is
# removed from matrix_pins.direct and polled with its own sense in
# loudest_micro.c, which injects the key event at logical [3,2]. The check that
# GP16 is still claimed by firmware moved to check_touch_outside_matrix().
MATRIX_FUNCTIONS = [
    ["SW1", "SW2", "SW3", "SW4"],
    ["SW5", "SW6", "SW7", "SW8"],
    ["SW9", "SW10", "SW11", "SW12"],
    ["SW13", "ENC_SW", None, None],
]

# Reporting labels for positions with no scanned pin, so a `null` that is
# deliberate does not print as "unused".
MATRIX_LABELS = {(3, 2): "TOUCH_OUT (GP16, out of matrix by design)"}

# GPIOs firmware must never reference: I2C spares to the DNP J2 header
# (GP18 SDA / GP19 SCL / GP20 / GP28) plus every NC pad (GPIO21/22/23/25/29)
# and GPIO24 - the trap: the J2 net NAMED "GP21" is silicon GPIO24.
FORBIDDEN = {f"GP{n}" for n in (18, 19, 20, 21, 22, 23, 24, 25, 28, 29)}

ALLOWED = set(TABLE.values())

failures = []
checks = 0


def check(desc, ok, detail=""):
    global checks
    checks += 1
    status = "ok" if ok else "FAIL"
    line = f"  [{status}] {desc}"
    if detail and not ok:
        line += f"  <- {detail}"
    print(line)
    if not ok:
        failures.append(desc)


def assert_pin_config(cfg, source_name):
    """Assert matrix/encoder/ws2812/joystick pins in a keyboard.json-shaped dict."""
    print(f"-- {source_name}")
    direct = cfg["matrix_pins"]["direct"]
    check(f"{source_name}: matrix is 4 rows x 4 cols",
          len(direct) == 4 and all(len(r) == 4 for r in direct))
    for r, row in enumerate(MATRIX_FUNCTIONS):
        for c, func in enumerate(row):
            want = TABLE[func] if func else None
            got = direct[r][c]
            # qmk info resolves null to the string "NO_PIN"
            if got in (None, "NO_PIN"):
                got = None
            label = func or MATRIX_LABELS.get((r, c), "unused")
            check(f"{source_name}: [{r},{c}] {label} = {want or 'null'}",
                  got == want, f"got {got}")
    enc = cfg["encoder"]["rotary"][0]
    check(f"{source_name}: encoder pin_a ENC_A = {TABLE['ENC_A']}",
          enc["pin_a"] == TABLE["ENC_A"], f"got {enc['pin_a']}")
    check(f"{source_name}: encoder pin_b ENC_B = {TABLE['ENC_B']}",
          enc["pin_b"] == TABLE["ENC_B"], f"got {enc['pin_b']}")
    check(f"{source_name}: ws2812 pin RGB_MCU = {TABLE['RGB_MCU']}",
          cfg["ws2812"]["pin"] == TABLE["RGB_MCU"], f"got {cfg['ws2812']['pin']}")
    axes = cfg["joystick"]["axes"]
    check(f"{source_name}: joystick x JOY_X_ADC = {TABLE['JOY_X_ADC']}",
          axes["x"]["input_pin"] == TABLE["JOY_X_ADC"], f"got {axes['x']['input_pin']}")
    check(f"{source_name}: joystick y JOY_Y_ADC = {TABLE['JOY_Y_ADC']}",
          axes["y"]["input_pin"] == TABLE["JOY_Y_ADC"], f"got {axes['y']['input_pin']}")
    # Forbidden-pin sweep over the whole config. Documentation keys ("$..."
    # comments) may legitimately NAME spare pins while explaining that they
    # are unused, so they are stripped: only configuration values count.
    def strip_comments(node):
        if isinstance(node, dict):
            return {k: strip_comments(v) for k, v in node.items()
                    if not k.startswith("$")}
        if isinstance(node, list):
            return [strip_comments(v) for v in node]
        return node

    blob = json.dumps(strip_comments(cfg))
    hits = sorted(set(re.findall(r"\bGP(?:18|19|2[0-5]|28|29)\b", blob)))
    check(f"{source_name}: no spare/NC GPIO in configuration values (GP18-25/28/29)",
          not hits, f"found {hits}")


def check_touch_outside_matrix():
    """TOUCH_OUT (GP16) left the scanned matrix, so assert it is still claimed.

    The board straps the TTP223 active-HIGH (R10 0R: TOUCH_AHLB -> GND), so GP16
    cannot ride the direct-pin matrix, whose polarity knob is global. It must
    instead be bound to its own pin, read with an active-HIGH sense, and injected
    at logical [3,2]. Without these assertions, dropping GP16 from
    matrix_pins.direct would silently look like "touch removed".
    """
    print("-- touch (GP16) handled outside the matrix")
    src = (KEYBOARD_DIR / "loudest_micro.c").read_text()
    check(f"loudest_micro.c binds TOUCH_PIN to {TABLE['TOUCH_OUT']}",
          re.search(r"#define\s+TOUCH_PIN\s+" + TABLE["TOUCH_OUT"] + r"\b", src) is not None)
    check("loudest_micro.c declares the touch input ACTIVE-HIGH "
          "(TOUCH_PRESSED_STATE 1; board strap R10 TOUCH_AHLB->GND)",
          re.search(r"#define\s+TOUCH_PRESSED_STATE\s+1\b", src) is not None)
    check("loudest_micro.c injects the touch event at logical [3,2]",
          re.search(r"#define\s+TOUCH_MATRIX_ROW\s+3\b", src) is not None
          and re.search(r"#define\s+TOUCH_MATRIX_COL\s+2\b", src) is not None
          and "action_exec(MAKE_KEYEVENT(TOUCH_MATRIX_ROW, TOUCH_MATRIX_COL" in src)
    check("loudest_micro.c configures GP16 itself (matrix_init_pins no longer does)",
          "gpio_set_pin_input_low(TOUCH_PIN)" in src)
    # The global knob would invert the 13 genuinely active-low switches. Only a
    # real #define / config key counts here - the comments that explain WHY it
    # must not be used name the token on purpose.
    defs = []
    for f in sorted(KEYBOARD_DIR.rglob("*")):
        if not f.is_file() or f.suffix not in (".c", ".h", ".json", ".mk"):
            continue
        text = f.read_text()
        if re.search(r"^[ \t]*#[ \t]*define[ \t]+MATRIX_INPUT_PRESSED_STATE\b",
                     text, re.M):
            defs.append(f"{f.name} (#define)")
        if re.search(r'"MATRIX_INPUT_PRESSED_STATE"[ \t]*:', text):
            defs.append(f"{f.name} (json key)")
    check("MATRIX_INPUT_PRESSED_STATE is NOT defined (it is global; it would "
          "invert all 13 active-low switches)", not defs, f"defined in {defs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qmk-info", type=Path,
                    help="JSON dump from: qmk info -kb loudest_micro -f json")
    ap.add_argument("--qmk-home", type=Path,
                    help="vial-qmk checkout; verifies the via_command_kb backport")
    args = ap.parse_args()

    print("agentpad13 Rev A pin-map check "
          "(embedded definitive table; current public board v5_7)")

    kb_json = json.loads((KEYBOARD_DIR / "keyboard.json").read_text())
    assert_pin_config(kb_json, "keyboard.json")
    check_touch_outside_matrix()

    print("-- source scan")
    src_pins = set()
    for f in sorted(KEYBOARD_DIR.rglob("*.[ch]")):
        src_pins |= set(re.findall(r"\bGP\d+\b", f.read_text()))
    stray = sorted(src_pins - ALLOWED)
    check(f"sources reference only table-assigned pins ({sorted(src_pins)})",
          not stray, f"stray pins {stray}")
    check("sources reference no forbidden pin (incl. the GP21=GPIO24 net-name trap)",
          not (src_pins & FORBIDDEN), f"found {sorted(src_pins & FORBIDDEN)}")

    if args.qmk_info:
        info = json.loads(args.qmk_info.read_text())
        assert_pin_config(info, f"qmk info ({args.qmk_info.name})")
        print("-- resolved build config extras")
        check("qmk info: WS2812_DI_PIN resolves from ws2812.pin",
              info.get("ws2812", {}).get("pin") == TABLE["RGB_MCU"])
        check("qmk info: processor is RP2040",
              info.get("processor") == "RP2040", f"got {info.get('processor')}")

    if args.qmk_home:
        print("-- vial-qmk tree")
        via_c = args.qmk_home / "quantum" / "via.c"
        patched = via_c.exists() and "via_command_kb" in via_c.read_text()
        check("vial-qmk quantum/via.c carries the via_command_kb backport "
              "(patches/0001-via-command-kb-backport.patch)", patched,
              "unpatched tree: VIA will shadow status-protocol IDs 0x01-0x04")

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} checks failed")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS: all {checks} pin-map checks against the definitive "
          "v5 GPIO table succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())

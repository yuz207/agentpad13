#!/usr/bin/env python3
"""Raw HID status-protocol conformance test: firmware C vs daemon oracle (v0 + v1).

Compiles the REAL firmware handler (firmware/loudest_micro/loudest_micro.c)
on the host against tests/conformance/stubs/, then drives it with frames
built by the wire-format oracle, daemon/loudestd/protocol.py, asserting:

  * default (plain QMK) build path: every v0 command is handled and the CAPS
    reply to PING is byte-for-byte protocol.build_caps(...) - and parses back
    through the daemon's own parse_caps().
  * vial build path: the via_command_kb() dispatcher claims exactly the
    loudest frames and leaves every observed VIA/Vial client frame to VIA,
    with the three documented byte-collision exceptions:
      - SET_KEY(0, 0,0,0, solid)   -> VIA (get_protocol_version handshake)
      - SET_LAYER 1/2/3            -> VIA (uptime/layout_options/matrix_state)
      - VIA get_keycode(layer,0,0) -> loudest PING (vial-gui never sends it)
  * protocol v1 (docs/PROTOCOL-V1-CONTRACT.md): 0x50 GET_JOYSTICK, 0x51
    SET_CALIBRATION and 0x52 RESET_CALIBRATION, field by field against the
    oracle, including every validation boundary the contract names and the
    EEPROM write policy (AMENDED 2026-08-15: "writes happen ONLY on an accepted
    0x51, on 0x52, and on a successful SW14-triggered on-board calibration").
    The harness simulates the QMK keyboard datablock so a rejected write can be
    asserted to have written NOTHING, not merely to have answered "rejected".
    The third writer is deliberately NOT exercised here: it is time-driven, and
    stubs/quantum.h returns 0 from timer_elapsed32(), so the routine's 100 ms
    SW14 poll never comes due and the routine stays idle off target. That keeps
    every check below measuring exactly what it measured before the on-board
    routine existed. The routine is proven on the real binary instead, in the
    emulator, by firmware/sim/joystick.cjs section 10 (which also asserts it
    produces BYTE-IDENTICAL EEPROM contents to the 0x51 path).

Run:  python3 firmware/tests/conformance/run_conformance.py
Requires only a host C compiler (cc) and Python 3.10+.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KB_DIR = REPO / "firmware" / "loudest_micro"
DAEMON = REPO / "daemon"

sys.path.insert(0, str(DAEMON))
from loudestd import protocol as P  # noqa: E402  (the wire-format oracle)

FEATURES = P.Feature(0x1F)  # PER_KEY|UNDERGLOW|LAYER_INDICATOR|JOYSTICK|ENCODER
LAYERS = 8

passed = failed = 0


def check(desc, ok, detail=""):
    global passed, failed
    print(f"  [{'ok' if ok else 'FAIL'}] {desc}" + (f"  <- {detail}" if detail and not ok else ""))
    if ok:
        passed += 1
    else:
        failed += 1


def build(binary, extra_flags):
    cmd = ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-DRAW_ENABLE",
           *extra_flags, "-I", str(HERE / "stubs"), "-I", str(KB_DIR),
           str(HERE / "harness.c"), "-o", str(binary)]
    subprocess.run(cmd, check=True)


def run(binary, frames):
    """Feed 32-byte frames; return per-frame event dicts.

    An item may also be a control STRING passed to the harness verbatim:
    "ADC <gp26> <gp27>", "LEN <n>", "EE <hex>" or "BOOT" (see harness.c).
    Only frames and BOOT produce an event block, so index accordingly.
    """
    text = "".join(
        (item if isinstance(item, str) else item.hex()) + "\n" for item in frames
    )
    out = subprocess.run([str(binary)], input=text, capture_output=True,
                         text=True, check=True).stdout
    results = []
    for block in out.split("---\n")[:-1]:
        ev = {"claimed": None, "sent": [], "layers": [], "keys": {},
              "ee_writes": 0, "ee_block": b""}
        for line in block.splitlines():
            tok = line.split()
            if tok[0] == "CLAIMED":
                ev["claimed"] = bool(int(tok[1]))
            elif tok[0] == "SENT":
                ev["sent"].append(bytes.fromhex(tok[1]))
            elif tok[0] == "LAYER":
                ev["layers"].append(int(tok[1]))
            elif tok[0] == "KEY":
                ev["keys"][int(tok[1])] = tuple(int(t) for t in tok[2:])
            elif tok[0] == "EEWRITES":
                ev["ee_writes"] = int(tok[1])
            elif tok[0] == "EEBLOCK":
                ev["ee_block"] = bytes.fromhex(tok[1])
        results.append(ev)
    return results


def caps_checks(label, ev, token):
    want = P.build_caps(token=token, layer_count=LAYERS, features=FEATURES)
    check(f"{label}: exactly one CAPS reply", len(ev["sent"]) == 1, f"got {len(ev['sent'])}")
    if ev["sent"]:
        got = ev["sent"][0]
        check(f"{label}: CAPS == protocol.build_caps(token=0x{token:02x}) byte-for-byte",
              got == want, f"got {got.hex()} want {want.hex()}")
        caps = P.parse_caps(got)  # daemon's own parser on firmware bytes
        # protocol_version is 1 from 2026-08-15: the contract's Version section,
        # "LOUDEST_PROTO_VERSION 0 -> 1. The CAPS reply (PING 0x04) now reports 1
        # in byte 4." Every other CAPS byte is unchanged from v0.
        check(f"{label}: parse_caps -> v1/led24/layers8/features 0x1f",
              caps == P.Caps(token=token, protocol_version=1, led_count=24,
                             layer_count=LAYERS, features=FEATURES), repr(caps))


# --- protocol v1 helpers -------------------------------------------------------------

# One valid calibration, reused throughout. The axes deliberately rest at
# different values (512 / 498), which is the whole reason v1 stores a centre per
# axis instead of the old shared JS_CENTER 512.
GOOD_CAL = (512, 498, 289, 735, 270, 726)
# Every half-swing exactly at the contract's floor of 100.
FLOOR_CAL = (512, 498, 412, 612, 398, 598)
# What the harness feeds the two ADC pins. Deliberately different from each
# other, so a firmware that read GP27 into live_x would be caught here.
ADC_X, ADC_Y = 300, 700
# The EEPROM datablock struct: magic 'J', version 1 (contract, "EEPROM").
EE_MAGIC, EE_VERSION = 0x4A, 1


def cal_frame(rest_x, rest_y, min_x, max_x, min_y, max_y):
    """A SET_CALIBRATION frame built WITHOUT the host's validation.

    protocol.build_set_calibration() refuses to produce an invalid frame - that
    is its job - but the device's own validator is exactly what the boundary
    cases below have to exercise, so those bytes are laid out here instead. The
    first v1 check pins this packer against the oracle so it cannot drift.
    """
    payload = bytes((P.Command.SET_CALIBRATION.value,)) + b"".join(
        (v & 0xFFFF).to_bytes(2, "little")
        for v in (rest_x, rest_y, min_x, max_x, min_y, max_y)
    )
    return payload + bytes(P.REPORT_SIZE - len(payload))


def ee_bytes(cal, magic=EE_MAGIC, version=EE_VERSION):
    """The 14-byte loudest_js_cal_t as it sits in the EEPROM datablock."""
    return bytes((magic, version)) + b"".join(
        (v & 0xFFFF).to_bytes(2, "little") for v in cal
    )


def joystick_checks(label, ev, token, cal=None, live=(ADC_X, ADC_Y)):
    """Assert one GET_JOYSTICK reply against the oracle, field by field."""
    stored = {} if cal is None else dict(zip(P.CAL_FIELDS, cal))
    want = P.build_joystick(
        token=token, live_x=live[0], live_y=live[1],
        cal_state=P.CAL_STATE_UNCALIBRATED if cal is None else P.CAL_STATE_CALIBRATED,
        **stored,
    )
    check(f"{label}: exactly one JOYSTICK reply", len(ev["sent"]) == 1,
          f"got {len(ev['sent'])}")
    check(f"{label}: GET_JOYSTICK writes nothing to EEPROM", ev["ee_writes"] == 0,
          ev["ee_writes"])
    if not ev["sent"]:
        return
    got = ev["sent"][0]
    check(f"{label}: JOYSTICK == protocol.build_joystick(...) byte-for-byte",
          got == want, f"got {got.hex()} want {want.hex()}")
    js = P.parse_joystick(got)  # daemon's own parser on firmware bytes
    check(f"{label}: token echoed", js.token == token, js.token)
    check(f"{label}: GP26 -> live_x, GP27 -> live_y (no axis swap)",
          (js.live_x, js.live_y) == live, f"got ({js.live_x}, {js.live_y})")
    if cal is None:
        want_stored = (P.CAL_PLACEHOLDER_REST, P.CAL_PLACEHOLDER_REST,
                       P.CAL_PLACEHOLDER_MIN, P.CAL_PLACEHOLDER_MAX,
                       P.CAL_PLACEHOLDER_MIN, P.CAL_PLACEHOLDER_MAX)
        want_thresholds = (P.CAL_PLACEHOLDER_THRESHOLD, P.CAL_PLACEHOLDER_THRESHOLD)
    else:
        want_stored = cal
        want_thresholds = P.derive_thresholds(*cal)
    check(f"{label}: cal_state {0 if cal is None else 1}",
          js.cal_state == (0 if cal is None else 1), js.cal_state)
    check(f"{label}: stored values {want_stored}", js.as_tuple() == want_stored,
          js.as_tuple())
    check(f"{label}: thresholds {want_thresholds}",
          (js.threshold_x, js.threshold_y) == want_thresholds,
          (js.threshold_x, js.threshold_y))


def rejection_checks(label, ev, ee_before):
    """A rejected SET_CALIBRATION: answered 'rejected', and wrote NOTHING."""
    want = P.build_set_calibration_reply(P.CAL_REJECTED)
    check(f"{label}: replies status 1 (rejected)",
          ev["sent"] == [want],
          f"got {[f.hex() for f in ev['sent']]} want {want.hex()}")
    check(f"{label}: writes NOTHING to EEPROM", ev["ee_writes"] == 0, ev["ee_writes"])
    check(f"{label}: EEPROM datablock byte-for-byte unchanged",
          ev["ee_block"] == ee_before,
          f"{ev['ee_block'][:14].hex()} vs {ee_before[:14].hex()}")


def v1_present(binary):
    """Has the device side of protocol v1 landed in the firmware yet?"""
    ev = run(binary, [P.build_ping(0x01), P.build_get_joystick(0x01)])
    caps_is_v1 = bool(ev[0]["sent"]) and ev[0]["sent"][0][4] == 1
    return caps_is_v1 and bool(ev[1]["sent"])


def v1_checks(binary, label):
    """The whole v1 command set against one build of the firmware."""
    frames = [f"ADC {ADC_X} {ADC_Y}"]
    at = {}

    def add(name, frame):
        at[name] = sum(1 for f in frames if not isinstance(f, str))
        frames.append(frame)

    good_frame = P.build_set_calibration(*GOOD_CAL)
    check(f"{label}: cal_frame() packs exactly like protocol.build_set_calibration()",
          cal_frame(*GOOD_CAL) == good_frame,
          f"{cal_frame(*GOOD_CAL).hex()} vs {good_frame.hex()}")

    # Boundary cases the contract names, each at the exact edge of its rule.
    reject_cases = [
        ("rest_x 1024 (> 1023)", (1024, 498, 289, 735, 270, 726)),
        ("max_x 0xffff (full 16-bit)", (512, 498, 289, 0xFFFF, 270, 726)),
        ("min_y 1024 (> 1023)", (512, 498, 289, 735, 1024, 726)),
        ("min_x == rest_x", (512, 498, 512, 735, 270, 726)),
        ("min_x > rest_x", (512, 498, 600, 735, 270, 726)),
        ("rest_x == max_x", (512, 498, 289, 512, 270, 726)),
        ("rest_x > max_x", (512, 498, 289, 400, 270, 726)),
        ("min_y == rest_y", (512, 498, 289, 735, 498, 726)),
        ("rest_y == max_y", (512, 498, 289, 735, 270, 498)),
        ("x half-swing below rest = 99", (512, 498, 413, 735, 270, 726)),
        ("x half-swing above rest = 99", (512, 498, 289, 611, 270, 726)),
        ("y half-swing below rest = 99", (512, 498, 289, 735, 399, 726)),
        ("y half-swing above rest = 99", (512, 498, 289, 735, 270, 597)),
    ]

    add("uncal_read", P.build_get_joystick(0x11))
    add("accept_good", good_frame)
    add("cal_read", P.build_get_joystick(0x12))
    for i, (_, values) in enumerate(reject_cases):
        add(f"reject{i}", cal_frame(*values))
    add("survived_read", P.build_get_joystick(0x13))
    frames.append("LEN 12")  # one byte short of the 13-byte payload
    add("truncated", good_frame)
    frames.append(f"LEN {P.REPORT_SIZE}")
    add("after_truncated_read", P.build_get_joystick(0x14))
    add("accept_floor", P.build_set_calibration(*FLOOR_CAL))
    add("floor_read", P.build_get_joystick(0x15))
    add("reset", P.build_reset_calibration())
    add("reset_read", P.build_get_joystick(0x16))
    add("v0_set_key", P.build_set_key(5, 1, 2, 3, P.Effect.PULSE))
    add("v0_set_layer", P.build_set_layer(4))
    add("v0_clear", P.build_clear())
    add("v0_ping", P.build_ping(0x22))

    ev = run(binary, frames)

    # -- 0x50 on a board that has never been calibrated
    joystick_checks(f"{label}: GET_JOYSTICK uncalibrated", ev[at["uncal_read"]], 0x11)

    # -- 0x51 accepted
    accepted = ev[at["accept_good"]]
    check(f"{label}: SET_CALIBRATION replies status 0 (accepted)",
          accepted["sent"] == [P.build_set_calibration_reply(P.CAL_ACCEPTED)],
          [f.hex() for f in accepted["sent"]])
    check(f"{label}: an accepted SET_CALIBRATION writes EEPROM exactly once",
          accepted["ee_writes"] == 1, accepted["ee_writes"])
    check(f"{label}: EEPROM datablock == magic 'J', version 1, then the six values",
          accepted["ee_block"][:14] == ee_bytes(GOOD_CAL),
          f"{accepted['ee_block'][:14].hex()} vs {ee_bytes(GOOD_CAL).hex()}")
    joystick_checks(f"{label}: GET_JOYSTICK calibrated", ev[at["cal_read"]], 0x12,
                    cal=GOOD_CAL)

    # -- 0x51 rejected: every boundary the contract names, none of them writing
    ee_after_good = ev[at["accept_good"]]["ee_block"]
    for i, (desc, _) in enumerate(reject_cases):
        rejection_checks(f"{label}: SET_CALIBRATION {desc}", ev[at[f"reject{i}"]],
                         ee_after_good)
    joystick_checks(f"{label}: calibration survived every rejection",
                    ev[at["survived_read"]], 0x13, cal=GOOD_CAL)

    # -- a frame shorter than the 13-byte payload: ignored, not read past
    truncated = ev[at["truncated"]]
    check(f"{label}: SET_CALIBRATION truncated to 12 bytes is not accepted",
          truncated["sent"] != [P.build_set_calibration_reply(P.CAL_ACCEPTED)],
          [f.hex() for f in truncated["sent"]])
    rejection_checks(f"{label}: SET_CALIBRATION truncated to 12 bytes", truncated,
                     ee_after_good)
    joystick_checks(f"{label}: calibration survived the truncated frame",
                    ev[at["after_truncated_read"]], 0x14, cal=GOOD_CAL)

    # -- the accept side of the 99/100 boundary
    floor = ev[at["accept_floor"]]
    check(f"{label}: SET_CALIBRATION with every half-swing exactly 100 is ACCEPTED",
          floor["sent"] == [P.build_set_calibration_reply(P.CAL_ACCEPTED)],
          [f.hex() for f in floor["sent"]])
    check(f"{label}: that acceptance writes EEPROM exactly once",
          floor["ee_writes"] == 1, floor["ee_writes"])
    joystick_checks(f"{label}: GET_JOYSTICK at the half-swing floor",
                    ev[at["floor_read"]], 0x15, cal=FLOOR_CAL)

    # -- 0x52
    reset = ev[at["reset"]]
    check(f"{label}: RESET_CALIBRATION == protocol.build_reset_calibration_reply()",
          reset["sent"] == [P.build_reset_calibration_reply()],
          [f.hex() for f in reset["sent"]])
    check(f"{label}: RESET_CALIBRATION writes EEPROM exactly once",
          reset["ee_writes"] == 1, reset["ee_writes"])
    check(f"{label}: RESET_CALIBRATION invalidates the EEPROM magic",
          reset["ee_block"][0] != EE_MAGIC, f"magic still 0x{reset['ee_block'][0]:02x}")
    joystick_checks(f"{label}: placeholders are live again after RESET (no reboot)",
                    ev[at["reset_read"]], 0x16)

    # -- the contract's write policy: nothing else may touch the EEPROM
    for name in ("v0_set_key", "v0_set_layer", "v0_clear", "v0_ping"):
        check(f"{label}: {name.replace('v0_', '').upper()} writes nothing to EEPROM",
              ev[at[name]]["ee_writes"] == 0, ev[at[name]]["ee_writes"])


def boot_checks(binary, label):
    """What a board makes of the EEPROM it wakes up to (contract, "EEPROM")."""
    cases = [
        ("a valid stored calibration", ee_bytes(GOOD_CAL), GOOD_CAL),
        ("a blank block", bytes(14), None),
        ("bad magic", ee_bytes(GOOD_CAL, magic=0x00), None),
        ("wrong magic ('L' not 'J')", ee_bytes(GOOD_CAL, magic=0x4C), None),
        ("unknown version 2", ee_bytes(GOOD_CAL, version=2), None),
        ("right magic, values that fail validation (half-swing 99)",
         ee_bytes((512, 498, 413, 735, 270, 726)), None),
    ]
    for desc, block, expected in cases:
        ev = run(binary, [f"ADC {ADC_X} {ADC_Y}", f"EE {block.hex()}", "BOOT",
                          P.build_get_joystick(0x31)])
        check(f"{label}: boot with {desc} writes nothing", ev[0]["ee_writes"] == 0,
              ev[0]["ee_writes"])
        joystick_checks(f"{label}: boot with {desc}", ev[1], 0x31, cal=expected)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="loudest_conformance_"))
    default_bin, vial_bin = tmp / "harness_default", tmp / "harness_vial"
    build(default_bin, [])
    build(vial_bin, ["-DVIA_ENABLE", "-DVIAL_MODE", "-DDYNAMIC_KEYMAP_LAYER_COUNT=8"])

    print("== default (plain QMK) build path: full v0 protocol ==")
    frames = [
        P.build_set_key(5, 1, 2, 3, P.Effect.PULSE),
        P.build_set_key(23, 255, 128, 0, P.Effect.BLINK),
        P.build_set_key(0, 0, 0, 0, P.Effect.SOLID),  # all-zero payload: fine without VIA
        P.build_set_layer(3),
        P.build_ping(0x5A),
        P.build_clear(),
        P.build_ping(0x00),
    ]
    ev = run(default_bin, frames)
    check("SET_KEY(5,#010203,pulse) stored", ev[0]["keys"].get(5) == (1, 2, 3, 1), ev[0]["keys"])
    check("SET_KEY(23,#ff8000,blink) stored", ev[1]["keys"].get(23) == (255, 128, 0, 2), ev[1]["keys"])
    check("SET_KEY(0,#000000,solid) stored (no VIA to collide with)",
          ev[2]["keys"].get(0) == (0, 0, 0, 0), ev[2]["keys"])
    check("SET_LAYER(3) -> layer_move(3)", ev[3]["layers"] == [3], ev[3]["layers"])
    caps_checks("PING(0x5a)", ev[4], 0x5A)
    check("CLEAR wipes all slots", ev[5]["keys"] == {}, ev[5]["keys"])
    check("no unsolicited replies to SET_KEY/SET_LAYER/CLEAR",
          all(not e["sent"] for e in (ev[0], ev[1], ev[2], ev[3], ev[5])))
    caps_checks("PING(0x00)", ev[6], 0x00)

    print("== vial build path: via_command_kb() dispatch ==")
    # -- loudest frames that must be claimed
    claim = []
    for idx in range(24):
        claim.append(("SET_KEY idx %d" % idx, P.build_set_key(idx, 10, 20, 30, P.Effect.SOLID)))
    for fx in (P.Effect.SOLID, P.Effect.PULSE, P.Effect.BLINK):
        claim.append(("SET_KEY effect %s" % fx.name, P.build_set_key(1, 0, 0, 1, fx)))
    for layer in (0, 4, 5, 6, 7):
        claim.append(("SET_LAYER %d" % layer, P.build_set_layer(layer)))
    claim.append(("CLEAR", P.build_clear()))
    claim.append(("PING token 0x00", P.build_ping(0)))
    claim.append(("PING token 0xa7", P.build_ping(0xA7)))
    ev = run(vial_bin, [f for _, f in claim])
    for (desc, _), e in zip(claim, ev):
        check(f"claims {desc}", e["claimed"] is True)
        if desc.startswith("SET_LAYER"):
            n = int(desc.split()[1])
            check(f"vial {desc} -> layer_move({n})", e["layers"] == [n], e["layers"])
    caps_checks("vial PING(0x00)", ev[-2], 0x00)
    caps_checks("vial PING(0xa7)", ev[-1], 0xA7)

    # -- documented collisions + every observed VIA/Vial client frame: not claimed
    def via_frame(*bs):
        return bytes(bs) + bytes(32 - len(bs))

    leave = [
        ("SET_KEY(0,#000000,solid) == VIA get_protocol_version handshake (documented)",
         P.build_set_key(0, 0, 0, 0, P.Effect.SOLID)),
        ("SET_LAYER 1 == VIA get uptime (documented)", P.build_set_layer(1)),
        ("SET_LAYER 2 == VIA get layout_options (documented)", P.build_set_layer(2)),
        ("SET_LAYER 3 == VIA get switch_matrix_state (documented)", P.build_set_layer(3)),
        ("VIA get_keyboard_value(layout_options)", via_frame(0x02, 0x02)),
        ("VIA get_keyboard_value(switch_matrix_state)", via_frame(0x02, 0x03)),
        ("VIA set_keyboard_value(layout_options, ...)", via_frame(0x03, 0x02, 0, 0, 0, 1)),
        ("VIA get_keycode(0, row 1, col 2)", via_frame(0x04, 0x00, 0x01, 0x02)),
        ("VIA set_keycode", via_frame(0x05, 0x00, 0x00, 0x00, 0x00, 0x29)),
        ("VIA lighting_get_value (VialRGB)", via_frame(0x08, 0x40)),
        ("VIA keymap_get_buffer", via_frame(0x12, 0x00, 0x00, 0x1C)),
        ("Vial prefix get_keyboard_id", via_frame(0xFE, 0x00)),
        ("Vial prefix get_definition", via_frame(0xFE, 0x02, 0x00, 0x00, 0x00, 0x00)),
        ("VIA id_unhandled echo", via_frame(0xFF)),
        ("malformed SET_KEY index 24", via_frame(0x01, 24, 1, 1, 1, 0)),
        ("malformed SET_KEY effect 3", via_frame(0x01, 3, 1, 1, 1, 3)),
        ("malformed SET_KEY trailing garbage", via_frame(0x01, 3, 1, 1, 1, 0, 0, 9)),
        ("malformed SET_LAYER 8", via_frame(0x02, 8)),
        ("malformed SET_LAYER trailing garbage", via_frame(0x02, 4, 7)),
        ("malformed CLEAR trailing garbage", via_frame(0x03, 0, 5)),
        ("malformed PING trailing garbage", via_frame(0x04, 1, 0, 3)),
    ]
    ev = run(vial_bin, [f for _, f in leave])
    for (desc, _), e in zip(leave, ev):
        check(f"leaves to VIA: {desc}",
              e["claimed"] is False and not e["sent"] and not e["layers"])

    # the one deliberate steal from legacy VIA traffic
    ev = run(vial_bin, [via_frame(0x04, 0x02)])
    check("claims VIA get_keycode(2,0,0) as PING (documented steal; vial-gui "
          "never sends 0x04)", ev[0]["claimed"] is True and len(ev[0]["sent"]) == 1)

    print("== protocol v1: joystick + calibration (default build path) ==")
    if not v1_present(default_bin):
        print("  !! DEVICE SIDE NOT PRESENT: this firmware does not report")
        print("     protocol_version 1 and/or does not answer 0x50, so the v1")
        print("     handlers have not landed in firmware/loudest_micro/")
        print("     loudest_micro.c yet. The v1 checks below are NOT skipped and")
        print("     NOT weakened - they will FAIL until the device side lands.")
    v1_checks(default_bin, "default")
    boot_checks(default_bin, "default")

    print("== protocol v1: vial build path (0x50-0x52 claimed unconditionally) ==")
    # The contract's "Command IDs - why 0x50-0x52": these sit outside every VIA
    # range, so via_command_kb() claims them with NO payload heuristics - unlike
    # the tail-zero disambiguation that 0x01-0x04 need.
    unconditional = [
        ("GET_JOYSTICK", P.build_get_joystick(0x21)),
        ("GET_JOYSTICK with trailing garbage",
         P.build_get_joystick(0x21)[:4] + b"\x09" + bytes(27)),
        ("SET_CALIBRATION (valid)", P.build_set_calibration(*GOOD_CAL)),
        ("SET_CALIBRATION (invalid: half-swing 99)",
         cal_frame(512, 498, 413, 735, 270, 726)),
        ("SET_CALIBRATION with trailing garbage",
         P.build_set_calibration(*GOOD_CAL)[:13] + b"\x07" + bytes(18)),
        ("RESET_CALIBRATION", P.build_reset_calibration()),
        ("RESET_CALIBRATION with trailing garbage",
         P.build_reset_calibration()[:1] + b"\x05" + bytes(30)),
    ]
    ev = run(vial_bin, [f for _, f in unconditional])
    for (desc, _), e in zip(unconditional, ev):
        check(f"vial claims {desc} unconditionally", e["claimed"] is True)
        check(f"vial {desc} is fully handled (a reply, so VIA never sees it)",
              len(e["sent"]) == 1, f"got {len(e['sent'])}")
    v1_checks(vial_bin, "vial")
    boot_checks(vial_bin, "vial")

    print()
    total = passed + failed
    if failed:
        print(f"FAIL: {failed}/{total} conformance checks failed")
        return 1
    print(f"PASS: all {total} protocol v0+v1 conformance checks passed "
          "(firmware C handler vs daemon/loudestd/protocol.py oracle)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

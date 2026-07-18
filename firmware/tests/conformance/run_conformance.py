#!/usr/bin/env python3
"""Raw HID status-protocol v0 conformance test: firmware C vs daemon oracle.

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
    """Feed 32-byte frames; return per-frame event dicts."""
    text = "".join(f.hex() + "\n" for f in frames)
    out = subprocess.run([str(binary)], input=text, capture_output=True,
                         text=True, check=True).stdout
    results = []
    for block in out.split("---\n")[:-1]:
        ev = {"claimed": None, "sent": [], "layers": [], "keys": {}}
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
        check(f"{label}: parse_caps -> v0/led24/layers8/features 0x1f",
              caps == P.Caps(token=token, protocol_version=0, led_count=24,
                             layer_count=LAYERS, features=FEATURES), repr(caps))


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

    print()
    total = passed + failed
    if failed:
        print(f"FAIL: {failed}/{total} conformance checks failed")
        return 1
    print(f"PASS: all {total} protocol-v0 conformance checks passed "
          "(firmware C handler vs daemon/loudestd/protocol.py oracle)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

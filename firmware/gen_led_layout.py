#!/usr/bin/env python3
"""Generate the QMK rgb_matrix.layout block from the Rev A board file.

Usage:
    python3 gen_led_layout.py path/to/agentpad13.kicad_pcb

Reads the LED1..LED24 footprint centroids and the Edge.Cuts outline straight
out of the KiCad board file (v4_r27 is the shipped Rev A board, see
hardware/pcb/v4/ORDER-READINESS.md), scales them into QMK rgb_matrix space
(x 0-224, y 0-64, origin top-left), and prints the JSON "layout" array to
paste into keyboard.json.

Chain order (electrical, verified on the board: U5.B -> RGB_D00 -> LED1 ...
LED14 -> RGB_D14 -> LED15 ... LED24):
    chain 0-12  = LED1-LED13  = per-key, under SW1-SW13   (flags 4)
    chain 13    = LED14       = layer indicator           (flags 8)
    chain 14-23 = LED15-LED24 = edge underglow            (flags 2)

Per-key chain positions carry the QMK "matrix" association: SW1-SW4 = row 0,
SW5-SW8 = row 1, SW9-SW12 = row 2, SW13 (2U hero) = [3, 0].
"""
import json
import re
import sys


def footprint_positions(board_text):
    """Map footprint reference -> (x_mm, y_mm) for every footprint."""
    refs = {}
    for m in re.finditer(r'\(footprint\s+"[^"]+"', board_text):
        depth, i = 0, m.start()
        while i < len(board_text):
            c = board_text[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = board_text[m.start() : i + 1]
        at = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+[-\d.]+)?\)", block)
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if at and ref:
            refs[ref.group(1)] = (float(at.group(1)), float(at.group(2)))
    return refs


def outline_bbox(board_text):
    xs, ys = [], []
    for m in re.finditer(
        r"\(gr_(?:line|arc|rect|circle)[^)]*?\(start\s+([-\d.]+)\s+([-\d.]+)\)"
        r".*?\(end\s+([-\d.]+)\s+([-\d.]+)\).*?\(layer\s+\"Edge\.Cuts\"\)",
        board_text,
        re.S,
    ):
        xs += [float(m.group(1)), float(m.group(3))]
        ys += [float(m.group(2)), float(m.group(4))]
    return min(xs), min(ys), max(xs), max(ys)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    board_text = open(sys.argv[1]).read()
    refs = footprint_positions(board_text)
    x0, y0, x1, y1 = outline_bbox(board_text)
    w, h = x1 - x0, y1 - y0

    def qmk(ref, flags, matrix=None):
        x_mm, y_mm = refs[ref]
        entry = {}
        if matrix is not None:
            entry["matrix"] = matrix
        entry["x"] = round((x_mm - x0) / w * 224)
        entry["y"] = round((y_mm - y0) / h * 64)
        entry["flags"] = flags
        return entry

    leds = []
    # chain 0-11: LED1-LED12 under the SW1-SW12 4x3 grid
    for chain in range(12):
        leds.append(qmk(f"LED{chain + 1}", 4, matrix=[chain // 4, chain % 4]))
    # chain 12: LED13 under SW13 (2U hero)
    leds.append(qmk("LED13", 4, matrix=[3, 0]))
    # chain 13: LED14 layer indicator
    leds.append(qmk("LED14", 8))
    # chain 14-23: LED15-LED24 underglow ring
    for n in range(15, 25):
        leds.append(qmk(f"LED{n}", 2))

    print(json.dumps({"layout": leds}, indent=4))


if __name__ == "__main__":
    main()

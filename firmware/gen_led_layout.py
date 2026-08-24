#!/usr/bin/env python3
"""Generate the QMK rgb_matrix.layout block from the Rev A board file.

Usage:
    python3 gen_led_layout.py path/to/agentpad13.kicad_pcb

Reads the LED1..LED24 footprint centroids and the Edge.Cuts outline straight
out of the KiCad board file, scales them into QMK rgb_matrix space
(x 0-224, y 0-64, origin top-left), and prints the JSON "layout" array to
paste into keyboard.json.

THE TRANSFORM IS ISOTROPIC: ONE scale factor for BOTH axes.
    s        = 64 / bbox_height            (0.640 units/mm on v5_8)
    y_qmk    = round((y_mm - y0) * s)
    x_qmk    = round(112 + (x_mm - x_center) * s)
The board is portrait (84.2 x 100.0 mm) and QMK's coordinate space is landscape
(224 x 64), so the height is the binding axis: y is scaled to fill 0..64 and x
gets the SAME units/mm, which leaves the LED cloud only ~54 units wide. It is
therefore CENTERED on x = 112 -- QMK's default effect center
(k_rgb_matrix_center = {112, 32}, quantum/rgb_matrix/rgb_matrix.c:32), so no
RGB_MATRIX_CENTER override is needed: the default is correct by construction.
LED13 sits at board x = 42.1 mm = exactly the bbox center, so it lands on
x = 112 dead on.

(CHANGED 2026-08-15, recorded in `release/RELEASE.md` row K. This used to
normalise each axis INDEPENDENTLY to the bbox --
"x = round((x_mm - x0) / w * 224)", "y = round((y_mm - y0) / h * 64)" -- giving
x 2.660 units/mm against y 0.640 units/mm, an aspect distortion of 4.16:1. That
is QMK's own convention and is not a bug, but on a portrait board it skews every
geometry-bearing animation: of the 10 enabled here, cycle_pinwheel, cycle_spiral,
dual_beacon and rainbow_moving_chevron all read the LED coordinates as a plane.
The y column is NUMERICALLY UNCHANGED by this rewrite -- (y_mm - y0) * (64/h) is
the same arithmetic as (y_mm - y0) / h * 64 -- so only x moved, on 23 of the 24
entries. LED13 was already 112 under both transforms, because 42.1 mm is the
midpoint of the 0..84.2 span as well as the bbox center.)

THE CURRENT PUBLIC BOARD IS `release/hardware/pcb/v5_8.kicad_pcb`
(v5_8, md5 8c32ff4a6e6d77a87c4584029d4a1c75) -- run this against that file.
The layout was originally diffed against v5_6 at 24/24 entries and 0
mismatches. v5_8 retains the v5.7 LED20/LED21 correction and changes only TP5,
not any LED centroid, net, or board-outline coordinate
(`release/hardware/pcb/V5-NOTES.md`).

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


# QMK's default RGB-matrix effect center, i.e. the point every geometry-bearing
# animation spins/sweeps around: quantum/rgb_matrix/rgb_matrix.c:32,
# `const led_point_t k_rgb_matrix_center = {112, 32};` (used whenever
# RGB_MATRIX_CENTER is not defined). Centering the LED cloud here is what makes
# the default correct, so the keyboard does not have to override it.
QMK_CENTER_X = 112

# The current public v5_8 board, for the sanity assertion below.
PUBLIC_BOARD_SCALE = 0.64  # = 64 / 100.0 mm bbox height
PUBLIC_BOARD_X_CENTER = 42.1  # = (0.0 + 84.2) / 2 mm
_EPS = 1e-9


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    board_text = open(sys.argv[1]).read()
    refs = footprint_positions(board_text)
    x0, y0, x1, y1 = outline_bbox(board_text)
    w, h = x1 - x0, y1 - y0

    # ONE scale for both axes (see the module docstring). Height is binding
    # because the board is portrait and QMK's space is landscape.
    s = 64.0 / h
    x_center = (x0 + x1) / 2.0

    # Fail loudly rather than silently emit a layout for some other board: every
    # number downstream (keyboard.json rgb_matrix.layout, and the claim that the
    # default k_rgb_matrix_center is correct) is pinned to the public v5_8 board.
    if abs(s - PUBLIC_BOARD_SCALE) > _EPS or abs(x_center - PUBLIC_BOARD_X_CENTER) > _EPS:
        sys.exit(
            "REFUSING TO EMIT: this board's derived transform does not match the\n"
            "current public v5_8 board.\n"
            f"  Edge.Cuts bbox : x {x0} .. {x1}  (w {w})   y {y0} .. {y1}  (h {h})\n"
            f"  derived scale  : 64/h = {s!r}          expected {PUBLIC_BOARD_SCALE!r}\n"
            f"  derived center : (x0+x1)/2 = {x_center!r}   expected {PUBLIC_BOARD_X_CENTER!r}\n"
            "If the outline really changed, re-verify the x=112 centering claim and\n"
            "whether RGB_MATRIX_CENTER now needs an explicit override before\n"
            "relaxing this check."
        )

    def qmk(ref, flags, matrix=None):
        x_mm, y_mm = refs[ref]
        entry = {}
        if matrix is not None:
            entry["matrix"] = matrix
        entry["x"] = round(QMK_CENTER_X + (x_mm - x_center) * s)
        entry["y"] = round((y_mm - y0) * s)
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

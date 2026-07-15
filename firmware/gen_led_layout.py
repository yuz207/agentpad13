#!/usr/bin/env python3
"""Generate the QMK rgb_matrix layout block from the Phase-0 v2 mm coordinate table.

Source of truth: docs/independent-design/phase0-layout-v2-notes.md (mm table, D1 top-band).
QMK rgb_matrix space: x 0-224, y 0-64.

Chain order: 0-12 per-key (SW1-SW13), 13 layer indicator, 14-23 underglow
(clockwise from top-left; underglow positions provisional until PCB routing).
"""
import json

PCB_W, PCB_H = 84.2, 103.7  # mm — Phase-0 v2 outline (D1 resolved: top band)

def led(x_mm, y_mm, flags):
    return {
        "x": round(x_mm / PCB_W * 224),
        "y": round(y_mm / PCB_H * 64),
        "flags": flags,  # 4 = per-key, 8 = indicator, 2 = underglow
    }

leds = []
# SW1-SW12: 4x3 grid, pitch 19.05, column centers from x=13.525
for row, y in enumerate((33.35, 52.40, 71.45)):
    for col in range(4):
        e = led(13.525 + 19.05 * col, y, 4)
        e["matrix"] = [row, col]
        leds.append(e)
# SW13 (2U, bottom row)
e = led(42.100, 90.50, 4)
e["matrix"] = [3, 0]
leds.append(e)
# Layer indicator (chain 13), adjacent to touch pad
leds.append(led(13.525, 82.0, 8))
# Underglow 14-23: perimeter ring, clockwise from top-left (provisional)
perimeter = [
    (25, 5), (59, 5), (79, 30), (79, 62), (79, 90),
    (55, 99), (28, 99), (5, 90), (5, 62), (5, 30),
]
for x, y in perimeter:
    leds.append(led(x, y, 2))

print(json.dumps({"layout": leds}, indent=4))

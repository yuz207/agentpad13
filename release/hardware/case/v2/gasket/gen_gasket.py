#!/usr/bin/env python3
"""gen_gasket.py — optional PORON ledge-gasket kit generator (v5, 2026-07-20).

An OPTIONAL, user-cut foam accessory for the agentpad13 v2 band. NO design
geometry changes anywhere: the band/tray/plate/board STLs and fab files are
untouched. This script only READS the case-model constants and EMITS a paper/
foam cutting kit derived from the existing band rabbet-ledge geometry.

Derivation (EXECUTOR-PROTOCOL §2 — geometry from the source, never retyped):
  * The band's rabbet ledge is cut in `band()` of ../agentpad13_case_v2.py:
        ring -= _rprism(INNER_W,           INNER_H,           INNER_R,        ... LEDGE_Z0)   # opening below the ledge
        ring -= _rprism(INNER_W-2*LEDGE_W, INNER_H-2*LEDGE_W, INNER_R-LEDGE_W ...)            # the ledge band
    so the ledge is a LEDGE_W-wide perimeter ring whose OUTER outline is the
    band inner wall (INNER_W x INNER_H, R = INNER_R) and whose INNER outline is
    (INNER_W-2*LEDGE_W) x (INNER_H-2*LEDGE_W), R = INNER_R-LEDGE_W. Its
    underside sits at z = LEDGE_Z0 (+0.3) above the PCB top rim.
  * Every constant below is PARSED from ../agentpad13_case_v2.py and the board
    contract (the same two sources the case model itself reads); the derived
    values are recomputed with the module's own formulas and self-checked
    against the module's inline comment values.

Empirical cross-check (this session): the actual band STL
(../stl/agentpad13_v2_band_1.6mm.stl, md5 36980cc2ff011dc32d923fb04f7429f7)
was plane-sliced at y=50 / x=25 / x=60 — the ledge underside is FLAT at
z=0.300 spanning the full LEDGE_W width on all four sides (the code's inner-
edge chamfer was OCCT-refused and left square, per its own fallback message).

Outputs (into this directory):
  gasket_template.svg  — 1:1 (mm), ledge ring (light) + segment cut rects
                         (solid) + 50 mm scale bar + print-at-100% note + labels
  gasket_template.pdf  — same, exactly 1:1 (inkscape; page MediaBox verified mm)
  gasket_template.png  — raster preview for eyeball verification
  gasket_segments.dxf  — just the cut rectangles, mm units, for craft cutters
"""

import json
import math
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_PY = os.path.normpath(os.path.join(HERE, "..", "agentpad13_case_v2.py"))
CONTRACT = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "pcb", "harness", "contract_v4.json"))

def _band_stl_path(wall):
    """v2.6: the band export name carries the sidewall (_w{WALL}); fall back to
    the pre-v2.6 unsuffixed name for the 2.4 wall."""
    stl = os.path.join(HERE, "..", "stl")
    p = os.path.join(stl, f"agentpad13_v2_band_1.6mm_w{wall:.1f}.stl")
    if not os.path.exists(p):
        p = os.path.join(stl, "agentpad13_v2_band_1.6mm.stl")
    return os.path.normpath(p)


BAND_MD5_EXPECT = "36980cc2ff011dc32d923fb04f7429f7"   # RETIRED, see §3 below

# ---------------------------------------------------------------------------
# 1. PARSE constants from the case model + the board contract (no retyping)
# ---------------------------------------------------------------------------
_SRC = open(CASE_PY).read()


def _const(name):
    m = re.search(rf"^{name}\s*=\s*(-?\d+(?:\.\d+)?)", _SRC, re.M)
    if not m:
        raise SystemExit(f"constant {name!r} not found in {CASE_PY}")
    return float(m.group(1))


LEDGE_W = _const("LEDGE_W")            # 1.2  band rabbet ledge width
LEDGE_Z0 = _const("LEDGE_Z0")          # 0.3  ledge underside above PCB top
PCB_CLEARANCE = _const("PCB_CLEARANCE")  # 0.3 PCB edge -> band inner wall slip
WALL = _const("WALL")                  # v2.7: 5.4 (the case model's DECLARED
#   default). _const is a regex over the case source, so it reads the bare
#   `WALL = 5.4` literal — NOT the optional AGENTPAD13_WALL variant override
#   that follows it there. That is intentional and safe: this kit is derived
#   entirely from INNER_*/LEDGE_* (frozen INNER_R 5.6), so it is IDENTICAL for
#   every wall; the wall only picks which band STL the underside is
#   re-measured from, and the release band is the declared default.
OUTER_R = _const("OUTER_R")            # 8.0
BOSS_C = _const("BOSS_C")              # 3.7  corner-boss center on the diagonal
BOSS_OD = _const("BOSS_OD")            # 9.5
SOCKET_SLIP = _const("SOCKET_SLIP")    # 0.25
USB_CUTOUT_W = _const("USB_CUTOUT_W")  # 10.0
PLATE_TOP_TO_PCB = _const("PLATE_TOP_TO_PCB")  # 5.0
PLATE_T = _const("PLATE_T")            # 1.6
BAND_STL = _band_stl_path(WALL)        # v2.6: follows the current WALL

_C = json.load(open(CONTRACT))
PCB_W, PCB_H = _C["outline"]["target_mm"]          # 84.2 x 100.0  [contract]
OCTAGON = [tuple(p) for p in _C["outline"]["chamfer_vertices"]]
USB_X = _C["refs"]["J1"]["x"]                       # 42.1  [contract]

# ---------------------------------------------------------------------------
# 2. DERIVE (identical formulas to the case model) + self-check
# ---------------------------------------------------------------------------
INNER_W = PCB_W + 2 * PCB_CLEARANCE                 # 84.8
INNER_H = PCB_H + 2 * PCB_CLEARANCE                 # 100.6
INNER_R = _const("INNER_R")                         # 5.6 — v2.6: READ, not
#   derived. The case model FROZE INNER_R at 5.6 (it used to be OUTER_R - WALL)
#   precisely so an owner-tunable WALL cannot move the ledge, the plate's R5.4
#   corner or the tray's R5.35 corner. Re-deriving it here from OUTER_R - WALL
#   would break the moment WALL moves, while the ledge itself never does.
CX, CY = PCB_W / 2.0, PCB_H / 2.0                   # 42.1, 50.0
SOCKET_D = BOSS_OD + 2 * SOCKET_SLIP               # 10.0
Z_PLATE_BOT = PLATE_TOP_TO_PCB - PLATE_T           # 3.4  (ledge top / plate seat)
BOSS_CENTERS = [
    (BOSS_C, BOSS_C), (PCB_W - BOSS_C, BOSS_C),
    (BOSS_C, PCB_H - BOSS_C), (PCB_W - BOSS_C, PCB_H - BOSS_C)]

# Ledge ring outlines (board coords, centered CX,CY)
LEDGE_OUT_W, LEDGE_OUT_H, LEDGE_OUT_R = INNER_W, INNER_H, INNER_R
LEDGE_IN_W = INNER_W - 2 * LEDGE_W                  # 82.4
LEDGE_IN_H = INNER_H - 2 * LEDGE_W                  # 98.2
LEDGE_IN_R = INNER_R - LEDGE_W                      # 4.4

# Ledge strip extents on each side (board coords)
LOX0 = CX - INNER_W / 2                             # west outer x  = -0.3
LIX0 = CX - LEDGE_IN_W / 2                          # west inner x  =  0.9
LIX1 = CX + LEDGE_IN_W / 2                          # east inner x  = 83.3
LOX1 = CX + INNER_W / 2                             # east outer x  = 84.5
LOY0 = CY - INNER_H / 2                             # north outer y = -0.3
LIY0 = CY - LEDGE_IN_H / 2                          # north inner y =  0.9
LIY1 = CY + LEDGE_IN_H / 2                          # south inner y = 99.1
LOY1 = CY + INNER_H / 2                             # south outer y = 100.3

# --- self-check against the module's own commented values ---
_chk = {"INNER_W": (INNER_W, 84.8), "INNER_H": (INNER_H, 100.6),
        "INNER_R": (INNER_R, 5.6), "SOCKET_D": (SOCKET_D, 10.0),
        "CX": (CX, 42.1), "CY": (CY, 50.0), "Z_PLATE_BOT": (Z_PLATE_BOT, 3.4),
        "LEDGE_IN_W": (LEDGE_IN_W, 82.4), "LEDGE_IN_H": (LEDGE_IN_H, 98.2),
        "LEDGE_IN_R": (LEDGE_IN_R, 4.4)}
for k, (got, exp) in _chk.items():
    assert abs(got - exp) < 1e-9, f"derive self-check {k}: {got} != {exp}"

# ---------------------------------------------------------------------------
# 3. EMPIRICAL band-STL check (integrity: geometry unchanged, underside flat)
# ---------------------------------------------------------------------------
import hashlib  # noqa: E402
_band = open(BAND_STL, "rb").read()
BAND_MD5 = hashlib.md5(_band).hexdigest()
# v2.6 (2026-07-23): the band md5-INVARIANCE GATE IS RETIRED BY OWNER ORDER.
# PCBWay's 3D-print review flagged the 0.737 corner crescents on
# agentpad13_v2_band_1.6mm.stl (md5 36980cc2ff011dc32d923fb04f7429f7) as "too
# thin, may break"; the owner ordered the sidewall thickened ("increase the
# sidewall thickness by some amount; might even look better thicker — more
# visible diffuser"), which changes the band hash BY DESIGN, and the exact WALL
# is an open aesthetic pick (3.0 shipped / 5.4 / 7.4 under consideration). A
# hash equality test would now fail on every legitimate build, so it is
# replaced by the SEMANTIC gate that actually protects this kit: the ledge ring
# is re-measured from whichever band STL matches the case model's current WALL
# (BAND_STL above) by _slice_underside_flat() below, and the underside must
# still be a flat LEDGE_W run at z = LEDGE_Z0. The v2.6 band is a strict
# superset of the v2.5 band outboard of y = -2.7 (proved: zero volume removed,
# zero volume added into any mating void), so this kit is unchanged-valid.
print(f"[gasket] band STL {os.path.basename(BAND_STL)} md5 {BAND_MD5} "
      f"(WALL {WALL:g}; retired invariance hash "
      f"{BAND_MD5_EXPECT} = the superseded 2.4-wall band — DO NOT PRINT)")


def _slice_underside_flat(axis, val, lo, hi, zref=LEDGE_Z0):
    """Slice the band mesh at plane axis==val; return the flat run (min,max)
    of the OTHER in-plane coord at z==zref, within [lo,hi]. Confirms the ledge
    underside is a flat z=+0.3 face (not a ramp) on the sampled side."""
    n = struct.unpack("<I", _band[80:84])[0]
    tris = struct.iter_unpack("<12fH", _band[84:84 + n * 50])
    other = 2 if axis == 0 else (2 if axis == 1 else 1)  # in-plane non-z coord
    coord = 0 if axis != 0 else 1
    hits = []
    for t in tris:
        v = [(t[3 + 3 * i], t[4 + 3 * i], t[5 + 3 * i]) for i in range(3)]
        d = [v[i][axis] - val for i in range(3)]
        cr = []
        for a in range(3):
            b = (a + 1) % 3
            if (d[a] > 0) != (d[b] > 0) and d[a] != d[b]:
                s = d[a] / (d[a] - d[b])
                cr.append([v[a][j] + s * (v[b][j] - v[a][j]) for j in range(3)])
        if len(cr) == 2:
            for p in cr:
                if abs(p[2] - zref) < 0.02 and lo <= p[coord] <= hi:
                    hits.append(p[coord])
    return (min(hits), max(hits)) if hits else None


_w = _slice_underside_flat(1, 50.0, LOX0 - 0.1, LIX0 + 0.1)   # west, at y=50
assert _w and abs(_w[0] - LOX0) < 0.05 and abs(_w[1] - LIX0) < 0.05, (
    f"west ledge underside flat run {_w} != expected [{LOX0},{LIX0}]")

# ---------------------------------------------------------------------------
# 4. SEGMENT LAYOUT (8-12 x ~15 mm, clear of corner caps + USB)
# ---------------------------------------------------------------------------
SEG_LEN = 15.0                       # segment length along the edge
SEG_W = LEDGE_W                      # 1.2  (spans the ledge width; trim ok)
USB_MARGIN = 1.0                     # extra clearance past the USB aperture span

# Clear runs (corner keep-out = BOSS_CENTERS +/- SOCKET_D per the brief)
CLR_Y0 = BOSS_C + SOCKET_D                       # 13.7
CLR_Y1 = (PCB_H - BOSS_C) - SOCKET_D             # 86.3
CLR_X0 = BOSS_C + SOCKET_D                       # 13.7
CLR_X1 = (PCB_W - BOSS_C) - SOCKET_D             # 70.5
USB_LO = USB_X - USB_CUTOUT_W / 2 - USB_MARGIN   # 36.1
USB_HI = USB_X + USB_CUTOUT_W / 2 + USB_MARGIN   # 48.1

WEST_X = (LOX0 + LIX0) / 2           # 0.3   strip centre (x)
EAST_X = (LIX1 + LOX1) / 2           # 83.9
NORTH_Y = (LOY0 + LIY0) / 2          # 0.3   strip centre (y)
SOUTH_Y = (LIY1 + LOY1) / 2          # 99.7

# long sides (100 mm): 3 segments each at y = 25, 50, 75
LONG_YC = [25.0, 50.0, 75.0]
# short sides (84 mm): 2 segments each, one either side of the board centre;
# on NORTH they must also clear the USB span -> symmetric centres 24.9 / 59.3
SHORT_XC = [round((CLR_X0 + USB_LO) / 2, 2), round((USB_HI + CLR_X1) / 2, 2)]

# Segment = (cx, cy, w, h, side, label). w,h in board axes.
SEGMENTS = []
for yc in LONG_YC:
    SEGMENTS.append((WEST_X, yc, SEG_W, SEG_LEN, "W"))
    SEGMENTS.append((EAST_X, yc, SEG_W, SEG_LEN, "E"))
for xc in SHORT_XC:
    SEGMENTS.append((xc, NORTH_Y, SEG_LEN, SEG_W, "N"))
    SEGMENTS.append((xc, SOUTH_Y, SEG_LEN, SEG_W, "S"))

# --- clearance asserts (assert -> emit -> assert) ---
for (cx, cy, w, h, side) in SEGMENTS:
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    if side in ("W", "E"):
        assert CLR_Y0 - 1e-6 <= y0 and y1 <= CLR_Y1 + 1e-6, (side, cy)
    else:
        assert CLR_X0 - 1e-6 <= x0 and x1 <= CLR_X1 + 1e-6, (side, cx)
        if side == "N":
            assert x1 <= USB_LO + 1e-6 or x0 >= USB_HI - 1e-6, (side, cx)
    # every segment must sit inside the ledge strip footprint
    if side == "W":
        assert LOX0 - 1e-6 <= x0 and x1 <= LIX0 + 1e-6
    if side == "E":
        assert LIX1 - 1e-6 <= x0 and x1 <= LOX1 + 1e-6
    if side == "N":
        assert LOY0 - 1e-6 <= y0 and y1 <= LIY0 + 1e-6
    if side == "S":
        assert LIY1 - 1e-6 <= y0 and y1 <= LOY1 + 1e-6

N_SEG = len(SEGMENTS)
assert 8 <= N_SEG <= 12, f"segment count {N_SEG} outside 8..12"
FOAM_AREA = N_SEG * SEG_LEN * SEG_W                 # mm^2
COMPRESSION = (0.5 - LEDGE_Z0) / 0.5               # 0.5 mm foam into 0.3 gap

# ---------------------------------------------------------------------------
# 5. SVG  (1:1: width/height in mm == viewBox units -> 1 unit = 1 mm)
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = 190.0, 250.0        # fits A4 & US-Letter portrait at 100%
OFF_X = PAGE_W / 2 - CX              # centre the board horizontally
OFF_Y = 55.3 - LOY0                  # board top rim near y=55


def PX(bx):
    return bx + OFF_X


def PY(by):
    return by + OFF_Y


def rrect(x, y, w, h, r, **kw):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return (f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" '
            f'height="{h:.3f}" rx="{r:.3f}" ry="{r:.3f}" {a}/>')


def text(x, y, s, size=2.6, anchor="start", weight="normal", fill="#222"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" '
            f'font-family="DejaVu Sans, Arial, sans-serif" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'fill="{fill}">{s}</text>')


el = []
el.append(f'<rect x="0" y="0" width="{PAGE_W}" height="{PAGE_H}" fill="#ffffff"/>')

# --- title block ---
el.append(text(PAGE_W / 2, 12, "agentpad13 v2 — optional PORON ledge-gasket kit",
               size=4.6, anchor="middle", weight="bold", fill="#111"))
el.append(text(PAGE_W / 2, 18.5,
               "1:1 cutting template &#183; derived from band rabbet-ledge "
               "constants &#183; NO geometry change",
               size=2.5, anchor="middle", fill="#555"))
el.append(text(PAGE_W / 2, 24.8,
               f"Material: 0.5 mm PORON foam, 3M 468/9471-class adhesive back "
               f"&#183; {N_SEG} segments &#183; {SEG_LEN:g} &#215; {SEG_W:g} mm each",
               size=2.5, anchor="middle", fill="#555"))
el.append(text(PAGE_W / 2, 30.6,
               f"Stick to the BAND ledge underside (z +{LEDGE_Z0:g}); 0.5 into "
               f"{LEDGE_Z0:g} = {COMPRESSION * 100:.0f}% compression (PORON 20-50% band). "
               f"OPTIONAL — bare ledge is already the {LEDGE_Z0:g} mm backstop.",
               size=2.3, anchor="middle", fill="#777"))

# --- board octagon outline (very light dashed, context) ---
pth = "M " + " L ".join(f"{PX(x):.3f} {PY(y):.3f}" for x, y in OCTAGON) + " Z"
el.append(f'<path d="{pth}" fill="none" stroke="#d9d9d9" '
          f'stroke-width="0.18" stroke-dasharray="1.6 1.6"/>')

# --- ledge ring outlines (reference, light) ---
el.append(rrect(PX(LOX0), PY(LOY0), LEDGE_OUT_W, LEDGE_OUT_H, LEDGE_OUT_R,
                fill="none", stroke="#8a8a8a", stroke_width="0.22"))
el.append(rrect(PX(CX - LEDGE_IN_W / 2), PY(CY - LEDGE_IN_H / 2),
                LEDGE_IN_W, LEDGE_IN_H, LEDGE_IN_R,
                fill="none", stroke="#8a8a8a", stroke_width="0.22"))

# --- corner-cap / socket keep-out circles (light dashed) ---
for (bx, by) in BOSS_CENTERS:
    el.append(f'<circle cx="{PX(bx):.3f}" cy="{PY(by):.3f}" r="{SOCKET_D:.3f}" '
              f'fill="#f4e4e4" fill-opacity="0.5" stroke="#c98a8a" '
              f'stroke-width="0.16" stroke-dasharray="0.9 0.9"/>')
    el.append(f'<path d="M {PX(bx) - 1.4:.2f} {PY(by):.2f} h 2.8 M {PX(bx):.2f} '
              f'{PY(by) - 1.4:.2f} v 2.8" stroke="#c98a8a" stroke-width="0.16"/>')

# --- USB keep-out zone on the north edge (light dashed) ---
el.append(f'<rect x="{PX(USB_LO):.3f}" y="{PY(LOY0) - 3:.3f}" '
          f'width="{USB_HI - USB_LO:.3f}" height="{(LIY0 - LOY0) + 3:.3f}" '
          f'fill="#e4ecf4" fill-opacity="0.6" stroke="#8aa8c9" '
          f'stroke-width="0.16" stroke-dasharray="0.9 0.9"/>')
el.append(text(PX(USB_X), PY(LOY0) - 4.2, "USB &#8212; skip",
               size=2.0, anchor="middle", fill="#5f7fa0"))

# --- segment cut rectangles (SOLID cut lines) ---
for (cx, cy, w, h, side) in SEGMENTS:
    el.append(f'<rect x="{PX(cx - w / 2):.3f}" y="{PY(cy - h / 2):.3f}" '
              f'width="{w:.3f}" height="{h:.3f}" rx="0.3" '
              f'fill="#ffdccf" stroke="#b3300a" stroke-width="0.4"/>')

# --- side count labels ---
el.append(text(PX(LOX0) - 3, PY(CY), "W&#215;3", size=2.6, anchor="end",
               weight="bold", fill="#b3300a"))
el.append(text(PX(LOX1) + 3, PY(CY), "E&#215;3", size=2.6, anchor="start",
               weight="bold", fill="#b3300a"))
el.append(text(PX(CX), PY(LOY1) + 5, "S&#215;2", size=2.6, anchor="middle",
               weight="bold", fill="#b3300a"))
el.append(text(PX(CX), PY(LOY0) - 7.5, "N&#215;2", size=2.6, anchor="middle",
               weight="bold", fill="#b3300a"))

# --- one dimensioned segment (west middle) ---
wseg = [s for s in SEGMENTS if s[4] == "W" and abs(s[1] - 50) < 1e-6][0]
wx, wy = wseg[0], wseg[1]
el.append(text(PX(wx) + 3.0, PY(wy) - 2, f"{SEG_LEN:g} mm", size=2.2,
               anchor="start", fill="#333"))
el.append(text(PX(wx) + 3.0, PY(wy) + 1, f"&#215; {SEG_W:g} mm", size=2.2,
               anchor="start", fill="#333"))

# --- scale bar (exactly 50 mm) ---
sb_x, sb_y, sb_len = 22.0, 205.0, 50.0
el.append(f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x + sb_len}" y2="{sb_y}" '
          f'stroke="#111" stroke-width="0.5"/>')
for t in range(0, 6):
    xx = sb_x + t * 10
    el.append(f'<line x1="{xx}" y1="{sb_y}" x2="{xx}" y2="{sb_y - 2.4}" '
              f'stroke="#111" stroke-width="0.4"/>')
    el.append(text(xx, sb_y - 3.2, f"{t * 10}", size=2.1, anchor="middle",
                   fill="#111"))
el.append(text(sb_x, sb_y + 4.4, "50 mm scale bar", size=2.4, anchor="start",
               weight="bold", fill="#111"))
el.append(text(sb_x, sb_y + 8.4,
               "PRINT AT 100% / ACTUAL SIZE (no 'fit to page'/'shrink to fit'). "
               "Then measure this bar &#8212; it MUST read 50 mm.",
               size=2.3, anchor="start", fill="#b3300a"))

# --- legend / instructions block ---
ly = 222.0
lines = [
    ("Legend:", "bold", "#111"),
    ("  solid red rect = CUT LINE (0.5 mm PORON segment, adhesive side down)",
     "normal", "#b3300a"),
    ("  grey outline = band ledge ring (reference)   grey dashed = board edge",
     "normal", "#666"),
    ("  pink circle = corner-cap / socket keep-out   blue = USB aperture keep-out",
     "normal", "#666"),
    (f"  {N_SEG} segments: W&#215;3 E&#215;3 (y 25/50/75) + N&#215;2 S&#215;2 "
     f"(x {SHORT_XC[0]:g}/{SHORT_XC[1]:g}); ~{FOAM_AREA:.0f} mm&#178; foam total.",
     "normal", "#333"),
]
for i, (s, wt, fl) in enumerate(lines):
    el.append(text(sb_x, ly + i * 4.2, s, size=2.3, weight=wt, fill=fl))

svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" '
       f'width="{PAGE_W}mm" height="{PAGE_H}mm" '
       f'viewBox="0 0 {PAGE_W:g} {PAGE_H:g}">\n'
       + "\n".join(el) + "\n</svg>\n")

SVG_PATH = os.path.join(HERE, "gasket_template.svg")
open(SVG_PATH, "w").write(svg)
print(f"[svg]  {SVG_PATH}  page {PAGE_W:g}x{PAGE_H:g} mm (1 unit = 1 mm)")

# ---------------------------------------------------------------------------
# 6. DXF  (cut rectangles only, mm units, closed polylines)
# ---------------------------------------------------------------------------
import ezdxf  # noqa: E402

doc = ezdxf.new("R2000")
doc.units = ezdxf.units.MM          # $INSUNITS = 4 (millimetres)
doc.header["$MEASUREMENT"] = 1       # metric
msp = doc.modelspace()
# CAD is Y-up; flip the board's Y-down layout so the DXF map reads like the SVG,
# then shift into the positive quadrant with a 10 mm margin.
DXF_MARGIN = 10.0
for (cx, cy, w, h, side) in SEGMENTS:
    x0, x1 = cx - w / 2 + DXF_MARGIN, cx + w / 2 + DXF_MARGIN
    yd0 = (LOY1 - (cy + h / 2)) + DXF_MARGIN      # flip Y
    yd1 = (LOY1 - (cy - h / 2)) + DXF_MARGIN
    msp.add_lwpolyline([(x0, yd0), (x1, yd0), (x1, yd1), (x0, yd1)],
                       close=True, dxfattribs={"layer": "GASKET_CUT"})
DXF_PATH = os.path.join(HERE, "gasket_segments.dxf")
doc.saveas(DXF_PATH)
_aud = doc.audit()
assert len(_aud.errors) == 0, f"DXF audit errors: {_aud.errors}"
assert len(list(msp.query("LWPOLYLINE"))) == N_SEG
print(f"[dxf]  {DXF_PATH}  {N_SEG} closed rects, mm units, audit clean")

# ---------------------------------------------------------------------------
# 7. PDF + PNG via inkscape, then verify PDF is exactly 1:1
# ---------------------------------------------------------------------------
PDF_PATH = os.path.join(HERE, "gasket_template.pdf")
PNG_PATH = os.path.join(HERE, "gasket_template.png")
INK = "inkscape"


def _ink(*args):
    subprocess.run([INK, *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if "--no-render" not in sys.argv:
    _ink(SVG_PATH, "--export-type=pdf", f"--export-filename={PDF_PATH}")
    _ink(SVG_PATH, "--export-type=png", f"--export-filename={PNG_PATH}",
         "--export-dpi=200", "--export-background=white")
    print(f"[pdf]  {PDF_PATH}")
    print(f"[png]  {PNG_PATH}")

    # verify PDF page box is exactly PAGE_W x PAGE_H mm (1:1 guarantee)
    import fitz  # PyMuPDF
    d = fitz.open(PDF_PATH)
    r = d[0].rect                    # points (1 pt = 1/72 inch)
    w_mm = r.width * 25.4 / 72.0
    h_mm = r.height * 25.4 / 72.0
    d.close()
    ok = abs(w_mm - PAGE_W) < 0.3 and abs(h_mm - PAGE_H) < 0.3
    print(f"[verify] PDF MediaBox = {w_mm:.3f} x {h_mm:.3f} mm "
          f"(target {PAGE_W:g} x {PAGE_H:g}) -> {'1:1 OK' if ok else 'FAIL'}")
    assert ok, "PDF page not 1:1"

# ---------------------------------------------------------------------------
# 8. summary
# ---------------------------------------------------------------------------
print("\n=== LEDGE / GASKET DERIVATION SUMMARY ===")
print(f"band STL md5           : {BAND_MD5}  ({os.path.basename(BAND_STL)}; "
      f"the {BAND_MD5_EXPECT} invariance gate is RETIRED — owner order "
      "2026-07-23, PCBWay thin-wall EQ)")
print(f"ledge outer outline    : {LEDGE_OUT_W:g} x {LEDGE_OUT_H:g} mm, "
      f"R{LEDGE_OUT_R:g}  (band inner wall INNER_W/H/R)")
print(f"ledge inner outline    : {LEDGE_IN_W:g} x {LEDGE_IN_H:g} mm, "
      f"R{LEDGE_IN_R:g}  (INNER_-2*LEDGE_W)")
print(f"ledge width / underside: {LEDGE_W:g} mm @ z +{LEDGE_Z0:g}")
print(f"board / overhang       : {PCB_W:g} x {PCB_H:g}; ledge overhangs the "
      f"board rim by {LIX0:g} mm (= LEDGE_W - PCB_CLEARANCE)")
print(f"west underside flat run: x [{_w[0]:.3f}, {_w[1]:.3f}] @ z {LEDGE_Z0:g} "
      f"(STL-measured; flat, not ramped)")
print(f"clear runs             : long y [{CLR_Y0:g},{CLR_Y1:g}]  "
      f"short x [{CLR_X0:g},{CLR_X1:g}]  USB skip x [{USB_LO:g},{USB_HI:g}]")
print(f"segments ({N_SEG})          : {SEG_LEN:g} x {SEG_W:g} mm; "
      f"foam total {FOAM_AREA:.0f} mm^2; compression {COMPRESSION * 100:.0f}%")
for side in ("W", "E", "N", "S"):
    pos = [f"({s[0]:g},{s[1]:g})" for s in SEGMENTS if s[4] == side]
    print(f"   {side} x{len(pos)}: " + "  ".join(pos))

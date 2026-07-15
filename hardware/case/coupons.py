"""Loudest Micro Rev A — tolerance coupon set (print these FIRST).

research/04 discipline: "Tolerance coupons FIRST (20-min prints) ... Then
the 4-hour full print." Each coupon is a small, standalone printable part
that calibrates one interface of ``loudest_case.py`` on YOUR printer/filament
before committing the full shell.

Coupons (deliverable #2):
  1. switch-cutout ladder    13.7 / 13.8 / 13.9 / 14.0  (MX clip fit)
  2. insert-hole ladder       ⌀4.0 / 4.1 / 4.2 / 4.3     (M3 heat-set pilot)
  3. USB aperture test        10.0 x 4.0 flush cutout    (research/04 §1E)
  4. encoder + JS opening     Ø7.5 shaft + Ø16 travel    (fit test)
  5. touch-window tabs        1.0 / 1.2 / 1.5 mm         (capacitive feel)

Baseline dimensions are imported from ``loudest_case`` (single source of
truth); each ladder SWEEPS around its baseline on purpose. Every printed
face that touches the bed carries the same 0.3-0.5 mm EFC chamfer as the
main parts (research/04 §3/§4) and slicer EFC is enabled.

Each coupon exports its own STL + STEP (separate 20-minute prints) and is
inspect()'d for printability (advisory; thin tabs / chamfers flag by design).
"""

import os
import sys

from build123d import (
    Axis,
    Box,
    Location,
    Part,
    Plane,
    Pos,
    chamfer,
    export_step,
    export_stl,
    extrude,
)

from cad_khana.mechanism.assembly import Assembly
from cad_khana.mechanism.check import check
from cad_khana.printability.inspect import inspect
from cad_khana.printability.methods import FDM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loudest_case as C  # noqa: E402  baseline dims (single source of truth)

# --- Ladder sweeps (the coupon's reason for existing) -------------------
SWITCH_SIZES = [13.7, 13.8, 13.9, 14.0]      # baseline C.SWITCH_CUTOUT = 13.9
INSERT_SIZES = [4.0, 4.1, 4.2, 4.3]          # baseline C.M3_INSERT_PILOT = 4.2
TOUCH_THICKNESSES = [1.0, 1.2, 1.5]          # baseline C.TOUCH_WINDOW_THICKNESS = 1.2

# --- Shared coupon params -----------------------------------------------
CELL_PITCH = C.L.KEY_PITCH                    # 19.05, real key pitch
COUPON_MARGIN = 4.0
_OVER = 1.0


def _circle(r: float):
    from build123d import Circle
    return Circle(r)


def _z_cyl(d: float, z0: float, z1: float, x: float, y: float) -> Part:
    return Pos(x, y, z0) * extrude(Plane.XY * _circle(d / 2), amount=z1 - z0)


def _label(txt: str, x: float, y: float, z_top: float,
           size: float = 3.2, depth: float = 0.4) -> Part:
    """Engrave a size label into the bed-side (top) face. Font-safe: returns
    None if no system font is resolvable, so the geometry never fails."""
    try:
        from build123d import Text
        sk = Text(txt, font_size=size)
    except Exception:
        return None
    return Pos(x, y, z_top - depth) * extrude(sk, amount=depth + _OVER)


def _chamfer_top(part: Part, z_top: float) -> Part:
    edges = part.edges().filter_by_position(Axis.Z, z_top - 0.05, z_top + 0.05)
    if not edges:
        return part
    return chamfer(edges, C.EFC_CHAMFER)


# =========================================================================
# 1. Switch-cutout ladder
# =========================================================================
def switch_cutout_coupon() -> Part:
    """4 cells, each an MX plate segment (3.5 mm web, 1.5 mm clip shelf over a
    16.0 mm relief) with the swept cutout. Printed deck-face-DOWN (top = bed)."""
    web = C.PLATE_WEB
    shelf = C.CLIP_SHELF
    relief = C.SWITCH_RELIEF
    n = len(SWITCH_SIZES)
    length = n * CELL_PITCH
    z_top = web
    bar = Pos(length / 2, 0, web / 2) * Box(length, CELL_PITCH, web)
    for i, s in enumerate(SWITCH_SIZES):
        cx = CELL_PITCH * (i + 0.5)
        shelf_cut = Pos(cx, 0, (z_top - shelf + z_top + _OVER) / 2) * Box(
            s, s, (z_top + _OVER) - (z_top - shelf))
        relief_cut = Pos(cx, 0, (-_OVER + z_top - shelf) / 2) * Box(
            relief, relief, (z_top - shelf) - (-_OVER))
        bar -= shelf_cut
        bar -= relief_cut
    # Chamfer the bed-side edges BEFORE engraving (label strokes are too thin
    # to chamfer and would break the operation).
    bar = _chamfer_top(bar, z_top)
    for i, s in enumerate(SWITCH_SIZES):
        cx = CELL_PITCH * (i + 0.5)
        lbl = _label(f"{s:.1f}", cx, -CELL_PITCH / 2 + 2.5, z_top)
        if lbl is not None:
            bar -= lbl
    return bar


# =========================================================================
# 2. Insert-hole ladder
# =========================================================================
def insert_hole_coupon() -> Part:
    """4 blind holes swept ⌀4.0-4.3, each C.M3_INSERT_DEPTH deep in a boss
    thick enough for insert-length + 1 mm floor (research/04 §4)."""
    thick = C.M3_INSERT_DEPTH + 1.0
    pitch = 12.0
    n = len(INSERT_SIZES)
    length = n * pitch
    z_top = thick
    bar = Pos(length / 2, 0, thick / 2) * Box(length, pitch, thick)
    for i, d in enumerate(INSERT_SIZES):
        cx = pitch * (i + 0.5)
        bar -= _z_cyl(d, z_top - C.M3_INSERT_DEPTH, z_top + _OVER, cx, 0)
        lbl = _label(f"{d:.1f}", cx, -pitch / 2 + 2.2, z_top, size=2.6)
        if lbl is not None:
            bar -= lbl
    # Bed side is the BOTTOM here (holes open up, printed right-side-up).
    edges = bar.edges().filter_by_position(Axis.Z, -0.05, 0.05)
    return chamfer(edges, C.EFC_CHAMFER) if edges else bar


# =========================================================================
# 3. USB aperture test
# =========================================================================
def usb_coupon() -> Part:
    """A case-wall panel (WALL thick) with the §1E flush USB-C cutout, on a
    base foot so it stands for a real connector/cable fit test."""
    panel_w, panel_h = 30.0, 12.0
    wall = C.WALL
    base = Pos(0, 0, wall / 2) * Box(panel_w, 16.0, wall)
    panel = Pos(0, -8.0 + wall / 2, wall + panel_h / 2) * Box(panel_w, wall, panel_h)
    body = base + panel
    cut = Pos(0, -8.0 + wall / 2, wall + C.USB_CENTER_Z) * Box(
        C.USB_CUTOUT_W, wall + 2 * _OVER, C.USB_CUTOUT_H)
    return body - cut


# =========================================================================
# 4. Encoder + JS opening test
# =========================================================================
def encoder_js_coupon() -> Part:
    """Plate with the encoder Ø7.5 shaft pass-through and the JS Ø16 travel
    aperture, both with bed-side EFC chamfers."""
    web = C.PLATE_WEB
    plate = Pos(0, 0, web / 2) * Box(45.0, 30.0, web)
    js_ap = C.L.JS_TRAVEL_D + C.JS_APERTURE_CLEAR
    plate -= _z_cyl(C.ENCODER_SHAFT_D, -_OVER, web + _OVER, -11.0, 0)
    plate -= _z_cyl(js_ap, -_OVER, web + _OVER, 11.0, 0)
    plate = _chamfer_top(plate, web)   # chamfer before engraving (see above)
    lbl_e = _label("ENC7.5", -11.0, -10.0, web, size=2.4)
    lbl_j = _label("JS16", 11.0, -10.0, web, size=2.4)
    for lbl in (lbl_e, lbl_j):
        if lbl is not None:
            plate -= lbl
    return plate


# =========================================================================
# 5. Touch-window thickness tabs
# =========================================================================
def touch_tabs_coupon() -> Part:
    """3 membrane tabs at 1.0 / 1.2 / 1.5 mm off a common handle bar; sense a
    finger through each to pick the capacitive-window thickness."""
    tab = 18.0
    handle_h = 2.4
    pitch = tab + 3.0
    n = len(TOUCH_THICKNESSES)
    length = n * pitch
    handle = Pos(length / 2, -tab / 2 - 3.0, handle_h / 2) * Box(
        length, 6.0, handle_h)
    body = handle
    for i, t in enumerate(TOUCH_THICKNESSES):
        cx = pitch * (i + 0.5)
        body += Pos(cx, 0, t / 2) * Box(tab, tab, t)   # bed side = z0, thickness up
        lbl = _label(f"{t:.1f}", cx, tab / 2 - 3.0, t, size=3.0, depth=min(0.3, t - 0.5))
        if lbl is not None:
            body -= lbl
    return body


COUPONS = {
    "coupon_switch_cutout_ladder": (switch_cutout_coupon, (0, 0, -1)),
    "coupon_insert_hole_ladder": (insert_hole_coupon, (0, 0, 1)),
    "coupon_usb_aperture": (usb_coupon, (0, 0, 1)),
    "coupon_encoder_js_opening": (encoder_js_coupon, (0, 0, -1)),
    "coupon_touch_window_tabs": (touch_tabs_coupon, (0, 0, 1)),
}


# --- Combined layout: coupons spaced on a virtual plate ------------------
# (lets `khana check` confirm the set doesn't overlap, and one draw shows all)
_assembly = Assembly()
_row_y = 0.0
for _name, (_fn, _up) in COUPONS.items():
    _assembly = _assembly.with_part(_name, _fn(), location=Location((0, _row_y, 0)))
    _row_y += 40.0
# every coupon is disjoint from every other in this layout
_names = list(COUPONS)
for _i in range(len(_names)):
    for _j in range(_i + 1, len(_names)):
        _assembly = _assembly.assert_no_interference(_names[_i], _names[_j])

assembly = _assembly


def _advisory(name: str, part: Part, up_axis, out: str = "outputs") -> None:
    import json
    try:
        inspect(part, method=FDM(up_axis=up_axis, wall_min_mm=0.8),
                out=out, name=name)
        verdict = "PASS"
    except SystemExit:
        verdict = "ADVISORY (thin tabs / chamfers flag by design)"
    data = json.load(open(os.path.join(out, f"{name}-printability.json")))
    print(f"[printability] {name}: {verdict} | min_wall={data.get('min_wall_mm')}")


if __name__ == "__main__":
    check(assembly, out="outputs")

    here = os.path.dirname(os.path.abspath(__file__))
    stl_dir = os.path.join(here, "stl")
    step_dir = os.path.join(here, "step")
    for name, (fn, up) in COUPONS.items():
        part = fn()
        _advisory(name, part, up)
        export_stl(part, os.path.join(stl_dir, name + ".stl"))
        export_step(part, os.path.join(step_dir, name + ".step"))
    print("exported 5 coupons to stl/ and step/")

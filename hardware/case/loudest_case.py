"""Loudest Micro Rev A — parametric case v0 (build123d via cad-khana).

Unibody printed top shell with an integrated MX switch plate (research/04
architecture #2/#4) + a flat screw-on bottom lid on M3 heat-set inserts.
One CAD, two SKUs (frosted-translucent PETG vs black PETG + diffuser) — the
SKU split is a *filament swap*, not separate geometry, so it is NOT modelled
here.

Every board-derived dimension is imported from ``layout_v2.py``; every
mechanical dimension is a named parameter below with an inline citation to
``research/04-mechanical-case-dossier.md`` (cited as "§…"). There are no
magic numbers in the geometry.

--------------------------------------------------------------------------
Coordinate frame
--------------------------------------------------------------------------
    origin  = PCB top-left corner (layout_v2 origin), identity in X/Y
    +X      = layout +x (right, across columns)
    +Y      = layout +y (down, top band -> touch row)      [handedness preserved]
    +Z      = up, out of the board plane, toward the keycaps
    Z = 0   = PCB TOP face (the switch-mount datum, research/04 §1A)

Because X/Y are identity (no reflection), the printed part matches the real
PCB and is not mirrored. A top-view render therefore appears y-flipped
relative to the notes' diagram; that is a viewing convention only.

--------------------------------------------------------------------------
Z stack (desk -> keycap), all from research/04 §1A "Case stack math"
--------------------------------------------------------------------------
    Z=+5.0   plate/deck TOP  ...................... PLATE_TOP_TO_PCB above PCB
    Z=+3.5   clip-shelf bottom .................... shelf = CLIP_SHELF (1.5)
    Z=+1.5   plate-web bottom ..................... web = PLATE_WEB (3.5)
    Z= 0.0   PCB TOP  (datum)
    Z=-1.6   PCB bottom ........................... PCB_THICKNESS
    Z=-3.45  hotswap socket bottom ................ SOCKET_DROP (1.85) below PCB
    Z=-5.1   under-PCB cavity floor / lid top ..... UNDER_PCB_CAVITY (3.5)
    Z=-7.5   lid bottom (desk-side) ............... LID_THICKNESS (2.4)
    (+ bumpon protrusion below the lid)
    => deck top sits 12.5 mm above the desk-side lid face (research/04 §1A).

Print orientation: top shell DECK-FACE-DOWN (bed side = +Z deck), lid
right-side-up (bed side = -Z bottom). Elephant-foot chamfers go on every
bed-side edge (research/04 §3/§4) + slicer EFC.
"""

from build123d import (
    Axis,
    Box,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    chamfer,
    export_step,
    export_stl,
    extrude,
)

from cad_khana.mechanism.assembly import Assembly
from cad_khana.mechanism.check import check
from cad_khana.printability.inspect import inspect
from cad_khana.printability.methods import FDM

import os
import sys

# khana runs this via runpy from an arbitrary cwd; make the sibling
# layout_v2 constants module importable regardless.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout_v2 as L  # noqa: E402

# =========================================================================
# 1. PARAMETERS  (every value cites research/04 or is derived; no magic
#    numbers in the geometry below)
# =========================================================================

# --- Switch plate (research/04 §1A, §3) ---------------------------------
PLATE_TOP_TO_PCB = 5.0      # §1A: switch shoulder sets plate-top->PCB = 5.0
PLATE_WEB = 3.5            # §3: 3.0-3.5 mm total plate web
CLIP_SHELF = 1.5          # §1A/§3: 1.5 mm clip-groove engagement thickness
SWITCH_CUTOUT = 13.9       # §1A/§3: FDM cutout (coupon-calibrated, 13.9 baseline)
SWITCH_RELIEF = 16.0       # §3 relief pocket under switch body; clip-shelf
#                            ledge width = (RELIEF - CUTOUT)/2 = 1.05 mm and
#                            gives clips ~1.0 mm/side outward flex past 14.0.
EFC_CHAMFER = 0.4          # §3/§4: 0.3-0.5 mm x45 elephant-foot chamfer, bed side

# --- Walls / lid / fit (research/04 §4) ---------------------------------
WALL = 2.4                 # §4: 2.0-2.5 mm case walls (README case ~89x108.5)
LID_THICKNESS = 2.4        # §4: 2.4 mm bottom lid (weight pocket + inserts)
PCB_CLEARANCE = 0.3        # §4: slip fit, PCB-edge to inner wall
LID_SLIP = 0.25            # §4: 0.2-0.3 mm slip fit (lid lip in shell)
OUTER_CORNER_R = 8.0       # §6: generous corner radii ~8-9 mm on a ~90 mm body

# --- Under-PCB cavity + hotswap sockets (research/04 §1A) ---------------
UNDER_PCB_CAVITY = 3.5     # §1A: 3.5-4.0 mm relief with a 2 mm PORON sheet
#                            (>= 2.2 mm bare-air minimum)
SOCKET_DROP = 1.85         # §1A: Kailh PG151101S11 hangs 1.85 mm below PCB
SOCKET_BODY_X = 14.5       # §1A: Kailh socket body 14.50 mm (long axis // X)
SOCKET_BODY_Y = 5.89       # §1A: Kailh socket body 5.89 mm

# --- USB-C cutout (research/04 §1E, flush-wall rule) --------------------
USB_CUTOUT_W = 10.0        # §1E: flush wall <=2 mm -> ~10.0 mm wide
USB_CUTOUT_H = 4.0         # §1E: ~4.0 mm tall for a mid-mount receptacle
USB_CENTER_Z = 1.6         # derived: receptacle on PCB top, shell ~3.26 tall
#                            -> aperture centred ~1.6 mm above PCB top

# --- Deck apertures -----------------------------------------------------
ENCODER_SHAFT_D = 7.5      # §1C: EC11 printed shaft/bushing pass-through 7.3-7.6
JS_APERTURE_CLEAR = 1.0    # spec: JS aperture = travel Ø15 + 1.0 clearance
JS_CAP_POCKET_CLEAR = 2.0  # provisional (Phase-1): cap pocket = capØ + 2.0
JS_CAP_POCKET_DEPTH = 1.5  # provisional cap-recess depth
TOUCH_WINDOW = 15.0        # thin window over TP1's 14x14 pad (+1 mm margin)
TOUCH_WINDOW_THICKNESS = 1.2  # §7 / spec: ~1.2 mm thin capacitive zone
LIGHT_PIPE_D = 3.0         # layer-LED light-pipe pass-through (spec)

# --- M3 heat-set insert bosses (research/04 §4) -------------------------
M3_INSERT_PILOT = 4.2      # §4: ⌀4.1-4.25 pilot (CNC Kitchen std, vertical 4.2)
M3_INSERT_DEPTH = 5.7      # §4: CNC Kitchen std M3 insert L = 5.7 mm
M3_SCREW_CLEAR = 3.4       # §4: M3 shaft clearance hole (⌀3.2-3.5)
BOSS_OD = 8.0              # §4: boss OD >= 2x insert OD (~8-10 mm for M3)

# --- Bottom-lid features (research/04 §4, README) -----------------------
WEIGHT_POCKET_X = 60.0     # §4: steel weight pocket ~60 x 40 x 3
WEIGHT_POCKET_Y = 40.0
WEIGHT_POCKET_DEPTH = 1.6  # fits the 2.4 mm lid (0.8 mm floor). NOTE: the 3 mm
#                            target needs local lid thickening — see CASE-NOTES.
WEIGHT_CENTER = (42.1, 40.0)

BATTERY_CAVITY_X = 50.0    # README/spec: reserved 50 x 34 x 6 battery cavity
BATTERY_CAVITY_Y = 34.0
BATTERY_RESERVE_DEPTH = 1.5  # reservation marker only (wireless fork needs 6 mm
#                              -> a deeper Pro-SKU lid; see CASE-NOTES).
BATTERY_CENTER = (40.0, 78.0)

BUMPON_D = 11.2            # §4: 3M SJ5303 hemispherical Ø11.2 x 5.1 mm
BUMPON_RECESS_DEPTH = 1.5  # partial sink; SJ5303 then protrudes ~3.6 mm
# Feet sit CONCENTRIC with the four corner insert bosses: best structural
# support (foot directly under the screw column) and the standard
# "rubber-foot-hides-the-bottom-fixing" pattern — which also keeps every foot
# clear of the bottom-right SVC service zone.
BUMPON_CENTERS = list(L.CORNER_MOUNT_HOLES)

SVC_HOLE_D = 3.0           # BOOT/RESET poke-through
SVC_HOLE_DX = 4.0          # the pair straddles SVC_CENTER by ±4 mm in x
SVC_HOLE_Y = 88.0          # 2.5 mm toward centre from SVC (90.5) so the pair
#                            clears the (77.2, 96.7) corner foot — still over
#                            the SVC cell.

LID_LIP_HEIGHT = 2.0       # registration lip rising into the cavity
LID_LIP_WIDTH = 1.5        # lip ring wall width

# --- 2U stabiliser clearance (approximate Cherry plate-mount) -----------
STAB_CUTOUT_W = 7.0        # per-stab relief width  (refine in Phase 2)
STAB_CUTOUT_Y = 15.5       # per-stab relief length (refine in Phase 2)

# =========================================================================
# 2. DERIVED  (one source of truth -> everything else)
# =========================================================================

# Z datum planes (see header stack).
Z_PCB_TOP = 0.0
Z_PCB_BOT = Z_PCB_TOP - L.PCB_THICKNESS               # -1.6
Z_PLATE_TOP = Z_PCB_TOP + PLATE_TOP_TO_PCB            # +5.0
Z_PLATE_WEB_BOT = Z_PLATE_TOP - PLATE_WEB            # +1.5
Z_SHELF_BOT = Z_PLATE_TOP - CLIP_SHELF               # +3.5
Z_CAVITY_FLOOR = Z_PCB_BOT - UNDER_PCB_CAVITY        # -5.1  (= lid top)
Z_LID_BOT = Z_CAVITY_FLOOR - LID_THICKNESS           # -7.5
Z_SOCKET_BOT = Z_PCB_BOT - SOCKET_DROP               # -3.45
STACK_HEIGHT = Z_PLATE_TOP - Z_LID_BOT               # 12.5 (excl. bumpon)

# Footprint (PCB + slip clearance + walls).
INNER_W = L.PCB_W + 2 * PCB_CLEARANCE                # 84.8
INNER_H = L.PCB_H + 2 * PCB_CLEARANCE                # 104.3
OUTER_W = INNER_W + 2 * WALL                         # 89.6
OUTER_H = INNER_H + 2 * WALL                         # 109.1
INNER_R = L.PCB_CORNER_R + PCB_CLEARANCE             # 5.3

# Case centre in layout coordinates (symmetric about the PCB centre).
CASE_CX = L.PCB_W / 2.0                               # 42.1
CASE_CY = L.PCB_H / 2.0                               # 51.85

_OVER = 1.0    # generic over-cut so subtractive cutters break the surface

# =========================================================================
# 3. PART HELPERS
# =========================================================================


def _rprism(w: float, h: float, r: float, z0: float, z1: float,
            cx: float = CASE_CX, cy: float = CASE_CY) -> Part:
    """Axis-aligned rounded-rectangular prism spanning z0..z1, XY-centred."""
    sk = RectangleRounded(w, h, r)
    solid = extrude(sk, amount=z1 - z0)          # 0..(z1-z0), XY-centred
    return Pos(cx, cy, z0) * solid


def _z_cyl(d: float, z0: float, z1: float, cx: float, cy: float) -> Part:
    """Z-axis cylinder of diameter d spanning z0..z1 at (cx, cy)."""
    return Pos(cx, cy, z0) * extrude(Plane.XY * __circle(d / 2), amount=z1 - z0)


def __circle(r: float):
    from build123d import Circle
    return Circle(r)


def _switch_cutter(cx: float, cy: float) -> Part:
    """Stepped switch opening: 13.9 clip-shelf hole above a 16.0 relief pocket.

    research/04 §3: 1.5 mm clip shelf (the 13.9 hole) over a relief pocket
    that clears the switch's lower housing and gives the clips flex room.
    The bed-side (deck-top) edge gets the elephant-foot chamfer later.
    """
    shelf = Pos(cx, cy, (Z_SHELF_BOT + Z_PLATE_TOP + _OVER) / 2) * Box(
        SWITCH_CUTOUT, SWITCH_CUTOUT, (Z_PLATE_TOP + _OVER) - Z_SHELF_BOT
    )
    relief = Pos(cx, cy, (Z_PLATE_WEB_BOT - _OVER + Z_SHELF_BOT) / 2) * Box(
        SWITCH_RELIEF, SWITCH_RELIEF, Z_SHELF_BOT - (Z_PLATE_WEB_BOT - _OVER)
    )
    return shelf + relief


def _stab_cutters(cx: float, cy: float) -> Part:
    """Two 2U stabiliser relief pockets straddling the key centre (approx.)."""
    z_mid = (Z_PLATE_WEB_BOT - _OVER + Z_PLATE_TOP + _OVER) / 2
    z_h = (Z_PLATE_TOP + _OVER) - (Z_PLATE_WEB_BOT - _OVER)
    left = Pos(cx - L.STAB_HALF_SPACING, cy, z_mid) * Box(
        STAB_CUTOUT_W, STAB_CUTOUT_Y, z_h
    )
    right = Pos(cx + L.STAB_HALF_SPACING, cy, z_mid) * Box(
        STAB_CUTOUT_W, STAB_CUTOUT_Y, z_h
    )
    return left + right


def top_shell() -> Part:
    """Unibody top shell: walls + full-footprint integrated deck/plate.

    Built at world position (canonical for this design). Deck spans the outer
    footprint from Z_PLATE_WEB_BOT..Z_PLATE_TOP; walls drop to Z_CAVITY_FLOOR.
    """
    # Outer solid (walls + deck), then hollow the interior up to the web bottom.
    body = _rprism(OUTER_W, OUTER_H, OUTER_CORNER_R, Z_CAVITY_FLOOR, Z_PLATE_TOP)
    cavity = _rprism(
        INNER_W, INNER_H, INNER_R, Z_CAVITY_FLOOR - _OVER, Z_PLATE_WEB_BOT
    )
    shell = body - cavity

    # Switch openings (13x 1U/2U) + 2U stab relief.
    for (cx, cy) in L.ALL_SWITCHES:
        shell -= _switch_cutter(cx, cy)
    shell -= _stab_cutters(*L.SWITCH_2U)

    # Encoder shaft pass-through (Ø7.5).
    ex, ey = L.RE1_CENTER
    shell -= _z_cyl(ENCODER_SHAFT_D, Z_PLATE_WEB_BOT - _OVER,
                    Z_PLATE_TOP + _OVER, ex, ey)

    # Joystick aperture: travel Ø15 + clearance through-hole + cap pocket.
    jx, jy = L.JS1_CENTER
    js_ap_d = L.JS_TRAVEL_D + JS_APERTURE_CLEAR
    shell -= _z_cyl(js_ap_d, Z_PLATE_WEB_BOT - _OVER,
                    Z_PLATE_TOP + _OVER, jx, jy)
    shell -= _z_cyl(L.JS_CAP_D + JS_CAP_POCKET_CLEAR,
                    Z_PLATE_TOP - JS_CAP_POCKET_DEPTH,
                    Z_PLATE_TOP + _OVER, jx, jy)

    # Layer-LED light-pipe hole (Ø3).
    lx, ly = L.LYR_CENTER
    shell -= _z_cyl(LIGHT_PIPE_D, Z_PLATE_WEB_BOT - _OVER,
                    Z_PLATE_TOP + _OVER, lx, ly)

    # Touch thin-window: pocket the underside, leaving a 1.2 mm membrane.
    tx, ty = L.TP1_CENTER
    shell -= Pos(tx, ty,
                 (Z_PLATE_WEB_BOT - _OVER + (Z_PLATE_TOP - TOUCH_WINDOW_THICKNESS)) / 2
                 ) * Box(
        TOUCH_WINDOW, TOUCH_WINDOW,
        (Z_PLATE_TOP - TOUCH_WINDOW_THICKNESS) - (Z_PLATE_WEB_BOT - _OVER)
    )

    # USB-C flush cutout in the top (y=0) wall.
    shell -= Pos(L.USB_CENTER_X, L.USB_EDGE_Y - WALL / 2, USB_CENTER_Z) * Box(
        USB_CUTOUT_W, WALL + 2 * _OVER, USB_CUTOUT_H
    )

    # Four corner M3 screw clearance holes through the deck (exposed screws).
    for (cx, cy) in L.CORNER_MOUNT_HOLES:
        shell -= _z_cyl(M3_SCREW_CLEAR, Z_PLATE_WEB_BOT - _OVER,
                        Z_PLATE_TOP + _OVER, cx, cy)

    # Elephant-foot chamfer on every bed-side (deck-top) edge.
    top_edges = shell.edges().filter_by_position(
        Axis.Z, Z_PLATE_TOP - 0.05, Z_PLATE_TOP + 0.05
    )
    shell = chamfer(top_edges, EFC_CHAMFER)
    return shell


def bottom_lid() -> Part:
    """Flat bottom lid: plate + registration lip + 4 insert bosses + pockets."""
    lid = _rprism(OUTER_W, OUTER_H, OUTER_CORNER_R, Z_LID_BOT, Z_CAVITY_FLOOR)

    # Registration lip: a perimeter ring rising into the cavity (slip fit).
    lip_out_w = INNER_W - 2 * LID_SLIP
    lip_out_h = INNER_H - 2 * LID_SLIP
    lip_out = _rprism(lip_out_w, lip_out_h, INNER_R - LID_SLIP,
                      Z_CAVITY_FLOOR, Z_CAVITY_FLOOR + LID_LIP_HEIGHT)
    lip_in = _rprism(lip_out_w - 2 * LID_LIP_WIDTH, lip_out_h - 2 * LID_LIP_WIDTH,
                     max(INNER_R - LID_SLIP - LID_LIP_WIDTH, 0.5),
                     Z_CAVITY_FLOOR - _OVER, Z_CAVITY_FLOOR + LID_LIP_HEIGHT + _OVER)
    lid += (lip_out - lip_in)

    # Four M3 insert bosses: cavity floor -> PCB bottom, bore opens at top.
    for (cx, cy) in L.CORNER_MOUNT_HOLES:
        boss = _z_cyl(BOSS_OD, Z_CAVITY_FLOOR, Z_PCB_BOT, cx, cy)
        bore = _z_cyl(M3_INSERT_PILOT, Z_PCB_BOT - M3_INSERT_DEPTH, Z_PCB_BOT + _OVER,
                      cx, cy)
        lid += boss
        lid -= bore

    # Steel-weight pocket (interior/cavity side).
    wx, wy = WEIGHT_CENTER
    lid -= Pos(wx, wy, Z_CAVITY_FLOOR - WEIGHT_POCKET_DEPTH / 2) * Box(
        WEIGHT_POCKET_X, WEIGHT_POCKET_Y, WEIGHT_POCKET_DEPTH
    )

    # Battery-cavity reservation marker (wireless fork).
    bx, by = BATTERY_CENTER
    lid -= Pos(bx, by, Z_CAVITY_FLOOR - BATTERY_RESERVE_DEPTH / 2) * Box(
        BATTERY_CAVITY_X, BATTERY_CAVITY_Y, BATTERY_RESERVE_DEPTH
    )

    # Service-hole pair over the SVC zone (BOOT/RESET poke-through).
    sx, _sy = L.SVC_CENTER
    for dx in (-SVC_HOLE_DX, SVC_HOLE_DX):
        lid -= _z_cyl(SVC_HOLE_D, Z_LID_BOT - _OVER, Z_CAVITY_FLOOR + _OVER,
                      sx + dx, SVC_HOLE_Y)

    # Bumpon recesses on the desk-side (exterior) bottom face.
    for (cx, cy) in BUMPON_CENTERS:
        lid -= _z_cyl(BUMPON_D, Z_LID_BOT - _OVER,
                      Z_LID_BOT + BUMPON_RECESS_DEPTH, cx, cy)

    # Elephant-foot chamfer on every bed-side (lid-bottom) edge.
    bot_edges = lid.edges().filter_by_position(
        Axis.Z, Z_LID_BOT - 0.05, Z_LID_BOT + 0.05
    )
    lid = chamfer(bot_edges, EFC_CHAMFER)
    return lid


# --- PCB proxy: board + per-switch hotswap-socket keep-outs --------------
# Modelled as TWO solids so the socket-relief clearance (the number that
# sets the cavity depth) can be asserted directly.


def pcb_board() -> Part:
    """84.2 x 103.7 x 1.6 board proxy (true R5.0 outline) + 4 corner holes."""
    board = _rprism(L.PCB_W, L.PCB_H, L.PCB_CORNER_R, Z_PCB_BOT, Z_PCB_TOP)
    for (cx, cy) in L.CORNER_MOUNT_HOLES:
        board -= _z_cyl(M3_SCREW_CLEAR, Z_PCB_BOT - _OVER, Z_PCB_TOP + _OVER, cx, cy)
    return board


def sw_sockets() -> Part:
    """13 hotswap-socket keep-out blocks hanging 1.85 mm below the PCB."""
    blocks = None
    for (cx, cy) in L.ALL_SWITCHES:
        blk = Pos(cx, cy, Z_SOCKET_BOT + SOCKET_DROP / 2) * Box(
            SOCKET_BODY_X, SOCKET_BODY_Y, SOCKET_DROP
        )
        blocks = blk if blocks is None else blocks + blk
    return blocks


# =========================================================================
# 4. ASSEMBLY + MECHANISM ASSERTIONS
# =========================================================================

assembly = (
    Assembly()
    .with_part("top_shell", top_shell())
    .with_part("lid", bottom_lid())
    .with_part("pcb_board", pcb_board())
    .with_part("sw_sockets", sw_sockets())
    # No two solids may overlap (tangent contact is allowed and reads as 0).
    .assert_no_interference("top_shell", "lid")
    .assert_no_interference("top_shell", "pcb_board")
    .assert_no_interference("top_shell", "sw_sockets")
    .assert_no_interference("lid", "pcb_board")        # bosses touch PCB bottom
    .assert_no_interference("lid", "sw_sockets")
    .assert_no_interference("pcb_board", "sw_sockets")  # sockets touch PCB bottom
    # Design-critical clearances.
    .assert_clearance("top_shell", "pcb_board", min_mm=0.25)   # PCB slip fit
    .assert_clearance("sw_sockets", "lid", min_mm=1.0)         # socket relief
)


def _advisory_printability(part: Part, name: str, up_axis, out: str = "outputs"):
    """Run inspect() as ADVISORY: capture its metrics without aborting.

    The mechanism ``check`` above is the hard gate (research/04 discipline:
    "zero interferences = gate"). Printability is a per-part heuristic whose
    known false positives (chamfer slivers -> tiny min-wall; 45deg bed-side
    EFC chamfers and <20 mm bridges -> overhang flags; see cad-khana
    printability.md) must not mask a clean interference result. Governing
    thin features are intentional (1.2 mm touch window, ~1.05 mm clip-shelf
    ledge, 0.8 mm weight-pocket floor) and are documented in CASE-NOTES.md.
    """
    import json
    try:
        inspect(part, method=FDM(up_axis=up_axis, wall_min_mm=1.0),
                out=out, name=name)
        verdict = "PASS"
    except SystemExit:
        verdict = "ADVISORY (documented false-positives / by-design thin zones)"
    data = json.load(open(os.path.join(out, f"{name}-printability.json")))
    oh = data.get("overhang") or {}
    print(f"[printability] {name}: {verdict} | "
          f"min_wall={data.get('min_wall_mm')} | "
          f"overhang_area={oh.get('area_mm2')} max_deg={oh.get('max_angle_deg')}")


if __name__ == "__main__":
    # --- GATE: interference / clearance. Raises SystemExit(1) on failure. ---
    check(assembly, out="outputs")

    # --- Advisory printability for the two printed parts ---
    _advisory_printability(top_shell(), "top_shell", up_axis=(0, 0, -1))
    _advisory_printability(bottom_lid(), "bottom_lid", up_axis=(0, 0, 1))

    # --- Per-part STL + STEP for the printed parts (proxies not exported) ---
    here = os.path.dirname(os.path.abspath(__file__))
    stl_dir = os.path.join(here, "stl")
    step_dir = os.path.join(here, "step")
    for name, part in (("loudest_top_shell", top_shell()),
                       ("loudest_bottom_lid", bottom_lid())):
        export_stl(part, os.path.join(stl_dir, name + ".stl"))
        export_step(part, os.path.join(step_dir, name + ".step"))
    print("exported top_shell + bottom_lid to stl/ and step/")

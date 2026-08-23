"""agentpad13 v2.9 — TRAY BASE family, built on the CENTRAL MOUNT contract.

Owner directives, verbatim.

  2026-08-18, which produced the v2.8 corner-boss design:
    "We should think about the tray base as well. Perhaps we can come up with
     variants like angled ones? Or make this modular/stick on in some way so we
     can add bases or grips or whatever. Also low priority."

  2026-08-19, which SUPERSEDED it:
    "No magnets, either just alternative trays or notches in the tray where
     bases can insert, whether TPU or hard filaments."
    "I'm just saying why is the base so big? Why don't we have the notche
     closer to the middle to enable a variety of styles perhaps even a circular
     pedestal like the actual Codex Micro."
    "A full footprint variety is fine too. Just saying regardless, we should
     have more flexibility in the bases this way esp if this is open source
     people can make their own."

WHAT CHANGED, AND WHY IT IS THE INTERFACE THAT MATTERS
-----------------------------------------------------
v2.8 put the four locating pockets in the tray's CORNER BOSSES, 76.8 x 92.6 mm
apart. That did not make a large base wrong; it made a large base MANDATORY,
because the only places to attach were at the extremes of the footprint. Every
v2.8 variant was therefore 91.6 x 107.4 — not by choice, by geometry.

v2.9 moves the pattern to a 25.0 mm square on the case-outline centre. The
interface now spans a 35.36 mm circle, so it fits inside anything from a Ø42
puck upward, and the base's size and shape become FREE. This module proves
that with two bases chosen to be as different as they can be:

    riser      91.6 x 107.4 full-footprint 3.0 mm sheet (TPU or hard)
    wedge      same plan, 8.0 deg back-raised typing angle
    pedestal   Ø78 tilted drum — the wedge, cut to a circle

Same four pegs, same ladder, no special-casing anywhere. A `wedge` variant is
included because the 2026-08-18 directive asked for angled bases and because it
exercises the pattern's 4-fold symmetry (one printed wedge tilts four ways).

THE PUBLISHED CONTRACT  (also in CASE-V2-NOTES §22; this module is its
reference implementation, not its definition)
-----------------------------------------------------------------------------
    datum      centre of the case outline in plan. The band outer
               (95.6 x 111.4) and the tray outline (84.3 x 100.1) are BOTH
               centred there, so a builder finds it with a ruler.
    mating     the flat tray bottom plane. All base material below it. Since
               v2.11 this is 2.0 mm below the separate band bottom.
    features   4 blind flat-bottomed pockets Ø6.0 x 1.6 deep, axes vertical,
               at (±12.5, ±12.5) from the datum.
    peg        Ø from the printed FIT LADDER below, 1.4 long, 0.4 tip chamfer.
    fit        the tray side is CAD-nominal and carries no allowance. ALL fit
               lives on the peg. Print the FIT GAUGE, keep the rung that holds.
    keep-outs  BOOT/RESET service window; the USB face. (v2.15: the bumpon
               lands are GONE — feet are the builder's business.)

Coordinate frame (identical to agentpad13_case_v2 — this module CONSUMES that
module and never modifies it, so the interface cannot drift from the tray):

    origin xy = PCB origin; x = 0 LEFT, y = 0 FAR (control band / USB edge,
                away from the user), y = 100 NEAR (the 2U key edge)
    +Z        = up; z = 0 = PCB TOP face
    z        = C.Z_TRAY_BOT = the tray bottom = the MATING plane. This is
               -9.5 since v2.11 gave the tray a 2.0 mm plinth (it was -7.5,
               and flush with the band bottom, through v2.10). Read from the
               case module, never retyped.

Orientation provenance: docs/independent-design/phase0-layout-v2-notes.md
("control band moves to the top ... RE1 top-LEFT"), and RE1 sits at
(13.525, 12.5) — so small y is the FAR edge and the USB cable exits away from
the user. A back-raised typing wedge thickens toward y = 0.

WHY PRESS-FIT PEGS AND NOT SOMETHING CLEVERER
---------------------------------------------
The deciding criterion is a STRANGER'S FIRST PRINT, on an unknown machine in
an unknown filament. A blind round hole and a round peg are the one pair every
FDM printer makes predictably, and their error is a single number a builder can
measure with calipers and correct by choosing a ladder rung. A keyed recess, a
dovetail ring or a bolt circle with a spigot all add a second dimension that
has to be right at the same time, and none of them buys anything the round
pockets do not already deliver: the base is LOCATED by the four pegs and
LOADED through the flat mating plane, never through the pegs.

Magnets stay rejected on the v2.8 arithmetic, which this pass did not revisit:
a Ø6 pocket necks the notched (0,0) boss wall to 0.651 mm against a 1.6512 mm
minimum that is already a first-article watch-item.

TPU: fine, and the reason the ladder has a dedicated rung. A TPU peg compresses
into the pocket instead of shearing the pocket wall, so it wants the TIGHT rung
(PEG_TPU), not the loose one. That is the whole of the material question.

PRINT ORIENTATION: desk face on the bed, every variant, no support.
"""

import json
import math
import os
import sys

from build123d import (
    Box,
    Circle,
    Cone,
    Plane,
    Polyline,
    Pos,
    RectangleRounded,
    Rot,
    export_stl,
    extrude,
    make_face,
    mirror,
)

from cad_khana.mechanism.assembly import Assembly
from cad_khana.mechanism.check import check
from cad_khana.printability.inspect import inspect
from cad_khana.printability.methods import FDM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import agentpad13_case_v2 as C          # noqa: E402  CONSUME, never modify


# =========================================================================
# 1. PARAMETERS
# =========================================================================

# --- consumed from the case (single source of truth for the interface) ----
MATE_Z = C.Z_TRAY_BOT                   # v2.11 plinth: -9.5 (was -7.5)
DATUM = (C.CX, C.CY)                    # (42.1, 50.0) case-outline centre
PEG_XY = list(C.BASE_MOUNT_XY)          # (29.6,37.5) (54.6,37.5) (29.6,62.5) (54.6,62.5)
PEG_BORE = C.BASE_MOUNT_D               # 6.0
PEG_POCKET_DEPTH = C.BASE_MOUNT_DEPTH   # 1.6
PEG_PITCH = C.BASE_MOUNT_PITCH          # 25.0
BAND_W, BAND_H, BAND_R = C.OUTER_W, C.OUTER_H, C.OUTER_R
BAND_EFC = C.EFC_CHAMFER

# --- MEASURED, not assumed: the tray's real elephant-foot chamfer ---------
# `_safe_chamfer` tries EFC_CHAMFER (0.4), then 0.75x, then 0.2, and takes the
# first OCCT accepts. On the tray's z=-7.5 face the first two are REFUSED and
# it settles at 0.2 — verified against the committed HEAD build as well as the
# current one, so this is pre-existing behaviour, not a v2.9 side effect. The
# pocket mouth therefore offers a 0.2 lead-in, NOT the 0.4 the constant
# advertises, and the peg has to carry the rest. Designing the peg against the
# advertised 0.4 would have made every rung tighter than intended.
TRAY_POCKET_MOUTH_CHAMFER = 0.2

# --- peg fit ladder -------------------------------------------------------
# A nominal hole prints ~0.15 undersize and a nominal peg ~0.10 oversize on a
# typical 0.4 mm-nozzle profile, so CAD-equal lands ~0.25 mm INTERFERENCE. The
# ladder brackets that: as printed the rungs should read slip / line-to-line /
# light press / firm press. Same doctrine as the encoder-knob bore
# (5.9/6.0/6.1) and the stick-cap socket (nom/p05/p10).
PEG_LADDER = [5.60, 5.70, 5.80, 5.90]
PEG_NOM = 5.80           # rigid filament default (light press)
PEG_TPU = 5.90           # TPU default: it compresses, so it wants the tight rung
PEG_LEN = 1.4            # into the 1.6 pocket -> 0.2 seat gap, so the base
#                          always lands on its mating FACE, never on peg tips
PEG_TIP_CHAMFER = 0.4    # peg-side lead-in; with the tray's measured 0.2 mouth
#                          chamfer that is 0.6 mm of combined lead-in and
#                          1.0 mm of full-Ø peg inside a 1.4 mm full-Ø pocket

# --- full-footprint outline (mat / wedge) ---------------------------------
BASE_REVEAL = 2.0        # inset from the band's outer face, per side. A flush
#                          base would have to match a printed band's outline to
#                          ~0.2 mm or the seam reads as a defect; 2.0 is ~10x
#                          FDM outline variance, so it reads as a deliberate
#                          shadow gap. Net visible step = 2.0 - band EFC.
BASE_W = BAND_W - 2 * BASE_REVEAL                 # 91.6
BASE_H = BAND_H - 2 * BASE_REVEAL                 # 107.4
BASE_R = BAND_R - BASE_REVEAL                     # 6.0
BASE_T = 2.4             # minimum section of a full-footprint base.
# [v2.15] DECOUPLED FROM THE TRAY. This read `C.TRAY_T` — chosen because 2.4
# was "the tray floor's own thickness", i.e. a proven-adequate section. That
# was a RATIONALE for picking 2.4, never a requirement to track the tray
# forever, and the coupling turned into a ghost the moment v2.11 took
# TRAY_T 2.4 -> 4.4 to stand the tray proud of the band as a plinth. That
# change had nothing to do with bases, but it silently made the mat 4.4 mm
# thick: +83 % mass (26.7 -> 48.8 g) and +83 % filament, on a part whose
# whole point is to be a thin TPU sheet. Nobody asked for it and nothing
# recorded it. Pinned to a literal so a future stance/aesthetic change to
# the tray cannot re-import itself here.

RISER_T = 3.0            # [v2.16] body of the flat `riser`. Owner: "So I
#                          think 2 or 3mm is enough for the riser. Maybe it can
#                          be printed in TPU or something." 3.0 of the 2-3 band
#                          because at the full 91.6 x 107.4 footprint a 2 mm
#                          TPU sheet is floppy enough to curl at the corners,
#                          and 3.0 still prints in one short job.

# --- circular pedestal (v2.16: REDESIGNED) --------------------------------
# Owner, 2026-08-20: "the pedestar is the wedge but just a circular cutout of
# it from above. No need for the ballast if the diameter is reasonable enough.
# Keep it fucking ismple."
#
# So it is built LITERALLY that way: the wedge solid INTERSECTED with a
# vertical cylinder on the datum. Not a re-derivation of a tilted disc, not a
# lofted cone — one boolean, so it inherits the wedge's angle, its mating
# plane and its peg pattern by construction and cannot drift from them.
#
# Ø78 is the LARGEST windowless circle, recomputed from current geometry
# rather than inherited: the nearest BOOT/RESET slot bbox corner sits
# 39.182 mm from the datum (the true rounded-slot corner is 39.518), so a
# base that never covers the service slots caps at Ø78.364. Ø78 leaves
# +0.182 mm against the conservative bbox figure and +0.518 mm against the
# real geometry. That is deliberately the maximum: every millimetre of radius
# buys tipping margin, and this variant has no ballast to fall back on.
PED_D = 78.0
# NO BALLAST. The Ø70 pedestal needed 69-135 g of steel because it covered
# only a fifth of the footprint; at Ø78 the base's own printed mass carries
# it — see the stability block, which now reports margins as a function of
# INFILL rather than of added weight. The cavity, its ribs, the packing
# fraction and the headroom assert are all deleted.
PED_SLOT_KEEPOUT = 0.40  # [v2.16] print-tolerance floor between the pedestal
#                          rim and the REAL (radiused) BOOT/RESET slot edge.
#                          Replaces a blanket 2.0 mm rule that Ø78 cannot meet
#                          and that no diameter can meet while also clearing
#                          the stability bars — full derivation at the assert.
PED_SOLIDITY = 1.00      # REQUIRED effective solidity for the pedestal, and a
#                          published print instruction, not an assumption. The
#                          5 N abuse case needs >= ~0.85; a normal 3-wall /
#                          20 % gyroid print (0.62) clears the 3 N DESIGN case
#                          but NOT abuse. Docs therefore say: print it solid.
# --- desk friction, feet excluded (v2.15) ---------------------------------
MU_HARD = 0.4            # bare printed rigid plastic (PLA/PETG) on a hard
#                          desk. Was 0.8 while the bases carried rubber
#                          bumpons; with the recesses gone that figure would
#                          be a claim about feet this project no longer
#                          ships. 0.4 is the conservative end of the usual
#                          0.3-0.5 band for rigid thermoplastic on laminate
#                          or finished wood. It affects ONLY the slide/tip
#                          comparison, never the tipping force itself.
MU_TPU = 1.2             # TPU sheet on a desk (unchanged — the mat never had
#                          feet, so nothing about it moved)

# --- FEET: DELETED in v2.15 (owner ruling 2026-08-20) ---------------------
# Every base used to carry Ø8.3 x 1.0 recesses for 3M bumpons — four at the
# tray's boss centres on the full-footprint variants, four more on a Ø59 bolt
# circle under the pedestal. They are GONE. Owner:
#     "I don't really care about bumps or whatever, people can stick whatever
#      they want."
#     "NO, there are no more recesses! The only recesses on the tray are the
#      notches for the base!"
# Feet are therefore UNOFFICIAL: no part number, no bolt circle, no
# prescription anywhere in this module or its docs. Every base underside is
# FLAT, and a builder sticks on whatever they like, wherever they like.
#
# Two consequences that are verified, not assumed:
#   * PRINTABILITY. The recesses were the ONLY overhang features on the mat
#     and the wedge (blind pockets in the desk face, which the detector
#     reports as 90-deg bridges). With them gone those two variants print
#     with ZERO overhang area. The pedestal keeps exactly one overhang, its
#     tilted desk face, which is printed flat ON the bed (v2.16: the
#     ballast cavity and its ribs are gone).
#   * STABILITY. Removing the pedestal's and wedge's feet ENLARGES their
#     support polygon: they now rest on the full rim / full footprint rather
#     than on four Ø7.9 pads. Every stance figure below therefore EXCLUDES
#     feet and states so.

# --- service window (BOOT / RESET tact access from below) -----------------
SVC_WINDOW_RELIEF = 0.6
SVC_WINDOW_R = 2.3
SVC_CONTAIN_MIN = 0.2

# --- direction key (wedge only) -------------------------------------------
KEY_W = 11.0
KEY_INSET = 16.0
KEY_DEPTH = 0.8

# --- typing angle ---------------------------------------------------------
# The device has NO intrinsic typing angle: its deck is flat and tilting it
# neither helps nor hurts the joystick (a planar slider) or the encoder. The
# angle is population-matched to the keyboard the pad sits beside — 6.5 deg is
# the standard "feet-out" second stage of full-travel boards. Stated as an
# assumption, not a measurement.
WEDGE_DEG = 8.0          # [v2.16] 6.5 -> 8.0. Owner: "I think 6.5deg is too
#                          low but IDK, you tell me. Base this on real
#                          products, maybe it's not too low, what is a typical
#                          mechanical keyboard pitch?" Researched: the
#                          mainstream standard sits at 7 deg, the comfort band
#                          across real boards is 4-8 deg, and high-profile
#                          customs land 6-8 deg. 8.0 is the top of that band —
#                          chosen because this deck is LOW (a 13-key pad, not a
#                          full-height board), so it wants the steeper end to
#                          read as a typing angle at all. ONE constant: the
#                          wedge and the pedestal both take their angle here,
#                          so they can never disagree.

# --- fit gauge ------------------------------------------------------------
GAUGE_PITCH = 14.0
GAUGE_T = 3.0
GAUGE_MARK_D = 2.0
GAUGE_MARK_Z = 0.6

# --- variants: (name, kind, tilt, body_thickness) -------------------------
# [v2.16] THE OFFICIAL CATALOG IS EXACTLY THREE. Owner: "I only see the need
# for two official bases to start. A flat one that elevates slightly further,
# and an angled one at some reasonable degree. Perhaps a circular angled one if
# we want to get stylish like Codex Micro." -> riser, wedge, pedestal.
# `mat` is RETIRED: the riser replaces it (same plan, 2.4 -> 3.0 body, and it
# is the one you print in TPU if you want grip). Its files are deleted rather
# than kept as a museum piece.
VARIANTS = [
    ("riser",    "full",   0.0,       RISER_T),
    ("wedge",    "full",   WEDGE_DEG, BASE_T),
    ("pedestal", "circle", WEDGE_DEG, BASE_T),
]
DEFAULT_VARIANT = "wedge"

_OVER = 1.0

# --- material densities used in the mass model (g/cm3) --------------------
RHO = {"PLA": 1.24, "PETG": 1.27, "TPU95": 1.21, "FR4": 1.85, "steel": 7.85}
PRINT_FILL = 0.62        # ASSUMED effective solidity, 3 walls / 20% gyroid


# =========================================================================
# 2. GEOMETRY HELPERS
# =========================================================================

def _rprism(w, h, r, z0, z1, cx=None, cy=None):
    cx = DATUM[0] if cx is None else cx
    cy = DATUM[1] if cy is None else cy
    return Pos(cx, cy, z0) * extrude(RectangleRounded(w, h, r), amount=z1 - z0)


def _cyl(d, z0, z1, cx, cy):
    return Pos(cx, cy, z0) * extrude(Plane.XY * Circle(d / 2), amount=z1 - z0)


def _rung_name(v):
    return f"{v:g}".replace(".", "p")


Y_NEAR = DATUM[1] + BASE_H / 2.0     # 103.7 — NEAR (user) edge
Y_FAR = DATUM[1] - BASE_H / 2.0      # -3.7  — FAR (USB) edge


def tilt_rise(deg, span=BASE_H):
    return span * math.tan(math.radians(deg))


def desk_z(y, deg, t0=BASE_T):
    return MATE_Z - t0 - (Y_NEAR - y) * math.tan(math.radians(deg))


def _desk_frame(deg, t0=BASE_T):
    """Frame whose local z = 0 IS the desk face, local +z into the part.
    Everything on the desk side is cut here so its depth is measured
    perpendicular to the face the part is printed on."""
    return Pos(DATUM[0], Y_NEAR, MATE_Z - t0) * Rot(X=deg)


def _desk_uv(x, y, deg):
    return x - DATUM[0], (y - Y_NEAR) / math.cos(math.radians(deg))


def _rrect_sdf(px, py, cx, cy, w, h, r):
    """Exact signed distance to a rounded-rect boundary; negative inside."""
    qx = abs(px - cx) - (w / 2.0 - r)
    qy = abs(py - cy) - (h / 2.0 - r)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def print_pose(part, deg):
    """The part as it really sits on the bed: desk face down, min z = 0.

    cad_khana's overhang detector derives the build-plate level from BOUNDING
    BOX corners dotted with up_axis, which is only the true minimum when
    up_axis is axis-aligned. With a tilted up_axis the build-plate exclusion
    never fires and the desk face itself is reported as a huge 90-degree
    overhang. Rotating into the real pose and inspecting with up=(0,0,1)
    sidesteps that. (Logged as cad-khana feedback.)"""
    p = Rot(X=-deg) * part
    return Pos(0.0, 0.0, -p.bounding_box().min.Z) * p


def _service_window():
    """Union bbox of the tray's own two service slots, relieved."""
    xs, ys = [], []
    for (_lbl, x0, x1, y0, y1, _z0, _z1) in C._TACTS:
        xs += [x0 - C.SVC_CLEAR, x1 + C.SVC_CLEAR]
        ys += [y0 - C.SVC_CLEAR, y1 + C.SVC_CLEAR]
    return (min(xs) - SVC_WINDOW_RELIEF, max(xs) + SVC_WINDOW_RELIEF,
            min(ys) - SVC_WINDOW_RELIEF, max(ys) + SVC_WINDOW_RELIEF)


def svc_corner_radius():
    """Distance from the datum to the NEAREST corner of the service-slot
    union. This is the hard cap on any windowless circular base."""
    x0, x1, y0, y1 = _service_window()
    return min(math.hypot(px - DATUM[0], py - DATUM[1])
               for px in (x0, x1) for py in (y0, y1))


# =========================================================================
# 3. PARTS
# =========================================================================

def _pegs(peg_d):
    """The four locating pegs, up from the mating plane. Cylinder + truncated
    cone rather than a chamfer() edge selection, so the tip is deterministic
    across every ladder rung."""
    out = None
    shank = PEG_LEN - PEG_TIP_CHAMFER
    for (px, py) in PEG_XY:
        p = _cyl(peg_d, MATE_Z, MATE_Z + shank, px, py)
        p += Pos(px, py, MATE_Z + shank + PEG_TIP_CHAMFER / 2.0) * Cone(
            bottom_radius=peg_d / 2.0,
            top_radius=peg_d / 2.0 - PEG_TIP_CHAMFER,
            height=PEG_TIP_CHAMFER)
        out = p if out is None else out + p
    return out


def pedestal(peg_d=PEG_NOM, d=PED_D):
    """[v2.16] The wedge, cut to a circle — exactly as the owner described it.

    `full_base(WEDGE_DEG) & vertical cylinder Ø{d}`, so the angle, the mating
    plane, the peg pattern and the desk face are all INHERITED from the wedge
    rather than restated. No ballast cavity and no service windows: Ø78 is
    inside the windowless cap, so the base never covers the BOOT/RESET slots.

    Its desk face is the wedge's tilted plane clipped to the cylinder — an
    ellipse — so the part sits flush on the desk and tilts the device by the
    same angle the wedge does. The plan silhouette is the vertical cylinder,
    which makes the support polygon an exact circle of radius d/2.
    """
    solid = full_base(WEDGE_DEG, peg_d=peg_d, t0=BASE_T, key=True,
                      windows=False)
    # The cylinder is a PLAN-silhouette cut: only its radius is meant to carry
    # information, and its z-bounds must be incapable of touching anything. So
    # they are derived from the solid's OWN bounding box, not written by hand.
    #
    # This is not defensive styling — a hand-written z-top shipped a real bug.
    # v2.16 first used `MATE_Z + _OVER` (= -8.5), which sits 0.4 mm BELOW the
    # peg tips at MATE_Z + PEG_LEN (= -8.1). The cut therefore sliced 0.4 mm
    # off all four pegs, and because PEG_TIP_CHAMFER is exactly 0.4 the part
    # it removed was precisely the tip chamfer — the pedestal shipped with
    # blunt, short pegs and no insertion lead-in, while the riser and wedge
    # had correct ones. The peg-containment gate could not see it: a SHORT peg
    # is still fully contained in its pocket. assert_pegs_intact() below now
    # closes that hole by comparing the built pegs against the reference peg
    # solid, so length and chamfer are both checked.
    bb = solid.bounding_box()
    return solid & _cyl(d, bb.min.Z - _OVER, bb.max.Z + _OVER, *DATUM)


def full_base(tilt=0.0, peg_d=PEG_NOM, t0=BASE_T, key=False, windows=True):
    """Full-footprint base: flat `riser` (tilt 0) or typing `wedge`.

    `windows=False` is used by the pedestal, which is small enough to
    clear the BOOT/RESET slots entirely and therefore must not cut them.
    """
    frame = _desk_frame(tilt, t0)
    z_low = min(desk_z(Y_FAR, tilt, t0), desk_z(Y_NEAR, tilt, t0)) - _OVER
    b = _rprism(BASE_W, BASE_H, BASE_R, z_low, MATE_Z)

    # desk face as a half-space. The side walls stay vertical in the case
    # frame, so in print space they lean by `tilt` — 6.5 deg of overhang at
    # worst, 0.023 mm of step per 0.2 mm layer. Self-supporting.
    b -= frame * Pos(0, 0, -100.0) * Box(400.0, 400.0, 200.0)

    # Service window, cut along case-z (the axis the tray slots and the tool
    # run on). [v2.15] Cut as a SYMMETRIC PAIR: the functional window over the
    # tray's BOOT/RESET slots, PLUS its mirror image about the datum's x
    # centreline. The tray's slots sit at x 58.4..76.6, nowhere near centre,
    # so a single window makes the base x-asymmetric — and by the owner's
    # design law an asymmetric base is designed wrong, full stop. The mirror
    # window is not decoration and not waste: it is what makes the part obey
    # its own definition, it costs a few grams of a part that has mass to
    # spare, and it means the base cannot be installed 180-deg wrong.
    wx0, wx1, wy0, wy1 = _service_window()
    for _sx in ((1.0, -1.0) if windows else ()):
        _cx = DATUM[0] + _sx * ((wx0 + wx1) / 2.0 - DATUM[0])
        b -= _rprism(wx1 - wx0, wy1 - wy0, SVC_WINDOW_R,
                     z_low - _OVER, MATE_Z + _OVER, _cx, (wy0 + wy1) / 2.0)

    if key:
        # The peg pattern is 4-fold symmetric, so a wedge can be fitted any of
        # four ways. That is the point — but the user still needs to know which
        # way is up, so the desk face carries a debossed arrow at the NEAR edge.
        u, v = _desk_uv(DATUM[0], Y_NEAR - KEY_INSET, tilt)
        pts = [(-KEY_W / 2.0, 0.0), (KEY_W / 2.0, 0.0), (0.0, KEY_W / 2.0),
               (-KEY_W / 2.0, 0.0)]
        arrow = make_face(Polyline(*[(px, py, 0.0) for (px, py) in pts]))
        b -= frame * Pos(u, v, -0.2) * extrude(arrow, amount=KEY_DEPTH + 0.2)
    return b + _pegs(peg_d)


def base(variant=DEFAULT_VARIANT, peg_d=PEG_NOM):
    _n, kind, tilt, t0 = {v[0]: v for v in VARIANTS}[variant]
    if kind == "circle":
        return pedestal(peg_d)
    return full_base(tilt, peg_d, t0, key=(tilt > 0.0))


def export_pose(part):
    """[v2.15] MIRROR AT EXPORT — the same handedness fix the tray carries.

    This module CONSUMES agentpad13_case_v2, whose frame is LEFT-handed (x
    right, y DOWN from raw KiCad board coords, z up), while STL is
    right-handed. Everything exported straight out of that frame is the
    ENANTIOMORPH of the intended part. The tray was caught by this on a
    printed part (v2.10) and is mirrored at export; the band is exempt only
    because it was PROVEN achiral. Bases are neither: the wedge has a tilt
    direction and a direction arrow, so a wrong-handed base is a real defect.

    Adopted now because this pass rebuilds every base STL anyway, so the
    frame fix rides along at zero extra hash cost — exactly the condition the
    band-deferral ruling named for taking it.
    """
    return Pos(0, C.PCB_H, 0) * mirror(part, about=Plane.XZ)


def assert_pegs_intact(part, peg_d, name):
    """[v2.16] Every peg on every variant must be the SAME peg.

    Measured on the BUILT SOLID, not asserted from constants: take everything
    the part has above the mating plane — which is exactly its pegs, because
    every base body tops out at MATE_Z — and require it to be geometrically
    identical to the reference `_pegs(peg_d)` solid. Both difference volumes
    must vanish, so this catches a truncated peg, a short peg, a missing peg,
    a decapitated tip chamfer and a mispositioned peg alike.

    It exists because the peg-containment gate cannot: containment asks
    "is the peg inside its pocket", and a peg that is too SHORT passes that
    test perfectly. The v2.16 pedestal shipped 0.4 mm short for exactly that
    reason — see the note in pedestal().
    """
    ref = _pegs(peg_d)
    rb = ref.bounding_box()
    above = part & Box(4 * BASE_W, 4 * BASE_H, (rb.max.Z - MATE_Z) + 4 * _OVER).locate(
        Pos(DATUM[0], DATUM[1], MATE_Z + ((rb.max.Z - MATE_Z) + 4 * _OVER) / 2.0))
    a, b = (above - ref).volume, (ref - above).volume
    assert a < 1e-6 and b < 1e-6, (
        f"BASE '{name}' HAS BAD PEGS: the material above the mating plane is not "
        f"the reference peg set. Extra {a:.6f} mm^3, missing {b:.6f} mm^3 (both "
        f"must be < 1e-6). Peg tips must reach MATE_Z + PEG_LEN = "
        f"{MATE_Z + PEG_LEN} with the {PEG_TIP_CHAMFER} mm tip chamfer intact. "
        "The usual cause is a boolean whose z-bounds clip the pegs — see "
        "pedestal(), where a hand-written cylinder z-top did exactly that.")


def assert_x_symmetric(part, name):
    """THE DESIGN LAW, made executable. Owner, 2026-08-20:

        "they should be symmetric over x by definition because why wouldn't
         they be? If they're not, they're designed wrong. This is a fact of
         the design, not something that needs to be memasured."

    So this is NOT a measurement and NOT a tolerance — it is the definition
    of a correct base, checked exactly, on every build. Note there is no
    mirrored-export escape hatch here the way there is for a chiral tray:
    for a base, symmetry is definitional, so the only correct responses to a
    failure are to re-centre the offending feature or to redesign it.
    """
    m = Pos(2 * DATUM[0], 0, 0) * mirror(part, about=Plane.YZ)
    a, b = (part - m).volume, (m - part).volume
    assert a < 1e-6 and b < 1e-6, (
        f"BASE '{name}' IS DESIGNED WRONG: it is not symmetric about the "
        f"pattern centreline x = {DATUM[0]}. Measured part-minus-mirror "
        f"{a:.6f} mm^3 and mirror-minus-part {b:.6f} mm^3; both must be "
        "< 1e-6. Owner ruling 2026-08-20: bases are symmetric over x BY "
        "DEFINITION — 'if they're not, they're designed wrong'. Re-centre the "
        "offending feature, or mirror it so it appears on both sides "
        "(that is what the service window does). There is NO mirrored-export "
        "escape here as there is for a chiral part: symmetry is definitional, "
        "not a property to be worked around.")


def fit_gauge():
    """One small print that tells a builder which ladder rung their machine
    lands on. Push each peg into any tray pocket; keep the rung that holds.

    Marked by COUNT, not by text: n raised dots beside rung n, smallest first.
    Raised dots survive on any printer; a 3 mm debossed numeral does not."""
    n = len(PEG_LADDER)
    L = GAUGE_PITCH * n
    z0 = MATE_Z - GAUGE_T
    g = Pos(DATUM[0], DATUM[1], z0) * extrude(
        RectangleRounded(L, GAUGE_PITCH + 4.0, 3.0), amount=GAUGE_T)
    for i, pd in enumerate(PEG_LADDER):
        px = DATUM[0] - L / 2.0 + GAUGE_PITCH * (i + 0.5)
        shank = PEG_LEN - PEG_TIP_CHAMFER
        g += _cyl(pd, MATE_Z, MATE_Z + shank, px, DATUM[1] + 2.0)
        g += Pos(px, DATUM[1] + 2.0, MATE_Z + shank + PEG_TIP_CHAMFER / 2.0) * Cone(
            bottom_radius=pd / 2.0, top_radius=pd / 2.0 - PEG_TIP_CHAMFER,
            height=PEG_TIP_CHAMFER)
        for k in range(i + 1):
            mx = px - (i * 1.5) + k * 3.0
            g += _cyl(GAUGE_MARK_D, MATE_Z - 0.001, MATE_Z + GAUGE_MARK_Z,
                      mx, DATUM[1] - 6.0)
    return g


# =========================================================================
# 4. STABILITY  — the engineering that actually sizes a small base
# =========================================================================
#
# A base that does not span the footprint makes the device CANTILEVER: press a
# far control and the assembly wants to rotate about the base's rim. Two load
# cases, and they respond to mass in OPPOSITE ways, which is why both are here.
#
# (A) VERTICAL PRESS, force F at plan point p, weight W at plan point g:
#         the ground reaction resultant sits at  CoP(F) = g + t*(p - g),
#         t = F/(W+F).
#     CoP walks the segment g->p as F rises and can never pass p, so a press at
#     a point INSIDE the support polygon cannot tip the device at ANY force.
#     If p is outside, let t_e be where the segment crosses the boundary:
#         F_tip = W * t_e / (1 - t_e)         margin = F_tip / F_applied
#     Mass helps here, linearly.
#
# (B) HORIZONTAL PUSH, force F at height h above the desk:
#         reaction offset  d = F*h/W  from the CG.
#         F_tip = W*b/h   (b = boundary distance from the CG that way)
#         F_slide = mu*W
#     It tips before it slides iff  b < mu*h  — MASS CANCELS. Only the support
#     radius and the push height matter. So mass cannot buy you out of a
#     too-small base under a hard shove; only diameter can. This is the case
#     that a naive "just add weight" answer gets wrong.
#
# NOTE the CG's HEIGHT appears in neither case. Where ballast sits vertically
# inside a base is mechanically irrelevant; only its plan position is. That is
# why the pedestal's cavity is placed for printability, not for a low CG.

G = 9.81

# --- pad mass model -------------------------------------------------------
# "vol": mass = model volume (cm3) x density x fill fraction.
# "fixed": a bought part; the model's envelope volume is NOT its mass.
# Every row carries its provenance. Numbers marked EST are estimates and are
# reported as estimates — they are not datasheet values.
PAD_MASS_MODEL = [
    # name            kind     args                 provenance
    ("band",          "vol",  (RHO["PETG"], 0.65), "PETG. 5.4 mm walls: 3 perims solid + 20% gyroid core -> 0.65 (EST)"),
    ("tray",          "vol",  (RHO["PETG"], 0.90), "PETG. 4.4 mm floor (v2.11 plinth) prints effectively solid (EST)"),
    ("pcb_rail",      "vol",  (RHO["PETG"], 0.95), "prints as one body with the tray"),
    ("pcb_retention", "vol",  (RHO["PETG"], 0.95), "prints as one body with the tray"),
    ("fr4_plate",     "vol",  (2.005, 1.00),       "FR4 + copper, effective 2.005 g/cm3"),
    ("pcb_board",     "vol",  (2.19, 1.00),        "FR4 + 2x35um Cu at the measured 98%/98% pour -> 2.19 g/cm3"),
    ("pcb_components","fix",  2.9,                 "SMD population 1.4 + MX 2U stabiliser 1.5 (EST)"),
    ("sockets",       "fix",  5.5,                 "26x Kailh CPG151101S11 (2 per switch) @ ~0.21 g (EST, unpublished)"),
    ("leds",          "fix",  0.6,                 "14x SK6812MINI-E + 10 side (EST)"),
    ("ec11_body",     "fix",  5.0,                 "Bourns PEC11R-4215F-S0024 datasheet MAX (PUBLISHED)"),
    ("js_body",       "fix",  2.5,                 "YA13-FL7.4-B5Ka THT tilt stick (EST; NOT a PSP-class module)"),
    ("js_pins",       "fix",  0.0,                 "included in js_body"),
    ("screws",        "fix",  3.2,                 "4x M3x8 DIN912 @ 0.8 g (PUBLISHED, boltport)"),
    ("switch_bodies", "fix", 24.7,                 "13x Kailh BOX Jade @ 1.9 g (EST; no published mass exists)"),
    ("keycaps",       "fix", 14.3,                 "12x cap_dish_1u_17p5 1.03 + 1x cap_dish_2u_stab 1.93, from this repo's own STL volumes"),
    ("knob",          "fix",  2.4,                 "this project's printed knob_knurled_cup (an ALU knob would be ~8.6 g)"),
    ("stick_cap",     "fix",  0.81,                "printed stick_cap_dish"),
]
# Parts with no geometry in the assembly, placed explicitly.
PAD_EXTRAS = [
    ("M3 heat-set inserts x4", 1.3,  "boss centres", "4x 0.32 g brass (EST)"),
    ("PORON gasket",           2.5,  "datum",        "EST"),
    ("solder + fillets",       1.0,  "datum",        "EST"),
]


def pad_mass_and_cg():
    """Assembled pad (everything ABOVE the mating plane), mass in g and plan CG.

    Computed live from the case module's own solids, so it tracks any change to
    the case rather than quoting a number that silently goes stale."""
    from build123d import CenterOf
    rows, M, Sx, Sy = [], 0.0, 0.0, 0.0
    for name, kind, args, prov in PAD_MASS_MODEL:
        part = getattr(C, name)()
        c = part.center(CenterOf.MASS)
        v = part.volume / 1000.0
        m = v * args[0] * args[1] if kind == "vol" else args
        rows.append((name, v, m, c.X, c.Y, prov))
        M += m
        Sx += m * c.X
        Sy += m * c.Y
    for name, m, where, prov in PAD_EXTRAS:
        pts = C.BOSS_CENTERS if where == "boss centres" else [DATUM]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        rows.append((name, 0.0, m, cx, cy, prov))
        M += m
        Sx += m * cx
        Sy += m * cy
    return rows, M, (Sx / M, Sy / M)


def _circle_exit(g, p, c, R):
    dx, dy = p[0] - g[0], p[1] - g[1]
    ex, ey = g[0] - c[0], g[1] - c[1]
    a = dx * dx + dy * dy
    b = 2 * (ex * dx + ey * dy)
    cc = ex * ex + ey * ey - R * R
    disc = b * b - 4 * a * cc
    if a == 0 or disc < 0:
        return None
    t = (-b + math.sqrt(disc)) / (2 * a)
    return t if t > 0 else None


def _rect_exit(g, p, x0, x1, y0, y1):
    dx, dy = p[0] - g[0], p[1] - g[1]
    ts = []
    for (d, o, lo, hi) in ((dx, g[0], x0, x1), (dy, g[1], y0, y1)):
        if abs(d) > 1e-12:
            ts += [(lo - o) / d, (hi - o) / d]
    ts = [t for t in ts if t > 0]
    return min(ts) if ts else None


# Press points. Force values are the ASSUMPTION set; every one is stated.
#   key presses: Kailh BOX Jade actuates at ~0.5 N; a fast bottom-out peak runs
#     2-3x that, and a deliberate hard press ~2x again -> 1.5 / 3.0 N.
#   encoder push: EC11-class push switches are a 2-4 N class part -> 3.0 / 5.0 N.
#     This is the GOVERNING case and it is an ESTIMATE; the sensitivity is
#     printed with the results.
PRESS_POINTS = [
    ("SW6 centre key",        32.575, 50.75, 14.6, 1.5, 3.0),
    ("SW13 2U key centre",    42.100, 88.85, 14.6, 1.5, 3.0),
    ("SW13 2U cap near edge", 42.100, 97.85, 14.6, 1.5, 3.0),
    ("SW9 far-left key",      13.525, 69.80, 14.6, 1.5, 3.0),
    ("encoder knob centre",   13.525, 12.50, 17.5, 3.0, 5.0),
    ("encoder knob far edge",  7.161,  6.14, 17.5, 3.0, 5.0),
    ("joystick cap",          69.710, 13.37, 19.6, 1.5, 3.0),
]
LATERAL_PUSHES = [("joystick shove", 19.6, 1.5), ("knob side load", 17.5, 1.5)]

SM_DESIGN = 1.5   # required margin at the DESIGN load
SM_ABUSE = 1.0    # required margin at the ABUSE load (i.e. must not tip)


def stability(support, m_pad, cg_pad, m_base, base_h, foot_h, mu):
    """One base's stability. `support` is ("circle", R) or ("rect", x0,x1,y0,y1),
    expressed about the datum. Returns (rows, worst_margin)."""
    W = (m_pad + m_base) * G / 1000.0
    gx = (m_pad * cg_pad[0] + m_base * DATUM[0]) / (m_pad + m_base)
    gy = (m_pad * cg_pad[1] + m_base * DATUM[1]) / (m_pad + m_base)
    g = (gx, gy)

    def exit_t(p):
        return (_circle_exit(g, p, DATUM, support[1]) if support[0] == "circle"
                else _rect_exit(g, p, *support[1:]))

    rows = []
    for (lbl, px, py, _pz, Fd, Fa) in PRESS_POINTS:
        t = exit_t((px, py))
        for tag, F in (("design", Fd), ("abuse", Fa)):
            if t is None or t >= 1.0:
                rows.append((math.inf, f"press {lbl} [{tag} {F:.1f} N]",
                             "cannot tip: press point is INSIDE the support polygon"))
            else:
                Ft = W * t / (1 - t)
                rows.append((Ft / F, f"press {lbl} [{tag} {F:.1f} N]",
                             f"tips at {Ft:.2f} N"))
    for (lbl, pz, F) in LATERAL_PUSHES:
        h = (pz - MATE_Z) + base_h + foot_h
        worst = None
        for a in range(0, 360, 5):
            u = (math.cos(math.radians(a)), math.sin(math.radians(a)))
            t = exit_t((g[0] + u[0] * 500, g[1] + u[1] * 500))
            if t is None:
                continue
            b = t * 500
            if worst is None or b < worst[0]:
                worst = (b, a)
        b, _a = worst
        F_tip, F_slide = W * b / h, mu * W
        if F_slide < F_tip:
            rows.append((math.inf, f"push {lbl} [{F:.1f} N at h={h:.0f} mm]",
                         f"cannot tip: SLIDES at {F_slide:.2f} N before it could tip at {F_tip:.2f} N"))
        else:
            rows.append((F_tip / F, f"push {lbl} [{F:.1f} N at h={h:.0f} mm]",
                         f"tips at {F_tip:.2f} N (b={b:.1f}) BEFORE sliding at {F_slide:.2f} N"))
    return rows, min(r[0] for r in rows)


def ballast_needed(R, m_pad, cg_pad, target_sm, F, p):
    """Base mass (g) required for margin `target_sm` against press F at p."""
    lo, hi = 0.0, 5000.0

    def sm(mb):
        rows, _ = stability(("circle", R), m_pad, cg_pad, mb, 0, 0, 1.0)
        for margin, lbl, _n in rows:
            if p in lbl and f"{F:.1f} N" in lbl:
                return margin
        return math.inf
    if sm(hi) < target_sm:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if sm(mid) >= target_sm:
            hi = mid
        else:
            lo = mid
    return hi


# =========================================================================
# 5. MAIN
# =========================================================================

def _variant_support(name):
    """Support polygon about the datum, and the desk-contact story."""
    # [v2.15] EVERY figure here EXCLUDES FEET — the undersides are flat and
    # feet are the builder's business (owner ruling). Two effects, and they
    # pull in opposite directions, so both are stated:
    #   + the support polygon GROWS: the pedestal rests on its full Ø70 rim
    #     and the wedge on its full footprint, instead of on four Ø7.9 pads.
    #   - mu DROPS: bare printed rigid plastic on a desk, not rubber. MU_HARD
    #     below is deliberately conservative. Lower mu is not a safety loss —
    #     it means the part SLIDES sooner, and sliding is the benign failure;
    #     tipping is the one that matters, and mu does not appear in the tip
    #     condition at all (see the note at the top of section 4).
    x0, x1 = DATUM[0] - BASE_W / 2, DATUM[0] + BASE_W / 2
    y0, y1 = DATUM[1] - BASE_H / 2, DATUM[1] + BASE_H / 2
    if name == "pedestal":
        # [v2.16] The plan silhouette of a VERTICAL cylinder is the circle
        # itself, whatever the tilt cut does to its faces — so the support
        # polygon is exactly r = PED_D/2, not an approximation of an ellipse.
        # base_h here is the STABILITY-MODEL height input: the full-wedge
        # envelope, deliberately conservative for the tip condition (a taller
        # assumed CG understates stability). The pedestal SOLID's true height
        # is lower (~15.43, STL-verified in the configurator's positions data)
        # because the Ø78 circle never reaches the footprint's far edge.
        return ("circle", PED_D / 2.0), BASE_T + tilt_rise(WEDGE_DEG), 0.0, MU_HARD
    if name == "riser":
        # Full-footprint sheet: the whole outline touches the desk. Printed in
        # TPU it is a high-mu contact; in PETG it is MU_HARD. The stability
        # figures below use the WORSE of the two, so the published margin holds
        # for either material.
        return ("rect", x0, x1, y0, y1), RISER_T, 0.0, MU_HARD
    # wedge: rests on its whole footprint
    return (("rect", x0, x1, y0, y1),
            BASE_T + tilt_rise(WEDGE_DEG), 0.0, MU_HARD)


if __name__ == "__main__":
    stl_dir = os.path.join(HERE, "stl")
    par_dir = os.path.join(HERE, "params")
    out_dir = os.path.join(HERE, "outputs")
    for d in (stl_dir, par_dir, out_dir):
        os.makedirs(d, exist_ok=True)

    print("=" * 78)
    print(f"agentpad13 v2.9 base family — CENTRAL MOUNT contract, WALL {C.WALL}")
    print("=" * 78)

    # ---- the interface contract, restated from the case module -----------
    bolt_circle = math.hypot(PEG_PITCH, PEG_PITCH)
    print(f"[contract] datum ({DATUM[0]}, {DATUM[1]}) = centre of the case outline")
    print(f"[contract] 4 pockets Ø{PEG_BORE} x {PEG_POCKET_DEPTH} deep at "
          f"(±{PEG_PITCH/2}, ±{PEG_PITCH/2}) -> bolt circle Ø{bolt_circle:.2f}")
    print(f"[contract] smallest base carrying the whole pattern with a 3 mm "
          f"wall = Ø{bolt_circle + PEG_BORE + 6:.1f}")
    print(f"[contract] peg {PEG_LEN} long, {PEG_TIP_CHAMFER} tip chamfer; tray "
          f"mouth chamfer MEASURED at {TRAY_POCKET_MOUTH_CHAMFER} (not the "
          f"{C.EFC_CHAMFER} EFC_CHAMFER advertises — OCCT refuses 0.4 and 0.3 "
          "on that face and settles at 0.2, at HEAD as well as here)")
    print(f"[contract] ladder {PEG_LADDER} -> CAD diametral clearance "
          f"{PEG_BORE - max(PEG_LADDER):.2f}..{PEG_BORE - min(PEG_LADDER):.2f}; "
          f"rigid default {PEG_NOM}, TPU default {PEG_TPU}")

    assert max(PEG_LADDER) < PEG_BORE, "ladder must stay CAD-clearance in the pocket"
    assert PEG_LEN + 0.2 <= PEG_POCKET_DEPTH, "peg would bottom out before the base seats"
    assert PEG_TIP_CHAMFER < PEG_LEN, "tip chamfer must not consume the whole peg"

    # ---- keep-outs the contract must publish -----------------------------
    svc_r = svc_corner_radius()
    raw_slot_r = min(math.hypot(px - DATUM[0], py - DATUM[1])
                     for (_l, x0, x1, y0, y1, _z0, _z1) in C._TACTS
                     for px in (x0 - C.SVC_CLEAR, x1 + C.SVC_CLEAR)
                     for py in (y0 - C.SVC_CLEAR, y1 + C.SVC_CLEAR))
    print(f"[keepout] BOOT/RESET slots: nearest tray-slot corner {raw_slot_r:.3f} mm "
          f"from the datum (relieved window corner {svc_r:.3f}) -> a windowless "
          f"circular base caps at Ø{2*raw_slot_r:.2f}")
    # [v2.16] THE SLOT KEEP-OUT, RE-DERIVED — read this before changing PED_D.
    #
    # The old rule was a blanket "windowless base must clear the slot by 2 mm",
    # chosen when the pedestal was Ø70 and had 4.18 mm to spare. It is now a
    # BINDING constraint rather than a comfortable one, and it collides head-on
    # with stability: the largest 2 mm-compliant circle is Ø74.36, and a solid
    # Ø74.36 tilted drum reaches only SM 1.45 against the 1.50 design bar. So a
    # windowless, unballasted pedestal CANNOT satisfy both the old rule and the
    # stability bars. Measured, whole range, solid print:
    #     Ø70.00  keep-out 4.18  SM design 1.19  abuse 0.71   design FAIL
    #     Ø74.36  keep-out 2.00  SM design 1.45  abuse 0.87   design FAIL
    #     Ø76.00  keep-out 1.18  SM design 1.56  abuse 0.94   abuse  FAIL
    #     Ø78.00  keep-out 0.18  SM design 1.72  abuse 1.03   both OK
    #
    # Ø78 is therefore not a preference, it is the only point that clears both
    # bars without ballast — which is what the owner asked for ("No need for
    # the ballast if the diameter is reasonable enough").
    #
    # The keep-out is now asserted against the REAL slot geometry instead of a
    # blanket number. The 39.182 figure above is the slot's BBOX corner; the
    # tray actually cuts those slots with SVC_TOOL_R corner radii, so the
    # nearest real material sits 39.518 mm out and the true clearance at Ø78 is
    # 0.518 mm, not 0.182. The floor below is set against that real number and
    # is a print-tolerance budget: a base would have to print ~1 mm oversize on
    # DIAMETER before it began to overlap a slot, and it would still not block
    # the tool, because the slots are 7-10 mm wide and the encroachment would
    # be one rim corner. Anything tighter than this, or any larger diameter,
    # requires the symmetric service-window pair instead (full_base already
    # builds it — pass windows=True) and is a design change, not a tweak.
    true_slot_r = min(
        math.hypot(cx - DATUM[0], cy - DATUM[1]) - C.SVC_TOOL_R
        for (_l, x0, x1, y0, y1, _z0, _z1) in C._TACTS
        for cx in (x0 - C.SVC_CLEAR + C.SVC_TOOL_R, x1 + C.SVC_CLEAR - C.SVC_TOOL_R)
        for cy in (y0 - C.SVC_CLEAR + C.SVC_TOOL_R, y1 + C.SVC_CLEAR - C.SVC_TOOL_R))
    assert PED_D / 2.0 < raw_slot_r, (
        f"PEDESTAL FAIL (HARD): Ø{PED_D} reaches {PED_D/2:.3f} and the nearest "
        f"BOOT/RESET slot corner is {raw_slot_r:.3f} — the base would COVER the "
        "service slot. Either shrink it or give it the symmetric window pair "
        "(full_base(..., windows=True)).")
    assert PED_D / 2.0 + PED_SLOT_KEEPOUT <= true_slot_r, (
        f"PEDESTAL FAIL: Ø{PED_D} leaves {true_slot_r - PED_D/2.0:.3f} mm to the "
        f"real slot edge, under the {PED_SLOT_KEEPOUT} mm print-tolerance floor. "
        "See the derivation above: shrinking costs stability (Ø74.36 is only "
        "SM 1.45 vs the 1.50 design bar), so the fix is the symmetric window "
        "pair, not a smaller circle.")
    print(f"[keepout] pedestal Ø{PED_D:g}: {raw_slot_r - PED_D/2.0:.3f} mm to the "
          f"slot BBOX corner, {true_slot_r - PED_D/2.0:.3f} mm to the REAL "
          f"(radiused) slot edge; floor {PED_SLOT_KEEPOUT} mm")

    # ---- pad mass model --------------------------------------------------
    print("-" * 78)
    rows, M_PAD, CG_PAD = pad_mass_and_cg()
    print(f"[mass] assembled pad = {M_PAD:.1f} g; plan CG ({CG_PAD[0]:.2f}, "
          f"{CG_PAD[1]:.2f}) = datum {CG_PAD[0]-DATUM[0]:+.2f}, "
          f"{CG_PAD[1]-DATUM[1]:+.2f} mm. The pad's own CG lands within 1 mm of "
          "the case-outline centre, which is WHY that centre is the datum.")
    for n, v, m, cx, cy, prov in sorted(rows, key=lambda r: -r[2])[:6]:
        print(f"[mass]   {n:16s} {m:6.2f} g   {prov[:60]}")
    print(f"[mass]   ... {len(rows)-6} smaller rows; full table in params JSON")

    # ---- what the physics demands of a circular base ---------------------
    print("-" * 78)
    print("[stability] governing case = a firm press on the ENCODER KNOB EDGE, "
          f"{math.hypot(7.161-DATUM[0], 6.14-DATUM[1]):.1f} mm from the datum. "
          "It beats SW13 (the farthest KEY) because the knob is farther out AND "
          "an EC11 push is a 2-4 N part against a keyswitch's ~1.5 N.")
    need = {}
    for D in (50, 60, 65, 70, 74, PED_D, 80):
        a = ballast_needed(D / 2.0, M_PAD, CG_PAD, SM_DESIGN, 3.0, "encoder knob far edge")
        b = ballast_needed(D / 2.0, M_PAD, CG_PAD, SM_ABUSE, 5.0, "encoder knob far edge")
        need[D] = (a, b)
        print(f"[stability]   Ø{D:<3.0f} needs {a:6.0f} g of base for SM>={SM_DESIGN} "
              f"at 3 N, {b:6.0f} g for SM>={SM_ABUSE} at 5 N")
    M_BASE_REQ = max(need[PED_D])
    print(f"[stability] -> a Ø{PED_D:g} pedestal must weigh at least "
          f"{M_BASE_REQ:.0f} g. [v2.16] THAT IS NOW REACHABLE IN PLASTIC — which "
          "is the whole reason the ballast could go. It needs a SOLID print: see "
          "the per-solidity margins below.")

    # ---- build, gate and export ------------------------------------------
    print("-" * 78)
    gate = {}
    variants_rec = {}
    for (name, kind, tilt, _t0) in VARIANTS:
        part = base(name, PEG_NOM)
        vol = part.volume / 1000.0
        support, base_h, foot_p, mu = _variant_support(name)

        if name == "pedestal":
            # [v2.16] NO BALLAST. Mass is whatever the print weighs, so the
            # honest variable is INFILL, and it is published as a requirement
            # rather than assumed. PED_SOLIDITY is the instruction: print solid.
            base_g = vol * RHO["PLA"] * PED_SOLIDITY
            print(f"[{name:8s}] Ø{PED_D:g} tilted drum ({WEDGE_DEG:g} deg) = wedge "
                  f"INTERSECT cylinder | {vol:.1f} cm3 -> {base_g:.0f} g at "
                  f"{PED_SOLIDITY:.0%} solidity | NO ballast, NO service window")
            for _s in (1.00, 0.62):
                _m = vol * RHO["PLA"] * _s
                _r, _w = stability(support, M_PAD, CG_PAD, _m, base_h, 0.0, mu)
                _fin = [x[0] for x in _r if x[0] != math.inf]
                print(f"[{name:8s}]   solidity {_s:.2f} -> {_m:5.1f} g, worst SM "
                      f"{min(_fin, default=math.inf):.2f}")
            print(f"[{name:8s}] physics wants {M_BASE_REQ:.0f} g for the 5 N abuse "
                  f"case; a solid print is {vol * RHO['PLA']:.0f} g, a 3-wall/20% "
                  f"gyroid print only {vol * RHO['PLA'] * PRINT_FILL:.0f} g -> "
                  "PRINT THIS ONE SOLID (the docs say so plainly)")
        elif name == "riser":
            base_g = vol * RHO["TPU95"] * 0.95
            print(f"[{name:8s}] {BASE_W:.1f} x {BASE_H:.1f} x {RISER_T:g} flat sheet | "
                  f"{vol:.1f} cm3 -> {base_g:.0f} g in TPU | needs NO ballast: full "
                  "footprint means every control is inside the support polygon")
        else:
            base_g = vol * RHO["PLA"] * 0.42
            print(f"[{name:8s}] {WEDGE_DEG:g} deg wedge | {vol:.1f} cm3 -> "
                  f"{base_g:.0f} g at 20% infill | rise {tilt_rise(WEDGE_DEG):.2f} mm "
                  f"over {BASE_H:.1f}")

        srows, worst = stability(support, M_PAD, CG_PAD, base_g, base_h, foot_p, mu)
        finite = [r for r in srows if r[0] != math.inf]
        cannot = len(srows) - len(finite)
        print(f"[{name:8s}] stability: {cannot}/{len(srows)} load cases CANNOT tip; "
              f"worst finite margin {min([r[0] for r in finite], default=math.inf):.2f}")
        for m_, lbl, note in sorted(finite)[:3]:
            print(f"[{name:8s}]    SM={m_:5.2f}  {lbl:44s} {note}")
        assert worst >= SM_ABUSE, f"{name} STABILITY FAIL: worst margin {worst:.2f}"

        variants_rec[name] = {
            "kind": kind, "tilt_deg": tilt, "body_mm": _t0,
            "feet": "none — flat underside (v2.15)",
            "model_volume_cm3": round(vol, 3),
            "base_mass_g": round(base_g, 1),
            "support": list(support), "base_height_mm": round(base_h, 2),
            "foot_protrusion_mm": round(foot_p, 2), "assumed_mu": mu,
            "worst_margin": (None if worst == math.inf else round(worst, 3)),
            "load_cases": [{"margin": (None if m_ == math.inf else round(m_, 3)),
                            "case": lbl, "note": note} for m_, lbl, note in srows],
            "stl": {},
        }
        gate[name] = part

    # ---- THE DESIGN LAW: x-symmetry, every variant, every build ----------
    print("-" * 78)
    for (name, _k, _t, _f) in VARIANTS:
        assert_x_symmetric(gate[name], name)
        assert_pegs_intact(gate[name], PEG_NOM, name)
        _tip = gate[name].bounding_box().max.Z
        assert abs(_tip - (MATE_Z + PEG_LEN)) < 1e-9, (
            f"BASE '{name}': peg tips reach z={_tip:.4f}, expected exactly "
            f"{MATE_Z + PEG_LEN} (MATE_Z + PEG_LEN)")
        print(f"[law] {name:8s} x-symmetric about the pattern centreline "
              f"x={DATUM[0]} — exact; pegs identical to reference, tips at "
              f"z={_tip:.2f}")
    # The FIT GAUGE is deliberately EXEMPT. The owner's ruling is about BASES
    # ("they should be symmetric over x by definition"); the gauge is not a
    # base but a disposable measuring aid, and its asymmetry IS its function —
    # rung n is identified by n raised dots, so a symmetric gauge could not
    # tell you which rung you were holding. Exempting it is scoping the law
    # correctly, not weakening it.
    print(f"[law] {'gauge':8s} EXEMPT — a measuring aid, not a base; its "
          "n-dot rung marking is asymmetric BY FUNCTION")

    # ---- STL export: every variant on every ladder rung + the gauge -------
    print("-" * 78)
    for (name, _k, _t, _f) in VARIANTS:
        for pd in PEG_LADDER:
            fn = os.path.join(stl_dir, f"base_{name}_peg_{_rung_name(pd)}.stl")
            export_stl(export_pose(base(name, pd)), fn)
            variants_rec[name]["stl"][_rung_name(pd)] = os.path.basename(fn)
    gfn = os.path.join(stl_dir, "base_fit_gauge.stl")
    export_stl(export_pose(fit_gauge()), gfn)
    print(f"[export] {len(VARIANTS)} variants x {len(PEG_LADDER)} rungs + fit gauge")

    # ---- printability, measured in the real print pose -------------------
    for (name, _k, tilt, _f) in VARIANTS:
        p = print_pose(gate[name], tilt)
        bb = p.bounding_box()
        try:
            inspect(p, method=FDM(wall_min_mm=1.2), out=out_dir, name=f"base_{name}")
            st = "ok"
        except SystemExit:
            st = "ADVISORY (see JSON)"
        print(f"[print] {name:8s} bed {bb.size.X:.1f} x {bb.size.Y:.1f}, height "
              f"{bb.size.Z:.2f} mm, desk face on the bed, no support -> {st}")

    # ---- khana hard gate, one per variant --------------------------------
    print("-" * 78)
    print("[print] pedestal min_wall: the v2.15 note here described a Ø70 disc "
          "with a blind ballast cavity and its ribbed roof. [v2.16] NONE OF THAT "
          "EXISTS — the pedestal is now a SOLID tilted drum (wedge INTERSECT "
          "cylinder): no cavity, no ribs, no internal wall to assert, and its "
          "only overhang is the tilted desk face itself, which is printed ON the "
          "bed. Any small min_wall reading is the same grazing artifact the "
          "wedge shows, documented immediately below.")
    print("[print] wedge min_wall reads 0.3049 mm. SAME ESTIMATOR ARTIFACT, and "
          "v2.15 made it visible rather than causing it. Proof, measured three "
          "ways: the identical solid at tilt 0 reads exactly 2.4000 (= BASE_T, "
          "the true minimum section); tilted, with a CLEAN desk face, it reads "
          "0.3049 because the sampler grazes the feather geometry where the "
          "tilted desk plane meets the perimeter wall; tilted WITH the old foot "
          "recesses it read 1.3310 — also an artifact, the recesses merely "
          "changed which sample won. Deleting recesses only ADDS material, so it "
          "is geometrically impossible for it to thin the part. The wedge's true "
          "minimum section is BASE_T at the NEAR edge, asserted analytically "
          "below.")
    assert BASE_T >= 1.2, "wedge/pedestal minimum section (NEAR edge) below 1.2"
    assert RISER_T >= 1.2, "riser section below 1.2"
    print(f"[print] analytic minimum sections: wedge/pedestal BASE_T {BASE_T} mm at "
          f"the NEAR edge (wedge thickens to {BASE_T + tilt_rise(WEDGE_DEG):.2f} mm "
          f"at the FAR edge); riser {RISER_T} mm uniform. [v2.16] the pedestal has "
          "no cavity and no window, so it has NO internal wall to assert — it is a "
          "solid tilted drum.")
    print("-" * 78)
    tray_solid = C.tray()
    band_solid = C.band()
    # Positive regression alarm: a solid the exact shape of the four tray
    # pockets. If anyone deletes the pockets from tray(), the pegs stop
    # interfering with this witness and the gate FAILS LOUDLY.
    witness = None
    for (px, py) in PEG_XY:
        w = _cyl(PEG_BORE, MATE_Z, MATE_Z + PEG_POCKET_DEPTH, px, py)
        witness = w if witness is None else witness + w
    for (name, _k, _t, _f) in VARIANTS:
        a = (Assembly()
             .with_part("base", gate[name])
             .with_part("tray", tray_solid)
             .with_part("band", band_solid)
             .with_part("pocket_witness", witness)
             .assert_no_interference("base", "tray")
             .assert_no_interference("base", "band")
             .assert_interference("base", "pocket_witness",
                                  reason="the pegs must occupy the tray's four "
                                         "BASE_MOUNT pockets; if this stops "
                                         "failing, tray() lost the interface"))
        check(a, out=os.path.join(out_dir, name))
        print(f"[gate] {name:8s} outputs/{name}/mechanism.json")

    # ---- the publishable interface spec ----------------------------------
    spec = {
        "part": "agentpad13 tray base",
        "rev": "v2.9",
        "license": "CERN-OHL-W v2",
        "contract": {
            "datum": {
                "where": "centre of the case outline in plan",
                "board_coords": list(DATUM),
                "how_to_find_it": (
                    f"the band outer ({BAND_W:.1f} x {BAND_H:.1f}) and the tray "
                    f"outline ({C.TRAY_W:.1f} x {C.TRAY_H:.1f}) are both centred "
                    "on it — measure the finished case, no source read needed"),
            },
            "mating_plane": {"z": MATE_Z,
                             "what": "flat tray bottom; 2.0 mm below band bottom",
                             "rule": "all base material at or below this plane"},
            "orientation": {
                "far_edge": "y = 0, the USB / control-band edge, away from the user",
                "near_edge": "y = 100, the 2U key edge",
                "landmark": "the USB port is on the FAR edge",
                "symmetry": "the peg pattern is 4-fold symmetric — a base mounts "
                            "in any of four 90 deg orientations"},
            "features": {
                "count": 4, "type": "blind flat-bottomed cylindrical pocket",
                "diameter_mm": PEG_BORE, "depth_mm": PEG_POCKET_DEPTH,
                "positions_from_datum": [[round(p[0] - DATUM[0], 3),
                                          round(p[1] - DATUM[1], 3)] for p in PEG_XY],
                "pitch_mm": PEG_PITCH,
                "bolt_circle_mm": round(bolt_circle, 3),
                "mouth_chamfer_mm": TRAY_POCKET_MOUTH_CHAMFER,
                "mouth_chamfer_note": (
                    "MEASURED, not nominal. EFC_CHAMFER is 0.4 but OCCT refuses "
                    "0.4 and 0.3 on the tray's bottom face and _safe_chamfer "
                    "settles at 0.2. Design the peg against 0.2."),
                "floor_above_pocket_mm": round(C.TRAY_T - PEG_POCKET_DEPTH, 3),
            },
            "peg": {"ladder_mm": PEG_LADDER, "default_rigid": PEG_NOM,
                    "default_tpu": PEG_TPU, "length_mm": PEG_LEN,
                    "tip_chamfer_mm": PEG_TIP_CHAMFER,
                    "seat_gap_mm": round(PEG_POCKET_DEPTH - PEG_LEN, 3),
                    "rule": "the tray side is CAD-nominal and carries NO "
                            "allowance; all fit lives on the peg",
                    "gauge": "print base_fit_gauge.stl, push each peg into any "
                             "pocket, keep the rung that holds. Marks are raised "
                             "dots: n dots = rung n, smallest first."},
            "load_rating": {
                "path": "vertical load goes through the FLAT MATING PLANE, never "
                        "through the pegs. The pegs locate and resist shear.",
                "peg_bearing_area_mm2": round(PEG_BORE * PEG_LEN, 2),
                "note": "at even 30 MPa bearing that is ~250 N per peg against "
                        "single-digit-newton service loads, so engagement depth "
                        "is not the limiting factor — location is the job.",
            },
            "keep_outs": {
                "service_slots": {
                    "what": "BOOT / RESET tact access, pierced through the tray floor",
                    "tray_slot_bbox": [round(min(x0 - C.SVC_CLEAR for (_l, x0, x1, y0, y1, _a, _b) in C._TACTS), 2),
                                       round(max(x1 + C.SVC_CLEAR for (_l, x0, x1, y0, y1, _a, _b) in C._TACTS), 2),
                                       round(min(y0 - C.SVC_CLEAR for (_l, x0, x1, y0, y1, _a, _b) in C._TACTS), 2),
                                       round(max(y1 + C.SVC_CLEAR for (_l, x0, x1, y0, y1, _a, _b) in C._TACTS), 2)],
                    "rule": "any base covering this area MUST carry a through "
                            "window; a base that stays inside Ø"
                            f"{2*raw_slot_r:.1f} about the datum never reaches it",
                    "max_windowless_circular_base_mm": round(2 * raw_slot_r, 2)},
                "usb": {"rule": "the USB face is on the FAR edge above the mating "
                                "plane; a wedge that raises the far edge reduces "
                                "plug clearance to the desk"},
            },
        },
        "stability": {
            "method": "see agentpad13_base.py section 4 — CoP walk for vertical "
                      "press, tip-vs-slide for horizontal push",
            "pad_mass_g": round(M_PAD, 1),
            "pad_cg_plan": [round(CG_PAD[0], 3), round(CG_PAD[1], 3)],
            "pad_cg_offset_from_datum": [round(CG_PAD[0] - DATUM[0], 3),
                                         round(CG_PAD[1] - DATUM[1], 3)],
            "governing_case": "firm press on the encoder knob edge, "
                              f"{math.hypot(7.161-DATUM[0], 6.14-DATUM[1]):.1f} mm from the datum",
            "margins_required": {"design": SM_DESIGN, "abuse": SM_ABUSE},
            "min_base_mass_by_diameter_g": {
                str(k): {"sm1.5_at_3N": (None if v[0] is None else round(v[0], 1)),
                         "sm1.0_at_5N": (None if v[1] is None else round(v[1], 1))}
                for k, v in need.items()},
            "ruling": (
                "A free-standing base smaller than the footprint must carry the "
                f"mass itself. A Ø{PED_D:g} pedestal needs {M_BASE_REQ:.0f} g, "
                "which a SOLID print in PLA/PETG does reach — so v2.16 deletes "
                "the ballast and publishes an infill requirement instead. At "
                f"{PRINT_FILL:.0%} effective solidity (3 walls / 20% gyroid) it "
                "clears the 3 N design case but NOT the 5 N abuse case."),
            "mass_model": [{"part": n, "volume_cm3": round(v, 3), "mass_g": round(m, 3),
                            "centroid_xy": [round(cx, 3), round(cy, 3)],
                            "provenance": prov} for n, v, m, cx, cy, prov in rows],
            "assumptions": [
                "Kailh BOX Jade 1.9 g — NO published mass exists; +/-25% is "
                "+/-3 g across 13 switches",
                "EC11 push force 2-4 N class -> 3.0 N design / 5.0 N abuse. This "
                "is the GOVERNING input and it is an ESTIMATE",
                "keyswitch press 1.5 N design / 3.0 N abuse",
                f"mu = {MU_HARD} bare printed plastic on desk, {MU_TPU} TPU on desk "
                "(v2.15: feet deleted, so no rubber contact is assumed)",
                "printed-part fill fractions are stated per row in mass_model",
            ],
            "resolved_2026_08_20": (
                "The long-standing 3M SJ61A1 dimension conflict (Ø7.92 x 5.08 "
                "per DigiKey/3M vs Ø7.9 x 2.2 as modelled) is MOOT for bases: "
                "v2.15 deletes every foot recess, so no base geometry, stance "
                "figure or desk plane in this module depends on a bumpon "
                "dimension any more. Feet are unofficial."),
        },
        "print": {"orientation": "desk face on the bed, every variant",
                  "support": "none",
                  "pedestal_infill": (
                      f"PRINT SOLID. The pedestal carries no ballast in v2.16 — its "
                      f"own printed mass is what keeps the device upright, so infill "
                      f"is a STRUCTURAL setting here, not a speed/cost one. A solid "
                      f"print clears the 5 N abuse case; a normal 3-wall / 20 % "
                      f"gyroid print ({PRINT_FILL:.0%} effective solidity) clears the "
                      f"3 N design case but NOT abuse."),
                  "riser_material": "TPU for a grip base, PETG/PLA for a rigid stand "
                                    "— same file either way",
                  "ballast": "none — deleted in v2.16 (owner: \"No need for the "
                             "ballast if the diameter is reasonable enough\")"},
        "variants": variants_rec,
    }
    with open(os.path.join(par_dir, "agentpad13_base_params.json"), "w") as f:
        json.dump(spec, f, indent=2)
    print(f"[params] {os.path.join('params', 'agentpad13_base_params.json')}")

    # ---- INTERFACE.md: the spec a third party actually reads --------------
    # GENERATED, never hand-edited, so the published contract cannot drift from
    # the geometry. CASE-V2-NOTES §22 is the internal ledger; this is the page a
    # stranger on the GitHub mirror lands on.
    ft = spec["contract"]["features"]
    pg = spec["contract"]["peg"]
    ko = spec["contract"]["keep_outs"]
    NL = chr(10)
    pos = ", ".join(f"({x:+g}, {y:+g})" for x, y in ft["positions_from_datum"])
    mass_rows = NL.join(
        f"| Ø{k} | {v['sm1.5_at_3N']:.0f} g | {v['sm1.0_at_5N']:.0f} g |"
        for k, v in spec["stability"]["min_base_mass_by_diameter_g"].items())
    var_rows = NL.join(
        "| `{n}` | {o} | {m} | {b} |".format(
            n=n,
            o=(f"Ø{PED_D:g} tilted drum, {WEDGE_DEG:g} deg"
               if n == "pedestal" else
               f"{BASE_W:.1f} x {BASE_H:.1f} full footprint"
               + (f", {r['tilt_deg']:g} deg back-raised" if r["tilt_deg"]
                  else f" x {RISER_T:g} mm flat")),
            m=f"{r['base_mass_g']:.0f} g",
            b=("**print SOLID** — its own mass is the ballast"
               if n == "pedestal" else "none"))
        for n, r in variants_rec.items())
    knob_r = math.hypot(7.161 - DATUM[0], 6.14 - DATUM[1])
    sb = ko["service_slots"]["tray_slot_bbox"]

    md = f"""# agentpad13 — tray base interface

**Design your own base.** The tray carries four pockets near its centre. Put
four matching pegs on anything you like and it mounts. The interface does not
care how big your base is or what shape it is.

License: CERN-OHL-W v2. GENERATED by `agentpad13_base.py` — do not hand-edit.

## The datum

The centre of the case outline, in plan. The band outer
({BAND_W:.1f} x {BAND_H:.1f} mm) and the tray outline
({C.TRAY_W:.1f} x {C.TRAY_H:.1f} mm) are **both** centred on it, so you can find
it with a ruler on a finished case. Everything below is measured from there.

**Orientation.** The USB port is on the FAR edge, away from you. The pattern is
4-fold symmetric, so a base fits in any of four 90 deg rotations.

## The four pockets

| | |
|---|---|
| count | {ft["count"]} |
| diameter | **Ø{ft["diameter_mm"]} mm** |
| depth | **{ft["depth_mm"]} mm** below the mating plane |
| positions from datum | {pos} mm |
| square pitch | {ft["pitch_mm"]} mm (bolt circle Ø{ft["bolt_circle_mm"]}) |
| mouth chamfer | {ft["mouth_chamfer_mm"]} x 45 deg |
| mating plane | the flat tray bottom — keep all your material below it |

Smallest base that carries the whole pattern with a 3 mm wall:
**Ø{bolt_circle + PEG_BORE + 6:.1f} mm.**

## Your pegs

| | |
|---|---|
| length | {pg["length_mm"]} mm — leaves a {pg["seat_gap_mm"]} mm gap so the base seats on its FACE, not on peg tips |
| tip chamfer | {pg["tip_chamfer_mm"]} mm |
| fit ladder | **{" / ".join(str(v) for v in pg["ladder_mm"])} mm** |
| start with | {pg["default_rigid"]} in rigid filament, **{pg["default_tpu"]} in TPU** |

The tray side is CAD-nominal and carries **no** allowance — all the fit lives on
your peg. Print `stl/base_fit_gauge.stl`, push each peg into any pocket, keep
the rung that holds. The gauge is marked with raised dots: n dots = rung n,
smallest first.

TPU compresses instead of shearing the pocket wall, so it wants the **tight**
rung, not the loose one.

## Load path — read this before you make it thin

Vertical load goes through the **flat mating plane**, never through the pegs.
The pegs locate the base and take shear. Each has
{pg["length_mm"] * ft["diameter_mm"]:.1f} mm2 of bearing, about 250 N at 30 MPa,
against single-digit-newton service loads. Engagement depth is not your limiting
factor; flatness of the mating face is.

## Keep-outs

- **BOOT / RESET service slots**, x {sb[0]}..{sb[1]}, y {sb[2]}..{sb[3]} mm. If
  your base covers this area it **must** carry a through window. A base that
  stays inside **Ø{ko["service_slots"]["max_windowless_circular_base_mm"]} mm**
  about the datum never reaches it.
- **Feet are not part of the design.** Every base underside is FLAT — no
  recesses, no bolt circle, no prescribed part. Stick on whatever you like,
  wherever you like; every stance figure below EXCLUDES feet.
- **USB face** is on the far edge, above the mating plane. A wedge that raises
  the far edge eats plug-to-desk clearance.

## Will it tip over? (small bases only)

The assembled pad is **{M_PAD:.0f} g**, with its centre of mass within 1 mm of
the datum. A base narrower than the footprint makes it cantilever. The worst
load is a firm press on the **encoder knob edge**, {knob_r:.0f} mm out — not the
farthest key.

Minimum base mass for a **circular** base, to hold a 1.5x margin at a 3 N press
and not tip at all at 5 N:

| diameter | >=1.5x at 3 N | no tip at 5 N |
|---|---|---|
{mass_rows}

**This is why the pedestal must be printed SOLID.** At Ø{PED_D:g} its own
printed mass is the only thing resisting the tip, so infill is a structural
setting here, not a speed one. A solid print clears the 5 N abuse case; a normal
3-wall / 20 % gyroid print clears the 3 N design case but not abuse. The
full-footprint `riser` and `wedge` need nothing at all — every control already
sits inside their support polygon.

Full method and the per-part mass model are in
`params/agentpad13_base_params.json` under `stability`. Several inputs are
estimates and are labelled as such — notably the encoder push force, which is
what sizes everything here.

## Reference bases in this folder

| variant | outline | mass | ballast |
|---|---|---|---|
{var_rows}

All three print **desk face on the bed, no support**.
"""
    with open(os.path.join(HERE, "INTERFACE.md"), "w") as f:
        f.write(md)
    print("[spec]   INTERFACE.md (generated — the page a third party reads)")
    print("=" * 78)

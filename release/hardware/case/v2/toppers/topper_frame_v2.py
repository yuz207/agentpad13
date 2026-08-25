"""work-loudest v5 toppers — SHARED FRAME (v2 family).

The single source of cited facts, the collision law, the profile helpers and
the gate primitives used by BOTH v2 topper scripts:

    encoder_knob_v2.py   Knob A (helical knurl) / B2 (scoop) / C (cross-hatch)
    stick_topper_v2.py   Nub C2 (seven-dot) / one-piece TPU puck

Run either with the khana python (has build123d):

    /Users/yuanz/.local/share/uv/tools/cad-khana/bin/python encoder_knob_v2.py
    /Users/yuanz/.local/share/uv/tools/cad-khana/bin/python stick_topper_v2.py

This module has a __main__ of its own that runs the frame-level gates (the
collision law, the keycap chain cross-check and their negative controls) and
prints the transcript, so the shared arithmetic can be audited on its own.

------------------------------------------------------------------------------
Coordinate frame  (identical to agentpad13_case_v2.py)
    origin xy = the part's own axis (knob -> RE1 13.525,12.5;
                                     stick -> JS1 69.71,13.37)
    +Z        = up;  z = 0 = PCB TOP face;  z = +5.0 = deck (plate top)

    *** THE DESIGN FRAME IS LEFT-HANDED *** (x right, y DOWN from raw KiCad
    board coordinates, z up) while STL and STEP are right-handed.  Every solid
    built here is therefore the ENANTIOMORPH of the intended physical part and
    MUST be mirrored at export -- see export_print_frame() and the chirality
    section below.  [CASE:1074-1118, 2474-2483]
------------------------------------------------------------------------------

SOURCES.  Every number below is transcribed from a PRIMARY document or from a
repo file that is read-only to this module; the tag is carried on the line.

    [ALPS]   Alps Alpine "11 mm Size Metal Shaft Type EC11E Series" catalogue,
             Update 2510, p.2 Drawing No.2 (vertical / flat actuator /
             actuator length 20 / with push-on switch).  The board is
             footprinted RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm
             [hardware/pcb/v5_7.kicad_pcb:754].
    [BOURNS] Bourns PEC11R datasheet REV 04/26 p.2 outline + p.3 Flatted Shaft
             L/LB/F table  (compatibility table only)
    [YA13]   YTL drawing CF-G04-J13-016  (joystick JS1)
    [KEYCAP] hardware/case/keycaps/keycaps.py + params/keycap_params.json
    [CASE]   hardware/case/agentpad13_case_v2.py  (line numbers given)
    [TOPPER] hardware/case/toppers/stick_cap.py / encoder_knob.py  (v1, shipped)
    [CM-EST] ESTIMATE off Codex Micro imagery — NOT a published dimension
    [TPU-EST] engineering judgement about TPU — NOT a datasheet value
"""

import math
import os

from build123d import (
    Axis,
    Box,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    export_stl,
    mirror,
    revolve,
)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

D2R = math.radians


# =========================================================================
# 1. CASE / PART FACTS
# =========================================================================

DECK_Z = 5.0             # [CASE:348,1029] plate top; z = 0 is the PCB top
PLATE_BOT_Z = 3.4        # [CASE] plate underside

# --- the keycap vertical chain (STEM-INSERTED, not cap+switch stacked) ----
# The cap does not sit ON the switch: it slides ONTO the stem and swallows it.
SW_SHOULDER_H = 6.60     # [KEYCAP:289] Cherry MX stem shoulder above the deck
SW_CROSS_H = 3.60        # [KEYCAP:290] exposed cross above that shoulder
SW_STEM_TOP_H = 10.20    # [KEYCAP:291] = 6.60 + 3.60
SW_HOUSING_TOP_H = 6.01  # [KEYCAP:292] fixed top-housing face
CAP_SOCKET_DEPTH = 3.80  # [KEYCAP:718] the cap's stem socket depth
CAP_MOUNT_RECESS = 0.0   # [KEYCAP:430]
CAP_H_DISH = 6.00        # [KEYCAP:1079,1085] CAVITY_D 4.5 + TOP_T 1.5
CAP_H_PLATEAU = 6.60     # [KEYCAP:1081] + STEP_H 0.6
KEYCAP_W = 17.50         # [KEYCAP CAP_SIZES 17p5 PRIMARY] + [STL] bbox

KEYCAP_RIM_Z = DECK_Z + SW_SHOULDER_H - CAP_MOUNT_RECESS      # +11.6
KEYCAP_TOP_DISH_Z = KEYCAP_RIM_Z + CAP_H_DISH                 # +17.6
KEYCAP_TOP_PLATEAU_Z = KEYCAP_RIM_Z + CAP_H_PLATEAU           # +18.2
INSERTION_N = min(CAP_SOCKET_DEPTH, SW_CROSS_H)               # 3.60
NAIVE_STACK_TOP_Z = DECK_Z + SW_STEM_TOP_H + CAP_H_DISH       # +21.2 WRONG

KEYCAP_Z0, KEYCAP_Z1 = KEYCAP_RIM_Z, KEYCAP_TOP_DISH_Z        # gate band

# --- joystick JS1 : YTL YA13-FL7.4-B5Ka(45-10)-R-Y06 ---------------------
JS1_X, JS1_Y = 69.71, 13.37     # [CASE:335 / contract_v4 refs.JS1]
PIVOT_Z = 6.1                   # [YA13 front elev, dim "6.1"]
FRAME_TOP_Z = 11.0              # [YA13 front elev, dim "11"]
FRAME_TOP_TOL = 0.5             # [YA13 tol block: 10..100 -> +/-0.5]
BLADE_TIP_Z = 18.4              # [YA13 front elev, dim "18.4"]
TILT_FULL = 30.0                # [YA13 "60 deg" mechanical fan / 2]
TILT_RESTRICTED = 22.5          # pot electrical half-angle 45/2 [YA13 spec 1.1]
JS_FRAME_HALF = 6.5             # [CASE:662] 13x13 frame half-extent

SOCKET_DEPTH = 4.0              # [TOPPER stick_cap.py:100] DESIGN CHOICE
SOCKET_MOUTH_Z = round(BLADE_TIP_Z - SOCKET_DEPTH, 6)    # +14.4
SOCKET_ROOF_Z = BLADE_TIP_Z                              # +18.4
ROOF_T = 1.2                    # [TOPPER stick_cap.py:103] solid over the tip
CAP_TOP_Z = round(BLADE_TIP_Z + ROOF_T, 6)               # +19.6

# --- the SW4 keycap, the thing a tilted topper can hit -------------------
SW4_X, SW4_Y = 70.675, 31.7     # [CASE contract_v4 refs.SW4]
SW4_EDGE_Y = SW4_Y - KEYCAP_W / 2.0                      # 22.95
MARGIN = 0.25                   # [TOPPER stick_cap.py:128] SW4_CLEAR_TARGET
DECK_FLOOR_Z = 5.6              # [TOPPER stick_cap.py:87]
DECK_ZONE_R = 8.6               # [TOPPER stick_cap.py:88]

# --- encoder RE1 ---------------------------------------------------------
RE1_X, RE1_Y = 13.525, 12.5     # [CASE:334 RE1_SHAFT_DESIGN]
ENC_OPEN_W, ENC_OPEN_H = 14.0, 13.0     # [CASE:584-585] plate opening
ENC_OPEN_DX = 0.5                       # [CASE:587] opening centre = shaft +x
ENC_OPEN_R = 1.5                        # [CASE:591]
CASE_ENC_BODY_PROXY_Z = 7.5             # [CASE:612] the case's own proxy
SW1_X, SW1_Y = 13.525, 31.7             # [CASE contract_v4] nearest key

WALL_MIN = 1.2                  # [TOPPER] house minimum wall

# =========================================================================
# 2. PUBLISHED-SPEC-ALPS-EC11E-H20
# -------------------------------------------------------------------------
# Drawing No.2's axial datum is the BODY TOP FACE -- the face the bushing
# rises from, which is what Bourns calls the MOUNTING SURFACE and measures its
# shaft L from.  "(20)" is parenthesised (a REFERENCE dimension) and the shaft
# is drawn foreshortened, so the AXIAL chain is taken from the dimension text,
# never from pixels.  The RADIAL dimensions are to scale and were pixel
# verified (shaft 111 px, flat offset 26.5 px -> 0.478 R vs a nominal 0.500 R).
# =========================================================================
SHAFT_ROUND_D = 6.0          # [ALPS p.2 dwg2] "o6  0/-0.05"
SHAFT_FLAT_ACROSS = 4.5      # [ALPS p.2 dwg2] "4.5  0/-0.1" across-flat
SHAFT_FLAT_LEN = 10.0        # [ALPS p.2 dwg2] "10", measured from the TIP
SHAFT_ACTUATOR_LEN = 20.0    # [ALPS p.2 dwg2] "(20)" from the body top face
ENC_BODY_H = 4.5             # [ALPS p.2 dwg2] "4.5" seating plane -> body top
ENC_BUSHING_LEN = 7.0        # [ALPS p.2 dwg2] "7" body top -> bushing end
BUSHING_D = 7.0              # [ALPS-SCALED] the sheet does not dimension the
#                              bushing o; measured 7.2 +/-0.3 at the verified
#                              radial scale, taken as the 11 mm-size standard
#                              o7.0.  The counterbore gate is re-run at o7.5.
BUSHING_D_WORST = 7.5        # [ALPS-SCALED] the pessimistic re-run

Z_BODY_TOP = ENC_BODY_H                                   # +4.5
Z_BUSHING_TOP = Z_BODY_TOP + ENC_BUSHING_LEN              # +11.5
Z_SHAFT_TIP = Z_BODY_TOP + SHAFT_ACTUATOR_LEN             # +24.5
SHAFT_EXPOSED_LEN = SHAFT_ACTUATOR_LEN - ENC_BUSHING_LEN  # 13.0
Z_FLAT_START = Z_SHAFT_TIP - SHAFT_FLAT_LEN               # +14.5

# The other EC11-class stacks, for the compatibility table only.
BOURNS_L15 = {"name": "Bourns PEC11R-42xxF (L15)",
              "mount_face_z": 6.5, "L": 15.0, "LB": 5.0, "F": 7.0}
BOURNS_L20 = {"name": "Bourns PEC11R-40/42-20F (L20)",
              "mount_face_z": 6.5, "L": 20.0, "LB": 7.0, "F": 10.0}
ALPS = {"name": "Alps EC11E-Switch-Vertical H20 (the board's footprint)",
        "mount_face_z": ENC_BODY_H, "L": SHAFT_ACTUATOR_LEN,
        "LB": ENC_BUSHING_LEN, "F": SHAFT_FLAT_LEN}
SHAFT_VARIANTS = [ALPS, BOURNS_L15, BOURNS_L20]

TIP_HEADROOM = 1.0           # bore roof must clear the shaft tip by >= 1.0
KNOB_ROOF_T = 1.5            # solid over the bore (>= the 1.2 house floor)
CBORE_D = 9.0                # clears the o7.0 bushing by 1.00 radial
CBORE_CEIL_Z = Z_BUSHING_TOP + 0.5                        # +12.0
JOURNAL_CLEAR = 0.20         # diametral clearance of the round journal bore


def shaft_stack(mount_face_z, L, LB, F):
    """World-z chain of any EC11-class flatted shaft."""
    return {"bushing_top_z": mount_face_z + LB,
            "tip_z": mount_face_z + L,
            "flat_start_z": mount_face_z + L - F,
            "exposed_len": L - LB}


# =========================================================================
# 3. THE COLLISION LAW  (derived here, never transcribed)
# -------------------------------------------------------------------------
# A topper point at radius r from the stick axis and world height h, rigidly
# tilted theta about the gimbal pivot (z = PIVOT_Z [YA13]) toward SW4:
#
#     y' = JS1_Y + r*cos(th) + (h - PIVOT_Z)*sin(th)
#     z' = PIVOT_Z + (h - PIVOT_Z)*cos(th) - r*sin(th)
#     r_max(h, th) = [ (y_edge - JS1_Y) - m - (h - PIVOT_Z)*sin(th) ] / cos(th)
#
# r (not signed y) is used because the user can push at any azimuth and a cap
# can be pressed on at any clocking, so the WHOLE ring at radius r is treated
# as if it could face SW4.  That is the conservative reading.
# =========================================================================

def tilt_point(r, h, theta_deg):
    """(y', z') of a rest-frame point (r, h) after tilting theta toward SW4."""
    th = D2R(theta_deg)
    return (JS1_Y + r * math.cos(th) + (h - PIVOT_Z) * math.sin(th),
            PIVOT_Z + (h - PIVOT_Z) * math.cos(th) - r * math.sin(th))


def r_max(h, theta_deg, y_edge=SW4_EDGE_Y, m=MARGIN):
    """Largest radius at height h that keeps m mm off the SW4 keycap edge."""
    th = D2R(theta_deg)
    return ((y_edge - JS1_Y) - m - (h - PIVOT_Z) * math.sin(th)) / math.cos(th)


def profile_clearance(prof, theta_deg):
    """Worst (smallest) SW4 clearance over a densified (r, h) profile.

    Returns (clearance, (r, h), y_prime, z_prime) for the governing point."""
    best = None
    for (r, h) in prof:
        y, z = tilt_point(r, h, theta_deg)
        clr = SW4_EDGE_Y - y
        if best is None or clr < best[0]:
            best = (clr, (r, h), y, z)
    return best


def profile_deck_floor(prof, theta_deg):
    """Lowest z reached inside the protected deck zone at this tilt."""
    lo = None
    for (r, h) in prof:
        y, z = tilt_point(r, h, theta_deg)
        plan_r = abs(y - JS1_Y)
        if plan_r <= DECK_ZONE_R and (lo is None or z < lo[0]):
            lo = (z, (r, h), plan_r)
    return lo


def solve_R(profile_fn, theta, target=MARGIN, lo=1.5, hi=12.0):
    """Bisect the largest max-radius whose real profile keeps `target` mm."""
    for _ in range(60):
        mid = (lo + hi) / 2
        if profile_clearance(densify(profile_fn(mid)), theta)[0] > target:
            lo = mid
        else:
            hi = mid
    return lo


def zero_clearance_angle(profile_fn, R, m=0.0):
    """Tilt at which a given part first touches SW4 (m=0) or eats its margin."""
    prof = densify(profile_fn(R))
    lo, hi = 0.0, TILT_FULL
    if profile_clearance(prof, hi)[0] > m:
        return TILT_FULL
    for _ in range(60):
        mid = (lo + hi) / 2
        if profile_clearance(prof, mid)[0] > m:
            lo = mid
        else:
            hi = mid
    return lo


# =========================================================================
# 4. PROFILE / SOLID HELPERS
# =========================================================================

def arc_pts(cx, cz, R, a0, a1, n=40):
    """n+1 points along a circular arc in the (r, z) plane."""
    return [(cx + R * math.cos(a), cz + R * math.sin(a))
            for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]


def revolve_profile(pts):
    """Revolve an (r, z) polygon about the z axis."""
    poly = Polygon(*[(r, z) for (r, z) in pts], align=None)
    return revolve(Plane.XZ * poly, Axis.Z)


def densify(pts, step=0.02):
    """Resample a closed (r, z) polygon at <= `step` mm so bisection sees the
    REAL profile (arcs included), not just its vertices."""
    out = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / step))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def capsule(length, width, h):
    """A stadium prism: a Box with a half-cylinder on each end."""
    return (Box(length, width, h)
            + Pos(length / 2, 0, 0) * Cylinder(width / 2, h)
            + Pos(-length / 2, 0, 0) * Cylinder(width / 2, h))


def rung_name(add):
    """nom / p05 / m05 ... naming for a fit-ladder rung."""
    if abs(add) < 1e-9:
        return "nom"
    return ("m%02d" if add < 0 else "p%02d") % int(round(abs(add) * 100))


# =========================================================================
# 5. HANDEDNESS — the export transform and its gate
# -------------------------------------------------------------------------
# [CASE:1074-1118] states the invariant this section enforces for toppers:
#
#   "The design frame is LEFT-handed (x right, y DOWN from raw KiCad board
#    coords, z up) while STL/STEP are right-handed, so every solid exported
#    through this path is the ENANTIOMORPH of the intended part."
#
# The tray is corrected at export with
#     Pos(0, PCB_H, 0) * mirror(part, about=Plane.XZ)     [CASE:2483]
# and the band is exported UN-mirrored ONLY because it is provably ACHIRAL
# (it owns an exact mirror plane at x = CX, so its enantiomorph is itself
# rotated 180 deg).  [CASE:1085-1099]
#
# v1 toppers (encoder_knob.py / stick_cap.py) export UN-mirrored.  That was
# moot, not correct-by-argument: every v1 topper is a body of revolution with
# n-fold vertical flutes, i.e. achiral, so the mirror was a no-op.  v2 breaks
# that: Knob A is a HELIX and a helix has a hand.
#
# THE v2 RULE, applied uniformly to every topper: MIRROR AT EXPORT.  Toppers
# are centred on their own axis, so no Pos() companion is needed and the whole
# transform is  mirror(part, about=Plane.XZ).  Uniform application means a
# future chiral feature (a helix, a spiral, an off-diagonal dash) cannot ship
# the wrong hand by omission, and chirality_mm3() below measures, per part,
# whether the mirror was a no-op or a real change -- so the record is
# MEASURED, never assumed.
# =========================================================================

def export_print_frame(part):
    """Design frame (left-handed) -> print frame (right-handed).

    The toppers' own axis is the origin in x and y, so the tray's companion
    translation is not needed here."""
    return mirror(part, about=Plane.XZ)


# --- STL tessellation ----------------------------------------------------
# [v2.1 2026-08-21] The v2 toppers first shipped at export_stl()'s DEFAULT
# deflection (tolerance 1e-3, angular 0.1).  On a body of revolution that is
# free, but the A/C textures are thousands of tiny analytic faces, so the
# default drove knob A to 11.43 MB (239,602 tri) and knob C to 14.64 MB
# (306,926 tri) -- 78 MB of the release bundle in six files, against a 0.59 MB
# house tray.  That is tessellation, not information: 1e-3 mm is 1/400 of a
# 0.4 mm nozzle, so no printer can render the difference.
#
# 5e-3 / 0.2 is the house topper setting: knob A -> 2.41 MB (50,610 tri),
# knob C -> 2.09 MB (43,854 tri), both inside the 3 MB bar, with mesh volume
# -0.069% / -0.071% off the exact solid -- 7x inside the +/-0.5% fidelity
# floor.  Applied UNIFORMLY to every topper export (same doctrine as the
# export mirror above): a per-part exception is how one part silently ships
# at a different fidelity than its own gate measured.
#
# *** OCCT TRAP.  BRepMesh_IncrementalMesh will NOT re-mesh a shape that
# already carries a triangulation finer than the deflection asked for.  A
# sweep that exports ONE solid at several tolerances therefore returns the
# FIRST mesh every time and reads "tolerance has no effect" (measured
# 2026-08-21: identical 239,602 tri at all six rungs).  Rebuild the solid for
# each export, which is what the ladder loops below already do per rung. ***
STL_TOL = 5e-3           # linear deflection [mm]
STL_ANG_TOL = 0.2        # angular deflection [rad]


def export_stl_house(part, path):
    """export_stl at the house topper deflection. Use for EVERY topper STL."""
    return export_stl(part, path,
                      tolerance=STL_TOL, angular_tolerance=STL_ANG_TOL)


def chirality_mm3(part, about=Plane.XZ):
    """(a_minus_b, b_minus_a) volumes between a part and its reflection.

    Both ~0  => the part owns that mirror plane, i.e. it is ACHIRAL about it
                and export_print_frame() is a no-op on it.
    Either >0 => the part is CHIRAL about that plane and the mirror is real.

    *** OCCT TRAP — READ BEFORE TRUSTING A NUMBER OUT OF THIS. ***
    Booleans against the mirror of a solid produced by
    Solid.extrude_linear_with_rotation() FAIL SILENTLY.  Measured on Knob A's
    bare knurl band (2026-08-20, this build of OCCT):

        band volume                    2005.193 mm^3
        band - mirror(band)            2005.193 mm^3   <- should be ~ grooves
        band & mirror(band)               0.155 mm^3   <- should be ~ all of it
        band - translate(band, dz 0.5)  162.966 mm^3   correct
        band - rotate(band, 7 deg)       52.651 mm^3   correct

    Both shapes report BRepCheck_Analyzer.IsValid() == True and both are
    TopAbs_FORWARD, so nothing warns you.  A gate written as
    (part - mirror(part)).volume therefore returns ~the FULL VOLUME for any
    single-family twisted solid and would read "chiral" forever, including
    after someone made it achiral.  DO NOT gate Knob A this way — gate it with
    helix_hand() on the exported STL bytes.

    This function IS trustworthy where the result can be corroborated
    analytically (Knob C: see the D-flat segment cross-check in
    encoder_knob_v2.py), and it is used only there."""
    m = mirror(part, about=about)
    try:
        a = (part - m).volume
    except Exception:                                    # pragma: no cover
        a = float("nan")
    try:
        b = (m - part).volume
    except Exception:                                    # pragma: no cover
        b = float("nan")
    return a, b


# =========================================================================
# 6. STL-BYTES READBACK  — the proof that the EXPORT, not the model, is right
# =========================================================================

def read_stl_triangles(path):
    """Parse a binary STL into an (n, 3, 3) float array of vertices.

    Deliberately dependency-light and deliberately reading the FILE: the
    handedness gate must see the bytes a slicer would see, not the in-memory
    solid the exporter was handed."""
    import struct

    import numpy as np
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        data = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
    verts = np.ascontiguousarray(data[:, 12:48]).view("<f4").reshape(n, 3, 3)
    return np.array(verts, dtype=float)


def helix_hand(tri, od, n, helix_deg, z_lo, z_hi, depth=0.40):
    """Measure a knurl band's HANDEDNESS from STL bytes.  Phase clustering.

    Groove-bottom vertices lie on n helices  theta = theta_i + s*k*z  with
    k = tan(helix)/R and s = +1 or -1.  Fold every such vertex by the trial
    law and measure how tightly it clusters within one groove pitch:

        w  = ((theta - s*k*z) mod pitch) * 2*pi/pitch
        Rbar = |mean(exp(i*w))|          1 = perfect, 0 = uniform noise

    The correct sign clusters; the wrong sign smears.  Returns
    (n_vertices, Rbar_plus, Rbar_minus).  Sign convention is the right-hand
    rule about +z: PLUS means the grooves rotate counter-clockwise (seen from
    +z) as z rises, i.e. a RIGHT-handed helix.

    Why not cross-correlate two z slices?  Tried, rejected: at a 0.15 mm slice
    band the tessellation covers only ~0.6 of the azimuth bins, and filling
    the gaps by interpolation puts the correlation peak on noise — it returned
    +28.250 deg and -60.000 deg where +/-3.482 deg was expected.  This measure
    uses EVERY vertex in the band instead of two thin slices, and separates
    the two hypotheses by an order of magnitude (0.87 vs 0.08 in practice)."""
    import numpy as np
    R = od / 2.0
    k = math.tan(D2R(helix_deg)) / R
    pitch = 2 * math.pi / n
    v = tri.reshape(-1, 3)
    v = v[(v[:, 2] > z_lo) & (v[:, 2] < z_hi)]
    rad = np.hypot(v[:, 0], v[:, 1])
    g = v[(rad > R - depth - 0.15) & (rad < R - depth + 0.07)]
    if len(g) == 0:                                      # pragma: no cover
        return 0, 0.0, 0.0
    th = np.arctan2(g[:, 1], g[:, 0])
    out = []
    for s in (+1, -1):
        w = ((th - s * k * g[:, 2]) % pitch) * (2 * math.pi / pitch)
        out.append(float(abs(np.exp(1j * w).mean())))
    return len(g), out[0], out[1]


# =========================================================================
# 7. GATE PRIMITIVES
# =========================================================================

class GateLog:
    """Collects the transcript so the caller can print AND persist it."""

    def __init__(self):
        self.lines = []
        self.failures = []

    def p(self, s=""):
        print(s)
        self.lines.append(s)

    def rule(self, ch="-", n=78):
        self.p(ch * n)

    def gate(self, name, ok, detail):
        tag = "PASS" if ok else "FAIL"
        self.p(f"    [{tag}] {name}: {detail}")
        if not ok:
            self.failures.append(f"{name}: {detail}")
        return ok

    def negative_control(self, name, gate_fn, bad_input, why):
        """A gate that cannot fail is not a gate.  Feed it a deliberately bad
        input and require it to reject."""
        rejected = not gate_fn(bad_input)
        tag = "PASS" if rejected else "FAIL"
        self.p(f"    [{tag}] NEG-CTRL {name}: {why} -> "
               f"{'REJECTED as required' if rejected else 'ACCEPTED — GATE IS DEAD'}")
        if not rejected:
            self.failures.append(f"NEG-CTRL {name} did not reject {bad_input}")
        return rejected

    def finish(self, path=None):
        self.rule("=")
        if self.failures:
            self.p(f"GATE RUN FAILED — {len(self.failures)} failure(s):")
            for f in self.failures:
                self.p(f"  * {f}")
        else:
            self.p("GATE RUN CLEAN — every gate passed and every negative "
                   "control rejected its bad input.")
        if path:
            with open(path, "w") as fh:
                fh.write("\n".join(self.lines) + "\n")
            self.p(f"wrote transcript {os.path.relpath(path, REPO)}")
        assert not self.failures, self.failures


def keycap_chain_crosscheck(log):
    """Re-derive the stem-inserted keycap chain and cross-check it against the
    repo's own emitted keycap_params.json.  Returns True on agreement."""
    import json
    log.p(f"  deck (plate top)          z = +{DECK_Z}")
    log.p(f"  fixed top-housing face    z = +{DECK_Z + SW_HOUSING_TOP_H:.2f}")
    log.p(f"  STEM SHOULDER = cap rim   z = +{KEYCAP_RIM_Z:.2f}"
          f"   <- the cap's socket mouth lands HERE")
    log.p(f"  stem cross tip            z = +{DECK_Z + SW_STEM_TOP_H:.2f}")
    log.p(f"  insertion overlap N = min(socket {CAP_SOCKET_DEPTH}, cross "
          f"{SW_CROSS_H}) = {INSERTION_N:.2f}")
    log.p(f"  cap top, DISH             z = +{KEYCAP_TOP_DISH_Z:.2f}")
    log.p(f"  cap top, PLATEAU          z = +{KEYCAP_TOP_PLATEAU_Z:.2f}")
    log.p(f"  the WRONG stack (cap + switch, no insertion) = "
          f"+{NAIVE_STACK_TOP_Z:.2f}, i.e. "
          f"{NAIVE_STACK_TOP_Z - KEYCAP_TOP_DISH_Z:.2f} too high = exactly N")
    path = os.path.join(REPO, "hardware/case/keycaps/params/keycap_params.json")
    try:
        d = json.load(open(path))["derived"]["17p5"]
    except (OSError, KeyError):                          # pragma: no cover
        log.p("  (keycap_params.json unavailable — chain NOT cross-checked)")
        return False
    ok = (abs(d["dish"]["cap_top_z_world"] - KEYCAP_TOP_DISH_Z) < 1e-9
          and abs(d["plateau"]["cap_top_z_world"] - KEYCAP_TOP_PLATEAU_Z) < 1e-9
          and abs(d["dish"]["cross_engagement_mm"] - INSERTION_N) < 1e-9
          and d["dish"]["seats_on"] == "stem shoulder")
    return log.gate(
        "keycap chain vs the repo's emitted keycap_params.json",
        ok,
        f"dish {d['dish']['cap_top_z_world']} / plateau "
        f"{d['plateau']['cap_top_z_world']} / engagement "
        f"{d['dish']['cross_engagement_mm']} / seats_on "
        f"'{d['dish']['seats_on']}'")


def opening_corner_reach():
    """Plate-opening corner reach FROM THE SHAFT, recomputed [CASE:584-591].

    The opening is 14.0 x 13.0 R1.5 centred at shaft + (0.5, 0), so the reach
    is ASYMMETRIC: the +x corners are the ones a knob has to hide."""
    cx = RE1_X + ENC_OPEN_DX
    out = []
    for sx in (-1.0, 1.0):
        ax = cx + sx * (ENC_OPEN_W / 2.0 - ENC_OPEN_R) - RE1_X
        ay = ENC_OPEN_H / 2.0 - ENC_OPEN_R
        out.append(math.hypot(ax, ay) + ENC_OPEN_R)
    return max(out), min(out)


# =========================================================================
# 8. FRAME-LEVEL GATE RUN
# =========================================================================

if __name__ == "__main__":
    log = GateLog()
    log.rule("=")
    log.p("TOPPER FRAME v2 — shared gates")
    log.rule("=")

    log.p("1.  KEYCAP CHAIN (stem-inserted, NOT cap + switch stacked)")
    keycap_chain_crosscheck(log)
    log.p("")

    log.p("2.  THE COLLISION LAW")
    log.p(f"  JS1 = ({JS1_X}, {JS1_Y});  SW4 = ({SW4_X}, {SW4_Y});  "
          f"y_edge = {SW4_Y} - {KEYCAP_W}/2 = {SW4_EDGE_Y}")
    log.p(f"  reach budget {SW4_EDGE_Y - JS1_Y:.3f};  m = {MARGIN};  "
          f"pivot +{PIVOT_Z}")
    for th in (30.0, 22.5, 15.0):
        log.p(f"    th={th:4.1f} deg : r_max(+{CAP_TOP_Z}) = "
              f"{r_max(CAP_TOP_Z, th):6.4f}  -> straight-wall cap "
              f"o{2 * r_max(CAP_TOP_Z, th):6.4f}")
    # A straight cylinder of exactly r_max must land ON the margin, and one
    # 0.1 mm fatter must break it — the law's own self-test.
    rr = r_max(CAP_TOP_Z, TILT_RESTRICTED)

    def _straight(r):
        return [(0.0, SOCKET_MOUTH_Z), (r, SOCKET_MOUTH_Z),
                (r, CAP_TOP_Z), (0.0, CAP_TOP_Z)]

    c_ok = profile_clearance(densify(_straight(rr)), TILT_RESTRICTED)[0]
    log.gate("collision law self-test (r = r_max lands on the margin)",
             abs(c_ok - MARGIN) < 1e-6, f"clearance {c_ok:+.6f} vs m {MARGIN}")
    log.negative_control(
        "collision law", lambda r: profile_clearance(
            densify(_straight(r)), TILT_RESTRICTED)[0] >= MARGIN - 1e-9,
        rr + 0.1, f"a cap 0.1 mm fatter than r_max ({rr + 0.1:.4f})")
    log.p("")

    log.p("3.  ENCODER SHAFT — PUBLISHED-SPEC-ALPS-EC11E-H20")
    log.p(f"  {'variant':<46} {'bush top':>9} {'flat @':>7} {'tip z':>7}"
          f" {'exposed':>8}")
    for v in SHAFT_VARIANTS:
        s = shaft_stack(v["mount_face_z"], v["L"], v["LB"], v["F"])
        log.p(f"  {v['name']:<46} {s['bushing_top_z']:>9.2f} "
              f"{s['flat_start_z']:>7.2f} {s['tip_z']:>7.2f} "
              f"{s['exposed_len']:>8.2f}")
    log.gate("Alps chain internally consistent",
             abs(Z_SHAFT_TIP - 24.5) < 1e-9 and abs(Z_FLAT_START - 14.5) < 1e-9,
             f"body top +{Z_BODY_TOP}, bushing top +{Z_BUSHING_TOP}, "
             f"flat starts +{Z_FLAT_START}, tip +{Z_SHAFT_TIP}")
    log.p("")

    log.p("4.  PLATE OPENING (what a knob has to hide)")
    cmax, cmin = opening_corner_reach()
    log.p(f"  opening {ENC_OPEN_W} x {ENC_OPEN_H} R{ENC_OPEN_R}, centre = "
          f"shaft + ({ENC_OPEN_DX}, 0)  [CASE:584-591]")
    log.p(f"  corner reach from the SHAFT: +x {cmax:.4f}   -x {cmin:.4f}")
    log.p("")

    log.finish()

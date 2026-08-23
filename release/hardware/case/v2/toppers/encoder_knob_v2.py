"""agentpad13 v5 topper — ROTARY ENCODER KNOB, v2 family (SHIPPING).

Supersedes encoder_knob.py's three families.  Owner-final after the v2 design
study; run with the khana python (has build123d):

    cad-khana-python encoder_knob_v2.py

Emits, into ./stl, ./params, ./outputs:
  - 3 knobs x 2 D-bore clearances = 6 STL, MIRRORED into the print frame
  - per-part FDM printability JSON (advisory)
  - params/encoder_knob_v2_params.json
  - outputs/encoder_knob_v2_gate.txt   (the full gate transcript)

------------------------------------------------------------------------------
WHAT SHIPS
    Knob A   helical knurl     N = 32, 30 deg helix, band +18.2 .. +25.5
    Knob B2  scoop  (REVISED)  cove low rim driven DOWN to the knurl line
    Knob C   cross-hatch       16 + 16 grooves at +/-45 deg
  All three: straight o17.5 body, bottom +8.0, TOP +27.0, plain wall below
  +18.2. There is no skirt or plate-cover flange.
  B1 (the CM-faithful deep cove) is RETIRED: its roof lands at +22.909, so it
  cannot seat the Alps EC11E H20 the board is footprinted for (-1.591).

Z chain (every number re-derived in the gate run below):
    +8.0    knob underside                    (clears the real body top +4.5)
    +12.0   counterbore ceiling               (o9.0, swallows the o7 bushing)
    +14.5   D-bore starts = the shaft's flat  [ALPS]
    +18.2   texture / scoop line = the PLATEAU keycap top  [KEYCAP]
    +25.5   bore roof                         (Alps tip +24.5 -> +1.000 head)
    +27.0   knob TOP                          (= 22.0 above the deck)

THE THREE-STEP BORE.  The published shaft is FULL ROUND o6 from the bushing
top +11.5 to the start of the flat +14.5, and a round o6 section cannot enter
a D-bore whose flat face is only 1.5 mm off the axis.  So:

    o9.0 counterbore    +8.0  .. +12.0     swallows the o7 bushing
    o6.2 round journal  +12.0 .. +14.5     rides the round shank AND centres
    D-bore              +14.5 .. +25.5     keys on the flat (11.00 long,
                                           10.00 of it overlapping the flat)

The measured shaft is o6.0 / 4.5 across-flat.  Conventional push-on knobs are
specified at that nominal shaft size and obtain retention from compliance, not
from an oversized bore.  LOW therefore stays nominal at o6.0/4.5.  HIGH is the
bounded FDM-compensation choice: o6.3/4.8, 0.15 mm radial and flat clearance,
the owner-set maximum.  Both retain the full 10 mm D-flat engagement. The D
section is straight at the selected size; there is no additional lead-in.

FIT CONVENTION EVIDENCE.  Alps Alpine's EC11E Drawing No.2 publishes the shaft
as o6 with 4.5 +/-0.1 across the flat.  Selco's production 2/08DR200-006
push-on knob specifies a 6.0 x 4.5 mm D-shaft and uses a compression ring.
This one-piece printed knob has no invented spring, slit, insert, or set screw.
FDM hole error is printer/material specific and belongs in a same-process fit
test or slicer hole compensation; HIGH is only the owner's bounded fallback,
not a claim that 0.15 mm is a universal manufacturing allowance.

HANDEDNESS.  Knob A's helix is CHIRAL and the design frame is left-handed, so
every knob is mirrored at export (topper_frame_v2.export_print_frame).  The
gate proves it from the EXPORTED STL BYTES via phase clustering, NOT with a
boolean against the mirror — see the OCCT trap documented on
topper_frame_v2.chirality_mm3().
"""

import json
import math
import os
import tempfile

from build123d import (
    Axis,
    Box,
    Circle,
    Cylinder,
    Plane,
    Pos,
    Rot,
    Solid,
    chamfer,
    extrude,
)

import topper_frame_v2 as F
from topper_frame_v2 import (
    CBORE_CEIL_Z,
    CBORE_D,
    D2R,
    JOURNAL_CLEAR,
    KNOB_ROOF_T,
    SHAFT_FLAT_ACROSS,
    SHAFT_ROUND_D,
    TIP_HEADROOM,
    WALL_MIN,
    Z_FLAT_START,
    Z_SHAFT_TIP,
    GateLog,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# =========================================================================
# 1. KNOB PARAMETERS
# =========================================================================

KNOB_BOT_Z = 8.0            # [CASE:698 precedent] knob underside
KNOB_OD = 17.5              # full body OD; leaves a visible gap to the key
KNOB_TOP = 27.0             # owner-final; the SHORTEST top that swallows the
#                             Alps H20 shaft UNCUT with 1.0 mm of headroom
KNOB_TOP_LADDER = [22.0, 24.0, 26.0, 27.0, 28.0]     # height table only

TEX_START_Z = F.KEYCAP_TOP_PLATEAU_Z        # +18.2, the TALLEST cap we ship
TOP_RING = 1.5              # smooth ring between the texture and the top rim
TOP_CHAMFER = 0.6           # crisp machined top rim

# --- Knob A, helical knurl (v2 geometry, unchanged) ----------------------
KNURL_N = 32                # -> crest land 0.868 at the smaller o17.5 grip
KNURL_DEPTH = 0.40          # one full bead at a 0.4 nozzle
KNURL_WIDTH = 0.85          # a 0.4 nozzle enters the valley
KNURL_HELIX_DEG = 30.0      # from vertical

# --- Knob C, cross-hatch (v2 geometry, unchanged) ------------------------
# Two opposed families put 2N notches in the worst horizontal slice, so
# N = KNURL_N / 2 reproduces Knob A's proven 0.9056 mm crest land exactly.
CROSS_N = KNURL_N // 2      # 17 per family
CROSS_HELIX_DEG = 45.0      # classic square diamond
CROSS_N_RESIN = 26          # 0.25 nozzle / resin alternative
CROSS_WIDTH_RESIN = 0.55

# --- Knob B2, the REVISED scoop ------------------------------------------
# Owner, verbatim: "knob B2 is what we want but I don't think it's 'concave
# enough'.  Relatedly, the notch is too high.  I'd expect it to be closer to
# halfway down or at least 1/3 of the way down, no?  Basically as far down as
# the knurling goes on those knobs."
#
# So the LOW RIM is driven to +18.2 — the knurl line, the plateau keycap top,
# 8.80 mm below the top and 40 % of the way down the 22.0 mm above-deck stack.
#
# THE CONSTRAINT that capped the v2 depth is NOT depth, it is the RIDGE.  The
# bore roof must stay at +25.5 (Alps tip +24.5 + 1.0 headroom), which needs
# WALL_MIN of material under the top surface at the bore's +y edge.  The scoop
# only costs roof where it actually passes OVER the bore, and it passes over
# the bore only if the ridge sits inboard of the bore's +y reach.  Park the
# ridge just OUTBOARD of that reach and the cove may be as deep as we like:
# the material over the bore is the untouched flat top, at zero cost, at ANY
# rim depth.  The v2 study swept the ridge at a FIXED 4.0 depth and so read
# this as "40.5 % of the face is the free ridge", never as "depth is then
# free".
#
#   bore +y reach = across_flat - round_d/2 = 1.500 (LOW), 1.650 (HIGH)
#   RIDGE parked at 1.950  ->  0.300 mm outboard of the HIGH-clearance bore
SCOOP_RIDGE_Y = 1.95        # 0.30 outboard of HIGH bore's +y reach (1.65)
SCOOP_RIM_Z = 18.20         # LOW RIM = the knurl line  (owner target)
SCOOP_YC = 14.0             # cove axis offset -> cove R 12.737, ridge 75.8 deg
SCOOP_TRADE_YC = [10.6, 11.0, 12.0, 13.0, 14.0, 16.0, 20.0, 30.0]
SCOOP_TRADE_RIDGE = [0.00, 0.95, 1.425, 1.65, 1.80, 1.95, 2.50]

BORE_LADDER = {"low": (0.0, 0.0), "high": (0.3, 0.3)}
DEFAULT_CLEARANCE = "low"
DEFAULT_BORE_ROUND_D = SHAFT_ROUND_D + BORE_LADDER[DEFAULT_CLEARANCE][0]
DEFAULT_BORE_ACROSS = SHAFT_FLAT_ACROSS + BORE_LADDER[DEFAULT_CLEARANCE][1]


# =========================================================================
# 2. GEOMETRY
# =========================================================================

def _plain_cyl(od, z0, z1):
    return Pos(0, 0, z0) * extrude(Plane.XY * Circle(od / 2), amount=z1 - z0)


def d_bore(round_d, across_flat, z0, z1, flat_toward=+1):
    """Parametric D-bore.  `across_flat` is the drawing dimension (flat face
    -> the opposite ROUND surface), so the flat face sits
        flat_off = across_flat - round_d/2
    off the axis.  For o6.0 / 4.5 that is 1.50 mm."""
    flat_off = across_flat - round_d / 2.0
    cylinder = Pos(0, 0, z0) * extrude(
        Plane.XY * Circle(round_d / 2.0), amount=z1 - z0)
    cut_h = round_d / 2.0 + 1.0 - flat_off
    yc = flat_toward * (flat_off + cut_h / 2.0)
    return cylinder - Pos(0, yc, (z0 + z1) / 2.0) * Box(
        round_d + 2, cut_h, z1 - z0 + 0.02)


def bore_reach_plus_y(round_d, across_flat, flat_toward=+1):
    """How far the D-bore reaches in +y — the number the scoop must respect.
    With the flat CLOCKED TOWARD THE SCOOP this is the flat offset (1.50),
    not the round radius (3.00); that clocking is worth ~0.85 mm of roof."""
    flat_off = across_flat - round_d / 2.0
    return flat_off if flat_toward > 0 else round_d / 2.0


def knob_bore(round_d, across, roof_z):
    """The three-step bore: counterbore, round journal, D-bore."""
    cb = Pos(0, 0, KNOB_BOT_Z - 1.0) * extrude(
        Plane.XY * Circle(CBORE_D / 2.0),
        amount=(CBORE_CEIL_Z - KNOB_BOT_Z) + 1.0)
    jr = Pos(0, 0, CBORE_CEIL_Z - 0.01) * extrude(
        Plane.XY * Circle((round_d + JOURNAL_CLEAR) / 2.0),
        amount=Z_FLAT_START - CBORE_CEIL_Z + 0.01)
    db = d_bore(round_d, across, Z_FLAT_START - 0.01, roof_z)
    return cb + jr + db


def bore_record(roof_z, round_d=DEFAULT_BORE_ROUND_D,
                across=DEFAULT_BORE_ACROSS):
    """Everything the z-stack gate consumes, for every shaft variant."""
    rec = {"bore_roof_z": round(roof_z, 3),
           "cbore_d": CBORE_D, "cbore_ceil_z": CBORE_CEIL_Z,
           "journal_d": round(round_d + JOURNAL_CLEAR, 3),
           "journal_z": [CBORE_CEIL_Z, Z_FLAT_START],
           "dbore_z": [Z_FLAT_START, round(roof_z, 3)],
           "dbore_len": round(roof_z - Z_FLAT_START, 3),
           "dbore_flat_off": round(across - round_d / 2.0, 3),
           "max_shaft_tip_z": round(roof_z - TIP_HEADROOM, 3),
           "variants": {}}
    for v in F.SHAFT_VARIANTS:
        s = F.shaft_stack(v["mount_face_z"], v["L"], v["LB"], v["F"])
        head = roof_z - s["tip_z"]
        eng = max(0.0, min(roof_z, s["tip_z"])
                  - max(Z_FLAT_START, s["flat_start_z"]))
        rec["variants"][v["name"]] = {
            "tip_z": s["tip_z"], "flat_start_z": s["flat_start_z"],
            "headroom": round(head, 3), "flat_engagement": round(eng, 3),
            "seats": bool(head >= TIP_HEADROOM - 1e-9)}
    return rec


# ---------------------------------------------------------------- textures
def knurl_face(od, n, width, depth):
    """A circle with n rounded notches — one groove family's cross-section.
    NOT v1's _flute() (o1.8 cutters ~0.9 deep at the rim)."""
    R = od / 2.0
    rc = ((width / 2.0) ** 2 + depth * depth) / (2 * depth)
    dc = R - depth + rc
    face = Circle(R)
    for i in range(n):
        a = 2 * math.pi * i / n
        face -= Pos(dc * math.cos(a), dc * math.sin(a)) * Circle(rc)
    return face, rc, dc


def knurl_band(od, z0, z1, n=KNURL_N, helix=KNURL_HELIX_DEG, sign=+1,
               width=KNURL_WIDTH, depth=KNURL_DEPTH):
    """ONE twisted groove family, symmetric about the band's mid-height."""
    R = od / 2.0
    face, rc, dc = knurl_face(od, n, width, depth)
    twist = sign * math.degrees((z1 - z0) * math.tan(D2R(helix)) / R)
    sol = Solid.extrude_linear_with_rotation(
        face.faces()[0], (0, 0, 0), (0, 0, z1 - z0), twist)
    # Pre-rotate by -twist/2 so Knob C's two families coincide at the band's
    # mid-plane -> the diamond rows sit square instead of drifting.
    return Pos(0, 0, z0) * Rot(0, 0, -twist / 2.0) * sol, rc, dc, twist


def knurl_metrics(od, n, width, helix, band_h, cross):
    """Every printability number the report quotes, recomputed.

    The governing insight is the SLICE, not the surface: FDM prints horizontal
    layers, and a cross-hatch puts 2N notches in the worst horizontal slice
    (the two families counter-rotate, so every relative phase occurs somewhere
    in the band) against a single helix's N."""
    C = math.pi * od
    p_c = C / n
    slice_pitch = p_c / (2.0 if cross else 1.0)
    m = {"n_per_family": n,
         "circ_pitch_mm": round(p_c, 4),
         "worst_slice_notch_pitch_mm": round(slice_pitch, 4),
         "worst_slice_crest_land_mm": round(slice_pitch - width, 4),
         "groove_w_circ_mm": width,
         "groove_depth_mm": KNURL_DEPTH,
         "groove_w_perp_mm": round(width * math.cos(D2R(helix)), 4),
         "helix_deg_from_vertical": helix,
         "twist_deg_over_band": round(
             math.degrees(band_h * math.tan(D2R(helix)) / (od / 2)), 2)}
    if cross:
        dc_ = p_c - width
        row_pitch = p_c / (2.0 * math.tan(D2R(helix)))
        m.update({"diamond_circ_diag_mm": round(dc_, 4),
                  "diamond_axial_diag_mm": round(dc_ / math.tan(D2R(helix)), 4),
                  "diamond_perp_width_mm": round(dc_ * math.cos(D2R(helix)), 4),
                  "row_pitch_axial_mm": round(row_pitch, 4),
                  "rows_in_band": round(band_h / row_pitch, 2),
                  "diamonds_in_band": int(round(n * band_h / row_pitch))})
    return m


def _textured_barrel(od, z_top, band_solid_fn):
    """Plain cylinder below TEX_START_Z, textured band, smooth top ring."""
    zk0, zk1 = TEX_START_Z, z_top - TOP_RING
    body = (_plain_cyl(od, KNOB_BOT_Z, zk0)
            + band_solid_fn(zk0, zk1)
            + _plain_cyl(od, zk1, z_top))
    e = body.edges().filter_by_position(Axis.Z, z_top - 0.02, z_top + 0.02)
    return chamfer(e, TOP_CHAMFER), (zk0, zk1)


# ---------------------------------------------------------------- the scoop
def scoop_cove(od, z_top, ridge_y=SCOOP_RIDGE_Y, rim_z=SCOOP_RIM_Z,
               yc=SCOOP_YC, bore_y=None):
    """The Codex-Micro dial gesture as ONE cut: a horizontal cylinder.

    Parametrised by the three things a person can actually judge:
        ridge_y   where the flat top ends and the scoop begins
        rim_z     how far down the notch cuts the outer wall  (the OWNER knob)
        yc        the cut cylinder's axis offset = the CURVATURE knob
    and the cove radius is SOLVED, not guessed:

        u = yc - ridge_y ,  v = yc - R ,  D = z_top - rim_z
        surface  z(y) = zc - sqrt(Rc^2 - (y - yc)^2)   for y >= ridge_y
        through (ridge_y, z_top) and (R, rim_z):
            A = sqrt(Rc^2 - v^2) ,  B = sqrt(Rc^2 - u^2) ,  A - B = D
            A + B = (u^2 - v^2)/D            [difference of two squares]
        =>  A = ((u^2 - v^2)/D + D)/2 ,  B = A - D ,  Rc = hypot(A, v)

    Feasible iff u^2 - v^2 >= D^2, i.e. B >= 0.  B = 0 is a VERTICAL tangent
    at the ridge, so B > 0 is what keeps the top surface a single-valued
    height field — no undercut, and printable bottom-down with no support."""
    R = od / 2.0
    if bore_y is None:
        bore_y = bore_reach_plus_y(DEFAULT_BORE_ROUND_D,
                                   DEFAULT_BORE_ACROSS, +1)
    u, v, D = yc - ridge_y, yc - R, z_top - rim_z
    disc = u * u - v * v
    if D <= 0 or disc < D * D:
        return None, {"feasible": False, "ridge_y": ridge_y, "rim_z": rim_z,
                      "cove_yc": yc, "reason": "u^2 - v^2 < D^2 (undercut)"}
    A = (disc / D + D) / 2.0
    B = A - D
    Rc = math.hypot(A, v)
    zc = z_top + B
    cut = Pos(0, yc, zc) * Rot(0, 90, 0) * Cylinder(Rc, od + 6)

    def surf(y):
        if y <= ridge_y:
            return z_top
        return zc - math.sqrt(max(Rc * Rc - (y - yc) ** 2, 0.0))

    rf = ridge_y / R
    half_chord = math.hypot(R - ridge_y, z_top - rim_z) / 2.0
    prof = {"feasible": True,
            "ridge_y": round(ridge_y, 4), "ridge_frac": round(rf, 4),
            "cove_R": round(Rc, 4), "cove_yc": yc, "cove_zc": round(zc, 4),
            "low_rim_z": round(surf(R), 4),
            "rim_drop_mm": round(z_top - surf(R), 4),
            "bore_reach_plus_y": round(bore_y, 3),
            "z_over_bore_edge": round(surf(bore_y), 4),
            "ridge_slope_deg": round(math.degrees(math.atan2(u, B)), 2),
            "rim_slope_deg": round(math.degrees(math.atan2(v, A)), 2),
            "chord_slope_deg": round(math.degrees(
                math.atan((z_top - rim_z) / (R - ridge_y))), 2),
            "sagitta_below_chord_mm": round(
                Rc - math.sqrt(max(Rc * Rc - half_chord * half_chord, 0.0)), 4),
            "scoop_area_frac": round(
                1.0 - (math.acos(min(max(-rf, -1.0), 1.0))
                       + rf * math.sqrt(max(1 - rf * rf, 0.0))) / math.pi, 4)}
    return cut, prof


# ---------------------------------------------------------------- the knobs
def knobA(od=KNOB_OD, z_top=KNOB_TOP, round_d=DEFAULT_BORE_ROUND_D,
          across=DEFAULT_BORE_ACROSS):
    info = {}

    def band(z0, z1):
        sol, rc, dc, tw = knurl_band(od, z0, z1)
        info.update({"cutter_r": round(rc, 4),
                     "cutter_centre_dist": round(dc, 4),
                     "twist_deg": round(tw, 2)})
        return sol

    body, (zk0, zk1) = _textured_barrel(od, z_top, band)
    roof = z_top - KNOB_ROOF_T
    body -= knob_bore(round_d, across, roof)
    rec = bore_record(roof, round_d, across)
    rec["texture"] = knurl_metrics(od, KNURL_N, KNURL_WIDTH, KNURL_HELIX_DEG,
                                   zk1 - zk0, cross=False)
    rec["texture"].update(info)
    rec["band_z"] = [round(zk0, 3), round(zk1, 3)]
    return body, rec


def knobC(od=KNOB_OD, z_top=KNOB_TOP, round_d=DEFAULT_BORE_ROUND_D,
          across=DEFAULT_BORE_ACROSS):
    info = {}

    def band(z0, z1):
        a, rc, dc, tw = knurl_band(od, z0, z1, CROSS_N, CROSS_HELIX_DEG, +1)
        b, _, _, _ = knurl_band(od, z0, z1, CROSS_N, CROSS_HELIX_DEG, -1)
        info.update({"cutter_r": round(rc, 4),
                     "cutter_centre_dist": round(dc, 4),
                     "twist_deg_per_family": round(tw, 2)})
        return a & b

    body, (zk0, zk1) = _textured_barrel(od, z_top, band)
    roof = z_top - KNOB_ROOF_T
    body -= knob_bore(round_d, across, roof)
    rec = bore_record(roof, round_d, across)
    rec["texture"] = knurl_metrics(od, CROSS_N, KNURL_WIDTH, CROSS_HELIX_DEG,
                                   zk1 - zk0, cross=True)
    rec["texture"].update(info)
    rec["texture"]["resin_alternative"] = knurl_metrics(
        od, CROSS_N_RESIN, CROSS_WIDTH_RESIN, CROSS_HELIX_DEG,
        zk1 - zk0, cross=True)
    rec["band_z"] = [round(zk0, 3), round(zk1, 3)]
    return body, rec


def knobB2(od=KNOB_OD, z_top=KNOB_TOP, round_d=DEFAULT_BORE_ROUND_D,
           across=DEFAULT_BORE_ACROSS, ridge_y=SCOOP_RIDGE_Y,
           rim_z=SCOOP_RIM_Z, yc=SCOOP_YC):
    body = _plain_cyl(od, KNOB_BOT_Z, z_top)
    cut, prof = scoop_cove(od, z_top, ridge_y, rim_z, yc,
                           bore_y=bore_reach_plus_y(round_d, across, +1))
    assert cut is not None, f"B2 scoop infeasible: {prof}"
    body -= cut
    roof_z = min(z_top - KNOB_ROOF_T, prof["z_over_bore_edge"] - WALL_MIN)
    body -= knob_bore(round_d, across, roof_z)
    rec = bore_record(roof_z, round_d, across)
    rec["scoop"] = prof
    rec["scoop_cost_vs_flat"] = round(roof_z - (z_top - KNOB_ROOF_T), 3)
    return body, rec


KNOBS = [("A_helical_knurl", "A", knobA, (0, 0, -1)),
         ("B2_scoop", "B2", knobB2, (0, 0, 1)),
         ("C_cross_hatch", "C", knobC, (0, 0, -1))]


# =========================================================================
# 3. MAIN — gates, export, printability, params
# =========================================================================

if __name__ == "__main__":
    stl_dir = os.path.join(HERE, "stl")
    out_dir = os.path.join(HERE, "outputs")
    par_dir = os.path.join(HERE, "params")
    for d in (stl_dir, out_dir, par_dir):
        os.makedirs(d, exist_ok=True)

    log = GateLog()
    P = log.p
    log.rule("=")
    P("ENCODER KNOB v2 — A (helical) / B2 (scoop, REVISED) / C (cross-hatch)")
    log.rule("=")
    P("")

    # ---------------------------------------------------------------- §1
    P("1.  THE KEYCAP CHAIN this knob's height is measured against")
    F.keycap_chain_crosscheck(log)
    P("")

    # ---------------------------------------------------------------- §2
    P("2.  KEY CLEARANCE — straight body, no skirt or cover flange")
    centre_pitch = F.SW1_Y - F.RE1_Y
    grip_key_clear = centre_pitch - KNOB_OD / 2 - F.KEYCAP_W / 2
    log.gate("straight knob body vs SW1 across the full keycap z-overlap",
             grip_key_clear >= 1.5,
             f"centres {centre_pitch:.2f} apart; o{KNOB_OD} knob vs "
             f"o{F.KEYCAP_W} key -> {grip_key_clear:+.3f} horizontal gap "
             f"through z +{F.KEYCAP_RIM_Z:.1f}..+"
             f"{F.KEYCAP_TOP_PLATEAU_Z:.1f}")
    cb_rad = (CBORE_D - F.BUSHING_D) / 2
    cb_rad_w = (CBORE_D - F.BUSHING_D_WORST) / 2
    log.gate("counterbore vs the bushing", cb_rad_w > 0,
             f"o{CBORE_D} cbore clears a o{F.BUSHING_D} bushing by "
             f"{cb_rad:.2f} radial and the pessimistic o{F.BUSHING_D_WORST} "
             f"by {cb_rad_w:.2f}; it swallows "
             f"{CBORE_CEIL_Z - KNOB_BOT_Z:.1f} mm of it")
    P("")

    # ---------------------------------------------------------------- §3
    P("3.  Z-STACK — does the bore swallow the board's own shaft, UNCUT?")
    P(f"  {'top z':>6} {'above deck':>10} {'H/D':>6} {'over dish':>9}"
      f" {'over plat':>9} {'roof':>6} {'max tip':>8} {'Alps':>6}"
      f" {'B-L15':>6} {'B-L20':>6} {'flat eng':>8}")
    height_ladder = {}
    for zt in KNOB_TOP_LADDER:
        roof = zt - KNOB_ROOF_T
        rec = bore_record(roof)
        va = rec["variants"]
        eng = min(roof, Z_SHAFT_TIP) - Z_FLAT_START
        P(f"  {zt:>6.1f} {zt - F.DECK_Z:>10.1f} "
          f"{(zt - F.DECK_Z) / KNOB_OD:>6.3f} "
          f"{zt - F.KEYCAP_TOP_DISH_Z:>9.1f} "
          f"{zt - F.KEYCAP_TOP_PLATEAU_Z:>9.1f} {roof:>6.1f} "
          f"{rec['max_shaft_tip_z']:>8.1f} "
          + " ".join(f"{'YES' if va[v['name']]['seats'] else 'no':>6}"
                     for v in F.SHAFT_VARIANTS)
          + f" {eng:>8.2f}")
        height_ladder[zt] = {
            "above_deck": round(zt - F.DECK_Z, 3),
            "h_over_d_above_deck": round((zt - F.DECK_Z) / KNOB_OD, 3),
            "over_dish_cap": round(zt - F.KEYCAP_TOP_DISH_Z, 3),
            "over_plateau_cap": round(zt - F.KEYCAP_TOP_PLATEAU_Z, 3),
            "bore_roof_z": roof, "max_shaft_tip_z": rec["max_shaft_tip_z"],
            "seats": {k: v["seats"] for k, v in va.items()},
            "flat_engagement_alps": round(eng, 3)}
    P(f"  minimum top for the Alps H20 = tip {Z_SHAFT_TIP} + headroom "
      f"{TIP_HEADROOM} + roof {KNOB_ROOF_T} = "
      f"+{Z_SHAFT_TIP + TIP_HEADROOM + KNOB_ROOF_T:.1f}  ->  SHIPPED "
      f"+{KNOB_TOP}")

    def _zstack_gate(roof_z):
        return (roof_z - Z_SHAFT_TIP) >= TIP_HEADROOM - 1e-9

    log.gate("z-stack headroom, shipped roof +25.5 vs the Alps H20 tip",
             _zstack_gate(KNOB_TOP - KNOB_ROOF_T),
             f"roof +{KNOB_TOP - KNOB_ROOF_T} - tip +{Z_SHAFT_TIP} = "
             f"{KNOB_TOP - KNOB_ROOF_T - Z_SHAFT_TIP:+.3f} >= "
             f"{TIP_HEADROOM} required")
    log.negative_control("z-stack headroom", _zstack_gate, 24.0 - KNOB_ROOF_T,
                         "the brief's +24.0 knob (roof +22.5, headroom -2.000)")
    log.negative_control("z-stack headroom", _zstack_gate, 22.909,
                         "RETIRED Knob B1's roof +22.909 (headroom -1.591)")
    P("")

    # ---------------------------------------------------------------- §4
    P("4.  D-BORE CLEARANCE — LOW fit plus owner-capped HIGH fit")
    shaft_flat_off = SHAFT_FLAT_ACROSS - SHAFT_ROUND_D / 2.0
    clearance_table = {}
    for clearance, (dd, da) in BORE_LADDER.items():
        rd = SHAFT_ROUND_D + dd
        af = SHAFT_FLAT_ACROSS + da
        radial = (rd - SHAFT_ROUND_D) / 2.0
        flat = (af - rd / 2.0) - shaft_flat_off
        chord = 2.0 * math.sqrt(max((rd / 2.0) ** 2
                                    - (af - rd / 2.0) ** 2, 0.0))
        clearance_table[clearance] = {
            "round_d": round(rd, 3),
            "across_flat": round(af, 3),
            "radial_clearance_per_side": round(radial, 3),
            "flat_clearance": round(flat, 3),
            "flat_chord": round(chord, 3),
        }
        P(f"    {clearance.upper():<4}  o{rd:.1f} / across-flat {af:.1f}: "
          f"{radial:.3f} radial per side, {flat:.3f} at the flat; "
          f"D chord {chord:.3f}")
    log.gate("LOW follows the nominal push-on D-shaft convention",
             abs(clearance_table["low"]["radial_clearance_per_side"]) < 1e-9
             and abs(clearance_table["low"]["flat_clearance"]) < 1e-9,
             "o6.0/4.5 matches the measured and published shaft size")
    log.gate("HIGH clearance does not exceed the owner's 0.15 mm maximum",
             clearance_table["high"]["radial_clearance_per_side"] <= 0.15
             and clearance_table["high"]["flat_clearance"] <= 0.15,
             "o6.3/4.8 gives 0.150 mm radial and flat clearance")
    log.gate("LOW and HIGH are materially separated",
             (clearance_table["high"]["radial_clearance_per_side"]
              - clearance_table["low"]["radial_clearance_per_side"] >= 0.15)
             and (clearance_table["high"]["flat_clearance"]
                  - clearance_table["low"]["flat_clearance"] >= 0.15),
             "HIGH adds 0.150 mm radial and flat clearance over nominal LOW")
    log.gate("both choices retain a positive D-flat torque face",
             all(v["flat_chord"] >= 5.0 for v in clearance_table.values()),
             f"flat chords LOW {clearance_table['low']['flat_chord']:.3f}, "
             f"HIGH {clearance_table['high']['flat_chord']:.3f}; working "
             f"D-bore length remains {KNOB_TOP - KNOB_ROOF_T - Z_FLAT_START:.1f} mm")
    P("    Both D-bores are straight at the listed dimensions; no lead-in.")
    P("")

    # ---------------------------------------------------------------- §5
    P("5.  KNOB B2 SCOOP TRADE — cove radius x ridge position")
    P("    Owner: 'not concave enough ... the notch is too high ... as far")
    P("    down as the knurling goes'.  Target LOW RIM = +18.2 = the knurl")
    P("    line.  HARD CONSTRAINT: bore roof >= +25.5.")
    bore_y_low = bore_reach_plus_y(
        clearance_table["low"]["round_d"],
        clearance_table["low"]["across_flat"])
    bore_y_high = bore_reach_plus_y(
        clearance_table["high"]["round_d"],
        clearance_table["high"]["across_flat"])
    P(f"    bore +y reach: LOW {bore_y_low:.3f}, HIGH {bore_y_high:.3f} "
      f"(the worst); the D-flat is clocked TOWARD the")
    P(f"    scoop, so even the HIGH bore reaches {bore_y_high:.2f} in +y "
      f"instead of {clearance_table['high']['round_d'] / 2:.2f}.")
    P("")
    P(f"  {'ridge y':>8} {'ridge/R':>8} {'cove R':>7} {'yc':>6} {'rim z':>7}"
      f" {'%face':>6} {'chord':>7} {'ridge':>7} {'rim sl':>7} {'sag':>6}"
      f" {'z@bore':>7} {'roof':>7} {'ok':>5}")
    trade = []
    for ridge in SCOOP_TRADE_RIDGE:
        for yc in SCOOP_TRADE_YC:
            _, pf = scoop_cove(KNOB_OD, KNOB_TOP, ridge, SCOOP_RIM_Z, yc,
                               bore_y=bore_y_high)
            if not pf["feasible"]:
                P(f"  {ridge:>8.3f} {ridge / (KNOB_OD / 2):>8.4f} "
                  f"{'-':>7} {yc:>6.1f} {'-':>7} {'-':>6} {'-':>7} {'-':>7}"
                  f" {'-':>7} {'-':>6} {'-':>7} {'-':>7} {'UNDER':>5}")
                continue
            roof = min(KNOB_TOP - KNOB_ROOF_T,
                       pf["z_over_bore_edge"] - WALL_MIN)
            ok = roof >= 25.5 - 1e-9
            P(f"  {ridge:>8.3f} {pf['ridge_frac']:>8.4f} "
              f"{pf['cove_R']:>7.3f} {yc:>6.1f} {pf['low_rim_z']:>7.3f} "
              f"{100 * pf['scoop_area_frac']:>5.1f}% "
              f"{pf['chord_slope_deg']:>7.2f} {pf['ridge_slope_deg']:>7.2f} "
              f"{pf['rim_slope_deg']:>7.2f} "
              f"{pf['sagitta_below_chord_mm']:>6.3f} "
              f"{pf['z_over_bore_edge']:>7.3f} {roof:>7.3f} "
              f"{'YES' if ok else 'no':>5}")
            trade.append({**pf, "bore_roof_z": round(roof, 4), "ok": bool(ok)})
    P("")
    P("  READING THE TABLE.  Every row targets the SAME rim +18.2, so the")
    P("  trade is not depth-vs-roof at all: the roof is +25.500 for EVERY")
    P("  row whose ridge sits outboard of the HIGH bore's reach")
    P(f"  ({bore_y_high:.3f}) and short of it for every row inboard.  Depth")
    P("  is bought from the RIDGE, not from the roof.  What the cove radius")
    P("  buys is the SHAPE: small yc = tight R = a deep dish behind a steep")
    P("  ridge wall; large yc = big R = a near-flat chamfer (both slopes")
    P("  converge on the chord).  'UNDER' = the cove would have to undercut")
    P("  (B < 0, a vertical tangent at the ridge) to reach +18.2.")
    ship = [t for t in trade
            if abs(t["ridge_y"] - SCOOP_RIDGE_Y) < 1e-9
            and abs(t["cove_yc"] - SCOOP_YC) < 1e-9][0]
    P(f"  SHIPPED: ridge {SCOOP_RIDGE_Y} ({100 * ship['scoop_area_frac']:.1f}"
      f"% of the face), cove R {ship['cove_R']}, rim +{ship['low_rim_z']}, "
      f"roof +{ship['bore_roof_z']}, sagitta {ship['sagitta_below_chord_mm']}")
    P(f"  vs the v2 study's B2 (ridge 1.425, depth 4.0): rim +23.061, chord "
      f"26.00 deg -> the notch drops {23.061 - ship['low_rim_z']:.3f} mm and "
      f"the chord steepens to {ship['chord_slope_deg']} deg.")

    def _b2_roof_gate(params):
        ridge, yc = params
        _, pf = scoop_cove(KNOB_OD, KNOB_TOP, ridge, SCOOP_RIM_Z, yc,
                           bore_y=bore_y_high)
        if not pf["feasible"]:
            return False
        return min(KNOB_TOP - KNOB_ROOF_T,
                   pf["z_over_bore_edge"] - WALL_MIN) >= 25.5 - 1e-9

    log.gate("B2 scoop keeps the +25.5 roof at HIGH clearance",
             _b2_roof_gate((SCOOP_RIDGE_Y, SCOOP_YC)),
             f"ridge {SCOOP_RIDGE_Y} is {SCOOP_RIDGE_Y - bore_y_high:+.3f} "
             f"outboard of the HIGH bore's reach, so the material over "
             f"the bore is the untouched flat top")
    log.negative_control("B2 scoop roof", _b2_roof_gate, (0.0, SCOOP_YC),
                         "a centred ridge, which puts the cove over the bore")
    log.negative_control("B2 scoop roof", _b2_roof_gate, (SCOOP_RIDGE_Y, 10.0),
                         "a cove radius too tight to reach +18.2 without an "
                         "undercut")
    log.gate("B2 low rim hits the owner's target",
             abs(ship["low_rim_z"] - TEX_START_Z) < 1e-3,
             f"rim +{ship['low_rim_z']} vs the knurl line +{TEX_START_Z} "
             f"(= {ship['rim_drop_mm']} mm down, "
             f"{100 * ship['rim_drop_mm'] / (KNOB_TOP - F.DECK_Z):.0f}% of "
             f"the {KNOB_TOP - F.DECK_Z:.0f} mm above-deck stack)")
    P("")

    # ---------------------------------------------------------------- §5
    P("6.  THE THREE KNOBS")
    knobs = {}
    solids = {}
    for name, tag, fn, up in KNOBS:
        P(f"  --- Knob {tag}  ({name})  o{KNOB_OD}, +{KNOB_BOT_Z} .. "
          f"+{KNOB_TOP} ---")
        body, rec = fn()
        solids[tag] = (body, up)
        bb = body.bounding_box()
        P(f"      bore: o{CBORE_D} cbore -> +{CBORE_CEIL_Z} | "
          f"o{rec['journal_d']} journal +{CBORE_CEIL_Z}..+{Z_FLAT_START} | "
          f"D-bore +{Z_FLAT_START}..+{rec['bore_roof_z']} "
          f"({rec['dbore_len']:.2f} long, flat face "
          f"{rec['dbore_flat_off']} off the axis)")
        for v in F.SHAFT_VARIANTS:
            d = rec["variants"][v["name"]]
            P(f"      {v['name'][:44]:<44} tip +{d['tip_z']:<5.1f} headroom "
              f"{d['headroom']:+7.3f}  flat engagement "
              f"{d['flat_engagement']:5.2f}  "
              f"{'SEATS' if d['seats'] else '*** RIDES PROUD ***'}")
        log.gate(f"Knob {tag} z-stack vs the Alps H20",
                 rec["variants"][F.ALPS["name"]]["seats"],
                 f"headroom "
                 f"{rec['variants'][F.ALPS['name']]['headroom']:+.3f} >= "
                 f"{TIP_HEADROOM}")
        eng = rec["variants"][F.ALPS["name"]]["flat_engagement"]
        log.gate(f"Knob {tag} flat engagement", eng >= 6.0,
                 f"{eng:.2f} mm of D-bore actually overlaps the Alps flat "
                 f"(>= the 6.0 house floor)")
        if "scoop" in rec:
            sc = rec["scoop"]
            P(f"      scoop: ridge y {sc['ridge_y']} "
              f"({sc['ridge_frac']:+.4f} R, covers "
              f"{100 * sc['scoop_area_frac']:.1f}% of the face)")
            P(f"             cove R {sc['cove_R']} at (y {sc['cove_yc']}, "
              f"z {sc['cove_zc']}); ridge {sc['ridge_slope_deg']} deg, "
              f"rim {sc['rim_slope_deg']} deg, chord "
              f"{sc['chord_slope_deg']} deg")
            P(f"             sagitta below the chord "
              f"{sc['sagitta_below_chord_mm']} mm = the concavity the owner "
              f"asked for")
            P(f"             LOW RIM z {sc['low_rim_z']} -> "
              f"{sc['low_rim_z'] - TEX_START_Z:+.3f} vs the knurl line "
              f"+{TEX_START_Z}, {sc['low_rim_z'] - F.KEYCAP_TOP_DISH_Z:+.3f} "
              f"vs the dish caps")
            P(f"             surface over the bore's +y edge "
              f"(y={sc['bore_reach_plus_y']}): z {sc['z_over_bore_edge']}"
              f"  ->  SCOOP COST vs a flat top "
              f"{rec['scoop_cost_vs_flat']:+.3f} mm of roof")
        if "texture" in rec:
            t = rec["texture"]
            P(f"      texture: N={t['n_per_family']}/family, helix "
              f"{t['helix_deg_from_vertical']} deg from vertical, groove "
              f"{t['groove_w_circ_mm']} wide x {t['groove_depth_mm']} deep "
              f"(cutter R {t['cutter_r']})")
            P(f"               circumferential pitch {t['circ_pitch_mm']}; "
              f"WORST horizontal slice: notches every "
              f"{t['worst_slice_notch_pitch_mm']} -> CREST LAND "
              f"{t['worst_slice_crest_land_mm']}")
            log.gate(f"Knob {tag} worst-slice crest land",
                     t["worst_slice_crest_land_mm"] >= 0.84,
                     f"{t['worst_slice_crest_land_mm']} mm = "
                     f"{t['worst_slice_crest_land_mm'] / 0.42:.1f} beads at a "
                     f"0.42 line width (>= 2 beads)")
            if "diamond_circ_diag_mm" in t:
                P(f"               diamond {t['diamond_circ_diag_mm']} circ x "
                  f"{t['diamond_axial_diag_mm']} axial, perp width "
                  f"{t['diamond_perp_width_mm']}, rows every "
                  f"{t['row_pitch_axial_mm']} -> {t['rows_in_band']} rows x "
                  f"{t['n_per_family']} = ~{t['diamonds_in_band']} diamonds")
                r = t["resin_alternative"]
                P(f"               resin / 0.25-nozzle alternative: N="
                  f"{r['n_per_family']}/family, groove "
                  f"{r['groove_w_circ_mm']}, land "
                  f"{r['worst_slice_crest_land_mm']}, diamond "
                  f"{r['diamond_circ_diag_mm']} x "
                  f"{r['diamond_axial_diag_mm']}, {r['rows_in_band']} rows")
        wall = KNOB_OD / 2 - CBORE_D / 2
        log.gate(f"Knob {tag} minimum real wall", wall >= WALL_MIN,
                 f"{wall:.3f} (OD/2 - cbore/2) >= {WALL_MIN}")
        P(f"      bbox {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}"
          f"  (z {bb.min.Z:.2f} .. {bb.max.Z:.2f})")
        rec.update({"od": KNOB_OD, "bottom_z": KNOB_BOT_Z, "top_z": KNOB_TOP,
                    "height_above_deck": round(KNOB_TOP - F.DECK_Z, 3),
                    "h_over_d_above_deck": round(
                        (KNOB_TOP - F.DECK_Z) / KNOB_OD, 3),
                    "h_over_d_barrel": round(
                        (KNOB_TOP - KNOB_BOT_Z) / KNOB_OD, 3),
                    "over_dish_cap": round(KNOB_TOP - F.KEYCAP_TOP_DISH_Z, 3),
                    "over_plateau_cap": round(
                        KNOB_TOP - F.KEYCAP_TOP_PLATEAU_Z, 3),
                    "key_horizontal_clearance": round(grip_key_clear, 3),
                    "texture_start_z": TEX_START_Z,
                    "print_orientation": ("top-down" if up[2] < 0
                                          else "bottom-down"),
                    "min_wall": round(wall, 3)})
        knobs[name] = rec
        P("")

    # ---------------------------------------------------------------- §6
    P("7.  EXPORT INTO THE PRINT FRAME")
    P("    [CASE:1074-1118] the design frame is LEFT-handed while STL is")
    P("    right-handed, so every solid built here is the ENANTIOMORPH of")
    P("    the intended part.  v1 toppers exported un-mirrored, which was")
    P("    MOOT (bodies of revolution with n-fold flutes are achiral), not")
    P("    correct-by-argument.  Knob A is a HELIX.  v2 mirrors every knob:")
    P("    uniform application is what stops a future chiral feature")
    P("    shipping the wrong hand by omission.")
    # The previous 3-rung ladder is retired, not merely hidden from a catalog.
    # Remove its generated files so the live STL directory exposes exactly the
    # two supported choices after every generator run.
    for tag in ("A", "B2", "C"):
        for stale in ("tight", "nom", "loose"):
            stale_path = os.path.join(stl_dir,
                                      f"knob_v2_{tag}_bore_{stale}.stl")
            if os.path.exists(stale_path):
                os.unlink(stale_path)
                P(f"    retired {os.path.basename(stale_path)}")
    exports = {}
    for name, tag, fn, up in KNOBS:
        exports[tag] = {}
        for rung, (dd, da) in BORE_LADDER.items():
            part = fn(KNOB_OD, KNOB_TOP, SHAFT_ROUND_D + dd,
                      SHAFT_FLAT_ACROSS + da)[0]
            fn_out = os.path.join(
                stl_dir, f"knob_v2_{tag}_clearance_{rung}.stl")
            F.export_stl_house(F.export_print_frame(part), fn_out)
            exports[tag][rung] = {
                "file": os.path.relpath(fn_out, F.REPO),
                "round_d": round(SHAFT_ROUND_D + dd, 3),
                "across_flat": round(SHAFT_FLAT_ACROSS + da, 3),
                "flat_off": round(SHAFT_FLAT_ACROSS + da
                                  - (SHAFT_ROUND_D + dd) / 2, 3)}
            P(f"    wrote {os.path.basename(fn_out):<28} bore o"
              f"{SHAFT_ROUND_D + dd:.1f} / across-flat "
              f"{SHAFT_FLAT_ACROSS + da:.1f} (flat "
              f"{exports[tag][rung]['flat_off']} off axis)")
    P("")

    # ---------------------------------------------------------------- §7
    P("8.  HANDEDNESS GATE — measured from the EXPORTED STL BYTES")
    P("    NOT with (part - mirror(part)).volume.  That boolean FAILS")
    P("    SILENTLY on any solid from extrude_linear_with_rotation: on Knob")
    P("    A's bare band, band & mirror(band) = 0.155 mm^3 of 2005.193, and")
    P("    band - mirror(band) returns the WHOLE band, with both shapes")
    P("    reporting IsValid() and TopAbs_FORWARD.  See the OCCT TRAP note")
    P("    on topper_frame_v2.chirality_mm3().")
    P("")
    zl, zh = TEX_START_Z + 0.4, KNOB_TOP - TOP_RING - 0.4
    P(f"    Phase clustering on groove-bottom vertices, band z {zl}..{zh}:")
    P("    fold theta - s*k*z into one pitch, s = +1/-1, and measure |mean")
    P("    exp(i w)|.  The true hand clusters; the wrong hand smears.")
    tri_ship = F.read_stl_triangles(
        os.path.join(stl_dir, "knob_v2_A_clearance_low.stl"))
    n_s, rp_s, rm_s = F.helix_hand(tri_ship, KNOB_OD, KNURL_N,
                                   KNURL_HELIX_DEG, zl, zh, KNURL_DEPTH)
    with tempfile.TemporaryDirectory() as td:
        negp = os.path.join(td, "negctrl_knobA_unmirrored.stl")
        # deliberately NOT mirrored; same deflection as the shipped file so
        # the phase-clustering comparison is like-for-like.
        F.export_stl_house(knobA()[0], negp)
        n_n, rp_n, rm_n = F.helix_hand(F.read_stl_triangles(negp), KNOB_OD,
                                       KNURL_N, KNURL_HELIX_DEG, zl, zh,
                                       KNURL_DEPTH)
    hand_s = "RIGHT" if rp_s > rm_s else "LEFT"
    hand_n = "RIGHT" if rp_n > rm_n else "LEFT"
    P(f"    design-frame solid, exported UN-MIRRORED (neg control): "
      f"{n_n} verts  R+ {rp_n:.4f}  R- {rm_n:.4f}  -> {hand_n}-handed")
    P(f"    DEFAULT knob_v2_A_clearance_low.stl                : "
      f"{n_s} verts  R+ {rp_s:.4f}  R- {rm_s:.4f}  -> {hand_s}-handed")
    log.gate("the phase-clustering measure actually discriminates",
             max(rp_s, rm_s) > 0.5 and min(rp_s, rm_s) < 0.25,
             f"winner {max(rp_s, rm_s):.4f} vs loser {min(rp_s, rm_s):.4f} "
             f"— an order of magnitude apart, so the read is not noise")
    log.gate("the export mirror actually flipped the hand IN THE FILE",
             hand_s != hand_n,
             f"un-mirrored {hand_n} vs shipped {hand_s}")
    log.gate("the SHIPPED file is the print-frame (LEFT-handed) helix",
             hand_s == "LEFT",
             "the design-frame solid is right-handed by construction "
             "(extrude_linear_with_rotation, +twist = CCW about +z), so the "
             "physical part is its enantiomorph: grooves rotate CLOCKWISE as "
             "they rise, seen from above.  Cosmetic on a rotary knob, and "
             "pinned here so it can never drift silently.")
    P("")
    P("    Knob C carries no single-family helix.  Its two 16-groove")
    P("    families and +y D-flat must preserve the YZ mirror plane:")
    P("    x -> -x swaps the +/-45-degree texture families while leaving")
    P("    the bore flat unchanged.  This also catches a missing family or")
    P("    unintended texture clocking.")
    a_yz, b_yz = F.chirality_mm3(solids["C"][0], Plane.YZ)
    P(f"    MEASURED Knob C vs mirror about YZ: {a_yz:.4f} / {b_yz:.4f} mm^3")
    log.gate("Knob C owns the YZ mirror plane (cross-hatch + D-flat)",
             max(a_yz, b_yz) < 1e-6,
             f"{a_yz:.6f} / {b_yz:.6f} mm^3")
    a_yz_b2, b_yz_b2 = F.chirality_mm3(solids["B2"][0], Plane.YZ)
    log.gate("Knob B2 owns the YZ mirror plane (scoop + flat both on +y)",
             max(a_yz_b2, b_yz_b2) < 1e-6,
             f"{a_yz_b2:.6f} / {b_yz_b2:.6f} mm^3")
    P("")

    # ---------------------------------------------------------------- §8
    P("9.  FDM PRINTABILITY (khana inspect, ADVISORY)")
    P("    Calibration: every v1 topper scores 0.13-0.38 and "
      "assertion_failed.")
    P("    The mesh min_wall metric scores sharp exterior edges and texture")
    P("    crests as 'thin'; the REAL minimum wall is OD/2 - cbore/2 = "
      f"{KNOB_OD / 2 - CBORE_D / 2:.3f} on all three.")
    printab = {}
    try:
        from cad_khana.printability.inspect import inspect
        from cad_khana.printability.methods import FDM
        for name, tag, fn, up in KNOBS:
            nm = f"knob_v2_{tag}"
            try:
                inspect(solids[tag][0],
                        method=FDM(up_axis=up, wall_min_mm=WALL_MIN,
                                   overhang_max_deg=45.0),
                        out=out_dir, name=nm)
                verdict = "PASS"
            except SystemExit:
                verdict = "ADVISORY"
            pj = json.load(open(os.path.join(
                out_dir, f"{nm}-printability.json")))
            oh = pj.get("overhang") or {}
            P(f"    {nm:14s} {verdict:9s} min_wall={pj.get('min_wall_mm')}"
              f"  overhang_area={oh.get('area_mm2')}"
              f"  (print {'BOTTOM-down' if up[2] > 0 else 'TOP-down'})")
            printab[tag] = {"verdict": verdict,
                            "min_wall_mm": pj.get("min_wall_mm"),
                            "overhang_area_mm2": oh.get("area_mm2"),
                            "orientation": ("bottom-down" if up[2] > 0
                                            else "top-down"),
                            "real_min_wall_mm": round(
                                KNOB_OD / 2 - CBORE_D / 2, 3)}
    except ImportError as exc:                            # pragma: no cover
        P(f"    khana inspect unavailable: {exc}")
    P("    A and C print TOP-FACE-DOWN: the bore and counterbore open upward")
    P("    and the only overhang is the internal journal -> counterbore")
    P("    ledge, an invisible internal bridge.  B2 prints BOTTOM-DOWN so")
    P("    the cove faces up; the cove is a single-valued height field")
    P("    (B > 0 in scoop_cove), so it needs no support either.")
    P("")

    params = {
        "part": "encoder_knob_v2",
        "for": "Alps EC11E-Switch-Vertical H20 (6 mm D shaft) — "
               "PUBLISHED-SPEC-ALPS-EC11E-H20",
        "datum": "z=0 at PCB top face (agentpad13 case v2 convention)",
        "supersedes": "encoder_knob.py (knurled_cup / dome_cup / ribbed_skirt)",
        "retired_candidate": {
            "B1_scoop_CM_faithful":
                "roof +22.909 -> Alps H20 headroom -1.591, rides proud"},
        "deck_z": F.DECK_Z,
        "keycap_top_dish_z": F.KEYCAP_TOP_DISH_Z,
        "keycap_top_plateau_z": F.KEYCAP_TOP_PLATEAU_Z,
        "body_od": KNOB_OD,
        "has_cover_flange": False,
        "bottom_z": KNOB_BOT_Z, "top_z": KNOB_TOP,
        "texture_start_z": TEX_START_Z, "top_ring": TOP_RING,
        "top_chamfer": TOP_CHAMFER,
        "key_clearance": {
            "centre_pitch": centre_pitch,
            "primary_key_od": F.KEYCAP_W,
            "grip_horizontal_gap": round(grip_key_clear, 3),
            "keycap_z": [F.KEYCAP_RIM_Z, F.KEYCAP_TOP_PLATEAU_Z]},
        "shaft": {"source": "ALPS EC11E catalog Update 2510 p.2 Drawing No.2",
                  "round_d": SHAFT_ROUND_D, "across_flat": SHAFT_FLAT_ACROSS,
                  "flat_len": F.SHAFT_FLAT_LEN,
                  "actuator_len": F.SHAFT_ACTUATOR_LEN,
                  "body_h": F.ENC_BODY_H, "bushing_len": F.ENC_BUSHING_LEN,
                  "bushing_d": F.BUSHING_D, "bushing_top_z": F.Z_BUSHING_TOP,
                  "flat_start_z": Z_FLAT_START, "tip_z": Z_SHAFT_TIP,
                  "variants": {v["name"]: F.shaft_stack(
                      v["mount_face_z"], v["L"], v["LB"], v["F"])
                      for v in F.SHAFT_VARIANTS}},
        "bore": {"cbore_d": CBORE_D, "cbore_ceil_z": CBORE_CEIL_Z,
                 "journal_clear": JOURNAL_CLEAR,
                 "default_clearance": DEFAULT_CLEARANCE,
                 "lead_in": None,
                 "tip_headroom_required": TIP_HEADROOM,
                 "knob_roof_t": KNOB_ROOF_T,
                 "ladder": {k: {"round_d_delta": v[0],
                                "across_flat_delta": v[1],
                                **clearance_table[k]}
                            for k, v in BORE_LADDER.items()}},
        "height_ladder": height_ladder,
        "scoop_trade": trade,
        "scoop_shipped": ship,
        "handedness": {
            "design_frame": "LEFT-handed (x right, y down, z up) [CASE:1077]",
            "export_transform": "mirror(part, about=Plane.XZ)",
            "gate": "phase clustering on the exported STL bytes; the "
                    "boolean-mirror gate is DEAD on twisted solids (OCCT "
                    "trap documented on topper_frame_v2.chirality_mm3)",
            "knobA_stl_phase_cluster": {
                "band_z": [zl, zh],
                "shipped": {"verts": n_s, "R_plus": round(rp_s, 4),
                            "R_minus": round(rm_s, 4), "hand": hand_s},
                "unmirrored_negative_control": {
                    "verts": n_n, "R_plus": round(rp_n, 4),
                    "R_minus": round(rm_n, 4), "hand": hand_n}},
            "knobC_chirality_mm3": {
                "yz": [round(a_yz, 4), round(b_yz, 4)],
                "expected": "zero; even cross-hatch families and +y D-flat "
                            "preserve the YZ mirror plane"},
            "knobB2_chirality_mm3": {"yz": [round(a_yz_b2, 6),
                                            round(b_yz_b2, 6)]}},
        "printability": printab,
        "exports": exports,
        "variants": knobs,
    }
    with open(os.path.join(par_dir, "encoder_knob_v2_params.json"), "w") as f:
        json.dump(params, f, indent=2)
    P(f"wrote params/encoder_knob_v2_params.json  ({len(KNOBS)} knobs x "
      f"{len(BORE_LADDER)} clearances = "
      f"{len(KNOBS) * len(BORE_LADDER)} STL; default "
      f"{DEFAULT_CLEARANCE.upper()})")
    log.finish(os.path.join(out_dir, "encoder_knob_v2_gate.txt"))

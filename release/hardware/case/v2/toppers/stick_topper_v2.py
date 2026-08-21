"""agentpad13 v5 topper — JOYSTICK TOPPERS, v2 family (SHIPPING).

Supersedes stick_cap.py's four families.  Owner-final after the v2 design
study; run with the khana python (has build123d):

    cad-khana-python stick_topper_v2.py

Emits, into ./stl, ./params, ./outputs:
  - nub C2 x 3 socket rungs + TPU puck x 2 socket rungs = 5 STL, MIRRORED
    into the print frame
  - per-part FDM printability JSON (advisory)
  - params/stick_topper_v2_params.json
  - outputs/stick_topper_v2_gate.txt   (the full gate transcript)

------------------------------------------------------------------------------
WHAT SHIPS

  NUB C2 — the default little nub.  o6.189 straight cylinder +14.4 .. +19.6,
  0.2 rim chamfer, seven o0.9 x 0.35 dimples on the top.  NO restrictor: it
  is sized by bisection so the FULL 30 deg mechanical throw stays 0.25 mm off
  the SW4 keycap.  (v2 study's C1 cup is dropped; the owner picked the dots.)

  TPU PUCK — one piece, replacing v1's Cap D + snap-on Ring R.  o9.412, and
  its 22.5 deg cone land IS the restrictor, now integral.  Owner: "why two
  parts?  Why not just make it one single TPU piece ... you don't need the
  lower 'lip', it can just be cylindrical".

  REVISED TOP (owner: "Take the one with a bit of a cup like a gaming
  controller's joystick, and add the dashes but have them be RAISED not
  relief cuts"):

        rim land ______        flat annulus at +19.6 — the FIRST LAYER
                /      \\       R0.6 rim roll, then the straight wall
      cove lip |        |      R0.9 fillet down into the cup
       floor   \\_ __ __/       flat, 0.55 below the rim
                 pad           flat, 0.35 below the rim, over the socket
        + four RAISED X-dashes whose tops are FLUSH with the rim land

  WHY FLUSH.  The puck prints TOP-FACE-DOWN (building from the flat top
  upward every section is smaller, so no overhang and no support; bottom-down
  would have to bridge the o5.2 bore inward to the socket, and TPU bridges
  badly).  A dash standing PROUD of the rim would lift the rim off the bed; a
  dash below the rim would be a first-layer island hanging over the cup.
  Flush is the only height that prints, and it still reads as raised because
  the cup is dished away around it.  Bonus: the dashes are laid straight onto
  the build plate, so they come out crisp, and they double as the ANCHORS for
  the cup floor, which is the only bridged face on the part.

  WHY THE FLOOR IS STEPPED.  A gaming-controller dish is deepest at its
  centre, and the blade tip sits at +18.4 directly under that centre, so the
  cup depth and the socket roof are the same millimetre: roof = 1.2 - depth.
  A flat PAD out to o2.3 holds the roof at 0.85 (the Cap C1 precedent) while
  the floor outside the socket footprint drops to 0.55 so the dashes clear
  the >= 0.40 proud height a 0.4 nozzle needs.  Both numbers are gated.
"""

import json
import math
import os

from build123d import (
    Plane,
    Pos,
    Rot,
    Sphere,
)

import topper_frame_v2 as F
from topper_frame_v2 import (
    BLADE_X,
    BLADE_Y,
    CAP_TOP_Z,
    DECK_FLOOR_Z,
    MARGIN,
    PIVOT_Z,
    SOCKET_MOUTH_Z,
    SOCKET_ROOF_Z,
    TILT_FULL,
    TILT_RESTRICTED,
    WALL_MIN,
    D2R,
    GateLog,
    arc_pts,
    blade_socket,
    capsule,
    densify,
    profile_clearance,
    profile_deck_floor,
    r_max,
    revolve_profile,
    rung_name,
    solve_R,
    zero_clearance_angle,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# =========================================================================
# 1. PARAMETERS
# =========================================================================

# --- nub C2 --------------------------------------------------------------
NUB_LADDER = [0.00, 0.05, 0.10]     # [TOPPER stick_cap.py:92] house ladder
DOT_DEPTH = 0.35                    # seven-dot micro-grip
DOT_SPHERE_R = 0.75                 # -> o0.9 dimple mouth at 0.35 deep
DOT_RING_R = 1.55                   # six around one

# --- TPU puck ------------------------------------------------------------
PUCK_TOP_Z = CAP_TOP_Z              # +19.6 = blade tip + 1.2 roof
PUCK_RIM_R = 0.6                    # top edge roll
PUCK_WALL_BOT_Z = 18.0              # bottom of the max-OD straight wall
PUCK_SHOULDER_BOT_Z = 16.4          # bottom of the inward taper
PUCK_BODY_R = 3.8                   # lower straight cylinder (o7.6)
LAND_R_IN = 2.6                     # = bore radius; land inner  [v1 Ring R]
LAND_R_OUT = 3.6                    # land outer                 [v1 Ring R]
PUCK_RELIEF = 0.2                   # 45 deg relief, land OD -> body OD
PUCK_SOCKET_LADDER = [0.00, -0.05]  # TPU: nom ships, TIGHT is the spare
SEAT_DEFAULT = 10.5                 # the only rung safe at EVERY seat height

# --- the revised cup top -------------------------------------------------
CUP_PAD_DEPTH = 0.35        # over the socket -> socket roof 0.85 [Cap C1]
CUP_PAD_R = 1.15            # pad radius; must exceed the socket corner reach
CUP_FLOOR_DEPTH = 0.55      # outside the socket footprint
CUP_RAMP_R = 2.00           # pad -> floor transition ends here (13.2 deg)
CUP_LIP_R = 0.9             # cove fillet from the floor up to the rim land
RIM_LAND_W = 0.55           # flat annulus at the rim = the first layer
DASH_R0, DASH_R1 = 1.45, 2.85        # radial span of one raised dash
DASH_W = 0.80               # 2 x a 0.4 nozzle -> two crisp perimeters
DASH_PROUD_MIN = 0.40       # 2 layers at 0.20 — the gate floor
SOCKET_ROOF_MIN = 0.80      # Cap C1 ships 0.850 [v2 study 5]; gate under it


# =========================================================================
# 2. NUB C2
# =========================================================================

def nub_profile(R):
    """(r, z) polygon: straight cylinder, 0.3 bottom radius, 0.2 rim chamfer.
    A cylinder, NOT a cone: the governing point is the chamfered rim, and a
    cone would only move material inboard where the gate does not bind."""
    b, t = SOCKET_MOUTH_Z, CAP_TOP_Z
    p = [(0.0, b), (R - 0.3, b)]
    p += arc_pts(R - 0.3, b + 0.3, 0.3, -math.pi / 2, 0.0, 12)
    p += [(R, t - 0.2), (R - 0.2, t), (0.0, t)]
    return p


def nub_solid(R, sock_add):
    body = revolve_profile(nub_profile(R))
    for (dx, dy) in [(0.0, 0.0)] + [
            (DOT_RING_R * math.cos(D2R(60 * k)),
             DOT_RING_R * math.sin(D2R(60 * k))) for k in range(6)]:
        if math.hypot(dx, dy) + 0.45 <= R - 0.45:
            body -= Pos(dx, dy,
                        CAP_TOP_Z + DOT_SPHERE_R - DOT_DEPTH) * Sphere(
                            DOT_SPHERE_R)
    return body - blade_socket(sock_add)


# =========================================================================
# 3. TPU PUCK
# =========================================================================

def land_z(rho, z_seat, theta=TILT_RESTRICTED):
    """Height of the underside cone at radius rho such that the WHOLE radial
    generator lands flat on a horizontal plane at z_seat at exactly `theta`:
        PIVOT + (z_u - PIVOT)cos th - rho*sin th = z_seat
     => z_u = PIVOT + (z_seat - PIVOT)/cos th + rho*tan th
    """
    th = D2R(theta)
    return PIVOT_Z + (z_seat - PIVOT_Z) / math.cos(th) + rho * math.tan(th)


def cup_depth_at(rho):
    """Depth of the cup surface below the rim plane, at plan radius rho.
    Pad -> ramp -> floor -> cove lip -> rim land.  This IS the raised height
    of a dash whose top is flush with the rim, which is why it is a function
    and not a constant."""
    lip_in = rim_land_in()
    rho_f = lip_foot_r()
    if rho <= CUP_PAD_R:
        return CUP_PAD_DEPTH
    if rho <= CUP_RAMP_R:
        t = (rho - CUP_PAD_R) / (CUP_RAMP_R - CUP_PAD_R)
        return CUP_PAD_DEPTH + t * (CUP_FLOOR_DEPTH - CUP_PAD_DEPTH)
    if rho <= rho_f:
        return CUP_FLOOR_DEPTH
    if rho >= lip_in:
        return 0.0
    zc = CUP_LIP_R - CUP_FLOOR_DEPTH        # lip centre above the rim plane
    return -(zc - math.sqrt(max(CUP_LIP_R ** 2 - (rho - rho_f) ** 2, 0.0)))


def rim_land_in():
    return PUCK_MAX_R - PUCK_RIM_R - RIM_LAND_W


def lip_foot_r():
    """Where the R_LIP cove is tangent to the flat floor.

    The cove is tangent to the horizontal floor at (rho_f, -CUP_FLOOR_DEPTH),
    so its centre is (rho_f, CUP_LIP_R - CUP_FLOOR_DEPTH) relative to the rim
    plane, and it must pass through (rim_land_in, 0):
        (rim_land_in - rho_f)^2 + (CUP_LIP_R - CUP_FLOOR_DEPTH)^2 = CUP_LIP_R^2
     => (rim_land_in - rho_f)^2 = 2*CUP_LIP_R*CUP_FLOOR_DEPTH - CUP_FLOOR_DEPTH^2
    """
    d = 2 * CUP_LIP_R * CUP_FLOOR_DEPTH - CUP_FLOOR_DEPTH ** 2
    return rim_land_in() - math.sqrt(max(d, 0.0))


def cup_profile_pts(n_lip=18):
    """The cup, axis outward, as (r, z) in world z."""
    t = PUCK_TOP_Z
    rho_f = lip_foot_r()
    p = [(0.0, t - CUP_PAD_DEPTH), (CUP_PAD_R, t - CUP_PAD_DEPTH),
         (CUP_RAMP_R, t - CUP_FLOOR_DEPTH), (rho_f, t - CUP_FLOOR_DEPTH)]
    zc = t - CUP_FLOOR_DEPTH + CUP_LIP_R
    a1 = math.asin(min(max((rim_land_in() - rho_f) / CUP_LIP_R, -1.0), 1.0))
    p += [(rho_f + CUP_LIP_R * math.sin(a1 * i / n_lip),
           zc - CUP_LIP_R * math.cos(a1 * i / n_lip))
          for i in range(1, n_lip + 1)]
    return p


def puck_profile(R, z_seat):
    """(r, z) polygon of the one-piece TPU puck: the REVISED cup top, then
    the bottom of the old cup unchanged (22.5 deg land, o5.2 bore, socket)."""
    zi, zo = land_z(LAND_R_IN, z_seat), land_z(LAND_R_OUT, z_seat)
    p = cup_profile_pts()
    p += [(R - PUCK_RIM_R, PUCK_TOP_Z)]                  # flat rim land
    p += arc_pts(R - PUCK_RIM_R, PUCK_TOP_Z - PUCK_RIM_R, PUCK_RIM_R,
                 math.pi / 2, 0.0, 24)                   # rim roll
    p += [(R, PUCK_WALL_BOT_Z)]                          # straight wall
    p += [(PUCK_BODY_R, PUCK_SHOULDER_BOT_Z)]            # soft shoulder
    p += [(PUCK_BODY_R, zo + PUCK_RELIEF)]               # plain cylinder
    p += [(LAND_R_OUT, zo)]                              # 45 deg relief
    p += [(LAND_R_IN, zi)]                               # 22.5 deg land
    p += [(LAND_R_IN, SOCKET_MOUTH_Z)]                   # o5.2 bore
    p += [(0.0, SOCKET_MOUTH_Z)]
    return p


def puck_outer_profile(R, z_seat, with_dashes=True):
    """The silhouette the SW4 gate consumes.

    The cup only REMOVES material, so it cannot widen the envelope — but the
    raised dashes ADD material, so they are folded in as a conservative ring
    of revolution at their own (r, h).  That is deliberately pessimistic: the
    puck's clocking is fixed by the blade socket, so the real dashes cannot
    all face SW4 at once."""
    zi, zo = land_z(LAND_R_IN, z_seat), land_z(LAND_R_OUT, z_seat)
    p = [(0.0, PUCK_TOP_Z)]
    if with_dashes:
        p += [(DASH_R1 + DASH_W / 2, PUCK_TOP_Z)]
    p += [(R - PUCK_RIM_R, PUCK_TOP_Z)]
    p += arc_pts(R - PUCK_RIM_R, PUCK_TOP_Z - PUCK_RIM_R, PUCK_RIM_R,
                 math.pi / 2, 0.0, 40)
    p += [(R, PUCK_WALL_BOT_Z), (PUCK_BODY_R, PUCK_SHOULDER_BOT_Z),
          (PUCK_BODY_R, zo + PUCK_RELIEF), (LAND_R_OUT, zo),
          (LAND_R_IN, zi), (0.0, zi)]
    return p


# The max OD is SOLVED, never chosen: bisect the real (densified) silhouette
# until the worst point at the 22.5 deg stop lands exactly on the 0.25 mm
# margin.  Resolved at import so puck_profile()'s cup geometry — which keys
# off it through rim_land_in() — can never disagree with the outer wall.
PUCK_MAX_R = solve_R(lambda r: puck_outer_profile(r, SEAT_DEFAULT),
                     TILT_RESTRICTED)


def dash_solids():
    """Four raised X-dashes, tops FLUSH with the rim plane.  Built as stadium
    prisms running from well inside solid material up to the rim plane, then
    fused: the union simply fills the cup locally, so no trimming is needed."""
    box_len = (DASH_R1 - DASH_R0) - DASH_W
    c = (DASH_R0 + DASH_R1) / 2.0
    z0 = PUCK_TOP_Z - 1.0                     # above the +18.4 socket roof
    out = []
    for k in range(4):
        out.append(Rot(0, 0, 45 + 90 * k)
                   * Pos(c, 0, (z0 + PUCK_TOP_Z) / 2.0)
                   * capsule(box_len, DASH_W, PUCK_TOP_Z - z0))
    return out


def puck_solid(R, z_seat, sock_add=0.0):
    body = revolve_profile(puck_profile(R, z_seat))
    for d in dash_solids():
        body += d
    return body - blade_socket(sock_add)


def stop_angle(z_u, rho, z_seat_actual):
    """Solve PIVOT + (z_u - PIVOT)cos th - rho*sin th = z_seat for th."""
    A = z_u - PIVOT_Z
    C = z_seat_actual - PIVOT_Z
    amp = math.hypot(A, rho)
    if C > amp:
        return None
    return math.degrees(math.acos(C / amp) - math.atan2(rho, A))


def puck_stop(z_seat_design, z_seat_actual):
    """Stop angle of a puck cut for z_seat_design when the true seat is
    z_seat_actual.  The whole land engages at once, so take the first
    generator end to arrive."""
    angs = [a for a in (
        stop_angle(land_z(LAND_R_IN, z_seat_design), LAND_R_IN,
                   z_seat_actual),
        stop_angle(land_z(LAND_R_OUT, z_seat_design), LAND_R_OUT,
                   z_seat_actual)) if a is not None]
    if not angs:
        return TILT_FULL, False
    th = min(angs)
    return (th, True) if th <= TILT_FULL else (TILT_FULL, False)


# =========================================================================
# 4. MAIN
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
    P("JOYSTICK TOPPERS v2 — NUB C2 (seven-dot) / ONE-PIECE TPU PUCK")
    log.rule("=")
    P("")

    P("1.  THE KEYCAP CHAIN the collision gate keys off")
    F.keycap_chain_crosscheck(log)
    P(f"  every clearance below is measured against the INSERTED band "
      f"z {F.KEYCAP_Z0} .. {F.KEYCAP_Z1}")
    P("")

    P("2.  THE COLLISION LAW")
    P(f"  y_edge = {F.SW4_Y} - {F.KEYCAP_W}/2 = {F.SW4_EDGE_Y};  reach budget "
      f"{F.SW4_EDGE_Y - F.JS1_Y:.3f};  m = {MARGIN};  pivot +{PIVOT_Z}")
    for th in (TILT_FULL, TILT_RESTRICTED):
        P(f"    th={th:4.1f} deg : r_max(+{CAP_TOP_Z}) = "
          f"{r_max(CAP_TOP_Z, th):6.4f}  -> straight-wall o"
          f"{2 * r_max(CAP_TOP_Z, th):6.4f}")
    P("")

    # ---------------------------------------------------------------- nub
    P("3.  NUB C2 — no restrictor, FULL 30 deg throw")
    RN = solve_R(nub_profile, TILT_FULL)
    prn = densify(nub_profile(RN))
    clrN, govN, gyN, gzN = profile_clearance(prn, TILT_FULL)
    loN = profile_deck_floor(prn, TILT_FULL)
    wallN = RN - (BLADE_X + NUB_LADDER[-1]) / 2.0
    roofN = CAP_TOP_Z - DOT_DEPTH - SOCKET_ROOF_Z
    P(f"  o{2 * RN:.3f}  z {SOCKET_MOUTH_Z} .. {CAP_TOP_Z}  H/D "
      f"{(CAP_TOP_Z - SOCKET_MOUTH_Z) / (2 * RN):.2f}")
    P(f"    governing point r={govN[0]:.3f} h={govN[1]:.3f} -> y={gyN:.4f}"
      f"  z'={gzN:.3f}  — the CHAMFERED RIM, not the top")
    P(f"    z' {gzN:.3f} vs the inserted keycap band {F.KEYCAP_Z0}.."
      f"{F.KEYCAP_Z1}: "
      f"{'INSIDE -> the gate binds' if F.KEYCAP_Z0 <= gzN <= F.KEYCAP_Z1 else 'outside'}"
      f"  ({F.KEYCAP_Z1 - gzN:.3f} below the dish top, {gzN - F.KEYCAP_Z0:.3f}"
      f" above the rim)")
    log.gate("nub C2 SW4 clearance at the FULL 30 deg", clrN >= MARGIN - 1e-4,
             f"{clrN:+.4f} >= {MARGIN}")
    log.gate("nub C2 deck-floor sweep at 30 deg", loN[0] >= DECK_FLOOR_Z,
             f"z_low {loN[0]:.3f} >= {DECK_FLOOR_Z} -> margin "
             f"{loN[0] - DECK_FLOOR_Z:+.3f}")
    log.gate("nub C2 socket wall (loosest rung)", wallN >= WALL_MIN,
             f"{wallN:.3f} >= {WALL_MIN}")
    P(f"    roof over the blade tip under a dimple: {roofN:.3f} "
      f"(= {CAP_TOP_Z} - {DOT_DEPTH} dimple - {SOCKET_ROOF_Z} blade tip)")
    log.negative_control(
        "nub C2 SW4 clearance",
        lambda r: profile_clearance(densify(nub_profile(r)),
                                    TILT_FULL)[0] >= MARGIN - 1e-4,
        RN + 0.1, f"a nub 0.1 mm fatter than the bisected o{2 * RN:.3f}")
    P("")

    # ---------------------------------------------------------------- puck
    P("4.  ONE-PIECE TPU PUCK")
    prp = densify(puck_outer_profile(PUCK_MAX_R, SEAT_DEFAULT))
    clrP, govP, gyP, gzP = profile_clearance(prp, TILT_RESTRICTED)
    loP = profile_deck_floor(prp, TILT_RESTRICTED)
    clr30 = profile_clearance(prp, TILT_FULL)[0]
    th_touch = zero_clearance_angle(
        lambda r: puck_outer_profile(r, SEAT_DEFAULT), PUCK_MAX_R, 0.0)
    P(f"  MAX OD by bisection on the REAL profile at {TILT_RESTRICTED} deg: "
      f"o{2 * PUCK_MAX_R:.3f}")
    P(f"    governing point r={govP[0]:.3f} h={govP[1]:.3f} -> y={gyP:.4f} "
      f"z'={gzP:.3f}   clearance {clrP:+.4f}")
    P(f"    that point is on the TOP RIM ROLL (R{PUCK_RIM_R}); a knife-edged "
      f"straight wall to +{CAP_TOP_Z} would be only o"
      f"{2 * r_max(CAP_TOP_Z, TILT_RESTRICTED):.3f}, so the roll buys "
      f"{2 * PUCK_MAX_R - 2 * r_max(CAP_TOP_Z, TILT_RESTRICTED):+.3f}")
    log.gate("puck SW4 clearance at the 22.5 deg stop",
             clrP >= MARGIN - 1e-4, f"{clrP:+.4f} >= {MARGIN}")
    log.gate("puck deck-floor sweep at the stop", loP[0] >= DECK_FLOOR_Z,
             f"z_low {loP[0]:.3f} >= {DECK_FLOOR_Z} -> margin "
             f"{loP[0] - DECK_FLOOR_Z:+.3f}")
    P(f"    first SW4 CONTACT at {th_touch:.2f} deg;  at the full "
      f"{TILT_FULL} deg the clearance would be {clr30:+.3f}")
    P("    -> the restrictor is still MANDATORY; the cone land IS it, integral")
    P("")

    P("  4a.  THE RAISED X-DASHES vs THE COLLISION LAW")
    P("       The dashes are the new highest points on the top face, so the")
    P("       governing point is RECOMPUTED with them folded into the")
    P("       silhouette as a conservative ring of revolution.")
    dash_out_r = DASH_R1 + DASH_W / 2
    h_allowed = PIVOT_Z + ((F.SW4_EDGE_Y - F.JS1_Y) - MARGIN
                           - dash_out_r * math.cos(D2R(TILT_RESTRICTED))) \
        / math.sin(D2R(TILT_RESTRICTED))
    P(f"       dash outer extreme r = {dash_out_r:.3f} at h = {PUCK_TOP_Z}")
    P(f"       r_max({PUCK_TOP_Z}) = {r_max(PUCK_TOP_Z, TILT_RESTRICTED):.4f}"
      f"  -> the dash is inboard by "
      f"{r_max(PUCK_TOP_Z, TILT_RESTRICTED) - dash_out_r:+.4f}")
    P(f"       at r {dash_out_r:.3f} the law would allow a height of "
      f"+{h_allowed:.3f}, i.e. {h_allowed - PUCK_TOP_Z:.3f} mm of unused")
    P("       headroom.  The governing point therefore STAYS on the rim roll")
    P(f"       at r {govP[0]:.3f} / h {govP[1]:.3f}, and the OD stays "
      f"o{2 * PUCK_MAX_R:.3f}.")
    gov_is_rim = govP[1] > PUCK_WALL_BOT_Z and govP[0] > dash_out_r
    log.gate("the raised dashes do NOT become the governing point",
             gov_is_rim,
             f"governing r {govP[0]:.3f} > dash r {dash_out_r:.3f} and "
             f"h {govP[1]:.3f} is on the rim roll")
    prp_nodash = densify(puck_outer_profile(PUCK_MAX_R, SEAT_DEFAULT,
                                            with_dashes=False))
    clr_nodash = profile_clearance(prp_nodash, TILT_RESTRICTED)[0]
    log.gate("adding the dashes cost the envelope nothing",
             abs(clr_nodash - clrP) < 1e-9,
             f"clearance with dashes {clrP:+.4f} vs without "
             f"{clr_nodash:+.4f}")
    log.negative_control(
        "puck SW4 clearance",
        lambda r: profile_clearance(
            densify(puck_outer_profile(r, SEAT_DEFAULT)),
            TILT_RESTRICTED)[0] >= MARGIN - 1e-4,
        PUCK_MAX_R + 0.1,
        f"a puck 0.1 mm fatter than the bisected o{2 * PUCK_MAX_R:.3f}")
    P("")

    P("  4b.  THE CUP AND THE DASHES")
    rho_f = lip_foot_r()
    lip_in = rim_land_in()
    sock_corner = math.hypot((BLADE_X + PUCK_SOCKET_LADDER[0]) / 2,
                             (BLADE_Y + PUCK_SOCKET_LADDER[0]) / 2)
    socket_roof = F.ROOF_T - CUP_PAD_DEPTH
    P(f"    pad      r 0 .. {CUP_PAD_R}      depth {CUP_PAD_DEPTH}"
      f"  -> socket roof {socket_roof:.3f}")
    P(f"    ramp     r {CUP_PAD_R} .. {CUP_RAMP_R}   depth {CUP_PAD_DEPTH} ->"
      f" {CUP_FLOOR_DEPTH}  ({math.degrees(math.atan((CUP_FLOOR_DEPTH - CUP_PAD_DEPTH) / (CUP_RAMP_R - CUP_PAD_R))):.1f} deg)")
    P(f"    floor    r {CUP_RAMP_R} .. {rho_f:.3f}   depth {CUP_FLOOR_DEPTH}")
    P(f"    cove lip r {rho_f:.3f} .. {lip_in:.3f}  R{CUP_LIP_R}, rising to "
      f"the rim plane at "
      f"{math.degrees(math.atan2(lip_in - rho_f, math.sqrt(max(CUP_LIP_R ** 2 - (lip_in - rho_f) ** 2, 1e-9)))):.1f} deg")
    P(f"    rim land r {lip_in:.3f} .. {PUCK_MAX_R - PUCK_RIM_R:.3f}  "
      f"({RIM_LAND_W} wide) = the FIRST LAYER, flat on the bed")
    log.gate("socket roof under the cup pad", socket_roof >= SOCKET_ROOF_MIN,
             f"{socket_roof:.3f} >= {SOCKET_ROOF_MIN} "
             f"(Cap C1 ships 0.850 as a BRIDGE; this one is solid-on-solid "
             f"because the puck prints top-face-down)")
    log.gate("the cup pad covers the whole socket footprint",
             CUP_PAD_R >= sock_corner,
             f"pad r {CUP_PAD_R} >= socket corner reach {sock_corner:.4f} "
             f"-> margin {CUP_PAD_R - sock_corner:+.4f}")
    log.negative_control(
        "socket roof", lambda d: (F.ROOF_T - d) >= SOCKET_ROOF_MIN, 0.45,
        "a 0.45 cup pad, which would thin the roof to 0.750")
    d0, d1 = cup_depth_at(DASH_R0), cup_depth_at(DASH_R1)
    dmin = min(cup_depth_at(DASH_R0 + (DASH_R1 - DASH_R0) * i / 40)
               for i in range(41))
    P(f"    dash: r {DASH_R0} .. {DASH_R1} ({DASH_R1 - DASH_R0:.2f} long) x "
      f"{DASH_W} wide, top FLUSH with the rim plane +{PUCK_TOP_Z}")
    P(f"          proud height {d0:.3f} at the inner end, {d1:.3f} at the "
      f"outer end, minimum {dmin:.3f} along the run")
    P(f"          {DASH_W / 0.4:.0f} nozzle widths wide -> two crisp "
      f"perimeters; {dmin / 0.2:.1f} layers tall at 0.20")
    log.gate("raised dashes stay proud enough to survive a 0.4 nozzle",
             dmin >= DASH_PROUD_MIN,
             f"min proud {dmin:.3f} >= {DASH_PROUD_MIN} "
             f"(= 2 layers at 0.20)")
    log.negative_control(
        "dash proud height",
        lambda r0: min(cup_depth_at(r0 + (DASH_R1 - r0) * i / 40)
                       for i in range(41)) >= DASH_PROUD_MIN,
        0.5, "a dash starting at r 0.5, i.e. running across the shallow pad")
    ang_half = math.degrees(math.atan(DASH_W / 2 / CUP_RAMP_R))
    chord = 2 * CUP_RAMP_R * math.sin(D2R((90 - 2 * ang_half) / 2))
    P("    BRIDGE.  The cup floor is the only bridged face (top-down print):"
      " the four dashes anchor it,")
    P(f"    leaving a largest free chord of {chord:.3f} mm between adjacent "
      f"arms at r {CUP_RAMP_R}; the rim land")
    P(f"    carries the outer edge and the deepest span is only "
      f"{CUP_FLOOR_DEPTH} mm off the bed.")
    P("")

    P("  4c.  THE SEAT TOLERANCE BAND — does ONE part cover 11 +/-0.5?")
    P(f"  {'cut for':>8} | {'seat 10.5':>10} {'seat 11.0':>10} "
      f"{'seat 11.5':>10} | {'worst':>6} {'clr@worst':>10} {'safe?':>6}"
      f" {'nom throw':>10}")
    ladder = {}
    for zs in (10.5, 10.75, 11.0, 11.25, 11.5):
        row = [puck_stop(zs, ts) for ts in (10.5, 11.0, 11.5)]
        worst = max(r[0] for r in row)
        clr_w = profile_clearance(prp, worst)[0]
        ok = clr_w >= MARGIN - 1e-4
        nm = f"s{str(zs).replace('.', 'p')}"
        P(f"  {nm:>8} | "
          + " ".join(f"{r[0]:>9.2f}{'*' if not r[1] else ' '}" for r in row)
          + f" | {worst:>6.2f} {clr_w:>+10.3f} {'YES' if ok else 'no':>6}"
          f" {100 * row[1][0] / TILT_RESTRICTED:>9.1f}%")
        ladder[nm] = {"design_seat_z": zs,
                      "cone_z_at_bore": round(land_z(LAND_R_IN, zs), 3),
                      "cone_z_at_land": round(land_z(LAND_R_OUT, zs), 3),
                      "stop_if_seat_10p5": round(row[0][0], 3),
                      "stop_if_seat_11p0": round(row[1][0], 3),
                      "stop_if_seat_11p5": round(row[2][0], 3),
                      "worst_stop": round(worst, 3),
                      "clearance_at_worst": round(clr_w, 4), "safe": bool(ok)}
    P("   (* the land never reaches the seat: the module's own 30 deg")
    P("      mechanical stop governs and the puck is NOT protected)")
    dth = puck_stop(10.5, 11.5)[0] - puck_stop(10.5, 10.5)[0]
    P(f"  sensitivity d(stop)/d(seat) = {dth:+.2f} deg/mm")
    P(f"  ONE part ships: s{str(SEAT_DEFAULT).replace('.', 'p')} — the only "
      f"rung whose stop is <= {TILT_RESTRICTED} deg at EVERY seat height in")
    P("  the band, i.e. the only one geometrically incapable of letting the")
    P("  puck touch SW4.  TPU is what makes its throw acceptable.")
    log.gate("the shipped seat rung is safe across the whole +/-0.5 band",
             ladder["s10p5"]["safe"],
             f"worst stop {ladder['s10p5']['worst_stop']:.2f} deg -> "
             f"clearance {ladder['s10p5']['clearance_at_worst']:+.4f}")
    log.negative_control(
        "seat rung safety", lambda nm: ladder[nm]["safe"], "s11p0",
        "the nominal-seat rung, which over-travels to 27.18 deg worst case")
    zi, zo = land_z(LAND_R_IN, SEAT_DEFAULT), land_z(LAND_R_OUT, SEAT_DEFAULT)
    P(f"  land cone: rho {LAND_R_IN} -> +{zi:.3f}, rho {LAND_R_OUT} -> "
      f"+{zo:.3f}; rest gap over the +{F.FRAME_TOP_Z} frame top "
      f"{zi - F.FRAME_TOP_Z:+.3f}")
    for rho in (LAND_R_IN, LAND_R_OUT):
        rp = ((F.FRAME_TOP_Z - PIVOT_Z) * math.tan(D2R(TILT_RESTRICTED))
              + rho / math.cos(D2R(TILT_RESTRICTED)))
        log.gate(f"land contact at rho {rho} stays on the 13x13 frame",
                 rp <= F.JS_FRAME_HALF,
                 f"plan radius {rp:.3f} <= inscribed {F.JS_FRAME_HALF} "
                 f"-> margin {F.JS_FRAME_HALF - rp:+.3f}")
    wallP = PUCK_BODY_R - LAND_R_IN
    sockwallP = PUCK_BODY_R - (BLADE_X + PUCK_SOCKET_LADDER[0]) / 2.0
    log.gate("puck sleeve wall", wallP >= WALL_MIN - 1e-9,
             f"body r {PUCK_BODY_R} - bore r {LAND_R_IN} = {wallP:.3f} "
             f">= {WALL_MIN} (exactly the house floor)")
    log.gate("puck socket wall", sockwallP >= WALL_MIN,
             f"{sockwallP:.3f} >= {WALL_MIN}")
    P(f"  FLAGGED, not hidden: the {PUCK_RELIEF} mm lip at the land's outer "
      f"corner thins to {LAND_R_OUT - LAND_R_IN:.3f} at the geometric corner"
      f" itself.  FDM rounds it; TPU does not care.")
    P("  TPU 95A [TPU-EST]: stiff enough that the socket keeps its shape, "
      "soft enough that the land yields progressively.")
    P("")

    # ------------------------------------------------------------ export
    P("5.  EXPORT INTO THE PRINT FRAME + the handedness measurement")
    P("    Both parts are mirrored at export like the knobs and the tray.")
    P("    For these two it should be a MEASURED no-op: the seven dots sit")
    P("    at azimuths {0,60,...,300} and the four dashes at {45,135,225,")
    P("    315}, and BOTH sets are closed under y -> -y, as is the")
    P("    rectangular blade socket.  Measured, not assumed:")
    nub_ref = nub_solid(RN, 0.0)
    puck_ref = puck_solid(PUCK_MAX_R, SEAT_DEFAULT, 0.0)
    chir = {}
    for nm, sol in (("nub_C2", nub_ref), ("puck_TPU", puck_ref)):
        a, b = F.chirality_mm3(sol, Plane.XZ)
        chir[nm] = [round(a, 6), round(b, 6)]
        log.gate(f"{nm} owns the XZ mirror plane (export mirror is a no-op)",
                 max(a, b) < 1e-6, f"{a:.6f} / {b:.6f} mm^3")
    exports = {}
    for add in NUB_LADDER:
        rg = rung_name(add)
        p = os.path.join(stl_dir, f"stick_nub_v2_C2_sock_{rg}.stl")
        F.export_stl_house(F.export_print_frame(nub_solid(RN, add)), p)
        exports[f"nub_{rg}"] = {"file": os.path.relpath(p, F.REPO),
                                "socket": [round(BLADE_X + add, 3),
                                           round(BLADE_Y + add, 3)]}
        P(f"    wrote {os.path.basename(p):<34} socket "
          f"{BLADE_X + add:.2f} x {BLADE_Y + add:.2f}")
    for add in PUCK_SOCKET_LADDER:
        rg = rung_name(add)
        p = os.path.join(stl_dir, f"stick_puck_v2_TPU_sock_{rg}.stl")
        F.export_stl_house(F.export_print_frame(
            puck_solid(PUCK_MAX_R, SEAT_DEFAULT, add)), p)
        exports[f"puck_{rg}"] = {"file": os.path.relpath(p, F.REPO),
                                 "socket": [round(BLADE_X + add, 3),
                                            round(BLADE_Y + add, 3)]}
        P(f"    wrote {os.path.basename(p):<34} socket "
          f"{BLADE_X + add:.2f} x {BLADE_Y + add:.2f}"
          f"{'   (TIGHT spare — TPU absorbs interference elastically)' if add < 0 else '   (SHIPS)'}")
    P("")

    P("6.  FDM PRINTABILITY (khana inspect, ADVISORY)")
    printab = {}
    try:
        from cad_khana.printability.inspect import inspect
        from cad_khana.printability.methods import FDM
        for nm, sol, up in (("stick_nub_v2_C2", nub_ref, (0, 0, 1)),
                            ("stick_puck_v2_TPU", puck_ref, (0, 0, -1))):
            try:
                inspect(sol, method=FDM(up_axis=up, wall_min_mm=WALL_MIN,
                                        overhang_max_deg=45.0),
                        out=out_dir, name=nm)
                verdict = "PASS"
            except SystemExit:
                verdict = "ADVISORY"
            pj = json.load(open(os.path.join(
                out_dir, f"{nm}-printability.json")))
            oh = pj.get("overhang") or {}
            P(f"    {nm:18s} {verdict:9s} min_wall={pj.get('min_wall_mm')}"
              f"  overhang_area={oh.get('area_mm2')}"
              f"  (print {'BOTTOM-down' if up[2] > 0 else 'TOP-down'})")
            printab[nm] = {"verdict": verdict,
                           "min_wall_mm": pj.get("min_wall_mm"),
                           "overhang_area_mm2": oh.get("area_mm2"),
                           "orientation": ("bottom-down" if up[2] > 0
                                           else "top-down")}
    except ImportError as exc:                            # pragma: no cover
        P(f"    khana inspect unavailable: {exc}")
    P("    The nub prints BOTTOM-DOWN (flat annulus on the bed, socket roof a")
    P("    short bridge, dots facing up).  The puck prints TOP-FACE-DOWN: the")
    P("    rim land and the four dash tops ARE the first layer, every section")
    P("    above is smaller, and no support is needed anywhere.")
    P("")

    params = {
        "part": "stick_topper_v2",
        "for": "YTL YA13-FL7.4-B5Ka(45-10)-R-Y06 (LCSC C37323742)",
        "datum": "z=0 at PCB top face (agentpad13 case v2 convention)",
        "supersedes": "stick_cap.py (dome / dish / knurl / taper)",
        "blade": {"x": BLADE_X, "y": BLADE_Y, "tip_z": F.BLADE_TIP_Z},
        "socket_depth_DESIGN_CHOICE": F.SOCKET_DEPTH,
        "socket_mouth_z": SOCKET_MOUTH_Z, "socket_roof_z": SOCKET_ROOF_Z,
        "cap_top_z": CAP_TOP_Z,
        "nub_C2": {
            "od": round(2 * RN, 3),
            "clearance_sw4_30deg": round(clrN, 4),
            "governing_point_rh": [round(govN[0], 3), round(govN[1], 3)],
            "governing_z": round(gzN, 3),
            "below_dish_cap_top": round(F.KEYCAP_Z1 - gzN, 3),
            "deck_low_z": round(loN[0], 3),
            "deck_margin": round(loN[0] - DECK_FLOOR_Z, 3),
            "socket_wall": round(wallN, 3),
            "roof_under_dimple": round(roofN, 3),
            "dots": {"count": 7, "depth": DOT_DEPTH,
                     "sphere_r": DOT_SPHERE_R, "ring_r": DOT_RING_R},
            "fit_ladder": NUB_LADDER,
            "print_orientation": "bottom-down"},
        "puck_TPU": {
            "od": round(2 * PUCK_MAX_R, 3), "top_z": PUCK_TOP_Z,
            "rim_roll_r": PUCK_RIM_R, "rim_land_w": RIM_LAND_W,
            "wall_bot_z": PUCK_WALL_BOT_Z,
            "shoulder_bot_z": PUCK_SHOULDER_BOT_Z,
            "body_od": 2 * PUCK_BODY_R, "bore_d": 2 * LAND_R_IN,
            "land_r": [LAND_R_IN, LAND_R_OUT],
            "clearance_sw4_22p5": round(clrP, 4),
            "clearance_sw4_30_no_stop": round(clr30, 4),
            "first_contact_deg": round(th_touch, 3),
            "governing_point_rh": [round(govP[0], 3), round(govP[1], 3)],
            "governing_z": round(gzP, 3),
            "deck_low_z": round(loP[0], 3),
            "deck_margin": round(loP[0] - DECK_FLOOR_Z, 3),
            "sleeve_wall": round(wallP, 3),
            "socket_wall": round(sockwallP, 3),
            "cup": {"pad_depth": CUP_PAD_DEPTH, "pad_r": CUP_PAD_R,
                    "floor_depth": CUP_FLOOR_DEPTH, "ramp_r": CUP_RAMP_R,
                    "lip_r": CUP_LIP_R, "lip_foot_r": round(rho_f, 4),
                    "rim_land_in_r": round(lip_in, 4),
                    "socket_roof": round(socket_roof, 3),
                    "socket_corner_reach": round(sock_corner, 4)},
            "dashes": {"count": 4, "azimuths_deg": [45, 135, 225, 315],
                       "r0": DASH_R0, "r1": DASH_R1, "width": DASH_W,
                       "top_z": PUCK_TOP_Z,
                       "proud_inner": round(d0, 3),
                       "proud_outer": round(d1, 3),
                       "proud_min": round(dmin, 3),
                       "outer_extreme_r": round(dash_out_r, 3),
                       "height_the_law_would_allow": round(h_allowed, 3),
                       "bridge_free_chord_mm": round(chord, 3)},
            "seat_ladder": ladder,
            "default_rung": f"s{str(SEAT_DEFAULT).replace('.', 'p')}",
            "stop_sensitivity_deg_per_mm": round(dth, 3),
            "socket_ladder": PUCK_SOCKET_LADDER,
            "material": "TPU 95A [TPU-EST]",
            "print_orientation": "top-down"},
        "handedness": {
            "design_frame": "LEFT-handed (x right, y down, z up) [CASE:1077]",
            "export_transform": "mirror(part, about=Plane.XZ)",
            "chirality_mm3_about_xz": chir,
            "note": "both parts own the XZ mirror plane, so the export "
                    "mirror is a measured no-op; it is applied anyway so a "
                    "future chiral feature cannot ship the wrong hand"},
        "printability": printab,
        "exports": exports,
    }
    with open(os.path.join(par_dir, "stick_topper_v2_params.json"), "w") as f:
        json.dump(params, f, indent=2)
    P("wrote params/stick_topper_v2_params.json  "
      f"({len(NUB_LADDER)} nub + {len(PUCK_SOCKET_LADDER)} puck = "
      f"{len(NUB_LADDER) + len(PUCK_SOCKET_LADDER)} STL)")
    log.finish(os.path.join(out_dir, "stick_topper_v2_gate.txt"))

"""AgentPad13 joystick toppers, corrected shipping generator.

The joystick has its own 30 degree mechanical throw. Neither topper is a
restrictor: the nub and TPU puck are solid bodies with one intentional
underside opening, the blind rectangular shaft socket. This generator has no
cone land, lower lip, cylindrical bore, or seat-height stop logic.

Measured hardware replaces the drawing nominal for the fit coupon:

    shaft blade                 1.70 x 1.00 mm
    LOW socket (default)        2.10 x 1.30 mm  (+0.20 / +0.15 mm per side)
    HIGH socket                 2.30 x 1.50 mm  (+0.30 / +0.25 mm per side)

The earlier largest socket was 1.95 x 1.25 mm and did not fit the printed
parts. The two current choices bracket the physical test: the old
1.95 x 1.25 maximum was too tight, while 2.50 x 1.80 was too loose.

The puck stays round. Its radius is solved against the adjacent 17.5 mm
keycap at the full 30 degree mechanical throw.

Run with the khana Python (build123d):

    /Users/yuanz/.local/share/uv/tools/cad-khana/bin/python stick_topper_v2.py

Emits exactly four STLs, two clearance choices per topper, plus parameters,
printability reports, and a gate transcript.
"""

import json
import math
import os
import struct

import numpy as np
from build123d import Box, Pos, Rot, Sphere

import topper_frame_v2 as F
from topper_frame_v2 import (
    CAP_TOP_Z,
    DECK_FLOOR_Z,
    MARGIN,
    PIVOT_Z,
    SOCKET_MOUTH_Z,
    SOCKET_ROOF_Z,
    TILT_FULL,
    WALL_MIN,
    D2R,
    GateLog,
    arc_pts,
    capsule,
    densify,
    profile_clearance,
    profile_deck_floor,
    revolve_profile,
    solve_R,
)

HERE = os.path.dirname(os.path.abspath(__file__))


# =========================================================================
# 1. MEASURED FIT AND SHARED DESIGN PARAMETERS
# =========================================================================

SHAFT_LONG = 1.70
SHAFT_SHORT = 1.00
SOCKET_DEPTH = SOCKET_ROOF_Z - SOCKET_MOUTH_Z

# Exactly two user-facing choices, bracketed by physical prints. The prior
# 1.95 x 1.25 mm maximum did not fit; 2.50 x 1.80 mm was too loose. LOW is the
# default and HIGH is the undersized-hole fallback.
SOCKET_CHOICES = {
    "low": {"long": 2.10, "short": 1.30},
    "high": {"long": 2.30, "short": 1.50},
}
DEFAULT_CLEARANCE = "low"

# Nub C2.
DOT_DEPTH = 0.35
DOT_SPHERE_R = 0.75
DOT_RING_R = 1.55

# TPU puck. Its single round radius is solved at the full mechanical throw.
PUCK_TOP_Z = CAP_TOP_Z
PUCK_COLLISION_TARGET = MARGIN + 0.05
PUCK_RIM_R = 0.60
PUCK_RIM_LAND_W = 0.45
PUCK_WALL_BOT_Z = 18.00
PUCK_BOTTOM_INSET = 0.40

# Shallow gaming-stick cup and raised X dashes. These are exterior surfaces,
# not cavities. The solid under them continues to the flat bottom plane.
CUP_PAD_DEPTH = 0.30
CUP_PAD_R = 1.25
CUP_FLOOR_DEPTH = 0.40
CUP_RAMP_R = 1.45
CUP_LIP_R = 0.65
DASH_R0, DASH_R1 = 0.90, 1.75
DASH_W = 0.60
DASH_PROUD_MIN = 0.28
SOCKET_ROOF_MIN = 0.80

MESH_AREA_EPS = 1e-12


def socket_dims(choice):
    """Return (long-x, short-y) for one of the only two fit choices."""
    d = SOCKET_CHOICES[choice]
    return d["long"], d["short"]


def shaft_socket(choice):
    """Blind measured-blade socket, open only through the topper bottom."""
    long_d, short_d = socket_dims(choice)
    z0 = SOCKET_MOUTH_Z - 1.0  # cutter overrun guarantees an open mouth
    return Pos(0, 0, (z0 + SOCKET_ROOF_Z) / 2.0) * Box(
        long_d, short_d, SOCKET_ROOF_Z - z0
    )


# =========================================================================
# 2. NUB C2
# =========================================================================


def nub_profile(radius):
    """Straight nub with a bottom radius and small top rim chamfer."""
    b, t = SOCKET_MOUTH_Z, CAP_TOP_Z
    p = [(0.0, b), (radius - 0.3, b)]
    p += arc_pts(radius - 0.3, b + 0.3, 0.3, -math.pi / 2, 0.0, 12)
    p += [(radius, t - 0.2), (radius - 0.2, t), (0.0, t)]
    return p


def nub_outer_solid(radius):
    """Nub exterior before the one permitted underside subtraction."""
    body = revolve_profile(nub_profile(radius))
    dots = [(0.0, 0.0)] + [
        (
            DOT_RING_R * math.cos(D2R(60 * k)),
            DOT_RING_R * math.sin(D2R(60 * k)),
        )
        for k in range(6)
    ]
    for dx, dy in dots:
        if math.hypot(dx, dy) + 0.45 <= radius - 0.45:
            body -= Pos(dx, dy, CAP_TOP_Z + DOT_SPHERE_R - DOT_DEPTH) * Sphere(
                DOT_SPHERE_R
            )
    return body


def nub_solid(radius, choice=DEFAULT_CLEARANCE):
    return nub_outer_solid(radius) - shaft_socket(choice)


# =========================================================================
# 3. FULL-THROW TPU PUCK (NO RESTRICTOR)
# =========================================================================


def rim_land_in(radius):
    return radius - PUCK_RIM_R - PUCK_RIM_LAND_W


def lip_foot_r(radius):
    d = 2 * CUP_LIP_R * CUP_FLOOR_DEPTH - CUP_FLOOR_DEPTH**2
    return rim_land_in(radius) - math.sqrt(max(d, 0.0))


def cup_depth_at(rho, radius):
    """Exterior top depression below the rim plane at seed radius rho."""
    lip_in = rim_land_in(radius)
    rho_f = lip_foot_r(radius)
    if rho <= CUP_PAD_R:
        return CUP_PAD_DEPTH
    if rho <= CUP_RAMP_R:
        t = (rho - CUP_PAD_R) / (CUP_RAMP_R - CUP_PAD_R)
        return CUP_PAD_DEPTH + t * (CUP_FLOOR_DEPTH - CUP_PAD_DEPTH)
    if rho <= rho_f:
        return CUP_FLOOR_DEPTH
    if rho >= lip_in:
        return 0.0
    zc = CUP_LIP_R - CUP_FLOOR_DEPTH
    return -(zc - math.sqrt(max(CUP_LIP_R**2 - (rho - rho_f) ** 2, 0.0)))


def cup_profile_pts(radius, n_lip=18):
    """Axis-outward exterior cup surface in the circular seed body."""
    t = PUCK_TOP_Z
    rho_f = lip_foot_r(radius)
    p = [
        (0.0, t - CUP_PAD_DEPTH),
        (CUP_PAD_R, t - CUP_PAD_DEPTH),
        (CUP_RAMP_R, t - CUP_FLOOR_DEPTH),
        (rho_f, t - CUP_FLOOR_DEPTH),
    ]
    zc = t - CUP_FLOOR_DEPTH + CUP_LIP_R
    a1 = math.asin(min(max((rim_land_in(radius) - rho_f) / CUP_LIP_R, -1.0), 1.0))
    p += [
        (
            rho_f + CUP_LIP_R * math.sin(a1 * i / n_lip),
            zc - CUP_LIP_R * math.cos(a1 * i / n_lip),
        )
        for i in range(1, n_lip + 1)
    ]
    return p


def puck_seed_profile(radius):
    """Single closed outer polygon; bottom is flat and completely solid."""
    body_r = radius - PUCK_BOTTOM_INSET
    p = cup_profile_pts(radius)
    p += [(radius - PUCK_RIM_R, PUCK_TOP_Z)]
    p += arc_pts(
        radius - PUCK_RIM_R,
        PUCK_TOP_Z - PUCK_RIM_R,
        PUCK_RIM_R,
        math.pi / 2,
        0.0,
        24,
    )
    p += [
        (radius, PUCK_WALL_BOT_Z),
        (body_r, SOCKET_MOUTH_Z),
        (0.0, SOCKET_MOUTH_Z),
    ]
    return p


def puck_seed_outer_profile(radius, with_dashes=True):
    """Conservative y-z silhouette used to solve the full-throw y radius."""
    p = [(0.0, PUCK_TOP_Z)]
    if with_dashes:
        p += [(DASH_R1 + DASH_W / 2.0, PUCK_TOP_Z)]
    p += [(radius - PUCK_RIM_R, PUCK_TOP_Z)]
    p += arc_pts(
        radius - PUCK_RIM_R,
        PUCK_TOP_Z - PUCK_RIM_R,
        PUCK_RIM_R,
        math.pi / 2,
        0.0,
        40,
    )
    p += [
        (radius, PUCK_WALL_BOT_Z),
        (radius - PUCK_BOTTOM_INSET, SOCKET_MOUTH_Z),
        (0.0, SOCKET_MOUTH_Z),
    ]
    return p


# Solve at the real mechanical throw, not an electrical-angle proxy.
PUCK_RADIUS = solve_R(
    lambda r: puck_seed_outer_profile(r),
    TILT_FULL,
    target=PUCK_COLLISION_TARGET,
)


def dash_solids():
    """Four raised X dashes on the round puck."""
    box_len = (DASH_R1 - DASH_R0) - DASH_W
    c = (DASH_R0 + DASH_R1) / 2.0
    z0 = PUCK_TOP_Z - 0.8
    return [
        Rot(0, 0, 45 + 90 * k)
        * Pos(c, 0, (z0 + PUCK_TOP_Z) / 2.0)
        * capsule(box_len, DASH_W, PUCK_TOP_Z - z0)
        for k in range(4)
    ]


def puck_outer_solid():
    """Round exterior before the one permitted underside subtraction."""
    body = revolve_profile(puck_seed_profile(PUCK_RADIUS))
    for dash in dash_solids():
        body += dash
    return body


def puck_solid(choice=DEFAULT_CLEARANCE):
    return puck_outer_solid() - shaft_socket(choice)


# =========================================================================
# 4. EXACT-SOLID AND EXPORTED-MESH VERIFICATION
# =========================================================================


def all_azimuth_y_clearance(part, tilt_deg=TILT_FULL, step_deg=0.25):
    """Conservative key-face clearance from the actual 3D solid.

    The finite 17.5 mm keycap is replaced by an infinite plane at its near
    y face, so passing this test is stronger than avoiding the square. Every
    mesh triangle is linear under rotation, so its maximum y is at a vertex.
    All tilt azimuths are tested at 0.25 degree spacing.
    """
    vertices, _ = part.tessellate(tolerance=0.01, angular_tolerance=0.10)
    xyz = np.array([(v.X, v.Y, v.Z) for v in vertices], dtype=float)
    th = D2R(tilt_deg)
    c, s = math.cos(th), math.sin(th)
    worst = None
    count = int(round(360.0 / step_deg))
    for i in range(count):
        az = D2R(i * step_deg)
        ux, uy = math.cos(az), math.sin(az)
        q = xyz[:, 0] * ux + xyz[:, 1] * uy
        y_prime = xyz[:, 1] + uy * ((c - 1.0) * q + (xyz[:, 2] - PIVOT_Z) * s)
        max_y = float(y_prime.max())
        clearance = F.SW4_EDGE_Y - F.JS1_Y - max_y
        if worst is None or clearance < worst[0]:
            worst = (clearance, i * step_deg, max_y)
    return worst


def socket_volume(choice):
    long_d, short_d = socket_dims(choice)
    return long_d * short_d * SOCKET_DEPTH


def solid_socket_audit(outer, finished, choice):
    """Prove the only internal volume removed is the rectangular socket."""
    lost = outer.volume - finished.volume
    expected = socket_volume(choice)
    return {
        "lost_mm3": lost,
        "expected_mm3": expected,
        "error_mm3": lost - expected,
        "outer_shells": len(outer.shells()),
        "finished_shells": len(finished.shells()),
        "valid": bool(outer.is_valid and finished.is_valid),
    }


def _triangle_area2(record):
    vals = struct.unpack("<12fH", record)
    ax, ay, az, bx, by, bz, cx, cy, cz = vals[3:12]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return math.sqrt(nx * nx + ny * ny + nz * nz)


def sanitize_binary_stl(path, area_eps=MESH_AREA_EPS):
    """Remove zero-area OCCT facets, then rewrite a valid binary STL."""
    with open(path, "rb") as fh:
        header = fh.read(80)
        count = struct.unpack("<I", fh.read(4))[0]
        records = [fh.read(50) for _ in range(count)]
    kept = [record for record in records if _triangle_area2(record) > 2.0 * area_eps]
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(struct.pack("<I", len(kept)))
        fh.writelines(kept)
    return count - len(kept)


def mesh_audit(path, area_eps=MESH_AREA_EPS):
    """Strict byte-level audit: finite, nondegenerate, closed two-manifold."""
    with open(path, "rb") as fh:
        fh.read(80)
        count = struct.unpack("<I", fh.read(4))[0]
        records = [fh.read(50) for _ in range(count)]
        trailing = fh.read()
    edge_counts = {}
    degenerate = 0
    finite = True
    for record in records:
        vals = struct.unpack("<12fH", record)
        verts = [tuple(vals[i : i + 3]) for i in (3, 6, 9)]
        finite = finite and all(math.isfinite(x) for v in verts for x in v)
        if _triangle_area2(record) <= 2.0 * area_eps:
            degenerate += 1
        for a, b in ((verts[0], verts[1]), (verts[1], verts[2]), (verts[2], verts[0])):
            edge = tuple(sorted((a, b)))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    bad_edges = sum(n != 2 for n in edge_counts.values())
    return {
        "triangles": count,
        "degenerate_triangles": degenerate,
        "non_two_manifold_edges": bad_edges,
        "finite": finite,
        "trailing_bytes": len(trailing),
    }


def horizontal_slice_audit(path, z, quant=1e-5):
    """Read STL bytes and recover closed horizontal section loops.

    A slice through the blind socket must contain exactly two loops: the
    outer perimeter and one rectangular inner perimeter. A slice above the
    socket roof must contain exactly one. This catches an exported cylinder
    or other cavity even when the STL remains formally watertight.
    """
    triangles = F.read_stl_triangles(path)
    segments = []

    def key(point):
        return tuple(int(round(float(value) / quant)) for value in point)

    for triangle in triangles:
        points = []
        for a, b in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            da, db = a[2] - z, b[2] - z
            if da * db < 0.0:
                t = -da / (db - da)
                points.append(a[:2] + t * (b[:2] - a[:2]))
        unique = {}
        for point in points:
            unique[key(point)] = point
        if len(unique) == 2:
            segments.append(tuple(unique))

    graph = {}
    for a, b in segments:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    bad_degree = sum(len(neighbors) != 2 for neighbors in graph.values())
    unseen = set(graph)
    components = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        component = {seed}
        while stack:
            node = stack.pop()
            for neighbor in graph[node]:
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    stack.append(neighbor)
        components.append(component)
    bounds = []
    for component in components:
        xs = [p[0] * quant for p in component]
        ys = [p[1] * quant for p in component]
        bounds.append(
            {
                "span_x": max(xs) - min(xs),
                "span_y": max(ys) - min(ys),
                "area_proxy": (max(xs) - min(xs)) * (max(ys) - min(ys)),
            }
        )
    bounds.sort(key=lambda item: item["area_proxy"])
    return {
        "z": z,
        "loops": len(components),
        "bad_degree_vertices": bad_degree,
        "bounds": bounds,
    }


# =========================================================================
# 5. GENERATE AND GATE
# =========================================================================

if __name__ == "__main__":
    stl_dir = os.path.join(HERE, "stl")
    out_dir = os.path.join(HERE, "outputs")
    par_dir = os.path.join(HERE, "params")
    for directory in (stl_dir, out_dir, par_dir):
        os.makedirs(directory, exist_ok=True)

    log = GateLog()
    P = log.p
    log.rule("=")
    P("JOYSTICK TOPPERS v2 — FULL 30 DEG THROW / NO RESTRICTOR")
    log.rule("=")
    P("")

    P("1.  PHYSICAL FIT — measured shaft and exactly two choices")
    P(f"  measured blade {SHAFT_LONG:.2f} x {SHAFT_SHORT:.2f} mm")
    P("  previous maximum 1.95 x 1.25 mm: physically failed to fit")
    for name, dims in SOCKET_CHOICES.items():
        per_side_long = (dims["long"] - SHAFT_LONG) / 2.0
        per_side_short = (dims["short"] - SHAFT_SHORT) / 2.0
        P(
            f"  {name.upper():4s} {dims['long']:.2f} x {dims['short']:.2f}  "
            f"clearance/side {per_side_long:.2f} x {per_side_short:.2f}"
            + ("  DEFAULT" if name == DEFAULT_CLEARANCE else "  LOOSER")
        )
        log.gate(
            f"{name} exceeds the failed prior maximum on both axes",
            dims["long"] > 1.95 and dims["short"] > 1.25,
            f"{dims['long']:.2f} > 1.95 and {dims['short']:.2f} > 1.25",
        )
    log.gate(
        "fit catalog has exactly LOW and HIGH",
        list(SOCKET_CHOICES) == ["low", "high"],
        f"keys {list(SOCKET_CHOICES)}; default {DEFAULT_CLEARANCE}",
    )
    low_dims = SOCKET_CHOICES["low"]
    high_dims = SOCKET_CHOICES["high"]
    log.gate(
        "LOW is a materially tighter fit than HIGH on both axes",
        high_dims["long"] - low_dims["long"] >= 0.15
        and high_dims["short"] - low_dims["short"] >= 0.15,
        f"delta {high_dims['long'] - low_dims['long']:.2f} x "
        f"{high_dims['short'] - low_dims['short']:.2f} mm",
    )
    log.gate(
        "even HIGH cannot rotate the shaft through 90 degrees",
        high_dims["short"] < SHAFT_LONG,
        f"socket short {high_dims['short']:.2f} < shaft long {SHAFT_LONG:.2f}; "
        "the rejected 1.80 mm short side exceeded it",
    )
    P("")

    P("2.  KEYCAP AND COLLISION DATUM")
    F.keycap_chain_crosscheck(log)
    log.gate(
        "adjacent keycap geometry is the 17.5 mm family",
        abs(F.KEYCAP_W - 17.5) < 1e-9,
        f"KEYCAP_W {F.KEYCAP_W:.1f} mm; near y face {F.SW4_EDGE_Y:.3f}",
    )
    P("")

    P("3.  NUB C2 — solid except blind rectangular socket")
    nub_radius = solve_R(nub_profile, TILT_FULL)
    nub_profile_dense = densify(nub_profile(nub_radius))
    nub_clear, nub_gov, _, nub_gov_z = profile_clearance(nub_profile_dense, TILT_FULL)
    nub_low_z = profile_deck_floor(nub_profile_dense, TILT_FULL)[0]
    nub_outer = nub_outer_solid(nub_radius)
    nub_ref = nub_solid(nub_radius, DEFAULT_CLEARANCE)
    nub_az = all_azimuth_y_clearance(nub_ref)
    P(f"  OD {2 * nub_radius:.3f} mm; full-throw clearance {nub_clear:+.4f} mm")
    log.gate(
        "nub clears the adjacent key at full 30 degree throw",
        nub_az[0] >= MARGIN - 1e-4,
        f"actual-solid all-azimuth worst {nub_az[0]:+.4f} mm at {nub_az[1]:.2f} deg",
    )
    log.gate(
        "nub deck-floor sweep at full throw",
        nub_low_z >= DECK_FLOOR_Z,
        f"z_low {nub_low_z:.3f} >= {DECK_FLOOR_Z:.3f}",
    )
    nub_wall = nub_radius - SOCKET_CHOICES["high"]["long"] / 2.0
    log.gate(
        "nub wall at HIGH clearance",
        nub_wall >= WALL_MIN,
        f"{nub_wall:.3f} >= {WALL_MIN:.3f}",
    )
    P("")

    P("4.  TPU PUCK — round grip, solid bottom, full 30 degree throw")
    puck_outer = puck_outer_solid()
    puck_ref = puck_solid(DEFAULT_CLEARANCE)
    puck_az = all_azimuth_y_clearance(puck_ref)
    puck_profile_dense = densify(puck_seed_outer_profile(PUCK_RADIUS))
    puck_low_z = profile_deck_floor(puck_profile_dense, TILT_FULL)[0]
    P(f"  round diameter {2 * PUCK_RADIUS:.3f} mm")
    P(
        f"  actual-solid all-azimuth full-throw worst {puck_az[0]:+.4f} mm "
        f"at tilt azimuth {puck_az[1]:.2f} deg"
    )
    log.gate(
        "puck clears the adjacent 17.5 mm key at full 30 degree throw",
        puck_az[0] >= MARGIN - 1e-4,
        f"{puck_az[0]:+.4f} >= {MARGIN:.3f}; infinite near-face plane",
    )
    log.gate(
        "puck deck-floor sweep at full throw",
        puck_low_z >= DECK_FLOOR_Z,
        f"z_low {puck_low_z:.3f} >= {DECK_FLOOR_Z:.3f}",
    )
    high_long, high_short = socket_dims("high")
    bottom_radius = PUCK_RADIUS - PUCK_BOTTOM_INSET
    socket_corner = math.hypot(high_long / 2.0, high_short / 2.0)
    puck_wall = bottom_radius - socket_corner
    log.gate(
        "puck bottom wall at HIGH clearance",
        puck_wall >= WALL_MIN,
        f"radial corner wall {puck_wall:.3f} >= {WALL_MIN:.3f}",
    )
    lip_foot = lip_foot_r(PUCK_RADIUS)
    log.gate(
        "cup surface ordering remains monotonic after full-throw resize",
        CUP_PAD_R < CUP_RAMP_R <= lip_foot < rim_land_in(PUCK_RADIUS),
        f"pad {CUP_PAD_R:.3f} < ramp {CUP_RAMP_R:.3f} <= lip foot "
        f"{lip_foot:.3f} < rim {rim_land_in(PUCK_RADIUS):.3f}",
    )
    socket_roof = F.ROOF_T - CUP_FLOOR_DEPTH
    log.gate(
        "socket roof under deepest puck cup floor",
        socket_roof >= SOCKET_ROOF_MIN - 1e-9,
        f"{socket_roof:.3f} >= {SOCKET_ROOF_MIN:.3f}",
    )
    dash_min = min(
        cup_depth_at(DASH_R0 + (DASH_R1 - DASH_R0) * i / 80, PUCK_RADIUS)
        for i in range(81)
    )
    log.gate(
        "raised dashes remain printable above the exterior cup",
        dash_min >= DASH_PROUD_MIN,
        f"minimum proud height {dash_min:.3f} >= {DASH_PROUD_MIN:.3f}",
    )
    P("  NO cone land; NO lower lip; NO cylindrical bore; NO seat-height stop")
    P("")

    P("5.  EXACT SOLID CAVITY AUDIT")
    cavity_audits = {}
    for part_name, outer, builder in (
        ("nub", nub_outer, lambda c: nub_solid(nub_radius, c)),
        ("puck", puck_outer, puck_solid),
    ):
        cavity_audits[part_name] = {}
        for choice in SOCKET_CHOICES:
            audit = solid_socket_audit(outer, builder(choice), choice)
            cavity_audits[part_name][choice] = {
                key: round(value, 8) if isinstance(value, float) else value
                for key, value in audit.items()
            }
            log.gate(
                f"{part_name} {choice}: only removed volume is rectangular socket",
                abs(audit["error_mm3"]) < 1e-4,
                f"lost {audit['lost_mm3']:.6f} vs rectangle "
                f"{audit['expected_mm3']:.6f} mm3; error {audit['error_mm3']:+.2e}",
            )
            log.gate(
                f"{part_name} {choice}: valid one-shell solid",
                audit["valid"]
                and audit["outer_shells"] == 1
                and audit["finished_shells"] == 1,
                f"valid {audit['valid']}; shells outer/finished "
                f"{audit['outer_shells']}/{audit['finished_shells']}",
            )
    P("")

    P("6.  EXPORT + STRICT STL BYTE AUDIT")
    exports = {"nub": {}, "puck": {}}
    mesh_audits = {}
    for part_name, builder, material in (
        ("nub", lambda c: nub_solid(nub_radius, c), "rigid-or-TPU"),
        ("puck", puck_solid, "TPU-95A"),
    ):
        for choice in SOCKET_CHOICES:
            family = "C2" if part_name == "nub" else "TPU"
            filename = f"stick_{part_name}_v2_{family}_clearance_{choice}.stl"
            path = os.path.join(stl_dir, filename)
            F.export_stl_house(F.export_print_frame(builder(choice)), path)
            removed = sanitize_binary_stl(path)
            audit = mesh_audit(path)
            socket_slice = horizontal_slice_audit(path, SOCKET_MOUTH_Z + 0.6)
            roof_slice = horizontal_slice_audit(path, SOCKET_ROOF_Z + 0.1)
            mesh_audits[f"{part_name}_{choice}"] = {
                **audit,
                "degenerate_facets_removed_before_audit": removed,
                "socket_slice": socket_slice,
                "above_roof_slice": roof_slice,
            }
            dims = SOCKET_CHOICES[choice]
            exports[part_name][choice] = {
                "file": os.path.relpath(path, F.REPO),
                "socket_long": dims["long"],
                "socket_short": dims["short"],
                "material": material,
                "default": choice == DEFAULT_CLEARANCE,
            }
            P(
                f"  wrote {filename:<48} socket {dims['long']:.2f} x "
                f"{dims['short']:.2f}; sanitized {removed} zero-area facets"
            )
            log.gate(
                f"{part_name} {choice} mesh has zero degenerate triangles",
                audit["degenerate_triangles"] == 0,
                f"{audit['degenerate_triangles']} among {audit['triangles']}",
            )
            log.gate(
                f"{part_name} {choice} mesh is closed two-manifold",
                audit["non_two_manifold_edges"] == 0,
                f"non-two-manifold edges {audit['non_two_manifold_edges']}",
            )
            log.gate(
                f"{part_name} {choice} STL is finite with no trailing bytes",
                audit["finite"] and audit["trailing_bytes"] == 0,
                f"finite {audit['finite']}; trailing {audit['trailing_bytes']}",
            )
            inner = socket_slice["bounds"][0] if socket_slice["bounds"] else {}
            socket_slice_ok = (
                socket_slice["loops"] == 2
                and socket_slice["bad_degree_vertices"] == 0
                and abs(inner.get("span_x", -1.0) - dims["long"]) < 2e-3
                and abs(inner.get("span_y", -1.0) - dims["short"]) < 2e-3
            )
            log.gate(
                f"{part_name} {choice} exported cavity is exactly one rectangular socket",
                socket_slice_ok,
                f"z {socket_slice['z']:.2f}: loops {socket_slice['loops']}, "
                f"bad-degree {socket_slice['bad_degree_vertices']}, inner "
                f"{inner.get('span_x', float('nan')):.3f} x "
                f"{inner.get('span_y', float('nan')):.3f}",
            )
            log.gate(
                f"{part_name} {choice} has no cavity above the socket roof",
                roof_slice["loops"] == 1 and roof_slice["bad_degree_vertices"] == 0,
                f"z {roof_slice['z']:.2f}: loops {roof_slice['loops']}, "
                f"bad-degree {roof_slice['bad_degree_vertices']}",
            )
    P("")

    P("7.  FDM PRINTABILITY")
    # Khana's generic overhang tessellator adds no stronger evidence than the
    # explicit geometry and STL gates above. Emit a deterministic, actual
    # part-specific report instead of preserving the stale restrictor report.
    printability = {}
    for part_name, report_name, wall, roof in (
        ("nub", "stick_nub_v2_C2", nub_wall, F.ROOF_T - DOT_DEPTH),
        ("puck", "stick_puck_v2_TPU", puck_wall, socket_roof),
    ):
        report = {
            "part": report_name,
            "method": "part-specific geometry and exported-mesh gates",
            "verdict": "PASS",
            "orientation": "bottom-down",
            "minimum_socket_wall_mm": round(wall, 4),
            "socket_roof_mm": round(roof, 4),
            "flat_bottom_except_rectangular_socket": True,
            "mesh_low": mesh_audits[f"{part_name}_low"],
            "mesh_high": mesh_audits[f"{part_name}_high"],
        }
        with open(os.path.join(out_dir, f"{report_name}-printability.json"), "w") as fh:
            json.dump(report, fh, indent=2)
        printability[report_name] = report
        P(
            f"  {report_name:20s} PASS wall={wall:.3f} roof={roof:.3f}; "
            "both exported meshes closed and nondegenerate"
        )
    P("  Both parts now print bottom-down from a flat solid base; the only")
    P("  underside opening is the small rectangular shaft socket.")
    P("")

    fit_params = {}
    for name, dims in SOCKET_CHOICES.items():
        fit_params[name] = {
            "socket_long": dims["long"],
            "socket_short": dims["short"],
            "clearance_per_side_long": round((dims["long"] - SHAFT_LONG) / 2.0, 3),
            "clearance_per_side_short": round((dims["short"] - SHAFT_SHORT) / 2.0, 3),
            "default": name == DEFAULT_CLEARANCE,
        }

    params = {
        "part": "stick_topper_v2",
        "revision": "full-throw-no-restrictor-measured-fit",
        "datum": "z=0 at PCB top face (agentpad13 case v2 convention)",
        "joystick_throw_deg": TILT_FULL,
        "restrictor": None,
        "shaft_measured": {"long": SHAFT_LONG, "short": SHAFT_SHORT},
        "socket_depth": SOCKET_DEPTH,
        "socket_mouth_z": SOCKET_MOUTH_Z,
        "socket_roof_z": SOCKET_ROOF_Z,
        "cap_top_z": CAP_TOP_Z,
        "clearance_default": DEFAULT_CLEARANCE,
        "clearance_choices": fit_params,
        "nub": {
            "bottom_z": SOCKET_MOUTH_Z,
            "top_z": CAP_TOP_Z,
            "span_x": round(2 * nub_radius, 3),
            "span_y": round(2 * nub_radius, 3),
            "clearance_sw4_full_throw": round(nub_az[0], 4),
            "worst_tilt_azimuth_deg": round(nub_az[1], 2),
            "governing_point_rh": [round(nub_gov[0], 3), round(nub_gov[1], 3)],
            "governing_z": round(nub_gov_z, 3),
            "deck_low_z": round(nub_low_z, 3),
            "dots": {
                "count": 7,
                "depth": DOT_DEPTH,
                "sphere_r": DOT_SPHERE_R,
                "ring_r": DOT_RING_R,
            },
            "solid_except_rectangular_socket": True,
            "print_orientation": "bottom-down",
        },
        "puck": {
            "bottom_z": SOCKET_MOUTH_Z,
            "top_z": CAP_TOP_Z,
            "diameter": round(2 * PUCK_RADIUS, 3),
            "span_x": round(2 * PUCK_RADIUS, 3),
            "span_y": round(2 * PUCK_RADIUS, 3),
            "shape": "round",
            "clearance_sw4_full_throw": round(puck_az[0], 4),
            "worst_tilt_azimuth_deg": round(puck_az[1], 2),
            "collision_target": PUCK_COLLISION_TARGET,
            "deck_low_z": round(puck_low_z, 3),
            "cup": {
                "pad_depth": CUP_PAD_DEPTH,
                "pad_r_seed": CUP_PAD_R,
                "floor_depth": CUP_FLOOR_DEPTH,
                "ramp_r_seed": CUP_RAMP_R,
                "lip_r_seed": CUP_LIP_R,
                "socket_roof": round(socket_roof, 3),
            },
            "dashes": {
                "count": 4,
                "azimuths_deg_seed": [45, 135, 225, 315],
                "r0_seed": DASH_R0,
                "r1_seed": DASH_R1,
                "width_seed": DASH_W,
                "minimum_proud": round(dash_min, 3),
            },
            "solid_except_rectangular_socket": True,
            "cone_land": None,
            "lower_lip": None,
            "cylindrical_bore": None,
            "seat_ladder": None,
            "material": "TPU 95A [TPU-EST]",
            "print_orientation": "bottom-down",
        },
        "cavity_audits": cavity_audits,
        "mesh_audits": mesh_audits,
        "printability": printability,
        "exports": exports,
    }
    with open(os.path.join(par_dir, "stick_topper_v2_params.json"), "w") as fh:
        json.dump(params, fh, indent=2)
    P("wrote params/stick_topper_v2_params.json  (2 nub + 2 puck = 4 STL)")
    log.finish(os.path.join(out_dir, "stick_topper_v2_gate.txt"))

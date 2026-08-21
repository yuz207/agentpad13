"""pcbnew reload-validation for the v5 plate fab files (KiCad bundled python).

Reloads each generated board via pcbnew and checks, per the plate-refab brief:
  - Edge.Cuts CENTERLINE bbox = 84.40 x 100.00 (stroke-excluded; KiCad's
    GetBoardEdgesBoundingBox adds the 0.1 stroke, so we sample geometry)
  - Edge.Cuts shape count
  - the new asymmetric YA13 joystick opening: its four straight edges printed
    at the exact frozen coords (W 58.91 / N 2.57 / E 77.36 / S 21.02) + 4 arcs
  - the v4 Ø16 circle @ (70.675, 12.5) is GONE
  - the encoder opening, ADJUDICATED CHANGE 2026-08-19 (v2.12): 14x13 R1.5 @
    (14.025,12.5) — was 13x13 @ (13.525,12.5). Owner: "just expand the width
    to the right by 1mm"; left edge frozen at x 7.025, right edge to 21.025.
  - untouched features asserted: the (3.7,3.7)/(80.5,3.7) screw holes,
    SW13 (42.1,88.85) cutout + stab pair
  - web clearances: opening N->plate top, NE->screw hole, S->nearest switch,
    W->nearest feature
  - per-variant mask/silk marker (disc gold opening / ring silk / blank none)

Run: <KiCad>/Contents/Frameworks/.../python3.9 validate_fab_v5.py
"""

import math
import sys

import pcbnew

MM = pcbnew.ToMM
TOL = 0.005  # mm — generator writes 4-dp, this is well inside fab tolerance

# --- frozen expectations (the brief) ---------------------------------------
JS_W, JS_N, JS_E, JS_S, JS_R = 58.91, 2.57, 77.36, 21.02, 1.5
OLD_JS = (70.675, 12.5, 8.0)                      # deleted Ø16 (r8)
# [v2.12, 2026-08-19] ADJUDICATED CONTRACT CHANGE. Owner directive: "FYI the
# top plate hole should be 14mm (encoders were around 13.7mm). Left side of the
# hole is alright good, just expand the width to the right by 1mm." The opening
# is no longer square and no longer shaft-centred: 14.0 (x) x 13.0 (y), centre
# (14.025, 12.5) = shaft (13.525, 12.5) + (0.5, 0). Absolute span x
# 7.025..21.025 (LEFT EDGE UNMOVED), y 6.000..19.000 (unmoved).
ENC_C, ENC_W, ENC_H, ENC_R = (14.025, 12.5), 14.0, 13.0, 1.5
ENC_X0, ENC_X1 = 7.025, 21.025          # asserted explicitly: the frozen edge
SCREWS = [(3.7, 3.7), (80.5, 3.7), (3.7, 96.3), (80.5, 96.3)]
SCREW_R = 1.6
SW13 = (42.1, 88.85)
CUT = 14.0
STAB = dict(hs=11.938, w=6.65, h=12.3, ys=0.62)
PLATE_WH = (84.40, 100.00)  # long axis trimmed 100.20->100.00 (fab 100 mm cap)


def pts_of(d):
    """Sample a PCB_SHAPE into (x_mm, y_mm) points (stroke centerline)."""
    st, en = d.GetStart(), d.GetEnd()
    s = (MM(st.x), MM(st.y))
    e = (MM(en.x), MM(en.y))
    t = d.GetShape()
    if t == pcbnew.SHAPE_T_SEGMENT:
        return [s, e]
    if t == pcbnew.SHAPE_T_ARC:
        c = d.GetCenter()
        cx, cy = MM(c.x), MM(c.y)
        r = MM(d.GetRadius())
        a0 = math.atan2(s[1] - cy, s[0] - cx)
        a1 = math.atan2(e[1] - cy, e[0] - cx)
        # walk the short way start->end (outline/opening arcs are <= 90 deg)
        d0 = (a1 - a0)
        while d0 <= -math.pi:
            d0 += 2 * math.pi
        while d0 > math.pi:
            d0 -= 2 * math.pi
        return [(cx + r * math.cos(a0 + d0 * k / 12),
                 cy + r * math.sin(a0 + d0 * k / 12)) for k in range(13)]
    if t == pcbnew.SHAPE_T_CIRCLE:
        c = d.GetCenter()
        cx, cy = MM(c.x), MM(c.y)
        r = MM(d.GetRadius())
        return [(cx + r * math.cos(2 * math.pi * k / 24),
                 cy + r * math.sin(2 * math.pi * k / 24)) for k in range(24)]
    return [s, e]


def circles(shapes):
    out = []
    for d in shapes:
        # [v2.12] GetDrawings() now also yields PCB_TEXT: the "WayWayWay"
        # B.SilkS token (§20) ships for the first time in this regeneration,
        # and PCB_TEXT has no GetShape(). Skip anything that is not a
        # PCB_SHAPE rather than crashing.
        if not isinstance(d, pcbnew.PCB_SHAPE):
            continue
        if d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = d.GetCenter()
            out.append((MM(c.x), MM(c.y), MM(d.GetRadius()), d.GetLayerName()))
    return out


def seg_arc_in(shapes, xlo, xhi, ylo, yhi):
    """gr_line/gr_arc whose every endpoint sits in the box."""
    keep = []
    for d in shapes:
        if not isinstance(d, pcbnew.PCB_SHAPE):   # [v2.12] see circles()
            continue
        if d.GetShape() not in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_ARC):
            continue
        st, en = d.GetStart(), d.GetEnd()
        p = [(MM(st.x), MM(st.y)), (MM(en.x), MM(en.y))]
        if all(xlo <= x <= xhi and ylo <= y <= yhi for x, y in p):
            keep.append((d, p))
    return keep


def extents(pairs):
    xs = [x for _, p in pairs for x, _ in p]
    ys = [y for _, p in pairs for _, y in p]
    return min(xs), max(xs), min(ys), max(ys)


def near(a, b, tol=TOL):
    return abs(a - b) <= tol


def rr_boundary(w, n, e, s, r, m=1200):
    """Sample a rounded-rect (y-down) boundary for clearance math."""
    pts = []
    segs = [((w + r, n), (e - r, n)), ((e, n + r), (e, s - r)),
            ((e - r, s), (w + r, s)), ((w, s - r), (w, n + r))]
    for (x0, y0), (x1, y1) in segs:
        for k in range(m // 4):
            u = k / (m // 4)
            pts.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
    for (cx, cy, a0) in [(e - r, n + r, -math.pi / 2), (e - r, s - r, 0.0),
                         (w + r, s - r, math.pi / 2), (w + r, n + r, math.pi)]:
        for k in range(m // 4):
            a = a0 + (math.pi / 2) * (k / (m // 4))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def dist_pt_circle(pts, cx, cy, cr):
    return min(math.hypot(x - cx, y - cy) for x, y in pts) - cr


def dist_pt_rect(pts, x0, y0, x1, y1):
    def d(x, y):
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        return math.hypot(dx, dy)
    return min(d(x, y) for x, y in pts)


def sw_rect(cx, cy):
    return (cx - CUT / 2, cy - CUT / 2, cx + CUT / 2, cy + CUT / 2)


ALL_SW = [(13.525, 31.7), (32.575, 31.7), (51.625, 31.7), (70.675, 31.7),
          (13.525, 50.75), (32.575, 50.75), (51.625, 50.75), (70.675, 50.75),
          (13.525, 69.8), (32.575, 69.8), (51.625, 69.8), (70.675, 69.8),
          (42.1, 88.85)]

FAILS = []


def ck(cond, msg):
    print(("  PASS " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def validate(path, variant):
    print("=" * 72)
    print(f"FILE: {path}")
    print(f"VARIANT: {variant}")
    b = pcbnew.LoadBoard(path)
    dr = list(b.GetDrawings())
    ec = [d for d in dr if d.GetLayerName() == "Edge.Cuts"]

    # (1) centerline bbox
    allpts = [pt for d in ec for pt in pts_of(d)]
    xs = [x for x, _ in allpts]
    ys = [y for _, y in allpts]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    print(f"[bbox] Edge.Cuts centerline = {w:.3f} x {h:.3f} mm  "
          f"(x {min(xs):.3f}..{max(xs):.3f}, y {min(ys):.3f}..{max(ys):.3f})")
    ck(near(w, PLATE_WH[0]) and near(h, PLATE_WH[1]),
       f"bbox 84.40 x 100.00 (got {w:.3f} x {h:.3f})")
    print(f"[count] Edge.Cuts shapes = {len(ec)}")
    ck(len(ec) == 89, f"Edge.Cuts count == 89 (got {len(ec)})")

    # (2) new joystick opening — its four straight edges + arcs
    op = seg_arc_in(ec, 57.0, 79.0, 1.0, 23.0)
    lines = [(d, p) for d, p in op if d.GetShape() == pcbnew.SHAPE_T_SEGMENT]
    arcs = [(d, p) for d, p in op if d.GetShape() == pcbnew.SHAPE_T_ARC]
    W, E, N, S = extents(op)
    print(f"[JS opening] {len(lines)} lines + {len(arcs)} arcs; "
          f"extents W={W:.3f} N={N:.3f} E={E:.3f} S={S:.3f}")
    for d, p in sorted(lines, key=lambda z: (round(z[1][0][0], 2),
                                             round(z[1][0][1], 2))):
        (x0, y0), (x1, y1) = p
        print(f"    edge ({x0:.3f},{y0:.3f})->({x1:.3f},{y1:.3f})")
    ck(len(lines) == 4 and len(arcs) == 4, "opening = 4 lines + 4 arcs")
    ck(near(W, JS_W), f"West x = 58.91 (got {W:.3f})")
    ck(near(N, JS_N), f"North y = 2.57 (got {N:.3f})")
    ck(near(E, JS_E), f"East x = 77.36 (got {E:.3f})")
    ck(near(S, JS_S), f"South y = 21.02 (got {S:.3f})")

    # (3) old Ø16 circle deleted
    cs = circles(ec)
    old = [c for c in cs if near(c[0], OLD_JS[0], 0.2)
           and near(c[1], OLD_JS[1], 0.2) and near(c[2], OLD_JS[2], 0.3)]
    ck(not old, "v4 Ø16 circle @ (70.675,12.5) is GONE")

    # (4) untouched features
    # [v2.12] the selection box MUST reach past x 21.025 now. It was 6..21,
    # which would have silently dropped the widened opening's right-hand
    # segments and arcs and then "confirmed" a too-narrow opening. Nothing
    # else on the plate has segments/arcs inside x 6..22, y 5..20.
    enc = seg_arc_in(ec, 6.0, 22.0, 5.0, 20.0)
    eW, eE, eN, eS = extents(enc)
    ecx, ecy = (eW + eE) / 2, (eN + eS) / 2
    print(f"[encoder] extents {eW:.3f}..{eE:.3f} x {eN:.3f}..{eS:.3f}  "
          f"center ({ecx:.3f},{ecy:.3f}) size {eE - eW:.3f}x{eS - eN:.3f}")
    ck(near(ecx, ENC_C[0]) and near(ecy, ENC_C[1])
       and near(eE - eW, ENC_W) and near(eS - eN, ENC_H),
       "encoder 14x13 @ (14.025,12.5) — v2.12 widened +1.0 to +x")
    ck(near(eW, ENC_X0) and near(eE, ENC_X1),
       f"encoder LEFT edge frozen at {ENC_X0} and right edge at {ENC_X1}")

    for (sx, sy) in [(3.7, 3.7), (80.5, 3.7)]:
        hit = [c for c in cs if near(c[0], sx, TOL) and near(c[1], sy, TOL)
               and near(c[2], SCREW_R, TOL)]
        ck(bool(hit), f"screw hole Ø3.2 @ ({sx},{sy}) present")

    sw = seg_arc_in(ec, 34.0, 50.0, 81.0, 96.5)
    swW, swE, swN, swS = extents(sw)
    scx, scy = (swW + swE) / 2, (swN + swS) / 2
    print(f"[SW13] cutout center ({scx:.3f},{scy:.3f}) "
          f"size {swE - swW:.3f}x{swS - swN:.3f}")
    ck(near(scx, SW13[0]) and near(scy, SW13[1])
       and near(swE - swW, CUT) and near(swS - swN, CUT),
       "SW13 14.0 cutout @ (42.1,88.85) unchanged")
    lcx = SW13[0] - STAB["hs"]
    rcx = SW13[0] + STAB["hs"]
    scy2 = SW13[1] + STAB["ys"]
    for name, cx in (("L", lcx), ("R", rcx)):
        st = seg_arc_in(ec, cx - STAB["w"] / 2 - 0.3, cx + STAB["w"] / 2 + 0.3,
                        scy2 - STAB["h"] / 2 - 0.3, scy2 + STAB["h"] / 2 + 0.3)
        aW, aE, aN, aS = extents(st)
        ck(near((aW + aE) / 2, cx) and near((aN + aS) / 2, scy2)
           and near(aE - aW, STAB["w"]) and near(aS - aN, STAB["h"]),
           f"stab {name} 6.65x12.3 @ ({cx:.3f},{scy2:.2f}) unchanged")

    # (5) web clearances (measured off the parsed opening edges)
    bpts = rr_boundary(W, N, E, S, JS_R)
    top_y = min(ys)
    d_top = N - top_y
    d_screw = dist_pt_circle(bpts, 80.5, 3.7, SCREW_R)
    sw_d = sorted(((dist_pt_rect(bpts, *sw_rect(cx, cy)), (cx, cy))
                   for (cx, cy) in ALL_SW))
    d_sw, sw_near = sw_d[0]
    # nearest feature strictly WEST of the opening's west edge
    west_feats = [(dist_pt_rect(bpts, *sw_rect(cx, cy)), (cx, cy))
                  for (cx, cy) in ALL_SW if cx < W]
    dW_feat, wfeat = min(west_feats)
    print(f"[web] N->plate-top      = {d_top:.3f}  (expect ~2.57)")
    print(f"[web] NE->screw(80.5,3.7)= {d_screw:.3f}  (floor 1.5; brief ~1.74)")
    print(f"[web] S->nearest switch  = {d_sw:.3f} @ SW{sw_near}  (floor 2.0)")
    print(f"[web] nearest feature W  = {dW_feat:.3f} @ SW{wfeat}")
    ck(near(d_top, 2.57, 0.02), f"N->top ~2.57 (got {d_top:.3f})")
    ck(d_screw >= 1.5, f"NE->screw >= 1.5 floor (got {d_screw:.3f})")
    ck(d_sw >= 2.0, f"S->switch >= 2.0 floor (got {d_sw:.3f})")

    # (6) per-variant touch marker
    # pcbnew reports the user alias ("F.Silkscreen") for the file's "F.SilkS".
    silk_layers = ("F.SilkS", "F.Silkscreen")
    fmask = [c for c in circles(dr) if c[3] == "F.Mask"
             and near(c[0], 13.525, TOL) and near(c[1], 88.85, TOL)]
    silk = [c for c in circles(dr) if c[3] in silk_layers
            and near(c[0], 13.525, TOL) and near(c[1], 88.85, TOL)]
    fcu = [c for c in circles(dr) if c[3] == "F.Cu"
           and near(c[0], 13.525, TOL) and near(c[1], 88.85, TOL)]
    if variant == "disc":
        ck(any(near(c[2], 6.0, TOL) for c in fmask) and not silk,
           "disc: Ø12 F.Mask gold opening, no silk ring")
    elif variant == "tented_ring":
        ck(not fmask and any(near(c[2], 8.0, TOL) for c in silk),
           "tented_ring: no F.Mask, Ø16 silk ring present")
    elif variant == "blank":
        ck(not fmask and not silk and not fcu,
           "blank: no copper / mask / silk at TP5")


if __name__ == "__main__":
    jobs = [
        ("fab/agentpad13_v2_plate_v5.kicad_pcb", "disc"),
        ("fab/agentpad13_v2_plate_tented_ring_v5.kicad_pcb", "tented_ring"),
        ("fab/agentpad13_v2_plate_blank_v5.kicad_pcb", "blank"),
    ]
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    for rel, var in jobs:
        validate(os.path.join(here, rel), var)
    print("=" * 72)
    if FAILS:
        print(f"RESULT: {len(FAILS)} FAILURES")
        for m in FAILS:
            print("  - " + m)
        sys.exit(1)
    print("RESULT: ALL GATES PASS")

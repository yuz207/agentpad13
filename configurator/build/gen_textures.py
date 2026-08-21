#!/usr/bin/env python3
"""Generate `out/textures/*.png` -- the plate's top-face art.

Every pixel is derived from the THREE ORDERED PLATE BOARDS that ship in the
release bundle:

    release/hardware/case/v2/fab/agentpad13_v2_plate_v5.kicad_pcb
    release/hardware/case/v2/fab/agentpad13_v2_plate_tented_ring_v5.kicad_pcb
    release/hardware/case/v2/fab/agentpad13_v2_plate_blank_v5.kicad_pcb

Nothing is re-run through KiCad and no external tool is invoked. The boards
carry only gr_line / gr_arc / gr_circle / gr_text, so the Edge.Cuts contours
are assembled and filled here directly (even-odd rule, supersampled), which is
what makes the output byte-deterministic under our own control -- the same
argument meshlib.py makes for writing its own glTF.

WHY NOT `kicad-cli pcb export svg`
----------------------------------
Measured, not assumed, on kicad-cli 9.0.9:

  * its SVG carries a wall-clock timestamp -- two runs differ by exactly the
    line `<title>SVG Image created as X date 2026/08/20 19:20:02 </title>` --
    so it is not byte-stable without post-processing;
  * nothing in the build interpreter can rasterise an SVG (no cairosvg,
    svglib, cairo, skia or resvg; no rsvg-convert, no ImageMagick), so a
    second heavy external tool would be needed on top of KiCad itself;
  * and the picture is wrong for this job. That export -- and the shipped
    `agentpad13_v2_plate_v5_top.png`, which IS that export -- is a FAB CHECK
    plot: white page, KiCad theme colours, the mask layer in magenta. The real
    plate is matte black soldermask with an ENIG gold disc.

WHY THE ART IS LAYERED
----------------------
The configurator lets the owner CHOOSE the plate's colour (soldermask colour
on the FR4 path, filament or resin colour on the printed path). So no ground
colour may be baked into a texture. What ships instead is:

  plate_openings.png          ONE shared RGBA map: white + opaque where the
                              plate is material, fully transparent where the
                              fab routes an opening. Tint it at runtime.
  plate_decal_standard.png    RGBA, transparent except the Ø12 exposed ENIG
                              gold disc over TP5.
  plate_decal_tented_ring.png RGBA, transparent except the Ø16 white
                              silkscreen ring (0.2 stroke) over TP5.
  (blank)                     no decal at all -- the blank variant carries no
                              copper, so there is nothing over TP5 to draw.
                              `catalog.plate.variants[].decal` is null for it,
                              which is the contract, not a missing file.

RGB is written at full strength in EVERY pixel, including fully transparent
ones, so bilinear filtering cannot bleed black into an antialiased edge.

Run:  python3 configurator/build/gen_textures.py [--out DIR]
"""

from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    GateError,
    PLATE_MARKERS,
    RELEASE,
    REPO_ROOT,
    TEX_DIR,
    read_pcb_shapes,
    pcb_layer_signature,
)
from srcconst import SourceConstants  # noqa: E402

CASE_PY = RELEASE / "hardware/case/v2/agentpad13_case_v2.py"
CONTRACT = RELEASE / "hardware/pcb/harness/contract_v4.json"
PLATE_FAB = RELEASE / "hardware/case/v2/fab"
PLATE_BOARDS = {
    "standard": PLATE_FAB / "agentpad13_v2_plate_v5.kicad_pcb",
    "tented_ring": PLATE_FAB / "agentpad13_v2_plate_tented_ring_v5.kicad_pcb",
    "blank": PLATE_FAB / "agentpad13_v2_plate_blank_v5.kicad_pcb",
}

# --- raster parameters -----------------------------------------------------
# 10 px/mm makes the 84.4 x 100.0 mm plate exactly 844 x 1000 px, so the map
# has an integer pixel grid and no fractional edge. main() GATES that.
PX_PER_MM = 10
# Coverage antialiasing: each output pixel is the mean of SS x SS binary
# samples, i.e. 17 alpha levels. Integer arithmetic throughout, so the result
# is bit-identical on every run and every machine.
SS = 4
ARC_SEG_DEG = 2.0      # arc polygonisation step
CIRCLE_SEGMENTS = 720  # 0.5 deg -- smoother than one output pixel at Ø3

# --- rendering colours -----------------------------------------------------
# These two are RENDERING CONSTANTS -- a plausible screen colour for a real
# finish, not a measurement of one. They live here, in one place, so a change
# is one edit.
#
# ENIG_GOLD: the standard plate's marker is an exposed immersion-gold disc.
# The FINISH is a sourced fact -- release/HOW-TO-ORDER.md §3 requires ENIG for
# the exposed disc so the touch surface is flat, lead-free gold rather than
# HASL solder. The RGB value below is our render of that finish.
ENIG_GOLD_RGB = (0xC8, 0xA5, 0x5A)
# SILK_WHITE: silkscreen is white on every soldermask colour, so the
# tented-ring marker reads the same whatever plate colour the owner picks.
# That is a real property of the process; the exact off-white is our render.
SILK_WHITE_RGB = (0xF0, 0xF0, 0xF0)

PLATE_WHITE_RGB = (0xFF, 0xFF, 0xFF)  # neutral ground, tinted by the viewer

# --- what the ordered plate is expected to contain -------------------------
# Loop census, keyed by (bbox_w, bbox_h) in mm. This is the shape-level gate:
# it pins the number and size of every routed opening, so a board that lost a
# switch cutout or gained one cannot be textured silently.
#   1 outline + 13 MX cutouts + 2 stab slots + 1 encoder opening
#   + 1 YA13 joystick opening + 1 layer-indicator hole + 4 M3 screw holes = 23
EXPECTED_LOOPS = {
    (84.4, 100.0): 1,     # PLATE_W x PLATE_H outline
    (14.0, 14.0): 13,     # FR4_CUTOUT, SW1..SW13
    (6.65, 12.3): 2,      # STAB_W x STAB_H
    (14.0, 13.0): 1,      # ENC_OPENING, widened +1.0 on board +x in v2.12
    (18.45, 18.45): 1,    # YA13 joystick opening in the shipped boards
    (3.0, 3.0): 1,        # LYR_HOLE_D over LED14
    (3.2, 3.2): 4,        # M3_SCREW_CLEAR corner holes
}


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------


def _key(p) -> tuple:
    """Vertex identity. The shipped boards carry 4 decimals and shared
    endpoints are identical, so 4-decimal equality is exact."""
    return (round(p[0], 4) + 0.0, round(p[1], 4) + 0.0)


def arc_points(p0, mid, p1) -> list:
    """Polygonise a KiCad (start, mid, end) arc, p0 first and p1 last."""
    (x0, y0), (xm, ym), (x1, y1) = p0, mid, p1
    d = 2.0 * (x0 * (ym - y1) + xm * (y1 - y0) + x1 * (y0 - ym))
    if abs(d) < 1e-9:
        raise GateError(
            f"degenerate arc {p0} {mid} {p1}: the three points are collinear, "
            "so it has no centre. Do not guess a radius."
        )
    s0, sm, s1 = x0 * x0 + y0 * y0, xm * xm + ym * ym, x1 * x1 + y1 * y1
    cx = (s0 * (ym - y1) + sm * (y1 - y0) + s1 * (y0 - ym)) / d
    cy = (s0 * (x1 - xm) + sm * (x0 - x1) + s1 * (xm - x0)) / d
    r = math.hypot(x0 - cx, y0 - cy)

    a0 = math.atan2(y0 - cy, x0 - cx)
    am = math.atan2(ym - cy, xm - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    tau = 2.0 * math.pi
    ccw_m, ccw_1 = (am - a0) % tau, (a1 - a0) % tau
    sweep = ccw_1 if ccw_m <= ccw_1 else ccw_1 - tau

    n = max(2, int(math.ceil(abs(math.degrees(sweep)) / ARC_SEG_DEG)))
    return [
        (cx + r * math.cos(a0 + sweep * i / n), cy + r * math.sin(a0 + sweep * i / n))
        for i in range(n + 1)
    ]


def circle_points(c, r, n: int = CIRCLE_SEGMENTS) -> list:
    step = 2.0 * math.pi / n
    return [
        (c[0] + r * math.cos(step * i), c[1] + r * math.sin(step * i))
        for i in range(n)
    ]


def assemble_loops(segments: list) -> list:
    """Chain open polylines into CLOSED loops by endpoint identity.

    KiCad emits a rounded rectangle as line/arc/line/arc... with shared
    endpoints but no consistent direction, so segments are walked from either
    end. Anything that does not close, or a vertex where three segments meet,
    is a GateError -- an open contour would flood-fill the whole plate.
    """
    ends = defaultdict(list)
    for i, seg in enumerate(segments):
        ends[_key(seg[0])].append(i)
        ends[_key(seg[-1])].append(i)

    unused = set(range(len(segments)))
    loops = []
    while unused:
        seed = min(unused)          # lowest index first -> deterministic order
        unused.discard(seed)
        pts = list(segments[seed])
        while True:
            k = _key(pts[-1])
            nxt = [i for i in ends[k] if i in unused]
            if not nxt:
                break
            if len(nxt) > 1:
                raise GateError(
                    f"vertex {k} joins {len(nxt) + 1} Edge.Cuts segments -- the "
                    "contour walk cannot choose a branch. The plate outline is "
                    "meant to be a set of simple closed contours."
                )
            i = nxt[0]
            unused.discard(i)
            seg = segments[i]
            pts.extend(seg[1:] if _key(seg[0]) == k else seg[-2::-1])
        if _key(pts[0]) != _key(pts[-1]):
            raise GateError(
                f"open Edge.Cuts contour: starts at {_key(pts[0])}, ends at "
                f"{_key(pts[-1])}. Filling it would flood the whole plate."
            )
        loops.append(pts[:-1])
    return loops


def edge_loops(shapes: dict) -> list:
    """Every closed Edge.Cuts contour of a plate board, as a point list."""
    segs = []
    for ln in shapes["lines"]:
        if ln["layer"] == "Edge.Cuts":
            segs.append([ln["p0"], ln["p1"]])
    for a in shapes["arcs"]:
        if a["layer"] == "Edge.Cuts":
            segs.append(arc_points(a["p0"], a["mid"], a["p1"]))
    loops = assemble_loops(segs)
    for c in shapes["circles"]:
        if c["layer"] == "Edge.Cuts":
            loops.append(circle_points(c["c"], c["d"] / 2.0))
    return loops


def bbox(loop) -> tuple:
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    return min(xs), min(ys), max(xs), max(ys)


# --------------------------------------------------------------------------
# raster
# --------------------------------------------------------------------------


def rasterize(loops: list, x0: float, y0: float, w_px: int, h_px: int) -> np.ndarray:
    """Even-odd fill of `loops` into an (h_px, w_px) uint8 coverage map.

    Even-odd is exactly right here: the outline encloses every hole and the
    holes are disjoint, so XOR-accumulating each loop leaves plate material
    set and openings clear. Each loop is drawn only inside its own bounding
    box, which keeps the supersampled work proportional to the geometry.
    """
    from PIL import Image, ImageDraw

    acc = np.zeros((h_px * SS, w_px * SS), dtype=bool)
    lim_w, lim_h = w_px * SS, h_px * SS
    for loop in loops:
        px = [
            (int(round((x - x0) * PX_PER_MM * SS)),
             int(round((y - y0) * PX_PER_MM * SS)))
            for (x, y) in loop
        ]
        bx0 = max(0, min(p[0] for p in px) - 1)
        by0 = max(0, min(p[1] for p in px) - 1)
        bx1 = min(lim_w, max(p[0] for p in px) + 2)
        by1 = min(lim_h, max(p[1] for p in px) + 2)
        if bx1 <= bx0 or by1 <= by0:
            raise GateError(f"loop with bbox {bbox(loop)} falls outside the map")
        img = Image.new("1", (bx1 - bx0, by1 - by0), 0)
        ImageDraw.Draw(img).polygon([(x - bx0, y - by0) for (x, y) in px], fill=1)
        acc[by0:by1, bx0:bx1] ^= np.array(img, dtype=bool)

    counts = acc.reshape(h_px, SS, w_px, SS).sum(axis=(1, 3), dtype=np.int32)
    full = SS * SS
    return ((counts * 255 + full // 2) // full).astype(np.uint8)


def write_rgba(path: Path, rgb: tuple, alpha: np.ndarray) -> int:
    """RGBA PNG, flat `rgb` in every pixel, `alpha` as the coverage."""
    from PIL import Image

    h, w = alpha.shape
    buf = np.empty((h, w, 4), dtype=np.uint8)
    buf[..., 0], buf[..., 1], buf[..., 2] = rgb
    buf[..., 3] = alpha
    path.parent.mkdir(parents=True, exist_ok=True)
    # optimize=False + a fixed compress_level pins zlib's behaviour; PIL writes
    # no tIME chunk, so the bytes depend only on the pixels.
    Image.fromarray(buf, mode="RGBA").save(
        path, format="PNG", optimize=False, compress_level=6
    )
    return path.stat().st_size


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------


def gate_identity(boards: dict) -> None:
    """All three variants must carry the SAME Edge.Cuts geometry.

    This is what licenses one shared openings map. CASE-V2-NOTES.md §14
    records validate_fab_v5 reporting "ALL GATES PASS (3/3 variants)" against
    one profile; this re-proves it from the boards themselves.
    """
    sigs = {vid: pcb_layer_signature(s, "Edge.Cuts") for vid, s in boards.items()}
    ids = sorted(sigs)
    ref = sigs[ids[0]]
    for vid in ids[1:]:
        if sigs[vid] != ref:
            only_ref = sorted(set(ref) - set(sigs[vid]), key=repr)[:5]
            only_vid = sorted(set(sigs[vid]) - set(ref), key=repr)[:5]
            raise GateError(
                f"plate variants {ids[0]!r} and {vid!r} do NOT share an "
                f"Edge.Cuts profile ({len(ref)} vs {len(sigs[vid])} shapes). "
                f"Only in {ids[0]}: {only_ref}. Only in {vid}: {only_vid}. "
                "One shared openings map would be wrong for at least one "
                "variant -- emit per-variant maps or fix the boards."
            )


def gate_census(loops: list) -> None:
    seen = Counter(
        (round(x1 - x0, 3), round(y1 - y0, 3))
        for (x0, y0, x1, y1) in (bbox(lp) for lp in loops)
    )
    want = Counter({k: v for k, v in EXPECTED_LOOPS.items()})
    if seen != want:
        raise GateError(
            "the ordered plate's Edge.Cuts census changed.\n"
            f"  expected: {dict(sorted(want.items()))}\n"
            f"  measured: {dict(sorted(seen.items()))}\n"
            "Sizes are (bbox_w, bbox_h) in mm. Re-derive EXPECTED_LOOPS "
            "against the new board before shipping a texture of it."
        )


def gate_orientation(alpha: np.ndarray, x0: float, y0: float, case) -> str:
    """Pin the map's handedness AND its flip, using an asymmetric feature.

    The plate outline is a symmetric rounded rectangle and carries no
    orientation information at all. The layer-indicator hole does: LED14 sits
    at (13.525, 79.35), and BOTH of its mirror images -- about the x centreline
    and about the y centreline -- land on solid plate. So three probes pin the
    map completely. A mirrored or flipped raster fails at least one.
    """

    def at(x: float, y: float) -> int:
        col = int((x - x0) * PX_PER_MM)
        row = int((y - y0) * PX_PER_MM)
        return int(alpha[row, col])

    cx, cy = case.get("CX"), case.get("CY")
    led = (13.525, 79.35)             # LYR_HOLE_D over LED14, case:337
    mirror_x = (2 * cx - led[0], led[1])
    mirror_y = (led[0], 2 * cy - led[1])
    enc = (14.025, 12.5)              # encoder opening centre, v2.12
    tp5 = (13.525, 88.85)             # touch pad -- a PAD, so plate is solid

    probes = [
        ("LED14 hole", led, "open", at(*led)),
        ("LED14 mirrored in x", mirror_x, "solid", at(*mirror_x)),
        ("LED14 mirrored in y", mirror_y, "solid", at(*mirror_y)),
        ("encoder opening", enc, "open", at(*enc)),
        ("TP5 touch pad", tp5, "solid", at(*tp5)),
    ]
    bad = [
        p for p in probes
        if (p[2] == "open" and p[3] > 20) or (p[2] == "solid" and p[3] < 235)
    ]
    if bad:
        raise GateError(
            "ORIENTATION GATE FAILED on the plate openings map. Expected "
            + "; ".join(f"{n} at {xy} to be {want}" for n, xy, want, _ in bad)
            + f"; measured alpha {[p[3] for p in bad]}. The raster is "
            "mirrored, flipped or mis-framed."
        )
    return "; ".join(f"{n} {want} (alpha {got})" for n, _xy, want, got in probes)


def gate_markers(boards: dict) -> dict:
    """Each variant carries EXACTLY the one marker the catalog claims."""
    tp5 = (13.525, 88.85)
    found = {}
    for vid, shapes in boards.items():
        f_mask = [
            c for c in shapes["circles"]
            if c["layer"] == "F.Mask" and abs(c["c"][0] - tp5[0]) < 5e-4
            and abs(c["c"][1] - tp5[1]) < 5e-4
        ]
        f_silk = [
            c for c in shapes["circles"]
            if c["layer"] == "F.SilkS" and abs(c["c"][0] - tp5[0]) < 5e-4
            and abs(c["c"][1] - tp5[1]) < 5e-4
        ]
        if len(f_mask) > 1 or len(f_silk) > 1:
            raise GateError(f"{vid}: more than one marker circle over TP5")
        if f_mask and f_silk:
            raise GateError(f"{vid}: carries BOTH marker kinds over TP5")
        if f_mask:
            found[vid] = ("exposed_pad", f_mask[0]["d"], 0.0)
        elif f_silk:
            found[vid] = ("silk_ring", f_silk[0]["d"], f_silk[0]["width"])
        else:
            found[vid] = ("none", None, None)

    for vid, (marker, _d, _w) in found.items():
        want = PLATE_MARKERS[vid][0]
        if marker != want:
            raise GateError(
                f"plate variant {vid!r} carries a {marker!r} marker over TP5 "
                f"but common.PLATE_MARKERS claims {want!r}. The catalog would "
                "describe a plate nobody can order."
            )
    return found


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out_dir = TEX_DIR
    if "--out" in argv:
        out_dir = Path(argv[argv.index("--out") + 1]).resolve()

    import json

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    pcb_w, pcb_h = contract["outline"]["target_mm"]
    case = SourceConstants(CASE_PY, REPO_ROOT, seed={"PCB_W": pcb_w, "PCB_H": pcb_h})

    boards = {vid: read_pcb_shapes(p) for vid, p in PLATE_BOARDS.items()}
    gate_identity(boards)
    markers = gate_markers(boards)

    loops = edge_loops(boards["standard"])
    gate_census(loops)

    # The raster frame is the ORDERED outline's own bounding box, cross-checked
    # against the case model. A disagreement is a stop, not a pick.
    outline = max(loops, key=lambda lp: (bbox(lp)[2] - bbox(lp)[0]))
    x0, y0, x1, y1 = bbox(outline)
    span_w, span_h = round(x1 - x0, 6), round(y1 - y0, 6)
    want_w, want_h = round(case.get("PLATE_W"), 6), round(case.get("PLATE_H"), 6)
    if (span_w, span_h) != (want_w, want_h):
        raise GateError(
            f"the ordered plate outline spans {span_w} x {span_h} mm but "
            f"agentpad13_case_v2.py says PLATE_W x PLATE_H = {want_w} x "
            f"{want_h}. The fab file and the case model disagree about the "
            "size of the part -- do not texture either one."
        )

    w_px, h_px = span_w * PX_PER_MM, span_h * PX_PER_MM
    if abs(w_px - round(w_px)) > 1e-9 or abs(h_px - round(h_px)) > 1e-9:
        raise GateError(
            f"{span_w} x {span_h} mm at {PX_PER_MM} px/mm is {w_px} x {h_px} "
            "px, not an integer grid. Choose a PX_PER_MM that divides the "
            "plate exactly rather than shipping a fractional edge."
        )
    w_px, h_px = int(round(w_px)), int(round(h_px))

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"textures -> {out_dir}")
    print(f"  frame: board x {x0}..{x1}, y {y0}..{y1} @ {PX_PER_MM} px/mm "
          f"= {w_px} x {h_px} px (supersample {SS}x{SS})")

    alpha = rasterize(loops, x0, y0, w_px, h_px)
    orient = gate_orientation(alpha, x0, y0, case)
    size = write_rgba(out_dir / "plate_openings.png", PLATE_WHITE_RGB, alpha)
    solid = float((alpha == 255).sum()) / alpha.size
    print(f"  {'plate_openings':24} {size/1024:8.1f} KiB  "
          f"{solid*100:5.1f}% material, {len(loops)} contours")

    emitted = ["plate_openings.png"]
    for vid, (marker, d, stroke) in sorted(markers.items()):
        rel = PLATE_MARKERS[vid][1]
        if rel is None:
            print(f"  {'(' + vid + ')':24} markerless -- no decal emitted, "
                  "catalog decal is null")
            continue
        c = (13.525, 88.85)
        if marker == "exposed_pad":
            decal_loops = [circle_points(c, d / 2.0)]
            rgb = ENIG_GOLD_RGB
            what = f"Ø{d:g} exposed ENIG gold disc"
        elif marker == "silk_ring":
            decal_loops = [
                circle_points(c, (d + stroke) / 2.0),
                circle_points(c, (d - stroke) / 2.0),
            ]
            rgb = SILK_WHITE_RGB
            what = f"Ø{d:g} silkscreen ring, {stroke:g} stroke"
        else:  # pragma: no cover -- gate_markers has already vetted this
            raise GateError(f"{vid}: unhandled marker {marker!r}")

        a = rasterize(decal_loops, x0, y0, w_px, h_px)
        if not a.any():
            raise GateError(f"{vid}: the {marker} decal rendered fully empty")
        name = Path(rel).name
        size = write_rgba(out_dir / name, rgb, a)
        emitted.append(name)
        print(f"  {name[:-4]:24} {size/1024:8.1f} KiB  {what}")

    total = sum((out_dir / n).stat().st_size for n in emitted)
    print(f"\n{len(emitted)} textures = {total/1024:.1f} KiB total")
    print(f"  Edge.Cuts identity: all 3 variants share one "
          f"{len(pcb_layer_signature(boards['standard'], 'Edge.Cuts'))}-shape "
          "profile -- PASS")
    print(f"  orientation: {orient} -- PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateError as exc:
        print(f"TEXTURE GATE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

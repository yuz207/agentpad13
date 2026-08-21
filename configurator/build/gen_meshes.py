#!/usr/bin/env python3
"""Generate `out/meshes/*.glb` -- viewer meshes derived from SHIPPED artifacts.

Nothing here re-runs CAD. Every mesh comes from a file that is listed in
`release/MANIFEST.md`: the printed/ordered STLs, the plate STEP, and the board
plot PNG. Inputs are gated against the manifest before anything is written.

Output space is glTF's Y-up right-handed frame. Per-part source frames and the
handedness argument are documented in build/README.md; the short version is in
common.py's module docstring.

Run:  python3 configurator/build/gen_meshes.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    GateError,
    MESH_DIR,
    RELEASE,
    read_manifest,
    repo_path,
)
from meshlib import (  # noqa: E402
    Prim,
    crease_normals,
    decimate,
    load_stl,
    signed_volume,
    transform,
    weld,
    write_glb,
)

CASE = "hardware/case/v2"
CAPS = "hardware/PCBWay_keycaps_boxfit_2026-07-24"
BOARD_PLOT = "hardware/pcb/v5_7_render_top.png"

CONTRACT = RELEASE / "hardware/pcb/harness/contract_v4.json"
_contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
PCB_W, PCB_H = _contract["outline"]["target_mm"]
OCTAGON = [tuple(map(float, v)) for v in _contract["outline"]["chamfer_vertices"]]
PCB_T = 1.6  # agentpad13_case_v2.py:353 PCB_T_DESIGN

# --- frame -> glTF matrices ------------------------------------------------
# BOARD ("D"): the left-handed case-model frame. (x, y, z) -> (x, z, y).
# det = -1, which is what makes the render the real device and not its mirror.
M_BOARD = np.array(
    [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=np.float64
)
# PRINT ("A"): what the mirrored-at-export tray/base STLs contain.
# y_A = PCB_H - y_D, so (x, y, z) -> (x, z, PCB_H - y). det = +1.
M_PRINT = np.array(
    [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, PCB_H], [0, 0, 0, 1]], dtype=np.float64
)

# Per-mesh triangle budgets. Chosen so that any ONE configuration the viewer
# shows (tray + one band + plate + board + one base + two cap meshes + one
# knob + one stick cap) stays around 45k triangles.
BUDGET_TRAY = 12000
BUDGET_CASE = 6000
BUDGET_CAP = 6000
BUDGET_TOPPER = 5000
BUDGET_PLATE = 8000

# OCCT tessellation parameters for the plate STEP. Fixed values -> fixed
# output; proven byte-identical across separate processes on OCP 7.9.3.1.
PLATE_LIN_DEFLECTION = 0.05
PLATE_ANG_DEFLECTION = 0.3


def _parts() -> list[dict]:
    """(name, release-relative source, frame matrix, triangle budget)."""
    out: list[dict] = []
    out.append(
        dict(name="tray", src=f"{CASE}/stl/agentpad13_v2_tray_v5.stl",
             m=M_PRINT, budget=BUDGET_TRAY, placement="baked")
    )
    for w in ("w3.0", "w5.4", "w7.4"):
        out.append(
            dict(name=f"band_{w}", src=f"{CASE}/stl/agentpad13_v2_band_1.6mm_{w}.stl",
                 m=M_BOARD, budget=BUDGET_CASE, placement="baked")
        )
    for item in ("riser", "wedge", "pedestal"):
        out.append(
            dict(name=f"base_{item}", src=f"{CASE}/bases/stl/base_{item}_peg_5p8.stl",
                 m=M_PRINT, budget=BUDGET_CASE, placement="baked")
        )
    for profile in ("dish", "plateau"):
        for width, suffix in (("17p5", "_17p5"), ("std", "")):
            for size in ("1u", "2u", "2u_stab"):
                out.append(
                    dict(
                        name=f"cap_{profile}_{size}_{width}",
                        src=f"{CAPS}/cap_{profile}_{size}{suffix}_boxfit.stl",
                        m=M_BOARD, budget=BUDGET_CAP, placement="instance",
                    )
                )
    for style in ("A", "B2", "C"):
        out.append(
            dict(name=f"knob_{style}",
                 src=f"{CASE}/toppers/stl/knob_v2_{style}_bore_nom.stl",
                 m=M_BOARD, budget=BUDGET_TOPPER, placement="instance")
        )
    for part, stem in (("nub_C2", "stick_nub_v2_C2"), ("puck_TPU", "stick_puck_v2_TPU")):
        out.append(
            dict(name=f"stick_cap_{part}",
                 src=f"{CASE}/toppers/stl/{stem}_sock_nom.stl",
                 m=M_BOARD, budget=BUDGET_TOPPER, placement="instance")
        )
    return out


# --------------------------------------------------------------------------
# plate: tessellate the SHIPPED STEP
# --------------------------------------------------------------------------


def plate_mesh():
    from build123d import import_step
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS

    step = RELEASE / CASE / "step/agentpad13_v2_plate.step"
    shape = import_step(str(step)).wrapped
    BRepMesh_IncrementalMesh(
        shape, PLATE_LIN_DEFLECTION, False, PLATE_ANG_DEFLECTION, True
    )
    verts: list[tuple] = []
    faces: list[tuple] = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            base = len(verts)
            for i in range(1, tri.NbNodes() + 1):
                p = tri.Node(i).Transformed(trsf)
                verts.append((p.X(), p.Y(), p.Z()))
            reversed_face = face.Orientation().name == "TopAbs_REVERSED"
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                t = (base + a - 1, base + b - 1, base + c - 1)
                faces.append((t[0], t[2], t[1]) if reversed_face else t)
        exp.Next()
    if not faces:
        raise GateError(f"{step}: STEP tessellation produced no triangles")
    vert_arr = np.array(verts, dtype=np.float64)
    soup = vert_arr[np.array(faces, dtype=np.int64)]  # (n_tri, 3, 3)
    return weld(soup)


# --------------------------------------------------------------------------
# board: octagonal slab textured with the shipped F.Cu plot
# --------------------------------------------------------------------------


def crop_board_texture(out_png: Path) -> dict:
    """Crop `v5_7_render_top.png` to exactly the board octagon.

    The shipped file is a matplotlib F.Cu plot with axes and a title. The axis
    spines and the black board outline are located from the pixels, then the
    crop is VERIFIED against known geometry before use:
      * aspect must equal 84.2 / 100.0
      * the image's TOP row of the outline must span the 13.2 -> 69.6 chamfer
        edge and the BOTTOM row the 14.6 -> 69.6 edge
    The second check is the texture's chirality gate: those two legs differ
    (contract outline.chamfer_vertices), so it pins image-top to board y = 0
    and rules out a flipped or mirrored plot.
    """
    from PIL import Image

    src = repo_path(f"release/{BOARD_PLOT}")
    im = Image.open(src).convert("RGB")
    a = np.array(im).astype(np.int16)
    black = a.max(axis=2) < 70
    h, w = black.shape

    rows = np.nonzero(black.sum(axis=1) > 0.6 * w)[0]
    cols = np.nonzero(black.sum(axis=0) > 0.6 * h)[0]
    if len(rows) < 2 or len(cols) < 2:
        raise GateError(
            f"{BOARD_PLOT}: could not find the plot's axis spines "
            f"(rows={rows.tolist()}, cols={cols.tolist()}). The shipped render "
            "changed shape -- re-derive the crop before shipping a texture."
        )
    r0, r1 = int(rows[0]), int(rows[-1])
    c0, c1 = int(cols[0]), int(cols[-1])

    inner = black[r0 + 3: r1 - 2, c0 + 3: c1 - 2]
    ys, xs = np.nonzero(inner)
    x0, x1 = int(xs.min()) + c0 + 3, int(xs.max()) + c0 + 3
    y0, y1 = int(ys.min()) + r0 + 3, int(ys.max()) + r0 + 3

    span_x, span_y = x1 - x0, y1 - y0
    aspect = span_x / span_y
    want = PCB_W / PCB_H
    if abs(aspect - want) / want > 0.005:
        raise GateError(
            f"{BOARD_PLOT}: detected outline aspect {aspect:.5f} != board "
            f"{want:.5f}. The crop is not the board -- do not texture with it."
        )
    px_per_mm = span_x / PCB_W

    def flat_run(row: int) -> tuple[float, float]:
        r = np.nonzero(black[row])[0]
        r = r[(r >= x0 - 3) & (r <= x1 + 3)]
        return (r.min() - x0) / px_per_mm, (r.max() - x0) / px_per_mm

    top_lo, top_hi = flat_run(y0 + 1)
    bot_lo, bot_hi = flat_run(y1 - 1)
    tol = 0.35
    ok = (
        abs(top_lo - 13.2) < tol and abs(top_hi - 69.6) < tol
        and abs(bot_lo - 14.6) < tol and abs(bot_hi - 69.6) < tol
    )
    if not ok:
        raise GateError(
            f"{BOARD_PLOT}: CHIRALITY GATE FAILED. Expected the outline's top "
            f"edge to run 13.2..69.6 mm (the board's unique 13.2 chamfer leg) "
            f"and the bottom edge 14.6..69.6, but measured top "
            f"{top_lo:.2f}..{top_hi:.2f} and bottom {bot_lo:.2f}..{bot_hi:.2f}. "
            "The plot is flipped, mirrored or re-framed; the texture would put "
            "the board on the wrong hand."
        )

    im.crop((x0, y0, x1 + 1, y1 + 1)).save(
        out_png, format="PNG", optimize=False, compress_level=6
    )
    return {
        "crop_px": [x0, y0, x1 + 1, y1 + 1],
        "px_per_mm": round(px_per_mm, 6),
        "chirality_check": (
            f"top edge {top_lo:.2f}..{top_hi:.2f} mm (expect 13.2..69.6), "
            f"bottom edge {bot_lo:.2f}..{bot_hi:.2f} mm (expect 14.6..69.6) -- PASS"
        ),
    }


def board_mesh():
    """Octagonal PCB slab, z = -PCB_T .. 0 in the board frame.

    Returns (top_prim_data, side_prim_data) as (verts, faces, uv|None).
    """
    poly = list(OCTAGON)
    area2 = sum(
        poly[i][0] * poly[(i + 1) % len(poly)][1]
        - poly[(i + 1) % len(poly)][0] * poly[i][1]
        for i in range(len(poly))
    )
    if area2 < 0:  # force a consistent CCW loop in the raw (x, y) numbers
        poly = poly[::-1]
    n = len(poly)

    top = np.array([[x, y, 0.0] for (x, y) in poly], dtype=np.float64)
    bot = np.array([[x, y, -PCB_T] for (x, y) in poly], dtype=np.float64)

    top_f = np.array([[0, i, i + 1] for i in range(1, n - 1)], dtype=np.int64)
    uv = np.array([[x / PCB_W, y / PCB_H] for (x, y) in poly], dtype=np.float64)

    rest_v = np.concatenate([top, bot])
    rest_f = [[n, n + i + 1, n + i] for i in range(1, n - 1)]  # bottom, reversed
    for i in range(n):
        j = (i + 1) % n
        rest_f.append([i, n + i, n + j])
        rest_f.append([i, n + j, j])
    return (top, top_f, uv), (rest_v, np.array(rest_f, dtype=np.int64), None)


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def emit(name: str, V, F, matrix, budget: int | None, report: list) -> None:
    """Decimate -> transform into glTF space -> crease normals -> write .glb.

    Gates on the way through: the decimated solid must keep its bounding box
    and its volume, and the transformed solid must still have positive signed
    volume (i.e. it is not inside out after a reflection).
    """
    tri_in = len(F)
    bbox_in = (V.min(axis=0), V.max(axis=0))
    vol_in = abs(signed_volume(V, F))
    if budget is not None and tri_in > budget:
        V, F = decimate(V, F, budget)
        drift = np.max(
            np.abs(np.array([V.min(axis=0) - bbox_in[0], V.max(axis=0) - bbox_in[1]]))
        )
        if drift > 0.25:
            raise GateError(
                f"{name}: decimation moved the bounding box by {drift:.3f} mm "
                "(limit 0.25). Raise the triangle budget for this part."
            )
        vol_out = abs(signed_volume(V, F))
        if vol_in > 1.0 and abs(vol_out - vol_in) / vol_in > 0.05:
            raise GateError(
                f"{name}: decimation changed volume {vol_in:.1f} -> "
                f"{vol_out:.1f} mm^3 (>5%). Raise the triangle budget."
            )
    V, F = transform(V, F, matrix)
    vol = signed_volume(V, F)
    if vol <= 0:
        raise GateError(
            f"{name}: signed volume {vol:.3f} <= 0 after transform -- the mesh "
            "is inside out. A reflection was applied without reversing the "
            "winding, or the source STL is not a closed outward-facing solid."
        )
    pos, nrm, faces = crease_normals(V, F)
    size = write_glb(MESH_DIR / f"{name}.glb", [Prim(pos, nrm, faces)])
    report.append(
        dict(name=name, tris_in=tri_in, tris_out=int(len(F)),
             verts=int(pos.shape[0]), bytes=size, volume_mm3=round(vol, 3))
    )
    print(
        f"  {name:28} {tri_in:6d} -> {len(F):6d} tris  "
        f"{pos.shape[0]:6d} verts  {size/1024:8.1f} KiB  vol {vol:10.1f}"
    )


def main(argv: list[str] | None = None) -> int:
    global MESH_DIR
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--out" in argv:
        MESH_DIR = Path(argv[argv.index("--out") + 1]).resolve()
    manifest = read_manifest()
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    report: list = []
    t0 = time.time()

    parts = _parts()
    needed = [p["src"] for p in parts] + [
        f"{CASE}/step/agentpad13_v2_plate.step",
        BOARD_PLOT,
    ]
    missing = [s for s in needed if s not in manifest]
    if missing:
        print("MESH GATE FAILED: inputs not listed in release/MANIFEST.md:",
              file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1
    absent = [s for s in needed if not (RELEASE / s).is_file()]
    if absent:
        print("MESH GATE FAILED: inputs absent on disk:", file=sys.stderr)
        for m in absent:
            print(f"  - release/{m}", file=sys.stderr)
        return 1

    print(f"meshes -> {MESH_DIR}")
    for p in parts:
        V, F = weld(load_stl(RELEASE / p["src"]))
        emit(p["name"], V, F, p["m"], p["budget"], report)

    V, F = plate_mesh()
    emit("plate", V, F, M_BOARD, BUDGET_PLATE, report)

    tex_info = crop_board_texture(MESH_DIR / "board_top.png")
    (tv, tf, tuv), (rv, rf, _) = board_mesh()
    materials = [
        {
            "name": "board_top",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 0.85,
            },
        },
        {
            "name": "board_edge",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.09, 0.11, 0.10, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.9,
            },
        },
    ]
    images = {
        "images": [{"uri": "board_top.png"}],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987,
                      "wrapS": 33071, "wrapT": 33071}],
    }
    rv_t, rf_t = transform(rv, rf, M_BOARD)
    rpos, rnrm, rfaces = crease_normals(rv_t, rf_t)
    side_prim = Prim(rpos, rnrm, rfaces, material=1)
    tv_t, tf_t = transform(tv, tf, M_BOARD)
    tpos, tnrm, tfaces = crease_normals(tv_t, tf_t)
    tuvs = np.stack(
        [tpos[:, 0] / PCB_W, tpos[:, 2] / PCB_H], axis=1
    ).astype(np.float32)
    size = write_glb(
        MESH_DIR / "board.glb",
        [Prim(tpos, tnrm, tfaces, uv=tuvs, material=0), side_prim],
        materials=materials,
        images=images,
    )
    report.append(dict(name="board", tris_in=int(len(tf) + len(rf)),
                       tris_out=int(len(tf) + len(rf)),
                       verts=int(tpos.shape[0] + rpos.shape[0]),
                       bytes=size, volume_mm3=None))
    print(f"  {'board':28} {len(tf)+len(rf):6d} tris (textured slab)"
          f"  {size/1024:8.1f} KiB")

    tex_bytes = (MESH_DIR / "board_top.png").stat().st_size
    total = sum(r["bytes"] for r in report) + tex_bytes
    print(
        f"\n{len(report)} meshes + 1 texture = "
        f"{total/1024/1024:.2f} MiB total ({time.time()-t0:.1f}s)"
    )
    print(f"  texture chirality: {tex_info['chirality_check']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateError as exc:
        print(f"MESH GATE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

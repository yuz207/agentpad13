#!/usr/bin/env python3
"""Render the v2.16 base-family STLs to iso + side PNGs (same pattern as
toppers/render_toppers.py: matplotlib is NOT in the khana build env, so this
runs on the SYSTEM python3 and parses the binary STLs agentpad13_base.py
already exported).

    python3 render_bases.py

Writes ./renders/bases.png — one row per variant: a 3D iso plus a TRUE y-z
silhouette at 1:1 aspect. The silhouette is the one that matters, because it is
the only view in which the wedge is not uniform.

[v2.15] ORIENTATION: these parse the EXPORTED STLs, which are now mirrored at
export (the same left-handed-frame fix the tray carries), so the FAR / USB /
control-band edge lands at y = 100 and a correct back-raised wedge is THICK ON
THE RIGHT. Before v2.15 the exports were un-mirrored and it was thick on the
left; if you are comparing against an old render, that flip is the fix, not a
regression. The dashed line marks the mating plane = the tray bottom, which
v2.11 moved to -9.5 when it gave the tray its 2 mm plinth.
"""

import os
import struct

import numpy as np

MATE_Z = -9.5   # = C.Z_TRAY_BOT since the v2.11 plinth (was -7.5)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "stl")
RENDERS = os.path.join(HERE, "renders")
os.makedirs(RENDERS, exist_ok=True)

VARIANTS = ["riser", "wedge", "pedestal"]
RUNG = "5p8"


def load_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        data = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
    verts = np.ascontiguousarray(data[:, 12:48]).view("<f4").reshape(n, 3, 3)
    return np.array(verts, dtype=float)


def face_normals(tris):
    """Unit face normals. Degenerate (zero-area) triangles do occur in exported
    STLs; they are mapped to a zero normal so they cull out cleanly instead of
    poisoning every later matmul with NaN/inf."""
    v = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n = np.linalg.norm(v, axis=1, keepdims=True)
    with np.errstate(all="ignore"):
        out = np.where(n > 1e-12, v / np.where(n > 1e-12, n, 1.0), 0.0)
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def render_ax(ax, tris, title, elev, azim):
    """Orthographic iso, drawn as a 2D PolyCollection with BACKFACE CULLING and
    painter's-algorithm depth sorting.

    Poly3DCollection was giving a wrong picture here: its `zsort` averages the
    transformed z of each face, which interleaves badly for a solid with a deep
    internal cavity, so the pedestal's ballast ribs were drawn THROUGH the top
    face and the part read as an open dish. Culling faces whose normal points
    away from the camera, then sorting the survivors back-to-front, renders a
    closed solid correctly and is what the two commits below actually show."""
    # The BLAS kernel raises spurious divide/overflow/invalid FPE flags on
    # these matmuls even though every input is finite (verified: no NaN, no inf,
    # no zero-length normals). Silenced deliberately rather than left to noise
    # up the build log.
    np.errstate(all="ignore").__enter__()
    el, az = np.radians(elev), np.radians(azim)
    view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    right = np.array([-np.sin(az), np.cos(az), 0.0])
    up = np.cross(view, right)

    nrm = face_normals(tris)
    keep = (nrm @ view) > 0.0                      # backface cull
    tris, nrm = tris[keep], nrm[keep]

    depth = (tris.reshape(-1, 3, 3).mean(axis=1)) @ view
    order = np.argsort(depth)                      # far -> near
    tris, nrm = tris[order], nrm[order]

    light = np.array([0.35, -0.5, 0.78])
    light /= np.linalg.norm(light)
    inten = np.clip(np.abs(nrm @ light), 0, 1) * 0.65 + 0.35
    cols = np.clip(np.array([0.62, 0.66, 0.72])[None, :] * inten[:, None], 0, 1)

    flat = tris.reshape(-1, 3)
    polys = np.stack([flat @ right, flat @ up], axis=-1).reshape(-1, 3, 2)
    # No wireframe: STL fan-triangulation of the big flat mating face was
    # reading as 60 radial RIBS on the pedestal, which the part does not have.
    # Shading alone carries the form, and every real edge is a normal break.
    ax.add_collection(PolyCollection(polys, facecolors=cols, edgecolors="none"))
    xs, ys = polys[:, :, 0], polys[:, :, 1]
    ax.set_xlim(xs.min() - 3, xs.max() + 3)
    ax.set_ylim(ys.min() - 3, ys.max() + 3)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(title, fontsize=8)


def silhouette_ax(ax, tris, title):
    """True orthographic y-z silhouette, 1:1 aspect (the wedge-revealing view)."""
    polys = tris[:, :, 1:3]                       # drop x -> (y, z) per vertex
    ax.add_collection(PolyCollection(polys, facecolors=(0.45, 0.49, 0.56),
                                     edgecolors="none"))
    ymin, ymax = polys[:, :, 0].min(), polys[:, :, 0].max()
    zmin, zmax = polys[:, :, 1].min(), polys[:, :, 1].max()
    ax.set_xlim(ymin - 4, ymax + 4)
    ax.set_ylim(zmin - 3, zmax + 3)
    ax.set_aspect("equal")
    ax.axhline(MATE_Z, color="crimson", lw=0.8, ls="--")
    ax.text(ymin - 2, MATE_Z + 0.3, f"z = {MATE_Z}  tray bottom / mating plane",
            fontsize=6, color="crimson", va="bottom")
    ax.text(ymin, zmin - 2.2, "NEAR (user)", fontsize=6, ha="left")
    ax.text(ymax, zmin - 2.2, "FAR (USB)", fontsize=6, ha="right")
    ax.set_xlabel("exported y (mm)  — mirrored frame, USB at y=100", fontsize=6)
    ax.set_ylabel("z (mm)", fontsize=6)
    ax.tick_params(labelsize=6)
    ax.set_title(title, fontsize=8)


if __name__ == "__main__":
    fig = plt.figure(figsize=(10, 2.6 * len(VARIANTS)))
    for i, v in enumerate(VARIANTS):
        tris = load_stl(os.path.join(STL, f"base_{v}_peg_{RUNG}.stl"))
        zmin, zmax = tris[:, :, 2].min(), tris[:, :, 2].max()
        ax = fig.add_subplot(len(VARIANTS), 2, 2 * i + 1)
        render_ax(ax, tris, f"{v}  —  iso from ABOVE (mating face + pegs)", 26, -62)
        ax = fig.add_subplot(len(VARIANTS), 2, 2 * i + 2)
        silhouette_ax(ax, tris,
                      f"{v}  —  y-z silhouette 1:1   (z {zmin:.2f}..{zmax:.2f}, "
                      f"{zmax - zmin:.2f} mm tall)")
    fig.suptitle("agentpad13 v2.16 tray-base family (peg rung 5.8) — one central "
                 "4-peg interface: flat riser, 8\u00b0 wedge, \u00d878 tilted drum.\n"
                 "Silhouette: thick on the RIGHT = raises the far/USB edge "
                 "(mirrored export)",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = os.path.join(RENDERS, "bases.png")
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")

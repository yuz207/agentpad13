#!/usr/bin/env python3
"""OPTIONAL visual gate: render the composed scene and check its handedness.

Not part of the required build (it needs matplotlib, which the generators do
not). Run it whenever a mesh source or a frame transform changes, and compare
the output against the shipped renders:

    release/renders/v27_turntable.png   TOP-DOWN panel
    release/renders/v27_hero.png        3/4 iso

What must be true, and why it is not a matter of taste: the board frame is
LEFT-handed (agentpad13_case_v2.py:1077), so rendering its numbers in a
right-handed viewer without the det -1 axis swap shows the ENANTIOMORPH. The
give-away features are asymmetric -- encoder on -x, stick on +x, USB on the
far wall -- so a mirrored build is visible at a glance.

    python3 configurator/build/verify_chirality.py out/chirality_check.png
"""

import json
import struct
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

OUT = str(__import__("pathlib").Path(__file__).resolve().parent / "out")
COMP = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    d = open(path, "rb").read()
    assert d[:4] == b"glTF"
    off, chunks = 12, {}
    while off < len(d):
        ln, ty = struct.unpack("<II", d[off:off + 8])
        chunks[ty] = d[off + 8: off + 8 + ln]
        off += 8 + ln
    g = json.loads(chunks[0x4E4F534A].decode("utf-8"))
    bin_ = chunks[0x004E4942]

    def acc(i):
        a = g["accessors"][i]
        v = g["bufferViews"][a["bufferView"]]
        n = a["count"] * NC[a["type"]]
        arr = np.frombuffer(bin_, dtype="<" + COMP[a["componentType"]],
                            count=n, offset=v.get("byteOffset", 0))
        return arr.reshape(a["count"], NC[a["type"]])

    return [(acc(p["attributes"]["POSITION"]).astype(np.float64),
             acc(p["indices"]).astype(np.int64).reshape(-1, 3))
            for p in g["meshes"][0]["primitives"]]


pos = json.load(open(f"{OUT}/positions.json"))


def g3(x, y, z=0.0):
    """board frame -> glTF, per positions.json frame.to_gltf: (x, z, y)."""
    return np.array([x, z, y], dtype=np.float64)


parts = []


def add(name, offset=(0, 0, 0), color="0.6", alpha=1.0):
    for V, F in read_glb(f"{OUT}/meshes/{name}.glb"):
        parts.append((V + np.asarray(offset, dtype=np.float64), F, color, alpha))


add("tray", color="#39404d")
add("board", color="#166534")
add("plate", color="#17181a")
add("band_w5.4", color="#a8c8ee", alpha=0.40)
seat = pos["keycap_seat_z"]
for sw in pos["switches"]:
    mesh = "cap_dish_1u_17p5" if sw["size"] == "1u" else "cap_dish_2u_stab_17p5"
    add(mesh, offset=g3(sw["x"], sw["y"], seat), color="#dcdcdc")
add("knob_knurled_cup", offset=g3(pos["encoder"]["x"], pos["encoder"]["y"]),
    color="#f0a020")
add("stick_cap_taper", offset=g3(pos["stick"]["x"], pos["stick"]["y"]),
    color="#8b3fd0")

allv = np.concatenate([p[0] for p in parts])
ctr = (allv.min(0) + allv.max(0)) / 2


def basis(w):
    w = np.asarray(w, float)
    w /= np.linalg.norm(w)
    up = np.array([0.0, 1.0, 0.0])
    if abs(w @ up) > 0.999:
        up = np.array([0.0, 0.0, -1.0])
    r = np.cross(up, w)
    r /= np.linalg.norm(r)
    return r, np.cross(w, r), w


VIEWS = [
    ("TOP-DOWN\nexpect USB far edge at TOP, encoder TOP-LEFT,\n"
     "stick TOP-RIGHT, 2U key at BOTTOM", (0, 1, 0)),
    ("3/4 ISO from the user's side\nexpect encoder far-LEFT, stick far-RIGHT",
     (0.42, 0.55, 0.72)),
    ("FAR WALL (looking at the USB side)\nexpect USB port centred on the wall",
     (0.0, 0.30, -0.95)),
]

fig, axes = plt.subplots(1, 3, figsize=(19, 7))
for ax, (title, wdir) in zip(axes, VIEWS):
    R, U, W = basis(wdir)
    polys, cols, depth = [], [], []
    for V, F, color, alpha in parts:
        P = V - ctr
        tri = P[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(n, axis=1)
        n = n / np.where(ln > 1e-12, ln, 1)[:, None]
        facing = n @ W
        vis = facing > 0 if alpha > 0.9 else np.ones(len(tri), bool)
        if not vis.any():
            continue
        tri = tri[vis]
        shade = 0.30 + 0.70 * np.clip(np.abs(facing[vis]), 0, 1)
        base = np.array(matplotlib.colors.to_rgb(color))
        rgb = np.clip(base[None, :] * shade[:, None], 0, 1)
        polys.extend(np.stack([tri @ R, tri @ U], axis=-1))
        cols.extend(np.concatenate(
            [rgb, np.full((len(tri), 1), alpha)], axis=1))
        depth.extend(tri.mean(1) @ W)
    order = np.argsort(depth)
    ax.add_collection(PolyCollection(
        [polys[i] for i in order],
        facecolors=[cols[i] for i in order], linewidths=0))
    lim = 70
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10)
plt.tight_layout()
out = sys.argv[1] if len(sys.argv) > 1 else f"{OUT}/chirality_check.png"
plt.savefig(out, dpi=95, facecolor="white")
print("wrote", out)

"""Deterministic mesh pipeline: load -> weld -> decimate -> normals -> glb.

DETERMINISM CONTRACT
--------------------
Same input bytes + same parameters -> byte-identical .glb. Achieved by:
  * no RNG anywhere;
  * no wall-clock or generator metadata in the glTF JSON (asset.version only);
  * the decimator's priority queue is totally ordered -- ties break on the
    (a, b) vertex-index pair, never on insertion order;
  * the 3x3 solve in the inner loop is written out with explicit scalar
    arithmetic (Cramer) instead of calling into BLAS, so no threaded or
    CPU-dispatch-dependent kernel can reorder a floating-point sum;
  * JSON is serialised with fixed separators and the buffer is padded with
    fixed bytes.
`configurator/tests/test_mesh_determinism.py` runs the whole pipeline twice
and compares sha256 per file.
"""

from __future__ import annotations

import heapq
import json
import struct
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# STL
# --------------------------------------------------------------------------


def load_stl(path: Path) -> np.ndarray:
    """Binary STL -> (n_tri, 3, 3) float64 triangle soup."""
    data = Path(path).read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path}: too short to be a binary STL")
    n = struct.unpack("<I", data[80:84])[0]
    expect = 84 + 50 * n
    if len(data) != expect:
        raise ValueError(
            f"{path}: not a binary STL ({len(data)} bytes, expected {expect} "
            f"for {n} triangles) -- ASCII STL is not supported"
        )
    raw = np.frombuffer(data[84:expect], dtype=np.uint8).reshape(n, 50)
    tris = raw[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(np.float64)
    return tris


def weld(tris: np.ndarray, quantum: float = 1e-6) -> tuple[np.ndarray, np.ndarray]:
    """Triangle soup -> (vertices, faces). Vertices merged on a fixed lattice.

    Quantising to a fixed lattice (not a tolerance search) is what makes the
    weld order-independent and therefore deterministic.
    """
    flat = tris.reshape(-1, 3)
    keys = np.rint(flat / quantum).astype(np.int64)
    # np.unique returns (unique, index, inverse) in THAT order.
    _uniq, first, inverse = np.unique(
        keys, axis=0, return_index=True, return_inverse=True
    )
    verts = flat[first]
    # NumPy has shipped both 1-D and (n, 1) inverse shapes for axis=0; ravel.
    faces = np.asarray(inverse).reshape(-1)[: len(flat)].reshape(-1, 3).astype(np.int64)
    keep = (
        (faces[:, 0] != faces[:, 1])
        & (faces[:, 1] != faces[:, 2])
        & (faces[:, 0] != faces[:, 2])
    )
    return verts, faces[keep]


def signed_volume(verts: np.ndarray, faces: np.ndarray) -> float:
    """6x the signed volume /6. Positive == outward-facing CCW winding."""
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


# --------------------------------------------------------------------------
# Quadric error metric decimation
# --------------------------------------------------------------------------

_BOUNDARY_W = 1000.0  # weight on the synthetic plane that pins open edges
_FLIP_DOT = 0.2       # reject a collapse that swings any face normal this far


def _q_add(p, q):
    return tuple(a + b for a, b in zip(p, q))


def _q_from_plane(a, b, c, d, w):
    return (
        w * a * a, w * a * b, w * a * c, w * a * d,
        w * b * b, w * b * c, w * b * d,
        w * c * c, w * c * d,
        w * d * d,
    )


def _q_cost(q, x, y, z):
    (q11, q12, q13, q14, q22, q23, q24, q33, q34, q44) = q
    return (
        q11 * x * x + 2 * q12 * x * y + 2 * q13 * x * z + 2 * q14 * x
        + q22 * y * y + 2 * q23 * y * z + 2 * q24 * y
        + q33 * z * z + 2 * q34 * z
        + q44
    )


def _q_optimal(q):
    """Cramer's rule on the 3x3 block. Returns None when near-singular."""
    (q11, q12, q13, q14, q22, q23, q24, q33, q34, _q44) = q
    a11, a12, a13 = q11, q12, q13
    a21, a22, a23 = q12, q22, q23
    a31, a32, a33 = q13, q23, q33
    c11 = a22 * a33 - a23 * a32
    c12 = a23 * a31 - a21 * a33
    c13 = a21 * a32 - a22 * a31
    det = a11 * c11 + a12 * c12 + a13 * c13
    scale = abs(a11) + abs(a22) + abs(a33) + 1e-30
    if abs(det) < 1e-10 * scale * scale * scale:
        return None
    b1, b2, b3 = -q14, -q24, -q34
    inv = 1.0 / det
    x = inv * (b1 * c11 + b2 * (a13 * a32 - a12 * a33) + b3 * (a12 * a23 - a13 * a22))
    y = inv * (b1 * c12 + b2 * (a11 * a33 - a13 * a31) + b3 * (a13 * a21 - a11 * a23))
    z = inv * (b1 * c13 + b2 * (a12 * a31 - a11 * a32) + b3 * (a11 * a22 - a12 * a21))
    return x, y, z


def decimate(verts: np.ndarray, faces: np.ndarray, target_faces: int):
    """Edge-collapse QEM decimation. Deterministic; returns (verts, faces)."""
    if len(faces) <= target_faces:
        return verts, faces

    P = [tuple(map(float, v)) for v in verts]
    F: list[list[int] | None] = [list(map(int, f)) for f in faces]
    n_faces = len(F)

    adj: list[set[int]] = [set() for _ in P]
    for fi, f in enumerate(F):
        for v in f:
            adj[v].add(fi)

    def face_plane(f):
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = P[f[0]], P[f[1]], P[f[2]]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5
        if ln < 1e-18:
            return None
        return nx / ln, ny / ln, nz / ln, -(nx * ax + ny * ay + nz * az) / ln, ln * 0.5

    Q = [(0.0,) * 10 for _ in P]
    edge_faces: dict[tuple[int, int], int] = {}
    for f in F:
        pl = face_plane(f)
        if pl is None:
            continue
        nx, ny, nz, d, area = pl
        q = _q_from_plane(nx, ny, nz, d, area)
        for v in f:
            Q[v] = _q_add(Q[v], q)
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            key = (a, b) if a < b else (b, a)
            edge_faces[key] = edge_faces.get(key, 0) + 1

    # Open edges get a heavy synthetic plane so silhouettes do not erode.
    for (a, b), count in sorted(edge_faces.items()):
        if count != 1:
            continue
        fset = adj[a] & adj[b]
        if not fset:
            continue
        pl = face_plane(F[min(fset)])
        if pl is None:
            continue
        nx, ny, nz, _d, _area = pl
        ax, ay, az = P[a]
        bx, by, bz = P[b]
        ex, ey, ez = bx - ax, by - ay, bz - az
        px, py, pz = ey * nz - ez * ny, ez * nx - ex * nz, ex * ny - ey * nx
        ln = (px * px + py * py + pz * pz) ** 0.5
        if ln < 1e-18:
            continue
        px, py, pz = px / ln, py / ln, pz / ln
        w = _BOUNDARY_W * (ex * ex + ey * ey + ez * ez)
        q = _q_from_plane(px, py, pz, -(px * ax + py * ay + pz * az), w)
        Q[a] = _q_add(Q[a], q)
        Q[b] = _q_add(Q[b], q)

    alive = [True] * len(P)
    version: dict[tuple[int, int], int] = {}
    heap: list[tuple[float, int, int, int]] = []

    def evaluate(a, b):
        q = _q_add(Q[a], Q[b])
        cand = _q_optimal(q)
        best = None
        options = [P[a], P[b], tuple((P[a][i] + P[b][i]) / 2.0 for i in range(3))]
        if cand is not None:
            options.insert(0, cand)
        for pt in options:
            c = _q_cost(q, *pt)
            if best is None or c < best[0]:
                best = (c, pt)
        return best

    def push(a, b):
        if a > b:
            a, b = b, a
        cost, pt = evaluate(a, b)
        version[(a, b)] = version.get((a, b), 0) + 1
        heapq.heappush(heap, (cost, a, b, version[(a, b)]))
        return pt

    targets: dict[tuple[int, int], tuple] = {}
    for key in sorted(edge_faces):
        targets[key] = push(*key)

    def collapse_ok(a, b, pt):
        """No incident face may flip or go degenerate."""
        shared = adj[a] & adj[b]
        for fi in (adj[a] | adj[b]) - shared:
            f = F[fi]
            if f is None:
                continue
            pl = face_plane(f)
            if pl is None:
                continue
            onx, ony, onz, _d, _ar = pl
            pts = [pt if (v == a or v == b) else P[v] for v in f]
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts
            ux, uy, uz = bx - ax, by - ay, bz - az
            vx, vy, vz = cx - ax, cy - ay, cz - az
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = (nx * nx + ny * ny + nz * nz) ** 0.5
            if ln < 1e-14:
                return False
            if (nx * onx + ny * ony + nz * onz) / ln < _FLIP_DOT:
                return False
        return True

    while n_faces > target_faces and heap:
        cost, a, b, ver = heapq.heappop(heap)
        if version.get((a, b)) != ver or not alive[a] or not alive[b]:
            continue
        if not (adj[a] & adj[b]):
            continue
        pt = targets.get((a, b))
        if pt is None:
            continue
        if not collapse_ok(a, b, pt):
            continue

        P[a] = pt
        Q[a] = _q_add(Q[a], Q[b])
        alive[b] = False
        shared = list(adj[a] & adj[b])
        for fi in shared:
            f = F[fi]
            if f is None:
                continue
            for v in f:
                adj[v].discard(fi)
            F[fi] = None
            n_faces -= 1
        for fi in sorted(adj[b]):
            f = F[fi]
            if f is None:
                continue
            F[fi] = [a if v == b else v for v in f]
            adj[a].add(fi)
        adj[b] = set()

        neigh = set()
        for fi in sorted(adj[a]):
            f = F[fi]
            if f is None:
                continue
            for v in f:
                if v != a and alive[v]:
                    neigh.add(v)
        for w in sorted(neigh):
            key = (a, w) if a < w else (w, a)
            targets[key] = push(*key)

    remap = {}
    out_v = []
    for i, ok in enumerate(alive):
        if ok:
            remap[i] = len(out_v)
            out_v.append(P[i])
    out_f = [
        [remap[v] for v in f]
        for f in F
        if f is not None and len(set(f)) == 3 and all(alive[v] for v in f)
    ]
    return np.array(out_v, dtype=np.float64), np.array(out_f, dtype=np.int64)


# --------------------------------------------------------------------------
# Transform + normals
# --------------------------------------------------------------------------


def transform(verts: np.ndarray, faces: np.ndarray, matrix: np.ndarray):
    """Apply a 4x4 affine. Reverses winding when det < 0 so that faces keep
    pointing outward (a reflection would otherwise turn the solid inside out).
    """
    m = np.asarray(matrix, dtype=np.float64)
    out = verts @ m[:3, :3].T + m[:3, 3]
    if np.linalg.det(m[:3, :3]) < 0:
        faces = faces[:, ::-1].copy()
    return out, faces


def crease_normals(verts: np.ndarray, faces: np.ndarray, crease_deg: float = 31.0):
    """Split vertices across sharp edges, smooth across soft ones.

    Returns (positions, normals, faces) ready for glTF. Deterministic: faces
    are visited in index order and clusters are matched greedily against the
    first representative that is within the crease angle.
    """
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    ln = np.linalg.norm(fn, axis=1)
    area = ln * 0.5
    safe = np.where(ln > 1e-18, ln, 1.0)
    fn = fn / safe[:, None]

    incident: list[list[tuple[int, int]]] = [[] for _ in range(len(verts))]
    for fi in range(len(faces)):
        for k in range(3):
            incident[faces[fi, k]].append((fi, k))

    thresh = float(np.cos(np.deg2rad(crease_deg)))
    fnl = [tuple(map(float, n)) for n in fn]   # plain floats: no numpy call
    areal = [float(a) for a in area]           # overhead in the hot loop
    vl = [tuple(map(float, v)) for v in verts]

    out_pos: list[tuple] = []
    out_nrm: list[tuple] = []
    out_faces = np.empty_like(faces)

    for vi, items in enumerate(incident):
        reps: list[tuple] = []
        accum: list[list] = []
        slot: list[int] = []
        for fi, _k in items:
            nx, ny, nz = fnl[fi]
            w = areal[fi]
            found = -1
            for ci, (rx, ry, rz) in enumerate(reps):
                if rx * nx + ry * ny + rz * nz >= thresh:
                    found = ci
                    break
            if found < 0:
                reps.append((nx, ny, nz))
                accum.append([nx * w, ny * w, nz * w])
                found = len(reps) - 1
            else:
                acc = accum[found]
                acc[0] += nx * w
                acc[1] += ny * w
                acc[2] += nz * w
            slot.append(found)
        base = len(out_pos)
        for ci, (ax, ay, az) in enumerate(accum):
            mag = (ax * ax + ay * ay + az * az) ** 0.5
            out_pos.append(vl[vi])
            out_nrm.append(
                (ax / mag, ay / mag, az / mag) if mag > 1e-18 else reps[ci]
            )
        for (fi, k), ci in zip(items, slot):
            out_faces[fi, k] = base + ci

    return (
        np.array(out_pos, dtype=np.float32),
        np.array(out_nrm, dtype=np.float32),
        out_faces,
    )


# --------------------------------------------------------------------------
# glTF 2.0 binary writer (no external deps, no metadata)
# --------------------------------------------------------------------------


class Prim:
    def __init__(self, pos, nrm, idx, uv=None, material=None):
        self.pos = np.ascontiguousarray(pos, dtype=np.float32)
        self.nrm = np.ascontiguousarray(nrm, dtype=np.float32)
        self.idx = np.ascontiguousarray(idx, dtype=np.int64).reshape(-1)
        self.uv = None if uv is None else np.ascontiguousarray(uv, dtype=np.float32)
        self.material = material


def write_glb(path: Path, prims: list[Prim], materials=None, images=None) -> int:
    """Write one mesh (n primitives) as a .glb. Returns the byte count."""
    buf = bytearray()
    views: list[dict] = []
    accs: list[dict] = []

    def add_view(data: bytes, target: int | None) -> int:
        while len(buf) % 4:
            buf.append(0)
        off = len(buf)
        buf.extend(data)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target is not None:
            v["target"] = target
        views.append(v)
        return len(views) - 1

    def add_acc(arr, comp_type, type_str, target, minmax=False) -> int:
        vi = add_view(arr.tobytes(), target)
        a = {
            "bufferView": vi,
            "componentType": comp_type,
            "count": int(arr.shape[0]),
            "type": type_str,
        }
        if minmax:
            a["min"] = [round(float(x), 6) for x in arr.min(axis=0)]
            a["max"] = [round(float(x), 6) for x in arr.max(axis=0)]
        accs.append(a)
        return len(accs) - 1

    gl_prims = []
    for p in prims:
        attrs = {
            "POSITION": add_acc(p.pos, 5126, "VEC3", 34962, minmax=True),
            "NORMAL": add_acc(p.nrm, 5126, "VEC3", 34962),
        }
        if p.uv is not None:
            attrs["TEXCOORD_0"] = add_acc(p.uv, 5126, "VEC2", 34962)
        if int(p.pos.shape[0]) <= 65535:
            idx = p.idx.astype("<u2")
            comp = 5123
        else:
            idx = p.idx.astype("<u4")
            comp = 5125
        gp = {
            "attributes": attrs,
            "indices": add_acc(idx.reshape(-1, 1), comp, "SCALAR", 34963),
            "mode": 4,
        }
        if p.material is not None:
            gp["material"] = p.material
        gl_prims.append(gp)

    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": gl_prims}],
        "accessors": accs,
        "bufferViews": views,
        "buffers": [{"byteLength": len(buf)}],
    }
    if materials:
        gltf["materials"] = materials
    if images:
        gltf["images"] = images["images"]
        gltf["textures"] = images["textures"]
        gltf["samplers"] = images["samplers"]

    js = json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    bin_chunk = bytes(buf) + b"\x00" * ((4 - len(buf) % 4) % 4)

    total = 12 + 8 + len(js) + 8 + len(bin_chunk)
    out = bytearray()
    out += b"glTF" + struct.pack("<II", 2, total)
    out += struct.pack("<II", len(js), 0x4E4F534A) + js
    out += struct.pack("<II", len(bin_chunk), 0x004E4942) + bin_chunk

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))
    return len(out)

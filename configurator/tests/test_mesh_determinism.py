"""Same input bytes -> byte-identical meshes.

The end-to-end test runs the WHOLE mesh pipeline twice into two fresh
directories and compares sha256 per file. The unit tests below pin the
individual stages so that a regression names the stage that broke.
"""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))

import numpy as np  # noqa: E402

from common import RELEASE  # noqa: E402
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

PY = sys.executable
CAP = RELEASE / "hardware/PCBWay_keycaps_boxfit_2026-07-24/cap_dish_1u_17p5_boxfit.stl"
TRAY = RELEASE / "hardware/case/v2/stl/agentpad13_v2_tray_v5.stl"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class TestStageDeterminism(unittest.TestCase):
    def test_weld_is_stable(self):
        tris = load_stl(CAP)
        a = weld(tris)
        b = weld(tris)
        self.assertEqual(sha_arr(a), sha_arr(b))

    def test_decimate_is_stable(self):
        V, F = weld(load_stl(CAP))
        a = decimate(V, F, 3000)
        b = decimate(V, F, 3000)
        self.assertEqual(sha_arr(a), sha_arr(b))
        self.assertLessEqual(len(a[1]), 3000)

    def test_crease_normals_are_stable(self):
        V, F = weld(load_stl(CAP))
        a = crease_normals(V, F)
        b = crease_normals(V, F)
        self.assertEqual(sha_arr(a), sha_arr(b))

    def test_glb_bytes_are_stable_and_carry_no_metadata(self):
        V, F = weld(load_stl(CAP))
        pos, nrm, faces = crease_normals(V, F)
        with tempfile.TemporaryDirectory() as td:
            p1, p2 = Path(td) / "a.glb", Path(td) / "b.glb"
            write_glb(p1, [Prim(pos, nrm, faces)])
            write_glb(p2, [Prim(pos, nrm, faces)])
            self.assertEqual(sha(p1), sha(p2))
            blob = p1.read_bytes()
        self.assertEqual(blob[:4], b"glTF")
        for word in (b"generator", b"Generator", b"copyright"):
            self.assertNotIn(word, blob, f"{word!r} leaked into the glb")


class TestGeometryIsPreserved(unittest.TestCase):
    def test_decimation_keeps_volume_and_bbox(self):
        V, F = weld(load_stl(CAP))
        v0 = abs(signed_volume(V, F))
        bb0 = (V.min(0), V.max(0))
        V2, F2 = decimate(V, F, 6000)
        v1 = abs(signed_volume(V2, F2))
        self.assertLess(abs(v1 - v0) / v0, 0.05, f"{v0} -> {v1}")
        self.assertLess(float(np.max(np.abs(V2.min(0) - bb0[0]))), 0.25)
        self.assertLess(float(np.max(np.abs(V2.max(0) - bb0[1]))), 0.25)

    def test_a_reflection_reverses_winding_so_the_solid_stays_outward(self):
        """The det -1 board->glTF map must not turn parts inside out."""
        import gen_meshes

        V, F = weld(load_stl(CAP))
        self.assertGreater(signed_volume(V, F), 0)
        self.assertLess(np.linalg.det(gen_meshes.M_BOARD[:3, :3]), 0)
        V2, F2 = transform(V, F, gen_meshes.M_BOARD)
        self.assertGreater(signed_volume(V2, F2), 0)

    def test_tray_print_frame_map_is_a_proper_rotation(self):
        """The tray STL is already the real-hand part; its map must be det +1."""
        import gen_meshes

        self.assertAlmostEqual(
            float(np.linalg.det(gen_meshes.M_PRINT[:3, :3])), 1.0, places=9
        )
        V, F = weld(load_stl(TRAY))
        V2, F2 = transform(V, F, gen_meshes.M_PRINT)
        self.assertAlmostEqual(signed_volume(V2, F2), signed_volume(V, F), places=3)


class TestEndToEndDeterminism(unittest.TestCase):
    def test_two_full_runs_produce_identical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            for out in (a, b):
                r = subprocess.run(
                    [PY, str(BUILD / "gen_meshes.py"), "--out", str(out)],
                    capture_output=True, text=True,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
            fa = sorted(p.name for p in a.iterdir())
            fb = sorted(p.name for p in b.iterdir())
            self.assertEqual(fa, fb)
            self.assertGreaterEqual(len(fa), 27)  # 26 glb + 1 texture (v2: 5 topper meshes, was 7)
            diffs = [n for n in fa if sha(a / n) != sha(b / n)]
            self.assertEqual(diffs, [], f"non-deterministic outputs: {diffs}")

    def test_scene_weight_is_within_budget(self):
        meshes = BUILD / "out" / "meshes"
        if not meshes.is_dir():
            self.skipTest("meshes not built")
        total = sum(p.stat().st_size for p in meshes.iterdir())
        self.assertLess(total, 8 * 1024 * 1024, f"{total} bytes over the ~8 MiB target")


def sha_arr(arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


if __name__ == "__main__":
    unittest.main(verbosity=2)

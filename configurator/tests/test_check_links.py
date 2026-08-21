"""The link checker must pass on the real tree and fail on a doctored catalog."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))

import check_links  # noqa: E402
import gen_catalog  # noqa: E402
from common import MESH_DIR  # noqa: E402

PY = sys.executable
REAL = gen_catalog.build_catalog("x")


class TestPassesOnTheRealTree(unittest.TestCase):
    def test_every_release_path_resolves(self):
        checked, failures = check_links.check(REAL, MESH_DIR, require_meshes=False)
        self.assertEqual(failures, [])
        self.assertGreater(checked, 90)

    def test_cli_passes(self):
        meshes_built = MESH_DIR.is_dir() and any(MESH_DIR.glob("*.glb"))
        with tempfile.TemporaryDirectory() as td:
            cat = Path(td) / "catalog.json"
            r = subprocess.run(
                [PY, str(BUILD / "gen_catalog.py"), "--out", str(cat)],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            argv = [PY, str(BUILD / "check_links.py"), "--catalog", str(cat)]
            if not meshes_built:
                argv.append("--no-meshes")
            r = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("references resolve", r.stdout)


class TestFailsOnADoctoredCatalog(unittest.TestCase):
    def test_a_fabricated_path_is_reported(self):
        bad = copy.deepcopy(REAL)
        bad["tray"]["stl"] = "release/hardware/case/v2/stl/does_not_exist.stl"
        _checked, failures = check_links.check(bad, MESH_DIR, require_meshes=False)
        self.assertTrue(failures)
        self.assertTrue(any("does_not_exist.stl" in f for f in failures), failures)

    def test_cli_exits_nonzero_on_a_doctored_catalog(self):
        bad = copy.deepcopy(REAL)
        bad["keycaps"]["files"][3]["stl"] = "release/hardware/ghost_cap.stl"
        with tempfile.TemporaryDirectory() as td:
            cat = Path(td) / "catalog.json"
            cat.write_text(json.dumps(bad), encoding="utf-8")
            r = subprocess.run(
                [PY, str(BUILD / "check_links.py"),
                 "--catalog", str(cat), "--no-meshes"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("LINK CHECK FAILED", r.stderr)
        self.assertIn("ghost_cap.stl", r.stderr)

    def test_a_dropped_fixed_link_is_reported(self):
        for pointer in ("/firmware/uf2", "/firmware/flash_doc", "/bases/interface",
                        "/gasket/template_pdf"):
            with self.subTest(pointer=pointer):
                bad = copy.deepcopy(REAL)
                parts = pointer.strip("/").split("/")
                node = bad
                for token in parts[:-1]:
                    node = node[token]
                del node[parts[-1]]
                _c, failures = check_links.check(bad, MESH_DIR, require_meshes=False)
                self.assertTrue(
                    any("FIXED LINK MISSING" in f and pointer in f for f in failures),
                    f"{pointer}: {failures}",
                )

    def test_an_unbuilt_mesh_is_reported(self):
        bad = copy.deepcopy(REAL)
        bad["tray"]["mesh"] = "meshes/never_built.glb"
        _c, failures = check_links.check(bad, MESH_DIR, require_meshes=True)
        self.assertTrue(
            any("never_built.glb" in f for f in failures), failures
        )


class TestCostsStub(unittest.TestCase):
    def test_costs_is_exactly_the_empty_stub(self):
        path = BUILD / "out" / "costs.json"
        if not path.is_file():
            self.skipTest("costs.json not generated")
        data = json.loads(path.read_text())
        self.assertEqual(data, {"updated": None, "lines": {}})

    def test_no_price_like_number_is_committed(self):
        path = BUILD / "out" / "costs.json"
        if not path.is_file():
            self.skipTest("costs.json not generated")
        text = path.read_text()
        self.assertNotIn("$", text)
        self.assertFalse(any(ch.isdigit() for ch in text), text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

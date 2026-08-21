"""The manifest gate must FAIL when the catalog names a file the release lacks.

Negative controls run against DOCTORED COPIES in a temp dir. Nothing under
release/ is ever touched.
"""

import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))

import gen_catalog  # noqa: E402
from common import RELEASE, read_manifest, stated_file_count  # noqa: E402

PY = sys.executable


class TestManifestParse(unittest.TestCase):
    def test_parses_as_a_file_enumeration(self):
        entries = read_manifest()
        self.assertGreater(len(entries), 100)
        self.assertEqual(len(entries), stated_file_count())

    def test_every_manifest_row_exists_on_disk(self):
        missing = [p for p in read_manifest() if not (RELEASE / p).is_file()]
        self.assertEqual(missing, [], f"manifest rows with no file: {missing}")

    def test_retired_rows_are_excluded(self):
        # MANIFEST.md:35 marks loudest_micro_calibrate.uf2 *(retired)* and says
        # it was REMOVED FROM THIS BUNDLE. It must not reach the catalog.
        self.assertNotIn(
            "firmware/prebuilt/loudest_micro_calibrate.uf2", read_manifest()
        )


class TestGatePasses(unittest.TestCase):
    def test_cli_succeeds_on_the_real_tree(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "catalog.json"
            r = subprocess.run(
                [PY, str(BUILD / "gen_catalog.py"), "--out", str(out)],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            cat = json.loads(out.read_text())
            self.assertEqual(cat["schema"], "agentpad13-configurator-catalog-v1")
            self.assertEqual(len(cat["keycaps"]["files"]), 12)
            self.assertEqual(len(cat["bases"]["items"]), 3)
            self.assertEqual(len(cat["band"]["widths"]), 3)
            self.assertEqual(len(cat["plate"]["variants"]), 3)
            self.assertEqual(len(cat["toppers"]["knobs"]), 3)
            self.assertEqual(len(cat["toppers"]["stick_caps"]), 2)  # v2: nub_C2 + puck_TPU

    def test_keycap_counts_total_thirteen(self):
        cat = gen_catalog.build_catalog("x")
        c = cat["keycaps"]["counts"]
        self.assertEqual(c["1u"] + c["2u"] + c["2u_stab"], 13)
        w = c["with_stabilizer"]
        self.assertEqual(w["1u"] + w["2u"] + w["2u_stab"], 13)
        self.assertEqual(c["1u"], 12)
        self.assertTrue(c["source"])
        self.assertTrue(w["source"])


class TestGateFailsOnAMissingFile(unittest.TestCase):
    """NEGATIVE CONTROL -- the whole point of the gate."""

    def test_cli_fails_when_the_manifest_stops_listing_a_catalog_file(self):
        src = (RELEASE / "MANIFEST.md").read_text(encoding="utf-8")
        target = "hardware/case/v2/stl/agentpad13_v2_tray_v5.stl"
        self.assertIn(f"`{target}`", src)
        # Rename the row rather than deleting it, so the file COUNT still
        # matches and it is unambiguously the path gate that fires.
        doctored = src.replace(
            f"`{target}`", "`hardware/case/v2/stl/NOT_A_REAL_TRAY.stl`", 1
        )
        with tempfile.TemporaryDirectory() as td:
            man = Path(td) / "MANIFEST.md"
            man.write_text(doctored, encoding="utf-8")
            out = Path(td) / "catalog.json"
            r = subprocess.run(
                [PY, str(BUILD / "gen_catalog.py"),
                 "--manifest", str(man), "--out", str(out)],
                capture_output=True, text=True,
            )
        self.assertNotEqual(r.returncode, 0, "gate passed on a doctored manifest")
        self.assertIn("MANIFEST GATE FAILED", r.stderr)
        self.assertIn(target, r.stderr)
        self.assertIn("NOT LISTED", r.stderr)
        self.assertFalse(out.exists(), "a failing gate must not write a catalog")

    def test_gate_reports_a_file_that_is_listed_but_absent_on_disk(self):
        manifest = read_manifest()
        fake = "hardware/case/v2/stl/ghost_part.stl"
        manifest = dict(manifest)
        manifest[fake] = manifest["hardware/case/v2/stl/agentpad13_v2_tray_v5.stl"]
        catalog = gen_catalog.build_catalog("x")
        catalog = copy.deepcopy(catalog)
        catalog["tray"]["stl"] = f"release/{fake}"
        failures = gen_catalog.run_gate(catalog, manifest)
        self.assertTrue(failures)
        self.assertTrue(
            any("DOES NOT EXIST" in f and fake in f for f in failures), failures
        )

    def test_prose_citations_are_not_mistaken_for_paths(self):
        # /keycaps/counts/source quotes a path inside a sentence; the gate must
        # not try to open it. Guard against a regression to a naive scanner.
        catalog = gen_catalog.build_catalog("x")
        pointers = [p for p, _ in gen_catalog.iter_catalog_paths(catalog)]
        self.assertNotIn("/keycaps/counts/source", pointers)
        self.assertIn("/tray/stl", pointers)

    def test_unparseable_manifest_is_a_stop_not_an_empty_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            man = Path(td) / "MANIFEST.md"
            man.write_text("# MANIFEST\n\nno tables here at all\n", encoding="utf-8")
            r = subprocess.run(
                [PY, str(BUILD / "gen_catalog.py"), "--manifest", str(man),
                 "--out", str(Path(td) / "c.json")],
                capture_output=True, text=True,
            )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no longer enumerates", r.stderr)


class TestCatalogShape(unittest.TestCase):
    def test_every_path_is_repo_relative_under_release(self):
        catalog = gen_catalog.build_catalog("x")
        for pointer, val in gen_catalog.iter_catalog_paths(catalog):
            self.assertTrue(val.startswith("release/"), f"{pointer}: {val}")
            self.assertFalse(val.startswith("/"), pointer)
            self.assertNotIn("..", val, pointer)

    def test_mesh_refs_are_named_consistently(self):
        catalog = gen_catalog.build_catalog("x")
        cat_json = json.dumps(catalog)
        for name in re.findall(r'"(meshes/[^"]+)"', cat_json):
            self.assertTrue(
                name.endswith((".glb", ".png")), f"odd mesh reference {name}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""The round-2 catalog additions: the flash command and the plate art.

Like test_positions_sources.py, every check here re-reads the source a SECOND,
INDEPENDENT way -- the raw markdown, the raw board file, the emitted PNG's own
pixels -- rather than re-running the generator's parser and comparing it to
itself.
"""

import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"
SITE = Path(__file__).resolve().parents[1] / "site"
sys.path.insert(0, str(BUILD))

import numpy as np  # noqa: E402

import check_links  # noqa: E402
import gen_catalog  # noqa: E402
import gen_positions  # noqa: E402
import gen_textures  # noqa: E402
from common import GateError, MESH_DIR, PLATE_MARKERS, RELEASE, TEX_DIR  # noqa: E402

PY = sys.executable
BRINGUP = RELEASE / "firmware/BRING-UP.md"
CATALOG = gen_catalog.build_catalog("x")
POS = gen_positions.build()


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def png(name: str):
    """(rgb array, alpha array) of an emitted texture, or None if absent."""
    from PIL import Image

    p = TEX_DIR / name
    if not p.is_file():
        return None
    a = np.array(Image.open(p).convert("RGBA"))
    return a[..., :3], a[..., 3]


def at(alpha, x: float, y: float) -> int:
    """Sample a texture at a BOARD-frame (x, y) in mm."""
    em = CATALOG["plate"]["openings_map"]
    col = int((x - em["extent_mm"]["x0"]) * em["px_per_mm"])
    row = int((y - em["extent_mm"]["y0"]) * em["px_per_mm"])
    return int(alpha[row, col])


# ==========================================================================
# 1. catalog.firmware.flash
# ==========================================================================


class TestFlashCommand(unittest.TestCase):
    def test_it_is_the_line_the_bring_up_doc_carries(self):
        """Independent read: strip the blockquote marker off line 42."""
        lines = BRINGUP.read_text().splitlines()
        raw = [ln for ln in lines if ln.lstrip("> ").startswith("dd if=")]
        self.assertEqual(len(raw), 1, raw)
        self.assertEqual(CATALOG["firmware"]["flash"], raw[0].lstrip("> ").strip())
        self.assertEqual(
            CATALOG["firmware"]["flash"],
            "dd if=firmware/prebuilt/agentpad13.uf2 "
            "of=/Volumes/RPI-RP2/fw.uf2 bs=1m",
        )

    def test_the_cited_line_number_is_the_right_line(self):
        m = re.search(r"BRING-UP\.md line (\d+)", CATALOG["firmware"]["flash_source"])
        self.assertTrue(m, CATALOG["firmware"]["flash_source"])
        line = BRINGUP.read_text().splitlines()[int(m.group(1)) - 1]
        self.assertIn(CATALOG["firmware"]["flash"], line)

    def test_it_matches_the_constant_the_site_falls_back_to(self):
        """The key exists to retire that constant; they must agree today."""
        js = (SITE / "sheet.js").read_text()
        m = re.search(r"FLASH_FALLBACK\s*=\s*'([^']+)'", js)
        self.assertTrue(m, "sheet.js no longer defines FLASH_FALLBACK")
        self.assertEqual(CATALOG["firmware"]["flash"], m.group(1))

    def test_the_citation_cannot_be_mistaken_for_a_repo_path(self):
        """A bare `release/...:42` token would fail the manifest gate."""
        from common import _is_path_value

        self.assertFalse(_is_path_value(CATALOG["firmware"]["flash_source"]))
        self.assertFalse(_is_path_value(CATALOG["firmware"]["flash"]))
        self.assertIn("release/firmware/BRING-UP.md", CATALOG["firmware"]["flash_source"])

    def test_round_one_firmware_keys_are_untouched(self):
        self.assertEqual(CATALOG["firmware"]["uf2"],
                         "release/firmware/prebuilt/agentpad13.uf2")
        self.assertEqual(CATALOG["firmware"]["flash_doc"],
                         "release/firmware/BRING-UP.md")
        self.assertEqual(CATALOG["firmware"]["polarity_doc"],
                         "release/firmware/POLARITY-NOTE.md")


class TestFlashParseFailsLoudly(unittest.TestCase):
    """The negative controls: a doctored doc must STOP, never fall back."""

    def _doctored(self, transform) -> Path:
        td = tempfile.mkdtemp()
        p = Path(td) / "BRING-UP.md"
        p.write_text(transform(BRINGUP.read_text()), encoding="utf-8")
        return p

    def test_a_removed_command_is_a_gate_error(self):
        doc = self._doctored(
            lambda t: "\n".join(
                ln for ln in t.splitlines() if not ln.lstrip("> ").startswith("dd if=")
            )
        )
        with self.assertRaises(GateError) as ctx:
            gen_catalog.flash_command(doc)
        self.assertIn("found 0", str(ctx.exception))

    def test_a_second_command_is_a_gate_error(self):
        doc = self._doctored(
            lambda t: t.replace(
                "> dd if=", "> dd if=/dev/zero of=/Volumes/RPI-RP2/x bs=1m\n> dd if=", 1
            )
        )
        with self.assertRaises(GateError) as ctx:
            gen_catalog.flash_command(doc)
        self.assertIn("found 2", str(ctx.exception))

    def test_a_command_for_the_wrong_volume_is_a_gate_error(self):
        doc = self._doctored(lambda t: t.replace("RPI-RP2", "SOME-OTHER-DISK"))
        with self.assertRaises(GateError) as ctx:
            gen_catalog.flash_command(doc)
        self.assertIn("RPI-RP2", str(ctx.exception))

    def test_build_catalog_refuses_rather_than_emitting_a_stale_command(self):
        doc = self._doctored(
            lambda t: "\n".join(
                ln for ln in t.splitlines() if not ln.lstrip("> ").startswith("dd if=")
            )
        )
        with self.assertRaises(GateError):
            gen_catalog.build_catalog("x", doc)


# ==========================================================================
# 2. catalog.plate -- the variant keys and the shared openings map
# ==========================================================================


class TestPlateVariantKeys(unittest.TestCase):
    def test_every_variant_declares_a_marker_and_a_decal(self):
        for v in CATALOG["plate"]["variants"]:
            with self.subTest(variant=v["id"]):
                self.assertIn("marker", v)
                self.assertIn("decal", v)
                self.assertIn("marker_note", v)
                self.assertEqual((v["marker"], v["decal"]), PLATE_MARKERS[v["id"]])

    def test_the_blank_variant_is_markerless_by_contract_not_by_omission(self):
        blank = next(v for v in CATALOG["plate"]["variants"] if v["id"] == "blank")
        self.assertEqual(blank["marker"], "none")
        self.assertIsNone(blank["decal"])
        self.assertIn("MARKERLESS BY DESIGN", blank["marker_note"])
        self.assertFalse((TEX_DIR / "plate_decal_blank.png").exists(),
                         "an empty decal file was shipped for the blank plate")

    def test_catalog_markers_agree_with_positions_touch_pad(self):
        for v in CATALOG["plate"]["variants"]:
            with self.subTest(variant=v["id"]):
                self.assertEqual(v["marker"],
                                 POS["touch_pad"]["variants"][v["id"]]["marker"])

    def test_round_one_plate_keys_are_untouched(self):
        p = CATALOG["plate"]
        self.assertEqual(p["mesh"], "meshes/plate.glb")
        self.assertEqual(p["size_mm"], [84.4, 100.0])
        self.assertEqual(p["thickness_mm"], 1.6)
        self.assertEqual([v["id"] for v in p["variants"]],
                         ["standard", "tented_ring", "blank"])
        for v in p["variants"]:
            self.assertTrue(v["gerbers"].startswith("release/"))
            self.assertTrue(v["kicad_pcb"].startswith("release/"))


class TestOpeningsMapContract(unittest.TestCase):
    def test_the_declared_frame_matches_the_plate_the_case_model_defines(self):
        em = CATALOG["plate"]["openings_map"]
        w = em["extent_mm"]["x1"] - em["extent_mm"]["x0"]
        h = em["extent_mm"]["y1"] - em["extent_mm"]["y0"]
        self.assertAlmostEqual(w, CATALOG["plate"]["size_mm"][0], places=6)
        self.assertAlmostEqual(h, CATALOG["plate"]["size_mm"][1], places=6)
        self.assertEqual(em["size_px"],
                         [round(w * em["px_per_mm"]), round(h * em["px_per_mm"])])

    def test_the_declared_size_matches_the_file_actually_emitted(self):
        got = png("plate_openings.png")
        if got is None:
            self.skipTest("textures not built")
        _rgb, alpha = got
        self.assertEqual(list(alpha.shape[::-1]),
                         CATALOG["plate"]["openings_map"]["size_px"])

    def test_the_frame_is_centred_on_the_case_datum(self):
        em = CATALOG["plate"]["openings_map"]["extent_mm"]
        self.assertAlmostEqual((em["x0"] + em["x1"]) / 2, 42.1, places=6)
        self.assertAlmostEqual((em["y0"] + em["y1"]) / 2, 50.0, places=6)


# ==========================================================================
# 3. the emitted pixels
# ==========================================================================


class TestTextureContent(unittest.TestCase):
    def setUp(self):
        self.op = png("plate_openings.png")
        if self.op is None:
            self.skipTest("textures not built -- run gen_textures.py")

    def test_the_openings_map_carries_no_ground_colour(self):
        """The plate colour is the OWNER'S choice; it must not be baked in."""
        rgb, _a = self.op
        self.assertEqual(np.unique(rgb).tolist(), [255])

    def test_every_routed_opening_reads_transparent(self):
        _rgb, a = self.op
        for name, (x, y) in [
            ("screw NW", (3.7, 3.7)),
            ("screw NE", (80.5, 3.7)),
            ("screw SW", (3.7, 96.3)),
            ("screw SE", (80.5, 96.3)),
            ("LED14 hole", (13.525, 79.35)),
            ("encoder opening", (14.025, 12.5)),
            ("joystick opening", (68.135, 11.795)),
            ("stab slot L", (30.162, 89.47)),
            ("stab slot R", (54.038, 89.47)),
        ]:
            with self.subTest(feature=name):
                self.assertEqual(at(a, x, y), 0)
        for sw in POS["switches"]:
            with self.subTest(feature=sw["ref"]):
                self.assertEqual(at(a, sw["x"], sw["y"]), 0)

    def test_the_plate_is_solid_where_it_should_be(self):
        _rgb, a = self.op
        for name, (x, y) in [
            ("TP5 touch pad (a pad, not a hole)", (13.525, 88.85)),
            ("web between switch rows", (42.1, 41.225)),
            ("plate centre of the left margin", (1.5, 50.0)),
        ]:
            with self.subTest(feature=name):
                self.assertEqual(at(a, x, y), 255)

    def test_it_is_not_mirrored_or_flipped(self):
        """LED14's two mirror images land on solid plate; the hole does not."""
        _rgb, a = self.op
        self.assertEqual(at(a, 13.525, 79.35), 0)          # the real hole
        self.assertEqual(at(a, 2 * 42.1 - 13.525, 79.35), 255)   # mirrored in x
        self.assertEqual(at(a, 13.525, 2 * 50.0 - 79.35), 255)   # mirrored in y

    def test_the_standard_decal_is_a_filled_gold_disc_over_tp5(self):
        got = png("plate_decal_standard.png")
        self.assertIsNotNone(got)
        rgb, a = got
        self.assertEqual(
            [tuple(v) for v in np.unique(rgb.reshape(-1, 3), axis=0)],
            [gen_textures.ENIG_GOLD_RGB],
        )
        self.assertEqual(at(a, 13.525, 88.85), 255)           # centre filled
        self.assertEqual(at(a, 13.525 + 5.5, 88.85), 255)     # inside Ø12
        self.assertEqual(at(a, 13.525 + 6.5, 88.85), 0)       # outside Ø12
        self.assertEqual(at(a, 42.1, 50.0), 0)                # nothing elsewhere

    def test_the_tented_ring_decal_is_a_hollow_white_ring_over_tp5(self):
        got = png("plate_decal_tented_ring.png")
        self.assertIsNotNone(got)
        rgb, a = got
        self.assertEqual(
            [tuple(v) for v in np.unique(rgb.reshape(-1, 3), axis=0)],
            [gen_textures.SILK_WHITE_RGB],
        )
        self.assertEqual(at(a, 13.525, 88.85), 0)             # HOLLOW centre
        self.assertGreater(at(a, 13.525 + 8.0, 88.85), 200)   # on the Ø16 stroke
        self.assertEqual(at(a, 13.525 + 6.0, 88.85), 0)       # inside the ring
        self.assertEqual(at(a, 42.1, 50.0), 0)

    def test_the_two_decals_differ(self):
        self.assertNotEqual(sha(TEX_DIR / "plate_decal_standard.png"),
                            sha(TEX_DIR / "plate_decal_tented_ring.png"))

    def test_the_textures_are_light(self):
        total = sum(p.stat().st_size for p in TEX_DIR.iterdir())
        self.assertLess(total, 512 * 1024, f"{total} bytes of plate art")


# ==========================================================================
# 4. determinism
# ==========================================================================


class TestTextureDeterminism(unittest.TestCase):
    def test_two_full_runs_produce_identical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            for out in (a, b):
                r = subprocess.run(
                    [PY, str(BUILD / "gen_textures.py"), "--out", str(out)],
                    capture_output=True, text=True,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
            fa = sorted(p.name for p in a.iterdir())
            fb = sorted(p.name for p in b.iterdir())
            self.assertEqual(fa, fb)
            self.assertEqual(
                fa,
                ["plate_decal_standard.png", "plate_decal_tented_ring.png",
                 "plate_openings.png"],
            )
            diffs = [n for n in fa if sha(a / n) != sha(b / n)]
            self.assertEqual(diffs, [], f"non-deterministic textures: {diffs}")

    def test_the_committed_textures_are_what_the_generator_produces(self):
        if not TEX_DIR.is_dir():
            self.skipTest("textures not built")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "fresh"
            r = subprocess.run(
                [PY, str(BUILD / "gen_textures.py"), "--out", str(out)],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            for p in out.iterdir():
                with self.subTest(texture=p.name):
                    self.assertEqual(sha(p), sha(TEX_DIR / p.name))

    def test_no_timestamp_or_generator_string_leaks_into_a_png(self):
        for p in sorted(TEX_DIR.glob("*.png")):
            blob = p.read_bytes()
            with self.subTest(texture=p.name):
                self.assertEqual(blob[1:4], b"PNG")
                for chunk in (b"tIME", b"tEXt", b"iTXt", b"zTXt"):
                    self.assertNotIn(chunk, blob, f"{chunk!r} in {p.name}")


# ==========================================================================
# 5. the link gate covers the new assets
# ==========================================================================


class TestCheckLinksCoversTextures(unittest.TestCase):
    def test_it_passes_on_the_real_tree(self):
        if not TEX_DIR.is_dir():
            self.skipTest("textures not built")
        checked, failures = check_links.check(CATALOG, MESH_DIR, True, TEX_DIR)
        self.assertEqual(failures, [])
        self.assertGreater(checked, 120)

    def test_an_unbuilt_texture_is_reported(self):
        import copy

        bad = copy.deepcopy(CATALOG)
        bad["plate"]["variants"][0]["decal"] = "textures/never_built.png"
        _c, failures = check_links.check(bad, MESH_DIR, True, TEX_DIR)
        self.assertTrue(any("never_built.png" in f for f in failures), failures)

    def test_a_dropped_decal_key_is_reported(self):
        """Null means markerless; MISSING means the site cannot tell."""
        import copy

        bad = copy.deepcopy(CATALOG)
        del bad["plate"]["variants"][2]["decal"]
        _c, failures = check_links.check(bad, MESH_DIR, True, TEX_DIR)
        self.assertTrue(any("no `decal` key" in f for f in failures), failures)

    def test_a_dropped_openings_map_is_reported(self):
        import copy

        bad = copy.deepcopy(CATALOG)
        del bad["plate"]["openings_map"]
        _c, failures = check_links.check(bad, MESH_DIR, True, TEX_DIR)
        self.assertTrue(
            any("openings_map" in f for f in failures), failures
        )

    def test_a_null_decal_is_accepted(self):
        import copy

        bad = copy.deepcopy(CATALOG)
        bad["plate"]["variants"][0]["decal"] = None
        _c, failures = check_links.check(bad, MESH_DIR, True, TEX_DIR)
        self.assertEqual(failures, [])


# ==========================================================================
# 6. the texture gates themselves
# ==========================================================================


class TestTextureGates(unittest.TestCase):
    def test_all_three_boards_really_do_share_one_edge_cuts_profile(self):
        """Independent of gen_textures: compare the raw Edge.Cuts text."""
        sets = {}
        for vid, rel in (
            ("standard", "agentpad13_v2_plate_v5.kicad_pcb"),
            ("tented_ring", "agentpad13_v2_plate_tented_ring_v5.kicad_pcb"),
            ("blank", "agentpad13_v2_plate_blank_v5.kicad_pcb"),
        ):
            txt = (RELEASE / "hardware/case/v2/fab" / rel).read_text()
            rows = [
                re.sub(r' \(uuid "[^"]+"\)', "", ln).strip()
                for ln in txt.splitlines()
                if '(layer "Edge.Cuts")' in ln
            ]
            sets[vid] = sorted(rows)
        self.assertEqual(len(sets["standard"]), 89)
        self.assertEqual(sets["standard"], sets["tented_ring"])
        self.assertEqual(sets["standard"], sets["blank"])

    def test_the_census_gate_fires_on_a_missing_cutout(self):
        loops = gen_textures.edge_loops(
            gen_textures.read_pcb_shapes(gen_textures.PLATE_BOARDS["standard"])
        )
        self.assertEqual(len(loops), 23)
        gen_textures.gate_census(loops)               # the real board passes
        with self.assertRaises(GateError) as ctx:
            gen_textures.gate_census(loops[:-1])      # one opening removed
        self.assertIn("census changed", str(ctx.exception))

    def test_an_open_contour_is_refused_rather_than_flood_filled(self):
        with self.assertRaises(GateError) as ctx:
            gen_textures.assemble_loops(
                [[(0.0, 0.0), (1.0, 0.0)], [(1.0, 0.0), (1.0, 1.0)]]
            )
        self.assertIn("open Edge.Cuts contour", str(ctx.exception))

    def test_the_marker_gate_fires_when_a_variant_lies(self):
        boards = {
            vid: gen_textures.read_pcb_shapes(p)
            for vid, p in gen_textures.PLATE_BOARDS.items()
        }
        self.assertEqual(
            {k: v[0] for k, v in gen_textures.gate_markers(boards).items()},
            {"standard": "exposed_pad", "tented_ring": "silk_ring", "blank": "none"},
        )
        swapped = dict(boards)
        swapped["blank"] = boards["standard"]
        with self.assertRaises(GateError) as ctx:
            gen_textures.gate_markers(swapped)
        self.assertIn("PLATE_MARKERS", str(ctx.exception))

    def test_the_identity_gate_fires_when_a_profile_diverges(self):
        boards = {
            vid: gen_textures.read_pcb_shapes(p)
            for vid, p in gen_textures.PLATE_BOARDS.items()
        }
        gen_textures.gate_identity(boards)            # the real boards pass
        import copy

        bad = {k: copy.deepcopy(v) for k, v in boards.items()}
        bad["blank"]["circles"] = [
            c for c in bad["blank"]["circles"] if c["layer"] != "Edge.Cuts"
        ]
        with self.assertRaises(GateError) as ctx:
            gen_textures.gate_identity(bad)
        self.assertIn("do NOT share an", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)

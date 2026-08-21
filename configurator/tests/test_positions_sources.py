"""Every published position must match the source it cites.

These checks deliberately re-read the sources a SECOND, INDEPENDENT way --
regex over the raw text, the shipped STL/STEP geometry, and the markdown table
in HOW-TO-ORDER.md -- rather than re-running the generator's own AST reader.
A value that only agrees with itself has not been verified.
"""

import json
import math
import re
import struct
import sys
import unittest
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD))

import gen_positions  # noqa: E402
from common import RELEASE, REPO_ROOT  # noqa: E402

CASE_PY = (RELEASE / "hardware/case/v2/agentpad13_case_v2.py").read_text()
BASE_PY = (RELEASE / "hardware/case/v2/bases/agentpad13_base.py").read_text()
KEYCAPS_PY = (REPO_ROOT / "hardware/case/keycaps/keycaps.py").read_text()
HOW_TO_ORDER = (RELEASE / "HOW-TO-ORDER.md").read_text()
NOTES = (REPO_ROOT / "hardware/case/CASE-V2-NOTES.md").read_text()
PLATE_FAB_PY = (REPO_ROOT / "hardware/case/gen_plate_fab.py").read_text()
BASE_PARAMS = json.loads(
    (RELEASE / "hardware/case/v2/bases/params/agentpad13_base_params.json").read_text()
)
CONTRACT = json.loads(
    (RELEASE / "hardware/pcb/harness/contract_v4.json").read_text()
)
POS = gen_positions.build()

PLATE_BOARDS = {
    "standard": "hardware/case/v2/fab/agentpad13_v2_plate_v5.kicad_pcb",
    "tented_ring": "hardware/case/v2/fab/agentpad13_v2_plate_tented_ring_v5.kicad_pcb",
    "blank": "hardware/case/v2/fab/agentpad13_v2_plate_blank_v5.kicad_pcb",
}


def const(text: str, name: str) -> float:
    m = re.search(rf"^{re.escape(name)}\s*=\s*(-?[\d.]+)", text, re.M)
    assert m, f"{name} not found"
    return float(m.group(1))


# --- an INDEPENDENT reader for the ordered plate boards --------------------
# Deliberately not common.read_pcb_shapes(): a value that only agrees with the
# generator's own parser has not been verified. These patterns spell out the
# stroke/type/fill structure that common.py skips over with `.*?`.
_T_CIRCLE = re.compile(
    r'\(gr_circle \(center (-?[\d.]+) (-?[\d.]+)\) \(end (-?[\d.]+) (-?[\d.]+)\) '
    r'\(stroke \(width ([\d.]+)\) \(type \w+\)\) \(fill (\w+)\) \(layer "([^"]+)"\)'
)
_T_LINE = re.compile(
    r'\(gr_line \(start (-?[\d.]+) (-?[\d.]+)\) \(end (-?[\d.]+) (-?[\d.]+)\) '
    r'\(stroke \(width ([\d.]+)\) \(type \w+\)\) \(layer "([^"]+)"\)'
)


def board_circles(rel: str) -> list[dict]:
    txt = (RELEASE / rel).read_text()
    out = []
    for m in _T_CIRCLE.finditer(txt):
        cx, cy, ex, ey = (float(m.group(i)) for i in (1, 2, 3, 4))
        out.append(
            {
                "c": (cx, cy),
                "d": 2.0 * math.hypot(ex - cx, ey - cy),
                "w": float(m.group(5)),
                "fill": m.group(6) == "yes",
                "layer": m.group(7),
            }
        )
    assert out, f"{rel}: no circles parsed"
    return out


def board_edge_lines(rel: str) -> list[tuple]:
    txt = (RELEASE / rel).read_text()
    return [
        tuple(float(m.group(i)) for i in (1, 2, 3, 4))
        for m in _T_LINE.finditer(txt)
        if m.group(6) == "Edge.Cuts"
    ]


def axis_rects(segs: list[tuple], w: float, h: float) -> list[tuple]:
    """Centres of every axis-aligned `w` x `h` rectangle in `segs`."""
    verticals = {}
    for (x1, y1, x2, y2) in segs:
        if abs(x1 - x2) < 1e-9 and abs(abs(y1 - y2) - h) < 1e-6:
            verticals.setdefault(round(min(y1, y2), 4), set()).add(round(x1, 4))
    out = []
    for y_top, xs in verticals.items():
        for x in sorted(xs):
            if round(x + w, 4) in xs:
                out.append((round(x + w / 2, 4), round(y_top + h / 2, 4)))
    return sorted(out)


def stl_bbox(rel: str):
    d = (RELEASE / rel).read_bytes()
    n = struct.unpack("<I", d[80:84])[0]
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for i in range(n):
        o = 84 + 50 * i + 12
        for k in range(3):
            for j, v in enumerate(struct.unpack("<3f", d[o + 12 * k: o + 12 * k + 12])):
                lo[j] = min(lo[j], v)
                hi[j] = max(hi[j], v)
    return lo, hi


class TestFrameAndDeck(unittest.TestCase):
    def test_deck_z_matches_plate_top_to_pcb(self):
        self.assertEqual(POS["deck_z"], const(CASE_PY, "PLATE_TOP_TO_PCB"))
        self.assertEqual(POS["deck_z"], 5.0)

    def test_plate_span_is_derived_not_copied_from_the_stale_comment(self):
        top = const(CASE_PY, "PLATE_TOP_TO_PCB")
        thick = const(CASE_PY, "PLATE_T")
        self.assertEqual(POS["plate"]["z1"], top)
        self.assertAlmostEqual(POS["plate"]["z0"], top - thick, places=9)
        # The source line carries a stale "# +3.5" comment from when PLATE_T
        # was 1.5. Assert we published the EVALUATED 3.4, not the comment.
        line = [ln for ln in CASE_PY.splitlines() if ln.startswith("Z_PLATE_BOT")][0]
        self.assertIn("+3.5", line, "the stale comment moved; re-check this test")
        self.assertAlmostEqual(POS["plate"]["z0"], 3.4, places=9)

    def test_plate_span_matches_the_shipped_step(self):
        """Strongest cross-check: the ORDERED artifact's own geometry."""
        try:
            from build123d import import_step
        except ImportError:  # pragma: no cover
            self.skipTest("build123d not installed")
        bb = import_step(
            str(RELEASE / "hardware/case/v2/step/agentpad13_v2_plate.step")
        ).bounding_box()
        self.assertAlmostEqual(bb.min.Z, POS["plate"]["z0"], places=6)
        self.assertAlmostEqual(bb.max.Z, POS["plate"]["z1"], places=6)
        self.assertAlmostEqual(bb.max.X - bb.min.X, POS["plate"]["size"][0], places=3)
        self.assertAlmostEqual(bb.max.Y - bb.min.Y, POS["plate"]["size"][1], places=3)

    def test_frame_is_declared_left_handed_with_the_det_minus_one_map(self):
        f = POS["frame"]
        self.assertEqual(f["handedness"], "left")
        m = f["to_gltf"]["matrix_column_major"]
        lin = [[m[0], m[4], m[8]], [m[1], m[5], m[9]], [m[2], m[6], m[10]]]
        det = (
            lin[0][0] * (lin[1][1] * lin[2][2] - lin[1][2] * lin[2][1])
            - lin[0][1] * (lin[1][0] * lin[2][2] - lin[1][2] * lin[2][0])
            + lin[0][2] * (lin[1][0] * lin[2][1] - lin[1][1] * lin[2][0])
        )
        self.assertAlmostEqual(det, -1.0, places=9)
        self.assertIn("LEFT-handed", CASE_PY.splitlines()[1199])


class TestSwitchesAndControls(unittest.TestCase):
    def test_switches_match_the_contract_exactly(self):
        self.assertEqual(len(POS["switches"]), 13)
        for sw in POS["switches"]:
            ref = CONTRACT["refs"][sw["ref"]]
            self.assertEqual(sw["x"], ref["x"])
            self.assertEqual(sw["y"], ref["y"])
        sizes = [s["size"] for s in POS["switches"]]
        self.assertEqual(sizes, ["1u"] * 12 + ["2u"])
        self.assertEqual(POS["switches"][12]["ref"], "SW13")

    def test_grid_is_the_19_05_pitch_it_should_be(self):
        xs = sorted({s["x"] for s in POS["switches"][:12]})
        ys = sorted({s["y"] for s in POS["switches"][:12]})
        for a, b in zip(xs, xs[1:]):
            self.assertAlmostEqual(b - a, 19.05, places=6)
        for a, b in zip(ys, ys[1:]):
            self.assertAlmostEqual(b - a, 19.05, places=6)

    def test_encoder_is_the_shaft_not_the_footprint_anchor(self):
        re1 = CONTRACT["refs"]["RE1"]
        m = re.search(r"EC11_ANCHOR_TO_SHAFT\s*=\s*\(([\d.]+),\s*([\d.]+)\)", CASE_PY)
        dx, dy = float(m.group(1)), float(m.group(2))
        self.assertAlmostEqual(POS["encoder"]["x"], re1["x"] + dx, places=9)
        self.assertAlmostEqual(POS["encoder"]["y"], re1["y"] + dy, places=9)
        self.assertEqual((POS["encoder"]["x"], POS["encoder"]["y"]), (13.525, 12.5))
        self.assertNotEqual(POS["encoder"]["x"], re1["x"])

    def test_encoder_matches_the_ordered_plate_opening(self):
        # CASE-V2-NOTES.md validate_fab_v5 output:
        #   "[encoder] center (13.525,12.500) size 13.000x13.000  UNCHANGED"
        notes = (REPO_ROOT / "hardware/case/CASE-V2-NOTES.md").read_text()
        self.assertIn("[encoder] center (13.525,12.500)", notes)

    def test_stick_matches_the_contract(self):
        js1 = CONTRACT["refs"]["JS1"]
        self.assertEqual(POS["stick"], {"x": js1["x"], "y": js1["y"]})
        self.assertEqual((js1["x"], js1["y"]), (69.71, 13.37))

    def test_stabilizer_slots_match_the_fab_gate_output(self):
        notes = (REPO_ROOT / "hardware/case/CASE-V2-NOTES.md").read_text()
        self.assertIn("stab L (30.162,89.47) / R (54.038,89.47)", notes)
        left, right = POS["stabilizer"]["slot_centers"]
        self.assertAlmostEqual(left[0], 30.162, places=3)
        self.assertAlmostEqual(left[1], 89.47, places=3)
        self.assertAlmostEqual(right[0], 54.038, places=3)
        self.assertAlmostEqual(right[1], 89.47, places=3)


class TestKeycapSeat(unittest.TestCase):
    def test_seat_is_deck_plus_stem_shoulder(self):
        deck = const(CASE_PY, "PLATE_TOP_TO_PCB")
        shoulder = const(KEYCAPS_PY, "SW_SHOULDER_H")
        recess = const(KEYCAPS_PY, "MOUNT_RECESS")
        self.assertEqual(recess, 0.0)
        self.assertAlmostEqual(POS["keycap_seat_z"], deck + shoulder - recess, places=9)
        self.assertAlmostEqual(POS["keycap_seat_z"], 11.6, places=9)

    def test_the_mx_datum_chain_says_11_6(self):
        # keycaps.py:152 -- '11.6   PCB top -> the "11.6" datum == 6.60 above the deck'
        self.assertIn('11.6   PCB top -> the "11.6" datum', KEYCAPS_PY)
        self.assertIn("it is the STEM'S SHOULDER", KEYCAPS_PY)

    def test_cap_stl_local_origin_is_its_bottom_rim(self):
        lo, hi = stl_bbox(
            "hardware/PCBWay_keycaps_boxfit_2026-07-24/cap_dish_1u_17p5_boxfit.stl"
        )
        self.assertAlmostEqual(lo[2], 0.0, places=4)
        self.assertAlmostEqual(hi[0] - lo[0], 17.5, places=3)
        self.assertAlmostEqual(hi[1] - lo[1], 17.5, places=3)


class TestCaseParts(unittest.TestCase):
    def test_tray_z_matches_the_shipped_tray_stl(self):
        lo, hi = stl_bbox("hardware/case/v2/stl/agentpad13_v2_tray_v5.stl")
        self.assertAlmostEqual(POS["tray"]["z0"], lo[2], places=4)
        self.assertAlmostEqual(POS["tray"]["z0"], -9.5, places=9)

    def test_band_z_matches_the_shipped_band_stl(self):
        lo, hi = stl_bbox("hardware/case/v2/stl/agentpad13_v2_band_1.6mm_w5.4.stl")
        self.assertAlmostEqual(POS["band"]["z0"], lo[2], places=4)
        self.assertAlmostEqual(POS["band"]["z1"], hi[2], places=4)

    def test_band_outer_sizes_match_the_how_to_order_table(self):
        """HOW-TO-ORDER.md publishes the outer size of all three bands."""
        # The default row carries bold markup around every cell, so cells are
        # matched as "anything but a pipe" rather than by exact spacing.
        table = dict(
            re.findall(
                r"`…_(w[\d.]+)\.stl`[^|]*\|[^|]*\|[^0-9|]*([\d.]+ × [\d.]+) mm",
                HOW_TO_ORDER,
            )
        )
        self.assertEqual(len(table), 3, f"table not parsed: {table}")
        for wid, size in table.items():
            want = [float(v) for v in size.split(" × ")]
            got = POS["band"]["widths"][wid]["outer"]
            self.assertAlmostEqual(got[0], want[0], places=6, msg=wid)
            self.assertAlmostEqual(got[1], want[1], places=6, msg=wid)

    def test_band_outer_matches_each_bands_own_stl(self):
        for wid in ("w3.0", "w5.4", "w7.4"):
            lo, hi = stl_bbox(f"hardware/case/v2/stl/agentpad13_v2_band_1.6mm_{wid}.stl")
            want = POS["band"]["widths"][wid]["outer"]
            self.assertAlmostEqual(hi[0] - lo[0], want[0], places=3, msg=wid)
            self.assertAlmostEqual(hi[1] - lo[1], want[1], places=3, msg=wid)

    def test_base_peg_top_matches_the_shipped_base_stls(self):
        for item in ("riser", "wedge", "pedestal"):
            lo, hi = stl_bbox(f"hardware/case/v2/bases/stl/base_{item}_peg_5p8.stl")
            self.assertAlmostEqual(POS["base"]["peg_top_z"], hi[2], places=4, msg=item)
        self.assertAlmostEqual(POS["base"]["peg_top_z"], -8.1, places=9)

    def test_pcb_sits_with_its_top_face_at_z_zero(self):
        self.assertEqual(POS["pcb"]["z1"], 0.0)
        self.assertAlmostEqual(POS["pcb"]["z0"], -const(CASE_PY, "PCB_T_DESIGN"), places=9)
        self.assertEqual(POS["pcb"]["outline_mm"], CONTRACT["outline"]["target_mm"])
        self.assertEqual(len(POS["pcb"]["octagon"]), 8)


class TestScrews(unittest.TestCase):
    """The four M3 corner screws the plate shows."""

    def test_positions_match_every_ordered_plate_board(self):
        for vid, rel in PLATE_BOARDS.items():
            with self.subTest(variant=vid):
                holes = sorted(
                    (round(c["c"][0], 4), round(c["c"][1], 4))
                    for c in board_circles(rel)
                    if c["layer"] == "Edge.Cuts" and abs(c["d"] - 3.2) < 5e-4
                )
                self.assertEqual(len(holes), 4, holes)
                self.assertEqual(
                    holes, [(3.7, 3.7), (3.7, 96.3), (80.5, 3.7), (80.5, 96.3)]
                )
                self.assertEqual(
                    [tuple(p) for p in POS["screws"]["positions"]], holes
                )

    def test_hole_diameter_is_the_iso_273_close_fit(self):
        self.assertEqual(POS["screws"]["hole_d"], const(CASE_PY, "M3_SCREW_CLEAR"))
        self.assertEqual(POS["screws"]["hole_d"], 3.2)

    def test_positions_are_the_corner_bosses_inset_by_boss_c(self):
        c = const(CASE_PY, "BOSS_C")
        w, h = CONTRACT["outline"]["target_mm"]
        self.assertEqual(
            sorted(tuple(p) for p in POS["screws"]["positions"]),
            sorted([(c, c), (w - c, c), (c, h - c), (w - c, h - c)]),
        )

    def test_head_is_a_button_head_not_a_socket_head_cap(self):
        """The site asked for socket heads; the case model says button."""
        self.assertEqual(POS["screws"]["head_d"], const(CASE_PY, "M3_HEAD_D"))
        self.assertEqual(POS["screws"]["head_h"], const(CASE_PY, "M3_HEAD_H"))
        self.assertEqual((POS["screws"]["head_d"], POS["screws"]["head_h"]),
                         (5.7, 1.8))
        self.assertIn("BUTTON head", POS["screws"]["fastener"])
        self.assertIn("ISO 7380", CASE_PY.splitlines()[601])   # M3_HEAD_D line
        self.assertIn("button heads sit PROUD on the deck", CASE_PY)

    def test_head_stands_proud_of_the_plate(self):
        z = POS["screws"]["z"]
        self.assertEqual(z["seat"], POS["plate"]["z1"])
        self.assertAlmostEqual(z["head_top"], z["seat"] + POS["screws"]["head_h"], 9)
        self.assertAlmostEqual(
            z["tip"], z["seat"] - POS["screws"]["length_mm"], places=9
        )
        self.assertEqual((z["head_top"], z["tip"]), (6.8, -3.0))

    def test_the_fab_gate_readback_agrees(self):
        # CASE-V2-NOTES.md:714, validate_fab_v5's own output.
        self.assertIn("screw holes Ø3.2 @ (3.7,3.7) and (80.5,3.7) present", NOTES)


class TestStabSlots(unittest.TestCase):
    def test_slots_match_the_rectangles_the_ordered_plate_cuts(self):
        for vid, rel in PLATE_BOARDS.items():
            with self.subTest(variant=vid):
                centres = axis_rects(board_edge_lines(rel), 6.65, 12.3)
                self.assertEqual(centres, [(30.162, 89.47), (54.038, 89.47)])
                self.assertEqual(
                    [tuple(round(v, 4) for v in s["center"]) for s in POS["stab"]["slots"]],
                    centres,
                )

    def test_slot_size_is_the_cherry_envelope(self):
        m = re.search(r"^STAB_W, STAB_H = ([\d.]+), ([\d.]+)", CASE_PY, re.M)
        self.assertEqual(POS["stab"]["slot_size"], [float(m[1]), float(m[2])])
        self.assertEqual(POS["stab"]["slot_size"], [6.65, 12.3])
        for slot in POS["stab"]["slots"]:
            self.assertEqual(slot["size"], [6.65, 12.3])

    def test_the_fab_gate_readback_agrees(self):
        self.assertIn(
            "stab L (30.162,89.47) / R (54.038,89.47) 6.65x12.3", NOTES
        )

    def test_stab_and_stabilizer_cannot_disagree(self):
        """Both keys are published; they are one computation, so they match."""
        self.assertEqual(POS["stab"]["slots"], POS["stabilizer"]["slots"])
        self.assertEqual(POS["stab"]["slot_size"], POS["stabilizer"]["slot_size"])
        self.assertEqual(
            [s["center"] for s in POS["stab"]["slots"]],
            POS["stabilizer"]["slot_centers"],
        )
        self.assertEqual(POS["stab"]["switch"],
                         [POS["stabilizer"]["x"], POS["stabilizer"]["y"]])


class TestTouchPad(unittest.TestCase):
    def test_centre_is_the_contract_ref(self):
        tp5 = CONTRACT["refs"]["TP5"]
        self.assertEqual((POS["touch_pad"]["x"], POS["touch_pad"]["y"]),
                         (tp5["x"], tp5["y"]))
        self.assertEqual((tp5["x"], tp5["y"]), (13.525, 88.85))
        self.assertIn("TP5 = _REFS[", CASE_PY.splitlines()[378])

    def test_every_diameter_is_measured_off_the_ordered_boards(self):
        want = {
            "standard": {"F.Cu": 14.0, "B.Cu": 14.0, "B.Mask": 8.0, "F.Mask": 12.0},
            "tented_ring": {"F.Cu": 14.0, "B.Cu": 14.0, "B.Mask": 8.0, "F.SilkS": 16.0},
            "blank": {},
        }
        for vid, rel in PLATE_BOARDS.items():
            with self.subTest(variant=vid):
                got = {
                    c["layer"]: round(c["d"], 4)
                    for c in board_circles(rel)
                    if c["c"] == (13.525, 88.85)
                }
                self.assertEqual(got, want[vid])

        tp = POS["touch_pad"]
        self.assertEqual(tp["pad_d"], 14.0)
        self.assertEqual(tp["back_pad_d"], 14.0)
        self.assertEqual(tp["back_mask_open_d"], 8.0)
        self.assertEqual(tp["exposed_pad_d"], 12.0)
        self.assertEqual(tp["ring_d"], 16.0)

    def test_each_variant_carries_exactly_one_marker(self):
        v = POS["touch_pad"]["variants"]
        self.assertEqual(v["standard"]["marker"], "exposed_pad")
        self.assertEqual(v["standard"]["exposed_d"], 12.0)
        self.assertIsNone(v["standard"]["ring_d"])
        self.assertEqual(v["tented_ring"]["marker"], "silk_ring")
        self.assertEqual((v["tented_ring"]["ring_d"], v["tented_ring"]["ring_stroke"]),
                         (16.0, 0.2))
        self.assertIsNone(v["tented_ring"]["exposed_d"])
        self.assertEqual(v["blank"]["marker"], "none")
        self.assertFalse(v["blank"]["electrode"])

    def test_the_blank_plate_really_carries_no_copper_at_all(self):
        layers = {c["layer"] for c in board_circles(PLATE_BOARDS["blank"])}
        self.assertEqual(layers, {"Edge.Cuts"})

    def test_ring_diameter_is_the_generators_tented_ring_constant(self):
        self.assertEqual(POS["touch_pad"]["ring_d"],
                         const(PLATE_FAB_PY, "TENTED_RING_D"))

    def test_the_published_ring_is_the_16_the_notes_describe(self):
        self.assertIn("Ø14 F.Cu pad, Ø12 F.Mask opening", NOTES)
        self.assertIn("Ø14 B.Cu landing pad with Ø8 B.Mask opening", NOTES)

    def test_the_stale_generator_docstring_is_cited_accurately(self):
        """The Ø10 in gen_plate_fab's docstring is a DOC BUG we record."""
        line = PLATE_FAB_PY.splitlines()[135]        # gen_plate_fab.py:136
        self.assertIn("Ø10 bottom landing pad", line)
        self.assertIn('filled_circle(cx, cy, 7.0, "B.Cu")',
                      PLATE_FAB_PY.splitlines()[139])  # :140 -- the real Ø14
        self.assertIn("Ø10 bottom landing", POS["sources"]["touch_pad"])
        self.assertIn("DOC BUG", POS["sources"]["touch_pad"])

    def test_board_side_pour_is_the_14x14_the_pcb_docs_record(self):
        dd = (REPO_ROOT / "hardware/pcb/DESIGN-DECISIONS.md").read_text()
        self.assertIn("14×14 mm touch pour", dd)
        self.assertEqual(POS["touch_pad"]["board_pour_mm"], [14.0, 14.0])


class TestBases(unittest.TestCase):
    def test_tilt_matches_the_shipped_params_file(self):
        for vid, item in POS["bases"]["items"].items():
            with self.subTest(base=vid):
                self.assertEqual(item["tilt_deg"],
                                 BASE_PARAMS["variants"][vid]["tilt_deg"])
        self.assertEqual(POS["base"]["tilt_deg"],
                         {"riser": 0.0, "wedge": 8.0, "pedestal": 8.0})

    def test_tilt_is_the_one_wedge_constant(self):
        deg = const(BASE_PY, "WEDGE_DEG")
        self.assertEqual(deg, 8.0)
        self.assertEqual(POS["bases"]["items"]["wedge"]["tilt_deg"], deg)
        self.assertEqual(POS["bases"]["items"]["pedestal"]["tilt_deg"], deg)
        self.assertEqual(POS["bases"]["items"]["riser"]["tilt_deg"], 0.0)

    def test_base_tilt_deg_map_and_bases_block_cannot_disagree(self):
        self.assertEqual(
            POS["base"]["tilt_deg"],
            {k: v["tilt_deg"] for k, v in POS["bases"]["items"].items()},
        )

    def test_desk_plane_reproduces_each_shipped_base_stl(self):
        """The strongest check: the printed part's own lowest point."""
        for vid, item in POS["bases"]["items"].items():
            with self.subTest(base=vid):
                lo, hi = stl_bbox(f"hardware/case/v2/bases/stl/base_{vid}_peg_5p8.stl")
                self.assertAlmostEqual(item["desk_z"][0], lo[2], places=2)
                self.assertAlmostEqual(
                    item["height_mm"], item["mating_plane_z"] - lo[2], places=2
                )
        self.assertAlmostEqual(POS["bases"]["items"]["riser"]["desk_z"][0], -12.5, 3)
        self.assertAlmostEqual(POS["bases"]["items"]["wedge"]["desk_z"][0], -26.994, 3)
        self.assertAlmostEqual(POS["bases"]["items"]["pedestal"]["desk_z"][0], -24.928, 3)

    def test_plan_silhouettes_match_the_shipped_stls(self):
        for vid, item in POS["bases"]["items"].items():
            with self.subTest(base=vid):
                lo, hi = stl_bbox(f"hardware/case/v2/bases/stl/base_{vid}_peg_5p8.stl")
                span = (hi[0] - lo[0], hi[1] - lo[1])
                if item["plan"]["shape"] == "circle":
                    self.assertAlmostEqual(span[0], item["plan"]["d"], places=2)
                    self.assertAlmostEqual(span[1], item["plan"]["d"], places=2)
                else:
                    self.assertAlmostEqual(span[0], item["plan"]["size"][0], places=2)
                    self.assertAlmostEqual(span[1], item["plan"]["size"][1], places=2)
        self.assertEqual(POS["bases"]["items"]["pedestal"]["plan"]["d"],
                         const(BASE_PY, "PED_D"))

    def test_hinge_is_the_near_user_edge_at_the_desk_face(self):
        """A tilt must raise the FAR/USB edge, not the edge under the hand."""
        for vid, item in POS["bases"]["items"].items():
            with self.subTest(base=vid):
                self.assertAlmostEqual(item["hinge"]["y"], 103.7, places=6)
                self.assertAlmostEqual(
                    item["hinge"]["z"], item["mating_plane_z"] - item["body_mm"], 9
                )
                self.assertAlmostEqual(
                    item["desk_plane"]["slope_per_mm"],
                    math.tan(math.radians(item["tilt_deg"])), places=6,
                )
        # the far edge really is the LOW-z end of the plane for a tilted base
        w = POS["bases"]["items"]["wedge"]
        far_z = w["desk_plane"]["ref_z"] - (
            w["desk_plane"]["ref_y"] - 0.0) * w["desk_plane"]["slope_per_mm"]
        near_z = w["desk_plane"]["ref_z"]
        self.assertLess(far_z, near_z, "the wedge must RAISE the far/USB edge")

    def test_y_near_source_line_is_pinned(self):
        """gen_positions evaluates this line by hand; it must not drift."""
        self.assertIn("Y_NEAR = DATUM[1] + BASE_H / 2.0", BASE_PY)
        self.assertIn("Y_FAR = DATUM[1] - BASE_H / 2.0", BASE_PY)

    def test_the_pedestal_params_disagreement_is_recorded_not_hidden(self):
        stated = BASE_PARAMS["variants"]["pedestal"]["base_height_mm"]
        derived = POS["bases"]["items"]["pedestal"]["height_mm"]
        self.assertEqual(stated, 17.49)
        self.assertAlmostEqual(derived, 15.428, places=3)
        self.assertNotAlmostEqual(stated, derived, places=1)
        self.assertIn("PARAMS-FILE DISAGREEMENT", POS["sources"]["bases"])
        # and the WEDGE, whose figure the pedestal inherited, does agree
        self.assertAlmostEqual(
            BASE_PARAMS["variants"]["wedge"]["base_height_mm"],
            POS["bases"]["items"]["wedge"]["height_mm"], places=2,
        )


class TestCitations(unittest.TestCase):
    def test_every_cited_line_number_actually_holds_that_constant(self):
        """A citation that points at the wrong line is worse than none."""
        pairs = re.findall(r"(release/[\w./-]+\.py):(\d+)", json.dumps(POS["sources"]))
        self.assertGreater(len(pairs), 8, "sources lost its citations")
        seen = set()
        for rel, lineno in pairs:
            key = (rel, lineno)
            if key in seen:
                continue
            seen.add(key)
            line = (REPO_ROOT / rel).read_text().splitlines()[int(lineno) - 1]
            self.assertRegex(
                line, r"^[A-Z_][A-Z_0-9]*\s*(,\s*[A-Z_][A-Z_0-9]*\s*)*=",
                f"{rel}:{lineno} is not a constant assignment: {line!r}",
            )

    def test_sources_covers_every_published_group(self):
        for key in ("deck_z", "plate_z", "switches", "encoder", "stick",
                    "keycap_seat_z", "tray", "band", "base", "stabilizer",
                    "bases", "touch_pad", "screws", "stab"):
            self.assertIn(key, POS["sources"])
            self.assertTrue(POS["sources"][key])

    def test_every_new_top_level_key_is_present(self):
        for key in ("bases", "touch_pad", "screws", "stab"):
            self.assertIn(key, POS, f"{key} is missing from positions.json")
        self.assertIn("tilt_deg", POS["base"])
        self.assertIn("slot_size", POS["stabilizer"])
        self.assertIn("slots", POS["stabilizer"])

    def test_no_pre_existing_key_changed_shape(self):
        """This round is strictly ADDITIVE -- pin the round-1 contract."""
        self.assertEqual(POS["schema"], "agentpad13-configurator-positions-v1")
        self.assertEqual(POS["stabilizer"]["slot_centers"],
                         [[30.162, 89.47], [54.038, 89.47]])
        self.assertEqual(POS["stabilizer"]["half_spacing"], 11.938)
        self.assertEqual(POS["base"]["mating_plane_z"], -9.5)
        self.assertEqual(POS["base"]["peg_top_z"], -8.1)
        self.assertEqual(POS["base"]["peg_nominal_d"], 5.8)
        self.assertEqual(POS["encoder"], {"x": 13.525, "y": 12.5})
        self.assertEqual(POS["deck_z"], 5.0)
        self.assertEqual(POS["keycap_seat_z"], 11.6)


if __name__ == "__main__":
    unittest.main(verbosity=2)

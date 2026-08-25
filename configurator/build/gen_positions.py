#!/usr/bin/env python3
"""Generate `out/positions.json` -- where every part sits, in ONE frame.

Every number is read from a shipped source file and carries its citation in
the `sources` block. Nothing here is typed in by hand except the names of the
constants being read.

Run:  python3 configurator/build/gen_positions.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    OUT_DIR,
    RELEASE,
    REPO_ROOT,
    read_named_zone_polygon,
    read_pcb_shapes,
    round_floats,
    write_json,
)
from srcconst import SourceConstants  # noqa: E402

CASE_PY = RELEASE / "hardware/case/v2/agentpad13_case_v2.py"
BASE_PY = RELEASE / "hardware/case/v2/bases/agentpad13_base.py"
BASE_PARAMS = RELEASE / "hardware/case/v2/bases/params/agentpad13_base_params.json"
CONTRACT = RELEASE / "hardware/pcb/harness/contract_v4.json"
TOPPER_FRAME_PY = RELEASE / "hardware/case/v2/toppers/topper_frame_v2.py"
PCB_BOARD = RELEASE / "hardware/pcb/v5_7.kicad_pcb"
# The ORDERED plate boards are the primary source for what the plate actually
# shows: screw holes, stab slots and the TP5 touch marker.
PLATE_FAB = RELEASE / "hardware/case/v2/fab"
PLATE_BOARDS = {
    "standard": PLATE_FAB / "agentpad13_v2_plate_v5.kicad_pcb",
    "tented_ring": PLATE_FAB / "agentpad13_v2_plate_tented_ring_v5.kicad_pcb",
    "blank": PLATE_FAB / "agentpad13_v2_plate_blank_v5.kicad_pcb",
}

BAND_WIDTHS = {"w3.0": 3.0, "w5.4": 5.4, "w7.4": 7.4}
BASE_ITEMS = ("riser", "wedge", "pedestal")

# Tolerance for matching a value read out of a board file against the same
# value computed from the case model's constants. The boards carry 4 decimal
# places, so anything above 1e-4 is a real disagreement, not formatting.
FAB_TOL = 5e-4


def _edge_circles(shapes: dict) -> list[tuple[float, float, float]]:
    """Routed Edge.Cuts circles as (x, y, d), sorted. These ARE holes."""
    return sorted(
        (c["c"][0], c["c"][1], round(c["d"], 6))
        for c in shapes["circles"]
        if c["layer"] == "Edge.Cuts"
    )


def _circle_on(shapes: dict, layer: str, at: tuple[float, float]):
    """The single circle on `layer` centred at `at`, or None."""
    hits = [
        c
        for c in shapes["circles"]
        if c["layer"] == layer
        and abs(c["c"][0] - at[0]) < FAB_TOL
        and abs(c["c"][1] - at[1]) < FAB_TOL
    ]
    if len(hits) > 1:
        raise SystemExit(
            f"STOP: {len(hits)} circles on {layer} at {at} -- the touch-marker "
            "reader expects at most one and cannot choose between them."
        )
    return hits[0] if hits else None


def _screws(boards: dict, case) -> list[list[float]]:
    """The four M3 corner holes, read from the ORDERED boards and cross-checked.

    The boards are primary; the case model's BOSS_CENTERS / M3_SCREW_CLEAR are
    the independent second opinion. A disagreement is a STOP, never a pick.
    """
    want_d = case.get("M3_SCREW_CLEAR")
    want_xy = sorted(tuple(map(float, p)) for p in case.get("BOSS_CENTERS"))

    per_board = {}
    for vid, shapes in boards.items():
        holes = [c for c in _edge_circles(shapes) if abs(c[2] - want_d) < FAB_TOL]
        per_board[vid] = sorted((round(x, 6), round(y, 6)) for x, y, _d in holes)

    ids = sorted(per_board)
    first = per_board[ids[0]]
    for vid in ids[1:]:
        if per_board[vid] != first:
            raise SystemExit(
                "STOP: the plate variants disagree about the M3 screw holes -- "
                f"{ids[0]} has {first}, {vid} has {per_board[vid]}. They are "
                "meant to share one Edge.Cuts profile; do not guess which is "
                "the product."
            )
    if len(first) != 4:
        raise SystemExit(
            f"STOP: found {len(first)} Ø{want_d} Edge.Cuts holes in the shipped "
            f"plate boards, expected 4 (the M3 corner screws). Holes seen: "
            f"{[c for c in _edge_circles(boards[ids[0]])]}"
        )
    if [list(p) for p in first] != [list(p) for p in want_xy]:
        raise SystemExit(
            "STOP: the ordered plate's screw holes are at "
            f"{first} but agentpad13_case_v2.py BOSS_CENTERS says {want_xy}. "
            "The fab file and the case model disagree about where the case is "
            "screwed together -- do not guess which one the site should draw."
        )
    return [list(p) for p in first]


def _touch_pad(
    boards: dict, tp5: tuple[float, float], board_zone: list[tuple[float, float]]
) -> dict:
    """The TP5 touch electrode + its per-variant marker, from the ORDERED boards.

    Every diameter here is measured off the shipped plate boards. The board-
    side copper area is independently measured from the named zone in the
    shipped v5.7 PCB source.
    """
    per_variant, pad_ds, back_ds, back_open_ds = {}, set(), set(), set()
    for vid, shapes in boards.items():
        f_cu = _circle_on(shapes, "F.Cu", tp5)
        b_cu = _circle_on(shapes, "B.Cu", tp5)
        b_mask = _circle_on(shapes, "B.Mask", tp5)
        f_mask = _circle_on(shapes, "F.Mask", tp5)
        f_silk = _circle_on(shapes, "F.SilkS", tp5)

        if f_mask is not None and f_silk is not None:
            raise SystemExit(
                f"STOP: plate variant {vid!r} carries BOTH an exposed-pad mask "
                "opening and a silkscreen ring over TP5. The three shipped "
                "variants are meant to differ by exactly one marker."
            )
        if f_mask is not None:
            marker, exposed_d, ring_d, ring_stroke = "exposed_pad", f_mask["d"], None, None
        elif f_silk is not None:
            marker, exposed_d, ring_d, ring_stroke = (
                "silk_ring", None, f_silk["d"], f_silk["width"],
            )
        else:
            marker, exposed_d, ring_d, ring_stroke = "none", None, None, None

        if marker != "none" and f_cu is None:
            raise SystemExit(
                f"STOP: plate variant {vid!r} draws a {marker} over TP5 but "
                "carries no F.Cu electrode under it."
            )
        if f_cu is not None:
            pad_ds.add(round(f_cu["d"], 6))
        if b_cu is not None:
            back_ds.add(round(b_cu["d"], 6))
        if b_mask is not None:
            back_open_ds.add(round(b_mask["d"], 6))

        per_variant[vid] = {
            "marker": marker,
            "exposed_d": exposed_d,
            "ring_d": ring_d,
            "ring_stroke": ring_stroke,
            "electrode": f_cu is not None,
        }

    for name, seen in (("F.Cu pad", pad_ds), ("B.Cu landing", back_ds),
                       ("B.Mask opening", back_open_ds)):
        if len(seen) > 1:
            raise SystemExit(
                f"STOP: the plate variants disagree about the TP5 {name} "
                f"diameter ({sorted(seen)}). Do not average or pick."
            )

    xs = [p[0] for p in board_zone]
    ys = [p[1] for p in board_zone]
    rectangle = {
        (min(xs), min(ys)),
        (min(xs), max(ys)),
        (max(xs), min(ys)),
        (max(xs), max(ys)),
    }
    if len(board_zone) != 4 or set(board_zone) != rectangle:
        raise SystemExit(
            "STOP: the shipped PCB's TP5_touch design polygon is no longer "
            f"one four-corner rectangle: {board_zone}. Re-derive how its size "
            "is represented instead of publishing its bounding box as copper."
        )
    board_pour = [max(xs) - min(xs), max(ys) - min(ys)]
    board_pour_center = [(max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0]
    if any(abs(a - b) >= FAB_TOL for a, b in zip(board_pour_center, tp5)):
        raise SystemExit(
            "STOP: the shipped PCB's TP5_touch zone is centred at "
            f"{board_pour_center}, but contract refs.TP5 is {tp5}. Do not "
            "publish a touch area from a different location."
        )

    return {
        "ref": "TP5",
        "x": tp5[0],
        "y": tp5[1],
        "exposed_pad_d": per_variant["standard"]["exposed_d"],
        "ring_d": per_variant["tented_ring"]["ring_d"],
        "pad_d": next(iter(pad_ds)) if pad_ds else None,
        "back_pad_d": next(iter(back_ds)) if back_ds else None,
        "back_mask_open_d": next(iter(back_open_ds)) if back_open_ds else None,
        "board_pour_mm": board_pour,
        "variants": per_variant,
    }


def _bases(case, base) -> dict:
    """Where each base sits and how far it leans the device.

    The desk face is a PLANE, given verbatim by agentpad13_base.py's desk_z():

        z = MATE_Z - t0 - (Y_NEAR - y) * tan(tilt)

    so the base's flat top is the tray bottom (MATE_Z) and the whole device
    pivots about the NEAR (user) edge at y = Y_NEAR. Every number below is that
    formula evaluated with constants read out of the module; the shipped STLs
    are the independent check (tests/test_positions_sources.py).
    """
    mate_z = base.get("MATE_Z")
    datum = tuple(base.get("DATUM"))
    base_h = base.get("BASE_H")
    base_w = base.get("BASE_W")
    base_r = base.get("BASE_R")
    ped_d = base.get("PED_D")

    # Y_NEAR/Y_FAR are `DATUM[1] +/- BASE_H / 2.0`, which srcconst refuses to
    # evaluate (a subscript is not literal arithmetic). Rather than loosen that
    # reader -- its refuse-rather-than-guess property is load-bearing -- the two
    # lines are evaluated here and the SOURCE TEXT is pinned, so an upstream
    # edit fails the build instead of silently changing the desk plane.
    for name, expect in (
        ("Y_NEAR", "Y_NEAR = DATUM[1] + BASE_H / 2.0"),
        ("Y_FAR", "Y_FAR = DATUM[1] - BASE_H / 2.0"),
    ):
        got = base.source_line(name).split("#")[0].strip()
        if got != expect:
            raise SystemExit(
                f"STOP: {base.cite(name)} now reads {got!r}, not {expect!r}. "
                "The desk-plane reference edge is computed from that exact "
                "expression -- re-derive it before publishing a base tilt."
            )
    y_near = datum[1] + base_h / 2.0
    y_far = datum[1] - base_h / 2.0

    variants = {v[0]: v for v in base.get("VARIANTS")}
    missing = [v for v in BASE_ITEMS if v not in variants]
    if missing:
        raise SystemExit(
            f"STOP: {base.cite('VARIANTS')} no longer offers {missing}. The "
            "catalog ships exactly riser/wedge/pedestal."
        )

    def desk_z(y: float, deg: float, t0: float) -> float:
        return mate_z - t0 - (y_near - y) * math.tan(math.radians(deg))

    items = {}
    for vid in BASE_ITEMS:
        _n, kind, deg, t0 = variants[vid]
        if kind == "circle":
            plan = {"shape": "circle", "d": ped_d, "center": list(datum)}
            y_lo, y_hi = datum[1] - ped_d / 2.0, datum[1] + ped_d / 2.0
        else:
            plan = {
                "shape": "rounded_rect",
                "size": [base_w, base_h],
                "corner_r": base_r,
                "center": list(datum),
            }
            y_lo, y_hi = y_far, y_near
        z_lo, z_hi = desk_z(y_lo, deg, t0), desk_z(y_hi, deg, t0)
        items[vid] = {
            "tilt_deg": deg,
            "kind": kind,
            "body_mm": t0,
            "mating_plane_z": mate_z,
            "desk_plane": {
                "ref_y": y_near,
                "ref_z": mate_z - t0,
                "slope_per_mm": math.tan(math.radians(deg)),
            },
            "hinge": {"axis": "x", "y": y_near, "z": mate_z - t0},
            "desk_z": [min(z_lo, z_hi), max(z_lo, z_hi)],
            "height_mm": mate_z - min(z_lo, z_hi),
            "plan": plan,
            "mesh": f"meshes/base_{vid}.glb",
        }
    return {
        "note": (
            "A base's flat top IS the tray bottom (mating_plane_z), so a base "
            "mesh needs no transform -- it is baked. What the viewer needs from "
            "here is the LEAN: rotate the whole device about the hinge line, "
            "which is the board-frame x axis at (y = hinge.y, z = hinge.z). "
            "The desk face is the plane z = desk_plane.ref_z - "
            "(desk_plane.ref_y - y) * slope_per_mm."
        ),
        "tilt_axis": (
            "board x (the owner's LEFT-RIGHT axis). A tilt raises the FAR edge "
            "(y = 0, the USB / control-band edge away from the user) and leaves "
            "the NEAR edge (y = 100, the 2U key edge) down on the desk -- a "
            "back-raised typing wedge, agentpad13_base.py:69."
        ),
        "mating_plane_z": mate_z,
        "items": items,
    }


def build() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    refs = contract["refs"]
    pcb_w, pcb_h = contract["outline"]["target_mm"]
    octagon = [list(map(float, v)) for v in contract["outline"]["chamfer_vertices"]]
    contract_rel = str(CONTRACT.relative_to(REPO_ROOT))

    # PCB_W/PCB_H are unpacked from the contract at case:294; seed them so the
    # derived chain (INNER_W -> PLATE_W -> TRAY_W ...) evaluates statically.
    case = SourceConstants(CASE_PY, REPO_ROOT, seed={"PCB_W": pcb_w, "PCB_H": pcb_h})
    topper = SourceConstants(TOPPER_FRAME_PY, REPO_ROOT)
    # agentpad13_base.py CONSUMES the case module (`import ... as C`), so its
    # first six constants are attribute reads that srcconst refuses to guess at.
    # They are seeded here from the case module's OWN cited constants, which is
    # exactly what the source line says each one is -- never a retyped number.
    base = SourceConstants(
        BASE_PY,
        REPO_ROOT,
        seed={
            "BAND_W": case.get("OUTER_W"),   # base.py:135  = C.OUTER_W
            "BAND_H": case.get("OUTER_H"),   # base.py:135  = C.OUTER_H
            "BAND_R": case.get("OUTER_R"),   # base.py:135  = C.OUTER_R
            "MATE_Z": case.get("Z_TRAY_BOT"),  # base.py:129 = C.Z_TRAY_BOT
            "DATUM": (case.get("CX"), case.get("CY")),  # base.py:130 = (C.CX, C.CY)
        },
    )
    boards = {vid: read_pcb_shapes(p) for vid, p in PLATE_BOARDS.items()}

    deck_z = case.get("PLATE_TOP_TO_PCB")
    plate_t = case.get("PLATE_T")
    z_plate_top = case.get("Z_PLATE_TOP")
    z_plate_bot = case.get("Z_PLATE_BOT")
    z_pcb_bot = case.get("Z_PCB_BOT")
    z_floor_top = case.get("Z_FLOOR_TOP")
    z_tray_bot = case.get("Z_TRAY_BOT")
    band_z_bot = case.get("BAND_Z_BOT")
    inner_w, inner_h = case.get("INNER_W"), case.get("INNER_H")
    tray_w, tray_h, tray_r = case.many("TRAY_W", "TRAY_H", "TRAY_R")
    plate_w, plate_h, plate_r = case.many("PLATE_W", "PLATE_H", "PLATE_R")
    inner_r = case.get("INNER_R")

    # --- encoder: footprint anchor is PIN A, not the shaft (case:314-326) ---
    re1 = refs["RE1"]
    anchor_dx, anchor_dy = case.get("EC11_ANCHOR_TO_SHAFT")
    shaft_from_board = (re1["x"] + anchor_dx, re1["y"] + anchor_dy)
    shaft_design = tuple(case.get("RE1_SHAFT_DESIGN"))
    if tuple(round(v, 6) for v in shaft_from_board) != tuple(
        round(v, 6) for v in shaft_design
    ):
        raise SystemExit(
            "STOP: the encoder SHAFT disagrees between board truth and design. "
            f"contract RE1 {(re1['x'], re1['y'])} + anchor offset "
            f"{(anchor_dx, anchor_dy)} = {shaft_from_board}, but "
            f"RE1_SHAFT_DESIGN = {shaft_design}. Do not guess which is right "
            "-- see agentpad13_case_v2.py:327-334 (DESIGN-vs-BOARD separation)."
        )

    js1 = refs["JS1"]
    switches = [
        {"ref": f"SW{i}", "x": refs[f"SW{i}"]["x"], "y": refs[f"SW{i}"]["y"], "size": "1u"}
        for i in range(1, 13)
    ] + [{"ref": "SW13", "x": refs["SW13"]["x"], "y": refs["SW13"]["y"], "size": "2u"}]

    # --- keycap seat -------------------------------------------------------
    # The public topper frame records the cap/switch datum chain it consumes.
    # CAP_MOUNT_RECESS = 0.0 means the shipped cap STL's local z=0 bottom rim
    # is the seating face; the 6.60 mm shoulder over the 5.0 mm deck gives
    # KEYCAP_RIM_Z = 11.6 mm above the PCB.
    topper_deck = topper.get("DECK_Z")
    mount_recess = topper.get("CAP_MOUNT_RECESS")
    shoulder_h = topper.get("SW_SHOULDER_H")
    recorded_seat = topper.get("KEYCAP_RIM_Z")
    if abs(topper_deck - deck_z) >= FAB_TOL:
        raise SystemExit(
            f"STOP: topper_frame_v2.py DECK_Z is {topper_deck}, but the case "
            f"model's PLATE_TOP_TO_PCB is {deck_z}. Reconcile the public "
            "assembly datums before placing keycaps."
        )
    if mount_recess != 0.0:
        raise SystemExit(
            f"STOP: topper_frame_v2.py CAP_MOUNT_RECESS is {mount_recess}, not "
            "0.0. The cap's local z=0 is then no longer the seating face and "
            "keycap_seat_z must be re-derived."
        )
    keycap_seat_z = deck_z + shoulder_h - mount_recess
    if abs(keycap_seat_z - recorded_seat) >= FAB_TOL:
        raise SystemExit(
            "STOP: the derived keycap seat "
            f"{keycap_seat_z} disagrees with topper_frame_v2.py KEYCAP_RIM_Z "
            f"{recorded_seat}. Reconcile the public datum chain."
        )

    stab_half = case.get("STAB_HALF_SPACING")
    stab_y_shift = case.get("STAB_Y_SHIFT")
    stab_w, stab_h = case.get("STAB_W"), case.get("STAB_H")
    sw13 = refs["SW13"]
    stab_slots = [
        {
            "side": side,
            "center": [sw13["x"] + sgn * stab_half, sw13["y"] + stab_y_shift],
            "size": [stab_w, stab_h],
        }
        for side, sgn in (("left", -1.0), ("right", 1.0))
    ]

    # --- the plate's own record: screws, touch marker, base lean ------------
    screw_xy = _screws(boards, case)
    tp5 = (float(refs["TP5"]["x"]), float(refs["TP5"]["y"]))
    board_zone = read_named_zone_polygon(
        PCB_BOARD, name="TP5_touch", net_name="TOUCH_PAD", layer="F.Cu"
    )
    touch_pad = _touch_pad(boards, tp5, board_zone)
    bases = _bases(case, base)

    sources = {
        "_": (
            "Every value below is read from the file:line named here. Line "
            "numbers are emitted by the generator from the parsed source, not "
            "typed in, so they cannot drift silently."
        ),
        "contract": f"{contract_rel} (schema {contract['schema']}, generated {contract['generated']})",
        "board_outline_mm": f"{contract_rel} outline.target_mm",
        "board_octagon": f"{contract_rel} outline.chamfer_vertices",
        "switches": f"{contract_rel} refs.SW1..SW13",
        "switch_size_split": case.cite(
            "SW_1U", "SW_1U = SW1..SW12 (12 x 1U grid); SW_2U = SW13"
        )
        + " / "
        + case.cite("SW_2U"),
        "encoder": (
            f"{contract_rel} refs.RE1 = ({re1['x']}, {re1['y']}) is the footprint "
            f"ANCHOR (pin A), + {case.cite('EC11_ANCHOR_TO_SHAFT')} offset "
            f"{(anchor_dx, anchor_dy)} = the SHAFT; cross-checks exactly against "
            f"{case.cite('RE1_SHAFT_DESIGN')}. The plate opening is centred on "
            "the shaft, so this is the visible knob axis."
        ),
        "stick": f"{contract_rel} refs.JS1 (YTL YA13-FL7.4, current v5_7 board) / " + case.cite("JS1"),
        "deck_z": case.cite("PLATE_TOP_TO_PCB", "MX switch shoulder -> PCB = 5.0"),
        "plate_z": (
            case.cite("Z_PLATE_TOP")
            + " and "
            + case.cite("Z_PLATE_BOT")
            + f" = Z_PLATE_TOP - {case.cite('PLATE_T')}. NOTE the trailing "
            "comment on that line still reads '# +3.5' from when PLATE_T was "
            "1.5; the EVALUATED value is 3.4 and the shipped "
            "step/agentpad13_v2_plate.step measures z 3.4..5.0, which is what "
            "is published here."
        ),
        "pcb_z": case.cite("Z_PCB_BOT") + " = -" + case.cite("PCB_T_DESIGN"),
        "keycap_seat_z": (
            f"{deck_z} (deck, {case.cite('PLATE_TOP_TO_PCB')}) + {shoulder_h} "
            f"(stem shoulder above deck, {topper.cite('SW_SHOULDER_H')}) - "
            f"{mount_recess} ({topper.cite('CAP_MOUNT_RECESS')}) = "
            f"{keycap_seat_z}, cross-checked against "
            f"{topper.cite('KEYCAP_RIM_Z')}. The shipped cap STLs are measured "
            "independently by the tests: their local z=0 is the bottom rim."
        ),
        "tray": (
            case.cite("Z_TRAY_BOT")
            + ", "
            + case.cite("Z_FLOOR_TOP")
            + ", outline "
            + case.cite("TRAY_W")
            + "/"
            + case.cite("TRAY_H")
            + "/"
            + case.cite("TRAY_R")
        ),
        "band": (
            case.cite("BAND_Z_BOT", "FROZEN, decoupled from the tray's bottom")
            + ", inner "
            + case.cite("INNER_W")
            + "/"
            + case.cite("INNER_H")
            + "/"
            + case.cite("INNER_R")
            + ", outer = inner + 2*wall ("
            + case.cite("OUTER_W")
            + ")"
        ),
        "plate_outline": (
            case.cite("PLATE_W") + "/" + case.cite("PLATE_H") + "/" + case.cite("PLATE_R")
        ),
        "stabilizer": (
            f"{contract_rel} refs.STAB1 (co-located with SW13) + "
            + case.cite("STAB_HALF_SPACING")
            + " / "
            + case.cite("STAB_Y_SHIFT")
            + ", slot envelope "
            + case.cite("STAB_W", "STAB_W, STAB_H = 6.65, 12.3")
        ),
        "stab": (
            "The same slots as `stabilizer`, published as rectangles because "
            "the plate CUTS them: centres from "
            + case.cite("STAB_HALF_SPACING")
            + " / "
            + case.cite("STAB_Y_SHIFT")
            + " about contract refs.SW13, envelope from "
            + case.cite("STAB_W")
            + ". Independently confirmed by the fab gate's own readback in "
            "release/hardware/case/v2/CASE-V2-NOTES.md §14: '[SW13] cutout center "
            "(42.100,88.850) size 14.000x14.000 + stab L (30.162,89.47) / R "
            "(54.038,89.47) 6.65x12.3 UNCHANGED', and re-measured from the "
            "Edge.Cuts rectangles of the three shipped plate boards under "
            "release/hardware/case/v2/fab/ by the test suite."
        ),
        "screws": (
            "MEASURED from the ORDERED boards: the four Ø"
            + f"{case.get('M3_SCREW_CLEAR')} Edge.Cuts circles present and "
            "identical in all three of release/hardware/case/v2/fab/"
            "agentpad13_v2_plate{,_tented_ring,_blank}_v5.kicad_pcb. "
            "Cross-checked against the case model's "
            + case.cite("BOSS_CENTERS")
            + " (built on "
            + case.cite("BOSS_C")
            + ") and "
            + case.cite("M3_SCREW_CLEAR")
            + "; the generator STOPs if the two disagree. Fastener envelope: "
            + case.cite("M3_HEAD_D")
            + " / "
            + case.cite("M3_HEAD_H")
            + " / "
            + case.cite("M3_SCREW_D")
            + " / "
            + case.cite("SCREW_LEN")
            + ", z from "
            + case.cite("Z_HEAD_TOP")
            + " and "
            + case.cite("Z_SCREW_TIP")
            + ". NOTE the head is an ISO 7380 BUTTON head, not a socket-head "
            "cap: agentpad13_case_v2.py line 10 says the 'exposed M3 button "
            "heads sit PROUD on the deck'. A socket-head cap would be Ø5.5 x "
            "3.0 and would not match the shipped counterbore-free plate. "
            "Also confirmed by the fab gate readback in the public "
            "CASE-V2-NOTES.md §14: 'screw holes Ø3.2 @ (3.7,3.7) and "
            "(80.5,3.7) present'."
        ),
        "touch_pad": (
            f"Centre from {contract_rel} refs.TP5, restated at "
            + case.cite("TP5")
            + ". Every DIAMETER is measured off the ordered boards under "
            "release/hardware/case/v2/fab/: "
            "F.Cu electrode Ø14, B.Cu landing Ø14, B.Mask foam opening Ø8, "
            "and the per-variant marker -- Ø12 F.Mask opening (standard, the "
            "exposed ENIG gold disc) or Ø16 F.SilkS ring at 0.2 stroke "
            "(tented_ring) or nothing (blank). board_pour_mm is measured from "
            "the design polygon of the named TP5_touch / TOUCH_PAD zone in "
            "release/hardware/pcb/v5_7.kicad_pcb and cross-checked against "
            "contract refs.TP5."
        ),
        "bases": (
            "Tilt from "
            + base.cite("VARIANTS", "(name, kind, tilt, body_thickness)")
            + ", whose wedge/pedestal angle is the single constant "
            + base.cite("WEDGE_DEG")
            + "; riser 0.0, wedge 8.0, pedestal 8.0. Cross-checks "
            "release/hardware/case/v2/bases/params/agentpad13_base_params.json "
            "variants[].tilt_deg. The desk face is the plane in "
            "release/hardware/case/v2/bases/agentpad13_base.py desk_z(), "
            "lines 343-344, referenced to "
            + base.cite("Y_NEAR")
            + " and "
            + base.cite("MATE_Z")
            + "; plan silhouettes from "
            + base.cite("BASE_W")
            + " / "
            + base.cite("BASE_H")
            + " / "
            + base.cite("BASE_R")
            + " (full-footprint) and "
            + base.cite("PED_D")
            + " (pedestal). Verified against the shipped STLs: riser z_min "
            "-12.500, wedge -26.994, pedestal -24.928. "
            "PARAMS-FILE DISAGREEMENT, recorded not fixed: that params file "
            "lists base_height_mm 17.49 for the PEDESTAL, which is the wedge's "
            "full-footprint figure inherited unchanged; the pedestal's own "
            "solid is 15.428 tall below the mating plane, because its Ø78 plan "
            "never reaches the far edge. height_mm here is the geometry-derived "
            "value and it matches the shipped STL."
        ),
        "base": (
            case.cite("BASE_MOUNT_DEPTH")
            + ", "
            + case.cite("BASE_MOUNT_PITCH")
            + ", peg "
            + base.cite("PEG_LEN")
            + " / "
            + base.cite("PEG_NOM", "rigid-filament default, matches "
                        "bases/INTERFACE.md:41 'start with 5.8 in rigid filament'")
            + ". Mating plane = the tray bottom "
            + case.cite("Z_TRAY_BOT")
        ),
    }

    frame = {
        "name": "board",
        "definition": (
            "The case model's xy board frame. Origin at the PCB's (0,0) "
            "corner; x -> physical RIGHT, y -> physical FRONT (toward the "
            "user), z -> UP with z = 0 at the PCB top face. Millimetres."
        ),
        "handedness": "left",
        "handedness_source": (
            case.cite("Z_PLATE_TOP").rsplit(":", 1)[0]
            + ":1077 -- 'The design frame is LEFT-handed (x right, y DOWN from "
            "raw KiCad board coords, z up) while STL/STEP are right-handed, so "
            "every solid exported through this path is the ENANTIOMORPH of the "
            "intended part.'"
        ),
        "orientation_facts": [
            "USB (J1) is at y = %s, the FAR edge away from the user -- "
            "release/hardware/case/v2/bases/INTERFACE.md:17 'The USB port is on "
            "the FAR edge, away from you.'" % refs["J1"]["y"],
            "Encoder at x %.3f (left of the x centreline 42.1) and stick at "
            "x %.3f (right of it); board +x is 'the OWNER'S RIGHT' per "
            "agentpad13_case_v2.py:1597-1598."
            % (shaft_design[0], js1["x"]),
            "Rendered as reality this reads: encoder BACK-LEFT, stick "
            "BACK-RIGHT, 2U key at the FRONT -- matching the TOP-DOWN panel of "
            "release/renders/v27_turntable.png.",
        ],
        "to_gltf": {
            "note": (
                "Meshes in out/meshes/*.glb are ALREADY in glTF's Y-up "
                "right-handed space. To place a position from this file into "
                "that space use (X, Y, Z)_gltf = (x, z, y)_board. That swap has "
                "determinant -1, which is exactly what converts these "
                "left-handed board-frame numbers into the correctly handed real "
                "device; applying the usual det +1 Z-up->Y-up rotation "
                "(x, z, -y) instead would render the MIRROR IMAGE."
            ),
            "matrix_column_major": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
        },
    }

    mesh_placement = {
        "note": (
            "'baked' meshes already carry their assembly position in their "
            "vertex data -- load and add to the scene, no transform. "
            "'instance' meshes sit at their own local origin and must be "
            "placed using the positions in this file."
        ),
        "baked": ["tray", "band_*", "plate", "board", "base_*"],
        "instance": {
            "cap_*": (
                "place at (switch.x, keycap_seat_z, switch.y) in glTF space; "
                "cap local origin = centre of the bottom rim, +x along the 2U "
                "long axis (which is the board x axis for SW13)"
            ),
            "knob_*": (
                "place at (encoder.x, 0, encoder.y); the knob mesh already "
                "carries its absolute z (skirt bottom .. knob top)"
            ),
            "stick_cap_*": (
                "place at (stick.x, 0, stick.y); the cap mesh already carries "
                "its absolute z (14.4 .. 19.6)"
            ),
        },
    }

    # Rounded HERE rather than in main(), so that what build() returns and what
    # positions.json contains are the same numbers. Derived values carry binary
    # noise (42.1 + 11.938 evaluates to 54.038000000000004) and the tests read
    # build() directly; rounding at the boundary would let a test pass against
    # a number the site never sees. 6 places is 1 nm.
    return round_floats({
        "schema": "agentpad13-configurator-positions-v1",
        "units": "mm",
        "sources": sources,
        "frame": frame,
        "mesh_placement": mesh_placement,
        "deck_z": deck_z,
        "plate": {
            "z0": z_plate_bot,
            "z1": z_plate_top,
            "thickness": plate_t,
            "size": [plate_w, plate_h],
            "corner_r": plate_r,
            "center": [pcb_w / 2.0, pcb_h / 2.0],
        },
        "pcb": {
            "z0": z_pcb_bot,
            "z1": 0.0,
            "outline_mm": [pcb_w, pcb_h],
            "octagon": octagon,
        },
        "switches": switches,
        "encoder": {"x": shaft_design[0], "y": shaft_design[1]},
        "stick": {"x": js1["x"], "y": js1["y"]},
        "stabilizer": {
            "ref": "STAB1",
            "for": "SW13",
            "x": sw13["x"],
            "y": sw13["y"],
            "half_spacing": stab_half,
            "y_shift": stab_y_shift,
            "slot_centers": [
                [sw13["x"] - stab_half, sw13["y"] + stab_y_shift],
                [sw13["x"] + stab_half, sw13["y"] + stab_y_shift],
            ],
            # additive: the slot ENVELOPE, which slot_centers alone never gave.
            "slot_size": [stab_w, stab_h],
            "slots": stab_slots,
        },
        # `stab` is the same two slots as rectangles, under the name the site
        # asked for. Both are built from `stab_slots` above, so they cannot
        # drift apart.
        "stab": {
            "ref": "STAB1",
            "for": "SW13",
            "switch": [sw13["x"], sw13["y"]],
            "half_spacing": stab_half,
            "y_shift": stab_y_shift,
            "slot_size": [stab_w, stab_h],
            "slots": stab_slots,
            "caveat": (
                "The plate slots are measured from every shipped plate board. "
                "release/hardware/case/v2/CASE-V2-NOTES.md §8 item 6 still "
                "requires coupon verification with the real 2U stabilizer; "
                "release/HOW-TO-ORDER.md §7 therefore tells stabilized builds "
                "to use the shipped 2u_stab cap."
            ),
        },
        "screws": {
            "count": len(screw_xy),
            "fastener": "M3x8 ISO 7380 BUTTON head (NOT a socket-head cap)",
            "hole_d": case.get("M3_SCREW_CLEAR"),
            "head_d": case.get("M3_HEAD_D"),
            "head_h": case.get("M3_HEAD_H"),
            "shaft_d": case.get("M3_SCREW_D"),
            "length_mm": case.get("SCREW_LEN"),
            "z": {
                "seat": z_plate_top,
                "head_top": case.get("Z_HEAD_TOP"),
                "tip": case.get("Z_SCREW_TIP"),
            },
            "positions": screw_xy,
            "note": (
                "The head seats ON the plate top and stands proud: seat "
                f"{z_plate_top} -> head_top {case.get('Z_HEAD_TOP')}. There is "
                "no counterbore -- the plate hole is a plain Ø"
                f"{case.get('M3_SCREW_CLEAR')} clearance."
            ),
        },
        "touch_pad": touch_pad,
        "keycap_seat_z": keycap_seat_z,
        "tray": {
            "z0": z_tray_bot,
            "floor_top_z": z_floor_top,
            "size": [tray_w, tray_h],
            "corner_r": tray_r,
            "center": [pcb_w / 2.0, pcb_h / 2.0],
            "mesh": "meshes/tray.glb",
        },
        "band": {
            "z0": band_z_bot,
            "z1": z_plate_top,
            "inner": [inner_w, inner_h],
            "inner_r": inner_r,
            "center": [pcb_w / 2.0, pcb_h / 2.0],
            "widths": {
                wid: {
                    "wall": wall,
                    "outer": [inner_w + 2 * wall, inner_h + 2 * wall],
                    "mesh": f"meshes/band_{wid}.glb",
                }
                for wid, wall in BAND_WIDTHS.items()
            },
        },
        "base": {
            "mating_plane_z": z_tray_bot,
            "peg_top_z": z_tray_bot + base.get("PEG_LEN"),
            "pocket_depth": case.get("BASE_MOUNT_DEPTH"),
            "pocket_pitch": case.get("BASE_MOUNT_PITCH"),
            "peg_nominal_d": base.get("PEG_NOM"),
            "center": [pcb_w / 2.0, pcb_h / 2.0],
            # additive: the per-variant lean, as a plain {id: degrees} map.
            # Taken from the SAME `bases` computation below, so the two can
            # never disagree.
            "tilt_deg": {k: v["tilt_deg"] for k, v in bases["items"].items()},
        },
        "bases": bases,
    })


def main() -> int:
    out = build()
    write_json(OUT_DIR / "positions.json", out)
    print(
        f"positions: {len(out['switches'])} switches, deck_z={out['deck_z']}, "
        f"plate z {out['plate']['z0']}..{out['plate']['z1']}, "
        f"keycap_seat_z={out['keycap_seat_z']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""agentpad13 case v2 — plate-as-deck over the v4_r27 octagon (build123d/khana).

Owner-locked architecture (2026-07-18), top to bottom, FOUR product parts:
  1. fr4_plate : 1.6 mm FR4 (fab stock; v2.1), BLANK (no decoration — owner
                 directive; art is a
                 later separate pass). The product face AND the switch skeleton:
                 its cutouts clip-hold all 13 switches and take every keypress
                 and hot-swap insertion. Rounded rectangle, INSET inside the
                 band with a 0.2 mm groove. Four plain Ø3.4 corner holes;
                 exposed M3 button heads sit PROUD on the deck (a 1.6 mm plate
                 cannot carry the v1 Ø6.2x1.8 counterbore — flagged in
                 CASE-V2-NOTES for owner sign-off; the CM2/Codex renders show
                 proud heads).
  2. band      : the top case — a printed "band around the side" (owner's
                 words), the entire visible wall. FDM or resin; transparent/
                 frosted resin is the default look. Carries the USB aperture
                 and four internal corner caps that the plate clamps onto.
  3. pcb       : the v5-lineage octagon (84.2 x 100; per-corner chamfers —
                 13.2 at the (0,0) corner, 14.6 elsewhere, read from the
                 adjudicated contract). Floating: located by three tray press
                 pins (H5/H6/H7), supported by tray bosses, captured by the
                 sandwich. NEVER screwed, NEVER touched by the case.
  4. tray      : bottom case, ALWAYS FDM (heat-set inserts are thermoplastic-
                 only). Floor, four Ø9.5 corner bosses w/ M3 inserts, PCB
                 support bosses + press pins, service slots, and the
                 v2.9 four-pocket BASE MOUNT interface (published contract —
                 see CASE-V2-NOTES §22).

One screw path: M3x8 button head -> plate Ø3.4 -> band cap Ø4.4 -> tray boss
insert (bore Ø4.2 from +1.5 to -4.2). Four screws total. The corner bosses
live in the voids the octagon's 14.6 mm chamfers vacate — the v1 "ears"
(CASE-NOTES §v1.1) dissolve; the case is a clean rounded rectangle.

Coordinate frame:
    origin = PCB top-left corner (contract_v4.json board coords)
    +X     = right, across key columns;  +Y = down, controls -> touch row
    +Z     = up toward keycaps;  z = 0 = PCB TOP face (switch-mount datum)

Z stack (desk -> keycap), every value re-derived (CASE-NOTES §1 chain):
    +6.8   screw head top (proud button head, ISO 7380 env 1.8)
    +5.0   plate TOP = band rim top (flush; 0.2 groove around plate)
    +3.4   plate underside = band cap top (plate clamps here; v2.1: 1.6 plate)
    +1.5   band cap underside = tray boss top (v1 parting plane, §3/§4)
     0.0   PCB TOP (datum)
    -1.51  PCB bottom (real STEP board thickness; design datum -1.6)
    -3.45  hotswap socket bottom (SOCKET_DROP, §1A)
    -5.10  cavity floor = tray floor top (UNDER_PCB_CAVITY 3.5, §1A)
    -5.895 BOOT/RESET tact bottoms (fresh STEP) -> tray service slots
    -7.50  band bottom (BAND_Z_BOT, FROZEN — the band is ordered)
    -9.50  tray bottom (v2.11 plinth; TRAY_T 4.4, §4). NO LONGER flush with
           the band: the tray stands 2.0 mm proud below it, inset 5.65 mm
           per side, so the band floats on a recessed plinth (owner
           directive 2026-08-19 — see TRAY_T and CASE-V2-NOTES §1).
    -11.7  desk plane (3M SJ61A1 Ø7.9x2.2 bumpons on the boss bottom faces)

Dimension provenance:
  [C]   contract_v4.json (pcbnew 9.0.9 read-back of the frozen board;
        cross-checked 45/45 vs v4_r27 by grade_board.py this session)
  [S]   pcb_components_data_v2.py (FRESH STEP from v4_r27, this session)
  [R]   direct v4_r27 pcbnew read-back this session (H5/6/7 drill Ø2.2 NPTH)
  [§n]  hardware/case/CASE-NOTES.md section n (v1 case, values re-derived)
  [D]   part datasheet / published standard (cited inline)
  [V5]  v5 board lineage (2026-07-19): the adjudicated contract (RE1 anchor
        6.025,10.0 -> shaft-true 13.525,12.5; corner-(0,0) chamfer leg 13.2)
        and the v5_5 J1-flip ledger (USB mating face 0.49 mm PROUD of the
        y=0 board edge, body y -0.49..6.81, x 37.3..46.9) — the number the
        board executor and this case pass converged on.

v2.2 (2026-07-19): board-v5 convergence. Chamfer legs now read PER-CORNER
from the contract octagon (the (0,0) corner shrank 14.6 -> 13.2 for the
encoder move); any tray boss whose corner slip falls under the 0.3 gate gets
an automatic 45° notch flat (the (0,0) boss: board corner reaches 4.101 from
the boss center vs Ø9.5/2 = 4.75 -> 0.649 interference -> flat at 3.751,
clearance 0.35 by construction). J1 flipped per the v5_5 plan: the hand
usb_recept envelope now faces the wall with its mouth 0.49 PROUD, which
makes the band-aperture gates load-bearing for the first time (with the old
backwards-J1 envelope they were vacuously clear of the wall). JS1 envelope
upgraded to the board-truth 18.72 sq F.Fab frame + nub cylinder (frame
HEIGHT provisional — caliper watch-item, §8.5 carries). The STEP component
set [S] remains valid for v5: only copper plus the RE1/J1 footprints moved,
and neither footprint resolves a 3D model in the STEP (both are hand
keep-outs here) — re-verify by regen diff when v5_5 banks.

v2.4 (2026-07-20): TRUE E2E fitment — the joystick, encoder, switches and
keycaps are now MODELLED, not assumed (the named blindness class). The
slider-era JS geometry is RETIRED for the YTL YA13-FL7.4 THT tilt joystick:
the plate opening becomes the asymmetric rounded rect mirrored from the
ORDERED fab file (§14); js_body is the faithful CROSS envelope (frame + W/N
pot boxes + E/S tabs, z 0..11.1); js_pins are the 10 THT tails PARSED from
the banked board (v5_6, md5 checked) reaching -3.71; js_sweep is the REAL
dome-cap swept 30° tilt cone. New populated parts: switch_bodies (13 MX
envelopes), keycaps (12x1U + 1x2U), knob (static Ø18) and stick_cap (static
dome). Consumed from the toppers params (dome cap, knurled knob). Findings:
(a) js_body clears the NE screw boss by 0.584 — the §12.4 caliper item,
resolved by the adjudicated SW JS1 move (the old Ø15-cage gate was blind to
the square frame's corner); (b) js_pins hit the perimeter rail at the MP2
lug (8.03 mm^3) -> a JS1 rail skip was ADDED (tray_v5 md5 changes; band
untouched); (c) THE joystick-clearance finding: js_sweep overlaps the SW4
keycap by 40.78 mm^3 at full 30° tilt — a real graze, unfixable case-side,
escalated as a §15 STOP-CONDITION advisory (measured, not gated).

v2.5 (2026-07-20): DEFAULT STICK-CAP FLIP dome → taper + case re-gate. The
§15 SW4 graze (lever (c), topper-side fix) is now the SHIPPING default:
coordinator ruling — the release default stick cap = the TAPER cone, the only
variant whose wall clears the SW4 keycap at full 30° tilt (the owner's "make
sure it won't hit a key"). dome/dish/knurl ship as ALTERNATES (dome documented
with its >15.8°-tilt SW4 graze caveat). This module now CONSUMES the taper
profile for both `stick_cap` (rest pose) and `js_sweep` (tilt cone): a straight
30°-from-vertical wall, bottom Ø11.285 @+14.4 → Ø6.667 @+18.4 (dome spring),
then a spherical dome roof to +19.6 (all from stick_cap_params, default_variant
now "taper"). The v2.4 [v2.4-JS-KEYCAP] STOP-CONDITION advisory is REPLACED by
a green [v2.5-JS-KEYCAP] report: js_sweep×keycaps overlap = 0.00 mm^3, taper
wall→SW4 keycap edge clearance ≈ +0.29 mm. Assertions unchanged (~101, all
green); band/tray STL byte-identical (the cap touches neither export). No
topper re-run: the taper STLs + params already exist from the v2.5 topper add.

v2.6 (2026-07-23): BAND SIDEWALL 2.4 → 3.0 (owner order, PCBWay EQ). PCBWay's
3D-print review of agentpad13_v2_band_1.6mm.stl (order C-Y15W1075301A_) flagged
the four corner crescents (0.737 mm — the documented §3/§8 COSMETIC thin zone)
as "too thin, may break". Owner ruling: thicken the sidewall — "increase the
sidewall thickness by some amount; might even look better thicker (more visible
diffuser)". WALL is the single tunable (owner range under consideration: 3.0 /
5.4 / 7.4; this file ships 3.0). Two invariance guarantees make it a one-line
retune: (a) INNER_W/INNER_H are PCB-driven (PCB_W/H + 2·PCB_CLEARANCE) and
(b) INNER_R is now FROZEN at 5.6 instead of `OUTER_R - WALL` — otherwise the
ORDERED plate's R5.4 corner and the banked tray_v5's R5.35 corner would silently
re-cut. Everything the band mates to (plate recess, 1.2 rabbet ledge, Ø10 boss
sockets, Ø8.6 caps, Ø4.4 screw pass, USB aperture x/z, tray nesting) is derived
from INNER_*/PCB/const and is provably unmoved: band(2.4) ⊂ band(3.0) with ZERO
volume removed, and ZERO volume added inside the mating envelope. Proven three
ways this session (scratch v26_prove.py, verbatim in CASE-V2-NOTES §16):
  P1  the v2.6 code AT WALL=2.4 re-exports md5 36980cc2ff011dc32d923fb04f7429f7
      — the retired band, byte for byte. WALL is the only value that moved.
  P2  vol(band_2.4 - band_3.0)                = 0.000000 mm^3 (nothing removed)
  P3  vol((band_3.0 - band_2.4) & MATING)     = 0.000000 mm^3 (nothing added
      into the cavity / ledge / plate recess / boss sockets / screw pass / USB
      aperture) — so every mating interface is literally unmoved, corner radii
      included.
Measured consequences: OUTER 89.6×105.4 → 90.8×106.6; band_crescent_wall
0.737 → 1.586; band printability min_wall advisory 0.642 → 1.569 (funnel-free
comparison — see below); band volume 11794.7 → 14677.7 mm^3 (+24.4 %); plate
and tray exports BYTE-IDENTICAL (tray_v5 md5 d7d16481df24bae4c7769d7624dfc620
held; the .step files differ only in their FILE_NAME timestamp line).
The band md5-invariance gate (36980cc2ff011dc32d923fb04f7429f7) is RETIRED by
owner order — that hash is now the SUPERSEDED 2.4-wall record; do not print it.
New export names carry the wall: agentpad13_v2_band_1.6mm_w{WALL}.stl/.step.

v2.6b (2026-07-23, same session): USB PORT FUNNEL — a parametric outer
counterbore at the USB mouth (owner directive) that REMOVES the USB constraint
from the wall decision. Depth = WALL - 2.4, so the plug-shell bridge is a
wall-INVARIANT 2.10 mm at 3.0 / 5.4 / 7.4 and the wall pick is purely
aesthetic. See usb_funnel() + the USB_FUNNEL_* block. Two measured deviations
from the first-cut spec, both forced by geometry and both documented at their
constants: (a) the bottom lead-in leg is clamped to 0 (a 4-sided 1.0 leg left a
0.566 mm knife edge on the band's bottom face and made OCCT refuse the
elephant-foot chamfer); (b) the pocket floor leaves an 0.8 mm rooted step under
the port — that is the GEOMETRIC MAXIMUM: the band bottom is at -7.50 and a
max-size USB-C overmold's bottom face reaches -6.45, so no closed-bottom pocket
can leave more than 1.05, and 0.8 is what a centered 0.5 mm height clearance
gives. Unlike the retired 0.737 crescent (a free-standing arc shell) this step
is bonded to the full wall across its whole 13 x 0.8 back face — it is a step,
not a fin. It does move the printability ADVISORY for the funnelled band to
0.600 (the sampler reads the pocket void); the crescent fix itself is measured
on the funnel-free band at 1.569. If the owner wants the advisory clean too,
the one-line lever is to ramp the pocket floor out to the band bottom (removes
the step; adds a 13 mm wide scallop in the band's bottom outer edge).

v2.7 (2026-07-24): BAND DEFAULT WALL 3.0 -> 5.4 (OWNER DECISION: "1.6 mm
doesn't seem like an especially strong corner to me" — the v2.6 3.0-wall band's
arc-region corner measure). 5.4 is now the SHIPPING default: it is the band in
release/, the band offered to PCBWay as the option-A replacement
file, and the band the public agentpad13 repo will carry. 3.0 and 7.4 stay
SUPPORTED VARIANTS — all three are khana-gated (101/101, the same 8 documented
interferences) and exported under their own _w{WALL} names. The wall is read
once, from AGENTPAD13_WALL (default 5.4), so a variant needs no file edit:
`AGENTPAD13_WALL=7.4 khana build agentpad13_case_v2.py`.
Measured consequences at 5.4 (all re-proven this session, scratch
v27_prove.py, verbatim in CASE-V2-NOTES §18):
  P1  the v2.7 code at WALL=3.0 re-exports md5 887b2538619db46d63b07cf044762bab
      and at WALL=2.4 md5 36980cc2ff011dc32d923fb04f7429f7 — the v2.6 band and
      the retired v2.5 band, byte for byte. The v2.7 edit moved WALL and two
      PRINT-ONLY formulas; it moved no geometry.
  P2  vol(band_2.4 - band_5.4)            = 0.000000 mm^3 (nothing removed)
  P3  vol((band_5.4 - band_2.4) & MATING) = 0.000000 mm^3 (nothing added into
      the cavity / ledge / plate recess / boss sockets / screw pass / USB
      aperture) — every mating interface literally unmoved, radii included;
      vol(usb_funnel_5.4 & band_2.4)      = 0.000000 mm^3 (the 3.00-deep funnel
      is carved out of ADDED shell only).
OUTER 90.8x106.6 -> 95.6x111.4 (R8.0); corner min wall 1.586 (arc) -> 4.400
(FLAT — above WALL 4.0 the nearest outer surface is the flat, not the arc; see
_corner_margins, whose v2.6 closed form over-reported this as 4.980); funnel
depth 0.60 -> 3.00 with the shell bridge still 2.10; band volume 14677.7 ->
26580.6 mm^3. tray_v5 STL md5 d7d16481df24bae4c7769d7624dfc620 UNCHANGED.
REPORTING ERRATUM (v2.7, no geometry impact): head_to_plate_edge and
plate_hole_edge_web were computed off the BAND's WALL-driven outer arc center,
so §16.4's "0.287 -> 1.136" / "1.537 -> 2.386" improvements at WALL 3.0 were
artifacts — the plate is frozen and those margins are WALL-INVARIANT at 0.287 /
1.537. Fixed here; see _corner_margins and CASE-V2-NOTES §18.

v2.17 (2026-08-20): TOPPERS v2 RE-POINT. This module's topper consumption
moves off the v1 params (stick_cap_params / encoder_knob_params, now RETIRED
to archive/toppers-v1/) onto the shipped v2 families
(stick_topper_v2_params / encoder_knob_v2_params, toppers commit 74a4b07).
Three envelope changes follow: (a) the encoder knob is Ø19 to +27.0, not Ø18
to +17.5 — so knob_sweep and knob() both grow, and the +x opening sliver the
v2.12 ruling accepted is CLOSED (+0.190 concealment); (b) the shipped default
stick topper is the nub_C2, a plain Ø6.189 cylinder +14.4..+19.6, replacing
the v2.5 taper cone; (c) NEW PART js_sweep_puck — the v2 family ships TWO
stick toppers with DIFFERENT throws (nub 30° unrestricted, TPU puck 22.5°
enforced by its own integral cone land), and modelling only the default would
leave the case blind to the larger of the two. Gate moves 101 -> 104
assertions and 8 -> 10 reported interference pairs, every delta ledgered with
its closed-form cause in CASE-V2-NOTES §27 — which SUPERSEDES the frozen
"101/101/8" strings in §22.5, §26.6 and §23. Also fixed: the SW4-clearance
advisory now reports the TRUE 3-D distance instead of a bbox-corner proxy
that had started printing a false negative. pivot_z / tilt_deg are not in the
v2 params, so they are stated here from the YA13 drawing and cross-checked at
import against deck_low_z and cone_z_at_bore. Two OCCT boolean traps were hit
and are documented at _revolve_rz; _tilt_sweep now carries a containment gate
because both failed silently toward a SMALLER envelope. No case geometry
changed: the band, tray and plate STLs are byte-identical across this pass.
"""

import hashlib
import json
import math
import os
import re
import sys

from build123d import (
    Axis,
    Box,
    Circle,
    Compound,
    Plane,
    Polyline,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Sphere,
    chamfer,
    export_step,
    export_stl,
    extrude,
    loft,
    make_face,
    mirror,
    revolve,
)

from cad_khana.mechanism.assembly import Assembly
from cad_khana.mechanism.check import check
from cad_khana.printability.inspect import inspect
from cad_khana.printability.methods import FDM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcb_components_data_v2 as PCB  # noqa: E402  [S]

# =========================================================================
# 0. CONTRACT COORDINATES  (single source: contract_v4.json read at runtime)
# =========================================================================

# AGENTPAD13_CONTRACT overrides the board contract (v5+ overlays); the
# default remains the frozen v4 contract.
_CONTRACT_PATH = os.environ.get("AGENTPAD13_CONTRACT") or os.path.normpath(
    os.path.join(HERE, "..", "pcb", "harness", "contract_v4.json"))
with open(_CONTRACT_PATH) as _f:
    _CONTRACT = json.load(_f)
_REFS = {k: (v["x"], v["y"]) for k, v in _CONTRACT["refs"].items()}

# --- Toppers params (v2.4: CONSUME, never modify — the printed knob + stick
#     cap are the single source of truth for those envelopes). ---------------
# [v2.17 2026-08-20] RE-POINTED to the v2 topper families (toppers commit
# 74a4b07). The v1 generators and params (stick_cap.py / encoder_knob.py,
# stick_cap_params.json / encoder_knob_params.json) are RETIRED to
# archive/toppers-v1/. Bare [] subscripts below are DELIBERATE: a missing or
# renamed key must raise KeyError at import, never silently fall back to a
# stale default — that is the same fail-loudly contract v2.4 shipped with.
_TOPPER_DIR = os.path.join(HERE, "toppers", "params")
with open(os.path.join(_TOPPER_DIR, "stick_topper_v2_params.json")) as _f:
    _STICK = json.load(_f)
with open(os.path.join(_TOPPER_DIR, "encoder_knob_v2_params.json")) as _f:
    _KNOB = json.load(_f)
_SV = _STICK["nub_C2"]        # shipped DEFAULT stick topper (Ø6.189 -> +19.6)
_PV = _STICK["puck_TPU"]      # the OTHER shipped stick topper (Ø9.412, 22.5°)
_KV = _KNOB                   # v2 knob envelope lives at the top level
# The case models ONE knob envelope for all three v2 textures (A/B2/C). That
# is only legitimate while the three agree — assert it rather than assume it.
for _kn, _kb in _KNOB["variants"].items():
    assert (_kb["od"], _kb["bottom_z"], _kb["top_z"]) == (
        _KV["od"], _KV["bottom_z"], _KV["top_z"]), (
        f"KNOB ENVELOPE FAIL: variant {_kn} is "
        f"({_kb['od']}, {_kb['bottom_z']}, {_kb['top_z']}) but the top-level "
        f"envelope is ({_KV['od']}, {_KV['bottom_z']}, {_KV['top_z']}) — the "
        "case's single knob envelope is no longer valid for every texture; "
        "model them separately before trusting any knob gate")

# --- Banked board (v2.4: DERIVE the YA13 THT pin tails from the board pads,
#     never retype). md5 MUST match the frozen v5_6 or the parse is stale. ---
BANKED_BOARD = os.path.normpath(
    os.path.join(HERE, "..", "pcb", "v5_6.kicad_pcb"))
BANKED_BOARD_MD5 = "221ebb98fcf44f860ed65f7ed8d1bc45"


def _parse_js1_pads(path=BANKED_BOARD):
    """Parse the JS1 footprint's 10 THT pads from the banked board and return
    world-frame keep-outs: [(x, y, drill, pad_d)]. The footprint pose is at
    (69.71, 13.37, rot 180); a rot-180 pad at local (lx, ly) lands at world
    (fx - lx, fy - ly). Guards: board md5, footprint pose vs contract JS1,
    pad count == 10. [v5_6 parse]"""
    txt = open(path).read()
    got = hashlib.md5(txt.encode()).hexdigest()
    assert got == BANKED_BOARD_MD5, (
        f"v5_6 board md5 {got} != frozen {BANKED_BOARD_MD5} — the board "
        "changed; re-verify JS1 pads before trusting js_pins()")
    i0 = txt.index('(footprint "Joystick:YA13')
    i1 = txt.index("\n\t(footprint", i0 + 16)
    blk = txt[i0:i1]
    m = re.search(r"\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)", blk)
    fx, fy, frot = float(m.group(1)), float(m.group(2)), float(m.group(3))
    assert (fx, fy, frot) == tuple(_REFS["JS1"]) + (180.0,), (
        f"JS1 footprint pose ({fx},{fy},{frot}) != contract JS1 {_REFS['JS1']}")
    pat = re.compile(
        r'\(pad "[^"]+" thru_hole circle\s*\(at ([-\d.]+) ([-\d.]+)\)\s*'
        r'\(size ([-\d.]+) [-\d.]+\)\s*\(drill ([-\d.]+)\)')
    out = [(fx - float(a), fy - float(b), float(d), float(s))
           for a, b, s, d in pat.findall(blk)]
    assert len(out) == 10, f"expected 10 JS1 pads, parsed {len(out)}"
    return out


JS1_PADS = _parse_js1_pads()

PCB_W, PCB_H = _CONTRACT["outline"]["target_mm"]          # 84.2 x 100.0 [C]
OCTAGON = [tuple(p) for p in _CONTRACT["outline"]["chamfer_vertices"]]


def _corner_leg(cx0, cy0):
    """Chamfer leg at a board corner, read from the contract octagon [C][V5].

    The L1 distance from the corner to its nearest octagon vertex IS the leg
    (each chamfer vertex sits leg-mm along one edge from the corner). v2.2:
    legs are PER-CORNER — the (0,0) corner is 13.2, the other three 14.6.
    """
    return min(abs(vx - cx0) + abs(vy - cy0) for (vx, vy) in OCTAGON)


BOARD_CORNERS = [(0.0, 0.0), (PCB_W, 0.0), (0.0, PCB_H), (PCB_W, PCB_H)]

SW_1U = [_REFS[f"SW{i}"] for i in range(1, 13)]           # [C] 12 x 1U grid
SW_2U = _REFS["SW13"]                                     # [C] (42.1, 88.85)
ALL_SWITCHES = SW_1U + [SW_2U]
RE1 = _REFS["RE1"]                                        # [C] footprint ANCHOR
# ERRATUM FIX (2026-07-19): the EC11E footprint anchor is PIN A, not the
# shaft. The shaft axis = anchor + (7.5, 2.5) at rotation 0 — measured from
# the frozen board's mounting-tab midpoint AND confirmed by the fab-drawing
# body center [R]. ALL case features (plate opening, body keep-out, knob
# sweep) center on the SHAFT. This is what made the v4 62/62 runs blind:
# the same anchor==shaft assumption fed both the model and the gate.
_RE1_ROT = _CONTRACT["refs"]["RE1"].get("rot", 0.0)
assert _RE1_ROT == 0.0, (
    f"RE1 rot={_RE1_ROT}: EC11_ANCHOR_TO_SHAFT offset below is rot-0 only — "
    "update the rotation transform before trusting any gate result")
EC11_ANCHOR_TO_SHAFT = (7.5, 2.5)                         # [R] tab midpoint
RE1_SHAFT = (RE1[0] + EC11_ANCHOR_TO_SHAFT[0],
             RE1[1] + EC11_ANCHOR_TO_SHAFT[1])
# DESIGN-vs-BOARD role separation (the second half of the erratum fix):
# the PLATE is an ordered artifact — its encoder opening is a DESIGN
# CONSTANT (the shaft target, symmetric with JS1), NOT a contract-derived
# value. The body/knob keep-outs are BOARD TRUTH (contract + offset).
# Against the v4 contract this makes the overlay FAIL (body at 21.025,15
# vs the ordered opening at 13.525,12.5 = the caught bug); against v5_r1
# board truth coincides with design and every gate goes green.
RE1_SHAFT_DESIGN = (13.525, 12.5)                         # design grid
JS1 = _REFS["JS1"]                                        # [C] (69.71, 13.37) v5_6
TP5 = _REFS["TP5"]                                        # [C] (13.525, 88.85)
LED14 = _REFS["LED14"]                                    # [C] (13.525, 79.35) LYR
USB_X = _REFS["J1"][0]                                    # [C] 42.1
RETENTION = [_REFS["H5"], _REFS["H6"], _REFS["H7"]]       # [C]
UNDERGLOW_LEDS = [_REFS[f"LED{i}"] for i in range(15, 25)]  # [C] 10 side-fire
PERKEY_LEDS = [_REFS[f"LED{i}"] for i in range(1, 14)]    # [C] reverse-mount

# =========================================================================
# 1. PARAMETERS  (values re-derived; provenance tags in comments)
# =========================================================================

# --- Z stack --------------------------------------------------------------
PLATE_TOP_TO_PCB = 5.0     # [§1] MX switch shoulder -> PCB = 5.0 (MX standard)
PLATE_T = 1.6              # [D] FR4 plate thickness. v2.1: 1.6 because the fab
#                            stocks 1.6 mm FR4, not 1.5 (owner order 2026-07-19).
#                            Plate TOP is the invariant (+5.0, switch seating);
#                            the band seat/rabbet deepens to +3.4 to absorb it.
PCB_T_DESIGN = 1.6         # [§1] design datum (real STEP board is 1.51 [S])
UNDER_PCB_CAVITY = 3.5     # [§1] B.Cu relief (2 mm PORON sheet fits under)
TRAY_T = 4.4               # [v2.11] tray floor thickness. WAS 2.4 through
#                            v2.10. Owner directive 2026-08-19:
#                              "Let's make the tray a little taller. The bases
#                               are optional and there's no reason for the tray
#                               to be flush on the bottom, if anything it might
#                               look better with a little bit of height."
#                              "I think a more pronounced gap would be better."
#                            then, refining the amount:
#                              "Though I suppose 2mm is fine if the idea is one
#                               would also typically use an optional base?"
#                            -> +2.0 mm adopted. The bases are the styling
#                            layer; the tray's plinth is a REVEAL, not a
#                            statement, so it stays small enough that an
#                            optional base still reads as the feature.
#
#                            THIS DELIBERATELY BREAKS a v1..v2.10 invariant:
#                            "tray bottom = band bottom, flush at -7.50". The
#                            tray bottom is now -9.50 and the band's stays
#                            -7.50 (see BAND_Z_BOT, which exists solely to hold
#                            it there). It also AMENDS the §2 doctrine "from
#                            the side only the band is visible": the band now
#                            floats on a 2.0 mm recessed plinth, inset
#                            (OUTER_W - TRAY_W)/2 = 5.65 mm per side, so the
#                            case reads as a floating slab rather than a solid
#                            block. Amending the doctrine is the point of the
#                            directive, not a side effect of it.
#
#                            Two structural side effects, both improvements:
#                              * base-mount pocket floor 0.8 -> 2.8 mm. That
#                                0.8 was the TIGHTEST margin in the part (its
#                                own gate floor, BASE_MOUNT_FLOOR_MIN 0.8, met
#                                with zero slack); it is no longer the binding
#                                constraint anywhere.
#                              * heat-set insert over-press buffer below the
#                                insert 3.3 -> 5.3 mm (gate is >= 3.0).
#                            Nothing ABOVE the floor moves: Z_FLOOR_TOP is
#                            derived from the PCB side (Z_PCB_BOT -
#                            UNDER_PCB_CAVITY), so the cavity, the bosses'
#                            upper geometry, the notch (z >= -1.85), the
#                            retention pins and all 14 supports are untouched,
#                            and every khana interface is unmoved.
SOCKET_DROP = 1.85         # [§1] Kailh PG151101S11 hangs 1.85 below PCB [D]

# --- Walls / outline -------------------------------------------------------
# THE single owner-tunable sidewall parameter. Nothing else needs editing to
# retune it: INNER_W/INNER_H are PCB-driven and INNER_R is FROZEN below, so no
# mating interface can move with the wall (proven, not asserted — see the v2.6
# / v2.7 docstring entries and CASE-V2-NOTES §16/§18).
#
# v2.7 (2026-07-24) DEFAULT = 5.4  — OWNER DECISION: "1.6 mm doesn't seem like
#   an especially strong corner to me" (the 3.0 wall's ARC-region corner
#   measure). The 5.4 band is the SHIPPING default: it is what goes into
#   release/ and the public agentpad13 repo, and it is the STL the
#   PCBWay reply offers as the option-A replacement file.
# v2.6 (2026-07-23) had shipped 3.0, itself the fix for PCBWay's 3D-print EQ on
#   agentpad13_v2_band_1.6mm.stl (order C-Y15W1075301A_), which flagged the
#   four corner crescents (0.737 mm — the §3/§8 cosmetic thin zone) as "too
#   thin, may break". OWNER ORDER then: "increase the sidewall thickness by
#   some amount; might even look better thicker (more visible diffuser)".
#
# SUPPORTED, GATED VARIANTS: {3.0, 5.4, 7.4}. Every one of the three has been
#   khana-built (101/101 assertions, the same 8 documented interferences) and
#   exported under its own _w{WALL} name, so no supersession is silent:
#       3.0 -> corner  1.586 (arc)   outer  90.8 x 106.6   funnel depth 0.60
#       5.4 -> corner  4.400 (flat)  outer  95.6 x 111.4   funnel depth 3.00
#       7.4 -> corner  6.400 (flat)  outer  99.6 x 115.4   funnel depth 5.00
#   Build a variant WITHOUT editing this file (the value is read exactly once,
#   here; everything downstream is derived):
#       AGENTPAD13_WALL=7.4 khana build agentpad13_case_v2.py
#   Any other positive value builds too — but only these three carry a gate
#   record. The run prints which source it used ([v2.7-WALL] ... source=...).
#
# The USB-C constraint that used to bound the wall from above is GONE: v2.6b's
#   parametric port funnel holds the plug-shell bridge at a WALL-INVARIANT
#   2.10 mm (the bare-wall tunnel would have been WALL - 0.30 = 5.10 @5.4 /
#   7.10 @7.4, past the ~6.5 mm typical plug-shell reach). The wall pick is
#   therefore PURELY AESTHETIC. Band-only change either way: the plate and tray
#   exports are byte-identical across the whole range.
WALL = 5.4                 # <- v2.7 DEFAULT (owner decision). KEEP THIS A BARE
#                            NUMERIC LITERAL ON ITS OWN LINE: gasket/
#                            gen_gasket.py reads the wall by regex
#                            (`^WALL\s*=\s*<number>`) rather than importing this
#                            module, so an expression here would break the
#                            gasket kit's constant-parse. The env override below
#                            deliberately sits on a SECOND statement, leaving
#                            this line as the file's declared default.
_WALL_ENV = os.environ.get("AGENTPAD13_WALL")
WALL_SOURCE = "v2.7 file default"
if _WALL_ENV:                                     # variant build, no file edit
    WALL = float(_WALL_ENV)
    WALL_SOURCE = f"AGENTPAD13_WALL={_WALL_ENV} (variant build)"
# --- [v2.13] PLATE-POCKET FIT — one number, one shipped band ---------------
# THE DEFECT: against the SHIPPED 100.0 plate the legacy pocket is 100.8, so
# the plate slides 0.8 mm end to end and shows the whole gap at one end —
# owner, on the assembled unit: "the gap is closer to 1mm vertically ... we
# should try to eliminate this gap ... This isn't about our existing order,
# it's about the correct moving forward."
#
# DECISION TRAIL (recorded because it reversed once):
#   1. Owner sets the target: "The plate is already 100mm. That's already the
#      final. The issue is the band's pocket, which you confirmed is 100.8? We
#      should make the pocket 100.2 then. Perhaps keep the 100.8 after all but
#      that's the low tolerance version for people with crappy printers."
#      -> Y tightens to 0.1/end; the legacy pocket survives as LOOSE.
#   2. Asked whether the WIDTH should tighten too, owner first declined:
#      "What's the current width (in what is now the loose tolerance
#      version?). That's honestly fine as is. Small visible gap but
#      tolerable."  -> a Y-only change was briefly the spec.
#   3. Owner then WITHDREW that: "Nah let's go with the original plan. 84.6 or
#      maybe 84.8. +/-0.2. Thoughts?" -> 84.6 adopted, i.e. a UNIFORM 0.1/side
#      fit on both axes and the corner radius. Rationale for symmetry over the
#      Y-only version: one number to reason about, an even 0.1 reveal all the
#      way round instead of 0.3 on the sides and 0.1 on the ends, and the
#      loose pocket was at that point still planned as a second variant — so
#      the tight path was free to be genuinely tight.
#   4. Owner then collapsed the two-variant plan to one: "I'm kind of inclined
#      to make this the only version actually. Since even on crappy printers,
#      someone can sand." -> ONE band ships. There is no `_loose` artifact.
#
# WHY ONE VERSION IS THE SAFE CALL: the two error directions are not
# symmetric. A pocket that comes out too TIGHT is correctable by anyone in
# about a minute with sandpaper. A pocket that comes out too LOOSE cannot be
# fixed at all — the plate rattles and the only remedy is reprinting the band.
# So the shipped fit is deliberately the correctable direction.
#
# IF A PRINTED POCKET IS TOO TIGHT: sand the pocket walls lightly, or raise
# THIS ONE NUMBER and re-export — the generator IS the loose variant. 0.3
# reproduces the legacy pocket on X and the corner R (with 0.4 on Y it
# reproduces the ordered band exactly; that equivalence is proven by a
# scratch-only byte-identity check each time this constant is refactored).
PLATE_FIT = 0.1            # THE fit. Uniform per side on x, y and corner R.
#                            -> pocket 84.6 x 100.2 R5.5 around the shipped
#                            84.4 x 100.0 R5.4 plate. Reveal 0.1 all round.
PCB_CLEARANCE = 0.3        # [§4] PCB edge -> band inner wall slip
OUTER_R = 8.0              # [§6] + owner 2026-07-18: "fillet ~R8" (sign-off).
#                            FROZEN at 8.0 through the v2.6 wall change: the
#                            outer fillet is a signed-off aesthetic, so the
#                            wall grows inward-of-the-arc-center, not by
#                            inflating R (see INNER_R below).
PLATE_GROOVE = 0.2         # plate undersize vs the band INNER wall, per side
PLATE_LONG_TRIM = 0.2      # [v2.13] LONG-AXIS TRIM, total (0.1 per end).
#                            THE 100.2 GHOST, KILLED AT SOURCE. Owner
#                            2026-07-21: "Resize the top plates to 100mm.
#                            That 0.2 is gonna cost us 25%. Not worth it."
#                            (the fab's <=100 mm promo tier). That trim was
#                            applied in gen_plate_fab.py ONLY, as a local
#                            subtraction, because the band was frozen at the
#                            time and PLATE_H drives the band's plate pocket.
#                            So for two years of revisions the MODEL plate was
#                            100.2 and the SHIPPED plate was 100.0, and the
#                            pocket was sized around a plate that never
#                            existed. Owner 2026-08-19, on the ~1 mm gap he
#                            measured on the assembled unit: "Is the original
#                            board really 100.2? Because the gap is closer to
#                            1mm vertically. ... we should try to eliminate
#                            this gap. ... This isn't about our existing
#                            order, it's about the correct moving forward. So
#                            no, we don't need to keep the ordered files, this
#                            is what prototyping is about." The trim now lives
#                            HERE, PLATE_H is the shipped 100.0, and
#                            gen_plate_fab.py consumes C.PLATE_H directly —
#                            proven emit-identical, so no fab file moves.
#                            Original fit rationale (owner 2026-07-18): the
#                            plate must drop into a PRINTED band despite FDM
#                            inner-cavity shrink/bulge (typ. 0.1-0.3 tight)
#                            plus fab routing up to +0.15 on the plate. That
#                            0.3/side is now the LOOSE variant; see below.
LEDGE_W = 1.2              # band rabbet ledge under the plate rim (owner
#                            2026-07-18: plate "flush with the top of the
#                            case", band "countersunk so to speak" -> the
#                            plate seats into a perimeter rabbet, supported
#                            all around, not only at the corner caps)
LEDGE_Z0 = 0.3             # ledge underside: 0.3 above PCB top; the fresh
#                            STEP shows NO F.Cu solids in the 1.2 mm rim
#                            strip [S], and band/pcb clearance >=0.25 gates it
TRAY_SLIP = 0.25           # [§4] tray floor / boss radial slip in the band

# --- Corner screw stack (chamfer-void bosses; §3/§4 values preserved) ------
BOSS_OD = 9.5              # [§4] boss OD >= 2x M3 insert OD
BOSS_C = 3.7               # boss center (c,c) on each corner diagonal: PCB
#                            chamfer slip = (14.6-2c)/sqrt2 - 4.75 = 0.341 >= 0.3
#                            (derived this session; khana-asserted below)
CAP_D = 8.6                # band corner cap Ø: seat ring 2.1 around the Ø4.4
#                            pass; ≤8.9 or it clashes the EC11 body corner
#                            (khana-caught at Ø12.4); still fuses ~1.0 into
#                            the wall corner (arc-center offset 2.263 + 4.3
#                            reaches 6.56 > inner R5.6)
CAP_Z0 = 1.5               # cap underside = tray boss top +1.5 [§3]
CAP_Z1 = PLATE_TOP_TO_PCB - PLATE_T  # cap top = plate seat (== Z_PLATE_BOT,
#                            +3.4). v2.1: was hardcoded 3.5; derived now so the
#                            caps always end exactly at the plate underside.
SOCKET_SLIP = 0.25         # [§4] tray boss in band socket (Ø9.5 in Ø10.0)
M3_INSERT_PILOT = 4.2      # [§4] CNC Kitchen std M3 pilot (4.1-4.25) [D]
M3_INSERT_DEPTH = 5.7      # [§4] CNC Kitchen std M3 length [D]
M3_SCREW_CLEAR = 3.2       # [D] ISO 273 CLOSE-fit M3 clearance (plate holes).
#                            Owner 2026-07-18: tightened from 3.4 so the four
#                            screws center the plate to ±0.1 and the 0.2
#                            reveal stays visually even (worst case 0.1/0.3
#                            instead of 0.0/0.4). Trade-off: the tray print
#                            must hold the boss pattern to ~±0.1 (calibrate
#                            slicer scale); fallback if screws fight = open
#                            the FR4 holes to 3.3/3.4 with a pin vise.
M3_PASS_BAND = 4.4         # band cap pass bore: loose, screw never threads it
M3_SCREW_D = 3.0           # [D] M3 nominal
M3_HEAD_D = 5.7            # [D] ISO 7380 button head OD
M3_HEAD_H = 1.8            # [§4] head envelope (ISO 7380 nominal 1.65)
SCREW_LEN = 8.0            # [§4] M3x8: head seat +5.0 -> tip -3.0; insert
#                            spans +1.5..-4.2 -> 4.5 mm engagement

# --- Plate openings ---------------------------------------------------------
FR4_CUTOUT = 14.0          # [§1] Cherry MX plate cutout in 1.5 FR4 [D]
STAB_HALF_SPACING = 11.938 # [D] Cherry 2U plate-mount stab spacing (+-11.9)
STAB_W, STAB_H = 6.65, 12.3  # [D] Cherry plate-mount stab cutout envelope
STAB_Y_SHIFT = 0.62        # [D] cutout center sits 0.62 south of switch center
# --- Encoder plate opening — [v2.12] WIDENED +1.0 TO THE RIGHT ONLY --------
# Owner directives 2026-08-19, verbatim and in order:
#   "1) wider hole (I'll measure to confirm, left side of hole is perfect,
#    right side needs more space)"
#   "the hole needs to be slightly rectangular, not square"
#   "And no, don't widen the hole symmetrically, widen to fit the parts."
#   "FYI the top plate hole should be 14mm (encoders were around 13.7mm).
#    Left side of the hole is alright good, just expand the width to the
#    right by 1mm."
# Convention agreed with the owner: viewed with USB-C facing UP, the owner's
# LEFT is board -x and his RIGHT is board +x (the S1/S2 switch-pin side).
# So the LEFT edge is FROZEN at x 7.025 and only the RIGHT edge moves, to
# 21.025. The opening is consequently NO LONGER CENTRED ON THE SHAFT — its
# centre sits at shaft + (ENC_OPENING_DX, 0) = (14.025, 12.500). Everything
# below derives from the SHAFT so the asymmetry can never drift.
ENC_OPENING_W = 14.0       # [owner] was 13.0; the +1.000 is all on +x
ENC_OPENING_H = 13.0       # unchanged -> y 6.000..19.000 ("slightly
#                            rectangular, not square")
ENC_OPENING_DX = 0.5       # opening centre offset from the SHAFT, +x only
#                            (half the widening — this is exactly what keeps
#                            the left edge at 7.025 while the right goes to
#                            21.025)
ENC_OPENING_R = 1.5        # [§5] house style, matches the JS opening.
#                            DO NOT enlarge R to help the knob hide the
#                            opening: a bigger corner radius eats precisely
#                            the body-corner clearance the owner's measured
#                            ~13.7 mm part needs (at R1.5 a sharp-cornered
#                            13.7 x 12.5 body is already near-tangent at the
#                            corners; at R2.0 it would bind by ~0.2). Body
#                            fit outranks cosmetics.
ENC_BODY_SQ = 11.7         # [§5] EC11E body square [D]. This is the khana
#                            INTERFERENCE PROXY and it DELIBERATELY STAYS.
#                            [v2.12] the owner measured ~13.7 mm across the
#                            pin axis on his generic encoders, but the DATUM
#                            is unresolved: a shaft-CENTRED 13.7 is
#                            contradicted by his own empirical fit ("left
#                            side of hole is perfect, right side needs more
#                            space") — that is what an OFF-centre body does,
#                            and we do not know the offset. Project rule:
#                            mechanical claims come from a primary drawing or
#                            an owner measurement, never a guessed datum. So
#                            the proxy stays 11.7 and the OPENING was sized
#                            from the owner's measured fit instead.
ENC_BODY_H = 7.5           # [§5] EC11E body height above F.Cu [D]
KNOB_D = _KNOB["od"]       # [§5][v2.17] Ø19, params-consumed. LEDGER — this
#                            constant carried an owner ruling that is now
#                            SUPERSEDED, recorded here rather than deleted:
#                            v2.12 (2026-08-19) froze Ø18 as "the floor" after
#                            the plate opening was widened +1.0 to the right,
#                            leaving a 0.310 mm sliver of opening visible at
#                            each of the two +x corners — OWNER-ACCEPTED on the
#                            grounds that "the measured body fit outranks
#                            concealment", with the Ø19 knob logged as an
#                            escape hatch that was "PARKED, not shipped".
#                            SUPERSEDED 2026-08-20: the owner reviewed the v2
#                            knob candidate set with full Ø19 concealment
#                            stated and ordered "Execute final changes to the
#                            toppers". The v2 catalog (A/B2/C) is Ø19, so the
#                            sliver is CLOSED (+0.190 concealment, matching the
#                            params' hide_floor 0.1897) and Ø18 is no longer
#                            the floor — it is retired geometry. The v2.12
#                            record itself stands in CASE-V2-NOTES §23.
KNOB_H = _KNOB["top_z"] - _KNOB["deck_z"]   # [§5][v2.17] 22.0 above the deck
#                            (top +27.0 - deck +5.0); v1 was 12.5 to top +17.5
# Derived from the SHAFT (design datum — the plate is an ORDERED artifact;
# see the DESIGN-vs-BOARD role separation at RE1_SHAFT_DESIGN).
# gen_plate_fab.py consumes ENC_OPENING_C too, so the fab file and this model
# cannot disagree about the asymmetry.
ENC_OPENING_C = (RE1_SHAFT_DESIGN[0] + ENC_OPENING_DX, RE1_SHAFT_DESIGN[1])
ENC_OPENING_X0 = ENC_OPENING_C[0] - ENC_OPENING_W / 2.0    # 7.025  FROZEN
ENC_OPENING_X1 = ENC_OPENING_C[0] + ENC_OPENING_W / 2.0    # 21.025
ENC_OPENING_Y0 = ENC_OPENING_C[1] - ENC_OPENING_H / 2.0    # 6.000
ENC_OPENING_Y1 = ENC_OPENING_C[1] + ENC_OPENING_H / 2.0    # 19.000
# The owner's ONE hard constraint, machine-checked: the left edge does not
# move. "Left side of the hole is alright good, just expand the width to the
# right by 1mm."
assert abs(ENC_OPENING_X0 - 7.025) < 1e-9, (
    f"ENC OPENING FAIL: left edge is {ENC_OPENING_X0:.4f}, owner froze it at "
    "7.025 — widen to +x only (ENC_OPENING_DX = (W - 13.0) / 2)")
assert abs(ENC_OPENING_DX - (ENC_OPENING_W - 13.0) / 2.0) < 1e-9, (
    "ENC OPENING FAIL: ENC_OPENING_DX must be half the widening or the left "
    "edge moves")
# --- v2.4 YA13 joystick: plate opening + body + THT pins + swept cap ---------
# The v4 slider (Ø16 aperture + Ø15 cage + Ø12 nub) is RETIRED — the part
# changed to a YTL YA13-FL7.4 THT tilt joystick (LCSC C37323742). Every
# envelope below cites its source; nothing is assumed.
#
# Plate opening: the asymmetric rounded rect mirrored from the ORDERED fab
# file (fab/agentpad13_v2_plate_v5.kicad_pcb, CASE-V2-NOTES §14). Frozen
# board-coord edges (y-down); fr4_plate() reproduces the fab cut exactly.
JS_OPEN_W_X = 58.91        # West x  = JS1.x - 10.80  [fab §14]
JS_OPEN_N_Y = 2.57         # North y = JS1.y - 10.80  [fab §14]
JS_OPEN_E_X = 77.36        # East x  = JS1.x + 7.65   [fab §14]
JS_OPEN_S_Y = 21.02        # South y = JS1.y + 7.65   [fab §14]
JS_OPEN_R = 1.5            # corner R (house style = encoder opening) [fab §14]
# Body envelope — faithful CROSS (13x13 frame + West/North pot boxes + East/
# South corner-tab bumps), NOT a filled bbox: the pots sit on the W+N faces
# only, so the bbox corners are void (a filled square would false-interfere
# with the plate opening's R1.5 corners AND the NE screw boss — both void in
# the real part). Source: height-extraction report 2026-07-20 + v5_6 F.Fab.
JS_FRAME_HALF = 6.5        # 13x13 F.Fab frame half-extent [v5_6 F.Fab ±6.5]
JS_WN_EXTENT = 10.5        # W+N pot-box + retention-tab reach from stick center
#                            (F.Fab bbox 9.3 + tab lobes to 10.5) [ext report]
JS_ES_EXTENT = 7.4         # E+S bbox reach = frame + corner tabs
#                            (F.Fab bbox local -7.4) [v5_6 F.Fab bbox]
JS_POT_HALF = 4.5          # pot-box / edge-tab half width — conservative
#                            envelope covering the 3 THT pot pads + margin [R]
JS_BODY_Z1 = 11.1          # full body/pot-box height above PCB top [ext report]
JS_PIN_Z_BOT = -3.71       # THT tail bottom = -1.51 (board underside) - 2.2
#                            (pin length 3.7 from PCB-top seating) [DRAWING].
#                            Pin xy + Ø are PARSED from v5_6 (JS1_PADS above).
LYR_HOLE_D = 3.0           # [§6] LYR light hole Ø3 over LED14 [C]

# --- v2.17 Stick toppers — BOTH shipped parts are modelled ------------------
#     CONSUMED from stick_topper_v2_params (do not modify). The v2 family
#     ships TWO stick toppers, and they have DIFFERENT throws, so one envelope
#     cannot represent both:
#       nub_C2   — the shipped DEFAULT. Ø6.189 straight cylinder +14.4..+19.6,
#                  NO restrictor: sized by bisection so the FULL 30° mechanical
#                  throw stays 0.25 off SW4. Drives js_sweep / stick_cap.
#       puck_TPU — the one-piece TPU puck. Ø9.412, and its 22.5° cone land IS
#                  the restrictor (integral), so it swings the pot's electrical
#                  half-angle, not the mechanical one. Drives js_sweep_puck.
#     Modelling only the default would leave the case BLIND to the larger of
#     the two shipped envelopes (coordinator ruling 2026-08-20).
#
#     pivot_z / tilt angles are NOT in the v2 params file, so they are stated
#     here from the YA13 drawing [D] and then CROSS-CHECKED below against
#     numbers the params DO publish. The cross-checks are load-bearing, not
#     decorative: they re-derive deck_low_z / cone_z_at_bore from these three
#     constants, so a wrong pivot, a wrong tilt or a wrong fillet all fail at
#     import instead of silently shrinking a swept envelope.
STICK_PIVOT_Z = 6.1        # [D YA13 front elev, dim "6.1"] gimbal pivot
STICK_TILT_DEG = 30.0      # [D YA13 "60 deg" mechanical fan / 2] full throw
STICK_TILT_RESTRICTED_DEG = 22.5   # [D YA13 spec 1.1] pot electrical 45°/2 —
#                            the angle the puck's own cone land enforces
STICK_TOP_STYLE = "nub"    # shipped default; dome/taper below are v1 ALTERNATES
STICK_CAP_R = _SV["od"] / 2.0              # 3.0945 (nub Ø6.189 / 2)
STICK_CAP_Z0 = _STICK["socket_mouth_z"]    # +14.4 cap bottom (socket mouth)
STICK_CAP_Z1 = _STICK["cap_top_z"]         # +19.6 cap top
NUB_FILLET_R = 0.3         # [TOPPER stick_topper_v2.nub_profile] bottom radius
#                            (VALIDATED by the deck_low_z cross-check below)
# Cross-check 1 — the nub. Its lowest swept point rides the bottom fillet, so
# the extremum is (rotated fillet centre) - fillet R. Params publish 11.851.
_th_full = math.radians(STICK_TILT_DEG)
_nub_low_z = (STICK_PIVOT_Z
              - (STICK_CAP_R - NUB_FILLET_R) * math.sin(_th_full)
              + (STICK_CAP_Z0 + NUB_FILLET_R - STICK_PIVOT_Z) * math.cos(_th_full)
              - NUB_FILLET_R)
assert abs(_nub_low_z - _SV["deck_low_z"]) < 1e-3, (
    f"STICK PIVOT/TILT FAIL: pivot {STICK_PIVOT_Z} + tilt {STICK_TILT_DEG}° + "
    f"fillet {NUB_FILLET_R} re-derive the nub's swept floor as "
    f"{_nub_low_z:.4f}, but stick_topper_v2_params publishes deck_low_z "
    f"{_SV['deck_low_z']} — one of the three is wrong; do NOT trust js_sweep")
# --- v2 TPU puck: params-consumed outer silhouette (the SW4 gate's own) -----
PUCK_R = _PV["od"] / 2.0                   # 4.706 max radius
PUCK_TOP_Z = _PV["top_z"]                  # +19.6
PUCK_RIM_R = _PV["rim_roll_r"]             # 0.6 top edge roll
PUCK_WALL_BOT_Z = _PV["wall_bot_z"]        # +18.0 bottom of the max-OD wall
PUCK_SHOULDER_BOT_Z = _PV["shoulder_bot_z"]  # +16.4 bottom of the inward taper
PUCK_BODY_R = _PV["body_od"] / 2.0         # 3.8 lower straight cylinder
PUCK_LAND_R_IN, PUCK_LAND_R_OUT = _PV["land_r"]          # 2.6 / 3.6
PUCK_SEAT_Z = _PV["deck_low_z"]            # +10.5 where the cone lands flat
PUCK_DASH_OUT_R = _PV["dashes"]["r1"] + _PV["dashes"]["width"] / 2.0   # 3.25
PUCK_RIM_SEGMENTS = 8      # chords across the 90° rim roll. A BOOLEAN-
#                            ROBUSTNESS setting, NOT a fidelity knob: at 24 the
#                            sweep's 25-way fuse silently loses 59.44 mm^3, at
#                            8 it is exact. 8 also puts a sample exactly on the
#                            22.5° governing point (90°·(1 - 6/8) = 22.5°),
#                            which _puck_cap asserts. See _revolve_rz.
_PUCK_SEAT = _PV["seat_ladder"][_PV["default_rung"]]
# Cross-check 2 — the puck. Its 22.5° cone land is defined so the WHOLE radial
# generator lands flat at PUCK_SEAT_Z: z(r) = piv + (seat - piv)/cos t + r*tan t.
# Re-derive the bore-edge height and match the published cone_z_at_bore.
_th_res = math.radians(STICK_TILT_RESTRICTED_DEG)


def _puck_land_z(rho):
    """Underside-cone height at plan radius `rho` [TOPPER land_z]."""
    return (STICK_PIVOT_Z + (PUCK_SEAT_Z - STICK_PIVOT_Z) / math.cos(_th_res)
            + rho * math.tan(_th_res))


assert abs(_puck_land_z(PUCK_LAND_R_IN) - _PUCK_SEAT["cone_z_at_bore"]) < 1e-3, (
    f"PUCK PIVOT/TILT FAIL: pivot {STICK_PIVOT_Z} + restricted tilt "
    f"{STICK_TILT_RESTRICTED_DEG}° re-derive the cone at the bore edge as "
    f"{_puck_land_z(PUCK_LAND_R_IN):.4f}, but the params publish "
    f"{_PUCK_SEAT['cone_z_at_bore']} — do NOT trust js_sweep_puck")
assert _PUCK_SEAT["safe"], (
    f"PUCK SEAT FAIL: default rung {_PV['default_rung']} is not marked safe "
    "in the params seat_ladder")
# --- v1 ALTERNATE cap envelopes (dome / taper) ------------------------------
# RETIRED with the v1 topper family (archive/toppers-v1/) and unreachable while
# STICK_TOP_STYLE == "nub". Kept, not deleted, so the v2.4/v2.5 envelopes stay
# reproducible from this file; their params are no longer on the live tree, so
# the constants below now degenerate to the nub's own Ø and are NOT meaningful
# taper geometry — re-derive from the archived params before reviving them.
STICK_DOME_RISE = 2.2                      # dome shaping rise [v1 stick_cap.py]
STICK_TAPER_BOT_D = _SV.get("taper_bottom_d", 2 * STICK_CAP_R)      # v1 only
STICK_TAPER_SPRING_D = _SV.get("taper_spring_d", 2 * STICK_CAP_R)   # v1 only
STICK_TAPER_SPRING_Z = _SV.get("taper_spring_z", STICK_CAP_Z1)      # v1 only

# --- v2.17 Encoder knob (the v2 catalog: A_helical_knurl / B2_scoop /
#     C_cross_hatch, all Ø19) — CONSUMED from encoder_knob_v2_params (do not
#     modify). Static envelope on the shaft. The three textures share one
#     envelope; the loop at the loader asserts that they still do. ----------
KNOB_OD = _KV["od"]                        # 19.0 outer Ø  (v1 was 18.0)
KNOB_SKIRT_Z0 = _KV["bottom_z"]            # +8.0 skirt bottom (clears body top)
KNOB_TOP_Z_ABS = _KV["top_z"]              # +27.0 knob top (v1 was +17.5)
# [v2.12] MAX corner reach from the SHAFT. Now ASYMMETRIC because the opening
# is: the two -x arc centres sit at (-5.0, +-5.0) from the shaft -> reach
# 7.071 + 1.5 = 8.571 (UNCHANGED — the left edge is frozen); the two +x arc
# centres moved to (+6.0, +-5.0) -> reach sqrt(61) + 1.5 = 9.310. Consumers
# want the worst case, so this is the MAX. Both are re-derived and asserted
# against the params file at import.
# [v2.17] the v2 params publish these as ONE dict keyed by side, replacing the
# v1 scalar + _min pair. Same two numbers, same meaning.
ENC_OPENING_CORNER_REACH = _KNOB["opening_corner_reach"]["plus_x"]    # 9.3102
ENC_OPENING_CORNER_REACH_MIN = _KNOB["opening_corner_reach"]["minus_x"]  # 8.5711
_ecr = [math.hypot(ENC_OPENING_C[0] + sx * (ENC_OPENING_W / 2.0 - ENC_OPENING_R)
                   - RE1_SHAFT_DESIGN[0],
                   ENC_OPENING_H / 2.0 - ENC_OPENING_R) + ENC_OPENING_R
        for sx in (-1.0, 1.0)]
assert abs(max(_ecr) - ENC_OPENING_CORNER_REACH) < 5e-4, (
    f"ENC REACH FAIL: geometry says max {max(_ecr):.4f}, encoder_knob_v2_params "
    f"says {ENC_OPENING_CORNER_REACH} — regenerate the params or fix the "
    "opening")
assert abs(min(_ecr) - ENC_OPENING_CORNER_REACH_MIN) < 5e-4, (
    f"ENC REACH FAIL: geometry says min {min(_ecr):.4f}, encoder_knob_v2_params "
    f"says {ENC_OPENING_CORNER_REACH_MIN}")

# --- v2.4 MX switch body envelope (Cherry MX seated in the plate). [MX]/[D] --
SW_FLANGE = 15.8           # top flange square, rests on the deck [MX]
SW_FLANGE_Z0, SW_FLANGE_Z1 = 5.0, 5.9      # flange z band (on the plate top)
SW_UPPER_SQ = 14.8         # upper housing (conservative max of 14.8->11 taper)
SW_UPPER_Z1 = 8.4          # upper housing top z [MX]
SW_STEM_D = 7.0            # stem-zone proxy Ø [MX, conservative]
SW_STEM_Z1 = 11.6          # stem-zone top z [MX]
SW_LOWER_SQ = 13.9         # lower housing (inside the 14.0 plate cutout) [MX]

# --- v2.4 Keycaps (envelope proxies). [CONVENTION] --------------------------
KEYCAP_1U = 18.0           # 1U cap footprint (19.05 pitch - 1.05) [CONVENTION]
KEYCAP_2U = 37.1           # 2U cap = 1U + 19.05 = 18.0 + 19.05 [CONVENTION]
KEYCAP_Z0, KEYCAP_Z1 = 10.6, 14.6   # cap underside .. top above PCB [CONVENTION]

# --- USB (J1 bottom-mounted; v2.2 = the v5_5 FLIP: mouth faces the wall) ----
USB_CUTOUT_W = 10.0        # [§5] band aperture width (band UNCHANGED in v2.2)
USB_CUTOUT_Z0, USB_CUTOUT_Z1 = -5.0, -1.4   # [§5] aperture span
USB_RECEPT_W = 9.6         # [V5] flipped-body x envelope 37.3..46.9 (was 9.0
#                            shell-only; the wider box is the frozen v5_5 plan
#                            envelope incl. the plastic body/peg lugs)
USB_RECEPT_DEPTH = 7.3     # [V5] fab body depth (face -0.49 .. rear 6.81)
USB_FACE_PROUD = 0.60      # [V5] mating face y = -0.60: PROUD of the board
#                            edge — THE convergence number with the board
#                            executor's AUTHORIZED v5_5 run (anchor 3.05;
#                            supersedes the 0.49 plan value; case-side
#                            max-proud is the outer wall at 2.7, nowhere
#                            near — more proud = easier plug seating).
#                            Sign tripwire in usb_receptacle() guards the
#                            flip direction.
# --- v2.6 USB PORT FUNNEL (outer counterbore; owner directive 2026-07-23) ---
# WHY: the sidewall is an owner-tunable aesthetic (3.0 / 5.4 / 7.4 under
# consideration) but a USB-C plug's metal shell only reaches ~6.5 mm past its
# overmold face (~5 mm is the comfortable seating reach). A bare thick wall
# would bury the receptacle. The funnel DECOUPLES the two: a rectangular
# counterbore on the band's OUTER face whose depth AUTO-TRACKS the wall
# (WALL - USB_FUNNEL_WEB), so the inner web the shell must bridge is ALWAYS
# USB_FUNNEL_WEB + PCB_CLEARANCE - USB_FACE_PROUD = 2.10 mm, at ANY wall. The
# pocket bottom therefore always sits at the ORIGINAL 2.4-wall outer plane
# (y = -2.7) and the plug overmold seats flat on it. The funnel VANISHES at
# WALL == 2.4 (depth 0) — this is a pure superset of the v2.5 geometry.
# The inner aperture (USB_CUTOUT_W x z, through the web) is UNCHANGED.
USB_FUNNEL_W = 13.0        # pocket width: USB-IF plug overmold max 12.35 [D]
#                            + 0.65 clearance (print slop + hand alignment)
USB_FUNNEL_H = 7.0         # pocket height: overmold max 6.5 [D] + 0.5
USB_FUNNEL_LEAD = 1.0      # 45° chamfered lead-in leg on the pocket mouth
#                            edges (self-supporting print: the pocket ceiling
#                            becomes a 45° slope instead of a flat bridge;
#                            the lead-in is CLAMPED to the pocket depth, so a
#                            shallow funnel is all-chamfer and has no flat
#                            ceiling at all)
USB_FUNNEL_FLOOR_MIN = 0.8  # band material that must remain under the pocket
#                            (pocket floor z -> band bottom z). The BOTTOM
#                            lead-in leg is clamped by this and evaluates to
#                            0.0 at the shipped dimensions — see usb_funnel().
#                            0.8 is the GEOMETRIC MAXIMUM, not a preference:
#                            band bottom -7.50; a max-size USB-C overmold
#                            (12.35 x 6.5 [D]) centered on the receptacle
#                            (-3.23) has its bottom face at -6.48, so a
#                            closed-bottom pocket can never leave more than
#                            1.02, and a centered 0.5 mm height clearance
#                            leaves exactly 0.8. That 0.8 x 0.6 x 13 step is
#                            bonded to the full wall over its whole back face
#                            (a step, not a free-standing fin like the retired
#                            0.737 crescent), but it IS what the printability
#                            sampler now reports for the funnelled band. Lever
#                            if it ever needs to go: ramp the pocket floor out
#                            to the band bottom — no step, at the price of a
#                            13 mm scallop in the band's bottom outer edge.
#                            MEASURED reason, not taste: a 1.0 bottom leg on a
#                            pocket whose floor sits only 0.8 above the band
#                            bottom leaves a 45° knife-edge wedge — khana read
#                            the band min_wall at 0.566 mm (WORSE than the
#                            0.737 crescent PCBWay rejected) and OCCT then
#                            refused the elephant-foot chamfer on that edge.
#                            At WALL >= 4.9 the 9.0-tall mouth would also have
#                            broken out through the band's bottom face. The
#                            bottom edge is an upward-facing floor: it needs no
#                            lead-in for printability (no overhang) and none
#                            for insertion (the plug drops in from above the
#                            floor line). Top/left/right keep the full leg.
USB_FUNNEL_WEB = 2.4       # the web held constant = the ORIGINAL stock wall.
#                            Do not retune this to "recover" wall thickness at
#                            the port: 2.4 + 0.3 - 0.60 = 2.10 mm of shell
#                            bridge is the number the v2.2..v2.5 band shipped
#                            and the one the USB gates were written against.
USB_RECEPT_Z0, USB_RECEPT_Z1 = -4.86, -1.6  # [§5] receptacle z envelope
#                            (z is flip-invariant: rotation is about the z axis)

# --- Keep-outs for parts with no STEP model (positions [C], dims [D]/[§]) ---
SOCKET_X, SOCKET_Y = 14.5, 5.89   # [§1] Kailh socket body [D]
LED_SIDE_BOX = 5.0         # SK6812-SIDE class, conservative square envelope
LED_SIDE_Z0, LED_SIDE_Z1 = -3.4, -1.595
LED_RM_BOX = 3.5           # reverse-mount per-key LED envelope
LED_RM_Z0, LED_RM_Z1 = -3.6, -1.595

# --- PCB retention (owner model: board floats, pins locate) -----------------
PIN_D = 2.0                # [§8] press pin Ø2.0 into the Ø2.2 NPTH [R]
PIN_TOP = -0.3             # [§8] pin stops 0.3 below PCB top (spec gate)
SUPPORT_BOSS_D = 4.0       # [§8] backs the board during switch insertion

# --- Discrete PCB edge supports (v2.10, 2026-08-19) -------------------------
# THE v2.3 CONTINUOUS RAIL IS GONE. It was a closed ring standing 0.2..1.7
# inboard of the octagon over the FULL cavity height (-5.10 -> -1.51), i.e.
# a 3.59 mm tall wall parked directly in the beam of the ten SK6812-SIDE
# underglow LEDs. Those parts emit IN-PLANE, sideways into the frosted band
# — the band IS the diffuser — so a wall at the board edge is not "near"
# the light path, it IS the light path. Measured on the v2.3 geometry
# before the change: the rail's outboard face occupied 307.7 of the 335.0
# mm octagon perimeter (91.8 %), and only ~13-16 % of the band's inner
# perimeter still had line-of-sight to any lens.
#
# Owner directives (2026-08-19), verbatim:
#   "the lip around the edge holding the PCB covers up the LEDs so it needs
#    to instead be replaced by a series of 'columns' all around the edge
#    with just a few per side"
#   "We should just have the corner support the PCB and maybe a few short
#    segments along the edges, not a continuous lip."
RAIL_INSET0 = 0.2          # support outboard face: 0.2 inboard of the
#                            octagon edge (stays under the rim across the
#                            ±0.3 slip) — unchanged meaning from v2.3
RAIL_SUP_D = 2.0           # support RADIAL depth (0.2 -> 2.2 inboard).
#                            DEEPER than the old 1.5 rail on purpose: radial
#                            depth costs no light (only TANGENTIAL length
#                            shadows the band), and 2.0 prints as a sturdier
#                            tower than 1.5 at the same 3.59 mm height.
RAIL_INFL = 0.75           # xy keep-out margin to component / pad envelopes
#                            (covers the ±0.3 slip + envelope conservatism)
RAIL_LED_INFL = 1.0        # xy keep-out margin around the 10 side-fire LED
#                            packages. This is BODY clearance only — the
#                            OPTICAL rule is structural, not a margin: no
#                            support may stand in front of a lens at all.
#
# RE1 RELIEF DELETED (owner: "the cutout for the rotary encoder is pointless
# and doesn't fit the profile of the pins anyway so get rid of it" / "I'm
# telling you just get rid of it. It's pointless and doesn't even align.").
# The retired v2.3 relief constant (deleted, so it greps to zero) cut five
# r2.75 circles at RE1's THREE encoder + TWO switch solder tails. But the
# footprint has SEVEN through-holes: the two MP mounting posts at
# (13.525, 6.9) and (13.525, 18.1) carry the LARGEST drills on the part
# (2.80 vs 1.00) and were NEVER relieved — the relief was both unnecessary
# and wrong. No support passes under RE1 now; instead the (0,0) chamfer
# pad's clearance to every one of the seven RE1 pads is machine-checked in
# _verify_rail_supports().
#
# Support table: (cx, cy, tangential_len, rot_deg). Chamfer pads sit on the
# four corner arcs the Ø9.5 screw bosses already black out (free light-wise),
# each slid along its chamfer away from the nearest hazard (RE1 tail cluster,
# JS1 THT pads, LED20, LED21). Edge columns sit in the dark gaps between the
# LED beam windows, clear of USB, the JS1 pads and the service slots.
RAIL_SUPPORTS = [
    (11.929,  2.968, 6.0, -45.0),  # (0,0) chamfer pad - clear of RE1 pads
    (81.231, 13.329, 6.0,  45.0),  # (84.2,0) chamfer pad - clear of JS1 pads
    (70.349, 97.555, 4.5, -45.0),  # (84.2,100) chamfer pad - clear of LED20
    ( 8.151, 91.854, 6.0,  45.0),  # (0,100) chamfer pad - clear of LED21
    (20.5,    1.2,   5.0,   0.0),  # top W: RE1 cluster .. LED15 outward cone
    (63.5,    1.2,   5.0,   0.0),  # top E: LED16 outward cone .. JS1
    ( 1.2,   30.0,   5.0,  90.0),  # left: chamfer .. LED24
    ( 1.2,   50.0,   5.0,  90.0),  # left: LED24 .. LED23
    ( 1.2,   70.0,   5.0,  90.0),  # left: LED23 .. LED22
    (83.0,   25.0,   5.0,  90.0),  # right: JS1 .. LED17
    (83.0,   43.0,   5.0,  90.0),  # right: LED17 .. LED18
    (83.0,   62.0,   5.0,  90.0),  # right: LED18 .. LED19
    (32.0,   98.8,   5.0,   0.0),  # bottom W: LED21 .. LED20 gap
    (50.0,   98.8,   5.0,   0.0),  # bottom E: LED21 .. LED20 gap
]
# DEVIATION FROM THE FIRST-CUT TABLE, recorded here because it is a real
# measurement and not a preference: the two TOP-edge columns were specified
# at x 23.5 and x 60.5. Both OVERLAPPED the ±60° outward beam cones of
# LED15 (32, 4.35) and LED16 (52, 4.35) — check 3 in _verify_rail_supports
# measured hard zero clearance at both. LED15/LED16 are the only two of the
# ten side-fire parts aimed OUTWARD (-y, into the near band wall: the
# deliberate USB accent), so a column in front of them is exactly the defect
# this rev exists to remove. Each was slid tangentially along its own edge
# by the permitted 3.0 mm — 23.5 -> 20.5 and 60.5 -> 63.5 — which is the
# position of MAXIMUM cone clearance available inside that allowance
# (+0.986 mm at both). Lengths, depths and every other support are as
# specified.

# --- Tray features -----------------------------------------------------------
NOTCH_MIN_SLIP = 0.3       # tray/pcb gate floor: any corner boss whose round
#                            profile gives less slip than this gets a 45° flat
NOTCH_CLEAR = 0.35         # built board-corner -> notch-flat clearance [V5]
NOTCH_Z0 = -1.85           # [v2.10] BACK to the v2.2 board-passage-only
#                            depth. v2.3 drove the flat the FULL boss height
#                            (to -8.5, through the tray bottom) for exactly
#                            one reason: the v2.2 shallow notch left the
#                            LOWER boss full-round, and the then-continuous
#                            perimeter rail's corner segment hit it
#                            (khana-caught, 2.79 mm^3). That rail no longer
#                            exists. Its replacement, the v2.10 (0,0)
#                            chamfer pad, clears a FULL-ROUND Ø9.5 boss by a
#                            measured +0.694 mm (exact: both solids are
#                            z-prismatic over the overlap, so the 2D
#                            polygon distance IS the 3D distance), so the
#                            flat's only remaining job is board passage:
#                            the board corner occupies z -1.51..0 and the
#                            flat now starts 0.34 below it.
#                            TWO THINGS THIS FIXES. (1) The full-height flat
#                            sliced the boss cylinder's cap clean through
#                            the 2.4 mm floor, leaving a 3.94 mm^2 crescent
#                            through-hole at the encoder corner (measured on
#                            the exported STL; analytic cap 3.970 mm^2) —
#                            the last remnant of the owner's "square hole"
#                            report, whose main body was the unbounded notch
#                            cutter fixed in tray(). Gone: the floor there
#                            is now continuous. (2) The insert-bore wall is
#                            full thickness (4.75 - 2.1 = 2.65) below -1.85
#                            again; the 1.6512 mm thin band now spans only
#                            the notch's top zone instead of the whole
#                            insert depth, which improves the standing
#                            first-article watch-item, and the SJ61A1
#                            bumpon lands on a truly full Ø9.5 boss bottom.
#                            The flat itself is UNMOVED: same plane, same
#                            NOTCH_CLEAR, same standoff — the standoff
#                            arithmetic in _boss_notches() is z-independent,
#                            so notch_insert_wall stays 1.6512.
SVC_CLEAR = 0.5            # service slot clearance around the tact solids [S]
SVC_TOOL_R = 1.0           # slot corner R: at R1.0/0.5 the corner arc clears
#                            the tact box corner (R1.5/0.4 clipped it by 0.06,
#                            khana-caught as a 0.02 mm^3 sliver)
# WEIGHT POCKET — RETIRED in v2.9. It was a 60 x 30 x 1.6 cavity-side relief
# at (42.1, 58.0) for "washers/bar stock + epoxy"
# (docs/handoff-2026-07-15-case-lighting-assembly.md), never ordered, never
# gated, and flagged in its own comment as "3 mm steel = open item" — i.e. the
# 1.6 depth never fit the steel it was drawn for. It occupied x 12.1..72.1,
# y 43..73, which is EXACTLY the centre of the floor, so it was the single
# obstruction to a central base interface, and it left only 0.8 mm of floor
# across 1800 mm^2 — the largest thin region in the part everything else bolts
# to. A base carries ballast better in every way (an order of magnitude more
# mass, reversible, no epoxy, and BELOW the desk plane rather than 6 mm above
# it). Retiring it restores the full 2.4 mm floor. Ballast now lives in the
# base; see bases/agentpad13_base.py BALLAST_* and CASE-V2-NOTES §22.4.
EFC_CHAMFER = 0.4          # [§4] elephant-foot chamfer on bed-side edges

# --- v2.9 BASE MOUNT INTERFACE — a PUBLISHED CONTRACT, not a detail --------
# Owner directives. 2026-08-19, on the v2.8 corner-boss design:
#   "No magnets, either just alternative trays or notches in the tray where
#    bases can insert, whether TPU or hard filaments."
#   "I'm just saying why is the base so big? Why don't we have the notche
#    closer to the middle to enable a variety of styles perhaps even a
#    circular pedestal like the actual Codex Micro."
#   "A full footprint variety is fine too. Just saying regardless, we should
#    have more flexibility in the bases this way esp if this is open source
#    people can make their own."
#
# v2.8 put the interface at the four CORNER BOSSES. That was the defect: it
# did not make big bases wrong, it made big bases MANDATORY, because the only
# attachment points were 91 mm apart. Moving the pattern inboard decouples the
# interface from the footprint — a base may now be a Ø150 grip mat or a Ø70
# pedestal and neither is privileged.
#
# THE CONTRACT (everything a third party needs; full spec in §22):
#   datum   : (CX, CY) — the centre of the case outline in plan. The band
#             outer (OUTER_W x OUTER_H) and the tray outline (TRAY_W x TRAY_H)
#             are BOTH centred there, so it is findable with a ruler on a
#             finished case; no source read required.
#   mating  : the flat TRAY bottom plane, z = Z_TRAY_BOT (v2.11: -9.5; it was
#             -7.5 and flush with the band through v2.10 — the plinth moved it
#             down 2.0. Bases mate to a physical surface, so the contract is
#             unaffected: same Ø, same pitch, same datum, 2.0 mm lower.)
#   feature : 4 blind flat-bottomed cylindrical pockets, Ø BASE_MOUNT_D x
#             BASE_MOUNT_DEPTH deep, axes +Z, at the corners of a
#             BASE_MOUNT_PITCH square centred on the datum.
#   fit     : CAD-nominal on the tray side. ALL fit allowance lives on the
#             PEG, as a printed ladder (bases/agentpad13_base.py PEG_LADDER) —
#             the same doctrine as the encoder-knob bore and the stick cap.
#
# Chosen over every alternative considered, on stranger-printability:
#   * 4 plain round pockets beat a keyed recess / dovetail ring / bolt circle
#     with a boss, because a round blind hole is the ONE feature every FDM
#     printer makes predictably, and its error is a single number a builder
#     can measure with calipers and correct on the peg.
#   * Ø6.0 beats the v2.8 Ø3.6: for a press fit the hoop strain goes as
#     (interference / D), so for a given absolute dimensional error a LARGER
#     bore is the MORE forgiving one. It also doubles the bearing area.
#   * MAGNETS STAY REJECTED (v2.8 arithmetic, unchanged and not revisited):
#     a Ø6 pocket necks the notched (0,0) boss wall to 0.651 against a
#     1.6512 minimum that is already a first-article watch-item.
#
# The pattern is 4-fold symmetric ON PURPOSE: a base mounts in any of four
# 90° orientations, so one printed wedge tilts four ways.
BASE_MOUNT_D = 6.0          # pocket Ø (tray side, CAD nominal)
BASE_MOUNT_DEPTH = 1.6      # pocket depth below Z_TRAY_BOT. PUBLISHED
#                             CONTRACT — frozen at 1.6; third-party pegs are
#                             cut to it. Originally set EQUAL to the retired
#                             weight pocket's depth, when it left only 0.8 mm
#                             of floor over 113 mm^2 (the relief this design
#                             had already accepted over 1800 mm^2). [v2.11]
#                             that justification is now MOOT, not merely
#                             satisfied: the plinth leaves 2.8 mm of floor
#                             above each pocket, so the depth is no longer
#                             trading against floor strength at all.
BASE_MOUNT_PITCH = 25.0     # square pitch -> ±12.5 from the datum;
#                             circumscribed Ø35.36, so ANY base from ~Ø42
#                             upward carries the whole pattern. Deliberately
#                             smaller than the minimum stable free-standing
#                             pedestal (§22.3) so the PATTERN never sets the
#                             minimum base size — the physics does.
BASE_MOUNT_FLOOR_MIN = 0.8  # asserted: floor left above every pocket
BASE_MOUNT_KEEPOUT = 2.0    # asserted: pocket wall -> every other tray
#                             feature (support-boss roots, service slots,
#                             corner bosses, the tray edge)

_OVER = 1.0                # subtractive over-cut

# =========================================================================
# 2. DERIVED
# =========================================================================

Z_PLATE_TOP = PLATE_TOP_TO_PCB                    # +5.0
Z_PLATE_BOT = Z_PLATE_TOP - PLATE_T               # +3.5
Z_PCB_BOT = -PCB_T_DESIGN                         # -1.6 (design)
REAL_PCB_BOT = PCB.BOARD[5]                       # -1.51 [S]
Z_SOCKET_BOT = Z_PCB_BOT - SOCKET_DROP            # -3.45
Z_FLOOR_TOP = Z_PCB_BOT - UNDER_PCB_CAVITY        # -5.1
Z_TRAY_BOT = Z_FLOOR_TOP - TRAY_T                 # v2.11: -9.5 (was -7.5)
BAND_Z_BOT = -7.5          # [v2.11] FROZEN. The band's bottom plane, DECOUPLED
#                            from the tray's. Through v2.10 these were the same
#                            number and band() simply used Z_TRAY_BOT — which
#                            was safe only while the two parts were flush. The
#                            v2.11 plinth (TRAY_T 2.4 -> 4.4) moves the TRAY
#                            bottom to -9.5; the band is ORDERED and must not
#                            move by so much as a micron, so every band-side
#                            consumer now reads BAND_Z_BOT instead:
#                              band()      outer prism, inner cavity, shell clip,
#                                          boss sockets, bottom EFC chamfer
#                              usb_funnel() the lead_bot floor clamp
#                                          (USB_FUNNEL_FLOOR_MIN is measured up
#                                          from the BAND bottom, not the tray's)
#                            Gate: stl/agentpad13_v2_band_1.6mm_w5.4.stl must
#                            stay md5 34be6bf79a6bb81995807448639f4822.
#                            If the band ever needs its own height change, edit
#                            THIS constant — never TRAY_T.

INNER_W = PCB_W + 2 * PCB_CLEARANCE               # 84.8
INNER_H = PCB_H + 2 * PCB_CLEARANCE               # 100.6
OUTER_W = INNER_W + 2 * WALL                      # v2.7: 95.6 @5.4 (90.8 @3.0,
OUTER_H = INNER_H + 2 * WALL                      # v2.7: 111.4 @5.4  89.6 @2.4)
INNER_R = 5.6                                     # FROZEN v2.6. WAS
#   `OUTER_R - WALL` (= 5.6 @ WALL 2.4), which made the inner and outer corner
#   arcs concentric. That expression is WALL-driven, and TWO FROZEN ARTIFACTS
#   hang off it: PLATE_R = INNER_R - 0.2 = 5.4 (the ORDERED FR4 plate's corner
#   radius — fab files already at PCBWay) and TRAY_R = INNER_R - 0.25 = 5.35
#   (the banked tray_v5 STL; md5 was d7d16481df24bae4c7769d7624dfc620 through
#   v2.7, now 2e4d510381c7a4420d46ce741a22fe22 after the v2.8 base pockets —
#   TRAY_R itself is unmoved, see §21). Letting
#   INNER_R follow WALL to 5.0 would silently re-cut both. Pinned at 5.6, the
#   sidewall parameter cannot move ANY mating interface. Consequence: with
#   WALL > 2.4 the arcs are no longer concentric — the outer arc center slides
#   outboard by (WALL - 2.4) per axis, so the corner wall is THICKER than the
#   flat, never thinner (@3.0: 3.000 on the flats rising to 3.249 on the
#   diagonal; the band min wall stays the flat 3.000).
CX, CY = PCB_W / 2.0, PCB_H / 2.0                 # 42.1, 50.0

# =========================================================================
# [v2.14] THE BAND'S MIRROR-IMMUNITY INVARIANT — READ BEFORE MOVING THE USB
# =========================================================================
# The design frame is LEFT-handed (x right, y DOWN from raw KiCad board
# coords, z up) while STL/STEP are right-handed, so every solid exported
# through this path is the ENANTIOMORPH of the intended part. The TRAY is
# corrected for this at export (v2.10: `Pos(0, PCB_H, 0) * mirror(...,
# Plane.XZ)`) because the printed tray came out the wrong hand. The BAND is
# exported UN-mirrored and is nevertheless correct. That is not luck, and it
# is not an oversight — it holds for a specific, checkable reason:
#
#   A solid that possesses ANY mirror plane is ACHIRAL: its enantiomorph is
#   congruent to itself by a rigid motion. The band has an exact mirror
#   plane at x = CX. Composing the export reflection (about XZ, y -> -y)
#   with the band's own x-mirror gives (x, y) -> (-x, -y), i.e. a pure 180
#   deg rotation about z. So the "wrong-handed" band IS the right band,
#   merely rotated — and the USB hole tells you which way round it goes.
#
# MEASURED, not assumed (2026-08-19, CAD booleans on the v2.13 band):
#   band  vs mirror about x = 42.1 : (a-b) 0.000000 and (b-a) 0.000000 mm^3
#                                    -> the mirror plane is EXACT
#   tray  vs mirror about x = 42.1 : 1034.23 mm^3  -> chiral, hence its fix
#   band  vs mirror about y = 50.0 :  373.57 mm^3  -> NOT y-symmetric, and it
#                                    does not need to be: achirality needs
#                                    only ONE plane, and the USB feature is
#                                    what breaks y while being centered in x.
#
# The x mirror plane exists ONLY because every x-asymmetric candidate feature
# is centered on x = CX. Today that is exactly one feature: the USB aperture
# and its funnel, both anchored on USB_X, and USB_X == CX because J1 sits on
# the board's x centreline. The asserts below pin that.
#
# ==> IF YOU EVER MOVE THE USB PORT OFF CENTRE, OR ADD ANY OTHER
#     x-ASYMMETRIC FEATURE TO THE BAND (a vent, a logo, a side button), THE
#     MIRROR PLANE IS DESTROYED, THE BAND BECOMES CHIRAL, AND ITS EXPORT
#     MUST BE MIRRORED EXACTLY LIKE THE TRAY'S. Doing one without the other
#     ships a band that is the wrong hand.
assert USB_X == CX, (
    f"BAND MIRROR-IMMUNITY BROKEN: USB_X ({USB_X}) != CX ({CX}). The band's "
    "only mirror plane is x = CX, and it survives only while the USB feature "
    "is centred there. The band is exported UN-mirrored (unlike the tray), "
    "which is safe ONLY for an achiral part. With the port off centre the "
    "band is chiral: you must now mirror the band export the way the tray "
    "does it (Pos(0, PCB_H, 0) * mirror(part, about=Plane.XZ)) or the "
    "printed band will be the wrong hand.")

PLATE_W = INNER_W - 2 * PLATE_GROOVE              # 84.4
PLATE_H = INNER_H - 2 * PLATE_GROOVE - PLATE_LONG_TRIM   # v2.13: 100.0
PLATE_R = INNER_R - PLATE_GROOVE                  # 5.4
# The SHIPPED plate is 84.4 x 100.0 — this is now the single source, consumed
# by fr4_plate() AND by gen_plate_fab.py (which no longer re-does the trim).
assert abs(PLATE_H - 100.0) < 1e-9, (
    f"PLATE_H is {PLATE_H}, expected the shipped 100.0 — the long-axis trim "
    "moved or PLATE_LONG_TRIM changed; the fab files are FINAL and must not "
    "move (see PLATE_LONG_TRIM)")
# Band plate pocket — uniform PLATE_FIT on every axis (v2.13).
POCKET_W = PLATE_W + 2 * PLATE_FIT                # 84.6
POCKET_H = PLATE_H + 2 * PLATE_FIT                # 100.2
POCKET_R = PLATE_R + PLATE_FIT                    # 5.5
# Float the plate can take inside the pocket (what the owner saw as the gap).
PLATE_FLOAT_X = POCKET_W - PLATE_W                # 0.2 (was 0.6)
PLATE_FLOAT_Y = POCKET_H - PLATE_H                # 0.2 (was 0.8 -> the ~1 mm)
# The legacy pocket, kept ONLY as a documented reference point — NO artifact is
# built from it. That is the geometry of the 2026-07 PCBWay resin order, which
# is therefore usable but carries the ~0.8 mm y-float the owner measured.
# NOMINAL values. To REPRODUCE the legacy band byte-for-byte you must use the
# original EXPRESSIONS, not these decimals:
#     PLATE_W + 2*0.3  |  (INNER_H - 2*PLATE_GROOVE) + 2*0.3  |  PLATE_R + 0.3
# because the pre-v2.13 chain accumulates float error — PLATE_W + 2*0.3 is
# 84.999999999999986, not 85.0. That ~1.4e-14 propagates into the tessellated
# STL coordinates and changes the file's bytes. Learned the hard way: the
# geometry-neutrality gate failed on rounded decimals and passed on the
# expressions (scratch proof, 2026-08-19).
LEGACY_POCKET = (85.0, 100.8, 5.7)      # nominal, for documentation only

TRAY_W = INNER_W - 2 * TRAY_SLIP                  # 84.3
TRAY_H = INNER_H - 2 * TRAY_SLIP                  # 100.1
TRAY_R = INNER_R - TRAY_SLIP                      # 5.35

SOCKET_D = BOSS_OD + 2 * SOCKET_SLIP              # 10.0 band socket bore
BOSS_CENTERS = [
    (BOSS_C, BOSS_C),
    (PCB_W - BOSS_C, BOSS_C),
    (BOSS_C, PCB_H - BOSS_C),
    (PCB_W - BOSS_C, PCB_H - BOSS_C),
]

# v2.6 USB funnel: depth tracks the wall so the web (and therefore the plug
# shell bridge) is wall-INVARIANT. 0.0 at the stock 2.4 wall -> no funnel.
USB_FUNNEL_DEPTH = max(0.0, WALL - USB_FUNNEL_WEB)          # 0.6 @WALL 3.0
USB_FUNNEL_Y_OUT = -(WALL + PCB_CLEARANCE)                  # band outer face
USB_FUNNEL_Y_BOT = USB_FUNNEL_Y_OUT + USB_FUNNEL_DEPTH      # -2.7 at any wall
USB_SHELL_BRIDGE = USB_FUNNEL_WEB + PCB_CLEARANCE - USB_FACE_PROUD   # 2.10

Z_HEAD_TOP = Z_PLATE_TOP + M3_HEAD_H              # +6.8
Z_SCREW_TIP = Z_PLATE_TOP - SCREW_LEN             # -3.0
Z_INSERT_BOT = CAP_Z0 - M3_INSERT_DEPTH           # -4.2

# The two service tacts, straight from the fresh STEP envelopes [S].
_TACTS = [c for c in PCB.COMPONENTS if c[0].startswith("SW_SPST_PTS645")]
assert len(_TACTS) == 2, f"expected 2 PTS645 tacts in the STEP, got {len(_TACTS)}"

# v2.9 base-interface derived + invariants (printed in __main__ as [v2.9-BASE]).
Z_BASE_MOUNT_TOP = Z_TRAY_BOT + BASE_MOUNT_DEPTH      # v2.11: -7.9 (was -5.9)
_H = BASE_MOUNT_PITCH / 2.0
BASE_MOUNT_XY = [(CX + sx * _H, CY + sy * _H)
                 for sy in (-1.0, 1.0) for sx in (-1.0, 1.0)]

# (1) the pocket may never eat the floor below the relief this design already
#     accepts. This is what keeps the interface a SURFACE feature.
_floor_left = TRAY_T - BASE_MOUNT_DEPTH
assert _floor_left >= BASE_MOUNT_FLOOR_MIN - 1e-9, (   # 2.4-1.6 is 0.7999...
    f"BASE MOUNT FAIL: {_floor_left:.3f} mm of floor left above the pocket "
    f"< {BASE_MOUNT_FLOOR_MIN}")
assert Z_BASE_MOUNT_TOP < Z_FLOOR_TOP, "BASE MOUNT FAIL: pocket breaks into the cavity"

# (2) every pocket keeps BASE_MOUNT_KEEPOUT of solid to every other tray
#     feature. Written as an exhaustive sweep, not a spot check, so moving
#     BASE_MOUNT_PITCH can never silently undercut a boss or a slot web.
for (_mx, _my) in BASE_MOUNT_XY:
    for (_rx, _ry) in RETENTION:                      # PCB support boss roots
        _d = math.hypot(_mx - _rx, _my - _ry) - BASE_MOUNT_D / 2 - SUPPORT_BOSS_D / 2
        assert _d >= BASE_MOUNT_KEEPOUT, (
            f"BASE MOUNT FAIL: pocket ({_mx:.1f},{_my:.1f}) is {_d:.3f} from "
            f"the support boss at ({_rx},{_ry}) < {BASE_MOUNT_KEEPOUT}")
    for (_cx, _cy) in BOSS_CENTERS:                   # corner bosses
        _d = math.hypot(_mx - _cx, _my - _cy) - BASE_MOUNT_D / 2 - BOSS_OD / 2
        assert _d >= BASE_MOUNT_KEEPOUT, (
            f"BASE MOUNT FAIL: pocket ({_mx:.1f},{_my:.1f}) is {_d:.3f} from "
            f"the corner boss at ({_cx},{_cy}) < {BASE_MOUNT_KEEPOUT}")
    for (_l, _x0, _x1, _y0, _y1, _z0, _z1) in _TACTS:  # service slots (thru)
        _sx0, _sx1 = _x0 - SVC_CLEAR, _x1 + SVC_CLEAR
        _sy0, _sy1 = _y0 - SVC_CLEAR, _y1 + SVC_CLEAR
        _dx = max(_sx0 - _mx, 0.0, _mx - _sx1)
        _dy = max(_sy0 - _my, 0.0, _my - _sy1)
        _d = math.hypot(_dx, _dy) - BASE_MOUNT_D / 2
        assert _d >= BASE_MOUNT_KEEPOUT, (
            f"BASE MOUNT FAIL: pocket ({_mx:.1f},{_my:.1f}) is {_d:.3f} from "
            f"a service slot < {BASE_MOUNT_KEEPOUT}")
    _edge = min(_mx - (CX - TRAY_W / 2), (CX + TRAY_W / 2) - _mx,
                _my - (CY - TRAY_H / 2), (CY + TRAY_H / 2) - _my) - BASE_MOUNT_D / 2
    assert _edge >= BASE_MOUNT_KEEPOUT, (
        f"BASE MOUNT FAIL: pocket ({_mx:.1f},{_my:.1f}) is {_edge:.3f} from "
        f"the tray edge < {BASE_MOUNT_KEEPOUT}")

# (3) the corner bosses are BACK to solid below the insert. v2.8 cut a Ø3.6
#     pocket there and cost the heat-set over-press buffer 2.0 mm of its
#     3.3 (CASE-V2-NOTES §21.6 watch-item). Retiring those pockets CLOSES it.
assert Z_INSERT_BOT - Z_TRAY_BOT >= 3.0, (
    "BASE MOUNT FAIL: heat-set over-press buffer below the insert dropped "
    f"to {Z_INSERT_BOT - Z_TRAY_BOT:.3f}")


def _boss_notches():
    """v2.2: per-corner boss-vs-chamfer slips; a notch flat wherever the
    round Ø9.5 boss would violate the 0.3 tray/pcb gate.

    Returns [(boss_center, corner, leg, round_slip, flat_standoff|None)].
    flat_standoff = perpendicular distance boss-center -> notch flat; the
    flat sits NOTCH_CLEAR back from the chamfer line, so the board-corner
    clearance equals NOTCH_CLEAR by construction. The (0,0) corner at leg
    13.2: round slip = (13.2 - 7.4)/sqrt2 - 4.75 = -0.649 -> notched at
    3.751 from center; insert-bore wall thins to 3.751 - 2.1 = 1.65 at one
    azimuth (CNC Kitchen M3 in PETG: acceptable, first-article watch-item).
    """
    out = []
    for (bx, by), (cx0, cy0) in zip(BOSS_CENTERS, BOARD_CORNERS):
        leg = _corner_leg(cx0, cy0)
        slip = (leg - 2 * BOSS_C) / math.sqrt(2) - BOSS_OD / 2
        standoff = None
        if slip < NOTCH_MIN_SLIP:
            standoff = (leg - 2 * BOSS_C) / math.sqrt(2) - NOTCH_CLEAR
        out.append(((bx, by), (cx0, cy0), leg, slip, standoff))
    return out


def _crescent_mode(wall=None):
    """Which outer surface is nearest the corner boss socket at this wall.

    The transition is at WALL = OUTER_R - PCB_CLEARANCE - BOSS_C = 4.0: below
    it the OUTER CORNER ARC is nearest (the classic crescent); at/above it the
    boss center has left the arc quadrant and the nearest outer surface is a
    FLAT. Returns "arc" or "flat".
    """
    w = WALL if wall is None else wall
    return "arc" if (-w - PCB_CLEARANCE + OUTER_R) > BOSS_C else "flat"


def _corner_margins():
    """Derived corner-geometry margins (documented in CASE-V2-NOTES §3/§16/§18).

    Everything here is PRINTED, never asserted — no khana gate reads it. v2.7
    corrects TWO reporting defects that only bite once WALL is a live knob;
    both are proven against the built solids in scratch v27_prove.py (P6),
    which bisects the true boss-center -> surface breakout radius:

    (1) band_crescent_wall is now BRANCH-CORRECT across the arc/flat
        transition at WALL 4.0 (see _crescent_mode). v2.6's closed form is the
        ARC measure only; above 4.0 it OVER-REPORTS (4.980 instead of the true
        4.400 at WALL 5.4, because d goes negative).
    (2) head_to_plate_edge / plate_hole_edge_web are PLATE measures and must be
        WALL-INVARIANT — the plate is frozen (PLATE_R = INNER_R - PLATE_GROOVE
        with INNER_R FROZEN at 5.6; the FR4 fab files are already ordered).
        v2.6 measured them off the BAND's outer arc center, which IS
        WALL-driven; the two agreed only at WALL 2.4, where the outer / inner /
        plate corner arcs were still CONCENTRIC at (5.3, 5.3). They now key off
        the plate's own arc center, so they read 0.287 / 1.537 at EVERY wall.
        ERRATUM: the "head_to_plate_edge 1.136 (was 0.287)" and
        "plate_hole_edge_web 2.386 (was 1.537)" improvements recorded in
        CASE-V2-NOTES §16.4 for the WALL 3.0 build were REPORTING ARTIFACTS —
        the plate never moved (P2/P3 prove zero material moved anywhere), so
        those two margins never changed. See §18.
    """
    arc_c = (-WALL - PCB_CLEARANCE + OUTER_R)     # OUTER corner arc center
    #                                               (x=y): 5.3 @WALL 2.4,
    #                                               4.7 @3.0, 2.3 @5.4
    plate_c = (CX - PLATE_W / 2.0) + PLATE_R      # PLATE corner arc center
    #                                               (x=y) = 5.3, WALL-INVARIANT
    d_plate = math.sqrt(2) * (plate_c - BOSS_C)   # boss center -> plate arc c
    if _crescent_mode() == "arc":                 # WALL < 4.0
        d_band = math.sqrt(2) * (arc_c - BOSS_C)
        crescent = OUTER_R - d_band - SOCKET_D / 2       # 0.737 @2.4, 1.586 @3.0
    else:                                         # WALL >= 4.0: nearest = flat
        crescent = BOSS_C + WALL + PCB_CLEARANCE - SOCKET_D / 2  # 4.400 @5.4
    m = {
        "band_crescent_wall": crescent,
        "head_to_plate_edge": PLATE_R - d_plate - M3_HEAD_D / 2,     # 0.287
        "plate_hole_edge_web": PLATE_R - d_plate - M3_SCREW_CLEAR / 2,  # 1.537
    }
    for (bx, by), _c, leg, slip, standoff in _boss_notches():
        key = f"pcb_chamfer_slip[{bx:g},{by:g}]"
        if standoff is None:
            m[key] = slip
        else:
            m[key] = NOTCH_CLEAR
            m[f"notch_insert_wall[{bx:g},{by:g}]"] = (
                standoff - M3_INSERT_PILOT / 2)
    return m


# =========================================================================
# 3. PRIMITIVE HELPERS
# =========================================================================


def _rprism(w, h, r, z0, z1, cx=CX, cy=CY):
    return Pos(cx, cy, z0) * extrude(RectangleRounded(w, h, r), amount=z1 - z0)


def _z_cyl(d, z0, z1, cx, cy):
    return Pos(cx, cy, z0) * extrude(Plane.XY * Circle(d / 2), amount=z1 - z0)


def _box(cx, cy, z0, z1, sx, sy):
    return Pos(cx, cy, (z0 + z1) / 2) * Box(sx, sy, z1 - z0)


def _box_from_bbox(rec, pad_xy=0.0):
    _lbl, x0, x1, y0, y1, z0, z1 = rec
    return _box((x0 + x1) / 2, (y0 + y1) / 2, z0, z1,
                (x1 - x0) + 2 * pad_xy, (y1 - y0) + 2 * pad_xy)


def _safe_chamfer(part, z, value, exclude_xy=(), exclude_r=0.0):
    """EFC chamfer edges at plane z; skip near-tangent seams around points."""
    z0, z1 = z - 0.05, z + 0.05

    def _sel(p):
        out = []
        for e in p.edges().filter_by_position(Axis.Z, z0, z1):
            mp = e @ 0.5
            if any(math.hypot(mp.X - bx, mp.Y - by) < exclude_r
                   for (bx, by) in exclude_xy):
                continue
            out.append(e)
        return out

    if not _sel(part):
        return part
    for v in (value, value * 0.75, 0.2):
        try:
            return chamfer(_sel(part), v)
        except Exception:
            continue
    print(f"[chamfer] z={z}: OCCT refused; left square (slicer EFC covers it)")
    return part


# =========================================================================
# 4. BOARD PROXY + KEEP-OUTS (positions [C], envelopes [S], dims [D])
# =========================================================================


def pcb_board():
    """Board proxy: contract octagon (v5 legs) x real 1.51 mm, Ø2.2 pin holes."""
    from build123d import Polyline, make_face
    pts = OCTAGON + [OCTAGON[0]]
    face = make_face(Polyline(*[(x, y, 0) for (x, y) in pts]))
    board = Pos(0, 0, REAL_PCB_BOT) * extrude(face, amount=-REAL_PCB_BOT)
    for (cx, cy) in RETENTION:
        board -= _z_cyl(2.2, REAL_PCB_BOT - _OVER, _OVER, cx, cy)   # [R]
    return board


def pcb_components():
    """72 real envelopes from the fresh STEP [S]. J2 is DNP-excluded there."""
    return Compound(children=[_box_from_bbox(r) for r in PCB.COMPONENTS])


def sockets():
    """13 Kailh hotswap keep-outs (no STEP models; dims [D], positions [C])."""
    return Compound(children=[
        _box(cx, cy, Z_SOCKET_BOT, Z_PCB_BOT, SOCKET_X, SOCKET_Y)
        for (cx, cy) in ALL_SWITCHES
    ])


def leds():
    """LED keep-outs (no STEP models): 10 side-fire + 13 per-key + LYR [C]."""
    parts = [
        _box(cx, cy, LED_SIDE_Z0, LED_SIDE_Z1, LED_SIDE_BOX, LED_SIDE_BOX)
        for (cx, cy) in UNDERGLOW_LEDS
    ] + [
        _box(cx, cy, LED_RM_Z0, LED_RM_Z1, LED_RM_BOX, LED_RM_BOX)
        for (cx, cy) in PERKEY_LEDS + [LED14]
    ]
    return Compound(children=parts)


def ec11_body():
    return _box(*RE1_SHAFT, 0.0, ENC_BODY_H, ENC_BODY_SQ, ENC_BODY_SQ)


def js_body():
    """YA13 joystick body (v2.4) — faithful CROSS envelope, z 0..11.1: a
    13x13 frame + West/North pot boxes + East/South corner-tab bumps. [YA13]

    Modeled as a cross (NOT a filled bbox) because the real part's pot boxes
    sit on the West and North faces only, so the NE/SE/NW/SW bbox *corners*
    are void. A filled-square model would false-interfere with (a) the plate
    opening's R1.5 corners and (b) the NE screw boss — both void in reality.
    Reaches: W/N 10.5 (pot box 9.3 + tab lobes) and E/S 7.4 (frame + tabs);
    frame ±6.5 [v5_6 F.Fab]. De-risk-measured (2026-07-20): fits the new
    plate opening with 0.25 clearance and clears the NE boss by 0.584 —
    the §12.4 caliper item, RESOLVED by the adjudicated SW JS1 move."""
    z0, z1 = 0.0, JS_BODY_Z1
    fh, wn, es, ph = JS_FRAME_HALF, JS_WN_EXTENT, JS_ES_EXTENT, JS_POT_HALF
    frame = _box(*JS1, z0, z1, 2 * fh, 2 * fh)
    wpot = _box(JS1[0] - (wn + fh) / 2, JS1[1], z0, z1, wn - fh, 2 * ph)
    npot = _box(JS1[0], JS1[1] - (wn + fh) / 2, z0, z1, 2 * ph, wn - fh)
    etab = _box(JS1[0] + (es + fh) / 2, JS1[1], z0, z1, es - fh, 2 * ph)
    stab = _box(JS1[0], JS1[1] + (es + fh) / 2, z0, z1, 2 * ph, es - fh)
    return frame + wpot + npot + etab + stab


def js_pins():
    """The 10 YA13 THT pin tails BELOW the board (v2.4). Positions + Ø are
    PARSED from the banked board's JS1 pads (JS1_PADS), never retyped. Tails
    from the board underside (-1.51) to -3.71 (= -1.51 - 2.2; pin length 3.7
    from PCB-top seating [DRAWING]). Keep-out Ø = pad Ø (captures the solder
    joint). [v5_6 parse]"""
    return Compound(children=[
        _z_cyl(pad, JS_PIN_Z_BOT, REAL_PCB_BOT, wx, wy)
        for (wx, wy, _drill, pad) in JS1_PADS
    ])


def usb_receptacle():
    """Flipped J1 [V5]: mouth AT the wall, 0.49 proud of the board edge.

    Sign tripwire (the hazard-2 class: a flip-direction error makes every
    interference gate pass VACUOUSLY, because the envelope retreats behind
    the wall exactly like the original backwards connector did): the face
    must sit OUTSIDE the board edge, i.e. beyond the band's inner wall
    plane at y = -PCB_CLEARANCE, or this build refuses to produce geometry.
    """
    y_face = -USB_FACE_PROUD
    assert y_face < -PCB_CLEARANCE + 0.2, (
        f"USB face y={y_face}: not proud of the board edge — flip direction "
        "wrong or USB_FACE_PROUD stale; band gates would pass vacuously")
    cy = y_face + USB_RECEPT_DEPTH / 2.0
    return _box(USB_X, cy, USB_RECEPT_Z0, USB_RECEPT_Z1,
                USB_RECEPT_W, USB_RECEPT_DEPTH)


def knob_sweep():
    """v2 swept-occupancy proxy: Ø19 from the deck up to the knob top (carries
    the coaxial knob-on-shaft assert vs ec11_body). [v2.17] Ø18 -> Ø19 and top
    +17.5 -> +27.0 with the v2 knob catalog. The accurate static knob() is
    below; the sweep CONTAINS it by construction, so their reported
    interference volume is exactly the knob's own volume."""
    return _z_cyl(KNOB_D, Z_PLATE_TOP, Z_PLATE_TOP + KNOB_H, *RE1_SHAFT)


def _revolve_rz(pts, cx, cy):
    """ONE solid of revolution about the vertical axis at (cx, cy), from a list
    of (r, z) silhouette points closed along the axis.

    ⚠ TWO OCCT traps were hit building this, both recorded because both fail
    SILENTLY and in the OPTIMISTIC direction — a swept envelope that loses
    material simply stops interfering, and no assertion in this file would
    notice:

      1. Union-of-lofted-frusta. Tried first, so no new import was needed.
         A rolled edge chopped into many arc segments yields near-degenerate
         conical slivers (some 0.001 mm tall); fusing those, then fusing the
         result 24 more times for the tilt sweep, made OCCT drop 64.76 mm^3
         and under-report the puck's reach by 0.146 mm. `revolve` on one
         closed profile fixes it — no slivers, true conical faces.

      2. Over-discretised arcs. Even with `revolve`, chopping the R0.6 rim
         roll into 24 chords still lost 59.44 mm^3 in the 25-way sweep fuse
         (and a balanced-tree fuse of the same operands collapsed the solid
         to nothing at all — bbox 0). At 8 chords the fuse is EXACT: zero
         lost, reach 9.3301 = the params' own governing value. So arc
         resolution here is a BOOLEAN-ROBUSTNESS parameter, not a fidelity
         knob — see PUCK_RIM_SEGMENTS.

    _tilt_sweep asserts containment so a regression of this class cannot
    ship silently."""
    # Drop consecutive duplicates before building edges: an arc that starts at
    # a=90° lands on the point the caller already listed as the rim land, and
    # a zero-length Edge makes OCCT raise "BRep_API: command not done".
    uniq = []
    for q in pts:
        if not uniq or math.hypot(q[0] - uniq[-1][0], q[1] - uniq[-1][1]) > 1e-9:
            uniq.append(q)
    prof = Polyline(*[(r, 0.0, z) for (r, z) in uniq], close=True)
    return Pos(cx, cy, 0) * revolve(make_face(prof), Axis.Z, 360.0)


def _arc_rz(rc, zc, rad, a0, a1, n):
    """(r, z) points along an arc, centre (rc, zc) [TOPPER arc_pts]."""
    return [(rc + rad * math.cos(a0 + (a1 - a0) * i / n),
             zc + rad * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _nub_cap(cx, cy):
    """v2.17 SHIPPED-DEFAULT stick topper at (cx, cy): the nub_C2 envelope, a
    plain Ø6.189 cylinder z 14.4..19.6.

    DELIBERATELY CONSERVATIVE — the real part's 0.2 rim chamfer, 0.3 bottom
    fillet and seven Ø0.9 dimples all REMOVE material from this cylinder, so
    the envelope over-approximates the part everywhere. The one place that
    costs anything is the swept floor: this solid sweeps to z 11.741 where the
    filleted part reaches 11.851 (the params' deck_low_z), i.e. 0.110 mm
    pessimistic. [stick_topper_v2_params nub_C2]"""
    return _z_cyl(2 * STICK_CAP_R, STICK_CAP_Z0, STICK_CAP_Z1, cx, cy)


def _puck_cap(cx, cy):
    """v2.17 the OTHER shipped stick topper at (cx, cy): the puck_TPU OUTER
    silhouette, revolved.

    Mirrors toppers/stick_topper_v2.py puck_outer_profile — the same silhouette
    the topper's own SW4 gate consumes: the cup only REMOVES material so it
    cannot widen the envelope, while the four raised dashes ADD material and
    are folded in as a conservative full ring of revolution at their own
    radius. Two further deliberate conservatisms here: the 45° land->body
    relief is dropped (the body cylinder runs straight down to the land OD
    height, adding material), and the Ø5.2 bore is filled solid. All three
    push the envelope OUTWARD, never inward. [stick_topper_v2_params puck_TPU]
    """
    z_in, z_out = _puck_land_z(PUCK_LAND_R_IN), _puck_land_z(PUCK_LAND_R_OUT)
    pts = [(0.0, PUCK_TOP_Z), (PUCK_DASH_OUT_R, PUCK_TOP_Z),
           (PUCK_R - PUCK_RIM_R, PUCK_TOP_Z)]
    pts += _arc_rz(PUCK_R - PUCK_RIM_R, PUCK_TOP_Z - PUCK_RIM_R, PUCK_RIM_R,
                   math.pi / 2, 0.0, PUCK_RIM_SEGMENTS)   # rim roll
    pts += [(PUCK_R, PUCK_WALL_BOT_Z),                    # straight max-OD wall
            (PUCK_BODY_R, PUCK_SHOULDER_BOT_Z),           # inward shoulder
            (PUCK_BODY_R, z_out),                         # body (relief dropped)
            (PUCK_LAND_R_OUT, z_out),
            (PUCK_LAND_R_IN, z_in),                       # the 22.5° land
            (0.0, z_in)]                                  # bore filled solid
    # The rim roll is CHORDED, so between samples the profile runs up to
    # ~0.003 mm inside the true arc. That is only acceptable because the one
    # point that decides the SW4 answer — the params' published governing
    # point, where the outward normal is exactly the 22.5° tilt direction — is
    # itself a sample. Assert that rather than trust the arithmetic: it ties
    # PUCK_RIM_SEGMENTS to the toppers' own gate, so changing the segment
    # count to a value that skips the governing point fails loudly here.
    _gr, _gz = _PV["governing_point_rh"]
    assert any(math.hypot(r - _gr, z - _gz) < 5e-3 for (r, z) in pts), (
        f"PUCK PROFILE FAIL: the params' governing point ({_gr}, {_gz}) is not "
        f"a sample of the chorded rim roll at PUCK_RIM_SEGMENTS="
        f"{PUCK_RIM_SEGMENTS} — the swept envelope would under-reach toward "
        "SW4. Use a segment count for which 22.5° lands on a sample")
    return _revolve_rz(pts, cx, cy)


def _dome_cap(cx, cy):
    """v1 ALTERNATE (RETIRED with archive/toppers-v1/, unreachable while
    STICK_TOP_STYLE == "nub"): Ø13 cylinder z 14.4..17.4 topped by a spherical
    dome to z 19.6 — the v2.4 default. Its params are no longer on the live
    tree; re-derive from the archived stick_cap_params before reviving."""
    r = STICK_CAP_R
    z_sh = STICK_CAP_Z1 - STICK_DOME_RISE                 # dome springs (17.4)
    rr = (r * r + STICK_DOME_RISE ** 2) / (2 * STICK_DOME_RISE)
    z_c = STICK_CAP_Z1 - rr                                # sphere center
    body = _z_cyl(2 * r, STICK_CAP_Z0, STICK_CAP_Z1, cx, cy)
    below = _box(cx, cy, STICK_CAP_Z0 - _OVER, z_sh, 2 * r + 2, 2 * r + 2)
    return body & (below + Pos(cx, cy, z_c) * Sphere(rr))


def _taper_cap(cx, cy):
    """v1 ALTERNATE (RETIRED with archive/toppers-v1/, unreachable while
    STICK_TOP_STYLE == "nub"): the v2.5 taper cone — a straight 30°-from-
    vertical wall from bottom Ø11.285 @z14.4 to Ø6.667 @z18.4, then a spherical
    dome roof to z19.6. Mirrored the OUTER profile of toppers/stick_cap.py
    _taper_body. Its params left the live tree with v2.17, so STICK_TAPER_*
    now degenerate to the nub's Ø — re-derive from the archived params before
    reviving this branch."""
    r_bot = STICK_TAPER_BOT_D / 2.0
    r_spring = STICK_TAPER_SPRING_D / 2.0
    z_spring = STICK_TAPER_SPRING_Z
    frustum = loft([
        Plane.XY.offset(STICK_CAP_Z0) * Circle(r_bot),
        Plane.XY.offset(z_spring) * Circle(r_spring),
    ])
    rise = STICK_CAP_Z1 - z_spring                         # 1.2 dome roof over tip
    rr = (r_spring * r_spring + rise * rise) / (2 * rise)  # sphere thru rim + peak
    z_c = STICK_CAP_Z1 - rr                                # sphere center (peak @19.6)
    slab = _box(0.0, 0.0, z_spring, STICK_CAP_Z1 + _OVER,
                2 * r_spring + 4, 2 * r_spring + 4)
    dome = (Pos(0, 0, z_c) * Sphere(rr)) & slab
    return Pos(cx, cy, 0) * (frustum + dome)


def _cap_solid(cx, cy):
    """The SHIPPED-DEFAULT stick-topper solid at (cx, cy). v2.17 default =
    nub_C2; taper/dome are the v1 alternates, retired to archive/toppers-v1/
    and unreachable (kept so the v2.4/v2.5 envelopes stay reproducible)."""
    if STICK_TOP_STYLE == "nub":
        return _nub_cap(cx, cy)
    if STICK_TOP_STYLE == "taper":
        return _taper_cap(cx, cy)
    return _dome_cap(cx, cy)


def stick_cap():
    """Static (upright, centered) stick topper at JS1 — the rest pose, shipped
    default (nub_C2). js_sweep() covers its tilt envelope; the puck alternate
    is stick_puck()/js_sweep_puck(). [stick_topper_v2_params nub_C2]."""
    return _cap_solid(*JS1)


def _tilt_sweep(cap0, tilt_deg, naz=24):
    """Revolve `cap0` (built upright at the origin) about the stick axis at
    `tilt_deg`, unioned with the upright pose. Discrete in azimuth (`naz`
    steps) — an honest, slightly-scalloped OVER-approximation of the true
    solid of revolution, with an azimuth sample landing due-south (toward SW4)
    so the tightest reach is captured exactly. Placed at JS1."""
    piv = STICK_PIVOT_Z
    south = Pos(0, 0, piv) * Rot(-tilt_deg, 0, 0) * Pos(0, 0, -piv) * cap0
    swept = cap0
    for k in range(naz):
        swept += Rot(0, 0, 360.0 * k / naz) * south
    # CONTAINMENT GATE. A union must contain every one of its operands — but
    # OCCT does not always deliver one: fusing sliver-rich solids can silently
    # drop material, and the loss shows up as an envelope that is too SMALL,
    # which no interference assertion can catch (a missing envelope simply
    # stops interfering). This caught a real 64.76 mm^3 loss on the puck's
    # first construction; see _revolve_rz. k=0 is the due-south copy, the one
    # that carries the tightest reach toward SW4, so it is the one to check.
    _lost = (south - swept).volume
    assert _lost < 1e-3, (
        f"SWEEP FUSE FAIL: {_lost:.4f} mm^3 of the {tilt_deg}° tilted topper "
        f"is missing from its own swept union (naz={naz}) — OCCT dropped "
        "geometry, so this envelope UNDERSTATES the real one. Do NOT trust "
        "any clearance measured against it; simplify the cap solid first")
    return Pos(JS1[0], JS1[1], 0) * swept


def js_sweep(naz=24):
    """Swept envelope of the SHIPPED-DEFAULT stick topper over the FULL 30°
    mechanical tilt cone. [v2.17] the nub_C2 has NO restrictor, so 30° is its
    real throw; it was sized by bisection to hold 0.25 mm off SW4 there.
    Nub swept floor z 11.741 (envelope) / 11.851 (part); south reach 9.430.
    v2.5's taper reached 9.037 and floored at 10.467; the v2.4 dome reached
    11.279 and grazed SW4. [stick_topper_v2_params nub_C2; pivot/tilt [D]]."""
    return _tilt_sweep(_cap_solid(0.0, 0.0), STICK_TILT_DEG, naz)


def js_sweep_puck(naz=24):
    """[v2.17] Swept envelope of the OTHER shipped stick topper, the TPU puck,
    over ITS OWN throw — 22.5°, not 30°, because the puck's 22.5° cone land IS
    an integral mechanical restrictor (that is the whole point of the part).
    Sweeping it to 30° would model a stop that physically cannot be reached and
    would invent interferences; sweeping the NUB to 22.5° would understate the
    default. Hence two parts, two angles. [stick_topper_v2_params puck_TPU]."""
    return _tilt_sweep(_puck_cap(0.0, 0.0), STICK_TILT_RESTRICTED_DEG, naz)


def knob():
    """Encoder knob — accurate static envelope of the v2 catalog (A/B2/C all
    share it): Ø19 cylinder z 8.0..27.0 on the EC11 shaft (skirt bottom +8.0
    clears the body top +7.5 by 0.5). [v2.17] was Ø18 z 8.0..17.5.
    [encoder_knob_v2_params]."""
    return _z_cyl(KNOB_OD, KNOB_SKIRT_Z0, KNOB_TOP_Z_ABS, *RE1_SHAFT)


def switch_bodies():
    """MX switch envelopes at all 13 switch sites (v2.4): lower housing 13.9
    sq (z 0..5.0, INSIDE the 14.0 plate cutouts by design), flange 15.8 sq
    (z 5.0..5.9, rests on the deck), upper housing 14.8 sq (z 5.9..8.4,
    conservative max of the 14.8->11 taper), stem Ø7 (z 8.4..11.6). [MX]/[D].
    switch_bodies x fr4_plate is a REAL cutout-alignment check (13.9 lower
    housing in the 14.0 cutout = 0.05/side must not overlap)."""
    parts = []
    for (cx, cy) in ALL_SWITCHES:
        parts.append(_box(cx, cy, 0.0, SW_FLANGE_Z0, SW_LOWER_SQ, SW_LOWER_SQ))
        parts.append(_box(cx, cy, SW_FLANGE_Z0, SW_FLANGE_Z1, SW_FLANGE, SW_FLANGE))
        parts.append(_box(cx, cy, SW_FLANGE_Z1, SW_UPPER_Z1, SW_UPPER_SQ, SW_UPPER_SQ))
        parts.append(_z_cyl(SW_STEM_D, SW_UPPER_Z1, SW_STEM_Z1, cx, cy))
    return Compound(children=parts)


def keycaps():
    """Keycap envelopes (v2.4): 12x 1U (18x18) at SW1..12, 1x 2U (37.1x18) at
    SW13, all z 10.6..14.6. [CONVENTION]. The control row (RE1 knob, JS1 stick
    cap) and TP5 carry no keycap."""
    parts = [_box(cx, cy, KEYCAP_Z0, KEYCAP_Z1, KEYCAP_1U, KEYCAP_1U)
             for (cx, cy) in SW_1U]
    parts.append(_box(*SW_2U, KEYCAP_Z0, KEYCAP_Z1, KEYCAP_2U, KEYCAP_1U))
    return Compound(children=parts)


def screws():
    """4x M3x8 as installed: proud head on the plate + shaft to z=-3.0."""
    parts = []
    for (cx, cy) in BOSS_CENTERS:
        parts.append(_z_cyl(M3_HEAD_D, Z_PLATE_TOP, Z_HEAD_TOP, cx, cy))
        parts.append(_z_cyl(M3_SCREW_D, Z_SCREW_TIP, Z_PLATE_TOP, cx, cy))
    return Compound(children=parts)


# =========================================================================
# 5. PLATE  (the product face — BLANK, all 13 real cutouts, fab-accurate)
# =========================================================================


def _stab_cutters(cx, cy):
    z0, z1 = Z_PLATE_BOT - _OVER, Z_PLATE_TOP + _OVER
    cy_s = cy + STAB_Y_SHIFT
    left = _box(cx - STAB_HALF_SPACING, cy_s, z0, z1, STAB_W, STAB_H)
    right = _box(cx + STAB_HALF_SPACING, cy_s, z0, z1, STAB_W, STAB_H)
    return left + right


def fr4_plate():
    plate = _rprism(PLATE_W, PLATE_H, PLATE_R, Z_PLATE_BOT, Z_PLATE_TOP)
    z0, z1 = Z_PLATE_BOT - _OVER, Z_PLATE_TOP + _OVER
    for (cx, cy) in ALL_SWITCHES:                       # 13x 14.0 cutouts
        plate -= _box(cx, cy, z0, z1, FR4_CUTOUT, FR4_CUTOUT)
    plate -= _stab_cutters(*SW_2U)                      # 2U stab slots
    # [v2.12] 14.0 x 13.0 R1.5 at (14.025, 12.5) — widened +1.0 to the OWNER'S
    # RIGHT (board +x) only; the left edge stays frozen at 7.025.
    plate -= _rprism(ENC_OPENING_W, ENC_OPENING_H, ENC_OPENING_R, z0, z1,
                     *ENC_OPENING_C)
    # v2.4: YA13 asymmetric rounded-rect opening (mirrors the ORDERED fab
    # plate_v5, CASE-V2-NOTES §14) — replaces the v4 Ø16 circle.
    plate -= _rprism(JS_OPEN_E_X - JS_OPEN_W_X, JS_OPEN_S_Y - JS_OPEN_N_Y,
                     JS_OPEN_R, z0, z1,
                     (JS_OPEN_W_X + JS_OPEN_E_X) / 2,
                     (JS_OPEN_N_Y + JS_OPEN_S_Y) / 2)
    plate -= _z_cyl(LYR_HOLE_D, z0, z1, *LED14)         # LYR Ø3
    for (cx, cy) in BOSS_CENTERS:
        plate -= _z_cyl(M3_SCREW_CLEAR, z0, z1, cx, cy)  # plain Ø3.4 (no cbore)
    return plate


# =========================================================================
# 6. BAND  (top case: the visible side wall; one geometry, any material)
# =========================================================================


def usb_funnel():
    """v2.6 USB port funnel — the OUTER counterbore cut (None when it vanishes).

    A rectangular pocket USB_FUNNEL_W x USB_FUNNEL_H on the band's outer face,
    centered on the USB aperture, with a 45° lead-in chamfer of leg
    min(USB_FUNNEL_LEAD, depth) on the TOP and both SIDE mouth edges, and a
    FLAT bottom (the plug overmold's seating face) at y = USB_FUNNEL_Y_BOT =
    -2.7 for every wall thickness. Depth = WALL - USB_FUNNEL_WEB, so:

        WALL 2.4 -> depth 0.00  (no funnel; v2.5 geometry exactly)
        WALL 3.0 -> depth 0.60  leg 0.60  mouth 14.2 w x 7.6 h (z -6.7..+0.9)
        WALL 5.4 -> depth 3.00  leg 1.00  mouth 15.0 w x 8.0 h (z -6.7..+1.3)
        WALL 7.4 -> depth 5.00  leg 1.00  mouth 15.0 w x 8.0 h (z -6.7..+1.3)

    and the shell bridge stays 2.10 mm throughout — the wall pick is purely
    aesthetic. The pocket is mid-wall (x 42.1 ± 7.5 = 34.6..49.6); the nearest
    corner boss socket is at x 3.7 / 80.5, i.e. >25 mm clear, so the funnel can
    never reach the corner stack. Its z floor (-6.7) is USB_FUNNEL_FLOOR_MIN =
    0.8 above the band bottom (-7.5) at every wall, which is why the BOTTOM
    lead-in leg is clamped to 0 (see USB_FUNNEL_FLOOR_MIN — the 4-sided version
    measured a 0.566 mm knife edge and broke the EFC chamfer).
    """
    d = USB_FUNNEL_DEPTH
    if d <= 1e-9:
        return None
    lead = min(USB_FUNNEL_LEAD, d)
    zc = (USB_CUTOUT_Z0 + USB_CUTOUT_Z1) / 2.0
    z_lo, z_hi = zc - USB_FUNNEL_H / 2.0, zc + USB_FUNNEL_H / 2.0   # -6.7..+0.3
    # Per-edge lead-in legs. Sides + top get the full leg; the bottom leg is
    # whatever room is left over USB_FUNNEL_FLOOR_MIN (0.0 at the shipped
    # dimensions), so the pocket floor never walks down onto the band bottom.
    lead_bot = max(0.0, min(lead, (z_lo - BAND_Z_BOT) - USB_FUNNEL_FLOOR_MIN))
    m_lo, m_hi = z_lo - lead_bot, z_hi + lead            # mouth z span
    mw = USB_FUNNEL_W + 2 * lead                         # mouth width

    def _yface(y, w, za, zb):
        # A rectangle in the world XZ plane at depth y (plane x = world +X,
        # normal = world +Y = the inward cut direction). za/zb are explicit so
        # the mouth and the pocket section need not share a z center.
        return Plane(origin=(USB_X, y, (za + zb) / 2.0), x_dir=(1, 0, 0),
                     z_dir=(0, 1, 0)) * Rectangle(w, zb - za)

    # 45° lead-in: mouth (outer face) -> pocket section, over `lead` of depth.
    cut = loft([_yface(USB_FUNNEL_Y_OUT, mw, m_lo, m_hi),
                _yface(USB_FUNNEL_Y_OUT + lead, USB_FUNNEL_W, z_lo, z_hi)])
    # Outward overshoot so the boolean never rides a face coincident with the
    # band's outer surface.
    cut += _box(USB_X, USB_FUNNEL_Y_OUT - _OVER / 2.0, m_lo, m_hi, mw, _OVER)
    # Straight pocket walls from the end of the lead-in down to the flat
    # bottom (empty when the lead-in consumed the whole depth).
    if d - lead > 1e-9:
        cut += _box(USB_X, (USB_FUNNEL_Y_OUT + lead + USB_FUNNEL_Y_BOT) / 2.0,
                    z_lo, z_hi, USB_FUNNEL_W, d - lead)
    return cut


_BAND_ACHIRAL_VERIFIED = False


def _verify_band_achiral(part):
    """[v2.14] THE catch-all guard behind the deferred band mirror-at-export.

    Coordinator ruling 2026-08-19: do NOT mirror the band at export until a
    genuinely x-asymmetric band feature lands (it would churn six artifacts
    for a physically identical part, and break the `34be6bf7...` citation
    chain that answers "is the band I ordered the right one?"). Deferral is
    only safe if it CANNOT be violated silently — this is what makes it
    airtight rather than merely signposted.

    WHY THE PER-CUT ASSERTS ARE NOT ENOUGH: they pin the features we already
    know about (the USB aperture and funnel, checked against CX). They are
    blind to a NEW x-asymmetric feature — a vent, a logo, a side button, an
    off-centre boss. This check is feature-agnostic: it tests the finished
    solid for the mirror plane itself, so anything that destroys achirality
    trips it, named or not.

    THE TEST: a solid possessing any mirror plane is ACHIRAL — its
    enantiomorph is congruent to it by a rigid motion. The band's plane is
    x = CX. If band == mirror(band about x=CX), then the left-handed export
    path (a reflection) yields a part congruent to the intended one by a
    180-deg z rotation, i.e. physically identical; orient by the USB hole and
    it lands. Measured on the shipped v2.13 band: both difference volumes are
    exactly 0.000000 mm^3.

    COST ~0.4 s (two booleans; the band itself builds in ~0.26 s). Run ONCE
    per process, not per call: band() is called ~5x in a full build and the
    geometry is fully determined by module constants that are fixed at
    import, so re-running it per call would pay ~2 s for an answer that
    cannot change.
    """
    global _BAND_ACHIRAL_VERIFIED
    if _BAND_ACHIRAL_VERIFIED:
        return
    _m = Pos(2 * CX, 0, 0) * mirror(part, about=Plane.YZ)
    _a, _b = (part - _m).volume, (_m - part).volume
    assert _a < 1e-6 and _b < 1e-6, (
        f"BAND MIRROR-IMMUNITY BROKEN: the band is no longer symmetric about "
        f"x = CX ({CX}). Measured band-minus-mirror {_a:.6f} mm^3 and "
        f"mirror-minus-band {_b:.6f} mm^3 (both must be < 1e-6). Some feature "
        "is off the centreline — if it is not the USB cuts (those have their "
        "own asserts) then it is a NEW asymmetric feature this guard exists "
        "to catch. The band is exported UN-mirrored, which is safe ONLY while "
        "the part is achiral, and its only mirror plane is x = CX. Either "
        "re-centre the offending feature, or mirror the band at export the "
        "way the tray does (Pos(0, PCB_H, 0) * mirror(part, about=Plane.XZ)) "
        "— and if you do the latter, every band hash changes, so re-sync the "
        "bundle MANIFEST, RELEASE.md, HOW-TO-ORDER.md and the public mirror.")
    _BAND_ACHIRAL_VERIFIED = True


def band():
    # [v2.11] Every z-bottom below is BAND_Z_BOT (-7.5, frozen), NOT Z_TRAY_BOT
    # — the tray dropped to -9.5 for the plinth and the band must not follow.
    outer = _rprism(OUTER_W, OUTER_H, OUTER_R, BAND_Z_BOT, Z_PLATE_TOP)
    # Stepped inner profile: full 84.8 opening below the ledge and in the
    # plate recess; 82.4 across the ledge band (+0.3..+3.5) — the rabbet the
    # plate drops into (flush deck, perimeter-seated).
    ring = outer - _rprism(INNER_W, INNER_H, INNER_R,
                           BAND_Z_BOT - _OVER, LEDGE_Z0)
    ring -= _rprism(INNER_W - 2 * LEDGE_W, INNER_H - 2 * LEDGE_W,
                    INNER_R - LEDGE_W, LEDGE_Z0 - _OVER, Z_PLATE_BOT)
    # Plate recess: PLATE + PLATE_FIT/side (NOT the inner-wall width) so a
    # printed band still swallows a worst-case fab plate. Reveal = 0.3 nom.
    # [v2.13] Per-axis fit: X + R frozen at the legacy 0.3 (owner: the width
    # "is honestly fine as is"); Y is the variant (tight 0.1 / loose 0.4 per
    # end) against the corrected 100.0 plate.
    ring -= _rprism(POCKET_W, POCKET_H, POCKET_R,
                    Z_PLATE_BOT, Z_PLATE_TOP + _OVER)
    # 45° chamfer under the ledge so the upright FDM print needs no support.
    # Select ONLY the inner ledge-bottom ring (the concave wall junction ring
    # at the same z must stay square).
    z0, z1 = LEDGE_Z0 - 0.05, LEDGE_Z0 + 0.05
    hx = INNER_W / 2 - LEDGE_W + 0.05
    hy = INNER_H / 2 - LEDGE_W + 0.05
    ledge_edges = [
        e for e in ring.edges().filter_by_position(Axis.Z, z0, z1)
        if abs((e @ 0.5).X - CX) < hx and abs((e @ 0.5).Y - CY) < hy
    ]
    if ledge_edges:
        for v in (LEDGE_W - 0.05, 0.8, 0.6):
            try:
                ring = chamfer(ledge_edges, v)
                break
            except Exception:
                ledge_edges = [
                    e for e in ring.edges().filter_by_position(Axis.Z, z0, z1)
                    if abs((e @ 0.5).X - CX) < hx and abs((e @ 0.5).Y - CY) < hy
                ]
        else:
            print("[band] ledge chamfer refused; square ledge underside "
                  "(1.2 mm overhang ring — PETG bridges it; resin unaffected)")
    # Corner caps: solid +1.5..+3.5, fused into the wall corners, then
    # clipped back to the outer surface (the cap cylinder pokes past it).
    caps = None
    for (bx, by) in BOSS_CENTERS:
        c = _z_cyl(CAP_D, CAP_Z0, CAP_Z1, bx, by)
        caps = c if caps is None else caps + c
    shell = (ring + caps) & _rprism(OUTER_W, OUTER_H, OUTER_R,
                                    BAND_Z_BOT, Z_PLATE_TOP)
    # Boss sockets below the caps + screw pass through them.
    for (bx, by) in BOSS_CENTERS:
        shell -= _z_cyl(SOCKET_D, BAND_Z_BOT - _OVER, CAP_Z0, bx, by)
        shell -= _z_cyl(M3_PASS_BAND, CAP_Z0 - _OVER, CAP_Z1 + _OVER, bx, by)
    # USB aperture through the y=0 wall [§5]: 10.0 wide, z -5.0..-1.4.
    _aperture = _box(USB_X, -WALL - PCB_CLEARANCE / 2, USB_CUTOUT_Z0,
                     USB_CUTOUT_Z1, USB_CUTOUT_W, 2 * (WALL + PCB_CLEARANCE))
    # v2.6 USB port funnel: the OUTER counterbore that keeps the plug-shell
    # bridge at 2.10 mm for any wall (see usb_funnel()). Purely subtractive on
    # the outer face; the aperture cut above is untouched, so every USB gate
    # (band x usb_recept >= 0.1) measures the same inner geometry as v2.5.
    _funnel = usb_funnel()
    # [v2.14] MIRROR-IMMUNITY GEOMETRIC GATE. Checked against CX, the band's
    # own centreline — NOT against USB_X. Comparing a cut to the constant it
    # was built from is vacuous (it passes by construction, even with the
    # port moved); pinning it to CX is what actually protects the mirror
    # plane, and it catches BOTH failure routes: a moved USB_X, and an offset
    # written into a cut expression. See the invariant block at CX/CY.
    for _nm, _cut in (("USB aperture", _aperture), ("USB funnel", _funnel)):
        if _cut is None:
            continue                      # funnel vanishes at WALL == 2.4
        _bb = _cut.bounding_box()
        _c = (_bb.min.X + _bb.max.X) / 2.0
        assert abs(_c - CX) < 1e-9, (
            f"BAND MIRROR-IMMUNITY BROKEN: the {_nm} cut is centred at x="
            f"{_c:.6f}, not on the band centreline CX={CX} (cut spans "
            f"{_bb.min.X:.4f}..{_bb.max.X:.4f}). The band is exported "
            "UN-mirrored, which is safe only while it is achiral, and its "
            "only mirror plane is x = CX. Re-centre the cut, or mirror the "
            "band at export the way the tray does "
            "(Pos(0, PCB_H, 0) * mirror(part, about=Plane.XZ)).")
    shell -= _aperture
    if _funnel is not None:
        shell -= _funnel
    # EFC chamfer for the FDM print (upright, bottom edge on the bed).
    _band = _safe_chamfer(shell, BAND_Z_BOT, EFC_CHAMFER,
                          exclude_xy=BOSS_CENTERS, exclude_r=SOCKET_D / 2 + 2)
    _verify_band_achiral(_band)
    return _band


# =========================================================================
# 7. TRAY  (bottom case: floor + bosses + pins + slots; always FDM)
# =========================================================================


def tray():
    t = _rprism(TRAY_W, TRAY_H, TRAY_R, Z_TRAY_BOT, Z_FLOOR_TOP)
    # Corner bosses: solid Ø9.5 pillars, tray bottom -> +1.5 [§3].
    for (bx, by) in BOSS_CENTERS:
        t += _z_cyl(BOSS_OD, Z_TRAY_BOT, CAP_Z0, bx, by)
        t -= _z_cyl(M3_INSERT_PILOT, Z_INSERT_BOT, CAP_Z0 + _OVER, bx, by)
    # v2.2 boss notch flats: wherever a corner's chamfer leg leaves the round
    # boss under the 0.3 tray/pcb gate (the (0,0) corner at leg 13.2), cut a
    # 45° flat parallel to the chamfer, NOTCH_CLEAR back from it, over the
    # board-passage z zone only. The tray x pcb_board khana gates measure the
    # result — a wrong-corner or wrong-side cut fails them loudly.
    for (bx, by), (cx0, cy0), leg, _slip, standoff in _boss_notches():
        if standoff is None:
            continue
        sx = 1.0 if cx0 == 0.0 else -1.0
        sy = 1.0 if cy0 == 0.0 else -1.0
        c = leg - math.sqrt(2) * NOTCH_CLEAR      # cut plane: |dx|+|dy| = c
        px = cx0 + sx * c / 2.0
        py = cy0 + sy * c / 2.0
        off = 6.0 / math.sqrt(2)
        ang = math.degrees(math.atan2(sy, sx))
        z1 = CAP_Z0 + _OVER
        # [v2.10] The notch cutter is INTERSECTED with the boss cylinder so it
        # can only shave the boss. Unbounded (v2.3..v2.9) its 12x12 diamond
        # footprint also punched a through-hole in the 2.4 mm floor at the
        # encoder corner (x ~2.1..19.1, y ~2.1..19.1) — the "square hole" the
        # owner reported on the printed tray. The boss flat itself is
        # unchanged: same plane, same NOTCH_Z0, same insert-wall number.
        t -= ((Pos(px + sx * off, py + sy * off, (NOTCH_Z0 + z1) / 2.0)
               * Rot(Z=ang) * Box(12.0, 12.0, z1 - NOTCH_Z0))
              & _z_cyl(BOSS_OD, NOTCH_Z0, z1, bx, by))
    # Service slots over the two tacts: fresh-STEP envelope + clearance [S].
    for rec in _TACTS:
        _lbl, x0, x1, y0, y1, _z0, _z1 = rec
        t -= _rprism((x1 - x0) + 2 * SVC_CLEAR, (y1 - y0) + 2 * SVC_CLEAR,
                     SVC_TOOL_R, Z_TRAY_BOT - _OVER, Z_FLOOR_TOP + _OVER,
                     (x0 + x1) / 2, (y0 + y1) / 2)
    # v2.9 BASE MOUNT interface: four blind Ø6.0 x 1.6 pockets in the tray's
    # flat BOTTOM face, on a 25.0 square centred on the case-outline datum.
    # This REPLACES both the v1..v2.8 weight pocket (retired — see the
    # constants block) and v2.8's four corner-boss pockets, which are gone:
    # the bosses are solid again from -7.5 to the insert bottom at -4.2.
    #
    # Cut BEFORE _safe_chamfer, and — unlike v2.8 — deliberately LEFT IN the
    # chamfer pass. v2.8 had to exclude its mouths because they sat on the
    # notched boss where 0.5 mm of lead-in would have necked an already
    # first-article-flagged wall. These mouths sit in the middle of a full
    # 2.4 mm floor with nothing thin within 2 mm, so the elephant-foot pass
    # gives every pocket a free 0.4 x 45° LEAD-IN — which is precisely what a
    # stranger's four-peg base needs in order to start square.
    for (bx, by) in BASE_MOUNT_XY:
        t -= _z_cyl(BASE_MOUNT_D, Z_TRAY_BOT - _OVER, Z_BASE_MOUNT_TOP, bx, by)
    return _safe_chamfer(t, Z_TRAY_BOT, EFC_CHAMFER,
                         exclude_xy=BOSS_CENTERS, exclude_r=BOSS_OD / 2 + 2)


def pcb_retention():
    """Support bosses + press pins at H5/H6/H7 (board floats on these)."""
    parts = []
    for (cx, cy) in RETENTION:
        parts.append(_z_cyl(SUPPORT_BOSS_D, Z_FLOOR_TOP, REAL_PCB_BOT, cx, cy))
        parts.append(_z_cyl(PIN_D, REAL_PCB_BOT, PIN_TOP, cx, cy))
    return Compound(children=parts)


# --- v2.10 support keep-out proof (pure math; NO CAD calls) ----------------
# These are plain build-time asserts, deliberately NOT khana assertions: the
# khana gate set is frozen at 101/8 and the mechanism check only sees the
# FINISHED solid, so it can tell you a support hit something but not that a
# support is standing in an LED's beam. Optics are not interference.


def _rect_poly(cx, cy, sx, sy, rot_deg=0.0):
    """Vertices of an sx x sy rectangle centred (cx, cy), rotated rot_deg."""
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    hx, hy = sx / 2.0, sy / 2.0
    return [(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca)
            for (dx, dy) in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def _aabb_poly(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _poly_axes(poly):
    """Unit edge normals; empty for a degenerate 1-point polygon."""
    out = []
    if len(poly) < 2:
        return out
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        ex, ey = x1 - x0, y1 - y0
        ln = math.hypot(ex, ey)
        if ln > 1e-12:
            out.append((-ey / ln, ex / ln))
    return out


def _poly_overlap(a, b):
    """Separating-axis overlap test (both polygons must be convex)."""
    for (ax, ay) in _poly_axes(a) + _poly_axes(b):
        pa = [px * ax + py * ay for (px, py) in a]
        pb = [px * ax + py * ay for (px, py) in b]
        if max(pa) < min(pb) - 1e-12 or max(pb) < min(pa) - 1e-12:
            return False
    return True


def _pt_seg_dist(px, py, ax, ay, bx, by):
    ex, ey = bx - ax, by - ay
    ln2 = ex * ex + ey * ey
    t = 0.0 if ln2 < 1e-18 else max(
        0.0, min(1.0, ((px - ax) * ex + (py - ay) * ey) / ln2))
    return math.hypot(px - (ax + t * ex), py - (ay + t * ey))


def _poly_dist(a, b):
    """EXACT 2D distance between two convex polygons; 0.0 if they overlap.

    Points are degenerate polygons. Deliberately NOT a bounding-box proxy:
    the chamfer-pad clearances this gates are decided at the 1-2 mm scale
    and a bbox would silently pass a real collision (and silently fail a
    legal 45-deg pad).
    """
    if _poly_overlap(a, b):
        return 0.0
    best = float("inf")
    for (p, q) in ((a, b), (b, a)):
        for (px, py) in p:
            if len(q) == 1:
                best = min(best, math.hypot(px - q[0][0], py - q[0][1]))
                continue
            for i in range(len(q)):
                (x0, y0), (x1, y1) = q[i], q[(i + 1) % len(q)]
                best = min(best, _pt_seg_dist(px, py, x0, y0, x1, y1))
    return best


def _support_poly(sup):
    """Plan footprint of one support: tangential_len x RAIL_SUP_D, rotated."""
    cx, cy, tlen, ang = sup
    return _rect_poly(cx, cy, tlen, RAIL_SUP_D, ang)


def _verify_rail_supports():
    """BUILD-TIME keep-out proof for all 14 v2.10 supports (plain math).

    Returns {class: (margin_mm, support_index, tag)} — the tightest case per
    check class, margin = measured distance MINUS required keep-out, so the
    pass condition is margin >= 0 everywhere. Every failure is an assert
    naming the support index + centre, the keep-out and the measurement.
    """
    worst = {}

    def _note(cls, margin, idx, tag):
        if cls not in worst or margin < worst[cls][0]:
            worst[cls] = (margin, idx, tag)

    # RE1's SEVEN through-holes: 3 encoder + 2 switch signal pads (half
    # extent 1.0) and the 2 MP mounting posts (half extent 1.9 — the Ø2.80
    # drills, the largest on the part, which the deleted v2.3 relief missed).
    re1_pads = [(RE1[0] + dx, RE1[1] + dy, 1.0) for (dx, dy) in
                ((0.0, 0.0), (0.0, 2.5), (0.0, 5.0),
                 (14.5, 0.0), (14.5, 5.0))]
    re1_pads += [(RE1[0] + 7.5, RE1[1] - 3.1, 1.9),
                 (RE1[0] + 7.5, RE1[1] + 8.1, 1.9)]
    # LED15/LED16 are the only two side-fire parts aimed OUTWARD (-y, into
    # the near band wall: the deliberate USB accent). Identified by
    # COORDINATE, never by list order.
    lens_out = [(lx, ly) for (lx, ly) in UNDERGLOW_LEDS
                if (round(lx, 3), round(ly, 3)) in ((32.0, 5.0), (52.0, 5.0))]
    assert len(lens_out) == 2, (
        "RAIL SUPPORT FAIL: expected the 2 outward-firing side-fire lenses "
        f"at (32,5) and (52,5) in UNDERGLOW_LEDS, found {lens_out}")
    tan60 = math.tan(math.radians(60.0))

    for i, sup in enumerate(RAIL_SUPPORTS):
        p = _support_poly(sup)
        at = f"support {i} centre ({sup[0]}, {sup[1]}) len {sup[2]} rot {sup[3]}"
        # (1) every STEP component envelope, +RAIL_INFL
        for rec in PCB.COMPONENTS:
            lbl, x0, x1, y0, y1, _za, _zb = rec
            d = _poly_dist(p, _aabb_poly(x0, x1, y0, y1))
            _note("component", d - RAIL_INFL, i, lbl)
            assert d >= RAIL_INFL - 1e-9, (
                f"RAIL SUPPORT FAIL: {at} is {d:.3f} mm from component "
                f"{lbl} [{x0}..{x1}, {y0}..{y1}] — keep-out RAIL_INFL "
                f"{RAIL_INFL}")
        # (2) the 10 side-fire LED packages, +RAIL_LED_INFL (body clearance)
        for (lx, ly) in UNDERGLOW_LEDS:
            d = _poly_dist(p, _rect_poly(lx, ly, LED_SIDE_BOX, LED_SIDE_BOX))
            _note("led_body", d - RAIL_LED_INFL, i, f"LED ({lx}, {ly})")
            assert d >= RAIL_LED_INFL - 1e-9, (
                f"RAIL SUPPORT FAIL: {at} is {d:.3f} mm from the side-fire "
                f"LED package at ({lx}, {ly}) — keep-out RAIL_LED_INFL "
                f"{RAIL_LED_INFL}")
        # (3) THE optical check: LED15/LED16 fire OUTWARD, so nothing may
        #     stand in their +/-60 deg cone from the lens face down to the
        #     board edge. (The other eight fire INWARD across the cavity; a
        #     support BESIDE one of those blocks nothing.)
        for (lx, _ly) in lens_out:
            cone = [(lx - 0.5, 4.35), (lx + 0.5, 4.35),
                    (lx + 0.5 + 4.35 * tan60, 0.0),
                    (lx - 0.5 - 4.35 * tan60, 0.0)]
            d = _poly_dist(p, cone)
            _note("led_beam", d, i, f"lens x={lx}")
            assert d > 0.0, (
                f"RAIL SUPPORT FAIL: {at} stands IN the +/-60 deg outward "
                f"beam cone of the lens at ({lx}, 4.35) — measured overlap "
                f"(distance {d:.3f}); keep-out is structural (no contact "
                f"permitted, not a margin)")
        # (4) the USB receptacle zone
        d = _poly_dist(p, _rect_poly(USB_X, 3.0, USB_RECEPT_W, 16.0))
        _note("usb", d - RAIL_INFL, i, "USB zone")
        assert d >= RAIL_INFL - 1e-9, (
            f"RAIL SUPPORT FAIL: {at} is {d:.3f} mm from the USB zone "
            f"({USB_X}, 3.0) {USB_RECEPT_W} x 16 — keep-out RAIL_INFL "
            f"{RAIL_INFL}")
        # (5) RE1's seven through-hole pads (replaces the deleted relief)
        for (px, py, he) in re1_pads:
            d = _poly_dist(p, [(px, py)])
            _note("re1_pad", d - he - RAIL_INFL, i, f"RE1 pad ({px}, {py})")
            assert d >= he + RAIL_INFL - 1e-9, (
                f"RAIL SUPPORT FAIL: {at} is {d:.3f} mm from the RE1 pad "
                f"centre ({px}, {py}) — keep-out {he} half-extent + "
                f"RAIL_INFL {RAIL_INFL} = {he + RAIL_INFL}")
        # (6) the 10 parsed JS1 THT pads
        for (wx, wy, _drill, pad) in JS1_PADS:
            d = _poly_dist(p, [(wx, wy)])
            _note("js1_pad", d - pad / 2.0 - RAIL_INFL, i,
                  f"JS1 pad ({wx:.2f}, {wy:.2f})")
            assert d >= pad / 2.0 + RAIL_INFL - 1e-9, (
                f"RAIL SUPPORT FAIL: {at} is {d:.3f} mm from the JS1 pad "
                f"centre ({wx:.2f}, {wy:.2f}) — keep-out pad/2 "
                f"{pad / 2.0} + RAIL_INFL {RAIL_INFL}")
        # (7) the service slots (measured openings [S])
        d = _poly_dist(p, _aabb_poly(59.0, 76.0, 83.3, 93.3))
        _note("service", d - 0.5, i, "service slots")
        assert d >= 0.5 - 1e-9, (
            f"RAIL SUPPORT FAIL: {at} is {d:.3f} mm from the service-slot "
            f"opening x 59..76 y 83.3..93.3 — keep-out 0.5")
    return worst


def pcb_rail():
    """v2.10 discrete edge supports (owner directive 2026-08-19: the
    continuous lip "covers up the LEDs"; replace it with columns, a few per
    side). Fourteen towers rising floor -> board underside (-1.51, the same
    plane as the support bosses): four 45-deg pads on the chamfer corner
    arcs that the O9.5 screw bosses already black out, plus 2-3 short
    columns per edge in the dark gaps between the LED beam windows.

    Still a separate assembly part named pcb_rail ON PURPOSE: it TOUCHES
    pcb_board by design (so it cannot live in `tray`, whose >=0.3 board
    gate is the boss/chamfer spec), and keeping the name keeps every
    existing khana gate (components/leds/usb >=0.3, js_pins >=0.5) binding
    on the new geometry. It prints as one body with the tray (unioned at
    export).

    Every support is verified at BUILD TIME by _verify_rail_supports()
    against: component envelopes (+RAIL_INFL), the 10 side-fire LED
    packages (+RAIL_LED_INFL), LED15/16's outward +/-60-deg beam cones, the
    USB receptacle zone, RE1's SEVEN through-hole pads (the deleted v2.3
    relief covered only five - it missed the two MP posts carrying the
    largest drills on the part), the JS1 THT pads, and the service slots."""
    _verify_rail_supports()
    sups = []
    for (cx, cy, tlen, ang) in RAIL_SUPPORTS:
        sups.append(Pos(cx, cy, 0) * Rot(0, 0, ang)
                    * _box(0, 0, Z_FLOOR_TOP, REAL_PCB_BOT, tlen, RAIL_SUP_D))
    return Compound(children=sups)


# =========================================================================
# 8. ASSEMBLY + MECHANISM GATES
# =========================================================================


def build_assembly():
    a = (
        Assembly()
        .with_part("fr4_plate", fr4_plate())
        .with_part("band", band())
        .with_part("tray", tray())
        .with_part("pcb_retention", pcb_retention())
        .with_part("pcb_rail", pcb_rail())
        .with_part("pcb_board", pcb_board())
        .with_part("pcb_components", pcb_components())
        .with_part("sockets", sockets())
        .with_part("leds", leds())
        .with_part("ec11_body", ec11_body())
        .with_part("js_body", js_body())
        .with_part("usb_recept", usb_receptacle())
        .with_part("knob_sweep", knob_sweep())
        .with_part("js_sweep", js_sweep())
        # [v2.17] the SECOND shipped stick topper, at its own 22.5° restricted
        # throw. js_sweep (nub, 30°) and js_sweep_puck are ALTERNATES — never
        # fitted together — so their mutual overlap, and each one's overlap
        # with the other's rest pose, are modelling artifacts, not defects.
        # They are reported (never asserted) and ledgered in §27.
        .with_part("js_sweep_puck", js_sweep_puck())
        .with_part("screws", screws())
        # v2.4 E2E completion: real populated hardware above/below the deck.
        .with_part("js_pins", js_pins())
        .with_part("switch_bodies", switch_bodies())
        .with_part("keycaps", keycaps())
        .with_part("knob", knob())
        .with_part("stick_cap", stick_cap())
    )
    # Case-controlled parts vs everything; board-resident proxies are NOT
    # asserted against each other — sockets/LEDs/components all live on the
    # frozen board and my envelopes for the unmodeled parts are deliberately
    # coarse (the centered Kailh socket box overlaps real neighboring caps
    # and the per-key LEDs by construction). Their mutual geometry is the
    # PCB designer's solved fact, out of case scope. v1 drew the same line.
    case_parts = ["fr4_plate", "band", "tray", "pcb_retention", "pcb_rail",
                  "screws"]
    board_parts = ["pcb_board", "pcb_components", "sockets", "leds",
                   "ec11_body", "js_body", "usb_recept"]
    for i, p in enumerate(case_parts):
        for q in case_parts[i + 1:]:
            a = a.assert_no_interference(p, q)
        for q in board_parts:
            a = a.assert_no_interference(p, q)
    a = (
        a
        # Swept controls vs everything they could shave.
        .assert_no_interference("knob_sweep", "fr4_plate")
        .assert_no_interference("knob_sweep", "band")
        .assert_no_interference("knob_sweep", "screws")
        .assert_no_interference("js_sweep", "fr4_plate")
        .assert_no_interference("js_sweep", "band")
        .assert_no_interference("js_sweep", "screws")
        # [v2.17] the puck alternate gets the SAME case-side gate set as the
        # nub. It is the LARGER envelope (Ø9.412 vs Ø6.189) and reaches
        # 1.24 mm lower, so these three are the ones that could newly bind.
        .assert_no_interference("js_sweep_puck", "fr4_plate")
        .assert_no_interference("js_sweep_puck", "band")
        .assert_no_interference("js_sweep_puck", "screws")
        # Documented coaxial overlap: knob mounts on the EC11 shaft above the
        # body — alarm if it ever vanishes (v1 pattern).
        .assert_interference("knob_sweep", "ec11_body",
                             reason="knob mounts on the EC11 shaft above its body")
        # Design-critical clearances (spec gates).
        .assert_clearance("band", "pcb_board", min_mm=0.25)
        .assert_clearance("sockets", "tray", min_mm=1.0)
        .assert_clearance("usb_recept", "tray", min_mm=0.2)
        # v2.2: with the FLIPPED J1 the receptacle envelope crosses the band
        # wall plane into the aperture — this gate is load-bearing for the
        # first time (against the backwards J1 it was vacuous). Expected
        # margins: 0.2 per x side (Ø10.0 vs 9.6), 0.2 top, 0.14 bottom.
        .assert_clearance("band", "usb_recept", min_mm=0.1)
        .assert_clearance("tray", "pcb_board", min_mm=0.3)     # boss/chamfer
        .assert_clearance("screws", "pcb_board", min_mm=1.0)   # bolts-out
        .assert_clearance("screws", "pcb_components", min_mm=1.0)
        # Opening vs the square 11.7 body proxy. [v2.12] now ASYMMETRIC: the
        # flats are 0.65 on -x/N/S and 1.65 on +x (the widened side); the
        # corner diagonals are 0.298 on -x (5*sqrt2+1.5 - 5.85*sqrt2,
        # UNCHANGED — that edge is frozen) and ~0.64 on +x. The BINDING
        # number is therefore still the 0.298 at the two -x corners: widening
        # to the right cannot improve a left-side minimum. Real EC11 corners
        # are relieved; v1 shipped this opening with a bare no-interference
        # gate. 0.25 keeps a hard positive floor.
        .assert_clearance("fr4_plate", "ec11_body", min_mm=0.25)
        # v2.4: the YA13 body threads the new plate opening. The binding
        # distance is HORIZONTAL now (E/S tabs 0.25 from the opening's E/S
        # edges); floor 0.2 per spec (de-risk measured 0.25).
        .assert_clearance("fr4_plate", "js_body", min_mm=0.2)
        .assert_clearance("pcb_retention", "ec11_body", min_mm=5.0)
        .assert_clearance("pcb_retention", "js_body", min_mm=5.0)
        # v2.3 rail gates: it touches pcb_board BY DESIGN (no-interference
        # covers that pair — contact is zero-volume); everything populated
        # must keep real distance to it.
        .assert_clearance("pcb_rail", "pcb_components", min_mm=0.3)
        .assert_clearance("pcb_rail", "leds", min_mm=0.3)
        .assert_clearance("pcb_rail", "usb_recept", min_mm=0.3)
    )
    # ==== v2.4 E2E gates (populated hardware) ============================
    # switch_bodies vs everything they could clash (fr4_plate = REAL cutout-
    # alignment check: 13.9 lower housing inside the 14.0 cutout).
    for q in ("fr4_plate", "band", "tray", "pcb_rail", "screws", "knob",
              "stick_cap", "js_body", "ec11_body"):
        a = a.assert_no_interference("switch_bodies", q)
    # keycaps "won't hit a key". NOTE: keycaps x js_sweep is DELIBERATELY not
    # asserted here. v2.5: the shipping DEFAULT taper cap CLEARS SW4 (overlap
    # 0.00, +0.29 edge clearance — reported in __main__). The pair stays
    # NON-asserted because the dome/dish/knurl ALTERNATES still graze SW4 at
    # full tilt (v2.4 measured the dome at 40.78 mm^3); gating it would abort
    # the other 100 gates whenever an alternate cap is selected. The measured
    # advisory (__main__ + CASE-V2-NOTES §15) is the record. Every other
    # keycap pair IS gated.
    for q in ("band", "screws", "knob_sweep", "fr4_plate"):
        a = a.assert_no_interference("keycaps", q)
    # knob (accurate static Ø18 z 8.0..17.5) vs the deck stack + keys.
    for q in ("fr4_plate", "band", "keycaps", "screws"):
        a = a.assert_no_interference("knob", q)
    # stick cap (static rest pose) vs the deck.
    a = (a.assert_no_interference("stick_cap", "fr4_plate")
          .assert_no_interference("stick_cap", "band")
          # js_body threads the opening (no-interference) + clears the NE
          # boss + rail + band (all in the case/board loop above); explicit
          # de-risk margins are printed in __main__.
          # js_pins (10 THT tails) vs the tray floor + perimeter rail.
          .assert_no_interference("js_pins", "tray")
          .assert_no_interference("js_pins", "pcb_rail")
          .assert_clearance("js_pins", "tray", min_mm=0.5)
          .assert_clearance("js_pins", "pcb_rail", min_mm=0.5))
    return a


assembly = build_assembly()


def _advisory_printability(part, name, up_axis, out):
    """inspect() as ADVISORY (mechanism check is the sole hard gate).

    Known intentional thin zones: the band's corner crescents (~0.74 mm at
    one azimuth per corner, cosmetic shell around the structural Ø9.5 boss)
    and the tray weight-pocket floor (0.8 mm, v1-accepted)."""
    try:
        inspect(part, method=FDM(up_axis=up_axis, wall_min_mm=1.0),
                out=out, name=name)
        verdict = "PASS"
    except SystemExit:
        verdict = "ADVISORY (documented thin zones; see CASE-V2-NOTES)"
    data = json.load(open(os.path.join(out, f"{name}-printability.json")))
    oh = data.get("overhang") or {}
    print(f"[printability] {name}: {verdict} | min_wall={data.get('min_wall_mm')}"
          f" | overhang_area={oh.get('area_mm2')} max_deg={oh.get('max_angle_deg')}")


if __name__ == "__main__":
    for k, v in _corner_margins().items():
        print(f"[corner] {k} = {v:.3f}")
    print(f"[corner] band_crescent_wall class = {_crescent_mode()} "
          f"(WALL {WALL} vs the arc/flat transition at "
          f"{OUTER_R - PCB_CLEARANCE - BOSS_C:.1f}); head_to_plate_edge + "
          "plate_hole_edge_web are PLATE measures and are WALL-INVARIANT "
          "(v2.7 erratum — CASE-V2-NOTES §18)")
    # v2.6 sidewall report (the owner-tunable parameter + what rides on it).
    # rim = plate-recess wall -> outer face, on the flats (the visible ring)
    _rim = (CX - POCKET_W / 2) + WALL + PCB_CLEARANCE
    # bridge = outer face -> USB mating face: the tunnel the plug shell crosses
    _bridge = WALL + PCB_CLEARANCE - USB_FACE_PROUD
    print(f"[v2.7-WALL] WALL = {WALL} (source: {WALL_SOURCE}; v2.7 default "
          "5.4, gated variants 3.0 / 5.4 / 7.4 via AGENTPAD13_WALL)")
    print(f"[v2.6-WALL] WALL = {WALL} (owner-tunable) -> OUTER "
          f"{OUTER_W:.1f} x {OUTER_H:.1f} (R{OUTER_R}); INNER "
          f"{INNER_W:.1f} x {INNER_H:.1f} (R{INNER_R} FROZEN -> PLATE_R "
          f"{PLATE_R}, TRAY_R {TRAY_R} unmoved)")
    print(f"[v2.6-WALL] visible rim ring (band material, plate recess -> outer "
          f"face, flats) = {_rim:.2f} mm, plus the {PLATE_FIT:.1f} nominal "
          f"reveal per side; bare-wall USB tunnel would be "
          f"{_bridge:.2f} mm "
          f"(~5.0 comfortable / ~6.5 typical plug shell reach)")
    # ---- v2.13 PLATE POCKET FIT ------------------------------------------
    print(f"[v2.13-FIT] PLATE_FIT = {PLATE_FIT} uniform -> pocket "
          f"{POCKET_W:.1f} x {POCKET_H:.1f} R{POCKET_R:.1f} around the shipped "
          f"plate {PLATE_W:.1f} x {PLATE_H:.1f} R{PLATE_R:.1f} "
          f"(legacy pocket was {LEGACY_POCKET[0]:.1f} x {LEGACY_POCKET[1]:.1f} "
          f"R{LEGACY_POCKET[2]:.1f} — the 2026-07 resin order)")
    print(f"[v2.13-FIT] plate float in the pocket: X {PLATE_FLOAT_X:.1f} mm "
          f"(was {LEGACY_POCKET[0] - PLATE_W:.1f}) | Y {PLATE_FLOAT_Y:.1f} mm "
          f"(was {LEGACY_POCKET[1] - PLATE_H:.1f} — the ~1 mm gap the owner "
          "measured). ONE band ships; too-tight sands loose in a minute, "
          "too-loose is unfixable, so the shipped fit is the correctable one")
    print(f"[v2.13-FIT] PLATE_H ghost killed: model plate is now the SHIPPED "
          f"{PLATE_W:.1f} x {PLATE_H:.1f} (was 100.2 in the model / 100.0 on "
          f"disk); PLATE_LONG_TRIM {PLATE_LONG_TRIM} now lives in this file "
          "and gen_plate_fab.py consumes PLATE_H directly")
    _pk_x = (INNER_W - POCKET_W) / 2.0
    _pk_y = (INNER_H - POCKET_H) / 2.0
    _lg_x = (INNER_W - LEGACY_POCKET[0]) / 2.0
    _lg_y = (INNER_H - LEGACY_POCKET[1]) / 2.0
    print(f"[v2.13-FIT] pocket wall vs inner cavity wall (+ = lip standing "
          f"inboard above the ledge, - = undercut into the sidewall): "
          f"X {_pk_x:+.2f}/side (legacy {_lg_x:+.2f}) | "
          f"Y {_pk_y:+.2f}/end (legacy {_lg_y:+.2f}) — both axes move from a "
          "shallow undercut to a shallow lip; the ledge below already stands "
          f"{LEDGE_W} inboard, so the lip adds no new overhang")
    _fn = usb_funnel()
    _lead = min(USB_FUNNEL_LEAD, USB_FUNNEL_DEPTH)
    _fb = None if _fn is None else _fn.bounding_box()
    print(f"[v2.6-FUNNEL] USB port funnel depth = {USB_FUNNEL_DEPTH:.2f} "
          f"(= WALL - {USB_FUNNEL_WEB}); pocket {USB_FUNNEL_W} x "
          f"{USB_FUNNEL_H} @ y {USB_FUNNEL_Y_OUT:.2f}..{USB_FUNNEL_Y_BOT:.2f} "
          f"(flat bottom); 45° lead-in leg {_lead:.2f} (bottom leg 0 by "
          f"USB_FUNNEL_FLOOR_MIN); cut bbox x "
          f"{'n/a' if _fb is None else f'{_fb.min.X:.2f}..{_fb.max.X:.2f}'} z "
          f"{'n/a' if _fb is None else f'{_fb.min.Z:.2f}..{_fb.max.Z:.2f}'} "
          f"(band bottom {BAND_Z_BOT}); cut volume "
          f"{0.0 if _fn is None else _fn.volume:.1f} mm^3")
    print(f"[v2.6-FUNNEL] shell bridge (outer seating face -> USB mating face) "
          f"= {USB_SHELL_BRIDGE:.2f} mm — WALL-INVARIANT by construction, so "
          f"the wall pick is purely aesthetic")
    # v2.2 convergence prints (the eyeball-detector companions):
    print(f"[v5] RE1 shaft (board truth) = {RE1_SHAFT}  design = "
          f"{RE1_SHAFT_DESIGN}  match = {RE1_SHAFT == RE1_SHAFT_DESIGN}")
    _ub = usb_receptacle().bounding_box()
    print(f"[v5] usb_recept y {_ub.min.Y:.2f}..{_ub.max.Y:.2f} "
          f"(face proud of board edge by {-_ub.min.Y:.2f}; wall plane at "
          f"{-PCB_CLEARANCE}) x {_ub.min.X:.2f}..{_ub.max.X:.2f}")
    # ---- v2.4 YA13 joystick envelope + de-risk margins -------------------
    _jb = js_body()
    _jbb = _jb.bounding_box()
    print(f"[v2.4-JS] YA13 body (cross) x {_jbb.min.X:.2f}..{_jbb.max.X:.2f} "
          f"y {_jbb.min.Y:.2f}..{_jbb.max.Y:.2f} z 0..{JS_BODY_Z1}; opening "
          f"W{JS_OPEN_W_X} N{JS_OPEN_N_Y} E{JS_OPEN_E_X} S{JS_OPEN_S_Y} R{JS_OPEN_R}; "
          f"{len(JS1_PADS)} THT pins parsed")
    print(f"[v2.4-JS] js_body->plate opening clr = {_jb.distance_to(fr4_plate()):.3f} "
          f"(gate >=0.2); js_body->NE tray boss clr = {_jb.distance_to(tray()):.3f} "
          "(the §12.4 caliper item — RESOLVED by the SW JS1 move; Ø15 cage was "
          "blind to the square-frame corner)")
    _jp = js_pins()
    print(f"[v2.4-JS] js_pins->tray floor clr = {_jp.distance_to(tray()):.3f} "
          f"(gate >=0.5); js_pins->pcb_rail clr = {_jp.distance_to(pcb_rail()):.3f} "
          "(gate >=0.5, after the v2.4 rail skip)")
    # knob covers-the-opening arithmetic. [v2.12] the opening is asymmetric,
    # so report BOTH corner families and the TRUE SIGNED margin — the Ø18
    # default no longer hides the +x corners and saying "hides by" would be a
    # lie. The shortfall is owner-accepted, not a defect.
    _hide_max = KNOB_OD / 2.0 - ENC_OPENING_CORNER_REACH
    _hide_min = KNOB_OD / 2.0 - ENC_OPENING_CORNER_REACH_MIN
    _verdict = ("HIDES all four corners" if _hide_max >= 0 else
                f"LEAVES a {-_hide_max:.3f} mm sliver at the two +x corners "
                "(OWNER-ACCEPTED, v2.12)")
    print(f"[v2.4-KNOB] knob Ø{KNOB_OD}/2 = {KNOB_OD/2:.3f} vs encoder-opening "
          f"corner reach -x {ENC_OPENING_CORNER_REACH_MIN} (margin "
          f"{_hide_min:+.3f}) / +x {ENC_OPENING_CORNER_REACH} (margin "
          f"{_hide_max:+.3f}) -> {_verdict}")
    print(f"[v2.12-ENC] plate opening {ENC_OPENING_W} x {ENC_OPENING_H} "
          f"R{ENC_OPENING_R} centred {ENC_OPENING_C} = shaft "
          f"{RE1_SHAFT_DESIGN} + ({ENC_OPENING_DX}, 0); x "
          f"{ENC_OPENING_X0:.3f}..{ENC_OPENING_X1:.3f} y "
          f"{ENC_OPENING_Y0:.3f}..{ENC_OPENING_Y1:.3f} (left edge FROZEN by "
          "owner directive; +1.000 all on the owner's RIGHT = board +x)")
    print(f"[v2.17-ENC] SUPERSEDED v2.12's 'Ø19 is PARKED' note: the v2 knob "
          f"catalog IS Ø19 and ships, so the +x sliver is CLOSED by "
          f"{KNOB_OD / 2.0 - ENC_OPENING_CORNER_REACH:+.3f} (params hide_floor "
          f"{_KNOB['hide_floor']}). Owner ordered the v2 toppers 2026-08-20.")
    # ---- v2.17 STICK TOPPERS: both shipped parts, each at its own throw ----
    _js = js_sweep()
    _jsb = _js.bounding_box()
    _jpk = js_sweep_puck()
    _jpkb = _jpk.bounding_box()
    print(f"[v2.17-SWEEP] nub_C2 @ {STICK_TILT_DEG}° (no restrictor): south "
          f"reach {_jsb.max.Y - JS1[1]:.3f}, floor z {_jsb.min.Z:.3f} "
          f"(part 11.851 — envelope drops the 0.3 fillet). "
          f"v2.5 taper was 9.037 / 10.467; v2.4 dome 11.279 / 10.038")
    print(f"[v2.17-SWEEP] puck_TPU @ {STICK_TILT_RESTRICTED_DEG}° (its cone "
          f"land IS the stop): south reach {_jpkb.max.Y - JS1[1]:.3f}, floor z "
          f"{_jpkb.min.Z:.3f} (seat {PUCK_SEAT_Z}); LARGER Ø ({2 * PUCK_R} vs "
          f"{2 * STICK_CAP_R:.3f}) and lower floor — the envelope the case "
          "would have been blind to if only the default were modelled")
    # THE joystick-clearance finding the v2.4 directive named: the swept
    # toppers vs the neighbouring keycaps. MEASURED, loud, NOT gated (see the
    # build_assembly note). [v2.17] the reported number is now the TRUE 3-D
    # minimum distance. It used to be (SW4 edge y - sweep bbox max Y), which
    # was only accidentally meaningful for the v2.5 taper, whose south extreme
    # happened to sit inside the keycap z band. The nub's south extreme is at
    # z ~16.24, ABOVE the keycap proxy top (14.6), so that bbox corner is not
    # a point any keycap can touch: the old formula prints -0.100 mm while the
    # solids are 0.736 mm apart. A reporting gate that cries wolf is a defect.
    _kc = keycaps()
    _sw4_edge_y = _REFS["SW4"][1] - KEYCAP_1U / 2.0        # 22.7 (case proxy)
    for _nm, _sw in (("nub_C2 @30°", _js), ("puck_TPU @22.5°", _jpk)):
        print(f"[v2.17-JS-KEYCAP] {_nm}: x keycaps overlap = "
              f"{(_sw & _kc).volume:.2f} mm^3 ; TRUE 3-D min distance = "
              f"{_sw.distance_to(_kc):+.3f} mm (bbox-corner proxy would say "
              f"{_sw4_edge_y - _sw.bounding_box().max.Y:+.3f} — retired)")
    print(f"[v2.17-JS-KEYCAP] ⚠ MODEL CAVEAT: any SW4-clearance number must "
          f"name its keycap model. THIS case models {KEYCAP_1U} sq x z "
          f"{KEYCAP_Z0}..{KEYCAP_Z1} [CONVENTION]; the toppers model the real "
          "inserted cap (17.50 wide, rim +11.6, top +17.6 dish / +18.2 "
          "plateau) and it is the toppers' 0.25 mm that sized both parts. The "
          "case cap is 0.5 wider and 3.0-3.6 SHORTER, so these two numbers "
          "are different measurements, not a contradiction — never quote one "
          "as 'the' SW4 clearance. See CASE-V2-NOTES §27.")
    # ---- v2.10 DISCRETE EDGE SUPPORTS (the v2.3 continuous rail is gone) --
    _sup_min = _verify_rail_supports()
    _sup_h = REAL_PCB_BOT - Z_FLOOR_TOP                    # 3.59 mm tall
    _sup_vol = pcb_rail().volume
    _oct_per = sum(
        math.hypot(OCTAGON[(i + 1) % len(OCTAGON)][0] - _x,
                   OCTAGON[(i + 1) % len(OCTAGON)][1] - _y)
        for i, (_x, _y) in enumerate(OCTAGON))
    _sup_tan = sum(s[2] for s in RAIL_SUPPORTS)
    _n_pad = sum(1 for s in RAIL_SUPPORTS if abs(s[3]) == 45.0)
    print(f"[v2.10-SUPPORTS] {len(RAIL_SUPPORTS)} discrete supports "
          f"({_n_pad} chamfer pads + {len(RAIL_SUPPORTS) - _n_pad} edge "
          f"columns) x {RAIL_SUP_D} mm radial depth, z {Z_FLOOR_TOP} -> "
          f"{REAL_PCB_BOT} (top = board underside, same plane as the "
          f"bosses); bearing area {_sup_vol / _sup_h:.1f} mm^2 "
          f"({_sup_vol:.1f} mm^3 / {_sup_h:.2f} mm)")
    print(f"[v2.10-SUPPORTS] tangential occupancy {_sup_tan:.1f} / "
          f"{_oct_per:.1f} mm of octagon perimeter = "
          f"{100 * _sup_tan / _oct_per:.1f}% (was 91.8% for the v2.3 "
          "continuous rail — same measure, its 0.2-inset outboard face "
          "covered 307.7 of the same 335.0 mm; the 84% the old [v2.3-RAIL] "
          "line printed was VOLUME survival, not perimeter). The remaining "
          "perimeter is now open to the ten side-fire LEDs.")
    print("[v2.10-SUPPORTS] per-support keep-outs are ASSERTED at build by "
          "_verify_rail_supports(); tightest margin per class below "
          "(measured minus required, mm; led_beam is raw clearance to the "
          "outward +/-60 deg cone, required > 0):")
    for _k in sorted(_sup_min):
        _m, _i, _t = _sup_min[_k]
        print(f"[v2.10-SUPPORTS]   {_k:<10s} {_m:+7.3f}  (support {_i} @ "
              f"{RAIL_SUPPORTS[_i][0]}, {RAIL_SUPPORTS[_i][1]} vs {_t})")
    # ---- v2.9 BASE MOUNT interface (the only tray change this rev) --------
    _nb = [r for r in _boss_notches() if r[4] is not None]
    _stand = _nb[0][4] if _nb else None
    _insert_wall = None if _stand is None else _stand - M3_INSERT_PILOT / 2.0
    print(f"[v2.9-BASE] datum ({CX}, {CY}) = centre of the case outline "
          f"(band {OUTER_W:.1f}x{OUTER_H:.1f} and tray {TRAY_W:.1f}x{TRAY_H:.1f} "
          "are both centred on it)")
    print(f"[v2.9-BASE] 4 pockets Ø{BASE_MOUNT_D} x {BASE_MOUNT_DEPTH} deep "
          f"(z {Z_TRAY_BOT} .. {Z_BASE_MOUNT_TOP}) on a {BASE_MOUNT_PITCH} "
          f"square: {[(round(a, 2), round(b, 2)) for a, b in BASE_MOUNT_XY]}")
    print(f"[v2.9-BASE] bolt-circle Ø{math.hypot(BASE_MOUNT_PITCH, BASE_MOUNT_PITCH):.2f} "
          f"-> smallest base carrying the whole pattern with a 3 mm wall = "
          f"Ø{math.hypot(BASE_MOUNT_PITCH, BASE_MOUNT_PITCH) + BASE_MOUNT_D + 6:.1f}")
    print(f"[v2.9-BASE] floor left above each pocket = "
          f"{TRAY_T - BASE_MOUNT_DEPTH:.2f} (>= {BASE_MOUNT_FLOOR_MIN}); "
          f"material removed = "
          f"{4 * math.pi / 4 * BASE_MOUNT_D ** 2 * BASE_MOUNT_DEPTH:.1f} mm^3")
    _wmin = min(
        [math.hypot(mx - rx, my - ry) - BASE_MOUNT_D / 2 - SUPPORT_BOSS_D / 2
         for (mx, my) in BASE_MOUNT_XY for (rx, ry) in RETENTION]
        + [math.hypot(mx - cx, my - cy) - BASE_MOUNT_D / 2 - BOSS_OD / 2
           for (mx, my) in BASE_MOUNT_XY for (cx, cy) in BOSS_CENTERS])
    print(f"[v2.9-BASE] tightest pocket->feature gap = {_wmin:.3f} mm "
          f"(>= {BASE_MOUNT_KEEPOUT} asserted)")
    print(f"[v2.9-BASE] WEIGHT POCKET RETIRED: +{60.0 * 30.0 * 1.6:.0f} mm^3 of "
          "floor restored; the tray's 1800 mm^2 of 0.8 mm floor is now "
          f"{4 * math.pi / 4 * BASE_MOUNT_D ** 2:.0f} mm^2 at "
          f"{TRAY_T - BASE_MOUNT_DEPTH:.1f} mm (v2.11: the plinth took the "
          "thinnest floor in the part off the table). Ballast moves to "
          "the base (bases/ BALLAST_*), which carries ~10x more, reversibly, "
          "and BELOW the desk plane instead of 6 mm above it.")
    print(f"[v2.9-BASE] v2.8 corner-boss pockets REMOVED -> heat-set "
          f"over-press buffer below the insert back to "
          f"{Z_INSERT_BOT - Z_TRAY_BOT:.1f} mm (was 1.3 in v2.8); "
          f"(0,0) notch wall unchanged at {_insert_wall:.4f}; the SJ61A1 "
          "bumpon lands on a FULL Ø9.5 boss bottom again")

    out = os.path.join(HERE, "outputs", "case")
    os.makedirs(out, exist_ok=True)
    check(assembly, out=out)                            # HARD GATE

    stl_dir = os.path.join(HERE, "stl")
    step_dir = os.path.join(HERE, "step")
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(step_dir, exist_ok=True)

    band_part = band()
    # pins + perimeter rail print as one body with the tray (v2.3)
    tray_part = tray() + pcb_retention() + pcb_rail()
    plate_part = fr4_plate()

    _advisory_printability(band_part, "band", up_axis=(0, 0, 1), out=out)
    _advisory_printability(tray_part, "tray", up_axis=(0, 0, 1), out=out)

    # v2.1: band exported with a _1.6mm suffix (seat deepened for the 1.6 mm
    # fab-stock plate); the 1.5-seat agentpad13_v2_band.* files stay on disk
    # untouched as the record of the earlier geometry.
    # v2.6: the name now carries the SIDEWALL too (_w{WALL}) — the wall is an
    # owner-tunable aesthetic parameter, so every value gets its own file and
    # no supersession is silent. The 2.4-wall agentpad13_v2_band_1.6mm.*
    # (md5 36980cc2ff011dc32d923fb04f7429f7) stay on disk as the SUPERSEDED
    # record of the geometry PCBWay flagged — DO NOT PRINT THEM. Owner uploads
    # the _w{WALL} STL for printing.
    # [v2.13] The tight pocket regenerates IN PLACE under the canonical
    # _w{WALL} names — one band ships, no variant suffix (owner: "I'm kind of
    # inclined to make this the only version actually").
    _band_name = f"agentpad13_v2_band_1.6mm_w{WALL:.1f}"
    export_stl(band_part, os.path.join(stl_dir, f"{_band_name}.stl"))
    export_step(band_part, os.path.join(step_dir, f"{_band_name}.step"))
    # v2.2: tray gained the corner-boss notch for the v5 board's 13.2
    # chamfer — exported under a _v5 suffix; the old agentpad13_v2_tray.*
    # stay on disk as the pre-notch record. Do NOT print those for a v5
    # board (the (0,0) corner would sit 0.65 into the boss).
    # [v2.10] MIRROR AT EXPORT. The design frame is LEFT-handed (x right,
    # y DOWN from raw KiCad board coordinates, z up) while STL and STEP are
    # right-handed, so every solid exported through this path is the
    # enantiomorph of the intended part. The owner printed the tray and it
    # came out mirrored over the x-axis. Fixed HERE, for the tray only: the
    # band is ordered, fits the PCB, and is orientation-agnostic up to its
    # USB hole, so it exports exactly as before. Proof: retention-pin tops
    # land at y 3.00..59.75 (was 40.25..97.00), matching H5/H6/H7 on the
    # real board, with the service slots over SW14/SW15.
    tray_print = Pos(0, PCB_H, 0) * mirror(tray_part, about=Plane.XZ)
    export_stl(tray_print, os.path.join(stl_dir, "agentpad13_v2_tray_v5.stl"))
    export_step(tray_print,
                os.path.join(step_dir, "agentpad13_v2_tray_v5.step"))
    # Plate is ORDERED (FR4), not printed: STEP for records; the fab files
    # (.kicad_pcb + DXF) come from gen_plate_fab.py.
    export_step(plate_part, os.path.join(step_dir, "agentpad13_v2_plate.step"))
    print(f"exported band ({_band_name}), tray(+pins), plate to stl/ and step/")

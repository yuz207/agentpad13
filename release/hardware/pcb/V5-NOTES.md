# V5-NOTES — corrected board lineage (started fresh 2026-07-19, evening)

> **Historical ledger.** Paths and order holds below record superseded work and
> are not public build instructions. `v5_7` is the sole current public board and
> order set; it supersedes v5_6 by correcting the LED20/LED21 underglow direction.

Predecessor v5 attempt discarded in full → `v5-discarded/` (owner order; kept as evidence).
This v5 = **v4_r27 + the RE1 block move**, executed per `hardware/pcb/v4/RE1-MOVE-CHARTER.md`
and the owner's block-shift doctrine (poo3-1/2/3, poo4 — rigid cluster move, straight shears,
bypass pass-throughs, surgical-route only the flagged stubs).

## v5.kicad_pcb — EXECUTION LEDGER (2026-07-19, append-only)

**Base:** `hardware/pcb/v4/v4_r27.kicad_pcb` md5 `af5ad274558fc034d2d098a72d423a25` (verified at load).
**Target (charter §1, MEASURED):** plate file `hardware/case/v2/fab/agentpad13_v2_plate.kicad_pcb`
frame maps 1:1 to board frame (outline 84.4×100.2 rim, M3 circles on boss centers); 13×13 encoder
opening center = **(13.525, 12.5)**. Shaft = RE1 anchor + (7.5, 2.5) ⇒ anchor (13.525,12.5) → **(6.025,10.0)**,
Δ = (−7.5, −2.5).

**Method:** manifest-first block move. Box [11.9,29.2]×[7.6,21.2]; rides = RE1 + all in-box copper of
ENC_A/ENC_B/ENC_SW/GP28/RGB_MCU/+5V + 1 GND stitcher (re-seated (16.96,11.13)→(9.46,9.3));
bypassed (untouched) = GP20, GP21, SW1, RGB_D14, +3V3, GND rest, 3 anchor stubs (ENC_A via
(25.8395,10.6549)+F tail, RGB_MCU vertical (22.9,7.9–11.1), GP28 tip (19.3,7.6)–(19.1,7.8)).
Full clearance sweep (all moved + reconnects vs all static incl. every foreign pad, both layers,
0.152/hole/edge rules) = **0 violations** before any board mutation
(generator: session scratch `gen_manifest.py` → `move_manifest.json`).

**Applied (guarded executor `exec_re1_move.py`, pcbnew 9.0.9, assert→mutate→assert):**
- RE1 (13.525,12.5)→(6.025,10.0), rot 0 preserved, stock pads kept (no shrink, no facet)
- SW chamfer leg 14.6→13.2 (3 Edge.Cuts endpoints; owner: asymmetric OK, band+screws move out in case pass)
- J2 DNP set
- 7 whole segs translated; 6 cuts (ENC_B N, ENC_SW E, GP28 N+S, RGB_MCU N+S… see manifest); 5 moved
  cut-parts re-added; +5V west moved-horizontal DROPPED (owner poo3-3) + static stub trimmed to (11.5,19.0238)
- 18 manual reconnect segments (straight shears + computed bows, all sweep-verified)
- Surgical A* (tools_exec3/autoroute.py, all other copper locked): +5V east (21.7,6.0635)→(29.2,8.5635)
  5 tracks + 2 vias; ENC_A rejoin (18.3395,8.1549)→(25.8395,10.6549) 4 tracks + 2 vias (routed after +5V applied)
- 1 fix post-DRC: GP28 rejoin bend (15.55,5.95)→(15.55,5.6) (slot rect corner graze, stadium-model artifact)
- Zones refilled (3), both layers

**Adjudicated contract/referee updates (charter §3 — owner-directed geometry changes, not reverts):**
- `harness/contract_v4.json`: RE1 → (6.025,10.0); chamfer_vertices SW leg → 13.2; status annotated
- `harness/grade_board.py` CHAMFER_VERTS: SW leg → 13.2 (hard-coded product geometry, same adjudication)

**Verification battery:**
- kicad-cli DRC: **0 violations, 0 unconnected**
- Full harness `grade_board.py v5.kicad_pcb --no-ring`: **PASS all gates** — DRC 0, unconnected 0,
  contract 45/45, ABSENT ok, outline 84.2×100.0 chamfer=ok, +5V spine 207 segs min 0.5, USB pair clean,
  TP5 pour 177mm²
- Positional diff vs v4_r27: 126/126 footprints, **only RE1 moved**; DNP delta = {J2} only;
  segments 1100→1132 (+32 = 18 manual + 5 cut-parts + 9 router — matches manifest exactly); vias 178→182 (+4 router)
- Renders: `~/Desktop/v5_before_after.png` (owner-inspected), poo4.png (plan schematic)

## OPEN ITEMS (in order)
1. **Owner render inspection** (renders-before-commit law) — then optional streamline pass
   (ratcheted, keep-iff-better re-grade) on the moved diagonals/rejoins aesthetics.
2. **Fabpack rebuild** from v5.kicad_pcb (`fabpack/build_fabpack.py` + verify 17/17).
3. **⚠️ PCBWay: DO NOT PAY** — order in audit has the OLD encoder position. Owner swaps gerbers
   (+ verify CPL diff empty; RE1 is hand-solder) BEFORE payment. Plate already ordered = correct.
4. Case pass: band/screw stack moves outward for the 13.2 chamfer (owner-approved growth); khana re-run;
   contract cross_check re-adjudication by coordinator.
5. J1 USB-C 180° blocker: still open, next board action after this banks.

## v5_2.kicad_pcb — streamline pass (2026-07-19 evening, owner-directed de-kink)

Owner directive: smooth the kinks, avoid the new vias where possible (v5_fixed.png). Executed as
rip-and-relay of exactly four affected chains (nothing else touched): ENC_A (now ONE clean B.Cu run
pad→via, (6.025,10)→(19,9.2)→(19.5,8.7)→(21.6,8.7)→(25.8395,10.6549), **0 vias**), GP28 (single F.Cu
re-lay (19.1,7.8)→(15.75,17.6)→(15.35,19.65)→(13.5,20.11)→(12.5736,21.2)), RGB_MCU (single F.Cu re-lay
(22.9,11.1)→(19.3,14)→(16.4,18.4)→(16.05,19.9)→(13.5436,21.2)), +5V (A* re-route, 25.7mm).
**Via floor proven, not assumed:** exhaustive A* at via_pen=50 in every routing order — the ENC_A×+5V
corridor crossing is intrinsic (2 vias) and +5V's entry past the static GP20/GP21 B stubs costs 2 more;
total stays +4 vs v4 (same as v5), but ENC_A is via-free and all paths are single clean runs.
Tool fact for the ledger: tools_exec3/autoroute.py requires BOTH endpoints reachable on B.Cu
(THT-era design) — F.Cu-to-F.Cu reconnects (GP28/RGB_MCU) must be hand-laid or the tool reports
"no path"; hand paths verified against slot/S1/SW1-diag/each-other before apply.
Battery: DRC 0/0; full harness --no-ring ALL GREEN (+5V spine 209 segs min 0.5); segs 1126 (v5: 1132),
vias 182. Banked: v5/hardware/pcb/v5_2.kicad_pcb (+.kicad_pro).

## Case-stack finding (2026-07-19, flagged to owner): chamfer 13.2 vs SW boss
Boss slip at leg 13.2 = (13.2−7.4)/√2 − 4.75 = **−0.649mm (interference)**. Options: (1) notch SW tray
boss 0.65 flat (tray reprint only; ORDERED PLATE STAYS VALID) ← recommended; (2) move boss+screws out
~0.95mm (band grows; plate holes+R5.4 corners move → PLATE RE-ORDER); (3) boss OD shrink (rejected,
knife-edge). Decision at CAD pass.

## Independent verification (background agent, 2026-07-19 night) — ALL PASS, FINALIZATION MET
Report: v5/verify_out/VERIFICATION-REPORT.md. Verdicts: electrical parity PASS (503/503 pads, 87 nets
identical, only RE1 moved, only J2-DNP attr delta); plate lineup PASS (ALL 22 plate features Δ=0.000mm
incl. encoder=shaft exact, 13/13 switches, JS1, LED14 viewing hole, STAB1 wings); firmware PASS
(U1 pad→net byte-identical, check_pins 51/51, conformance 80/80, emulator smoke PASS both UF2s,
UF2 SHA exact — ZERO firmware changes needed); CPL byte-identical to v4 (owner uploads ONLY the new
gerber zip); drill/chamfer deltas exact; DRC 0/0. Surprises (non-blocking): 2 spec-label corrections
(plate Ø3 hole = LED14 viewing hole; 6.65×12.3 slots = STAB1 wings); 1 NEW cosmetic severity-all DRC
warning — RE1 silkscreen RefDes clipped by the 13.2 chamfer (electrically nil; optional silk nudge +
fabpack re-run, owner call). **FINALIZATION CRITERIA: parity MET; plate lineup MET.**

## v5_3.kicad_pcb — owner-directed de-jag round 2 (2026-07-19 late night) — SHIPPING BOARD
Owner rejected v5_2's +5V (jagged, 4 vias "not my line"). Proven at 0.025mm exhaustive: owner's 0-via
line is valid ONLY at signal width; at the mandated 0.5mm (+5V spine gate + LED rail) 0-via AND 1-hop
(2-via) are both impossible (F-islands from west and remnant never meet) → 4 vias = true floor at 0.5mm.
Executed: +5V re-laid (same route class), then the NEW LOS shortcut smoothing pass (smooth_pass analyzer:
LOS vertex-collapse per chain vs full obstacle model NOW INCLUDING footprint Edge.Cuts windows — the LED
aperture arcs; first pass without them clipped 11 apertures, caught by DRC, reverted). Final: 26/30 chains
smoothed (segments 262→~225 on touched nets), 4 chains kept original near 2 mis-sampled arcs.
RE1 silk RefDes → (9.5,8.2) (chamfer clip warning cleared). Battery: DRC 0/0, harness --no-ring ALL GREEN.
Fabpack rebuilt from v5_3, verify 17/17, both SKUs. Tool banked: smooth_pass (LOS de-jag, no re-routing) —
candidate for tools_exec3 adoption; MUST include footprint Edge.Cuts in any obstacle model (lesson).

## v5_3 delta re-verification (background agent, 2026-07-19 late night) — ALL PASS, FINALIZATION MET
D1 pad→net parity vs v4_r27 identical (503/503, 87 nets, only RE1 moved, J2-DNP only attr); D2 DRC 0/0,
zones filled, netlist sync exact; D3 CPL byte-identical (no re-upload); D4 shaft (13.5250,12.5000) exact,
Edge.Cuts byte-identical to v5_2; D5 all six smoothed nets = exactly 1 connected component each;
D6 severity-all = 63 = v4 baseline exactly (silk warning gone, zero RE1-referencing items).
Note: agent's "ENC_A 2 vias" = ENC_A's two PRE-EXISTING v4 vias ((25.8395,10.6549),(28.2854,23.4169));
the v5_2/v5_3 ledger phrase "0 vias" meant zero NEW vias on the rejoin. Total 182 = 178 original + 4 (+5V).
**v5_3 FINALIZATION: MET both criteria. Owner action: swap gerbers_v5_3.zip at PCBWay, CPL/BOM unchanged, then pay.**

## ORDER HOLD (owner, 2026-07-20): NO PCBWay upload/payment until J1 is fixed
v5_3 is the verified BASE, not the order candidate — J1 USB-C is still mounted 180° backwards
(mating face points into the board; unbuildable as a product). Sequence: J1 block-move fix (rotate 180°
about anchor + move to (42.1,3.16), face 0.49 proud; CC1/CC2 swap sides, DP/DM mirror in-row; same
manifest→sweep→executor→harness→verify pipeline as RE1) → bank → fabpack rebuild → re-verify →
ONE gerber swap at PCBWay → pay. Supersedes the earlier "swap gerbers_v5_3 and pay" line above.

## v5_4.kicad_pcb — owner's zero-via +5V line, executed (2026-07-19 night) — SHIPPING BOARD
Owner-approved revised_plan_v2: +5V re-laid as ONE all-B.Cu run on the owner's drawn line — west diagonal
truncated at (14.43,12.55), then (18.3,12.55)→(20.525,12.35) THROUGH THE S1/S2 PAD GAP →(23.3,11.7)→
(26.1,10.85) through the widened via-window →(26.9,10.5)→(28.9,9.8)→ tie (30.3,7.4635) on the remnant.
DELETED: all 8 hop segments + ALL 4 VIAS of the old route. ENC_SW: same spot ~1mm lower, beside +5V:
(20.525,15)→(21.6,12.9)→(23.5,12.3)→(26,11.65)→(26.9,11.6)→(28.9,11.3)→(31.6,10.15)→(32.64,9.81), 0 vias.
Enabler: ENC_A's via slid 0.56mm along its own F track (25.8395,10.6549)→(25.79,10.1) + 0.152 F jog —
widens the GP21/ENC_A via window 1.74→2.24mm; all window margins ≥0.15. Guarded executor exec_v54.py
(exact-endpoint rips, count asserts — two aborts caught bad rip windows before any mutation; final rip:
8 segs + 4 vias + 1 truncation + 2 ENC_SW segs). Battery: DRC 0/0; harness --no-ring ALL GREEN.
**Board vias now 178 = EXACTLY v4's count. Net delta vs v4: 0 vias.** Fabpack rebuilt from v5_4.

## v5_4 delta re-verification (background agent) — ALL PASS, FINALIZATION MET
E1 parity identical (503/503; vias 178 = v4 EXACT); E2 DRC 0/0, severity-all 63 item-for-item = v4
baseline; E3 CPL byte-identical; E4 shaft (13.5250,12.5000) exact; E5 +5V/ENC_SW/ENC_A each exactly
1 component, ties carry copper, NO rip stubs; E6 drill census identical to v4 (178×Ø0.2, PTH 223/NPTH 48),
fabpack md5 = board md5. v5_4 = the encoder-fixed board at ZERO routing cost vs v4. J1 fix next.

## J1 fix (v5_5) — PLAN 85% CONVERGED, NOT EXECUTED (2026-07-20, session end — clean handoff)
Board is UNTOUCHED: v5_4 remains the banked, verified baseline. Plan artifacts: `v5/hardware/pcb/j1_plan.py`
(survey + sweep, run against v5_4 — currently 15 violations in 3 knots) + `j1_manifest.json`.
SETTLED by 4 sweep iterations: rotation 180→0 + anchor (42.1,5.1)→(42.1,3.16) (row→y7.205, face −0.49 proud,
verified pad map: A/B pairs same-net, CC1/CC2 symmetric 5.1k Rd → NO firmware/netlist changes); complete rip
lists for CC1/CC2/DP/DM/VBUS approaches (+6 vias ripped incl. 2 legacy DP-hop vias); deterministic re-dresses
verified: CC1 (via under-body), CC2 (under-body to (47.869,0.465)), GP21 (under-body north of the moved pegs,
west descent x40.6), JOY re-jog ((42.7,11.7)→(42.7,8.7)→(43.5,8.6)→(45,10)); ENC_B via relocation to the
vacated strip (east side, (44.4,1.5)); F-under-body is FREE (pads are B-side) — key routing resource.
REMAINING 3 KNOTS (exact): (1) RUN-vs-ENC_B F-parity crossing — RUN's west tie (41.4,8.7) vs ENC_B's F
descent x43.3–44.4: every corridor tried crosses; candidate: RUN via the far-north strip, blocked by the
+5V-F piece (46.226,4.0614)→(48.9302,1.3572) whose CONNECTIVITY after rips is unverified — resolve what its
ends join first; (2) +5V-B U4 approach: KEEP the original vertical (47.2,7.5215→8.0625) (don't rip), bow only
the diagonal ((50.3083,4.4132)→(47.55,6.6)→(47.2,7.5215)); east-peg 0.334-vs-0.402 is a rect-vs-oval model
artifact — let DRC arbitrate; (3) GP21 vs NPTH (39.21,5.76): reroute leg to (38.6,4.6)→(40.3,4.8)→(41.0,6.3).
THE FUNNEL (DM×2/DP×2/VBUS×2 → U4 anchors (46.25,8.0625)/(45.9273,8.9797)+(47.53,8.98)/(45.7808,9.3463)):
interleaved DM-DP-DM-DP row + crossed anchor order forces ≥1 hop (v4 spent 2 vias on DP-A6 here);
plan: surgical A* per net (all endpoints B-side ✓ tool-compatible), order DM-A7(trapped), DP-A6, DM-B7,
DP-B6, VBUS-E, VBUS-W. NEXT SESSION: resolve knot-1 connectivity → sweep to 0 → executor (guarded, pattern
exec_v54.py) → A* funnel chain → refill → DRC → harness --no-ring → USB-pair gate → bank v5_5 → fabpack →
delta re-verify → THEN the single PCBWay gerber swap. ORDER HOLD STANDS.

## v5_5 execution attempt (2026-07-19 night) — ANCHOR RESOLVED, ROUTING WALL — NOT BANKED
**Base:** v5_4.kicad_pcb md5 `8db3e8e972666bbb430fb705110d1740` (.kicad_pro `21155fc0f4eb6f798484edca0e04d403`) —
recorded as the base hash (ledger gap closed; only v4_r27 hash was previously recorded). v5_4 lineage byte-identical/UNTOUCHED throughout.
**Anchor decision (coordinator-approved, 2 escalations):** pure-rotation-to-3.16 both rejected in favor of
**J1 (42.1,5.1,rot180) → (42.1,3.05,rot0)**, face **0.60mm proud**, row y=7.095. Chain: brief said "pure rotation
anchor-fixed 5.1" (face RECESSED 1.45mm — coordinator agreed unbuildable, chose ledger's reach intent); ledger's
3.16 then found INFEASIBLE — J1's tall east shell tab S1(46.42,6.29) top y=7.34 vs U4.4 bottom y=7.40 = **0.060mm,
need 0.152** (hard pad-pad, not routing-fixable). Feasible window anchor≤3.068; 3.05 chosen (gap 0.170, more proud, still reaches aperture).
**TOOL-TRUTH #1 (prior sweep blind spots — successors MUST know):** `j1_plan.py` parses pad geometry WITHOUT
applying pad rotation (U4 is rot 90°, real extent 0.6×1.325 not 1.325×0.6) AND never checks J1 shell-tabs vs fixed
pads. Both bugs hid the S1-vs-U4.4 conflict and gave false +5V-vs-U4 violations. Use kicad-cli DRC as the authority for any rotated-pad clearance.
**TOOL-TRUTH #2 (over-rip discovery):** the prior manifest over-ripped. DRC on rotate-only board proves the TRUE
minimal rip set at 3.05 = 36 segs + 6 vias (CC1 2, CC2 6+2v, DM 5, DP 7+2v, VBUS 8+2v, ENC_B 1 diagonal, RUN 3, JOY 4).
**+5V needs ZERO rip** (all its copper is x≥47.2, east of the connector body — never conflicts; U4.5 stays connected).
**GP21 and JOY-conflict-with-J1 = ZERO** (all F.Cu; J1 pads are B.Cu-only — no cross-layer conflict). JOY still ripped, but only because it BLOCKS ENC_B's reconnection (not a J1 conflict).
**ROUTING WALL (the blocker):** rip+rotate executor verified (assert 36/6). Reconnection routed via FREEROUTING
1.9.0 (java at /opt/homebrew/Cellar/openjdk/26.0.1; full-network keep-wiring, NO subset dialog — mission-sanctioned).
FR achieves **0 DRC violations** on ~95% of the reconnection but CANNOT close 3 connections in any config
(DM cluster→U4.4, ENC_B→stub-via 43.201/8.236, VBUS A9→tie 45.781/9.346) — genuine 2-layer density limit: J1's
16-pad escape + the U4 funnel + the 3 foreign crossers (ENC_B/RUN/JOY, which now traverse the space J1 occupies)
cram a ~6mm band. FR itself logs "finish the board manually." TOOL FACT: the custom A* (tools_exec3/autoroute.py)
is UNUSABLE for clean finishing — original max(hx,hy)-square pads = can't start (over-conservative); bbox-patched =
DRC-DIRTY (821 viol on a full funnel). FR is the only clean router; it leaves the last ~5%.
**ORDER-FLIP EXECUTED (coordinator's hard-first doctrine, 2nd round):** net-filtered FR (strip easy manifest nets →
filter DSN to hard set → FR) placed the 3 HARD nets (DM/ENC_B/VBUS) SOLID through virgin space (0 DRC) — the method
works for the hard nets. BUT the wall SHIFTS not closes: FR leaves ~4 stragglers in EVERY config tried
(plain→DP unrouted; DP-first→DM/ENC_B/VBUS; hard-first→CC1/DP-B6 + RUN/JOY far-copper gaps). Family-resolving the
easy nets (strip+re-FR) DISTURBS their far/perfect copper (RUN/JOY left FAR gaps at U1.26/U1.38, x>60) — NOT minimal.
**FINDING: the reconnection at 3.05 is at/beyond clean 2-layer routability; no FR ordering closes 100%; the last ~4
connections need DISPLACEMENT (settled-element/via nudge to open ~0.2mm) — each is a judgment call.** Best clean
artifacts (both 0 DRC): `wip305_it.kicad_pcb` (3 local gaps, no far disturbance) and `wip305_full2.kicad_pcb`
(hard nets solid + 4 stragglers incl. 2 near-trivial: RUN 0.08mm, JOY 0.8mm). AWAITING coordinator ruling on the
specific displacement levers. NOT BANKED. ORDER HOLD STANDS.

## CASE v2.2 CONVERGENCE + v5_5 ORDER-SET CORRECTIONS (coordinator, 2026-07-19)

Case side is DONE and green against v5 (see hardware/case/v2/CASE-V2-NOTES.md
§12): khana 63/63, tray notched for the 13.2 chamfer (new files
agentpad13_v2_tray_v5.stl/.step), band geometry PROVEN unchanged (re-export
md5-identical to the ordered-geometry STL), EC11 shaft-true gates landed,
usb_recept envelope = the flip ledger (face 0.49 PROUD; x 37.3–46.9,
y −0.49..6.81) with a sign tripwire + section renders as the eyeball gate.

FOR THE v5_5 EXECUTOR — two order-set corrections found this session:

1. **CPL is NOT unchanged for v5_5** (supersedes the earlier "one gerber
   swap, CPL/BOM unchanged" ledger line — that was true for v5_4 only).
   J1 is machine-placed: both SKU CPLs carry `J1 ... 42.100000,-5.100000,
   180.000000,bottom`; after the flip the row must read y −3.16, rot 0.
   build_fabpack derives CPL from the board via kicad-cli, so a REBUILD
   from v5_5 fixes it automatically — but the PCBWay swap must therefore be
   **gerbers + BOTH cpl_*.csv** (BOM genuinely unchanged, same C165948).
   Recommended: add a targeted verify_fabpack assert on the J1 CPL row
   (y=-3.16, rot=0, bottom) — the numeric twin of the render requirement.
2. **contract_v4.json J1 ref still reads y 5.1 rot 180** — adjudicate to
   y 3.16 rot 0 when banking v5_5 or the harness contract check fails.

Also verified case-side, for the record: no bottom-side component bbox
intersects the flipped J1 body region (nearest U4 at y≥7.8, 0.99 clear);
drill-file diff (pegs/NPTH moved with the footprint) stays on the executor's
battery per the named hazard-1.

ORDER GATES (case side): tray_v5 = self-print, no order; band upload file
UNCHANGED and valid, but the band ORDER stays gated on the §12 JS caliper
rule (cage reach toward (80.5,3.7) ≤ 8.1 mm at z≤3.4; height < 3.15) —
a 60-second measurement of the physical PSP-3000 module.

### ADDENDUM (coordinator): 0.60 proud ACCEPTED — bake it
Case-side answer to the executor's pre-bank question: NO tighter max-proud
exists at x≈42 — the band aperture is a through-wall void; 0.60 accepted and
baked into the case (v2.2.1: khana 63/63, band/tray files byte-identical,
renders updated). No re-land needed. Correction to item 2 above: adjudicate
contract_v4.json J1 to **y 3.05** rot 0 (not 3.16 — that was the plan
value; 3.05 is the authorized anchor). CPL rows will read y −3.05.

## JS1 REPLACEMENT — SOURCING RECORD (BOM-ready; coordinator, 2026-07-19)

Owner decision: the PSP-3000 slider (Adafruit 3103 class) is REJECTED (no real
travel + its Ø18.4 disc rides 0.4 into the plate underside per its own drawing
C4812-001). Replacement selected: **YTL YA13 tilt gimbal, default MPN
YA13-FL7.4-B5Ka(45-10)-R-Y06, LCSC C37323742** ($0.456@1/$0.233@1k, 1014 in
stock, machine-placeable by PCBWay from LCSC).

Verified by drawing (local copies kept out of tree; datasheet
https://datasheet.lcsc.com/datasheet/pdf/14431af5f0bc0c9a36d5b7490e4ae0c6.pdf):
frame 13x13 / bbox 16.7x16.7, body 11.0, stem tip 18.4 (= body 11.0 + free
lever FL7.4), blade top 1.85x1.15, +-30 deg mech (60 deg total), 45+-5 deg
electrical, 2x 5k B +-20%, 100k cycles, stem pull-out >= 3 kgf, pins 6x Ø1.0
(two 3-groups, 2.5 pitch) + 4x Ø1.2 lugs on 10.6x12.5, pin tails ~3.7.
**PIVOT z = 6.1 +- 0.3 above PCB [D]** (1.1 above deck; lever arm to bare tip
12.3) — the sweep-cone input for the case gate.

FOOTPRINT FREEZE: GO. The J13-series base (frame, body, PCB pattern) is
drawing-proven IDENTICAL across variants (YA13 vs YA13S dwg CF-G04-J13-016);
lever length is a reference dim that only moves the stem tip (tip = 11.0+FL).
Shorter levers: NOT commercially available (LCSC carries only FL7.4;
manufacturer publishes no J13 catalog; factory-inquiry only). Owner accepted
FL7.4 height ("couple of keycaps at most").

BOM lines (take effect with the JS1 footprint rev):
- DEFAULT: JS1 = YTL YA13-FL7.4-B5Ka(45-10)-R-Y06, LCSC C37323742,
  machine-placed THT. Nets map 1:1 to existing +3V3/JOY_X/JOY_Y/GND; lugs to
  GND (terminal-frame isolation >=100 Mohm per spec 1.11).
- ALTERNATE 1: YTL YA13S-L7.4-B10Ka(60)-0-DL01, LCSC C37323748 ($0.574, 62
  stock) — SAME core/footprint + integrated tact switch (12V/50mA, travel
  0.3+-0.2); its 4 switch pads extend the pattern to 22.6 wide — NOT in the
  frozen footprint; adopting it needs a footprint extension + spare GPIO.
- ALTERNATE 2 (hand-solder, low-profile): Adafruit 5628 / K-Silver JP19-012
  (+-16 deg, cap+click included) — different footprint, kept as record only.
- DELETED: Adafruit 3103 slider line.
- HOUSE PARTS: printed stick cap (blade-socket 1.85x1.15, sets final height;
  min top ~ +14.2 above deck) + printed encoder knob (Ø>=18 floor) — designed
  as a matched pair. Stock caps: NONE verifiable for the blade; PS4-class caps
  proven INCOMPATIBLE (round Ø4/3.0-flats socket); Joy-Con-class caps
  plausible-unverified (optional $6 caliper test).

Caliper-on-sample list: blade corner radii/tip step (for the printed cap
socket), pivot 6.1 confirmation if any sweep margin < 0.3, Joy-Con cap fit.
Board-side rework scoped on live copper (see js1_pad_swap.png): re-dress
JOY_X/JOY_Y/+3V3 approaches, nudge FB1/C9 ~1mm (W signal column lands 0.55
from FB1 pad), FID2 relocate only if mirrored. RGB_D16 and +5V untouched.

## RELEASE PLAN (owner decision, 2026-07-19): ONE-SHOT v5
Single public release: v5 = J1-flipped board + JS1->YA13 footprint rev +
square-opening plate refab + case v2.3 slice + printed cap/knob, released
together. v5_5 stays an INTERNAL verified checkpoint (no public tag, no
orders from it). Sequence: (1) executor banks v5_5 (in progress — everything
else waits on this); (2) YA13 design pass (task: footprint + FB1/C9 nudge,
plate files, case gates incl. keycap-clearance cone from pivot 6.1, cap+knob
pair); (3) sample caliper confirms; (4) fabpack both SKUs + full checklist;
(5) orders. No PCBWay upload/payment before step 4 completes.

## v5_5 ENDGAME (2026-07-19 late night, finisher session) — append-only phase ledger
P0: base wip305_it.kicad_pcb (md5 a44a5142eca34800a6fe752e2c277839) copied to scratch w0; kicad-cli DRC re-verified: 0 error-severity violations, exactly 3 unconnected (DM-cluster→U4.4, ENC_B B↔F at stub-via, VBUS→J1.A9); 71 warnings all silk/courtyard/text/dangling classes (danglers = the open gap ends). Proceeding to ENC_B stub-via relocation.
P1a (analysis, no mutation yet): full2-vs-it forensics done. full2 PROVES the corridors: ENC_B west descent x36.731 (clears S1-W oval tab 0.238) -> y~8.38 B corridor -> seat; DM cluster->(43.291,5.906)via->F 45-diag->via into U4.4; VBUS-A9 south descent. In wip305_it these are blocked ONLY by session-FR copper: DP-A6 diag crosses ENC_B corridor at (42.535,8.376), DP-B6 hairpin at x~42.7, RUN via (41.4,8.7) 0.324<0.478 (dodgeable by 8.15 dip), CC2 horiz y8.05+via(45.426,8.444) seals DM full2-landing AND VBUS-A9 descent (pinch CC2-end/A12 = 0.231 < 0.532 needed). MEASURED: coordinator step-2 as-literal is infeasible (DM south lane sealed x44.82-45.88 by pad-row/CC2-horiz sandwich 0.23mm; A12+S1-tab pinches 0.27/0.35 < 0.456). DERIVED PLAN (all within the 8-net manifest family; CC1/RUN/JOY untouched): (1) via slide (43.201,8.236)->(43.201,8.56) north-along-stub per step-1 (clear seat vs new DP lane 0.5, A8 0.74, RGB_D15 0.77, JOY-F-vert 0.501); (2) DP re-dress: delete A6/B6 west spaghetti, relay A6 exit->(42.35,8.06)->E-run y8.06->(44.56,8.06)->45diag->(45.48,8.98)->(45.927,8.98), B6 drops 0.24 to join E-run (kills both ENC_B crossings; descent now EAST of seat); (3) VBUS-A9: trivial ~1.6mm B vertical pad-top->(44.4,4.829) VBUS horizontal (A9 component = 2 stacked pads only - verify); (4) DM: full2 topology re-aimed (42.561,5.906)->(43.291,5.906)->via->F diag->(46.05,7.95) via-in-pad U4.4 (margins RUN-F 0.86/0.627, JOY 1.09, A12 0.421>=0.402, CC2-freed); (5) CC2 re-dress north corridor to its east target (geometry TBD after CC2/R2 survey). No U4 break-glass needed if this lands. Next: rules+CC2+west-corridor surveys, then guarded executor.
P1b (plan final, arithmetic-verified): rules read from board: clr 0.152, hole_clr 0.250, h2h 0.250, via 0.5/0.2. VBUS A9+B4 = isolated 2-pad component (union-find verified) -> closes via x44.28 vertical pad->(44.28,4.829) T into VBUS y4.829 horizontal (peg 44.99 edge margin 0.309>=0.25). CC2 today: B5->south dip->via(45.426,8.444)->F->(47.529,4.235-6.653)vert->via(48.925,2.839)->B->R2.1; re-dress: B5->north vert x43.85->via(43.65,5.32)->F y4.85 horiz->45diag->(47.529,4.235) join (S1-E oval cap seg-start dist 0.923-0.5=0.423 ok; +5V-F diag perp 1.04; peg dy edge 0.399). PHASES: A) ENC_B via (43.201,8.236)->(43.201,8.56) slide+stub trim+blob rip + DP re-dress (rip 7 spaghetti segs; relay A6 exit->E-run y8.06 (pad-bottom margin 0.24)->45diag->(45.48,8.98)->join kept 0.2 U4.6 approach; B6 = 0.965 drop to E-run) - seat-vs-E-run 0.5>=0.478, seat-vs-JOY-F-vert 0.501; B) ENC_B corridor: T-descent x36.731 (full2-proven, S1-W cap 0.238)->45->(38.384,8.376)->y8.376->rise y8.15 over RUN via (dy 0.55)->45 down->(42.31,8.56)->seat; C) VBUS vertical; D) CC2 re-dress (rip 6 segs+via, add 5 segs+via); E) DM: cluster->(43.291,5.906)via->F 45diag (y=x-37.186; RUN-F parallel gap 0.627)->(45.246,8.06)->horiz->via(46.05,8.06) IN-PAD U4.4 (A12 corner 0.466>=0.402; CC2-F-old endpoint 0.495>=0.478) - via-in-pad flagged as deliberate (only DRC-clean U4.4 entry; north face sealed by S1-E tab, west by A12). Net count: +2 vias (DM hop) -1 net-zero relocations; only PORT_DP/CC2/ENC_B/VBUS/PORT_DM copper touched (all manifest-family; CC1/RUN/JOY untouched). Executing A.
P2 (Phase A' applied -> wA): first attempt sequenced DP-relay before CC2-rip; DRC caught 4 errors (E-run y8.06 vs CC2 y8.05 shorts) - discarded, folded CC2 re-dress into same mutation. A' = rip 15 segs + 2 vias (ENC_B blob+stub+via, DP 7-seg spaghetti, CC2 south dip), add 12 segs + 2 vias (trimmed stub + seat via (43.201,8.56); DP south lane; CC2 north corridor via (43.65,5.32) + F y4.85). kicad-cli --severity-error: 0 errors, 3 unconnected (same trio; CC2+DP verified still closed). Zones refilled (3).
P3 (Phase B applied -> wB): ENC_B CLOSED. v1 corridor east end clashed with the 45-deg DP exit diag (my plan-vs-implementation mismatch, 3 clearance errors, DRC-caught, discarded); v2 re-geometrized (dive back to y8.5 after RUN-via dodge; via-diag clearance 0.495>=0.478) -> 0 errors but GND_F/GND_B split: bisection + island probe proved the descent seals the west pocket whose C40.2/LED15.4 GND pads were FILL-ONLY grounded (pre-existing fragility, corridor position forced). Fix: +1 GND stitch via (34.0,4.2) restoring their ground via F-fill. DEVIATION vs the 8-net copper-diff law: +1 GND via, ledgered here as required-consequence (refill-only and half-corridor controls ran; not a filler artifact). Final B: 9 ENC_B segs + 1 GND via; DRC 0 errors, 2 unconnected (DM, VBUS). Pre-existing BOOTSEL-area F orphan island (52.5,27.5)-(54.6,30.1) noted - exists in w0/v5_4-era fills too, not mine, left for cosmetics review.
P4 (Phase C applied -> wC): VBUS CLOSED via the trivial north vertical - in-pad anchor (44.55,7.095)->(44.28,7.095) + (44.28,7.095)->(44.28,4.829) T into the live VBUS horizontal (peg 44.99 edge margin 0.309 >= hole_clr 0.25). The ledgered tie target (45.781,9.346) was NOT needed: A9+B4 was an isolated 2-pad component and the 4.829 rail is the same VBUS component as the tie (verified). DRC 0 errors, 1 unconnected (DM).
P5 (Phase E applied -> wE): DM CLOSED - cluster->(42.561,5.906)->(43.291,5.906)via->F 45-diag y=x-37.186 (RUN-F parallel corridor 0.627)->(45.246,8.06)->(46.05,8.06) via-in-pad U4.4 (deliberate, flagged: the only DRC-clean entry; 0.2 drill @ SOT pad interior, PCBWay-acceptable class) -> B tail to pad center. kicad-cli --severity-error: **0 violations, 0 unconnected. BOARD FULLY ROUTED.** Totals since w0: ripped 15 segs+2 vias, added 29 segs+5 vias (net +14 segs, +3 vias: ENC_B seat & CC2 via relocations net-zero; DM hop +2; GND stitch +1). Nets touched: ENC_B/PORT_DP/PORT_DM/VBUS/CC2 + 1 GND stitch via; CC1/RUN/JOY untouched. Proceeding to cosmetics (dead-stub sweep, zone chamfer stretch).
P6 (cosmetics-a applied -> wF): dead-stub sweep. Engine v1 (coordinator's literal endpoint criterion) cascade-flagged 52 segs incl. the owner's +5V line and live T-trunks - REJECTED, rewrote as T-protected tip-eater cross-checked against KiCad's own w0 track_dangling census. Deleted 10 KiCad-confirmed dead stubs: CC2 old-approach spur (47.869,0.465)->(50.004,2.6); VBUS dead funnel-tie (45.781,9.346)->(48.518,9.346)->(51.264,6.6) + F1-pad spur (55.062,6.6)->(54.4,5.9); phantom old-J2-row escapes SCL/JOY_Y/+3V3x2/+1V1 (J2 now lives at (39,41)); +3V3 (38.663,16.3) west escape. Plus ENC_B east-tail trim (38.539->36.731, dead past my T). VETOED deletions: U5.3 pad-exit overshoot (11.05,41.14-41.89) = live (KiCad agrees); +3V3 twin-escape bridge ladder at (45.538-46.538,15.9/16.3) = live parallel pad-bridge. FINDING: the ledgered "known +5V B sliver near W pocket" DOES NOT EXIST on this lineage (zero +5V entries in KiCad dangling census of w0; sweep concurs) - presumed observed on an earlier discarded artifact. DRC: 0 errors, 0 unconnected, warnings 71->61 (dangling 24->14, rest baseline-class).
P7 (cosmetics-b/c -> wG): both GND zone outlines' top-left verts moved (0,14.6)->(0,13.2) and (14.6,0)->(13.2,0) (the corner v5-ledger calls SW, coordinator calls NW - same kicad top-left, Edge.Cuts verified (0,13.2)-(13.2,0), bottom-left 14.6 corner untouched/correct); refilled; fill extent at the corner improved min(x+y) 14.6 -> 13.484 = new chamfer + 0.2 edge clearance, BOTH layers - grown corner now pours. Dog-leg pass (c): SKIPPED - no exactly-collinear free merges exist on touched nets; anything else moves copper for zero functional gain ("only if free" not met). DRC wG: 0 errors, 0 unconnected, 61 warnings. Tool note: pcbnew-python aborts (SIGABRT, exit 134) at teardown on this env - harmless but stdout must be flushed/unbuffered (-u) or output is lost.
P8 (battery-1): contract_v4.json J1 adjudicated y 5.1->3.05 rot 180->0 (status + adjudications[] annotated, owner-authorized per coordinator addendum; 3.05 not the 3.16 plan value). grade_board wG --no-ring VERBATIM: DRC errors 0 / unconnected 0 / contract 45/45 refs ok / ABSENT none / outline 84.200x100.000 chamfer=ok / +5V spine 184 segs min=0.5000 0-under / USB pair clean / TP5 pour 177.0mm2 @0.00 -> RESULT: PASS (all gates green).
P9 (battery-2/3/4 -> wH): pad->net parity vs v5_4: 126/126 footprints, ONLY J1 moved (42.1,5.1,180)->(42.1,3.05,0), per-pad nets IDENTICAL. Copper diff: exactly the 8 manifest-family nets + the 5 ledgered deviations (GND +1 stitch via (34,4.2); dead-stub deletions +1V1 -1, +3V3 -3, SCL -1, JOY_Y -1 - all KiCad-dangling-confirmed) + GND zone outline verts (P7). Found+removed 1 far-copper blemish: FR grid-snap 0.01mm JOY_X bridge (67.0->67.01,22.5) inherited from wip305_it (electrically nil - via copper overlaps neighbor seg; rip verified DRC 0/0). FAR-COPPER LAW NOW EXACT: RUN 0 far diffs, JOY_X 0 far diffs. USB chain pad-net continuity J1->U4->R3/R4->DP/DM: PASS. wH = bank candidate.
P10 (battery-5): fabpack rebuilt from wH -> scratch fabpack_out_v5_5: CPL 89 (opaque) / 109 (translucent) as registered; verify_fabpack **17/17 PASS**, ratsnest 0, Edge.Cuts octagon shows 13.2 chamfer correct in gerber frame; GR-004 F-paste sparse = documented single-sided-SMD expected finding. CPL/BOM diff vs v5_4 fabpack_out: both CPLs differ in EXACTLY the J1 row (42.1,-5.1,180,bottom)->(42.1,-3.05,0,bottom); both BOMs byte-identical - prediction EXACT, no stop condition. PCBWay swap set therefore = gerbers + BOTH cpl_*.csv (BOM unchanged, same C165948), per coordinator correction #1.
P11 — **v5_5 BANKED** (2026-07-20): v5/hardware/pcb/v5_5.kicad_pcb md5 **27493b30f17de8cd568f9cdcb171f4a9** (+v5_5.kicad_pro md5 21155fc0f4eb6f798484edca0e04d403 = byte-identical to v5_4's, only-diff-was-filename-metadata verified). Banked-file DRC re-run: 0 errors / 0 unconnected. Lineage v5_4 md5 re-verified UNTOUCHED (8db3e8e...). Renders banked: v5_5_render_top/bottom.png (owner eyeball: shell slots AT the y=0 edge, pad row inboard = face out, 0.60 proud; grown 13.2 corner pours). OFFICIAL fabpack: v5/hardware/pcb/fabpack_out_v5_5/ — 17/17 PASS, ratsnest 0, gerbers_v5_5.zip; J1 CPL rows both SKUs = 42.1,-3.05,0.0,bottom (numeric twin of the render gate, per coordinator's recommended assert); BOMs byte-identical to v5_4 fabpack (same C165948). PCBWay swap set when order resumes: gerbers_v5_5 + BOTH cpl_*.csv. v5_5 = INTERNAL verified checkpoint per one-shot-v5 release plan; ORDER HOLD STANDS (owner sequence: YA13 pass -> caliper -> fabpack both SKUs -> orders). Deviations-from-brief register (all ledgered with arithmetic above): (1) coordinator's literal DM-lane/DP-hop step-2 was measured-infeasible; closed via full2-proven topologies + DP/CC2 re-dress inside the manifest family; (2) +1 GND stitch via (34,4.2); (3) 6 non-manifest dead-stub deletions (owner-ordered sweep, KiCad-dangling-confirmed); (4) "+5V W-pocket sliver" nonexistent on this lineage; (5) DM via-in-pad U4.4 (46.05,8.06) deliberate. J1 FIX COMPLETE.

## v5_6 — JS1 -> YA13 tilt-joystick footprint rev (2026-07-20, executor) — append-only phase ledger
**Base:** v5/hardware/pcb/v5_5.kicad_pcb md5 `27493b30f17de8cd568f9cdcb171f4a9` (verified at load; matches P11 bank). Working copy = v5_6_work; base NEVER mutated. Tools: kicad-cli/pcbnew 9.0.9 (the KiCad app bundle).
**§1 spec-vs-ledger reconciliation (resolved, NOT a stop):** the JS1 SOURCING RECORD line "RGB_D16 and +5V untouched" (2026-07-19, scoped on the preliminary js1_pad_swap.png BEFORE the placement froze) is SUPERSEDED by the 2026-07-20 placement-study freeze in the brief. Empirical board proof (my authority per §2): RGB_D16 F.Cu diagonal (70.42,24.411)->(58.7497,12.7407) is the 45deg line y=x-46.009; perp distance to the frozen pot-W GND hole (61.46,15.87) = |61.46-15.87-46.009|/sqrt2 = 0.419/1.41421 = **0.296mm** = a trace centerline 0.296<0.9 (pad radius) INSIDE the GND pad => hard short (RGB_D16 != GND). The reroute is physically mandatory; ledger's preliminary "untouched" was simply pre-freeze. +5V confirmed untouched (all its copper x>=47.2, far east; zero JS1-region entries).
**Datasheet check (C37323742, YA13-FL7.4-B5Ka(45-10)-R-Y06):** CIRCUIT diagram = wiper is the CENTER pin (VR1 pin2, VR2 pin2') of each 3-group -> HARD requirement MET (an end-pin wiper would be a stop; it is not). Datum: VR1 body SOUTH, VR2 body EAST; our West+North clocking = exactly 180deg-from-datum -> datum-VR1(S)->our-North, datum-VR2(E)->our-West, matches brief (pot-N=VR1=Y, pot-W=VR2=X). X/Y axis identity + 3V3-vs-GND end-pin polarity = FIRMWARE-TRIVIAL (180deg clocking inverts both axes' sense vs drawing; brief pre-flagged) -> POLARITY NOTE for firmware, NOT a stop. All wipers physically reach their assigned nets (no impossibility).
**Base geometry (empirical, pcbnew read-back of v5_5):** old JS1 = JS1_PSP_slider_4pad_handsolder @ (70.675,12.5) rot0 F.Cu, 6 SMD pads (1=+3V3,2=JOY_X,3=GND,4=+3V3,5=JOY_Y,6=GND). Net codes: +3V3=2, JOY_X=17, JOY_Y=19, GND=13. R11.pad1=JOY_X @(65.99,22.5) B.Cu; R12.pad1=JOY_Y @(69.99,22.5) B.Cu. FB1 @(63.0,15.0) B.Cu (pad1 +3V3 (62.515,15.0), pad2 ADC_AVDD (63.485,15.0)); C9 @(65.3,14.5) B.Cu (pad1 ADC_AVDD (64.82,14.5), pad2 GND (65.78,14.5)). +3V3 spine kept = F.Cu (67.175,11.9625)->(55.905,11.9625). Design rules: clr 0.152, hole_clr 0.25, h2h 0.25, edge 0.2, min_via 0.5.
**MANIFEST (everything else FROZEN):**
- FOOTPRINT: rebuild JS1 in place (ref preserved; no schematic path exists on this custom fp) as YA13 THT, pos (69.71,13.37) rot 180 (=180deg-from-datum; auth by §5 adjudication), F.Cu, attr through_hole. 10 THT pads: pins Ø1.0 drill/Ø1.8 pad {1=+3V3@(61.46,10.87),2=JOY_X@(61.46,13.37),3=GND@(61.46,15.87),4=+3V3@(67.21,5.12),5=JOY_Y@(69.71,5.12),6=GND@(72.21,5.12)}; lugs Ø1.2 drill/Ø2.0 pad GND {MP1@(64.41,7.12),MP2@(75.01,7.12),MP3@(64.41,19.62),MP4@(75.01,19.62)}. F.Fab 13x13 frame (63.21,6.87)-(76.21,19.87) + 16.7 bbox (60.41,4.07)-(77.11,20.77) [9.3 W/N, 7.4 E/S] + Ø15 stem circle @anchor r7.5; F.CrtYd bbox+0.25; F.SilkS ref clear of opening.
- RIPS (guarded count-assert per family): JOY_X {F(68.925,12.75)-(68.925,20.3636); F(70.675,11.0)-(68.925,12.75); B(68.1264,20.3636)-(68.925,20.3636); B(65.99,22.5)-(68.1264,20.3636); via(68.925,20.3636)} = 4 seg+1 via. JOY_Y {F(70.675,14.0)-(70.675,21.3284); B(69.99,22.5)-(69.99,22.0134); B(69.99,22.0134)-(70.675,21.3284); via(70.675,21.3284)} = 3 seg+1 via. +3V3 stubs {F(67.175,11.9625)-(67.175,11.0); F(67.175,14.0)-(67.175,11.9625)} = 2 seg (KEEP spine + all else). RGB_D16 {F(70.42,24.411)-(58.7497,12.7407)} = 1 seg (KEEP via (58.7497,12.7407) + (73.7032,24.411)-(70.42,24.411) + all B.Cu).
- NEW ROUTES: JOY_X wiper (61.46,13.37)->R11.pad1 (65.99,22.5); JOY_Y wiper (69.71,5.12)->R12.pad1 (69.99,22.5); +3V3 tap spine @(61.46,11.9625)->pad1 (61.46,10.87) and spine east end (67.175,11.9625)->pad4 (67.21,5.12); RGB_D16 (70.42,24.411)->dodge-S of W column->(58.7497,12.7407); GND pins/lugs via pour (+ stitches iff ratsnest>0).
- KNOWN CONFLICTS (brief; these 3 ONLY - a 4th = STOP): (1) RGB_D16 0.296mm from pot-W GND hole [CONFIRMED, rip+dodge]; (2) +3V3 B.Cu (62.515,15.0)-(60.1,15.0) 0.87 center from pot-W GND pad [hand-calc says overlaps; DRC-arbitrated]; (3) FB1.pad1 edge 0.038mm from pot-W GND pad [hand-calc <0.152; DRC-arbitrated; nudge FB1/C9 iff fails].
**PREDICTIONS (§2):** copper diff confined to JOY_X, JOY_Y, +3V3, GND (JS1-local), RGB_D16 (reroute). CONDITIONAL: IF DRC triggers the FB1/C9 nudge (brief conflict-3), consequent local copper on +3V3/ADC_AVDD/GND (FB1<->C9 AVDD filter) will differ - ADC_AVDD is not in exit-criterion-3's copper list but is the unavoidable consequence of the brief-authorized nudge; flagged here as a registered prediction + deviation-to-report, NOT a surprise. Pad->net parity: only JS1 pads' nets differ (allowed). Next: build footprint on v5_6_work -> refill -> DRC to enumerate the COMPLETE conflict set; if any conflict beyond the 3 known appears, STOP.

**PHASE footprint (applied -> v5_6_work):** JS1 rebuilt in place as YA13 THT via guarded pcbnew (assert-pre: old fpid + 6 SMD pads; assert-post reload: 10 THT pads at EXACT frozen positions/nets/drills, fpid=Joystick:YA13-FL7.4-B5Ka_C37323742, pos(69.71,13.37) rot180 F.Cu). Graphics: F.Fab 13x13 frame + 16.7 bbox(9.3 W/N,7.4 E/S) + Ø15 stem circle + pin1 dot; F.CrtYd bbox+0.25; F.SilkS ref (69.71,21.8) clear of opening. Refill 3 zones. Base v5_5 re-verified UNTOUCHED (27493b30...).

**PHASE gates-probe (DRC enumeration, kicad-cli 9.0.9 --severity-error+warning):** 4 error-severity + 4 unconnected (unconnected = the 4 not-yet-routed new pads: pad1/pad4 +3V3, pad2 JOY_X, pad5 JOY_Y - EXPECTED, pre-routing). The 4 hard conflicts (exact sweep, edge-to-edge):
  (1) KNOWN RGB_D16: F.Cu diag (70.42,24.41)->(58.75,12.74) shorts pad3 GND (-0.680) AND MP3 lug (-0.214). Resolves via manifest rip+dodge (dodge must clear both pad3 and MP3).
  (2) KNOWN +3V3-B: B.Cu (62.52,15.0)->(60.10,15.0) [FB1.1 feed] shorts pad3 GND (-0.155). Resolves via FB1/C9 nudge re-lay.
  (3) KNOWN FB1: FB1.1 +3V3 vs pad3 GND, DRC actual 0.097 < 0.152. Resolves via FB1/C9 nudge SE (brief conflict-3, check FAILED as predicted).
  (4) **NEW / 4th CONFLICT - STOP TRIGGER:** MP3 GND lug (64.41,19.62, FROZEN) shorts **JOY_X_ADC** F.Cu seg (49.50,9.30)->(67.00,22.50). Centerline 0.7396mm from lug center; required padR1.0+halfw0.076+clr0.152 = 1.228mm; **deficit 0.4884mm**. JOY_X_ADC is OUTSIDE the manifest family; the frozen lug cannot move; fix REQUIRES rerouting JOY_X_ADC (a non-manifest net) -> violates brief "these three ONLY - anything new = STOP" AND exit-criterion-3 copper-diff confinement (JOY_X_ADC not listed). All other 8 pads clear (nearest foreign >= +0.38mm) - no 5th conflict.
  Placement-study GAP: the study enumerated only the pot-W column (pad3) conflicts; it did NOT check the SE frame lug (MP3) against JOY_X_ADC, which runs a long F.Cu diagonal from the MCU to R11.pad2 via (67,22.5) straight through the frozen MP3 lug position.
**WORK HALTED at STOP trigger (per brief §Communication + protocol §6).** NOT ripped, NOT routed, NOT banked. Base v5_5 UNTOUCHED. Contract NOT yet adjudicated. Proposed minimal fix (pending coordinator authorization to touch JOY_X_ADC + expand exit-crit-3 copper list): local ~0.49mm NE bow of the JOY_X_ADC diagonal around MP3 into R11.pad2 via (67,22.5) - open F.Cu space (only neighbor RGB_D16 which is leaving via the conflict-1 reroute; ADC_AVDD neighbors are B.Cu). AWAITING coordinator ruling: (a) authorize JOY_X_ADC local dodge (+ add JOY_X_ADC to copper-diff allowlist), or (b) alternative resolution. v5_6_work = halted-WIP (footprint only; 4 DRC errors).

**COORDINATOR RULING (2026-07-20, verbatim adjudication of the STOP) — AUTHORIZED option 1 + fold-in, RESUME:**
1. JOY_X_ADC local dodge APPROVED exactly as scoped: bow the (49.50,9.30)->(67.00,22.50) F.Cu diagonal ~0.49mm NE around MP3 lug (64.41,19.62), landing on existing R11.pad2 via (67.00,22.50); restore min clearance >= pad-edge+0.152 with positive margin (PRINT achieved margin in ledger). Keep LOCAL: NO other JOY_X_ADC segment may move.
2. Exit-criterion-3 copper-diff allowlist EXPANDED to: JS1 nets (JOY_X, JOY_Y, +3V3-local, GND-local), RGB_D16 (authorized reroute), JOY_X_ADC (THIS dodge only), ADC_AVDD (FB1<->C9 local re-lay only, predicted consequence of the authorized FB1/C9 nudge). Nothing else.
3. Rationale (for record): JOY_X_ADC + ADC_AVDD are the joystick subsystem's own signal/filter copper; original allowlist drawn too literally around the study's checked set. Study's miss (SE lug vs ADC diagonal) = LESSON for the fitment stage: re-check ALL frozen holes vs ALL copper, not just the studied column.
4. All other brief terms stand: 3 known conflicts as specified, guarded rips w/ count asserts, DRC 0 + harness PASS verbatim, pad-net parity (only JS1 differs), orientation renders inspected+described, contract adjudication JS1->(69.71,13.37,rot180,F.Cu), bank v5_6 + md5, base re-verified untouched at end. Any FURTHER new conflict = STOP again, same form.
RESUMING execution from v5_6_work (footprint already built+verified).

**PHASE rips (guarded, exact-endpoint match + count-assert, all applied atomically):** 21 items = 17 trk + 4 via.
JOY_X 4trk+1via (old approach, R11.pad1 kept); JOY_Y 3trk+1via (R12.pad1 kept); +3V3 2 feed stubs (spine kept);
RGB_D16 1 diagonal (via 58.75,12.74 + rest kept); JOY_X_ADC 1 diagonal (49.5,9.3)-(67,22.5); FB1 boundary 4 (1 +3V3
feed + 3 ADC_AVDD: link x2 + south x1); dead +3V3 WEST stub chain 2trk+2via (via 60.1,15 / via 57.9,15 + F/B segs) -
orphaned once FB1 re-fed from spine, +3V3-local cleanup that clears the JOY_X west corridor. Each family assert PASS.
**PHASE FB1 nudge:** only FB1 moved (C9 did NOT need to move - no conflict). FB1 (63.0,15.0)->(64.0,15.0) [east 1.0mm];
clears conflict-3 (pad1 +3V3 now 2.23mm from pot-W GND pad) AND opens the JOY_X wiper exit. FB1 pad->net UNCHANGED.
**PHASE routes (hard-first; DRC-arbitrated over 14 iterations):**
- +3V3 to JS1: pad1 spine-tap (61.46,11.9625)->(61.46,10.87); pad4 spine-east-end (67.175,11.9625)->(67.21,5.12).
- FB1 re-lay: +3V3 fed from F.Cu spine via NEW via (63.5,11.9625)->B.Cu->pad1 (avoids threading pot-W column gap);
  ADC_AVDD link pad2(64.485,15)->C9.pad1(64.82,14.5); ADC_AVDD south re-attach pad2->(63.485,17.3658) [rest kept].
- JOY_X wiper(61.46,13.37)->R11.pad1(65.99,22.5): B.Cu thread between pad3/FB1 -> F.Cu via-hop (2 vias at 63.0,16.8 /
  63.0,18.7) over the ADC_AVDD-south B.Cu seg (inherent E-vs-W crossing; ADC is local-only so JOY_X takes the layer
  change) -> B.Cu to R11 clear of MP3.
- JOY_Y wiper(69.71,5.12)->R12.pad1(69.99,22.5): single straight B.Cu run (corridor cleared by rips).
- RGB_D16 dodge (F.Cu): (70.42,24.411)->(66.5,16.5)->(62.3,14.62)->(61.0,14.62)->via(58.75,12.74); threads pot-W column
  gap between JOY_X(13.37)/GND(15.87) pads at y14.62, clears pad3 GND, MP3 lug, and the old +3V3 vias.
- JOY_X_ADC dodge (F.Cu, coordinator-authorized, LOCAL): (49.5,9.3)->(63.0,19.512)[on original line]->(63.0,21.5)
  ->via(67,22.5). MP3 clearance restored to **edge 0.294mm (>=0.152, margin +0.142)** [ruling req: print margin]. No
  other JOY_X_ADC segment moved.
- GND: pins/lugs via pour; MP3 lug was caged (no thermal) -> stitch (64.41,19.62)->(66.5,18.5) + via(66.5,18.5)
  [connects MP3 AND bridges F<->B main pour]; + 1 stitch via(61.6,21.4) tying the JOY_X/JOY_X_ADC-caged B-island back
  to F.Cu main pour (KiCad kept-island artifact; precedent = v5_5 P3 GND-island stitch).
**PHASE gates (BANKED file v5_6.kicad_pcb):** grade_board v5_6.kicad_pcb --no-ring VERBATIM: DRC errors 0 / unconnected
0 / contract **45/45 refs ok** / ABSENT none / outline 84.200x100.000 chamfer=ok / +5V spine 184 segs min=0.5000
0-under / USB pair clean / TP5 pour 177.0mm2 @0.00 -> **RESULT: PASS (all gates green)**. kicad-cli DRC (severity-error
+warning): 0 error, 0 unconnected, 54 warnings (silk/courtyard/dangling classes = documented baseline).
Pad->net parity vs v5_5: ONLY JS1 pad->net differs (6 pot pins keep exact nets +3V3/JOY_X/GND/+3V3/JOY_Y/GND; +4 GND
lugs MP1-4 added). All other footprints' per-pad nets IDENTICAL. Positions moved: JS1 (adjudicated) + FB1 (authorized).
Copper diff nets: {+3V3, ADC_AVDD, GND, JOY_X, JOY_X_ADC, JOY_Y, RGB_D16} = EXACTLY the coordinator allowlist,
**NOTHING outside**. Renders (v5_6_render_top/bottom.png + v5_6_js1_zoom.png banked next to board): INSPECTED - 13x13
frame centered at (69.71,13.37) [inner rect on anchor crosshairs]; pot groups exiting WEST (x=61.46: +3V3/JOY_X/GND)
and NORTH (y=5.12: +3V3/JOY_Y/GND); 16.7 bbox asymmetric 9.3 W/N vs 7.4 E/S; bare NE frame region (east of N pot-box,
7.4 side) faces the board's NE chamfer; 4 GND lugs at 10.6x12.5 corners; Ø15 stem circle centered on anchor. Octagon
outline + NE chamfer + switch matrix/MCU/USB all normal.
**FIRMWARE POLARITY NOTE (not a stop; per brief):** datasheet CIRCUIT confirms wiper = CENTER pin (VR1 pin2 / VR2
pin2') - the hard requirement, MET. VR-to-position: pot-N=VR1(Y), pot-W=VR2(X), consistent with 180deg-from-datum
rotation. The 180deg clocking INVERTS both axes' direction sense vs the datasheet drawing; firmware should invert
JOY_X and/or JOY_Y readings as needed (or conceptually swap the +3V3/GND end assignment per axis). Firmware-trivial;
no netlist/board change.

## v5_6 — **BANKED** (2026-07-20, executor)
v5/hardware/pcb/v5_6.kicad_pcb md5 **221ebb98fcf44f860ed65f7ed8d1bc45** (+v5_6.kicad_pro md5 21155fc0f4eb6f798484edca0e04d403
= byte-identical to v5_5's pro, filename-only diff). Base v5_5 md5 re-verified UNTOUCHED (27493b30f17de8cd568f9cdcb171f4a9).
Contract adjudicated: contract_v4.json JS1 (70.675,12.5,rot0)->(69.71,13.37,rot180) F.Cu + status/adjudications[] annotated
(YA13 rev, placement-study freeze, RE1-mirror 1.30mm break owner-approved). Renders banked: v5_6_render_top/bottom.png +
v5_6_js1_zoom.png. Fabpack NOT rebuilt (brief: later stage owns BOM/CPL). **DEVIATIONS-FROM-BRIEF register (all authorized
+ ledgered):** (1) 4th conflict MP3-lug vs JOY_X_ADC found + coordinator-authorized JOY_X_ADC local dodge (allowlist +=
JOY_X_ADC, ADC_AVDD); (2) only FB1 moved (C9 needed no move) - within conflict-3 authorization; (3) FB1 +3V3 re-fed from
spine via a new via (cleaner than threading the column gap) -> orphaned dead +3V3 west stub removed (+3V3-local); (4) JOY_X
took 2 via-hops (F.Cu) - the wiper->R11 path inherently crosses the local-only ADC-south seg; the R11/C23/MP3 pocket is
denser than "wide open"; (5) GND stitches (MP3 stitch + 2 stitch vias) for lug connectivity + a KiCad kept-island artifact.
Net copper stays inside the coordinator allowlist. Owner sequence unchanged: v5_6 = internal checkpoint; YA13 design pass /
caliper / fabpack both SKUs / orders still downstream. ORDER HOLD STANDS. JS1->YA13 FOOTPRINT REV COMPLETE.

## v5_6 FABPACK — JS1->YA13 PLACE reclassification + rebuild both SKUs (2026-07-20, assembly-files executor) — append-only

**Base integrity:** v5/hardware/pcb/v5_6.kicad_pcb md5 `221ebb98fcf44f860ed65f7ed8d1bc45` verified at start AND re-verified UNTOUCHED at end (never mutated; source.kicad_pcb copy in the pack carries the same md5). v5_5 OFFICIAL fabpack (fabpack_out_v5_5/) NOT touched (read-only diff reference; original 01:20 bank mtimes intact). Stale fabpack_out/ (v5_4) NOT touched.

**Policy change implemented (per JS1 SOURCING RECORD 2026-07-19):** JS1 reclassified HAND_SOLDER->PLACE (machine-placed THT), BOTH SKUs.
- `hardware/pcb/BOM-FINAL.csv` JS1 row replaced (md5 ad31424f5df4e3ffba76f21f3c82d6c6 -> **9fac6d302c926c943e8180b0bfd737cf**): Value `2-axis tilt joystick`; MPN `YA13-FL7.4-B5Ka(45-10)-R-Y06`; Mfr `Shenzhen Yatelian/YTL`; LCSC `C37323742`; DigiKey/sourcing `by LCSC C#`; price 0.456/0.456/0.456 ($0.456@1); Assembly `PCBWay-THT` (pop_status default -> PLACE); Alternate_MPN col (house alternates mechanism, not placed) = `YA13S C37323748 (click variant; +tact switch, needs FP ext) / Adafruit 5628 (hand-solder, diff FP)`; Notes `tilt joystick, THT, 10 pads; replaces PSP slider`. Old Adafruit-3103/PSP-slider line fully superseded.
- `hardware/pcb/fabpack/build_fabpack.py` (md5 685d03c8... -> **1392d64b624d5b625d31f828c6830d17**): removed the dead JS1 Adafruit-3103/"METER PINOUT FIRST"/DigiKey-6193574 special-case in write_afterlist (JS1 no longer hand-solder). RE1 remains the only hand-solder afterlist entry.
- `hardware/pcb/fabpack/verify_fabpack.py` (md5 1ea85d8a... -> **dc2890171c736c60193a6df0c026420f**): (a) side check relaxed from "all rows bottom" to "each CPL row side == board footprint layer" (JS1 is F.Cu->top, all others B.Cu->bottom); (b) added targeted asserts: J1 CPL row, JS1 CPL row, JS1 BOM line/LCSC/MPN, no-3103/6193574/live-slider, JS1 6xØ1.0+4xØ1.2 drill census; (c) GR-004 triage wording de-staled (JS1 now THT, not hand-solder). Checks 17 -> **26**.

**CPL/rotation/side convention (READ from actual kicad-cli 9.0.9 pos export, not assumed):** header `Ref,Val,Package,PosX,PosY,Rot,Side`; PosY NEGATED; Side from board layer; rotation kept as-placed. J1 (B.Cu) = `42.100000,-3.050000,0.000000,bottom`. JS1 (F.Cu) = `69.710000,-13.370000,180.000000,top` (top-side because YA13 sits on F.Cu; PosY 13.37->-13.37; rot 180 preserved).

**Build:** `python3 build_fabpack.py v5_6.kicad_pcb fabpack_out_v5_6/` (same invocation pattern as v5_5). Reconcile OK: 126 footprints, 31 BOM groups. opaque CPL=90 place / BOM 29 lines (place 90, DNP 23); translucent CPL=110 place / BOM 29 lines (place 110, DNP 3); afterlist 3 entries. Bare board (both SKUs): outline octagon 84.2x100.0 centerline, 285 drill holes (PTH 237 incl 182 vias / NPTH 48), min track 0.152mm, min via drill 0.20mm, ratsnest 0.

**verify_fabpack.py VERBATIM — RESULT: 26/26 checks PASS** (sources: gerber-analyzer + Edge.Cuts RS-274X parse + pcbnew 9.0.9). All PASS incl: layer completeness 9/9; board size gbrjob & centerline; octagon 8-vert closed; drill analyzer==pcbnew (285 holes / 182 vias); CPL opaque/translucent row-count==policy(90/110) & side-matches-layer; **CPL both SKUs J1 == 42.100000,-3.050000,0.000000,bottom**; **CPL both SKUs JS1 == 69.710000,-13.370000,180.000000,top**; BOM DNP==policy(23/3); **BOM both SKUs JS1 line present LCSC C37323742 YA13 MPN**; **BOM both SKUs no Adafruit-3103/6193574/live-PSP-slider**; **JS1 drill census 6xØ1.0 + 4xØ1.2 (10 holes)**; afterlist + both zips present. Gerber-analyzer findings: 0. Ratsnest 0.

**DIFF vs v5_5 official fabpack (both SKUs):**
- CPL: `+ JS1 row` (new placement, top) **AND** `FB1 PosX 63.000000 -> 64.000000` (Y/rot/side unchanged). J1 row UNCHANGED. Nothing else differs.
- BOM: `+ JS1 line` only (byte-identical otherwise). JS1 line identical across both SKUs (PLACE in both). opaque!=translucent only on the pre-existing populate-per-variant rows (LED15-24, C40-49).
- Afterlist: `- JS1` hand-solder entry removed (4->3). Retired line carried the only Adafruit-3103/6193574 reference in the pack; now gone. RE1 hand-solder entry retained verbatim.
- Grep sweep of fabpack_out_v5_6/assembly for retired tokens: `3103`=0, `6193574`=0, `PSP-slider`=0, `Adafruit`=0. `slider`/`PSP` appear ONLY in the brief-specified JS1 Notes supersession breadcrumb "replaces PSP slider" (HISTORY reference, by design exempt from the no-live-slider assert; asserts Value/MPN cols only).

**DEVIATION — brief item-4 reconciliation (spec-vs-ledger, per EXECUTOR-PROTOCOL §1; NOT a defect):** brief item 4 stated the CPL diff v5_5->v5_6 must be "EXACTLY: + JS1 row". The actual (and predicted-from-ledger) diff ALSO contains `FB1 PosX 63.000000 -> 64.000000`. This is the coordinator-AUTHORIZED conflict-3 FB1 nudge already banked in v5_6 (ledger 2026-07-20: "FB1 (63.0,15.0)->(64.0,15.0) [east 1.0mm]" / "Positions moved: JS1 (adjudicated) + FB1 (authorized)" / coordinator ruling item 4 "positions moved: JS1 (adjudicated) + FB1 (authorized)"). Empirical footprint-position diff v5_5 vs v5_6 = EXACTLY 2 changed footprints {JS1 (fp rev), FB1 (nudge)}; 124 others byte-identical. The brief's "EXACTLY + JS1 row" is an incomplete paraphrase that omitted the FB1 nudge's CPL surfacing; the ledger (which the brief instructed me to implement exactly) documents FB1 as authorized. **Corrected expected CPL diff = {+ JS1 row, FB1 PosX 63->64}. Coordinator: please confirm this reconciliation.** No unauthorized delta exists — no STOP-class surprise.

**Deliverables (fabpack_out_v5_6/, md5):** cpl_opaque.csv d4ce1d8029b92094d96d1c31ee73c0dd; cpl_translucent.csv 4d29ef087a634f83b82f78298824d6ca; bom_opaque.csv 15003fef83789e737b9e44419dd9f1b4; bom_translucent.csv 7c11c343763c90d9125386ce483f5b54; hand_solder_afterlist.csv 18ee563b1fc47c6be2ce3707e2203c3a; gerbers_v5_6.zip 824b7a92a11975c97a2c67953b687ca1; fabpack_opaque.zip bbe7b63348c2ea2f574d957373aa5524; fabpack_translucent.zip d69228096fe83810cf50d63d9ce770ab; build_manifest.json be87132053da02c823f133eb78dae916; build_report.txt dfb5ce927f5b17dc65b45b57fcb9a835; source.kicad_pcb 221ebb98fcf44f860ed65f7ed8d1bc45 (=base); + 15 gerber/drill/map files in gerbers/.

**HOLD:** fabpack_out_v5_6 is the CANDIDATE order set. ORDER HOLD STANDS — no uploads, no orders, no payments. Release packaging is CONTINGENT on the parallel E2E fitment gate going green (do not release fabpack_out_v5_6 until fitment confirms). PCBWay swap set when order resumes = gerbers_v5_6.zip + BOTH cpl_*.csv + BOTH bom_*.csv (BOM now carries the new JS1 C37323742 line, unlike the v5_5 set).

### Coordinator confirmation (2026-07-20): fabpack_out_v5_6 CPL-diff reconciliation
The expected CPL diff vs the v5_5 set is CONFIRMED as {+ JS1 row (new, top,
rot 180), FB1 PosX 63.000->64.000} — the FB1 delta is the coordinator-
authorized conflict-3 nudge banked in v5_6; my build brief's "EXACTLY + JS1
row" was an incomplete paraphrase. verify 26/26 accepted. fabpack_out_v5_6
remains the CANDIDATE order set, contingent on E2E fitment green; ORDER HOLD
stands.

## CASE v2.5 default stick-cap flip (2026-07-20, release-packaging executor) — one line
Stick-cap default flipped **dome → taper** (coordinator ruling: taper = the only variant clearing SW4 at full 30° tilt — the owner's "won't hit a key"; dome/dish/knurl ship as alternates, dome with its >15.8°-tilt SW4 graze caveat). `khana build agentpad13_case_v2.py`: **101/101 assertions green**, SW4 advisory now **0.00 mm³ / +0.293 mm** clearance; band STL md5 36980cc2… + tray_v5 STL md5 d7d16481… both **UNCHANGED** (hard gates held). Board/fabpack UNTOUCHED. Detail: CASE-V2-NOTES §15 v2.5-flip record. ORDER HOLD STANDS.

### OWNER ADJUDICATION (2026-07-20, coordinator-recorded): JS1 silk warning removal ACKNOWLEDGED
Release-verify red-ink #2 resolved by owner ("Yeah, let it go"): the "VERIFY PINOUT BEFORE SOLDERING"
silk died with the provisional hand-solder Adafruit-3103 footprint; the YA13 is fab-placed with
datasheet-verified wiring, and the residual bring-up duties (axis inversion + ADC calibration) are
carried by POLARITY-NOTE.md, not silk. v5-release-compiled verdict: RELEASE-READY (verifier
READY-EXCEPT-2 → hygiene paths fixed by coordinator + this ack). Bundle is the order set.

### Coordinator confirmation (2026-07-20): gasket-kit MANIFEST bookkeeping
The packager's update of the RELEASE.md self-row + Stats line in MANIFEST.md
(necessitated by adding the gasket assembly note) is CONFIRMED correct — a
stale self-hash would fail the bundle's own verification gate. All frozen
artifact rows untouched; bundle re-verifies 110/110. Release folder is FINAL
pending owner audit; ORDER HOLD stands.

### DOC-CONSISTENCY FIX (2026-07-20, executor): fabpack ORDERING.md refreshed for v5_6 JS1 policy
The `ORDERING.md` bundled in the v5_6 fabpack zips predated the JS1 joystick policy change and
contradicted the (verified) CSVs. **Doc-only refresh — no board / gerber / CPL / BOM / manifest-CSV
changes.** verify_fabpack re-run 26/26 to prove nothing else drifted.

**Corrections (old → new), source `hardware/pcb/fabpack/ORDERING.md` (md5 c30f40163cac4cff96f839cea9c7ab2d → 7b99467e9cf2b51e123d5884b2ea83c0; 11544 → 12062 B):**
- Header: added "*Updated 2026-07-20 for v5_6 (JS1 = machine-placed YA13 THT top-side).*"
- §0 listing: CPL "(89 parts placed)"→"(90)", "(109)"→"(110)"; afterlist "the 2 parts YOU solder"→"the part YOU hand-solder (RE1); sockets/tacts opt-out only".
- §2a citation: "The **test-article** package reports min track 0.152 / min via 0.20 → Variant A … the final routed board will report its own numbers" → "The packaged **v5_6 routed board** reports … (its build report shows **0 unconnected**)". Makes the citation match build_report.txt's PCBWAY TIER HINT (the numbers 0.152/0.20/Variant-A/standard were already correct; only the "test-article" attribution was stale). §2 fab parameters UNTOUCHED.
- §3 assembly: "Assembly side | **Bottom only**" → "**Both sides** — bottom-side SMD reflow **plus one top-side part**: JS1"; added row "Through-hole assembly | **Yes — 1 THT part, machine-placed**: JS1 (YA13, LCSC C37323742), top-side/F.Cu; enable PCBWay mixed SMT+THT"; "(28 lines)"→"(29 lines)"; "opaque 89 / translucent 109"→"opaque 90 / translucent 110".
- §3 CPL convention: "`Side = bottom`" → "Every SMD row is `Side = bottom`; the lone exception is **JS1** … `Side = top`".
- §4 afterlist table: **deleted** the JS1/Adafruit-3103 row (DigiKey 6193574, $4.95, "METER THE PINOUT FIRST"); RE1 row retained, annotated "the only always-hand-soldered part (JS1 is now fab-placed)".
- §6 gate 1: "packaged **test article** … reports **41 unconnected**" → "packaged **v5_6** board is the final routed board; its build report shows **0 unconnected**" (matches build_report + verify_fabpack ratsnest 0).
- §6 gate 2: "Order the Adafruit 3103 early and meter its pinout" → "Joystick (JS1) is machine-placed … LCSC **C37323742** … residual first-power-on check is the axis-direction polarity note (`firmware/POLARITY-NOTE.md` in the release) — one-line firmware config flip per reversed axis".
- §6 gate 3: "bottom-side single-pass assembly" → "mixed assembly (**bottom-side SMD + top-side JS1 through-hole**)".
- §2 fab params (dims 84.2×100.0, layers, finish, mask, tier hint) LEFT UNTOUCHED — they do not contradict build_report (84.300×100.100 is bbox incl. edge stroke; 84.2×100.0 is the board outline verified by verify_fabpack centerline; ratsnest 0).

**Propagation + member-hash proof (only ORDERING.md changed inside each of the 4 zips; the other 15/15 members are content-hash byte-identical before→after):**
- Surgically replaced the ORDERING.md member in the v5 zips, then copied to v5-release-compiled (both locations byte-identical per SKU).
- fabpack_opaque.zip:  bbe7b63348c2ea2f574d957373aa5524 → **d8968f1323e562c72e5775095a0ff30a** (264163 → 264327 B)
- fabpack_translucent.zip: d69228096fe83810cf50d63d9ce770ab → **3619137fbf0391bea07ff51fd9829570** (264415 → 264579 B)
- gerbers_v5_6.zip UNTOUCHED (824b7a92a11975c97a2c67953b687ca1; confirmed no ORDERING.md member; byte-identical in both locations).

**MANIFEST.md (v5-release-compiled):** updated the two zip rows (new md5 + bytes; provenance "ORDERING.md refreshed for v5_6 JS1 policy, 2026-07-20") and the Stats bytes 20385791 → **20386119** (+328 = 2×164 B; 111 files unchanged). All other rows untouched. **Manifest self-verification 9/9 PASS** (every listed md5/bytes match on disk, no orphans, Stats == sum == on-disk).

**verify_fabpack.py against v5/hardware/pcb/fabpack_out_v5_6: RESULT 26/26 checks PASS** (pcbnew 9.0.9; ratsnest 0; JS1 top-row + 6×Ø1.0/4×Ø1.2 drill census + no-Adafruit-3103 asserts all green) — proves the doc refresh drifted nothing in the gated artifacts. ORDER HOLD STANDS.

### Coordinator confirmation (2026-07-20): ORDERING.md refresh accepted
The two edits beyond the literal JS1 items (§2a test-article attribution and
§6 gate-1's "41 unconnected" line) are CONFIRMED correct — the packaged board
is the final routed v5_6 with 0 unconnected; the old test-article framing was
stale and would have alarmed the owner's auditors. Doc now matches the gated
artifacts. Release folder FINAL: 111 manifest rows, self-verify 9/9,
verify_fabpack 26/26 re-confirmed post-fix. ORDER HOLD stands.

---

## CASE v2.6 — band sidewall 2.4 → 3.0 + USB port funnel; **band md5-invariance gate RETIRED** (2026-07-23, band-revision executor)

**Why.** PCBWay's 3D-print review of the uploaded band
(`agentpad13_v2_band_1.6mm.stl`, order prefix `C-Y15W1075301A_`) flagged the four
corner crescents (`0.737 mm` — the documented §3/§8 COSMETIC thin zone) as *"too
thin, may break"*. **Owner ruling:** thicken the sidewall — *"increase the
sidewall thickness by some amount; might even look better thicker (more visible
diffuser)"*.

**GATE RETIREMENT (owner order, record it here as well as in CASE-V2-NOTES §16).**
The band **md5-invariance gate `36980cc2ff011dc32d923fb04f7429f7` is RETIRED**.
It is no longer a pass/fail condition anywhere in this repo: `gen_gasket.py`'s
hash assert is replaced by a semantic ledge re-measurement, and the hash is now
recorded ONLY as the identity of the **SUPERSEDED 2.4-wall band**. That file
stays on disk as the historical artifact and **must NOT be printed or uploaded**.

**New canonical band (WALL 3.0, the gated build):**

| artifact | md5 |
|---|---|
| `hardware/case/v2/stl/agentpad13_v2_band_1.6mm_w3.0.stl` | **`887b2538619db46d63b07cf044762bab`** |
| `hardware/case/v2/step/agentpad13_v2_band_1.6mm_w3.0.step` | `fe952d8cd20cba00c2c2a22f820e3a2a` **as of this export** — OCCT writes a wall-clock `FILE_NAME` timestamp into every STEP header, so a STEP md5 changes on each re-export even when the geometry does not (that is also why `plate.step` / `tray_v5.step` show a 1-line git diff while `tray_v5.stl` is byte-identical). Hash the STL for invariance. |
| *(retired)* `stl/agentpad13_v2_band_1.6mm.stl` | `36980cc2ff011dc32d923fb04f7429f7` — **SUPERSEDED, do not print** |

**BOARD-SIDE IMPACT: NONE.** This is a case-only change and it touches nothing
the ORDER HOLD covers. `v5_6.kicad_pcb`, the fabpacks, the gerbers and every
board artifact are untouched (the case model only *reads* `v5_6` — its md5 guard
`221ebb98fcf44f860ed65f7ed8d1bc45` passed on every run this session). The FR4
**plate fab files are unaffected**: `INNER_R` was FROZEN at 5.6 (it used to be
`OUTER_R − WALL`) precisely so the ordered plate's R5.4 corner and the banked
tray's R5.35 corner cannot move with the wall. Proven, not asserted:

```
P1  the v2.6 source re-run at WALL=2.4 re-exports md5 36980cc2… — the retired
    band, byte for byte  (WALL is the only value that moved)
P2  vol(band_2.4 − band_3.0)            = 0.000000 mm^3  (nothing removed)
P3  vol((band_3.0 − band_2.4) & MATING) = 0.000000 mm^3  (nothing added into
    the cavity / ledge / plate recess / boss sockets / screw pass / aperture)
tray_v5.stl md5 d7d16481df24bae4c7769d7624dfc620 — byte-identical after rebuild
```

**Gates:** `khana build` → `mechanism.json status ok, assertions 101/101, the
same 8 documented interferences`; `band_crescent_wall 0.737 → 1.586`; band
printability advisory `0.642 → 1.569` (funnel-free comparison). Outer envelope
`89.6 × 105.4 → 90.8 × 106.6`.

**USB port funnel (owner directive, same day).** A parametric outer counterbore
at the port whose depth = `WALL − 2.4`, so the plug-shell bridge is a
wall-invariant **2.10 mm** at 3.0 / 5.4 / 7.4 — the wall pick is now purely
aesthetic and the "thick wall buries the USB-C plug" constraint is gone. Inner
aperture unchanged; `band × usb_recept ≥ 0.1` still green.

**STATUS: NOT FINALISED IN THE RELEASE FOLDER.** Per coordinator instruction
(2026-07-23), `v5-release-compiled/` (MANIFEST, RELEASE.md, the case STL/STEP
copies) and the PCBWay reply are **held** until the owner picks the wall from
{3.0 shipped-ready, 5.4, 7.4}. 5.4 and 7.4 are one-parameter re-runs of
`agentpad13_case_v2.py`. **ORDER HOLD stands.** No git action taken.

## CASE v2.7 — BAND DEFAULT WALL 3.0 → **5.4** (owner decision, 2026-07-24, band-default executor)

**Owner ruling (verbatim).** *"1.6 mm doesn't seem like an especially strong
corner to me"* — i.e. the v2.6 3.0-wall band's `1.586` corner. **WALL = 5.4 is
the DEFAULT band**; 3.0 and 7.4 stay **supported, gated variants**. Detail:
CASE-V2-NOTES **§18** (with the §16.4 erratum).

**PUBLIC-REPO INTENT (record only — no push taken).** *agentpad13 public repo
push upcoming; `v5-release-compiled` is the payload; default band w5.4.*

**BOARD-SIDE IMPACT: NONE.** Case-only. `v5_6.kicad_pcb`, the fabpacks, the
gerbers and every board artifact are untouched (the case model only *reads*
`v5_6`; its md5 guard `221ebb98fcf44f860ed65f7ed8d1bc45` passed on every run).
The **FR4 plate fab files are unaffected** — `INNER_R` is FROZEN at 5.6 so the
ordered plate's R5.4 and the banked tray's R5.35 cannot move with the wall.
**ORDER HOLD STANDS.** No git action taken.

**Canonical band hashes after this session:**

| artifact | md5 |
|---|---|
| **`stl/agentpad13_v2_band_1.6mm_w5.4.stl` — DEFAULT, the resin-order file** | **`34be6bf79a6bb81995807448639f4822`** |
| `stl/agentpad13_v2_band_1.6mm_w3.0.stl` (variant) | `887b2538619db46d63b07cf044762bab` — byte-identical to the v2.6 bank |
| `stl/agentpad13_v2_band_1.6mm_w7.4.stl` (variant) | `163669962a928793a4e65347a80e4cfe` |
| `step/agentpad13_v2_band_1.6mm_w5.4.step` | `964a501ca8d49762c8288ce64bdeb395` **in the release copy** (this hash moved on every re-export this session; the STL never did — MANIFEST.md is the authority for the shipped bytes) (OCCT timestamps every STEP header — hash the STL for invariance) |
| *(retired)* `stl/agentpad13_v2_band_1.6mm.stl` | `36980cc2ff011dc32d923fb04f7429f7` — **SUPERSEDED, do not print**; REMOVED from `v5-release-compiled/` this session so it cannot ride into the public repo |
| `stl/agentpad13_v2_tray_v5.stl` | `d7d16481df24bae4c7769d7624dfc620` — **UNCHANGED** |
| base of this session: `agentpad13_case_v2.py` (v2.6b) | `40eed84b1b58744836a0421758679822` (had no recorded hash; recorded per protocol §1) |
| **the v2.7 source that produced every gate + export here** | **`f2df0203aa9cd03df0ec48aa0477e049`** |

**Gates — ALL THREE WALLS gated under v2.7** (`khana build agentpad13_case_v2.py`,
variants via `AGENTPAD13_WALL=…`): each run `status ok`, **101 assertions / 101
passed / 0 failed**, **8 interferences** (the documented set, unchanged), tray
byte-identical. `band_crescent_wall` 1.586 (3.0, arc) / **4.400 (5.4, flat)** /
6.400 (7.4, flat); OUTER 90.8×106.6 / **95.6×111.4** / 99.6×115.4; funnel depth
0.60 / **3.00** / 5.00 with the shell bridge a WALL-INVARIANT **2.10** in all
three. Gasket kit re-run against the 5.4 band: PASS, `.svg`/`.png` byte-identical.

**Invariance re-proven at 5.4** (scratch `v27_prove.py`):

```
P1  the v2.7 source at WALL=2.4 re-exports 36980cc2… and at WALL=3.0 re-exports
    887b2538… — BOTH banked bands, byte for byte (the edit moved WALL and two
    PRINT-ONLY formulas; it moved no geometry)
P2  vol(band_2.4 − band_5.4) = vol(band_3.0 − band_5.4) = 0.000000 mm^3
P3  vol((band_5.4 − band_2.4) & MATING) = 0.000000 mm^3 ;
    vol(usb_funnel_5.4 & band_2.4)      = 0.000000 mm^3
P7  plate + tray solids md5-identical at WALL 2.4 / 3.0 / 5.4 / 7.4
```

**ERRATUM carried from §16.4 (reporting only, no geometry):** the v2.6 record's
`head_to_plate_edge 0.287 → 1.136` and `plate_hole_edge_web 1.537 → 2.386`
"improvements" were artifacts — both are PLATE measures computed off the band's
WALL-driven arc centre. Measured from the built solids they are **WALL-INVARIANT
at 0.287 / 1.537** at every wall. `band_crescent_wall` is likewise now
branch-correct across the arc/flat transition at WALL 4.0 (the un-branched form
would have printed 4.980 at 5.4). Neither number was ever gated.

**Release folder UPDATED (this session — the v2.6 hold is lifted by the owner's
wall pick):** `v5-release-compiled/` now carries the **w5.4 band as primary**
with w3.0 + w7.4 alongside, the v2.7 case script + CASE-V2-NOTES §18, the 5.4
`mechanism.json`, the refreshed gasket kit, the shipping-geometry renders
(`renders/v27_assembly_*.png`), a MANIFEST with a full self-verification, and a
RELEASE.md whose §(e) band line now names `agentpad13_v2_band_1.6mm_w5.4.stl`.

---

## SW14/SW15 TACT — SOURCING ERROR, PCBWay CATCH, CORRECTION + NEW GATE (2026-08-05, BOM-correction executor)

### The error (shipped)
`BOM-FINAL.csv` row `SW14 SW15` specified **XKB TS-1187A, LCSC C318884** against the
board footprint `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92` — a **C&K PTS645
6.0 × 6.0 mm / H4.3 gull-wing** land pattern. They are not the same part class:

| | footprint expects (PTS645Sx43) | TS-1187A (C318884, XKB) |
|---|---|---|
| body | 6.0 × 6.0 mm | **5.1 × 5.1 mm** |
| height | 4.3 mm | **1.5 mm** |
| lead span (pad-to-pad) | **7.96 mm** pad span | **6.5 mm** |

At a 6.5 mm lead span against a 7.96 mm pad span the leads land **~45 µm over the
pad edge — ~9 % of pad area — not solderable.**

### Detection
**PCBWay's component verification caught it**, not us. Every gate in this repo passed
that BOM: `verify_fabpack` was 26/26 green, the board/BOM reconciliation was clean, the
CPL/gerber census matched. **No gate in this project compared an MPN to its footprint.**
That is the root cause; the wrong part is the symptom. The owner has already replied to
PCBWay naming the replacement.

### The corrected part (drawing-verified by the prior sourcing agent; C-numbers re-resolved live at LCSC 2026-08-05)
- **PRIMARY:** C&K **PTS645SM43SMTR92 LFS** — LCSC **C221880**, DigiKey **CKN9112CT-ND**
  — 6.0 × 6.0 mm SMT gull-wing, H4.3, **160 gf**, SPST-NO. Land pattern matches this
  board to **0.01 mm X / 0.00 mm Y**. ~**$0.313@10**. LCSC live: `C&K
  PTS645SM43SMTR92LFS, SMD-4P 6x6mm, "Tactile Switch SPST 160gf 4.3mm Gull Wing", stock 412`.
- **ALTERNATES (identical land pattern, drop-in):** Omron **B3S-1000P** (C180420, 160 gf,
  stock 1025) / Megastar **ZX-QC66-4.3TP** (C7470150, 260 gf, stock 30120) / C&K
  **PTS645SK43SMTR92 LFS** (DigiKey CKN9084CT-ND, 260 gf — stiffer feel, deeper stock).
- **FORBIDDEN SUBSTITUTION:** C&K **PTS645SM43JSMTR92 LFS** (LCSC **C2801847**) — one
  inserted letter, **J-lead**, **DIFFERENT land pattern**. LCSC live confirms
  `"Tactile Switch SPST-NO 160gf J-Lead Surface Mount"`.
- **Cost impact:** $0.018 → $0.313 each = **+$0.59/board** for the pair
  (Ext_USD_per_board 0.035 → 0.626).

### Source fixed (not just the outputs)
`hardware/pcb/BOM-FINAL.csv` (md5 `9fac6d302c926c943e8180b0bfd737cf` →
**`df67156f983d50ec44ef6cdc04c90a00`**), row `SW14 SW15`, before → after:

| column | before | after |
|---|---|---|
| MPN | `TS-1187A` | `PTS645SM43SMTR92 LFS` |
| Manufacturer | `XKB/multi` | `C&K` |
| LCSC | `C318884` | `C221880` |
| DigiKey | `by MPN` | `CKN9112CT-ND` |
| Unit_USD_qty5 / qty10 | `0.018` / `0.018` | `0.313` / `0.313` |
| Ext_USD_per_board | `0.035` | `0.626` |
| Assembly | `PCBWay-SMD` | *(unchanged)* |
| `Alternate_MPN(LCSC)` | `K2-1114 series (verify)` | `Omron B3S-1000P (C180420) / Megastar ZX-QC66-4.3TP (C7470150; 260gf) / C&K PTS645SK43SMTR92 LFS (DK CKN9084CT-ND; 260gf stiffer)` |
| `Verified_2026-07-15` | `LIVE stock 918009 (JLC-Basic)` | `LIVE stock 412 C221880 (LCSC 2026-08-04); $0.313@10 DigiKey; land pattern drawing-verified 0.01mm X / 0.00mm Y` |
| Notes | `reachable through case holes` | `6.0x6.0mm H4.3 SMT gull-wing 160gf SPST-NO; matches FP SW_SPST_PTS645Sx43SMTR92. 2026-08-04 CORRECTION: prior TS-1187A (C318884) REJECTED by PCBWay component verification - 5.1x5.1mm body / 6.5mm lead span vs 7.96mm pad span (not solderable). DO NOT substitute PTS645SM43JSMTR92 LFS (C2801847) - J-lead, DIFFERENT land pattern. Reachable through case holes` |

Value/RefDes_Group/Qty deliberately unchanged (`BOOT/RESET tact`, 2) — they named no
wrong part. No new columns invented; the alternates use the existing house
`Alternate_MPN(LCSC)` column in the same format as the JS1 row.

### Fabpack rebuild — REGISTERED PREDICTION, then proven
Prediction before rebuild: *only* `bom_opaque.csv`, `bom_translucent.csv`,
`hand_solder_afterlist.csv` change (one row each); CPL/gerbers/drills byte-identical.

Ran the generator (`python3 hardware/pcb/fabpack/build_fabpack.py
v5/hardware/pcb/v5_6.kicad_pcb <outdir>` — same invocation as the v5_6 build) into a
**scratch outdir first**, then diffed every file against the banked pack:

```
assembly/cpl_opaque.csv        IDENTICAL (byte-for-byte)
assembly/cpl_translucent.csv   IDENTICAL (byte-for-byte)
source.kicad_pcb               IDENTICAL
assembly/bom_opaque.csv        DIFFER — exactly 1 line (the SW14,SW15 row)
assembly/bom_translucent.csv   DIFFER — exactly 1 line (the SW14,SW15 row)
assembly/hand_solder_afterlist.csv DIFFER — exactly 1 line (the SW14,SW15 opt-out row)
all 9 gerbers + 2 .drl + .gbrjob + drill-report  DIFFER in the TIMESTAMP LINES ONLY:
    %TF.CreationDate,2026-07-20T04:37:48-07:00  ->  ...2026-08-05T12:06:35-07:00
    G04 Created by KiCad (PCBNEW 9.0.9) date ...  (same substitution)
    ; DRILL file {KiCad 9.0.9} date ... / ; #@! TF.CreationDate,...
  ZERO manufacturing-content bytes differ. Full line-by-line diff run on every file.
build_manifest.json / build_report.txt DIFFER only in "generated": <timestamp>
```

**TOOL TRUTH (record it):** `kicad-cli` 9.0.9 does **NOT** honour `SOURCE_DATE_EPOCH`
— it was set to the original build's epoch and the export still stamped wall-clock.
A gerber rebuild is therefore **never** byte-reproducible in this toolchain.

**SPEC-CONFLICT RESOLUTION (protocol §6, reported not improvised):** the brief asked
both for a rebuild *into* `fabpack_out_v5_6/` **and** for gerbers/drills/CPL to stay
byte-identical. Those are mutually exclusive under the timestamp behaviour above. The
byte-identity requirement wins — the banked gerbers are the ORDER-HOLD candidate set,
their md5s are the MANIFEST contract, and the change is metadata-only by construction.
So the **generator-produced** CSVs were landed into the banked pack and the two
fabpack zips were patched **member-surgically** (same precedent as the 2026-07-20
ORDERING.md refresh): each replacement zip re-written member-by-member preserving
name/`date_time`/`compress_type`, with an assert that **all 14 non-replaced members
keep their original CRC32**. Nothing was hand-edited; no gerber, drill, drill map, CPL,
`gerbers_v5_6.zip`, `source.kicad_pcb`, `build_manifest.json` or `build_report.txt`
byte moved.

**Whole-directory md5 diff, before → after (27 files; exactly 5 moved):**

| file | before | after | bytes |
|---|---|---|---|
| `assembly/bom_opaque.csv` | `15003fef83789e737b9e44419dd9f1b4` | **`8d3e00f16b26993d37833de060228875`** | 4879 → 5221 |
| `assembly/bom_translucent.csv` | `7c11c343763c90d9125386ce483f5b54` | **`2072f15353766912a300a16694c3d84d`** | 4883 → 5225 |
| `assembly/hand_solder_afterlist.csv` | `18ee563b1fc47c6be2ce3707e2203c3a` | **`96418a5ad7bbd20474381cd1d27acd32`** | 831 → 1173 |
| `fabpack_opaque.zip` | `d8968f1323e562c72e5775095a0ff30a` | **`77b39ffaefe8bfc0c45675c7ba94632e`** | 264327 → 264724 |
| `fabpack_translucent.zip` | `3619137fbf0391bea07ff51fd9829570` | **`02b2c2c702da13173bc2bd3a20ff1e0f`** | 264579 → 264974 |
| *(22 others incl. all gerbers/drills/CPLs/`gerbers_v5_6.zip`/`source.kicad_pcb`)* | — | **UNCHANGED** | — |

The `hand_solder_afterlist.csv` duplicate of the wrong MPN (its SW14/SW15 opt-out row)
was fixed **by the generator**, not by hand — confirmed by regenerating and diffing.

### NEW GATE — `verify_fabpack.py` BOM-MPN-vs-FOOTPRINT consistency (26 → **31 checks**)
`hardware/pcb/fabpack/verify_fabpack.py` (md5 `dc2890171c736c60193a6df0c026420f` →
**`2fcdf5813d1d0caaef2b0f33855a3baa`**). `build_fabpack.py` **UNCHANGED**
(`1392d64b624d5b625d31f828c6830d17`).

1. **Targeted** (`tact_row_check` + `forbidden_cells`, one check per SKU): the
   SW14/SW15 row's footprint must be `SW_SPST_PTS645Sx43SMTR92`, its MPN must be one of
   the four approved PTS645-land parts, its LCSC must agree with that MPN, and none of
   `TS-1187A` / `C318884` / `PTS645SM43JSMTR92` / `C2801847` may appear in **any
   non-Notes cell**. (The Notes column intentionally *carries* those strings as the
   do-not-substitute breadcrumb — the same exemption the no-Adafruit-3103 check uses.)
2. **General heuristic** (`footprint_families` + `family_violations`, one check per SKU
   + the afterlist): split the footprint name on `_`; a token ≥5 chars containing both
   letters and digits and not matching the generic package/dimension vocabulary
   (`1005Metric`, `SOT-23-5`, `QFN-56-1EP`, `7x7mm`, `P0.4mm`, `H20mm`, `3225-4Pin`,
   `6028R`, …) is treated as a claimed **manufacturer part family**; its
   `^[A-Za-z]+\d+` prefix (or the whole token) must appear in the row's
   MPN + LCSC + Manufacturer, else the row FAILS. Documented exemptions only, with a
   written justification each.
3. **Afterlist** gets both treatments in one check — the stale-duplicate path.

**Empirical false-positive sweep over all 19 distinct footprints in the pack** — the
heuristic extracts exactly 5 real families and nothing else:

```
SW_SPST_PTS645Sx43SMTR92                -> PTS645          corroborated by MPN
SW_MX_HS_CPG151101S11_1u                -> CPG151101       corroborated by MPN
USB_C_Receptacle_HRO_TYPE-C-31-M-12     -> TYPE-C-31-M-12  corroborated by MPN
YA13-FL7.4-B5Ka_C37323742               -> YA13 + C37323742 corroborated by MPN + LCSC
RotaryEncoder_Alps_EC11E-Switch_..._H20mm -> EC11          corroborated by MPN PEC11R-…
LED_WS2812_4020                         -> WS2812          *** EXEMPT (documented) ***
all 13 other footprints                 -> (no family token; generic packages only)
```

The single exemption `("LED_WS2812_4020", "SK6812SIDE-A")` is justified in code: KiCad
names the generic 4020 side-emit land pattern after WS2812; BOM-FINAL already lists
`WS2812B-4020 (C965557)` as the drop-in alternate on that identical footprint.

**Regression proof — the gate fires on the OLD artifacts and is silent on the new
ones** (run against the pre-correction copies still on disk):

```
NEW  bom_opaque / bom_translucent / afterlist : tact PASS, forbidden 0, family_viol 0
OLD  bom_opaque      : tact FAIL ("MPN 'TS-1187A' is NOT an approved PTS645-land part")
                       forbidden 2 (TS-1187A col3, C318884 col5)
                       family_viol 1 ("footprint 'SW_SPST_PTS645Sx43SMTR92' claims
                                       family 'PTS645' but MPN/LCSC/Mfr =
                                       'TS-1187A XKB/MULTI C318884'")
OLD  bom_translucent : identical failures
OLD  afterlist       : tact FAIL, forbidden 1, family_viol 1
```

**verify_fabpack.py VERBATIM — RESULT: 31/31 checks PASS** (pcbnew 9.0.9;
gerber-analyzer findings 0; ratsnest 0). The 5 new lines:

```
[PASS] BOM opaque: SW14/SW15 MPN is an approved PTS645-land tact; no TS-1187A / J-lead part in any non-Notes cell   (MPN='PTS645SM43SMTR92 LFS' LCSC=C221880 vs FP='SW_SPST_PTS645Sx43SMTR92')
[PASS] BOM opaque: every footprint-embedded part family corroborated by MPN/LCSC/Mfr   (rows=29 violations=0)
[PASS] BOM translucent: SW14/SW15 MPN is an approved PTS645-land tact; no TS-1187A / J-lead part in any non-Notes cell   (MPN='PTS645SM43SMTR92 LFS' LCSC=C221880 vs FP='SW_SPST_PTS645Sx43SMTR92')
[PASS] BOM translucent: every footprint-embedded part family corroborated by MPN/LCSC/Mfr   (rows=29 violations=0)
[PASS] afterlist: SW14/SW15 opt-out row == approved PTS645-land tact; no forbidden part; footprint families corroborated   (MPN='PTS645SM43SMTR92 LFS' vs FP='SW_SPST_PTS645Sx43SMTR92' | forbidden=0 family_violations=0)
```

All 26 pre-existing checks still PASS unchanged (layer completeness 9/9; gbrjob +
Edge.Cuts centerline 84.2 × 100.0; octagon 8-vert closed; drill analyzer == pcbnew
285 holes / 182 vias; CPL 90/110 + side==layer; CPL J1 `42.1,-3.05,0,bottom` and JS1
`69.71,-13.37,180,top` both SKUs; BOM DNP 23/3; JS1 LCSC C37323742 / YA13; no
Adafruit-3103 / 6193574 / live PSP-slider; JS1 drill census 6×Ø1.0 + 4×Ø1.2; afterlist
+ both zips present).

### Release folder
`v5-release-compiled/` fabpack copies re-synced from `v5/` — all **27** files in
`hardware/pcb/fabpack_out_v5_6/` are byte-identical between the two locations.
MANIFEST.md: the 5 moved rows updated (md5 + bytes + provenance), the superseded
`verify_fabpack 26/26` provenance citation updated to `31/31` on all 22 remaining
fabpack/board rows, plus refreshed rows for the two docs this session edited
(`RELEASE.md`, `hardware/pcb/V5-NOTES.md`). Stats bytes `22133450` → **`22155730`**
(fabpack +1818 = 3×342 + 397 + 395; RELEASE.md +2993; V5-NOTES.md +17469); **117 rows
unchanged**. RELEASE.md: title dated, a `Revision 2026-08-05` block added, the
§(b)3 fabpack gate block re-run verbatim at 31/31, and a new **row H** in the A–G diff
table. HOW-TO-ORDER.md and `fabpack/ORDERING.md` contain **no** TS-1187A / C318884 /
tact-part reference — checked, nothing to fix, both left byte-identical (so the
ORDERING.md member inside the fabpack zips is untouched).

### Public repo `agentpad13` — committed, NOT pushed
`git fetch` first: HEAD == `origin/main` == `c9908ec` (nobody had moved it). Grep for
`TS-1187A` / `C318884` found **6 hits in 5 files**; all fixed:

| file | fix |
|---|---|
| `hardware/pcb/BOM.csv` | SW14/SW15 row, same field set as BOM-FINAL but in the public repo's sanitized style (`stock N` not `LIVE stock N`, no internal decision jargon) |
| `hardware/pcb/assembly/bom_opaque.csv` | copied from the regenerated fabpack (was byte-identical to ours before, is byte-identical after) |
| `hardware/pcb/assembly/bom_translucent.csv` | ditto |
| `hardware/pcb/assembly/hand_solder_afterlist.csv` | ditto |
| `hardware/pcb/agentpad13/agentpad13.kicad_sch` | SW14 + SW15 `MPN` / `LCSC` symbol properties (2 lines, 4 token substitutions) |

Also refreshed: `hardware/pcb/fabpack_{opaque,translucent}.zip` (the same surgical member
replacement). `hardware/pcb/gerbers.zip` **UNTOUCHED** (`824b7a92…`, confirmed no BOM
member). READMEs mention "tact switches" generically and carry no MPN — nothing to fix.

**Schematic edit is provably metadata-only.** `kicad-cli sch export netlist` before vs
after (normalized for the `date`/`source`/`Sheetfile` path noise) differs in **exactly
the 4 MPN/LCSC field+property values**; census identical at **89 nets / 387 nodes /
119 components**. (The `Default`→`PWR`/`USB` netclass lines in the raw diff are an
artifact of exporting the pre-image from a temp dir without its sibling `.kicad_pro`,
not a change.)

Post-fix grep: the only remaining `TS-1187A` / `C318884` strings anywhere in the repo
are inside the **Notes** column of the corrected rows, where they are the deliberate
"REJECTED — do not substitute" breadcrumb (mirrors the private side; the new verify
gate exempts the Notes column for exactly this reason). The schematic is clean.

**Commit `5ae22e64ebae0917a23b656070f8870bd1ffbaed`** ("BOM: SW14/SW15 tact was the
wrong part for its footprint (PCBWay catch)"), 7 files, +6/−6 lines + 2 binaries.
`main` is **ahead 1, NOT PUSHED** — coordinator pushes after review.

**MANIFEST self-verification: 7/9 PASS.** All 117 listed rows verify byte-exact
(md5 + size + existence), Stats == row sum == on-disk sum, MANIFEST self-excludes.
The **2 failures are PRE-EXISTING and outside this change surface**: 12 files on disk
carry no manifest row —
`hardware/PCBWay_keycaps_boxfit_2026-07-24/cap_{dish,plateau}_{1u,2u,2u_stab}{,_17p5}_boxfit.stl`
— dropped into the bundle by the in-flight keycaps session (untracked in git, gated in
`KEYCAP-NOTES §10.3`, never given MANIFEST rows). Fabricating provenance rows for
artifacts this session did not gate would be worse than reporting the gap:
**the keycaps session must add those 12 rows and bump Stats to 129 files.**

### Scope NOT touched (STOP-and-report, protocol §1/§6 — needs coordinator authorization)
The wrong MPN/LCSC also lives as **symbol properties and generator strings** on the
private side, which the brief did not authorize touching (schematic/netlist changes):
- `hardware/pcb/agentpad13/agentpad13.kicad_sch` — SW14 + SW15 `(property "MPN"
  "TS-1187A")` / `(property "LCSC" "C318884")`
- `hardware/pcb/agentpad13/gen/build_loudest.py` (the schematic **generator** — the
  true source of those strings) and `hardware/pcb/agentpad13/gen/netlist.net`
- doc-only stale references: `hardware/pcb/TOOLCHAIN.md` L130/L177,
  `hardware/pcb/DESIGN-DECISIONS.md` L129, `hardware/pcb/LAYOUT-NOTES.md` L229,
  `hardware/pcb/BOM-draft.csv` L22–23 (all v4-era; TOOLCHAIN L130 even carries the
  prophetic note *"verify PTS645 pads vs TS-1187A at bind"* — the check that was never done)

These are **metadata-only** (no symbol, pin, net or footprint change) but they are
schematic/netlist-adjacent, so they are reported rather than executed. **They matter:
the public repo's `agentpad13.kicad_sch` is a snapshot of this schematic, so a future
re-snapshot would REGRESS the public fix made this session.**

`hardware/pcb/COST-ANALYSIS.md` also moves with this change and was **not** edited (the
brief scoped it out and it is already v4-stale: it says 89 placements and counts JS1 as
hand-solder). For the record, the arithmetic: §(d) common-SMD LCSC cost/board
**$4.76 → $5.35**, ×1.7 markup **$8.10 → $9.10**; full build-up per-board TOTAL
**$81.76 → $82.76** (qty 5), **$73.06 → $74.06** (qty 10), **$67.24 → $68.24** (qty 25).

**ORDER HOLD STANDS.** Board artifacts untouched; `v5_6.kicad_pcb` still
`221ebb98fcf44f860ed65f7ed8d1bc45`.

## v5_7 — released wired board (2026-08-19; re-audited 2026-08-22)

`v5_7` is the public-release and future-spin board. It is derived from the
fabricated `v5_6` board and changes the orientation of exactly two footprints:
`LED20` and `LED21` remain at the same coordinates and on B.Cu, but rotate from
0 to 180 degrees so the bottom underglow pair fires inward. `LED15` and `LED16`
remain outward by owner choice. The orientation gate reports 8 inward and 2
outward, compared with 6 inward and 4 outward on `v5_6`.

The banked board is `v5_7.kicad_pcb`, MD5
`08cf68dae979ab28aadd5e0dda34de01`, SHA-256
`45f1b4b9632c3a42f85a4dd2350bc1ae9b9e65e33300be7a8eb36dc57b967e8a`.
Its fabpack source board is byte-identical. The 2026-08-22 release audit passed:

- board harness: DRC 0, unconnected 0, contract 45/45, outline
  84.200 x 100.000 mm, +5V minimum 0.5000 mm, USB pair clean, TP5 pour
  177.0 mm2;
- orientation: 8 inward / 2 outward;
- fabpack: 31/31 checks, 289 holes including 186 vias, 90/110 CPL rows,
  23/3 BOM DNP designators, and zero Gerber-analyzer findings;
- v5_6-to-v5_7 delta: 126/126 footprint refs unchanged, only LED20/LED21
  geometry differs, 414/414 unique pad identities retain their nets, and no
  component value, footprint ID, population attribute, or pad-net assignment
  changes;
- assembly delta: both BOMs, the opaque CPL, and the hand-solder afterlist are
  byte-identical to v5_6; the translucent CPL changes only LED20/LED21 rotation
  from 0 to 180 degrees.

`v5_6` remains the fabricated board in hand. `v5_7` is the corrected file to
order for the next wired spin.

# V5-NOTES — corrected board lineage (started fresh 2026-07-19, evening)

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
(generator: session scratchpad `gen_manifest.py` → `move_manifest.json`).

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

Verified by drawing (local copies in session scratchpad; datasheet
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
**Base:** v5/hardware/pcb/v5_5.kicad_pcb md5 `27493b30f17de8cd568f9cdcb171f4a9` (verified at load; matches P11 bank). Working copy = v5_6_work; base NEVER mutated. Tools: kicad-cli/pcbnew 9.0.9 (/Users/yuanz/Applications/KiCad.app).
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

**Invariance re-proven at 5.4** (scratchpad `v27_prove.py`):

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
- `hardware/pcb/loudest-micro/loudest-micro.kicad_sch` — SW14 + SW15 `(property "MPN"
  "TS-1187A")` / `(property "LCSC" "C318884")`
- `hardware/pcb/loudest-micro/gen/build_loudest.py` (the schematic **generator** — the
  true source of those strings) and `hardware/pcb/loudest-micro/gen/netlist.net`
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

---

## SW14/SW15 TACT — **PRIVATE-SOURCE ROOT-CAUSE CLEANUP** (2026-08-05, follow-up executor)

Follow-up to the entry above. That pass fixed every *deliverable* (BOM-FINAL, both fabpacks,
the release folder, the public `agentpad13` repo — pushed at `5ae22e6`) and then **correctly
STOPped** at the private schematic/generator, which the brief had not authorized. The owner has
now authorized it. This entry closes that gap. **No netlist/connectivity change anywhere; no git
commit in work-loudest; `agentpad13` not touched.**

### Why this pass had to happen: the fix was REGRESSIBLE

The public `agentpad13.kicad_sch` is a **snapshot** of the private
`hardware/pcb/loudest-micro/loudest-micro.kicad_sch`. Measured, pre-fix, the two files differed
in **exactly 4 hunks**: the title_block (L7), the descriptive text (L922), and the SW14 (L238) +
SW15 (L378) symbol lines. The only engineering difference between public and private was the
wrong tact part. **The next re-snapshot would have silently reverted `5ae22e6`.** Post-fix the
same diff is **2 hunks — branding only (L7, L922)** — and every `MPN`/`LCSC` property across all
119 components is byte-identical between the two repos. The public fix is now non-regressible by
construction: re-snapshotting carries the correction instead of erasing it.

### ROOT CAUSE: the generator, not the schematic

`hardware/pcb/loudest-micro/gen/build_loudest.py` **emits** the schematic. The strings
`mpn="TS-1187A", lcsc="C318884"` were hardcoded at its SW14 (L202) and SW15 (L255) `put()` calls.
The schematic was only ever the *output*. Fixing the schematic alone would have been undone by the
next `build_loudest.py` run — the same regression, from a second direction. **The generator is the
authoritative source of every MPN in this design; MPN corrections must land there first.**

Fixed at both `put()` calls, plus a 5-line comment block at the `FP.TACT` declaration (L40) binding
the land pattern to the constraint it imposes on the MPN, pointing at `TACT_APPROVED` in
`fabpack/verify_fabpack.py`. The comment deliberately still names TS-1187A — as the recorded
counter-example, not as a part choice.

### Metadata-only proof (same method as the public-schematic proof)

`kicad-cli sch export netlist --format kicadsexpr` before vs after, both exported **in place** (so
no `.kicad_pro`-sibling netclass artifact of the kind the public proof had to annotate around):

```
4c4
<     (date "2026-08-05T12:26:44-0700")          <- export timestamp only
---
>     (date "2026-08-05T12:27:13-0700")
2126,2127c2126,2127   (field    MPN/LCSC, SW14)
2133,2134c2133,2134   (property MPN/LCSC, SW14)
2146,2147c2146,2147   (field    MPN/LCSC, SW15)
2153,2154c2153,2154   (property MPN/LCSC, SW15)
```

Nothing else. The whole-file diff with those 9 lines filtered out is **byte-for-byte identical**.
Census **unchanged and identical**: **89 nets / 387 nodes / 119 components / 20 libparts / 3176
lines** before and after — the same 89/387/119 the public proof reported.

| ref | property | before | after |
|---|---|---|---|
| SW14 | `MPN` | `TS-1187A` | `PTS645SM43SMTR92 LFS` |
| SW14 | `LCSC` | `C318884` | `C221880` |
| SW15 | `MPN` | `TS-1187A` | `PTS645SM43SMTR92 LFS` |
| SW15 | `LCSC` | `C318884` | `C221880` |

`Footprint` / `Description` / `JLC` / `Value` / `Reference` / pin UUIDs / instances untouched. No
`Manufacturer` property exists on these symbols (manufacturer lives in the BOM CSVs only). Field
values match the public repo character-for-character.

### `gen/netlist.net` — CORRECTED IN PLACE (not re-exported)

The checked-in `gen/netlist.net` proved to be a faithful `kicad-cli` export: diffed against a fresh
export of the *fixed* schematic it differed in the 8 MPN/LCSC lines **plus only** its `(date
"2026-07-18T02:11:42-0700")` header. So it was corrected surgically (8 lines) rather than
regenerated, preserving the original export provenance timestamp. **Post-correction it is
byte-identical to a fresh export of the fixed schematic except that one `(date …)` line** — proof
that the in-place edit is exactly what a regeneration would have produced. Census re-measured on
the corrected file: 89 nets / 387 nodes / 119 comps / 20 libparts / 3176 lines.

### Doc staleness — 6 lines in 4 files

| file:line | change |
|---|---|
| `hardware/pcb/TOOLCHAIN.md` L130 | §5 footprint-binding table, SW14/SW15 row. Part now `C&K PTS645SM43SMTR92 LFS` / C221880. **The old "verify PTS645 pads vs TS-1187A at bind" text is PRESERVED as a quoted LESSON, not deleted** — see below. |
| `hardware/pcb/TOOLCHAIN.md` L177 | §8 bind-time verify list: `TS-1187A vs PTS645 tact` → "tact MPN vs the PTS645Sx43 land pattern (**this one bit us** — see §5 row; now PTS645SM43SMTR92 LFS / C221880)". |
| `hardware/pcb/DESIGN-DECISIONS.md` L129 | Was `` `SW_SPST_PTS645` (or match TS-1187A) ``. Now names the real bound footprint + the real part, and records that **the "or match TS-1187A" escape hatch in this very row was the defect**. |
| `hardware/pcb/LAYOUT-NOTES.md` L229 | §13 "Bind-time verifies — resolutions". Row retitled and re-adjudicated: it had been **closed prematurely** — the *footprint* was verified (2 pads vs the 2-pin symbol; 9.5 mm body drove §5.3 spacing — original wording preserved verbatim, not re-derived), the *MPN behind it* never was. Genuinely closed 2026-08-04. |
| `hardware/pcb/BOM-draft.csv` L22–23 | SW14 + SW15: MPN → `PTS645SM43SMTR92 LFS`, LCSC → `C221880`, and `Footprint_intended` `SW_SPST_PTS645  # generic tact` → `SW_SPST_PTS645Sx43SMTR92`. All three columns now equal what `bom_gen.py` would emit from the corrected schematic. |

### THE TOOLCHAIN L130 LESSON (preserved, not deleted)

TOOLCHAIN.md L130 already carried, since the v4 bind, the note:

> *"verify PTS645 pads vs TS-1187A at bind"*

**The check was written down and never executed.** The board then shipped to PCBWay carrying XKB
TS-1187A against a C&K PTS645 6.0×6.0 mm gull-wing land pattern, and **PCBWay's component
verification caught it — not us, on 2026-08-04.** Every numeric gate in this project passed that
BOM. The line is therefore kept in place, reworded to state that it was written and not run, so the
lesson survives in the document that failed to enforce it. Doctrinal form:

> **A written verify is not a performed verify.** An unexecuted check in a doc is indistinguishable
> from no check at all — worse, it *reads* as coverage. Every "verify X at bind" note needs an
> owner, a gate, or an expiry; the durable answer is the gate, which is why the previous session
> added the MPN↔FOOTPRINT tripwire (`fabpack/verify_fabpack.py`, `TACT_APPROVED` /
> `TACT_FORBIDDEN`) that now fails this class of error automatically in 3 of the 31 checks.

Same shape as the `feedback-verify-mechanical-claims` lesson: a plausible-looking part model went
unchecked against a primary drawing.

### Full-tree grep verdict — `TS-1187A` / `C318884`, 49 files

Every remaining hit is accounted for — **49 files / 144 hits, and the four classes below sum to
exactly 49 files (4 + 11 + 14 + 20)**. Nothing left unintentional.

| class | files | verdict |
|---|---|---|
| **FIXED this pass** | `loudest-micro.kicad_sch` (2→0), `gen/netlist.net` (8→0), `gen/build_loudest.py` (2→1, remaining hit is the new counter-example comment), `TOOLCHAIN.md` (2→1, the preserved lesson), `DESIGN-DECISIONS.md` (1→1, now a correction note), `LAYOUT-NOTES.md` (1→1, now a correction note), `BOM-draft.csv` (2→0) | ✅ |
| **Deliberate do-not-substitute breadcrumb** (Notes column / gate literal / ledger) | `BOM-FINAL.csv` (1, Notes), `fabpack/verify_fabpack.py` (9 — `TACT_FORBIDDEN` keys + rationale comments; **removing these disarms the tripwire**), `v5/hardware/pcb/fabpack_out_v5_6/assembly/{bom_opaque,bom_translucent,hand_solder_afterlist}.csv` (1 each, Notes), `v5-release-compiled/…/fabpack_out_v5_6/assembly/*.csv` (1 each, Notes), `v5/V5-NOTES.md` (30, including this entry) + `v5-release-compiled/hardware/pcb/V5-NOTES.md` (16), `v5-release-compiled/RELEASE.md` (5) | 🔒 RETAIN |
| **Superseded-lineage / banked builds — MUST NOT be touched** | `v5/hardware/pcb/fabpack_out/assembly/*.csv` + `fabpack_out_v5_5/assembly/*.csv` (3+3; banked builds of superseded boards), `hardware/pcb/v4/fabpack_out/assembly/*.csv` (3), `hardware/pcb/v4/analysis/schematic.json` (4, frozen analyzer output over the v4 schematic), `hardware/pcb/routing-v3/netlist.net` (8), `hardware/pcb/quilter-probe/loudest-micro.kicad_sch` + `quilter-probe/v3/…` (2+2, autorouter-probe inputs), `hardware/pcb/candidate-finish/cand1-work.kicad_sch` (2) — all untracked working artifacts frozen at their session date | ⛔ FROZEN |
| **Banked snapshot trees — MUST NOT be touched** | `v4-release-compiled/**` (10 files, 23 hits), `v5-discarded/**` (10 files, 23 hits) — each carries its own frozen copy of the schematic, generator, netlist, the three v4-era docs and the v4 fabpack BOMs; these are *supposed* to record the design as it was | ⛔ FROZEN |

The prior agent's call to leave `fabpack_out/` and `fabpack_out_v5_5/` alone is confirmed correct
and is extended to the whole superseded-lineage class above by the same reasoning: a banked build's
BOM must keep describing the parts that build was ordered with, or the bank stops being evidence.

### Gate re-run — nothing drifted

`python3 hardware/pcb/fabpack/verify_fabpack.py v5/hardware/pcb/fabpack_out_v5_6`

```
RESULT: 31/31 checks PASS
        board unconnected ratsnest (informational): 0
```

including the three tact-gate checks, verbatim:

```
  [PASS] BOM opaque: SW14/SW15 MPN is an approved PTS645-land tact; no TS-1187A / J-lead part in any non-Notes cell   (MPN='PTS645SM43SMTR92 LFS' LCSC=C221880 vs FP='SW_SPST_PTS645Sx43SMTR92')
  [PASS] BOM translucent: SW14/SW15 MPN is an approved PTS645-land tact; no TS-1187A / J-lead part in any non-Notes cell   (MPN='PTS645SM43SMTR92 LFS' LCSC=C221880 vs FP='SW_SPST_PTS645Sx43SMTR92')
  [PASS] afterlist: SW14/SW15 opt-out row == approved PTS645-land tact; no forbidden part; footprint families corroborated   (MPN='PTS645SM43SMTR92 LFS' vs FP='SW_SPST_PTS645Sx43SMTR92' | forbidden=0 family_violations=0)
```

Gerber-analyzer findings triage: 0. Edge.Cuts octagon 84.2 × 100.0, 8 vertices closed. CPL 90/110,
J1 `42.1,-3.05,0,bottom`, JS1 `69.71,-13.37,180,top`. Unchanged from the previous run.

### Deliberate non-actions

- **No fabpack rebuild.** This pass changed no fabpack input — `build_fabpack` reads the BOM CSVs
  and the board, neither of which moved. `fabpack_out_v5_6` is byte-unchanged and still 31/31.
- **`v5-release-compiled/hardware/pcb/V5-NOTES.md` deliberately NOT re-synced** with this entry.
  It carries MANIFEST md5 rows; re-syncing would mutate a release artifact and its manifest for a
  private-source cleanup that changed **zero** release artifacts. The release copy is intentionally
  one ledger entry behind; its MANIFEST remains valid.
- `hardware/pcb/BOM-draft.csv` remains v4-stale in its **other** rows (RE1/SW1–13 still carry
  `# TBD bind at layout` footprint strings from the v4-era schematic). It is a `bom_gen.py` output
  superseded by `BOM-FINAL.csv`; a full regeneration is a separate owner decision, not part of a
  part-number correction.
- `hardware/pcb/COST-ANALYSIS.md` still not edited (unchanged from the previous entry's note).
- **No git commit in work-loudest** (owner commits this repo). `agentpad13` untouched at `5ae22e6`.

**ORDER HOLD STANDS.** Board artifacts untouched; `v5_6.kicad_pcb` re-verified at the end of this
pass: **`221ebb98fcf44f860ed65f7ed8d1bc45`** — unchanged.

---

## FINAL STALENESS CLEANUP — `BOM-draft.csv` regenerated + `COST-ANALYSIS.md` re-derived (2026-08-05, staleness executor)

Owner-authorized pass over the **two v4-era artifacts that never caught up with the v5 campaign**.
No board, schematic, netlist or fabpack input was touched. No git commit (owner commits this repo).

### Task A — `hardware/pcb/BOM-draft.csv` REGENERATED

**Root cause found (differs from the brief's premise, reported per §6):** the brief described the
file as needing regeneration "from the schematic — now corrected". The schematic *was* already
correct; the defect was that **`BOM-draft.csv` had been HAND-EDITED, never regenerated**. The prior
pass patched only the SW14/SW15 rows in place (ledgered above), leaving the other 33 rows frozen at
a pre-v4 generator run. Regeneration therefore fixed far more than the two TBD families the brief
named.

**Command (verbatim, the documented invocation from `gen/README.md`):**
```
python3 hardware/pcb/loudest-micro/gen/bom_gen.py \
        hardware/pcb/loudest-micro/loudest-micro.kicad_sch \
        hardware/pcb/BOM-draft.csv
→ wrote hardware/pcb/BOM-draft.csv: 35 unique lines, 119 parts (116 populated, 3 DNP)
  unique component refdes count: 119
```
Determinism proven: generated twice (scratch + in place), byte-identical.
md5 `b7df2b222b366b1af72e00c55c8ec048` → **`e86ecb2c4c09b4f0569a6a474dac88d8`**.

**Row diff: 34 → 35 rows, 118 → 119 parts. 1 added, 0 removed, 11 changed, 23 untouched.**

| Row | What changed |
|---|---|
| **FB1** | **ADDED** — 600R@100MHz `BLM15AG601SN1D` / C76884 / `L_0402_1005Metric` (DECISION C ADC_AVDD ferrite) |
| D1 | LCSC `C907858` → `C1884584` |
| F1 | Value `500mA` → `750mA`; MPN `MF-MSMF050-2` → `MF-MSMF075/24-2`; LCSC `C17313` → `C208467`; Description (DECISION B derate) |
| J2 | DNP `` → `DNP`; Description gains "(DNP Rev A; pads stay)" |
| JS1 | FP `loudest:Joystick_PSP_Slider  # TBD Phase-1 part select` → `loudest:JS1_PSP_slider_4pad_handsolder`; MPN `Adafruit-444_or_clone` → `Adafruit 3103 (PSP-3000); fallback 444/PSP clone`; TBD flag cleared — **STILL v5-STALE, see below** |
| LED1–14 | FP `marbastlib:LED_SK6812MINI-E_ReverseMount  # TBD bind at layout` → `marbastlib-various:LED_6028R` |
| LED15–24 | FP `…LED_SK6812-SIDE_4020  # TBD bind at layout` → `marbastlib-xp-various:LED_WS2812_4020`; MPN `SK6812-SIDE-A` → `SK6812SIDE-A`; **LCSC `C_TBD_verify` → `C5378721`**; tier → `PCBWay-SMD(back)`; all flags cleared |
| RE1 | FP `…EC11E-Switch_Vertical_H20mm  # TBD bind at layout` → same FP without the TBD suffix |
| SW1–13 | FP `marbastlib-mx:SW_MX_HS_Combined_pre-mirrored  # TBD bind at layout` → `marbastlib-mx:SW_MX_HS_CPG151101S11_1u`; LCSC `C2803348` (OOS) → `C41430893`; tier → `PCBWay-SMD(back)`; all flags cleared |
| U2 | FP `SOIC-8_5.23x5.23mm_P1.27mm` → `SOIC-8_5.3x5.3mm_P1.27mm` |
| U6 | LCSC `C80757` → `C42422127` |
| Y1 | FP `Crystal_SMD_Abracon_ABM8-4Pin_3.2x2.5mm` → `Crystal_SMD_3225-4Pin_3.2x2.5mm` |

Per-field: `Footprint_intended` 7 rows · `Verify_Flags` 5 · `LCSC` 5 · `MPN` 3 · `Description` 3 ·
`JLC_Tier` 2 · `Value` 1 · `DNP` 1. **All 7 `# TBD bind at layout` strings and the `C_TBD_verify`
LCSC are now gone from the live file.**

**Independent cross-check vs board + order truth.** Every regenerated footprint was compared against
the actual bound footprint parsed out of `v5/hardware/pcb/v5_6.kicad_pcb`, and every LCSC against
`BOM-FINAL.csv`. **18 of 19 refdes groups clean.**

> ### ⚠️ RESIDUAL — JS1 is stale IN THE SCHEMATIC (reported, NOT fixed — protocol §1/§6)
> The schematic's JS1 symbol still carries the v4-era PSP slider:
> `(property "Footprint" "loudest:JS1_PSP_slider_4pad_handsolder")`,
> `(property "MPN" "Adafruit 3103 (PSP-3000); fallback 444/PSP clone")`, **no LCSC property**.
> Board + `BOM-FINAL.csv` truth is **YTL `YA13-FL7.4-B5Ka(45-10)-R-Y06`, LCSC `C37323742`**, footprint
> **`Joystick:YA13-FL7.4-B5Ka_C37323742`**, machine-placed THT.
> `bom_gen.py` can only emit what the schematic holds, so **the regenerated draft carries the stale
> JS1 row**. Closing it is a **schematic + `gen/build_loudest.py` generator edit** — metadata-only
> (no symbol, pin, net or footprint-bind change), but schematic/netlist-adjacent and **not authorized
> by this brief**. Same class as, and the direct successor to, the SW14/SW15 scope-out ledgered above.
> **The public `agentpad13.kicad_sch` is a snapshot of this schematic — a future re-snapshot would
> carry the stale JS1 part forward.** Recommend authorizing it with the tact fix's sibling edits.
> (`J2` also differs — draft LCSC `` vs BOM-FINAL `by MPN` — but that is a column-semantics
> artifact for a generic header, not a part discrepancy. Not a defect.)

**Historical snapshot preserved.** `SCHEMATIC-REVIEW.md` cites `BOM-draft.csv` as a reviewed
deliverable and quotes its state as evidence in **§5.5** (`# TBD bind at layout` placeholders),
**§7 Q4** (`C_TBD_verify`) and **§8** (the unbound-footprint table). Regeneration **destroys all
three citations** — and since the *schematic* lost its TBD strings during the v4 bind, `BOM-draft.csv`
was the **last artifact on disk still showing that state**. So, per the band/tray convention
(CASE-V2-NOTES §18.7 — superseded file stays on disk, marker lives in the governing doc):

- **`hardware/pcb/BOM-draft-v4-historical.csv`** created, **byte-identical** to the pre-regeneration
  file, md5 **`b7df2b222b366b1af72e00c55c8ec048`**. Not annotated — an unmodified snapshot is
  stronger evidence than an annotated one. **DO NOT ORDER FROM IT.**
- `SCHEMATIC-REVIEW.md` updated in 4 places, all dated 2026-08-05: the deliverable list (L9) now
  points at the snapshot and carries a ⚠️ CITATION NOTE covering the md5 change, the do-not-order
  marker, the JS1 residual and the pointer to `BOM-FINAL.csv` as order truth; §5.5 and §7 Q4 each
  gain a one-line supersession note (§7 Q4 **CLOSED** — C5378721); §8 gains a banner listing the
  **six** entries that no longer match what is bound. **The §8 table itself was left unedited as the
  historical record.**

### Task B — `hardware/pcb/COST-ANALYSIS.md` FULLY RE-DERIVED

Every number re-derived from current artifacts. **Model validated first:** all six of the document's
previous headline figures ($81.76 / $73.06 / $67.24 and $86.23 / $77.53 / $71.71) were reproduced
**exactly** from v4 inputs before any input was changed — so every delta is a real artifact change,
not a modelling difference.

**Headline (per built unit):**

| Build | q5 | q10 | q25 |
|---|---|---|---|
| Opaque | $81.76 → **$78.22** | $73.06 → **$69.51** | $67.24 → **$63.85** |
| Translucent | $86.23 → **$82.68** | $77.53 → **$73.98** | $71.71 → **$68.31** |
| Electronics-only (opaque) | $48.26 → **$44.72** | $39.56 → **$36.01** | — |

**Net −$3.55/board (q5, q10), −$3.40 (q25).** Decomposition: JS1 leaves hand-solder **−$4.950**;
JS1 enters fab-sourced parts **+$0.775**; tact correction **+$1.003**; +1 placement **+$0.140**;
smaller board **−$0.51/−$0.52/−$0.37**.

**Every headline figure that moved, with provenance:**

| Figure | Was | Now | Source |
|---|---|---|---|
| Placements opaque / translucent | 89 / 109 | **90 / 110** | `fabpack_out_v5_6/assembly/cpl_*.csv` (JS1 became machine-placed) |
| Hand-solder afterlist | RE1 + JS1 = $7.31/bd | **RE1 ONLY = $2.36/bd** | `hand_solder_afterlist.csv` — RE1 is the only `ALWAYS (not fab-placed)` row |
| JS1 | Adafruit 3103 $4.95 hand-solder | **YA13 C37323742 $0.456 machine-placed THT** | `BOM-FINAL.csv` |
| SW14/SW15 | $0.018 ea | **$0.313 ea (+$0.590/bd)** | `BOM-FINAL.csv` |
| Common SMD /bd | $4.763 → ×1.7 $8.10 | **$5.353 (+JS1 → $5.809) → ×1.7 $9.88** | `BOM-FINAL.csv` |
| Assembly /bd (opaque) | $18.86 / $15.66 / $13.74 | **$19.00 / $15.80 / $13.88** | 90 pl × $0.14 + $32 NRE |
| **Board outline / area** | 84.2 × 103.7 mm, 87.3 cm² | **84.2 × 100.0 mm octagon, 84.20 cm² bbox** (true poly 80.13) | `verify_fabpack.py` Edge.Cuts centerline |
| PCB fab /bd (HASL+matte) | $9.00 / $6.00 / $3.60 | **$8.49 / $5.48 / $3.23** | same $10 + $0.207/cm² model, new area |
| Band resin volume | never costed | **11.79 → 26.58 cm³ (×2.25, +125 %)** | CASE-V2-NOTES §18.6 (wall 2.4 → 5.4) |
| Margin under $144 | 43 / 49 / 53 % | **46 / 52 / 56 %** | |

**Two findings the brief did not anticipate — both material:**

1. 🔺 **The board is 84.2 × 100.0 mm, not 84.2 × 103.7.** The doc's "Critical size fact" (*the 103.7
   long axis exceeds the 100 mm promo cap*) **has reversed** — the long axis is now **exactly
   100.0 mm**, inside the ≤100×100 promo envelope. The owner already priced this lesson on the plate
   (*"Resize the top plates to 100mm. That 0.2 is gonna cost us 25%."* — `gen_plate_fab.py:202-204`).
   Corroborates the note already standing at `fabpack/ORDERING.md:169-172`. Caveats recorded: the
   `.gbrjob` reports **100.100** (Edge.Cuts line width) and matte-black+ENIG is a custom quote
   regardless. **The headline deliberately does NOT assume the promo** — NOT-QUOTED.
2. 🔺 **The through-hole assembly tier is now TRIGGERED.** Costing assumption 4 ("EC11 is
   hand-soldered — it avoids PCBWay's separate through-hole assembly fee tier") is **void**: JS1 is a
   machine-placed THT part (10 holes: 6 × Ø1.0 + 4 × Ø1.2, drill-census gated), so the tier is
   already paid. Whether RE1 should now *also* be machine-placed is an **open owner decision**, not a
   settled saving. Assumption 4 struck through and re-stated; NOT-QUOTED.

**New line items added (never previously costed):** printed encoder knob (2.02 / 2.06 / 2.71 cm³),
printed stick cap (**taper default 0.27 cm³**; dome 0.54 / knurl 0.52 / dish 0.68), printed 13-cap
keycap set (1U 1.069 + 2U 1.976 → **set 14.80 cm³ derived** — the repo never sums it), optional PORON
gasket kit (10 segments, ~180 mm² total). **Printed bill of volume ≈63.6 cm³/unit** (band 26.58 +
tray 19.92 + caps 14.80 + toppers 2.30) recorded for a print-service quote.
**The $12.00 purchased-keycap line was NOT removed** — no document anywhere asserts that the printed
caps supersede it, and `HOW-TO-ORDER.md` still lists purchased keycaps in its shopping list while
omitting them from its "printed at home, always" card. Flagged as an owner decision worth up to
$12/unit, not silently applied.

**Plate:** re-stated from "$3.00 FR4 fallback" to an ordered PCB with **3 finish-coupled variants**
(gold-disc default = **ENIG required**; tented-ring = **HASL-LF fine**; blank = any). Recorded the
interaction the brief flagged: **if the main board moves to HASL-LF, the gold-disc plate still forces
ENIG on the plate order** — either two finishes/two line items, or take the tented-ring plate.

### NOT-QUOTED register (9 gaps — no price was invented anywhere)

1. **Revised PCBWay resin quote, 5.4-wall band** (11.79 → 26.58 cm³). Order of record
   **`C-Y15W1075301A_`**; *the original order's price was never recorded in the repo either*. Owner's
   reply draft already warns PCBWay to expect a revision (CASE-V2-NOTES:1466-1468). **Blocking input.**
2. **THT / mixed-assembly tier for JS1** — ask for 1 THT part vs 2 (JS1+RE1) on the same quote.
3. **≤100 mm promo tier** at 84.2 × 100.0.
4. **Plate ENIG upcharge** + the two-finish question. (`HOW-TO-ORDER.md`'s plate "cost table" is
   qualitative — it contains **zero dollar figures**.)
5. **Matte-black upcharge** (+$15/order est.) — pre-existing.
6. **Printed house parts** — home-FDM filament cost never modelled; ≈63.6 cm³/unit if print-serviced.
7. **Whether printed keycaps supersede the $12.00 purchased line** — owner decision.
8. **PORON gasket kit** — no vendor/PN/price in repo.
9. **US import tariff** — volatile, excluded from headline by design.

Also labelled and NOT re-derived: the **JLCPCB comparison rows** (carried from 2026-07-15; they
predate the 90/110 counts, the THT part and the size change).

### Gate re-run — nothing drifted

`python3 hardware/pcb/fabpack/verify_fabpack.py v5/hardware/pcb/fabpack_out_v5_6`

```
RESULT: 31/31 checks PASS
        board unconnected ratsnest (informational): 0
```
Gerber-analyzer findings triage: 0. Edge.Cuts octagon 84.2 × 100.0, 8 vertices closed.
CPL 90/110; J1 `42.1,-3.05,0,bottom`; JS1 `69.71,-13.37,180,top`. Unchanged from the previous run.

### Deliberate non-actions

- **No fabpack rebuild** — this pass changed no fabpack input (docs + one generated CSV only).
  `fabpack_out_v5_6` byte-unchanged, still 31/31.
- **Schematic / `gen/build_loudest.py` / netlist NOT touched** — the JS1 residual above is reported,
  not executed (protocol §1/§6).
- **`SCHEMATIC-REVIEW.md` §8 table left unedited** — a banner was added above it; the table is the
  2026-07-15 record and rewriting it would destroy the evidence this pass exists to protect.
- **Banked/superseded lineage untouched**: `v4-release-compiled/`, `v5-discarded/`, `fabpack_out/`,
  `fabpack_out_v5_5/`, `hardware/pcb/v4/`, `routing-v3/`, `quilter-probe/`, `candidate-finish/`.
  Each still carries its own frozen `COST-ANALYSIS.md` / `BOM-draft.csv` describing what that build
  was ordered with.
- **`v5-release-compiled/` NOT re-synced** — it carries MANIFEST md5 rows and this pass changed zero
  release artifacts. Consistent with the previous entry's reasoning.
- **No git commit in work-loudest** (owner commits this repo). `agentpad13` untouched (already pushed).

**ORDER HOLD STANDS.** Board artifacts untouched; `v5_6.kicad_pcb` re-verified at the end of this
pass: **`221ebb98fcf44f860ed65f7ed8d1bc45`** — unchanged.

---

## JS1 → YA13 — **PRIVATE-SOURCE ROOT-CAUSE CLEANUP** (2026-08-05, JS1 staleness executor)

Closes the **⚠️ RESIDUAL** raised by the previous entry ("JS1 is stale IN THE SCHEMATIC — reported,
NOT fixed"). Same regression class as the SW14/SW15 tact cleanup two entries above, and its direct
successor: a deliverable-level fix (board + BOM-FINAL + fabpack, done 2026-07-19/20) that never
reached the **source** the deliverables are generated from. Owner has now authorized the source edit.
**No git commit in work-loudest; `agentpad13` NOT touched; board byte-unchanged.**

### ROOT CAUSE: the generator, not the schematic

`hardware/pcb/loudest-micro/gen/build_loudest.py` **emits** `loudest-micro.kicad_sch`. Measured this
pass and worth recording as a project invariant: **the checked-in schematic is byte-identical to a
fresh generator run modulo UUID values** (`diff` of both files with every UUID token normalised =
empty, 925 lines). The schematic has only ever been an *output*. The dead PSP-slider part was
hardcoded in three places in the generator:

| build_loudest.py | before | after |
|---|---|---|
| L36 `FP["JOY"]` | `loudest:JS1_PSP_slider_4pad_handsolder` | `Joystick:YA13-FL7.4-B5Ka_C37323742` |
| L83 `define_symbol` | `Joystick:PSP_Slider`, 6 pins (XA XW XB YA YW YB) | `Joystick:YA13_Tilt_Gimbal`, **10 pins** — the same 6 + `MP1`–`MP4` |
| L307 `put("JS1", …)` | value `PSP-Slider`, MPN `Adafruit 3103 (PSP-3000); fallback 444/PSP clone`, **lcsc `""`**, jlc `n/a(hand-solder)` | value `YA13-FL7.4-B5Ka`, MPN `YA13-FL7.4-B5Ka(45-10)-R-Y06`, LCSC `C37323742`, jlc `PCBWay-THT` |

md5 `c6b15e06931b7b91c568a0568ae879c1` → **`6313a73f9b4e4288b8893236bee17dd5`**. Each site also gained
a comment block binding the part to its evidence (rejection of the 3103 per drawing C4812-001; the
datasheet wiper=centre-pin fact; the lugs→GND fact; where the footprint actually lives). The comments
deliberately still name the PSP slider — as the recorded counter-example, not as a part choice, the
same convention the tact fix used at `FP.TACT`.

**Why the symbol, not just metadata.** The v5_6 board's JS1 footprint has **10 pads**: 6 signal
(Ø1.0) + `MP1`–`MP4` frame lugs (Ø1.2), and all four lugs carry `(net 13 "GND")`. A 6-pin symbol
against a 10-pad footprint means the next *Update PCB from Schematic* silently clears the net on four
GND pads. Declaring the lugs is what makes the schematic a faithful source for the board, so it was
done rather than deferred. Pin **names** were NOT invented: the YA13 is two 3-pin pots with the wiper
on the centre pin (pins 1-3 = VR2 = X = board West group; 4-6 = VR1 = Y = North group), which is
exactly what the slider's `XA/XW/XB` + `YA/YW/YB` names already said — only the part behind them
changed. Symbol name is deliberately lever-length-agnostic (`YA13_Tilt_Gimbal`): the J13 base is
drawing-proven identical across YA13 variants (dwg CF-G04-J13-016).

### `loudest-micro.kicad_sch` — SURGICAL SPLICE, not regenerated

Regeneration was rejected for two measured reasons: (1) `kschem.py` mints a fresh `uuid4()` for every
element, so a rerun churns all **1275** UUIDs and destroys the cheap public-vs-private diff the tact
pass established as a verification tool; (2) `build_loudest.py` also rewrites `loudest-micro.kicad_pro`.
Instead the *fixed generator's* output was transplanted onto the live file, reusing the live UUIDs for
every element that already existed (`scratchpad/splice_js1.py`, guarded assert→mutate→assert):

```
lines 925 -> 933
uuids preserved 1275, fresh 12 (4 lug pins + 4 stub wires + 4 GND power symbols), lost 0
constant-uuid identity with fresh generator output: PROVEN
```

The final assertion is the load-bearing one: **the spliced file, with every UUID replaced by a constant,
is byte-for-byte identical to a fresh run of the fixed generator.** The splice is therefore provably
*exactly* what a regeneration would have produced. md5 `afd77982f5a9755d8fc54d55ae6b8d87` →
**`fa91f15b026dc5a2069d0bbaa9042cda`**; `loudest-micro.kicad_pro` untouched (`2af4a0e6…`).

Region touched — 3 hunks, everything else frozen:

| line | change |
|---|---|
| L19 | `lib_symbols` entry: `Joystick:PSP_Slider` (6 pins, body −6.35) → `Joystick:YA13_Tilt_Gimbal` (10 pins, body −11.43) |
| L529 | placed JS1 symbol: `lib_id`, `Value`, `Footprint`, `Description`, `MPN`, **new `LCSC` property**, `JLC`, + 4 lug pin-uuid entries |
| after L541 | **+8 lines** — MP1–MP4 stub wires + their `power:GND` symbols at y 209.55 / 212.09 |
| L542–561 | R11 / R12 / C23 / C24 block shifted **+5.08 mm in y** — the generator's own cursor advance for a 10-pin vs 6-pin symbol. Cosmetic sheet layout; UUIDs, nets and labels all preserved. |

### Metadata + declared-lug proof (netlist census, before → after)

`kicad-cli sch export netlist --format kicadsexpr`, both exported **in place** (project dir, so the
`.kicad_pro` netclasses and `fp-lib-table` resolve identically on both sides):

| | before | after | verdict |
|---|---|---|---|
| nets | 89 | **89** | unchanged |
| nodes | 387 | **391** | **+4 — EXPECTED**, see below |
| components | 119 | **119** | unchanged |
| libparts | 20 | **20** | unchanged (renamed in place) |
| lines | 3176 | 3186 | +10 |

**The +4 is entirely the four GND lugs.** Full per-net membership was dumped for all 89 nets before
and after and diffed: **exactly one line differs** —

```
< GND  113  … JS1.3 JS1.6 …
> GND  117  … JS1.3 JS1.6 JS1.MP1 JS1.MP2 JS1.MP3 JS1.MP4 …
```

All **88** other nets are byte-identical. JS1's own membership: `+3V3 {1,4}`, `JOY_X {2}`,
`JOY_Y {5}`, `GND {3,6}` — **unchanged**, plus the 4 lugs joining GND, which is where the board
already has them. No net gained, lost or re-assigned a signal node; the circuit is untouched. The
whole-file netlist diff is **9 hunks and nothing outside the JS1 comp record / the `Joystick` libpart
/ the 4 GND nodes / the export timestamp**.

**ERC (`kicad-cli sch erc`, in place, both runs):** before **337 violations, 0 error-severity**;
after **342 violations, 0 error-severity**. The +5 is fully accounted for at message level:

```
+4   218 -> 222   "does not include the symbol library 'power'"      (the 4 new power:GND symbols)
+1     0 -> 1     "does not include the footprint library 'Joystick'"
```

The `lib_symbol_issues` class is the documented headless-ERC noise (protocol §4). The single new
`footprint_link_issues` warning is a **real, reported consequence**: `Joystick:` resolves to nothing on
disk — the YA13 footprint was built *inside* `v5_6.kicad_pcb` (2026-07-20 phase ledger, "rebuild JS1
in place"), there is no `Joystick.pretty` and no `fp-lib-table` entry. Matching the board exactly was
the brief's instruction and is the right call; see "Recommended follow-up" below.

### `gen/netlist.net` — CORRECTED IN PLACE (not re-exported)

Same finding as the tact pass: the checked-in `netlist.net` proved a faithful `kicad-cli` export of the
*pre-fix* schematic — diffed against a fresh export it differed **only** at its
`(date "2026-07-18T02:11:42-0700")` header (1 line, guarded assertion). It was therefore corrected
surgically (12 lines removed / 20 added — the exact netlist delta above) with the original provenance
date preserved, and **post-correction it is byte-identical to a fresh export of the fixed schematic
except that one `(date …)` line** — proof the in-place edit is exactly what a regeneration produces.
md5 `d3a695663287149337081ddf72a021c1` → **`6d5374a369741290a8d07de15286efbd`**, 3177 → 3187 lines.

### `BOM-draft.csv` — REGENERATED (1 row moved)

```
python3 hardware/pcb/loudest-micro/gen/bom_gen.py \
        hardware/pcb/loudest-micro/loudest-micro.kicad_sch \
        hardware/pcb/BOM-draft.csv
→ wrote hardware/pcb/BOM-draft.csv: 35 unique lines, 119 parts (116 populated, 3 DNP)
  unique component refdes count: 119
```
Determinism re-proven (scratch + in-place runs byte-identical). md5
`e86ecb2c4c09b4f0569a6a474dac88d8` → **`54516c66eede4b6edf68fb8cfc8e7165`**. **35 rows / 119 parts
unchanged; exactly one row differs**, JS1:

| field | before | after |
|---|---|---|
| `Value` | `PSP-Slider` | `YA13-FL7.4-B5Ka` |
| `Footprint_intended` | `loudest:JS1_PSP_slider_4pad_handsolder` | `Joystick:YA13-FL7.4-B5Ka_C37323742` |
| `MPN` | `Adafruit 3103 (PSP-3000); fallback 444/PSP clone` | `YA13-FL7.4-B5Ka(45-10)-R-Y06` |
| `LCSC` | *(empty)* | `C37323742` |
| `JLC_Tier` | `n/a(hand-solder)` | `PCBWay-THT` |
| `Verify_Flags` | `LCSC# to verify at order` | *(empty — flag legitimately cleared)* |
| `Description` | PSP-slider text incl. "pinout TBD-until-metered" | YA13 text incl. manufacturer + "6 signal pins + 4 GND frame lugs" |

Re-verified against order truth: `BOM-FINAL.csv` JS1 = `YA13-FL7.4-B5Ka(45-10)-R-Y06` / `C37323742` /
`PCBWay-THT` — **exact match on MPN, LCSC and assembly tier**; footprint is an **exact full-string
match** to the board's fpid (JS1 is in fact the only footprint on `v5_6` that carries a library prefix
at all). Re-running the previous pass's independent cross-check (every draft footprint vs the fpid
parsed out of `v5_6.kicad_pcb`, every LCSC vs `BOM-FINAL.csv`) now gives **35/35 groups clean, 0
flagged** — it was 34/35 with JS1 the sole residual.

**Manufacturer:** this schematic schema has **no `Manufacturer` property on any of its 119 symbols**
(same finding as the tact pass; `bom_gen.py` has no such column). Rather than invent a property class
for one part, the manufacturer is carried in JS1's `Description` — "2-axis tilt joystick (Shenzhen
Yatelian/YTL) …" — which `bom_gen.py` does emit. `BOM-FINAL.csv` / the fabpack BOMs remain the
manufacturer-column authority (`Shenzhen Yatelian/YTL`).

### PUBLIC-REPO CONSEQUENCE — the direction has now flipped

Measured, not assumed. `agentpad13/hardware/pcb/agentpad13/agentpad13.kicad_sch` is a byte-snapshot of
this private schematic (identical UUIDs). Against the private file:

| | hunks | what |
|---|---|---|
| public vs private **before this pass** | **2** | L7 title_block, L922 descriptive text — **branding only**, exactly the state the tact pass left |
| public vs private **after this pass** | **5** | branding (L7, L922→L930) **+ L19, L529, L542–561→542–569 = the JS1 fix** |

So **the public repo is now the one carrying the dead PSP-slider part**, in exactly 2 lines (L19 lib
symbol, L529 placed symbol) plus the 8 lug lines and the ±5.08 R11/R12/C23/C24 shift that come with
them. `agentpad13` was NOT edited (still at `5ae22e6`) — reported for the coordinator per brief §7.
Note the public repo's *order-facing* files are already correct: `hardware/pcb/BOM.csv:28`,
`assembly/bom_{opaque,translucent}.csv:13` and `assembly/cpl_*.csv` all carry the YA13 / `C37323742` /
`PCBWay-THT`. **Only the schematic snapshot is stale — the identical shape the tact defect had.**
The cheapest correct follow-up is to re-snapshot `loudest-micro.kicad_sch` → `agentpad13.kicad_sch`
re-applying only the 2 branding hunks. Also stale in public, for the same commit: `firmware/
FIRMWARE-V4-NOTES.md:307` and `firmware/loudest_micro/keyboard.json:38` (both still tell the reader to
meter an Adafruit 3103 module), and `hardware/pcb/lib/loudest.pretty/JS1_PSP_slider_4pad_handsolder.
kicad_mod` (the superseded footprint, shipped — keep as record or drop, owner call).

### NON-REGRESSIBLE FROM BOTH DIRECTIONS

- **Generator → schematic:** the next `build_loudest.py` run now emits the YA13. (Before this pass it
  would have re-written the PSP slider back over any schematic-only fix.)
- **Schematic → public:** the next re-snapshot now *carries* the correction instead of erasing it.
- **Schematic → board:** the 4 GND lugs are declared, so an Update-PCB-from-Schematic can no longer
  strip the frame lugs' net.
- **Deliverables → order:** `verify_fabpack.py` already gates this class — `BOM {sku}: no
  Adafruit-3103 / live PSP-slider reference` and `BOM {sku}: JS1 line present, LCSC C37323742, YA13
  MPN` and `JS1 drill census: 6x Ø1.0 + 4x Ø1.2` (5 of the 31 checks). Those literals are the
  tripwire; **removing them disarms it.**

### Full-tree grep verdict — `3103` / `PSP_slider` / `6193574`

Counted with `(?<![\d.])3103(?![\d])` (a bare `\b3103\b` false-positives on PCB coordinates like
`27.3103` / `12.3103` — inflating the raw sweep by ~35 hits). **280 files / 961 hits total.**

| class | files | hits | verdict |
|---|---|---|---|
| **FIXED this pass — now 0 hits** | `loudest-micro.kicad_sch` (**3→0**), `gen/netlist.net` (**7→0**), `BOM-draft.csv` (**2→0**) | 0 | ✅ |
| **FIXED, hit retained as counter-example** | `gen/build_loudest.py` (**4→2** — both remaining hits are on the one new "this REPLACED …" comment line), `SCHEMATIC-REVIEW.md` (**1→3** — the residual note struck through and annotated, not deleted) | 5 | ✅ |
| **Deliberate do-not-substitute breadcrumb** — removing these disarms a gate or destroys a lesson | `fabpack/verify_fabpack.py` (10 — `no_3103` / `no_live_slider` literals + rationale), `fabpack/build_fabpack.py` (1 — the "RECORD 2026-07-19" comment), `COST-ANALYSIS.md` (3 — the supersession rows, already correct), `v5/V5-NOTES.md` (27, incl. this entry), `BOM-draft-v4-historical.csv` (1 — the frozen pre-regen snapshot), `lib/loudest.pretty/JS1_PSP_slider_4pad_handsolder.kicad_mod` (5 — the superseded footprint, kept as the record of what was replaced) | 47 | 🔒 RETAIN |
| **LIVE DOC STALENESS — reported, NOT fixed (brief §6 is report-only)** | `docs/HANDOFF-STATE.md:19` ("order Adafruit 3103 + meter pinout BEFORE soldering JS1" — **an actionable owner instruction that is now wrong**), `firmware/FIRMWARE-V4-NOTES.md:307`, `firmware/loudest_micro/keyboard.json:38`, `hardware/pcb/DESIGN-DECISIONS.md` (9 — Decision A "Locked: Adafruit 3103", reversed 2026-07-19), `hardware/pcb/LAYOUT-NOTES.md` (5 — §3 custom-footprint record + §13 "meter the 3103 before soldering"), `docs/open-agent-macropad-spec.md` (4), `docs/research-synthesis-and-review.md` (2), `docs/independent-design/phase0-layout-v2-notes.md` (2), `docs/phase1-breadboard.md` (1), `docs/PREORDER-REVIEW-2026-07-19.md` (1), `hardware/case/{CASE-NOTES.md, agentpad13_case.py, layout_v2.py}` (3, case v1 — superseded by case v2), `hardware/case/v2/CASE-V2-NOTES.md:487` (1, historical context; **file is live-edited by the owner right now — do not touch**), `hardware/pcb/loudest-micro/loudest-micro.kicad_pcb` (4 — the v4-era project board, superseded by `v5_6`) | 36 | ⚠️ REPORT |
| **Superseded lineage — MUST NOT be touched** | `v5/hardware/pcb/v5{,_2,_3,_4,_5}*.kicad_pcb`, `fabpack_out/`, `fabpack_out_v5_5/`, `hardware/pcb/{v4,routing-v3,quilter-probe,candidate-finish,cleanroom}/**` | 179 files / 608 | ⛔ FROZEN |
| **Banked snapshot trees** | `v4-release-compiled/**`, `v5-discarded/**` | 74 files / 238 | ⛔ FROZEN |
| **Release artifact** | `v5-release-compiled/**` (3 files / 27) — deliberately NOT re-synced, same reasoning as the tact entry: it carries MANIFEST md5 rows and this pass changed **zero** release artifacts | 3 files / 27 | ⛔ FROZEN |

One live-tree hit is pure noise and is not counted as a finding:
`lib/marbastlib/.../PDFN3.3x3.3_EP.kicad_mod` — the string `3103` inside a UUID (`e5c3103f-…`).

### Gate re-run — nothing drifted

`python3 hardware/pcb/fabpack/verify_fabpack.py v5/hardware/pcb/fabpack_out_v5_6`

```
RESULT: 31/31 checks PASS
        board unconnected ratsnest (informational): 0
```
including, verbatim, the five JS1-relevant checks:
```
  [PASS] CPL opaque: JS1 row present == 69.710000,-13.370000,180.000000,top   (got=69.710000,-13.370000,180.000000,top)
  [PASS] BOM opaque: JS1 line present, LCSC C37323742, YA13 MPN   (matches=1 C37323742/YA13-FL7.4-B5Ka(45-10)-R-Y06)
  [PASS] BOM opaque: no Adafruit-3103 / live PSP-slider reference   (3103/6193574_free=True no_live_slider=True)
  [PASS] BOM translucent: no Adafruit-3103 / live PSP-slider reference   (3103/6193574_free=True no_live_slider=True)
  [PASS] JS1 drill census: 6x Ø1.0 + 4x Ø1.2 THT holes   (tally={1.0: 6, 1.2: 4})
```
Gerber-analyzer findings triage: 0. Edge.Cuts octagon 84.2 × 100.0, 8 vertices closed. CPL 90/110,
J1 `42.1,-3.05,0,bottom`, JS1 `69.71,-13.37,180,top`. Unchanged from the previous run.

### Recommended follow-up (NOT done — new deliverable, outside this brief)

**Export the YA13 footprint out of `v5_6.kicad_pcb` into `hardware/pcb/lib/Joystick.pretty/
YA13-FL7.4-B5Ka_C37323742.kicad_mod` and add a `Joystick` row to
`hardware/pcb/loudest-micro/fp-lib-table`.** That is what clears the one new ERC warning
("does not include the footprint library 'Joystick'") and completes the schematic→board link; today
the footprint exists *only* inside the board file, which is why `JS1_PSP_slider_4pad_handsolder`
resolves and its replacement does not. Deliberately not improvised here per EXECUTOR-PROTOCOL §6 (new
files + a lib-table edit are not in the brief). No electrical consequence: the board already carries
the footprint, so nothing about the fab pack or the order depends on it.

### Deliberate non-actions

- **No fabpack rebuild.** This pass changed no fabpack input — `build_fabpack` reads the BOM CSVs and
  the board, neither of which moved. `fabpack_out_v5_6` byte-unchanged (mtimes still 2026-08-05 12:06/
  12:08 from the tact pass) and still 31/31.
- **`hardware/pcb/BOM-FINAL.csv` untouched** — it was already correct (`ad31424f…` → `9fac6d30…`
  happened on 2026-07-19); this pass only had to make the *generated* draft agree with it.
- **`BOM-draft-v4-historical.csv` untouched** (md5 `b7df2b222b366b1af72e00c55c8ec048`) — it is the
  frozen pre-v5 snapshot and is *supposed* to show the PSP slider.
- **Docs beyond `SCHEMATIC-REVIEW.md` not edited** — brief §6 asked for a report, not a sweep. The one
  doc edited is the one this pass falsified: `SCHEMATIC-REVIEW.md`'s ⚠️ CITATION NOTE said "one
  residual mismatch, reported not fixed"; the residual paragraph is **struck through and preserved**
  (not deleted) with a CLOSED 2026-08-05 note carrying the census numbers. md5 `66279ebf…` →
  `4235142a83c77d65d4e99921e1ee9d5d`.
- **`docs/HANDOFF-STATE.md:19` flagged loudly, not edited** — it still tells the owner to *order an
  Adafruit 3103*. Of everything in the ⚠️ REPORT class this is the one that can still cost money.
- **Banked/superseded lineage untouched**: `v4-release-compiled/`, `v5-discarded/`,
  `v5-release-compiled/`, `fabpack_out/`, `fabpack_out_v5_5/`, `hardware/pcb/v4/`, `routing-v3/`,
  `quilter-probe/`, `candidate-finish/`, `cleanroom/`.
- **No git commit in work-loudest** (owner commits this repo). `agentpad13` untouched at `5ae22e6`.

**ORDER HOLD STANDS.** Board artifacts untouched; `v5_6.kicad_pcb` re-verified at the end of this
pass: **`221ebb98fcf44f860ed65f7ed8d1bc45`** — unchanged.

---

## JS1 CLOSEOUT — live-doc staleness swept, footprint library created, public mirror re-synced (2026-08-05, closeout executor)

**Owner-authorized.** Three tasks, all doc/library-level. **Zero board mutation** — `v5_6.kicad_pcb`
md5 `221ebb98fcf44f860ed65f7ed8d1bc45` asserted at load, after the footprint export, and at the end of
the pass: **unchanged** every time. No fabpack rebuild (no fabpack input moved). No git commit in
work-loudest.

### Task 1 — the ⚠️ REPORT class from the previous entry, now FIXED

The previous pass enumerated live-doc staleness and deliberately did not touch it (its brief was
report-only). This pass corrects it. **House convention held throughout: annotate reversals as
lessons; strike, do not delete.** Every falsified claim is preserved struck-through with a dated
🔻 box giving current truth *and the reason the old decision was wrong*.

| File:line | Before | After |
|---|---|---|
| **`docs/HANDOFF-STATE.md:19`** — *the money hit* | "Owner physical gates: **order Adafruit 3103 + meter pinout BEFORE soldering JS1**; print coupons; …" | struck + 🔻 **REVERSED 2026-07-19 — do NOT buy a joystick and do NOT meter one.** YA13 / C37323742 / $0.456 / machine-placed THT / off the afterlist; reason-for-reversal sentence; residual = axis polarity only. Remaining owner gates (coupons, 1:1 print, DFM) kept. |
| `firmware/FIRMWARE-V4-NOTES.md:307` | "…ADC sweep on the real **Adafruit 3103 module (which itself must be pinout-metered before soldering, per the hardware hand-solder afterlist)**" | struck + 🔻 **CORRECTED 2026-07-19**: YA13, machine-placed THT, **nothing to meter, nothing to hand-solder**; ADC sweep still needed on the assembled board; axis-polarity residual named. |
| `firmware/loudest_micro/keyboard.json:38` (`$joystick_comment`) | "…sweep on the **Adafruit 3103 module (meter its pinout before soldering; see the hand-solder afterlist)**" | "…sweep on the **assembled board**. JS1 = YTL YA13… machine-placed THT… nothing to meter, nothing to hand-solder (CORRECTED 2026-07-19; this line used to say …)" + POLARITY-NOTE pointer. **JSON re-parsed; the functional `joystick` block is byte-unchanged.** |
| `firmware/loudest_micro/config.h:6` — **not in the previous grep** (its pattern was `PSP_slider`; this line reads `PSP-slider`) | `// --- Joystick (analog PSP-slider on ADC, planar) ---` | `// --- Joystick (analog 2-axis tilt gimbal on ADC) ---` + 4 comment lines: part/LCSC/THT, "used to read …", *electrically identical from firmware's side*, polarity pointer. **Comment-only; no code touched.** |
| `hardware/pcb/DESIGN-DECISIONS.md` §2 **Decision A** | "**Locked: Adafruit 3103 … hand-soldered to a custom 4-pad landing pattern.**" | struck; a 🔻 **DECISION A WAS REVERSED 2026-07-19** box added above it with current truth, a 4-row was/now table (price, assembly, footprint, metering gate) and the **lesson**: *Decision A's premise "no PSP-slider is pick-and-place" was true of the part **class** and false of the **requirement** — the requirement was never "a PSP slider", it was "a 2-axis analog joystick the fab can place". The error was accepting a part class as a constraint and never re-asking whether the class was required.* The three "hunt" paragraphs are left intact as the record. |
| …§2 **Residual risk** para | "…unverified until a physical 3103 is on the bench and metered…" | left intact + 🔻 **RESIDUAL RISK RETIRED 2026-07-19** note: no metering gate, no sample to buy; records that the *hedge* (GP26/27 kept swappable) is exactly why the surviving item is a one-line config flip and not a respin. |
| …§4 disposition 3 | "**Resolved (Decision A)** — Adafruit 3103 locked, custom 4-pad footprint, ~20×20 keep-out …; pinout TBD-until-metered." | struck + 🔻 **RE-RESOLVED 2026-07-19**: YA13, `Joystick:YA13-FL7.4-B5Ka_C37323742`, THT 6×Ø1.0 + 4×Ø1.2, no flex channel, **no metering gate**; case keep-out now derives from the v2 model against `v5_6`. |
| …§5 sourcing table, Joystick row | "Adafruit 3103 (DigiKey 6193574)" / "Decision A: 444 OOS, 3103 in stock" | struck → **YTL YA13… C37323742, $0.456, machine-placed THT** / "**Decision A REVERSED 2026-07-19** … −$4.494/board, no metering gate". |
| …§6 binding table, JS1 row | "Adafruit 3103 \| **CUSTOM** 4-pad hand-solder pattern \| …flex-cable exit channel; **pinout TBD-until-metered**; keep GP26/27 swappable" | struck → YA13 / `Joystick:YA13-FL7.4-B5Ka_C37323742` **BOUND**; flex channel + metering struck; **"keep GP26/27 swappable" explicitly marked as still standing** (it is the reason the polarity fix is one line). |
| `hardware/pcb/LAYOUT-NOTES.md` §1 binding table | "JS1 \| `loudest:JS1_PSP_slider_4pad_handsolder` \| custom, authored this wave" | struck → `Joystick:YA13-…`; annotated that the old fpid **is still the binding on this Wave-2 board file** but **not** on the live board `v5/hardware/pcb/v5_6.kicad_pcb`. |
| …§3 (the custom-footprint section) | whole section describes the provisional hand-solder landing | 🔻 **§3 IS SUPERSEDED** box added: current fpid + 10-pad geometry + export/registration; names the **three things now false of the product** — (a) not hand-installed, (b) no TBD-until-metered gate, (c) the **"VERIFY PINOUT BEFORE SOLDERING" silk is gone** (owner-adjudicated 2026-07-20, "Yeah, let it go"). Section text untouched below the box. |
| …§15 "Wave 3 must verify" item 3 | "**JS1 pinout** metered against a physical Adafruit 3103 before soldering (footprint is provisional)." | struck + 🔻 **RETIRED 2026-07-19 — do not buy a joystick and do not meter one.** |
| `docs/open-agent-macropad-spec.md` §3.3 | "**Decision (v0.2): 2-axis planar micro-slider, PSP-slider class — Adafruit 444 … or Adafruit 3103 …**" | struck + 🔻 **§3.3 SUPERSEDED — DO NOT BUY ANY PART FROM THIS SECTION** box: as-built part, and an explicit **honest divergence** paragraph — *the YA13 is a tilt gimbal, not a planar slider; §1's teardown row still correctly describes the Creator Micro 2 and Rev A deliberately does not match it there. Electrically identical (dual B pot → ADC), so every firmware statement carries over; what is traded is feel. Note this section's own "Rejected alternatives" line rejected tilting thumbsticks as "too tall and wrong feel" — the YA13 is the counter-example that reopened and won that question.* |
| …§3.3 buy paragraph | "For Rev A, **buy 2× Adafruit 444 + 2× 3103** … and 10× AliExpress PSP-slider equivalents; qualify at Phase 1…" | struck + 🔻 **BUY NOTHING FROM THIS PARAGRAPH (2026-07-19)**; the "Phase-0 keep-out must be re-derived" sentence kept and marked **done** (case v2 derives it from the YA13 on `v5_6`). |
| …§7 shopping table, joystick row | "2-axis planar joystick (PSP-slider class …) \| 1 \| Adafruit/Mouser + AliExpress \| ~$3–6" | struck → "2-axis tilt joystick, YTL YA13… — **machine-placed by the fab, NOT bought separately**" \| LCSC C37323742 via PCBWay turnkey \| 🔻 **$0.456**. |
| `docs/phase1-breadboard.md` shopping list, 3 joystick rows (444 ×2 / 3103 ×2 / Ali clones ×10) | live buy rows totalling ~$18 | all three struck, qty → **0**, cost → **$0**, each marked 🔻 **DO NOT BUY (2026-07-19)**; total line "≈$25–35" annotated → **≈$12–17 without them**; a 🔻 box explains the Phase-1 joystick qualification **never ran and is moot** and notes the other three de-risk items are unaffected. |
| …test plan item 1 | "**Joystick (C1 follow-up):** wire each candidate's X/Y pots … pick the Rev-A part; caliper its body/pad geometry" | struck + 🔻 **RETIRED 2026-07-19**; what survives moves to first-power-on on the real board (the ADC sweep that replaces the placeholder `0/512/1023`, plus the axis-direction check). |
| `docs/PREORDER-REVIEW-2026-07-19.md` **Blocker 2** | "**Action: caliper the actual joystick module** … before releasing the band print" | ✅ **BLOCKER 2 CLOSED 2026-07-19** box added: *this blocker is the reason JS1 changed.* Records that its finding ("unverifiable without the real part") was **correct**, and that the cheaper fix than buying a part to caliper was **buying a part that comes with a drawing**. Caliper action explicitly retired. Finding text preserved. |
| `hardware/pcb/SCHEMATIC-REVIEW.md` §7 open question 3 | "**Joystick JS1 is unselected (Phase-1 gate)** … re-derived from the finally-selected part (Adafruit 444 / 3103 / clone)." | added a *2026-07-19: **CLOSED*** sub-note in the same style the previous pass used for question 4 (it had closed 4 and missed 3). Notes the generic 2-pot 6-pin model was right and carried over; the symbol only gained MP1–MP4. |

**md5 before → after (11 files):**

| file | before | after |
|---|---|---|
| `docs/HANDOFF-STATE.md` | `3233025c808c46eaed0ffb226c0aa29f` | **`09bfbccf2cc030a29616cf3106922aaa`** |
| `docs/PREORDER-REVIEW-2026-07-19.md` | `05e5936f2be27271f6d8e9127d553a4b` | **`9f0b0416ec922e5e06099265f111a6cf`** |
| `docs/open-agent-macropad-spec.md` | `8ebc939a5bdf29d2cef949f33adccc53` | **`e2fcc17add23fa4cad6b1267c5f5f806`** |
| `docs/phase1-breadboard.md` | `99a13bbdab9d92100173209d22a1eed2` | **`321288a6d17a46549715c5c437068692`** |
| `firmware/FIRMWARE-V4-NOTES.md` | `af7fcb90bea6d863bcc5c0f34e59c939` | **`f54efe9ff43ae3c460c921e638c41da0`** |
| `firmware/loudest_micro/keyboard.json` | `22454b24601d4821c48bc2ae74bb6643` | **`9370e82dfc0af6a9e7278e1cc63cfafd`** |
| `firmware/loudest_micro/config.h` | `e203115ced69229b1520b424d83f4e6b` | **`304857e366a9d4e79ecbc7d793d55d3f`** |
| `hardware/pcb/DESIGN-DECISIONS.md` | `9f02619a5b04223b8f82e61c0dd98a9c` | **`322ad417cff59609b88195615f83fc7e`** |
| `hardware/pcb/LAYOUT-NOTES.md` | `5082b7a42ed4b5a2c3e273b6fe3bd147` | **`cd4829b5e5956adbbe35e2b1eb189886`** |
| `hardware/pcb/SCHEMATIC-REVIEW.md` | `4235142a83c77d65d4e99921e1ee9d5d` *(the previous pass's output, not HEAD)* | **`2b8291b5931c0c0abef641852c4c6b27`** |
| `hardware/pcb/loudest-micro/fp-lib-table` | `b24a1ecfdd006fda337d24308ea8c8ea` | **`bf1ac5691ae7538a0570dc3bde66fb53`** |

### Task 1 judgments — what was deliberately LEFT, and why

Brief asked for a live-vs-historical judgment on the case-v1 files and gave latitude on the rest.
**Left unedited, reported as HISTORICAL** (each is a dated record of a decision, not an instruction a
reader would act on; the money-facing instructions they descend from are all corrected above):

- `docs/research-synthesis-and-review.md` (2) — dated **2026-07-15** blind review *of the founding
  spec*. Its recommendation ("replace 'Adafruit 3102' with PSP-slider class") was accepted into
  spec v0.2, and **v0.2 §3.3 now carries the superseding box** — the record of the chain is worth more
  than a rewrite. No independent buy instruction.
- `docs/independent-design/phase0-layout-v2-notes.md` (2) — Phase-0 layout freeze for the
  **84.2 × 103.7** board, superseded by `layout_v3_table` and then `v5_6` (84.2 × 100.0). Historical.
- **Case v1 trio — `hardware/case/CASE-NOTES.md:328`, `hardware/case/agentpad13_case.py:372`,
  `hardware/case/layout_v2.py:66` (3 hits): HISTORICAL, left.** Proven, not assumed: case **v2** is the
  live case (`hardware/case/v2/`), `agentpad13_case_v2.py` imports `pcb_components_data_v2` and derives
  from the `v5_6` contract — it does **not** import `layout_v2.py` or `agentpad13_case.py`, and cites
  v1 only as "`[§n]` … (v1 case, values re-derived)"; `v5-release-compiled/hardware/case/` ships
  **v2 only**. The v1 files describe the v1 case against a v4-era board and are not on any live path.
- `hardware/case/v2/CASE-V2-NOTES.md:487` (1) — **NOT TOUCHED**, owner is live-editing it (brief).
- `hardware/pcb/loudest-micro/loudest-micro.kicad_pcb` (4) — the v4-era project board; superseded by
  `v5_6`. Its JS1 binding is *correctly* the old fpid; LAYOUT-NOTES §1 now says so explicitly.
- Retained do-not-substitute breadcrumbs untouched as ordered: `verify_fabpack.py` gate literals (15),
  `build_fabpack.py` (1), `build_loudest.py` counter-example comments (4), `COST-ANALYSIS.md`
  supersession rows (4, already correct), `BOM-draft-v4-historical.csv` (2),
  `lib/loudest.pretty/JS1_PSP_slider_4pad_handsolder.kicad_mod` (6), `harness/contract_v4.json` (2 —
  both are correct *adjudication* text describing the replacement), `exports/fab-*.pdf` (v4-era).

**Also observed, NOT acted on (outside brief, flagged for the coordinator):** `docs/HANDOFF-STATE.md`
is stale **well beyond line 19** — it is stamped "Updated 2026-07-16" and its "Critical path RIGHT NOW"
still calls `hardware/pcb/cleanroom/cleanroom.kicad_pcb` the live Rev-A board with routing incomplete.
None of that is money-facing (line 19 was the only line that could cost money, and it is fixed), but
the doc bills itself as "read this first in any new session". Recommend a coordinator-level refresh.

### Task 2 — `Joystick.pretty` created; the last ERC warning is gone

The YA13 footprint existed **only inside** `v5_6.kicad_pcb`, so the schematic's fpid
`Joystick:YA13-FL7.4-B5Ka_C37323742` resolved to nothing on disk. Exported (export only — **the board
was loaded read-only and never saved**; no `SaveBoard` call exists in the script):

- **NEW:** `hardware/pcb/lib/Joystick.pretty/YA13-FL7.4-B5Ka_C37323742.kicad_mod`
  md5 **`7bdcc38ea47b0085e689f647e68cf274`**, 3963 B, `(version 20241229) generator_version "9.0"`.
- Normalizations applied (the standard board-instance → library set, each deliberate): orientation
  180° → 0 and anchor → (0,0) via `FOOTPRINT::SetOrientation/SetPosition` so KiCad's own transform
  un-bakes the rotation from the pad angles; board sheet `path` cleared; pad net codes → 0;
  `Reference` → `REF**`. **Nothing else** — descr, tags, Value, pads, F.Fab/F.CrtYd/F.SilkS graphics
  are the board's own bytes.
- `hardware/pcb/loudest-micro/fp-lib-table`: `Joystick` row added, matching the table's existing row
  style and `${KIPRJMOD}/../lib/...` path convention. The `loudest` row's descr (which still read
  "pinout metered-before-solder") is re-worded to mark it SUPERSEDED and retained-as-record.

**Round-trip proof (21/21 PASS).** Method: load the *exported* `.kicad_mod`, place it at the board's
JS1 anchor/orientation with KiCad's transform, then diff every pad against a fresh read of `v5_6`:

```
lib fp pad count == 10                                          PASS
lib fp is through-hole attr / pads carry no net                 PASS
pad number sets identical      board == lib == 1..6, MP1..MP4   PASS
every pad identical (pos/size/drill/shape/attr/angle/layers)    PASS   differing=none
frozen hole table, all 10 (V5-NOTES v5_6 MANIFEST):
  1 (61.46,10.87) 2 (61.46,13.37) 3 (61.46,15.87)  drill Ø1.0 pad Ø1.8 PTH
  4 (67.21, 5.12) 5 (69.71, 5.12) 6 (72.21, 5.12)  drill Ø1.0 pad Ø1.8 PTH
  MP1 (64.41,7.12) MP2 (75.01,7.12) MP3 (64.41,19.62) MP4 (75.01,19.62)
                                                   drill Ø1.2 pad Ø2.0 PTH
drill census 6x Ø1.0 + 4x Ø1.2      tally={1.0: 6, 1.2: 4}      PASS
board md5 unchanged                 221ebb98…                    PASS
```

**ERC before/after — measured, not asserted.** Proved by temporarily restoring the HEAD fp-lib-table,
re-running, then restoring the fixed one (`kicad-cli sch erc --severity-all`, KiCad 9.0.9):

```
BEFORE (no Joystick row):  Found 342 violations   footprint_link_issues = 1   error-severity = 0
AFTER  (Joystick row):     Found 341 violations   footprint_link_issues = 0   error-severity = 0
```

Delta is exactly **−1** and it is exactly the target: `[footprint_link_issues]: The current
configuration does not include the footprint library 'Joystick'`. **0 error-severity maintained.** The
surviving 341 are all `; warning` and all `lib_symbol_issues` ("does not include the symbol library
'power' / 'Device' / …") — the documented headless noise, unchanged in count and kind.

*Tool note for successors:* `kicad-cli sch erc` reports the footprint-library warning under
`[footprint_link_issues]`, **not** under a footprint heading, and the file also carries a *symbol*
library warning for `Joystick` that looks identical at a glance. Grep the rule id, not the message.

### Task 3 — public repo `agentpad13`: committed, NOT pushed

`git fetch` first; base `5ae22e6`, clean. **New commit `e5fdd2c`**, `origin/main` still at `5ae22e6`
(**ahead 1, not pushed** — coordinator pushes after review).

**Diff-hunk proof (the deliverable).** `diff -u public private` on the schematic:

```
BEFORE this pass : 5 hunks  = branding (L7 title_block, L927 text) + JS1 (L19 lib_symbol,
                             L529 placed symbol, L539-564 lug/GND block + ±5.08 R11/R12/C23/C24 shift)
AFTER re-snapshot: 2 hunks  = @@ -4,7 +4,7 @@ and @@ -927,6 +927,6 @@ , 4 changed lines total
                             — branding ONLY, exactly the state the tact pass left
```
Method: copy private → public, then exactly 2 guarded string substitutions (each asserted to match
exactly once, and asserted absent in the public form beforehand). Public md5
`b9a9c5b7a197d6c192ee26c3c5382c7f` → **`8656aea34899dc6705628e95826aa658`**.

Leak sweep on the written file: `/Users/yuanz` 0, `Loudest` 0, `work-loudest` 0, `PSP_slider` 0,
`PSP-Slider` 0, `3103` 0, `6193574` 0.

Two things that look like leaks and are **not**, recorded so nobody "fixes" them:
1. `(instances (project "loudest-micro" …))` appears 341× in the public schematic. It is the KiCad
   **project binding inside every symbol instance**, structural not branding, and the public snapshot
   has always carried it verbatim (337 → 341; the +4 are the four new GND symbols on the MP lug rows).
   Scrubbing it is outside the 2 branding hunks and would break instance resolution.
2. JS1's `Description` reads "… **replaces the rejected PSP slider**" — the intentional breadcrumb the
   previous pass wrote (same text in `BOM-draft.csv`). Bare `PSP` is therefore **not** a valid guard
   word; only the dead-part identifiers are.

**Also carried to public:**
- `firmware/FIRMWARE-V4-NOTES.md:307` and `firmware/loudest_micro/keyboard.json:38` — the two the brief
  named, same corrections as private.
- `firmware/loudest_micro/config.h` — **beyond the brief, deliberate**: it carries the same stale
  description, and it was byte-identical private↔public at HEAD; leaving it would have opened a new
  mirror divergence in a file this pass just edited.
- `hardware/pcb/lib/Joystick.pretty/…kicad_mod` (byte-identical to private) + the `Joystick` row in
  `hardware/pcb/agentpad13/fp-lib-table`. **It belongs**: the public repo already ships
  `hardware/pcb/lib/` and its own `fp-lib-table` (byte-identical to the private one at HEAD), and the
  public schematic's fpid dangled identically. Public ERC after: **341 violations, 0
  footprint_link_issues, 0 error-severity** — matches private exactly. `lib/LIBS.md` was **not**
  touched: it documents *vendored third-party* libs (marbastlib, MX_V2) with license/provenance;
  first-party `loudest.pretty` has no row there either, so omitting `Joystick.pretty` follows the file's
  own convention.

**⚠️ NEAR-MISS, recorded because it nearly shipped a branding regression.** A first attempt copied the
three firmware files private → public wholesale on the strength of a comparison that was **silently
bogus** — both `git show HEAD:$f` invocations resolved against the *same* repo because of an earlier
`cd`, so "identical" was compared against itself. `FIRMWARE-V4-NOTES.md:76` in fact differs
legitimately between the repos ("renamed \"Loudest Micro\" → **\"agentpad13\"**" vs "renamed to
**\"agentpad13\"** (from the legacy internal project name)") and the copy clobbered it. Caught by a
post-copy leak grep, restored, and re-diffed to **exactly 1 branding hunk**. `keyboard.json` and
`config.h` genuinely were byte-identical at HEAD. **Lesson: `git -C <repo>` always; a bare `git show`
after a `cd` in the same command line is not a cross-repo comparison.**

**Order-facing public files VERIFIED, not re-edited** (brief): `BOM.csv:28`,
`assembly/bom_opaque.csv:13`, `assembly/bom_translucent.csv:13` all carry
`YA13-FL7.4-B5Ka(45-10)-R-Y06` / `Shenzhen Yatelian/YTL` / `C37323742` / `PCBWay-THT`;
`assembly/cpl_opaque.csv:43` and `cpl_translucent.csv:53` both read
`"JS1","YA13-FL7.4-B5Ka","YA13-FL7.4-B5Ka_C37323742",69.710000,-13.370000,180.000000,top`.
`hardware/pcb/README.md:16` already described the swap correctly. The three shipped zips were swept
with the guarded regex: **0 real hits** — all 38 raw `3103` matches inside them are numeric
false-positives in gerber coordinates (`27.3103`-class), the same artefact the previous pass
documented.

### OWNER CALL — the superseded public footprint

`agentpad13/hardware/pcb/lib/loudest.pretty/JS1_PSP_slider_4pad_handsolder.kicad_mod` is still shipped
publicly. **Recommendation: KEEP** — concurring with the coordinator's read. Grounds:

1. **The precondition is met, measured:** a full-tree sweep of the public repo for
   `JS1_PSP_slider` returns **exactly one file — the `.kicad_mod` itself.** No schematic, board,
   BOM, CPL, fp-lib-table row, README or zip member references it. It is inert.
2. It costs ~4 kB and it is the only artifact that shows *what* the YA13 replaced — the lineage the
   annotated docs now point at.
3. Its `fp-lib-table` row is retained (the lib must stay registered for the file to be loadable at
   all) but its descr now says **SUPERSEDED … referenced by no live file**, so nobody can mistake it
   for live.

**If the owner prefers deletion**, delete the `.kicad_mod`, the `loudest` fp-lib-table row in **both**
repos, and expect no other consequence — but the private-tree copy should then be kept as the record.

### Gates re-run at close

```
python3 hardware/pcb/fabpack/verify_fabpack.py v5/hardware/pcb/fabpack_out_v5_6

RESULT: 31/31 checks PASS
        board unconnected ratsnest (informational): 0
```
including verbatim:
```
  [PASS] CPL opaque: JS1 row present == 69.710000,-13.370000,180.000000,top   (got=69.710000,-13.370000,180.000000,top)
  [PASS] BOM opaque: JS1 line present, LCSC C37323742, YA13 MPN   (matches=1 C37323742/YA13-FL7.4-B5Ka(45-10)-R-Y06)
  [PASS] BOM opaque: no Adafruit-3103 / live PSP-slider reference   (3103/6193574_free=True no_live_slider=True)
  [PASS] BOM translucent: no Adafruit-3103 / live PSP-slider reference   (3103/6193574_free=True no_live_slider=True)
  [PASS] JS1 drill census: 6x Ø1.0 + 4x Ø1.2 THT holes   (tally={1.0: 6, 1.2: 4})
```
Gerber-analyzer findings triage: 0. Edge.Cuts octagon 84.2 × 100.0, 8 vertices closed. CPL 90/110.
Identical to the previous run — nothing drifted.

### Deliberate non-actions

- **No board mutation, no fabpack rebuild, no release-folder edit.** `fabpack_out_v5_6` byte-unchanged
  (no fabpack input moved). `v5-release-compiled/` untouched — this pass changed **zero** release
  artifacts, so no MANIFEST md5 row moves. Banked/superseded trees untouched.
- **`hardware/case/v2/CASE-V2-NOTES.md` NOT opened for writing** (owner live-editing).
- **No git commit in work-loudest** (owner commits this repo).
- `firmware/POLARITY-NOTE.md` exists only under `v5-release-compiled/firmware/`. Every new reference
  this pass wrote says "**in the release**", matching the existing convention in
  `hardware/pcb/fabpack/ORDERING.md:184`. Creating a working-tree copy was not authorized and is
  flagged instead: if the owner wants `firmware/POLARITY-NOTE.md` to resolve in the working tree, that
  is a one-file copy out of the release.

**ORDER HOLD STANDS.** `v5_6.kicad_pcb` re-verified at the end of this pass:
**`221ebb98fcf44f860ed65f7ed8d1bc45`** — unchanged.

---

## DOC CLEANUP — `HANDOFF-STATE.md` full refresh + `POLARITY-NOTE.md` working-tree copy (2026-08-05, doc-cleanup executor)

**Owner-authorized, doc-only.** **Zero board mutation, zero fabpack rebuild, zero release-artifact
change.** `v5/hardware/pcb/v5_6.kicad_pcb` md5 `221ebb98fcf44f860ed65f7ed8d1bc45` asserted at start
and at close — **unchanged**. No git commit (coordinator commits and pushes).

### Task 1 — `docs/HANDOFF-STATE.md` REWRITTEN to current truth

The previous pass fixed line 19 (the dead-joystick buy instruction) and flagged the rest as broadly
stale: stamped **2026-07-16**, its "Critical path RIGHT NOW" still called
`hardware/pcb/cleanroom/cleanroom.kicad_pcb` the live board with routing unfinished — in a document
that bills itself "read this first in any new session".

**md5:** ledger-recorded pre-image `09bfbccf2cc030a29616cf3106922aaa` (previous pass's output) →
**`358acf9eb162dd2d5fcaa3a4981cea7b`**, 5802 → **27580 B** (25 → 350 lines). *Honesty note (protocol §1): the file was
read in full and its content matched the ledger's description exactly (25 lines, 2026-07-16 stamp,
the line-19 🔻 box), but its md5 was **not** independently hashed before the overwrite — the identity
above is content-confirmed, not hash-confirmed.*

**Every factual claim is artifact-derived and carries its source inline in the document.** Sources
used: `v5/V5-NOTES.md`, `hardware/case/v2/CASE-V2-NOTES.md` (**read-only — never opened for
writing**, owner live-editing), `v5-release-compiled/RELEASE.md` + `MANIFEST.md` + `HOW-TO-ORDER.md`,
`hardware/pcb/BOM-FINAL.csv`, `hardware/pcb/COST-ANALYSIS.md`, `hardware/pcb/harness/contract_v4.json`,
`hardware/case/v2/gasket/README.md`, `hardware/case/v2/keycaps/KEYCAP-NOTES.md`,
`hardware/case/v2/gen_plate_fab.py`, and the fabpack in `v5/hardware/pcb/fabpack_out_v5_6/`.

**Before → after structure:**

| Before (2026-07-16, 25 lines / 5802 B) | After (2026-08-05, 350 lines / 27580 B) |
|---|---|
| — | **🔄 Revision banner** (dated, says what was stale and why) |
| Mission (verbatim owner standard) | **PRESERVED verbatim** |
| **Critical path RIGHT NOW** = cleanroom board, FR run staged, routing fallback ladder | **REPLACED** — "nothing is blocked on engineering; the blockers are owner-side": order hold + the 4-step unblock sequence (2 drafted PCBWay replies, 1 live mixed SMT+THT quote, then upload) |
| *(implicit)* | **NEW — State of record**: board / case / fabpack / firmware, each with verbatim gate output |
| *(absent)* | **NEW — Ordering reality**: per-part order-vs-print table, the 3 no-BOM hardware lines, the optional lines, per-board cost |
| *(absent)* | **NEW — Open decisions + the 9-item NOT-QUOTED register** (blocking item first) |
| *(absent)* | **NEW — What has actually been ordered vs not** (6-row table, incl. two ❓ UNKNOWN rows) |
| *(absent)* | **NEW — ⚠️ Known divergence**: the release bundle's plate fab set is pre-trim (see below) |
| item 6 "Owner physical gates" | **Owner physical gates** section — the line-19 🔻 box preserved verbatim, + first-article and first-power-on gates |
| Do-not-relearn list | **PRESERVED** + 3 v5-campaign additions (STEP `FILE_NAME` non-determinism; `kicad-cli sch erc` files the footprint-lib warning under `[footprint_link_issues]`; `git -C <repo>` always) |
| Fixed truths | **PRESERVED and corrected**: 🔺 "All-SMD-one-side (bottom)" struck (JS1 is top-side THT); costs re-stated from the 2026-08-05 re-derivation; licenses re-marked **planned, not decided**; public-mirror push state re-measured |
| "After the routed board (in order)" items 1–6 | **MOVED to `# HISTORY`**, dated, each marked closed/not-closed — incl. the two Wave-3 sub-items that were **never done and never re-scoped: the Wokwi sim of the real UF2, and the `kicad-happy:spice` run** |
| — | **HISTORY** also gains the 2026-07-19 → 2026-08-05 sourcing-reversal lessons (JS1, SW14/15) in the house strike-don't-delete style |

**Claim → source spot-check (the ones that would cost money if wrong):**

| Claim | Source |
|---|---|
| board `221ebb98…`; DRC 0 / unconnected 0 / contract 45/45; outline 84.200 × 100.000 | RELEASE.md §(b)1 verbatim; re-hashed this pass |
| J1 anchor (42.1, **3.05**, rot 0), face **0.60** proud | RELEASE.md row B; CASE-V2-NOTES §12.1; contract_v4.json J1 adjudication |
| JS1 = YA13 / C37323742 / (69.71, 13.37, rot 180) F.Cu / 6×Ø1.0 + 4×Ø1.2 | RELEASE.md row C; verify_fabpack JS1 drill census + CPL row |
| band WALL **5.4** default, 3.0/5.4/7.4 all gated; OUTER 95.6 × 111.4; corner 4.400 flat | CASE-V2-NOTES §18.1/§18.3/§18.6 |
| funnel **depth = WALL − 2.4** (3.00 at default); shell bridge **2.10 WALL-INVARIANT** | CASE-V2-NOTES §16.5 + §18.3 gate line |
| perimeter support rail, 86 % rim coverage (1520/1770 mm³) | CASE-V2-NOTES §13 |
| SW-corner boss notch; `notch_insert_wall[3.7,3.7] = 1.651` | CASE-V2-NOTES §12 item 2 + §18.3 |
| plate opening = YA13 asymmetric rect W58.91/N2.57/E77.36/S21.02 R1.5 | CASE-V2-NOTES §14 frozen table + validate_fab_v5 gate |
| khana **101/101**, 8 interferences, tray `d7d16481…` unchanged | RELEASE.md §(b)2; CASE-V2-NOTES §18.3 |
| fabpack **31/31**; `fabpack_out/` (v5_4) + `fabpack_out_v5_5/` superseded | re-run this pass (below); V5-NOTES 2026-07-20 fabpack entry |
| placements **opaque 90 / translucent 110**; DNP 23/3 | verify_fabpack verbatim |
| RE1 = PEC11R-4215F-S0024, **LCSC C143790 stock 797 (low, buy early)**, DigiKey 4499665, $2.357 | BOM-FINAL.csv RE1 row; COST-ANALYSIS §c |
| no-BOM hardware: 4× M3×8 ISO 7380; 4× CNC Kitchen M3 insert L5.7/Ø4.2 pilot (tray only); 4× 3M SJ61A1 Ø7.9×2.2 | CASE-V2-NOTES §0 "Hardware:" line + §1 z-stack |
| gasket = **0.5 mm** PORON 4701-30/92 + 3M 468MP/9471LE-class PSA, 10 segs ~180 mm² | `gasket/README.md` L66/L76/L80 |
| costs $78.22/$69.51/$63.85 opaque, $82.68/$73.98/$68.31 translucent | COST-ANALYSIS 2026-08-05 revision block |
| RE1 hand-solder rationale **VOID** (JS1 already pays the THT tier) | COST-ANALYSIS assumption 4 (struck) + §b/§c |
| switch grid 19.05 (SW1 13.525 → SW2 32.575); 45 refs; chamfer 13.2 at (0,0) | contract_v4.json parsed this pass |

**Two consistency defects found in live docs, recorded in HANDOFF-STATE, NOT silently fixed:**

1. **⚠️ The release bundle's plate fab set is PRE-TRIM — a real ordering hazard.** Measured directly
   off Edge.Cuts geometry of both copies, all three variants:

   ```
   hardware/case/v2/fab/agentpad13_v2_plate_v5.kicad_pcb          84.400 x 100.000 mm  (working tree)
   v5-release-compiled/.../fab/agentpad13_v2_plate_v5.kicad_pcb   84.400 x 100.200 mm  (release bundle)
   ```
   plain / blank / tented-ring `.kicad_pcb` **and** all three gerber zips differ (6 files, md5s in the
   report). Cause: the owner-directed long-axis trim of 2026-07-21 (*"Resize the top plates to 100mm.
   That 0.2 is gonna cost us 25%. Not worth it."*) implemented as `PLATE_LONG_TRIM = 0.2` in
   `gen_plate_fab.py:200-215`. The working tree was regenerated; **`v5-release-compiled/` was not, and
   `MANIFEST.md` still carries the pre-trim md5s.** `RELEASE.md §(e)` points at the working-tree path,
   which is the correct file — but uploading the bundle's own copy would ship a 100.2 mm plate and
   lose the ≤100 mm promo tier, i.e. exactly the 25 % the owner refused to pay. The trim is recorded
   **only in generator code comments**; there is **no §-record in CASE-V2-NOTES** and §14's gate
   transcript still prints `100.200`. **Not fixed here** — release-folder writes and CASE-V2-NOTES
   writes are both out of scope for this brief. **Coordinator: this needs a decision.**
2. `HOW-TO-ORDER.md`'s shopping line says *"PORON/EVA sheet 1–2 mm (optional gasket)"*; the kit's own
   `gasket/README.md` specifies **0.5 mm** (0.5 into the 0.3 mm gap = 40 % compression). HANDOFF-STATE
   now carries the correction with a ⚠️; the release doc is untouched.

**Deliberately recorded as UNCERTAIN rather than invented.** The brief stated *"keycaps and Box Jade
switches already ordered by the owner"*. **Keycaps: corroborated** — PCBWay holds the 2026-07-22
unsuffixed STLs and returned a thin-socket-wall review (CASE-V2-NOTES §17; KEYCAP-NOTES §10/§10.6).
**Box Jade switches: NOT corroborated in-repo** — the newest repo statement points the other way
(*"Owner decision, taken with no physical switches on hand"*, KEYCAP-NOTES §10.2, 2026-07-24).
HANDOFF-STATE records the switch order as owner-side truth with an explicit ❓ and cites both.
Likewise the RE1/screws/inserts/bumpons/foam/PORON row is **UNKNOWN**, not "not ordered".

### Task 2 — `firmware/POLARITY-NOTE.md` now exists in the working tree

`cp -p v5-release-compiled/firmware/POLARITY-NOTE.md firmware/POLARITY-NOTE.md` — this closes the
item the previous pass flagged and declined to do without authorization (V5-NOTES 2026-08-05 closeout,
"Deliberate non-actions").

```
release  v5-release-compiled/firmware/POLARITY-NOTE.md  e03f1a547adc7609d0b5c19c33bfc592  3432 B
worktree firmware/POLARITY-NOTE.md                      e03f1a547adc7609d0b5c19c33bfc592  3432 B
cmp: BYTE-IDENTICAL
```

**Release copy UNTOUCHED and its MANIFEST row still valid**: `MANIFEST.md:31` asserts
`e03f1a547adc7609d0b5c19c33bfc592` / `3432` — both re-measured PASS after the copy. No MANIFEST row
moves; no release artifact changed.

**Reference update — scoped, not swept.** Only `docs/HANDOFF-STATE.md` (a doc this pass was already
rewriting) now points at the bare working-tree path, and it states explicitly that the older
"in the release" wording remains correct because **both paths now resolve**. The other 9 live-doc
references (`firmware/loudest_micro/config.h:11`, `firmware/FIRMWARE-V4-NOTES.md:315`,
`firmware/loudest_micro/keyboard.json:38`, `hardware/pcb/SCHEMATIC-REVIEW.md:253`,
`hardware/pcb/LAYOUT-NOTES.md:87,269`, `hardware/pcb/DESIGN-DECISIONS.md:44,71,156`,
`hardware/pcb/COST-ANALYSIS.md:99`, `hardware/pcb/fabpack/ORDERING.md:184`) were **left untouched by
design** — the brief forbade a tree sweep, and none of them is now wrong.

### Gates re-run at close

```
python3 hardware/pcb/fabpack/verify_fabpack.py v5/hardware/pcb/fabpack_out_v5_6

RESULT: 31/31 checks PASS
        board unconnected ratsnest (informational): 0
```
Verbatim, identical to the previous run — nothing drifted. Gerber-analyzer findings triage: 0.
Edge.Cuts octagon 84.200 × 100.000, 8 vertices closed. CPL 90/110. BOM DNP 23/3. All five
MPN-vs-footprint checks green (`PTS645SM43SMTR92 LFS` / `C221880` vs `SW_SPST_PTS645Sx43SMTR92`).

**Board md5 at close: `221ebb98fcf44f860ed65f7ed8d1bc45` — unchanged.**

### Files written (2)

| file | before | after |
|---|---|---|
| `docs/HANDOFF-STATE.md` | `09bfbccf2cc030a29616cf3106922aaa` *(ledger-recorded)* | **`358acf9eb162dd2d5fcaa3a4981cea7b`** (27580 B, 350 lines) |
| `firmware/POLARITY-NOTE.md` | *(did not exist)* | **`e03f1a547adc7609d0b5c19c33bfc592`** (byte-identical to the release copy) |

*(plus this append-only entry in `v5/V5-NOTES.md`.)*

### Deliberate non-actions

- **`hardware/case/v2/CASE-V2-NOTES.md` NEVER opened for writing** (owner live-editing) — read-only throughout.
- **`v5-release-compiled/` untouched**, including `MANIFEST.md`; the only interaction was reading, and
  a `cp` **out of** it. Zero release artifacts changed, so zero MANIFEST rows move.
- Banked/superseded trees untouched: `v4-release-compiled`, `v5-discarded`, `fabpack_out`,
  `fabpack_out_v5_5`, `v4/`, boards `v5`..`v5_5`, `routing-v3`, `quilter-probe`, `candidate-finish`,
  `cleanroom`. Retained do-not-substitute breadcrumbs untouched.
- **No board mutation, no fabpack rebuild, no plate regeneration, no schematic/netlist touch.**
- **No git commit, no push, no upload, no spending.**

**ORDER HOLD STANDS.**

---

## PLATE FAB SET — PRE-TRIM COPIES PURGED FROM THE RELEASE BUNDLE AND THE PUBLIC MIRROR (2026-08-05, plate-sync executor)

Resolves defect **1** of the two "consistency defects found in live docs, recorded in HANDOFF-STATE,
NOT silently fixed" above, and defect **2** (the PORON line) with it. Coordinator-authorized this
pass: release-folder writes, `CASE-V2-NOTES.md` writes, and an `agentpad13` commit.

### 1. The measurement, re-verified from scratch before anything was touched

Edge.Cuts parsed directly out of every copy — `.kicad_pcb` via s-expression walk with true arc
sampling (3-point circle fit, quadrant extremes included), gerber zips via an RS-274X coordinate
parse of the `-Edge_Cuts.gm1` member. **Not read from renders, docs or prior sessions' numbers.**

| variant | working tree `hardware/case/v2/fab/` | `v5-release-compiled/…/fab/` | public `agentpad13/hardware/case/fab/` |
|---|---|---|---|
| `agentpad13_v2_plate_v5.kicad_pcb` | **84.400 × 100.000** ✅ | 84.400 × **100.200** ❌ | 84.400 × **100.200** ❌ |
| `agentpad13_v2_plate_tented_ring_v5.kicad_pcb` | **84.400 × 100.000** ✅ | 84.400 × **100.200** ❌ | 84.400 × **100.200** ❌ |
| `agentpad13_v2_plate_blank_v5.kicad_pcb` | **84.400 × 100.000** ✅ | 84.400 × **100.200** ❌ | 84.400 × **100.200** ❌ |
| `plate_v5_gerbers.zip` (`Edge_Cuts.gm1`) | **84.400 × 100.000** ✅ | 84.400 × **100.200** ❌ | 84.400 × **100.200** ❌ |
| `plate_v5_ring_gerbers.zip` | **84.400 × 100.000** ✅ | 84.400 × **100.200** ❌ | 84.400 × **100.200** ❌ |
| `plate_v5_blank_gerbers.zip` | **84.400 × 100.000** ✅ | 84.400 × **100.200** ❌ | 84.400 × **100.200** ❌ |
| `agentpad13_v2_plate_v5.dxf` | **100.000** ✅ | **100.203** ❌ | **100.203** ❌ |
| `agentpad13_v2_plate_v5_top.svg` (page box) | 84.4804 × **100.0760** ✅ | 84.4804 × **100.2792** ❌ | 84.4804 × **100.2792** ❌ |
| `agentpad13_v2_plate_v5_top.png` | 1000 × **1185** px ✅ | 1000 × **1187** px ❌ | 1000 × **1187** px ❌ |

**The prior agent's report is CONFIRMED, and it under-counted the blast radius**: it named 6 files in
2 trees; the true set is **9 files in 2 trees** (the DXF and both renders carry the drift too), and
the **public mirror was equally stale** — byte-identical to the bundle's pre-trim copies
(`9e488bbe` / `0a2603c5` / `d2dbab7b` / `35bd5a39` / `bac58f79` / `6a854c59`), i.e. the mirror had
never received the trim either.

**Corroboration that the working tree is the CORRECT side**, derived from the generator source, not
assumed. `gen_plate_fab.py` emits
`rounded_rect(-0.1, -0.1 + TRIM/2, C.PLATE_W - 0.1, C.PLATE_H - 0.1 - TRIM/2, C.PLATE_R)`; with
`PLATE_W = 84.4`, `PLATE_H = 100.2`, `PLATE_R = 5.4`, `PLATE_LONG_TRIM = 0.2` that is
`rounded_rect(-0.1, 0.0, 84.3, 100.0, 5.4)` — **exactly** the working-tree geometry including the
corner tangents at `y = 5.4` / `y = 94.6`. Setting `TRIM = 0` reproduces the bundle's geometry
exactly (`-0.1 … 100.1`, tangents `5.3` / `94.7`). Independently, `validate_fab_v5.py` already
carried `PLATE_WH = (84.40, 100.00)  # long axis trimmed 100.20->100.00 (fab 100 mm cap)` and
`ck(near(d_top, 2.57, 0.02), ...)` — the sanctioned gate had been updated with the trim; only the
shipped bytes and the ledger lagged.

**Blast-radius proof.** UUID-blind unordered set-difference of pre-trim vs post-trim
`agentpad13_v2_plate_v5.kicad_pcb` (93 primitives each): **exactly 8 differ** — the 4 outline lines
and 4 corner arcs — and **85 are byte-identical**. No cutout, opening, hole or marker moved.

### 2. The mystery `fab/` files — identified, NOT assumed (they supersede nothing)

| file | verdict |
|---|---|
| `plate_v5_gerbers_100mm.zip` | **byte-identical md5 duplicate** of `plate_v5_gerbers.zip` (`de2f9391`) |
| `plate_v5_ring_gerbers_100mm.zip` | **byte-identical md5 duplicate** of `plate_v5_ring_gerbers.zip` (`ef58b6c4`) |
| `plate_v5_blank_gerbers_100mm.zip` | **byte-identical md5 duplicate** of `plate_v5_blank_gerbers.zip` (`8463dcd7`) |
| `agentpad13_v2_plate_filled_v5.kicad_pcb` + `plate_filled_100mm.zip` | **new unreleased touch-marker STYLE variant**, already at 84.400 × 100.000 |
| `agentpad13_v2_plate_ring_v5.kicad_pcb` + `plate_ring_100mm.zip` | **new unreleased touch-marker STYLE variant**, already at 84.400 × 100.000 |

The three `_100mm.zip` files (mtime 20:19) are re-saves of the shipped zips under a name advertising
the 100 mm fact — same md5, byte for byte. The `filled` / `ring` pair (mtime 20:51) differ from their
named siblings by **exactly one primitive**, the TP5 marker at (13.525, 88.85):
`filled` = `F.SilkS` r5.0 **fill yes** stroke 0.8 (a solid Ø10 silk disc, no mask opening ⇒ no ENIG
requirement) vs shipped `disc` = `F.Mask` r6.0 fill yes; `ring` = `F.SilkS` r5.0 fill no **stroke
0.8** (Ø10 heavy ring) vs shipped `tented_ring` = `F.SilkS` r8.0 fill no stroke 0.2 (Ø16 thin ring).
Their zips are full 26-file KiCad default exports, not the curated 10-file set the shipped variants
use. **Referenced by no generator path, no doc, no manifest, and untracked in git.** They are a
style experiment; the release set remains the three named variants. Full write-up: CASE-V2-NOTES §19.7.

### 3. What was synced

All **9** plate artifacts copied working tree → `v5-release-compiled/hardware/case/v2/fab/` **and** →
`agentpad13/hardware/case/fab/`. All three trees are now byte-identical:

| file | md5 (all three trees) | bytes |
|---|---|---|
| `agentpad13_v2_plate_v5.kicad_pcb` | `b15a683bf6a1fcede54ee08478080105` | 15328 |
| `agentpad13_v2_plate_tented_ring_v5.kicad_pcb` | `7c384ae41dd8e0bd4b8ce22a06776983` | 15330 |
| `agentpad13_v2_plate_blank_v5.kicad_pcb` | `f1bf659421287aa16bdce5db7fe57a43` | 14437 |
| `plate_v5_gerbers.zip` | `de2f939102c8314cae51a5ca2089308d` | 6072 |
| `plate_v5_ring_gerbers.zip` | `ef58b6c41ca84c1e8d18d0d390f08f6a` | 6378 |
| `plate_v5_blank_gerbers.zip` | `8463dcd7ef6d530f262015ea714d212d` | 5828 |
| `agentpad13_v2_plate_v5.dxf` | `529b60f7e9833683a9f1ec89f1abbf27` | 13017 |
| `agentpad13_v2_plate_v5_top.png` | `c1d1ab21cbc7c67e56114874cfef8551` | 31450 |
| `agentpad13_v2_plate_v5_top.svg` | `668fd03cf4d525b6a154fe8ab83436b7` | 5908 |

Post-sync re-measure of the bundle and the mirror: **84.400 × 100.000 on all three variants and all
three gerber zips, both trees.**

`v5-release-compiled/hardware/case/v2/CASE-V2-NOTES.md` was ALSO re-synced (it was byte-identical to
the working tree pre-edit, `ac2314c7` / 92496 B) so the shipped ledger is not the stale one — the
bundle's copy would otherwise still print `100.200` in §14 with no §19 at all.

### 4. `validate_fab_v5.py` VERBATIM — post-trim, real pcbnew, 3/3 variants

Run under the KiCad 9.0.9 bundled Python (`~/Applications/KiCad.app/…/Versions/3.9/bin/python3.9`).
Full transcript is quoted in **CASE-V2-NOTES §19.5**; the load-bearing lines:

```
[bbox] Edge.Cuts centerline = 84.400 x 100.000 mm  (x -0.100..84.300, y 0.000..100.000)
[count] Edge.Cuts shapes = 89
[JS opening] 4 lines + 4 arcs; extents W=58.910 N=2.570 E=77.360 S=21.020
[web] N->plate-top      = 2.570  (expect ~2.57)
[web] NE->screw(80.5,3.7)= 1.555  (floor 1.5; brief ~1.74)
[web] S->nearest switch  = 3.680 @ SW(70.675, 31.7)  (floor 2.0)
[web] nearest feature W  = 3.979 @ SW(51.625, 31.7)
RESULT: ALL GATES PASS
```

Exactly ONE web moved: `N->plate-top` 2.670 → **2.570**, i.e. the 0.1 mm the north edge travelled.
`NE->screw` is measured opening→screw (both frozen) and holds at **1.555**, still clearing the 1.5
floor by 0.055 per §14's addendum. Shape count 89 unchanged.

### 5. MANIFEST — clean N/N for the first time since the keycaps drop

- **9 plate rows** re-hashed (md5 + bytes + provenance note *"plate fab set re-synced to the
  2026-07-21 100.000 trim, 2026-08-05"*).
- **`HOW-TO-ORDER.md`** row re-hashed (`22fd1a48` → `d085320d`, 7363 → 7700 B) for the PORON fix.
- **`hardware/case/v2/CASE-V2-NOTES.md`** row re-hashed (`ac2314c7` → `51fc158c`, 92496 → 107190 B)
  for §19.
- **12 keycap STLs ADOPTED** into a new `### hardware/PCBWay_keycaps_boxfit_2026-07-24` section
  (`cap_{dish,plateau}_{1u,2u,2u_stab}{,_17p5}_boxfit.stl`). These are the owner's **ordered** resin
  set; provenance cites **`KEYCAP-NOTES.md` §10.3** as instructed — as-built ray cast plus an
  independent Möller–Trumbore re-measure (wall opening 1.420000, crest 1.280000, Y slot 1.250000,
  slot span 4.200000, roof z 3.800000, rib proud 0.070000/side; `min_wall_mm` 0.6499999999999735 on
  all twelve, bit-identical to pass one; Hausdorff vs pass one 0.085000 mm confined to the X-slot
  region; watertight + manifold, V−E+F = 2). The prior pass declined to invent rows for artifacts it
  had not gated — correct call; the gate record existed, so the rows are now real, not fabricated.
- **Stray `v5-release-compiled/hardware/case/v2/.DS_Store` deleted.**
- **Stats: 117 files / 22155730 B → 129 files / 42138523 B.**

**Self-verification VERBATIM (9 checks: existence, md5, bytes, no-orphans, Stats-count-vs-rows,
Stats-count-vs-disk, Stats-bytes-vs-rows, Stats-bytes-vs-disk, self-exclusion):**

```
[PASS] 1 existence          129/129 listed files present
[PASS] 2 md5                129/129 md5 match
[PASS] 3 bytes              129/129 byte counts match
[PASS] 4 no-orphans         0 on-disk file(s) without a row
[PASS] 5 stats-count-rows   Stats 129 vs rows 129
[PASS] 6 stats-count-disk   Stats 129 vs on-disk 129
[PASS] 7 stats-bytes-rows   Stats 42138523 vs row-sum 42138523
[PASS] 8 stats-bytes-disk   Stats 42138523 vs on-disk-sum 42138523
[PASS] 9 self-exclusion     MANIFEST.md has no self-row
RESULT: 9/9 checks PASS
```

Baseline for comparison, same 9-check split, run BEFORE any mutation: **6/9** — failures 4/6/8, all
one root cause (13 orphans = the 12 keycap STLs + the `.DS_Store`). The prior session reported
**7/9** counting 12 orphans; the delta is bookkeeping (its walk skipped the dotfile and it folded the
two Stats-vs-disk checks differently), **not** a different defect. Same root cause, now zero.

### 6. CASE-V2-NOTES — the trim finally has a §-record

**§19 added** (`## 19. Plate long-axis fab-cap trim — 100.2 → 100.000 mm (owner directive 2026-07-21;
§-record written 2026-08-05)`), 7 subsections: 19.1 what/why with the owner quote, 19.2 the
emit-time implementation and why `C.PLATE_H` deliberately stays 100.2 (it drives the band pocket,
which must not move — the plate-to-lip gap merely relaxes 0.30 → 0.40 mm/end), 19.3 exact before/after
geometry + the 8-of-93 primitive proof, 19.4 the 9 regenerated files with md5s, 19.5 the verbatim
post-trim validator run, 19.6 the propagation failure and its fix, 19.7 the mystery-file verdicts.

**Three stale spots annotated in place, none deleted** (house style: bold bracket / `>` erratum block):

- **§14's gate transcript** — `> **⚠ SUPERSEDED TRANSCRIPT (annotated 2026-08-05, §19).**` block
  above it naming the exactly two lines that moved (`bbox 100.200 → 100.000`, `N->plate-top 2.670 →
  2.570`) and stating explicitly that everything else in the block still stands verbatim.
- **§1's** `Plate 84.4 × 100.2 R5.4` — annotated as the **case-model** dimension, correct as written,
  with the emitted fab outline (84.4 × 100.0) called out.
- **§6's** Rev-A `84.40×100.20 / 82 edge shapes` fab line — annotated as superseded by the `_v5`
  plates (84.40×100.00, 89 shapes); coupon panel and touch chip unaffected.

### 7. PORON gasket stock — `1–2 mm` → `0.5 mm`

Defect 2 fixed at both live copies. The kit's own `gasket/README.md` specifies **0.5 mm** PORON
(`(0.5 − 0.3) / 0.5` = **40 %** compression into the band's 0.3 mm ledge gap, inside PORON's 20–50 %
band); 1–2 mm stock cannot enter that gap at all, so the shopping line was sending builders to buy
foam that physically does not fit.

- `v5-release-compiled/HOW-TO-ORDER.md` L17–20 — corrected, with the *why* inline.
- `agentpad13/HOW-TO-ORDER.md` L17–20 — same correction.
- The two ledger mentions (`docs/HANDOFF-STATE.md:159`, `v5/V5-NOTES.md:1827`) are **left as-is on
  purpose** — they are the historical record of the finding, not live guidance.

Also added (not a stale-fix, an ordering safeguard directly serving the promo tier): the plate's
**84.4 × 100.0 mm** size and its ≤100 mm promo-tier intent now appear in `HOW-TO-ORDER.md` Card 2
(both copies) and in `agentpad13/hardware/case/README.md`'s plate order settings, so a stale upload
becomes visible on the fab's own quote form.

### 8. Public mirror — committed, NOT pushed

`git fetch` first; the mirror was at `e5fdd2c` and clean (`main...origin/main`, no ahead/behind).
Its plate copies measured **84.400 × 100.200 on all six** geometry-bearing files — pre-trim, same
bytes as the bundle. No public doc claimed a stale plate DIMENSION (checked `README.md`,
`hardware/case/README.md`, `HOW-TO-ORDER.md`, `hardware/pcb/README.md`) — the dimension was simply
absent from the order settings, which is why the staleness was invisible; that gap is now closed.

**Commit `3a47533c99160a1c23e77643189052cefd346a99`** — *"Plate fab set was PRE-TRIM: 100.2 mm long
axis, outside the <=100 mm promo tier"*, 11 files, +473/−467. `main` is **ahead 1, NOT PUSHED** —
coordinator pushes.

### 9. No-drift gates

**`verify_fabpack.py v5/hardware/pcb/fabpack_out_v5_6` VERBATIM: RESULT 31/31 checks PASS** (sources:
gerber-analyzer + Edge.Cuts RS-274X parse + pcbnew 9.0.9). Layer completeness 9/9; gbrjob 84.300 ×
100.100 and centerline **84.200 × 100.000**; octagon 8-vert closed; drill analyzer == pcbnew
(285 holes / 182 vias); CPL 90/110 exact sets, both SKUs J1 `42.100000,-3.050000,0.000000,bottom`
and JS1 `69.710000,-13.370000,180.000000,top`; BOM DNP 23/3; JS1 LCSC C37323742 YA13 both SKUs; no
Adafruit-3103 / live PSP-slider; SW14/15 `PTS645SM43SMTR92 LFS` / C221880 both SKUs + afterlist;
JS1 drill census 6×Ø1.0 + 4×Ø1.2; both zips present. Gerber-analyzer findings triage: **0**.
Ratsnest **0**. The plate is not in the fabpack — this is a pure no-drift check and it did not drift.

**Board md5 CONFIRMED UNCHANGED at `221ebb98fcf44f860ed65f7ed8d1bc45`** on all three copies
(`v5/hardware/pcb/v5_6.kicad_pcb`, `v5-release-compiled/hardware/pcb/v5_6.kicad_pcb`,
`v5-release-compiled/hardware/pcb/fabpack_out_v5_6/source.kicad_pcb`), measured before and after.

### 10. Deliberate non-actions

- **No board, schematic, netlist, fabpack or case-model mutation.** No plate REgeneration — the
  trimmed files already on disk were copied, never re-emitted (build123d is not installed on this
  host, so a re-emit was not even possible; the arithmetic derivation in §1 stands in for it).
- The 5 untracked mystery files in `fab/` were **left exactly where they are** — identified and
  ledgered (§2, CASE-V2-NOTES §19.7), not adopted, not deleted. Adopting or deleting an owner-adjacent
  artifact is a coordinator call.
- Banked/superseded trees untouched: `v4-release-compiled`, `v5-discarded`, `fabpack_out`,
  `fabpack_out_v5_5`, `v4/`, boards `v5`..`v5_5`, the Rev-A unsuffixed plate files, the coupon panel
  and the touch chip.
- **No push, no upload, no spending.** One commit, in `agentpad13` only, as authorized.

**ORDER HOLD STANDS.**

---

## FIRMWARE VERIFICATION PASS — first behavioral-adjacent audit; **1 ships-broken defect found** (2026-08-13, firmware-verify executor)

**Report-first, doc-only.** **Zero board mutation, zero fabpack rebuild, zero release-artifact
change, zero firmware-source change.** `v5/hardware/pcb/v5_6.kicad_pcb` md5
`221ebb98fcf44f860ed65f7ed8d1bc45` asserted at start and at close — **unchanged**. No git commit.
This entry is the only file written. Nothing was "fixed": every defect below is either a judgment
call (fix strategy has >1 legitimate option) or needs hardware, so all are REPORTED, not applied.

Context: `docs/HANDOFF-STATE.md:328` records *"Not done and never re-scoped: the Wokwi sim of the
real UF2, and the `kicad-happy:spice` run."* Nothing behavioral had ever been exercised. This pass
substitutes a build + a full static firmware↔board cross-check from the board file itself.

### Path taken — TOOLCHAIN EXISTS, both keymaps BUILT (not the static-audit fallback)

A working toolchain was found on this host, so the build path was taken **and** the static audit was
done on top of it:

- `qmk` CLI 1.2.0 (`~/.local/bin/qmk`), `user.qmk_home` → the prior wave's
  `~/.claude/jobs/8b1a462c/tmp/firmware-wave/vial-qmk` (complete checkout, all submodules present).
- Homebrew `arm-none-eabi-gcc` 16.1.0 is **broken on this host** (`fatal error: stdint.h: No such
  file or directory` — no newlib headers). The bundled Arm GNU Toolchain 15.2.Rel1 in the same
  firmware-wave dir works and is what the Rev-A prebuilts were made with.
- macOS ships GNU Make 3.81, which rejects the `--output-sync=target` that `qmk compile -j N` adds.
  **Build serially (no `-j`)** or the build dies before compiling anything. Recorded so the next
  executor does not re-discover it.

Verbatim tails:

```
Linking: .build/loudest_micro_default.elf                                    [OK]
Creating UF2 file for deployment: .build/loudest_micro_default.uf2           [OK]
Copying loudest_micro_default.uf2 to qmk_firmware folder                     [OK]
DEFAULT_RC=0
...
VIAL_RC=0
```

| artifact | built | prebuilt | size | verdict |
|---|---|---|---|---|
| `loudest_micro_default.uf2` | `4af788ae28cc7f368607e69a270c18ad` | `4af788ae28cc7f368607e69a270c18ad` | 88064 = 88064 | **bit-identical** — reproduces, and matches the md5 `4af788ae…` claimed in `POLARITY-NOTE.md` |
| `loudest_micro_vial.uf2` | `cd246307…` run 1 / `d7c2e8fa…` run 2 | `e5008942…` | 104448 = 104448 | size-identical; **7 bytes** differ, and the **vial build is non-deterministic run-to-run** (two builds of identical sources differ), so the delta vs the prebuilt is build nondeterminism, not source drift |

The current working-tree sources differ from the Jul-18 copy in the build tree by **comments only**
(`config.h` header, `keyboard.json $joystick_comment`) — consistent with `default.uf2` reproducing
byte-for-byte. The scratch build tree was **restored byte-identical** to how it was found.

### Task 2 — LED chain: **CLEAN.** Chain order == refdes order == firmware index order

Chain reconstructed from the netlist (`RGB_D*` pad membership), **not** from refdes numbering:

```
U5.4 -> RGB_D00 -> LED1.3 | LED1.2 -> RGB_D01 -> LED2.3 | ... | LED14.2 -> RGB_D14 -> LED15.1
LED15.3 -> RGB_D15 -> LED16.1 | ... | LED23.3 -> RGB_D23 -> LED24.1 | LED24.3 = unconnected (end)
```

Every `RGB_Dnn` net has exactly 2 members (one DOUT, one DIN); no forks, no skips, no reversals.
`LED1..LED14` are `SK6812MINI-E` (DIN=pad3, DOUT=pad2); `LED15..LED24` are `SK6812-SIDE`
(DIN=pad1, DOUT=pad3) — the pad-role swap between the two part families is handled correctly on the
board. **Electrical order is exactly LED1→LED24, so firmware index i == LED(i+1). ZERO divergence.**
The scrambled-animation failure mode does **not** exist here.

**Coordinates re-derived, not trusted:** `firmware/gen_led_layout.py` was run against
`v5_6.kicad_pcb` and its output diffed against the live `keyboard.json` `rgb_matrix.layout`:
**24/24 entries, 0 mismatches.** Despite the file header still crediting "v4_r27", the shipped
coordinates are correct for v5_6 (the LED centroids did not move). Transform = per-axis independent
normalisation to the Edge.Cuts bbox (8 `gr_line`s, **84.2 × 100.0 mm**) → x·224/84.2, y·64/100.

**Flags vs physical part type — all correct:** flags 4 `KEYLIGHT` = chain 0-12 = LED1-13
SK6812MINI-E reverse-mount under SW1-SW13; flags 8 `INDICATOR` = chain 13 = LED14 SK6812MINI-E
(layer indicator); flags 2 `UNDERGLOW` = chain 14-23 = LED15-24 SK6812-SIDE side-fire. The
per-key/underglow classification matches which physical LED is which, part-family for part-family.

**Per-key LED↔switch spatial association verified:** every LEDn sits at the same x as SWn and 4.000
mm south of it (e.g. SW1 (13.525, 31.700) / LED1 (13.525, 35.700); SW13 (42.100, 88.850) /
LED13 (42.100, 92.850)), and the `matrix` tag on each per-key entry resolves to that same switch's
GPIO (see the pin table below). Reactive per-key effects will light the key that was actually pressed.

**SKU count:** firmware is hard-coded to 24 (`RGB_MATRIX_LED_COUNT 24` generated,
`LOUDEST_LED_COUNT 24` in `loudest_micro.h`) with **no SKU awareness**. Per this ledger (§ JS1 entry,
CPL 90 opaque / 110 translucent; *"opaque!=translucent only on the pre-existing populate-per-variant
rows (LED15-24, C40-49)"*), the opaque SKU populates **LED1-14 only**. This is **benign on the wire**
— LED1-14 latch pixels 0-13 and the remaining 10 pixels clock out of LED14's DOUT into an
unpopulated pad. Residual is cosmetic/protocol: `CAPS.led_count` reports 24 on an opaque board, so
`loudestd` may address 14-23 to no visible effect (finding 4).

### Task 3 — pin/net cross-check: **20/20 GPIO correct.** It is DIRECT-PIN, not a scanned matrix

`DIRECT_PINS` is generated as
`{ {GP12,GP9,GP5,GP2}, {GP11,GP8,GP4,GP1}, {GP10,GP7,GP3,GP0}, {GP6,GP15,GP16,NO_PIN} }` —
13 switches on 13 dedicated GPIO, **no diodes, no row/col scan**. RP2040 pad→GPIO numbering was
confirmed from the board's own auto-named nets (`unconnected-(U1-GPIO22-Pad34)`,
`…GPIO25-Pad37`, `…GPIO29_ADC3-Pad41`), not assumed.

| fw pin | fw role | U1 pad | board net | match |
|---|---|---|---|---|
| GP12 / GP9 / GP5 / GP2 | matrix row 0 | 15 / 12 / 7 / 4 | SW1 / SW2 / SW3 / SW4 | ✓ |
| GP11 / GP8 / GP4 / GP1 | matrix row 1 | 14 / 11 / 6 / 3 | SW5 / SW6 / SW7 / SW8 | ✓ |
| GP10 / GP7 / GP3 / GP0 | matrix row 2 | 13 / 9 / 5 / 2 | SW9 / SW10 / SW11 / SW12 | ✓ |
| GP6 | matrix [3,0] SW13 2U | 8 | SW13 | ✓ |
| GP15 | matrix [3,1] encoder push | 18 | ENC_SW | ✓ |
| GP16 | matrix [3,2] touch | 27 | TOUCH_OUT | pin ✓ / **POLARITY ✗ — finding 1** |
| GP13 / GP14 | encoder A / B | 16 / 17 | ENC_A / ENC_B | ✓ |
| GP17 | ws2812 DI | 28 | RGB_MCU | ✓ |
| GP26 | joystick X (ADC0) | 38 | JOY_X_ADC | ✓ |
| GP27 | joystick Y (ADC1) | 39 | JOY_Y_ADC | ✓ |

Corroborating chains: `RGB_MCU` → U5 `SN74LVC1T45` pad3 (A), DIR (pad5) = **+3V3 = high → A→B**,
VCCB (pad6) = +5V, out pad4 = `RGB_D00` — level-shift direction is **correct**. Joystick wipers are
`JS1.2`→R11 1k→`JOY_X_ADC`+C23 100n→GND and `JS1.5`→R12 1k→`JOY_Y_ADC`+C24 100n→GND (fc ≈ 1.6 kHz
anti-alias RC; the net rename across the resistor is the only reason the two names differ).
`BOOTSEL` (SW14 + R6 1k to QSPI_CS) and `RUN` (SW15 + R7 10k) are stock RP2040 and are not referenced
by firmware. No firmware-named GPIO is missing, mis-assigned, or doubled.

### FINDING 1 — **SHIPS-BROKEN.** Touch key GP16 polarity is inverted: board is active-HIGH, firmware assumes active-LOW

The board strap and the firmware documentation say opposite things, and **neither of the two
sanctioned fixes was ever applied.**

Board (netlist, this board file): `U6` TTP223 pad4 `TOUCH_AHLB` → **R10 (0R) → GND**; pad6 (TOG)
→ GND (direct/momentary). This ledger's own hardware review agrees in three independent places:

- `hardware/pcb/SCHEMATIC-REVIEW.md:156` — *"R10 0 Ω strap AHLB→GND (**active-high**); move to +3V3
  for active-low"*
- `hardware/pcb/loudest-micro/gen/build_loudest.py:323` — *"AHLB strap=GND (**active-high**); move to
  +3V3 for active-low"*
- `hardware/pcb/loudest-micro/gen/bom_gen.py:41` — *"0R AHLB strap (**GND=active-high**), 0402"*

⇒ TTP223 output **idles LOW, drives HIGH on touch.**

Firmware claims the opposite and implements no compensation:

- `firmware/loudest_micro/config.h:21-23` — *"The PCB straps the AHLB pad **active-low**, so the pad
  reads like a normal direct pin (**idle high, touched low**). If a batch ships without the strap,
  invert in the matrix read."*
- `firmware/loudest_micro/keyboard.json:32` — *"(GP16, PCB straps AHLB **active-low** so it reads
  like a normal direct pin)"*
- `MATRIX_INPUT_PRESSED_STATE` is **never defined** anywhere in the keyboard, keymaps, or generated
  config, so QMK's default applies (`quantum/matrix.c:50-51` → `0`), i.e.
  `readMatrixPin()` treats **LOW = pressed** and the pin is initialised `INPUT_PULLUP`.
- There is no custom matrix, no `matrix_scan_kb` override, no per-pin inversion anywhere in
  `loudest_micro.c`.

**Consequence on the default keymap.** GP16 idles LOW ⇒ QMK reads key `[3,2]` as **permanently
pressed**. `[3,2]` is the layer-cycle key (`TO(L_CTRL)` on layer 0, `TO(L_NAV)` on layer 1, …). The
TTP223 finishes its power-on calibration ~0.5 s after boot and drives its output low, which QMK sees
as a **press event** → `TO(L_CTRL)` fires. So:

1. **The pad boots into layer 1 (CTRL), never layer 0 (BASE).** The advertised F13–F24 macro layer
   is not what the user gets at power-on; they get JS_MODE/TP_TOG/RGB controls.
2. **The touch key triggers on finger LIFT, not on touch** (touch = HIGH = QMK "release", which does
   nothing; releasing = LOW = QMK "press", which fires the next `TO()`).
3. The layer indicator LED (chain 13) shows the wrong layer's hue from boot.

`TP_TOG` can suppress the key, but it lives on layer 1 and `touch_enabled` is a plain `static bool`
that resets on every power cycle.

**Root cause** — the design docs specified the choice and it was silently dropped on both sides:
`docs/independent-design/phase0-layout-notes.md:39` — *"⚠ default active-high momentary; **either**
strap TTP223 AHLB pad for active-low **or** invert in firmware"*. The board took neither branch
(strapped to GND = active-high), and the firmware then documented the *intent* (active-low) rather
than the *implementation*. `SCHEMATIC-REVIEW.md:156` ticked it ✓ because a strap **exists**, not
because it is on the correct rail. `docs/phase1-breadboard.md:38` had queued exactly this check —
*"test AHLB strap (active-low) and toggle mode; confirm QMK sees it as a plain key"* — as a
breadboard test, and that phase was never run. This is precisely the class of defect the skipped
behavioral gate existed to catch.

**NOT FIXED — coordinator/owner call, two legitimate options, both with real cost:**

- **(a) Firmware-only (recommended; boards are already fabbed).** Drop GP16 from `DIRECT_PINS`
  (`[3][2]` → `null`) and read GP16 explicitly with inverted sense, feeding the `[3,2]` matrix bit.
  Config + ~15 lines of C, one rebuild, no rework. Note `MATRIX_INPUT_PRESSED_STATE` is **global** —
  flipping it would invert all 15 keys and is NOT a valid fix.
- **(b) Hardware rework.** Move R10 (0402, B.Cu, at (32.000, 88.850)) from GND to +3V3 — U6 pad5
  (+3V3) is 5 mm away at (27.000, 88.850). Matches the existing firmware exactly, but is a per-board
  rework on every unit.

Either way `config.h:21` and `keyboard.json:32` must stop asserting "active-low"; they are wrong
about this board **today**.

### Task 4 — joystick calibration + polarity

**Calibration: placeholder is dimensionally CORRECT and cannot break input — it degrades feel, and
can silently kill two of the three joystick modes.**

Verified from the build tree rather than assumed: `platforms/chibios/drivers/analog.c:444-445` —
RP2040 samples 12-bit and returns `sample >> (12 - ADC_RESOLUTION)` with `ADC_RESOLUTION` defaulting
to 10 (`analog.c:125-131`) ⇒ **`analogReadPin()` returns 0..1023**. So `low 0 / rest 512 / high 1023` and
`JS_CENTER 512` are on the right scale. `quantum/joystick.c:93-114` uses them only as a linear
map into ±`JOYSTICK_MAX_VALUE` (= 511 at `JOYSTICK_AXIS_RESOLUTION 10`); both denominators
(`min-ref` = −512, `max-ref` = +511) are non-zero, so **no divide-by-zero, no crash, no lockup**.
A wrong calibration only mis-scales the HID axis.

**But** the custom arrow/scroll modes in `loudest_micro.c:205-206` use `JS_CENTER 512` ±
`JS_THRESHOLD 300`, i.e. they need the ADC to reach **≤212 or ≥812** to fire at all. A gimbal pot at
end-of-mechanical-travel commonly covers well under the full electrical track. If the assembled YA13
swings only e.g. 250..780, the native gamepad axis still works at ~52 % scale, but **JS_MODE_ARROWS
and JS_MODE_SCROLL never trigger** — two of the three joystick modes dead, with no error. The
bring-up ADC sweep must therefore capture the real end-stop values **and** `JS_THRESHOLD` must be
re-derived from them; recording only `low/rest/high` is not sufficient. (Finding 3.)

**Polarity: `POLARITY-NOTE.md` is CONSISTENT with this ledger and its recommended fix is CORRECT.**

The note's board facts match `V5-NOTES.md:310` verbatim in substance — *"Datum: VR1 body SOUTH, VR2
body EAST; our West+North clocking = exactly 180deg-from-datum … pot-N=VR1=Y, pot-W=VR2=X"* — and
`V5-NOTES.md:371-373` — *"The 180deg clocking INVERTS both axes' direction sense vs the datasheet
drawing; firmware should invert"*. Board file agrees: `JS1` at (69.710, 13.370) **rot 180**, F.Cu,
wiper = centre pin of each 3-group (pad2 → `JOY_X`, pad5 → `JOY_Y`). No spec-vs-ledger conflict.

The note's fix — swap `low` and `high` per reversed axis — was checked against the actual QMK math
(`joystick.c:99-107`) and **works**: with `low 1023 / rest 512 / high 0`, `ranged_val = -(v-512)`
on the lower branch and `((v-512)*511)/(0-512)` on the upper, giving a correctly inverted, correctly
scaled, non-degenerate axis (denominators +511 and −512). The note is also right that the custom
arrow/scroll path must be mirrored separately, since it reads `analogReadPin` directly and its
`want[]` comparisons are direction-bearing.

Two wording defects in that note, both cosmetic (findings 5, 6) — see below.

### Numbered defect list

| # | severity | defect |
|---|---|---|
| **1** | **ships-broken** | **GP16 touch polarity inverted.** Board straps TTP223 AHLB→GND = active-high (idle LOW); firmware documents active-low and defines no `MATRIX_INPUT_PRESSED_STATE` / no inversion. Key `[3,2]` reads permanently pressed; the pad boots into layer 1 instead of layer 0 and the touch key fires on finger-lift. Fix is a judgment call (firmware-only vs R10 rework) — **NOT applied.** |
| **2** | degrades | **Firmware provenance strings are stale/false.** `keyboard.json:2` and `config.h:2-3` still cite "Rev A (PCB v4_r27)" / "hardware/pcb/v4/ORDER-READINESS.md" as pin-map source of truth for a board that ships as v5_6, and `gen_led_layout.py:8-9` says "v4_r27 is the shipped Rev A board". The *values* are all correct for v5_6 (verified above), so this is documentation risk, not electrical risk — but it is exactly what makes a future executor re-verify against the wrong board. |
| **3** | degrades | **`JS_THRESHOLD 300` is unvalidated against the real YA13 travel.** If the assembled stick does not reach ≤212 / ≥812 on the 0..1023 ADC, the arrow and scroll modes are silently dead while gamepad mode still "works". Bring-up must sweep end-stops and re-derive the threshold, not just `low/rest/high`. |
| **4** | cosmetic | **No SKU awareness.** `LOUDEST_LED_COUNT`/`RGB_MATRIX_LED_COUNT` are hard-24 on both SKUs; the opaque board populates LED1-14. Harmless on the wire, but `CAPS.led_count` = 24 misinforms `loudestd` on opaque units. |
| **5** | cosmetic | **`POLARITY-NOTE.md:8-9` TL;DR is self-contradicting** — *"one line per axis, **no rebuild** is shipped in this bundle"* reads as "no rebuild needed", while line 62 correctly says *"Rebuild with the standard QMK/Vial flow"*. The intended meaning is "no pre-rebuilt UF2 is included". A polarity flip **is** compile-time and **does** require a toolchain + reflash. |
| **6** | cosmetic | **`POLARITY-NOTE.md:15` cites the vial prebuilt md5 as `e5008942…` as if it were reproducible.** The vial build is **non-deterministic run-to-run** (proved: two builds of byte-identical sources → `cd246307…` and `d7c2e8fa…`, 7 bytes apart, same 104448 size). The default UF2 *is* reproducible (`4af788ae…`, confirmed). Quoting a vial md5 as a verification target will fail for anyone who rebuilds. |
| **7** | cosmetic | **RGB matrix coordinate space is anisotropic by 4.16:1.** The board is portrait (84.2 × 100.0 mm) but QMK's space is 224 × 64, and `gen_led_layout.py` normalises each axis independently (x 2.660 units/mm, y 0.640 units/mm). This is QMK's own convention and is not a bug, but on a portrait board the distortion is severe: of the 10 enabled animations, the 4 geometry-bearing ones (`cycle_pinwheel`, `cycle_spiral`, `dual_beacon`, `rainbow_moving_chevron`) will render visibly skewed. Axis-aligned ones are unaffected. |

Cross-checked and found **correct**, for the record: LED chain order; all 24 LED coordinates; LED
flags vs part family; per-key LED↔switch pairing; all 20 GPIO assignments; level-shifter direction;
joystick RC + wiper nets; `button_count: 0` (the YA13 non-click variant is the one on the BOM);
`LAYOUT` 15 keys vs `keymaps[]` 15 entries vs 4×4 matrix with `[3,3]` null; F1 750 mA polyfuse vs
the `max_brightness 105` budget arithmetic.

### Untestable without hardware (explicitly NOT claimed either way)

- Encoder **detent direction** (whether ENC_A/ENC_B produce CW=volume-up) and whether the fitted EC11
  is 4-pulse/detent — `keyboard.json` sets no `resolution`, so QMK's default is used. Already on the
  hardware-arrival list at `firmware/FIRMWARE-V4-NOTES.md:326`.
- Real joystick `low/rest/high` and the resulting `JS_THRESHOLD` (finding 3).
- Whether the touch pad actually senses through the case window at the chosen thickness, and TTP223
  sensitivity tuning via the DNP `C25`.
- USB enumeration, Raw-HID round-trip with `loudestd`, the VIA-shadow dispatch rules in
  `loudest_micro.c:146-175`, and actual RGB current draw vs the 750 mA polyfuse.
- Confirmation of finding 1's observable symptom (boots to layer 1) — the reasoning is from the
  netlist, the TTP223 strap, and QMK's matrix source, all quoted above, but it has not been observed
  on silicon. It is falsifiable in ~10 seconds on the first assembled board: plug in and read the
  layer-indicator LED.

### Deliberate non-actions

- **No fix applied to finding 1** — it has two legitimate remedies with different cost profiles
  (firmware rebuild vs per-board 0402 rework); choosing between them is a coordinator/owner call, and
  the brief is report-first.
- **No firmware source edited**, including the stale-provenance strings (finding 2) and the
  `POLARITY-NOTE.md` wording (findings 5, 6) — those are unambiguous, but they sit in the release
  bundle, which this pass is barred from touching.
- **No board, schematic, netlist, fabpack, case or release-bundle mutation.** No banked tree touched.
- The prior wave's scratch build tree (`~/.claude/jobs/8b1a462c/…/vial-qmk`) was used to build and
  then **restored byte-identical**; `.build/` and the emitted UF2s were removed from it. Built
  artifacts and logs were kept only in this session's scratchpad.
- **No push, no upload, no spending, no git commit.**

**ORDER HOLD STANDS** — and finding 1 is now a first-power-on item, not a bring-up nicety.
---

## FIRMWARE FIX — defect 1 (TTP223 touch polarity) CLOSED, firmware-only (2026-08-13, firmware-fix executor)

**Board md5 `221ebb98fcf44f860ed65f7ed8d1bc45` asserted at start AND at close, on all three copies**
(`v5/hardware/pcb/v5_6.kicad_pcb`, `v5-release-compiled/hardware/pcb/v5_6.kicad_pcb`,
`v5-release-compiled/hardware/pcb/fabpack_out_v5_6/source.kicad_pcb`) — **UNCHANGED.** Zero board,
schematic, netlist, fabpack, plate, case or banked-tree mutation. No git commit, no push, no upload,
no spending. This entry closes the previous pass's **finding 1 (ships-broken)** and, as fallout of
having to rewrite the affected text, findings **5** and **6**.

Coordinator directive that forced the branch: **boards are ordered AND POPULATED**, so option (b) of
the previous entry — move `R10` from GND to +3V3 — is off the table. Option (a), firmware-only, is
the one implemented.

### 1. Defect re-verified independently from the board file (not taken on trust)

Parsed `v5/hardware/pcb/v5_6.kicad_pcb` directly (footprint blocks → pad → net):

```
R10  R_0402_1005Metric  value "0R"     pad 1 -> net 72 "TOUCH_AHLB"   pad 2 -> net 13 "GND"
U6   SOT-23-6 (TTP223)                 pad -> net 73 "TOUCH_OUT", net 74 "TOUCH_PAD", net 72 "TOUCH_AHLB"
U1   QFN-56 (RP2040)  pad "27"         -> net 73 "TOUCH_OUT"          (pad 27 = GPIO16)
C25  C_0402_1005Metric value "DNP"     pad 1 -> net 74 "TOUCH_PAD"    pad 2 -> net 13 "GND"
TP5  TestPoint_Pad_D1.5mm "TOUCHPAD"   pad 1 -> net 74 "TOUCH_PAD"
```

`TOUCH_OUT` has exactly **two** nodes (U6 → U1 pad 27) — **no external pull resistor**, so the pin's
idle level is whatever the TTP223 drives. `TOUCH_AHLB` → 0 Ω → `GND` ⇒ **active-HIGH**: Q idles LOW,
HIGH while touched. Matches `SCHEMATIC-REVIEW.md:156` (*"R10 0 Ω strap AHLB→GND (active-high); move
to +3V3 for active-low"*) and `BOM-FINAL.csv:25` (*"AHLB strap (GND=active-high)"*). Confirmed a
third time that `MATRIX_INPUT_PRESSED_STATE` appears in **no** `#define` and **no** config key
anywhere in the keyboard tree — only in prose that explains why it must not be used.

### 2. The fix — shape, and why this shape

**`MATRIX_INPUT_PRESSED_STATE 1` was rejected**, per the brief and per source: vial-qmk
`quantum/matrix.c` `readMatrixPin()` (`return (gpio_read_pin(pin) == MATRIX_INPUT_PRESSED_STATE) ? 0
: 1;`) is used by `matrix_read_cols_on_row()` for **every** direct pin, so setting it would invert
the 13 genuinely active-low switch-to-GND keys — thirteen broken keys to fix one.

Implementation (5 source lines of logic + 2 hooks, everything else comment):

| file | change |
|---|---|
| `firmware/loudest_micro/keyboard.json` | `matrix_pins.direct[3][2]` `"GP16"` → **`null`**. Matrix stays **4×4**; `LAYOUT` still carries `[3,2]`; both keymaps, `rgb_matrix.layout`, `layouts`, encoder, joystick, ws2812 untouched. `$matrix_comment` rewritten (it asserted active-low). |
| `firmware/loudest_micro/loudest_micro.c` | New `keyboard_pre_init_kb()` → `gpio_set_pin_input_low(GP16)` (pull-**down**: `matrix_init_pins()` no longer configures the pin, and an unpopulated/high-Z U6 must read *untouched* under an active-high strap). New `matrix_scan_kb()` → 3-variable debounce (5 ms, = QMK's default `DEBOUNCE`) over `gpio_read_pin(GP16) == 1`, emitting `action_exec(MAKE_KEYEVENT(3, 2, pressed))` on each debounced edge, then `matrix_scan_user()`. |
| `firmware/loudest_micro/config.h` | Touch block rewritten — it was the primary false statement (*"The PCB straps the AHLB pad active-low … idle high, touched low"*). |

Why `matrix_scan_kb()` and not `housekeeping_task_kb()`: `quantum/matrix.c:346` calls it once per
`matrix_scan()`, i.e. the touch input is sampled at **exactly the matrix cadence**, `matrix_can_read()`
is weak-`true` so it runs every loop, and the codebase already uses `_kb` hooks throughout
(`process_record_kb`, `housekeeping_task_kb`, `rgb_matrix_indicators_advanced_kb`). No
`CUSTOM_MATRIX`, no override of core matrix internals, no keyboard restructuring.

**Behavior preserved exactly:** `[3,2]` keeps its logical position, so both keymaps' `TO()` layer
chain and Vial's dynamic keymap at that position are unchanged; `TP_TOG` still gates it, because
`process_record_kb()` matches on `record->event.key.row/col` and `MAKE_KEYEVENT` carries those
verbatim. **One cost, ledgered:** Vial's matrix tester (`switch_matrix_state`) reads the scanned
`matrix[]`, so it can no longer light `[3,2]`.

Two secondary sources also encoded the wrong polarity and had to move or the gates would have been
asserting the defect:

- `firmware/tests/emulator/runner.cjs` — drove GP16 **high** with the switch lines and asserted a
  **pull-up** on it. Corrected to board truth (idle LOW; pull-**down** expected). Sensitivity proved
  both ways: the corrected runner **FAILs** the pre-fix binary `4af788ae…` (`pue=true pde=false`,
  plus the key-scan failure) and **PASSes** the new one.
- `firmware/tests/conformance/stubs/quantum.h` — host-side stubs; added `GP16`, `keypos_t/keyevent_t`,
  `MAKE_KEYEVENT`, `action_exec`, `gpio_read_pin` (returns 0 = untouched), `gpio_set_pin_input_low`,
  `timer_read/elapsed`, `keyboard_pre_init_user`, `matrix_scan_user`. Inert; no protocol behavior
  changed.
- `firmware/check_pins_v4.py` — `[3,2]` in `MATRIX_FUNCTIONS` is now `None` **by design**, and the
  GP16 assertion moved into a new `check_touch_outside_matrix()` (binds `TOUCH_PIN GP16`; declares
  `TOUCH_PRESSED_STATE 1`; injects at `[3,2]`; configures the pin itself; `MATRIX_INPUT_PRESSED_STATE`
  still undefined). Without this, dropping GP16 from the matrix would have looked like "touch removed".

**`firmware/sim/behavior.cjs` was NOT edited** — it is the referee. (Its `--touch=firmware` DIAGNOSIS
prose now reads backwards, since it was written for the pre-fix direction; left verbatim on purpose
and explained in `firmware/sim/README.md`.)

### 3. Build — both keymaps, SERIAL, Arm GNU Toolchain 15.2.Rel1

Toolchain exactly as the previous pass recorded: `qmk` CLI 1.2.0, `user.qmk_home` =
`~/.claude/jobs/8b1a462c/tmp/firmware-wave/vial-qmk` (branch `vial`, `00fc4627cd`, `via_command_kb`
backport present — 3 hits in `quantum/via.c`), `arm-none-eabi-gcc (Arm GNU Toolchain 15.2.Rel1 (Build
arm-15.86)) 15.2.1 20251203` from the bundled `arm-gnu-toolchain/` (Homebrew's 16.1.0 remains broken
here), **no `-j`** (macOS GNU Make 3.81 rejects `--output-sync=target`).

```
gcc: arm-none-eabi-gcc (Arm GNU Toolchain 15.2.Rel1 (Build arm-15.86)) 15.2.1 20251203
DEFAULT_RC=0
Compiling: platforms/chibios/vendors/RP/pico_sdk_shims.c                                            [OK]
Assembling: lib/pico-sdk/src/rp2_common/pico_divider/divider.S                                      [OK]
Assembling: lib/pico-sdk/src/rp2_common/pico_int64_ops/pico_int64_ops_aeabi.S                       [OK]
Linking: .build/loudest_micro_default.elf                                                           [OK]
Creating UF2 file for deployment: .build/loudest_micro_default.uf2                                  [OK]
Copying loudest_micro_default.uf2 to qmk_firmware folder                                            [OK]
-----
VIAL_RC=0
Compiling: keyboards/loudest_micro/loudest_micro.c                                                  [OK]
Linking: .build/loudest_micro_vial.elf                                                              [WARNINGS]
 |
 | lto-wrapper: warning: using serial compilation of 2 LTRANS jobs
 | lto-wrapper: note: see the '-flto' option documentation for more information
 |
Creating UF2 file for deployment: .build/loudest_micro_vial.uf2                                     [OK]
Copying loudest_micro_vial.uf2 to qmk_firmware folder                                               [OK]
```

**Zero code warnings in either build** (`-Werror` on). The vial `[WARNINGS]` is the LTO driver's
build-parallelism note (`lto-wrapper`), not a diagnostic about our code — the only two lines under it
are quoted above.

### 4. ACCEPTANCE GATE — `firmware/sim/behavior.cjs`, **33/33 under `--touch=board`**

Run against the shipped `firmware/prebuilt/*.uf2`, harness unmodified. **`--touch=board` is the real
hardware polarity and is the gate.**

```
agentpad13 behavioral sim — loudest_micro_default.uf2
loaded 173 UF2 blocks
touch model: BOARD TRUTH — TTP223 AHLB->GND (R10) = active-high, GP16 idles LOW

0. boot + USB enumeration
Write to invalid SIO address: 50, value=c
  [ok] USB configured
  ..   interfaces: #0 cls3/proto1 in1  #1 cls3/proto0 in2/out3
  [ok] ws2812 DMA source buffer located
  ..   pixel buffer @ 0x200020c0 (24 x uint32, GRB in bits 31:8)
  [ok] pixel words carry GRB<<8 (low byte always 0)

0b. boot layer — the layer indicator must say layer 0 (BASE)
  ..   layer indicator (chain 13) at boot: 31,0,0
  [ok] device booted into layer 0 (indicator is pure red, hue 0)

0c. blast radius — SW1 at the as-booted layer must still be KC_F13
  [ok] SW1 emits KC_F13 (0x68) from the as-booted layer

0d. touch polarity — the layer must advance ON TOUCH, not on release
  ..   layer indicator: rest 31,0,0 -> touched 31,23,0 -> released 31,23,0
  [ok] the layer advances while the pad is TOUCHED
  [ok] the layer does NOT advance again when the finger LIFTS
  [ok] touch sends no USB key report (TO() is a layer move)

1. LED chain — 24 positions, one unique color each (raw HID SET_KEY)
  [ok] all 24 chain positions independently addressable
  ..   0-12 per-key: 10,100,200  13,98,195  16,96,190  19,94,185  22,92,180  25,90,175  28,88,170  31,86,165  34,84,160  37,82,155  40,80,150  43,78,145  46,76,140
  ..   13 indicator: 49,74,135
  ..   14-23 underglow: 52,72,130  55,70,125  58,68,120  61,66,115  64,64,110  67,62,105  70,60,100  73,58,95  76,56,90  79,54,85
  [ok] repainting LED 9 alone moves only LED 9
  [ok] LED 9 took the exact requested color 254,2,127

2. CLEAR releases the chain back to the on-device animation
  [ok] no LED is still holding its host-set color
  [ok] chain is live (some LED is lit by the local animation)
  ..   layer-0 indicator (chain 13): 31,0,0
  [ok] layer-0 indicator is pure red (hue 0 = layer 0)

3. every switch — GPIO low -> the keycode the default keymap assigns
  [ok] GP12 SW1  [0,0] -> KC_F13 (0x68) then release
  [ok] GP 9 SW2  [0,1] -> KC_F14 (0x69) then release
  [ok] GP 5 SW3  [0,2] -> KC_F15 (0x6a) then release
  [ok] GP 2 SW4  [0,3] -> KC_F16 (0x6b) then release
  [ok] GP11 SW5  [1,0] -> KC_F17 (0x6c) then release
  [ok] GP 8 SW6  [1,1] -> KC_F18 (0x6d) then release
  [ok] GP 4 SW7  [1,2] -> KC_F19 (0x6e) then release
  [ok] GP 1 SW8  [1,3] -> KC_F20 (0x6f) then release
  [ok] GP10 SW9  [2,0] -> KC_F21 (0x70) then release
  [ok] GP 7 SW10 [2,1] -> KC_F22 (0x71) then release
  [ok] GP 3 SW11 [2,2] -> KC_F23 (0x72) then release
  [ok] GP 0 SW12 [2,3] -> KC_F24 (0x73) then release
  [ok] GP 6 SW13 [3,0] 2U hero -> KC_MPLY (consumer 0xcd)
  [ok] GP15 ENC_SW [3,1] push -> KC_MUTE (consumer 0xe2)

4. EC11 encoder — quadrature on GP13/GP14, layer 0 maps to volume
  [ok] rotate CW -> KC_VOLU (consumer 0xe9)
  [ok] rotate CCW -> KC_VOLD (consumer 0xea)

5. analog joystick — ADC injection -> HID gamepad report (report id 0x07)
  ..   rest                   report (none)  axes=n/a
  ..   ADC0 high / ADC1 low   report 071afee801  axes=-486,488
  ..   ADC0 low / ADC1 high   report 07e8011afe  axes=488,-486
  [ok] joystick emits HID gamepad reports at all
  [ok] both axes swing to near full scale on a full ADC sweep
  [ok] the two axes move independently (swapping the ADC inputs flips both signs)
  ..   ADC channels the emulator serviced: [1,0] — see README "Untrusted":
  ..   axis IDENTITY (which report slot is X) is NOT decided by this run.

touch model: board   checks: 33   failures: 0
BEHAVIOR SIM: PASS
```

(`Write to invalid SIO address: 50, value=c` is pre-existing rp2040js noise — an unimplemented
`SIO.FIFO_ST` write — present verbatim in **every** run of this harness including the pre-fix
baselines; it is emulator log output, not a verdict.)

`loudest_micro_vial.uf2 --touch=board`: identical 33/33 (204 UF2 blocks, pixel buffer `0x20000e64`
— which is why the harness discovers the buffer at runtime):

```
touch model: board   checks: 33   failures: 0
BEHAVIOR SIM: PASS
```

**No regression:** all 13 switches, all 24 LED chain positions (byte-exact + isolation), the encoder
(both directions), the joystick (both axes, independence) and the raw-HID/LED-CLEAR paths are inside
those 33 and all pass.

**The other A/B arm, `--touch=firmware`, now FAILS 4 — and that is the correct result.** It models
the polarity the firmware *used to* assume, which describes no board that exists. The A/B inverted
cleanly, which is the proof that the harness still discriminates:

```
touch model: FIRMWARE ASSUMPTION — config.h:21 "idle high, touched low", GP16 idles HIGH
  [FAIL] device booted into layer 0 (indicator is pure red, hue 0)  <- 31,23,0
  [FAIL] SW1 emits KC_F13 (0x68) from the as-booted layer  <- no keyboard report at all
  [FAIL] the layer advances while the pad is TOUCHED  <- still 31,23,0 while touched
  [FAIL] the layer does NOT advance again when the finger LIFTS  <- touched 31,23,0 -> released 15,31,0
touch model: firmware   checks: 33   failures: 4
BEHAVIOR SIM: FAIL
```

(identical 4 failures on the vial build). Full matrix, before and after:

| build | `--touch=board` **(the gate)** | `--touch=firmware` (counterfactual) |
|---|---|---|
| default **before** (`4af788ae…`) | 33 checks, **4 failures** — FAIL | 33 checks, 0 failures — PASS |
| vial **before** (`e5008942…`) | 33 checks, **4 failures** — FAIL | 33 checks, 0 failures — PASS |
| default **after** (`cf5bd628…`) | 33 checks, **0 failures — PASS** | 33 checks, 4 failures — FAIL |
| vial **after** (`b31673a7…`) | 33 checks, **0 failures — PASS** | 33 checks, 4 failures — FAIL |

The pre-fix rows were re-measured on this host at the start of this pass, not quoted from the sim
README.

### 5. No-regression gates (all re-run after the change)

| gate | result |
|---|---|
| `check_pins_v4.py` (bare) | **PASS 30/30** |
| `check_pins_v4.py --qmk-info --qmk-home` | **PASS 56/56** (incl. the resolved build config and the `via_command_kb` backport) |
| `tests/conformance/run_conformance.py` | **PASS 80/80** protocol-v0 checks vs `daemon/loudestd/protocol.py` |
| `qmk lint -kb loudest_micro -km default --strict` | `Ψ Lint check passed!` |
| `tests/emulator` `smoke:default` / `smoke:vial` | **EMULATOR SMOKE: PASS** both (incl. the new `GP16 (TOUCH_OUT): SIO input, pull-DOWN` verdict, `key scan: GP12 low -> F13`, raw-HID CAPS byte-exact) |
| MANIFEST self-verification | **9/9** (below) |

### 6. Artifacts — UF2 hash changes (SHIPPED ARTIFACTS MOVED)

| file | was (Rev A) | now | bytes |
|---|---|---|---|
| `firmware/prebuilt/loudest_micro_default.uf2` | md5 `4af788ae28cc7f368607e69a270c18ad`<br>sha256 `49642d69a53aef4308cb03a1d3e1b3c73c18d54946c6350adecfca47202ce39a` | md5 **`cf5bd62853ea591b39a1ce7246848229`**<br>sha256 **`35f34ea4f229eb65f0b3d9ad8d9cc0444a399af2c5943a25c06131d58b0f2ad3`** | 88064 → **88576** (+512 = one UF2 block, 172 → 173) |
| `firmware/prebuilt/loudest_micro_vial.uf2` | md5 `e5008942fd64597e0271b58241226a4a`<br>sha256 `5d33fffc57807bfdda263f36f919139e157b6b3cadccc0edc3fb06601f948fd0` | md5 **`b31673a7ba6a6219a0d5a3b9aee52e42`**<br>sha256 **`7056e6ad0ebe9673f077f69fb6d32873fbcf0cdd233e78d163ef940254f814c5`** | 104448 → 104448 (unchanged) |

The **default** build reproduces byte-for-byte; the **vial** build remains **non-deterministic
run-to-run** (previous pass proved it: two builds of byte-identical sources 7 bytes apart), so its
md5 records the shipped bytes and is **not** a rebuild target. Both facts are now written into
`POLARITY-NOTE.md`, `FIRMWARE-V4-NOTES.md §5` and the MANIFEST rows, which closes findings **5** and
**6** of the previous entry as a side effect (the note's *"no rebuild is shipped"* TL;DR and its
citation of the vial md5 as reproducible both had to be rewritten because they became false).

`firmware/FIRMWARE-V4-NOTES.md §5` table re-hashed + a superseded-artifacts block appended (the old
pair is preserved, not deleted); its §"known limitations" item 4 now marks the **AHLB strap polarity
item CLOSED from the board file**, leaving only the genuinely-hardware questions (does the pad sense
through the case, `C25` tuning, false triggering).

### 7. Release bundle — `v5-release-compiled/`

- `firmware/prebuilt/*.uf2` replaced with the fixed builds (md5s above).
- `firmware/POLARITY-NOTE.md` re-synced from the working tree — `e03f1a547adc7609d0b5c19c33bfc592` /
  3432 B → **`38895cdcbf27b60d899554241789880c`** / 4133 B. Both copies remain byte-identical.
- `RELEASE.md` — new **Revision 2026-08-13** block, new **diff row J**, section (a) retitled A–G →
  **A–J**, and the Version cross-map firmware row re-hashed (`4af788ae…`/`e5008942…` →
  `cf5bd628…`/`b31673a7…`, "UNCHANGED from Rev A" → "REBUILT 2026-08-13"). `a434d0feefb6ca6c459e30a6be2ccbef` /
  22102 B → **`ad6309a35311ad94ad89614bdb12e1da`** / 25890 B.
- `MANIFEST.md` — 4 rows re-hashed (`RELEASE.md`, `firmware/POLARITY-NOTE.md`, both UF2s) with
  provenance naming the fix and its gate; **Stats bytes 42141873 → 42146874** (+5001 = +512 UF2
  +701 POLARITY-NOTE +3788 RELEASE). **File count unchanged at 129** — no file added or removed.
- Everything else in the bundle is untouched: board, fabpack (all 26 artifacts), plate set, case
  model/STLs/STEP, keycaps, renders, `HOW-TO-ORDER.md`.

**MANIFEST self-verification VERBATIM (same 9-check split as 2026-08-05):**

```
[PASS] 1 existence          129/129 listed files present
[PASS] 2 md5                129/129 md5 match
[PASS] 3 bytes              129/129 byte counts match
[PASS] 4 no-orphans         0 on-disk file(s) without a row
[PASS] 5 stats-count-rows   Stats 129 vs rows 129
[PASS] 6 stats-count-disk   Stats 129 vs on-disk 129
[PASS] 7 stats-bytes-rows   Stats 42146874 vs row-sum 42146874
[PASS] 8 stats-bytes-disk   Stats 42146874 vs on-disk-sum 42146874
[PASS] 9 self-exclusion     MANIFEST.md has no self-row
RESULT: 9/9 checks PASS
```

Baseline for comparison, same script, run BEFORE the bundle mutation: **6/9** — failures 2/3/8,
naming exactly the four files this pass changed and nothing else. That is the prediction register
satisfied: no unexpected artifact moved.

### 8. Stale-doc corrections

- **`docs/HANDOFF-STATE.md:328` (the Wokwi line) — CORRECTED.** It read *"Not done and never
  re-scoped: the Wokwi sim of the real UF2, and the `kicad-happy:spice` run."* The emulator half was
  **stale when written**: `firmware/tests/emulator/` has existed since commit **`df76a9a`
  (2026-07-20)** — verified with `git ls-tree df76a9a` (`runner.cjs`, `get-bootrom.sh`,
  `package.json`, `package-lock.json`, `.gitignore`) — and it boots the real production `.uf2` in
  **rp2040js, which *is* Wokwi's own MIT-licensed RP2040 engine**, used directly rather than through
  Wokwi's cloud product (whose USB is CDC-only, so HID — the whole point for a keyboard — is
  unreachable). `firmware/sim/` now extends it to behavioral coverage and is what caught this defect.
  The line is struck through in place with a bracketed correction, house style; **the
  `kicad-happy:spice` half remains genuinely not done** and is left standing.
- **`docs/HANDOFF-STATE.md:119`** said the prebuilt UF2s are byte-identical to Rev A with the old
  md5s — false as of this pass; rewritten with the defect, the fix, the new hashes and the gate.
- **`firmware/BUILD.md`** — §5 pin table row 3 no longer claims GP16 is a matrix pin (footnote
  explains the strap, the global-knob trap and the `matrix_scan_kb()` handling); §9 gained the
  **build-serially-on-macOS** trap (Make 3.81 vs `--output-sync`), which until now lived only in the
  ledger.
- **`firmware/sim/README.md`** — the ⚠ banner (*"this harness fails on the shipped firmware"*), the
  four-way results table, the "Fixing it" section and the "has not been run against a fixed build"
  claim were all false post-fix; updated, with the defect section kept verbatim as a historical
  record and explicitly labelled as such. **`behavior.cjs` itself was not touched.**
- `v5/V5-NOTES.md:1783` and `:2138` quote the same stale Wokwi sentence inside dated historical
  entries; per append-only ledger discipline they are **left as written** — this entry is the
  correction of record.

### 9. Deliberate non-actions

- **No board / schematic / netlist / fabpack / plate / case / render mutation.** No banked tree
  touched (`v4-release-compiled`, `v5-discarded`, `fabpack_out*`, boards `v5`..`v5_5`) — their stale
  UF2 hashes are historical and correct for what they are.
- **`firmware/sim/behavior.cjs` unmodified** — editing the referee to pass its own gate would void
  the gate. Verified: the harness that failed the old binaries is byte-identical to the one that
  passed the new ones.
- **Findings 2, 3, 4, 7 of the previous entry NOT addressed** (stale "v4_r27" provenance strings;
  `JS_THRESHOLD 300` unvalidated against real YA13 travel; no SKU awareness in `LOUDEST_LED_COUNT`;
  anisotropic RGB coordinate space). All are out of this brief's scope; none is ships-broken.
- **Pre-existing latent issue observed, not changed:** `loudest_micro.c`'s `housekeeping_task_kb()`
  ends with `housekeeping_task_user()`, and vial-qmk's `housekeeping_task()`
  (`quantum/keyboard.c:433-436`) already calls `housekeeping_task_user()` itself — so it runs
  **twice** per loop. Harmless today (neither keymap defines it, so it is a weak no-op) and
  untouched, but it is a trap for anyone who later implements that hook in a keymap. The new
  `matrix_scan_kb()` deliberately does **not** repeat the pattern in a way that could double-fire:
  `matrix_scan_kb()`'s weak default is the only caller of `matrix_scan_user()`, so calling it there
  is correct.
- Scratch build tree (`~/.claude/jobs/8b1a462c/tmp/firmware-wave/vial-qmk/keyboards/loudest_micro`)
  was **left synced to the fixed working-tree sources**, with `.build/` and the emitted `.uf2`s
  removed — deliberately *not* restored to the stale pre-fix copy it was found in, because a
  build tree that silently rebuilds the ships-broken firmware is a landmine. The as-found copy is
  preserved reversibly in this session's scratchpad (`kb_backup_asfound/`, 11 files).
- **No git commit, no push, no upload, no spending.**

**ORDER HOLD STANDS.** Defect 1 is now a *closed* item rather than a first-power-on landmine — but
the falsifiable check survives and is cheap: plug in the first assembled board and read the layer
indicator. **Pure red (hue 0) = fixed.** Orange = the firmware on that unit predates 2026-08-13.

---

## BRING-UP CALIBRATION FACILITY — the ADC sweep gets a mechanism; finding **2** CLOSED (2026-08-13, firmware-calibrate executor)

**Board md5 `221ebb98fcf44f860ed65f7ed8d1bc45` asserted at start AND at close — UNCHANGED.** Zero board,
schematic, netlist, fabpack, plate, case, release-bundle or public-repo mutation. No git commit, no
push, no upload, no spending. Both SHIPPED prebuilts byte-identical at close (`cf5bd628…` /
`b31673a7…`). `firmware/sim/behavior.cjs` **not touched.**

(Session note: this work ran across the 2026-08-13 → 2026-08-15 wall-clock rollover. The brief
specified the correction stamp *"(2026-08-13)"* verbatim, and every in-source stamp written this pass
uses it, so this entry carries the same date rather than a third one.)

### Why this exists — the gap, stated plainly

`docs/HANDOFF-2026-08-06.md` §5 requires, on the first assembled board: *"Sweep the real ADC — and
**re-derive `JS_THRESHOLD` (300)**, not just the endpoints"*; *"If X or Y reads reversed …"*; *"Touch:
confirm the fix on real silicon."* `BUILD.md:256`, `FIRMWARE-V4-NOTES.md:319`, `POLARITY-NOTE.md:81`
and every `CALIBRATION-PENDING` marker name "the bring-up ADC sweep" — and **not one of them says
how.** There was no how: raw-HID protocol v0 is LOCKED and carries no ADC readout, and Vial exposes no
raw analog, so the numbers could not be got off the board at all.

Against the owner's standard (`docs/HANDOFF-STATE.md`) — *"AIM for this to be drag and drop ready. No
escape hatches… Act as the world's greatest systems integrator and PCB designer"* — an undocumented
"sweep the ADC" step **is** an escape hatch. The owner has no EE expertise; the deliverable had to be
executable by someone who can drag a UF2 onto a USB drive and use a text editor.

Resolution: the board is a keyboard, so it can **type its own calibration report**. New `calibrate`
keymap + new prebuilt UF2 + new referee + a §4a in `BUILD.md` written for a non-EE reader.

### 1. Base integrity, and the toolchain proved rather than assumed

`arm-none-eabi-gcc` on PATH resolves to `/opt/homebrew/bin/arm-none-eabi-gcc` = **GCC 16.2.0**, the
Homebrew formula `BUILD.md` §1.1 records as unusable (no newlib). The bundled Arm GNU Toolchain
15.2.Rel1 in the firmware-wave dir is the one that built the shipped artifacts and is what was used
here (serial, no `-j`, per §9). **The proof is not the version string, it is the bytes:**

| build | source state | md5 | verdict |
|---|---|---|---|
| `default`, before any edit | working tree as found | `cf5bd62853ea591b39a1ce7246848229` | **byte-identical to the shipped prebuilt** |
| `default`, after the Phase-1 comment edits | working tree + provenance fixes | `cf5bd62853ea591b39a1ce7246848229` | **still byte-identical — the edits were provably doc-only** |
| `default`, final re-sync | final working tree | `cf5bd62853ea591b39a1ce7246848229` | unchanged |

vial-qmk verified at `00fc4627cd038ac9b7e9b8bf2b40b50e9e88aecb` with the core patch applied
(`via_command_kb`: 3 hits in `quantum/via.c`, 1 in `via.h`), and `keyboards/loudest_micro` verified
byte-identical to `firmware/loudest_micro/` (`diff -r`, rc 0) before anything was built.

### 2. Finding **2** — stale provenance strings — CLOSED, and PROVEN doc-only

The previous pass's finding 2: *"`keyboard.json:2` and `config.h:2-3` still cite 'Rev A (PCB v4_r27)' /
'hardware/pcb/v4/ORDER-READINESS.md' as pin-map source of truth for a board that ships as v5_6, and
`gen_led_layout.py:8-9` says 'v4_r27 is the shipped Rev A board'."*

Corrected in **four** files, house style (state the current fact, keep a dated parenthetical naming
what the line used to claim; delete nothing):

| file | what now leads |
|---|---|
| `firmware/loudest_micro/keyboard.json` `$comment` | shipped board = `v5/hardware/pcb/v5_6.kicad_pcb` (md5 `221ebb98…`); pin map **unchanged from v4**, re-verified 20/20 GPIO against v5_6 (Task 3 above); `rgb_matrix.layout` re-derived against v5_6, **24/24, 0 mismatches** (Task 2 above); ORDER-READINESS.md Layer 4 named as the table it came from, which still describes v5_6 correctly |
| `firmware/loudest_micro/config.h` | same, in the header comment |
| `firmware/gen_led_layout.py` | docstring: run it against `v5_6.kicad_pcb`; the 24/24 re-derivation recorded |
| `firmware/BUILD.md` | header paragraph **and** the §5 heading + source-of-truth line (both carried the same false citation; fixing only the header would have left the pin-map section still pointing a verifier at a superseded board) |

**Constraint honored:** in `keyboard.json` only the `$`-prefixed comment key changed. Machine-proven,
not asserted — both revisions parsed, all `$`-keys stripped, deep-compared:

```
functional (non-$) content identical: True
keys added: set() | keys removed: set()
changed top-level keys: ['$comment']
```

In `config.h` / `gen_led_layout.py` / `BUILD.md` only comments, docstring and prose changed. **And the
`default` UF2 still hashes `cf5bd628…` afterwards** — that rebuild is the real proof.

`firmware/check_pins_v4.py` also carries "Rev A (board v4_r27)" in its header and its banner line. It
was **deliberately left alone**: it is a gate, its printed banner is part of the gate's verbatim
output, and it was not in this brief's four named files.

### 3. The `calibrate` keymap — `firmware/loudest_micro/keymaps/calibrate/`

**No shared firmware file was modified to build it.** `loudest_micro.c`, `loudest_micro.h`, `config.h`
and `keyboard.json` are untouched by Phase 2 (Phase 1's comment-only edits are the sole touches to the
latter two). The keymap is three new files: `keymap.c`, `rules.mk`, `readme.md`.

Wiring, each checked against the fork's own sources rather than assumed:

- **Every key is `KC_NO`** and dispatch is by `row`/`col` inside `process_record_user()`. So the
  firmware can never emit a stray character; the only bytes it ever sends come from `send_string()`.
  Verified reachable for `KC_NO`: `quantum/quantum.c:364` calls `process_record_kb(keycode, record)`
  for every keycode, and `loudest_micro.c`'s `process_record_kb()` falls through to
  `process_record_user()`.
- **Touch** needs nothing new: `loudest_micro.c`'s `matrix_scan_kb()` already injects
  `action_exec(MAKE_KEYEVENT(3, 2, pressed))`, so `[3,2]` arrives as an ordinary key event.
- **Encoder** uses `encoder_update_user()`, and `rules.mk` therefore **deliberately does not inherit
  `keymaps/default`'s `ENCODER_MAP_ENABLE = yes`**: `quantum/encoder.c:35-52` routes detents to
  `action_exec()` + `encoder_map[]` when the map is on and to `encoder_update_kb()` (→ `_user`) only
  when it is off. With the map enabled the callback would never fire and the encoder half of bring-up
  would have silently done nothing. This is the single build difference from `default`.
- **No custom keycodes were added.** `JS_MODE`/`TP_TOG` are keyboard-level (`QK_KB_0..`) in
  `loudest_micro.h`; extending that enum from a keymap would have meant editing a shared file, and
  matching on row/col makes it unnecessary.
- **All ADC reads and all typing happen in `housekeeping_task_user()`**, draining a 16-deep event
  queue — never nested inside the `action_exec()` that delivered the event. Note
  `housekeeping_task_user()` runs **twice** per loop on this keyboard (`quantum/keyboard.c:435-436`
  plus `loudest_micro.c`'s `housekeeping_task_kb()`; the pre-existing double-call ledgered in the
  previous entry). Draining a queue is idempotent under that — which is exactly why the queue exists.
  A queue overflow is **reported as a typed line**, never swallowed.
- The continuous min/max sweep runs in `matrix_scan_user()` — called exactly once per matrix scan.

### 4. The derivation rules the board applies (this is the engineering, not the plumbing)

All values in the firmware's 10-bit domain (`analogReadPin` → `sample >> (12 - ADC_RESOLUTION)`,
`ADC_RESOLUTION` 10 — `platforms/chibios/drivers/analog.c:444-445`), the same domain
`keyboard.json` `low/rest/high`, `JS_CENTER` and `JS_THRESHOLD` already use.

| quantity | rule | why |
|---|---|---|
| rest | mean of the first 16 samples of a 100-sample, 5 ms-spaced (≥500 ms) window | the mean is drawn from inside the same window as the noise band, so `min ≤ rest ≤ max` holds by construction and every half-swing below is non-negative |
| rest noise `+/-n` | largest deviation of that window from the rest mean | a threshold buried in the noise floor self-triggers |
| `inverted_y` | `y_up > y_rest` | `loudest_micro.c` fires UP on `y < JS_CENTER - JS_THRESHOLD`, so a correctly-sensed axis must **decrease** when pushed up |
| `inverted_x` | `x_right < x_rest` | it fires RIGHT on `x > JS_CENTER + JS_THRESHOLD` |
| `JS_CENTER` | `round((x_rest + y_rest) / 2)`, with a typed WARNING if the two rests differ by > 30 | the shipped code shares **one** `JS_CENTER` across both axes |
| `JS_THRESHOLD` | `floor(0.60 × min(x_rest−x_min, x_max−x_rest, y_rest−y_min, y_max−y_rest))` | every direction fires with 40 % of its half-swing still in reserve before the end-stop |
| guards | half-swing < 100 → `SWING TOO SMALL`; `T ≤ 3 × larger noise half-band` → `THRESHOLD INSIDE NOISE` | typed WARNINGs instead of silent garbage |
| shipped verdict | per direction, against the SHIPPED `512`/`300` | this is finding **3** answered per direction rather than as a single yes/no |
| typed JSON | `low`/`high` **already swapped** on any inverted axis | that swap *is* `POLARITY-NOTE.md` "The one-line fix"; the typed lines are final, so the owner never has to reason about polarity |

**DEVIATION FROM THE BRIEF, deliberate, reported.** The brief specified the verdict as *"X− fires iff
x_min ≤ 212, X+ fires iff x_max ≥ 812"*, inherited from this ledger's own prose at `:2325`
(*"they need the ADC to reach **≤212 or ≥812** to fire at all"*) and from
`docs/HANDOFF-2026-08-06.md:130`. **The code is strict:** `loudest_micro.c:322-325` reads
`want[0] = (y < JS_CENTER - JS_THRESHOLD)` and `want[3] = (x > JS_CENTER + JS_THRESHOLD)` — so a stick
that reaches *exactly* 212 or *exactly* 812 fires **nothing**. Implementing the brief literally would
print "fires" for a stick the shipped firmware will not respond to: the exact silent-lie class this
whole facility exists to prevent. The firmware, the typed line and the referee therefore all use the
**strict** form, and the typed line says so out loud:
`shipped JS_THRESHOLD 300 verdict (fires only below 212 or above 812): …`.

### 5. The referee — `firmware/sim/calibrate.cjs` (NEW file; `behavior.cjs` untouched)

Boots the real `loudest_micro_calibrate.uf2` in rp2040js, injects ADC values and GPIO edges, decodes
the typed HID stream back to ASCII (US layout, from the boot-keyboard interface `behavior.cjs`
already uses), and asserts the whole report **character for character** against expectations computed
**independently in JavaScript from this harness's own injections** — never against the firmware's
arithmetic. That independence is the point: a derivation bug would otherwise be confirmed by itself.

**A real emulator defect was found and is now worked around IN THE HARNESS, never in firmware —
workaround (f), new, on top of the five behavior.cjs already carries.** rp2040js never auto-clears
`ADC.CS.START_ONCE` (bit 2), which is self-clearing on real silicon. ChibiOS's RP ADC LLD sets the
channel with a **read-modify-write of `CS`** (`ADCv1/hal_adc_lld.c` `set_channel()`), so on the
unpatched emulator that RMW writes the stale `START_ONCE` back and kicks off a second, unwanted
conversion; the extra sample sits in the 4-deep ADC FIFO and **every `adcConvert()` then returns the
previous conversion's value** — a strict one-conversion lag. Measured on the unpatched emulator with
this firmware:

- alternating reads came back **swapped**: inject `ch0=800 / ch1=200` and the board typed
  `live X=200 Y=800`;
- 16 consecutive reads of one pin averaged in one foreign sample: inject `ch0=880 / ch1=140` and the
  16-sample average of GP26 came back **834** = exactly `(140 + 15×880 + 8) / 16`.

That second number is what identifies the fault as a **pipeline lag** and not a channel mix-up, and it
is why the lag cannot be cancelled by simply swapping the injection — its effect depends on the read
pattern. **This is a different mechanism from the one `firmware/sim/README.md` §"Untrusted" blames**
(the `adc.ts` `channel & CS_AINSEL_SHIFT` masking bug, rp2040js issue #141): that setter is only
reached from the hardware round-robin path, and the ChibiOS LLD never writes `CS.RROBIN` — it steps
channels in software. Both channels are serviced correctly here (`[0,1]`, printed every run). The
README's *conclusion* — that axis identity is not decided by a sim run — still stands, and the
pin↔axis binding remains proven statically by `check_pins_v4.py`, not by this harness.

The workaround is **switchable and audited**, in the spirit of `behavior.cjs`'s `--touch` A/B:

```
adc fix: on    checks: 37   failures: 0     CALIBRATE SIM: PASS
adc fix: OFF   checks: 37   failures: 15    CALIBRATE SIM: FAIL   (node calibrate.cjs --no-adc-fix)
```

The A/B inverts cleanly and **fails only on ADC-derived numbers**: boot silence, every prompt, touch
both edges, encoder both directions, encoder push, the no-op switch and the SW2 restart all still pass
with the workaround off. A workaround that cannot be switched off cannot be audited.

Scenarios (all four required by the brief, all PASS):

| # | scenario | what it pins down |
|---|---|---|
| 0 | harness self-check | boot silence; `live X=800 Y=200` then `live X=123 Y=987` read back exactly; both ADC channels serviced |
| 1 | nominal, rest ≈ (507, 514), dithered rest window (noise ±2/±2), swing 180..850 | `inverted=NO/NO`; `JS_CENTER 511`; `JS_THRESHOLD 196` (smallest half-swing 327); all four directions `fires`; exact JSON |
| 2 | inverted Y (`y_up > y_rest`) | `inverted=YES` on Y only; typed Y line has `low`/`high` **swapped**; X line untouched |
| 3 | reduced swing 250..780 | **all four directions `NEVER FIRES`** against the shipped 300; `JS_THRESHOLD` re-derived to 154 from the small swing, and re-checked to actually fire every direction |
| 4 | touch + encoder + restart + live | `TOUCH:DOWN`→`TOUCH:UP` in that order; `ENC:CW`/`ENC:CCW`/`ENC:PRESS`; an unassigned switch types **nothing**; SW2 restart re-runs a capture cleanly with no memory of the abandoned one; SW3 live matches mid-flow |

Two harness bugs were found and fixed before it was believed: the quiet-detector counted **all**
endpoints (QMK's joystick task writes a gamepad report on another endpoint whenever an axis moves),
and it returned during the deliberately silent 500 ms rest window, shifting every assertion one step
late. Both are commented at their site.

### 6. Gates — VERBATIM

```
node firmware/sim/behavior.cjs --touch=board                      (default)
  touch model: board   checks: 33   failures: 0
  BEHAVIOR SIM: PASS
node firmware/sim/behavior.cjs --touch=board ../prebuilt/loudest_micro_vial.uf2
  touch model: board   checks: 33   failures: 0
  BEHAVIOR SIM: PASS
node firmware/sim/behavior.cjs --touch=firmware                   (default AND vial)
  touch model: firmware   checks: 33   failures: 4
  BEHAVIOR SIM: FAIL            <- the A/B discrimination proof, unchanged
node firmware/sim/calibrate.cjs
  adc fix: on   checks: 37   failures: 0
  CALIBRATE SIM: PASS
node firmware/sim/calibrate.cjs --no-adc-fix
  adc fix: OFF   checks: 37   failures: 15
  CALIBRATE SIM: FAIL           <- required
python3 firmware/check_pins_v4.py
  PASS: all 30 pin-map checks against the ORDER-READINESS Layer 4 table succeeded
python3 firmware/check_pins_v4.py --qmk-info … --qmk-home …
  PASS: all 56 pin-map checks against the ORDER-READINESS Layer 4 table succeeded
python3 firmware/tests/conformance/run_conformance.py
  PASS: all 80 protocol-v0 conformance checks passed (firmware C handler vs daemon/loudestd/protocol.py oracle)
qmk lint -kb loudest_micro -km default   --strict   ->  Ψ Lint check passed!
qmk lint -kb loudest_micro -km calibrate --strict   ->  Ψ Lint check passed!
qmk lint -kb loudest_micro -km vial      --strict   ->  ☒ loudest_micro: The keymap vial should not exist!
npm run smoke:default  ->  EMULATOR SMOKE: PASS
npm run smoke:vial     ->  EMULATOR SMOKE: PASS
md5 firmware/prebuilt/loudest_micro_default.uf2 = cf5bd62853ea591b39a1ce7246848229   (UNCHANGED)
md5 firmware/prebuilt/loudest_micro_vial.uf2    = b31673a7ba6a6219a0d5a3b9aee52e42   (UNCHANGED)
```

**Denominators are unchanged** — 30/30, 56/56, 80/80, 33/33 — the new keymap moved no gate's
arithmetic. One printed *detail* moved inside a passing check: `check_pins_v4.py`'s source-pin scan
now lists `['GP12','GP15','GP16','GP26','GP27','GP5','GP9']` where it listed `['GP16','GP26','GP27']`
(re-measured on a pristine `git archive HEAD` tree to be sure). The four added pins are named in
`keymaps/calibrate/keymap.c`, which documents which GPIO backs SW1/SW2/SW3 and the encoder push; all
four are table-assigned, so the check — *"sources reference only table-assigned pins"* — still passes,
and no denominator changed.

**`qmk lint -km vial` is the one non-green line, it is PRE-EXISTING, and the brief was wrong to expect
it clean.** `firmware/BUILD.md` §3.1, written long before this pass: *"`qmk lint -km vial` prints
**"The keymap vial should not exist!"** — this is a mainline-QMK lint rule (`INVALID_KM_NAMES =
['via', 'vial']`) that every Vial keyboard trips. It is a false positive here."* The previous entry's
gate table likewise records only `-km default --strict` as the standing gate. `keymaps/vial/` is
byte-identical to `HEAD` (`git status` clean for that path), so nothing this pass did caused it.

### 7. Artifacts

| file | status | md5 | bytes |
|---|---|---|---|
| `firmware/prebuilt/loudest_micro_calibrate.uf2` | **NEW** | `a81ce4a137e667d73e3cd9da5c82a98a`<br>sha256 `7230a4de95851909f78893def51d49bcda68ff34670934495eabf760a31a61e7` | 96768 |
| `firmware/prebuilt/loudest_micro_default.uf2` | untouched | `cf5bd62853ea591b39a1ce7246848229` | 88576 |
| `firmware/prebuilt/loudest_micro_vial.uf2` | untouched | `b31673a7ba6a6219a0d5a3b9aee52e42` | 104448 |

The calibrate build is **byte-for-byte reproducible**, like `default` and unlike `vial`: two builds
from a clean `.build/` produced identical bytes, and a third from the final re-synced tree matched
again. `a81ce4a1…` is therefore a **rebuild target**, not merely a record of shipped bytes.

Zero code warnings under `-Werror` (`-Wall -Wstrict-prototypes -Werror`); the string `WARNINGS` does
not appear anywhere in the build log.

Files added: `firmware/loudest_micro/keymaps/calibrate/{keymap.c,rules.mk,readme.md}`,
`firmware/sim/calibrate.cjs`, `firmware/prebuilt/loudest_micro_calibrate.uf2`.
Files edited: `firmware/loudest_micro/keyboard.json` (`$comment` only), `firmware/loudest_micro/config.h`
(comment only), `firmware/gen_led_layout.py` (docstring only), `firmware/BUILD.md` (provenance + new
§4a + §8 cross-reference), `firmware/POLARITY-NOTE.md` (one "Related watch-item" pointer),
`firmware/sim/README.md` (one Files-table row, so the new harness is discoverable).

### 8. Deliberate non-actions

- **`firmware/sim/behavior.cjs` NOT modified.** Editing the referee to accommodate a new artifact
  would void the gate; `calibrate.cjs` is a separate file that reuses its *techniques*, not its bytes.
- **Both shipped prebuilts NOT rebuilt or replaced.** Their md5s are asserted unchanged above.
- **`v5-release-compiled/` NOT synced.** The bundle has no calibrate UF2, no §4a and the old
  `POLARITY-NOTE.md`; whether a bring-up tool belongs in the release bundle (and the MANIFEST
  re-hash + file-count change that follows) is a **coordinator/owner decision**, not an executor's.
  Same for the public `agentpad13` mirror.
- **Findings 4 and 7 of the verification pass NOT addressed.** Finding 4 (no SKU awareness:
  `LOUDEST_LED_COUNT` hard-24 while the opaque SKU populates LED1-14) would change the CAPS byte on
  the wire, and protocol v0 is **LOCKED** — that is a protocol decision, and it is out of this brief.
  Finding 7 (RGB coordinate space anisotropic 4.16:1) is QMK's own convention, cosmetic, and would
  mean re-authoring `rgb_matrix.layout` — also out of scope. Both remain open, both non-blocking.
- **`firmware/check_pins_v4.py` header/banner left stale** ("Rev A (board v4_r27)") — it is a gate
  whose printed output is quoted verbatim in these ledgers, and it was not among the brief's four
  named files. Flagged, not changed.
- **Newly observed, NOT changed, both stale-doc items of finding-2's class:**
  `docs/HANDOFF-STATE.md:224` still says the main PCB is *"❌ NOT ordered. Order hold in force"*, which
  the coordinator directive at `:2406` above (*"boards are ordered AND POPULATED"*) supersedes; and
  `firmware/sim/package.json`'s description still asserts *"the default --touch=board model FAILS on
  the current firmware by design"*, which the 2026-08-13 touch fix made false (the README half of that
  correction was done; the package.json half was missed).
- Scratch build tree (`~/.claude/jobs/8b1a462c/tmp/firmware-wave/vial-qmk`) left **synced to the final
  working-tree sources**, `.build/` and all emitted `.uf2`s removed, only the core patch modified —
  same disposition as the previous entry, for the same reason.
- **No git commit, no push, no upload, no spending, no remote.**

**ORDER HOLD STANDS.** The three bring-up items from `HANDOFF-2026-08-06.md` §5 are no longer
instructions without a mechanism: flash one UF2, open a text editor, press one key four times.

---

## FIRMWARE PERFECTION PASS — finding **7** closed in code, finding **4** closed by decision, the double `housekeeping_task_user()` trap removed (2026-08-15, firmware-wave2 executor)

**Board md5 `221ebb98fcf44f860ed65f7ed8d1bc45` asserted at start AND at close — UNCHANGED.** Zero
board, schematic, netlist, fabpack, plate, case, release-bundle or public-repo mutation. No git
operation of any kind — no commit, no push, no remote, no upload, no spending.
`firmware/sim/behavior.cjs` **not touched.** All three prebuilts REBUILT and replaced.

### 0. Base integrity, and the baseline reproduced BEFORE anything was edited

| artifact | expected | measured | verdict |
|---|---|---|---|
| `firmware/prebuilt/loudest_micro_default.uf2` | `cf5bd62853ea591b39a1ce7246848229` / 88576 | same | ✓ |
| `firmware/prebuilt/loudest_micro_vial.uf2` | `b31673a7ba6a6219a0d5a3b9aee52e42` / 104448 | same | ✓ |
| `firmware/prebuilt/loudest_micro_calibrate.uf2` | `a81ce4a137e667d73e3cd9da5c82a98a` / 96768 | same | ✓ |
| `v5/hardware/pcb/v5_6.kicad_pcb` | `221ebb98fcf44f860ed65f7ed8d1bc45` | same | ✓ |

Then, from the **untouched** tree, `default` was rebuilt and reproduced **byte-for-byte**:
`md5=cf5bd62853ea591b39a1ce7246848229 bytes=88576`. Only after that did the first edit happen.
vial-qmk verified at `00fc4627cd038ac9b7e9b8bf2b40b50e9e88aecb` with only the `via_command_kb`
backport modified (`M quantum/via.c`, `M quantum/via.h`), `keyboards/loudest_micro` proved
byte-identical to `firmware/loudest_micro/` by `diff -r` (rc 0) before and after. Toolchain:
`arm-none-eabi-gcc (Arm GNU Toolchain 15.2.Rel1 (Build arm-15.86)) 15.2.1 20251203` from the bundled
`arm-gnu-toolchain/` put FIRST on PATH (Homebrew's gcc 16 remains the documented-broken one), serial
builds, no `-j`.

### 1. Change A — finding **7** CLOSED: the RGB coordinate space is now ISOTROPIC

The finding, verbatim: *"The board is portrait (84.2 × 100.0 mm) but QMK's space is 224 × 64, and
`gen_led_layout.py` normalises each axis independently (x 2.660 units/mm, y 0.640 units/mm)... of the
10 enabled animations, the 4 geometry-bearing ones (`cycle_pinwheel`, `cycle_spiral`, `dual_beacon`,
`rainbow_moving_chevron`) will render visibly skewed."*

`firmware/gen_led_layout.py` now applies **one** scale to both axes, expressed through the bbox it
already derives, and centers the cloud on QMK's own default effect center:

```
s        = 64 / bbox_height                     -> 0.64 units/mm   (both axes)
y_qmk    = round((y_mm - y0) * s)               -> NUMERICALLY UNCHANGED
x_qmk    = round(112 + (x_mm - x_center) * s)   -> x_center = (x0+x1)/2 = 42.1
```

`112` is `k_rgb_matrix_center = {112, 32}` read out of the build tree at
`quantum/rgb_matrix/rgb_matrix.c:32`. The generator now **refuses to emit** (loud `sys.exit` printing
the measured bbox, scale and center) unless `s == 0.64` and `x_center == 42.1`, so it cannot silently
produce a layout for a board whose outline moved. Aspect ratio **4.157 : 1 → 1.000 : 1**.

**No `RGB_MATRIX_CENTER` was added.** See the discrepancy note in §6 — one already exists, and it is
already the default value.

**Prediction register (registered before the first mutation, computed read-only from
`v5_6.kicad_pcb`) → outcome:**

| prediction | outcome |
|---|---|
| all 24 `y` byte-identical | ✅ **24/24 unchanged** |
| `flags` and `matrix` untouched | ✅ all 24 flags `[4×13, 8, 2×10]`, `matrix` on chain 0-12 only — identical |
| LED13 lands at exactly `x = 112` | ✅ `(112, 59)` |
| all three UF2s change bytes | ✅ all three moved |
| *"all 24 layout entries change in `x`"* | ⚠️ **23/24** — see §6 deviation 1 |
| *"min/max x = 112 ± round-of-27"* | ⚠️ LED extremes are **112 ± 24** (88..136); 112±27 = 85..139 is the **board outline** mapped — see §6 deviation 2 |

24-point diff, x only (board mm → old → new): LED1/5/9/14 x=13.525 `36→94`; LED2/6/10 x=32.575
`87→106`; LED3/7/11 x=51.625 `137→118`; LED4/8/12 x=70.675 `188→130`; LED13 x=42.1 `112→112`;
LED15 x=32.0 `85→106`; LED16 x=52.0 `138→118`; LED17/18/19 x=80.0 `213→136`; LED20 x=65.695
`175→127`; LED21 x=18.3 `49→97`; LED22/23/24 x=5.0 `13→88`.

The generator was run against `v5/hardware/pcb/v5_6.kicad_pcb` and its output applied to
`keyboard.json` `rgb_matrix.layout`; re-diffed after application: **24/24 entries, 0 mismatches.**

### 2. Change B — the duplicate `housekeeping_task_user()` call REMOVED

Ledgered 2026-08-13 as *"a trap for anyone who later implements that hook in a keymap"* — and the
2026-08-13 `calibrate` keymap then became exactly that keymap, drains its typing queue in that hook,
and *"only survived because draining a queue is idempotent."* Trap closed.

Verified in the build tree, not assumed — `quantum/keyboard.c:433-437`:

```c
void housekeeping_task(void) {
    housekeeping_task_modules();
    housekeeping_task_kb();     // :435
    housekeeping_task_user();   // :436
}
```

and the weak `housekeeping_task_kb()` at `:420` is an **empty body**. So quantum calls `_user`
itself; our strong `_kb` calling it again ran the keymap hook **twice per loop**. The trailing call
is gone, replaced by a comment quoting those lines.

**Every other `_kb→_user` chain in the file was re-verified against the fork's sources before being
trusted, per the brief — the rule is "call `_user` iff the weak `_kb` default we override was its
only caller":**

| hook | sole caller of the `_user` hook | verdict |
|---|---|---|
| `keyboard_pre_init_user` | weak `keyboard_pre_init_kb()`, `quantum/keyboard.c:300-302` | ✅ correct, left alone |
| `matrix_scan_user` | weak `matrix_scan_kb()`, `quantum/matrix_common.c:40-42` | ✅ correct, left alone |
| `process_record_user` | weak `process_record_kb()`, `quantum/quantum.c:190-192` | ✅ correct, left alone |
| `rgb_matrix_indicators_advanced_user` | weak `rgb_matrix_indicators_advanced_kb()`, `quantum/rgb_matrix/rgb_matrix.c:468-470` | ✅ correct, left alone |
| `housekeeping_task_user` | **`housekeeping_task()` itself**, `quantum/keyboard.c:436` | ❌ **double-called — fixed** |

`via_command_kb()` and `raw_hid_receive_kb()` have no `_user` counterpart. **Exactly one hook was
double-called; no unbriefed fix was needed.** Also checked that `matrix_scan_kb()` is not itself
invoked twice per scan (which would have double-fired `matrix_scan_user()` and the touch sampler):
`quantum/matrix.c:323` defines a **strong** `matrix_scan()` that overrides the weak one at
`quantum/matrix_common.c:168`, and the third call site (`matrix_common.c:114`) is inside
`matrix_post_scan()`, `#ifdef SPLIT_KEYBOARD` — not compiled here. One call per scan confirmed.

Both stale comment sites rewritten: `loudest_micro.c`'s file header (it asserted *"Each _kb hook
still calls through to its _user counterpart"*, now false) and
`keymaps/calibrate/keymap.c` (~36-42), which documented the double call as pre-existing/ledgered and
now records the single call — while keeping the reason the queue is still the right design: events
must not type inside the `action_exec()` that delivered them.

### 3. Change C — finding **4** CLOSED-BY-DECISION (no code change)

Coordinator decision, final: **`CAPS.led_count` stays 24 on both SKUs.** The byte is redefined as the
**addressable chain length**, which is electrically true on both SKUs — on the opaque SKU (LED1-14
populated) LED14's DOUT clocks pixels 14-23 into an unpopulated pad, so host writes to indexes 14-23
are harmless no-ops rather than errors. Rationale: the byte is part of **LOCKED protocol v0**, and
forking per-SKU UF2s multiplies the shipped artifacts against the drag-and-drop standard for zero
visible benefit. Recorded in two places: a comment at the `LOUDEST_LED_COUNT` definition site in
`loudest_micro.h` (whose trailing comment also changed from *"addressable LEDs"* to *"addressable
chain length"*), and `FIRMWARE-V4-NOTES.md` §6 "Remaining gaps". **Zero wire change; the CAPS reply
is byte-identical** (conformance 80/80 and the emulator's byte-exact CAPS check both re-passed).

### 4. Change D — stale live-docs (annotated, never deleted)

1. `docs/HANDOFF-STATE.md` main-PCB row — was *"❌ NOT ordered. Order hold in force"*. Struck in
   place with a dated correction citing `v5/V5-NOTES.md:2406` (*"boards are ordered AND POPULATED"*).
   **Only that row touched**; no other row reconciled, none had new evidence.
2. `docs/HANDOFF-STATE.md` §Firmware — "Current prebuilts" re-hashed for all three; one sentence
   added for the `calibrate` bring-up UF2 (citing `BUILD.md` §4a) and one for the two 2026-08-15
   changes.
3. `firmware/sim/package.json` `description` — still claimed *"the default --touch=board model FAILS
   on the current firmware by design"*, false since the 2026-08-13 touch fix (the README half was
   corrected then; this half was missed). Rewritten. **`scripts` block byte-identical**, so
   npm-visible behavior is unchanged; JSON re-parsed to prove it still loads.
4. **Hash-citation sweep** (`grep -rn` for `cf5bd628` / `b31673a7` / `a81ce4a1` across the whole
   working tree): every live/current-state citation updated — `BUILD.md` §4a step 1 **and** the
   maintainers block, `POLARITY-NOTE.md`'s shipped-bytes table (now three rows, with the superseded
   pairs preserved beneath it), `FIRMWARE-V4-NOTES.md` §5 (sha256 table re-hashed + calibrate row
   added + md5 line + a **new appended** superseded-artifacts block; the 2026-08-13 block above it
   was **not** overwritten), `firmware/sim/README.md` (a dated hash note above the touch-fix A/B
   table, which keeps its `cf5bd628…`/`b31673a7…` labels because it is the record of *that* fix),
   `docs/HANDOFF-STATE.md`, and `docs/HANDOFF-2026-08-06.md` §1 (see §6 note 3).
   **Untouched, deliberately:** every occurrence in `v5-release-compiled/` (release bundle = the NEXT
   wave) and every occurrence in dated `v5/V5-NOTES.md` entries (frozen history).

### 5. Rebuild + gates — VERBATIM

`default` and `calibrate` each built **twice from a wiped `.build/`**; `default` a third time to
retain the ELF for the geometry proof. `vial` built once (non-determinism is ledgered and proven).

```
=== default   run1 -> default_RC=0   | RESULT md5=1c0ff911d545d0943c11a5971279d3ae bytes=88576
=== default   run2 -> default_RC=0   | RESULT md5=1c0ff911d545d0943c11a5971279d3ae bytes=88576
=== default   run3 -> default_RC=0   | RESULT md5=1c0ff911d545d0943c11a5971279d3ae bytes=88576
=== calibrate run1 -> calibrate_RC=0 | RESULT md5=aabf7954f1e2b46880f298fd620d63ff bytes=96768
=== calibrate run2 -> calibrate_RC=0 | RESULT md5=aabf7954f1e2b46880f298fd620d63ff bytes=96768
=== vial      run1 -> vial_RC=0      | RESULT md5=286fb09d0ce1d96c74f2a0baf8348378 bytes=104448
```

**Zero code warnings under `-Werror`.** The only `warning:` string anywhere in the six build logs is
the vial link's `lto-wrapper: warning: using serial compilation of 2 LTRANS jobs` — the LTO driver's
build-parallelism note, identical to the one ledgered 2026-08-13, not a diagnostic about our code.

```
node firmware/sim/behavior.cjs --touch=board                     (default)
  touch model: board   checks: 33   failures: 0
  BEHAVIOR SIM: PASS
node firmware/sim/behavior.cjs ../prebuilt/loudest_micro_vial.uf2 --touch=board
  touch model: board   checks: 33   failures: 0
  BEHAVIOR SIM: PASS
node firmware/sim/behavior.cjs --touch=firmware                  (default AND vial, identical)
  touch model: FIRMWARE ASSUMPTION — config.h:21 "idle high, touched low", GP16 idles HIGH
    [FAIL] device booted into layer 0 (indicator is pure red, hue 0)  <- 31,23,0
    [FAIL] SW1 emits KC_F13 (0x68) from the as-booted layer  <- no keyboard report at all
    [FAIL] the layer advances while the pad is TOUCHED  <- still 31,23,0 while touched
    [FAIL] the layer does NOT advance again when the finger LIFTS  <- touched 31,23,0 -> released 15,31,0
  touch model: firmware   checks: 33   failures: 4
  BEHAVIOR SIM: FAIL            <- required: the A/B still discriminates on the NEW builds
node firmware/sim/calibrate.cjs
  adc fix: on   checks: 37   failures: 0
  CALIBRATE SIM: PASS
node firmware/sim/calibrate.cjs --no-adc-fix
  adc fix: OFF   checks: 37   failures: 15
  CALIBRATE SIM: FAIL           <- required, and 15 is the established count
python3 firmware/check_pins_v4.py
  PASS: all 30 pin-map checks against the ORDER-READINESS Layer 4 table succeeded
python3 firmware/check_pins_v4.py --qmk-info … --qmk-home …
  PASS: all 56 pin-map checks against the ORDER-READINESS Layer 4 table succeeded
python3 firmware/tests/conformance/run_conformance.py
  PASS: all 80 protocol-v0 conformance checks passed (firmware C handler vs daemon/loudestd/protocol.py oracle)
qmk lint -kb loudest_micro -km default   --strict  ->  Ψ Lint check passed!
qmk lint -kb loudest_micro -km calibrate --strict  ->  Ψ Lint check passed!
qmk lint -kb loudest_micro -km vial      --strict  ->  ☒ loudest_micro: The keymap vial should not exist!
                                                       ☒ Lint check failed for: loudest_micro
npm run smoke:default  ->  EMULATOR SMOKE: PASS
npm run smoke:vial     ->  EMULATOR SMOKE: PASS
   (incl. [ok] GP16 (TOUCH_OUT): SIO input, pull-DOWN (active-high strap, non-matrix)
          [ok] key scan: GP12 low -> keyboard report with F13 (0x68)
          [ok] raw HID: CAPS byte-exact vs daemon oracle)
md5 v5/hardware/pcb/v5_6.kicad_pcb = 221ebb98fcf44f860ed65f7ed8d1bc45   (UNCHANGED)
```

`qmk lint -km vial` is the one non-green line and is the **documented false positive** recorded in
`BUILD.md` §3.1 (mainline rule `INVALID_KM_NAMES = ['via','vial']`, tripped by every Vial keyboard);
`keymaps/vial/` was not touched this pass.

**Denominators unchanged across the board — 33, 33, 37, 30, 56, 80.** `calibrate.cjs` needed **no
adjustment**: 37/37 passed first try on the new build, so the escape hatch the brief authorised
(adjusting a pure drain-cadence expectation with a ledgered justification) was **not used**. Removing
one of two idempotent drains per loop changed no observable cadence.

### 5a. Animation-geometry proof — the DATA, from the shipped binary

Finding 7 is about appearance, which no harness here can see, so the *data* was proven instead —
and not from `keyboard.json` (the input) but from the **built artifact**. `g_led_config` was located
in the `default` ELF (`arm-none-eabi-nm`: `20000814 00000058 V g_led_config`, 88 B = 16 matrix_co +
48 point + 24 flags), its initialiser read out of `.data`, and those exact 88 bytes then **found
inside the shipped `loudest_micro_default.uf2` payload at offset 42676** (173 blocks, 44288 B
reconstructed flash):

```
points : (94,23) (106,23) (118,23) (130,23) (94,35) (106,35) (118,35) (130,35)
         (94,47) (106,47) (118,47) (130,47) (112,59) (94,51) (106,3) (118,3)
         (136,21) (136,34) (136,45) (127,60) (97,62) (88,51) (88,39) (88,26)
flags  : 4 4 4 4 4 4 4 4 4 4 4 4 4 8 2 2 2 2 2 2 2 2 2 2
points+flags vs gen_led_layout.py output : 24/24 match
x  min 88  max 136  span 48   center of extremes 112.0
y  min 3   max 62   span 59
LED13 (chain 12) = (112, 59)
```

The LED cloud is **exactly centered on x = 112** (min and max are symmetric: 112−24 and 112+24). The
board *outline* maps to x 85..139 (84.2 mm × 0.64 = 53.888 ≈ 54 wide) and y 0..64 (100.0 × 0.64 =
64.0 tall); the LED extremes sit inside that because the outermost LEDs are inset from the edge
(LED22-24 at x = 5.0 mm, LED17-19 at x = 80.0 mm of an 84.2 mm board). Generated
`info_config.h` confirms `RGB_MATRIX_LED_COUNT 24` and `RGB_MATRIX_CENTER { 112, 32 }`.

**STATED PLAINLY: visual appearance on hardware remains UNVERIFIED.** No render path for RGB
animations exists in any harness here. What is proven is that the coordinates the animations read are
isotropic and centered on the effect origin; that the four geometry-bearing animations *look* right
on a real board is a first-power-on observation, not a claim of this pass.

### 6. Deviations, discrepancies and judgment calls — all reported, none improvised through

1. **The brief's prediction register is internally inconsistent, and the measurement resolves it.**
   It predicts *"all 24 layout entries change in `x` only"* **and** *"LED13 (board x = 42.1, the bbox
   center) lands at exactly `x = 112`"*. Both cannot hold: 42.1 mm is simultaneously the bbox center
   **and** the midpoint of the 0..84.2 span, so it is the one fixed point of *both* transforms —
   old `round((42.1-0)/84.2*224) = 112`, new `round(112 + 0×0.64) = 112`. Measured outcome:
   **23/24 x values changed, LED13 unchanged at 112.** The substantive prediction (LED13 → 112) holds
   exactly. Detected **before** mutation, from the board file, read-only. Not treated as a STOP
   because the deviation is arithmetically forced by the brief's own other clause and lands in the
   safe direction (fewer entries moved than predicted).
2. **`112 ± round-of-27` describes the board outline, not the LED extremes.** ±27 = the outline
   (84.2/2 × 0.64 = 26.944), i.e. x 85..139. The LEDs are inset, so their extremes are **112 ± 24**
   (88..136). Same for §6.4's *"x span ≈ 54"* / *"max_y−min_y ≈ 64"*: those are the outline mapped
   (53.888 and 64.0); the LED-cloud spans are **48** and **59**. Both consistent, both reported
   rather than rounded into agreement.
3. **`RGB_MATRIX_CENTER` already exists, and the brief says not to define it.** `keyboard.json`
   carries `rgb_matrix.center_point: [112, 32]`, which `data/mappings/info_config.hjson:140` maps to
   `#define RGB_MATRIX_CENTER`; the generated `info_config.h` confirms `{ 112, 32 }`. That is
   **byte-identical to QMK's default** `k_rgb_matrix_center` (`rgb_matrix.c:32`), so the brief's
   intent — the effect center is (112,32) and correct by construction — holds either way. **Nothing
   was added and nothing removed:** adding is forbidden, and removing would be an unbriefed
   functional edit for zero behavioral change. Flagged for the coordinator.
4. **`FIRMWARE-V4-NOTES.md` had no existing finding-4 item to annotate.** The brief says the
   finding-4 item in the known-limitations list "becomes CLOSED-BY-DECISION"; that list (§6
   "Remaining gaps") never carried one. A **new item 6** was added, written as the closure record.
   Nothing was deleted.
5. **Three files were annotated beyond the brief's named set, all in the same stale-doc class this
   wave exists to close, all additive:** (a) `loudest_micro.c`'s file header, which asserted every
   `_kb` hook calls its `_user` counterpart — made false by change B; (b) `FIRMWARE-V4-NOTES.md` §1's
   "rgb_matrix.layout coordinate regeneration" paragraph, which documents the old per-axis transform
   as the method to reproduce — a superseded-block was appended; (c) `docs/HANDOFF-2026-08-06.md` §1
   "Canonical hashes (verify before trusting anything downstream)", whose UF2 rows would otherwise
   send a successor to verify against dead hashes. That file is a dated session record, so its text
   was **not rewritten** — a dated forward pointer was appended below it, and the file is explicitly
   marked as left-as-written otherwise.
6. **Newly observed, NOT changed (out of brief scope, flagged for the coordinator):**
   `firmware/sim/package.json`'s `sim:all` script is `npm run sim:default:fwpolarity && npm run
   sim:vial:fwpolarity` — i.e. it aggregates the two **counterfactual** arms, which now correctly
   FAIL, so `npm run sim:all` exits non-zero by design. Harmless but misleading for a name that reads
   like "run everything". The brief scoped this file to the `description` string only and required
   npm-visible behavior unchanged, so the `scripts` block was left byte-identical.

### 7. Artifacts — all three UF2s moved

| file | was (2026-08-13) | now (2026-08-15) | bytes |
|---|---|---|---|
| `loudest_micro_default.uf2` | md5 `cf5bd62853ea591b39a1ce7246848229`<br>sha256 `35f34ea4f229eb65f0b3d9ad8d9cc0444a399af2c5943a25c06131d58b0f2ad3` | md5 **`1c0ff911d545d0943c11a5971279d3ae`**<br>sha256 **`d37efc5f375af822a72273ad86c76950fa005edc28bcc2c675f0bcefb5ef3926`** | 88576 → 88576 |
| `loudest_micro_vial.uf2` | md5 `b31673a7ba6a6219a0d5a3b9aee52e42`<br>sha256 `7056e6ad0ebe9673f077f69fb6d32873fbcf0cdd233e78d163ef940254f814c5` | md5 **`286fb09d0ce1d96c74f2a0baf8348378`**<br>sha256 **`d5dcb85f0185bf02b66ab657829222bc0354a845e8b76efde03c79497a4e3284`** | 104448 → 104448 |
| `loudest_micro_calibrate.uf2` | md5 `a81ce4a137e667d73e3cd9da5c82a98a`<br>sha256 `7230a4de95851909f78893def51d49bcda68ff34670934495eabf760a31a61e7` | md5 **`aabf7954f1e2b46880f298fd620d63ff`**<br>sha256 **`f9c5de9ba5834e0c810688520fa53d58ac72229c628be270b4987ceb57ff1541`** | 96768 → 96768 |

**All three byte sizes are unchanged** — the changes were a 24-entry coordinate table and one deleted
call, neither of which moves a section boundary. `default` and `calibrate` are **reproducibility
targets** (proved again here); `vial` records shipped bytes only.

### 8. Files touched, and why

| file | why |
|---|---|
| `firmware/gen_led_layout.py` | change A: isotropic transform + centering + the v5_6 assertion; docstring rewritten (it documented the per-axis normalisation) |
| `firmware/loudest_micro/keyboard.json` | change A: `rgb_matrix.layout` x column regenerated (23 entries); `$rgb_comment` annotated with the new transform and the `center_point`-is-the-default note |
| `firmware/loudest_micro/loudest_micro.c` | change B: duplicate `housekeeping_task_user()` removed + comment citing `quantum/keyboard.c:433-437`; file header corrected (it claimed every `_kb` calls its `_user`) |
| `firmware/loudest_micro/loudest_micro.h` | change C: `LOUDEST_LED_COUNT` semantics + SKU note + the finding-4 decision |
| `firmware/loudest_micro/keymaps/calibrate/keymap.c` | change B: the "runs TWICE per loop" comment was made false by the fix; rewritten, keeping why the queue is still right |
| `firmware/FIRMWARE-V4-NOTES.md` | change C (new gaps item 6) + change D (§5 re-hashed, superseded block appended, §1 transform paragraph annotated) |
| `firmware/POLARITY-NOTE.md` | change D: shipped-bytes table re-hashed to three rows, superseded pairs preserved |
| `firmware/BUILD.md` | change D: §4a step-1 calibrate md5 and the maintainers-block md5 |
| `firmware/sim/README.md` | change D: dated hash note above the touch-fix A/B table |
| `firmware/sim/package.json` | change D: `description` no longer claims `--touch=board` fails by design; `scripts` untouched |
| `docs/HANDOFF-STATE.md` | change D: main-PCB ordered row struck+corrected; §Firmware re-hashed + calibrate UF2 + the two 2026-08-15 changes |
| `docs/HANDOFF-2026-08-06.md` | change D: dated forward pointer under §1's canonical-hash table |
| `firmware/prebuilt/*.uf2` (×3) | rebuilt and replaced |

### 9. Deliberate non-actions

- **`v5-release-compiled/` NOT synced** — the release bundle (its `firmware/prebuilt/*.uf2`,
  `POLARITY-NOTE.md`, `RELEASE.md`, `MANIFEST.md` rows and Stats) still carries the 2026-08-13
  artifacts and no calibrate UF2. That re-sync + MANIFEST re-hash is **the next wave**, per the brief;
  it is not an executor's call. Same for the public `agentpad13/` mirror.
- **`firmware/sim/behavior.cjs` NOT modified.** Editing the referee to pass its own gate voids the
  gate. It is byte-identical to the harness that produced the 2026-08-13 results.
- **`firmware/sim/calibrate.cjs` NOT modified** — it passed 37/37 unaided, so the brief's conditional
  authorisation to adjust a drain-cadence expectation was never exercised.
- **`keymaps/vial/` and `keymaps/default/` sources NOT touched**; no new keymaps, no new features.
- **`docs/EXECUTOR-PROTOCOL.md` NOT touched.** No board, schematic, netlist, fabpack, plate, case,
  render or protocol edit. Protocol v0 wire format unchanged (finding 4 closed *by decision*, and
  conformance 80/80 + the emulator's byte-exact CAPS check prove the CAPS reply did not move).
- **No banked/frozen tree touched:** `v4-release-compiled/`, `v5-discarded/`, `fabpack_out*`,
  `agentpad13/`, boards `v5`..`v5_5`. **No dated ledger entry edited** — including the three entries
  above this one, whose now-superseded hashes are historical and correct for what they are.
- **`firmware/check_pins_v4.py` header/banner left stale** ("Rev A (board v4_r27)") — third pass to
  flag it; it is a gate whose printed output is quoted verbatim in these ledgers, and it is not in
  this brief.
- Scratch build tree (`~/.claude/jobs/8b1a462c/tmp/firmware-wave/vial-qmk`) left **synced to the final
  working-tree sources** (`diff -r` rc 0), `.build/` and all emitted `.uf2`s removed, only the core
  patch modified — the same disposition as the previous two entries, for the same reason.
- **No git operation of any kind, no push, no upload, no spending, no remote.**

**ORDER HOLD is superseded for the main PCB** (boards ordered and populated, per `:2406` — now
corrected in `HANDOFF-STATE.md`'s table). The first-power-on checklist is unchanged and still cheap:
plug in, layer indicator **pure red (hue 0) = touch fix present**; then flash
`loudest_micro_calibrate.uf2` and press one key four times for the ADC numbers. New this pass: the
four geometry-bearing animations should now look *round* rather than stretched — the first thing on
that board worth simply looking at.

---

## RELEASE BUNDLE RE-SYNC (wave 3) — `BRING-UP.md` split out of `BUILD.md` §4a and shipped; `v5-release-compiled/` brought current (2026-08-15, release-sync executor)

**Board md5 `221ebb98fcf44f860ed65f7ed8d1bc45` asserted at start AND at close — UNCHANGED.** Zero
board, schematic, netlist, fabpack, plate, case, render, firmware-source, keymap-source or prebuilt
mutation. No git operation of any kind — no commit, no push, no remote, no upload, no spending. The
public mirror `agentpad13/` is **untouched** (next wave).

### 0. Base integrity, verified on entry before anything was read further

| artifact | expected (brief) | measured | verdict |
|---|---|---|---|
| `firmware/prebuilt/loudest_micro_default.uf2` | `1c0ff911d545d0943c11a5971279d3ae` / 88576 | same | ✓ |
| `firmware/prebuilt/loudest_micro_vial.uf2` | `286fb09d0ce1d96c74f2a0baf8348378` / 104448 | same | ✓ |
| `firmware/prebuilt/loudest_micro_calibrate.uf2` | `aabf7954f1e2b46880f298fd620d63ff` / 96768 | same | ✓ |
| `v5-release-compiled/firmware/prebuilt/loudest_micro_default.uf2` | `cf5bd628…` (stale by design) | `cf5bd62853ea591b39a1ce7246848229` / 88576 | ✓ |
| `v5-release-compiled/firmware/prebuilt/loudest_micro_vial.uf2` | `b31673a7…` (stale by design) | `b31673a7ba6a6219a0d5a3b9aee52e42` / 104448 | ✓ |
| bundle `firmware/prebuilt/loudest_micro_calibrate.uf2` | absent | absent | ✓ |
| `v5/hardware/pcb/v5_6.kicad_pcb` | `221ebb98fcf44f860ed65f7ed8d1bc45` | same | ✓ |

### 1. The 9-check MANIFEST self-verifier had to be RECONSTRUCTED — stated plainly

The brief required finding how the 9-check self-verification was RUN in prior passes rather than
inventing a new checker. **No script producing that output exists anywhere on disk.** Searched the
whole repo and every `~/.claude/jobs/*/tmp` scratch tree for the literal check names
(`stats-count-rows`, `no-orphans`, `self-exclusion`): **zero hits.** The closest surviving artifact
is `~/.claude/jobs/8b1a462c/tmp/relverify/check_manifest.py`, which performs the *same semantic
checks* (row parse, existence, md5, bytes, strays, Stats-vs-rows, Stats-vs-disk, lineage) but prints
prose and folds them differently — it is **not** the script that emitted the 9-line block.

So it was reconstructed from the two verbatim transcripts in this ledger (`:2032-2043`, 2026-08-05;
`:2678-2688`, 2026-08-13), reproducing their exact format and their exact 9-check split: existence,
md5, bytes, no-orphans, Stats-count-vs-rows, Stats-count-vs-disk, Stats-bytes-vs-rows,
Stats-bytes-vs-disk, self-exclusion. The on-disk walk **includes dotfiles** — the 2026-08-05 entry
records that the prior session's walk skipped a `.DS_Store` and that the corrected walk counts it.
Row regex, Stats regex and byte accounting are identical in meaning to `check_manifest.py`'s. The
proof that the reconstruction is faithful is the **pre-mutation run below: 9/9 on a bundle that four
independent prior passes also scored 9/9, with the same denominators (129) and the same byte total
(42146874)**.

### 2. PREDICTION REGISTER — registered here BEFORE the first byte of the bundle was touched

**Run A — pre-mutation, before any file copy. VERBATIM:**

```
[PASS] 1 existence          129/129 listed files present
[PASS] 2 md5                129/129 md5 match
[PASS] 3 bytes              129/129 byte counts match
[PASS] 4 no-orphans         0 on-disk file(s) without a row
[PASS] 5 stats-count-rows   Stats 129 vs rows 129
[PASS] 6 stats-count-disk   Stats 129 vs on-disk 129
[PASS] 7 stats-bytes-rows   Stats 42146874 vs row-sum 42146874
[PASS] 8 stats-bytes-disk   Stats 42146874 vs on-disk-sum 42146874
[PASS] 9 self-exclusion     MANIFEST.md has no self-row
RESULT: 9/9 checks PASS
```

The bundle is internally consistent and merely **stale** — exactly as the brief predicted.

**Run B — predicted, after the 5 file operations, before the MANIFEST/RELEASE/HOW-TO-ORDER edits.**
The brief predicts failure on "the 3 replaced files + 2 no-row orphans". Refined to check level and
to the exact numbers, because the byte-count check is *sharper* than the file count suggests — **both
UF2s keep their byte sizes** (88576 and 104448, unchanged across the 2026-08-15 rebuild), so only
`POLARITY-NOTE.md` can fail check 3:

| # | check | predicted | offenders predicted |
|---|---|---|---|
| 1 | existence | **PASS** 129/129 | — |
| 2 | md5 | **FAIL** 126/129 | `firmware/POLARITY-NOTE.md`, `firmware/prebuilt/loudest_micro_default.uf2`, `firmware/prebuilt/loudest_micro_vial.uf2` |
| 3 | bytes | **FAIL** 128/129 | `firmware/POLARITY-NOTE.md` **only** (4133 → 5673) |
| 4 | no-orphans | **FAIL** 2 | `firmware/BRING-UP.md`, `firmware/prebuilt/loudest_micro_calibrate.uf2` |
| 5 | stats-count-rows | **PASS** 129 vs 129 | — |
| 6 | stats-count-disk | **FAIL** | Stats 129 vs on-disk **131** |
| 7 | stats-bytes-rows | **PASS** 42146874 vs 42146874 | — |
| 8 | stats-bytes-disk | **FAIL** | Stats 42146874 vs on-disk-sum **42252467** (= 42146874 + 1540 POLARITY-NOTE + 96768 calibrate UF2 + 7285 BRING-UP.md) |
| 9 | self-exclusion | **PASS** | — |

**Predicted RESULT: 5/9 checks PASS.** Any failing row outside this table, or any offender not named
in it, is a STOP.

**Run C — predicted, at close: 9/9, Stats `131 files`, byte total = 42252467 + the RELEASE.md and
HOW-TO-ORDER.md deltas.**

**Working-tree sources as they stood at registration time (this is what gets copied):**

| source | md5 | bytes |
|---|---|---|
| `firmware/BRING-UP.md` | `da5d89ebe5e1fa9242ce8b780ddeeba1` | 7285 |
| `firmware/POLARITY-NOTE.md` | `67592aaa66b432c69d3ebddab23025e5` | 5673 |
| `firmware/prebuilt/loudest_micro_default.uf2` | `1c0ff911d545d0943c11a5971279d3ae` | 88576 |
| `firmware/prebuilt/loudest_micro_vial.uf2` | `286fb09d0ce1d96c74f2a0baf8348378` | 104448 |
| `firmware/prebuilt/loudest_micro_calibrate.uf2` | `aabf7954f1e2b46880f298fd620d63ff` | 96768 |

**DEVIATION FROM THE BRIEF, reported.** The brief states the working-tree `POLARITY-NOTE.md` is the
one "wave 2 re-hashed" (`80646d22b5fd2b98ed1baeaf8bb51800` / 5521). That was true on entry and is
recorded here as measured. It is **no longer** the shipped hash: §3 below edits that file's
`BUILD.md §4a` pointer — an edit this brief's own §1 requires — which moves it to
`67592aaa66b432c69d3ebddab23025e5` / 5673 **before** the copy. The bundle is therefore synced to the
post-§1 hash, not to `80646d22…`; syncing to `80646d22…` would have shipped a bundle whose
`POLARITY-NOTE.md` points at a `BUILD.md` section that no longer holds the procedure.

### 3. `firmware/BRING-UP.md` — the procedure moved out of `BUILD.md` §4a

**Why:** the bundle's audience is the owner assembling and powering the first boards. §4a was the only
place the calibration procedure existed, and it was buried in a 431-line toolchain guide that a
bundle reader has no use for and that the bundle does not ship. `firmware/POLARITY-NOTE.md` is the
precedent — a standalone firmware note that ships byte-identical in both trees.

**What MOVED (verbatim — this was a move, not a rewrite).** Diffed line-by-line against the original
§4a body; the only textual deltas are the four listed under "what changed" below:

- Step 0, the ten-second firmware check (pure red = 2026-08-13 or later; orange = reflash).
- Step 1, the BOOTSEL flash flow, including the current calibrate md5 `aabf7954f1e2b46880f298fd620d63ff`,
  **the `Reset EEPROM` gesture warning** (*"Do not hold SW1 while plugging in"*), **the US-layout
  garble warning**, and **the boot-silence explanation** (*"The board types nothing at plug-in. That
  is deliberate…"*).
- Step 2, the four guided `SW1` presses, the continuous-sweep explanation, and the other-keys table:
  SW2 restart, SW3 live line, the touch pad's `TOUCH:DOWN`→`TOUCH:UP` **order-is-the-pass** check,
  the encoder's `ENC:CW`/`ENC:CCW`/`ENC:PRESS` lines, and "every other key does nothing, on purpose".
- Step 3, the sample REPORT block, both routes for applying it, the `WARNING:` guidance and the
  `NEVER FIRES` explanation.
- Step 4, put the real firmware back.

**What CHANGED in the move (four deltas, all reported):** (1) heading levels — `## 4a.` became the
document title, `###` steps became `##`; (2) a bundle-context framing blockquote added under the
intro, stating where the file lives and that only the second route in Step 3 needs a source
checkout; (3) Step 3's second route gained one sentence naming it as the source-repo route ("the two
files named below are firmware *sources*; they are not part of the release bundle") — **additive**,
the original "Two edits, both copy-paste:" is intact; (4) Step 3's *"Rebuild and reflash with the
normal flow in §3 and §4 above"* became *"…in `firmware/BUILD.md` — §3 (Build) and §4 (Flash) — in
the source repo"*, a forced repair because "above" no longer exists. A closing pointer paragraph to
`POLARITY-NOTE.md` and `BUILD.md` was appended.

**What STAYED in `BUILD.md` §4a, and why.** The heading is kept, followed by one paragraph naming
`firmware/BRING-UP.md` as the single source of truth. The **`### For maintainers`** block stayed:
`qmk compile -kb loudest_micro -km calibrate`, the two `firmware/sim/calibrate.cjs` referee arms, the
reproducibility statement and the pointer to `keymaps/calibrate/`. It is builder-facing and its
commands need a QMK build tree and repo paths a bundle reader does not have — moving it would have
put dead paths into a bundle document, i.e. it would have *hurt* BRING-UP.md's self-containment
rather than helped it. §4a went 132 lines → 27.

**Cross-references updated (3), grep-proven complete.** `grep -rn "4a" firmware/` at close returns
only: hash fragments (`a81ce4a1…`, `4af788ae…`), the §4a stub heading itself, `FIRMWARE-V4-NOTES.md`'s
own §4a and its `ORDER-READINESS §4a` citation (**different documents' §4a — not this procedure**),
this pass's own deliberate historical back-references, and the one item below.

| file | was | now |
|---|---|---|
| `firmware/BUILD.md` §8 | *"**The sweep now has a mechanism — see §4a**"* | *"— see [`firmware/BRING-UP.md`](BRING-UP.md)"* |
| `firmware/POLARITY-NOTE.md` | *"Step-by-step instructions: `firmware/BUILD.md` §4a."* | *"…: `firmware/BRING-UP.md`"* + a dated parenthetical naming where it moved from |
| `firmware/loudest_micro/keymaps/calibrate/readme.md` | *"live in **`firmware/BUILD.md` § "4a. Bring-up: first-power-on calibration"**"* | *"live in **`firmware/BRING-UP.md`**"* + the same dated parenthetical |

**`keymaps/calibrate/keymap.c` was NOT edited — judgment call, reported.** The brief authorises the
edit *"if they cite §4a"*. Its header reads `// real firmware back. See keymaps/calibrate/readme.md
and firmware/BUILD.md` / `// ("Bring-up: first-power-on calibration").` — it cites the section by
**title, not by §4a**, it names `readme.md` **first** (which now forwards to `BRING-UP.md`), and the
titled heading still exists in `BUILD.md` and forwards. So the citation resolves; it is one hop
indirect, not dangling. Against that cosmetic gain stands a real cost: `keymap.c` is the **compiled
source of the shipped `loudest_micro_calibrate.uf2`**, whose MANIFEST row this pass writes as a
byte-for-byte **reproducible build**. A comment-only edit does not reach the compiler output, but
this brief authorises **no rebuild**, so the claim would have gone from measured to merely reasoned.
Left alone; `keymap.c` mtime `07:48:08` (wave 2) is unchanged, so the shipped binary's source is
exactly what built it. Flagged for a firmware wave that can rebuild.

**`firmware/sim/README.md:423` NOT edited** — it describes `calibrate.cjs` as the referee for *"the
bring-up keymap, `BUILD.md` §4a"*. That is a descriptive identification, not a procedure pointer, and
`firmware/sim/` is on this brief's prohibition list. Flagged, not changed.

### 4. Bundle sync manifest — per-file was → now

| file | was (md5 / bytes) | now (md5 / bytes) | op |
|---|---|---|---|
| `firmware/prebuilt/loudest_micro_default.uf2` | `cf5bd62853ea591b39a1ce7246848229` / 88576 | **`1c0ff911d545d0943c11a5971279d3ae`** / 88576 | replaced |
| `firmware/prebuilt/loudest_micro_vial.uf2` | `b31673a7ba6a6219a0d5a3b9aee52e42` / 104448 | **`286fb09d0ce1d96c74f2a0baf8348378`** / 104448 | replaced |
| `firmware/prebuilt/loudest_micro_calibrate.uf2` | *(absent)* | **`aabf7954f1e2b46880f298fd620d63ff`** / 96768 | **added** |
| `firmware/POLARITY-NOTE.md` | `38895cdcbf27b60d899554241789880c` / 4133 | **`67592aaa66b432c69d3ebddab23025e5`** / 5673 | replaced |
| `firmware/BRING-UP.md` | *(absent)* | **`da5d89ebe5e1fa9242ce8b780ddeeba1`** / 7285 | **added** |
| `HOW-TO-ORDER.md` | `d085320d4ad1b407ada176aa667a75a6` / 7700 | **`3f334d63c57043d8658b056d4bb58696`** / 7951 | edited in place (+1 line) |
| `RELEASE.md` | `ad6309a35311ad94ad89614bdb12e1da` / 25890 | **`efd58e5fb90114d9b66d03c85ecdf9f4`** / 34542 | edited in place |

All five **copied** files are `cmp`-proven byte-identical to their working-tree sources (rc 0 on each;
`diff` rc 0 on both `.md` files). `RELEASE.md`: new **Revision 2026-08-15** block citing both V5-NOTES
entries by title, new **diff row K**, section (a) retitled **A–J → A–K**, Version cross-map firmware
row re-hashed (`cf5bd628…`/`b31673a7…` → `1c0ff911…`/`286fb09d…`, "REBUILT 2026-08-13" → "REBUILT
2026-08-15") **plus a second firmware row** for the calibrate UF2, labelled *not daily firmware*.
`HOW-TO-ORDER.md`: exactly one additive pointer line under Card 5's flash step; **no existing line
reworded or removed**; it is the **only** copy of that file in the repo (`find -name HOW-TO-ORDER.md`
returns the bundle copy alone — there is no working-tree or mirror copy to keep aligned).
`MANIFEST.md`: 5 rows re-hashed with provenance naming the change and its gate, **2 rows added**
(`firmware/BRING-UP.md`; the calibrate UF2, stating it is a **BRING-UP TOOL, not daily firmware** and
a reproducible build), 2 superseded UF2 rows removed, Stats **129 → 131 files / 42146874 → 42261370
bytes / 40.2 → 40.3 MiB**. `RELEASE.md`'s own row re-hashed **last**, after every other row was final.

Byte arithmetic, closed exactly: `42146874 + 1540` (POLARITY-NOTE) `+ 96768` (calibrate UF2) `+ 7285`
(BRING-UP.md) `+ 251` (HOW-TO-ORDER.md) `+ 8652` (RELEASE.md) `= 42261370` — the measured on-disk sum.

### 5. PREDICTION OUTCOMES — the two remaining runs, VERBATIM

**Run B — after the 5 file operations, before the MANIFEST/RELEASE/HOW-TO-ORDER edits:**

```
[PASS] 1 existence          129/129 listed files present
[FAIL] 2 md5                126/129 md5 match
         -> firmware/POLARITY-NOTE.md row=38895cdcbf27b60d899554241789880c disk=67592aaa66b432c69d3ebddab23025e5
         -> firmware/prebuilt/loudest_micro_default.uf2 row=cf5bd62853ea591b39a1ce7246848229 disk=1c0ff911d545d0943c11a5971279d3ae
         -> firmware/prebuilt/loudest_micro_vial.uf2 row=b31673a7ba6a6219a0d5a3b9aee52e42 disk=286fb09d0ce1d96c74f2a0baf8348378
[FAIL] 3 bytes              128/129 byte counts match
         -> firmware/POLARITY-NOTE.md row=4133 disk=5673
[FAIL] 4 no-orphans         2 on-disk file(s) without a row
         -> firmware/BRING-UP.md
         -> firmware/prebuilt/loudest_micro_calibrate.uf2
[PASS] 5 stats-count-rows   Stats 129 vs rows 129
[FAIL] 6 stats-count-disk   Stats 129 vs on-disk 131
[PASS] 7 stats-bytes-rows   Stats 42146874 vs row-sum 42146874
[FAIL] 8 stats-bytes-disk   Stats 42146874 vs on-disk-sum 42252467
[PASS] 9 self-exclusion     MANIFEST.md has no self-row
RESULT: 4/9 checks PASS
```

**Verdict: every substantive prediction landed exactly.** The failing checks are precisely the five
registered (2, 3, 4, 6, 8) and no others; each named offender is precisely the file registered for it,
with the registered row/disk values; the sharp prediction held — check 3 fails on
`POLARITY-NOTE.md` **alone**, because both UF2s keep their byte sizes; check 6 reads 129 vs **131**
and check 8 reads **42252467**, both as computed in advance. **No unexpected artifact moved.**

**One error, mine, in the register itself — recorded rather than quietly corrected.** §2 named five
failing checks and then wrote *"Predicted RESULT: 5/9 checks PASS"*. Nine minus five failures is
**4**, and the run returned `RESULT: 4/9`. The mistake is arithmetic in the summary line only; the
per-check and per-offender predictions — the ones the STOP condition is written against ("any extra
failing row → STOP") — were all correct, and there was no extra failing row. Not treated as a STOP;
recorded here because a prediction register that gets silently edited to match its outcome is worth
nothing.

**Run C — at close, after every edit:**

```
[PASS] 1 existence          131/131 listed files present
[PASS] 2 md5                131/131 md5 match
[PASS] 3 bytes              131/131 byte counts match
[PASS] 4 no-orphans         0 on-disk file(s) without a row
[PASS] 5 stats-count-rows   Stats 131 vs rows 131
[PASS] 6 stats-count-disk   Stats 131 vs on-disk 131
[PASS] 7 stats-bytes-rows   Stats 42261370 vs row-sum 42261370
[PASS] 8 stats-bytes-disk   Stats 42261370 vs on-disk-sum 42261370
[PASS] 9 self-exclusion     MANIFEST.md has no self-row
RESULT: 9/9 checks PASS
```

**Independent cross-check.** The surviving 2026-08-05 checker
(`~/.claude/jobs/8b1a462c/tmp/relverify/check_manifest.py`), written by a different pass and not
touched here, was run against the finished bundle and corroborates every number: `parsed rows: 131`,
`claimed stats: 131 files, 42261370 bytes`, `actual: 131 files on disk (excl MANIFEST), 42261370
bytes summed from listed files`, `manifest table byte sum: 42261370`, and **zero** MISSING /
STRAY / MD5-MISMATCH / SIZE-MISMATCH findings.

It does print **4 `LINEAGE-INCONSISTENT` lines — and they are a stale-script artifact, PROVEN
pre-existing, not caused by this pass.** Its lineage check looks up the row
`hardware/case/v2/stl/agentpad13_v2_band_1.6mm.stl` — the **retired 2.4 mm band removed from this
bundle on 2026-07-24** — so the lookup returns its `"?"` sentinel and every lineage label containing
the substring "band" mismatches it (including the *tray* row, whose label ends *"unchanged through
every band rev"*). Proven rather than asserted: its lineage logic was replayed against
`git show HEAD:v5-release-compiled/MANIFEST.md` (129 rows, the pre-pass state) and returns the
**same 4 failures, identical strings**. This is also independent evidence for §1's conclusion that
this script is *not* the one that emitted the 9-line block — it could not have scored 9/9 on any
bundle since 2026-07-24.

### 6. Containment — proven, not asserted

- **Bundle inventory: 132 files on disk = 131 manifest rows + `MANIFEST.md`** (which self-excludes).
- `git status --porcelain v5-release-compiled` names **exactly the 8 intended paths** and nothing
  else: ` M HOW-TO-ORDER.md`, ` M MANIFEST.md`, ` M RELEASE.md`, ` M firmware/POLARITY-NOTE.md`,
  ` M firmware/prebuilt/loudest_micro_{default,vial}.uf2`, `?? firmware/BRING-UP.md`,
  `?? firmware/prebuilt/loudest_micro_calibrate.uf2`. Both UF2 diffs read
  `Bin 88576 -> 88576` and `Bin 104448 -> 104448` — content moved, size did not, as predicted.
- **Working tree: exactly 4 files touched this pass**, proven by mtime rather than by claim —
  `find firmware -newermt '2026-08-15 09:00'` returns only `BRING-UP.md`, `BUILD.md`,
  `POLARITY-NOTE.md`, `keymaps/calibrate/readme.md`. Every other modified firmware file carries a
  wave-1/wave-2 mtime (07:46–08:00), including **`keymaps/calibrate/keymap.c` at 07:48:08** and all
  three prebuilts at **07:52:26**.
- **Board md5 `221ebb98fcf44f860ed65f7ed8d1bc45` re-measured at close — UNCHANGED.**
- **Public mirror `agentpad13/`: `git status --porcelain agentpad13/` returns EMPTY.**
- Nothing changed anywhere outside `firmware/`, `v5-release-compiled/`, `v5/V5-NOTES.md` and the
  pre-existing `docs/` + submodule-pointer entries inherited from earlier waves.

### 7. Deliberate non-actions

- **Public mirror `agentpad13/` NOT synced** — the brief scopes it to the next wave. It still carries
  the 2026-08-13 firmware, no calibrate UF2 and no `BRING-UP.md`.
- **No firmware source, keymap source, sim, prebuilt, board, schematic, netlist, fabpack, plate, case
  or render mutation.** The three working-tree prebuilts were **copied, never rebuilt**; their md5s
  are asserted unchanged in §0 and re-measured at close.
- **No dated ledger entry edited.** The three entries above this one keep their now-superseded
  hashes — historical and correct for what they are.
- **`firmware/BUILD.md` §5–§9, and §4a's maintainers block, left as found** apart from the two
  pointer edits named in §3.
- **`firmware/check_pins_v4.py` header/banner still stale** ("Rev A (board v4_r27)") — fourth pass to
  flag it; it is a gate whose printed output is quoted verbatim in these ledgers, and it is not in
  this brief.
- **No git operation beyond read-only inspection** (`status`, `diff --stat`, `show` of committed
  blobs, used as evidence above and required by the brief's Definition of Done). **No commit, no
  push, no remote, no upload, no spending.**

**The bundle is now current with the working tree.** A stranger handed only `v5-release-compiled/`
gets, for the first time, the firmware that actually ships *and* the procedure for the first
power-on: flash `loudest_micro_calibrate.uf2`, open a text editor, press one key four times, and the
board types its own calibration.

## COORDINATOR ADDENDUM — MANIFEST self-verifier banked to disk (2026-08-15, coordinator)

The wave-3 entry above records that the 9-check MANIFEST self-verifier existed only as verbatim
ledger transcripts — no script on disk anywhere in the repo or surviving job trees. The wave-3
reconstruction is now banked as `v5/manifest_selfverify.py` (md5 `218b31e1358b560b2f63d5529d10bc55`, 4494 B), copied
byte-identical from that pass's scratchpad. Fidelity evidence: it reproduces 9/9 with the same
denominators as the four prior transcripts (129 files / 42146874 B before this campaign's sync,
131 / 42261370 after), and its post-banking run against `v5-release-compiled/` printed 9/9 PASS
verbatim (coordinator re-run, this date). Known-open, carried from the wave-3 entry:
`check_manifest.py`'s lineage pass prints 4 false LINEAGE-INCONSISTENT lines from the retired
2.4 mm band row lookup — repair-or-retire is an open decision; it is NOT the 9-check gate.

## WAVE 4 — public mirror re-synced and PUSHED; ships-broken prebuilts removed from the public repo (2026-08-15, coordinator + mirror-prep executor)

**The hazard:** `agentpad13` (github.com/yuz207/agentpad13) still shipped the retired pre-touch-fix
prebuilt pair `4af788ae…` / `e5008942…` — its HEAD `3a47533` predates the 2026-08-13 touch fix. The
2026-08-06 handoff's "public repo consistent" claim was wrong for firmware. Closed this pass:
**pushed `3a47533..d66a1b8`**, 24 files (+3038/−87). 22 firmware files synced byte-identical
(13 replaced incl. both UF2s and the three gate files that still asserted the defect —
`check_pins_v4.py`, `tests/conformance/stubs/quantum.h`, `tests/emulator/runner.cjs`; 9 added incl.
`BRING-UP.md`, `keymaps/calibrate/`, the calibrate UF2 and all of `sim/`), plus README and
HOW-TO-ORDER edits. Scrub gate: six patterns, 0 hits, re-run independently by the coordinator
before push. Branding preserved by blob-proof: the mirror's `FIRMWARE-V4-NOTES.md` carries one
deliberate public wording (the rename line); the executor detected it by searching private history
for the mirror blob's md5 (12/13 matched, that one did not), re-applied the substitution after the
copy, and proved exactness by inverse-substitution hash (`f54efe9f…` = the private `d6a9a22` blob).
`grep -rn 'Loudest' agentpad13/firmware/` = 0.

**CORRECTION of the wave-3 entry (~lines 3586-3588), correction-of-record, prior entry left as
written:** it says `HOW-TO-ORDER.md` "is the only copy of that file in the repo … no working-tree
or mirror copy to keep aligned." Wrong about the mirror — that pass's `find` was scoped to
`work-loudest` and could not see the sibling repo. The mirror has always carried its own
structurally-diverged copy (repo-relative paths, extra keycaps bullet). Now aligned: same +251 B
pointer line, `378bb61e…` → `7e42117…`.

**Coordinator ruling — unresolvable provenance citations carried verbatim.** The mirror already
tolerated 23 `hardware/pcb/v4/ORDER-READINESS.md` and 16 `daemon/loudestd/protocol.py` citations to
paths it does not carry. The new citation classes this sync introduces (`v5/V5-NOTES.md`,
`v5_6.kicad_pcb`, `docs/HANDOFF-2026-08-06.md`) are the same kind; rewriting them would mint
mirror-only divergences every future sync must preserve (the branding line is already one). Precedent
followed, nothing adapted.

**Known-open, carried:** `firmware/sim/package.json` `sim:all` runs only the two counterfactual
`--touch=firmware` arms and fails by design — misleading alias, rename it in a future source pass
and re-sync (mirror-only fix rejected: divergence). `keymaps/calibrate/keymap.c` header cites the
BUILD.md section by title (resolves through the §4a stub; cosmetic; touching it moves the
reproducible calibrate UF2 hash — fold into the bring-up config rebuild). And when bring-up changes
`JS_CENTER`/`JS_THRESHOLD` in `loudest_micro.c`, the mirrored `CAL_SHIPPED_*` constants in
`keymap.c:64-65` MUST move with them or the tool's "shipped verdict" line lies.

## WAVE 5 — protocol v1 + ON-BOARD joystick calibration; the bring-up firmware retired (2026-08-15, coordinator + 4 executors)

**Committed `80e9ca9`.** The joystick's placeholder calibration finally has a replacement mechanism, and
it needs nothing but the board itself.

### The design went wrong twice before it went right — record why

1. **Separate `calibrate` keymap (wave 1)** — the board TYPED its measurements for a human to paste into
   source and rebuild. Root cause of the over-engineering: the coordinator treated "protocol v0 is LOCKED"
   as a law of physics rather than a decision it owned, so the board had no way to *report* an ADC value,
   so the only output channel left was keystrokes, so keys had to be inert, so it needed its own firmware.
   Every layer descended from that first false premise.
2. **Host-invoked routine (`loudestd calibrate`)** — correct that a mode was unnecessary, wrong that the
   trigger belonged on the host. Owner, verbatim: *"Calibration is stored in EEPROM, no daemon needed. You
   turn on calibration, it fucking calibrates, then it stores. End of story, calibrated usage does not
   depend on a daemon."* And: *"Nothing depends on daemon except the integration with coding agents we'll
   work on in the future."*
3. **On-board, SW14 (shipped)** — owner: *"Only it's not a key. Use one of the switches in the back. What
   are they mapped to while the macropad is booted? If either is not mapped to anything, just turn that
   into calibrate."* Measured answer: SW14 (`BOOTSEL`→GND via R6 1k to `QSPI_CS`) is read only by the mask
   ROM at power-up and is **inert while firmware runs**; SW15 (`RUN`→GND) is a hardware reset line with no
   runtime visibility. So SW14 was free, and it was the right answer.

**Lesson for the ledger:** a self-imposed constraint that is never re-examined produces architecture. The
"LOCKED" protocol cost two design rounds. Locked means *changes are adjudicated*, not *changes are
impossible* — v1 is that adjudication.

### What shipped

- **On-board routine**: hold SW14 ~1 s → 13 key LEDs are the whole UI (white armed / blue bar centring /
  amber→green bar swinging / green stored / red rejected / dim-white aborted) → EEPROM. ~15 s, bounded,
  abortable, keys stay live throughout, no mode and no layer change. Refuses to arm until it has observed
  SW14 *released* at least once — which also keeps it inert in emulators where the pad reads pressed forever.
- **Protocol v1** `0x50 GET_JOYSTICK` / `0x51 SET_CALIBRATION` / `0x52 RESET_CALIBRATION`. IDs chosen
  **outside VIA's 0x01-0x13** (measured from `quantum/via.h`; the first-draft 0x05/0x06/0x07 collided with
  `dynamic_keymap_set_keycode`/`reset`/`custom_set_value`), so `via_command_kb()` claims them
  unconditionally with none of the tail-zero heuristics 0x01-0x04 require.
- **One store, two callers**: SW14 and 0x51 both call `js_cal_store()`, so byte-identity is structural.
  Proven sensitive, not vacuous: under the ADC-lag counterfactual the referee fails by **exactly 8 bytes**.
- **Per-axis centre/threshold** replace the shared `JS_CENTER 512` / `JS_THRESHOLD 300`, which remain the
  uncalibrated fallback so a never-calibrated board behaves exactly as before. Native HID gamepad axes are
  rescaled too — `joystick_axes[]` proven non-const and in `.data`/SRAM, not `.rodata`.
- **Encoder**: `ENCODER_DIRECTION_FLIP` set from the owner's bench measurement on the first assembled board
  (clockwise produced volume-DOWN). `vial.json` gained the encoder declaration it never had — schema derived
  from vial-gui's own parser and two in-tree keyboards, which is why only the push button had been visible.
- **Retired**: `keymaps/calibrate/`, `sim/calibrate.cjs`, the calibrate UF2. **Renamed**: `agentpad13.uf2`
  (`a7b8da85…`, vial, the one users want) and `agentpad13_reference.uf2` (`4caac0bc…`, default,
  byte-reproducible). Owner: *"'default' should be something people can drag and drop to use."*

### Hard-won facts worth not re-deriving

- **`sw14_pressed()` MUST be RAM-resident.** Reading SW14 overrides `QSPI_CS`, during which XIP flash is
  unreadable. Proven by `nm`: `20000000 0000004c t sw14_pressed`, section `.data`, no `bl`, no flash
  literal, both register-alias constants inside its own RAM extent. If a future pass moves it to flash the
  board hard-faults on every button press.
- **Critical section = 14,016 cycles = 112.1 µs**, hand-counted off the shipped disassembly. The coordinator's
  50-65 µs projection was WRONG: `volatile int i` forces a stack load *and* store per iteration (14-cycle
  body, not ~6). 112 µs is also pico-sdk's own `get_bootsel_button()` window — matched deliberately, not
  inflated. Safe because `wear_leveling_rp2040_flash.c:185-203` already masks interrupts for a flash *erase*
  (~50-400 ms) on every Vial keymap save: 450-3500× longer.
- ⚠️ **The emulator reports 96.2 µs and it is WRONG** — rp2040js charges taken branches 2 cycles where
  Cortex-M0+ costs 3 (2,000-cycle gap over 1000 iterations). **112.1 µs is authoritative.** Both numbers and
  this reason are recorded in `loudest_micro.c` and `joystick.cjs`. This is the single most likely thing for
  a future pass to "correct" backwards.
- **rp2040js cannot write flash at all** out of the box (`RPSSI` discards `DR0`, `IO_QSPI` unimplemented), so
  every EEPROM write was a silent no-op and "stored in EEPROM" was unfalsifiable. `joystick.cjs` now attaches
  a byte-level serial-NOR model + `IO_QSPI` register file. Two non-obvious requirements found by measurement:
  the FIFO must answer while CS is HIGH (boot2's `flash_exit_xip()` clocks dummies through the same path —
  gating on CS-low hangs in ROM at `0x1784`), and must clear at BOTH CS edges (else exactly five writes
  succeed and the sixth hangs).
- **First flash of a v1 build re-initialises Vial's dynamic keymap once** — `EECONFIG_KB_DATA_SIZE 14` shifts
  `VIA_EEPROM_MAGIC_ADDR`. One-time, documented in `BRING-UP.md`.

### Gates (verbatim)

```
behavior.cjs, both builds, 4-way --touch/--encoder : 0 / 2 / 4 / 6 failures  (board·board PASS 33/33)
joystick.cjs, both builds                          : 62 checks, 0 failures — PASS
joystick.cjs --no-eeprom / --no-adc-fix, both      : 62 checks, 6 failures — FAIL (both required)
run_conformance.py                                 : PASS all 410 protocol v0+v1 checks
check_pins_v4.py                                   : 30/30 and 56/56
qmk lint --strict (default)                        : Ψ Lint check passed!
emulator smoke default / vial                      : EMULATOR SMOKE: PASS (both)
daemon pytest                                      : 219 passed
board md5                                          : 221ebb98fcf44f860ed65f7ed8d1bc45 UNCHANGED
```

Conformance grew 80 → 410 and the daemon suite 131 → 219. The host executor mutation-tested its own new
checks seven ways and reverted each — and recorded a trap: a same-size edit plus a stale `__pycache__`
produced three phantom failures, so any mutation testing here must clear `__pycache__` between steps.

### Contract amendment, adjudicated not silent

`docs/PROTOCOL-V1-CONTRACT.md` §Write policy originally admitted only 0x51 and 0x52. The on-board routine is
a third writer, so the clause was **amended with the owner's directive quoted**, and its intent restated as
still binding: every write is user-initiated and rare; nothing periodic, background, opportunistic or
automatic exists; **continuous auto-calibration was explicitly proposed by the coordinator and explicitly
rejected by the owner — that rejection stands.** The contract also gained a rounding clause (`floor`,
`half * 3 / 5`) after both implementations agreed only by luck.

### Deliberate non-actions

`behavior.cjs` extended (encoder A/B) but never edited to pass — watch hash `c9dea90f…` unchanged end to end.
Board, schematic, fabpack, case untouched. `v5-release-compiled/` and the public mirror deferred to wave 6 —
⚠️ **the bundle's `BRING-UP.md` currently instructs flashing the deleted calibrate UF2**, a broken instruction
in the shipping deliverable until that sync lands.

## v5_7 — underglow LED20/LED21 rotated 180° so the bottom pair fires inward (2026-08-19, executor)

**Base:** `v5/hardware/pcb/v5_6.kicad_pcb` md5 `221ebb98fcf44f860ed65f7ed8d1bc45` — verified at load and
**re-verified UNTOUCHED at close** (`.kicad_pro` `21155fc0f4eb6f798484edca0e04d403` likewise). Working copy =
`v5_7_work`; base never mutated. Tools: pcbnew/kicad-cli 9.0.9. No git operations performed.

**Owner directive (verbatim):** *"flip the two bottom LEDs to shoot inwards"*, with the reduced scope
pre-authorised verbatim: *"if it's really difficult with the top LEDs (it might be more crowded), that side
looks kinda cool with the hotspot near the USB, just rotate the bottom ones."* LED15/LED16 are therefore
**deliberately left outward-firing** and were not touched, nor were the left/right rails.

**Root cause — re-derived from the board, not inherited.** `gen/build_pcb.py:82` declares
`UGLOW_ROT = [180,180,90,90,90,0,0,270,270,270]`, a coherent all-inward set **in the un-flipped frame**;
`:252-254` applies the rotation and *only then* flips the part to B.Cu. `FOOTPRINT::Flip(FLIP_DIRECTION_
TOP_BOTTOM)` mirrors local geometry in Y **and negates the orientation**, so emission goes
`(−sinθ,−cosθ) → (−sinθ,+cosθ)`: parts aimed along ±Y (top and bottom pairs) **reverse**, parts aimed along
±X (left and right rails) **survive**. Empirically on this board the pad-row offset for a flipped part is
`0.65·(−sin ρ,−cos ρ)` and emission is the opposite face, giving `e = (sin ρ, cos ρ)` for stored angle ρ —
which reproduces the stored `180/180/−90/−90/−90/0/0/+90/+90/+90` exactly. 6 inward / 4 outward confirmed.

**Manifest — exactly 2 footprints, `rot` only.** LED20 `(65.694952, 94.374007)` and LED21 `(18.3, 96.3)`,
both B.Cu, `rot 0 → 180`. x/y/side unchanged; every pad keeps its net. New pad rows land 1.3 mm south
(LED20 pads y 94.374–95.674 @ x 64.4225/65.2725/66.1225/66.9725; LED21 pads y 96.30–97.60 @ x
17.0275/17.8775/18.7275/19.5775), and pad order reverses west→east to `Din, +5V, Dout, GND`.

**⚠️ REGISTERED PREDICTION VIOLATION — 4 signal vias, declared BEFORE mutating, coordinator-APPROVED.**
The brief's register said "no via added or moved". That is **topologically infeasible** with the specified
straight +5V drop, and the arithmetic was reported before any copper moved:
- No between-pad escape: pitch 0.85 − pad 0.42 = **0.430 mm** gap; a 0.152 trace with 0.152 clearance both
  sides needs **0.456 mm** → deficit **0.026 mm**.
- The +5V feed to pad2 (which now sits *between* Din and Dout) is a continuous barrier from the trunk to the
  pad row; north of it is sealed by the 0.5 mm +5V trunk (`y = 92.3463, x 46.30→65.45` at LED20).
- Both data nets therefore detour south, where their spans strictly interleave — at LED20 RGB_D19 spans
  `[64.4225, ≈68]` and RGB_D20 spans `[62.30, 66.1225]` — forcing a crossing **in either lane order**.
⇒ one layer hop per LED (2 vias each). The via-free alternative (re-plumb +5V into pad2 from outside the
Din..Dout span) was measured as available but **REJECTED by the coordinator**: it stretches C45→LED20.2 from
**1.16 mm to ≈8 mm** (and C46→LED21.2 likewise) and adds ~12 mm of 0.5 mm power copper — trading a *data*-line
via against a *decoupling* path, which are not comparable quantities. Ruling: "Two 0.5/0.2 vias on an 800 kHz
WS2812 data line are electrically nil… degrades the one thing a local decoupling cap exists to do." Also the
minimal-destruction call — re-plumbing a power feed is a larger displacement than a layer hop (§7 ladder).

**RIPS — 9 segments, every one endpoint-asserted before deletion.** LED20: `RGB_D20 6bae227a, 07e89c86,
c11bb942`; `+5V 3d8c9921, 8d3b0b15`. LED21: `RGB_D20 1201968f`; `+5V 1265bd62`; `RGB_D21 1268f011, 26fd3cba`
(re-laid shortened; new east end `(16.3, 93.713)` is exactly on its original 45° line `y = x + 77.413`).
**RGB_D19 was NOT ripped at all** — better than the brief's manifest, which anticipated re-landing
`45089f97`; instead the via lands on that segment's existing west endpoint and it stays byte-identical.
**Preserved:** `45089f97`, `697a0022`, `df7a2519`, `d1e08c2f`, `9b2be037`, `89e7fd60`, `952bb219` (the last
left in place deliberately — fully overlapped by `89e7fd60`, same net, both endpoints landed; ripping it
would destroy copper the fix does not require).

**NEW COPPER — 18 tracks + 4 vias.**
- LED20 `+5V` (0.5 mm, B.Cu): `C45.1 (65.4527, 92.3463) → pad2 (65.272452, 95.024007)` — one straight
  segment, clearance to pad1/pad3 **0.390 each**. Decoupling path stays 1.16 mm.
- LED20 `RGB_D19`: via `(66.9675, 93.7240)` → F.Cu `y = 93.724` → via `(64.422452, 93.7240)` → B.Cu south
  into pad1. Via-to-+5V-drop margins **1.104 / 0.435**.
- LED20 `RGB_D20`: pad3 → south `y = 96.5` → west → north at `x = 63.4` → rejoins the preserved trunk at
  `(62.2999, 94.6042)` along the *proven* horizontal approach vector. H7 NPTH (Ø2.2 @ 61.0, 96.0) clear by
  **1.224 mm**.
- LED21 `+5V` (0.5 mm): `C46.1 (18.723, 94.1) → pad2 (17.8775, 96.95)`, straight.
- LED21 `RGB_D20`: `(20.9022, 94.3203)` → south → west `y = 98.9` → north into pad1 (no vias).
- LED21 `RGB_D21`: pad3 → south → via `(18.7275, 97.95)` → F.Cu → via `(16.3, 97.95)` → north, rejoining the
  shortened diagonal. **The F.Cu jumper had to sit at y = 97.95, not in the north band**: `TP5_touch`
  (F.Cu, x 6.525–20.525, y 81.850–95.850, net TOUCH_PAD) carries a **1.000 mm local clearance**, so any F.Cu
  near LED21 must stand ≥1.076 mm off it. TP5 pour consequently held at **177.0 mm²**, unchanged.

**GND:** no GND *track* changed and **no stitch via was needed** — both rotated GND pads took zone thermals
in open field (proved by `unconnected 0`). GND differs only in zone-fill polygons, inherent to refill.

**PHASE gates (BANKED file `v5_7.kicad_pcb`) — `grade_board.py --no-ring` VERBATIM:**
```
  [PASS] DRC errors   : 0
  [PASS] unconnected  : 0
  [PASS] contract     : 45/45 refs ok
  [PASS] ABSENT H1-H4 : none present (v3)
  [PASS] outline bbox : 84.200 x 100.000 mm (target 84.2 x 100.0 +/-0.15), chamfer=ok
  [PASS] +5V spine    : 183 segs, min=0.5000, 0 under 0.500
  [PASS] USB pair     : clean
  [PASS] TP5 pour     : 177.0 mm2 @ 0.00mm from center
RESULT: PASS (all gates green)
```
`+5V spine 184 → 183 segs` (3 ripped, 2 added) — the gate is min-width, not count.

**Independent diffs vs v5_6:** 126/126 footprints, **only LED20 and LED21 differ, and only in `rot`**;
414/414 pads with **0 net changes**, 8 moved pads, all on those two refs; per-net copper diff = exactly
`{+5V, RGB_D19, RGB_D20, RGB_D21}`, **nothing outside**.

**Contract — ADJUDICATED (not convenient).** `contract_v4.json` LED20/LED21 `rot 0.0 → 180.0` (:285, :291),
`status` appended and a third `cross_check.adjudications` entry added quoting the owner's directive verbatim
and recording the flip-after-rotate mechanism. Lockstep: `CONTRACT-V4-PROPOSAL.md:57,58` and
`grade_board.py` **EXPECTED_TABLE line 1019 only**.

**Fabpack:** rebuilt into `v5/hardware/pcb/fabpack_out_v5_7/`; `verify_fabpack.py` **RESULT: 31/31 checks
PASS**, ratsnest 0. Drill census 285 → **289** (PTH 237→241, vias 182→**186** = exactly the 4 authorized
vias; NPTH unchanged at 48). CPL/BOM diff vs `fabpack_out_v5_6`: **translucent CPL differs in exactly the 2
predicted rows** (`LED20`/`LED21` `Rot 0.000000 → 180.000000`, PosX/PosY/Side identical); **both BOMs and the
afterlist byte-identical**.

**DEVIATION FROM THE REGISTER (reported, not a defect):** the register predicted "the CPL changes exactly 2
rows in **both** SKUs". Actual: **2 rows translucent, 0 rows opaque** — the entire underglow ring LED15–24 is
DNP on the opaque SKU (opaque CPL contains 0 of the 10; translucent contains all 10). Correct-by-policy, but
the prediction was wrong in detail and is recorded as such.

**Renders — banked and read.** `v5_7_render_top.png`, `v5_7_render_bottom.png`, `v5_7_led_zoom.png`, plus the
orientation pair `orient_v5_6.png` / `orient_v5_7.png`.
- **Known gate weakness, now closed.** The standard pad/copper plot draws no body, no silk, no pin-1 marker
  and no emission indicator; a 180° rotation of this part moves the four pad x-positions by **0.004952 mm**.
  That plot is structurally incapable of showing this defect, which is why it shipped. New tool
  `hardware/pcb/harness/render_orientation.py` (documented in `TOOL-REFERENCE.md`) draws the pad row, the
  pin-1/DIN pad, the Fab body outline and an emission arrow per part, prints an INWARD/OUTWARD tally against
  the board's own Edge.Cuts centroid, runs against any board file, and gates via `--expect-inward N`.
  Measured: **v5_6 = INWARD 6 / OUTWARD 4** (the defect) → **v5_7 = INWARD 8 / OUTWARD 2** (GATE PASS).
- Read of `orient_v5_7.png`: LED20/LED21 bodies now show the pad row on the board-edge side and the lens
  (chamfered face) inboard, arrows pointing north into the field; LED17–19 pad rows east / arrows west;
  LED22–24 pad rows west / arrows east; LED15/LED16 unchanged, arrows north off-board **by design**.
- Read of `v5_7_led_zoom.png`: both +5V drops short and straight into pad2; the RGB_D19 F.Cu jumper spans the
  vacated 1.3 mm band between its two vias; RGB_D20 leaves LED20.3 southward and rejoins the preserved trunk
  clear of H7; at LED21 the RGB_D21 via pair sits south of the pad row, clear of the RGB_D20 lane and of the
  bottom-left chamfer. SW14/SW15, BOOTSEL, C45/C46 and H6/H7 untouched.
- Read of the full-board pair: octagon and both chamfers intact, MCU cluster/USB/switch matrix unchanged.

**Generator fixed:** `build_pcb.py:82` → `UGLOW_ROT = [180,180,90,90,90,180,180,270,270,270]` with a dated
comment block explaining the rotate-then-flip trap, spelling out which indices are pre-compensated, and
flagging that **LED15/16's outward aim is intentional — do not "correct" it**.
**HONEST CAVEAT:** `build_pcb.py` still does **not** reproduce the shipped board regardless of this fix — its
`UGLOW` *positions* are stale (it holds LED20 at `(61, 99)` vs the shipped `(65.694952, 94.374007)`; LED17–24
were hand-nudged). Out of scope by instruction; recorded here rather than fixed.

## v5_7 — **BANKED** (2026-08-19, executor)
`v5/hardware/pcb/v5_7.kicad_pcb` md5 **`08cf68dae979ab28aadd5e0dda34de01`**
(+ `v5_7.kicad_pro` md5 `21155fc0f4eb6f798484edca0e04d403` = byte-identical to v5_6's, filename-only diff,
same as the v5_5→v5_6 precedent). Base `v5_6` re-verified UNTOUCHED (`221ebb98fcf44f860ed65f7ed8d1bc45`).
Official fabpack: `v5/hardware/pcb/fabpack_out_v5_7/` — 31/31 PASS. **v5_6 and `fabpack_out_v5_6` remain the
fabricated/populated revision; v5_7 is the public-release + future-spin fix, NOT a rescue of hardware in
hand.** ORDER HOLD STANDS. UNDERGLOW BOTTOM-PAIR ROTATION COMPLETE.

## v5_8 — prediction register before mutation: optional touch contact + factory RE1 (2026-08-24)

**Owner directives:** the touch bridge is optional and user-soldered; a builder may solder a spring, a
wire, another conductive contact, or nothing. RE1 is factory-populated alongside JS1 with **no** encoder
geometry, footprint, placement or routing change. The accepted joystick toppers/restrictor and all other
board, case, firmware and mechanical geometry are out of scope. The separate touchpad/gesture investigation
is not a v5_8 input.

**Verified base:** `hardware/pcb/v5_7.kicad_pcb` md5
`08cf68dae979ab28aadd5e0dda34de01`; `v5_7.kicad_pro` md5
`21155fc0f4eb6f798484edca0e04d403`. Both match the banked v5_7 ledger entry above.

**Board mutation manifest — exactly one footprint, no routing:** TP5 remains at `(13.525, 88.85)`,
F.Cu, rotation 0, pad 1 on `TOUCH_PAD`. Its stock KiCad test-point footprint changes from
`TestPoint_Pad_D1.5mm` to stock `TestPoint_Pad_D4.0mm`: pad and F.Mask opening Ø1.5 → Ø4.0, with the
stock footprint's corresponding silk, courtyard, description and label offsets. Ø4.0 is the largest
standard pad-only test-point footprint shipped by the installed KiCad 9 library, not a custom spring
dimension. The pad remains inside the existing 14 × 14 mm same-net sensing pour. No track, via, zone
outline, other footprint, board outline, net, pad number or pad-to-net assignment may change. `v5_7`
itself is immutable; work occurs only in new `v5_8_work`/`v5_8` files.

**Source/manufacturing metadata manifest:** TP5's schematic footprint binding and the schematic generator's
dedicated touch-pad binding move to `TestPoint:TestPoint_Pad_D4.0mm`; no symbol, pin, wire, net or other
schematic property changes. RE1 stays `PEC11R-4215F-S0024` / LCSC `C143790`; only its assembly annotation
changes hand-solder → `PCBWay-THT`. The optional contact is recorded as an unpriced, user-selected
spring/wire accessory and must never enter the factory CPL or turnkey BOM.

**Predicted downstream diffs:** both CPLs gain exactly one top-side RE1 row at its unchanged position and
rotation; both fab BOMs gain exactly one placed RE1 group; the always-hand-solder RE1 row disappears from
the afterlist, which retains the documented optional opt-out rows plus the optional user touch-contact
accessory. Gerbers may differ only on TP5 F.Cu/F.Mask and its non-fabrication silk metadata; drill files and
drill census are byte-identical. LED20/LED21 remain at v5_7's corrected 180° rotations. Any diff outside
these predictions is a STOP condition.

### v5_8 bank and verification record (2026-08-24)

**Banked artifacts:** `v5_8.kicad_pcb` md5 `8c32ff4a6e6d77a87c4584029d4a1c75`, sha256
`b6974f39eae3d65243b4cfbf1d19c503cab709d1b31ba3483b19a1308575e903`;
`v5_8.kicad_pro` is byte-identical to v5_7 (md5 `21155fc0f4eb6f798484edca0e04d403`, sha256
`33ac132acbec26d44ab08d661ddeca26a7288b114b4980c209865d872b6c5592`). The immutable v5_7 base
rechecked at its original md5 `08cf68dae979ab28aadd5e0dda34de01` / sha256
`45f1b4b9632c3a42f85a4dd2350bc1ae9b9e65e33300be7a8eb36dc57b967e8a`.

**Intentional-diff proof:** pcbnew readback found 126/126 footprints, with `TP5` the only changed
footprint. Track/via records are identical (1311/1311), zones identical (3/3), and board drawings
unchanged (47/47). RE1 footprint, position `(6.025, 10.0)`, rotation 0, side and pads are identical;
only its external source/BOM assembly classification changed. TP5 remains `(13.525, 88.85)`, F.Cu,
rotation 0, pad 1 `TOUCH_PAD`; only its pad/mask diameter changes 1.5 → 4.0 mm with the stock
footprint's silk/courtyard/text metadata. LED20/LED21 remain 180° in both v5_7 and v5_8.

**Electrical gates:** `grade_board.py v5_8_work.kicad_pcb --no-ring` returned PASS: DRC errors 0,
unconnected 0, contract 45/45, outline 84.200 × 100.000 mm, +5V minimum 0.5000 mm, USB clean and
TP5 pour 177.0 mm². Fresh KiCad schematic netlist export has the same 89-net pin/connectivity graph as
the pre-change source; RE1 changes assembly metadata only. Standalone CLI ERC reported 0 errors and
341 missing-library-table warnings while reading the embedded-symbol schematic.

**Manufacturing gates:** `fabpack_out_v5_8/` rebuilt from the banked board and
`verify_fabpack.py` returned **37/37 PASS**. Opaque = 91 CPL placements / 30 BOM lines / 23 DNP;
translucent = 111 / 30 / 3. RE1 is present once in both CPLs at unchanged
`6.025000,-10.000000,0.000000,top`, and once in both factory BOMs as exact
`PEC11R-4215F-S0024` / `C143790` / `PCBWay-THT`. RE1 is absent from the afterlist; the afterlist has
three rows: socket opt-out, tact opt-out and optional `TP5_CONTACT`. Gerber content comparison against
v5_7, ignoring generated timestamps/project identifiers, is identical on B.Cu, both back technical
layers, Edge.Cuts, F.Paste and both drill files; the only fabrication changes are the expected Ø4.0
TP5 aperture on F.Cu/F.Mask plus its front-silkscreen footprint graphics.

**Release boundary:** this revision passed the digital release gates and received explicit owner
approval for public promotion on 2026-08-24, so v5_8 replaces v5_7 as the public build. It has not
yet been fabricated as a first article; that physical validation remains an honest release caveat,
not a blocker on the open-source files.

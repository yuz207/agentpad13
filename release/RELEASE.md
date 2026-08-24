# v5-release-compiled — release checkpoint (2026-07-20, band default updated 2026-07-24, SW14/15 BOM corrected 2026-08-05, board refreshed to v5_7 2026-08-19, plate encoder opening widened 2026-08-19, band plate-pocket fit corrected 2026-08-19, tray bases published 2026-08-20, base catalog finalised 2026-08-20, joystick outputs refreshed 2026-08-24)

Self-contained snapshot of the v5 deliverables. Every file here is a **COPY**;
the originals remain in their working locations. This bundle mirrors the
`v4-release-compiled/` (Rev A) pattern, scoped to the v5 diff. Companion
contract: `MANIFEST.md` (every file, md5, provenance).

> **Revision 2026-07-24 — band `WALL` default 3.0 → 5.4 (owner decision).** The
> band STL/STEP in this bundle are now `…_w5.4` (primary) plus the `…_w3.0` and
> `…_w7.4` gated variants. The superseded 2.4 mm-sidewall band
> (`agentpad13_v2_band_1.6mm.stl`, `36980cc2…`) has been **removed from this
> bundle** — it is the geometry PCBWay flagged as too thin and must not be
> printed; it survives only as a historical artifact in the working tree. Case
> script, `CASE-V2-NOTES` (new §18), `mechanism.json`, the gasket kit and the
> fitment renders were refreshed to match. Board, fabpack, plate and firmware
> artifacts are **untouched**.

> **Revision 2026-08-05 — SW14/SW15 tact switch MPN corrected (PCBWay component
> verification catch).** The BOOT/RESET tacts were specified as XKB **TS-1187A
> (LCSC C318884)** against the footprint `SW_SPST_PTS645Sx43SMTR92` — a C&K PTS645
> **6.0 × 6.0 mm / H4.3 gull-wing** land pattern. The TS-1187A is a **5.1 × 5.1 mm**
> part with a **6.5 mm lead span** against this footprint's **7.96 mm** pad span: its
> leads land ~45 µm over the pad edge (~9 % pad overlap) — **not solderable.** The
> shipped part is now C&K **PTS645SM43SMTR92 LFS** (LCSC **C221880**, DigiKey
> CKN9112CT-ND, 160 gf, SPST-NO), land-pattern-verified to 0.01 mm X / 0.00 mm Y.
> Approved drop-in alternates (identical land pattern): Omron **B3S-1000P**
> (C180420), Megastar **ZX-QC66-4.3TP** (C7470150), C&K **PTS645SK43SMTR92 LFS**
> (DigiKey CKN9084CT-ND, 260 gf). **FORBIDDEN substitution:** C&K
> **PTS645SM43JSMTR92 LFS** (C2801847) — one inserted letter, **J-lead**, different
> land pattern. Cost impact ≈ **+$0.59/board** for the pair ($0.018 → $0.313 each).
> **Metadata-only change:** only `assembly/bom_opaque.csv`,
> `assembly/bom_translucent.csv`, `assembly/hand_solder_afterlist.csv` and the two
> `fabpack_*.zip` (those members only) moved — **every Gerber, drill, drill map,
> CPL, `build_manifest.json`, `build_report.txt` and board source were
> byte-identical.** `verify_fabpack.py` grew a new
> BOM-MPN-vs-footprint gate (26 → **31 checks**) so this class of error cannot ship
> silently again.

> **Revision 2026-08-05 — this bundle's plate fab set was PRE-TRIM; re-synced.**
> The nine plate artifacts in `hardware/case/v2/fab/` were the files as they
> existed BEFORE the owner's 2026-07-21 long-axis trim, so they measured
> **84.400 × 100.200 mm** — 0.2 mm outside the fab's **≤100 mm promo tier**, the
> exact ~25 % upcharge the trim was ordered to avoid. Anyone using this bundle as
> the self-contained payload it is meant to be would have uploaded the oversized
> plate. All nine (`agentpad13_v2_plate_v5` / `_tented_ring_v5` / `_blank_v5`
> `.kicad_pcb`, the three gerber zips, the DXF, and the top PNG/SVG) are now
> re-synced from the trimmed source and measure **84.400 × 100.000 mm**. The
> change is **outline-only** — 8 of 93 primitives (4 edges + 4 corner arcs); every
> switch cutout, the encoder and joystick openings, the touch/LED holes and all
> four M3 screw holes keep their exact positions, and `validate_fab_v5.py` passes
> 3/3 variants post-trim (`bbox 84.400 x 100.000`, shapes 89, NE→screw web 1.555
> over the 1.5 floor). **Board, fabpack and firmware artifacts are untouched**
> (board md5 `221ebb98…`). `CASE-V2-NOTES` gains §19 as the trim's §-record and
> annotates §14's pre-trim transcript in place; `MANIFEST.md`'s nine plate rows
> carry the new md5s. Also in this revision: `HOW-TO-ORDER.md`'s gasket stock
> corrected **1–2 mm → 0.5 mm** (the kit sizes its segments for ~40 % compression
> into the band's 0.3 mm ledge gap; 1–2 mm cannot enter that gap), and the 12
> ordered PCBWay keycap STLs are adopted into `MANIFEST.md` (117 → 129 rows,
> self-verification **9/9**).

> **Revision 2026-08-13 — FIRMWARE REBUILT: TTP223 touch polarity was
> ships-broken.** The shipped UF2s assumed the capacitive touch pad was strapped
> **active-low**; the fabricated board straps it **active-high** — `R10` (0 Ω)
> ties `TOUCH_AHLB → GND` on the current `v5_7.kicad_pcb`, and on a TTP223 an AHLB low
> selects active-high output, so `GP16` idles **LOW** and drives HIGH while
> touched. QMK reads a direct pin's LOW as *pressed* and this tree defines no
> `MATRIX_INPUT_PRESSED_STATE`, so matrix `[3,2]` — the layer-cycle key — read
> **held from power-on**: the pad booted into layer 1 and could never reach layer
> 0, every `F13`–`F24` macro key was unreachable, `SW1` emitted nothing (layer 1
> maps `JS_MODE` there), the encoder became `RGB_MOD` instead of volume, and
> touch fired on finger **lift**. Boards are already fabricated **and
> populated**, so the `R10`-to-`+3V3` rework escape hatch was not available and
> the fix is **firmware-only**: `GP16` is removed from `matrix_pins.direct`
> (`[3][2] = null`) and polled in `loudest_micro.c` (`matrix_scan_kb()`) with its
> own active-high sense, injecting the key event at the **same** logical position
> `[3,2]`. `MATRIX_INPUT_PRESSED_STATE 1` was rejected: `quantum/matrix.c` applies
> it globally and would invert the 13 genuinely active-low switches. Keymaps,
> `LAYOUT`, matrix size, keycodes, `TP_TOG` and the RGB layout are unchanged.
> **Both UF2s in `firmware/prebuilt/` are replaced**: `loudest_micro_default.uf2`
> `4af788ae…`/88064 B → **`cf5bd628…`/88576 B**, `loudest_micro_vial.uf2`
> `e5008942…`/104448 B → **`b31673a7…`**/104448 B; `firmware/POLARITY-NOTE.md`
> re-hashed to match. Gate: `firmware/sim/behavior.cjs` (rp2040js, boots the real
> UF2) **33/33 PASS under `--touch=board`** on both builds — it was **4 failures**
> before — with all 13 switches, 24 LEDs, the encoder and the joystick still
> passing. **Board, fabpack, plate and case artifacts are untouched** (board md5
> `221ebb98fcf44f860ed65f7ed8d1bc45`).

> **Revision 2026-08-15 — ALL THREE UF2s REBUILT, and the bring-up procedure now
> ships in this bundle.** Two ledgered firmware passes land here together:
> `v5/V5-NOTES.md` *"BRING-UP CALIBRATION FACILITY — the ADC sweep gets a
> mechanism; finding 2 CLOSED"* (2026-08-13) and *"FIRMWARE PERFECTION PASS —
> finding 7 closed in code, finding 4 closed by decision, the double
> `housekeeping_task_user()` trap removed"* (2026-08-15).
>
> **(1) Bring-up calibration facility — NEW, and it is why this bundle grew two
> files.** Every document in this project told the owner to "do the bring-up ADC
> sweep" and **none said how**: raw-HID protocol v0 is LOCKED and carries no ADC
> readout, and Vial exposes no raw analog, so the joystick's real `low`/`rest`/
> `high` could not be got off the board at all. The board is a keyboard, so it
> now **types its own calibration report**: a third prebuilt,
> `firmware/prebuilt/loudest_micro_calibrate.uf2` (`aabf7954…`, 96768 B), turns
> every key into a calibration function, and four guided `SW1` presses produce
> the measured endpoints, a per-axis `inverted=YES/NO` verdict, a re-derived
> `JS_CENTER`/`JS_THRESHOLD`, a per-direction `fires`/`NEVER FIRES` verdict
> against the **shipped** constants, and finished copy-pasteable config lines
> with the `POLARITY-NOTE.md` `low`/`high` swap **already applied** to any
> inverted axis. **It is a bring-up TOOL, not daily firmware** — it emits no
> normal keystrokes; flash it once, read the numbers, flash the real build back.
> The owner-facing procedure ships here as **`firmware/BRING-UP.md`** (new,
> byte-identical to the working-tree file; split out of `firmware/BUILD.md` §4a
> on 2026-08-15 precisely so a bundle reader gets the procedure without the
> toolchain guide, the same arrangement `firmware/POLARITY-NOTE.md` has).
>
> **(2) The RGB coordinate space is now ISOTROPIC (finding 7, closed in code).**
> The board is portrait (84.2 × 100.0 mm) but QMK's matrix space is 224 × 64, and
> the layout generator had normalised each axis independently (x 2.660 units/mm,
> y 0.640 units/mm) — a **4.157 : 1** distortion under which the four
> geometry-bearing animations (`cycle_pinwheel`, `cycle_spiral`, `dual_beacon`,
> `rainbow_moving_chevron`) render visibly skewed. One scale now applies to both
> axes (`s = 64 / bbox_height = 0.64`), centred on QMK's own effect origin
> `k_rgb_matrix_center = {112, 32}`; aspect ratio **4.157 : 1 → 1.000 : 1**, all
> 24 `y` values numerically unchanged, `flags` and `matrix` untouched. The
> generator now **refuses to emit** unless it re-measures `s == 0.64` and
> `x_center == 42.1` off the board file, so it cannot silently produce a layout
> for a board whose outline moved. Proven **from the shipped binary**, not from
> the JSON input: `g_led_config` was located in the `default` ELF, its 88-byte
> initialiser read out of `.data`, and those exact bytes found inside the
> shipped UF2 payload at offset 42676 — LED cloud x 88..136, exactly symmetric
> about 112. *Visual appearance on hardware remains a first-power-on
> observation; no harness here renders animations.*
>
> **(3) The duplicate `housekeeping_task_user()` call is gone.** vial-qmk's
> `housekeeping_task()` (`quantum/keyboard.c:436`) already calls the user hook,
> and this keyboard's `housekeeping_task_kb()` called it **again** — twice per
> loop. Harmless while no keymap implemented it; the 2026-08-13 `calibrate`
> keymap then became exactly that keymap and only survived because draining its
> typing queue is idempotent. Every other `_kb → _user` chain in the file was
> re-verified against the fork's sources and left alone; **exactly one hook was
> double-called.**
>
> **(4) `CAPS.led_count` stays 24 on both SKUs — finding 4 CLOSED BY DECISION,
> no code change.** The byte is redefined as the **addressable chain length**,
> which is electrically true on both SKUs: on the opaque SKU (LED1-14 populated)
> LED14's DOUT clocks pixels 14-23 into an unpopulated pad, so host writes to
> indexes 14-23 are harmless no-ops. Rationale: the byte is part of **LOCKED
> protocol v0**, and forking per-SKU UF2s multiplies the shipped artifacts for
> zero visible benefit. **Zero wire change** — the CAPS reply is byte-identical.
>
> **Artifacts:** `loudest_micro_default.uf2` `cf5bd628…` → **`1c0ff911…`**
> (88576 B, unchanged), `loudest_micro_vial.uf2` `b31673a7…` → **`286fb09d…`**
> (104448 B, unchanged), `loudest_micro_calibrate.uf2` **added** (`aabf7954…`,
> 96768 B); `firmware/POLARITY-NOTE.md` re-hashed (its shipped-bytes table now
> carries all three rows and its bring-up pointer now names `BRING-UP.md`);
> `firmware/BRING-UP.md` **added**. All three byte sizes are unchanged from
> 2026-08-13 — the changes were a 24-entry coordinate table and one deleted call,
> neither of which moves a section boundary. `default` and `calibrate` are
> **byte-for-byte reproducible** (each built twice from a wiped `.build/`);
> `vial` remains non-deterministic run-to-run and its md5 records shipped bytes
> only. **Gates, all re-run on the new builds:** `behavior.cjs --touch=board`
> **33/33, 0 failures** on both default and vial, with the `--touch=firmware`
> counterfactual still **failing 4/33** (the A/B still discriminates);
> `calibrate.cjs` **37/37 PASS** with its `--no-adc-fix` arm still failing 15;
> `check_pins_v4.py` 30/30 and 56/56; protocol conformance **80/80**; emulator
> smoke PASS both builds. **Board, fabpack, plate and case artifacts are
> untouched** (board md5 `221ebb98fcf44f860ed65f7ed8d1bc45`).

> **Revision 2026-08-15 (protocol v1 / on-board calibration) — THE BOARD NOW
> CALIBRATES ITSELF, AND BOTH PREBUILTS ARE RENAMED.** The joystick shipped on
> placeholder calibration and there was no way to replace it. Two designs are
> **retired** by this revision, including the one the revision immediately above
> introduced: the separate bring-up firmware that TYPED its measurements for a
> human to paste back into source and rebuild, and a host-command-only routine.
> Owner's ruling: *"Calibration is stored in EEPROM, no daemon needed. You turn
> on calibration, it fucking calibrates, then it stores. End of story, calibrated
> usage does not depend on a daemon."*
>
> **(1) The primary path is now a button on the board.** Hold **SW14** — the
> BOOTSEL button in the back, which is inert while firmware runs — for about a
> second, and the 13 key LEDs become the whole UI: white armed, a blue bar while
> it finds centre, an amber-to-green bar while you roll the stick to its edges, a
> green flash when it stores (red = rejected, nothing written). ~15 s, bounded,
> abortable with a second press. The result lands in a 14-byte EEPROM datablock
> and **survives unplugging and reflashing**. The keyboard keeps working
> throughout — no mode, no layer change, nothing made inert (the arrow/scroll
> joystick modes stop *emitting* only while the stick is the instrument being
> measured). **No host, no second firmware, no reflash, and no `daemon/`:** a
> builder holding only this bundle can now calibrate a board.
>
> **(2) Protocol v1 is the second path, for host tooling** — `0x50`
> GET_JOYSTICK, `0x51` SET_CALIBRATION, `0x52` RESET. IDs sit outside VIA's
> 0x01–0x13, so in the vial build `via_command_kb()` claims them
> **unconditionally**, with no payload heuristics. SW14 and 0x51 call **one
> shared `js_cal_store()`**, so both paths write byte-identical EEPROM by
> construction — proven, not asserted: the referee fails by exactly **8 bytes**
> when the two are made to disagree. Per-axis centre/threshold replace the shared
> `JS_CENTER 512` / `JS_THRESHOLD 300`, which stay on as the **uncalibrated
> fallback** — a never-calibrated board behaves exactly as it did before.
> `LOUDEST_PROTO_VERSION` 0 → **1**; v0 clients are unaffected.
>
> **(3) Encoder direction flipped** to match the as-built A/B landing measured on
> the first assembled board (clockwise was volume-**down**), and `vial.json` now
> declares the encoder, so Vial's GUI exposes rotation for per-layer remapping —
> it never had, which is why only the push button appeared.
>
> **(4) Artifacts RENAMED; the third prebuilt is GONE.**
> `loudest_micro_vial.uf2` → **`agentpad13.uf2`** (`a7b8da85…`, 109568 B — the
> vial build, and the one to flash), `loudest_micro_default.uf2` →
> **`agentpad13_reference.uf2`** (`4caac0bc…`, 93696 B — the default build, kept
> because it is byte-reproducible). *"default"* was read as *"the one to use"*
> when it is the one **without** live remapping, which is why the names changed.
> **`loudest_micro_calibrate.uf2` is deleted from this bundle** along with the
> `keymaps/calibrate/` keymap and its `sim/calibrate.cjs` referee — protocol v1
> and SW14 replaced it, and it must not be flashed. The sizes grew 2560 B (vial)
> and 2048 B (default): the v1 handlers, the EEPROM store and the calibration
> derivation. `agentpad13_reference` **reproduces byte-for-byte** (two builds from
> a wiped `.build/`); the vial build stays non-deterministic run-to-run, so its
> md5 records shipped bytes, not a rebuild target.
>
> **(5) `firmware/BRING-UP.md` is REWRITTEN, and this bundle's old copy was a
> broken instruction.** It told the owner to flash `loudest_micro_calibrate.uf2`
> — a file that no longer exists anywhere. It now documents the SW14 routine, the
> LED-by-LED table, the failure/cancel cases and the touch/encoder checks, in
> about five minutes and with nothing but a USB cable.
>
> **Watch-item, first flash only:** the new EEPROM block shifts where the layout
> editor keeps its own data by 14 bytes, so the board starts that area fresh
> **once** on the first flash of this version. A layout customised in Vial must be
> redone after this one upgrade; later updates do not repeat it.
>
> **Gates, all re-run on the shipped builds:** `firmware/sim/behavior.cjs`
> **33/33** `--touch=board` on both builds with the encoder A/B discriminating
> across the four arms (**0/2/4/6** failures); `firmware/sim/joystick.cjs`
> **62/62** with **both** counterfactual arms failing **6**; protocol conformance
> **410/410** (device vs `daemon/loudestd/protocol.py`, both written against
> `docs/PROTOCOL-V1-CONTRACT.md`); `check_pins_v4.py` **30/30** and **56/56**;
> daemon suite **219**; `qmk lint --strict` pass; emulator smokes PASS. EEPROM
> persistence is **proven, not assumed** — `joystick.cjs` stores a calibration,
> restarts the emulated MCU carrying only the flash image, and reads it back;
> that required teaching rp2040js to write flash at all (stock, every write is a
> silent no-op). **Board, fabpack, plate and case artifacts are untouched**
> (board md5 `221ebb98fcf44f860ed65f7ed8d1bc45`).

> **Revision 2026-08-19 — this bundle's board was the DEFECTIVE `v5_6`; refreshed
> to `v5_7`.** Four of the ten underglow LEDs fired **out of the case instead of
> into it**. The bundle shipped that board, its fabpack and its renders as the
> candidate order set, so anyone using it as the self-contained payload it is meant
> to be would have ordered the defect. Every board- and fabpack-derived artifact
> here is now the `v5_7` equivalent: `hardware/pcb/v5_7.kicad_pcb`, the renders, and
> the whole `hardware/pcb/fabpack_out_v5_7/` tree (gerbers, drill, CPL, BOM, zips).
> `v5_7` supersedes `v5_6` and is the sole current public board and order set.
> Full detail in diff row **M**; firmware, plate and case artifacts are
> **untouched**.

> **Revision 2026-08-19 (v2.12 plate) — THE ENCODER DID NOT FIT THE PLATE, AND
> THIS BUNDLE'S CASE TREE WAS TWO REVISIONS BEHIND.** The owner assembled the v5
> plate and the encoder fouled the aperture's right-hand wall: the opening is
> **13.000 × 13.000** centred on the shaft, and his encoders measure **~13.7 mm**
> across the pin axis. His directives, in order: *"1) wider hole (I'll measure to
> confirm, left side of hole is perfect, right side needs more space)"*, *"the
> hole needs to be slightly rectangular, not square"*, *"And no, don't widen the
> hole symmetrically, widen to fit the parts."*, *"FYI the top plate hole should
> be 14mm (encoders were around 13.7mm). Left side of the hole is alright good,
> just expand the width to the right by 1mm."*
>
> The opening is now **14.000 × 13.000 R1.5 at (14.025, 12.500)** — the left edge
> **frozen** at x 7.025, the right edge out to 21.025, y 6.000..19.000 unmoved.
> Corner radius stays **1.5 on purpose**: enlarging it would eat exactly the
> body-corner clearance the measured part needs. The knob is independently
> sized as a straight **Ø17.5** body to leave a gap beside the adjacent key;
> it does not attempt to cover this opening. See §(f).
> `ENC_BODY_SQ` stays
> **11.7** — the ~13.7 figure has **no
> resolved datum**, and a shaft-centred 13.7 is contradicted by the owner's own
> left-perfect / right-binding fit, so the opening was sized from the measured
> fit rather than from a guessed body model.
>
> **Three bundle-hygiene defects close with it.** (1) This bundle's
> `validate_fab_v5.py` still asserted the **pre-trim 84.40 × 100.20** outline —
> it would have **rejected the bundle's own shipped gerbers**; it is now the
> current gate. (2) The packaged tray was **pre-v2.8**, predating the base-mount
> interface; it is now **v2.11** (`8bfd7eaf…`) and carries the mirror-at-export
> fix, the 14 discrete edge supports that replaced the LED-blocking rail, the
> notch-depth fix and the 2.0 mm plinth. (3) The plate regeneration ships the
> §20 **`WayWayWay` B.SilkS token for the first time**, discharging §20.4's
> standing generator/on-disk divergence. Section (a) gains row **N**; **board,
> fabpack, firmware and the band are untouched** (band md5 `34be6bf7…`).

> **Revision 2026-08-19 (v2.13 band pocket) — THE PLATE FLOATED 0.8 mm IN A
> POCKET SIZED FOR A PLATE THAT NEVER SHIPPED.** The owner measured a visible
> gap at one end of the assembled deck: *"Is the original board really 100.2?
> Because the gap is closer to 1mm vertically. … we should try to eliminate this
> gap. … This isn't about our existing order, it's about the correct moving
> forward. So no, we don't need to keep the ordered files, this is what
> prototyping is about."*
>
> **Root cause.** The band's plate pocket was `PLATE_H + 2·PLATE_FIT`, and
> `PLATE_H` was **100.2** — the PRE-TRIM plate. The 2026-07-21 long-axis trim to
> 100.000 (row I) was applied only inside the plate generator, as a local
> subtraction, because the band was frozen at the time and `PLATE_H` drives the
> pocket. So the model plate stayed 100.2, the shipped plate became 100.0, and
> the pocket was cut around a plate that never existed. The trim now lives in the
> case model, `PLATE_H` is the shipped 100.0, and the generator consumes it
> directly. **The plate fab files did not move** — proven by a UUID-blind dry
> render of all three variants against the on-disk set: zero geometric delta,
> nothing overwritten.
>
> **The fix, and the ruling behind it.** Pocket **85.0 × 100.8 R5.7 →
> 84.6 × 100.2 R5.5**: a uniform 0.1 mm/side on both axes and the corner radius,
> so the reveal is 0.1 on the flats *and* at the corners (the arcs are exactly
> concentric now; the legacy pocket was not). Plate float 0.6/0.8 → **0.2/0.2**.
> A two-variant plan (tight + a "loose" file for poor printers) was considered
> and dropped on the owner's ruling: *"I'm kind of inclined to make this the only
> version actually. Since even on crappy printers, someone can sand."* **One band
> ships.** The error directions are not symmetric — too tight sands loose in a
> minute, too loose is unfixable — so the shipped fit is the correctable one. If a
> printed pocket binds: sand it, or raise `PLATE_FIT` (one line) and re-export.
> All three wall variants were re-cut in place. **The band ordered in 2026-07 is
> dimensionally the old loose pocket, is usable, and is not recalled.** Board,
> fabpack, firmware, plate fab set and tray are untouched (tray `8bfd7eaf…`);
> section (a) gains row **O**.

> **Revision 2026-08-20 (v2.15 tray bases) — THE INSERTABLE BASES NOW SHIP,
> AND EVERY FOOT RECESS IS GONE.** The base family existed in the repo but was
> in NO release: this bundle carries it for the first time. Owner on scope:
> *"I see the official offering as tray only or tray + insertable bases."*
>
> **Feet are no longer part of the design.** Owner: *"I don't really care about
> bumps or whatever, people can stick whatever they want."* and *"NO, there are
> no more recesses! The only recesses on the tray are the notches for the
> base!"* Every Ø8.3 x 1.0 bumpon recess is deleted — four per full-footprint
> base, four more under the pedestal — so every underside is FLAT, no part
> number is prescribed anywhere, and every stance figure states that it
> EXCLUDES feet. Two measured consequences: the mat's overhang area goes to
> **zero** and the wedge's to **30.25 mm²** (its direction-arrow deboss alone,
> down from 245.87), and removing the pads ENLARGES each support polygon, so
> the wedge now cannot tip in **16/16** load cases (was 14/16).
>
> **The bases are symmetric over x BY DEFINITION, and that is now executable.**
> Owner: *"they should be symmetric over x by definition because why wouldn't
> they be? If they're not, they're designed wrong. This is a fact of the
> design, not something that needs to be memasured."* An exact CAD boolean
> against the part's own x-mirror runs per variant on every build. It caught a
> real violation immediately: the BOOT/RESET service window sits at x
> 58.4..76.6, nowhere near centre, so the mat and wedge were asymmetric. Fixed
> the way the law implies — the window is now a symmetric PAIR.
>
> **The bases are mirrored at export**, the same left-handed-frame fix the tray
> carries. This pass rebuilt every base anyway, so the frame fix rode along at
> zero extra hash cost — the exact condition the band-deferral ruling named.
>
> Rebuilt against the CURRENT v2.11 tray, which surfaced a ghost: `BASE_T` read
> `C.TRAY_T`, so the tray's 2 mm plinth had silently made the mat **4.4 mm
> thick, +83 % mass**. Decoupled to a literal 2.4. Section (a) gains row **P**.
> Band, tray, plate and board artifacts are all untouched.

> **Revision 2026-08-20 (v2.16 base catalog) — THREE BASES, NO BALLAST, AND AN
> 8-DEGREE TYPING ANGLE.** The v2.15 family was a demonstration that the
> central-mount interface works for any shape; this cuts it to a product line.
> Owner: *"I only see the need for two official bases to start. A flat one that
> elevates slightly further, and an angled one at some reasonable degree.
> Perhaps a circular angled one if we want to get stylish like Codex Micro."*
> and *"So I think 2 or 3mm is enough for the riser... And then the pedestar is
> the wedge but just a circular cutout of it from above. No need for the
> ballast if the diameter is reasonable enough. Keep it fucking ismple."*
>
> **`riser`** (new, replaces `mat`): the same 91.6 × 107.4 plan at a **3.0 mm**
> body — one file, two materials, TPU for grip or PETG for a rigid stand.
> **`wedge`**: angle **6.5° → 8.0°**. The owner asked for a real number rather
> than a guess (*"what is a typical mechanical keyboard pitch?"*); researched,
> the mainstream standard is 7°, the comfort band 4–8°, high-profile customs
> 6–8°, and 8.0° is the top of that band because this deck is a 13-key pad, not
> a full-height board. Far edge derives to 17.49 mm. **`pedestal`**: rebuilt
> literally as described — the wedge INTERSECTED with a Ø78 vertical cylinder,
> so it inherits the angle, mating plane and pegs by construction. No ballast,
> no cavity, no service window. `mat` is retired and its files deleted.
>
> **⚠️ Two constraints collided, and the record matters.** A windowless,
> unballasted pedestal must both clear the BOOT/RESET slots and carry its own
> mass. The largest circle meeting the old blanket "2 mm clear of the slots"
> rule is Ø74.36 — and printed solid it reaches only **SM 1.45 against the 1.50
> design bar**. Ø78 is the only diameter that clears both bars, so it is forced,
> not chosen. The keep-out is re-derived rather than deleted: measured against
> the tray's REAL radiused slot geometry the clearance is **0.518 mm** (not the
> 0.182 mm the bbox corner suggests), and it is now asserted with a 0.40 mm
> print-tolerance floor plus a hard "can never reach a slot" assert. Anyone
> wanting a bigger pedestal must add the symmetric window pair, not shave the
> margin.
>
> **The pedestal must be printed SOLID** — its own mass replaced the ballast, so
> infill is a structural setting here. Solid: 59.1 g, abuse-case SM **1.03**.
> A normal 3-wall/20 % gyroid print: 36.6 g, SM 0.93 — clears the 3 N design
> case but not the 5 N abuse case. The docs say so plainly. `riser` and `wedge`
> span the footprint and cannot tip in any of the 16 modelled cases. Section (a)
> gains row **Q**; band, tray, plate, board and firmware untouched.

> ## ⛔ ORDER HOLD IN FORCE (owner, 2026-07-20)
> **No PCBWay upload, no order, no payment.** `fabpack_out_v5_7/` and the
> `plate_v5` fab set are the **candidate** order set, held pending the owner's
> release sequence (caliper confirmations → owner render sign-off → release).
> The order set and the exact files to upload are listed in section (e) below.

## Version cross-map (one product checkpoint)

| Workstream | Version | Canonical artifact in this bundle | md5 |
|---|---|---|---|
| PCB | **v5_7** (underglow LED20/LED21 rotation; the board shipped in this bundle) | `hardware/pcb/v5_7.kicad_pcb` | `08cf68dae979ab28aadd5e0dda34de01` |
| PCB base | v5_5 (J1-flip) | (lineage; not shipped here) | `27493b30f17de8cd568f9cdcb171f4a9` |
| Case | **v2.17** (v2 topper re-point; E2E fitment + band `WALL` 5.4 default) | `hardware/case/v2/agentpad13_case_v2.py` | see MANIFEST |
| Plate | v5 (YA13 opening) — **unchanged by the band revs** (`INNER_R` frozen) | `hardware/case/v2/fab/agentpad13_v2_plate_v5.kicad_pcb` | see MANIFEST |
| Band | **v2.13 — `WALL = 5.4` DEFAULT, plate pocket 84.6 × 100.2** (1.6 mm seat; PCBWay thin-wall EQ fix + USB port funnel) | `hardware/case/v2/stl/agentpad13_v2_band_1.6mm_w5.4.stl` | `60c74d75bfd024696d6d2e261d4f8083` |
| Band variants | `WALL` 3.0 and 7.4 — gated, shipped alongside | `…_w3.0.stl` / `…_w7.4.stl` | `ed313f69…` / `4f3bf6f2…` |
| Firmware | v4 pin map — **REBUILT + RENAMED 2026-08-15** (protocol v1, on-board SW14 calibration, encoder direction flip; pin map itself unchanged) — **`agentpad13.uf2` is the one to flash** | `firmware/prebuilt/agentpad13.uf2` (vial) | `a7b8da85a7d3f0de96b983be8c782ba2` |
| Firmware — reference build | same sources, `-km default` — kept because it is **byte-for-byte reproducible**; no live remapping | `firmware/prebuilt/agentpad13_reference.uf2` | `4caac0bca0cafb1d3ebf7d46dd9e7adb` |

**Independent verification (this packaging session):** all three release gates
were **re-run on the PACKAGED copies** (not just cited from the ledger) — board
harness `grade_board.py` on `hardware/pcb/v5_7.kicad_pcb`, `verify_fabpack.py`
on `hardware/pcb/fabpack_out_v5_7/`, and `khana build agentpad13_case_v2.py`.
(2026-08-19: the board and fabpack gates were re-run again on the refreshed
`v5_7` copies, plus the new `render_orientation.py` emission gate.)
Verbatim results in section (b).

---

## (a) What changed vs Rev A — A–Q diff

Reconstructed from `hardware/pcb/V5-NOTES.md` + `hardware/case/v2/CASE-V2-NOTES.md`
and **verified against the packaged artifacts** (right column). Rev A = the
`v4-release-compiled/` checkpoint (board v4_r27, case v2.2-era, PSP-slider JS1).

| ID | Change (v5 vs Rev A) | Verified against (packaged) |
|---|---|---|
| **A** | **Encoder RE1 block move** (v4_r27→v5): RE1 footprint relocated so its shaft centers on the plate encoder opening (13.525, 12.5); the SW-adjacent Edge.Cuts chamfer leg shrank 14.6→13.2 mm (asymmetric, owner-approved). Positional diff: only RE1 moved. | `contract_v4.json` status annotation ("RE1+SW-chamfer adjudicated … shaft→plate opening 13.525,12.5 … chamfer leg 14.6→13.2"); `V5-NOTES.md` v5 ledger |
| **B** | **USB-C J1 180° flip** (v5_5): J1 rotated 180° + re-anchored to (42.1, 3.05, rot 0); the receptacle mouth now faces the wall aperture, 0.60 mm proud (v4 had it mounted backwards, mating face into the board). | `contract_v4.json` J1 (42.1,3.05,rot0); CPL J1 row `42.100000,-3.050000,0.000000,bottom`; harness "USB pair clean" |
| **C** | **Joystick JS1 → YA13**: PSP-slider SMD footprint replaced by the YTL YA13-FL7.4 THT tilt gimbal (LCSC C37323742), placed (69.71, 13.37, rot 180) F.Cu, machine-placed THT, 10 pads. 180°-from-datum clocking → see `firmware/POLARITY-NOTE.md`. | `contract_v4.json` JS1; BOM JS1 line C37323742 / YA13 MPN (both SKUs); CPL JS1 row `69.710000,-13.370000,180.000000,top`; JS1 drill census 6×Ø1.0 + 4×Ø1.2 |
| **D** | **Plate opening refab** (v5 plate): the circular Ø16 joystick opening replaced by the YA13 asymmetric rounded-rect (W 58.91 / N 2.57 / E 77.36 / S 21.02, R1.5); 1.6 mm FR4; 3 fab variants (plain / blank / tented-ring). | `fab/agentpad13_v2_plate_v5.kicad_pcb` + `validate_fab_v5.py` frozen expectations (W58.91/N2.57/E77.36/S21.02); CASE-V2-NOTES §14/§15 |
| **E** | **Case v2.2 → v2.7**: board-v5 convergence (tray notch for the 13.2 chamfer → `tray_v5`), perimeter support rail (v2.3), true E2E populated-hardware fitment (v2.4), taper stick-cap default (v2.5), **band sidewall `WALL` 2.4 → 3.0 + parametric USB port funnel (v2.6/v2.6b, PCBWay thin-wall EQ)**, **`WALL` default → 5.4 (v2.7, owner decision)**. Tray gained the notch + JS1 rail-skip; the band grew OUTWARD ONLY — every mating interface is provably unmoved. | `agentpad13_case_v2.py` (v2.7); `outputs/case/mechanism.json` (101/101, status ok); band md5 `34be6bf7…` (w5.4) + tray_v5 md5 `d7d16481…` (UNCHANGED through every band rev) |
| **F** | **House toppers — current release set (2026-08-24)**: the six encoder-knob STLs remain unchanged (three straight Ø17.5 styles × LOW/HIGH D-bores). Joystick outputs are now exactly three `cell2` toppers sharing a **2.00 × 1.25 × 4.00 mm** socket: the **Ø6.189** dot nub, restored **Ø9.412** TPU puck, and conventional **Ø12** restricted topper. The four obsolete nub/puck LOW/HIGH STLs are removed. Nub and puck preserve the full **30°** travel; the Ø12 topper uses the separate continuous-wall TPU restrictor, which limits throw to **15.354–15.487°** so it clears the adjacent 17.5 mm key. | `toppers/stl/` **10 STLs** (6 knob + 3 joystick topper + 1 restrictor). The restrictor and small TPU sockets are printer/material-sensitive; verify seating and throw on the first print. |
| **G** | **Fabpack reclassification**: JS1 reclassified HAND_SOLDER → PLACE (machine-placed THT), both SKUs; retired PSP-slider/Adafruit-3103 BOM + afterlist line removed; verify harness grew 17 → 26 checks. | `fabpack_out_v5_7/assembly/` BOM (JS1 Place / PCBWay-THT; no 3103/6193574/live-slider) + `hand_solder_afterlist.csv` (RE1 only); `verify_fabpack` 31/31 |
| **H** | **SW14/SW15 tact MPN correction (2026-08-05, PCBWay component-verification catch)**: XKB **TS-1187A / C318884** (5.1 × 5.1 mm, 6.5 mm lead span) was specified against the C&K PTS645 6.0 × 6.0 / H4.3 gull-wing land pattern `SW_SPST_PTS645Sx43SMTR92` (7.96 mm pad span) — not solderable. Now C&K **PTS645SM43SMTR92 LFS / C221880** (DigiKey CKN9112CT-ND, 160 gf); alternates B3S-1000P (C180420) / ZX-QC66-4.3TP (C7470150) / PTS645SK43SMTR92 LFS; **forbidden:** PTS645SM43JSMTR92 LFS (C2801847, J-lead). +$0.59/board. Metadata-only: Gerbers/drills/CPL unchanged. Verify harness grew 26 → **31** checks (new BOM-MPN-vs-footprint gate). | `fabpack_out_v5_7/assembly/bom_{opaque,translucent}.csv` + `hand_solder_afterlist.csv` (MPN `PTS645SM43SMTR92 LFS`, LCSC `C221880`, FP `SW_SPST_PTS645Sx43SMTR92`); `verify_fabpack` 31/31 incl. the 5 new MPN↔footprint checks; MANIFEST rows for the 3 CSVs + 2 zips |
| **I** | **Plate fab set re-synced to the 2026-07-21 long-axis trim (2026-08-05)**: this bundle's nine plate artifacts were PRE-TRIM at **84.400 × 100.200 mm**, 0.2 mm outside the fab's **≤100 mm promo tier** (owner: *"Resize the top plates to 100mm. That 0.2 is gonna cost us 25%. Not worth it."*). Now **84.400 × 100.000**. Outline-only: 8 of 93 primitives (4 long edges + 4 corner arcs, 0.1 mm/edge, outline stays centred on y = 50.0); every cutout, opening and screw hole holds its exact position. The case model keeps `C.PLATE_H = 100.2` on purpose (it drives the band pocket, which must not move — the plate-to-lip gap merely relaxes 0.30 → 0.40 mm/end). Board, fabpack and firmware **untouched**. | `fab/agentpad13_v2_plate_{v5,tented_ring_v5,blank_v5}.kicad_pcb` + the 3 gerber zips + DXF + top PNG/SVG (new md5s in MANIFEST); `validate_fab_v5.py` **ALL GATES PASS 3/3** (`bbox 84.400 x 100.000`, shapes 89, `N->plate-top` 2.570, `NE->screw` 1.555 ≥ 1.5); CASE-V2-NOTES **§19** + annotated §14/§1/§6 |
| **J** | **TTP223 touch polarity — ships-broken firmware defect, FIXED firmware-only (2026-08-13)**: `R10` (0 Ω) straps `TOUCH_AHLB → GND` on `v5_7.kicad_pcb`, which on a TTP223 selects **active-HIGH** output (`GP16` idles LOW, HIGH while touched). The shipped firmware documented **active-low** and defined no `MATRIX_INPUT_PRESSED_STATE`, so QMK's default (LOW = pressed) made matrix `[3,2]` read **held from power-on** — the pad booted into layer 1, layer 0 (`F13`–`F24`) was unreachable, `SW1` emitted nothing, the encoder was `RGB_MOD` not volume, and touch fired on finger **lift**. Boards are fabricated **and populated**, so the `R10`→`+3V3` rework was unavailable. Fix: `GP16` dropped from `matrix_pins.direct` (`[3][2] = null`) and polled in `loudest_micro.c` `matrix_scan_kb()` with its own active-high sense + 5 ms debounce, injecting the event at the **same** logical `[3,2]`; `keyboard_pre_init_kb()` configures the pin with a pull-DOWN. `MATRIX_INPUT_PRESSED_STATE 1` rejected — `quantum/matrix.c` applies it to every direct pin and would invert the 13 active-low switches. Keymaps, `LAYOUT`, matrix size, keycodes, `TP_TOG` and the RGB layout unchanged; only cost is that Vial's matrix tester cannot show `[3,2]`. **Board/fabpack/plate/case untouched.** | `firmware/prebuilt/loudest_micro_default.uf2` `cf5bd628…` (88576 B) + `loudest_micro_vial.uf2` `b31673a7…` (104448 B); `firmware/sim/behavior.cjs --touch=board` **33/33, 0 failures** on BOTH builds (was 4 failures) — all 13 switches, 24 LEDs, encoder and joystick still pass; `firmware/tests/emulator` smoke **PASS** both builds; `check_pins_v4.py` **56/56**; conformance **80/80**; `qmk lint --strict` pass |
| **K** | **Bring-up calibration facility + isotropic RGB layout + the double `housekeeping_task_user()` call removed (2026-08-13 / 2026-08-15, firmware-only)**: three changes and one decision, none of which touch copper. **(1)** A third prebuilt, `firmware/prebuilt/loudest_micro_calibrate.uf2`, is a **BRING-UP TOOL, not daily firmware** — a `calibrate` keymap in which every key is `KC_NO` and dispatch happens on `row`/`col`, so it can never emit a stray character; four guided `SW1` presses make the board **type its own calibration report** (measured `low`/`rest`/`high`, per-axis `inverted=YES/NO`, re-derived `JS_CENTER`/`JS_THRESHOLD`, a per-direction `fires`/`NEVER FIRES` verdict against the SHIPPED `512`/`300`, and finished config lines with the `POLARITY-NOTE.md` `low`/`high` swap already applied). This closes the standing gap in which every document said *"do the bring-up ADC sweep"* and none said how — protocol v0 is LOCKED and carries no ADC readout, and Vial exposes no raw analog. The owner-facing procedure ships as **`firmware/BRING-UP.md`** (new in this bundle; moved out of `firmware/BUILD.md` §4a so it travels with the payload). **(2)** `rgb_matrix.layout` is regenerated **isotropically** — one scale on both axes (`64 / bbox_height = 0.64`) centred on QMK's own `k_rgb_matrix_center {112, 32}` — closing the 4.157 : 1 anisotropy under which `cycle_pinwheel`, `cycle_spiral`, `dual_beacon` and `rainbow_moving_chevron` rendered skewed; all 24 `y` unchanged, `flags` and `matrix` untouched. **(3)** `housekeeping_task_kb()` no longer re-calls `housekeeping_task_user()`, which `quantum/keyboard.c:436` already calls — it had been running twice per loop. **(4)** `CAPS.led_count` **stays 24 on both SKUs, closed by decision** (redefined as addressable chain length; LOCKED protocol v0, zero wire change). **Board, fabpack, plate and case untouched.** | `firmware/prebuilt/loudest_micro_default.uf2` `1c0ff911…` (88576 B) + `loudest_micro_vial.uf2` `286fb09d…` (104448 B) + `loudest_micro_calibrate.uf2` `aabf7954…` (96768 B); `firmware/sim/behavior.cjs --touch=board` **33/33, 0 failures** on BOTH shipped builds with the `--touch=firmware` counterfactual still **4 failures** (the A/B still discriminates on the new binaries); `firmware/sim/calibrate.cjs` **37/37 PASS**, `--no-adc-fix` arm **15 failures** as required; `check_pins_v4.py` **30/30** and **56/56**; conformance **80/80**; emulator smoke **PASS** both builds; isotropy proven from the SHIPPED binary — `g_led_config`'s 88-byte initialiser read out of the `default` ELF `.data` and found in the UF2 payload at offset 42676, LED cloud x 88..136 symmetric about 112 |
| **L** | **On-board joystick calibration (SW14) + protocol v1 + encoder direction, and BOTH prebuilts RENAMED (2026-08-15, firmware-only)**: the joystick shipped on placeholder calibration with no mechanism to replace it, and row K's answer — a separate `calibrate` firmware that TYPED its numbers for a human to paste into source and rebuild — is **retired here along with the host-only variant that followed it**, on the owner's ruling that *"calibrated usage does not depend on a daemon."* **(1)** Holding **SW14** (the BOOTSEL button, inert while firmware runs) for ~1 s starts a bounded ~15 s routine in which the 13 key LEDs are the entire UI — white armed, blue bar for centre, amber→green bar for the swing, green flash stored, red flash rejected — writing a 14-byte EEPROM datablock that survives unplug and reflash. Keys keep working throughout; no mode, no layer change, nothing inert. Reading SW14 at runtime means briefly overriding `QSPI_CS`, during which flash is unreadable, so `sw14_pressed()` is **RAM-resident** (`.time_critical` → `.data`, proven by `nm`) with interrupts masked for a measured **14016 cycles / 112.1 µs at 0.112 % duty** — 450–3500× shorter than the flash erase this firmware already masks for on every Vial keymap save. **(2)** Protocol v1 (`0x50`/`0x51`/`0x52`, IDs outside VIA's 0x01–0x13 so `via_command_kb()` claims them without heuristics) is the host path; it and SW14 share **one `js_cal_store()`**, so both write byte-identical EEPROM by construction. Per-axis centre/threshold replace `JS_CENTER 512`/`JS_THRESHOLD 300`, which remain the uncalibrated fallback. **(3)** Encoder direction flipped to the as-built A/B landing (clockwise was volume-down) and `vial.json` now declares the encoder. **(4)** `loudest_micro_vial.uf2` → **`agentpad13.uf2`**, `loudest_micro_default.uf2` → **`agentpad13_reference.uf2`**; `loudest_micro_calibrate.uf2`, `keymaps/calibrate/` and `sim/calibrate.cjs` **deleted**. `firmware/BRING-UP.md` rewritten — the copy in this bundle had been instructing a flash of the now-nonexistent calibrate UF2. **Board, fabpack, plate and case untouched.** | `firmware/prebuilt/agentpad13.uf2` `a7b8da85…` (109568 B) + `agentpad13_reference.uf2` `4caac0bc…` (93696 B); `firmware/sim/behavior.cjs` **33/33** on both builds with the encoder A/B failing **0/2/4/6** across the four arms; `firmware/sim/joystick.cjs` **62/62** with **both** counterfactuals failing **6**, incl. §10b asserting the SW14 and 0x51 EEPROM images are byte-identical (**8-byte** divergence when forced to disagree); protocol conformance **410/410** against `daemon/loudestd/protocol.py`; `check_pins_v4.py` **30/30** and **56/56**; daemon suite **219**; emulator smokes PASS; `qmk lint --strict` pass; EEPROM persistence proven by emulated power-cycle (required teaching rp2040js to write flash at all) |
| **M** | **Underglow bottom pair rotated 180° — 4 of 10 underglow LEDs were firing OUT of the case (v5_7, 2026-08-19, board-only)**: this bundle previously shipped `v5_6`, in which `LED20` and `LED21` emitted away from the diffuser instead of into it. **Root cause, re-derived from the board rather than inherited:** `gen/build_pcb.py:82` declares `UGLOW_ROT = [180,180,90,90,90,0,0,270,270,270]` — a coherent all-inward set **in the un-flipped frame** — and `:252-254` applies the rotation and *only then* flips the part to B.Cu. `FOOTPRINT::Flip()` mirrors local geometry in Y **and negates the orientation**, so emission goes `(−sinθ,−cosθ) → (−sinθ,+cosθ)`: the parts aimed along **±Y reverse** while the parts aimed along **±X survive**. That is why exactly the top and bottom pairs were wrong and the left/right rails were right — 6 inward / 4 outward. **Fix:** `LED20` and `LED21` `rot 0 → 180`, x/y/side unchanged; 126/126 footprints compared against v5_6 show **only those two differing and only in `rot`**, and 414/414 pads carry **0 net changes**. **`LED15`/`LED16` are deliberately left outward** on the owner's pre-authorised reduced scope (*"that side looks kinda cool with the hotspot near the USB, just rotate the bottom ones"*) — the emission gate's target is therefore **8 inward, not 10**. **4 signal vias were added, declared BEFORE any copper moved and coordinator-approved as a registered prediction violation:** a between-pad escape is topologically impossible (pitch 0.85 − pad 0.42 = **0.430 mm** available against **0.456 mm** needed for a 0.152 trace with 0.152 clearance both sides — a **0.026 mm** deficit), and with +5V now landing on the middle pad both data nets must detour south where their spans strictly interleave, forcing a crossing in either lane order ⇒ one layer hop per LED. The via-free alternative was **measured and rejected**: it stretches `C45→LED20.2` from **1.16 mm to ≈8 mm**, trading a data-line via against a decoupling path. `v5_7` supersedes `v5_6` and is the sole current public board and order set. **Firmware, plate and case untouched.** | `hardware/pcb/v5_7.kicad_pcb` `08cf68da…`; `grade_board.py --no-ring` **PASS all gates** (DRC 0, unconnected 0, contract **45/45 refs ok**, bbox 84.200 × 100.000, +5V spine 183 segs min 0.5000, USB pair clean, TP5 pour 177.0 mm²) re-run on the packaged copy; **new** `render_orientation.py` emission gate **INWARD 8 / OUTWARD 2, GATE PASS** (v5_6 scores 6/4) — the standard pad/copper plot is *structurally incapable* of catching this class, since a 180° rotation of this part moves the four pad x-positions by **0.004952 mm**; `verify_fabpack.py fabpack_out_v5_7` **31/31 PASS**, ratsnest 0, drill census 285 → **289** (vias 182 → **186** = exactly the 4 authorized vias, NPTH unchanged at 48); translucent CPL differs in **exactly 2 of 110 rows** (`LED20`/`LED21` `Rot 0.000000 → 180.000000`), opaque CPL and both BOMs and the afterlist **byte-identical**; `contract_v4.json` LED20/LED21 adjudicated with the owner's directive quoted verbatim |
| **N** | **Plate encoder opening widened +1.000 mm, ALL of it to the right (v2.12, 2026-08-19, plate-only)**: the assembled plate's encoder aperture was **13.000 × 13.000 R1.5** centred on the shaft (13.525, 12.5); the owner's encoders measure **~13.7 mm** across the pin axis and the part fouled the aperture's right-hand wall (*"left side of hole is perfect, right side needs more space"*). Now **14.000 × 13.000 R1.5 @ (14.025, 12.500)** — LEFT edge FROZEN at x 7.025, right edge to x 21.025, y 6.000..19.000 unmoved (*"don't widen the hole symmetrically, widen to fit the parts"* / *"just expand the width to the right by 1mm"*). R stays 1.5 deliberately: a larger corner radius eats the very body-corner clearance the measured part needs. The corrected topper is independently a straight **Ø17.5** body with no skirt or flange, chosen to preserve a gap beside the adjacent key rather than cover this opening. `ENC_BODY_SQ` stays **11.7** — the ~13.7 measurement has no resolved datum (a shaft-centred 13.7 contradicts the owner's own left-perfect/right-binding fit), so the OPENING was sized from the measured fit, not from a guessed body. This regeneration also ships the §20 **`WayWayWay` B.SilkS token for the first time**, discharging §20.4. Shipped alongside: the bundle's `validate_fab_v5.py` (which still asserted the **pre-trim 84.40 × 100.20** outline and would have rejected the bundle's own gerbers) and its **pre-v2.8 tray**, both now current. **Board, fabpack, firmware and band untouched.** | `fab/agentpad13_v2_plate_{v5,tented_ring_v5,blank_v5}.kicad_pcb` + the 3 gerber zips + DXF + top PNG/SVG (new md5s in MANIFEST); `validate_fab_v5.py` **ALL GATES PASS (57 PASS / 0 FAIL)** incl. a new assert pinning the frozen left edge; **independent Edge_Cuts gerber parse** of all three variants (14.0000 × 13.0000 @ x 7.0250..21.0250, y 6.0000..19.0000, R1.5; outline 84.400 × 100.000; `WayWayWay` present on B_Silkscreen, mirrored); case mechanism gate current; band and tray geometry unchanged |
| **O** | **Band plate-pocket fit corrected — the deck floated 0.8 mm (v2.13, 2026-08-19, band-only)**: the pocket was `PLATE_H + 2x0.3` with `PLATE_H` = the **pre-trim 100.2**, so a **85.0 x 100.8** pocket held an **84.4 x 100.0** plate — 0.8 mm of end-float, visible as a ~1 mm gap at one end. The 2026-07-21 trim (row I) had been applied only inside the plate generator because the band was frozen then, leaving the model plate and the shipped plate permanently disagreed. `PLATE_LONG_TRIM` moved into the case model, `PLATE_H` is now the shipped **100.0**, and the generator consumes it. Pocket -> **84.6 x 100.2 R5.5**, a uniform **0.1 mm/side** on both axes and the corner R (arcs exactly concentric, so 0.1 on flats AND corners); float **0.2/0.2**. A second "loose" variant was planned and then dropped — owner: *"I'm kind of inclined to make this the only version actually. Since even on crappy printers, someone can sand."* One band ships. 0.1/side is genuinely tight and may need a light sand at worst-case fab+print stack; that is the deliberate, correctable direction. All three wall variants re-cut in place. **The 2026-07 ordered band is the old loose pocket, usable, not recalled. Plate fab set, board, fabpack, firmware and tray untouched.** | band md5s `60c74d75…` (w5.4) / `ed313f69…` (w3.0) / `4f3bf6f2…` (w7.4); **plate fab UUID-blind dry render = ZERO geometric delta** on all three variants (nothing overwritten); **scratch-only byte-identity proof**: the band rebuilt with the pocket forced to the legacy geometry hashes `34be6bf79a6bb81995807448639f4822`, byte-identical to the ordered band, proving the refactor is geometry-neutral; khana **101/101 status ok**, same 8 interference pairs at identical volumes; band printability advisory **unchanged** (min_wall 0.7333333333333292, overhang 896.53 mm^2); band volume +142.65 mm^3, matching the closed-form pocket-shrink prediction exactly; tray `8bfd7eaf…` byte-identical |
| **P** | **Tray bases published + every foot recess deleted (v2.15, 2026-08-20, bases only)**: the insertable-base family ships for the FIRST time — `pedestal` (Ø70 x 20 circular, ballast required), `mat` (91.6 x 107.4 TPU sheet) and `wedge` (same outline, 6.5 deg back-raised), each on a 4-rung peg fit ladder, plus a fit gauge and the `INTERFACE.md` spec. Owner scope: *"I see the official offering as tray only or tray + insertable bases."* **Feet deleted** (*"NO, there are no more recesses!"*): all Ø8.3 bumpon pockets gone, undersides FLAT, no part number prescribed, every stance figure EXCLUDES feet — mat overhang -> ZERO, wedge 245.87 -> 30.25 mm² (its arrow deboss alone), and the larger support polygons take the wedge to 16/16 non-tipping load cases. **x-symmetry is now a DESIGN LAW** asserted exactly per variant per build (*"if they're not, they're designed wrong"*); it immediately caught the off-centre BOOT/RESET service window, now cut as a symmetric PAIR. **Bases mirrored at export** like the tray (free: this pass rebuilt them all). Rebuilt against the v2.11 tray, which exposed `BASE_T = C.TRAY_T` — the plinth had silently made the mat 4.4 mm / +83 % mass; decoupled to a literal 2.4. **Band, tray, plate, board and firmware untouched.** | 24 new MANIFEST rows (13 STL + INTERFACE.md + params + render + 3 printability + 3 mechanism + 2 sources); per-variant khana **ok, 3/3 assertions**, pegs asserted INTO the pocket witness against the CURRENT tray; peg-in-pocket proven at coordinate level in the EXPORTED frame (all four pegs CONTAINED, 0.000000 mm³ outside); wedge tilt verified thin 2.80 mm at the exported user edge / thick 14.35 mm at the USB edge; x-symmetry exact (0.000000 mm³) on all three variants with a negative control proving the assert fires; pedestal ballast floor 85 -> **69 g** and worst margin 1.161 -> **1.217** (the heavier plinthed tray helps); frozen hashes re-verified — tray `8bfd7eaf…`, bands `ed313f69…`/`60c74d75…`/`4f3bf6f2…` |
| **Q** | **Base catalog finalised: riser / wedge / pedestal (v2.16, 2026-08-20, bases only)**: the v2.15 demonstration family becomes a product line. **`riser`** (NEW, replaces the retired `mat`) is the 91.6 x 107.4 plan at a **3.0 mm** body, printed in TPU for grip or PETG for a rigid stand. **`wedge`** goes **6.5 deg -> 8.0 deg** — the owner asked what a real keyboard pitch is rather than accepting a guess; mainstream standard 7 deg, comfort band 4-8, high-profile customs 6-8, so 8.0 (top of band, because this deck is a 13-key pad not a full board); far edge derives to 17.49 mm. **`pedestal`** is rebuilt exactly as the owner described it — the wedge INTERSECT a O78 vertical cylinder — inheriting angle, mating plane and pegs by construction, with **no ballast, no cavity and no service window**. **O78 is forced, not styled:** the largest circle meeting the old 2 mm slot-margin rule is O74.36 and reaches only SM 1.45 against the 1.50 design bar, so keep-out and stability were mutually exclusive; the keep-out is re-derived against the tray's REAL radiused slot geometry (0.518 mm clear, not the 0.182 mm the bbox corner implies) with a 0.40 mm print-tolerance floor and a hard never-reach-a-slot assert. **The pedestal must be printed SOLID** — solid 59.1 g gives abuse SM 1.03; a 3-wall/20% gyroid print is 36.6 g and SM 0.93, clearing the 3 N design case but not 5 N abuse. **Band, tray, plate, board and firmware untouched.** | MANIFEST: 6 mat rows REMOVED, 6 riser rows ADDED, 18 rehashed (net 154 rows, -375017 bytes); per-variant khana **ok 3/3** each with pegs asserted INTO the pocket witness against the current tray; x-symmetry design law **exact (0.000000 mm^3)** on all three, the pedestal symmetric by construction; mirror-at-export retained with all four pegs of all three variants proven CONTAINED in the mirrored tray's pockets (0.000000 mm^3 outside) and both tilted variants verified thick at the exported USB edge (wedge 3.03 -> 17.00 mm, pedestal 5.10 -> 14.94 mm); riser/wedge cannot tip in 16/16 load cases; main khana untouched 101/101/8; tray `8bfd7eaf...` and all three band STLs byte-identical |

---

## (b) Verbatim gate records

**1. Board harness — `grade_board.py hardware/pcb/v5_7.kicad_pcb` (no-ring; RE-RUN 2026-08-19 on the packaged v5_7 board):**

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
`+5V spine 184 → 183 segs` (3 segments ripped, 2 added at the rotated LEDs) — the
gate is min-width, not segment count.

**1b. Emission orientation — `render_orientation.py hardware/pcb/v5_7.kicad_pcb --expect-inward 8` (NEW gate, 2026-08-19, run on the packaged board):**

```
  centre (42.100, 50.000)  ->  INWARD 8 / OUTWARD 2
  GATE PASS: INWARD == 8
```
The same tool scores the fabricated `v5_6` at **INWARD 6 / OUTWARD 4** — that is
the defect this revision closes. `LED15`/`LED16` are the two
remaining OUTWARD parts and are outward **by owner choice**; do not "fix" them to 8/0.
Note: the contract line prints `WARN OK … contract is provisional; see
cross_check (coordinator adjudicates)` — the adjudicated JS1/J1/RE1 refs pass
**45/45**; the WARN only flags that the geometry adjudication is provisional
pending the coordinator's cross_check (owner-directed changes, per protocol).

**2. Case khana — `khana build agentpad13_case_v2.py` (v2.7, `WALL = 5.4` DEFAULT; RE-RUN this session):**

```
mechanism.json: status=ok, 101 assertions, 101 passed, 0 failed
interferences : 8 (the documented set, unchanged)
[corner] band_crescent_wall = 4.400   (class = flat)
[corner] head_to_plate_edge = 0.287 ; plate_hole_edge_web = 1.537  (PLATE
         measures — WALL-INVARIANT; see the CASE-V2-NOTES §18.4 erratum)
[v2.7-WALL] WALL = 5.4 -> OUTER 95.6 x 111.4 (R8.0); INNER 84.8 x 100.6
            (R5.6 FROZEN -> PLATE_R 5.4, TRAY_R 5.35 unmoved)
[v2.6-WALL] visible rim ring = 5.30 mm + the 0.3 nominal reveal per side
[v2.6-FUNNEL] USB port funnel depth = 3.00; pocket 13.0 x 7.0 @ y -5.70..-2.70
[v2.6-FUNNEL] shell bridge = 2.10 mm — WALL-INVARIANT
[v2.5-SWEEP]     cap sweep south reach from stick = 9.037 ; lowest z = 10.467
[v2.5-JS-KEYCAP] js_sweep x keycaps overlap = 0.00 mm^3 ;
                 taper wall -> SW4 keycap edge (22.7) clearance = +0.293 mm
```
Interferences dropped 9 → 8 at v2.5 (the v2.4 dome `js_sweep×keycaps` 40.78 mm³
SW4 graze is **GONE** with the taper default) and have stayed at 8 through every
band rev. **All three walls {3.0, 5.4, 7.4} are gated at 101/101 with the same 8
interferences** (variants build via `AGENTPAD13_WALL=… khana build`). Frozen
artifacts held: tray_v5 STL md5 `d7d16481df24bae4c7769d7624dfc620` **UNCHANGED**,
and the plate + tray solids are md5-identical at every wall. The band's own
md5-invariance gate (`36980cc2…`) was **RETIRED by owner order** at v2.6 — that
hash is now the identity of the **superseded 2.4-wall band, which must not be
printed** and is no longer carried in this bundle.

**Band wall = a documented parameter.** `WALL` is the one owner-tunable sidewall
number; `INNER_R` is FROZEN at 5.6 so it cannot move any mating interface.
**3.0 / 5.4 / 7.4 are all gated and all shipped here; the default is 5.4**
(owner, 2026-07-24: *"1.6 mm doesn't seem like an especially strong corner to
me"*). Proven, not asserted: the v2.7 source re-exports the 2.4 and 3.0 bands
byte-for-byte, `vol(band_2.4 − band_5.4) = 0`, and
`vol((band_5.4 − band_2.4) ∩ mating envelope) = 0`. See CASE-V2-NOTES §18.

**3. Fabpack — `verify_fabpack.py fabpack_out_v5_7` (RE-RUN 2026-08-19 on the packaged v5_7 fabpack):**

```
RESULT: 31/31 checks PASS
```
Includes (all PASS): CPL opaque/translucent row counts 90/110; CPL J1 ==
`42.100000,-3.050000,0.000000,bottom` both SKUs; CPL JS1 ==
`69.710000,-13.370000,180.000000,top` both SKUs; BOM DNP 23/3; BOM JS1 line
LCSC C37323742 / YA13 MPN both SKUs; no Adafruit-3103 / 6193574 / live PSP-slider;
JS1 drill census 6×Ø1.0 + 4×Ø1.2; both fabpack zips present; ratsnest 0 — **plus the
five new MPN-vs-footprint checks (2026-08-05):** SW14/15 MPN is an approved
PTS645-land tact with no TS-1187A / J-lead part in any non-Notes cell (both SKUs);
every footprint-embedded part family corroborated by MPN/LCSC/Manufacturer (both
SKUs, 29 rows each, 0 violations); afterlist SW14/15 opt-out row matches the
approved part. The previous 26/26 result stands for the identical bare-board and
CPL artifacts, which did not change.

---

## (c) Watch-items (carry into first-article / owner sequence)

| Item | State | Action before it bites |
|---|---|---|
| **JS_POT_HALF = 4.5** | PROVISIONAL — a conservative pot-box/edge-tab half-width envelope, not a metered dimension (CASE-V2-NOTES §15). Does not gate the build. | Refine from the YA13 mechanical drawing **before the resin band order**. |
| **Cap socket depth 4.0** | DESIGN CHOICE — the blade-engagement depth is assumed 4.0 mm (drawing gives the tip + cross-section, not the run length). | The current three joystick toppers use one `cell2` socket, 2.00 × 1.25 × 4.00 mm. Fit remains printer/material-sensitive, especially in TPU; verify the first print rather than selecting from the retired LOW/HIGH ladder. |
| **EC11 shaft grip window** | The knob prints in two bounded D-bore sizes: nominal `clearance_low` Ø6.0 / 4.5 across-flat and FDM-compensation `clearance_high` Ø6.3 / 4.8 (0.15 mm maximum clearance). Top **+27.0** is sized to the published Alps EC11E-Switch-Vertical **H20** drawing (tip +24.5 + 1.0 headroom + 1.5 roof), so the board's own shaft seats **UNCUT**. | Start with `clearance_low`; use `clearance_high` if the printed bore closes. A Bourns **PEC11R-40/42-20F (L20)** shaft is longer and **rides proud** — cut it or use the L15. |
| **Insert-wall 1.65 mm** | `notch_insert_wall[3.7,3.7] = 1.651` at the notched corner boss (printed this build). | First-article print check of the M3 heat-set insert wall. |
| **Touch-foam (TP5) coupon** | Pre-existing open item (CASE-V2-NOTES §5/§8): conductive-foam pad + electrode construction pending the touch coupon. | Owner decision on the touch coupon (carried from Rev A). |
| **Joystick-topper clearance** | The nub and restored puck preserve the joystick's full **30°** travel. The Ø12 topper is paired with a separate restrictor cap and was verified at **15.354–15.487°** contact, with 0.431 mm minimum adjacent-key clearance. | Confirm seating and throw on the first print. The restrictor is digitally verified but TPU/printer retention remains process-sensitive. |

---

## (d) SKU / band pairing

Two board SKUs (the LED/cap populate-per-variant rows differ): **translucent**
and **opaque**. Band default look = **frosted/clear resin** (SLA), per
CASE-V2-NOTES §6.

- **Translucent PCB ↔ frosted resin band** — the intended light-through pairing.
- **Opaque PCB ↔ either band finish** (frosted or opaque) — no light-through
  constraint.

---

## (e) PCBWay order set — upload list for when the hold lifts

> ⛔ **ORDER HOLD STANDS.** Do not upload/order/pay. The list below is the
> *staged* set for when the owner lifts the hold; it is not authorization.

**Board (PCBWay, both SKUs):**
- `hardware/pcb/fabpack_out_v5_7/gerbers_v5_7.zip`
- `hardware/pcb/fabpack_out_v5_7/assembly/cpl_opaque.csv` **and** `cpl_translucent.csv`
- `hardware/pcb/fabpack_out_v5_7/assembly/bom_opaque.csv` **and** `bom_translucent.csv`
  (the v5_7 BOM carries the JS1 `C37323742` line — unlike the v5_5 set, both
  CPL **and** both BOM must go up.)
- Hand-solder afterlist: RE1 only (`hand_solder_afterlist.csv`).

**Plate (FR4 fab):**
- `hardware/case/v2/fab/plate_v5_gerbers.zip` (choose the variant: plain /
  `plate_v5_blank_gerbers.zip` / `plate_v5_ring_gerbers.zip`).
- **Size `84.4 × 100.0 mm`, 2 layers, 1.6 mm.** The long axis is deliberately
  **exactly 100.000** so the plate lands inside the **≤100 mm promo tier** — if
  the fab's form quotes a larger board, the upload is a stale pre-trim file, so
  stop and re-check. Post-trim md5s (re-synced 2026-08-05, see the revision block
  above): `plate_v5_gerbers.zip` `ddd03d3d5be406b977e754c31bbf3552` ·
  `plate_v5_ring_gerbers.zip` `acc4e503e79884924e7193550b5e8b52` ·
  `plate_v5_blank_gerbers.zip` `9dd48c8ed65bddec7aa0fbd31ff83226` (re-hashed 2026-08-19 for the v2.12 encoder opening — anything older is a stale pre-widening file).
  **Only ONE variant is ordered** — they are the same plate with different touch
  markers, and only `plate_v5_gerbers.zip` needs the ENIG upcharge.
- ⚠️ **Product-number placement — set it on the form, or it lands on the deck.**
  On the v5 order PCBWay printed their product number on the plate's **top
  (+Z / F.Silkscreen) face — the visible deck.** Their placement rule is
  component-driven (*"we will try to put it under the IC so that the number
  will be hidden when soldering"*) and this is a bare panel with no components,
  so the rule had nothing to aim at. On the order form set **`Remove product
  No.` = `Specify a location`** (the **free** option) and state in **"Other
  special request"** that the number goes on the **bottom face — the
  B.Silkscreen side, tray-facing and hidden once assembled** — not on the
  top/F.Silkscreen face. The paid `Yes (+$1.50)` removal was considered and
  **rejected** (owner: put it on the hidden face rather than pay to delete it).
  The uploaded gerbers now **do carry** a `WayWayWay` token on B.SilkS (new 2026-08-19) as belt-and-braces, but PCBWay's
  wording says *"the silkscreen layer"* — singular, no top/bottom language — so
  **that token yielding bottom placement is a reasonable inference, not a
  documented guarantee**; the written remark is the load-bearing part. Full
  record: `hardware/case/v2/CASE-V2-NOTES.md` §20.

**Band (resin SLA print/order):**
- **`hardware/case/v2/stl/agentpad13_v2_band_1.6mm_w5.4.stl`**
  (md5 `60c74d75bfd024696d6d2e261d4f8083`, re-cut 2026-08-19 — see the plate-fit
  note below; anything hashing `34be6bf7…` is the older loose-pocket band)
  — **THE band file to upload.** It
  replaces the earlier `agentpad13_v2_band_1.6mm.stl` (`36980cc2…`, the 2.4 mm
  sidewall) that PCBWay's 3D-print review flagged for thin corners; that file is
  **RETIRED — do not print or upload it**, and it is no longer in this bundle.
  Sidewall 2.4 → 5.4 mm; the flagged corner minimum goes `0.737` (free-standing
  arc) → **`4.400` mm, flat-backed**; overall `89.6 × 105.4` → `95.6 × 111.4` mm.
  All mating and internal geometry is unchanged.
- Variants shipped for completeness (both gated, same 101/101 build): `…_w3.0.stl`
  (`ed313f69…`, the thinner look) and `…_w7.4.stl` (`4f3bf6f2…`, the thickest).
  Upload exactly ONE.
- ⚠️ **Plate fit — the pocket is now 0.1 mm/side (v2.13).** All three bands were
  re-cut on 2026-08-19: the plate pocket was sized around a 100.2 mm plate that
  never shipped (the fab trim to 100.0 lived only in the plate generator), so the
  plate floated **0.8 mm** along its long axis and showed the gap at one end. The
  pocket is now **84.6 × 100.2 R5.5** around the 84.4 × 100.0 plate — a uniform
  **0.1 mm** reveal on the flats and at the corners, float 0.2 both axes. There is
  ONE band; there is no "loose" file. 0.1/side is genuinely tight: at a worst-case
  stack (fab routing up to +0.15 on the plate, plus resin/print shrink) **the plate
  may need a light sand to drop in.** That is the deliberate trade — too tight
  sands loose in a minute, too loose cannot be fixed at all. If a printed pocket
  binds: sand the pocket walls, or raise `PLATE_FIT` in `agentpad13_case_v2.py`
  (one line) and re-export — the generator is the loose variant. **The band already
  ordered from PCBWay in 2026-07 is dimensionally the OLD loose pocket; it is
  usable and is not recalled** (owner: *"In our case, we won't reorder it, it's
  usable."*).

**Tray:** self-print (`agentpad13_v2_tray_v5.stl`, PETG) — no external order.

---

## (f) The topper family (v2)

**If you printed the v1 toppers, reprint them — all of them.** Every v1 part is
retired to `archive/toppers-v1/` and none of it ships here any more. Two of the
changes are fit corrections, not taste:

- **The knob is a straight Ø17.5 body.** It has no skirt or flange and does not
  attempt to cover the encoder opening. At the 19.2 mm center pitch beside a
  17.5 mm keycap, it leaves a **1.7 mm horizontal gap**.
- **The v1 knob was too short for the shaft on your board.** v2 tops out at
  **+27.0**, derived from the published Alps **EC11E-Switch-Vertical H20**
  drawing: shaft tip **+24.5**, plus 1.0 mm headroom, plus a 1.5 mm roof. The
  board's own encoder shaft therefore seats **UNCUT**, with **10.00 mm** of
  D-bore gripping the flat (house floor is 6.0). The knob stays **plain below
  keycap height** so it reads as part of the deck, not a tower.

**Three knobs, one envelope.** All use the same straight Ø17.5 body,
+8.0..+27.0 height and D-bore; they differ only in surface:

| Knob | Surface | Print orientation |
|---|---|---|
| **A** `A_helical_knurl` | 34 grooves/family at 30° from vertical, 0.85 × 0.4 — a grip that winds as it rises | **top-face-down** |
| **B2** `B2_scoop` | Smooth barrel with a deep dished top: rim down at **+18.2** (level with the knurl line), 1.447 mm of concavity | **bottom-down** |
| **C** `C_cross_hatch` | 17 grooves/family at 45°, crossed — ~71 diamonds of 2.66 × 2.66 | **top-face-down** |

**Clearance pair (knobs):** `clearance_low` is the conventional nominal push-on
D-shaft size, **Ø6.0 / 4.5 mm across-flat**; `clearance_high` is **Ø6.3 / 4.8 mm**
(0.15 mm radial and flat clearance, the owner-set maximum). The rejected Ø6.6 / 5.1 mm high fit was
physically far too loose. Start with low and move to high only if the internal
D-bore prints closed. 6 STLs = 3 knobs × 2
clearances.

**A Bourns caveat:** a **PEC11R-42xxF (L15)** shaft seats with room to spare; a
**PEC11R-40/42-20F (L20)** is longer than the Alps and **rides proud** — shorten
it or use the L15.

**Three current stick toppers, one socket.** The four old nub/puck LOW/HIGH
files are gone. These three parts all use the same 2.00 × 1.25 × 4.00 mm
`cell2` rectangular socket:

- **The Ø6.189 dot nub** (`stick_nub_v2_C2`) — a low seven-dot button. It needs
  **no restrictor** and is clear of the SW4 keycap at the **full 30° throw**
  (+0.2508 mm at the governing point, which is the chamfered rim, not the top).
  It is solid except for its rectangular shaft socket and prints
  **bottom-down**.
- **The restored one-piece TPU puck** (`stick_puck_v2_TPU`) — a round
  **Ø9.412 mm**
  cupped thumb surface with four raised X-dashes. It is also solid except for the rectangular shaft
  socket. There is no cone land, hollow cylinder or restrictor: it preserves
  the joystick's **full 30° throw** and its outer profile is sized against SW4
  at that angle. **Print it in TPU ~95A.**
- **The conventional Ø12 restricted topper** (`stick_topper_v2_restricted_12mm_cell2.stl`) —
  use it with `ya13_restrictor_cap_TPU_print_roof_down.stl`. The separate cap's
  continuous wall and four narrow U-notches limit the joystick to
  **15.354–15.487°**, leaving **0.431 mm** minimum clearance to the adjacent
  17.5 mm key. The topper itself contains no restrictor.

**One current socket:** all three ship at **2.00 × 1.25 × 4.00 mm**. This
replaces the obsolete 2.10 × 1.30 LOW and 2.30 × 1.50 HIGH files. Small
internal TPU features are printer-sensitive; confirm that the first print
seats without rotation. The restrictor is also TPU/process-sensitive and its
self-retention must be checked on the physical switch.

**Provenance.** The six encoder outputs retain their existing generator gates.
The four joystick files are byte-for-byte copies of the approved development
outputs; their byte identities are recorded in `MANIFEST.md`. The public
release is consumption-only and does not regenerate these files.

**A note on the STL sizes:** these files were re-exported 2026-08-21 at the
house topper deflection (5e-3 mm / 0.2 rad) after the first cut shipped at a
default that put 78 MB into six textured-knob meshes. **The geometry is
identical** — only tessellation changed, and every mesh is within **0.23 %** of
its exact solid volume.

---

## (g) Optional PORON ledge-gasket kit (assembly note)

**OPTIONAL accessory — NO geometry change anywhere.** A user-cut `0.5 mm` PORON
foam kit that turns the band rabbet ledge's `+0.3 mm` air gap over the PCB rim
into a gentle downward preload (`0.5 mm` foam into the `0.3 mm` gap = **40 %**
compression, PORON's `20–50 %` sweet spot). Ten `~15 × 1.2 mm` adhesive segments
stick to the **BAND ledge underside** — `W×3, E×3, N×2, S×2` — clear of the four
corner caps (`BOSS_CENTERS ± SOCKET_D`) and the USB aperture span. Derived purely
from the band ledge constants; the **tray / plate / board files and md5s are
UNTOUCHED**, and the kit is **INNER-derived, so it is the same part at every
band wall** — re-run against the shipping `w5.4` band it re-measures the identical
ledge ring (`84.8 × 100.6 / 82.4 × 98.2`, width `1.2`, underside `+0.300`) and
regenerates `gasket_template.svg` / `.png` byte-identical. The bare
ledge is already the `0.3 mm` backstop, so the kit is entirely optional and
reversible. **Nothing here is fab-ordered** — the order hold in force above is
unaffected.

**Files:** `hardware/case/v2/gasket/` — `gasket_template.pdf` (print at 100%,
verified 1:1), `gasket_template.svg`, `gasket_template.png`, `gasket_segments.dxf`
(craft cutters), `README.md` (material spec + cut/place + compression math),
`gen_gasket.py` (regenerates from the case-model constants). See MANIFEST.md and
CASE-V2-NOTES §15 (gasket-kit addendum).

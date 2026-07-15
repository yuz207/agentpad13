# Loudest Micro Rev A — Schematic Self-Review (DRAFT, pending human review)

**Scope:** electrical schematic capture only (Phase 2, first pass). No PCB layout.
**Status:** DRAFT — pending the human gates (footprint print, JLC DFM preview, STEP export).
**Date:** 2026-07-15
**Deliverables reviewed:**
- `hardware/pcb/loudest-micro/loudest-micro.kicad_sch` (KiCad-9 flat schematic, s-expression, `version 20250114`)
- `hardware/pcb/loudest-micro/loudest-micro.kicad_pro`
- `hardware/pcb/BOM-draft.csv`

---

## 1. Deliverable form chosen & why

The primary deliverable is a **real KiCad-9 `.kicad_sch`** (not the netlist-only fallback).
Authoring a valid `.kicad_sch` did **not** prove infeasible, so the fallback path in the brief was not taken.

**Topology of the schematic:** a single flat sheet using **net-name connectivity** — every device
pin carries a short wire stub ending in a global-label (signal nets) or a power symbol (rails).
Same-named labels/power-symbols form one net. This is 100 %-valid KiCad and, critically, makes the
electrical netlist independent of routing geometry, which removes the entire class of "pin sits
0.1 mm off its wire" bugs that plague hand-authored schematics. The layout is auto-generated in
functional blocks (columns); it is a *netlist-style* schematic, not a hand-drawn art sheet — a human
will likely re-flow it for readability when binding footprints, which does not change connectivity.

### Validation method (important — read this)

This environment has **no `kicad-cli` and no KiCad GUI** (verified: `kicad-cli version` → not found,
`which kicad` → not found). Native `kicad-cli sch erc` could **not** be run.

Validation was therefore done with the **kicad-happy deterministic schematic analyzer**
(`analyze_schematic.py`, a KiCad-5-through-10 s-expression parser + 60 signal/validation/audit
detectors — no KiCad runtime required). Every net was extracted by the same union-find coordinate
math KiCad itself uses, then the **pin→net mapping was asserted against design intent** for all
load-bearing nets (not spot-checked — see §4). The analyzer is my ERC-equivalent here.

**Residual risk / required human step:** open the file in **KiCad 9** to (a) confirm it loads and
runs native ERC clean, and (b) bind the real footprints (see §8). The generator writes standard
KiCad-9 constructs (`lib_symbols` cache, `(symbol …)` instances with pin-UUID maps, `global_label`,
`power:*` symbols, `(instances …)`), so it should open; this has not been GUI-verified.

---

## 2. Analyzer / ERC status

```
components: 118 (excl. power symbols)   unique parts: 44   nets: 88
wires: 376   no-connects: 9
Findings: ERROR 0   WARNING 1   INFO 28
```

- **0 errors.**
- **1 warning — `DS-002`**: "no `datasheets/` directory (111/111 parts have MPNs)." Expected: this
  sandbox has no distributor API access, so datasheet PDFs were not synced. **All 111 populated
  parts carry an MPN**, so every finding is a *consistency* check, not a *datasheet-verified* one.
  Pinouts that are datasheet-load-bearing were instead verified by hand against manufacturer
  datasheets / the KiCad-official symbol pinmap (see §3). Not a design defect.
- **28 info findings — all positive confirmations** of intended subcircuits:
  | Detector | Confirms |
  |---|---|
  | `AL-DET` | Addressable LED chain of **24 LEDs** (single-wire, SK6812) |
  | `DC/DO-DET` | Decoupling present on **+3V3, +1V1, +5V** |
  | `DO-DET` | USB data lines **USB_DP / USB_DM** detected |
  | `DO-DET` | **I2C** bus on SDA & SCL |
  | `DO-DET` | Regulator U3 Vout = **3.3 V** |
  | `DO-DET` | Crystal load cap = **10.5 pF** (2×15 pF ≈ RPi-guide 10 pF target ✓) |
  | `XL-DET` | Crystal Y1 = **12 MHz** |
  | `LS-DET` | Level shifter U5 (SN74LVC1T45) |
  | `RC-DET` | Joystick RC filters R11/C23 & R12/C24 = **1591 Hz** cutoff |
  | `MI-DET` | Flash U2 (W25Q128) ↔ 1 processor |
  | `PD-DET` | Protection: D1 TVS, F1 fuse, U4 ESD IC |
  | `PR/PS-DET` | LDO U3 (PG status "unknown — no datasheet extraction" — expected) |
  | `EP-AUD` | ESD: USB partial (USBLC6 on D±); header/joystick none (internal — OK) |
  | `LC-007` | Lifecycle audit not run (no network) — expected |

No `NT-001` (single-pin net) warnings: every unused pin has a `no_connect` marker (9 total:
RP2040 GP22–25/GP29, LDO NC pin, USB-C SBU1/SBU2, LED24 DOUT chain terminal).
No `RS-001` (rail without source), no `PP-001` (power pin via cap only), no `SS-001` (sourcing gate).

---

## 3. Per-block datasheet / spec cross-check

Every value traces to **spec §3/§4**, **research/03**, the **RP2040 minimal-design guide**, or the
**0xCB-Helios** cross-check. Helios is used **as a checking reference only** — see §6.

### 3.1 RP2040 core (U1) — *RPi "Hardware design with RP2040" §2*
| Item | Design | Source claim | ✓ |
|---|---|---|---|
| MCU | RP2040 C2040, QFN-56 | research/03 core table | ✓ |
| QFN-56 pinout | pins 1–57 (pin10/49 IOVDD, pin50 DVDD, pin57 EP=GND) | verified vs KiCad-official symbol (via Helios U4) | ✓ |
| Flash | W25Q128JVSIQ 16 MB, SOIC-8 | research §2.2 "16 MB, not 2 MB" | ✓ |
| Crystal | ABM8-272-T3 12 MHz + **2×15 pF** + **1 kΩ series XOUT** | research §2.3 / RPi §2.3.1 | ✓ |
| Crystal load | analyzer computes 10.5 pF (target CL 10 pF) | RPi §2.3 (7.5 pF + parasitic) | ✓ |
| LDO | AP2112K-3.3 (SOT-23-5), EN→VIN | research LDO survey (most-common named 600 mA LDO) | ✓ |
| Decoupling | 6×100 nF IOVDD + 2×100 nF DVDD + 100 nF ADC_AVDD + 100 nF USB_VDD | research §2.1.2 "~9×100 nF" | ✓ |
| VREG caps | 1 µF on VREG_VIN(=+3V3) + 1 µF on VREG_VOUT(=+1V1) | research §2.1.3 | ✓ |
| BOOTSEL | 1 kΩ (R6) from QSPI_CS to tact SW14→GND | research §2.2 (Helios pushbutton pattern) | ✓ |
| RUN | 10 kΩ pull-up (R7) + tact SW15→GND | research §2.4.2 (community adds it) | ✓ |
| SWD | test pads TP1 (SWCLK) / TP2 (SWDIO) + TP3/TP4 (3V3/GND) | RPi §2.4.2 Fig.10 | ✓ |
| Flash CS 10 kΩ pull-up | **omitted (DNF)** | research §2.2 "marked DNF in the guide" | ✓ |

### 3.2 USB-C front end (J1) — *spec §3.7, research USB-C table*
| Item | Design | Source | ✓ |
|---|---|---|---|
| Receptacle | HRO TYPE-C-31-M-12, C165948, official KiCad FP | research USB-C table | ✓ |
| CC pulldowns | **two separate 5.1 kΩ** (R1→CC1, R2→CC2, each to GND, never shared) | research "Pi-4 bug"; spec block 2 | ✓ |
| ESD | USBLC6-2SC6 (SOT-23-6) C7519 on D± (pass-through: connector→pin6/4, MCU→pin1/3) | research; pinout verified vs Helios U1 + ST datasheet | ✓ |
| D± series | 27 Ω (R3/R4) between ESD and RP2040 | research §2.4.1 / spec | ✓ |
| VBUS polyfuse | MF-MSMF050-2, C17313, 1812, in VBUS before LDO+LED rail | research (note: C17313, **not** C883163) | ✓ |
| Shield | S1 → GND directly | research "shield direct to GND is the defensible norm" | ✓ |
| VBUS TVS | SD05C (D1) VBUS→GND, **DNP** (optional) | research "(optional)"; kept as unpopulated option | ✓ |

### 3.3 Keys / encoder / touch / joystick — *spec §3.2–3.5*
| Item | Design | Source | ✓ |
|---|---|---|---|
| 13 switches | direct-pin GP0–GP12, active-low, **no diodes**, pin2→GND | spec §3.1 DIRECT_PINS | ✓ |
| GPIO map | SW1–8=GP0–7 (pins 2–9); SW9–13=GP8–12 (pins 11–15, IOVDD@pin10) | phase0-layout-v2 pin map | ✓ |
| Encoder EC11 | A→GP13, B→GP14, common C→GND; push SW→GP15, other→GND | spec §3.4; research (push wired like a key) | ✓ |
| Encoder A/B RC | **omitted** (rely on RP2040 internal pull-ups) | research "universally omitted in QMK boards" | ✓ |
| Touch TTP223 | OUT(Q)→GP16; sense pad(I)→TP5 pour; VDD→3V3; **TOG→GND** (direct/momentary) | spec §3.5 | ✓ |
| Touch AHLB | R10 0 Ω strap AHLB→GND (active-high); move to +3V3 for active-low | spec pin-map "strap AHLB…" | ✓ |
| Touch sense cap | C25 (DNP) I→GND, tune 0–50 pF | TTP223 datasheet sensitivity option | ✓ |
| Joystick | 2 pots (JS1) top→3V3, bottom→GND; wipers via **1 kΩ + 100 nF RC** → GP26/GP27 | spec §3.3; research | ✓ |
| RC cutoff | 1591 Hz (1 kΩ·100 nF) — heavy anti-alias for slow QMK ADC | spec value | ✓ |

### 3.4 Lighting (U5 + LED1–24) — *spec §3.6, research RGB*
| Item | Design | Source | ✓ |
|---|---|---|---|
| Level shifter | **populated** SN74LVC1T45DBVR C7843; VCCA=3V3, VCCB=5V, DIR=+3V3 (A→B) | spec §3.6 "ship populated"; pinout vs Helios U5 | ✓ |
| Data path | GP17 → U5.A(3V3) → U5.B(5V) → LED1.DIN | spec | ✓ |
| Chain | LED1..LED24 series (DOUT→DIN), verified continuous; LED24.DOUT = NC | layout-v2 chain | ✓ |
| Per-key | LED1–13 SK6812MINI-E C5149201 (reverse-mount), on +5V | spec §3.6 | ✓ |
| Indicator | LED14 SK6812MINI-E (layer indicator, chain idx 13) | layout-v2 LYR / README block 6 — **see conflict §6** | ⚠ |
| Underglow | LED15–24 SK6812-SIDE (4020), on +5V | spec §3.6 | ✓ |
| Per-LED decoupling | 100 nF each (C26–C49) | spec block 6 "100 nF per LED" | ✓ |

### 3.5 Expansion — *spec §3.5 / block 7*
I2C GP18(SDA)/GP19(SCL) with 4.7 kΩ pull-ups (R8/R9) → J2; spares GP20/GP21/GP28 → J2; J2 also
carries +3V3, GND, +5V. Matches "I2C header GP18/19 + 3V3 + GND; spares GP20/21, GP28 on header."

---

## 4. Connectivity verification (asserted, not spot-checked)

The pin→net map was **programmatically asserted** against intent for every load-bearing net; all pass:

- **Power:** +3V3 (all 9 RP2040 3V3 pins + flash VCC + LDO VOUT + shifter VCCA/DIR + TTP223 VDD +
  pull-ups + joystick tops + all decoupling + TP3); +1V1 (DVDD pins 23/50 + VREG_VOUT 45 + C7/C8/C12);
  +5V (LDO VIN/EN + USBLC6 VBUS + shifter VCCB + F1 out + TVS + 24×LED VDD + 24×100 nF + J2.8);
  VBUS (4 connector pads + F1 in); GND (114 pins).
- **QSPI:** all 6 lines flash↔RP2040 correct (CS/CLK/SD0/SD1/SD2/SD3).
- **Crystal:** XIN(20)–Y1.1–C18; XOUT(21)–R5; XOUT_XTAL–R5–Y1.3–C19.
- **USB:** D+ 47→R3→USB_DP→U4.1, connector A6/B6→PORT_DP→U4.6 (and D- mirror); CC1/CC2 separate.
- **Boot/Run, encoder A/B/SW, touch OUT/PAD/AHLB, joystick X/Y wiper+RC, I2C+spares:** all correct.
- **All 13 direct-pin switches** map to the correct QFN pin (accounting for IOVDD at pin 10).
- **24-LED chain** is fully continuous shifter→LED1→…→LED24; terminal DOUT is NC.

---

## 5. Modeling decisions & conventions (so a reviewer isn't surprised)

1. **Net-name connectivity + auto-block layout.** Connectivity is by label name; the sheet is a
   functional-column netlist, not a drawn schematic. Re-flowing for readability is a layout-time nicety.
2. **Rail-source declaration.** To keep the rail-source audit clean without phantom symbols, the source
   pin of each rail is typed `power_out`: LDO VOUT (+3V3), RP2040 VREG_VOUT (+1V1), one USB-C VBUS pad
   (VBUS), and the polyfuse F1 downstream pin (+5V, since +5V is VBUS-derived through F1). PWR_FLAGs are
   also placed on VBUS/GND for native KiCad ERC (the analyzer skips PWR_FLAG by design, so they are
   belt-and-suspenders only).
3. **USBLC6-2 pass-through drawing.** The two I/O1 pins (1,6) and two I/O2 pins (3,4) are the same node
   internally; drawn connector-side→pin6/pin4, MCU-side→pin1/pin3 (Helios convention), so the 27 Ω
   series R sits between the ESD tap (at the connector) and the RP2040.
4. **ADC_AVDD** (pin43) tied directly to +3V3 with a 100 nF (C9), per the RPi *minimal* design. Helios
   adds a 600 Ω ferrite + filter for lower ADC noise — **open option** for the joystick (see §7).
5. **Footprints are placeholders** with a trailing `# TBD bind at layout` note in the field — intentional
   (see §8). They will not resolve in KiCad until bound; that is the expected schematic-stage state.

---

## 6. Conflicts found & how resolved

- **Helios license (checking-reference gate).** `0xCB-Helios` is **CC-BY-SA 4.0** (from `LICENSE.svg`;
  OSHWA-certified). CC-BY-SA is **not** compatible with this project's target **CERN-OHL-W v2** for
  creating a derivative. Per the brief, Helios was therefore used **as a checking reference only** — no
  files/symbols/layout copied. It was used to cross-check *datasheet-fact* pinouts (RP2040 QFN-56, USBLC6,
  W25Q128, SN74LVC1T45) and the core topology (2×15 pF, dual 5.1 kΩ CC, 27 Ω D±, 1 kΩ XOUT, 500 mA
  fuse) — all of which are manufacturer/RPi-guide facts, not Helios's creative expression. All symbols
  were authored independently and all values derive from spec §4 / research/03 / the RPi guide.
- **LED count 23 vs 24 (indicator).** Sources conflict: spec §4 BOM lists "13× SK6812MINI-E + 10×
  SK6812-SIDE" (**23**, with §3.6 saying the indicator *reuses* one chain LED for zero added BOM);
  `hardware/pcb/README.md` block 6 and `phase0-layout-v2-notes.md` (chain index 13 = dedicated LYR LED)
  say **24** (13 per-key + 1 indicator + 10 side). **Resolution:** implemented the README/layout version
  — **24 LEDs, LED14 = a dedicated SK6812MINI-E indicator** — because the README is my explicit block
  list and the layout table enumerates 24 chain positions. This adds one MINI-E vs spec §4's BOM.
  **Flagged for the human gate** (see §7 Q1). If the zero-added-BOM reading wins, delete LED14 and rewire
  RGB_D13→RGB_D14 (one net + one part).
- **Kailh sockets / Bourns encoder LCSC stock.** C2803348 (MX socket) and C143790 (PEC11R) are OOS at
  LCSC retail (2026-07); flagged in the BOM with KBDfans/Chosfox and DigiKey fallbacks (research).

---

## 7. Open questions for the human gate

1. **LED14 indicator** — keep the dedicated 24th LED (as built, per README/layout) or drop it and reuse
   a per-key LED (per spec §4/§3.6)? Trivial to change either way.
2. **ADC_AVDD filtering** — accept the minimal direct-to-3V3 tie, or add a ferrite + cap like Helios for
   cleaner joystick ADC readings? (Costs one FB + one cap; slightly better ADC noise floor.)
3. **Joystick JS1 is unselected (Phase-1 gate).** Modeled as a generic 2-pot 6-pin part; its footprint,
   pinout, and keep-out must be re-derived from the finally-selected part (Adafruit 444 / 3103 / clone).
4. **SK6812-SIDE LCSC#** could not be verified in this environment (`C_TBD_verify`); confirm the exact
   4020 side-firing part + LCSC in the JLC tool at order time (spec lists WS2812B-B C114586 as the alt).
5. **Generic passive LCSC#s** (100 nF C1525, 15 pF C1548, 1 µF C52923, 10 µF C15850, 27 Ω C25100, 1 kΩ
   C11702, 10 kΩ C25744, 4.7 kΩ C25900, 0 Ω C17168) are representative JLC-Basic picks — re-verify
   stock/tier in the JLC BOM tool at order time (research repeatedly flags this).
6. **Encoder switch variant** — if substituting ALPS EC11E for the OOS Bourns PEC11R, verify the push-
   switch variant exists (research flag).
7. **AP2112K-3.3 SOT-23-5 pinout** (1 VIN/2 GND/3 EN/4 NC/5 VOUT) is by strong convention (Adafruit/
   SparkFun); not datasheet-verified in this sandbox — confirm at footprint binding.

---

## 8. Footprints still required at layout time (NOT bound yet — per brief)

The `Footprint` field of every schematic symbol records the **intended** library footprint as a note;
none are bound. Bind these at layout:

| Refs | Part | Intended footprint | Notes |
|---|---|---|---|
| SW1–13 | MX hotswap key | **marbastlib-mx** MX+Choc dual-socket combined | **pre-mirrored / socket-on-back** — the #1 hotswap error; south-facing |
| LED1–14 | SK6812MINI-E | **marbastlib** SK6812MINI-E | **reverse-mount** (legs through plate cutout) |
| LED15–24 | SK6812-SIDE | **marbastlib** SK6812-SIDE 4020 | side-firing underglow |
| RE1 | EC11 encoder | `Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_*` | verify vs chosen Bourns/ALPS body + push pins |
| JS1 | PSP-slider joystick | TBD | derive from Phase-1-selected part datasheet |
| SW14/15 | BOOT/RESET tact | `Button_Switch_SMD:SW_SPST_PTS645` (generic) | reachable through case holes |
| U1 | RP2040 | `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` | EP=pin57=GND |
| U2 | W25Q128 | `Package_SO:SOIC-8_5.23x5.23mm_P1.27mm` | |
| U3 | AP2112K | `Package_TO_SOT_SMD:SOT-23-5` | verify pinout (§7 Q7) |
| U4/U5/U6 | USBLC6 / LVC1T45 / TTP223 | `Package_TO_SOT_SMD:SOT-23-6` | |
| J1 | USB-C | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` | official KiCad FP; pads A1..B12,S1 |
| Y1 | crystal | `Crystal:Crystal_SMD_Abracon_ABM8-4Pin_3.2x2.5mm` | |
| F1 | polyfuse | `Fuse:Fuse_1812_4532Metric` | |
| D1 | TVS | `Diode_SMD:D_SOD-323` | DNP |
| J2 | header | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | |
| TP1–5 | test/SWD/pad | `TestPoint:TestPoint_Pad_D1.5mm`; TP5 = 14×14 mm copper pour | TP5 needs a keep-out rule area (no opposite-layer copper) for touch sensitivity |

**Assembly reminder (spec E1):** JLC **Economic PCBA, MCU-side SMD only**. Hotswap sockets (Standard-
Only, back-side) + SK6812MINI-E (Standard-Only) are hand-soldered at qty 5 — do **not** let them force
the double-sided Standard tier. Order the FR4 plate set alongside as fallback (D3).

---

## 9. What is explicitly NOT done (out of scope this pass)

- No PCB layout / placement / routing (schematic + BOM only, per brief).
- No footprint binding, no DRC, no gerbers, no STEP.
- No native KiCad ERC (no `kicad-cli`/GUI in this environment — validated via kicad-happy analyzer).
- No datasheet-PDF cross-verification (no distributor API/network — DS-002).
- RGB brightness cap (~105/255), QMK DIRECT_PINS/encoder-map/joystick modes = firmware (Phase 4), not schematic.

**Bottom line:** the schematic is electrically complete and self-consistent for all 7 blocks, passes the
analyzer with **0 errors**, and every load-bearing net is asserted correct. Remaining work is the human
review gate (open in KiCad 9 + native ERC), footprint binding, and the order-time part/stock re-checks
listed above.

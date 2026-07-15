# PCB — Phase 2 (KiCad 9)

D1 resolved: outline = **84.2 × 103.7 top-band layout** per `docs/independent-design/phase0-layout-v2-notes.md` (+ `layout-v2.json` for kbplacer). Remaining gate before layout completion: **Phase-1 joystick selection** (JS1 keep-out). The schematic is layout-independent and can start immediately.

## Toolchain (locked by research, `research/03`)
- Libraries: **marbastlib** (MX hotswap + SK6812MINI-E combined, pre-mirrored), **ai03 MX_V2**; infused-kim combined footprints if the Choc-v2 option survives Phase 1. Never hand-draw switch/socket footprints.
- Placement: `kicad-kbplacer` reads `docs/independent-design/layout.json` for SW1–13 + per-key LEDs; encoder/joystick/touch/USB/holes hand-placed from the mm table.
- Fab out: **Fabrication Toolkit** (JLC gerber+BOM+CPL) + `kicad-jlcpcb-tools` for LCSC assignment.
- Review: kicad-happy skills (schematic/PCB analyzers, ERC/DRC vs JLC rules, EMC pre-check).

## Schematic blocks (spec §3, all parts with LCSC# in spec §4 BOM)
1. RP2040 core — per RPi minimal design: 16 MB W25Q128JVS, ABM8-272 12 MHz + 15 pF + 1 kΩ XOUT, AP2112K-3.3, 100 nF/pin + 2× 1 µF VREG, BOOT + RESET tacts, SWD pads.
2. USB-C front end — HRO C165948, 2× 5.1 kΩ CC (one per pin, never shared), USBLC6-2SC6, 27 Ω D±, MF-MSMF050-2 polyfuse.
3. 13 switches direct-pin GP0–12 (no diodes), dual-socket combined footprints.
4. EC11 (GP13/14, push GP15 in matrix), TTP223 + pad pour (GP16, AHLB strap).
5. Joystick pots → RC filter → GP26/27.
6. LED chain GP17 → **populated** SN74LVC1T45 → 13 MINI-E + 1 indicator + 10 SK6812-SIDE, 5 V VBUS rail.
7. I2C (GP18/19) + spares (GP20/21, GP28) expansion header.

## Gates before ordering
ERC clean → every footprint vs its datasheet (the single highest-leverage review hour; hotswap footprints MUST be socket-on-back mirrored) → DRC vs JLC rules → 1:1 paper print with real parts on top → JLC DFM/placement preview → STEP export for the case.

Assembly: **Economic PCBA, MCU side only**; hand-solder sockets/LEDs/encoder/joystick (spec E1). Order FR4 plate set alongside as fallback insurance.

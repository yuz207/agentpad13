# Project-local footprint libraries

Vendored footprint libraries for `agentpad13`. These are committed into the repo as
**project-local libs** (standard for open keyboards); nested `.git` directories were removed
after recording the commit hashes below. Registered in
`../agentpad13/fp-lib-table`.

Verified against **KiCad 9.0.9** (`kicad-cli`/`pcbnew` 9.0.9). Every footprint referenced by the
BOM was test-loaded with `pcbnew.FootprintLoad()` and parsed cleanly.

---

## marbastlib (`ebastler/marbastlib`)

| Field | Value |
|---|---|
| Source | https://github.com/ebastler/marbastlib |
| Commit | `6b0a9a73f579e377816d60b58eac2b3252de7868` |
| Date / subject | 2026-03-22 — "Huge release for KiCad 10.0, many new parts" |
| **License** | **CERN-OHL-P v2 (Permissive)** — file `marbastlib/LICENSE` |
| Footprint format | `(version 20240108)`, `generator_version "8.0"` → **KiCad 8/9 format; loads in KiCad 9.0.9** |
| Vendored size | ~48 MB (includes `3dmodels/`, `symbols/`, `PCM/`) |

**License note (task asked "marbastlib is MIT?" — it is NOT):** the repo is **CERN-OHL-P**, not MIT.
This does not block us: CERN-OHL-P is the *permissive* CERN variant and may be incorporated into a
larger **CERN-OHL-W v2** work (permissive → weakly-reciprocal is the allowed direction). Obligation:
**retain the copyright and CERN-OHL-P license notices** (keep `marbastlib/LICENSE`) and identify any
modifications. **Not incompatible with CERN-OHL-W distribution.**

**3D-model caveat:** `marbastlib/readme.md` §"3D models" states some `.step` models are third-party
and **NOT covered by the repo license**. The `.kicad_mod` files reference models via
`${KICAD8_3RD_PARTY}/3dmodels/...` (a PCM/env path), **not** the vendored `3dmodels/` dir — so the
vendored 3D models are currently orphaned. **Recommendation for the human/packaging gate:** either
prune `marbastlib/3dmodels/` before distribution (saves ~44 MB and removes the mixed-license
ambiguity) or vet individual model licenses. 2D footprint use (pads/courtyard) is unaffected.

**Footprints used by this design (family → dir):**
- `marbastlib-mx.pretty` — `SW_MX_HS_CPG151101S11_1u` (Kailh hotswap socket), `LED_MX_6028R`, `STAB_MX_2u`
- `marbastlib-various.pretty` — `LED_6028R` (SK6812MINI-E reverse-mount), `ROT_Alps_EC11E-Switch`, HRO USB-C
- `marbastlib-xp-various.pretty` — `LED_WS2812_4020` (side-firing 4020 / SK6812-SIDE)

---

## MX_V2 (`ai03-2725/MX_V2`)

| Field | Value |
|---|---|
| Source | https://github.com/ai03-2725/MX_V2 |
| Commit | `0b379eebbeb66c7fd6e82e400b47958ad695614e` |
| Date / subject | 2024-08-15 — "Update readme to notify about hotswap footprint updates" |
| **License** | **MIT** (Copyright (c) 2017 ai03) — file `MX_V2/LICENSE` |
| Footprint format | `(version 20240108)`, `generator_version "8.0"` → **KiCad 8/9 format; loads in KiCad 9.0.9** |
| Vendored size | ~4 MB |

**License note:** MIT is permissive; **compatible with CERN-OHL-W distribution**. Obligation: retain
the MIT copyright + permission notice (keep `MX_V2/LICENSE`). Role in this design: **alternative /
fallback** MX hotswap + solderable + stabilizer footprints (`MX_Hotswap.pretty`,
`MX_Solderable.pretty`, `Alps_MX_Stabilizers.pretty`).

---

## License compatibility summary (target: CERN-OHL-W v2)

| Library | License | Compatible w/ CERN-OHL-W distribution? | Obligation |
|---|---|---|---|
| marbastlib | CERN-OHL-P v2 (permissive) | **YES** | retain notices; mark modifications; vet/prune 3D models |
| MX_V2 | MIT | **YES** | retain MIT notice |

**No library carries a license incompatible with CERN-OHL-W distribution.** (For contrast, the
`0xCB-Helios` reference used during schematic capture is CC-BY-SA 4.0, which *would* be incompatible —
that is why it was used as a checking reference only and no files were copied.)

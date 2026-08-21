#!/usr/bin/env python3
"""Generate `out/catalog.json` from `release/MANIFEST.md`.

THE MANIFEST GATE (spec 2026-08-20-configurator-design.md section 4):
every path this catalog emits must (a) appear in the manifest and (b) exist on
disk. Any miss fails the build with a nonzero exit and a list of the misses,
so the site can never drift from the release bundle.

Run:  python3 configurator/build/gen_catalog.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    GateError,
    OUT_DIR,
    PLATE_MARKERS,
    RELEASE,
    TEXTURE_OPENINGS,
    iter_catalog_paths,
    read_manifest,
    release_rel,
    repo_path,
    sha256_file,
    stated_file_count,
    write_json,
)

# --------------------------------------------------------------------------
# Source-of-truth constants. Every one of these is a QUOTATION, not a choice.
# --------------------------------------------------------------------------

# release/HOW-TO-ORDER.md §4 Band -- `_w5.4` is the default.
BAND_DEFAULT = "w5.4"
# release/HOW-TO-ORDER.md §8 Toppers -- bore ladder, print `nom` first.
KNOB_DEFAULT_BORE = "nom"
# release/HOW-TO-ORDER.md §8 Toppers -- start `nom` on either stick part.
STICK_DEFAULT_SOCK = "nom"
# release/hardware/case/v2/bases/INTERFACE.md:41 -- "start with 5.8 in rigid
# filament, 5.9 in TPU". 5p8 is the rigid-filament start and is what the
# viewer mesh is built from (the peg Ø is not visible at viewer scale).
BASE_DEFAULT_PEG = "5p8"
# v2 toppers (2026-08-21): three knobs, no params default_variant -- A (helical
# knurl) is the knurled_cup's successor and the catalog default.
KNOB_DEFAULT_STYLE = "A"
# v2 stick: two PARTS (release/HOW-TO-ORDER.md §8) -- the nub is the
# full-throw-safe default; the puck needs TPU and its integral stop.
STICK_DEFAULT_STYLE = "nub_C2"

FABPACK = "hardware/pcb/fabpack_out_v5_7"
CASE = "hardware/case/v2"
CAPS = "hardware/PCBWay_keycaps_boxfit_2026-07-24"

BAND_WIDTHS = ["w3.0", "w5.4", "w7.4"]
PEG_RUNGS = ["5p6", "5p7", "5p8", "5p9"]
KNOB_BORES_V2 = ["tight", "nom", "loose"]
KNOB_STYLES = ["A", "B2", "C"]
# per-part sock rungs (release/hardware/case/v2/toppers/params/stick_topper_v2_params.json)
STICK_PARTS = {"nub_C2": ("stick_nub_v2_C2", ["nom", "p05", "p10"]),
               "puck_TPU": ("stick_puck_v2_TPU", ["m05", "nom"])}
BASE_ITEMS = ["riser", "wedge", "pedestal"]
CAP_PROFILES = ["dish", "plateau"]
CAP_SIZES = ["1u", "2u", "2u_stab"]
# keycaps/params_boxfit/keycap_params.json cap_sizes.sets:
#   17p5 -> PRIMARY, stl_suffix "_17p5";  18 -> ALTERNATE, no suffix
CAP_WIDTHS = {"17p5": ("_17p5", 17.5, "primary"), "std": ("", 18.0, "alternate")}


def cap_file(profile: str, size: str, width: str) -> str:
    suffix, _mm, _status = CAP_WIDTHS[width]
    return f"{CAPS}/cap_{profile}_{size}{suffix}_boxfit.stl"


# --------------------------------------------------------------------------
# firmware.flash -- READ OUT OF THE DOC, never typed in here
# --------------------------------------------------------------------------
# release/firmware/BRING-UP.md Step 1 carries the one flash command that works
# on macOS, inside a fenced block introduced by "**This always works:**". The
# site had it as a hardcoded fallback constant (configurator/site/sheet.js);
# this makes the DOC the source, so the two can never drift.

_FLASH_LINE = re.compile(r"^>?\s*(dd\s+if=\S+.*?)\s*$")
# Tokens the extracted command must contain, so a command that no longer
# flashes THIS firmware to THIS bootloader volume fails loudly.
_FLASH_REQUIRED = ("agentpad13.uf2", "RPI-RP2", "bs=")


def flash_command(doc: Path) -> tuple[str, int]:
    """The `dd` flash line from BRING-UP.md, VERBATIM, with its line number.

    Raises GateError rather than falling back to a constant: a hardcoded copy
    is exactly the drift this key exists to remove.
    """
    doc = Path(doc)
    try:
        name = f"release/{doc.relative_to(RELEASE)}"
    except ValueError:  # a test fixture outside the bundle
        name = str(doc)
    lines = doc.read_text(encoding="utf-8").splitlines()
    hits = [
        (i + 1, m.group(1))
        for i, ln in enumerate(lines)
        if (m := _FLASH_LINE.match(ln))
    ]
    if len(hits) != 1:
        raise GateError(
            f"{name}: expected exactly ONE `dd if=` flash line, found "
            f"{len(hits)}"
            + (f" (at lines {[h[0] for h in hits]})" if hits else "")
            + ". The bring-up doc changed shape -- re-derive the parse against "
            "the real format. Do NOT fall back to a hardcoded command: the doc "
            "is the source of truth for this key."
        )
    lineno, cmd = hits[0]
    missing = [t for t in _FLASH_REQUIRED if t not in cmd]
    if missing:
        raise GateError(
            f"{name}:{lineno}: the flash command {cmd!r} is missing {missing}. "
            "It no longer writes this project's UF2 to the RP2040 bootloader "
            "volume -- do not publish it."
        )
    return cmd, lineno


def build_catalog(manifest_sha: str, bringup: Path | None = None) -> dict:
    """Assemble the catalog. Paths are release-relative here; release_rel()
    turns them into repo-relative `release/...` strings at emit time.

    `bringup` overrides the flash-command source doc; tests use it to prove the
    parse FAILS on a doctored doc instead of silently emitting a stale command.
    """

    def R(p: str) -> str:
        return release_rel(p)

    board = {
        "fabpacks": {
            "opaque": R(f"{FABPACK}/fabpack_opaque.zip"),
            "translucent": R(f"{FABPACK}/fabpack_translucent.zip"),
        },
        # HOW-TO-ORDER §2 uploads gerbers + BOM/CPL separately.
        "gerbers": R(f"{FABPACK}/gerbers_v5_7.zip"),
        "assembly": {
            "bom_opaque": R(f"{FABPACK}/assembly/bom_opaque.csv"),
            "bom_translucent": R(f"{FABPACK}/assembly/bom_translucent.csv"),
            "cpl_opaque": R(f"{FABPACK}/assembly/cpl_opaque.csv"),
            "cpl_translucent": R(f"{FABPACK}/assembly/cpl_translucent.csv"),
            "hand_solder_afterlist": R(f"{FABPACK}/assembly/hand_solder_afterlist.csv"),
        },
        "outline_mm": [84.2, 100.0],
        "thickness_mm": 1.6,
        "mesh": "meshes/board.glb",
        "texture": "meshes/board_top.png",
        "texture_source": R("hardware/pcb/v5_7_render_top.png"),
    }

    plate_variants = [
        dict(
            id="standard",
            gerbers=R(f"{CASE}/fab/plate_v5_gerbers.zip"),
            kicad_pcb=R(f"{CASE}/fab/agentpad13_v2_plate_v5.kicad_pcb"),
            marker_note=(
                "Ø12 F.Mask opening over the Ø14 F.Cu pad = an exposed ENIG "
                "gold disc, the owner's requested 'circle to indicate there's "
                "a touchpad'. ORDER ENIG so the disc is flat gold, not HASL "
                "solder (CASE-V2-NOTES.md sections 5 and 6)."
            ),
        ),
        dict(
            id="tented_ring",
            gerbers=R(f"{CASE}/fab/plate_v5_ring_gerbers.zip"),
            kicad_pcb=R(f"{CASE}/fab/agentpad13_v2_plate_tented_ring_v5.kicad_pcb"),
            marker_note=(
                "The pad is TENTED (no mask opening, so no exposed copper) and "
                "the marker is a Ø16 front-silkscreen ring, 0.2 mm stroke. "
                "Silkscreen is white on every mask colour, so this variant "
                "does not need the ENIG finish."
            ),
        ),
        dict(
            id="blank",
            gerbers=R(f"{CASE}/fab/plate_v5_blank_gerbers.zip"),
            kicad_pcb=R(f"{CASE}/fab/agentpad13_v2_plate_blank_v5.kicad_pcb"),
            marker_note=(
                "MARKERLESS BY DESIGN: this variant carries no copper at all "
                "(a mask-over-laminate blank), so there is nothing over TP5 to "
                "draw and `decal` is null -- not a missing file. It reverts the "
                "touch key to the attenuated through-air mode "
                "(CASE-V2-NOTES.md section 5 option (c))."
            ),
        ),
    ]
    for v in plate_variants:
        v["marker"], v["decal"] = PLATE_MARKERS[v["id"]]

    plate = {
        "variants": plate_variants,
        # All three variants share ONE Edge.Cuts profile -- validate_fab_v5.py
        # reports "RESULT: ALL GATES PASS (3/3 variants)" against the same
        # geometry (public CASE-V2-NOTES.md §14). So one mesh AND one openings map
        # serve all three; gen_textures.py re-proves the identity from the
        # boards themselves before sharing the map.
        "mesh": "meshes/plate.glb",
        "openings_map": {
            "path": TEXTURE_OPENINGS,
            "px_per_mm": 10,
            "size_px": [844, 1000],
            "extent_mm": {"x0": -0.1, "y0": 0.0, "x1": 84.3, "y1": 100.0},
            "note": (
                "RGBA. WHITE and opaque where the plate is material, fully "
                "TRANSPARENT where the fab routes an opening. It carries NO "
                "ground colour on purpose -- tint it with the chosen mask or "
                "filament colour at runtime (as a base-colour map under a "
                "colour tint, or as an alpha map). Board frame: image row 0 is "
                "board y = 0, the FAR / USB edge away from the user; image "
                "column 0 is board x = -0.1. Shared by all three variants."
            ),
        },
        "step": R(f"{CASE}/step/agentpad13_v2_plate.step"),
        "dxf": R(f"{CASE}/fab/agentpad13_v2_plate_v5.dxf"),
        "size_mm": [84.4, 100.0],
        "thickness_mm": 1.6,
    }

    band = {
        "default": BAND_DEFAULT,
        "widths": [
            {
                "id": w,
                "stl": R(f"{CASE}/stl/agentpad13_v2_band_1.6mm_{w}.stl"),
                "step": R(f"{CASE}/step/agentpad13_v2_band_1.6mm_{w}.step"),
                "mesh": f"meshes/band_{w}.glb",
                "wall_mm": float(w[1:]),
            }
            for w in BAND_WIDTHS
        ],
    }

    tray = {
        "stl": R(f"{CASE}/stl/agentpad13_v2_tray_v5.stl"),
        "step": R(f"{CASE}/step/agentpad13_v2_tray_v5.step"),
        "mesh": "meshes/tray.glb",
    }

    bases = {
        "gauge": R(f"{CASE}/bases/stl/base_fit_gauge.stl"),
        "interface": R(f"{CASE}/bases/INTERFACE.md"),
        "default_peg": BASE_DEFAULT_PEG,
        "peg_rungs": PEG_RUNGS,
        "items": [
            {
                "id": item,
                "pegs": {
                    rung: R(f"{CASE}/bases/stl/base_{item}_peg_{rung}.stl")
                    for rung in PEG_RUNGS
                },
                "mesh": f"meshes/base_{item}.glb",
            }
            for item in BASE_ITEMS
        ],
    }

    keycaps = {
        "profiles": CAP_PROFILES,
        "widths": list(CAP_WIDTHS),
        "counts": keycap_counts(),
        "files": [
            {
                "profile": profile,
                "width": width,
                "size": size,
                "width_mm": CAP_WIDTHS[width][1],
                "stl": R(cap_file(profile, size, width)),
                "mesh": f"meshes/cap_{profile}_{size}_{width}.glb",
            }
            for profile in CAP_PROFILES
            for width in CAP_WIDTHS
            for size in CAP_SIZES
        ],
    }

    toppers = {
        "knobs": [
            {
                "id": style,
                "default": style == KNOB_DEFAULT_STYLE,
                "stl": R(f"{CASE}/toppers/stl/knob_v2_{style}_bore_{KNOB_DEFAULT_BORE}.stl"),
                "bores": {
                    b: R(f"{CASE}/toppers/stl/knob_v2_{style}_bore_{b}.stl")
                    for b in KNOB_BORES_V2
                },
                "mesh": f"meshes/knob_{style}.glb",
            }
            for style in KNOB_STYLES
        ],
        "stick_caps": [
            {
                "id": part,
                "default": part == STICK_DEFAULT_STYLE,
                "stl": R(f"{CASE}/toppers/stl/{stem}_sock_{STICK_DEFAULT_SOCK}.stl"),
                "socks": {
                    s: R(f"{CASE}/toppers/stl/{stem}_sock_{s}.stl")
                    for s in socks
                },
                "mesh": f"meshes/stick_cap_{part}.glb",
            }
            for part, (stem, socks) in STICK_PARTS.items()
        ],
        "default_knob_bore": KNOB_DEFAULT_BORE,
        "default_stick_sock": STICK_DEFAULT_SOCK,
        "renders": {
            "knobs": R(f"{CASE}/toppers/renders/toppers_v2_knobs.png"),
            "stick_caps": R(f"{CASE}/toppers/renders/toppers_v2_stick.png"),
        },
    }

    gasket = {
        "files": [
            R(f"{CASE}/gasket/README.md"),
            R(f"{CASE}/gasket/gasket_template.pdf"),
            R(f"{CASE}/gasket/gasket_template.svg"),
            R(f"{CASE}/gasket/gasket_template.png"),
            R(f"{CASE}/gasket/gasket_segments.dxf"),
        ],
        "template_pdf": R(f"{CASE}/gasket/gasket_template.pdf"),
        "readme": R(f"{CASE}/gasket/README.md"),
    }

    flash_doc = bringup or (RELEASE / "firmware/BRING-UP.md")
    flash_cmd, flash_line = flash_command(flash_doc)
    firmware = {
        "uf2": R("firmware/prebuilt/agentpad13.uf2"),
        "flash": flash_cmd,
        # NB the citation is deliberately a SENTENCE, not a bare token. A bare
        # `release/...:42` has no whitespace and would be picked up by
        # common._is_path_value as a repo path, which would then fail the
        # manifest gate because "firmware/BRING-UP.md:42" is not a file.
        "flash_source": (
            f"release/firmware/BRING-UP.md line {flash_line} -- Step 1, the "
            "'This always works' block. Extracted verbatim at build time; the "
            "doc is the source and this key can never drift from it."
        ),
        "flash_doc": R("firmware/BRING-UP.md"),
        "polarity_doc": R("firmware/POLARITY-NOTE.md"),
    }

    docs = {
        "how_to_order": R("HOW-TO-ORDER.md"),
        "release_notes": R("RELEASE.md"),
        "base_interface": R(f"{CASE}/bases/INTERFACE.md"),
    }

    return {
        "schema": "agentpad13-configurator-catalog-v1",
        "generated_from": {"manifest": "release/MANIFEST.md", "sha256": manifest_sha},
        "board": board,
        "plate": plate,
        "band": band,
        "tray": tray,
        "bases": bases,
        "keycaps": keycaps,
        "toppers": toppers,
        "gasket": gasket,
        "firmware": firmware,
        "docs": docs,
    }


def keycap_counts() -> dict:
    """The 1u / 2u / 2u_stab mix for the 13-key layout -- DERIVED, not chosen.

    Positions: contract_v4.json refs SW1..SW12 form the 4x3 1U grid and SW13
    is the single 2U station; agentpad13_case_v2.py:310-311 splits them
    exactly that way (`SW_1U = [SW1..SW12]`, `SW_2U = SW13`).

    Which 2U file: release/HOW-TO-ORDER.md §7 gives the complete rule. Print
    the ordinary `2u` cap without a stabilizer and the shipped `2u_stab` cap
    when a 2U plate-mount stabilizer is fitted.
    """
    return {
        "1u": 12,
        "2u": 1,
        "2u_stab": 0,
        "source": (
            "release/HOW-TO-ORDER.md §7 'Caps and switches': 12x1U + 1x2U; "
            "positions from release/hardware/pcb/harness/contract_v4.json "
            "refs SW1..SW12 (1U grid) + SW13 (2U), split at "
            "release/hardware/case/v2/agentpad13_case_v2.py:310-311"
        ),
        "with_stabilizer": {
            "1u": 12,
            "2u": 0,
            "2u_stab": 1,
            "source": (
                "release/HOW-TO-ORDER.md §7: fitting a 2U plate-mount "
                "stabilizer means printing the shipped `2u_stab` cap; the "
                "slots are measured from all three public plate boards"
            ),
        },
        "note": (
            "Use `with_stabilizer` when the build sheet includes the 2u "
            "plate-mount stabiliser; otherwise the plain `2u` cap. The plate "
            "is identical either way. The public CASE-V2-NOTES.md §8 item 6 "
            "keeps real-stabilizer coupon verification as an open fit check."
        ),
    }


# MANIFEST.md:3 -- "`MANIFEST.md` self-excludes." It cannot list itself, so it
# is exempt from the membership half of the gate but not from the exists half.
SELF_EXCLUDED = {"release/MANIFEST.md"}


def run_gate(catalog: dict, manifest: dict) -> list[str]:
    """Return a list of gate failures (empty == pass)."""
    failures: list[str] = []
    for pointer, repo_rel in iter_catalog_paths(catalog):
        if not repo_rel.startswith("release/"):
            failures.append(f"{pointer}: {repo_rel!r} is not under release/")
            continue
        rel_to_release = repo_rel[len("release/"):]
        if repo_rel not in SELF_EXCLUDED and rel_to_release not in manifest:
            failures.append(
                f"{pointer}: {repo_rel!r} is NOT LISTED in release/MANIFEST.md"
            )
        p = repo_path(repo_rel)
        if not p.is_file():
            failures.append(f"{pointer}: {repo_rel!r} DOES NOT EXIST on disk")
    return failures


def main(argv: list[str]) -> int:
    manifest_path = RELEASE / "MANIFEST.md"
    out_path = OUT_DIR / "catalog.json"
    if "--manifest" in argv:
        manifest_path = Path(argv[argv.index("--manifest") + 1]).resolve()
    if "--out" in argv:
        out_path = Path(argv[argv.index("--out") + 1]).resolve()

    try:
        manifest = read_manifest(manifest_path)
    except GateError as exc:
        print(f"MANIFEST GATE FAILED: {exc}", file=sys.stderr)
        return 2

    stated = stated_file_count(manifest_path)
    if stated is not None and stated != len(manifest):
        print(
            f"MANIFEST GATE FAILED: parsed {len(manifest)} file rows but the "
            f"manifest states {stated} files -- the parser and the bundle "
            "disagree; fix the parser before trusting the catalog.",
            file=sys.stderr,
        )
        return 2

    try:
        catalog = build_catalog(sha256_file(manifest_path))
    except GateError as exc:
        print(f"CATALOG GATE FAILED: {exc}", file=sys.stderr)
        return 2

    failures = run_gate(catalog, manifest)
    if failures:
        print(
            f"MANIFEST GATE FAILED: {len(failures)} catalog "
            f"{'entry' if len(failures) == 1 else 'entries'} do not resolve:",
            file=sys.stderr,
        )
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    write_json(out_path, catalog)
    n_paths = sum(1 for _ in iter_catalog_paths(catalog))
    print(
        f"catalog: {out_path.relative_to(out_path.parents[3])} "
        f"({n_paths} release paths, all present in "
        f"{len(manifest)}-file manifest and on disk)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

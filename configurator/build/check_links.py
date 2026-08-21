#!/usr/bin/env python3
"""Link integrity gate (spec 2026-08-20-configurator-design.md section 6).

Every URL the site can emit must resolve inside the repo tree:
  * every `release/...` path in catalog.json;
  * the build sheet's FIXED links, which appear on every build sheet
    regardless of configuration (spec section 3 item 4 + section 2): the UF2,
    the flash/bring-up doc, the polarity note, the bases INTERFACE.md and the
    gasket files -- checked by name here so that dropping one from the catalog
    is a failure rather than a silent omission;
  * every `meshes/...` reference, against the built mesh directory;
  * every `textures/...` reference, against the built texture directory, plus
    the structural requirement that EVERY plate variant declares a `decal`
    key (null is a valid answer -- the blank plate has no marker to draw -- but
    a missing key is not) and that the shared openings map is published.

Nonzero exit on any miss.

Run:  python3 configurator/build/check_links.py [--catalog PATH]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    MESH_DIR,
    OUT_DIR,
    TEX_DIR,
    iter_catalog_paths,
    iter_mesh_refs,
    iter_texture_refs,
    repo_path,
)

# The links the build sheet always carries. Keys are JSON pointers into
# catalog.json; the gate requires each to be present AND to resolve.
FIXED_LINKS = {
    "/firmware/uf2": "the single UF2 (spec 3.4 'the single UF2')",
    "/firmware/flash_doc": "the flash / bring-up doc (spec 3.4)",
    "/firmware/polarity_doc": "the polarity note (spec 3.4 'polarity/bring-up links')",
    "/bases/interface": "bases INTERFACE.md (spec 2 'DIY bases link to INTERFACE.md')",
    "/gasket/template_pdf": "gasket template (spec 3.3 print manifest)",
    "/gasket/readme": "gasket README (placement instructions)",
}


def pointer_get(obj, pointer: str):
    cur = obj
    for token in pointer.strip("/").split("/"):
        if isinstance(cur, list):
            idx = int(token)
            if idx >= len(cur):
                return None
            cur = cur[idx]
        elif isinstance(cur, dict):
            if token not in cur:
                return None
            cur = cur[token]
        else:
            return None
    return cur


def check(catalog: dict, mesh_dir: Path, require_meshes: bool = True,
          tex_dir: Path | None = None):
    failures: list[str] = []
    checked = 0
    tex_dir = TEX_DIR if tex_dir is None else tex_dir

    for pointer, rel in iter_catalog_paths(catalog):
        checked += 1
        if not repo_path(rel).is_file():
            failures.append(f"{pointer}: {rel} does not resolve in the repo tree")

    for pointer, why in FIXED_LINKS.items():
        val = pointer_get(catalog, pointer)
        if not isinstance(val, str) or not val:
            failures.append(f"FIXED LINK MISSING: {pointer} -- {why}")
            continue
        checked += 1
        if not repo_path(val).is_file():
            failures.append(f"FIXED LINK BROKEN: {pointer} -> {val} ({why})")

    gasket_files = pointer_get(catalog, "/gasket/files") or []
    if not gasket_files:
        failures.append("FIXED LINK MISSING: /gasket/files is empty")

    if require_meshes:
        for pointer, mesh in iter_mesh_refs(catalog):
            checked += 1
            if not (mesh_dir / Path(mesh).name).is_file():
                failures.append(
                    f"{pointer}: {mesh} has not been built into {mesh_dir}"
                )
        tex = pointer_get(catalog, "/board/texture")
        if tex:
            checked += 1
            if not (mesh_dir / Path(tex).name).is_file():
                failures.append(f"/board/texture: {tex} has not been built")

        # Plate art. `decal` is legitimately null on the blank variant (it
        # carries no copper, so there is no marker to draw), so the gate is
        # "every variant declares the key, and every non-null value resolves"
        # -- a missing key is a failure, an explicit null is not.
        for pointer, tex in iter_texture_refs(catalog):
            checked += 1
            if not (tex_dir / Path(tex).name).is_file():
                failures.append(
                    f"{pointer}: {tex} has not been built into {tex_dir}"
                )
        for i, variant in enumerate(pointer_get(catalog, "/plate/variants") or []):
            if "decal" not in variant:
                failures.append(
                    f"/plate/variants/{i}: no `decal` key -- the site cannot "
                    "tell a markerless variant from a missing texture"
                )
        if pointer_get(catalog, "/plate/openings_map/path") is None:
            failures.append(
                "FIXED LINK MISSING: /plate/openings_map/path -- the plate "
                "openings map is shared by every variant"
            )

    return checked, failures


def main(argv: list[str]) -> int:
    catalog_path = OUT_DIR / "catalog.json"
    mesh_dir = MESH_DIR
    tex_dir = TEX_DIR
    require_meshes = "--no-meshes" not in argv
    if "--catalog" in argv:
        catalog_path = Path(argv[argv.index("--catalog") + 1]).resolve()
    if "--meshes" in argv:
        mesh_dir = Path(argv[argv.index("--meshes") + 1]).resolve()
    if "--textures" in argv:
        tex_dir = Path(argv[argv.index("--textures") + 1]).resolve()

    if not catalog_path.is_file():
        print(
            f"LINK CHECK FAILED: {catalog_path} not found -- run gen_catalog.py first",
            file=sys.stderr,
        )
        return 2

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    checked, failures = check(catalog, mesh_dir, require_meshes, tex_dir)
    if failures:
        print(f"LINK CHECK FAILED: {len(failures)} broken:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"links: {checked} references resolve (incl. {len(FIXED_LINKS)} fixed links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

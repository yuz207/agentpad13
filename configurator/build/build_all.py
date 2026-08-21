#!/usr/bin/env python3
"""Run the whole configurator data pipeline and every gate. ONE command.

    python3 configurator/build/build_all.py

Stages, in order (each must exit 0 or the build stops):
  1. gen_catalog.py    catalog.json   + THE MANIFEST GATE
  2. gen_positions.py  positions.json + its source citations
  3. gen_meshes.py     meshes/*.glb   + the board texture chirality gate
  4. gen_textures.py   textures/*.png + the plate identity/census/orientation gates
  5. gen_costs.py      costs.json     (empty stub; never overwrites real data)
  6. check_links.py    every emitted path resolves in the repo tree
  7. unittest          the full test suite (add --no-tests to skip)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
TESTS = BUILD.parent / "tests"
PY = sys.executable


def run(label: str, argv: list[str]) -> bool:
    print(f"\n=== {label} " + "=" * max(0, 62 - len(label)), flush=True)
    r = subprocess.run(argv)
    if r.returncode != 0:
        print(f"\nBUILD FAILED at: {label} (exit {r.returncode})", file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    stages = [
        ("catalog   (manifest gate)", [PY, str(BUILD / "gen_catalog.py")]),
        ("positions (source citations)", [PY, str(BUILD / "gen_positions.py")]),
        ("meshes    (chirality gate)", [PY, str(BUILD / "gen_meshes.py")]),
        ("textures  (plate art gates)", [PY, str(BUILD / "gen_textures.py")]),
        ("costs     (empty stub)", [PY, str(BUILD / "gen_costs.py")]),
        ("links     (integrity gate)", [PY, str(BUILD / "check_links.py")]),
    ]
    if "--no-tests" not in argv:
        stages.append(
            ("tests", [PY, "-m", "unittest", "discover", "-s", str(TESTS),
                       "-p", "test_*.py", "-v"])
        )
    for label, cmd in stages:
        if not run(label, cmd):
            return 1
    print("\n" + "=" * 70)
    print("BUILD OK -- catalog.json, positions.json, costs.json, meshes/, "
          "textures/ all generated and gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

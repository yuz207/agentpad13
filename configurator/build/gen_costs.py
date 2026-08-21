#!/usr/bin/env python3
"""Emit `out/costs.json` -- the deliberately EMPTY cost data file.

Spec 2026-08-20-configurator-design.md section 4: "`costs.json` is a dated
data file; absent values render as no price shown. No numbers are committed
until the owner supplies real ones." Section 2 lists "prices until real data
is supplied" as explicitly OUT of the configurator.

So this file contains exactly `{"updated": null, "lines": {}}` and this script
will REFUSE to overwrite a costs.json that already carries real numbers -- the
owner's data must not be clobbered by a routine rebuild.

Run:  python3 configurator/build/gen_costs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import OUT_DIR, write_json  # noqa: E402

EMPTY = {"updated": None, "lines": {}}


def main() -> int:
    path = OUT_DIR / "costs.json"
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = None
        if isinstance(existing, dict) and (
            existing.get("updated") is not None or existing.get("lines")
        ):
            print(
                f"costs: {path} already holds owner-supplied data "
                f"(updated={existing.get('updated')!r}, "
                f"{len(existing.get('lines') or {})} lines) -- left untouched"
            )
            return 0
    write_json(path, EMPTY)
    print("costs: emitted the empty stub (no numbers -- spec section 4)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

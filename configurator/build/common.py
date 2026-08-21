"""Shared helpers for the agentpad13 configurator data pipeline.

Everything the generators emit is derived from files that ship in `release/`.
Nothing here invents a number: each caller cites the file (and line) it read.

Frames
------
Two coordinate frames appear in this repo and confusing them ships a mirrored
device, so they are named explicitly and used explicitly everywhere:

  BOARD frame ("D", the case model's xy board frame)
      x -> physical RIGHT, y -> physical FRONT (toward the user), z -> UP,
      z = 0 at PCB top face. This is the KiCad/contract frame that
      `hardware/pcb/harness/contract_v4.json` and `agentpad13_case_v2.py`
      both work in. It is LEFT-HANDED -- stated verbatim at
      `release/hardware/case/v2/agentpad13_case_v2.py:1077` ("The design frame
      is LEFT-handed (x right, y DOWN from raw KiCad board coords, z up)").

  PRINT frame ("A")
      What the mirrored-at-export STLs (tray, bases) actually contain:
      y_A = PCB_H - y_D. See `agentpad13_case_v2.py:2483` and
      `bases/agentpad13_base.py:513`, both `Pos(0, PCB_H, 0) * mirror(part,
      about=Plane.XZ)`.

glTF output is emitted in glTF's own Y-up right-handed space via
(X, Y, Z)_gltf = (x, z, y)_D -- a determinant -1 map, which is exactly what
turns the left-handed board-frame numbers into the correctly handed real
device. See build/README.md ("Handedness") for the proof and its checks.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

# configurator/build/common.py -> configurator/build -> configurator -> repo
REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE = REPO_ROOT / "release"
MANIFEST_REL = "release/MANIFEST.md"
OUT_DIR = Path(__file__).resolve().parent / "out"
MESH_DIR = OUT_DIR / "meshes"
TEX_DIR = OUT_DIR / "textures"


class GateError(RuntimeError):
    """A build gate failed. Callers turn this into a nonzero exit."""


# --------------------------------------------------------------------------
# Plate texture assets
# --------------------------------------------------------------------------
# Named HERE, in one place, because two modules must agree about them:
# `gen_textures.py` writes the files and `gen_catalog.py` publishes the keys.
#
# The plate art is LAYERED on purpose. The configurator lets the owner choose
# the plate's colour (soldermask colour on the FR4 path, filament/resin colour
# on the printed path), so no ground colour may be baked into a texture: the
# ground is the viewer's material tint at runtime.
#
#   openings map  ONE shared RGBA alpha map of the routed geometry -- white and
#                 opaque where the plate is material, fully transparent where
#                 the fab routes an opening. Shared across all three variants
#                 because their Edge.Cuts geometry is byte-for-byte identical
#                 (gen_textures.py gates that identity before sharing it).
#   decal         per-variant RGBA overlay, transparent except the ONE marker
#                 that variant carries over TP5.
TEXTURE_OPENINGS = "textures/plate_openings.png"
PLATE_MARKERS = {
    # marker ids describe what the ORDERED board carries over TP5; see
    # gen_textures.py for the per-variant provenance of each.
    "standard": ("exposed_pad", "textures/plate_decal_standard.png"),
    "tented_ring": ("silk_ring", "textures/plate_decal_tented_ring.png"),
    "blank": ("none", None),
}


@dataclass(frozen=True)
class ManifestEntry:
    """One row of a `release/MANIFEST.md` file table."""

    path: str  # relative to release/, e.g. "hardware/case/v2/stl/tray.stl"
    md5: str
    size: int
    section: str


# A manifest file row looks like:
#   | `hardware/case/v2/stl/x.stl` | `<md5>` | 12345 | provenance... |
# Retired rows are prefixed `*(retired)*` OUTSIDE the backticks and are not
# part of the bundle (see MANIFEST.md:35) -- they must never reach the catalog.
_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{32})`\s*\|\s*(\d+)\s*\|")
_RETIRED = re.compile(r"^\|\s*\*\(retired\)\*")
_SECTION = re.compile(r"^###\s+(.*?)\s*$")


def read_manifest(manifest_path: Path | None = None) -> dict[str, ManifestEntry]:
    """Parse `release/MANIFEST.md` into {release-relative path: ManifestEntry}.

    Raises GateError if the file does not parse as a file enumeration, so a
    manifest format change fails the build loudly instead of silently
    emitting an empty catalog.
    """
    path = manifest_path or (RELEASE / "MANIFEST.md")
    if not path.is_file():
        raise GateError(f"manifest not found: {path}")

    entries: dict[str, ManifestEntry] = {}
    section = ""
    retired: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m_sec = _SECTION.match(line)
        if m_sec:
            section = m_sec.group(1)
            continue
        if _RETIRED.match(line):
            m_r = re.search(r"`([^`]+\.[A-Za-z0-9]+)`", line)
            if m_r:
                retired.append(m_r.group(1))
            continue
        m = _ROW.match(line)
        if not m:
            continue
        rel, md5, size = m.group(1), m.group(2), int(m.group(3))
        if rel in entries:
            raise GateError(f"duplicate manifest row for {rel!r}")
        entries[rel] = ManifestEntry(rel, md5, size, section)

    if len(entries) < 100:
        raise GateError(
            f"{MANIFEST_REL} parsed as only {len(entries)} file rows -- it no "
            "longer enumerates the bundle in the expected "
            "`| `path` | `md5` | bytes | provenance |` table form. STOP: fix "
            "the parser against the real format before trusting the catalog."
        )
    for r in retired:
        if r in entries:
            raise GateError(f"retired entry {r!r} also parsed as live")
    return entries


def stated_file_count(manifest_path: Path | None = None) -> int | None:
    """The `## Stats: N files, ...` count the manifest declares about itself."""
    path = manifest_path or (RELEASE / "MANIFEST.md")
    m = re.search(r"^## Stats: (\d+) files", path.read_text(encoding="utf-8"), re.M)
    return int(m.group(1)) if m else None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def release_rel(path_under_release: str) -> str:
    """`hardware/x.stl` -> `release/hardware/x.stl` (repo-relative, POSIX)."""
    return f"release/{path_under_release}"


def repo_path(repo_relative: str) -> Path:
    return REPO_ROOT / repo_relative


def _is_path_value(s: str) -> bool:
    """True for a bare repo path, False for prose that merely mentions one.

    A repo path is a single whitespace-free token under `release/`. Provenance
    sentences quote paths inside prose ("per release/HOW-TO-ORDER.md §7, the
    parts list ..."), and those must not be mistaken for file references.
    """
    return s.startswith("release/") and not any(c.isspace() for c in s)


def iter_catalog_paths(node, _trail: tuple = ()):
    """Yield (json_pointer, value) for every string that names a repo path."""
    if isinstance(node, dict):
        for key, val in node.items():
            yield from iter_catalog_paths(val, _trail + (str(key),))
    elif isinstance(node, list):
        for i, val in enumerate(node):
            yield from iter_catalog_paths(val, _trail + (str(i),))
    elif isinstance(node, str) and _is_path_value(node):
        yield "/" + "/".join(_trail), node


def iter_mesh_refs(node, _trail: tuple = ()):
    """Yield (json_pointer, value) for every `meshes/...` reference."""
    if isinstance(node, dict):
        for key, val in node.items():
            yield from iter_mesh_refs(val, _trail + (str(key),))
    elif isinstance(node, list):
        for i, val in enumerate(node):
            yield from iter_mesh_refs(val, _trail + (str(i),))
    elif isinstance(node, str) and node.startswith("meshes/"):
        yield "/" + "/".join(_trail), node


def iter_texture_refs(node, _trail: tuple = ()):
    """Yield (json_pointer, value) for every `textures/...` reference.

    `None` is a legitimate value (the blank plate carries no decal), so a
    missing texture is expressed by the key being null rather than by pointing
    at a file that does not exist; nulls are simply not yielded.
    """
    if isinstance(node, dict):
        for key, val in node.items():
            yield from iter_texture_refs(val, _trail + (str(key),))
    elif isinstance(node, list):
        for i, val in enumerate(node):
            yield from iter_texture_refs(val, _trail + (str(i),))
    elif isinstance(node, str) and node.startswith("textures/"):
        yield "/" + "/".join(_trail), node


# --------------------------------------------------------------------------
# KiCad `.kicad_pcb` primitive reader
# --------------------------------------------------------------------------
# The three plate boards under `release/hardware/case/v2/fab/` are the ORDERED
# artifacts, so they are the PRIMARY source for anything the plate shows.
# Each board contains only gr_line / gr_arc / gr_circle / gr_text, so an exact
# regex reader is enough here and no KiCad install is needed at build time.
#
# Every reader below is paired with a COUNT GATE in read_pcb_shapes(): the
# number of shapes parsed must equal the number of `(layer "...")` tokens in
# the file. A KiCad format change that made a regex silently miss shapes would
# therefore fail the build instead of quietly shrinking the geometry.

_PCB_WIDTH = re.compile(r"\(width (-?[\d.]+)\)")
_PCB_LINE = re.compile(
    r'\(gr_line \(start (-?[\d.]+) (-?[\d.]+)\) \(end (-?[\d.]+) (-?[\d.]+)\)'
    r'(.*?)\(layer "([^"]+)"\)'
)
_PCB_ARC = re.compile(
    r'\(gr_arc \(start (-?[\d.]+) (-?[\d.]+)\) \(mid (-?[\d.]+) (-?[\d.]+)\) '
    r'\(end (-?[\d.]+) (-?[\d.]+)\)(.*?)\(layer "([^"]+)"\)'
)
_PCB_CIRCLE = re.compile(
    r'\(gr_circle \(center (-?[\d.]+) (-?[\d.]+)\) \(end (-?[\d.]+) (-?[\d.]+)\)'
    r'(.*?)\(fill (\w+)\) \(layer "([^"]+)"\)'
)
_PCB_TEXT = re.compile(r'\(gr_text "([^"]*)".*?\(layer "([^"]+)"\)')
_PCB_LAYER_TOKEN = re.compile(r'\(layer "[^"]+"\)')


def _pcb_width(blob: str) -> float:
    m = _PCB_WIDTH.search(blob)
    return float(m.group(1)) if m else 0.0


def read_pcb_shapes(path: Path) -> dict:
    """Parse one `.kicad_pcb` into {'lines','arcs','circles','texts'}.

    Circles carry `d` (diameter, from the KiCad start/end convention where the
    `end` point lies ON the circle), `fill` and `width`, which is what
    separates a routed Edge.Cuts hole (fill no) from a filled copper/mask disc
    (fill yes) and from a stroked silkscreen ring.
    """
    txt = Path(path).read_text(encoding="utf-8")
    out = {
        "lines": [
            {
                "p0": (float(m[1]), float(m[2])),
                "p1": (float(m[3]), float(m[4])),
                "width": _pcb_width(m[5]),
                "layer": m[6],
            }
            for m in _PCB_LINE.finditer(txt)
        ],
        "arcs": [
            {
                "p0": (float(m[1]), float(m[2])),
                "mid": (float(m[3]), float(m[4])),
                "p1": (float(m[5]), float(m[6])),
                "width": _pcb_width(m[7]),
                "layer": m[8],
            }
            for m in _PCB_ARC.finditer(txt)
        ],
        "circles": [
            {
                "c": (float(m[1]), float(m[2])),
                # KiCad stores a circle as centre + a point ON it. The radius
                # is therefore a distance, and the square root leaves binary
                # noise (Ø12 comes out 11.999999999999996). The file itself
                # only carries 4 decimals, so quantising at 6 removes the
                # noise without rounding away anything the board states.
                "d": round(
                    2.0
                    * (
                        (float(m[3]) - float(m[1])) ** 2
                        + (float(m[4]) - float(m[2])) ** 2
                    )
                    ** 0.5,
                    6,
                ),
                "width": _pcb_width(m[5]),
                "fill": m[6] == "yes",
                "layer": m[7],
            }
            for m in _PCB_CIRCLE.finditer(txt)
        ],
        "texts": [{"text": m[1], "layer": m[2]} for m in _PCB_TEXT.finditer(txt)],
    }
    parsed = sum(len(v) for v in out.values())
    tokens = len(_PCB_LAYER_TOKEN.findall(txt))
    if parsed != tokens:
        raise GateError(
            f"{path}: parsed {parsed} shapes but the file carries {tokens} "
            "`(layer \"...\")` tokens. The board no longer matches the reader "
            "in common.py -- fix the reader before trusting anything read out "
            "of this board; do NOT ship a silently truncated shape set."
        )
    if not parsed:
        raise GateError(f"{path}: no shapes parsed at all")
    return out


def read_named_zone_polygon(
    path: Path, *, name: str, net_name: str, layer: str
) -> list[tuple[float, float]]:
    """Read one named KiCad zone's design polygon from a shipped board.

    KiCad also stores one or more much larger ``filled_polygon`` blocks after
    the design polygon. This reader isolates each top-level ``(zone ...)``
    S-expression first, then reads only its first ``(polygon (pts ...))``.
    Missing or duplicate matches are a hard gate: silently selecting a
    different copper zone would publish a made-up touch area.
    """
    txt = Path(path).read_text(encoding="utf-8")

    def block_at(start: int) -> str:
        depth = 0
        quoted = False
        escaped = False
        for i in range(start, len(txt)):
            ch = txt[i]
            if quoted:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    quoted = False
                continue
            if ch == '"':
                quoted = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return txt[start:i + 1]
        raise GateError(f"{path}: unterminated KiCad zone at byte {start}")

    zones = []
    for m in re.finditer(r"(?m)^\t\(zone\s*$", txt):
        block = block_at(m.start() + 1)
        header = re.search(
            r'\(net_name "([^"]+)"\)\s+\(layer "([^"]+)"\)', block
        )
        if (
            f'(name "{name}")' in block
            and header is not None
            and (header[1], header[2]) == (net_name, layer)
        ):
            zones.append(block)
    if len(zones) != 1:
        raise GateError(
            f"{path}: expected exactly one zone named {name!r} on net "
            f"{net_name!r} / {layer}, found {len(zones)}"
        )

    polygon = re.search(
        r"\(polygon\s+\(pts\s+((?:\(xy\s+-?[\d.]+\s+-?[\d.]+\)\s*)+)\)\s*\)",
        zones[0],
    )
    if not polygon:
        raise GateError(f"{path}: zone {name!r} has no readable design polygon")
    points = [
        (float(m[1]), float(m[2]))
        for m in re.finditer(r"\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)", polygon[1])
    ]
    if len(points) < 3:
        raise GateError(
            f"{path}: zone {name!r} design polygon has only {len(points)} points"
        )
    return points


def pcb_layer_signature(shapes: dict, layer: str) -> tuple:
    """A canonical, hashable signature of one layer's geometry.

    Used to PROVE that two boards carry the identical geometry on a layer
    (which is what lets three plate variants share one openings map). UUIDs and
    emission order are excluded on purpose; only the numbers matter, quantised
    to 1e-4 mm, which is the precision the shipped plate boards carry.
    """

    def q(v: float) -> float:
        return round(float(v), 4) + 0.0

    rows = []
    for ln in shapes["lines"]:
        if ln["layer"] == layer:
            rows.append(("line", q(ln["p0"][0]), q(ln["p0"][1]),
                         q(ln["p1"][0]), q(ln["p1"][1]), q(ln["width"])))
    for a in shapes["arcs"]:
        if a["layer"] == layer:
            rows.append(("arc", q(a["p0"][0]), q(a["p0"][1]), q(a["mid"][0]),
                         q(a["mid"][1]), q(a["p1"][0]), q(a["p1"][1]), q(a["width"])))
    for c in shapes["circles"]:
        if c["layer"] == layer:
            rows.append(("circle", q(c["c"][0]), q(c["c"][1]), q(c["d"]),
                         q(c["width"]), c["fill"]))
    return tuple(sorted(rows, key=repr))


def round_floats(node, places: int = 6):
    """Round every float in a JSON-ish tree.

    Derived values carry binary-representation noise (INNER_H + 2*5.4 evaluates
    to 111.39999999999999, not 111.4). Rounding at emit time keeps the file
    readable AND keeps it byte-stable; 6 places is 1 nm, far below any
    manufacturing tolerance in this project.
    """
    if isinstance(node, dict):
        return {k: round_floats(v, places) for k, v in node.items()}
    if isinstance(node, list):
        return [round_floats(v, places) for v in node]
    if isinstance(node, float):
        r = round(node, places)
        return 0.0 if r == 0 else r
    return node


def write_json(path: Path, obj) -> None:
    """Deterministic JSON: fixed separators, UTF-8, trailing newline.

    Key order is the insertion order the generator chose (readable, stable);
    it is deterministic because the generators build dicts in fixed order.
    """
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")

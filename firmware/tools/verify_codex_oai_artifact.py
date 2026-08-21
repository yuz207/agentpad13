#!/usr/bin/env python3
"""Verify the generated AgentPad13 direct-OAI firmware artifact offline.

This tool accepts only regular local files, invokes the ARM inspection tools,
and writes a reproducible JSON manifest beneath ``firmware/evidence``.  It has
no USB, volume-discovery, or device-write code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "firmware" / "evidence"
TARGET = "loudest_micro:codex_oai"
EXPECTED_VID_PID = "303a:8360"
EXPECTED_USAGE = "ff00:0061"
EXPECTED_REPORT_ID = 6
EXPECTED_REPORT_BYTES = 64
REQUIRED_SYMBOLS = frozenset(
    {"raw_hid_receive", "codex_oai_notify", "codex_led_render", "encoder_update_user"}
)
REQUIRED_ACKS = ("rgbcfg_ack", "thstatus_ack", "device_status_ack")
DEFINED_SYMBOL_TYPES = frozenset("TtDdBbRrSsGgVvWw")


class VerificationError(RuntimeError):
    """The supplied artifact or emulator evidence does not meet the contract."""


def require_regular_file(path: Path, *, label: str) -> Path:
    """Return ``path`` only when it is an existing non-symlink regular file."""
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise VerificationError(f"{label} must be an existing regular file: {candidate}")
    return candidate


def _run_text(command: Sequence[str]) -> str:
    try:
        return subprocess.check_output(list(command), text=True, stderr=subprocess.STDOUT)
    except FileNotFoundError as exc:
        raise VerificationError(f"required inspection tool is unavailable: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise VerificationError(
            f"inspection command failed ({exc.returncode}): {' '.join(command)}\n{exc.output}"
        ) from exc


def sha256_and_size(path: Path) -> tuple[str, int]:
    """Calculate the digest and byte size without following a symlink."""
    artifact = require_regular_file(path, label="UF2")
    digest = hashlib.sha256()
    size = 0
    with artifact.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def elf_size(path: Path) -> dict[str, int]:
    """Inspect ELF text/data/bss through the pinned ARM-size compatible tool."""
    elf = require_regular_file(path, label="ELF")
    output = _run_text(("arm-none-eabi-size", "-B", str(elf)))
    rows = [row.split() for row in output.splitlines() if row.split()]
    for row in reversed(rows):
        if len(row) >= 4 and all(value.isdigit() for value in row[:4]):
            return {"text": int(row[0]), "data": int(row[1]), "bss": int(row[2])}
    raise VerificationError("arm-none-eabi-size output did not contain text/data/bss metrics")


def elf_symbols(path: Path) -> dict[str, str]:
    """Return defined and undefined ELF symbol names with their nm type letters."""
    elf = require_regular_file(path, label="ELF")
    output = _run_text(("arm-none-eabi-nm", str(elf)))
    symbols: dict[str, str] = {}
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 2:
            symbols[fields[-1]] = fields[-2]
    return symbols


def verify_symbols(symbols: Mapping[str, str] | Iterable[str]) -> None:
    """Require defined direct-OAI code/data symbols, never undefined imports."""
    available = dict(symbols) if isinstance(symbols, Mapping) else {name: "T" for name in symbols}
    for required in sorted(REQUIRED_SYMBOLS):
        if required not in available:
            raise VerificationError(f"required ELF symbol missing: {required}")
        if available[required] not in DEFINED_SYMBOL_TYPES:
            raise VerificationError(
                f"required ELF symbol is not defined code/data: {required} ({available[required]})"
            )


def verify_evidence(
    evidence: Mapping[str, Any], *, artifact_sha256: str, artifact_size: int
) -> None:
    """Require the exact enumeration, descriptor, protocol, key and LED proof."""
    if evidence.get("vid_pid") != EXPECTED_VID_PID:
        raise VerificationError(f"unexpected VID:PID; expected {EXPECTED_VID_PID}")
    if evidence.get("usage") != EXPECTED_USAGE:
        raise VerificationError(f"unexpected Raw HID usage; expected {EXPECTED_USAGE}")
    if evidence.get("report_id") != EXPECTED_REPORT_ID:
        raise VerificationError(f"unexpected report ID; expected {EXPECTED_REPORT_ID}")
    if evidence.get("report_bytes") != EXPECTED_REPORT_BYTES:
        raise VerificationError(f"unexpected report byte count; expected {EXPECTED_REPORT_BYTES}")
    for field in (
        "usb_enumerated", "keyboard_hid_enumerated", "oai_hid_enumerated",
        "descriptor_verified", *REQUIRED_ACKS, "ws2812_activity",
    ):
        if evidence.get(field) is not True:
            raise VerificationError(f"emulator evidence did not prove {field}")
    if evidence.get("uf2_sha256") != artifact_sha256:
        raise VerificationError("emulator evidence SHA-256 does not match the UF2")
    if evidence.get("uf2_size_bytes") != artifact_size:
        raise VerificationError("emulator evidence byte size does not match the UF2")
    if not isinstance(evidence.get("task_status_fragment_count"), int) or evidence["task_status_fragment_count"] < 2:
        raise VerificationError("emulator evidence did not prove fragmented task status")
    task_status = evidence.get("task_status")
    if not isinstance(task_status, Mapping) or not task_status.get("e") or not task_status.get("b"):
        raise VerificationError("emulator evidence did not prove visible task-driven RGB")
    if evidence.get("key_event") != {"k": "AG00", "act": 1}:
        raise VerificationError("emulator evidence did not prove the AG00 key event")


def verify(uf2: Path, elf: Path, evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe manifest payload after all offline checks pass."""
    digest, size = sha256_and_size(uf2)
    verify_evidence(evidence, artifact_sha256=digest, artifact_size=size)
    metrics = elf_size(elf)
    verify_symbols(elf_symbols(elf))
    return {
        "status": "pass",
        "target": TARGET,
        "vid_pid": EXPECTED_VID_PID,
        "usage": EXPECTED_USAGE,
        "report_id": EXPECTED_REPORT_ID,
        "report_bytes": EXPECTED_REPORT_BYTES,
        "sha256": digest,
        "size_bytes": size,
        "elf_size": metrics,
        "required_symbols": sorted(REQUIRED_SYMBOLS),
        "emulator_evidence": {
            "usb_enumerated": evidence["usb_enumerated"],
            "descriptor_verified": evidence["descriptor_verified"],
            "keyboard_hid_enumerated": evidence["keyboard_hid_enumerated"],
            "oai_hid_enumerated": evidence["oai_hid_enumerated"],
            "uf2_sha256": evidence["uf2_sha256"],
            "uf2_size_bytes": evidence["uf2_size_bytes"],
            "rgbcfg_ack": evidence["rgbcfg_ack"],
            "thstatus_ack": evidence["thstatus_ack"],
            "device_status_ack": evidence["device_status_ack"],
            "key_event": evidence["key_event"],
            "ws2812_activity": evidence["ws2812_activity"],
            "task_status_fragment_count": evidence["task_status_fragment_count"],
        },
    }


def _safe_manifest_destination(output: Path, evidence_root: Path) -> Path:
    """Ensure a manifest stays lexically and physically below evidence_root."""
    raw_output = Path(output)
    if ".." in raw_output.parts:
        raise VerificationError("manifest output path traversal is not permitted")
    root = Path(evidence_root).absolute()
    candidate = raw_output.absolute()
    if root.is_symlink() or not root.is_dir():
        raise VerificationError(f"firmware/evidence directory is unavailable or unsafe: {root}")
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"manifest output must be under firmware/evidence: {candidate}") from exc
    if candidate.is_symlink() or (candidate.exists() and not candidate.is_file()):
        raise VerificationError(f"manifest output must be a regular file path: {candidate}")
    current = candidate.parent
    while current != root.parent:
        if current.is_symlink():
            raise VerificationError(f"manifest output traverses a symlink: {current}")
        current = current.parent
    return candidate


def write_manifest(output: Path, manifest: Mapping[str, Any], *, evidence_root: Path = EVIDENCE_ROOT) -> None:
    """Atomically write a formatted manifest below the owned evidence directory."""
    destination = _safe_manifest_destination(output, evidence_root)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(manifest, temporary, sort_keys=True, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def load_evidence(path: Path) -> Mapping[str, Any]:
    """Load object-shaped JSON evidence from a regular file."""
    source = require_regular_file(path, label="emulator evidence")
    try:
        evidence = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"could not read emulator evidence JSON: {source}") from exc
    if not isinstance(evidence, dict):
        raise VerificationError("emulator evidence JSON must be an object")
    return evidence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uf2", required=True, type=Path)
    parser.add_argument("--elf", required=True, type=Path)
    parser.add_argument("--emulator-evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = verify(args.uf2, args.elf, load_evidence(args.emulator_evidence))
        write_manifest(args.output, manifest)
    except VerificationError as exc:
        print(f"artifact verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

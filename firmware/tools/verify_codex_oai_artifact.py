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
import struct
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
DEFINED_SYMBOL_TYPES = frozenset("TtDdBbRrSsGgVW")
UF2_BLOCK_SIZE = 512
UF2_DATA_OFFSET = 32
UF2_DATA_LIMIT = 508
UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_EXPECTED_FLAGS = 0x00002000
UF2_PAYLOAD_SIZE = 256
RP2040_FAMILY_ID = 0xE48BFF56
RP2040_FLASH_BASE = 0x10000000
RP2040_FLASH_LIMIT = 0x11000000


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


def file_sha256(path: Path, *, label: str) -> str:
    """Calculate a regular local file's SHA-256 digest."""
    source = require_regular_file(path, label=label)
    digest = hashlib.sha256()
    with source.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def uf2_flash_image(path: Path) -> bytes:
    """Return flash bytes from canonical QMK RP2040 UF2 blocks."""
    source = require_regular_file(path, label="UF2")
    contents = source.read_bytes()
    if not contents or len(contents) % UF2_BLOCK_SIZE:
        raise VerificationError("UF2 size must be a non-zero multiple of 512 bytes")

    actual_block_count = len(contents) // UF2_BLOCK_SIZE
    image = bytearray()
    seen_numbers: set[int] = set()
    seen_targets: set[int] = set()

    for index in range(actual_block_count):
        block = contents[index * UF2_BLOCK_SIZE : (index + 1) * UF2_BLOCK_SIZE]
        (
            magic0,
            magic1,
            flags,
            target,
            payload_size,
            block_number,
            declared_block_count,
            family_id,
        ) = struct.unpack_from("<IIIIIIII", block, 0)
        (end_magic,) = struct.unpack_from("<I", block, UF2_DATA_LIMIT)

        if (magic0, magic1, end_magic) != (
            UF2_MAGIC_START0,
            UF2_MAGIC_START1,
            UF2_MAGIC_END,
        ):
            raise VerificationError(f"UF2 block {index} has invalid magic")
        if flags != UF2_EXPECTED_FLAGS:
            raise VerificationError(
                f"UF2 block {index} flags must be 0x{UF2_EXPECTED_FLAGS:08x}; "
                f"found 0x{flags:08x}"
            )
        if family_id != RP2040_FAMILY_ID:
            raise VerificationError(
                f"UF2 block {index} family ID must be 0x{RP2040_FAMILY_ID:08x}; "
                f"found 0x{family_id:08x}"
            )
        if payload_size != UF2_PAYLOAD_SIZE:
            raise VerificationError(
                f"UF2 block {index} payload must be {UF2_PAYLOAD_SIZE} bytes; "
                f"found {payload_size}"
            )
        if declared_block_count != actual_block_count:
            raise VerificationError(
                f"UF2 block {index} declares {declared_block_count} blocks; found {actual_block_count}"
            )
        if block_number in seen_numbers:
            raise VerificationError(f"duplicate UF2 block number: {block_number}")
        seen_numbers.add(block_number)
        if block_number != index:
            raise VerificationError(
                f"UF2 block order is invalid: position {index} contains block {block_number}"
            )
        if target in seen_targets:
            raise VerificationError(f"duplicate UF2 target address: 0x{target:08x}")
        seen_targets.add(target)
        target_end = target + UF2_PAYLOAD_SIZE
        if target < RP2040_FLASH_BASE or target_end > RP2040_FLASH_LIMIT:
            raise VerificationError(
                f"UF2 block {index} target is outside RP2040 flash range: "
                f"0x{target:08x}..0x{target_end:08x}"
            )
        expected_target = RP2040_FLASH_BASE + block_number * UF2_PAYLOAD_SIZE
        if target != expected_target:
            raise VerificationError(
                f"UF2 block {index} target must be contiguous at 0x{expected_target:08x}; "
                f"found 0x{target:08x}"
            )
        image.extend(block[UF2_DATA_OFFSET : UF2_DATA_OFFSET + UF2_PAYLOAD_SIZE])

    return bytes(image)


def elf_binary(path: Path) -> bytes:
    """Convert a regular local ELF to its loadable binary image with objcopy."""
    elf = require_regular_file(path, label="ELF")
    with tempfile.TemporaryDirectory(prefix="agentpad13_elf_binary_") as temporary_dir:
        output = Path(temporary_dir) / "firmware.bin"
        command = ("arm-none-eabi-objcopy", "-O", "binary", str(elf), str(output))
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise VerificationError("required inspection tool is unavailable: arm-none-eabi-objcopy") from exc
        except subprocess.CalledProcessError as exc:
            raise VerificationError(
                f"inspection command failed ({exc.returncode}): {' '.join(command)}\n"
                f"{exc.stdout}{exc.stderr}"
            ) from exc
        binary = require_regular_file(output, label="ELF-derived binary").read_bytes()
    if not binary:
        raise VerificationError("ELF-derived binary is empty")
    return binary


def verify_elf_uf2_equivalence(uf2: Path, elf: Path) -> dict[str, Any]:
    """Require UF2 flash bytes to equal the ELF binary plus zero-only UF2 padding."""
    uf2_image = uf2_flash_image(uf2)
    binary = elf_binary(elf)
    expected_padding_size = (-len(binary)) % UF2_PAYLOAD_SIZE
    expected_image_size = len(binary) + expected_padding_size
    if len(uf2_image) != expected_image_size:
        raise VerificationError(
            "UF2 flash image length does not match canonical ELF padding: "
            f"expected {expected_image_size}; found {len(uf2_image)}"
        )
    if uf2_image[: len(binary)] != binary:
        raise VerificationError("ELF binary does not match UF2 flash image")
    padding = uf2_image[len(binary) :]
    if len(padding) != expected_padding_size:
        raise VerificationError("UF2 trailing zero padding length is not canonical")
    if any(padding):
        raise VerificationError("UF2 contains non-zero bytes beyond the ELF binary")
    return {
        "status": "pass",
        "flash_base": f"0x{RP2040_FLASH_BASE:08x}",
        "elf_binary_size_bytes": len(binary),
        "uf2_flash_size_bytes": len(uf2_image),
        "trailing_zero_padding_bytes": len(padding),
    }


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
    output = _run_text(("arm-none-eabi-nm", "--defined-only", str(elf)))
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
    equivalence = verify_elf_uf2_equivalence(uf2, elf)
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
        "elf_sha256": file_sha256(elf, label="ELF"),
        "elf_size": metrics,
        "elf_uf2_equivalence": equivalence,
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

#!/usr/bin/env python3
"""Stage and build the isolated AgentPad13 direct-OAI QMK keymap.

The script deliberately operates on a caller-provided, disposable QMK
worktree.  It proves the pinned Vial source and toolchain before linking the
AgentPad13 keyboard tree into that worktree, then removes only the link it
created.  Its only published artifact is the direct-OAI UF2 in this repo.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Sequence


PINNED_QMK_COMMIT = "00fc4627cd038ac9b7e9b8bf2b40b50e9e88aecb"
KEYBOARD_NAME = "loudest_micro"
KEYMAPS = ("default", "vial", "codex_oai")
REQUIRED_SUBMODULES = (
    "lib/chibios",
    "lib/chibios-contrib",
    "lib/lufa",
    "lib/pico-sdk",
    "lib/printf",
)
REPO_ROOT = Path(__file__).resolve().parents[2]
KEYBOARD_SOURCE = REPO_ROOT / "firmware" / KEYBOARD_NAME
OAI_ARTIFACT = REPO_ROOT / "release" / "firmware" / "prebuilt" / "agentpad13_codex_oai.uf2"
VIA_COMMAND_PATCH = REPO_ROOT / "firmware" / "patches" / "0001-via-command-kb-backport.patch"
OAI_DESCRIPTOR_PATCH = REPO_ROOT / "firmware" / "patches" / "0002-raw-hid-report-id-chibios.patch"
VIA_COMMAND_PATCH_SHA256 = "b12c375f7de6361fb2b26ecd003b0ffd717fb54d1441f37574866c86f473268c"
OAI_DESCRIPTOR_PATCH_SHA256 = "48eb5211383c8aa338e5b266b34cb3a90fc97cccc5586754f35d54a7bfdac002"
QMK_PATCHED_FILE_SHA256 = {
    "quantum/via.c": "48291b5dceb67de7daf7caad9db5399c69f463485203476ae4586814f3ad46f5",
    "quantum/via.h": "0a8ef108af7114bbc1da252f2017d7a9dc502750e6d75bd6506e1513ef226e7d",
}
QMK_DESCRIPTOR_BASE_SHA256 = {
    "tmk_core/protocol/usb_descriptor.c": "b5921e5311d40e50c5e4f88b133ba3b7cf10d4faa5cbd9c8da4ef4da7ba048aa",
    "tmk_core/protocol/usb_descriptor.h": "a75bb9a088e37ec51d88b8143c2cfce076dc02865c528be7591f15e566c2d477",
}
QMK_DESCRIPTOR_PATCHED_SHA256 = {
    "tmk_core/protocol/usb_descriptor.c": "09f655faea016c21e2318d1f34d1345b2e8424f64f064f1a92ef6be7118cf5e3",
    "tmk_core/protocol/usb_descriptor.h": "2e8dc4cd1edf372b6ffd1308a1e9e7c42bda07642c0d373a7b3e124103b9339e",
}
PINNED_GCC_VERSION = (
    "arm-none-eabi-gcc (Arm GNU Toolchain 15.2.Rel1 (Build arm-15.86)) "
    "15.2.1 20251203"
)


class BuildError(RuntimeError):
    """A precondition or build command did not meet the reproducibility contract."""


def _run(command: Sequence[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    """Run a checked child process without a shell."""
    try:
        subprocess.run(list(command), cwd=cwd, env=env, check=True)
    except FileNotFoundError as exc:
        raise BuildError(f"required command is unavailable: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        rendered = " ".join(command)
        raise BuildError(f"command failed ({exc.returncode}): {rendered}") from exc


def _git_head(qmk_home: Path) -> str:
    try:
        return subprocess.check_output(
            ("git", "-C", str(qmk_home), "rev-parse", "HEAD"), text=True
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise BuildError(f"QMK home is not a readable git worktree: {qmk_home}") from exc


def _file_sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise BuildError(f"required regular file is unavailable or unsafe: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_file_sha256(path: Path, expected: str, *, label: str) -> None:
    actual = _file_sha256(path)
    if actual != expected:
        raise BuildError(f"{label} content digest must be {expected}; found {actual}")


def validate_qmk_state(status: str, file_digests: Mapping[str, str]) -> str:
    """Accept only the exact repository-owned patch 0001 or 0001+0002 states."""
    patch1_paths = frozenset(QMK_PATCHED_FILE_SHA256)
    patch2_paths = frozenset(QMK_DESCRIPTOR_PATCHED_SHA256)
    actual_status = frozenset(line for line in status.splitlines() if line)
    patch1_status = frozenset(f" M {path}" for path in patch1_paths)
    patch12_status = patch1_status | frozenset(f" M {path}" for path in patch2_paths)
    if actual_status == patch1_status:
        expected_digests = QMK_PATCHED_FILE_SHA256 | QMK_DESCRIPTOR_BASE_SHA256
        state = "patch-0001"
    elif actual_status == patch12_status:
        expected_digests = QMK_PATCHED_FILE_SHA256 | QMK_DESCRIPTOR_PATCHED_SHA256
        state = "patch-0001+patch-0002"
    else:
        unexpected = ", ".join(sorted(actual_status ^ patch12_status)) or "unknown state"
        raise BuildError(f"unexpected QMK modification set: {unexpected}")

    for path, expected in expected_digests.items():
        actual = file_digests.get(path)
        if actual != expected:
            raise BuildError(
                f"QMK content digest mismatch for {path}: expected {expected}; found {actual}"
            )
    if set(file_digests) != set(expected_digests):
        raise BuildError("unexpected QMK content digest inventory")
    return state


def verify_qmk_source_state(qmk_home: Path) -> str:
    try:
        status = subprocess.check_output(
            (
                "git",
                "-C",
                str(qmk_home),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--ignore-submodules=none",
            ),
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise BuildError("could not read exact QMK worktree state") from exc
    paths = QMK_PATCHED_FILE_SHA256 | QMK_DESCRIPTOR_BASE_SHA256
    digests = {path: _file_sha256(qmk_home / path) for path in paths}
    return validate_qmk_state(status, digests)


def validate_qmk_home(qmk_home: Path, *, head: str | None = None) -> str:
    """Validate the exact Vial source and the required core backport."""
    qmk_home = qmk_home.resolve()
    if not qmk_home.is_dir():
        raise BuildError(f"QMK home does not exist: {qmk_home}")

    actual_head = head or _git_head(qmk_home)
    if actual_head != PINNED_QMK_COMMIT:
        raise BuildError(
            f"QMK home must be at exact QMK commit {PINNED_QMK_COMMIT}; found {actual_head}"
        )
    _verify_file_sha256(
        VIA_COMMAND_PATCH, VIA_COMMAND_PATCH_SHA256, label="repository patch 0001"
    )
    _verify_file_sha256(
        OAI_DESCRIPTOR_PATCH, OAI_DESCRIPTOR_PATCH_SHA256, label="repository patch 0002"
    )
    verify_qmk_source_state(qmk_home)

    missing = [path for path in REQUIRED_SUBMODULES if not (qmk_home / path).is_dir()]
    if missing:
        raise BuildError("required QMK submodules are unavailable: " + ", ".join(missing))

    try:
        status = subprocess.check_output(
            ("git", "-C", str(qmk_home), "submodule", "status", "--recursive"), text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise BuildError("could not read QMK submodule state") from exc
    uninitialised = [line for line in status.splitlines() if line.startswith(("-", "+", "U"))]
    if uninitialised:
        raise BuildError("QMK submodules are not at their recorded revisions")
    return actual_head


def _git_apply_check(qmk_home: Path, patch: Path, *, reverse: bool = False) -> bool:
    command = ["git", "-C", str(qmk_home), "apply", "--check"]
    if reverse:
        command.append("--reverse")
    command.append(str(patch))
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise BuildError("required command is unavailable: git") from exc
    return result.returncode == 0


def verify_oai_descriptor_support(qmk_home: Path) -> None:
    """Require Report-ID-aware Raw HID code in the pinned shared descriptor."""
    header = qmk_home / "tmk_core" / "protocol" / "usb_descriptor.h"
    source = qmk_home / "tmk_core" / "protocol" / "usb_descriptor.c"
    if not header.is_file() or not source.is_file():
        raise BuildError("QMK home is missing the shared USB descriptor sources")
    header_text = header.read_text(encoding="utf-8")
    source_text = source.read_text(encoding="utf-8")
    required_header = (
        "#ifndef RAW_EPSIZE",
        "#ifdef RAW_REPORT_ID",
        "#    define RAW_REPORT_PAYLOAD_SIZE (RAW_EPSIZE - 1)",
        "#    define RAW_REPORT_PAYLOAD_SIZE RAW_EPSIZE",
    )
    required_source = (
        "HID_RI_REPORT_ID(8, RAW_REPORT_ID)",
        "HID_RI_REPORT_COUNT(8, RAW_REPORT_PAYLOAD_SIZE)",
    )
    if not all(fragment in header_text for fragment in required_header) or not all(
        fragment in source_text for fragment in required_source
    ):
        raise BuildError("the required ChibiOS Raw HID Report-ID patch is not applied")


def apply_oai_descriptor_patch(qmk_home: Path, patch: Path = OAI_DESCRIPTOR_PATCH) -> None:
    """Apply the repository-owned descriptor patch, or verify it is already applied."""
    if patch.is_symlink() or not patch.is_file():
        raise BuildError(f"Raw HID descriptor patch is unavailable or unsafe: {patch}")
    _verify_file_sha256(
        patch, OAI_DESCRIPTOR_PATCH_SHA256, label="repository patch 0002"
    )
    if _git_apply_check(qmk_home, patch):
        _run(("git", "-C", str(qmk_home), "apply", str(patch)), cwd=qmk_home)
    elif not _git_apply_check(qmk_home, patch, reverse=True):
        raise BuildError("Raw HID descriptor patch does not apply cleanly to pinned QMK")
    verify_oai_descriptor_support(qmk_home)


def _same_target(link: Path, expected_target: Path) -> bool:
    """Compare a symlink's destination without ever following arbitrary paths."""
    return link.is_symlink() and link.resolve(strict=False) == expected_target.resolve()


def keyboard_link(qmk_home: Path, source: Path) -> Path:
    """Create the sole disposable keyboard symlink, rejecting existing paths."""
    source = source.resolve()
    if not source.is_dir():
        raise BuildError(f"AgentPad13 keyboard source does not exist: {source}")
    destination = qmk_home / "keyboards" / KEYBOARD_NAME
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() and not _same_target(destination, source):
            raise BuildError(f"foreign symlink at {destination}; refusing to replace it")
        raise BuildError(f"keyboard path already exists: {destination}")
    if not destination.parent.is_dir():
        raise BuildError(f"QMK home is missing keyboard directory: {destination.parent}")
    destination.symlink_to(source, target_is_directory=True)
    return destination


def cleanup_keyboard_link(link: Path, *, expected_target: Path) -> None:
    """Remove only the exact symlink made by :func:`keyboard_link`."""
    if not _same_target(link, expected_target):
        raise BuildError(f"refusing cleanup: {link} is not an owned symlink")
    link.unlink()


def find_cross_compiler() -> str:
    """Return a compiler that demonstrably includes both headers and newlib."""
    compiler = shutil.which("arm-none-eabi-gcc")
    if compiler is None:
        raise BuildError("arm-none-eabi-gcc is not on PATH")
    required_binutils = (
        "arm-none-eabi-ar",
        "arm-none-eabi-objcopy",
        "arm-none-eabi-size",
        "arm-none-eabi-nm",
    )
    binutils = {tool: shutil.which(tool) for tool in required_binutils}
    missing_binutils = [tool for tool, path in binutils.items() if path is None]
    if missing_binutils:
        raise BuildError(
            "cross toolchain is missing required binutils: " + ", ".join(missing_binutils)
        )
    compiler_path = Path(compiler).resolve()
    if any(Path(path).resolve().parent != compiler_path.parent for path in binutils.values()):
        raise BuildError("compiler and binutils must resolve from the same toolchain bin directory")
    try:
        version = subprocess.check_output((compiler, "--version"), text=True).splitlines()[0]
    except (subprocess.CalledProcessError, IndexError) as exc:
        raise BuildError("could not inspect arm-none-eabi-gcc version") from exc
    if version != PINNED_GCC_VERSION:
        raise BuildError(
            "arm-none-eabi-gcc must be Arm GNU Toolchain 15.2.Rel1 with gcc 15.2.1; "
            f"found {version}"
        )
    for probe in ("include/stdint.h", "libc.a"):
        try:
            value = subprocess.check_output((compiler, f"-print-file-name={probe}"), text=True).strip()
        except subprocess.CalledProcessError as exc:
            raise BuildError(f"could not inspect cross compiler for {probe}") from exc
        if not value or value == probe or not Path(value).is_file():
            raise BuildError(f"cross compiler is missing newlib component: {probe}")
    return str(compiler_path)


def _qmk_environment(qmk_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["QMK_HOME"] = str(qmk_home)
    return env


def run_lint(qmk_home: Path) -> None:
    """Run the QMK linter only for the isolated direct-OAI keymap."""
    _run(
        ("qmk", "lint", "-kb", KEYBOARD_NAME, "-km", "codex_oai", "--strict"),
        cwd=qmk_home,
        env=_qmk_environment(qmk_home),
    )
    print(f"lint {KEYBOARD_NAME}:codex_oai PASS")


def run_build(qmk_home: Path, keymap: str, *, clean: bool) -> Path:
    """Run a direct QMK make build and return the expected UF2 path."""
    if clean:
        _run(("make", "-f", "Makefile", "clean"), cwd=qmk_home, env=_qmk_environment(qmk_home))
    _run(
        ("make", "-f", "Makefile", f"{KEYBOARD_NAME}:{keymap}"),
        cwd=qmk_home,
        env=_qmk_environment(qmk_home),
    )
    artifact = qmk_home / f"{KEYBOARD_NAME}_{keymap}.uf2"
    if not artifact.is_file() or artifact.is_symlink():
        raise BuildError(f"expected regular build artifact was not produced: {artifact}")
    print(f"build {KEYBOARD_NAME}:{keymap} PASS")
    return artifact


def publish_oai_uf2(source: Path, destination: Path = OAI_ARTIFACT) -> None:
    """Atomically replace only the generated direct-OAI artifact."""
    if not source.is_file() or source.is_symlink():
        raise BuildError(f"refusing to publish a non-regular artifact: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            with source.open("rb") as input_file:
                shutil.copyfileobj(input_file, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def build_all(qmk_home: Path, *, clean: bool) -> None:
    """Validate, stage, lint, compile and publish without touching hardware."""
    validate_qmk_home(qmk_home)
    apply_oai_descriptor_patch(qmk_home)
    verify_qmk_source_state(qmk_home)
    find_cross_compiler()
    link = keyboard_link(qmk_home, KEYBOARD_SOURCE)
    try:
        run_lint(qmk_home)
        artifacts = {keymap: run_build(qmk_home, keymap, clean=clean) for keymap in KEYMAPS}
        publish_oai_uf2(artifacts["codex_oai"])
    finally:
        cleanup_keyboard_link(link, expected_target=KEYBOARD_SOURCE)
    print("flash operations 0")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qmk-home", required=True, type=Path, help="isolated pinned Vial QMK worktree")
    parser.add_argument("--clean", action="store_true", help="request clean object builds")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        build_all(args.qmk_home, clean=args.clean)
    except BuildError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

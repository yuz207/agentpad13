"""Safety contracts for the isolated AgentPad13 OAI build tool."""

from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
TOOLS = REPO / "firmware" / "tools"
sys.path.insert(0, str(TOOLS))

import build_codex_oai as builder  # noqa: E402
from build_codex_oai import (  # noqa: E402
    BuildError,
    apply_oai_descriptor_patch,
    cleanup_keyboard_link,
    find_cross_compiler,
    keyboard_link,
    publish_oai_uf2,
    run_build,
    validate_qmk_home,
    verify_oai_descriptor_support,
)


class BuildToolSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="agentpad13_build_tool_")
        self.root = Path(self._tmp.name)
        self.fake_qmk = self.root / "qmk"
        (self.fake_qmk / "keyboards").mkdir(parents=True)
        self.source = self.root / "loudest_micro"
        self.source.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_refuses_wrong_qmk_commit(self) -> None:
        with self.assertRaisesRegex(BuildError, "00fc4627"):
            validate_qmk_home(self.fake_qmk, head="deadbeef")

    def test_refuses_existing_real_keyboard_directory(self) -> None:
        (self.fake_qmk / "keyboards" / "loudest_micro").mkdir()
        with self.assertRaisesRegex(BuildError, "already exists"):
            keyboard_link(self.fake_qmk, self.source)

    def test_refuses_foreign_keyboard_symlink(self) -> None:
        foreign = self.root / "foreign_keyboard"
        foreign.mkdir()
        (self.fake_qmk / "keyboards" / "loudest_micro").symlink_to(foreign)
        with self.assertRaisesRegex(BuildError, "foreign symlink"):
            keyboard_link(self.fake_qmk, self.source)

    def test_cleanup_only_unlinks_owned_symlink(self) -> None:
        link = keyboard_link(self.fake_qmk, self.source)
        cleanup_keyboard_link(link, expected_target=self.source)
        self.assertFalse(link.exists())
        self.assertFalse(link.is_symlink())

    def test_cleanup_refuses_non_symlink(self) -> None:
        link = self.fake_qmk / "keyboards" / "loudest_micro"
        link.mkdir()
        with self.assertRaisesRegex(BuildError, "not an owned symlink"):
            cleanup_keyboard_link(link, expected_target=self.source)
        self.assertTrue(link.is_dir())

    def test_publish_replaces_only_oai_destination(self) -> None:
        source = self.root / "loudest_micro_codex_oai.uf2"
        source.write_bytes(b"oai-artifact")
        destination = self.root / "prebuilt" / "loudest_micro_codex_oai.uf2"
        default = self.root / "prebuilt" / "loudest_micro_default.uf2"
        vial = self.root / "prebuilt" / "loudest_micro_vial.uf2"
        default.parent.mkdir()
        default.write_bytes(b"default")
        vial.write_bytes(b"vial")

        publish_oai_uf2(source, destination)

        self.assertEqual(destination.read_bytes(), b"oai-artifact")
        self.assertEqual(default.read_bytes(), b"default")
        self.assertEqual(vial.read_bytes(), b"vial")

    def test_descriptor_patch_is_repository_owned_and_complete(self) -> None:
        patch = REPO / "firmware" / "patches" / "0002-raw-hid-report-id-chibios.patch"
        self.assertTrue(patch.is_file())
        text = patch.read_text(encoding="utf-8")
        for required in (
            "tmk_core/protocol/usb_descriptor.h",
            "tmk_core/protocol/usb_descriptor.c",
            "HID_RI_REPORT_ID(8, RAW_REPORT_ID)",
            "HID_RI_REPORT_COUNT(8, RAW_REPORT_PAYLOAD_SIZE)",
            "RAW_REPORT_PAYLOAD_SIZE (RAW_EPSIZE - 1)",
        ):
            self.assertIn(required, text)

    def test_descriptor_gate_rejects_unpatched_qmk(self) -> None:
        descriptor_dir = self.fake_qmk / "tmk_core" / "protocol"
        descriptor_dir.mkdir(parents=True)
        (descriptor_dir / "usb_descriptor.h").write_text("#define RAW_EPSIZE 32\n")
        (descriptor_dir / "usb_descriptor.c").write_text("RAW_EPSIZE\n")
        with self.assertRaisesRegex(BuildError, "Report-ID patch"):
            verify_oai_descriptor_support(self.fake_qmk)

    def test_builder_applies_then_verifies_descriptor_patch(self) -> None:
        descriptor_dir = self.fake_qmk / "tmk_core" / "protocol"
        descriptor_dir.mkdir(parents=True)
        header = descriptor_dir / "usb_descriptor.h"
        source = descriptor_dir / "usb_descriptor.c"
        header.write_text("unpatched\n")
        source.write_text("unpatched\n")

        def fake_apply(*_args, **_kwargs):
            header.write_text(
                "#ifndef RAW_EPSIZE\n#ifdef RAW_REPORT_ID\n"
                "#    define RAW_REPORT_PAYLOAD_SIZE (RAW_EPSIZE - 1)\n"
                "#    define RAW_REPORT_PAYLOAD_SIZE RAW_EPSIZE\n"
            )
            source.write_text(
                "HID_RI_REPORT_ID(8, RAW_REPORT_ID)\n"
                "HID_RI_REPORT_COUNT(8, RAW_REPORT_PAYLOAD_SIZE)\n"
            )

        with mock.patch.object(builder, "_git_apply_check", return_value=True), mock.patch.object(
            builder, "_run", side_effect=fake_apply
        ) as runner:
            apply_oai_descriptor_patch(self.fake_qmk)
        runner.assert_called_once()

    def test_repository_patch_really_applies_to_pinned_descriptor_shape(self) -> None:
        descriptor_dir = self.fake_qmk / "tmk_core" / "protocol"
        descriptor_dir.mkdir(parents=True)
        (descriptor_dir / "usb_descriptor.h").write_text(
            "#define KEYBOARD_EPSIZE 8\n"
            "#define SHARED_EPSIZE 32\n"
            "#define MOUSE_EPSIZE 16\n"
            "#define RAW_EPSIZE 32\n"
            "#define CONSOLE_EPSIZE 32\n"
            "#define MIDI_STREAM_EPSIZE 64\n"
            "#define CDC_NOTIFICATION_EPSIZE 8\n"
        )
        (descriptor_dir / "usb_descriptor.c").write_text(
            "#ifdef RAW_ENABLE\n"
            "const USB_Descriptor_HIDReport_Datatype_t PROGMEM RawReport[] = {\n"
            "    HID_RI_USAGE_PAGE(16, RAW_USAGE_PAGE), // Vendor Defined\n"
            "    HID_RI_USAGE(8, RAW_USAGE_ID),         // Vendor Defined\n"
            "    HID_RI_COLLECTION(8, 0x01),    // Application\n"
            "        // Data to host\n"
            "        HID_RI_USAGE(8, 0x62),     // Vendor Defined\n"
            "        HID_RI_LOGICAL_MINIMUM(8, 0x00),\n"
            "        HID_RI_LOGICAL_MAXIMUM(16, 0x00FF),\n"
            "        HID_RI_REPORT_COUNT(8, RAW_EPSIZE),\n"
            "        HID_RI_REPORT_SIZE(8, 0x08),\n"
            "        HID_RI_INPUT(8, HID_IOF_DATA | HID_IOF_VARIABLE | HID_IOF_ABSOLUTE),\n\n"
            "        // Data from host\n"
            "        HID_RI_USAGE(8, 0x63),     // Vendor Defined\n"
            "        HID_RI_LOGICAL_MINIMUM(8, 0x00),\n"
            "        HID_RI_LOGICAL_MAXIMUM(16, 0x00FF),\n"
            "        HID_RI_REPORT_COUNT(8, RAW_EPSIZE),\n"
            "        HID_RI_REPORT_SIZE(8, 0x08),\n"
            "        HID_RI_OUTPUT(8, HID_IOF_DATA | HID_IOF_VARIABLE | HID_IOF_ABSOLUTE | HID_IOF_NON_VOLATILE),\n"
            "    HID_RI_END_COLLECTION(0),\n"
            "};\n"
            "#endif\n"
        )
        subprocess.run(["git", "init", "-q", str(self.fake_qmk)], check=True)
        apply_oai_descriptor_patch(self.fake_qmk)
        verify_oai_descriptor_support(self.fake_qmk)

    def test_clean_runs_real_clean_target_before_build(self) -> None:
        artifact = self.fake_qmk / "loudest_micro_codex_oai.uf2"
        calls: list[tuple[str, ...]] = []

        def fake_run(command, **_kwargs):
            calls.append(tuple(command))
            if command[-1] == "loudest_micro:codex_oai":
                artifact.write_bytes(b"uf2")

        with mock.patch.object(builder, "_run", side_effect=fake_run):
            self.assertEqual(run_build(self.fake_qmk, "codex_oai", clean=True), artifact)
        self.assertEqual(
            calls,
            [
                ("make", "-f", "Makefile", "clean"),
                ("make", "-f", "Makefile", "loudest_micro:codex_oai"),
            ],
        )

    def test_compiler_preflight_rejects_missing_binutils(self) -> None:
        compiler = self.root / "bin" / "arm-none-eabi-gcc"
        include = self.root / "include" / "stdint.h"
        libc = self.root / "lib" / "libc.a"
        compiler.parent.mkdir()
        include.parent.mkdir()
        libc.parent.mkdir()
        compiler.touch()
        include.touch()
        libc.touch()

        def fake_which(name: str) -> str | None:
            if name == "arm-none-eabi-gcc":
                return str(compiler)
            return None

        with mock.patch.object(builder.shutil, "which", side_effect=fake_which), mock.patch.object(
            builder.subprocess, "check_output", side_effect=[str(include), str(libc)]
        ):
            with self.assertRaisesRegex(BuildError, "arm-none-eabi-ar"):
                find_cross_compiler()

    def test_tool_has_no_physical_operation_vocabulary(self) -> None:
        tool_text = (TOOLS / "build_codex_oai.py").read_text(encoding="utf-8")
        for forbidden in ("qmk" + " flash", "RPI" + "-RP2", "/Volumes/", "BOOT" + "SEL"):
            self.assertNotIn(forbidden, tool_text)


if __name__ == "__main__":
    unittest.main()

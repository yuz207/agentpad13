"""Host-only acceptance tests for the direct-OAI artifact verifier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPT = REPO / "firmware" / "tools" / "verify_codex_oai_artifact.py"

UF2_BLOCK_SIZE = 512
UF2_PAYLOAD_SIZE = 256
UF2_FLASH_BASE = 0x10000000


def make_uf2(image: bytes) -> bytes:
    if len(image) % UF2_PAYLOAD_SIZE:
        raise ValueError("test UF2 image must contain complete payload blocks")
    block_count = len(image) // UF2_PAYLOAD_SIZE
    output = bytearray()
    for block_number in range(block_count):
        block = bytearray(UF2_BLOCK_SIZE)
        payload = image[
            block_number * UF2_PAYLOAD_SIZE : (block_number + 1) * UF2_PAYLOAD_SIZE
        ]
        struct.pack_into(
            "<IIIIIIII",
            block,
            0,
            0x0A324655,
            0x9E5D5157,
            0x00002000,
            UF2_FLASH_BASE + block_number * UF2_PAYLOAD_SIZE,
            UF2_PAYLOAD_SIZE,
            block_number,
            block_count,
            0xE48BFF56,
        )
        block[32 : 32 + UF2_PAYLOAD_SIZE] = payload
        struct.pack_into("<I", block, 508, 0x0AB16F30)
        output.extend(block)
    return bytes(output)


def load_verifier():
    spec = importlib.util.spec_from_file_location("codex_oai_artifact_verifier", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load artifact verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArtifactVerifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.work = tempfile.TemporaryDirectory(prefix="agentpad13_artifact_test_")
        self.root = Path(self.work.name)
        self.elf_binary = bytes(range(256)) + b"agentpad13 direct oai fixture\n"
        self.uf2_image = self.elf_binary + bytes(
            (-len(self.elf_binary)) % UF2_PAYLOAD_SIZE
        )
        self.good_uf2 = self.root / "loudest_micro_codex_oai.uf2"
        self.good_uf2.write_bytes(make_uf2(self.uf2_image))
        self.good_elf = self.root / "loudest_micro_codex_oai.elf"
        self.good_elf.write_bytes(b"ELF fixture\n")
        uf2_bytes = self.good_uf2.read_bytes()
        self.good_evidence = {
            "usb_enumerated": True,
            "keyboard_hid_enumerated": True,
            "oai_hid_enumerated": True,
            "vid_pid": "303a:8360",
            "usage": "ff00:0061",
            "report_id": 6,
            "report_bytes": 64,
            "descriptor_verified": True,
            "rgbcfg_ack": True,
            "thstatus_ack": True,
            "device_status_ack": True,
            "key_event": {"k": "AG00", "act": 1},
            "ws2812_activity": True,
            "task_status": {"id": 0, "c": 3162110, "e": 4, "b": 1, "s": 0.5},
            "task_status_fragment_count": 2,
            "uf2_sha256": hashlib.sha256(uf2_bytes).hexdigest(),
            "uf2_size_bytes": len(uf2_bytes),
        }
        self.verifier = load_verifier()

    def tearDown(self) -> None:
        self.work.cleanup()

    def _tool_output(self, command, **_kwargs):
        if command[0].endswith("-size"):
            return "   text    data     bss     dec     hex filename\n   1000      20      30    1050     41a fixture.elf\n"
        if command[0].endswith("-nm"):
            return "00000000 T raw_hid_receive\n00000000 T codex_oai_notify\n00000000 T codex_led_render\n00000000 T encoder_update_user\n"
        raise AssertionError(f"unexpected tool command: {command}")

    def _verify(
        self,
        *,
        uf2: Path | None = None,
        elf: Path | None = None,
        evidence: dict | None = None,
        elf_binary: bytes | None = None,
    ):
        with mock.patch.object(
            self.verifier.subprocess, "check_output", side_effect=self._tool_output
        ), mock.patch.object(
            self.verifier,
            "elf_binary",
            return_value=self.elf_binary if elf_binary is None else elf_binary,
            create=True,
        ):
            return self.verifier.verify(
                uf2 or self.good_uf2,
                elf or self.good_elf,
                evidence or self.good_evidence,
            )

    def _evidence_for(self, uf2: Path) -> dict:
        data = uf2.read_bytes()
        return {
            **self.good_evidence,
            "uf2_sha256": hashlib.sha256(data).hexdigest(),
            "uf2_size_bytes": len(data),
        }

    def test_accepts_exact_descriptor_symbols_and_hash(self) -> None:
        result = self._verify()
        self.assertEqual(result["target"], "loudest_micro:codex_oai")
        self.assertEqual(result["vid_pid"], "303a:8360")
        self.assertEqual(result["report_id"], 6)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertEqual(result["size_bytes"], self.good_uf2.stat().st_size)
        self.assertEqual(result["elf_size"], {"text": 1000, "data": 20, "bss": 30})
        self.assertEqual(result["elf_sha256"], hashlib.sha256(self.good_elf.read_bytes()).hexdigest())
        self.assertEqual(
            result["elf_uf2_equivalence"],
            {
                "status": "pass",
                "flash_base": "0x10000000",
                "elf_binary_size_bytes": len(self.elf_binary),
                "uf2_flash_size_bytes": len(self.uf2_image),
                "trailing_zero_padding_bytes": len(self.uf2_image) - len(self.elf_binary),
            },
        )

    def test_rejects_unrelated_elf_even_when_symbols_and_emulator_evidence_pass(self) -> None:
        unrelated_elf = self.root / "unrelated.elf"
        unrelated_elf.write_bytes(b"unrelated ELF fixture\n")
        with self.assertRaisesRegex(self.verifier.VerificationError, "ELF binary does not match UF2"):
            self._verify(elf=unrelated_elf, elf_binary=b"unrelated flash image")

    def test_rejects_a_full_extra_zero_payload_beyond_the_elf(self) -> None:
        candidate = self.root / "extra-zero-block.uf2"
        candidate.write_bytes(make_uf2(self.uf2_image + bytes(UF2_PAYLOAD_SIZE)))
        with self.assertRaisesRegex(self.verifier.VerificationError, "padding"):
            self._verify(uf2=candidate, evidence=self._evidence_for(candidate))

    def test_rejects_uf2_with_bad_magic_or_payload_bounds(self) -> None:
        cases: list[tuple[str, bytearray, str]] = []
        bad_magic = bytearray(self.good_uf2.read_bytes())
        struct.pack_into("<I", bad_magic, 0, 0)
        cases.append(("magic", bad_magic, "magic"))
        oversized_payload = bytearray(self.good_uf2.read_bytes())
        struct.pack_into("<I", oversized_payload, 16, 477)
        cases.append(("payload", oversized_payload, "payload"))

        for name, contents, message in cases:
            with self.subTest(name=name):
                candidate = self.root / f"{name}.uf2"
                candidate.write_bytes(contents)
                with self.assertRaisesRegex(self.verifier.VerificationError, message):
                    self._verify(uf2=candidate, evidence=self._evidence_for(candidate))

    def test_rejects_uf2_target_outside_rp2040_flash(self) -> None:
        contents = bytearray(self.good_uf2.read_bytes())
        struct.pack_into("<I", contents, 12, UF2_FLASH_BASE - UF2_PAYLOAD_SIZE)
        candidate = self.root / "outside-flash.uf2"
        candidate.write_bytes(contents)
        with self.assertRaisesRegex(self.verifier.VerificationError, "flash range"):
            self._verify(uf2=candidate, evidence=self._evidence_for(candidate))

    def test_rejects_out_of_order_or_duplicate_uf2_blocks(self) -> None:
        original = self.good_uf2.read_bytes()
        out_of_order = original[UF2_BLOCK_SIZE:] + original[:UF2_BLOCK_SIZE]
        duplicate_target = bytearray(original)
        struct.pack_into("<I", duplicate_target, UF2_BLOCK_SIZE + 12, UF2_FLASH_BASE)
        duplicate_number = bytearray(original)
        struct.pack_into("<I", duplicate_number, UF2_BLOCK_SIZE + 20, 0)

        for name, contents, message in (
            ("out-of-order", out_of_order, "order"),
            ("duplicate-target", duplicate_target, "target"),
            ("duplicate-number", duplicate_number, "block number"),
        ):
            with self.subTest(name=name):
                candidate = self.root / f"{name}.uf2"
                candidate.write_bytes(contents)
                with self.assertRaisesRegex(self.verifier.VerificationError, message):
                    self._verify(uf2=candidate, evidence=self._evidence_for(candidate))

    def test_rejects_wrong_report_id(self) -> None:
        evidence = {**self.good_evidence, "report_id": 0}
        with self.assertRaisesRegex(self.verifier.VerificationError, "report ID"):
            self.verifier.verify(self.good_uf2, self.good_elf, evidence)

    def test_rejects_missing_oai_symbol(self) -> None:
        with self.assertRaisesRegex(self.verifier.VerificationError, "codex_oai_notify"):
            self.verifier.verify_symbols({"raw_hid_receive", "codex_led_render"})

    def test_rejects_required_symbol_that_is_only_undefined(self) -> None:
        symbols = {
            "raw_hid_receive": "T",
            "codex_oai_notify": "U",
            "codex_led_render": "T",
            "encoder_update_user": "T",
        }
        with self.assertRaisesRegex(self.verifier.VerificationError, "not defined code/data"):
            self.verifier.verify_symbols(symbols)

    def test_rejects_lowercase_undefined_weak_symbol_types(self) -> None:
        for weak_type in ("w", "v"):
            with self.subTest(weak_type=weak_type):
                symbols = {
                    "raw_hid_receive": "T",
                    "codex_oai_notify": weak_type,
                    "codex_led_render": "T",
                    "encoder_update_user": "T",
                }
                with self.assertRaisesRegex(
                    self.verifier.VerificationError, "not defined code/data"
                ):
                    self.verifier.verify_symbols(symbols)

    def test_nm_parser_does_not_turn_undefined_symbol_into_proof(self) -> None:
        output = (
            "00000000 T raw_hid_receive\n"
            "         U codex_oai_notify\n"
            "00000000 T codex_led_render\n"
            "00000000 T encoder_update_user\n"
        )
        with mock.patch.object(self.verifier.subprocess, "check_output", return_value=output):
            symbols = self.verifier.elf_symbols(self.good_elf)
        self.assertEqual(symbols["codex_oai_notify"], "U")
        with self.assertRaisesRegex(self.verifier.VerificationError, "codex_oai_notify"):
            self.verifier.verify_symbols(symbols)

    def test_nm_parser_keeps_defined_local_symbols_from_lto_builds(self) -> None:
        globals_only = (
            "10000000 T raw_hid_receive\n"
            "10000020 T codex_led_render\n"
            "10000040 T encoder_update_user\n"
        )

        def fake_nm(command):
            defined = globals_only + "10000060 t codex_oai_notify\n"
            if "--defined-only" in command:
                return defined
            return defined + "         w undefined_weak\n"

        with mock.patch.object(self.verifier, "_run_text", side_effect=fake_nm):
            symbols = self.verifier.elf_symbols(self.good_elf)
        self.assertIn("codex_oai_notify", symbols)
        self.assertNotIn("undefined_weak", symbols)
        self.verifier.verify_symbols(symbols)

    def test_rejects_evidence_from_different_uf2_hash_or_size(self) -> None:
        wrong_hash = {**self.good_evidence, "uf2_sha256": "0" * 64}
        with self.assertRaisesRegex(self.verifier.VerificationError, "SHA-256"):
            self.verifier.verify(self.good_uf2, self.good_elf, wrong_hash)
        wrong_size = {**self.good_evidence, "uf2_size_bytes": self.good_uf2.stat().st_size + 1}
        with self.assertRaisesRegex(self.verifier.VerificationError, "byte size"):
            self.verifier.verify(self.good_uf2, self.good_elf, wrong_size)

    def test_rejects_symlink_inputs(self) -> None:
        linked_uf2 = self.root / "linked.uf2"
        linked_uf2.symlink_to(self.good_uf2)
        with self.assertRaisesRegex(self.verifier.VerificationError, "regular file"):
            self.verifier.verify(linked_uf2, self.good_elf, self.good_evidence)

    def test_writes_manifest_atomically_only_in_evidence_directory(self) -> None:
        evidence_dir = self.root / "firmware" / "evidence"
        evidence_dir.mkdir(parents=True)
        output = evidence_dir / "codex-oai-manifest.json"
        result = self._verify()
        self.verifier.write_manifest(output, result, evidence_root=evidence_dir)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)
        self.assertFalse(any(path.name.startswith(".codex-oai-manifest.json.") for path in evidence_dir.iterdir()))
        with self.assertRaisesRegex(self.verifier.VerificationError, "firmware/evidence"):
            self.verifier.write_manifest(self.root / "outside.json", result, evidence_root=evidence_dir)

    def test_rejects_dotdot_output_without_creating_an_outside_file(self) -> None:
        evidence_dir = self.root / "firmware" / "evidence"
        evidence_dir.mkdir(parents=True)
        escaped = evidence_dir / ".." / "escaped.json"
        with self.assertRaisesRegex(self.verifier.VerificationError, "path traversal"):
            self.verifier.write_manifest(escaped, {"status": "pass"}, evidence_root=evidence_dir)
        self.assertFalse((self.root / "firmware" / "escaped.json").exists())

    def test_static_contract_has_no_device_or_volume_access(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("hidapi", "pyusb", "/Volumes/", "BOOTSEL", "qmk flash"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("import hid", source)


if __name__ == "__main__":
    unittest.main()

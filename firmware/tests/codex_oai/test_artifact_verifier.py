"""Host-only acceptance tests for the direct-OAI artifact verifier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPT = REPO / "firmware" / "tools" / "verify_codex_oai_artifact.py"


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
        self.good_uf2 = self.root / "loudest_micro_codex_oai.uf2"
        self.good_uf2.write_bytes(b"UF2\x00direct-oai\n")
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

    def test_accepts_exact_descriptor_symbols_and_hash(self) -> None:
        with mock.patch.object(self.verifier.subprocess, "check_output", side_effect=self._tool_output):
            result = self.verifier.verify(self.good_uf2, self.good_elf, self.good_evidence)
        self.assertEqual(result["target"], "loudest_micro:codex_oai")
        self.assertEqual(result["vid_pid"], "303a:8360")
        self.assertEqual(result["report_id"], 6)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertEqual(result["size_bytes"], self.good_uf2.stat().st_size)
        self.assertEqual(result["elf_size"], {"text": 1000, "data": 20, "bss": 30})

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
        with mock.patch.object(self.verifier.subprocess, "check_output", side_effect=self._tool_output):
            result = self.verifier.verify(self.good_uf2, self.good_elf, self.good_evidence)
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

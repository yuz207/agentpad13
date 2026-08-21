"""Pre-hardware contract for the AgentPad13 direct-OAI rp2040js smoke.

The test consumes only the generated OAI UF2 and its emulator JSON evidence;
it intentionally never discovers or opens a USB device.  Until Task 5 can
produce the isolated target UF2, this is a documented pre-hardware gate.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EMULATOR = REPO / "firmware" / "tests" / "emulator"
UF2 = REPO / "release" / "firmware" / "prebuilt" / "agentpad13_codex_oai.uf2"


def run_oai_emulator(uf2: Path) -> dict[str, object]:
    """Run the isolated emulator and return its recorded, JSON-safe evidence."""
    with tempfile.TemporaryDirectory(prefix="agentpad13_oai_emulator_") as directory:
        evidence_path = Path(directory) / "evidence.json"
        subprocess.run(
            ["node", "oai_runner.cjs", str(uf2), "--json", str(evidence_path)],
            cwd=EMULATOR,
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(evidence_path.read_text(encoding="utf-8"))


class OaiEmulatorContractTest(unittest.TestCase):
    def test_evidence_requires_oai_descriptor_and_handshake(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("pre-hardware emulator gate: node is unavailable")
        if not UF2.is_file():
            self.skipTest(
                "pre-hardware build gate: agentpad13_codex_oai.uf2 is not "
                "available; run firmware/tools/build_codex_oai.py first"
            )
        evidence = run_oai_emulator(UF2)
        self.assertTrue(evidence["usb_enumerated"])
        self.assertEqual(evidence["vid_pid"], "303a:8360")
        self.assertEqual(evidence["usage"], "ff00:0061")
        self.assertEqual(evidence["report_id"], 6)
        self.assertEqual(evidence["report_bytes"], 64)
        self.assertTrue(evidence["keyboard_hid_enumerated"])
        self.assertTrue(evidence["oai_hid_enumerated"])
        self.assertTrue(evidence["descriptor_verified"])
        self.assertTrue(evidence["rgbcfg_ack"])
        self.assertTrue(evidence["thstatus_ack"])
        self.assertTrue(evidence["device_status_ack"])
        self.assertEqual(evidence["key_event"], {"k": "AG00", "act": 1})
        self.assertGreater(evidence["task_status_fragment_count"], 1)
        self.assertEqual(evidence["task_status"]["e"], 4)
        self.assertEqual(evidence["task_status"]["b"], 1)
        self.assertTrue(evidence["ws2812_activity"])
        self.assertEqual(evidence["uf2_size_bytes"], UF2.stat().st_size)
        self.assertEqual(evidence["uf2_sha256"], hashlib.sha256(UF2.read_bytes()).hexdigest())

    def test_runner_has_exact_single_frame_wrapper_and_endpoint_contract(self) -> None:
        runner = (EMULATOR / "oai_runner.cjs").read_text(encoding="utf-8")
        for fragment in (
            "const payload = Buffer.from(json, 'utf8');",
            "if (payload.length > 61) throw new Error('single-frame fixture too large');",
            "const report = Buffer.alloc(64);",
            "report[0] = 6;",
            "report[1] = 2;",
            "report[2] = payload.length;",
            "payload.copy(report, 3);",
            "const OAI_USAGE_PAGE = 0xff00;",
            "const OAI_USAGE = 0x0061;",
            "wValue: 0x2200,",
            "wIndex: raw.number,",
            "function keyboardHid(interfaces)",
            "iface.sub === 1 && iface.proto === 1",
            "const reports = oaiReports(json);",
            "task_status_fragment_count: thstatusResult.fragmentCount",
            "uf2_size_bytes: uf2Data.length",
            "uf2_sha256: uf2Sha256",
            "mcu.gpio[12].setInputValue(false);",
            "edgesAfterStatus > edgesBeforeStatus",
        ):
            self.assertIn(fragment, runner)

    def test_fragmenter_and_keyboard_interface_detection_execute_on_host(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is unavailable")
        script = r'''
const runner = require('./oai_runner.cjs');
const json = '{"method":"v.oai.thstatus","id":2,"params":[{"id":0,"c":3162110,"e":4,"b":1,"s":0.5}]}';
const reports = runner.oaiReports(json);
const rebuilt = Buffer.concat(reports.map((report) => report.subarray(3, 3 + report[2]))).toString('utf8');
const keyboard = runner.keyboardHid([
  { number: 0, cls: 3, sub: 1, proto: 1, inEp: 1, inBytes: 8 },
  { number: 1, cls: 3, sub: 0, proto: 0, inEp: 2, inBytes: 64, outEp: 3, outBytes: 64 },
]);
if (reports.length < 2 || reports.some((report) => report.length !== 64 || report[0] !== 6) || rebuilt !== json || !keyboard || keyboard.number !== 0) process.exit(1);
'''
        subprocess.run(["node", "-e", script], cwd=EMULATOR, check=True)


if __name__ == "__main__":
    unittest.main()

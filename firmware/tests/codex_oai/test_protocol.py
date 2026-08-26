"""Byte-exact host conformance tests for the AgentPad13 OAI engine.

The tested C engine owns framing, readiness gating and its Raw HID replies;
the Python oracle supplies only the independently validated input fragments.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from firmware.tests.codex_oai import protocol_oracle


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEYMAP = REPO / "firmware" / "loudest_micro" / "keymaps" / "codex_oai"


def make_report(fragment: bytes, channel: int = 2) -> bytes:
    """Wrap a 63-byte CircuitPython payload in the QMK report-ID byte."""
    return bytes((6,)) + protocol_oracle.make_payload(channel, fragment)


def message_reports(message: bytes) -> tuple[bytes, ...]:
    """Turn the oracle's report-ID-less CP payloads into QMK reports."""
    return tuple(bytes((6,)) + payload for payload in protocol_oracle.fragment_message(message))


def oracle_feed(
    engine: protocol_oracle.Engine, reports: tuple[bytes, ...]
) -> tuple[bytes, ...]:
    """Feed the same complete QMK reports to the independent Python engine."""
    sent: list[bytes] = []
    for report in reports:
        for payload in engine.feed_payload(report[1:]):
            sent.append(bytes((6,)) + payload)
    return tuple(sent)


@dataclass(frozen=True)
class HarnessResult:
    sent: tuple[bytes, ...]
    ready: bool
    snapshot: "Snapshot"


@dataclass(frozen=True)
class SlotState:
    source_slot: int
    rgb: tuple[int, int, int]
    effect: int
    brightness: int
    speed: int
    flags: int


@dataclass(frozen=True)
class Snapshot:
    link: int
    revision: int
    error_revision: int
    handshake_revision: int
    slots: tuple[SlotState, ...]


class Harness:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="agentpad13_oai_")
        self._binary = Path(self._tmp.name) / "protocol_harness"
        subprocess.run(
            [
                "cc",
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-DRAW_EPSIZE=64",
                "-DRAW_REPORT_ID=6",
                "-DWEAR_LEVELING_ENABLE",
                "-I",
                str(HERE / "stubs"),
                "-I",
                str(KEYMAP),
                str(HERE / "protocol_harness.c"),
                str(KEYMAP / "codex_oai.c"),
                "-o",
                str(self._binary),
            ],
            check=True,
        )
        self._process = subprocess.Popen(
            [str(self._binary)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.reset()

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=5)
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        self._process.stdin.close()
        self._process.stdout.close()
        self._tmp.cleanup()

    def _command(self, command: str) -> HarnessResult:
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        self._process.stdin.write(command + "\n")
        self._process.stdin.flush()
        sent: list[bytes] = []
        ready = False
        link = 0
        revision = 0
        error_revision = 0
        handshake_revision = 0
        slots: list[SlotState] = []
        for line in self._process.stdout:
            line = line.rstrip("\n")
            if line == "---":
                return HarnessResult(
                    tuple(sent),
                    ready,
                    Snapshot(link, revision, error_revision, handshake_revision, tuple(slots)),
                )
            if line.startswith("SENT "):
                sent.append(bytes.fromhex(line[5:]))
            elif line.startswith("READY "):
                ready = line == "READY 1"
            elif line.startswith("LINK "):
                link = int(line[5:])
            elif line.startswith("REVISION "):
                revision = int(line[9:])
            elif line.startswith("ERROR_REVISION "):
                error_revision = int(line[15:])
            elif line.startswith("HANDSHAKE_REVISION "):
                handshake_revision = int(line[19:])
            elif line.startswith("SLOT "):
                fields = line.split()
                if len(fields) != 9:
                    raise AssertionError(f"invalid slot output: {line!r}")
                values = [int(field) for field in fields[1:]]
                slots.append(
                    SlotState(
                        values[0],
                        (values[1], values[2], values[3]),
                        values[4],
                        values[5],
                        values[6],
                        values[7],
                    )
                )
            else:
                raise AssertionError(f"unexpected harness output: {line!r}")
        raise AssertionError("protocol harness exited without a response")

    def reset(self) -> HarnessResult:
        return self._command("RESET")

    def corrupt_storage(self) -> HarnessResult:
        return self._command("CORRUPT")

    def seed_legacy_keymap(self) -> HarnessResult:
        return self._command("LEGACY")

    def seed_current_legacy_keymap(self) -> HarnessResult:
        return self._command("CURRENT_LEGACY")

    def seed_legacy_custom_keymap(self) -> HarnessResult:
        return self._command("LEGACY_CUSTOM")

    def feed(self, frames: tuple[bytes, ...]) -> HarnessResult:
        result = self.snapshot()
        for frame in frames:
            self.assert_report(frame)
            result = self._command(f"FRAME {frame.hex()}")
        return result

    def rpc(self, message: bytes) -> HarnessResult:
        return self.feed(message_reports(message))

    def thstatus(self, params: list[dict[str, object]]) -> HarnessResult:
        message = json.dumps(
            {"method": "v.oai.thstatus", "id": 1, "params": params},
            separators=(",", ":"),
        ).encode("ascii")
        return self.rpc(message)

    def keymap_get(self, layer: int = 0, request_id: int = 42) -> HarnessResult:
        message = json.dumps(
            {"method": "v.oai.keymap.get", "id": request_id, "params": {"l": layer}},
            separators=(",", ":"),
        ).encode("ascii")
        return self.rpc(message)

    def keymap_set(self, mapping: str, layer: int = 0, request_id: int = 42) -> HarnessResult:
        message = json.dumps(
            {
                "method": "v.oai.keymap.set",
                "id": request_id,
                "params": {"l": layer, "m": mapping},
            },
            separators=(",", ":"),
        ).encode("ascii")
        return self.rpc(message)

    def notify(self, control: str, pressed: bool) -> HarnessResult:
        return self._command(f"NOTIFY {control} {1 if pressed else 0}")

    def snapshot(self) -> HarnessResult:
        return self._command("SNAPSHOT")

    @staticmethod
    def assert_report(frame: bytes) -> None:
        if len(frame) != 64:
            raise AssertionError(f"expected 64-byte report, got {len(frame)}")


class ProtocolParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = Harness()

    def tearDown(self) -> None:
        self.harness.close()

    def test_handshake_is_byte_exact(self) -> None:
        frames = message_reports(b'{"method":"v.oai.rgbcfg","id":17,"params":{}}')
        result = self.harness.feed(frames)
        self.assertEqual(
            result.sent,
            (make_report(b'{"result":true,"id":17}\r\n'),),
        )

    def test_only_valid_rgbcfg_advances_handshake_revision(self) -> None:
        self.assertEqual(self.harness.snapshot().snapshot.handshake_revision, 0)
        self.harness.feed((bytes(64),))
        self.assertEqual(self.harness.snapshot().snapshot.handshake_revision, 0)
        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":17,"params":{}}')
        self.assertEqual(self.harness.snapshot().snapshot.handshake_revision, 1)
        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":18,"params":{}}')
        self.assertEqual(self.harness.snapshot().snapshot.handshake_revision, 2)

    def test_empty_thstatus_is_valid_handshake_noop(self) -> None:
        """A host may announce readiness before it has task rows to send."""
        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":1,"params":{}}')
        result = self.harness.rpc(
            b'{"method":"v.oai.thstatus","id":2,"params":[]}'
        )
        self.assertEqual(
            result.sent,
            (make_report(b'{"result":true,"id":2}\r\n'),),
        )
        self.assertTrue(result.ready)
        self.assertEqual(result.snapshot.link, 1)
        self.assertEqual(result.snapshot.revision, 0)

    def test_controls_are_silent_until_ready(self) -> None:
        self.assertEqual(self.harness.notify("AG00", True).sent, ())

    def test_only_allowlisted_methods_reply(self) -> None:
        result = self.harness.rpc(b'{"method":"unknown","id":5,"params":{}}')
        self.assertEqual(result.sent, ())

    def test_six_slots_remain_addressable(self) -> None:
        params = [
            {"id": index, "c": 0x102030 + index, "e": 1, "b": 1.0, "s": 0.5}
            for index in range(6)
        ]
        state = self.harness.thstatus(params).snapshot
        self.assertEqual([slot.source_slot for slot in state.slots], list(range(6)))

    def test_partial_update_preserves_unspecified_fields(self) -> None:
        self.harness.thstatus([{"id": 4, "c": 0x112233, "e": 4, "b": 1, "s": 0.25}])
        state = self.harness.thstatus([{"id": 4, "b": 0.5}]).snapshot
        self.assertEqual(state.slots[4].rgb, (0x11, 0x22, 0x33))
        self.assertEqual(state.slots[4].effect, 4)

    def test_malformed_frame_advances_error_revision(self) -> None:
        before = self.harness.snapshot().snapshot.error_revision
        after = self.harness.feed((bytes(64),)).snapshot
        self.assertNotEqual(after.error_revision, before)

    def test_link_tracks_latest_protocol_health(self) -> None:
        self.assertEqual(self.harness.snapshot().snapshot.link, 0)
        self.harness.feed((bytes(64),))
        self.assertEqual(self.harness.snapshot().snapshot.link, 2)
        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":3,"params":{}}')
        self.assertEqual(self.harness.snapshot().snapshot.link, 0)
        self.harness.thstatus([{"id": 0, "c": 0x010203, "e": 1, "b": 1, "s": 0.5}])
        self.assertEqual(self.harness.snapshot().snapshot.link, 1)

    def test_nonzero_padding_advances_error_revision(self) -> None:
        before = self.harness.snapshot().snapshot.error_revision
        frame = bytearray(make_report(b""))
        frame[-1] = 1
        after = self.harness.feed((bytes(frame),)).snapshot
        self.assertEqual(after.error_revision, (before + 1) & 0xFF)

    def test_invalid_thstatus_preserves_state_and_recovers_link(self) -> None:
        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":3,"params":{}}')
        before = self.harness.thstatus(
            [{"id": 2, "c": 0x102030, "e": 4, "b": 1, "s": 0.5}]
        ).snapshot
        self.assertEqual(before.link, 1)

        invalid = self.harness.thstatus(
            [{"id": 2, "b": 0.25}, {"id": 2, "b": 0.75}]
        )
        after = invalid.snapshot
        self.assertEqual(invalid.sent, ())
        self.assertEqual(after.error_revision, (before.error_revision + 1) & 0xFF)
        self.assertEqual(after.link, 2)
        self.assertEqual(after.revision, before.revision)
        self.assertEqual(after.slots, before.slots)

        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":4,"params":{}}')
        recovered = self.harness.thstatus(
            [{"id": 2, "b": 0.75}]
        ).snapshot
        self.assertEqual(recovered.link, 1)

    def test_keymap_get_returns_default_compact_map(self) -> None:
        result = self.harness.keymap_get()
        self.assertEqual(
            result.sent,
            (make_report(b'{"result":{"l":0,"m":"123456789abfcd1"},"id":42}\r\n'),),
        )
        self.assertLessEqual(result.sent[0][2], 61)

    def test_act11_press_and_release_are_byte_exact(self) -> None:
        self.harness.rpc(b'{"method":"v.oai.rgbcfg","id":1,"params":{}}')
        self.harness.rpc(b'{"method":"v.oai.thstatus","id":2,"params":[]}')
        pressed = self.harness.notify("ACT11", True)
        released = self.harness.notify("ACT11", False)
        self.assertEqual(
            pressed.sent,
            (make_report(b'{"method":"v.oai.hid","params":{"k":"ACT11","act":1}}\r\n'),),
        )
        self.assertEqual(
            released.sent,
            (make_report(b'{"method":"v.oai.hid","params":{"k":"ACT11","act":0}}\r\n'),),
        )

    def test_keymap_set_round_trips_and_rejects_nonzero_layer(self) -> None:
        mapping = "0123456789abcd0"
        accepted = self.harness.keymap_set(mapping)
        self.assertEqual(accepted.sent, (make_report(b'{"result":true,"id":42}\r\n'),))
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(
                b'{"result":{"l":0,"m":"0123456789abcd0"},"id":42}\r\n'
            ),),
        )

        rejected = self.harness.keymap_set(mapping, layer=1)
        self.assertEqual(rejected.sent, (make_report(b'{"error":"invalid_keymap","id":42}\r\n'),))
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(
                b'{"result":{"l":0,"m":"0123456789abcd0"},"id":42}\r\n'
            ),),
        )

    def test_keymap_set_accepts_microphone_action_digit(self) -> None:
        mapping = "0123456789abed1"
        accepted = self.harness.keymap_set(mapping)
        self.assertEqual(accepted.sent, (make_report(b'{"result":true,"id":42}\r\n'),))
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(
                b'{"result":{"l":0,"m":"0123456789abed1"},"id":42}\r\n'
            ),),
        )

    def test_keymap_set_accepts_act11_action_digit(self) -> None:
        mapping = "0123456789afcd0"
        accepted = self.harness.keymap_set(mapping)
        self.assertEqual(accepted.sent, (make_report(b'{"result":true,"id":42}\r\n'),))
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(
                b'{"result":{"l":0,"m":"0123456789afcd0"},"id":42}\r\n'
            ),),
        )

    def test_keymap_set_is_atomic_for_shape_digits_and_encoder_position(self) -> None:
        mapping = "0123456789abcd0"
        self.harness.keymap_set(mapping)
        for invalid in ("0123456789abcd", "0123456789abcd0e", "d123456789abc00"):
            with self.subTest(invalid=invalid):
                result = self.harness.keymap_set(invalid)
                self.assertEqual(
                    result.sent,
                    (make_report(b'{"error":"invalid_keymap","id":42}\r\n'),),
                )
                self.assertEqual(
                    self.harness.keymap_get().sent,
                    (make_report(
                        b'{"result":{"l":0,"m":"0123456789abcd0"},"id":42}\r\n'
                    ),),
                )

    def test_keymap_persists_across_firmware_reinitialization(self) -> None:
        mapping = "0123456789abcd0"
        self.harness.keymap_set(mapping)
        self.harness.reset()
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(
                b'{"result":{"l":0,"m":"0123456789abcd0"},"id":42}\r\n'
            ),),
        )

    def test_corrupt_persisted_keymap_recovers_factory_defaults(self) -> None:
        self.harness.keymap_set("0123456789abcd0")
        self.harness.corrupt_storage()
        self.harness.reset()
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(b'{"result":{"l":0,"m":"123456789abfcd1"},"id":42}\r\n'),),
        )

    def test_legacy_factory_map_migrates_to_official_act10_act11_act12_order(self) -> None:
        self.harness.seed_legacy_keymap()
        self.harness.reset()
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(b'{"result":{"l":0,"m":"123456789abfcd1"},"id":42}\r\n'),),
        )

    def test_current_old_factory_map_migrates_to_official_act10_act11_act12_order(self) -> None:
        self.harness.seed_current_legacy_keymap()
        self.harness.reset()
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(b'{"result":{"l":0,"m":"123456789abfcd1"},"id":42}\r\n'),),
        )

    def test_legacy_custom_map_survives_store_version_migration(self) -> None:
        self.harness.seed_legacy_custom_keymap()
        self.harness.reset()
        self.assertEqual(
            self.harness.keymap_get().sent,
            (make_report(b'{"result":{"l":0,"m":"0123456789abcd0"},"id":42}\r\n'),),
        )

    def test_shared_valid_corpus_has_true_c_python_report_and_readiness_parity(self) -> None:
        oracle = protocol_oracle.Engine()
        corpus = (
            b'{"method":"device.status","id":1,"params":{}}',
            b'{"method":"v.oai.rgbcfg","id":17,"params":{}}',
            b'{"method":"unknown","id":5,"params":{}}',
            b'{"method":"v.oai.thstatus","id":22,"params":[]}',
            b'{"method":"v.oai.thstatus","id":23,"params":[{"id":0,"c":66051,"e":1,"b":1,"s":0.5}]}',
            b'{"method":"device.status","id":998,"params":{"nested":{"ok":true}}}',
        )
        for message in corpus:
            with self.subTest(message=message):
                reports = message_reports(message)
                c_result = self.harness.feed(reports)
                python_sent = oracle_feed(oracle, reports)
                self.assertEqual(c_result.sent, python_sent)
                self.assertEqual(c_result.ready, oracle.ready)

        controls = tuple(
            (control, pressed, action)
            for control in (*protocol_oracle.AGENT_CONTROLS, *protocol_oracle.ACTION_CONTROLS, "ENC")
            for pressed, action in ((True, "press"), (False, "release"))
        ) + (
            ("ENC_CW", True, "rotate"),
            ("ENC_CC", True, "rotate"),
        )
        for control, pressed, action in controls:
            with self.subTest(control=control, action=action):
                c_result = self.harness.notify(control, pressed)
                python_sent = tuple(
                    bytes((6,)) + payload for payload in oracle.notify(control, action)
                )
                self.assertEqual(c_result.sent, python_sent)
                self.assertEqual(c_result.ready, oracle.ready)


if __name__ == "__main__":
    unittest.main()

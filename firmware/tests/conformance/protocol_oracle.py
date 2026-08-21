# SPDX-License-Identifier: MIT
"""agentpad13 Raw HID status protocol — v0 + v1 reference implementation.

This module is the single source of truth for the wire format. It has **no
hardware dependencies** and imports nothing outside the standard library, so
it can be reused verbatim by:

  * a future agentpad13 host application,
  * host-side round-trip tests run with no device attached, and
  * this repository's firmware conformance tests (the device side must
    serialise/parse identically to the functions below).

This dependency-free module is vendored with the public firmware so its
conformance suite runs from a clean checkout. It is byte-identical in behavior
to the host oracle used to build and validate the current UF2s.

Transport framing
------------------
Every frame produced here is **exactly 32 bytes** and carries **no HID report
ID**. QMK Raw HID reports are report-ID-less; the leading ``0x00`` report-ID
byte that ``hidapi`` requires on some platforms is a *transport* concern and is
added by the host transport layer, never here. Keeping the report ID out of
this module means these 32-byte frames are the exact bytes the firmware's
``raw_hid_receive(data, length)`` sees.

HID descriptor (must match the firmware / keyboard.json):
  * Vendor ID   : 0xFEED
  * Product ID  : 0x4C4D
  * Usage Page  : 0xFF60   (QMK Raw HID)
  * Usage       : 0x61     (QMK Raw HID)
  * Report size : 32 bytes

Command set (byte 0 = command id), host -> device
-------------------------------------------------
  0x01 SET_KEY   {index, r, g, b, effect}
  0x02 SET_LAYER {layer}
  0x03 CLEAR
  0x04 PING       {token}            -> device replies with a CAPS frame
  0x50 GET_JOYSTICK {token}          -> device replies with a JOYSTICK frame   (v1)
  0x51 SET_CALIBRATION {rest_x, rest_y, min_x, max_x, min_y, max_y}
                                     -> device replies {status}                (v1)
  0x52 RESET_CALIBRATION             -> device replies {0}                     (v1)

CAPS reply (device -> host), returned in response to PING
---------------------------------------------------------
  byte 0      : 0x04                 (echoes the PING command id)
  byte 1      : token                (echoes the PING token, for correlation)
  byte 2      : 0x4C 'L'             (magic)
  byte 3      : 0x44 'D'             (magic)
  byte 4      : protocol_version     (0x01 for v1)
  byte 5      : led_count            (addressable LEDs, e.g. 24)
  byte 6      : layer_count          (number of layers, e.g. 8)
  byte 7      : features             (Feature bitfield)
  byte 8..31  : reserved (0)

Protocol v1 — joystick calibration
----------------------------------
v1 adds 0x50-0x52 so the host can read the joystick ADC and store calibration on
the board; the v0 commands are unchanged byte-for-byte and v0 clients never send
0x50-0x52. The wire contract both this module and the firmware are written
against is ``docs/PROTOCOL-V1-CONTRACT.md``; every layout, rule and derived value
below cites the section it comes from. All multi-byte v1 fields are
little-endian uint16 in the firmware's 10-bit ADC domain (0..1023).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

__all__ = [
    "REPORT_SIZE",
    "VENDOR_ID",
    "PRODUCT_ID",
    "USAGE_PAGE",
    "USAGE",
    "PROTOCOL_VERSION",
    "MAGIC",
    "Command",
    "Effect",
    "Feature",
    "LED_PER_KEY_FIRST",
    "LED_PER_KEY_LAST",
    "LED_LAYER_INDICATOR",
    "LED_UNDERGLOW_FIRST",
    "LED_UNDERGLOW_LAST",
    "LED_COUNT",
    "ADC_MAX",
    "CAL_FIELDS",
    "CAL_MIN_HALF_SWING",
    "CAL_THRESHOLD_PERCENT",
    "CAL_PLACEHOLDER_REST",
    "CAL_PLACEHOLDER_MIN",
    "CAL_PLACEHOLDER_MAX",
    "CAL_PLACEHOLDER_THRESHOLD",
    "CAL_STATE_UNCALIBRATED",
    "CAL_STATE_CALIBRATED",
    "CAL_ACCEPTED",
    "CAL_REJECTED",
    "SetKey",
    "SetLayer",
    "Clear",
    "Ping",
    "Caps",
    "GetJoystick",
    "SetCalibration",
    "ResetCalibration",
    "Joystick",
    "CalibrationAck",
    "ProtocolError",
    "rgb_from_hex",
    "rgb_to_hex",
    "calibration_problems",
    "validate_calibration",
    "derive_thresholds",
    "build_set_key",
    "build_set_layer",
    "build_clear",
    "build_ping",
    "build_caps",
    "build_get_joystick",
    "build_joystick",
    "build_set_calibration",
    "build_set_calibration_reply",
    "build_reset_calibration",
    "build_reset_calibration_reply",
    "parse_command",
    "parse_caps",
    "parse_joystick",
    "parse_set_calibration_reply",
    "describe_frame",
]

# --- Transport-independent constants -------------------------------------------------

REPORT_SIZE = 32
VENDOR_ID = 0xFEED
PRODUCT_ID = 0x4C4D
USAGE_PAGE = 0xFF60
USAGE = 0x61
PROTOCOL_VERSION = 0x01
MAGIC = (0x4C, 0x44)  # 'L', 'D' — marks a genuine loudest CAPS/JOYSTICK reply

# LED chain map (from firmware/loudest_micro/keyboard.json rgb_matrix comment):
#   0-12  per-key SW1..SW13
#   13    layer indicator
#   14-23 underglow
# SET_KEY {index} addresses any LED in this chain.
LED_PER_KEY_FIRST = 0
LED_PER_KEY_LAST = 12
LED_LAYER_INDICATOR = 13
LED_UNDERGLOW_FIRST = 14
LED_UNDERGLOW_LAST = 23
LED_COUNT = 24

# --- Joystick calibration constants (protocol v1) ------------------------------------
# Every value here is quoted from docs/PROTOCOL-V1-CONTRACT.md; the firmware
# derives the same numbers from the same rules and the conformance suite asserts
# the two agree byte-for-byte.

# ADC domain. analogReadPin on RP2040 returns sample >> (12 - ADC_RESOLUTION)
# with ADC_RESOLUTION 10, so every axis value on the wire is 0..1023.
ADC_MAX = 1023

# The six stored calibration fields, in wire order (0x51 request bytes 1..12 and
# 0x50 reply bytes 9..20 use this same order).
CAL_FIELDS = ("rest_x", "rest_y", "min_x", "max_x", "min_y", "max_y")

# Contract §0x51 validation: the smallest credible half-swing, in ADC counts.
CAL_MIN_HALF_SWING = 100
# Contract "Derived values": threshold = 60% of the smaller half-swing, leaving
# 40% of the travel in reserve before the end-stop.
CAL_THRESHOLD_PERCENT = 60

# Contract "Uncalibrated fallback": what a board with no stored calibration
# reports and behaves as — byte-for-byte the shipped v0 behaviour.
CAL_PLACEHOLDER_REST = 512
CAL_PLACEHOLDER_MIN = 0
CAL_PLACEHOLDER_MAX = ADC_MAX
CAL_PLACEHOLDER_THRESHOLD = 300  # NOT derived from the placeholders (that would
                                 # give 306); the fallback threshold is fixed.

# 0x50 reply byte 8.
CAL_STATE_UNCALIBRATED = 0
CAL_STATE_CALIBRATED = 1

# 0x51 reply byte 1.
CAL_ACCEPTED = 0
CAL_REJECTED = 1


class Command(enum.IntEnum):
    """Byte 0 of every frame."""

    SET_KEY = 0x01
    SET_LAYER = 0x02
    CLEAR = 0x03
    PING = 0x04
    # v1. 0x50-0x52 sit outside every VIA range (VIA owns 0x01-0x13, 0xFE, 0xFF)
    # so the vial build claims them unconditionally — see the contract's
    # "Command IDs — why 0x50-0x52".
    GET_JOYSTICK = 0x50
    SET_CALIBRATION = 0x51
    RESET_CALIBRATION = 0x52


class Effect(enum.IntEnum):
    """LED effect for SET_KEY (byte 5)."""

    SOLID = 0x00
    PULSE = 0x01
    BLINK = 0x02

    @classmethod
    def from_name(cls, name: str) -> "Effect":
        try:
            return cls[name.strip().upper()]
        except KeyError as exc:
            valid = ", ".join(e.name.lower() for e in cls)
            raise ProtocolError(
                f"unknown effect {name!r}; valid effects: {valid}"
            ) from exc


class Feature(enum.IntFlag):
    """CAPS feature bitfield (byte 7)."""

    PER_KEY = 0x01
    UNDERGLOW = 0x02
    LAYER_INDICATOR = 0x04
    JOYSTICK = 0x08
    ENCODER = 0x10


class ProtocolError(ValueError):
    """Raised when a value is out of range or a frame is malformed."""


# --- Parsed-frame value objects ------------------------------------------------------


@dataclass(frozen=True)
class SetKey:
    index: int
    r: int
    g: int
    b: int
    effect: Effect = Effect.SOLID


@dataclass(frozen=True)
class SetLayer:
    layer: int


@dataclass(frozen=True)
class Clear:
    pass


@dataclass(frozen=True)
class Ping:
    token: int = 0


@dataclass(frozen=True)
class Caps:
    token: int
    protocol_version: int
    led_count: int
    layer_count: int
    features: Feature = field(default=Feature(0))


@dataclass(frozen=True)
class GetJoystick:
    token: int = 0


@dataclass(frozen=True)
class SetCalibration:
    rest_x: int
    rest_y: int
    min_x: int
    max_x: int
    min_y: int
    max_y: int

    def as_tuple(self) -> tuple[int, int, int, int, int, int]:
        """The six fields in wire order — the argument order of the builders."""
        return (self.rest_x, self.rest_y, self.min_x, self.max_x, self.min_y, self.max_y)


@dataclass(frozen=True)
class ResetCalibration:
    pass


@dataclass(frozen=True)
class Joystick:
    """A parsed 0x50 reply: live axes plus the calibration in force."""

    token: int
    live_x: int
    live_y: int
    cal_state: int
    rest_x: int
    rest_y: int
    min_x: int
    max_x: int
    min_y: int
    max_y: int
    threshold_x: int
    threshold_y: int

    @property
    def calibrated(self) -> bool:
        return self.cal_state == CAL_STATE_CALIBRATED

    def as_tuple(self) -> tuple[int, int, int, int, int, int]:
        """The six stored fields in wire order, for comparison against a send."""
        return (self.rest_x, self.rest_y, self.min_x, self.max_x, self.min_y, self.max_y)


@dataclass(frozen=True)
class CalibrationAck:
    """A parsed 0x51 reply. ``status`` is CAL_ACCEPTED or CAL_REJECTED."""

    status: int

    @property
    def accepted(self) -> bool:
        return self.status == CAL_ACCEPTED


# --- Validation helpers --------------------------------------------------------------


def _u8(name: str, value: int) -> int:
    """Validate that *value* fits in an unsigned byte, returning it."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProtocolError(f"{name} must be an int, got {type(value).__name__}")
    if not 0 <= value <= 0xFF:
        raise ProtocolError(f"{name} must be 0..255, got {value}")
    return value


def _pad(payload: bytes) -> bytes:
    """Right-pad *payload* with zeros to exactly REPORT_SIZE bytes."""
    if len(payload) > REPORT_SIZE:
        raise ProtocolError(
            f"payload is {len(payload)} bytes, exceeds {REPORT_SIZE}-byte report"
        )
    return payload + bytes(REPORT_SIZE - len(payload))


def _check_frame(frame: bytes) -> bytes:
    if not isinstance(frame, (bytes, bytearray)):
        raise ProtocolError(f"frame must be bytes, got {type(frame).__name__}")
    if len(frame) != REPORT_SIZE:
        raise ProtocolError(
            f"frame must be exactly {REPORT_SIZE} bytes, got {len(frame)}"
        )
    return bytes(frame)


def _int(name: str, value: int) -> int:
    """Reject non-ints (and bools, which are ints) before any range check."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProtocolError(f"{name} must be an int, got {type(value).__name__}")
    return value


def _adc(name: str, value: int) -> int:
    """Validate a 10-bit ADC value — the domain of every v1 axis field."""
    _int(name, value)
    if not 0 <= value <= ADC_MAX:
        raise ProtocolError(
            f"{name} must be 0..{ADC_MAX} (the firmware's 10-bit ADC domain), got {value}"
        )
    return value


def _le16(name: str, value: int) -> bytes:
    """Little-endian encode one validated uint16 — every multi-byte v1 field."""
    _int(name, value)
    if not 0 <= value <= 0xFFFF:
        raise ProtocolError(f"{name} must be 0..65535, got {value}")
    return value.to_bytes(2, "little")


def _read_le16(frame: bytes, offset: int) -> int:
    """Decode the little-endian uint16 at *offset* of an already-checked frame."""
    return int.from_bytes(frame[offset:offset + 2], "little")


# --- Colour helpers ------------------------------------------------------------------


def rgb_from_hex(value: str) -> tuple[int, int, int]:
    """Parse ``"22c55e"``, ``"#22c55e"`` or shorthand ``"2c5"`` -> (r, g, b)."""
    if not isinstance(value, str):
        raise ProtocolError(f"colour must be a string, got {type(value).__name__}")
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        raise ProtocolError(
            f"colour {value!r} must be 3 or 6 hex digits (e.g. '22c55e')"
        )
    try:
        r = int(text[0:2], 16)
        g = int(text[2:4], 16)
        b = int(text[4:6], 16)
    except ValueError as exc:
        raise ProtocolError(f"colour {value!r} is not valid hex") from exc
    return r, g, b


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Inverse of :func:`rgb_from_hex`; returns lower-case ``rrggbb``."""
    return f"{_u8('r', r):02x}{_u8('g', g):02x}{_u8('b', b):02x}"


# --- Calibration rules (one definition, shared by the CLI and the device) ------------


def calibration_problems(
    rest_x: int, rest_y: int, min_x: int, max_x: int, min_y: int, max_y: int
) -> list[str]:
    """Return every contract-§0x51 rule this calibration breaks; ``[]`` == valid.

    This is *the* definition of "valid calibration" on the host side: the CLI
    calls it to explain to the user what is wrong before anything is sent, and
    :func:`build_set_calibration` calls it (via :func:`validate_calibration`) so
    an invalid set can never reach the wire. The device applies the identical
    three rules and answers 0x51 with CAL_REJECTED when any of them fails; the
    conformance suite asserts the two agree, boundary case by boundary case.

    Rules, verbatim from the contract:
      * every value <= 1023
      * ``min_x < rest_x < max_x`` and ``min_y < rest_y < max_y``
      * ``rest_x - min_x >= 100``, ``max_x - rest_x >= 100``, same for y

    A broken ordering rule always implies a broken half-swing rule on the same
    axis (the swing would be <= 0), so only the ordering failure is reported for
    that axis — the root cause, not its consequence.
    """
    values = dict(zip(CAL_FIELDS, (rest_x, rest_y, min_x, max_x, min_y, max_y)))
    problems: list[str] = []
    for name, value in values.items():
        _int(name, value)
        if not 0 <= value <= ADC_MAX:
            problems.append(
                f"{name}={value} is outside the 10-bit ADC range 0..{ADC_MAX}"
            )
    if problems:
        # Ordering/swing arithmetic on out-of-range values would only add noise.
        return problems

    for axis, (low, rest, high) in (
        ("x", (min_x, rest_x, max_x)),
        ("y", (min_y, rest_y, max_y)),
    ):
        if not low < rest < high:
            problems.append(
                f"{axis} axis is not ordered min < rest < max "
                f"(min_{axis}={low}, rest_{axis}={rest}, max_{axis}={high})"
            )
            continue
        for side, swing in (("below", rest - low), ("above", high - rest)):
            if swing < CAL_MIN_HALF_SWING:
                problems.append(
                    f"{axis} axis only swings {swing} counts {side} rest; "
                    f"the minimum credible half-swing is {CAL_MIN_HALF_SWING}"
                )
    return problems


def validate_calibration(
    rest_x: int, rest_y: int, min_x: int, max_x: int, min_y: int, max_y: int
) -> None:
    """Raise :class:`ProtocolError` naming every broken rule, or return None."""
    problems = calibration_problems(rest_x, rest_y, min_x, max_x, min_y, max_y)
    if problems:
        raise ProtocolError(
            "invalid calibration (docs/PROTOCOL-V1-CONTRACT.md §0x51): "
            + "; ".join(problems)
        )


def _derive_axis_threshold(low: int, rest: int, high: int) -> int:
    """One axis of the contract's derived threshold.

    ``threshold = 60% of min(rest - low, high - rest)``.

    NOTE ON ROUNDING: the contract states the 60% rule but not how to round a
    non-integral result, and both sides must produce the same byte. This uses
    truncation (``half * 60 // 100``), which is what the plain C expression
    ``half * 60 / 100`` on uint16 arithmetic yields on the device. Flagged to
    the contract owner for an explicit sentence; do not change one side alone.
    """
    return min(rest - low, high - rest) * CAL_THRESHOLD_PERCENT // 100


def derive_thresholds(
    rest_x: int, rest_y: int, min_x: int, max_x: int, min_y: int, max_y: int
) -> tuple[int, int]:
    """Return ``(threshold_x, threshold_y)`` exactly as the device derives them."""
    validate_calibration(rest_x, rest_y, min_x, max_x, min_y, max_y)
    return (
        _derive_axis_threshold(min_x, rest_x, max_x),
        _derive_axis_threshold(min_y, rest_y, max_y),
    )


# --- Builders (host -> device) -------------------------------------------------------


def build_set_key(index: int, r: int, g: int, b: int, effect: Effect | int = Effect.SOLID) -> bytes:
    """Build a SET_KEY frame lighting LED *index* to (r, g, b) with *effect*."""
    effect_val = _u8("effect", int(effect))
    if effect_val not in {e.value for e in Effect}:
        valid = ", ".join(f"{e.name.lower()}={e.value}" for e in Effect)
        raise ProtocolError(f"effect {effect_val} is not a known effect ({valid})")
    payload = bytes(
        (
            Command.SET_KEY.value,
            _u8("index", index),
            _u8("r", r),
            _u8("g", g),
            _u8("b", b),
            effect_val,
        )
    )
    return _pad(payload)


def build_set_layer(layer: int) -> bytes:
    """Build a SET_LAYER frame selecting *layer*."""
    return _pad(bytes((Command.SET_LAYER.value, _u8("layer", layer))))


def build_clear() -> bytes:
    """Build a CLEAR frame (turn every status LED off)."""
    return _pad(bytes((Command.CLEAR.value,)))


def build_ping(token: int = 0) -> bytes:
    """Build a PING frame. *token* is echoed back in the CAPS reply."""
    return _pad(bytes((Command.PING.value, _u8("token", token))))


def build_caps(
    token: int = 0,
    protocol_version: int = PROTOCOL_VERSION,
    led_count: int = LED_COUNT,
    layer_count: int = 8,
    features: Feature | int = (
        Feature.PER_KEY | Feature.UNDERGLOW | Feature.LAYER_INDICATOR
    ),
) -> bytes:
    """Build a CAPS reply (device -> host).

    Lives here (rather than in the firmware only) so MockTransport can answer a
    PING and so firmware conformance tests can assert byte-for-byte equality.
    """
    payload = bytes(
        (
            Command.PING.value,
            _u8("token", token),
            MAGIC[0],
            MAGIC[1],
            _u8("protocol_version", protocol_version),
            _u8("led_count", led_count),
            _u8("layer_count", layer_count),
            _u8("features", int(features)),
        )
    )
    return _pad(payload)


# --- Builders, protocol v1 (joystick calibration) ------------------------------------


def build_get_joystick(token: int = 0) -> bytes:
    """Build a GET_JOYSTICK frame. *token* is echoed in the JOYSTICK reply."""
    return _pad(bytes((Command.GET_JOYSTICK.value, _u8("token", token))))


def build_joystick(
    token: int = 0,
    live_x: int = CAL_PLACEHOLDER_REST,
    live_y: int = CAL_PLACEHOLDER_REST,
    cal_state: int = CAL_STATE_UNCALIBRATED,
    rest_x: int = CAL_PLACEHOLDER_REST,
    rest_y: int = CAL_PLACEHOLDER_REST,
    min_x: int = CAL_PLACEHOLDER_MIN,
    max_x: int = CAL_PLACEHOLDER_MAX,
    min_y: int = CAL_PLACEHOLDER_MIN,
    max_y: int = CAL_PLACEHOLDER_MAX,
) -> bytes:
    """Build a JOYSTICK reply (device -> host), the answer to GET_JOYSTICK.

    Lives here for the same reason :func:`build_caps` does: MockTransport answers
    ``--mock`` runs with it and the firmware conformance suite asserts the device
    produces these exact bytes. The two threshold fields are always DERIVED here
    rather than passed in, because the contract gives them a single definition
    and a device that computed them differently is the bug this catches.

    ``cal_state=CAL_STATE_UNCALIBRATED`` means the placeholders are in force, so
    the stored fields must be the placeholders and the thresholds are the fixed
    fallback 300 — *not* a derived value (deriving from the placeholders would
    give 306 and would silently change the shipped uncalibrated behaviour).
    """
    state = _u8("cal_state", cal_state)
    if state not in (CAL_STATE_UNCALIBRATED, CAL_STATE_CALIBRATED):
        raise ProtocolError(
            f"cal_state must be {CAL_STATE_UNCALIBRATED} (uncalibrated) or "
            f"{CAL_STATE_CALIBRATED} (calibrated), got {state}"
        )
    stored = (rest_x, rest_y, min_x, max_x, min_y, max_y)
    if state == CAL_STATE_UNCALIBRATED:
        placeholders = (
            CAL_PLACEHOLDER_REST, CAL_PLACEHOLDER_REST,
            CAL_PLACEHOLDER_MIN, CAL_PLACEHOLDER_MAX,
            CAL_PLACEHOLDER_MIN, CAL_PLACEHOLDER_MAX,
        )
        if stored != placeholders:
            raise ProtocolError(
                "cal_state=0 means the placeholders are in force, so the stored "
                f"fields must be {placeholders}, got {stored}"
            )
        threshold_x = threshold_y = CAL_PLACEHOLDER_THRESHOLD
    else:
        threshold_x, threshold_y = derive_thresholds(*stored)

    payload = (
        bytes((Command.GET_JOYSTICK.value, _u8("token", token), MAGIC[0], MAGIC[1]))
        + _le16("live_x", _adc("live_x", live_x))
        + _le16("live_y", _adc("live_y", live_y))
        + bytes((state,))
        + b"".join(_le16(name, _adc(name, value)) for name, value in zip(CAL_FIELDS, stored))
        + _le16("threshold_x", threshold_x)
        + _le16("threshold_y", threshold_y)
    )
    return _pad(payload)


def build_set_calibration(
    rest_x: int, rest_y: int, min_x: int, max_x: int, min_y: int, max_y: int
) -> bytes:
    """Build a SET_CALIBRATION frame, validating the contract's rules FIRST.

    An invalid set raises :class:`ProtocolError` naming the broken rule and no
    frame is produced, so a rejected calibration never reaches the wire.
    """
    validate_calibration(rest_x, rest_y, min_x, max_x, min_y, max_y)
    stored = (rest_x, rest_y, min_x, max_x, min_y, max_y)
    payload = bytes((Command.SET_CALIBRATION.value,)) + b"".join(
        _le16(name, value) for name, value in zip(CAL_FIELDS, stored)
    )
    return _pad(payload)


def build_set_calibration_reply(status: int = CAL_ACCEPTED) -> bytes:
    """Build the device's SET_CALIBRATION reply: accepted (0) or rejected (1)."""
    value = _u8("status", status)
    if value not in (CAL_ACCEPTED, CAL_REJECTED):
        raise ProtocolError(
            f"status must be {CAL_ACCEPTED} (accepted) or {CAL_REJECTED} (rejected), "
            f"got {value}"
        )
    return _pad(bytes((Command.SET_CALIBRATION.value, value)))


def build_reset_calibration() -> bytes:
    """Build a RESET_CALIBRATION frame (wipe, revert to the placeholders)."""
    return _pad(bytes((Command.RESET_CALIBRATION.value,)))


def build_reset_calibration_reply() -> bytes:
    """Build the device's RESET_CALIBRATION reply — always ``[0x52, 0x00, ...]``."""
    return _pad(bytes((Command.RESET_CALIBRATION.value, 0x00)))


# --- Parsers -------------------------------------------------------------------------


def parse_command(
    frame: bytes,
) -> SetKey | SetLayer | Clear | Ping | GetJoystick | SetCalibration | ResetCalibration:
    """Parse a host->device frame back into its value object.

    This is the exact deserialisation the firmware must implement; the pytest
    round-trip tests pin ``parse_command(build_x(...)) == x`` for every command.

    SET_CALIBRATION is decoded as it appears on the wire, *without* applying the
    §0x51 rules: this is the device's-eye view of a frame it has received, and
    deciding whether to accept it is the next step (see
    :func:`calibration_problems`), not part of decoding it.
    """
    data = _check_frame(frame)
    cmd = data[0]
    if cmd == Command.SET_KEY:
        return SetKey(
            index=data[1],
            r=data[2],
            g=data[3],
            b=data[4],
            effect=Effect(data[5]) if data[5] in {e.value for e in Effect} else Effect.SOLID,
        )
    if cmd == Command.SET_LAYER:
        return SetLayer(layer=data[1])
    if cmd == Command.CLEAR:
        return Clear()
    if cmd == Command.PING:
        return Ping(token=data[1])
    if cmd == Command.GET_JOYSTICK:
        return GetJoystick(token=data[1])
    if cmd == Command.SET_CALIBRATION:
        return SetCalibration(
            rest_x=_read_le16(data, 1),
            rest_y=_read_le16(data, 3),
            min_x=_read_le16(data, 5),
            max_x=_read_le16(data, 7),
            min_y=_read_le16(data, 9),
            max_y=_read_le16(data, 11),
        )
    if cmd == Command.RESET_CALIBRATION:
        return ResetCalibration()
    raise ProtocolError(f"unknown command id 0x{cmd:02x}")


def parse_caps(frame: bytes) -> Caps:
    """Parse a device->host CAPS reply. Verifies the magic bytes."""
    data = _check_frame(frame)
    if data[0] != Command.PING:
        raise ProtocolError(
            f"CAPS reply must start with 0x{Command.PING.value:02x}, got 0x{data[0]:02x}"
        )
    if (data[2], data[3]) != MAGIC:
        raise ProtocolError(
            "CAPS reply magic mismatch: "
            f"expected {MAGIC[0]:#04x},{MAGIC[1]:#04x}, "
            f"got {data[2]:#04x},{data[3]:#04x} (not a loudest device?)"
        )
    return Caps(
        token=data[1],
        protocol_version=data[4],
        led_count=data[5],
        layer_count=data[6],
        features=Feature(data[7]),
    )


def parse_joystick(frame: bytes) -> Joystick:
    """Parse a device->host JOYSTICK reply (0x50). Verifies the magic bytes."""
    data = _check_frame(frame)
    if data[0] != Command.GET_JOYSTICK:
        raise ProtocolError(
            f"JOYSTICK reply must start with 0x{Command.GET_JOYSTICK.value:02x}, "
            f"got 0x{data[0]:02x}"
        )
    if (data[2], data[3]) != MAGIC:
        raise ProtocolError(
            "JOYSTICK reply magic mismatch: "
            f"expected {MAGIC[0]:#04x},{MAGIC[1]:#04x}, "
            f"got {data[2]:#04x},{data[3]:#04x} (not a loudest device?)"
        )
    if data[8] not in (CAL_STATE_UNCALIBRATED, CAL_STATE_CALIBRATED):
        raise ProtocolError(
            f"JOYSTICK reply cal_state must be {CAL_STATE_UNCALIBRATED} or "
            f"{CAL_STATE_CALIBRATED}, got {data[8]}"
        )
    return Joystick(
        token=data[1],
        live_x=_read_le16(data, 4),
        live_y=_read_le16(data, 6),
        cal_state=data[8],
        rest_x=_read_le16(data, 9),
        rest_y=_read_le16(data, 11),
        min_x=_read_le16(data, 13),
        max_x=_read_le16(data, 15),
        min_y=_read_le16(data, 17),
        max_y=_read_le16(data, 19),
        threshold_x=_read_le16(data, 21),
        threshold_y=_read_le16(data, 23),
    )


def parse_set_calibration_reply(frame: bytes) -> CalibrationAck:
    """Parse a device->host SET_CALIBRATION reply (0x51).

    Strict about the status byte: the contract defines exactly 0 (accepted and
    written) and 1 (rejected, nothing written), so any other value is a device
    bug we surface rather than guess at.
    """
    data = _check_frame(frame)
    if data[0] != Command.SET_CALIBRATION:
        raise ProtocolError(
            f"SET_CALIBRATION reply must start with "
            f"0x{Command.SET_CALIBRATION.value:02x}, got 0x{data[0]:02x}"
        )
    if data[1] not in (CAL_ACCEPTED, CAL_REJECTED):
        raise ProtocolError(
            f"SET_CALIBRATION reply status must be {CAL_ACCEPTED} (accepted) or "
            f"{CAL_REJECTED} (rejected), got {data[1]}"
        )
    return CalibrationAck(status=data[1])


def describe_frame(frame: bytes) -> str:
    """Human-readable one-liner for logging and ``--mock`` output."""
    try:
        cmd = parse_command(frame)
    except ProtocolError as exc:
        return f"<invalid frame: {exc}>"
    if isinstance(cmd, SetKey):
        return (
            f"SET_KEY   index={cmd.index} rgb=#{rgb_to_hex(cmd.r, cmd.g, cmd.b)} "
            f"effect={cmd.effect.name.lower()}"
        )
    if isinstance(cmd, SetLayer):
        return f"SET_LAYER layer={cmd.layer}"
    if isinstance(cmd, Clear):
        return "CLEAR"
    if isinstance(cmd, Ping):
        return f"PING      token=0x{cmd.token:02x}"
    if isinstance(cmd, GetJoystick):
        return f"GET_JOYSTICK      token=0x{cmd.token:02x}"
    if isinstance(cmd, SetCalibration):
        return (
            "SET_CALIBRATION   "
            f"rest=({cmd.rest_x},{cmd.rest_y}) "
            f"x=[{cmd.min_x}..{cmd.max_x}] y=[{cmd.min_y}..{cmd.max_y}]"
        )
    if isinstance(cmd, ResetCalibration):
        return "RESET_CALIBRATION"
    return "<unknown>"  # pragma: no cover - parse_command already raised

"""Pure OAI protocol engine shared by CPython tests and CircuitPython."""

REPORT_ID = 6
HID_PAYLOAD_SIZE = 63
FRAME_DATA_SIZE = 61
CHANNEL_DEBUG = 1
CHANNEL_RPC = 2

AGENT_CONTROLS = ("AG00", "AG01", "AG02", "AG03", "AG04", "AG05")
ACTION_CONTROLS = (
    "ACT06",
    "ACT07",
    "ACT08",
    "ACT09",
    "ACT10",
    "ACT11",
    "ACT12",
)
ENCODER_CONTROLS = ("ENC", "ENC_CW", "ENC_CC")


def make_payload(channel, fragment):
    if channel not in (CHANNEL_DEBUG, CHANNEL_RPC):
        raise ValueError("unsupported OAI channel")
    if not isinstance(fragment, (bytes, bytearray, memoryview)):
        raise ValueError("OAI fragment must be bytes")
    fragment = bytes(fragment)
    if len(fragment) > FRAME_DATA_SIZE:
        raise ValueError("OAI fragment exceeds 61 bytes")
    return (
        bytes((channel, len(fragment)))
        + fragment
        + bytes(FRAME_DATA_SIZE - len(fragment))
    )


def fragment_message(message, channel=CHANNEL_RPC):
    if not isinstance(message, (bytes, bytearray, memoryview)):
        raise ValueError("OAI message must be bytes")
    message = bytes(message)
    if not message:
        return (make_payload(channel, b""),)
    return tuple(
        make_payload(channel, message[offset : offset + FRAME_DATA_SIZE])
        for offset in range(0, len(message), FRAME_DATA_SIZE)
    )


def validate_control_action(control, action):
    if control in AGENT_CONTROLS:
        if action == "press":
            return 1
        if action == "release":
            return None
    elif control in ACTION_CONTROLS or control == "ENC":
        if action == "press":
            return 1
        if action == "release":
            return 0
    elif control in ("ENC_CW", "ENC_CC") and action == "rotate":
        return 2
    raise ValueError("unsupported OAI control/action pair")


def _is_space(value):
    return value in " \t\r\n"


def _skip_space(text, offset):
    while offset < len(text) and _is_space(text[offset]):
        offset += 1
    return offset


def _parse_plain_string(text, offset):
    if offset >= len(text) or text[offset] != '"':
        return None, offset
    offset += 1
    start = offset
    while offset < len(text) and text[offset] != '"':
        value = ord(text[offset])
        if value < 0x20 or value > 0x7E or text[offset] == "\\":
            return None, offset
        offset += 1
    if offset >= len(text):
        return None, offset
    return text[start:offset], offset + 1


def _skip_string(text, offset):
    if offset >= len(text) or text[offset] != '"':
        return None
    offset += 1
    escaped = False
    while offset < len(text):
        value = text[offset]
        offset += 1
        if escaped:
            escaped = False
        elif value == "\\":
            escaped = True
        elif value == '"':
            return offset
        elif ord(value) < 0x20:
            return None
    return None


def _matching(open_value, close_value):
    return (open_value == "{" and close_value == "}") or (
        open_value == "[" and close_value == "]"
    )


def _skip_compound(text, offset):
    if offset >= len(text) or text[offset] not in "{[":
        return None
    stack = [text[offset]]
    offset += 1
    while offset < len(text) and stack:
        value = text[offset]
        if value == '"':
            offset = _skip_string(text, offset)
            if offset is None:
                return None
            continue
        offset += 1
        if value in "{[":
            if len(stack) >= Engine.MAX_DEPTH:
                return None
            stack.append(value)
        elif value in "}]":
            if not _matching(stack[-1], value):
                return None
            stack.pop()
    return offset if not stack else None


def _skip_value(text, offset):
    offset = _skip_space(text, offset)
    if offset >= len(text):
        return None
    if text[offset] == '"':
        return _skip_string(text, offset)
    if text[offset] in "{[":
        return _skip_compound(text, offset)
    start = offset
    while offset < len(text) and text[offset] not in ",}":
        offset += 1
    end = offset
    while end > start and _is_space(text[end - 1]):
        end -= 1
    return offset if end > start else None


def _parse_id(text, offset):
    offset = _skip_space(text, offset)
    start = offset
    value = 0
    while offset < len(text) and "0" <= text[offset] <= "9":
        value = value * 10 + ord(text[offset]) - ord("0")
        offset += 1
        if offset - start > 3 or value > 998:
            return None, offset
    if offset == start:
        return None, offset
    return value, offset


def _parse_request(text):
    method = None
    request_id = None
    has_params = False
    offset = _skip_space(text, 0)
    if offset >= len(text) or text[offset] != "{":
        return None
    offset += 1
    while True:
        offset = _skip_space(text, offset)
        if offset < len(text) and text[offset] == "}":
            offset += 1
            break
        key, offset = _parse_plain_string(text, offset)
        if key is None:
            return None
        offset = _skip_space(text, offset)
        if offset >= len(text) or text[offset] != ":":
            return None
        offset = _skip_space(text, offset + 1)
        if key == "method":
            if method is not None:
                return None
            method, offset = _parse_plain_string(text, offset)
            if method is None:
                return None
        elif key == "id":
            if request_id is not None:
                return None
            request_id, offset = _parse_id(text, offset)
            if request_id is None:
                return None
        else:
            if key == "params":
                if has_params:
                    return None
                has_params = True
            offset = _skip_value(text, offset)
            if offset is None:
                return None
        offset = _skip_space(text, offset)
        if offset < len(text) and text[offset] == ",":
            offset += 1
            continue
        if offset < len(text) and text[offset] == "}":
            offset += 1
            break
        return None
    offset = _skip_space(text, offset)
    if (
        offset != len(text)
        or method is None
        or request_id is None
        or not has_params
    ):
        return None
    return method, request_id


class Engine:
    RX_CAPACITY = 768
    MAX_DEPTH = 8

    def __init__(self):
        self._saw_rgbcfg = False
        self._saw_thstatus = False
        self._rx_frames = 0
        self._tx_frames = 0
        self._discarded_objects = 0
        self._invalid_frames = 0
        self._incomplete_timeouts = 0
        self._reset_rpc_debug()
        self.reset_collector()

    @property
    def ready(self):
        return self._saw_rgbcfg and self._saw_thstatus

    @property
    def collecting(self):
        return self._collecting

    def reset_session(self):
        self._saw_rgbcfg = False
        self._saw_thstatus = False
        self._reset_rpc_debug()
        self.reset_collector()

    def _reset_rpc_debug(self):
        self._rpc_counts = {
            "v.oai.rgbcfg": 0,
            "v.oai.thstatus": 0,
            "device.status": 0,
        }
        self._unanswered_count = 0
        self._last_rpc_method = None
        self._last_rpc_id = None
        self._last_rpc_response = None

    def reset_collector(self):
        self._rx = bytearray()
        self._stack = []
        self._depth = 0
        self._collecting = False
        self._in_string = False
        self._escaped = False
        self._invalid = False
        self._overflowed = False

    def note_incomplete_timeout(self):
        self._incomplete_timeouts = min(
            self._incomplete_timeouts + 1, 0xFFFF
        )

    def snapshot(self):
        return {
            "ready": self.ready,
            "saw_rgbcfg": self._saw_rgbcfg,
            "saw_thstatus": self._saw_thstatus,
            "collecting": self._collecting,
            "rx_frames": self._rx_frames,
            "tx_frames": self._tx_frames,
            "discarded_objects": self._discarded_objects,
            "invalid_frames": self._invalid_frames,
            "incomplete_timeouts": self._incomplete_timeouts,
            "rpc_debug": {
                "rgbcfg_count": self._rpc_counts["v.oai.rgbcfg"],
                "thstatus_count": self._rpc_counts["v.oai.thstatus"],
                "device_status_count": self._rpc_counts["device.status"],
                "unanswered_count": self._unanswered_count,
                "last_method": self._last_rpc_method,
                "last_id": self._last_rpc_id,
                "last_response": self._last_rpc_response,
            },
        }

    def _response(self, method, request_id):
        if method == "v.oai.rgbcfg":
            self._saw_rgbcfg = True
            prefix = '{"result":true,"id":'
        elif method == "v.oai.thstatus":
            self._saw_thstatus = True
            prefix = '{"result":true,"id":'
        elif method == "device.status":
            prefix = '{"result":{},"id":'
        else:
            return ()
        message = (prefix + str(request_id) + "}\r\n").encode("ascii")
        self._rpc_counts[method] = min(
            self._rpc_counts[method] + 1, 0xFFFF
        )
        self._last_rpc_method = method
        self._last_rpc_id = request_id
        self._last_rpc_response = message.decode("ascii")
        frames = fragment_message(message)
        self._tx_frames = min(self._tx_frames + len(frames), 0xFFFF)
        return frames

    def _finish_object(self):
        frames = ()
        if not self._invalid and not self._overflowed:
            try:
                text = bytes(self._rx).decode("utf-8")
            except UnicodeError:
                text = None
            request = _parse_request(text) if text is not None else None
            if request is not None:
                frames = self._response(request[0], request[1])
                if not frames:
                    self._unanswered_count = min(
                        self._unanswered_count + 1, 0xFFFF
                    )
        if not frames and (self._invalid or self._overflowed):
            self._discarded_objects = min(
                self._discarded_objects + 1, 0xFFFF
            )
        self.reset_collector()
        return frames

    def _feed_byte(self, value):
        if not self._collecting:
            if value != ord("{"):
                return ()
            self._collecting = True
            self._depth = 1
            self._stack = ["{"]
            self._rx.append(value)
            return ()

        if len(self._rx) < self.RX_CAPACITY:
            self._rx.append(value)
        else:
            self._overflowed = True

        character = chr(value)
        if self._in_string:
            if self._escaped:
                self._escaped = False
            elif character == "\\":
                self._escaped = True
            elif character == '"':
                self._in_string = False
            elif value < 0x20:
                self._invalid = True
            return ()

        if character == '"':
            self._in_string = True
            return ()
        if character in "{[":
            self._depth += 1
            if self._depth > self.MAX_DEPTH:
                self._invalid = True
            else:
                self._stack.append(character)
            return ()
        if character in "}]":
            if self._depth <= 0:
                self.reset_collector()
                return ()
            if self._depth <= self.MAX_DEPTH:
                if not self._stack or not _matching(
                    self._stack[-1], character
                ):
                    self.reset_collector()
                    return ()
                self._stack.pop()
            self._depth -= 1
            if self._depth == 0:
                return self._finish_object()
        return ()

    def feed_payload(self, payload):
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            self._invalid_frames = min(self._invalid_frames + 1, 0xFFFF)
            return ()
        payload = bytes(payload)
        if len(payload) != HID_PAYLOAD_SIZE:
            self._invalid_frames = min(self._invalid_frames + 1, 0xFFFF)
            return ()
        self._rx_frames = min(self._rx_frames + 1, 0xFFFF)
        channel = payload[0]
        length = payload[1]
        if length > FRAME_DATA_SIZE or channel != CHANNEL_RPC:
            if channel != CHANNEL_DEBUG:
                self._invalid_frames = min(
                    self._invalid_frames + 1, 0xFFFF
                )
            return ()
        responses = ()
        for value in payload[2 : 2 + length]:
            responses += self._feed_byte(value)
        return responses

    def notify(self, control, action):
        act = validate_control_action(control, action)
        if not self.ready or act is None:
            return ()
        message = (
            '{"method":"v.oai.hid","params":{"k":"'
            + control
            + '","act":'
            + str(act)
            + "}}\r\n"
        ).encode("ascii")
        frames = fragment_message(message)
        self._tx_frames = min(self._tx_frames + len(frames), 0xFFFF)
        return frames

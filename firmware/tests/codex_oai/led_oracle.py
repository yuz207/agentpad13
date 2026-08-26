"""Deterministic six-slot RGB oracle for the AgentPad13 direct OAI target.

The module has no HID or firmware side effects.  It is intentionally a
separate implementation of the renderer contract so the host tests can compare
the firmware C engine frame-for-frame.
"""

from __future__ import annotations

from dataclasses import dataclass


UINT32_MASK = 0xFFFFFFFF
CODEX_LED_COUNT = 24
CODEX_TASK_LED_COUNT = 6
MAX_PROJECTED_RANKS = 6
CODEX_ACTION_FEEDBACK_MS = 160
STARTUP_STEP_MS = 80
STARTUP_SWEEP_MS = CODEX_LED_COUNT * STARTUP_STEP_MS
STARTUP_FLASH_MS = 90
STARTUP_COMPLETION_MS = STARTUP_FLASH_MS * 4
STARTUP_TOTAL_MS = STARTUP_SWEEP_MS + STARTUP_COMPLETION_MS
OAI_LINK_WAITING = 0
OAI_LINK_READY = 1
OAI_LINK_ERROR = 2
LAYER_COLORS = (
    (255, 0, 0),
    (255, 192, 0),
    (0, 255, 0),
    (0, 255, 192),
    (0, 64, 255),
    (128, 0, 255),
    (255, 0, 192),
    (255, 0, 64),
)

LED_TAIL_MS = 240
LED_CHROMA_ON_MS = 60
LED_CHROMA_OFF_MS = 60
EFFECT_STEPS = (
    ((2, 1, 0),),
    ((3, 1, 4),),
    ((1, 1, 4), (1, 1, 0), (1, 1, 4), (1, 1, 0)),
    ((1, 1, 1), (1, 1, 2), (1, 1, 4), (1, 1, 2), (1, 1, 1)),
    ((1, 1, 0), (1, 1, 1), (1, 1, 2), (1, 1, 4), (1, 1, 2), (1, 1, 1)),
    ((1, 2, 4), (1, 2, 0), (1, 2, 4), (2, 1, 0)),
    ((1, 2, 4), (1, 2, 0), (1, 2, 4), (1, 2, 0), (2, 1, 4)),
)
WORKING_STEPS = (
    (80, 8), (70, 0), (80, 8), (70, 0), (80, 8), (70, 0),
    (45, 0), (45, 1), (45, 3), (45, 6), (45, 8), (45, 6), (45, 3), (45, 1), (45, 0),
    (80, 8), (70, 0), (80, 8), (70, 0), (80, 8), (70, 0), (240, 0),
)


@dataclass(frozen=True)
class Task:
    source_slot: int = 0
    rgb: tuple[int, int, int] = (0, 0, 0)
    effect: int = 0
    brightness: int = 255
    speed: int = 0
    flags: int = 0


def task(
    *,
    slot: int = 0,
    rgb: tuple[int, int, int] = (0, 0, 0),
    effect: int = 0,
    brightness: int = 255,
    speed: int = 0,
    flags: int = 0,
) -> Task:
    """Construct an OAI task with the same fields as ``codex_oai_task_t``."""

    return Task(slot, rgb, effect, brightness, speed, flags)


def _elapsed(now_ms: int, start_ms: int) -> int:
    return (now_ms - start_ms) & UINT32_MASK


def _fraction_level(numerator: int, denominator: int) -> int:
    return (255 * numerator + denominator // 2) // denominator


def _color_family(value: Task) -> int:
    red, green, blue = value.rgb
    highest, lowest = max(value.rgb), min(value.rgb)
    if highest == 0:
        return 0
    difference = highest - lowest
    if difference <= highest // 8:
        return 7
    if highest == red:
        hue = (60 * (green - blue)) // difference
        hue %= 360
    elif highest == green:
        hue = 120 + (60 * (blue - red)) // difference
    else:
        hue = 240 + (60 * (red - green)) // difference
    if hue < 30 or hue >= 330:
        return 1
    if hue < 90:
        return 2
    if hue < 150:
        return 3
    if hue < 210:
        return 4
    if hue < 270:
        return 5
    return 6


def _visible(value: Task, active: bool) -> bool:
    return active and any(value.rgb) and value.brightness != 0 and value.effect != 0


def _working(value: Task) -> bool:
    return value.rgb == (48, 79, 254) and value.effect in (1, 4) and value.brightness != 0


def _working_level(elapsed: int) -> int:
    elapsed %= sum(duration for duration, _ in WORKING_STEPS)
    for duration, eighths in WORKING_STEPS:
        if elapsed < duration:
            return _fraction_level(eighths, 8)
        elapsed -= duration
    return 0


def _standard_level(elapsed: int, value: Task, family: int) -> int:
    tick = 120 - ((value.speed * 60 + 127) // 255)
    effect = value.effect if value.effect < len(EFFECT_STEPS) else 0
    total = LED_TAIL_MS + (family * (LED_CHROMA_ON_MS + LED_CHROMA_OFF_MS) if 1 <= family <= 6 else 300)
    total += sum(numerator * tick // denominator for numerator, denominator, _ in EFFECT_STEPS[effect])
    elapsed %= total
    if 1 <= family <= 6:
        for _ in range(family):
            if elapsed < LED_CHROMA_ON_MS:
                return 255
            elapsed -= LED_CHROMA_ON_MS
            if elapsed < LED_CHROMA_OFF_MS:
                return 0
            elapsed -= LED_CHROMA_OFF_MS
    else:
        if elapsed < 180:
            return 255
        elapsed -= 180
        if elapsed < 120:
            return 0
        elapsed -= 120
    for numerator, denominator, quarters in EFFECT_STEPS[effect]:
        duration = numerator * tick // denominator
        if elapsed < duration:
            return _fraction_level(quarters, 4)
        elapsed -= duration
    return 0


def pattern_level(value: Task, *, now_ms: int, start_ms: int, active: bool = True) -> int:
    """Return the unscaled 0..255 steady-state level for one task.

    The production firmware defaults to a hold-until-update LED policy. The
    historical animation helpers remain above as a reference corpus; the
    optional ``CODEX_LED_ANIMATION_ENABLE=1`` fade path is compiled and checked
    by the C harness separately. The default oracle deliberately ignores
    elapsed time so parity tests enforce stable state output.
    """

    if not _visible(value, active):
        return 0
    del now_ms, start_ms
    return 255


def task_rgb(value: Task, *, now_ms: int, start_ms: int, active: bool = True) -> tuple[int, int, int]:
    level = pattern_level(value, now_ms=now_ms, start_ms=start_ms, active=active)
    return tuple((channel * value.brightness * level + 32512) // 65025 for channel in value.rgb)


def working_rgb_timeline(value: Task, times: tuple[int, ...]) -> list[tuple[int, int, int]]:
    return [task_rgb(value, now_ms=timestamp, start_ms=0) for timestamp in times]


class Renderer:
    """Stateful pure renderer that mirrors the firmware renderer API."""

    def __init__(self) -> None:
        self._tasks = [task(slot=index) for index in range(CODEX_TASK_LED_COUNT)]
        self._active = [False] * CODEX_TASK_LED_COUNT
        self._starts = [0] * CODEX_TASK_LED_COUNT
        self._link_state = OAI_LINK_WAITING
        self._link_started = 0
        self._layer = 0
        self._feedback: dict[int, int] = {}
        self._startup_started: int | None = None

    def startup(self, now_ms: int) -> None:
        self._startup_started = now_ms & UINT32_MASK

    def set_tasks(self, tasks: list[Task] | tuple[Task, ...], active_mask: int, now_ms: int) -> None:
        if len(tasks) < CODEX_TASK_LED_COUNT:
            raise ValueError("at least six task slots are required")
        active_sources = {
            index for index in range(len(tasks)) if active_mask & (1 << index)
        }
        index = 0
        while index < CODEX_TASK_LED_COUNT:
            if not self._active[index]:
                break
            if self._tasks[index].source_slot not in active_sources:
                self._tasks.pop(index)
                self._starts.pop(index)
                self._active.pop(index)
                self._tasks.append(task(slot=0))
                self._starts.append(now_ms & UINT32_MASK)
                self._active.append(False)
                continue
            index += 1

        active_count = sum(self._active)
        for index in range(active_count):
            source_slot = self._tasks[index].source_slot
            value = tasks[source_slot]
            if self._tasks[index] != value:
                self._starts[index] = now_ms & UINT32_MASK
                self._tasks[index] = value

        for source_slot, value in enumerate(tasks):
            if not (active_mask & (1 << source_slot)):
                continue
            if any(self._active[index] and self._tasks[index].source_slot == source_slot for index in range(CODEX_TASK_LED_COUNT)):
                continue
            if active_count >= CODEX_TASK_LED_COUNT:
                self._tasks.pop(0)
                self._starts.pop(0)
                self._active.pop(0)
                self._tasks.append(task(slot=0))
                self._starts.append(now_ms & UINT32_MASK)
                self._active.append(False)
                active_count = CODEX_TASK_LED_COUNT - 1
            self._tasks[active_count] = value
            self._starts[active_count] = now_ms & UINT32_MASK
            self._active[active_count] = True
            active_count += 1

        for index in range(active_count, CODEX_TASK_LED_COUNT):
            self._tasks[index] = task(slot=index)
            self._starts[index] = now_ms & UINT32_MASK
            self._active[index] = False

    def reset_tasks(self, now_ms: int) -> None:
        self._tasks = [task(slot=index) for index in range(CODEX_TASK_LED_COUNT)]
        self._active = [False] * CODEX_TASK_LED_COUNT
        self._starts = [now_ms & UINT32_MASK] * CODEX_TASK_LED_COUNT

    def source_slots(self) -> list[int]:
        return [
            self._tasks[index].source_slot
            for index in range(CODEX_TASK_LED_COUNT)
            if self._active[index]
        ]

    def set_link(self, state: int, now_ms: int) -> None:
        if state not in (OAI_LINK_WAITING, OAI_LINK_READY, OAI_LINK_ERROR):
            raise ValueError("unknown link state")
        if state != self._link_state:
            self._link_state = state
            self._link_started = now_ms & UINT32_MASK

    def set_layer(self, layer: int, now_ms: int) -> None:
        del now_ms
        self._layer = layer & 0xFF

    def layer_color(self, layer: int | None = None) -> tuple[int, int, int]:
        value = self._layer if layer is None else layer
        return LAYER_COLORS[value % len(LAYER_COLORS)]

    def note_action(self, led_index: int, pressed: bool, now_ms: int) -> None:
        if pressed and CODEX_TASK_LED_COUNT <= led_index <= 12:
            self._feedback[led_index] = now_ms & UINT32_MASK

    def _global_task(self) -> tuple[Task, int] | None:
        selected: tuple[Task, int] | None = None
        for index, value in enumerate(self._tasks):
            if not _visible(value, self._active[index]):
                continue
            if selected is None or (_working(value) and not _working(selected[0])):
                selected = (value, index)
        return selected

    def _link_rgb(self, now_ms: int) -> tuple[int, int, int]:
        del now_ms
        return self.layer_color()

    def render(self, now_ms: int) -> list[tuple[int, int, int]]:
        frame = [(0, 0, 0) for _ in range(CODEX_LED_COUNT)]
        for index, value in enumerate(self._tasks):
            frame[index] = task_rgb(value, now_ms=now_ms, start_ms=self._starts[index], active=self._active[index])
        global_task = self._global_task()
        if global_task is not None:
            value, index = global_task
            global_rgb = task_rgb(value, now_ms=now_ms, start_ms=self._starts[index], active=True)
        else:
            global_rgb = (0, 0, 0)
        frame[12] = global_rgb
        frame[13] = self.layer_color() if self._link_state == OAI_LINK_READY else self._link_rgb(now_ms)
        for index in range(14, 24):
            frame[index] = tuple(channel // 2 for channel in global_rgb)
        for led_index, started in tuple(self._feedback.items()):
            if _elapsed(now_ms, started) < CODEX_ACTION_FEEDBACK_MS:
                frame[led_index] = (255, 255, 255)
            else:
                del self._feedback[led_index]
        if self._startup_started is not None:
            elapsed = _elapsed(now_ms, self._startup_started)
            if elapsed < STARTUP_TOTAL_MS:
                frame = [(0, 0, 0) for _ in range(CODEX_LED_COUNT)]
                if elapsed < STARTUP_SWEEP_MS:
                    frame[elapsed // STARTUP_STEP_MS] = (255, 255, 255)
                elif ((elapsed - STARTUP_SWEEP_MS) // STARTUP_FLASH_MS) % 2 == 0:
                    frame = [(0, 255, 0) for _ in range(CODEX_LED_COUNT)]
            else:
                self._startup_started = None
        return frame


def render(tasks: list[Task] | tuple[Task, ...], *, now_ms: int, active_mask: int | None = None) -> list[tuple[int, int, int]]:
    renderer = Renderer()
    values = list(tasks) + [task(slot=index) for index in range(len(tasks), CODEX_TASK_LED_COUNT)]
    values = values[:CODEX_TASK_LED_COUNT]
    mask = active_mask if active_mask is not None else (1 << len(tasks)) - 1
    renderer.set_tasks(values, mask, 0)
    return renderer.render(now_ms)


def render_at(start_ms: int, now_ms: int) -> list[tuple[int, int, int]]:
    renderer = Renderer()
    renderer.set_tasks([task(slot=0, rgb=(48, 79, 254), effect=4, brightness=255, speed=128)] + [task(slot=index) for index in range(1, 6)], 1, start_ms)
    return renderer.render(now_ms)

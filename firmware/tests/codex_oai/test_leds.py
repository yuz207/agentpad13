"""Host conformance tests for the AgentPad13 six-slot OAI RGB renderer."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from firmware.tests.codex_oai import led_oracle


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEYMAP = REPO / "firmware" / "loudest_micro" / "keymaps" / "codex_oai"


class Harness:
    def __init__(self, source_count: int = 6, animation: bool = False) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="agentpad13_led_")
        self._binary = Path(self._tmp.name) / "led_harness"
        command = ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror"]
        if animation:
            command.append("-DCODEX_LED_ANIMATION_ENABLE=1")
        if source_count != 6:
            command.append(f"-DOAI_SLOT_COUNT={source_count}")
        command.extend([
            "-I", str(KEYMAP),
            str(HERE / "led_harness.c"), str(KEYMAP / "codex_led.c"),
            "-o", str(self._binary),
        ])
        subprocess.run(command, check=True)
        self._process = subprocess.Popen(
            [str(self._binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=5)
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        self._process.stdin.close()
        self._process.stdout.close()
        self._tmp.cleanup()

    def command(self, command: str) -> None:
        assert self._process.stdin is not None
        self._process.stdin.write(command + "\n")
        self._process.stdin.flush()

    def reset(self) -> None:
        self.command("RESET")

    def task(self, value: led_oracle.Task, *, active: bool, now_ms: int) -> None:
        red, green, blue = value.rgb
        self.command(
            f"TASK {value.source_slot} {int(active)} {red} {green} {blue} "
            f"{value.effect} {value.brightness} {value.speed} {value.flags} {now_ms}"
        )

    def set_tasks(self, values: list[led_oracle.Task], active_mask: int, now_ms: int) -> None:
        padded = values + [led_oracle.task(slot=index) for index in range(len(values), 6)]
        for index, value in enumerate(padded[:6]):
            self.task(value, active=bool(active_mask & (1 << index)), now_ms=now_ms)

    def link(self, state: int, now_ms: int) -> None:
        self.command(f"LINK {state} {now_ms}")

    def layer(self, layer: int, now_ms: int) -> None:
        self.command(f"LAYER {layer} {now_ms}")

    def note_action(self, led_index: int, pressed: bool, now_ms: int) -> None:
        self.command(f"ACTION {led_index} {int(pressed)} {now_ms}")

    def startup(self, now_ms: int) -> None:
        self.command(f"STARTUP {now_ms}")

    def render(self, now_ms: int) -> list[tuple[int, int, int]]:
        assert self._process.stdout is not None
        self.command(f"RENDER {now_ms}")
        frame: list[tuple[int, int, int]] = []
        for line in self._process.stdout:
            line = line.rstrip("\n")
            if line == "---":
                break
            fields = line.split()
            if len(fields) != 5 or fields[0] != "LED" or int(fields[1]) != len(frame):
                raise AssertionError(f"invalid LED harness output: {line!r}")
            frame.append(tuple(map(int, fields[2:])))
        if len(frame) != 24:
            raise AssertionError(f"expected 24 LEDs, got {len(frame)}")
        return frame


class LedParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = Harness()

    def tearDown(self) -> None:
        self.harness.close()

    def assert_parity(self, renderer: led_oracle.Renderer, now_ms: int) -> list[tuple[int, int, int]]:
        expected = renderer.render(now_ms)
        self.assertEqual(self.harness.render(now_ms), expected)
        return expected

    @staticmethod
    def colored_task(slot: int, rgb: tuple[int, int, int]) -> led_oracle.Task:
        return led_oracle.task(slot=slot, rgb=rgb, effect=1, brightness=255)

    def apply_task(self, value: led_oracle.Task, *, active: bool, now_ms: int) -> None:
        self.harness.task(value, active=active, now_ms=now_ms)

    def task_leds(self, now_ms: int = 0) -> list[tuple[int, int, int]]:
        return self.harness.render(now_ms)[:led_oracle.CODEX_TASK_LED_COUNT]

    def test_new_tasks_append_in_activation_order_and_updates_keep_position(self) -> None:
        renderer = led_oracle.Renderer()
        tasks = [led_oracle.task(slot=i) for i in range(6)]
        active_mask = 0

        def apply(value: led_oracle.Task, active: bool, now_ms: int) -> None:
            nonlocal active_mask
            tasks[value.source_slot] = value
            if active:
                active_mask |= 1 << value.source_slot
            else:
                active_mask &= ~(1 << value.source_slot)
            renderer.set_tasks(tasks, active_mask, now_ms)
            self.harness.task(value, active=active, now_ms=now_ms)

        red = self.colored_task(3, (255, 0, 0))
        green = self.colored_task(1, (0, 255, 0))
        blue = self.colored_task(3, (0, 0, 255))
        apply(red, True, 0)
        apply(green, True, 10)
        apply(blue, True, 20)
        self.assertEqual(self.harness.render(20), renderer.render(20))
        self.assertEqual(renderer.source_slots(), [3, 1])
        self.assertEqual(self.task_leds(20), [(0, 0, 255), (0, 255, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)])

    def test_remove_compacts_and_reactivation_goes_to_tail(self) -> None:
        renderer = led_oracle.Renderer()
        tasks = [led_oracle.task(slot=i) for i in range(6)]
        active_mask = 0

        def apply(value: led_oracle.Task, active: bool, now_ms: int) -> None:
            nonlocal active_mask
            tasks[value.source_slot] = value
            if active:
                active_mask |= 1 << value.source_slot
            else:
                active_mask &= ~(1 << value.source_slot)
            renderer.set_tasks(tasks, active_mask, now_ms)
            self.harness.task(value, active=active, now_ms=now_ms)

        red = self.colored_task(3, (255, 0, 0))
        green = self.colored_task(1, (0, 255, 0))
        apply(red, True, 0)
        apply(green, True, 10)
        apply(red, False, 20)
        self.assertEqual(self.harness.render(20), renderer.render(20))
        self.assertEqual(renderer.source_slots(), [1])
        self.assertEqual(self.task_leds(20), [(0, 255, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)])
        apply(red, True, 30)
        self.assertEqual(self.harness.render(30), renderer.render(30))
        self.assertEqual(renderer.source_slots(), [1, 3])
        self.assertEqual(self.task_leds(30), [(0, 255, 0), (255, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)])

    def test_explicit_reset_clears_all_task_leds(self) -> None:
        renderer = led_oracle.Renderer()
        self.apply_task(self.colored_task(2, (255, 255, 0)), active=True, now_ms=0)
        self.harness.command("CLEAR 500")
        renderer.reset_tasks(500)
        self.assertEqual(self.harness.render(500), renderer.render(500))
        self.assertEqual(self.task_leds(500), [(0, 0, 0)] * led_oracle.CODEX_TASK_LED_COUNT)

    def test_full_fifo_evicts_oldest_before_appending_new_source(self) -> None:
        harness = Harness(source_count=8)
        try:
            renderer = led_oracle.Renderer()
            tasks = [led_oracle.task(slot=i) for i in range(8)]
            active_mask = 0
            colors = (
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
                (255, 255, 0),
                (0, 255, 255),
                (255, 0, 255),
                (255, 255, 255),
            )
            for slot, rgb in enumerate(colors):
                value = self.colored_task(slot, rgb)
                tasks[slot] = value
                active_mask |= 1 << slot
                renderer.set_tasks(tasks, active_mask, slot)
                harness.task(value, active=True, now_ms=slot)
            self.assertEqual(harness.render(6), renderer.render(6))
            self.assertEqual(
                harness.render(6)[:led_oracle.CODEX_TASK_LED_COUNT],
                list(colors[1:])
            )
        finally:
            harness.close()

    def test_each_task_slot_owns_led_zero_through_five(self) -> None:
        tasks = [led_oracle.task(slot=i, rgb=(10 + i, 20 + i, 30 + i), effect=1) for i in range(6)]
        renderer = led_oracle.Renderer()
        renderer.set_tasks(tasks, 0x3F, 0)
        self.harness.set_tasks(tasks, 0x3F, 0)
        frame = self.assert_parity(renderer, 0)
        self.assertEqual([frame[i] for i in range(6)], [item.rgb for item in tasks])

    def test_task_state_remains_steady_without_updates(self) -> None:
        task0 = led_oracle.task(slot=0, rgb=(48, 79, 254), effect=4, brightness=255, speed=128)
        renderer = led_oracle.Renderer()
        renderer.set_tasks([task0] + [led_oracle.task(slot=i) for i in range(1, 6)], 1, 0)
        self.harness.set_tasks([task0], 1, 0)
        times = (0, 80, 150, 300, 660, 900, 5000)
        levels = [self.assert_parity(renderer, timestamp)[0] for timestamp in times]
        self.assertEqual(levels, [task0.rgb] * len(times))

    def test_uint32_rollover_keeps_same_animation_phase(self) -> None:
        start = 0xFFFFFFF0
        value = led_oracle.task(slot=0, rgb=(48, 79, 254), effect=4, brightness=255, speed=128)
        wrapped = led_oracle.Renderer()
        wrapped.set_tasks([value] + [led_oracle.task(slot=i) for i in range(1, 6)], 1, start)
        self.harness.set_tasks([value], 1, start)
        self.assertEqual(self.assert_parity(wrapped, 0x10), led_oracle.render_at(0, 0x20))

    def test_action_feedback_expires_after_160_ms(self) -> None:
        renderer = led_oracle.Renderer()
        renderer.note_action(6, True, 1000)
        self.harness.note_action(6, True, 1000)
        self.assertEqual(self.assert_parity(renderer, 1159)[6], (255, 255, 255))
        self.assertEqual(self.assert_parity(renderer, 1160)[6], (0, 0, 0))

    def test_all_effects_match_c_renderer(self) -> None:
        for effect in range(7):
            value = led_oracle.task(slot=0, rgb=(210, 30, 90), effect=effect, brightness=173, speed=192)
            renderer = led_oracle.Renderer()
            renderer.set_tasks([value] + [led_oracle.task(slot=i) for i in range(1, 6)], 1, 0)
            self.harness.reset()
            self.harness.set_tasks([value], 1, 0)
            for now_ms in (0, 59, 60, 120, 360, 900, 0xFFFFFFF0):
                self.assert_parity(renderer, now_ms)

    def test_global_task_and_underglow_follow_working_preference(self) -> None:
        first = led_oracle.task(slot=0, rgb=(255, 0, 0), effect=4)
        working = led_oracle.task(slot=4, rgb=(48, 79, 254), effect=1)
        values = [first] + [led_oracle.task(slot=i) for i in range(1, 4)] + [working, led_oracle.task(slot=5)]
        renderer = led_oracle.Renderer()
        renderer.set_tasks(values, (1 << 0) | (1 << 4), 0)
        self.harness.set_tasks(values, (1 << 0) | (1 << 4), 0)
        frame = self.assert_parity(renderer, 0)
        self.assertEqual(renderer.source_slots(), [0, 4])
        self.assertEqual(frame[12], frame[1])
        self.assertTrue(all(frame[index] == tuple(channel // 2 for channel in frame[12]) for index in range(14, 24)))

    def test_link_states_and_feedback_hero_match_c_renderer(self) -> None:
        renderer = led_oracle.Renderer()
        self.assert_parity(renderer, 0)
        self.assertEqual(renderer.render(0)[13], renderer._link_rgb(0))
        self.assertEqual(renderer.render(500)[13], renderer._link_rgb(500))
        renderer.set_link(led_oracle.OAI_LINK_READY, 700)
        self.harness.link(led_oracle.OAI_LINK_READY, 700)
        self.assertEqual(self.assert_parity(renderer, 701)[13], renderer.layer_color())
        renderer.set_link(led_oracle.OAI_LINK_ERROR, 1000)
        self.harness.link(led_oracle.OAI_LINK_ERROR, 1000)
        self.assertEqual(self.assert_parity(renderer, 1001)[13], renderer._link_rgb(1001))
        self.assertEqual(self.assert_parity(renderer, 1120)[13], renderer._link_rgb(1120))
        renderer.note_action(12, True, 1200)
        self.harness.note_action(12, True, 1200)
        self.assertEqual(self.assert_parity(renderer, 1201)[12], (255, 255, 255))

    def test_touch_indicator_changes_for_every_enabled_layer_when_link_is_ready(self) -> None:
        renderer = led_oracle.Renderer()
        colors = []
        for layer in range(4):
            renderer.set_layer(layer, layer * 10)
            self.harness.layer(layer, layer * 10)
            colors.append(self.assert_parity(renderer, layer * 10)[13])
        self.assertEqual(
            colors,
            [renderer.layer_color(layer) for layer in range(4)],
        )
        self.assertEqual(len(set(colors)), 4)
        renderer.set_link(led_oracle.OAI_LINK_READY, 50)
        self.harness.link(led_oracle.OAI_LINK_READY, 50)
        for layer in range(4):
            renderer.set_layer(layer, 60 + layer)
            self.harness.layer(layer, 60 + layer)
            self.assertEqual(self.assert_parity(renderer, 60 + layer)[13], renderer.layer_color(layer))

    def test_layer_indicator_keeps_the_exact_layer_colour_before_oai_readiness(self) -> None:
        """A disconnected OAI endpoint must not make CODEX red look like FN yellow."""
        renderer = led_oracle.Renderer()
        renderer.set_layer(0, 0)
        self.harness.layer(0, 0)
        self.assertEqual(self.assert_parity(renderer, 1)[13], (255, 0, 0))

        renderer.set_link(led_oracle.OAI_LINK_ERROR, 10)
        self.harness.link(led_oracle.OAI_LINK_ERROR, 10)
        self.assertEqual(self.assert_parity(renderer, 11)[13], (255, 0, 0))

    def test_startup_sweep_visits_all_24_leds_in_order(self) -> None:
        renderer = led_oracle.Renderer()
        start_ms = 1000
        renderer.startup(start_ms)
        self.harness.startup(start_ms)
        for index in range(led_oracle.CODEX_LED_COUNT):
            frame = self.assert_parity(renderer, start_ms + index * led_oracle.STARTUP_STEP_MS + 40)
            self.assertEqual([led for led, color in enumerate(frame) if color != (0, 0, 0)], [index])
            self.assertEqual(frame[index], (255, 255, 255))
        completion = self.assert_parity(renderer, start_ms + led_oracle.STARTUP_SWEEP_MS + 45)
        self.assertEqual(completion, [(0, 255, 0)] * led_oracle.CODEX_LED_COUNT)
        self.assertEqual(
            self.assert_parity(renderer, start_ms + led_oracle.STARTUP_TOTAL_MS + 1),
            led_oracle.Renderer().render(start_ms + led_oracle.STARTUP_TOTAL_MS + 1),
        )

    def test_optional_animation_is_slow_and_fade_like(self) -> None:
        harness = Harness(animation=True)
        try:
            value = led_oracle.task(slot=0, rgb=(160, 80, 32), effect=4, brightness=255, speed=128)
            harness.task(value, active=True, now_ms=0)
            frames = [harness.render(now_ms)[0] for now_ms in (0, 300, 600, 1200, 1800, 2400)]
            self.assertGreaterEqual(len(set(frames)), 4)
            self.assertTrue(all(all(channel > 0 for channel in frame) for frame in frames))
            self.assertTrue(any(any(channel not in (0, original) for channel, original in zip(frame, value.rgb)) for frame in frames))
            harness.link(led_oracle.OAI_LINK_ERROR, 0)
            link_frames = [harness.render(now_ms)[13] for now_ms in (0, 600, 1200, 1800)]
            self.assertGreaterEqual(len(set(link_frames)), 3)
            self.assertTrue(all(frame[0] > 0 for frame in link_frames))
        finally:
            harness.close()


if __name__ == "__main__":
    unittest.main()

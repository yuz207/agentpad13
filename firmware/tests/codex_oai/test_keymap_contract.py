"""Static integration contract for the isolated AgentPad13 OAI keymap.

The host protocol and LED renderer have executable C harnesses.  This narrow
test protects the QMK glue whose observable boundary is the compiled keymap:
the USB Raw HID descriptor settings, physical layout and the absence of the
legacy helper/Vial route.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEYMAP = REPO / "firmware" / "loudest_micro" / "keymaps" / "codex_oai"

EXPECTED_LAYOUT = [
    "OAI_AG00", "OAI_AG01", "OAI_AG02", "OAI_AG03",
    "OAI_AG04", "OAI_AG05", "OAI_ACT06", "OAI_ACT07",
    "OAI_ACT08", "OAI_ACT09", "OAI_ACT10", "OAI_ACT11",
    "OAI_ACT12", "OAI_ENC",
]


class KeymapContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = (KEYMAP / "config.h").read_text()
        self.rules_text = (KEYMAP / "rules.mk").read_text()
        self.keymap = (KEYMAP / "keymap.c").read_text()
        self.common = (REPO / "firmware" / "loudest_micro" / "loudest_micro.c").read_text()
        self.rules = dict(
            re.findall(r"^([A-Z][A-Z0-9_]*)\s*=\s*([^\s#]+)", self.rules_text, re.MULTILINE)
        )

    def test_exact_usb_contract(self) -> None:
        for name, definition in (
            ("VENDOR_ID", "#define VENDOR_ID 0x303A"),
            ("PRODUCT_ID", "#define PRODUCT_ID 0x8360"),
            ("DEVICE_VER", "#define DEVICE_VER 0x0005"),
            ("MANUFACTURER", "#define MANUFACTURER \"hirlu\""),
            ("PRODUCT", "#define PRODUCT \"Codex Micro Lab OAI LED\""),
            ("RAW_USAGE_PAGE", "#define RAW_USAGE_PAGE 0xFF00"),
            ("RAW_USAGE_ID", "#define RAW_USAGE_ID 0x61"),
            ("RAW_EPSIZE", "#define RAW_EPSIZE 64"),
            ("RAW_REPORT_ID", "#define RAW_REPORT_ID 6"),
        ):
            undefinition = f"#undef {name}"
            self.assertIn(undefinition, self.config)
            self.assertIn(definition, self.config)
            self.assertLess(self.config.index(undefinition), self.config.index(definition))

    def test_isolated_keymap_excludes_vial_and_helper(self) -> None:
        self.assertEqual(self.rules["VIA_ENABLE"], "no")
        self.assertEqual(self.rules["VIAL_ENABLE"], "no")
        self.assertNotIn("CXH_", self.keymap)

    def test_physical_layout_and_feedback_contract(self) -> None:
        layout = re.search(r"\[L_CODEX\]\s*=\s*LAYOUT\((.*?)\)\s*,", self.keymap, re.DOTALL)
        self.assertIsNotNone(layout)
        assert layout is not None
        self.assertEqual(re.findall(r"OAI_[A-Z0-9_]+", layout.group(1)), EXPECTED_LAYOUT)
        self.assertIn("CODEX_TOUCH_LAYER", layout.group(1))
        self.assertIn("codex_led_note_action(feedback_led, pressed, timer_read32())", self.keymap)
        for led in (6, 7, 8, 9):
            self.assertIn(f"OAI_ACT{led:02d}: return", self.keymap)
        self.assertIn("codex_oai_position_for_keycode", self.keymap)
        self.assertIn("codex_oai_feedback_led", self.keymap)
        self.assertEqual(re.findall(r"OAI_[A-Z0-9_]+", layout.group(1))[10:13], ["OAI_ACT10", "OAI_ACT11", "OAI_ACT12"])

    def test_codex_grid_uses_official_act10_act11_act12_routes(self) -> None:
        """The thirteen physical positions use the official OAI action order."""
        layout = re.search(r"\[L_CODEX\]\s*=\s*LAYOUT\((.*?)\);", self.keymap, re.DOTALL)
        self.assertIsNotNone(layout)
        assert layout is not None
        positions = re.findall(r"OAI_[A-Z0-9_]+", layout.group(1))
        self.assertEqual(positions[10], "OAI_ACT10")
        self.assertEqual(positions[11], "OAI_ACT11")
        self.assertEqual(positions[12], "OAI_ACT12")
        self.assertIn("case OAI_ACT10: return 10;", self.keymap)
        self.assertIn("case OAI_ACT11: return 11;", self.keymap)
        self.assertIn("case OAI_ACT12: return 12;", self.keymap)
        self.assertIn("OAI_CONTROL_ACT11", (KEYMAP / "codex_oai.c").read_text())

    def test_function_feedback_is_white_but_task_keys_are_not(self) -> None:
        """Feedback follows physical function positions, never task positions."""
        self.assertIn("static uint8_t codex_oai_feedback_led(uint8_t position)", self.keymap)
        self.assertIn(
            "if (position < CODEX_ACTION_FEEDBACK_FIRST || position > CODEX_ACTION_FEEDBACK_LAST)",
            self.keymap,
        )
        self.assertIn("return position;", self.keymap)
        self.assertIn("uint8_t feedback_led = codex_oai_feedback_led(position);", self.keymap)
        self.assertIn("#define CODEX_ACTION_FEEDBACK_FIRST CODEX_TASK_LED_COUNT", (KEYMAP / "codex_led.h").read_text())
        self.assertIn("#define CODEX_ACTION_FEEDBACK_LAST 12U", (KEYMAP / "codex_led.h").read_text())
        self.assertIn("if (feedback_led != 0U)", self.keymap)

    def test_oai_positions_are_runtime_customizable(self) -> None:
        for token in (
            "codex_oai_keymap_action_for_position",
            "handle_dynamic_oai_position",
            "codex_oai_keymap_set_hex",
            "v.oai.keymap.get",
            "v.oai.keymap.set",
        ):
            source = self.keymap if token.startswith("handle_") or token.startswith("codex_oai_position") else (KEYMAP / "codex_oai.c").read_text()
            self.assertIn(token, source)

    def test_two_default_layers_are_table_driven_and_extensible(self) -> None:
        self.assertRegex(self.keymap, r"define CODEX_EXTRA_LAYERS\s+2")
        self.assertIn("#define CODEX_LAYER_COUNT (2 + CODEX_EXTRA_LAYERS)", self.keymap)
        self.assertIn("L_CODEX = 0", self.keymap)
        self.assertIn("#define CODEX_OAI_LAYER L_CODEX", self.keymap)
        self.assertIn("select_codex_layer(CODEX_OAI_LAYER)", self.keymap)
        self.assertIn("L_FN", self.keymap)
        self.assertIn("L_USER2", self.keymap)
        self.assertIn("L_USER3", self.keymap)
        self.assertIn("L_USER4", self.keymap)
        self.assertIn("CODEX_EXTRA_LAYERS > 3", self.keymap)
        self.assertIn("codex_layer_order[CODEX_LAYER_COUNT]", self.keymap)
        self.assertNotIn("_CODEX_ARMED", self.keymap)
        self.assertNotIn("layer_on(", self.keymap)

    def test_boot_clears_both_qmk_layer_state_sources_to_codex(self) -> None:
        """A persisted non-CODEX default layer must not override layer_move(0)."""
        post_init = re.search(
            r"void keyboard_post_init_user\(void\) \{(.*?)\n\}",
            self.keymap,
            re.DOTALL,
        )
        self.assertIsNotNone(post_init)
        assert post_init is not None
        body = post_init.group(1)
        default_reset = "default_layer_set(1UL << CODEX_OAI_LAYER);"
        oai_select = "select_codex_layer(CODEX_OAI_LAYER);"
        self.assertIn(default_reset, body)
        self.assertIn(oai_select, body)
        self.assertLess(body.index(default_reset), body.index(oai_select))

    def test_touch_pad_cycles_all_layers(self) -> None:
        for token in (
            "CODEX_TOUCH_LAYER",
            "case CODEX_TOUCH_LAYER:",
            "cycle_codex_layer();",
            "[L_USER2] = LAYOUT(",
            "[L_USER3] = LAYOUT(",
        ):
            self.assertIn(token, self.keymap)
        touch_layouts = re.findall(
            r"\[L_(?:CODEX|FN|USER2|USER3)\]\s*=\s*LAYOUT\((.*?)(?=\n    \[L_|\n};)",
            self.keymap,
            re.DOTALL,
        )
        self.assertEqual(len(touch_layouts), 4)
        for layout in touch_layouts:
            self.assertEqual(re.findall(r"CODEX_TOUCH_LAYER", layout)[-1], "CODEX_TOUCH_LAYER")

    def test_touch_layer_cycle_ignores_sensor_startup_transient(self) -> None:
        """TP5 cannot move a fresh CODEX boot into FN during the RGB self-check."""
        touch_case = re.search(
            r"case CODEX_TOUCH_LAYER:(.*?)(?=\n        case |\n        default:)",
            self.keymap,
            re.DOTALL,
        )
        self.assertIsNotNone(touch_case)
        assert touch_case is not None
        body = touch_case.group(1)
        self.assertIn("pressed && !codex_led_startup_active(timer_read32())", body)
        self.assertIn("cycle_codex_layer();", body)

    def test_encoder_press_is_oai_only_on_every_layer(self) -> None:
        layouts = re.findall(
            r"\[L_(?:CODEX|FN|USER2|USER3)\]\s*=\s*LAYOUT\((.*?)\)\s*,",
            self.keymap,
            re.DOTALL,
        )
        self.assertEqual(len(layouts), 4)
        for layout in layouts:
            positions = re.findall(r"[A-Z][A-Z0-9_]*(?:\([^)]*\))?", layout)
            self.assertEqual(positions[-2:], ["OAI_ENC", "CODEX_TOUCH_LAYER"])

    def test_encoder_oai_action_never_changes_layer_or_os_mode(self) -> None:
        start = self.keymap.index("if (action == OAI_KEYMAP_ENCODER)")
        end = self.keymap.index("if (action == OAI_KEYMAP_SEND", start)
        handler = self.keymap[start:end]
        self.assertIn("notify_encoder_press(pressed)", handler)
        self.assertNotIn("cycle_codex_layer()", handler)
        self.assertNotIn("select_codex_layer", handler)
        self.assertNotIn("eeconfig_update_user", handler)

    def test_physical_encoder_direction_matches_target_flip(self) -> None:
        """The flipped driver callback reports physical clockwise as true."""
        keyboard_config = (REPO / "firmware" / "loudest_micro" / "config.h").read_text()
        self.assertIn("#define ENCODER_DIRECTION_FLIP", keyboard_config)

        encoder = re.search(
            r"bool encoder_update_user\(uint8_t index, bool clockwise\) \{(.*?)\n\}",
            self.keymap,
            re.DOTALL,
        )
        self.assertIsNotNone(encoder)
        assert encoder is not None
        body = encoder.group(1)

        expected_mappings = {
            "FN scroll": "tap_code16(clockwise ? KC_WH_D : KC_WH_U);",
            "NAV paging": "tap_code16(clockwise ? KC_PGDN : KC_PGUP);",
            "MEDIA volume": "tap_code16(clockwise ? KC_VOLU : KC_VOLD);",
            "OAI notification": (
                "codex_oai_notify(clockwise ? OAI_CONTROL_ENCODER_CW : "
                "OAI_CONTROL_ENCODER_CCW, true)"
            ),
            "native fallback": (
                "native_action(clockwise ? CX_ACTION_REASONING_UP : "
                "CX_ACTION_REASONING_DOWN);"
            ),
        }
        for mapping, source in expected_mappings.items():
            with self.subTest(mapping=mapping):
                self.assertIn(source, body)

    def test_native_fallback_and_safety_contract(self) -> None:
        for token in (
            "static bool notify_or_native",
            "if (codex_oai_ready())",
            "CX_ACCEPT_TERM 600U",
            "safe_pressed",
            "codex_armed",
            "clear_codex_arm",
            "CX_ACTION_TERMINAL",
            "native_action(clockwise ? CX_ACTION_REASONING_UP : CX_ACTION_REASONING_DOWN)",
            "native_action(CX_ACTION_SEND)",
            "codex_oai_notify(OAI_CONTROL_ACT10, true)",
            "codex_oai_handshake_revision()",
            "codex_led_reset_tasks(timer_read32())",
        ):
            self.assertIn(token, self.keymap)

    def test_native_new_has_distinct_short_and_hold_actions(self) -> None:
        for token in (
            "static uint32_t new_timer",
            "CX_NEW_HOLD_TERM TAPPING_TERM",
            "timer_elapsed32(new_timer) >= CX_NEW_HOLD_TERM",
            "native_action(CX_ACTION_TERMINAL)",
        ):
            self.assertIn(token, self.keymap)

    def test_fn_layer_exposes_useful_hardware_controls(self) -> None:
        fn = re.search(r"\[L_FN\]\s*=\s*LAYOUT\((.*?)\)\s*,", self.keymap, re.DOTALL)
        self.assertIsNotNone(fn)
        assert fn is not None
        self.assertIn("JS_MODE", fn.group(1))
        self.assertIn("OAI_ENC", fn.group(1))
        self.assertIn("KC_F2", fn.group(1))
        self.assertIn("KC_F12", fn.group(1))
        self.assertIn("KC_WH_D", self.keymap)
        self.assertIn("TP_TOG", self.keymap)

    def test_touch_led_tracks_layer_while_oai_layer_stays_zero_based(self) -> None:
        for token in (
            "codex_led_set_layer",
            "get_highest_layer(layer_state | default_layer_state)",
            "select_codex_layer",
            "LED_LAYER_INDEX",
        ):
            source = self.keymap if token not in {"LED_LAYER_INDEX"} else (KEYMAP / "codex_led.c").read_text()
            self.assertIn(token, source)
        # The RPC is intentionally constrained to its first (human layer 1)
        # and must not silently become an OAI map for FN/NAV/MEDIA.
        self.assertIn("layer != 0U", (KEYMAP / "codex_oai.c").read_text())

    def test_touch_toggle_remains_reachable_after_touch_is_disabled(self) -> None:
        """TP_TOG must be allowed through the shared touch gate to re-enable it."""
        self.assertIn(
            "&& !touch_enabled && keycode != TP_TOG",
            self.common,
        )

    def test_startup_led_check_keeps_renderer_enabled_without_persisting(self) -> None:
        for token in (
            "codex_led_startup_begin(timer_read32())",
            "rgb_matrix_is_enabled()",
            "rgb_matrix_enable_noeeprom()",
        ):
            self.assertIn(token, self.keymap)
        self.assertNotIn("rgb_matrix_disable_noeeprom()", self.keymap)
        self.assertNotIn("codex_rgb_restore_off", self.keymap)

    def test_common_paths_are_guarded_for_oai_target(self) -> None:
        self.assertIn("!defined(LOUDEST_CUSTOM_RAW_HID)", self.common)
        self.assertIn("defined(LOUDEST_CUSTOM_RGB_STATUS)", self.common)
        self.assertIn("return rgb_matrix_indicators_advanced_user(led_min, led_max);", self.common)

    def test_custom_rgb_runs_user_renderer_before_calibration_overlay(self) -> None:
        """Custom RGB must retain the shared SW14 calibration display."""
        harness = HERE / "calibration_rgb_harness.c"
        with tempfile.TemporaryDirectory(prefix="agentpad13_calibration_rgb_") as directory:
            binary = Path(directory) / "calibration_rgb_harness"
            subprocess.run(
                [
                    "cc",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-DRAW_ENABLE",
                    "-DRGB_MATRIX_ENABLE",
                    "-DLOUDEST_CUSTOM_RAW_HID",
                    "-DLOUDEST_CUSTOM_RGB_STATUS",
                    "-I",
                    str(REPO / "firmware" / "tests" / "conformance" / "stubs"),
                    "-I",
                    str(REPO / "firmware" / "loudest_micro"),
                    str(harness),
                    "-o",
                    str(binary),
                ],
                check=True,
            )
            completed = subprocess.run([str(binary)], check=False)
            self.assertEqual(completed.returncode, 0)

    def test_raw_and_rgb_opt_out_guards_are_independent(self) -> None:
        raw_handler = self.common.index("static void loudest_status_handle")
        raw_guard = self.common.rfind(
            "#if defined(RAW_ENABLE) && !defined(LOUDEST_CUSTOM_RAW_HID)",
            0,
            raw_handler,
        )
        raw_end = self.common.index(
            "#endif // RAW_ENABLE && !LOUDEST_CUSTOM_RAW_HID", raw_handler
        )
        self.assertNotIn("#if !defined(LOUDEST_CUSTOM_RGB_STATUS)", self.common[raw_guard:raw_end])

        rgb_handler = self.common.index("bool rgb_matrix_indicators_advanced_kb")
        rgb_guard = self.common.rfind("#if defined(RGB_MATRIX_ENABLE)", 0, rgb_handler)
        self.assertIn("defined(LOUDEST_CUSTOM_RGB_STATUS)", self.common[rgb_guard:rgb_handler])
        self.assertNotIn("LOUDEST_CUSTOM_RAW_HID", self.common[rgb_guard:rgb_handler])

    def test_runbook_matches_press_only_agent_release_contract(self) -> None:
        runbook = (REPO / "docs" / "codex-oai-physical-runbook.md").read_text()
        ag_row = next(line for line in runbook.splitlines() if line.startswith("| AG00..AG05 |"))
        self.assertIn("press notification", ag_row)
        self.assertIn("release remains intentionally silent", ag_row)
        self.assertNotIn("press/release notification", ag_row)


if __name__ == "__main__":
    unittest.main()

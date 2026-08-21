"""Host proof that direct-OAI logical RGB cannot exceed the board power cap."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEYBOARD = REPO / "firmware" / "loudest_micro"
KEYMAP = KEYBOARD / "keymaps" / "codex_oai"


class RgbPowerCapTest(unittest.TestCase):
    def test_all_channels_and_live_values_stay_below_board_cap(self) -> None:
        board = json.loads((KEYBOARD / "keyboard.json").read_text(encoding="utf-8"))
        cap = board["rgb_matrix"]["max_brightness"]
        self.assertEqual(cap, 105)

        source = r'''
#include <stdint.h>
#include "codex_rgb_cap.h"

int main(void) {
    for (unsigned channel = 0; channel <= 255; ++channel) {
        for (unsigned value = 0; value <= 255; ++value) {
            uint8_t output = codex_rgb_cap_channel(channel, value, 105);
            if (output > 105 || output > value) {
                return 1;
            }
        }
    }
    return codex_rgb_cap_channel(255, 255, 105) == 105 ? 0 : 2;
}
'''
        with tempfile.TemporaryDirectory(prefix="agentpad13_rgb_cap_") as directory:
            source_path = Path(directory) / "rgb_cap.c"
            binary = Path(directory) / "rgb_cap"
            source_path.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(KEYMAP), str(source_path), "-o", str(binary),
                ],
                check=True,
            )
            subprocess.run([str(binary)], check=True)

    def test_keymap_caps_only_the_physical_output_path(self) -> None:
        source = (KEYMAP / "keymap.c").read_text(encoding="utf-8")
        self.assertIn("rgb_matrix_get_val()", source)
        self.assertEqual(source.count("codex_rgb_cap_channel(frame[led]."), 3)
        self.assertIn("RGB_MATRIX_MAXIMUM_BRIGHTNESS", source)


if __name__ == "__main__":
    unittest.main()

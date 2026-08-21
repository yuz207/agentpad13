# Codex OAI startup LED check implementation plan

> **Historical plan:** this preserves the startup-check implementation record.
> Its then-current artifact path and values are superseded by
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2` (93,696 bytes, SHA-256
> `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`).
> Physical validation remains PENDING and no flash occurred.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution approved for this request). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic power-on sweep across LEDs 1–24 to the direct OAI keymap, preserve normal task rendering afterward, and verify the complete pre-`dev` implementation against source, host, emulator, and artifact evidence.

**Architecture:** Keep the existing six-slot/FIFO renderer and OAI protocol unchanged. Add a short-lived startup diagnostic state inside `codex_led.c`; while active, `codex_led_render()` overlays one white pixel at a time over the complete 24-pixel chain, followed by a green completion indication, then returns to the existing task/link/feedback renderer. The keymap enables RGB without EEPROM writes so the check is visible even if RGB was previously disabled, and keeps it active for normal task/link rendering.

**Tech Stack:** QMK C keymap, C11 renderer harness, Python `unittest` oracle/parity tests, pinned RP2040 build, rp2040js emulator, SHA-256 artifact verifier.

## Global Constraints

- Preserve the direct OAI contract: VID:PID `303A:8360`, Raw HID usage `FF00:0061`, Report ID `6`, 64-byte reports.
- Preserve the existing two default layers, runtime keymap RPC, six-task FIFO, input routing, and default/Vial keymaps.
- The startup check is diagnostic only, does not write EEPROM, does not send OAI events, and runs once per boot.
- LED indexes are the physical chain order `0..23`, documented to the user as LEDs `1..24`.
- No physical flash or USB write is performed in this implementation turn.
- Keep all existing user-owned files outside this worktree untouched.

---

### Task 1: Add the failing startup-sweep contract test

**Files:**
- Modify: `firmware/tests/codex_oai/test_leds.py`
- Modify: `firmware/tests/codex_oai/led_oracle.py`
- Modify: `firmware/tests/codex_oai/led_harness.c`

**Interfaces:**
- Test harness command `STARTUP <now_ms>` calls `codex_led_startup_begin(uint32_t now_ms)`.
- Oracle method `Renderer.startup(now_ms)` models the same diagnostic timeline.

- [x] **Step 1: Add a red test for ordered one-pixel coverage.**

Assert that the midpoint of each 80 ms slot lights exactly one successive LED in white, and that the completion window lights the full chain green before normal rendering resumes.

- [x] **Step 2: Run the focused test and record the expected RED failure.**

Run `python3 -m unittest firmware.tests.codex_oai.test_leds.LedParityTest.test_startup_sweep_visits_all_24_leds_in_order -v`.
Expected: the test cannot compile the harness because the production startup API does not exist yet.

---

### Task 2: Implement the renderer startup diagnostic

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_led.c`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_led.h`

**Interfaces:**
- Produce `void codex_led_startup_begin(uint32_t now_ms)`.
- Produce `bool codex_led_startup_active(uint32_t now_ms)`.
- Preserve all existing renderer APIs and FIFO semantics.

- [x] **Step 1: Define the deterministic timeline.**

Use `CODEX_STARTUP_STEP_MS = 80`, one slot for each of 24 LEDs, then a 360 ms completion window with two 90 ms green flashes. Use unsigned `uint32_t` elapsed arithmetic so timer rollover remains safe.

- [x] **Step 2: Add state and lifecycle functions.**

Reset startup state in `codex_led_init()`. `codex_led_startup_begin()` marks the start time. `codex_led_startup_active()` returns true only inside the sweep/completion interval and clears the running flag after the interval.

- [x] **Step 3: Overlay the sweep in `codex_led_render()`.**

Render the existing task/link/feedback frame first. While startup is active, clear the frame and write either one white pixel at `elapsed / CODEX_STARTUP_STEP_MS` or an all-green completion frame during the two completion flashes.

- [x] **Step 4: Run the focused LED test to reach GREEN.**

Run `python3 -m unittest firmware.tests.codex_oai.test_leds.LedParityTest.test_startup_sweep_visits_all_24_leds_in_order -v`.

---

### Task 3: Make the keymap run the check without changing persistent RGB state

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- Modify: `firmware/tests/codex_oai/test_keymap_contract.py`

**Interfaces:**
- Keymap calls `codex_led_startup_begin(timer_read32())` during post-init.
- Keymap uses `rgb_matrix_enable_noeeprom()` when needed and does not disable RGB after the check, because task/link rendering must remain visible.

- [x] **Step 1: Add a static contract test before changing keymap code.**

Assert startup begin, `rgb_matrix_is_enabled`, and no-EEPROM enable are present; assert that no post-startup disable hides task/link rendering.

- [x] **Step 2: Implement the minimal keymap lifecycle.**

Enable RGB without EEPROM writes when needed, start the sweep, and keep the renderer active after completion. Do not route any key or OAI event through this state.

- [x] **Step 3: Run keymap and LED tests.**

Run `python3 -m unittest firmware.tests.codex_oai.test_leds firmware.tests.codex_oai.test_keymap_contract -v`.

---

### Task 4: Update diagnostics documentation and run the complete verification gate

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/README.md`
- Modify: `docs/codex-oai-physical-runbook.md`
- Modify: `docs/codex-oai-prehardware-results.md`
- Modify: `firmware/evidence/codex-oai-emulator.json`
- Modify: `firmware/evidence/codex-oai-manifest.json`
- Modify: `release/firmware/prebuilt/agentpad13_codex_oai.uf2`

- [x] **Step 1: Document the visible sequence.**

State that after USB power-up LEDs 1→24 light one at a time in white for 80 ms each, then the whole chain flashes green twice; normal OAI/link/task rendering resumes after roughly 2.28 s. Explain that RGB remains runtime-enabled without an EEPROM write and that this does not prove host handshake or task semantics.

- [x] **Step 2: Run host, parser, and syntax checks.**

Run the full OAI `unittest` suite, `node --check firmware/tests/emulator/oai_runner.cjs`, `python3 -m py_compile` for tools/tests, and `git diff --check`.

- [x] **Step 3: Rebuild clean default/Vial/OAI artifacts.**

Run `firmware/tools/build_codex_oai.py --clean` against pinned QMK, then run the OAI emulator smoke and `verify_codex_oai_artifact.py`; record the new SHA/size and ensure the build reports `flash operations 0`.

- [x] **Step 4: Report physical next steps without claiming PASS.**

Give the user the expected LED timeline and ask them to observe all 24 positions, then separately test USB enumeration/handshake and key events. Keep physical rows pending until observed.

### Audit follow-ups completed during execution

- [x] Accept an empty `v.oai.thstatus` array as a valid no-op readiness
  handshake while retaining partial-update semantics.
- [x] Keep `TP_TOG` reachable through the shared touch gate after touch is
  disabled, so FN can re-enable it.
- [x] Restore the documented native NEW short/hold split: primary-modifier+N
  on a short release and Control+grave at `TAPPING_TERM` or later.
- [x] Record the exact rebuilt artifact, emulator evidence, physical runbook
  hash and audit limitations. No flash or USB write was performed.

# AgentPad13 Direct OAI Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import the complete AgentPad13 Direct OAI firmware, tests, emulator, evidence, and operating documentation into the current `yuz207/agentpad13` repository without regressing its protocol-v1 joystick calibration, touch fix, release layout, or default/Vial firmware.

**Architecture:** Direct OAI remains an isolated non-Vial keymap under `firmware/loudest_micro/keymaps/codex_oai/`. OAI-specific protocol/rendering code, host harnesses, build tools, and rp2040js runner are imported as self-contained units; only two narrow guards are added to the shared keyboard implementation so the OAI keymap can own Raw HID and RGB rendering while the existing default/Vial protocol-v1 implementation stays unchanged.

**Tech Stack:** QMK/Vial-QMK C firmware, RP2040 UF2, Python `unittest`, C host harnesses, Node.js/npm, rp2040js 1.3.3, POSIX shell, Markdown, GitHub pull requests.

**Spec:** `docs/superpowers/specs/2026-08-09-agentpad13-direct-oai-design.md`, `docs/superpowers/specs/2026-08-14-oai-led-fifo-design.md`, and `firmware/CODEX-OAI-SOURCE.md`.

## Global Constraints

- Base the PR branch `codex/import-direct-oai-firmware` on `yuz207/agentpad13:main` commit `a110994` or its fetched equivalent.
- Publish the branch only to `lop1381997/agentpad13`; target the PR at `yuz207/agentpad13:main`.
- Preserve the current default/Vial protocol v1, SW14 on-board joystick calibration, active-high TP5 implementation, encoder direction fix, and release artifact names.
- Keep Direct OAI isolated: no helper Python process, daemon, Vial protocol, or automatic flash operation in `codex_oai`.
- Preserve Direct OAI USB identity `303A:8360`, Raw HID usage `FF00:61`, Report ID `6`, and 64-byte reports.
- Store the Direct OAI release artifact as `release/firmware/prebuilt/agentpad13_codex_oai.uf2`; do not restore retired default/Vial `loudest_micro_*.uf2` names.
- Do not copy the excluded legacy-board project archive or any unrelated
  firmware into AgentPad13.
- Do not modify hardware, configurator, or existing default/Vial UF2 files. The sole permitted release-manifest change is the new OAI UF2 row and aggregate count/bytes required by `manifest_selfverify.py`.
- Do not mark physical checks PASS and do not flash hardware without the runbook's literal authorization.

---

### Task 1: Import the OAI tests first and establish RED

**Files:**
- Create: `firmware/tests/codex_oai/led_harness.c`
- Create: `firmware/tests/codex_oai/led_oracle.py`
- Create: `firmware/tests/codex_oai/protocol_harness.c`
- Create: `firmware/tests/codex_oai/protocol_oracle.py`
- Create: `firmware/tests/codex_oai/stubs/raw_hid.h`
- Create: `firmware/tests/codex_oai/stubs/wear_leveling.h`
- Create: `firmware/tests/codex_oai/test_artifact_verifier.py`
- Create: `firmware/tests/codex_oai/test_build_tool.py`
- Create: `firmware/tests/codex_oai/test_emulator_contract.py`
- Create: `firmware/tests/codex_oai/test_keymap_contract.py`
- Create: `firmware/tests/codex_oai/test_leds.py`
- Create: `firmware/tests/codex_oai/test_phase3_contract.py`
- Create: `firmware/tests/codex_oai/test_protocol.py`
- Create: `firmware/tests/codex_oai/test_rgb_cap.py`

**Interfaces:**
- Consumes the checked-in C implementation and release UF2 through repository-relative paths.
- Produces a self-contained `python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py'` gate.

- [ ] **Step 1: Copy only source tests and fixtures**

  Copy `.py`, `.c`, and `stubs/` files from the validated CodexMicroPad snapshot. Exclude `__pycache__/` and `*.pyc`.

- [ ] **Step 2: Adapt artifact paths before running**

  Replace the retired Direct OAI artifact path with the literal target path:

  ```python
  UF2 = REPO / "release" / "firmware" / "prebuilt" / "agentpad13_codex_oai.uf2"
  ```

  Update the phase-3 release contract and emulator package expectations to the same filename without weakening USB, hash, descriptor, or protocol assertions.

- [ ] **Step 3: Run the imported tests and verify RED**

  ```sh
  python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py'
  ```

  Expected: failures caused by the absent `codex_oai` keymap, OAI tools, OAI runner, and release UF2. Existing destination firmware is not changed to manufacture this failure.

- [ ] **Step 4: Commit the RED test contract**

  ```sh
  git add -- firmware/tests/codex_oai
  git commit -m "test: import AgentPad13 Direct OAI contracts"
  ```

### Task 2: Port the isolated Direct OAI firmware onto protocol v1

**Files:**
- Create: `firmware/loudest_micro/keymaps/codex_oai/README.md`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_led.c`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_led.h`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.c`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_rgb_cap.h`
- Create: `firmware/loudest_micro/keymaps/codex_oai/config.h`
- Create: `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- Create: `firmware/loudest_micro/keymaps/codex_oai/rules.mk`
- Create: `firmware/patches/0002-raw-hid-report-id-chibios.patch`
- Modify: `firmware/loudest_micro/loudest_micro.c`
- Test: `firmware/tests/codex_oai/test_keymap_contract.py`
- Create: `firmware/tests/codex_oai/calibration_rgb_harness.c`

**Interfaces:**
- `LOUDEST_CUSTOM_RAW_HID` makes the shared protocol-v1 handler compile out only for `codex_oai`.
- `LOUDEST_CUSTOM_RGB_STATUS` delegates `rgb_matrix_indicators_advanced_kb()` to the keymap renderer only for `codex_oai`.
- Default and Vial builds continue compiling the current protocol-v1 code paths.

- [ ] **Step 1: Import the isolated keymap and descriptor patch**

  Copy the nine `codex_oai` keymap files and `0002-raw-hid-report-id-chibios.patch` byte-for-byte from the validated source snapshot.

- [ ] **Step 2: Add the minimum shared ownership guards**

  Change the existing shared include and Raw HID block to:

  ```c
  #if defined(RAW_ENABLE) && !defined(LOUDEST_CUSTOM_RAW_HID)
  #    include "raw_hid.h"
  #endif
  ```

  Guard all shared Raw-HID protocol-v1 state and handlers with `!defined(LOUDEST_CUSTOM_RAW_HID)` while leaving joystick calibration, TP5 scanning, SW14 handling, and default/Vial behavior byte-for-byte unchanged inside their existing path.

  Change RGB ownership to:

  ```c
  #if defined(RGB_MATRIX_ENABLE) && defined(LOUDEST_CUSTOM_RGB_STATUS)
  bool rgb_matrix_indicators_advanced_kb(uint8_t led_min, uint8_t led_max) {
      return rgb_matrix_indicators_advanced_user(led_min, led_max);
  }
  #elif defined(RGB_MATRIX_ENABLE)
  // existing protocol-v1 renderer, unchanged
  #endif
  ```

- [ ] **Step 3: Keep TP_TOG reachable while disabled**

  Change the shared touch gate to allow the toggle key itself through:

  ```c
  if (record->event.key.row == TOUCH_MATRIX_ROW &&
      record->event.key.col == TOUCH_MATRIX_COL &&
      !touch_enabled && keycode != TP_TOG) {
      return false;
  }
  ```

- [ ] **Step 4: Run keymap, protocol, and LED tests**

  Add regression coverage for the destination's physical encoder direction and
  for the SW14 calibration overlay under custom RGB ownership. Keep the physical
  runbook read isolated to its runbook-specific assertion so all other keymap
  contracts execute before Task 4.

  ```sh
  python3 -m unittest \
    firmware.tests.codex_oai.test_keymap_contract \
    firmware.tests.codex_oai.test_protocol \
    firmware.tests.codex_oai.test_leds \
    firmware.tests.codex_oai.test_rgb_cap -v
  ```

  Expected: host protocol and LED harnesses pass; emulator/artifact tests remain red until Task 3 supplies their inputs.

- [ ] **Step 5: Commit the firmware port**

  ```sh
  git add -- firmware/loudest_micro/keymaps/codex_oai firmware/loudest_micro/loudest_micro.c firmware/patches/0002-raw-hid-report-id-chibios.patch
  git commit -m "feat: add AgentPad13 Direct OAI firmware"
  ```

### Task 3: Import reproducible build tools, emulator, evidence, and UF2

**Files:**
- Create: `firmware/tools/build_codex_oai.py`
- Create: `firmware/tools/verify_codex_oai_artifact.py`
- Create: `firmware/tests/emulator/oai_runner.cjs`
- Modify: `firmware/tests/emulator/get-bootrom.sh`
- Modify: `firmware/tests/emulator/package.json`
- Create: `firmware/evidence/README.md`
- Create: `firmware/evidence/codex-oai-emulator.json`
- Create: `firmware/evidence/codex-oai-current-manifest.json`
- Create: `firmware/evidence/codex-oai-manifest.json`
- Create: `release/firmware/prebuilt/agentpad13_codex_oai.uf2`
- Modify: `release/MANIFEST.md`

**Interfaces:**
- Builder publishes only `release/firmware/prebuilt/agentpad13_codex_oai.uf2`.
- `npm ci` generates a digest-verified `bootrom.cjs` through `postinstall`.
- `npm run smoke:codex-oai` reads the release UF2 and writes `firmware/evidence/codex-oai-emulator.json`.

- [ ] **Step 1: Import tools and OAI runner**

  Copy the two Python tools and `oai_runner.cjs`. Update builder/verifier
  constants, CLI help, test fixtures, and package scripts from the retired
  source filename to `agentpad13_codex_oai.uf2` at the release path.

- [ ] **Step 2: Merge npm scripts without regressing existing smoke fixtures**

  Preserve current protocol-v1 `smoke:default` and `smoke:vial` commands. Add:

  ```json
  "postinstall": "./get-bootrom.sh",
  "smoke:codex-oai": "node oai_runner.cjs ../../../release/firmware/prebuilt/agentpad13_codex_oai.uf2 --json ../../evidence/codex-oai-emulator.json"
  ```

  Use the pinned bootrom commit `7701ee065f50a04380f81361befd754810cb9e28` and source digest `99f8a1f813ce3aa9415884de3fb6c5b962d3c6fa0394b05413ad3c7b3c39ec62`.

- [ ] **Step 3: Import, rebuild, and normalize current evidence**

  Import the 92,160-byte OAI UF2 and emulator evidence as the migration baseline, then rebuild the final release UF2 from the reviewed destination source with pinned QMK `00fc4627` and Arm GNU 15.2. Regenerate emulator evidence and a current ELF/UF2 manifest for the rebuilt artifact. Preserve SHA-256 `d1768471eef4d0be12c1fc264279f20b9a7d293ea902c0608ebcfb4643ae35be` in provenance as the superseded archive candidate, and label the older 92,672-byte manifest historical exactly as `firmware/evidence/README.md` does.

- [ ] **Step 4: Run clean-install and emulator gates**

  ```sh
  cd firmware/tests/emulator
  npm ci
  npm run smoke:codex-oai
  npm run smoke:default
  npm run smoke:vial
  cd ../../..
  ```

  Expected: all three smoke commands exit 0; OAI evidence reports `303a:8360`, `ff00:0061`, report ID 6, all three acknowledgements, AG00, task fragmentation, and WS2812 activity.

- [ ] **Step 5: Commit reproducibility assets**

  ```sh
  git add -- firmware/tools firmware/tests/emulator firmware/evidence release/firmware/prebuilt/agentpad13_codex_oai.uf2 release/MANIFEST.md firmware/tests/codex_oai
  git commit -m "test: add reproducible Direct OAI firmware validation"
  ```

### Task 4: Import and adapt all AgentPad13 Direct OAI documentation

**Files:**
- Create: `firmware/CODEX-OAI-SOURCE.md`
- Create: `docs/codex-oai-audit-2026-08-17.md`
- Create: `docs/codex-oai-physical-runbook.md`
- Create: `docs/codex-oai-pico-runbook.md`
- Create: `docs/codex-oai-prehardware-results.md`
- Create: `docs/superpowers/specs/2026-08-09-agentpad13-direct-oai-design.md`
- Create: `docs/superpowers/specs/2026-08-14-oai-led-fifo-design.md`
- Create: `docs/superpowers/plans/2026-08-09-agentpad13-direct-oai.md`
- Create: `docs/superpowers/plans/2026-08-14-agentpad-oai-keymap-rpc.md`
- Create: `docs/superpowers/plans/2026-08-14-agentpad-oai-two-layer-full.md`
- Create: `docs/superpowers/plans/2026-08-14-oai-led-fifo.md`
- Create: `docs/superpowers/plans/2026-08-17-codex-oai-startup-led-check.md`
- Modify: `README.md`
- Modify: `firmware/BUILD.md`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/README.md`

**Interfaces:**
- README links users to source, tests, build instructions, current evidence, and physical runbook.
- Documentation uses `agentpad13_codex_oai.uf2` and the release path consistently.

- [ ] **Step 1: Copy AgentPad13-only docs**

  Copy the direct-OAI audit, runbooks, prehardware results, plans, and specs.
  Exclude the legacy-board project archive and duplicate archived review diffs.

- [ ] **Step 2: Normalize project names and artifact paths**

  Replace the retired artifact path/name with `release/firmware/prebuilt/agentpad13_codex_oai.uf2`. Preserve the historical manifest disclaimer and all physical rows as PENDING.

- [ ] **Step 3: Extend current README and build guide**

  Add a concise `AgentPad13 Direct OAI` section after the existing firmware status. State that it is an experimental alternative target, not the normal `agentpad13.uf2`, and list the exact test command and evidence/runbook links.

- [ ] **Step 4: Verify links and forbidden legacy-board references**

  ```sh
  rg -n "loudest_micro_codex_oai[.]uf2|docs/codex-micro-project/(?:4by[3])|Codex Micro Lab MV[P]" \
    README.md firmware docs/codex-oai-* docs/superpowers
  ```

  Expected: no retired artifact path and no legacy-board project content in
  the imported AgentPad13 documentation; the USB product string
  `Codex Micro Lab OAI LED` remains allowed because it is part of the locked
  device identity.

- [ ] **Step 5: Commit documentation**

  ```sh
  git add -- README.md firmware/BUILD.md firmware/CODEX-OAI-SOURCE.md docs/codex-oai-* docs/superpowers
  git commit -m "docs: document AgentPad13 Direct OAI firmware"
  ```

### Task 5: Full verification, push, and draft pull request

**Files:**
- No expected source edits after verification.

**Interfaces:**
- Head: `lop1381997:codex/import-direct-oai-firmware`
- Base: `yuz207/agentpad13:main`

- [ ] **Step 1: Run the complete OAI suite**

  ```sh
  python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py'
  cd firmware/tests/emulator
  npm ci
  npm run smoke:codex-oai
  npm run smoke:default
  npm run smoke:vial
  cd ../../..
  git diff --check
  ```

- [ ] **Step 2: Run unaffected repository checks**

  ```sh
  python3 manifest_selfverify.py
  node --test configurator/tests/*.test.mjs
  ```

  Record the pre-existing `firmware/tests/conformance/run_conformance.py` failure separately if `daemon/loudestd` remains absent; do not claim this PR caused or fixed that baseline dependency.

- [ ] **Step 3: Inspect the exact PR diff**

  ```sh
  git status --short --branch
  git diff --stat origin/main...HEAD
  git diff --check origin/main...HEAD
  git log --oneline origin/main..HEAD
  ```

- [ ] **Step 4: Push only the feature branch to the fork**

  ```sh
  git push -u fork codex/import-direct-oai-firmware
  ```

- [ ] **Step 5: Create a draft PR against upstream main**

  Create exactly one draft pull request with base `yuz207/agentpad13:main` and
  head `lop1381997:codex/import-direct-oai-firmware`. The body must summarize
  firmware behavior, artifact hash, tests, baseline caveat, no-flash status,
  and explicit exclusion of unrelated legacy-board content.

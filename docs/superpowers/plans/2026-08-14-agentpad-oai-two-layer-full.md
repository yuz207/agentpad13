# AgentPad13 OAI Two-Layer Full Firmware Plan

> **Historical plan:** this records an intermediate two-layer design that was
> later extended and superseded. The current destination artifact is
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2`, 93,696 bytes, SHA-256
> `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`.
> Physical validation remains PENDING and no flash occurred.

**Goal:** Deliver a useful direct-OAI AgentPad13 firmware with exactly two
default layers, optional additional user layers, the Codex Micro native
fallback gestures, FIFO task LEDs, and a reproducible pre-hardware artifact.

**Target:** `loudest_micro:codex_oai` in the isolated
`codex/agentpad13-direct-oai` worktree.

**Architecture:** The first layer is `CODEX`, preserving the observed OAI
control layout. When the OAI handshake is ready it sends only OAI events; when
OAI is not ready it uses the corresponding Codex Micro native fallback actions.
The second layer is `FN`, with useful defaults but compile-time customization.
The layer engine is table-driven so adding `USER2`, `USER3`, or later layers
only extends the keymap table and count. SAFE/ACCEPT arming is stateful logic,
not a hidden third layer. Vial/helper remain the existing separate profile
because the OAI endpoint and Vial Raw HID contracts are incompatible.

**Tech Stack:** QMK C, direct Raw HID OAI protocol, 24-LED RGB renderer,
Python/C host harnesses, pinned QMK builder, rp2040js emulator.

## Global constraints

- Exactly two layers are enabled by default: `CODEX` and `FN`.
- Additional layers may be enabled later without changing the layer-cycle implementation.
- The short encoder click cycles all currently enabled layers; with defaults it is `CODEX ↔ FN`.
- A long encoder click remains the macOS/Windows persistence gesture.
- SAFE/ACCEPT is an internal state machine and must not create a third physical layer.
- The observed OAI framing, report ID 6, 64-byte report, VID:PID, control names, and six task slots remain unchanged.
- OAI-ready input emits OAI only; non-ready input may use native shortcuts, never both for one physical event.
- FIFO updates preserve task position; removal compacts; reactivation appends; full queues evict oldest.
- Default and Vial AgentPad keymaps and the helper are not modified by this goal.
- No flash, USB write, push, or remote release is part of implementation.
- The existing dirty worktree is preserved; only goal-scoped files may be staged.

## Functional contract

### CODEX layer

Physical positions retain the current OAI layout:

```text
AG00 AG01 AG02 AG03
AG04 AG05 ACT06 ACT07
ACT08 ACT09 ACT10 ACT12
ACT12 ENC   AG00(touch)
```

When OAI is ready, these produce only the allowlisted OAI controls. Before
readiness, the same positions use the native Codex fallback matrix:

```text
PREVIOUS NEXT NEW REVIEW
PLAN     IMPLEMENT REFACTOR TEST
ABORT    SAFE ACCEPT SEND
SEND     LAYER
```

Native fallback includes 600 ms ACCEPT protection, SAFE arming, 800 ms OS-mode
toggle/persistence, NEW hold Terminal fallback, and macOS/Windows shortcut
selection. This fallback is deliberately inactive while OAI is ready so an
OAI event is never duplicated by a native shortcut.

### FN layer

The default FN table provides F1–F12 on the twelve grid positions, F13–F23
plus a return key on the 2U position, and useful encoder actions. Users may
edit the table in `keymap.c`; no protocol or renderer source changes are
needed. Joystick mode/touch controls remain available through the existing
keyboard-level support and an explicitly documented FN mapping.

### Optional layers

The keymap declares a single layer-count constant and a table-driven click
cycle. A future `USER2` layer is added by extending the enum/table and the
count; no `switch` statement or safety code may assume there are exactly two.
The default build still compiles exactly two layers.

### LEDs and protocol

The direct OAI renderer retains six task contexts, effects 0–6, the blue
working pattern, action feedback, link state, global summary, underglow, power
cap, and 32-bit time rollover. FIFO order is renderer-owned. A valid repeated
`v.oai.rgbcfg` increments a handshake revision; keymap housekeeping clears FIFO
before the next task sync. Restart clears it through renderer initialization.

## Implementation tasks

### Task 1 — Freeze contracts and create RED tests

Files:

- `firmware/tests/codex_oai/test_keymap_contract.py`
- `firmware/tests/codex_oai/test_protocol.py`
- `firmware/tests/codex_oai/test_leds.py`
- `firmware/tests/codex_oai/led_oracle.py`
- `firmware/tests/codex_oai/led_harness.c`

Actions:

1. Add failing assertions for exactly two default layers, dynamic layer count,
   no `_CODEX_ARMED` keymap layer, and CODEX/FN click-cycle behavior.
2. Add failing tests for native fallback actions, 600 ms ACCEPT, SAFE release,
   NEW hold, OS persistence, and OAI-ready no-duplicate routing.
3. Add failing FIFO sequence tests for append, in-place update, removal,
   reactivation, full-queue eviction, explicit reset, and C/Python parity.
4. Add a failing handshake-revision test proving valid repeated `rgbcfg` resets
   FIFO while malformed frames do not.
5. Run the focused tests and record RED failures before changing production C.

### Task 2 — Implement two-layer table-driven keymap

Files:

- `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- `firmware/loudest_micro/keymaps/codex_oai/config.h`
- `firmware/loudest_micro/keymaps/codex_oai/rules.mk`

Actions:

1. Replace the single layout with `L_CODEX` and `L_FN` only.
2. Add `CODEX_LAYER_COUNT` and use it for the click-cycle helper.
3. Keep optional user layers compile-time extensible without enabling them in
   the default build.
4. Implement encoder click as a layer toggle/cycle and retain long-click OS
   persistence.
5. Implement the native fallback matrix as a separate action table, not as a
   second hidden layer.
6. Keep touch, joystick, RGB matrix, BOOTMAGIC, and direct OAI ownership
   isolated from default/Vial keymaps.

### Task 3 — Implement native fallback and safety state machine

Files:

- `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- `firmware/tests/codex_oai/` native harness/stubs as required

Actions:

1. Port the proven native shortcuts from `codex_micro_lab` without changing
   their key combinations.
2. Preserve `ACCEPT` short no-op, hold-at-least-600-ms one-shot Enter,
   SAFE-held arming, and SAFE-release clearing.
3. Preserve NEW short versus held Terminal behavior.
4. Persist macOS/Windows mode with the existing magic value and return to
   `L_CODEX` after a long encoder click.
5. Assert OAI-ready routing emits no native keycodes and non-ready routing emits
   no OAI frame for the same event.

### Task 4 — Finish FIFO renderer and handshake reset

Files:

- `firmware/loudest_micro/keymaps/codex_oai/codex_led.c`
- `firmware/loudest_micro/keymaps/codex_oai/codex_led.h`
- `firmware/loudest_micro/keymaps/codex_oai/codex_oai.c`
- `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`
- `firmware/loudest_micro/keymaps/codex_oai/keymap.c`

Actions:

1. Complete FIFO reconciliation and explicit reset API.
2. Add the handshake revision accessor and increment only after valid `rgbcfg`.
3. Reset FIFO before the first task sync after every new handshake revision.
4. Keep global-task preference, feedback, link indicator, underglow, effects,
   and brightness cap unchanged.

### Task 5 — Validate hardware-specific useful features

Files:

- `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- `firmware/tests/codex_oai/test_keymap_contract.py`
- `docs/codex-oai-pico-runbook.md`

Actions:

1. Preserve the AgentPad pin contract for 13 keys, encoder, touch, joystick,
   and WS2812 GP17.
2. Document which controls are OAI in CODEX and which are customizable in FN.
3. Keep joystick gamepad/arrows/scroll behavior useful without inventing OAI
   control names.
4. Keep Pico jumper tests and the future AgentPad physical matrix separate.

### Task 6 — Documentation and reproducible artifacts

Files:

- `firmware/loudest_micro/keymaps/codex_oai/README.md`
- `docs/codex-oai-prehardware-results.md`
- `firmware/evidence/codex-oai-manifest.json`
- `firmware/tools/build_codex_oai.py`
- `firmware/tools/verify_codex_oai_artifact.py`

Actions:

1. Document the two default layers, extension recipe, routing rule, safety
   gestures, FIFO semantics, and separate Vial/helper profile.
2. Build clean OAI, default, and Vial targets from the pinned QMK commit.
3. Verify descriptor, target, size, SHA-256, symbols, memory budgets, and no
   forbidden Vial/helper/EEPROM drift in the OAI driver.
4. Record that no flash occurred and leave physical rows pending.

### Task 7 — Final host/emulator gate

Run:

```sh
python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py' -v
node --check firmware/tests/emulator/oai_runner.cjs
npm run smoke:codex-oai --prefix firmware/tests/emulator
python3 -m py_compile firmware/tools/*.py
git diff --check
```

Then run the pinned artifact builder/verifier. A stale pre-FIFO UF2 cannot be
used as final evidence. No device operation is allowed in this task.

## Monday exit criteria

- Exactly two default layers are present and cycle correctly.
- Additional layers are structurally supported but disabled by default.
- Native fallback, ACCEPT/SAFE, NEW hold, OS persistence, reasoning, scroll,
  and volume are tested.
- OAI handshake, six task slots, controls, FIFO, and RGB renderer are tested.
- Default/Vial keymaps remain unchanged.
- Fresh final artifact has a matching manifest and emulator evidence.
- Physical installation and real matrix remain a separate authorized step when
  the AgentPad PCB arrives.

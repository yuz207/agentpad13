# AgentPad13 OAI LED FIFO Implementation Plan

> **Historical plan:** this dated implementation record preserves the FIFO
> design chronology. Any intermediate artifact status is superseded by
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2` (93,696 bytes, SHA-256
> `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`).
> Physical validation remains PENDING and no flash occurred.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution approved by the user) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the six active OAI tasks in first-activation FIFO order while preserving source-slot identity and direct-HID behavior.

**Architecture:** Keep `codex_oai.c` as the stable six-slot protocol store. Make `codex_led.c` reconcile source slots into its existing six LED contexts: remove inactive entries, update surviving entries in place, and append new entries with oldest-first eviction. Add a handshake revision from the OAI parser so the keymap can clear the LED projection whenever a valid RGB configuration handshake is repeated.

**Tech Stack:** C11 host harnesses, QMK C keymap, Python `unittest` oracle/parity suite, pinned ARM GCC/QMK build tooling, rp2040js emulator smoke.

## Global Constraints

- Do not change the OAI wire format, report ID, report size, VID:PID, or slot IDs.
- A task update preserves its current LED position; changing its content retains the existing animation-reset behavior.
- Deactivation compacts later entries; reactivation appends at the tail.
- When six entries are occupied, a newly active source slot evicts the oldest entry at LED0 and appends at LED5.
- Restart and every valid `v.oai.rgbcfg` handshake clear the FIFO before the next task sync.
- No firmware flash, USB write, commit to V1, or helper/Vial integration is part of this change.
- Preserve all pre-existing dirty user changes in the AgentPad13 worktree.

## File Map

- Modify `firmware/loudest_micro/keymaps/codex_oai/codex_led.c`: FIFO reconciliation and explicit reset API.
- Modify `firmware/loudest_micro/keymaps/codex_oai/codex_led.h`: expose reset API.
- Modify `firmware/loudest_micro/keymaps/codex_oai/codex_oai.c`: handshake revision counter and increment on valid `v.oai.rgbcfg`.
- Modify `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`: expose the handshake revision accessor and make the default source-slot count overrideable for the isolated capacity test while retaining the production default of six.
- Modify `firmware/loudest_micro/keymaps/codex_oai/keymap.c`: track handshake revision and clear LED FIFO before syncing after a new handshake.
- Modify `firmware/tests/codex_oai/led_oracle.py`: independent FIFO model and reset operation.
- Modify `firmware/tests/codex_oai/led_harness.c`: add an explicit task-clear command while retaining existing task commands.
- Modify `firmware/tests/codex_oai/test_leds.py`: FIFO sequence, eviction, reset, and C/Python parity tests.
- Modify `firmware/tests/codex_oai/protocol_harness.c`: print handshake revision.
- Modify `firmware/tests/codex_oai/test_protocol.py`: valid/invalid handshake revision coverage.
- Modify `firmware/tests/codex_oai/test_keymap_contract.py`: assert handshake reset wiring.
- Modify `firmware/loudest_micro/keymaps/codex_oai/README.md`: document LED FIFO semantics and reset trigger.
- Modify `docs/codex-oai-prehardware-results.md`: record host-only FIFO verification and hardware as pending.

---

### Task 1: Add failing FIFO behavior tests

**Files:**
- Modify: `firmware/tests/codex_oai/test_leds.py`
- Modify: `firmware/tests/codex_oai/led_oracle.py`
- Modify: `firmware/tests/codex_oai/led_harness.c`

**Interfaces:**
- The test harness continues to send `TASK <slot> <active> <rgb> <effect> <brightness> <speed> <flags> <now>` snapshots.
- Add `CLEAR <now>` to call `codex_led_reset_tasks(now)` in the C harness.

- [ ] **Step 1: Write tests that express FIFO order and eviction.**

Add tests with distinct solid task colors and these exact sequences:

```python
def test_new_tasks_append_in_activation_order_and_updates_keep_position(self):
    tasks = [led_oracle.task(slot=i) for i in range(6)]
    tasks[3] = led_oracle.task(slot=3, rgb=(255, 0, 0), effect=1)
    renderer.set_tasks(tasks, 1 << 3, 0)
    tasks[1] = led_oracle.task(slot=1, rgb=(0, 255, 0), effect=1)
    renderer.set_tasks(tasks, (1 << 3) | (1 << 1), 10)
    tasks[3] = led_oracle.task(slot=3, rgb=(0, 0, 255), effect=1)
    renderer.set_tasks(tasks, (1 << 3) | (1 << 1), 20)
    self.assertEqual(renderer.source_slots(), [3, 1])

def test_remove_compacts_and_reactivation_goes_to_tail(self):
    self.assertEqual(self._fifo_sources([(3, True), (1, True), (3, False), (3, True)]), [1, 3])

def test_full_fifo_evicts_oldest_before_appending_new_source(self):
    # This test uses the same harness compiled with OAI_SLOT_COUNT=8.
    self.assertEqual(self._fifo_sources_with_eight_sources(range(7)), [1, 2, 3, 4, 5, 6])
```

The normal target remains six OAI source slots. The capacity test uses a
test-only compile of the same renderer with `-DOAI_SLOT_COUNT=8`; the public
header makes the default overrideable without changing the production value.
Assert LED positions by rendering at a timestamp where each solid task is fully
lit, and expose `source_slots()` only from the Python oracle test helper rather
than from production firmware.

- [ ] **Step 2: Run the new tests before implementing FIFO.**

Run:

```bash
python3 -m unittest firmware.tests.codex_oai.test_leds.LedParityTest -v
```

Expected: the new FIFO assertions fail against the existing source-slot-to-LED
mapping, while the pre-existing animation/link tests remain understandable.

- [ ] **Step 3: Add the explicit C-harness reset command test.**

Send `CLEAR 500` after activating a task and assert all task LEDs are black in
the C frame. Keep the production reset function absent at this point so this
test is also RED for the missing interface.

---

### Task 2: Implement the minimal renderer FIFO

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_led.c`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_led.h`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`
- Modify: `firmware/tests/codex_oai/led_harness.c`

**Interfaces:**
- Produce `void codex_led_reset_tasks(uint32_t now_ms);`.
- Preserve `codex_led_set_tasks(const codex_oai_task_t *, uint8_t, uint32_t)`.

- [ ] **Step 1: Implement `codex_led_reset_tasks`.**

Clear `tasks_by_led`, zero each task, set `active = false`, and set every
`pattern_start_ms` to `now_ms`. Call it from `codex_led_init` after feedback and
link initialization.

- [ ] **Step 2: Make the source-slot count overrideable without changing its default.**

Change the public definition to:

```c
#ifndef OAI_SLOT_COUNT
#    define OAI_SLOT_COUNT 6
#endif
```

The normal firmware and protocol remain six-slot builds; only the isolated
renderer capacity test compiles with eight source slots.

- [ ] **Step 3: Implement source-slot lookup and FIFO reconciliation.**

For each current LED context:

1. Find the matching source slot in the incoming active mask.
2. Remove contexts whose source slot is absent by shifting later contexts left.
3. For remaining contexts, replace changed task data in place and reset only
   that context's `pattern_start_ms` when data differs.
4. Append every active source slot not already present. If six contexts are
   occupied, shift `[1..5]` to `[0..4]` and append at index 5.
5. Zero all unused tail contexts.

Do not derive FIFO order from numeric source-slot order; scan source slots only
when discovering entries that are absent from the existing queue.

- [ ] **Step 4: Wire `CLEAR` in the C harness.**

Parse `CLEAR <now>` and call `codex_led_reset_tasks((uint32_t)now)`, then run
the focused LED tests.

- [ ] **Step 5: Run the focused tests green.**

Run:

```bash
python3 -m unittest firmware.tests.codex_oai.test_leds -v
```

Expected: all LED tests pass, including C/Python parity for FIFO order,
compaction, tail reactivation, eviction, reset, animation, feedback, and
underglow.

- [ ] **Step 6: Commit the renderer slice.**

```bash
git add firmware/loudest_micro/keymaps/codex_oai/codex_led.c \
  firmware/loudest_micro/keymaps/codex_oai/codex_led.h \
  firmware/loudest_micro/keymaps/codex_oai/codex_oai.h \
  firmware/tests/codex_oai/led_oracle.py \
  firmware/tests/codex_oai/led_harness.c \
  firmware/tests/codex_oai/test_leds.py
git commit -m "feat: project AgentPad OAI tasks through FIFO LEDs"
```

---

### Task 3: Add handshake-triggered FIFO reset

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.c`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- Modify: `firmware/tests/codex_oai/protocol_harness.c`
- Modify: `firmware/tests/codex_oai/test_protocol.py`
- Modify: `firmware/tests/codex_oai/test_keymap_contract.py`

**Interfaces:**
- Produce `uint8_t codex_oai_handshake_revision(void);`.

- [ ] **Step 1: Add a RED protocol test.**

Extend `Snapshot` and the harness parser with `HANDSHAKE_REVISION`. Assert:

```python
before = harness.snapshot().snapshot.handshake_revision
harness.rpc(b'{"method":"v.oai.rgbcfg","id":9,"params":{}}')
after = harness.snapshot().snapshot.handshake_revision
self.assertEqual(after, (before + 1) & 0xFF)
```

Also send a malformed frame and assert the counter does not change.

- [ ] **Step 2: Run the protocol test and observe the expected failure.**

```bash
python3 -m unittest firmware.tests.codex_oai.test_protocol.ProtocolParityTest -v
```

Expected: harness output lacks the new field/accessor.

- [ ] **Step 3: Implement the revision counter.**

Initialize `handshake_revision` to zero in `codex_oai_init`, increment it only
after a successfully parsed `v.oai.rgbcfg` request, and expose the wrapping
`uint8_t` accessor. Invalid requests must not increment it.

- [ ] **Step 4: Reset the renderer from keymap housekeeping.**

Track `oai_handshake_revision` beside state/error revisions. Initialize it in
`keyboard_post_init_user`. In `housekeeping_task_user`, when it changes, call
`codex_led_reset_tasks(now_ms)` before `sync_oai_leds(now_ms)`; then update the
tracked value. Keep the existing state/error/link conditions unchanged.

- [ ] **Step 5: Add a static keymap contract assertion.**

Assert that the keymap declares the handshake revision tracker, calls
`codex_oai_handshake_revision()`, and invokes `codex_led_reset_tasks` before
syncing after revision changes.

- [ ] **Step 6: Run focused protocol/keymap tests and commit.**

```bash
python3 -m unittest firmware.tests.codex_oai.test_protocol firmware.tests.codex_oai.test_keymap_contract -v
git diff --check
git add firmware/loudest_micro/keymaps/codex_oai/codex_oai.c \
  firmware/loudest_micro/keymaps/codex_oai/codex_oai.h \
  firmware/loudest_micro/keymaps/codex_oai/keymap.c \
  firmware/tests/codex_oai/protocol_harness.c \
  firmware/tests/codex_oai/test_protocol.py \
  firmware/tests/codex_oai/test_keymap_contract.py
git commit -m "feat: clear LED FIFO on OAI handshake"
```

---

### Task 4: Document and run the complete host regression

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/README.md`
- Modify: `docs/codex-oai-prehardware-results.md`

- [ ] **Step 1: Document the FIFO contract.**

Update the LED table to say LEDs 0–5 are FIFO projection positions, add the
activation/update/removal/eviction rules, and state that restart or a repeated
valid RGB configuration handshake clears the queue.

- [ ] **Step 2: Record host-only verification.**

Add a dated entry naming the focused FIFO tests, protocol handshake revision
tests, full host count, and explicit `flash_operations: 0`. Keep physical rows
pending because this change is not flashed.

- [ ] **Step 3: Run all required verification.**

Run from the AgentPad13 worktree:

```bash
python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py' -v
node --check firmware/tests/emulator/oai_runner.cjs
npm run smoke:codex-oai
python3 -m py_compile firmware/tools/build_codex_oai.py firmware/tools/verify_codex_oai_artifact.py
git diff --check
```

Then run the pinned build/evidence verifier. If the disposable QMK clone or
UF2 gate is unavailable, report that exact external block and do not invent a
new artifact or flash.

- [ ] **Step 4: Commit documentation and final report.**

```bash
git add firmware/loudest_micro/keymaps/codex_oai/README.md \
  docs/codex-oai-prehardware-results.md
git commit -m "docs: record AgentPad OAI LED FIFO verification"
```

---

## Final Checklist

- [ ] FIFO tests fail before implementation and pass after it.
- [ ] C renderer and independent Python oracle agree on all FIFO sequences.
- [ ] Updates preserve position; removal compacts; reactivation appends; full queue evicts oldest.
- [ ] Restart and repeated valid handshake clear the projection.
- [ ] Existing protocol, animation, global/underglow, emulator, and artifact gates remain green.
- [ ] No flash, USB write, V1 change, helper integration, or push occurred.

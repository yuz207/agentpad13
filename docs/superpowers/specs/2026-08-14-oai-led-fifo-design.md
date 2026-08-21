# AgentPad13 OAI LED FIFO Design

> **Historical design record:** this preserves the approved FIFO contract.
> Artifact status from this phase is superseded by
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2` (93,696 bytes, SHA-256
> `fcb50b2419419be43b7cf90b00a96b16063fcaf182bc24b9642d57e2e8adf54d`).
> Physical validation remains PENDING and no flash occurred.

## Goal

Project active OAI tasks on the six task LEDs in first-activation order while
keeping each task's source slot stable in the OAI protocol.

## Approved behavior

- The LED projection is a FIFO queue with a maximum of six entries.
- A newly visible source slot is appended to the tail.
- Updating an already-visible source slot updates its task in place and keeps
  its LED position. Existing animation-reset behavior on task-content change
  is retained.
- Deactivating a source slot removes it and compacts later entries toward LED0.
- Reactivating a previously removed source slot appends it to the tail.
- If all six positions are occupied, activating a new source slot evicts LED0
  (the oldest entry), shifts the remaining entries left, and appends the new
  entry at LED5.
- Firmware restart clears the queue. A new successful OAI RGB configuration
  handshake also clears the queue before the next task snapshot is rendered.
- The task's `source_slot` remains unchanged; only the LED projection order is
  changed. Global-task selection and underglow continue to use the projected
  entries, including the existing preference for a working task.

## Architecture

The FIFO lives in `codex_led.c`, where `tasks_by_led` already represents the
rendered six-position projection. `codex_led_set_tasks()` reconciles the
source-slot snapshot against that projection: remove missing slots, update
survivors in place, then append newly active slots with oldest-first eviction.
No OAI wire format or slot API changes are required.

The OAI parser exposes a monotonically wrapping handshake revision incremented
after each valid `v.oai.rgbcfg` request. The keymap tracks that revision and
calls `codex_led_reset_tasks()` before syncing the first task snapshot after a
new handshake. This handles a repeated handshake even when the task values
themselves are unchanged.

## Data flow

```text
OAI source slots (stable IDs)
        |
        | active snapshot + source_slot
        v
codex_led_set_tasks()
  remove inactive -> update in place -> append/evict
        |
        v
LED0..LED5 FIFO projection -> global/underglow renderer
```

## Error and reset behavior

- Invalid OAI requests do not change the handshake revision or FIFO.
- A valid RGB configuration request increments the handshake revision even if
  the device was already ready; this is the reset trigger.
- A reset empties all six contexts, clears their task values, and sets their
  animation start timestamps to the supplied time.
- Existing link-state, action-feedback, and animation contracts remain intact.

## Tests and acceptance

The C harness and independent Python oracle will cover:

1. first activation order;
2. update-in-place position preservation;
3. removal/compaction and reactivation-at-tail;
4. full-queue oldest eviction;
5. explicit renderer reset;
6. C/Python frame parity for those sequences;
7. handshake revision increment and keymap reset wiring.

The existing host suite, emulator smoke tests, static checks, and pinned
artifact gates must remain green. This change does not authorize flashing.

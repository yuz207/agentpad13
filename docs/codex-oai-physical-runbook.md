# AgentPad13 direct OAI — physical verification runbook

This runbook is for the future, after the direct-OAI artifact has passed its
isolated build, emulator smoke and artifact-verifier gates. It deliberately
contains no automatic installation action. Do not proceed from this document
alone.

## Required authorization before a hardware operation

Obtain a literal approval that contains all three values below, with the real
artifact digest substituted for `<sha256>`:

```text
AUTORIZO <N> FLASH(ES) DE loudest_micro:codex_oai SHA-256 <sha256>
```

The authorization must state the exact target (`loudest_micro:codex_oai`),
the exact SHA-256 of the current UF2 recorded in
`firmware/evidence/codex-oai-emulator.json` and
`firmware/evidence/codex-oai-current-manifest.json` (or in a newly generated
verifier manifest for that same UF2), and the number of flashes. The checked-in
`firmware/evidence/codex-oai-manifest.json` is historical evidence for an older
artifact and must not authorize this candidate. A changed hash, target or
number requires a new approval. Keep the normal AgentPad13 UF2 available for
recovery. No physical check is PASS until a person has observed it on the
board.

Current build candidate (still unflashed):
`release/firmware/prebuilt/agentpad13_codex_oai.uf2`, UF2 `93696` bytes,
SHA-256
`64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`.

## Pre-flight, manual only

1. Confirm the generated direct-OAI UF2 and current emulator evidence JSON are
   regular files and their size/hash agree. If a clean ARM build produced an
   ELF, also confirm the artifact verifier produced a PASS manifest for this
   exact UF2; never substitute the historical manifest.
2. Record the target, UF2 SHA-256, byte size, timestamp and approved number
   of flashes in the test log.
3. Confirm the intended test computer has Codex Desktop available and that no
   normal AgentPad13/Vial session is using the device.
4. Use the approved recovery route only if it is necessary. This runbook does
   not provide an installation command.

## Physical matrix

| Check | Status | Observation to record |
|---|---|---|
| BOOTSEL recovery | PENDING | Recovery route works and normal firmware can be restored. |
| USB 303A:8360 / FF00:61 / report 6 | PENDING | Host observes the expected keyboard plus Raw HID endpoint. |
| rgbcfg + thstatus + device.status | PENDING | The three OAI RPC acknowledgements arrive once and readiness changes; an empty `thstatus` array is a valid no-op handshake. |
| power-on LED sweep 1→24 | PENDING | White dot visits every LED in chain order, then two green completion flashes. |
| CODEX boot layer | PENDING | After the 2.28-second sweep, LED 13 is red and the active layer is CODEX/OAI even if FN/NAV/MEDIA was active before USB was disconnected. TP5 is deliberately ignored during that sweep, then resumes its normal cycle. |
| keymap.get default | PENDING | `123456789abfcd1` is returned for layer 0; positions 0–12 follow `AG00..AG05`, `ACT06..ACT12`, with the encoder at position 13. |
| keymap.set + persistence | PENDING | A valid 15-digit map ACKs, survives reconnect, and invalid maps are rejected atomically. |
| AG00..AG05 | PENDING | Each grid agent key produces its matching press notification; release remains intentionally silent. |
| ACT06..ACT12 | PENDING | Matrix/function positions produce their matching press/release notifications; ACT10 is protected ACCEPT, ACT11 is the second microphone contact, and ACT12 is SEND. |
| ENC / ENC_CW / ENC_CC | PENDING | Encoder press and both directions produce the allowlisted notifications. |
| TP5 layer cycle + indicator | PENDING | A tap cycles `CODEX -> FN -> NAV -> MEDIA -> CODEX` without an OAI control; LED 13 changes red/yellow/green/cyan after the OAI link is ready. |
| native NEW short/hold fallback | PENDING | Before OAI readiness, short release produces primary-modifier+N; hold ≥ `TAPPING_TERM` produces Control+grave once. |
| FN F2 and NAV TP_TOG | PENDING | FN emits F2; `TP_TOG` is on NAV so touch can be disabled and re-enabled without losing the layer-cycle mapping. |
| slot LEDs 0..5 | PENDING | Six independent task slots show their received RGB/effect states. |
| action LEDs 6..12 | PENDING | Physical function keys at positions 6..12 flash white for approximately 160 ms; AG00..AG05 task positions do not flash. |
| TP5/layer LED 13 | PENDING | The LED always identifies CODEX/FN/NAV/MEDIA as red/yellow/green/cyan, including before OAI readiness or after an error; optional animation may only pulse brightness. |
| underglow 14..23 | PENDING | Underglow follows the selected/working task at reduced intensity. |
| restore normal firmware | PENDING | Approved normal default or Vial firmware is restored and re-enumerates normally. |

## Suggested observation order

1. Start with USB enumeration: verify `303A:8360`, Raw HID `FF00:61`, Report
   ID 6 and 64-byte reports before pressing controls.
2. Power-cycle the keyboard and observe the one-shot LED self-check: LEDs
   1–24 must light in physical chain order for about 80 ms each, followed by
   two green full-chain flashes. Record missing, reversed, or dark positions;
   this check is local and does not require the OAI host handshake.
3. Send `v.oai.rgbcfg`, `v.oai.thstatus` and `device.status`. Confirm that
   the link changes from waiting to ready and that the three acknowledgements
   are observed.
4. Test AG keys, matrix ACT keys, the separate 2U ACT12/SEND key, encoder
   press/rotation and touch; record press and release notifications separately
   where applicable. Confirm matrix key 11 keeps its protected ACCEPT timing,
   matrix key 12 emits ACT11, and the 2U emits ACT12/SEND.
5. Exercise task data for slots 0–5 and inspect their LEDs, action feedback,
   link state and underglow.
6. Test the error path using malformed or incomplete protocol input only in a
   controlled host tool; verify LED 13 indicates error and recovers after a
   valid readiness handshake.
7. Restore normal firmware only under its own explicit approval, then record
   normal AgentPad13 enumeration and function.

## Completion record

Do not change a row from PENDING without the date, observer, artifact SHA-256,
host application version and a concise observed result. Attach the Raw HID
capture or equivalent host log for each transport claim. If a row fails,
leave the artifact and recovery image available, record the failure, and stop
before any additional unapproved hardware operation.

Current state: all physical rows are **PENDING**. There have been no automatic
installations from this keymap or runbook.

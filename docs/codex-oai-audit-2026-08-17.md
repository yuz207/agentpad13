# AgentPad13 direct OAI audit — 2026-08-17

> **Historical audit:** this dated record preserves the conclusions and
> candidate facts observed during the original AgentPad13 work. Its artifact
> values are superseded. The current destination release is
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2`, 93,696 bytes, SHA-256
> `fcb50b2419419be43b7cf90b00a96b16063fcaf182bc24b9642d57e2e8adf54d`.
> Current physical validation remains PENDING; no flash occurred.

## Scope and verdict

The audit covers every implementation commit after the AgentPad13 baseline
(`a391068`) through the latest `dev` commit (`e435915`), plus the current
working-tree changes for the power-on LED check and protocol/touch fixes. There
is no merge commit in this history; “last merge” is therefore treated as the
latest `dev` integration.

**Software verdict:** the direct-OAI firmware should work on the AgentPad13
v5 PCB, whose pin map is documented as unchanged from Rev A/v4_r27, when the
new UF2 is built and the host opens the exact OAI HID interface. The host-side
and emulator gates are green. **Hardware verdict:** not proven yet. A physical
flash and every control/LED row are still pending, so the previous poor F2
observation cannot be called a firmware failure or a hardware pass from this
evidence alone.

## Functional inventory

| Area | Implemented behavior | Evidence / confidence |
|---|---|---|
| USB identity | `303A:8360`, product `Codex Micro Lab OAI LED`, usage `FF00:61`, Report ID 6, 64-byte reports | Clean build, descriptor verifier and RP2040 emulator PASS. |
| Direct transport | Raw HID JSON framing/reassembly, bounded parser, allowlisted replies, no helper/Vial route | C/Python parity tests and OAI emulator PASS. The target deliberately disables VIA/Vial. |
| Readiness | Controls stay quiet until valid `rgbcfg` and `thstatus`; `device.status` ACKs | Host and emulator PASS. Empty `thstatus: []` is now a valid no-op; older images rejected it. |
| Six task slots | RGB, effect, brightness, speed and flags retained; partial updates; FIFO projection, oldest eviction and working-task preference | C/Python renderer/protocol parity PASS. |
| Task LED renderer | LEDs 0–5 slots; 6–12 action feedback; 13 TP5/layer indicator (always CODEX/FN/NAV/MEDIA colour, with link tint/pulse); 14–23 dim global task; steady state by default with optional compile-time animation | 24-frame C/Python LED suite PASS, including four-layer indicator parity. Physical mapping remains unobserved. |
| Startup diagnostic | White dot visits chain indexes 0→23 at 80 ms; two green full-chain flashes; one-shot, no EEPROM writes; RGB remains runtime-enabled afterward | C/Python parity and keymap contract PASS. Requires the 24-pixel WS2812 chain; a bare Pico onboard LED is not part of this path. |
| CODEX layer | 15-position runtime map with a legacy reserved TP5 slot; native fallback before handshake; OAI notifications after handshake; matrix key 11 is protected ACCEPT, matrix key 12 is ACT11 (the second microphone contact), and the separate 2U key is ACT12/SEND | Static keymap contract, protocol and emulator AG00 event PASS. Physical matrix pending. |
| FN/layer navigation | F2–F12, joystick mode, media controls; four default layers (`CODEX`, `FN`, `NAV`, `MEDIA`) cycled by TP5 only; human layer 1/QMK index 0 is forced to OAI on boot | Static contract and clean build PASS. Actual F2/touch/layer observations remain pending. |
| Encoder | Click emits `ENC` when ready; it never changes layers or toggles OS mode; rotation emits `ENC_CW`/`ENC_CC` in CODEX and native scroll/media behavior on auxiliary layers | Source contracts and build PASS; direction/gesture timing physically pending. |
| ACCEPT/SAFE/NEW | Native fallback has short ACCEPT suppression, ≥600 ms one-shot release, SAFE arming/release clear, and NEW short/hold split | Static contract and clean build PASS; physical timing remains pending. |
| Keymap RPC | `v.oai.keymap.get/set`, 15 hex positions, validation, atomic update and RP2040 wear-leveling persistence | 75-test host suite PASS; no helper/Vial required. |
| Touch/joystick | TP5 cycles layers; `TP_TOG` remains on NAV; joystick supports native gamepad plus arrow/scroll modes | Build/static coverage. Touch/layer timing and joystick center/direction are still calibration items. |
| Default/Vial isolation | Existing `default`/`vial` keymap files and `keyboard.json` have no source drift from the baseline; shared touch gate now lets `TP_TOG` re-enable | Clean builds and both emulator smokes PASS. |
| Function-key feedback | Physical positions 6–12 flash white for 160 ms on press; task positions 0–5 never flash, even under custom OAI maps | Static physical-position gate, C/Python LED parity and clean build PASS. Physical observation pending. |
| Reproducibility/safety | Pinned QMK, VIA and ChibiOS descriptor patches, clean builds, artifact SHA/size/symbol gates, no device-write code path | Builder, verifier, 78 tests and `flash_operations: 0` PASS. |

The legacy `firmware/tests/conformance/run_conformance.py` was also attempted,
but it imports the historical `daemon/loudestd` tree, which is not present in
this AgentPad13 worktree. That is an external/legacy test dependency, not a
failure of the direct-OAI parser; the self-contained C/Python OAI suite is the
authoritative protocol gate for this target.

## Why an earlier F2 attempt may have looked bad

1. The previously flashed `20f475...` image predates the startup check and the
   empty-`thstatus` fix. A host that sends `params: []` could receive an ACK
   while the firmware stayed not-ready, leaving OAI controls quiet.
2. The direct target has no helper process and no Vial protocol. Codex Desktop
   must open `303A:8360`, usage `FF00:61`, Report ID 6; opening the normal
   AgentPad/Vial HID endpoint will not drive this keymap.
3. The emulator proves descriptor/framing and a synthetic AG00 event, not the
   assembled PCB's switch, encoder, touch or LED wiring. F2 is present in the
   FN source map, but only a physical key press can prove its report.
4. The startup pattern is visible only on the AgentPad13 WS2812 chain at GP17.
   A bare RP2040 Pico's onboard GP25 LED is not connected to that chain and is
   intentionally not claimed as evidence for the 24-LED check.

The observed combination “keys follow the Codex Micro configuration, but the
LEDs are dark” is consistent with the first startup implementation: it enabled
RGB for the sweep and then restored an EEPROM-disabled RGB state, which also
prevented later task/link frames from being rendered. The current working-tree
fix keeps RGB enabled with `rgb_matrix_enable_noeeprom()` after the sweep, so
task LEDs remain visible without changing EEPROM. The renderer also holds task
and link colours steady until their state changes, so idle hardware has no
background blink. The legacy effect timing remains available only via the
explicit `CODEX_LED_ANIMATION_ENABLE=1` build option, where it is rendered as a
slow non-zero fade; the shipped/default image leaves it disabled. It is included in the new artifact below and still
requires a physical observation.

## Historical audit artifact and required next observation

The exact rebuilt artifact at the time of this audit was 92,160 bytes, SHA-256
`0b2c9afc5bc1294d232aa1c711c471b37e7ffbce34766608220267c0aff3cc68`.
It is retained only as superseded provenance; it is not the current release
candidate named in the banner above.
No flash is authorized by this audit. Before writing hardware, obtain a new
literal approval containing this target, byte count/hash and flash count.
After an authorized flash:

1. Power-cycle and watch the one-shot 1→24 sweep. Record missing, reversed or
   dark positions; this is the first PCB integrity check.
2. Confirm USB identity and the three handshake ACKs, including an empty
   `thstatus` if the host sends one.
3. Test F2, encoder click/rotation, TP5 layer cycling and its layer LED, AG/ACT controls and task
   notifications; capture host events rather than inferring them from LEDs.
4. Exercise task slots and verify FIFO position, link LED, action feedback and
   underglow. Leave any unobserved row PENDING.

Until those observations exist, the correct conclusion is **“software is
ready for a controlled hardware test; physical functionality is unverified.”**

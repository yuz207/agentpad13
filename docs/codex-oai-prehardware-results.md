# AgentPad13 direct OAI — pre-hardware results

> **Historical chronology:** the dated sections below retain the exact host,
> build, emulator, and artifact facts recorded at each stage. Every use of
> “current” inside those sections means current at that dated stage and is
> superseded by the destination port rebuild. The current release is
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2`, 93,696 bytes, SHA-256
> `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`.
> All physical observations remain PENDING and no flash occurred.

This is a reproducible pre-hardware record for the isolated `codex_oai`
laboratory keymap. It records what was actually verified locally as of the
AgentPad13 commit below. It does not claim that an unbuilt artifact was
validated and it does not authorize a hardware operation.

## Revision and toolchain

| Item | Recorded value |
|---|---|
| AgentPad13 implementation revision | `bc437a66616edfcec20da4b5f9b70d3e50b813bc` |
| Required Vial-QMK revision | `00fc4627cd038ac9b7e9b8bf2b40b50e9e88aecb` |
| ARM compiler | `arm-none-eabi-gcc (Homebrew ARM GCC 8.5.0_2) 8.5.0` |
| Direct target | `loudest_micro:codex_oai` |
| USB / Raw HID contract | `303A:8360`, `FF00:61`, Report ID 6, 64 bytes |
| flash_operations | `0` |

## Reproduce the host checks

Run these commands from the repository root. They are host-only checks; none
connects to or writes a physical keyboard.

```bash
python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py' -v
cd firmware/tests/emulator && npm run smoke:default && npm run smoke:vial
git diff --check
```

Recorded exits on the revision above:

| Check | Result | Exact count / exit |
|---|---|---|
| OAI host suites | PASS | 36 tests run; 35 passed, 1 expected skip; exit 0 |
| Default RP2040 emulator smoke | PASS | USB, matrix, Raw HID v0 and WS2812 evidence; exit 0 |
| Vial RP2040 emulator smoke | PASS | USB, matrix, Raw HID v0 and WS2812 evidence; exit 0 |
| Diff whitespace check | PASS | exit 0 |

The expected skip is intentional: it is the direct-OAI emulator evidence test
and says that the then-planned Direct OAI UF2 had not yet been produced. The
static OAI report-wrapper and endpoint test still runs.

## Final pre-hardware verification — 2026-08-09

The final host pass was run against implementation revision
`bc437a66616edfcec20da4b5f9b70d3e50b813bc`. It is **not yet a complete
software validation**: the isolated QMK build gate below remains externally
blocked, so no UF2, emulator handshake evidence, or verifier manifest exists.

| Design validation requirement | Result | Evidence from this pass |
|---|---|---|
| 1. OAI parser, reassembly, bounds, readiness and responses | PASS | `test_protocol.py` ran in the 36-test host suite. |
| 2. Byte-for-byte C/Python protocol parity | PASS | handshake, allowlist and malformed-frame parity checks passed. |
| 3. Fifteen physical inputs are allowlisted only | PASS (static) | keymap contract test passed; it checks all 15 positions and encoder routes. Physical observation remains PENDING. |
| 4. Six slots retain RGB/brightness/speed/effect on LEDs 0–5 | PASS (host) | LED parity and per-slot projection checks passed. |
| 5. Stable RGB task/link states, FIFO projection and `uint32_t` rollover | PASS (host) | LED parity, steady-state and rollover checks passed; legacy animations remain an explicit opt-in build. |
| 6. `loudest_micro:codex_oai` lint + clean build | BLOCKED | pinned QMK staging tree has recursive submodules away from recorded revisions. |
| 7. Clean default/Vial builds without functional change | BLOCKED | same external build gate; existing default and Vial emulator smoke tests passed. |
| 8. OAI UF2 RP2040 emulator, descriptor and handshake | BLOCKED | no OAI UF2 may be published before the clean build succeeds. |
| 9. Reproducible verifier manifest/SHA-256 without flash path | BLOCKED | verifier correctly rejected the missing emulator evidence; no hash or manifest was invented. |

The physical runbook remains entirely **PENDING**. No physical check is
reported as PASS by this document.

## Startup LED self-check — 2026-08-17

The direct keymap now includes a host-tested, one-shot power-on diagnostic. It
projects a white pixel through chain indexes `0..23` (documented to the user as
LEDs 1–24, 80 ms per position), flashes the full chain green twice, and then
returns to the existing FIFO task/link renderer. The keymap enables RGB without
EEPROM writes when necessary and keeps it active so task/link LEDs remain
visible after the diagnostic. This is a local WS2812-path check only; USB, OAI
handshake, controls, and physical ordering remain pending until observed on the
PCB.

Host evidence for this change:

```text
test_startup_sweep_visits_all_24_leds_in_order: PASS (C/Python frame parity)
test_startup_led_check_keeps_renderer_enabled_without_persisting: PASS (keymap contract)
flash_operations: 0 (before the rebuild recorded below)
```

### Commands and outcomes

```text
python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py' -v
PASS: 36 run; 35 passed; 1 expected skip; exit 0

npm run smoke:default
PASS: keyboard, matrix, Raw HID v0 and WS2812 evidence

npm run smoke:vial
PASS: keyboard, matrix, Raw HID v0 and WS2812 evidence

npm run smoke:codex-oai
BLOCKED: OAI UF2 unavailable, as required before a successful isolated build

build_codex_oai.py --qmk-home <temporary pinned worktree> --clean
BLOCKED safely: QMK submodules are not at their recorded revisions

verify_codex_oai_artifact.py ...
BLOCKED safely: expected emulator evidence file is absent
```

`git diff --check` passed. The default and Vial keymap diff is empty. The
physical-operation search is empty for `firmware/tools`; its only match in the
host-test tree is the intentional forbidden-vocabulary assertion in
`test_artifact_verifier.py`, not an operation. The original repository still
contains its two user-owned untracked hardware items, and the staged set is
empty.

## External build gate

The isolated build tool is implemented and its seven safety tests pass, but a
fresh external Vial-QMK staging worktree did not have all recursive submodules
at the pinned revisions. The local VIA pre-hook patch was applied to that
disposable tree and the builder then correctly stopped before creating the
temporary keyboard link or publishing an image. Therefore these artifact
facts remain deliberately unavailable:

| Artifact evidence | Status |
|---|---|
| then-planned Direct OAI UF2 | absent |
| matching ELF | absent |
| OAI emulator evidence JSON | absent |
| UF2 SHA-256 | unavailable — do not invent one |
| UF2 byte size | unavailable — do not invent one |
| ELF text/data/bss | unavailable — do not invent values |
| direct-OAI descriptor/emulator result | PENDING external build gate |
| default/vial clean-build regression | PENDING external build gate |

To resolve that gate, create a disposable QMK worktree at the exact revision,
initialize submodules, apply the documented patch, then run the builder:

```bash
qmk_stage_parent="$(mktemp -d /tmp/agentpad13-qmk.XXXXXX)"
qmk_stage_dir="$qmk_stage_parent/qmk"
git -C /path/to/vial-qmk worktree add --detach "$qmk_stage_dir" 00fc4627
git -C "$qmk_stage_dir" submodule update --init --recursive
git -C "$qmk_stage_dir" apply /path/to/agentpad13/firmware/patches/0001-via-command-kb-backport.patch
PATH="/opt/homebrew/opt/arm-none-eabi-gcc@8/bin:$PATH" \
  python3 firmware/tools/build_codex_oai.py --qmk-home "$qmk_stage_dir" --clean
```

After a successful build, run `npm run smoke:codex-oai` in
`firmware/tests/emulator`, then pass the generated UF2, ELF and evidence JSON
to `firmware/tools/verify_codex_oai_artifact.py`. That verifier writes the
real manifest under `firmware/evidence/`; copy its SHA-256, byte size,
text/data/bss and PASS results back into this document only from that manifest.

## Boundary

`codex_oai` has Vial/VIA disabled and uses no helper process. The regular
`default` and `vial` prebuilt UF2s remain separate. This record contains no
automatic install step and no physical USB operation occurred:

```text
flash_operations: 0
```

## Addendum — 2026-08-14: two-layer OAI firmware gate

The direct-OAI keymap now has exactly two default layers (`CODEX` and `FN`),
with a table-driven cycle and an opt-in `CODEX_EXTRA_LAYERS` extension point.
The CODEX layer routes to OAI only after readiness; before readiness it uses
the native Codex fallback with the 600 ms ACCEPT guard, SAFE arming/release
clear, NEW hold terminal action, OS persistence, reasoning and send actions.
The FN layer exposes F2–F12, joystick-mode/touch toggles, and scroll encoder
behavior. FIFO task LED reconciliation and valid-`rgbcfg` handshake revision
resets are covered by the host parity suites.

Fresh verification from the isolated QMK worktree at `00fc4627`:

| Check | Result |
|---|---|
| OAI host suite | PASS — 58 tests, exit 0 |
| pinned lint | PASS — `loudest_micro:codex_oai` |
| clean builds | PASS — `default`, `vial`, `codex_oai` |
| direct-OAI emulator | PASS — keyboard HID, OAI HID, descriptor, rgbcfg/thstatus/device.status ACKs, AG00 event, WS2812 activity |
| artifact verifier | PASS — descriptor, symbols, size/hash, memory evidence |
| default/Vial emulator smokes | PASS |
| `git diff --check` / Python compile / Node check | PASS |

Current direct-OAI artifact evidence:

| Artifact fact | Value |
|---|---|
| UF2 size | `90624` bytes |
| UF2 SHA-256 | `d04ee3cdc62d1955f2f5545622b7491721592802e4ef9f6f10d4419703d1e703` |
| ELF text/data/bss | `45176 / 0 / 265296` |
| VID:PID / usage | `303A:8360` / `FF00:61` |
| Report | ID `6`, `64` bytes |

This is still pre-hardware evidence. No UF2 was copied to a Pico or AgentPad;
all physical rows remain **PENDING** and `flash_operations` remains `0`.

## Addendum — 2026-08-14: runtime OAI keymap RPC

The CODEX/OAI layer now accepts direct HID RPC methods for customization:
`v.oai.keymap.get` returns the compact 15-position map and
`v.oai.keymap.set` validates and persists a replacement. Only layer `0` is
accepted; `ENC` is restricted to the encoder-click position. Invalid requests
return `invalid_keymap` without changing the previous map. The map is stored
with magic/version/checksum in RP2040 wear-leveling and defaults are restored
when the record is absent or corrupt. FN remains ordinary QMK keymap data.

Fresh host/build/emulator evidence for this working tree:

| Check | Result |
|---|---|
| OAI host suite | PASS — 64 tests, exit 0 |
| strict lint | PASS — `loudest_micro:codex_oai` |
| clean builds | PASS — `default`, `vial`, `codex_oai` |
| OAI RP2040 emulator | PASS — descriptor, HID enumeration, ACKs, AG00 event, WS2812 activity |
| default/Vial RP2040 emulator | PASS |
| artifact verifier | PASS — descriptor, symbols, size/hash and emulator binding |
| `py_compile`, `node --check`, `git diff --check` | PASS |

Current direct-OAI artifact (no hardware action):

| Artifact fact | Value |
|---|---|
| UF2 size | `93184` bytes |
| UF2 SHA-256 | `20f475828845db0fda73606785676394586f6a89f6ea1b181899bf6378e28520` |
| ELF text/data/bss | `46340 / 0 / 265296` |
| VID:PID / usage | `303A:8360` / `FF00:61` |
| Report | ID `6`, `64` bytes |

The new RPC contract is host-verified, but all physical rows in the runbook
remain **PENDING**. `flash_operations` remains `0`.

## Addendum — 2026-08-10: clean build and emulator gate completed

The previous external-submodule block is historical. A disposable clone at
QMK `00fc4627` was fully initialized, the repository-owned VIA and ChibiOS
descriptor patches were applied, and the three clean builds completed with
Homebrew ARM GCC 8.5.0 plus binutils. No device was connected or written.

| Check | Result |
|---|---|
| `loudest_micro:codex_oai` strict lint | PASS |
| clean `default`, `vial` and `codex_oai` builds | PASS |
| OAI host suite | 50/50 PASS |
| OAI RP2040 emulator | PASS: USB, keyboard HID, Raw HID, Report ID 6, ACKs, key event and WS2812 activity |
| default/Vial RP2040 emulator | PASS |
| artifact verifier and `git diff --check` | PASS |

The resulting direct-OAI artifact is now available and bound to its emulator
evidence:

| Artifact fact | Value |
|---|---|
| UF2 size | `86016` bytes |
| UF2 SHA-256 | `49edc4d691fb371d69091a80c822589335418a42e2a0eaf992b2319ab0e241d7` |
| ELF text/data/bss | `42840 / 0 / 265296` |
| VID:PID / usage | `303A:8360` / `FF00:0061` |
| Report | ID `6`, `64` bytes |

Physical installation and every Pico/AgentPad control row remain **PENDING**;
the exact pin-by-pin procedure is in
[`codex-oai-pico-runbook.md`](codex-oai-pico-runbook.md). A separate explicit
authorization is required before copying the UF2 to `RPI-RP2`.

## Addendum — 2026-08-17: startup diagnostic, protocol hardening and steady LEDs

This is the current working-tree verification after the last `dev` feature
integration (`e435915`) plus the uncommitted startup-diagnostic changes. It is
the first record that includes the actual rebuilt artifact; it supersedes the
older artifact values above without rewriting their historical records.

| Check | Result |
|---|---|
| OAI host suite | PASS — 75 tests, exit 0 |
| Python compile / Node syntax / `git diff --check` | PASS |
| strict isolated lint | PASS — `loudest_micro:codex_oai` |
| clean builds | PASS — `default`, `vial`, `codex_oai` |
| direct-OAI RP2040 emulator | PASS — USB, keyboard HID, OAI HID, Report ID 6, handshake ACKs, AG00 event, WS2812 activity |
| default/Vial RP2040 emulator | PASS — matrix, USB, Raw HID v0 and WS2812 activity |
| artifact verifier | PASS — descriptor, symbols, ELF metrics, emulator binding and SHA |
| physical flash operations | `0` |

The rebuilt candidate is:

| Artifact fact | Value |
|---|---|
| Target | `loudest_micro:codex_oai` |
| UF2 size | `92160` bytes |
| UF2 SHA-256 | `fe8953013157dd427f7addda1ac3e340ea6b1ded0fda11bfc9d43ae654e5a10f` |
| ELF text/data/bss | `45872 / 0 / 265296` |
| USB / Raw HID | `303A:8360` / `FF00:0061`, Report ID `6`, 64 bytes |

Four software defects found during the audit are now covered by regression
tests: an empty `v.oai.thstatus` array is accepted as a valid readiness no-op
(it does not clear tasks; explicit slot updates still do that), `TP_TOG`
remains reachable after touch has been disabled so FN can re-enable it, and
native fallback NEW now distinguishes a short primary-modifier+N tap from a
held Control+grave terminal gesture. Legacy factory keymaps migrate the 2U
position from SEND to MICROPHONE while custom maps are preserved. The startup
diagnostic is one-shot and
non-persistent: it lights chain indexes
`0..23` one at a time in white for 80 ms, flashes the full chain green twice,
then keeps the RGB-backed task/link renderer active. No hardware was written while
producing this evidence.

The complete physical matrix, actual LED chain order, Codex Desktop host
handshake, F2 output, encoder directions, touch/joystick behavior and task
notifications remain **PENDING** until this exact hash is explicitly flashed
to the assembled board and observed. The previous `20f475...` image does not
contain this startup check and predates the empty-`thstatus` fix.

The latest working-tree correction also keeps RGB runtime-enabled after the
startup sweep. This prevents an EEPROM-disabled RGB state from hiding later
task/link frames; it changes no persistent EEPROM setting. The shipped renderer
now keeps task colours and link status steady until an OAI update or link-state
change, so it does not blink while idle. The legacy effect timing remains an
explicit opt-in (`CODEX_LED_ANIMATION_ENABLE=1`) and is rendered as a slow,
non-zero fade; the default artifact leaves animation disabled.

## Addendum — 2026-08-17: TP5 layer navigation and slow legacy animation

The direct keymap now ships four useful layers: `CODEX`, `FN`, `NAV` and
`MEDIA`. A short encoder click and a TP5 touch both advance the same cyclic
order; the encoder hold remains reserved for the persisted OS-mode toggle.
The grid ACT12 position remains SEND. The 2U position is now the independent
microphone control: it emits `ACT10` press/release, which Codex Desktop
normalizes to its combined `ACT10_ACT11` push-to-talk slot; it no longer emits
ACT12. TP5 no longer emits the legacy touch-to-AG00 event; the 15th OAI map
digit is retained only for wire compatibility, while `TP_TOG` is available on
NAV. The new default compact map is `123456789abced1` (`e` = microphone).

The default LED renderer remains steady. If the historical animation build is
enabled with `CODEX_LED_ANIMATION_ENABLE=1`, task/link output now uses a four
times slower, non-zero triangular fade rather than a hard on/off blink. This
optional path has a dedicated C harness regression; the default artifact keeps
animation disabled.

## Addendum — 2026-08-17: rebuilt OAI-first layer artifact

After the layer contract and TP5 indicator change, the complete host suite and
the pinned clean build were rerun. The disposable QMK worktree was fixed at
`00fc4627`, with initialized recursive submodules and both repository-owned
descriptor patches. No flash or USB write occurred.

| Check | Result |
|---|---|
| OAI host suite | PASS — 77 tests, exit 0 |
| C/Python LED parity | PASS — task FIFO, link states, startup sweep and four layer colours |
| strict lint | PASS — `loudest_micro:codex_oai` |
| clean builds | PASS — `default`, `vial`, `codex_oai` |
| direct-OAI RP2040 emulator | PASS — USB/HID descriptor, handshake ACKs, AG00 event and WS2812 activity |
| artifact verifier | PASS — SHA, size, ELF metrics and required symbols |
| default/Vial emulator smokes | PASS |
| `compileall`, Node syntax and `git diff --check` | PASS |
| flash operations | `0` |

The current unflashed candidate is:

| Artifact fact | Value |
|---|---|
| UF2 size | `92160` bytes |
| UF2 SHA-256 | `333b0e5d94f44d8c489433af74362499f2a6ca8218475ef2af32ff66a3550d1f` |
| ELF text/data/bss | `46056 / 0 / 265296` |
| USB / Raw HID | `303A:8360` / `FF00:0061`, Report ID `6`, 64 bytes |

Human layer 1 is always `CODEX` (QMK index 0) at boot and remains the only
layer accepted by the OAI keymap RPC. Encoder/TP5 cycling still exposes FN,
NAV and MEDIA; LED 13 changes to red/yellow/green/cyan for those four layers,
with an amber/red link tint or slow pulse before readiness. Physical switch,
TP5 and LED observations remain **PENDING**.

## Addendum — 2026-08-17: OAI-first layer indicator

The layer navigation contract now makes the first human layer explicit: `CODEX`
is QMK index `0`, is the only layer accepted by `v.oai.keymap.get/set`, and is
selected at every boot before the auxiliary `FN`, `NAV` and `MEDIA` cycle is
available. Encoder click and TP5 still cycle the auxiliary layers; the long
encoder gesture returns to CODEX while toggling the persisted OS mode.

The physical TP5/layer-indicator LED is chain index 13. It always shows the
active layer as CODEX red, FN yellow, NAV green or MEDIA cyan; the OAI waiting
or error state is an amber/red tint (and a slow pulse in the animation build).
The C renderer and independent Python oracle now cover all four colours; the
physical LED observation remains **PENDING**.

## Addendum — 2026-08-17: function feedback and duplicate SEND correction

The current working tree corrects the previous microphone interpretation. The
matrix key at position 11 and the 2U key at position 12 are both `ACT12`/`SEND`;
the default compact map is now `123456789abccd1`. The microphone action digit
remains available only for an explicitly customized OAI map and is not assigned
to a physical default key.

Action feedback is now selected by physical position rather than by the action
name: positions 6–12 flash white for `CODEX_ACTION_FEEDBACK_MS` (160 ms) on
press, while task positions 0–5 never flash white, even if a custom OAI map
assigns them another action. This keeps task-state LEDs and click feedback
independent.

| Check | Result |
|---|---|
| Host OAI suite | PASS — 78 tests, exit 0 |
| Clean pinned lint/builds | PASS — `default`, `vial`, `codex_oai` |
| OAI/default/Vial emulator smokes | PASS |
| Artifact verifier | PASS — 92,160 bytes, text/data/bss `46024/0/265296` |
| Current UF2 SHA-256 | `0027518334ad985619b8ea4ab548167e9c39a1ba3972cd228212f06890d75806` |
| Flash operations | `0` |

All physical switch, encoder, TP5, task-LED and function-feedback observations
remain **PENDING** until this exact candidate is explicitly authorized and
flashed to the assembled board or Pico test rig.

## Addendum — 2026-08-18: physical key count and 2U microphone assignment

The preceding duplicate-SEND paragraph is superseded by the current physical
map. AgentPad13 has **13 key switches** (the twelve matrix keys plus the
separate 2U key), plus the encoder click and TP5 touch pad. The final default
assignment is:

| Physical control | Function |
|---|---|
| Matrix key 11 (`[2,2]`) | protected `ACCEPT` |
| Matrix key 12 (`[2,3]`) | `ACT12` / `SEND` |
| Separate 2U (`[3,0]`) | `MICROPHONE`, `ACT10` press/release push-to-talk |

The internal OAI map therefore returns `123456789abced1`; index 12 names the
2U route and is not a claim that the 2U is matrix key 12. The source contract,
default-map migration (old version 1 and version 2 factory maps), and host
protocol tests cover this assignment. No flash or physical observation has
been performed.

## Addendum — 2026-08-18: rebuilt 2U-microphone candidate

The clean pinned-QMK build was regenerated after the physical-map correction.
The current unflashed candidate is:

| Artifact fact | Value |
|---|---|
| Target | `loudest_micro:codex_oai` |
| UF2 size | `92160` bytes |
| UF2 SHA-256 | `0b2c9afc5bc1294d232aa1c711c471b37e7ffbce34766608220267c0aff3cc68` |
| ELF text/data/bss | `46056 / 0 / 265296` |
| USB / Raw HID | `303A:8360` / `FF00:0061`, Report ID `6`, 64 bytes |
| Host OAI suite | PASS — 79 tests |
| Emulator + artifact verifier | PASS |
| Flash operations | `0` |

The emulator evidence confirms USB/HID enumeration, all three OAI handshake
acknowledgements, the AG00 event and WS2812 activity. Physical key, 2U
microphone, encoder, TP5 and LED observations remain **PENDING**.

## Addendum — 2026-08-18: official ACT11 order and fresh build

The current `dev` source supersedes the earlier 2U-microphone candidate. The
CODEX physical positions now follow the official action order through position
12: `AG00..AG05`, `ACT06..ACT12`; position 13 is encoder click and position 14
is the legacy protocol slot. In the board geometry this means matrix key 11 is
the protected `ACT10`/ACCEPT route, matrix key 12 is `ACT11` (the second
microphone contact), and the separate 2U position is `ACT12`/SEND. The legacy
`MICROPHONE` digit remains accepted for custom-map compatibility and aliases
`ACT10`.

The persisted keymap format is version 3. Factory records from both prior
layouts (`...abccd1` and `...abced1`) migrate to `123456789abfcd1`; custom
maps survive unchanged. `ACT11` is covered by the byte-exact protocol harness
and by the physical-layout contract test.

Fresh no-hardware verification after this change:

| Check | Result |
|---|---|
| Focused protocol + keymap contract | PASS — 40 tests |
| Full OAI host suite | PASS — 81 tests |
| Clean pinned QMK lint | PASS — `loudest_micro:codex_oai` |
| Clean `default`, `vial`, `codex_oai` builds | PASS — QMK `00fc4627`, Report-ID patch, ARM GCC 8.5 |
| Direct-OAI RP2040 emulator | PASS — new UF2 enumerates, handshakes, AG00 and WS2812 |
| Current UF2 | 92,672 bytes; SHA-256 `11ee3ed649cf198186fc1e3c190fcaf6a7a1cfbdb18f68ebbead974b09a1712b` |
| ELF text/data/bss | `46144 / 0 / 265296`; required symbols and manifest verifier PASS |
| Physical flash operations | `0` |

The emulator emitted one expected rp2040js SIO warning (`Write to invalid SIO
address: 50`) but completed with all required evidence fields true. Hardware
rows remain **PENDING** until the board/Pico is operated and observed.

## Import addendum — 2026-08-21: destination port rebuild

The AgentPad13 destination port rebuilt the reviewed Direct OAI source with
pinned Vial-QMK `00fc4627` and Arm GNU Toolchain 15.2.Rel1. The current
unflashed release candidate is:

| Artifact fact | Current destination value |
|---|---|
| File | `release/firmware/prebuilt/agentpad13_codex_oai.uf2` |
| UF2 size | `93,696` bytes |
| UF2 SHA-256 | `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c` |
| USB / Raw HID | `303A:8360` / `FF00:0061`, Report ID `6`, 64 bytes |
| Current evidence | `firmware/evidence/codex-oai-emulator.json` and `firmware/evidence/codex-oai-current-manifest.json` |
| Physical flash operations | `0` |

The imported phase-3 baseline (92,160 bytes,
`d1768471eef4d0be12c1fc264279f20b9a7d293ea902c0608ebcfb4643ae35be`)
and the older historical manifest (92,672 bytes,
`11ee3ed649cf198186fc1e3c190fcaf6a7a1cfbdb18f68ebbead974b09a1712b`)
remain provenance only and are superseded by the port rebuild. The complete
physical matrix remains **PENDING**; no automatic installation or flash was
performed.

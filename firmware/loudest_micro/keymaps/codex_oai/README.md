# AgentPad13 direct Codex OAI keymap

`codex_oai` is an isolated laboratory keymap for checking whether Codex Desktop
can drive an AgentPad13 directly through OAI Raw HID. It is **not** the normal
AgentPad13 firmware and it does not change the `default` or `vial` keymaps.

## Local USB identity

The keymap intentionally reproduces the local Codex Micro OAI LED endpoint:

| Property | Value |
|---|---|
| VID:PID | `303A:8360` |
| Manufacturer / product | `hirlu` / `Codex Micro Lab OAI LED` |
| Device version | `0x0005` |
| Raw HID usage | `FF00:61` |
| Report format | Report ID 6; 64 bytes total |

This identity is only for this local experiment. It must not be confused with
the regular AgentPad13 identity, and it must not be shipped as the normal
`default` or `vial` firmware.

## Direct endpoint

Codex Desktop talks straight to the keyboard's Raw HID endpoint. There is no
Python helper, daemon, bridge, Vial protocol, or Vial configuration interface
in this target. OAI RPC fragments use the validated Report-ID-6, 64-byte
framing. Controls do not emit OAI notifications until the endpoint has
received both `v.oai.rgbcfg` and `v.oai.thstatus`.

The only keyboard-originated OAI control names are:

`AG00`–`AG05`, `ACT06`–`ACT12`, `ENC`, `ENC_CW`, and `ENC_CC`.

The board has thirteen key switches: twelve matrix keys plus the separate
bottom-left 2U key. The CODEX layer assigns those thirteen physical positions
to the official action order (`AG00`–`AG05`, `ACT06`–`ACT12`); `ACT10` is the
protected ACCEPT wire route, `ACT11` is the second microphone contact, and
`ACT12` is SEND. The encoder click and TP5 touch pad are additional controls,
not extra matrix keys. The legacy `MICROPHONE` action digit remains accepted
in custom maps and aliases ACT10 for backwards compatibility.

Joystick movement is deliberately not translated into invented OAI events.

## Personalización de la capa CODEX/OAI por HID

Codex puede leer y cambiar las 15 posiciones de la capa CODEX sin helper ni
Vial. El mapa se representa como 15 dígitos hexadecimales, uno por posición:

| Dígito | Acción |
|---|---|
| `0` | NOOP |
| `1` | PREVIOUS |
| `2` | NEXT |
| `3` | NEW |
| `4` | REVIEW |
| `5` | PLAN |
| `6` | IMPLEMENT |
| `7` | REFACTOR |
| `8` | TEST |
| `9` | ABORT |
| `a` | SAFE |
| `b` | ACCEPT |
| `c` | SEND |
| `d` | ENC (solo click del encoder, posición 13) |
| `e` | MICROPHONE (`ACT10` push-to-talk) |
| `f` | ACT11 (second official microphone contact) |

El mapa de fábrica es `123456789abfcd1`: las posiciones 0–12 siguen el orden
oficial `AG00..AG05`, `ACT06..ACT12`; la posición 13 es el click del encoder y
14 se conserva como ranura OAI legacy para compatibilidad del protocolo. TP5
ya no emite esa ranura: cambia de capa. Las capas FN/NAV/MEDIA
siguen siendo keymap QMK normal y se pueden modificar en `keymap.c`; la API
solo cambia CODEX/OAI.

Leer el mapa:

```json
{"method":"v.oai.keymap.get","id":42,"params":{"l":0}}
```

Respuesta compacta:

```json
{"result":{"l":0,"m":"123456789abfcd1"},"id":42}
```

Guardar un mapa personalizado:

```json
{"method":"v.oai.keymap.set","id":42,"params":{"l":0,"m":"0123456789abcd0"}}
```

El firmware valida la longitud, cada dígito, la capa (`l` debe ser 0) y la
posición reservada de `ENC` antes de sustituir nada. Una respuesta
`{"result":true,"id":42}` confirma la escritura; los errores devuelven
`{"error":"invalid_keymap","id":42}` y dejan el mapa anterior intacto.
La copia se guarda con magic, versión y checksum en el wear-leveling del
RP2040 (fuera del área `eeconfig`); tras reiniciar se recupera automáticamente.
El formato persistido está en la versión 3. Las copias de fábrica anteriores
(`...abccd1` y `...abced1`) se migran al nuevo mapa `...abfcd1`, mientras que
un mapa personalizado se conserva. Si la copia está ausente o corrupta se
reinstala el mapa de fábrica. Un reset de EEPROM (`eeconfig_init_user`) también
vuelve a los defaults.

## Layer behavior and native fallback

The default firmware has four layers. TP5 is the only layer control and cycles
`CODEX -> FN -> NAV -> MEDIA -> CODEX`. Its input is intentionally ignored
during the 2.28-second power-on LED self-check, which filters the TTP223
settling edge and preserves the CODEX boot layer. The encoder press always
emits the OAI `ENC` press/release pair; neither a tap nor a hold changes layer
or OS mode. SAFE/ACCEPT arming is an internal timer state and is not a layer.

`CODEX` is human layer 1 and QMK layer index 0. At each boot the firmware
resets both QMK RAM layer-state sources to that layer, so an earlier persisted
default FN/NAV/MEDIA layer cannot override it. The direct OAI keymap RPC
accepts only `l:0`; FN/NAV/MEDIA are ordinary auxiliary layers and never
replace the OAI map at startup.

| Layer | Grid defaults | Hero / encoder / touch |
|---|---|---|
| `CODEX` | OAI controls below | `SEND` / OAI `ENC` / TP5 layer cycle |
| `FN` | `JS_MODE`, F2–F12 | media play / OAI `ENC` / TP5 layer cycle |
| `NAV` | Escape, home/end, arrows, paging and editing | OAI `ENC` / TP5 cycle / `TP_TOG` |
| `MEDIA` | media, volume and RGB controls | OAI `ENC` / TP5 layer cycle |

The FN/NAV/MEDIA rows are intentionally ordinary keymap data in `keymap.c`:
users can replace them without touching the OAI parser or LED renderer.
Additional extension layers remain compile-time opt-in through
`CODEX_EXTRA_LAYERS` (up to the three declared extension rows). `TP_TOG` lives on
NAV so touch can be re-enabled after it has been disabled; TP5 itself remains
the layer-cycle gesture while enabled.

Before the OAI handshake is ready, CODEX controls fall back to the proven
native Codex shortcuts: AG00/AG01 previous/next, AG02 new task, AG03 review,
AG04 plan, AG05 implement, ACT06 refactor, ACT07 test, ACT08 abort, ACT09 SAFE,
ACT10 protected ACCEPT, ACT11 microphone, and ACT12 SEND. ACCEPT is a no-op on a short tap
and fires once on release after 600 ms or after SAFE has been held long enough
to arm. NEW emits the primary-modifier+N shortcut on a short tap and
Control+grave when held for `TAPPING_TERM` or longer. Releasing SAFE always
clears the arm. Encoder rotation changes reasoning in CODEX and scrolls in FN.
The fallback
is mutually exclusive with OAI routing, so one physical event cannot emit both
a native shortcut and an OAI frame.

## Physical layout and OAI controls

The `LAYOUT` has fifteen positions: thirteen key switches, encoder click and
TP5. The thirteen switches use the official OAI order; the bottom-left 2U is
the physical position 12 and therefore carries `ACT12`/SEND in the default
map. TP5 is reserved for layer cycling; it is no longer an additional `AG00`
route. The normal `AG00` action remains on K00.

| Matrix position | Physical control | OAI control |
|---|---|---|
| `[0,0]` | grid key | `AG00` |
| `[0,1]` | grid key | `AG01` |
| `[0,2]` | grid key | `AG02` |
| `[0,3]` | grid key | `AG03` |
| `[1,0]` | grid key | `AG04` |
| `[1,1]` | grid key | `AG05` |
| `[1,2]` | grid key | `ACT06` |
| `[1,3]` | grid key | `ACT07` |
| `[2,0]` | grid key | `ACT08` |
| `[2,1]` | grid key | `ACT09` |
| `[2,2]` | matrix key 11 | `ACT10` / protected `ACCEPT` |
| `[2,3]` | matrix key 12 | `ACT11` / microphone |
| `[3,0]` | separate 2U key | `ACT12` / SEND |
| `[3,1]` | encoder press | `ENC` |
| `[3,2]` | capacitive touch TP5 | cycle layer |

When the endpoint is ready, encoder rotation sends `ENC_CW` or `ENC_CC` and an
encoder press sends `ENC` on every layer. The encoder never changes layers;
TP5 alone cycles the layer table without generating an OAI control. `[0,0]` is
also the ordinary Bootmagic Lite recovery position; that recovery behaviour
remains QMK-native.

## LED contract

The 24-pixel RGB chain is rendered locally from the six OAI task slots and the
endpoint link state. The direct keymap owns the renderer; the older AgentPad
status renderer is bypassed only for this keymap.

| LEDs | Meaning |
|---|---|
| 0–5 | one RGB task slot per LED (six slots) |
| 6–12 | white press feedback for function keys `ACT06`–`ACT12` |
| 12 | white press feedback for the physical `ACT12`/SEND position, otherwise selected task summary |
| 13 | TP5/layer indicator: exact active-layer colour; optional animation may pulse brightness only |
| 14–23 | dim global underglow for the selected task |

Action feedback is white for 160 ms on every physical function key (positions
6–12). The six task positions `AG00`–`AG05` never flash white, even if a
custom OAI map assigns them another action; their LEDs remain task-state LEDs.
By default, a task LED holds its selected
RGB/brightness value until that task changes or is removed. LED 13 always
identifies the active layer: CODEX/OAI red, FN yellow, NAV green, and MEDIA
cyan (additional layers continue through the palette), even while the OAI link
is waiting or in error. This keeps a fresh CODEX boot visibly distinct from
FN before the handshake. The optional animation build may add a slow brightness
pulse without changing the hue; the steady default build does not blink. LED 12 and the
underglow prefer the active working task when one exists. A build that wants the earlier animated mode can opt in explicitly with
`CODEX_LED_ANIMATION_ENABLE=1`; that compatibility mode is deliberately slow
and uses a non-zero colour fade instead of a hard blink. The shipped/default
build leaves it disabled.

## Power-on LED self-check

After each USB power-up the firmware runs a one-shot physical-chain check:
LEDs **1 → 24** (renderer indexes `0..23`) light one at a time in white for
80 ms each. The complete chain then flashes green twice and normal task/link
rendering resumes after approximately 2.28 seconds. If RGB had been disabled,
the keymap enables it with the `*_noeeprom` API and keeps it active for the
task/link renderer; no EEPROM or OAI event is written. This proves
the local WS2812 data path and ordering, but it does not prove USB enumeration,
the OAI handshake, or task notifications; those remain separate checks.

## Safe build and validation

The target is build-only. It does not search for, open, or write to a USB
device. Use the disposable-worktree builder in
[`../../../tools/build_codex_oai.py`](../../../tools/build_codex_oai.py) and
the complete recipe in [`../../../BUILD.md`](../../../BUILD.md). The builder
requires Vial-QMK commit `00fc4627`, the local VIA pre-hook and Raw HID
Report-ID patches, initialized submodules, and Arm GNU Toolchain 15.2.Rel1. It
publishes only
[`release/firmware/prebuilt/agentpad13_codex_oai.uf2`](../../../../release/firmware/prebuilt/agentpad13_codex_oai.uf2)
after clean builds pass. The current candidate is 93,696 bytes with SHA-256
`fcb50b2419419be43b7cf90b00a96b16063fcaf182bc24b9642d57e2e8adf54d`.

Run the complete host gate from the repository root with
`python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py'`.
The current offline result is bound to the exact release UF2 by the
[`emulator capture`](../../../evidence/codex-oai-emulator.json) and
[`current manifest`](../../../evidence/codex-oai-current-manifest.json).
Neither the builder nor these checks install or flash firmware.

Before any future hardware operation, complete the explicit authorization and
matrix in [`../../../../docs/codex-oai-physical-runbook.md`](../../../../docs/codex-oai-physical-runbook.md).
For the temporary Raspberry Pi Pico bench, use the pin-by-pin jumper guide in
[`../../../../docs/codex-oai-pico-runbook.md`](../../../../docs/codex-oai-pico-runbook.md).
The current host/build/emulator evidence and the still-pending physical matrix
are recorded in
[`../../../../docs/codex-oai-prehardware-results.md`](../../../../docs/codex-oai-prehardware-results.md).

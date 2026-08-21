# AgentPad13 Direct OAI Implementation Plan

> **Historical plan:** this records the original implementation sequence. Its
> source locations, intermediate status, and artifact values are provenance,
> not current instructions. The destination release is
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2`, 93,696 bytes, SHA-256
> `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`;
> physical validation remains PENDING and no flash occurred.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir y validar, sin flashear hardware, un target QMK `loudest_micro:codex_oai` que hable OAI directamente con Codex Desktop y represente seis tareas en los 24 LEDs RGB de AgentPad13.

**Architecture:** El parser OAI y el motor LED viven dentro del nuevo keymap experimental; el firmware común solo añade guardas de compilación para ceder Raw HID y RGB a ese target. Un oráculo Python autónomo y dos harnesses C verifican protocolo y animaciones; un runner RP2040 arranca el UF2 y genera evidencia de enumeración/handshake antes de producir un manifiesto reproducible.

**Tech Stack:** vial-qmk commit `00fc4627`, QMK C, RP2040/ChibiOS, WS2812 RGB Matrix, Python 3 `unittest`, C11 host harnesses, Node.js + `rp2040js`, UF2, `arm-none-eabi-{gcc,nm,size}`.

## Global Constraints

- Todo el código, pruebas, documentación y logs permanentes se guardan en `/Users/hirlu/Documents/Projects/agentpad13`.
- `/Users/hirlu/Documents/Projects/vial-qmk` es referencia y origen para un worktree de build; no es el destino de los cambios.
- Target local: `loudest_micro:codex_oai`; los keymaps `default` y `vial` no cambian de comportamiento.
- Contrato USB experimental exacto: `303A:8360`, manufacturer `hirlu`, product `Codex Micro Lab OAI LED`, device version `0x0005`, Usage `FF00:61`, Report ID `6`, 64 bytes.
- El target OAI desactiva VIA/Vial; no existe helper host y no se inventan eventos OAI de joystick.
- La identidad USB de terceros es solo para laboratorio local; no hay push, publicación ni distribución.
- No ejecutar `qmk flash`, copiar UF2 a un volumen, montar BOOTSEL ni escribir en un dispositivo.
- No staged/commit de `hardware/case/stl/agentpad13_v2_plate.3mf` ni `hardware/pcb/fabpack_translucent/`.
- Cada cambio de producción sigue RED → GREEN → REFACTOR y termina con pruebas frescas.

## File Structure

- `firmware/loudest_micro/keymaps/codex_oai/codex_oai.{c,h}`: framing, JSON acotado, handshake, seis slots y eventos OAI.
- `firmware/loudest_micro/keymaps/codex_oai/codex_led.{c,h}`: estado visual puro y render RGB determinista para 24 LEDs.
- `firmware/loudest_micro/keymaps/codex_oai/keymap.c`: mapeo físico, encoder, touch, feedback de acción y conexión OAI→LED.
- `firmware/loudest_micro/keymaps/codex_oai/{config.h,rules.mk,README.md}`: target experimental y documentación de uso.
- `firmware/loudest_micro/loudest_micro.c`: dos guardas opt-in; ningún cambio funcional fuera del target OAI.
- `firmware/tests/codex_oai/`: oráculos Python, fixtures, stubs, harnesses y tests.
- `firmware/tests/emulator/oai_runner.cjs`: boot real del UF2, enumeración USB y handshake OAI.
- `firmware/tools/build_codex_oai.py`: staging seguro en un QMK home validado; solo compila.
- `firmware/tools/verify_codex_oai_artifact.py`: manifiesto de artefacto, descriptor y símbolos; nunca flashea.
- `docs/codex-oai-{prehardware-results,physical-runbook}.md`: evidencia y futura matriz física.

---

### Task 1: Portar el motor OAI con paridad Python/C

**Files:**
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.c`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`
- Create: `firmware/tests/codex_oai/protocol_oracle.py`
- Create: `firmware/tests/codex_oai/protocol_harness.c`
- Create: `firmware/tests/codex_oai/stubs/raw_hid.h`
- Create: `firmware/tests/codex_oai/test_protocol.py`

**Interfaces:**
- Consumes: frames de 64 bytes `[report_id=6, channel, length, payload<=61, padding]`.
- Produces: `codex_oai_init()`, `codex_oai_ready()`, `codex_oai_notify()`, `raw_hid_receive()` y respuestas byte-exactas mediante `raw_hid_send()`.

- [ ] **Step 1: Escribir el test de paridad que falle por ausencia del motor**

Crear `test_protocol.py` con un helper que compile `protocol_harness.c` y estas aserciones mínimas:

```python
class ProtocolParityTest(unittest.TestCase):
    def test_handshake_is_byte_exact(self):
        frames = tuple(fragment_message(
            b'{"method":"v.oai.rgbcfg","id":17,"params":{}}'
        ))
        result = self.harness.feed(frames)
        self.assertEqual(
            result.sent,
            (make_report(b'{"result":true,"id":17}\r\n'),),
        )

    def test_controls_are_silent_until_ready(self):
        self.assertEqual(self.harness.notify("AG00", True).sent, ())

    def test_only_allowlisted_methods_reply(self):
        result = self.harness.rpc(
            b'{"method":"unknown","id":5,"params":{}}'
        )
        self.assertEqual(result.sent, ())
```

- [ ] **Step 2: Ejecutar RED**

Run:

```bash
python3 -m unittest firmware.tests.codex_oai.test_protocol -v
```

Expected: FAIL porque `protocol_oracle.py`, `codex_oai.c` y el harness todavía no existen.

- [ ] **Step 3: Importar mecánicamente las fuentes validadas**

Tomar como fuentes byte-for-byte la implementación Direct OAI validada en el
checkout de referencia original:

```text
codex_micro_lab_oai_led/codex_oai.c
codex_micro_lab_oai_led/codex_oai.h
codex_micro_lab/rp2040_oai_emulator/oai_engine.py
```

Copiar las dos fuentes C al nuevo keymap y copiar el motor Python como `protocol_oracle.py`. No cambiar opcodes, JSON, límites, nombres de controles ni framing en esta tarea.

- [ ] **Step 4: Añadir el harness C exacto**

El harness define el descriptor esperado, captura hasta 64 reports y expone comandos `RESET`, `FRAME <hex>` y `NOTIFY <control> <pressed>`:

```c
#define RAW_EPSIZE 64
#define RAW_REPORT_ID 6
#include <stdio.h>
#include <string.h>
#include "codex_oai.h"

static uint8_t sent[64][OAI_REPORT_SIZE];
static uint8_t sent_count;

void raw_hid_send(uint8_t *data, uint8_t length) {
    if (length == OAI_REPORT_SIZE && sent_count < 64) {
        memcpy(sent[sent_count++], data, OAI_REPORT_SIZE);
    }
}
```

`stubs/raw_hid.h` declara únicamente `void raw_hid_send(uint8_t *, uint8_t);`. Compilar el harness con `cc -std=c11 -Wall -Wextra -Werror` e incluir el `codex_oai.c` real.

- [ ] **Step 5: Completar el wrapper Python sin cambiar el oráculo**

`test_protocol.py` compila a un directorio temporal, escribe líneas al harness y parsea `SENT <hex>`, `READY 0|1` y `---`. Usar `protocol_oracle.fragment_message()` y comparar cada report completo de 64 bytes, incluido padding.

El wrapper convierte el payload CircuitPython de 63 bytes al report QMK así:

```python
def make_report(fragment: bytes, channel: int = 2) -> bytes:
    return bytes((6,)) + protocol_oracle.make_payload(channel, fragment)
```

- [ ] **Step 6: Ejecutar GREEN y regresión del oráculo original**

Run:

```bash
python3 -m unittest firmware.tests.codex_oai.test_protocol -v
python3 -m unittest \
  codex_micro_lab.tests.test_rp2040_engine \
  codex_micro_lab.tests.test_rp2040_parity -v
```

El segundo comando se ejecuta desde `/Users/hirlu/Documents/Projects/vial-qmk`. Expected: ambos PASS y respuestas idénticas.

- [ ] **Step 7: Commit local**

```bash
git add firmware/loudest_micro/keymaps/codex_oai/codex_oai.c \
        firmware/loudest_micro/keymaps/codex_oai/codex_oai.h \
        firmware/tests/codex_oai
git commit -m "feat: port validated OAI protocol engine"
```

---

### Task 2: Exponer los seis slots y el estado de enlace

**Files:**
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.c`
- Modify: `firmware/loudest_micro/keymaps/codex_oai/codex_oai.h`
- Modify: `firmware/tests/codex_oai/protocol_harness.c`
- Modify: `firmware/tests/codex_oai/test_protocol.py`

**Interfaces:**
- Consumes: actualizaciones `v.oai.thstatus` de slots `0..5`.
- Produces: `codex_oai_task_for_slot()`, revisión de slots, revisión de errores y `oai_link_state_t`.

- [ ] **Step 1: Añadir tests RED de seis slots, actualización parcial y error**

```python
def test_six_slots_remain_addressable(self):
    params = [
        {"id": index, "c": 0x102030 + index, "e": 1,
         "b": 1.0, "s": 0.5}
        for index in range(6)
    ]
    state = self.harness.thstatus(params)
    self.assertEqual([slot.source_slot for slot in state.slots], list(range(6)))

def test_partial_update_preserves_unspecified_fields(self):
    self.harness.thstatus([{"id": 4, "c": 0x112233, "e": 4, "b": 1, "s": 0.25}])
    state = self.harness.thstatus([{"id": 4, "b": 0.5}])
    self.assertEqual(state.slots[4].rgb, (0x11, 0x22, 0x33))
    self.assertEqual(state.slots[4].effect, 4)

def test_malformed_frame_advances_error_revision(self):
    before = self.harness.snapshot().error_revision
    after = self.harness.feed((bytes(64),)).snapshot
    self.assertNotEqual(after.error_revision, before)
```

- [ ] **Step 2: Ejecutar RED**

Expected: FAIL porque la API pública aún limita rangos visibles y no expone salud.

- [ ] **Step 3: Añadir las interfaces al header**

```c
#define OAI_SLOT_COUNT 6

typedef enum {
    OAI_LINK_WAITING = 0,
    OAI_LINK_READY = 1,
    OAI_LINK_ERROR = 2,
} oai_link_state_t;

bool codex_oai_task_for_slot(uint8_t slot, codex_oai_task_t *output);
uint8_t codex_oai_state_revision(void);
uint8_t codex_oai_error_revision(void);
oai_link_state_t codex_oai_link_state(void);
```

- [ ] **Step 4: Implementar estado acotado**

Cambiar el límite de proyección de dos a seis, añadir acceso directo por slot y un `uint8_t error_revision` que incrementa con rollover natural ante report ID, canal, longitud, padding u objeto JSON inválido. `codex_oai_link_state()` devuelve ERROR cuando la última revisión fue un error no seguido por un request válido; READY cuando se completaron `rgbcfg + thstatus`; WAITING en el resto.

- [ ] **Step 5: Ampliar la salida del harness**

Imprimir por snapshot:

```text
LINK <0|1|2>
REVISION <n>
ERROR_REVISION <n>
SLOT <id> <r> <g> <b> <effect> <brightness> <speed> <flags>
```

- [ ] **Step 6: Ejecutar GREEN y toda la paridad de protocolo**

```bash
python3 -m unittest firmware.tests.codex_oai.test_protocol -v
```

Expected: PASS; los mensajes y eventos existentes continúan byte-exactos.

- [ ] **Step 7: Commit local**

```bash
git add firmware/loudest_micro/keymaps/codex_oai/codex_oai.c \
        firmware/loudest_micro/keymaps/codex_oai/codex_oai.h \
        firmware/tests/codex_oai
git commit -m "feat: expose six OAI task slots"
```

---

### Task 3: Implementar el renderer RGB con oráculo Python

**Files:**
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_led.c`
- Create: `firmware/loudest_micro/keymaps/codex_oai/codex_led.h`
- Create: `firmware/tests/codex_oai/led_oracle.py`
- Create: `firmware/tests/codex_oai/led_harness.c`
- Create: `firmware/tests/codex_oai/test_leds.py`

**Interfaces:**
- Consumes: seis `codex_oai_task_t`, link state, feedback de acción y `uint32_t now_ms`.
- Produces: frame RGB determinista `codex_led_rgb_t output[24]`.

- [ ] **Step 1: Escribir tests RED de mapeo, working, feedback y rollover**

```python
def test_each_task_slot_owns_led_zero_through_five(self):
    tasks = [task(slot=i, rgb=(10 + i, 20 + i, 30 + i), effect=1) for i in range(6)]
    frame = render(tasks, now_ms=0)
    self.assertEqual([frame[i] for i in range(6)], [item.rgb for item in tasks])

def test_working_pattern_matches_validated_timeline(self):
    task0 = task(slot=0, rgb=(48, 79, 254), effect=4, brightness=255, speed=128)
    levels = [render([task0], now_ms=t)[0] for t in (0, 80, 150, 300, 660, 900)]
    self.assertEqual(levels, working_rgb_timeline(task0, (0, 80, 150, 300, 660, 900)))

def test_uint32_rollover_keeps_same_animation_phase(self):
    start = 0xFFFFFFF0
    self.assertEqual(render_at(start, 0x00000010), render_at(0, 0x20))

def test_action_feedback_expires_after_160_ms(self):
    renderer.note_action(6, True, 1000)
    self.assertEqual(renderer.render(1159)[6], (255, 255, 255))
    self.assertEqual(renderer.render(1160)[6], (0, 0, 0))
```

- [ ] **Step 2: Ejecutar RED**

Expected: FAIL porque no existe `led_oracle.py` ni renderer C.

- [ ] **Step 3: Crear la API C exacta**

```c
#define CODEX_LED_COUNT 24
#define CODEX_TASK_LED_COUNT 6
#define CODEX_ACTION_FEEDBACK_MS 160

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} codex_led_rgb_t;

void codex_led_init(void);
void codex_led_set_tasks(const codex_oai_task_t tasks[OAI_SLOT_COUNT], uint8_t active_mask, uint32_t now_ms);
void codex_led_set_link(oai_link_state_t state, uint32_t now_ms);
void codex_led_note_action(uint8_t led_index, bool pressed, uint32_t now_ms);
void codex_led_render(uint32_t now_ms, codex_led_rgb_t output[CODEX_LED_COUNT]);
```

- [ ] **Step 4: Portar el oráculo de efectos**

Tomar `EFFECT_STEPS`, `WORKING_STEPS`, cálculo de brillo, velocidad y rollover de:

```text
/Users/hirlu/Documents/Projects/vial-qmk/codex_micro_lab/tools/oai_led_lab.py
```

Adaptaciones exactas:

- `MAX_PROJECTED_RANKS = 6`;
- devolver `(r,g,b)` en lugar de niveles `0..31`;
- `channel_out = (channel * brightness * pattern_level + 32512) // 65025`;
- LEDs 0–5 = slots; 6–11 = feedback; 12 = tarea global; 13 = link; 14–23 = tarea global a mitad de intensidad;
- waiting = ámbar `(255,96,0)` blink 500/500 ms;
- ready = verde `(0,96,0)` sólido;
- error = rojo `(255,0,0)` blink 120/120 ms;
- feedback pulsado = blanco `(255,255,255)` durante 160 ms.

- [ ] **Step 5: Implementar el C con la misma tabla y fórmulas**

Usar `PROGMEM` solo bajo `__AVR__`; RP2040 y harness host usan arrays constantes normales. Mantener `uint32_t elapsed = now_ms - pattern_start_ms` para rollover definido.

- [ ] **Step 6: Añadir el harness LED**

El harness incluye el `codex_led.c` real y acepta `TASK`, `LINK`, `ACTION`, `RENDER`; cada render imprime exactamente 24 líneas `LED <index> <r> <g> <b>`.

- [ ] **Step 7: Ejecutar GREEN y paridad C/Python**

```bash
python3 -m unittest firmware.tests.codex_oai.test_leds -v
```

Expected: PASS para efectos 0–6, working, seis slots, underglow, link, feedback y rollover.

- [ ] **Step 8: Commit local**

```bash
git add firmware/loudest_micro/keymaps/codex_oai/codex_led.c \
        firmware/loudest_micro/keymaps/codex_oai/codex_led.h \
        firmware/tests/codex_oai
git commit -m "feat: render six OAI tasks on AgentPad RGB"
```

---

### Task 4: Integrar el keymap, encoder, touch y guardas comunes

**Files:**
- Create: `firmware/loudest_micro/keymaps/codex_oai/config.h`
- Create: `firmware/loudest_micro/keymaps/codex_oai/rules.mk`
- Create: `firmware/loudest_micro/keymaps/codex_oai/keymap.c`
- Modify: `firmware/loudest_micro/loudest_micro.c`
- Create: `firmware/tests/codex_oai/test_keymap_contract.py`

**Interfaces:**
- Consumes: API de Tasks 1–3 y layout AgentPad13 de 15 entradas.
- Produces: target QMK aislado con eventos OAI y overlay RGB.

- [ ] **Step 1: Escribir el contrato estático RED**

El test exige:

```python
EXPECTED_LAYOUT = [
    "OAI_AG00", "OAI_AG01", "OAI_AG02", "OAI_AG03",
    "OAI_AG04", "OAI_AG05", "OAI_ACT06", "OAI_ACT07",
    "OAI_ACT08", "OAI_ACT09", "OAI_ACT10", "OAI_ACT12",
    "OAI_ACT12", "OAI_ENC", "OAI_AG00",
]

def test_exact_usb_contract(self):
    self.assertIn("#define VENDOR_ID 0x303A", self.config)
    self.assertIn("#define PRODUCT_ID 0x8360", self.config)
    self.assertIn("#define RAW_USAGE_PAGE 0xFF00", self.config)
    self.assertIn("#define RAW_USAGE_ID 0x61", self.config)
    self.assertIn("#define RAW_EPSIZE 64", self.config)
    self.assertIn("#define RAW_REPORT_ID 6", self.config)

def test_no_vial_or_helper(self):
    self.assertEqual(self.rules["VIA_ENABLE"], "no")
    self.assertEqual(self.rules["VIAL_ENABLE"], "no")
    self.assertNotIn("CXH_", self.keymap)
```

- [ ] **Step 2: Ejecutar RED**

Expected: FAIL por ausencia de `config.h`, `rules.mk` y `keymap.c`.

- [ ] **Step 3: Crear configuración y reglas exactas**

`config.h` define identidad, `RAW_*`, Bootmagic K00 y:

```c
#define LOUDEST_CUSTOM_RAW_HID
#define LOUDEST_CUSTOM_RGB_STATUS
```

`rules.mk` contiene:

```make
VIA_ENABLE = no
VIAL_ENABLE = no
RAW_ENABLE = yes
BOOTMAGIC_ENABLE = yes
ENCODER_ENABLE = yes
ENCODER_MAP_ENABLE = no
RGB_MATRIX_ENABLE = yes
CONSOLE_ENABLE = no
COMMAND_ENABLE = no
QMK_SETTINGS = no
TAP_DANCE_ENABLE = no
COMBO_ENABLE = no
LTO_ENABLE = yes

SRC += codex_oai.c
SRC += codex_led.c
```

- [ ] **Step 4: Crear el keymap de una capa**

Usar `LAYOUT(...)` con los quince tokens de `EXPECTED_LAYOUT`. `process_record_user()` traduce cada custom keycode al enum `codex_oai_control_t`; registra feedback en el LED físico correspondiente y llama `codex_oai_notify(control, pressed)`.

`encoder_update_user(0, clockwise)` envía `ENC_CW` o `ENC_CC` con `pressed=true`. `keyboard_post_init_user()` inicializa OAI y LEDs.

`housekeeping_task_user()` compara `codex_oai_state_revision()`, copia slots 0–5 mediante `codex_oai_task_for_slot()`, actualiza máscara activa y link state. `rgb_matrix_indicators_advanced_user()` llama `codex_led_render(timer_read32(), frame)` y aplica solo índices dentro de `[led_min, led_max)` con `rgb_matrix_set_color()`.

La firma para el QMK fijado es `bool rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max)` y devuelve `true`. El feedback físico usa LED 6–10 para `ACT06..ACT10`, LED 11 para el `ACT12` de la rejilla y LED 12 para el `ACT12` 2U; el segundo se distingue mediante `record->event.key.row == 3 && record->event.key.col == 0`.

- [ ] **Step 5: Añadir guardas comunes mínimas**

En `loudest_micro.c`:

- envolver el protocolo Raw HID AgentPad13, sus buffers y sus callbacks con `#if defined(RAW_ENABLE) && !defined(LOUDEST_CUSTOM_RAW_HID)`;
- en `rgb_matrix_indicators_advanced_kb()`, si existe `LOUDEST_CUSTOM_RGB_STATUS`, omitir `loudest_status[]` y el indicador de capa, y devolver directamente `rgb_matrix_indicators_advanced_user(led_min, led_max)`;
- conservar byte-for-byte el camino existente cuando las macros no están definidas.

- [ ] **Step 6: Ejecutar GREEN y contratos anteriores**

```bash
python3 -m unittest firmware.tests.codex_oai.test_keymap_contract -v
python3 -m unittest firmware.tests.codex_oai.test_protocol firmware.tests.codex_oai.test_leds -v
```

Expected: PASS.

- [ ] **Step 7: Probar la ausencia de deriva en default/vial a nivel fuente**

```bash
git diff HEAD^ -- firmware/loudest_micro/keymaps/default firmware/loudest_micro/keymaps/vial
```

Expected: salida vacía.

- [ ] **Step 8: Commit local**

```bash
git add firmware/loudest_micro/loudest_micro.c \
        firmware/loudest_micro/keymaps/codex_oai \
        firmware/tests/codex_oai/test_keymap_contract.py
git commit -m "feat: add AgentPad13 direct OAI keymap"
```

---

### Task 5: Automatizar staging y builds QMK limpios

**Files:**
- Create: `firmware/tools/build_codex_oai.py`
- Create: `firmware/tests/codex_oai/test_build_tool.py`
- Modify: `firmware/BUILD.md`

**Interfaces:**
- Consumes: `--qmk-home`, AgentPad13 source root, `arm-none-eabi-gcc` con newlib.
- Produces: compilaciones `default`, `vial`, `codex_oai`; nunca instala ni flashea.

- [ ] **Step 1: Escribir tests RED de seguridad del staging**

```python
def test_refuses_wrong_qmk_commit(self):
    with self.assertRaisesRegex(BuildError, "00fc4627"):
        validate_qmk_home(self.fake_qmk, head="deadbeef")

def test_refuses_existing_real_keyboard_directory(self):
    (self.fake_qmk / "keyboards/loudest_micro").mkdir(parents=True)
    with self.assertRaisesRegex(BuildError, "already exists"):
        keyboard_link(self.fake_qmk, self.source)

def test_cleanup_only_unlinks_owned_symlink(self):
    link = keyboard_link(self.fake_qmk, self.source)
    cleanup_keyboard_link(link, expected_target=self.source)
    self.assertFalse(link.exists())
```

- [ ] **Step 2: Ejecutar RED**

Expected: FAIL porque `build_codex_oai.py` no existe.

- [ ] **Step 3: Implementar el staging con refusals explícitos**

El script:

1. exige un QMK home cuyo HEAD empiece por `00fc4627`;
2. verifica `quantum/via.c` y submódulos requeridos;
3. rechaza un `keyboards/loudest_micro` real o un symlink ajeno;
4. crea un symlink temporal a `firmware/loudest_micro`;
5. comprueba que el compilador encuentra `stdint.h` y newlib;
6. ejecuta lint `codex_oai` y builds limpios `default`, `vial`, `codex_oai`;
7. elimina únicamente el symlink que creó, incluso ante error;
8. no contiene las cadenas `qmk flash`, `RPI-RP2`, `/Volumes/` ni `BOOTSEL`.

Tras un build OAI correcto, copia el output QMK mediante archivo temporal +
`os.replace` a `release/firmware/prebuilt/agentpad13_codex_oai.uf2`. Nunca
reemplaza los UF2 `default` o `vial`.

- [ ] **Step 4: Preparar un QMK home aislado en el commit documentado**

Crear un worktree temporal fuera de ambos repositorios:

```bash
qmk_stage_parent="$(mktemp -d /tmp/agentpad13-qmk.XXXXXX)"
qmk_stage_dir="$qmk_stage_parent/qmk"
git -C /Users/hirlu/Documents/Projects/vial-qmk worktree add --detach "$qmk_stage_dir" 00fc4627
git -C "$qmk_stage_dir" submodule update --init --recursive
git -C "$qmk_stage_dir" apply /Users/hirlu/Documents/Projects/agentpad13/firmware/patches/0001-via-command-kb-backport.patch
```

Si submódulos o patch fallan, detener la tarea y registrar la causa; no cambiar el checkout principal.

- [ ] **Step 5: Ejecutar GREEN del build tool**

```bash
python3 -m unittest firmware.tests.codex_oai.test_build_tool -v
```

- [ ] **Step 6: Ejecutar los builds reales**

```bash
PATH="/opt/homebrew/opt/arm-none-eabi-gcc@8/bin:$PATH" \
python3 firmware/tools/build_codex_oai.py \
  --qmk-home "$qmk_stage_dir" \
  --clean
```

Expected:

```text
lint loudest_micro:codex_oai PASS
build loudest_micro:default PASS
build loudest_micro:vial PASS
build loudest_micro:codex_oai PASS
flash operations 0
```

- [ ] **Step 7: Documentar toolchain y target**

Añadir a `firmware/BUILD.md` el comando anterior, la identidad experimental y la advertencia de que el script solo compila.

- [ ] **Step 8: Commit local**

```bash
git add firmware/tools/build_codex_oai.py \
        firmware/tests/codex_oai/test_build_tool.py \
        firmware/BUILD.md
git commit -m "build: automate isolated AgentPad OAI builds"
```

---

### Task 6: Arrancar el UF2 y probar USB/OAI en rp2040js

**Files:**
- Create: `firmware/tests/emulator/oai_runner.cjs`
- Modify: `firmware/tests/emulator/package.json`
- Create: `firmware/tests/codex_oai/test_emulator_contract.py`

**Interfaces:**
- Consumes: UF2 `release/firmware/prebuilt/agentpad13_codex_oai.uf2`.
- Produces: evidencia JSON de USB, handshake, key scan y actividad WS2812.

- [ ] **Step 1: Escribir test RED del contrato de evidencia**

```python
def test_evidence_requires_oai_descriptor_and_handshake(self):
    evidence = run_oai_emulator(self.uf2)
    self.assertEqual(evidence["vid_pid"], "303a:8360")
    self.assertEqual(evidence["usage"], "ff00:0061")
    self.assertEqual(evidence["report_id"], 6)
    self.assertEqual(evidence["report_bytes"], 64)
    self.assertTrue(evidence["rgbcfg_ack"])
    self.assertTrue(evidence["thstatus_ack"])
    self.assertTrue(evidence["device_status_ack"])
    self.assertEqual(evidence["key_event"], {"k": "AG00", "act": 1})
    self.assertTrue(evidence["ws2812_activity"])
```

- [ ] **Step 2: Ejecutar RED**

Expected: FAIL porque no existe `oai_runner.cjs` ni script npm.

- [ ] **Step 3: Adaptar el runner existente sin alterar sus pruebas default/vial**

Reutilizar de `runner.cjs` únicamente boot ROM, carga UF2, enumeración y control GPIO. El nuevo runner localiza una interfaz HID vendor con Usage Page `0xFF00`, Usage `0x61`, endpoint IN/OUT de 64 bytes y Report ID 6.

Construir cada OUT report así:

```javascript
function oaiReport(json) {
  const payload = Buffer.from(json, 'utf8');
  if (payload.length > 61) throw new Error('single-frame fixture too large');
  const report = Buffer.alloc(64);
  report[0] = 6;
  report[1] = 2;
  report[2] = payload.length;
  payload.copy(report, 3);
  return report;
}
```

Enviar, en orden, `v.oai.rgbcfg`, un `v.oai.thstatus` de un slot y `device.status`; validar JSON de respuesta completo. Después llevar GP12 a nivel activo para SW1/AG00 y capturar `v.oai.hid`.

- [ ] **Step 4: Capturar actividad RGB**

Observar la configuración/actividad PIO del pin GP17 después del `thstatus`. No inferir colores desde PIO; la paridad RGB pertenece al harness C de Task 3.

- [ ] **Step 5: Añadir script npm**

```json
"smoke:codex-oai": "node oai_runner.cjs ../../../release/firmware/prebuilt/agentpad13_codex_oai.uf2 --json ../../evidence/codex-oai-emulator.json"
```

- [ ] **Step 6: Ejecutar GREEN y regresiones de emulador**

```bash
cd firmware/tests/emulator
npm run smoke:default
npm run smoke:vial
npm run smoke:codex-oai
```

Expected: tres PASS y JSON OAI con todos los campos del contrato.

- [ ] **Step 7: Commit local**

```bash
git add firmware/tests/emulator/oai_runner.cjs \
        firmware/tests/emulator/package.json \
        firmware/tests/codex_oai/test_emulator_contract.py
git commit -m "test: boot AgentPad OAI firmware in rp2040js"
```

---

### Task 7: Verificar y manifestar el artefacto sin flash

**Files:**
- Create: `firmware/tools/verify_codex_oai_artifact.py`
- Create: `firmware/tests/codex_oai/test_artifact_verifier.py`
- Create: `firmware/evidence/.gitkeep`

**Interfaces:**
- Consumes: UF2, ELF y evidencia JSON del emulador.
- Produces: manifiesto JSON reproducible o exit code no cero; no escribe dispositivos.

- [ ] **Step 1: Escribir tests RED de aceptación y rechazo**

```python
def test_accepts_exact_descriptor_symbols_and_hash(self):
    result = verify(self.good_uf2, self.good_elf, self.good_evidence)
    self.assertEqual(result["target"], "loudest_micro:codex_oai")
    self.assertEqual(result["vid_pid"], "303a:8360")
    self.assertEqual(result["report_id"], 6)
    self.assertEqual(len(result["sha256"]), 64)

def test_rejects_wrong_report_id(self):
    evidence = {**self.good_evidence, "report_id": 0}
    with self.assertRaisesRegex(VerificationError, "report ID"):
        verify(self.good_uf2, self.good_elf, evidence)

def test_rejects_missing_oai_symbol(self):
    with self.assertRaisesRegex(VerificationError, "codex_oai_notify"):
        verify_symbols({"raw_hid_receive", "codex_led_render"})
```

- [ ] **Step 2: Ejecutar RED**

Expected: FAIL por módulo ausente.

- [ ] **Step 3: Implementar verificación estricta**

El script:

- calcula tamaño y SHA-256 del UF2;
- ejecuta `arm-none-eabi-size` sobre ELF y registra text/data/bss;
- ejecuta `arm-none-eabi-nm -g` y exige `raw_hid_receive`, `codex_oai_notify`, `codex_led_render`, `encoder_update_user`;
- exige evidencia `303a:8360`, `ff00:0061`, Report ID 6, 64 bytes y tres ACK;
- rechaza paths que no sean archivos regulares o sean symlinks;
- escribe el manifiesto solo bajo `firmware/evidence/` mediante archivo temporal + `os.replace`;
- no importa módulos HID, no abre volúmenes y no contiene funciones de flash.

- [ ] **Step 4: Ejecutar GREEN**

```bash
python3 -m unittest firmware.tests.codex_oai.test_artifact_verifier -v
```

- [ ] **Step 5: Generar el manifiesto real**

```bash
python3 firmware/tools/verify_codex_oai_artifact.py \
  --uf2 release/firmware/prebuilt/agentpad13_codex_oai.uf2 \
  --elf "$qmk_stage_dir/.build/loudest_micro_codex_oai.elf" \
  --emulator-evidence firmware/evidence/codex-oai-emulator.json \
  --output firmware/evidence/codex-oai-manifest.json
```

Expected: JSON `status: pass` con hash y métricas reales.

- [ ] **Step 6: Commit local**

```bash
git add firmware/tools/verify_codex_oai_artifact.py \
        firmware/tests/codex_oai/test_artifact_verifier.py \
        firmware/evidence
git commit -m "test: gate AgentPad OAI firmware artifact"
```

---

### Task 8: Documentar evidencia y preparar la prueba física

**Files:**
- Create: `firmware/loudest_micro/keymaps/codex_oai/README.md`
- Create: `docs/codex-oai-prehardware-results.md`
- Create: `docs/codex-oai-physical-runbook.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: resultados frescos de Tasks 1–7 y manifiesto real.
- Produces: documentación reproducible y matriz física PENDING; ninguna instrucción se ejecuta automáticamente.

- [ ] **Step 1: Escribir el README del keymap**

Documentar identidad, layout de 15 controles, tabla de LEDs, controles allowlisted, ausencia de helper/Vial, build seguro y advertencia de identidad local.

- [ ] **Step 2: Registrar resultados pre-hardware con comandos y exits reales**

`docs/codex-oai-prehardware-results.md` incluye:

- commit AgentPad13 y commit QMK;
- versión del compilador;
- conteos exactos de tests;
- tamaños text/data/bss;
- SHA-256 UF2;
- descriptor/emulador PASS;
- regresiones default/vial PASS;
- `flash_operations: 0`.

- [ ] **Step 3: Crear runbook físico completamente PENDING**

La matriz debe incluir:

```text
BOOTSEL recovery                       PENDING
USB 303A:8360 / FF00:61 / report 6    PENDING
rgbcfg + thstatus + device.status      PENDING
AG00..AG05                             PENDING
ACT06..ACT12                           PENDING
ENC / ENC_CW / ENC_CC                  PENDING
touch -> AG00                          PENDING
slot LEDs 0..5                         PENDING
action LEDs 6..12                      PENDING
link LED 13                            PENDING
underglow 14..23                       PENDING
restore normal firmware                PENDING
```

El runbook exige en el futuro una autorización literal con target, SHA-256 y número de flashes. No incluye un comando que se lance al abrir el documento.

- [ ] **Step 4: Añadir entrada experimental al README raíz**

Enlazar al keymap y a resultados, marcándolo como laboratorio local y separado de los UF2 normales.

- [ ] **Step 5: Verificar documentación**

```bash
rg -n 'PENDING|303A:8360|FF00:61|Report ID 6|flash_operations: 0' \
  docs/codex-oai-*.md firmware/loudest_micro/keymaps/codex_oai/README.md
git diff --check
```

- [ ] **Step 6: Commit local**

```bash
git add README.md \
        firmware/loudest_micro/keymaps/codex_oai/README.md \
        docs/codex-oai-prehardware-results.md \
        docs/codex-oai-physical-runbook.md
git commit -m "docs: record AgentPad OAI prehardware validation"
```

---

### Task 9: Puerta final de verificación pre-hardware

**Files:**
- Modify only if evidence is stale: `docs/codex-oai-prehardware-results.md`
- Modify only if artifact changes: `firmware/evidence/codex-oai-manifest.json`

**Interfaces:**
- Consumes: repositorio completo y QMK home aislado.
- Produces: veredicto final pre-hardware; no cambia estado externo.

- [ ] **Step 1: Ejecutar todos los tests host desde AgentPad13**

```bash
python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py' -v
```

Expected: cero failures/errors.

- [ ] **Step 2: Repetir lint y los tres builds limpios**

```bash
PATH="/opt/homebrew/opt/arm-none-eabi-gcc@8/bin:$PATH" \
python3 firmware/tools/build_codex_oai.py \
  --qmk-home "$qmk_stage_dir" \
  --clean
```

Expected: lint OAI + builds default/vial/OAI PASS.

- [ ] **Step 3: Repetir los tres smoke tests RP2040**

```bash
cd firmware/tests/emulator
npm run smoke:default
npm run smoke:vial
npm run smoke:codex-oai
```

Expected: tres PASS.

- [ ] **Step 4: Repetir el verificador sobre los artefactos recién construidos**

Ejecutar el comando de Task 7 y comparar el JSON con el manifiesto registrado. Si cambia el hash por un cambio fuente conocido, actualizar resultados y volver a ejecutar desde Step 1; si cambia sin cambio fuente, detenerse.

- [ ] **Step 5: Verificar aislamiento y ausencia de operaciones físicas**

```bash
git diff --check
git status --short
git diff -- firmware/loudest_micro/keymaps/default firmware/loudest_micro/keymaps/vial
rg -n 'qmk flash|avrdude|/Volumes/RPI-RP2|diskutil|mount ' \
  firmware/tools firmware/tests/codex_oai
```

Expected: diff de default/vial vacío; búsqueda de operaciones físicas vacía; los dos archivos ajenos originales siguen sin staged.

- [ ] **Step 6: Revisar requisito por requisito contra la spec**

Confirmar explícitamente los nueve puntos de “Validación antes de recibir la PCB” en `docs/codex-oai-prehardware-results.md`. Ninguna fila física se marca PASS.

- [ ] **Step 7: Commit final local solo si cambió evidencia**

```bash
git add docs/codex-oai-prehardware-results.md firmware/evidence/codex-oai-manifest.json
git commit -m "test: finalize AgentPad OAI prehardware evidence"
```

No push y no flash.

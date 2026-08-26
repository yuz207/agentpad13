# AgentPad13 Direct OAI — Especificación de diseño

> **Especificación histórica:** conserva las decisiones y enmiendas del diseño
> original. Las comparaciones con prototipos previos se han retirado para que
> este documento describa únicamente AgentPad13. El artefacto actual es
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2`, 93.696 bytes, SHA-256
> `fcb50b2419419be43b7cf90b00a96b16063fcaf182bc24b9642d57e2e8adf54d`;
> la validación física sigue PENDING y no hubo flash.

Fecha: 2026-08-09
Estado: propuesta revisada para validación pre-hardware

## Objetivo

Demostrar, antes de que llegue la PCB de AgentPad13, que el hardware puede
ejecutar directamente el software OAI ya validado con la Raspberry Pi Pico:
Codex Desktop hablará con el teclado mediante Raw HID, el teclado
responderá al handshake OAI, emitirá los controles físicos admitidos y
representará en sus 24 LEDs RGB los estados de hasta seis tareas.

No habrá helper entre Codex y el teclado en este experimento.

```text
Codex Desktop
     │  OAI Raw HID directo
     ▼
AgentPad13 codex_oai
     ├── rgbcfg / thstatus / device.status
     ├── AG00..AG05 / ACT06..ACT12 / ENC
     └── 24 LEDs RGB
```

## Ubicación del trabajo

Todo el código, las pruebas, los oráculos Python, la documentación y los
artefactos de validación se guardarán en:

```text
/Users/hirlu/Documents/Projects/agentpad13
```

El checkout `/Users/hirlu/Documents/Projects/vial-qmk` será una fuente de
referencia y el árbol externo de compilación QMK. No será el destino de los
cambios de esta fase.

## Estrategia de aislamiento

Se añadirá un keymap experimental independiente:

```text
firmware/loudest_micro/keymaps/codex_oai/
```

Los keymaps `default` y `vial` de AgentPad13 permanecerán funcionalmente
intactos. El target `codex_oai` desactivará Vial porque el descriptor OAI
experimental no es el descriptor Raw HID/Vial normal de AgentPad13.

El código común solo recibirá guardas de compilación explícitas para permitir
que `codex_oai.c` sea propietario de `raw_hid_receive()` y del overlay RGB en
este target. En cualquier otro keymap continuará activo el protocolo de estado
AgentPad13 de 32 bytes existente.

## Contrato USB experimental

El target local reproducirá el contrato ya observado y validado:

| Campo | Valor |
|---|---|
| VID/PID | `303A:8360` |
| Manufacturer / Product | `hirlu` / `Codex Micro Lab OAI LED` |
| Device version | `0x0005` para distinguir el port AgentPad13 |
| Usage Page / Usage | `FF00:61` |
| Report ID | `6` |
| Tamaño | 64 bytes totales; 63 bytes de datos |
| Canales | debug `1`, RPC `2` |
| Fragmento RPC | máximo 61 bytes |

Esta identidad pertenece a un tercero y se utilizará exclusivamente para la
prueba local. El target no se publicará ni se instalará en hardware sin una
revisión explícita del artefacto y una autorización de flash específica.

## Protocolo OAI

Se portará el motor comprobado de `codex_micro_lab_oai_led` con estas
responsabilidades:

- reassembly acotado de mensajes JSON fragmentados;
- profundidad JSON máxima 8 y buffer RX acotado;
- respuesta exacta a `v.oai.rgbcfg`, `v.oai.thstatus` y `device.status`;
- readiness únicamente después de recibir `rgbcfg` y `thstatus` válidos;
- rechazo silencioso o respuesta acotada para métodos y frames no admitidos;
- emisión de eventos físicos solo cuando el motor está ready;
- conservación de seis slots OAI con color, efecto, brillo, velocidad y flags;
- revisión monotónica del estado para actualizar LEDs solo cuando sea necesario.

No se añadirán métodos inferidos. El contrato seguirá las capturas, fixtures y
tests ya existentes en `codex_micro_lab`.

## Mapeo físico

Las trece posiciones físicas conservan el orden oficial validado por el
prototipo Direct OAI anterior:

```text
AG00   AG01   AG02   AG03
AG04   AG05   ACT06  ACT07
ACT08  ACT09  ACT10  ACT11
2U=ACT12/SEND
```

Controles adicionales de AgentPad13:

- tecla 2U `[3,0]`: `MICROPHONE` mediante press/release `ACT10`;
- click del encoder `[3,1]`: `ENC` press/release;
- touch `[3,2]`: duplicado de `AG00` para verificar el sensor capacitivo;
- encoder CW: `ENC_CW`, `act=2`;
- encoder CCW: `ENC_CC`, `act=2`;
- joystick: permanece enumerado por QMK, pero no se enviarán eventos OAI
  inventados porque el protocolo observado no define controles de joystick.

### Enmienda física 2026-08-18

La placa tiene trece teclas físicas: las doce teclas de la matriz y una tecla
2U separada; el click del encoder y TP5 son controles adicionales. La matriz
conserva `ACT10`/ACCEPT en la tecla 11 (`[2,2]`) y `ACT11` en la tecla 12
(`[2,3]`). La 2U (`[3,0]`) es `ACT12`/`SEND`. El mapa OAI de fábrica
correspondiente es `123456789abfcd1`; el índice interno 12 representa la ruta
2U. El dígito legacy `e` (`MICROPHONE`) sigue aceptándose en mapas
personalizados y se enruta por `ACT10`.

`AG00..AG05` solo emiten su evento de press. `ACT06..ACT12` y `ENC` emiten
press/release. Los giros emiten un único evento `act=2`.

## Arquitectura de LEDs

AgentPad13 dispone de trece LEDs por tecla, un indicador y diez LEDs de
underglow. Se conservarán el RGB, brillo, velocidad y efecto recibidos en
`v.oai.thstatus`; los 24 LEDs de AgentPad13 permiten representar el color sin
codificarlo mediante destellos.

### Distribución

| LEDs | Uso |
|---|---|
| 0–5 | slots OAI 0–5, junto a `AG00..AG05` |
| 6–12 | feedback local de las funciones `ACT06..ACT12` al pulsar |
| 12 | feedback local de la posición 2U `ACT12`/SEND / resumen de tarea activa |
| 13 | handshake: esperando, ready o error de protocolo |
| 14–23 | estado global de la tarea activa mediante underglow |

Un slot invisible —color negro, brillo cero o efecto cero— apaga su LED. La
tarea global se seleccionará con la misma prioridad ya validada: un slot con
efecto working tiene prioridad; en su ausencia se usa el primer slot visible.

### Animaciones

El motor trabajará con aritmética entera y tiempo modular de 32 bits. Portará
la matriz de efectos 0–6 y el patrón working comprobado:

- efecto 0: apagado;
- efecto 1: sólido/patrón determinado por el estado recibido;
- efecto 2: blink;
- efecto 3: ripple;
- efecto 4: breath/working;
- efecto 5: spark;
- efecto 6: beacon.

El patrón azul working especial conservará su triple destello, onda de nueve
pasos, triple destello y pausa. La intensidad calculada se multiplicará por el
RGB original, en vez de producir un único nivel PWM monocromo.

Los LEDs de acción tendrán un feedback corto y local que no modifica el estado
OAI. Al terminar ese feedback volverán al estado base. El underglow reflejará
la tarea global a intensidad reducida y con el mismo reloj de animación.

## Reutilización del software Python RP2040

El código Python existente se empleará como oráculo, no como firmware final de
AgentPad13:

- `rp2040_oai_emulator/oai_engine.py`: framing, reassembly, respuestas y
  eventos OAI;
- `tools/oai_led_lab.py`: selección de slots, efectos, working pattern y
  rollover;
- fixtures `v.oai.rgbcfg` y `v.oai.thstatus`: entradas deterministas;
- tests de paridad existentes: referencia byte a byte frente al C de QMK.

Dentro de AgentPad13 se añadirá una copia mínima y autónoma del oráculo
necesario para que sus pruebas no dependan de otro repositorio. El oráculo
producirá timelines RGB para seis slots y se comparará contra un harness que
compile el C real del nuevo target.

## Archivos previstos

```text
firmware/loudest_micro/keymaps/codex_oai/
  config.h
  rules.mk
  keymap.c
  codex_oai.c
  codex_oai.h
  codex_led.c
  codex_led.h
  README.md

firmware/tests/codex_oai/
  protocol_oracle.py
  led_oracle.py
  protocol_harness.c
  led_harness.c
  test_protocol.py
  test_leds.py
  test_keymap_contract.py

firmware/tools/
  build_codex_oai.py
  verify_codex_oai_artifact.py

docs/
  codex-oai-prehardware-results.md
  codex-oai-physical-runbook.md
```

`build_codex_oai.py` preparará el árbol de build sin escribir en el teclado.
`verify_codex_oai_artifact.py` comprobará target, tamaño, SHA-256, descriptor,
Report ID y símbolos esperados antes de que exista cualquier autorización de
flash.

## Validación antes de recibir la PCB

La fase se considera validada en software cuando pase todo lo siguiente:

1. Pruebas del parser, reassembly, límites, readiness y respuestas OAI.
2. Paridad byte a byte entre el motor C y el oráculo Python.
3. Las quince entradas físicas generan únicamente los controles allowlisted.
4. Los seis slots se proyectan en sus LEDs correctos y conservan RGB, brillo,
   velocidad y efecto.
5. El patrón working y los efectos 0–6 coinciden con el timeline Python,
   incluido rollover de `uint32_t`.
6. El target `loudest_micro:codex_oai` pasa lint y build limpio.
7. Los targets `default` y `vial` continúan compilando sin cambios funcionales.
8. El UF2 arranca en el emulador RP2040, enumera teclado + OAI Raw HID y
   completa el handshake OAI con el descriptor esperado.
9. El verificador genera un manifiesto reproducible con SHA-256 y no contiene
   ninguna ruta de flash implícita.

Los resultados, comandos y logs se conservarán dentro de AgentPad13.

## Verificación física posterior

Cuando llegue la placa habrá un paso separado y autorizado:

1. comprobar identidad física y BOOTSEL;
2. construir de nuevo y comparar el manifiesto aprobado;
3. copiar el UF2 autorizado;
4. verificar enumeración `303A:8360`, `FF00:61`, Report ID 6;
5. observar handshake `rgbcfg + thstatus + device.status`;
6. probar `AG00..AG05`, `ACT06..ACT12`, encoder y touch;
7. comprobar cada slot LED y el underglow con cambios de estado reales;
8. restaurar el firmware AgentPad13 normal al terminar si se desea.

No se flasheará nada durante la implementación pre-hardware.

## Fuera de alcance

- helper Python entre Codex y AgentPad13;
- Vial dentro del target OAI experimental;
- inventar eventos OAI para el joystick;
- modificar PCB, GPIOs o el orden físico de la cadena WS2812;
- publicar la identidad USB experimental de terceros;
- flash, commit remoto o push sin autorización posterior.

## Addendum — 2026-08-18: official ACT11 physical order

The implemented CODEX map uses the official thirteen-action order through
position 12: `AG00..AG05`, `ACT06..ACT12`. Position 13 remains encoder click
and position 14 is retained only for wire compatibility. On the AgentPad13
geometry, matrix key 11 is the protected `ACT10`/ACCEPT route, matrix key 12
is `ACT11` (the second microphone contact), and the separate 2U key is
`ACT12`/SEND. The old `MICROPHONE` action digit is still accepted in custom
maps as a compatibility alias for ACT10.

The wear-leveling schema is version 3. Both earlier factory maps migrate to
`123456789abfcd1`; user-defined maps are preserved. This correction is covered
by the C/Python protocol tests, the keymap contract, a clean pinned-QMK build,
and the RP2040 emulator. No hardware flash has occurred.

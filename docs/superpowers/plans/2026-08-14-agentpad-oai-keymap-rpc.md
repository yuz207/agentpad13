# Implementación RPC de personalización de la capa OAI

> **Plan histórico:** conserva la secuencia y los contratos de esta fase. Sus
> artefactos intermedios están superseded por
> `release/firmware/prebuilt/agentpad13_codex_oai.uf2` (93.696 bytes, SHA-256
> `fcb50b2419419be43b7cf90b00a96b16063fcaf182bc24b9642d57e2e8adf54d`).
> La validación física sigue PENDING y no hubo flash.

> **Nota de ejecución:** aplicar este plan tarea por tarea, manteniendo el firmware de las capas BASE/FN sin cambios de contrato y sin realizar ningún flash.

**Objetivo:** permitir que Codex lea y personalice por HID directo la capa CODEX/OAI del AgentPad13 mediante `v.oai.keymap.get` y `v.oai.keymap.set`, con validación atómica, persistencia wear-levelled y restauración segura de la asignación por defecto.

**Diseño:** la capa OAI conserva 15 posiciones físicas (12 teclas de matriz, hero/2U, click del encoder y touch). El mapa se transporta como 15 dígitos hexadecimales compactos: cada dígito es una acción `0..d`. El firmware mantiene el mapa en RAM, lo valida antes de sustituirlo y guarda una copia versionada con checksum en el área de almacenamiento del RP2040. La ruta de eventos consulta el mapa para traducir cada posición a los controles OAI o a su fallback nativo; las capas FN y BASE siguen siendo compilables/personalizables en QMK.

## Contrato

- `v.oai.keymap.get`, `params: {"l":0}` devuelve `{"result":{"l":0,"m":"...15 hex..."},"id":N}`.
- `v.oai.keymap.set`, `params: {"l":0,"m":"...15 hex..."}` devuelve `{"result":true,"id":N}`.
- Solo se acepta `l=0` (CODEX/OAI). Mapas de longitud incorrecta, dígitos fuera de `0..d`, JSON duplicado/desconocido o `ENC` fuera de la posición 13 se rechazan con un error y dejan intacto el mapa anterior.
- Valores: `0 NOOP`, `1 PREVIOUS`, `2 NEXT`, `3 NEW`, `4 REVIEW`, `5 PLAN`, `6 IMPLEMENT`, `7 REFACTOR`, `8 TEST`, `9 ABORT`, `a SAFE`, `b ACCEPT`, `c SEND`, `d ENC`.
- Mapa inicial: `123456789abccd1` (posición 12 repite SEND, posición 13 es click de encoder y posición 14 conserva PREVIOUS/touch).

## Tareas

### 1. Fijar el contrato con pruebas RED

- Extender el harness RPC y `test_protocol.py` con GET por defecto, SET válido/round-trip, rechazo atómico de mapas inválidos y persistencia tras reinicializar el firmware.
- Añadir stubs de wear-leveling únicamente al harness para que las pruebas puedan simular almacenamiento no volátil sin QMK.
- Añadir aserciones de que el contrato solo expone la capa 0 y que las respuestas están dentro del payload Raw HID de 61 bytes.
- Ejecutar la suite enfocada y conservar el fallo RED antes de añadir producción.

### 2. Implementar mapa OAI y persistencia

- Añadir tipos, constantes y API pública en `codex_oai.h`.
- Implementar defaults, conversión hexadecimal, validación completa, checksum/magic/version y lectura/escritura atómica en `codex_oai.c`.
- Cargar el mapa durante `codex_oai_init`; ante almacenamiento ausente/corrupto usar defaults y poder reescribirlos mediante `codex_oai_reset_keymap`.
- Evitar colisiones con `eeconfig` usando una dirección wear-leveling fuera de `EECONFIG_SIZE`; no alterar helper/Vial ni otras familias de keymap.
- Ejecutar las pruebas RPC hasta GREEN.

### 3. Implementar los métodos RPC

- Extender el parser existente para aceptar `v.oai.keymap.get/set`, validar `params` estrictamente y rechazar capas/maps inválidos.
- Emitir respuestas compactas y errores deterministas; conservar el comportamiento de los métodos RGB/status existentes y sus revisiones.
- Cubrir errores de JSON, duplicados, longitud, caracteres y `ENC` mal posicionado.
- Ejecutar suite de protocolo, `py_compile` y `git diff --check`.

### 4. Conectar la capa CODEX/OAI al mapa dinámico

- Sustituir la traducción fija de los 15 keycodes OAI por una función posición→acción que consulte el mapa.
- Mantener los temporizadores y gestos existentes: ACCEPT corto/mantenido, SAFE armado, NEW corto/largo, SEND, click de encoder/cambio de capa/OS y touch.
- Mantener encoder giratorio y capa FN sin cambios de contrato; limitar `ENC` configurable al click del encoder para evitar gestos ambiguos.
- Añadir pruebas estáticas y de regresión que confirmen dos capas por defecto, extensiones opcionales y ausencia de deriva en default/Vial.

### 5. Build, emulación y evidencia

- Construir en el QMK fijado con el patch de descriptor ya registrado, ejecutando `make clean` real antes de cada target.
- Verificar default, Vial y OAI; ejecutar las 58+ pruebas host, smokes de emulador, `py_compile`, `node --check` y `git diff --check`.
- Regenerar UF2/ELF, manifest y evidencia; comprobar descriptor `303A:8360`, Raw HID report ID 6/64 bytes, tamaño/hash, símbolos y límite RGB.
- Actualizar README, resultados prehardware y runbook con el protocolo y el nuevo hash.

### 6. Revisión y cierre técnico

- Revisar el diff limitado al worktree AgentPad13; no tocar el repo vial-qmk
  sucio, firmware ajeno, helper ni hardware.
- Ejecutar revisión final de tests y documentar que no hubo flashes.
- Dejar el branch listo para una futura instalación física, sin commit/push adicional salvo autorización explícita.

## Verificación final

```text
python3 -m unittest discover -s firmware/tests/codex_oai -p 'test_*.py' -v
npm run smoke:codex-oai --prefix firmware/tests/emulator
npm run smoke:default --prefix firmware/tests/emulator
npm run smoke:vial --prefix firmware/tests/emulator
python3 -m py_compile firmware/tools/*.py firmware/tests/codex_oai/*.py
node --check firmware/tests/emulator/oai_runner.cjs
git diff --check
```

No se considera completado hasta que el protocolo GET/SET, la persistencia y la regresión del firmware estén en verde y el artefacto reproducible haya sido verificado.

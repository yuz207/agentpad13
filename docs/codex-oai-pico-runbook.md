# AgentPad13 direct OAI en Raspberry Pi Pico (RP2040)

Este montaje permite validar el firmware `loudest_micro:codex_oai` antes de
recibir la placa AgentPad13. La Pico se usa como banco de entradas: cada
entrada tiene pull-up interno y una pinza que la une momentáneamente a GND
simula una pulsación.

## Preparación eléctrica

- Con el USB arriba, usa los números de pin físicos de la tabla; no los
  confundas con el número `GPx`.
- Pulsa conectando **solo** un GPIO de entrada a un pin GND de la Pico.
- Suelta retirando la pinza: el pull-up devuelve la entrada a nivel alto.
- No conectes un GPIO a 3V3, VBUS, VSYS, RUN ni 3V3_EN.
- GP17 es una salida WS2812: no lo cortocircuites a GND. La Pico desnuda no
  tiene la cadena de 24 RGB; el LED integrado de la Pico está en GP25 y este
  keymap no lo controla.

## Pinout de pruebas

| Control OAI / función | GPIO | Pin físico Pico |
|---|---:|---:|
| AG00 / K00 | GP12 | 16 |
| AG01 | GP9 | 12 |
| AG02 | GP5 | 7 |
| AG03 | GP2 | 4 |
| AG04 | GP11 | 15 |
| AG05 | GP8 | 11 |
| ACT06 | GP4 | 6 |
| ACT07 | GP1 | 2 |
| ACT08 | GP10 | 14 |
| ACT09 | GP7 | 10 |
| ACCEPT / ACT10 (matriz, tecla 11) | GP3 | 5 |
| ACT11 (matriz, tecla 12) | GP0 | 1 |
| ACT12 / SEND (tecla 2U) | GP6 | 9 |
| ENC / pulsación del encoder | GP15 | 20 |
| Touch TP5 (cambio de capa) | GP16 | 21 |
| Encoder A | GP13 | 17 |
| Encoder B | GP14 | 19 |
| WS2812 DIN (salida; no puentear) | GP17 | 22 |

Usa cualquiera de estos GND: pines físicos 3, 8, 13, 18, 23, 28 o 38.

## Pruebas con pinzas

1. Con la Pico desconectada, mantén BOOTSEL, conecta USB y suelta BOOTSEL
   cuando aparezca `RPI-RP2`.
2. Solo después de una autorización explícita se copia el UF2 autorizado. La
   copia reinicia la Pico y el volumen desaparece; espera la enumeración HID.
3. Inicializa el enlace desde el host con `v.oai.rgbcfg`, `v.oai.thstatus` y
   `device.status`. Sin ese handshake los controles deben permanecer mudos.
4. Para cada fila de la tabla, une el GPIO a GND durante 100–200 ms y retira
   la pinza. Registra el evento OAI observado y comprueba que no aparece otro.
5. Para el encoder, mantén ambas entradas en alto y simula una vuelta con la
   secuencia de estados `00 → 01 → 11 → 10 → 00` (A/B a GND según cada bit).
   Si el sentido sale invertido, intercambia A y B; no cambies el firmware.
6. GP16/TP5 debe ciclar las capas `CODEX -> FN -> NAV -> MEDIA -> CODEX` sin
   generar un control OAI. GP0 (matriz, tecla 12) produce `ACT11` y GP6 (la
   tecla 2U) produce `ACT12`/SEND; comprueba que son rutas distintas. GP15
   produce `ENC`.

## Artefacto host validado

Antes de escribir la Pico, verifica siempre el manifiesto local:

- Target: `loudest_micro:codex_oai`
- Archivo: `release/firmware/prebuilt/agentpad13_codex_oai.uf2`
- UF2: 93.696 bytes
- SHA-256: `64cd5f40cd444f519222baa17437f42cea45b41617ac133ea577dd312c39ae3c`
- USB: `303A:8360`, Raw HID `FF00:0061`, Report ID 6, 64 bytes

Con el handshake todavía no iniciado, CODEX usa el fallback nativo. TP5 recorre
`CODEX -> FN -> NAV -> MEDIA -> CODEX`; F2–F12 están en FN y `TP_TOG` en NAV.
El click del encoder no cambia de capa: cuando OAI está listo emite `ENC`, y el
giro emite `ENC_CW`/`ENC_CC` (con fallback nativo de razonamiento en CODEX y
scroll en FN antes de readiness).

Las pruebas de emulador y protocolo no sustituyen la matriz física: dejan
pendientes el montaje, los eventos observados y la recuperación BOOTSEL. No se
ha instalado ni flasheado automáticamente este artefacto. Antes de cualquier
operación física se exige la autorización literal de
[`codex-oai-physical-runbook.md`](codex-oai-physical-runbook.md).

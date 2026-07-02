---
name: bring-up
description: Secuencia segura de encendido del Tapete (primera energización y calibración del umbral FSR). Úsalo cuando el hardware esté armado y vayas a energizar por primera vez. Es una guía para el HUMANO — el agente nunca flashea ni abre el serial (lo bloquea guard-flash).
user-invocable: true
allowed-tools:
  - Read
---

# bring-up — Encendido seguro del Tapete

Guía para energizar el prototipo por primera vez **sin dañar el ESP32** (único,
alimentado solo por USB). **El agente no flashea ni abre el serial**: esos pasos
los hace el humano, conscientemente (los bloquea el hook `guard-flash`). El agente
guía, interpreta lo que el humano pega, y ayuda a calibrar.

## Antes de energizar (obligatorio)
1. **Checklist con multímetro** — corre `docs/hardware/cableado.md` §6 **entero**:
   continuidad de GND, ausencia de corto 3V3↔5V, rieles correctos, polaridad.
   NO energizar si algún punto falla.
2. Verifica la secuencia de armado `cableado.md` §7 y las decisiones congeladas
   (`00_diseno_circuito.md` §2). Confirma valores contra `materiales.md`.
3. microSD grabada FAT32 con `/mp3/0001.mp3`..`/mp3/0004.mp3` (ver `audio/README.md`).
4. `cp firmware/src/secrets.h.example firmware/src/secrets.h` + credenciales WiFi.

## Energizar y flashear (lo hace el HUMANO)
5. Conecta el ESP32 por USB a la PC (única fuente).
6. El humano compila y flashea, y abre el monitor serial. Comandos en
   `docs/hardware/flashing.md`. (El agente no ejecuta `pio ... upload` ni
   `device monitor` — `guard-flash` los deniega.)

## Calibrar el umbral FSR
7. Con el serial abierto, el humano **pisa cada botón** y observa el valor del ADC.
8. Ajusta `cfg::UMBRAL_PISADA` en `Config.h` a un valor entre reposo y pisada firme
   (ver `flashing.md`); recompila y reflashea. El agente ayuda a elegir el umbral a
   partir de los valores que el humano pegue del serial.

## Verificación end-to-end
9. `dashboard/app.py --tcp <IP_ESP32>` contra el hardware real; confirma eventos
   (hello, led, pisada) y audio.

Unidades explícitas. Ante cualquier duda de un pin/valor: **detente y pregunta**.

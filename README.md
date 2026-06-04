# Tapete Interactivo Terapéutico

Sistema completo de un tapete físico con **6 botones** para terapia de niños con
síndrome de Down. Cada botón detecta la pisada (sensor FSR) y se ilumina (LEDs
blancos). Un **ESP32** ejecuta tres modos de juego terapéuticos, reproduce
sonidos de refuerzo y envía datos en tiempo real a una PC, donde un **dashboard**
permite al terapeuta monitorear y configurar las sesiones.

> **Principio rector:** una sola fuente de verdad para la lógica de juego
> (`GameCore`, C++ portable), validada en software (simulador + tests) y
> reutilizada **sin cambios** en el ESP32.

## Estado del proyecto

Construcción por fases (ver la especificación maestra en
`Tapete Interactivo Terapéutico — Especificación maestra para Claude Code.md`):

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Andamiaje (estructura, protocolo, golden vectors, runner de tests) | en curso |
| 2 | GameCore + tests unitarios + golden vectors | pendiente |
| 3 | Simulador visual (Pygame) | pendiente |
| 4 | Dashboard del terapeuta (PyQt6 + SQLite) | pendiente |
| 5 | Firmware ESP32 (FSR/LED/DFPlayer + WiFi/TCP) | pendiente |
| 6 | Documentación completa | pendiente |

## Estructura

```
firmware/   PlatformIO. lib/GameCore = lógica portable (fuente de verdad). src/ = ESP32.
simulator/  Simulador visual (Pygame) que carga GameCore.so vía ctypes.
dashboard/  Interfaz del terapeuta (PyQt6 + SQLite + export CSV/PDF).
shared/     protocol.md + golden_vectors.json (contrato común C++/Python).
audio/      MP3 para el DFPlayer (000X.mp3).
docs/       wiring.md, flashing.md, validation.md.
scripts/    run_all_tests.sh (corre TODOS los tests).
```

## Correr todos los tests

```bash
# Requisitos: g++ (C++17) y un venv de Python con pytest.
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
./scripts/run_all_tests.sh
```

(Comandos exactos para simulador, dashboard y flasheo del ESP32: ver Fase 6 /
sección final de este README cuando esté completa.)

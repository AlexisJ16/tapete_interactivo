# Tapete Interactivo Terapéutico — Guía para Claude

Sistema completo de un tapete físico de **6 botones** (terapia de niños con
síndrome de Down): cada botón = 1 sensor **FSR** (pisada) + 3 **LEDs blancos**
(no RGB). Un **ESP32** corre 3 modos de juego, reproduce sonidos (DFPlayer) y
habla con un **dashboard** de PC en tiempo real.

> **Principio rector (no negociable):** una sola fuente de verdad para la lógica.
> `firmware/lib/GameCore/` (C++17 portable, sin Arduino) se compila como
> `build/libgamecore.so` y el simulador lo carga por `ctypes`. El **mismo**
> GameCore se compila para el ESP32. No hay dos implementaciones.

## Estado actual (todo verde)

Las 6 fases del plan (`Tapete Interactivo Terapéutico — Especificación maestra
para Claude Code.md`) están **completas y validadas**:

- GameCore (RNG, protocolo, motor, 3 modos) — tests doctest, ~2118 aserciones.
- Simulador Pygame + puente ctypes + servidor TCP + golden runner.
- Dashboard PyQt6 + SQLite + export CSV/PDF + integración (FuenteCore y FuenteTCP).
- Firmware ESP32 (`EspHardware` + WiFi/TCP) — **compila para `esp32dev`**.
- Documentación completa en `docs/` y `README.md`.

`./scripts/run_all_tests.sh` → **TODO VERDE** (34 casos C++ + 16 pytest).
`pio run -e esp32dev` → **SUCCESS** (Flash ~60%, RAM ~14%).

Próximos pasos y mejoras: ver `docs/ROADMAP.md`.

## Comandos clave

```bash
# Entorno (una vez)
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -r simulator/requirements.txt -r dashboard/requirements.txt

# TODOS los tests (C++ doctest + .so + pytest)
./scripts/run_all_tests.sh

# Apps (hay display real en esta máquina: DISPLAY=:0 / Wayland)
.venv/bin/python simulator/tapete_sim.py            # ventana: clic = pisada
.venv/bin/python dashboard/app.py                   # dashboard embebido
.venv/bin/python dashboard/app.py --tcp <IP_ESP32>  # contra hardware real

# Firmware
cd firmware && pio run -e esp32dev                  # compila (no flashea)
pio run -e esp32dev -t upload && pio device monitor -b 115200

# Evidencia visual (capturas/GIF a /tmp/tapete_demo/)
.venv/bin/python scripts/demo_visual.py
```

## Convenciones (respetar)

- **TDD:** test primero, verlo fallar, mínimo para pasar. No avanzar de fase con
  tests en rojo. Tests C++ con **doctest** (en `firmware/test/vendor/`, sin
  PlatformIO); tests Python con **pytest**.
- **GameCore sin Arduino:** nada de `analogRead`/`ledcWrite`/`millis()` de Arduino
  dentro de `lib/GameCore/`. El hardware entra por la interfaz `IHardware`; los
  modos solo usan `IMotor`. El motor es **no bloqueante** (se le pasa el tiempo;
  nunca `delay()`).
- **Determinismo:** RNG propio **xorshift32** seedable (no `rand()`). Es la base
  de los **golden vectors** (`shared/golden_vectors.json`), que se reproducen
  contra el `.so` y prueban C++ y simulador a la vez.
- **Protocolo:** líneas JSON `\n` (Serial/TCP 3333). Mini-serializador propio
  (sin ArduinoJson), parseo idéntico en ambos lados. Spec: `shared/protocol.md`.
- **Sin secretos en git:** credenciales WiFi en `firmware/src/secrets.h`
  (gitignored; plantilla en `secrets.h.example`).
- **Commits pequeños por fase**, trailer `Co-Authored-By: Claude...`.

## Trampas conocidas (ya resueltas, no reintroducir)

- **La ruta del proyecto tiene un espacio** ("Tapete Interactivo"): un `-I` sin
  comillas se rompe por word-splitting. `run_all_tests.sh` usa rutas relativas y
  arrays; al compilar a mano, `cd` al raíz y usa rutas relativas.
- **PlatformIO instala Arduino-ESP32 core 2.0.17** (LEDC por *canal*). El código
  soporta ambas APIs vía `ESP_ARDUINO_VERSION` en `EspHardware.cpp`. No volver a
  asumir solo la API 3.x (`ledcAttach`/`ledcWrite(pin,...)`).
- **PEP 668:** usar siempre el `.venv` del proyecto, no el pip del sistema.
- **Audio ESP32:** los MP3 van en `/mp3/000X.mp3` de la SD (`playMp3Folder`).

## Estructura

```
firmware/lib/GameCore/   Lógica portable (fuente de verdad) + bridge.cpp (C ABI)
firmware/src/            EspHardware + main.cpp (ESP32)
firmware/test/           doctest (test_core, test_protocolo, test_modo_*)
simulator/               tapete_sim.py, core_bridge.py, golden_runner.py, servidor.py
dashboard/               app.py, sesion.py, storage.py, reports.py, fuente.py
shared/                  protocol.md, golden_vectors.json
docs/                    wiring.md, flashing.md, validation.md, ROADMAP.md
scripts/                 run_all_tests.sh, demo_visual.py
audio/                   000X.mp3 (simulador) — ver audio/README.md
```
```
[1] [2] [3]      <- disposición física (2 filas × 3 columnas)
[4] [5] [6]
```

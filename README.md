# Tapete Interactivo Terapéutico

Sistema completo de un tapete físico con **6 botones** para terapia de niños con
síndrome de Down. Cada botón detecta la pisada (sensor **FSR**) y se ilumina
(**LEDs blancos**, no RGB). Un **ESP32** ejecuta tres modos de juego
terapéuticos, reproduce sonidos de refuerzo y envía datos en tiempo real a una
PC, donde un **dashboard** permite al terapeuta monitorear y configurar las
sesiones.

> **Principio rector:** una sola fuente de verdad para la lógica de juego
> (`GameCore`, C++ portable), validada en software (simulador + tests) y
> reutilizada **sin cambios** en el ESP32. El simulador carga el **mismo
> `GameCore.so`** que se compila para el ESP32: no hay dos implementaciones.

## Modos de juego

1. **Memoria** (tipo "Simón dice"): secuencia creciente de casillas a repetir.
2. **Velocidad** (tipo "topo"): pisar la casilla encendida antes de que expire la ventana.
3. **Equilibrio** (patrones): pisar 2–4 casillas simultáneas dentro de un tiempo límite.

Retroalimentación **sin color** (LEDs blancos): patrón de parpadeo + sonido
(acierto = LED sólido + tono ascendente; error = parpadeo + tono grave).

## Estructura

```
firmware/   PlatformIO. lib/GameCore = lógica portable (fuente de verdad). src/ = ESP32.
simulator/  Simulador visual (Pygame) + servidor TCP, cargan GameCore.so vía ctypes.
dashboard/  Interfaz del terapeuta (PyQt6 + SQLite + export CSV/PDF).
shared/     protocol.md + golden_vectors.json (contrato común C++/Python).
audio/      MP3 para el DFPlayer (000X.mp3).
docs/       hardware/ (wiring, flashing, validation, planos), articulo/, evidencia/.
scripts/    run_all_tests.sh (corre TODOS los tests).
```

## Puesta en marcha (una vez)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt          # pytest
.venv/bin/pip install -r simulator/requirements.txt    # pygame
.venv/bin/pip install -r dashboard/requirements.txt    # PyQt6, matplotlib
# C++: g++ (C++17). doctest viene incluido en firmware/test/vendor/.
```

## Comandos exactos

### Correr TODOS los tests

```bash
./scripts/run_all_tests.sh
```

Compila y corre los tests de C++ (doctest), construye `build/libgamecore.so`, y
corre los tests de Python (golden vectors + integración + protocolo + reportes +
smokes). Termina en `>>> TODO VERDE <<<` (código 0) si todo pasa.

### Simulador visual

```bash
.venv/bin/python simulator/tapete_sim.py            # ventana jugable (clic = pisada)
.venv/bin/python simulator/tapete_sim.py --smoke    # prueba headless (sin pantalla)
```

### Dashboard del terapeuta

```bash
.venv/bin/python dashboard/app.py                   # modo embebido (incluye el simulador)
.venv/bin/python dashboard/app.py --tcp 192.168.1.50  # contra un ESP32 real por WiFi
```

Servidor TCP del simulador (para probar la red sin hardware):

```bash
.venv/bin/python simulator/servidor.py              # escucha en 0.0.0.0:3333
```

### Flashear el ESP32

```bash
cd firmware
cp src/secrets.h.example src/secrets.h              # edita tu SSID/contraseña WiFi
pio run -e esp32dev                                 # compila (no flashea)
pio run -e esp32dev -t upload                       # flashea por USB
pio device monitor -b 115200                        # muestra la IP del ESP32
```

Luego conecta el dashboard con `--tcp <IP>`. **Cero cambios de lógica** entre el
simulador y el hardware.

## Protocolo

Líneas JSON terminadas en `\n`, sobre Serial o TCP (puerto 3333). Especificación
completa en `shared/protocol.md`. Ejemplos:

```
PC → tapete:    {"cmd":"set_mode","mode":2,"level":1}   {"cmd":"start"}
tapete → PC:    {"ev":"led","cell":3,"level":255}        {"ev":"press","cell":3,"ms":420}
                {"ev":"score","mode":2,"hits":5,"misses":1,"rt_ms":820,"round":6}
```

## Documentación

- `docs/hardware/wiring.md` — mapa de pines, protoboard, divisor FSR (10 kΩ), LEDs a 5 V, DFPlayer.
- `docs/hardware/flashing.md` — flasheo, WiFi y calibración del umbral de pisada.
- `docs/hardware/validation.md` — cómo correr simulador, dashboard y todos los tests.
- `audio/README.md` — qué MP3 poner en la microSD.

## Hardware

ESP32 DevKit V1 · 6× FSR 402 (+ 6× 10 kΩ pull-down) · 18 LED blancos
(3 por botón) · 12× 110 Ω · DFPlayer Mini + parlante · protoboard. Detalle y
notas de montaje en `docs/hardware/wiring.md`.

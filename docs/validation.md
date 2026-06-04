# Validación: simulador y tests

Toda la lógica se valida **sin hardware**. Este documento explica cómo correr el
simulador, el dashboard y la batería completa de tests.

## 0. Preparar el entorno (una vez)

```bash
# Python: venv del proyecto
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt          # pytest
.venv/bin/pip install -r simulator/requirements.txt    # pygame
.venv/bin/pip install -r dashboard/requirements.txt    # PyQt6, matplotlib
# C++: g++ (C++17). doctest ya está incluido en firmware/test/vendor/.
```

## 1. Correr TODOS los tests (un solo comando)

```bash
./scripts/run_all_tests.sh
```

Hace, en orden:

1. **Tests unitarios C++** (doctest, compilados con g++): RNG, protocolo y los
   3 modos de juego.
2. **Construye `build/libgamecore.so`** (la misma lógica del ESP32, para el
   simulador y el golden runner).
3. **Tests Python (pytest):**
   - **Golden vectors** (`simulator/test_golden.py`): reproduce
     `shared/golden_vectors.json` contra el `.so`. Como el simulador usa el mismo
     GameCore que el ESP32, esto valida **firmware y simulador a la vez**.
   - **Integración** (`dashboard/test_integracion.py`): sesión de punta a punta,
     métricas calculadas y **persistidas en SQLite** + export **CSV**.
   - **TCP** (`dashboard/test_tcp.py`): dashboard ↔ servidor del simulador por
     red (mismo camino que el ESP32 real).
   - **Reportes** (`dashboard/test_reports.py`): export CSV y PDF.
   - **Smokes headless** del simulador y de la GUI.

Salida esperada al final: `>>> TODO VERDE <<<` (código de salida 0).

## 2. Jugar en el simulador visual (con ventana)

```bash
.venv/bin/python simulator/tapete_sim.py
```

- **Clic** en una casilla = pisada.
- LEDs **blancos**: apagado / encendido / brillo (PWM 0..255), nunca color.
- Teclas: `1`/`2`/`3` modo, `+`/`-` nivel, `S` start, `X` stop, `P` pausa.
- Sonidos: se reproducen desde `audio/000X.mp3` si los archivos existen.

Prueba headless (sin pantalla, para CI):

```bash
.venv/bin/python simulator/tapete_sim.py --smoke
```

## 3. Dashboard del terapeuta

Modo embebido (el dashboard incluye el simulador; se "pisa" con el ratón):

```bash
.venv/bin/python dashboard/app.py
```

Contra un ESP32 real (o un simulador en red):

```bash
# arrancar el servidor del simulador (opcional, para probar la red sin hardware)
.venv/bin/python simulator/servidor.py            # escucha en 0.0.0.0:3333
# conectar el dashboard
.venv/bin/python dashboard/app.py --tcp 127.0.0.1
```

## 4. Solo los golden vectors (diagnóstico)

```bash
.venv/bin/python simulator/golden_runner.py
```

## 5. Compilación del firmware (no flashea)

```bash
cd firmware
pio run -e esp32dev
```

Ver `docs/flashing.md` para flashear y conectar el dashboard al hardware.

# Evidencia de ejecución del software

**Tapete Interactivo Terapéutico — material de apoyo para la metodología y los resultados**

Este paquete demuestra que el software desarrollado corre en el PC y produce salidas
verificables. Reúne logs de consola, capturas de las aplicaciones y las porciones de código
que sostienen la arquitectura. Complementa a `../../articulo/stack-tecnologico.md`, que lista
las versiones de cada herramienta, y a `../GUIA_EVIDENCIA.md`, que responde punto por punto
lo solicitado por quien redacta el documento.

Todo se generó el 2026-07-10 en la máquina de desarrollo (Ubuntu 24.04 LTS, Python 3.12.3,
g++ 13.3.0, PlatformIO 6.1.19). Cada pieza es reproducible con el comando indicado.

## Contenido

| Archivo | Qué es | Qué demuestra | Cómo se reprodujo |
|---|---|---|---|
| `01_tests.log` | Salida de la suite completa de pruebas | La lógica es correcta: 8 binarios de C++ (doctest) con 52 casos y 2174 aserciones, más 137 pruebas de Python (pytest). 0 fallos. | `./scripts/run_all_tests.sh` |
| `02_firmware_build.log` | Salida de la compilación del firmware | El firmware compila para el ESP32: `SUCCESS`, RAM 13.8 % (45 324 / 327 680 B), Flash 60.2 % (788 501 / 1 310 720 B). | `pio run -e esp32dev` |
| `03_experimentos.log` | Salida del generador de evidencia | Las cifras del artículo se producen de forma reproducible desde un solo guion. | `python scripts/experimentos.py` |
| `04_protocolo_traza.txt` | Traza real del protocolo de comunicación | Los comandos funcionan: conexión TCP (ping→hello) y el diálogo completo de una partida en **los tres modos** (Velocidad, Memoria, Equilibrio), línea por línea. Responde a la sección 4.4. | `python docs/evidencia/ejecucion/gen_traza_protocolo.py` |
| `05_golden_vectors.txt` | Reproducción de los vectores de referencia | Los 8 escenarios deterministas se reproducen byte a byte (8/8 en verde): determinismo del motor y del protocolo. | `python simulator/golden_runner.py` |
| `06_estructura_codigo.txt` | Panorama del código | Líneas de código por componente (alcance del software desarrollado). | (incluido) |
| `capturas/sim_000.png … sim_004.png` | Fotogramas del simulador (con rótulo) | El motor de juego ejecuta una partida real (modo Velocidad, nivel 1). | `python scripts/demo_visual.py` |
| `capturas/simulador.gif` | Animación del simulador (con rótulo) | La misma partida, en secuencia. | idem |
| `capturas/dashboard_inicio.png` | Dashboard al iniciar (con rótulo) | La interfaz de escritorio arranca y presenta el estado inicial. | idem |
| `capturas/dashboard_juego.png` | Dashboard durante una sesión (con rótulo) | La interfaz refleja el juego en curso con datos reales (3 aciertos). | idem |
| `capturas/dashboard_modo_{memoria,velocidad,equilibrio}.png` | Dashboard en los 3 modos (con rótulo) | La interfaz en cada juego; Equilibrio muestra el patrón de dos celdas simultáneas. | `python docs/evidencia/ejecucion/gen_capturas_modos.py` |
| `reportes/sesion_ejemplo.csv` · `.pdf` | Export de reporte de una sesión | Las funciones de exportación (CSV y PDF, con gráfico) sobre datos de una partida real persistida en SQLite. | `python docs/evidencia/ejecucion/gen_export_reporte.py` |
| `codigo/` | Porciones de código clave | La arquitectura de una sola fuente de verdad (ver abajo). | copia directa del repositorio |

Las capturas llevan un **rótulo quemado dentro de la imagen** que aclara que muestran el
software conectado al simulador, no al tapete físico (generado por `rotular_capturas.py`).
Debe conservarse ese rótulo al insertarlas en el documento.

## Porciones de código incluidas (`codigo/`)

| Ruta | Qué es | Por qué es relevante |
|---|---|---|
| `GameCore/` | Lógica de juego portable (C++17, sin Arduino) | Es el corazón del sistema: el **mismo** código corre en el ESP32 y en el PC. Contiene el motor no bloqueante (`GameEngine`), los tres modos (`modes/`), el generador pseudoaleatorio con semilla (`Rng.h`), el protocolo (`Protocol`) y el mapa de pines (`Config.h`). |
| `GameCore/bridge.cpp` | Interfaz C ABI | Permite que Python cargue la lógica de C++ como librería. |
| `core_bridge.py` | Puente `ctypes` | Cómo el simulador de Python ejecuta la lógica de C++ sin reescribirla. |
| `protocol.md` | Especificación del protocolo | Formato de los mensajes JSON entre PC y ESP32. |
| `golden_vectors.json` | Vectores de referencia | Trazas deterministas que se reproducen en las pruebas: la base de la reproducibilidad. |

## Resultado medido

- **Pruebas:** `>>> TODO VERDE <<<`. C++ (doctest): 52 casos / 2174 aserciones, 0 fallos.
  Python (pytest): 137 pruebas en 65,4 s, 0 fallos.
- **Firmware:** `[SUCCESS]` para el entorno `esp32dev`.

## Alcance y límites (importante para la redacción)

La evidencia de este paquete es de **software**. La validación reportada es **funcional**:
simulación determinista con la misma lógica que el firmware, más el banco de pruebas
automatizado. Dos aclaraciones que deben mantenerse en el documento por integridad:

- **No hay evidencia de hardware físico en funcionamiento.** El prototipo está armado, pero
  la detección de pisada por los sensores aún no está validada; no se incluye —ni debe
  presentarse— ninguna captura o log que sugiera que el tapete físico ya funciona.
- **No hubo pruebas con usuarios ni evaluación clínica.** Lo terapéutico se enuncia como
  trabajo futuro, no como resultado obtenido.

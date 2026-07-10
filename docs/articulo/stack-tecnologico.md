# Stack tecnológico y herramientas de desarrollo

**Tapete Interactivo Terapéutico — insumo para la sección de Metodología**

Este documento lista los lenguajes, librerías, programas y herramientas usados para
desarrollar el sistema (firmware, aplicación de escritorio, simulador, pruebas y validación).
Está pensado como material de apoyo para redactar la metodología: cada tabla indica el
componente, su versión y la función que cumplió.

Las versiones se tomaron de los archivos de dependencias del proyecto
(`requirements*.txt`, `firmware/platformio.ini`, `.github/workflows/ci.yml`) y se
verificaron ejecutando cada herramienta en la máquina de desarrollo el 2026-07-10
(Ubuntu 24.04 LTS, kernel 6.17). Las dependencias de Python están fijadas por versión
para que el entorno sea reproducible.

---

## Parte A — Stack del sistema (prototipo)

Herramientas y librerías con las que se construyó y validó el prototipo. Esto es lo que
corresponde a la metodología de ingeniería del sistema.

### 1. Lenguajes de programación

| Lenguaje | Versión | Uso |
|---|---|---|
| C++ | C++17 | Lógica de juego portable (GameCore) y firmware del ESP32. La misma lógica se compila para el microcontrolador y para el PC. |
| Python | 3.12.3 | Aplicación de escritorio (dashboard), simulador, suite de pruebas y generación de evidencia cuantitativa. |

La lógica de juego (motor, tres modos, generador de números pseudoaleatorios, protocolo)
está escrita una sola vez en C++ portable, sin dependencias de Arduino, y se comparte entre
el firmware y el simulador de PC mediante un puente `ctypes`.

### 2. Firmware embebido y microcontrolador

| Componente | Versión | Función |
|---|---|---|
| Microcontrolador | ESP32 DevKit V1 (perfil `esp32dev`) | Unidad de cómputo: lee los sensores, controla los LED, reproduce audio y se comunica con el PC. |
| Framework | Arduino-ESP32 core 2.0.17 (paquete PlatformIO `framework-arduinoespressif32` 3.20017) | Capa de abstracción de hardware sobre el ESP32. |
| Toolchain / build | PlatformIO Core 6.1.19 | Compilación, gestión de dependencias y carga del firmware. |
| Driver de audio | DFRobotDFPlayerMini ^1.0.6 | Control del reproductor MP3 DFPlayer Mini. |
| Comunicación | Serial 115200 bps y WiFi/TCP (puerto 3333) | Enlace con el dashboard mediante un protocolo propio de líneas JSON. |

### 3. Aplicación de escritorio (dashboard del terapeuta)

| Librería | Versión | Función |
|---|---|---|
| PyQt6 | 6.11.0 | Interfaz gráfica del terapeuta. |
| matplotlib | 3.11.0 | Gráficas en la interfaz y generación del PDF de reporte de sesión. |
| pyserial | 3.5 | Enlace USB/serial con el ESP32. |
| SQLite | módulo `sqlite3` (biblioteca estándar de Python 3.12) | Persistencia local de perfiles y sesiones. |

El reporte de sesión en PDF se genera con matplotlib (`savefig`); la exportación a CSV usa
el módulo estándar `csv`. No se emplean librerías externas de reportería.

### 4. Simulador

| Componente | Versión | Función |
|---|---|---|
| pygame | 2.6.1 | Ventana de simulación del tapete: cada clic equivale a una pisada. |
| ctypes | biblioteca estándar de Python | Puente entre el simulador de Python y la lógica de juego en C++ (`libgamecore.so`). |
| socket / selectors | biblioteca estándar de Python | Servidor TCP para comunicación en red. |

### 5. Pruebas, calidad y determinismo

| Herramienta | Versión | Función |
|---|---|---|
| pytest | 9.1.1 | Pruebas de la parte en Python (integración, protocolo, vectores de referencia). |
| doctest | cabecera incluida en el repositorio | Pruebas unitarias de la lógica en C++. |
| g++ (GCC) | 13.3.0 | Compilación de la lógica portable y de sus pruebas en el PC. |

El determinismo se apoya en un generador pseudoaleatorio propio (xorshift32) con semilla, que
sustenta los *golden vectors* (vectores de referencia en JSON): la misma configuración
produce siempre la misma traza, y se reproduce contra la librería compartida para validar a
la vez el firmware y el simulador.

### 6. Diseño y validación del hardware

| Herramienta | Versión | Función |
|---|---|---|
| KiCad (`kicad-cli`) | 10.0.4 | Esquemático del circuito y verificación de reglas eléctricas (ERC). |
| ngspice | 42 | Simulación analógica del divisor de tensión del sensor FSR. |
| Graphviz (`dot`) | 2.43.0 | Diagrama de bloques del sistema, generado leyendo los pines directamente del firmware. |

### 7. Empaquetado y distribución

| Herramienta | Versión | Función |
|---|---|---|
| PyInstaller | 6.11.1 | Empaquetado del dashboard como ejecutable de Windows (`.exe`, modo *onedir*). |

### 8. Control de versiones e integración continua

| Herramienta | Versión | Función |
|---|---|---|
| Git | 2.54.0 | Control de versiones. |
| GitHub Actions | `ubuntu-latest` y `windows-latest`; `actions/setup-python` con Python 3.12 | Integración continua: pruebas, compilación del firmware y del ejecutable. |

### 9. Entorno de desarrollo

| Elemento | Detalle |
|---|---|
| Sistema operativo | Ubuntu 24.04 LTS (kernel 6.17) |
| Aislamiento de dependencias | Entorno virtual de Python (`venv`) con versiones fijadas en `requirements*.txt` |

**Nota sobre numpy:** el proyecto no importa numpy de forma directa; aparece únicamente como
dependencia transitiva de matplotlib. Los cálculos estadísticos (barridos y análisis Monte
Carlo de la evidencia) usan el módulo estándar `math`.

---

## Parte B — Cadena de producción del documento y las figuras

Estas herramientas no construyeron el prototipo: componen el artículo (`.docx`/`.pdf`) y
rasterizan algunas figuras. Se listan aparte para que quien redacte el documento decida si
son pertinentes para su propia metodología, ya que el documento final lo produce el equipo
redactor con sus propias herramientas.

| Herramienta | Versión | Función |
|---|---|---|
| Pandoc | 3.1.3 | Conversión de la fuente Markdown a `.docx` y `.pdf`, con citas resueltas por citeproc en estilo APA 7 (`apa.csl`). |
| XeLaTeX / TeX Live | TeX Live 2023 | Motor de composición del PDF (necesario por los caracteres Unicode: Ω, µ). |
| CairoSVG | 2.9.0 | Conversión del gráfico vectorial del tapete de SVG a PDF/PNG. |
| poppler-utils (`pdftoppm`) | 24.02.0 | Rasterizado del esquemático KiCad para insertarlo como figura. |

La evidencia cuantitativa del artículo (cifras, tablas y figuras de resultados) se genera de
forma reproducible con un guion de Python (`scripts/experimentos.py`) que usa matplotlib; esa
parte pertenece a la metodología de ingeniería (Parte A, sección 3 y 5), no a la composición
del documento.

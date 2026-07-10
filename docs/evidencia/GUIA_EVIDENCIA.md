# Guía de evidencia del proyecto — Tapete Interactivo Terapéutico

Material para quien redacta el documento. Responde punto por punto lo que se pidió:
código, ejecuciones, protocolo de comunicación, procedencia de las gráficas y el estado
real del hardware. Indica qué está listo, qué fotografías debe tomar el autor y qué **no**
puede presentarse como funcionando, por integridad.

Documentos relacionados:
- `articulo/stack-tecnologico.md` — versiones de cada herramienta (metodología).
- `ejecucion/README.md` — logs, capturas y código, con instrucciones de reproducción.
- `ejecucion/04_protocolo_traza.txt` — traza real del protocolo (sección 4.4).

---

## 1. Regla de integridad (leer antes que nada)

El prototipo está **armado**, pero la detección de pisada por los sensores **aún no está
validada** (ver §5). Por eso:

- La evidencia de **software** es completa y se entrega aquí.
- La evidencia de **construcción del hardware** (cómo se montó) son fotografías que toma el
  autor: son legítimas y valiosas para la metodología.
- **No** puede presentarse ninguna imagen, video o pie de foto que afirme que el tapete
  **físico detecta pisadas, enciende LEDs por el juego o reproduce audio en una partida
  real**: eso todavía no ocurre. Presentarlo como logrado sería faltar a la verdad en un
  documento evaluado.

La validación reportada es **funcional**: simulación determinista con el mismo código que
corre en el ESP32, más el banco de pruebas automatizado. Lo clínico y la puesta en marcha
física son **trabajo futuro**.

---

## 2. Mapa de lo solicitado

Estado: **[LISTO]** = entregado en este paquete · **[FOTO AUTOR]** = fotografía de
construcción que debe tomar el autor · **[NO DISPONIBLE]** = no puede evidenciarse como
funcionando hoy (hardware en depuración).

| Lo que se pidió | Estado | Qué se entrega / qué hacer |
|---|---|---|
| Diseño / arquitectura del prototipo | **[LISTO]** | Esquemático eléctrico (`evidencia/esquematico.png`, KiCad) y diagrama de bloques (`evidencia/diagrama_bloques.png`, Graphviz). |
| Fabricación de la estructura, distribución de casillas | **[FOTO AUTOR]** | Foto de la caja abierta y de las 6 casillas (2×3). Pie: montaje del prototipo. |
| Instalación de los sensores en cada casilla | **[FOTO AUTOR]** | Foto de un FSR colocado bajo una casilla. |
| Cableado eléctrico y conexiones internas | **[FOTO AUTOR] + [LISTO]** | Foto del protoboard/cableado real, acompañada del esquemático y la net list (`docs/hardware/cableado.md`). |
| Organización de los componentes | **[FOTO AUTOR]** | Foto general del interior con ESP32, protoboard, DFPlayer y cableado. |
| Integración del hardware (microcontrolador, audio, LED, alimentación USB) | **[FOTO AUTOR]** | Foto del ESP32 montado, el módulo de audio y el cable USB único de alimentación. |
| Desarrollo del firmware y su carga en el microcontrolador | **[FOTO AUTOR] + [LISTO]** | Log de compilación (`ejecucion/02_firmware_build.log`, `SUCCESS`) + captura de PlatformIO al cargar el firmware (la toma el autor; el agente no flashea). |
| Desarrollo del software | **[LISTO]** | Código en `ejecucion/codigo/` + logs de pruebas (`ejecucion/01_tests.log`). |
| Interfaz de monitoreo ejecutándose en el PC | **[LISTO]** | Capturas del dashboard (`ejecucion/capturas/dashboard_*.png`), rotuladas como software/simulador. |
| Comunicación hardware↔software efectiva | **[LISTO] (software) / [NO DISPONIBLE] (con pisada física)** | Traza real del protocolo por TCP (`ejecucion/04_protocolo_traza.txt`). El enlace físico serie/TCP con el ESP32 se estableció en pruebas previas (llegaron métricas), pero la detección de pisada aún no. Ver §5. |
| Prueba de los sensores | **[NO DISPONIBLE]** | Hoy los sensores no registran pisada con el acrílico puesto. Lo que existe es el **proceso de calibración** (§5), que documenta el estado, no un funcionamiento. |
| Encendido de los LEDs | **[NO DISPONIBLE]** | Sin prueba determinista; no confirmar como funcionando. |
| Audio del prototipo (video) | **[NO DISPONIBLE]** | Requiere grabar la microSD y validar en el equipo; pendiente de puesta en marcha. |
| Prototipo completo ensamblado y funcionando | **[FOTO AUTOR] (ensamblado) / [NO DISPONIBLE] (funcionando)** | Foto del prototipo cerrado como evidencia de ensamblaje. No rotular como “funcionando”. |
| Gráficas: de dónde salieron, programa estadístico | **[LISTO]** | Ver §3. |
| Protocolo de comunicación (4.4) + comandos funcionando | **[LISTO]** | Ver §4. |

---

## 3. Procedencia de las gráficas (sección 5.6 y todas las figuras)

**Todas las figuras son de elaboración propia y reproducibles por guion.** No se usó ningún
programa estadístico de terceros (no SPSS, R, Minitab, Stata ni Excel). Cómo citar cada una:

| Figura (en el artículo) | Herramienta | Guion que la genera | Contenido |
|---|---|---|---|
| `E3_adaptacion.png` | matplotlib (Python) | `scripts/experimentos.py` | Adaptación de dificultad frente al desempeño (modo Velocidad). |
| `E5_convergencia_modos.png` | matplotlib | `scripts/experimentos.py` | Convergencia de los tres modos. |
| `E6_montecarlo.png` (**5.6**) | matplotlib | `scripts/experimentos.py` | Verificación estadística de la regla de dificultad. |
| `E9_divisor_fsr.png` | ngspice (simulación) + matplotlib | `scripts/experimentos.py` | Caracterización del canal de sensado del FSR. |
| `diagrama_bloques.png` | Graphviz (`dot`) | `scripts/gen_diagrama_bloques.py` | Diagrama de bloques del sistema. |
| `esquematico.png` | KiCad (`kicad-cli`) | `scripts/gen_esquematico.py` | Esquemático eléctrico completo. |

**Método estadístico de la Figura E6 (5.6), para el texto:** análisis **Monte Carlo
determinista** implementado por el autor en Python. Un jugador simulado acierta cada pisada
con probabilidad *h*; se agregan **200 semillas** y se compara la tasa medida de rondas
ganadas con la predicción teórica (Velocidad *P = h*; Equilibrio *P = hᵏ*; Memoria *P = hᴸ*).
El intervalo de confianza es al **95 % por el método de Wald** para proporciones
(`margen = 1,96·√(p(1−p)/n)`), implementado en `simulator/montecarlo.py`. El graficado usa
**matplotlib 3.11.0** sobre **Python 3.12**.

Frase sugerida de crédito: *«Figura de elaboración propia, generada con Python 3.12 y
matplotlib; análisis Monte Carlo determinista (200 semillas) con intervalo de confianza al
95 % por el método de Wald.»*

---

## 4. Protocolo de comunicación (sección 4.4)

- **Especificación completa:** `ejecucion/codigo/protocol.md` (transporte, formato JSON,
  eventos, comandos, RNG determinista, versionado).
- **Comandos funcionando (traza real):** `ejecucion/04_protocolo_traza.txt`. Contiene:
  1. Una conexión **TCP real** en la que el PC envía `{"cmd":"ping"}` y el cerebro responde
     `{"ev":"hello","fw":"1.0.0","cells":6}` — el mismo transporte del ESP32 (puerto 3333).
  2. El **diálogo completo de una partida en los tres modos** (Velocidad, Memoria,
     Equilibrio): los comandos que envía el PC (`set_seed`, `set_mode`, `start`) y los
     eventos que devuelve el cerebro (`state`, `led`, `press`, `sound`, `score`), línea por
     línea.
- **Determinismo del protocolo:** `ejecucion/05_golden_vectors.txt` reproduce los 8
  escenarios de referencia byte a byte (8/8 en verde).

Cada diálogo coincide con un **golden vector** que la suite de pruebas verifica en cada
corrida: es reproducible byte a byte. Las líneas las produce el **mismo GameCore** que corre
en el ESP32 (cargado como biblioteca). En el `.txt`, «cerebro» es ese núcleo ejecutándose
como simulador; el protocolo es idéntico al del hardware.

---

## 5. Estado real del hardware (honesto, para la sección correspondiente)

El prototipo está **ensamblado** (caja de acrílico, protoboard, 6 sensores FSR + LEDs, ESP32,
módulo de audio, alimentación por un único USB). Lo verificado y lo pendiente:

- **Funciona:** el firmware compila y carga; el enlace serie/TCP con el PC se estableció; el
  motor de juego corre en el microcontrolador (en pruebas previas llegaron métricas de sesión
  al dashboard).
- **No validado:** la **detección de pisada**. Con el acrílico atornillado, ningún sensor
  registra la pisada en el dashboard. Está en **calibración** (se mide la lectura cruda del
  ADC para fijar el umbral); es el paso pendiente de puesta en marcha.
- **Sin prueba determinista:** encendido de LEDs y audio en el prototipo físico.

Encuadre correcto para el documento: hardware **construido e integrado**, con la
comunicación y la lógica operativas, y la **calibración de los sensores como trabajo en
curso**. Es un estado de proyecto, no un defecto que ocultar.

---

## 6. Fotografías que debe tomar el autor (paso a paso)

Cada foto documenta **cómo se construyó** el prototipo (metodología), no que funcione. Pie de
foto honesto sugerido entre paréntesis.

1. Caja abierta mostrando las 6 casillas 2×3. *(Estructura del tapete y distribución de casillas.)*
2. Un FSR colocado bajo una casilla, antes de cerrar. *(Instalación del sensor de fuerza.)*
3. Protoboard y cableado interno. *(Cableado eléctrico; contrastar con el esquemático.)*
4. Vista general del interior: ESP32, protoboard, módulo de audio, cableado. *(Integración de componentes.)*
5. El ESP32 y el cable USB único. *(Microcontrolador y alimentación por USB.)*
6. Pantalla del PC con PlatformIO cargando el firmware al ESP32. *(Carga del firmware.)*
7. Prototipo cerrado y terminado. *(Prototipo ensamblado.)* — no rotular como “funcionando”.

Lo que **no** se debe fotografiar/grabar como evidencia de funcionamiento: sensores
detectando pisada, LEDs encendiendo durante el juego, audio sonando en una partida, o el
tapete “funcionando” con un usuario. Eso corresponde a la puesta en marcha, aún pendiente.

---

## 7. Nota sobre las capturas de pantalla y el video

Las capturas del dashboard y del simulador que se entregan llevan un **rótulo quemado dentro
de la imagen** que aclara que muestran el **software conectado al simulador, no al tapete
físico**. Debe conservarse ese rótulo (o un pie equivalente) al insertarlas.

Sobre el **video** existente del que se pensaba extraer una imagen de “funcionamiento”: se
confirmó que **muestra el software** (el simulador o el dashboard en el PC), **no el tapete
físico**. Por tanto, cualquier fotograma que se saque de ese video es software y debe
rotularse como tal; **no** puede presentarse como el tapete físico funcionando. En su lugar
conviene usar directamente las capturas ya rotuladas de este paquete
(`ejecucion/capturas/`), que dicen lo mismo de forma más limpia y sin ambigüedad.

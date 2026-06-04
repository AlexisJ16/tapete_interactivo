
> **Cómo usar este documento**
> 
> 1. Guarda este archivo en la raíz de tu proyecto (la carpeta `Tapete Interactivo/`).
> 2. Abre Claude Code en esa carpeta.
> 3. Pega el bloque **“PROMPT DE ARRANQUE”** (más abajo) como tu primer mensaje, o simplemente di: _“Lee `Tapete_Interactivo__Prompt_Claude_Code.md` y constrúyelo siguiendo el plan por fases. Corre los tests en cada fase.”_
> 
> El objetivo es que **toda la lógica quede validada por software** (simulador visual + tests automatizados) **antes de tocar el hardware**. Cuando conectes el ESP32 físico y lo flashees, debe funcionar sin sorpresas: lo único que quedará por verificar es el cableado y la electrónica.

---

## PROMPT DE ARRANQUE (pégalo en Claude Code)

```
Eres un ingeniero senior de sistemas embebidos y full-stack. Vas a construir, de
principio a fin, el sistema completo de un "Tapete Interactivo Terapéutico" para
niños con síndrome de Down, siguiendo la especificación de este repositorio
(archivo Tapete_Interactivo__Prompt_Claude_Code.md).

Meta innegociable: TODA la lógica debe quedar validada por software —un simulador
visual jugable + tests automatizados— ANTES de tocar el hardware. Cuando yo conecte
el ESP32 real y lo flashee, debe funcionar sin cambiar una sola línea de lógica.

Trabaja en español en comentarios, commits y documentación. Empieza proponiendo el
plan y la estructura de carpetas; luego implementa por fases (GameCore + tests →
simulador → dashboard → firmware ESP32 → docs), corriendo los tests al cerrar cada
fase. No avances de fase si los tests de la fase anterior no están en verde.
Pregúntame solo si algo es realmente ambiguo; de lo contrario, avanza.
```

---

## 1. Objetivo y filosofía

Tapete físico con **6 botones**. Cada botón detecta la pisada del niño (sensor de presión) y se ilumina (LEDs blancos). Un microcontrolador ESP32 ejecuta tres modos de juego terapéuticos, reproduce sonidos de refuerzo y envía datos de desempeño en tiempo real a una PC, donde un dashboard permite al terapeuta monitorear y configurar las sesiones.

**Principio rector:** una sola fuente de verdad para la lógica de juego, validada en software, reutilizada sin cambios en el ESP32.

---

## 2. Hardware confirmado (es lo único con lo que se cuenta)

|Componente|Cantidad|Rol|
|---|---|---|
|ESP32 DevKit V1|1|Cerebro: lógica, I/O, WiFi|
|Sensor de presión FSR 402|6|Un sensor por botón (detección de pisada)|
|LED blanco|18|3 LEDs por botón (un grupo controlado en conjunto)|
|Resistencia 110 Ω|12|Limitadoras de corriente para los LEDs|
|DFPlayer Mini MP3 + parlante|1|Salida de audio (refuerzos, instrucciones)|
|Protoboard grande|1|Montaje sin soldadura|
|Cables Dupont (M-M, M-H)|varios|Conexiones|
|Cable USB-C|1|Programación/alimentación del ESP32|

---

## 3. Diseño físico

- **6 botones en disposición 2 filas × 3 columnas**, numerados `1..6`:
    
    ```
    [1] [2] [3]
    [4] [5] [6]
    ```
    
- Cada botón = **1 sensor FSR** (pisada) + **3 LEDs blancos** en un grupo, controlados por **un solo pin GPIO con PWM** (encienden/apagan y atenúan juntos).
    
- **Los LEDs son BLANCOS, no RGB.** No hay color. Por lo tanto la retroalimentación **NO puede depender del color**; se da mediante **patrones de parpadeo + sonido**:
    
    - **Acierto:** LED objetivo se mantiene sólido + tono ascendente alegre.
    - **Error:** LED parpadea rápido 3× + tono grave.
    - **Inicio de ronda:** breve barrido/parpadeo de todos los LEDs.
    - **Instrucción:** se enciende el LED de la casilla objetivo.

> **Importante para Claude Code:** NO uses librerías de LED direccionable (FastLED/NeoPixel/WS2812B). Son LEDs blancos simples controlados por **LEDC (PWM)** del ESP32. El simulador debe representar LEDs blancos (apagado / encendido / brillo), no colores.

---

## 4. Notas críticas de hardware (para `docs/wiring.md`)

Estas notas **no bloquean el desarrollo de software** (todo se valida en el simulador), pero deben quedar documentadas para la fase física:

1. **Resistencias de los FSR (importante):** los sensores FSR necesitan una resistencia _pull-down_ de aproximadamente **10 kΩ** para formar el divisor de voltaje que lee el ADC del ESP32. Las **resistencias de 110 Ω son para los LEDs**, no para los FSR. Con 110 Ω el rango de lectura del FSR queda muy comprimido y la detección es poco fiable.
    
    - **Acción recomendada para la fase física:** conseguir **6 resistencias de 10 kΩ** (una por FSR). Son muy económicas. Como alternativa de respaldo, los GPIO 32 y 33 del ESP32 tienen _pull-down_ interno (~45 kΩ) que puede usarse para 2 de los sensores, pero lo correcto es la resistencia externa de 10 kΩ.
    - El firmware debe definir un **umbral de pisada** configurable (calibrable) sobre la lectura del ADC.
2. **Brillo de los LEDs blancos:** el voltaje directo de un LED blanco (~3,0–3,4 V) está muy cerca de los 3,3 V del GPIO, por lo que **encender los LEDs directamente desde un pin a 3,3 V dará poco brillo**. Para brillo pleno conviene alimentarlos desde **5 V** mediante un transistor por grupo (p. ej. 2N2222) o un único integrado **ULN2803** (8 canales) controlado por los GPIO. Esto es opcional para empezar (se puede probar tenue desde 3,3 V), pero recomendado para el dispositivo final.
    
3. **Alimentación:** durante el desarrollo basta con alimentar el ESP32 por USB-C. Para el dispositivo portátil final se añadiría la batería de litio + cargador (no incluida en esta compra).
    

---

## 5. Mapa de pines del ESP32 (usar en `Config.h`)

|Señal|Pin ESP32|Notas|
|---|---|---|
|FSR 1|GPIO 36 (VP)|ADC1, solo entrada|
|FSR 2|GPIO 39 (VN)|ADC1, solo entrada|
|FSR 3|GPIO 34|ADC1, solo entrada|
|FSR 4|GPIO 35|ADC1, solo entrada|
|FSR 5|GPIO 32|ADC1 (tiene pull interno)|
|FSR 6|GPIO 33|ADC1 (tiene pull interno)|
|LED grupo 1|GPIO 4|salida, canal LEDC (PWM)|
|LED grupo 2|GPIO 5|salida, canal LEDC (PWM)|
|LED grupo 3|GPIO 18|salida, canal LEDC (PWM)|
|LED grupo 4|GPIO 19|salida, canal LEDC (PWM)|
|LED grupo 5|GPIO 21|salida, canal LEDC (PWM)|
|LED grupo 6|GPIO 23|salida, canal LEDC (PWM)|
|DFPlayer (RX del módulo)|GPIO 17 (TX2)|TX del ESP32 → RX DFPlayer (resistencia 1 kΩ en serie recomendada)|
|DFPlayer (TX del módulo)|GPIO 16 (RX2)|RX del ESP32 ← TX DFPlayer|

> Se usa **ADC1** para todos los FSR porque **ADC2 entra en conflicto con el WiFi** en el ESP32. Los GPIO 34–39 son solo entrada (perfecto para sensores).

---

## 6. Arquitectura del software (requisito estricto)

**Una sola fuente de verdad para la lógica de juego.** La lógica vive en C++ portable (sin llamadas Arduino) y se reutiliza tanto en el ESP32 como en el simulador.

```
┌──────────────────────────── PC ────────────────────────────┐
│   ┌──────────────┐         protocolo JSON        ┌────────┐ │
│   │  Dashboard   │◄────────(WiFi/TCP o Serial)──►│  ESP32 │ │  ← real
│   │ (terapeuta)  │                                │ (real) │ │
│   └──────────────┘                                └────────┘ │
│          ▲                                                    │
│          │ mismo protocolo                                    │
│   ┌──────┴──────────────┐                                     │
│   │  Simulador visual    │  ← reemplaza al ESP32 en software   │
│   │  (tapete virtual)    │     (lógica idéntica + I/O virtual) │
│   └─────────────────────┘                                     │
└───────────────────────────────────────────────────────────────┘
```

- La **lógica de juego** (`GameCore`) se escribe en **C++ portable** detrás de una interfaz de hardware abstracta `IHardware { leerSensor(i), setLed(i, nivel), reproducirSonido(id), millis() }`.
    - `EspHardware` implementa `IHardware` con FSR (ADC), LEDs (LEDC/PWM) y DFPlayer → corre en el ESP32.
    - El simulador provee un `IHardware` virtual (clics del ratón = pisadas; estado de LEDs = dibujo en pantalla; sonidos = reproducción de audio).
- **Preferido (máxima certeza):** compilar `GameCore` como **biblioteca nativa** (`.so`) y llamarla desde el simulador en Python vía `ctypes`/`cffi`. Así el simulador ejecuta _exactamente_ el mismo código que el ESP32.
- **Alternativa aceptable:** un _port_ limpio de `GameCore` en Python para el simulador, **validado contra los mismos `golden_vectors.json`** que los tests de C++ (ver §10). La equivalencia se demuestra con esos vectores; sin ellos no se acepta el port.

---

## 7. Estructura de carpetas objetivo

```
tapete-interactivo/
├── Tapete_Interactivo__Prompt_Claude_Code.md   # esta especificación
├── README.md
├── firmware/                       # PlatformIO
│   ├── platformio.ini              # envs: esp32dev (real) + native (tests)
│   ├── lib/GameCore/               # LÓGICA PORTABLE (fuente de verdad)
│   │   ├── Config.h                # mapa de pines, umbrales, tiempos
│   │   ├── IHardware.h             # interfaz de hardware abstracta
│   │   ├── Protocol.{h,cpp}        # serialización/parseo del protocolo JSON
│   │   ├── GameEngine.{h,cpp}      # máquina de estados general
│   │   └── modes/
│   │       ├── ModoMemoria.{h,cpp}
│   │       ├── ModoVelocidad.{h,cpp}
│   │       └── ModoEquilibrio.{h,cpp}
│   ├── src/
│   │   ├── main.cpp                # entrada ESP32: WiFi + EspHardware + GameEngine
│   │   └── EspHardware.{h,cpp}     # drivers reales FSR/LED/DFPlayer
│   └── test/                       # tests unitarios (env native)
│       ├── test_modo_memoria/
│       ├── test_modo_velocidad/
│       ├── test_modo_equilibrio/
│       └── test_protocolo/
├── simulator/                      # simulador visual (Python)
│   ├── tapete_sim.py               # ventana 2×3, clic = pisada, dibuja LEDs, suena
│   ├── core_bridge.py              # ctypes a GameCore.so  (o port verificado)
│   ├── golden_runner.py            # corre golden_vectors contra el simulador
│   └── requirements.txt
├── dashboard/                      # interfaz del terapeuta (Python)
│   ├── app.py                      # conecta a simulador O a ESP32 real
│   ├── ui/                         # vista en vivo, control de modo/nivel, perfiles
│   ├── storage.py                  # SQLite: perfiles, sesiones, métricas
│   ├── reports.py                  # export CSV/PDF
│   └── requirements.txt
├── shared/
│   ├── protocol.md                 # especificación del protocolo
│   └── golden_vectors.json         # escenarios de prueba (C++ y Python deben coincidir)
├── audio/                          # MP3 para el DFPlayer (0001.mp3, 0002.mp3, ...)
├── docs/
│   ├── wiring.md                   # mapa de pines, esquema en protoboard, notas §4
│   ├── flashing.md                 # cómo flashear + configurar WiFi
│   └── validation.md               # cómo correr simulador y tests
└── scripts/
    └── run_all_tests.sh            # un solo comando que corre TODOS los tests
```

---

## 8. Los tres modos de juego (en `lib/GameCore/modes/`)

Cada modo es una máquina de estados que consume eventos de pisada (con timestamp) y produce comandos de LED, sonido y eventos de puntaje.

### Modo 1 — Memoria de secuencias (tipo “Simón dice”)

- El sistema genera una secuencia de casillas (longitud inicial según el nivel).
- La reproduce: enciende cada LED en orden, uno a uno, con su sonido.
- El niño repite pisando en el mismo orden.
- Acierto al completar la secuencia → longitud +1 + sonido de éxito. Error → sonido de error y se reinicia/repite la secuencia.
- **Nivel** controla: longitud inicial (2–6), velocidad de exhibición y tolerancia de tiempo.
- **Métricas:** longitud máxima alcanzada, aciertos, errores, tiempo por pisada.

### Modo 2 — Velocidad de reacción (tipo “topo”)

- Se enciende una casilla al azar.
- El niño debe pisarla antes de que expire una ventana de tiempo.
- Acierto → registra `rt_ms` y pasa a la siguiente. Pisada equivocada o _timeout_ → error.
- **Nivel** controla: tamaño de la ventana (más corta = más difícil) y número de rondas.
- **Métricas:** tiempo de reacción promedio, aciertos, errores, _timeouts_.

### Modo 3 — Equilibrio y coordinación (patrones)

- Se enciende un patrón de 2–3 casillas simultáneas.
- El niño debe pisarlas todas dentro de un tiempo límite (subnivel: en cualquier orden o en orden específico).
- Patrón completo → éxito. Tiempo agotado o pisada fuera del patrón → error.
- **Nivel** controla: número de casillas simultáneas (2/3/4) y tiempo límite.
- **Métricas:** patrones completados, tiempo de completado, errores.

Todos los modos deben registrar `hits`, `misses` y tiempos, y emitir los eventos del protocolo (§9).

---

## 9. Protocolo de comunicación

Líneas **JSON terminadas en `\n`**. Funciona sobre **Serial (USB)** y sobre **WiFi (TCP)**. Recomendación: en el dispositivo real, el ESP32 actúa como **servidor TCP en el puerto 3333**; el dashboard se conecta como cliente. El simulador expone exactamente el mismo protocolo.

**Eventos ESP32/Simulador → PC**

```
{"ev":"hello","fw":"1.0.0","cells":6}
{"ev":"led","cell":1,"level":255}                  // 0..255 (brillo)
{"ev":"press","cell":3,"ms":1820}                  // pisada con timestamp de sesión
{"ev":"sound","id":2}
{"ev":"score","mode":1,"hits":5,"misses":1,"rt_ms":820,"round":6}
{"ev":"state","mode":1,"status":"running"}         // idle|running|paused|finished
```

**Comandos PC → ESP32/Simulador**

```
{"cmd":"set_mode","mode":1,"level":2}
{"cmd":"start"}
{"cmd":"stop"}
{"cmd":"pause"}
{"cmd":"set_level","level":3}
{"cmd":"set_player","id":"p001","name":"Juan"}
{"cmd":"ping"}                                     // responde con hello
```

Detalla y versiona este protocolo en `shared/protocol.md`. Usa **ArduinoJson** (funciona también en el build nativo) o una mini-serialización propia, pero el parseo debe ser idéntico en ambos lados.

---

## 10. Estrategia de testing y validación (obligatoria)

1. **Tests unitarios** (`firmware/test/`, env `native`, con Unity o doctest/GoogleTest): para cada modo, dado un guion de `(pisada, tiempo)` se verifican los `(led, sonido, score, state)` esperados. Cubrir aciertos, errores, _timeouts_ y cambios de nivel.
2. **Golden vectors** (`shared/golden_vectors.json`): escenarios `{entrada: [(evento, t)...], salida_esperada: [eventos...]}`. Se ejecutan **contra `GameCore` (C++)** y **contra el simulador** (`simulator/golden_runner.py`). Ambos deben producir la misma salida. Esto demuestra que firmware y simulador son equivalentes.
3. **Tests de integración** (`pytest`): dashboard ↔ simulador de punta a punta — iniciar sesión, simular una serie de pisadas, verificar que las métricas se calculan y **se persisten** correctamente en SQLite y se exportan a CSV.
4. **Tests de round-trip del protocolo:** serializar → parsear → comparar, en C++ y en Python.
5. **Compilación:** el firmware debe **compilar sin errores para `env:esp32dev`** (no se flashea en CI, solo se compila).
6. **`scripts/run_all_tests.sh`**: un solo comando que corre absolutamente todos los tests anteriores y reporta verde/rojo.

---

## 11. Criterios de aceptación (todo debe cumplirse al terminar)

1. Puedo **jugar los 3 modos en el simulador visual, sin hardware**, y se ve y suena correcto (clic en una casilla = pisada; los LEDs se encienden/parpadean; los sonidos se reproducen).
2. El **dashboard** muestra en vivo el estado de LEDs, las pisadas y los puntajes contra el simulador, permite elegir modo/nivel y **guarda el reporte de la sesión** (SQLite, exportable a CSV).
3. **Todos los tests** (unitarios + golden + integración + protocolo) pasan en verde con `scripts/run_all_tests.sh`.
4. `firmware` **compila para `esp32dev`** sin errores.
5. Pasar del simulador al ESP32 real es solo: **flashear + poner credenciales WiFi + abrir el dashboard**. Cero cambios de lógica.
6. `README.md`, `docs/wiring.md`, `docs/flashing.md` y `docs/validation.md` completos y en español.

---

## 12. Plan por fases (ejecutar en orden, tests en verde al cerrar cada una)

1. **Andamiaje:** estructura de carpetas, `platformio.ini` (envs `esp32dev` + `native`), `shared/protocol.md`, `golden_vectors.json` con 2–3 escenarios semilla, `scripts/run_all_tests.sh`.
2. **GameCore:** `IHardware`, `Protocol`, `GameEngine` y los 3 modos + **tests unitarios** + **golden vectors**. → verde.
3. **Simulador:** ventana 2×3 jugable (clic = pisada), dibujo de LEDs blancos (apagado/encendido/brillo), reproducción de sonidos; ejecuta `GameCore` (ctypes) o port verificado; `golden_runner` en verde.
4. **Dashboard:** UI del terapeuta (vista en vivo, control de modo/nivel, perfiles), persistencia SQLite, export CSV, **tests de integración** con el simulador. → verde.
5. **Firmware ESP32:** `EspHardware` (FSR/LED/DFPlayer), WiFi + servidor TCP, integración con `GameCore`; **compila para `esp32dev`**.
6. **Documentación:** `wiring.md` (mapa de pines, esquema en protoboard, notas §4), `flashing.md`, `validation.md`, `README.md`.

---

## 13. Stack tecnológico recomendado

- **Firmware:** PlatformIO + framework Arduino (`board = esp32dev`). LEDs por **LEDC (PWM)** nativo (no FastLED). DFPlayer con `DFRobotDFPlayerMini`. `ArduinoJson` para el protocolo.
- **GameCore:** C++17 portable, sin dependencias de Arduino en la lógica.
- **Simulador:** Python 3.11+, **Pygame** (dibujo + audio) y `ctypes` para `GameCore.so` (o port verificado).
- **Dashboard:** Python 3.11+, **PyQt6** (o Tkinter) + `matplotlib` para gráficas, **SQLite** para persistencia.
- **Tests:** `pytest` (Python); Unity o doctest/GoogleTest vía `pio test -e native` (C++).

---

## 14. Instrucciones finales para Claude Code

- Trabaja en **español** en comentarios, mensajes de commit y documentación.
- Mantén la **lógica de juego independiente del hardware** (nada de `analogRead`/`ledcWrite` dentro de `GameCore`).
- Haz **commits pequeños por fase** y deja los tests en verde antes de avanzar.
- Si una decisión de diseño es ambigua, propón la opción más sencilla y robusta y sigue adelante; pregunta solo si es indispensable.
- Al final, escribe en el `README.md` los comandos exactos para: correr el simulador, correr el dashboard, correr todos los tests y flashear el ESP32.
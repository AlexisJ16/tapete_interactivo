# Rediseño del dashboard — "Pantalla del doctor" (A2)

**Fecha:** 2026-07-07 · **Estado:** aprobado, listo para plan de implementación.
**Andamiaje:** este documento vive en `docs/superpowers/` y se purga del snapshot de entrega.

## 1. Objetivo

Convertir el dashboard del terapeuta en una **única pantalla clínica** que el
doctor usa mientras un niño juega en el tapete: iniciar el juego, elegir modo y
nivel, ver el juego en vivo, y recibir métricas y una recomendación de
dificultad que **apoye su toma de decisiones**. La prueba con hardware (A1) se
hará **contra esta pantalla** por **USB/Serial**.

## 2. Requisitos (del autor)

1. **Una sola ventana, tres zonas simultáneas** (aprobado): juego en vivo grande
   a la izquierda (~60%); a la derecha, dos paneles iguales apilados: **métricas**
   (arriba) y **análisis + recomendación** (abajo).
2. **Control desde la pantalla**: iniciar/pausar/detener, elegir modo y nivel,
   identificar el perfil del niño.
3. **Recomendación asistida**: se muestra la sugerencia de subir/bajar nivel y el
   terapeuta la **aplica con un clic** (no automática).
4. **Análisis = lógica adaptativa existente (SP1)** presentada de forma clara;
   **sin IA/LLM**, sin dependencias externas.
5. **Conexión USB/Serial** a 115200 (no WiFi para esta prueba).
6. **Máxima pulidez y profesionalismo visual/interactivo**, con **foco clínico**:
   en pantalla solo información que ayude al doctor a decidir. **Nada de ruido
   técnico** (semilla, puerto, jerga de firmware/IDs internos fuera de la vista).
7. El **histórico entre sesiones** (evolución por perfil, matplotlib) se conserva
   como **segunda pestaña**.

## 3. Hechos verificados que fundan el diseño

Verificado en `firmware/lib/GameCore/` (fuente de verdad) y `shared/protocol.md`:

- `score` se emite **una vez por ronda** en los 3 modos, y cada `score` sube
  exactamente **+1** en `hits` **o** `misses` (`GameEngine.cpp:129-136`). → La
  **tendencia de acierto por ronda es reconstruible** en el dashboard desde los
  deltas, sin tocar firmware. (Cuidado: el campo `round` **no** sirve para esto —
  en Memoria es la longitud de secuencia; usar los deltas de `hits`/`misses`.)
- `suggest` lo calcula `adapt::Recomendador` con **ventana W=4** (`Config.h:118`):
  `tasa≥0.75 → up`, `tasa≤0.25 → down`, resto `keep`; requiere ventana llena y
  satura en `[1,4]`. Se emite **solo al cambiar de dirección** (`GameEngine.cpp:141-148`).
- El motor **nunca cambia el nivel solo** (solo sugiere); `set_level` **sí** surte
  efecto en RUNNING, desde la ronda siguiente (`GameEngine.cpp:57-64`). → El botón
  **"Aplicar" funciona**.

## 4. Arquitectura

Extracción **moderada**. No se reescribe lo que funciona (`Sesion`, `storage`,
`FuenteCore`, `Recomendador`, `analitica`).

- **`dashboard/fuente.py`** — se añade **`FuenteSerial`** (hermana de `FuenteCore`
  / `FuenteTCP`, misma interfaz `enviar`/`recibir`/`cerrar`).
- **`dashboard/paneles.py`** (nuevo) — widgets con responsabilidad única:
  `PanelJuego`, `PanelMetricas`, `PanelAnalisis`. Reutiliza `CeldaLed`.
- **`dashboard/app.py`** — ensambla la ventana (barra de controles + `QSplitter`),
  la 2ª pestaña Histórico (el `PanelAnalitica` actual, intacto), `--serial`,
  `smoke` y `main`.
- **`dashboard/analitica.py`** — se añade una función **pura** `tendencia_ventana`
  (o equivalente) para el cálculo del análisis en vivo (sin Qt, testeable).

### Frontera de datos (sin duplicar lógica de juego)

`sesion.py` ya consume el protocolo y expone estado (`leds`, `hits`, `misses`,
`rondas`, `ultimo_rt`, `estado`, `ultima_sugerencia`). Los paneles **leen** de
`Sesion`; no reimplementan lógica. La única lógica nueva es de **visualización**:
derivar la tendencia de la ventana reciente a partir de los `score` observados.

## 5. Componentes

### 5.1 PanelJuego (izquierda, ~60%)
- Rejilla 2×3 de `CeldaLed` (gris = LED blanco PWM) reflejando los eventos `led`.
- Estado y ronda en grande y legibles.
- Con `FuenteCore` sigue siendo "pisable" con el ratón (pruebas sin hardware).

### 5.2 PanelMetricas (derecha-arriba)
- Tarjetas Qt propias (paintEvent/estilo, **sin matplotlib** — el refresco es a
  25 Hz): **Aciertos**, **Errores**, **Tasa de acierto de sesión** (acumulada),
  **Tiempo de reacción** (ms), **Ronda**.
- Color semántico: aciertos en verde, errores en rojo; tipografía jerarquizada
  (cifra grande + rótulo).

### 5.3 PanelAnalisis (derecha-abajo) — apoyo a la decisión
- **Tendencia reciente**: aciertos de las **últimas 4 rondas** (misma ventana que
  el motor) como puntos ●/○ + porcentaje. Derivada de los deltas de `score`.
- **Recomendación del motor**: la última `suggest` mostrada **verbatim**
  (dirección, nivel sugerido, `rate`, `window`) — el motor es la autoridad.
  Color: verde=subir, ámbar=bajar, neutro=mantener.
- **Botón "Aplicar"**: habilitado solo cuando hay cambio sugerido; envía
  `set_level(level)` (vía `Sesion.set_nivel`) y sincroniza el control de nivel.
- **Coherencia de cifras** (requisito): la "tasa reciente (4)" usa W=4 igual que
  el motor, así ≈ el `rate` del `suggest`; se **etiqueta distinta** de la "tasa de
  sesión" (acumulada) del panel de métricas. No pueden contradecirse en pantalla.

### 5.4 Barra de controles (superior, cruza la ventana)
- Perfil (ID + Nombre), Modo (combo), Nivel (spin 1–4), **Start / Pausa / Stop**.
- **Sin semilla** en la vista (valor por defecto interno fijo). Export CSV/PDF en
  una franja inferior discreta.

### 5.5 Pestaña Histórico
- El `PanelAnalitica` actual (evolución por perfil), sin cambios de fondo.

## 6. FuenteSerial

- **pyserial 3.5** (ya en el venv; declararlo en `dashboard/requirements.txt`).
- Puerto a 115200, **no bloqueante** (`timeout=0`), `enviar` añade `\n`.
- `recibir()` parte el buffer por `\n` y devuelve líneas; **tolera basura**: el
  banner/avisos de arranque del ESP32 no son JSON y `sesion.py` ya los descarta
  con `except JSONDecodeError`. La fuente no filtra; solo entrega líneas.
- `app.py`: `--serial <puerto>` (p. ej. `/dev/ttyUSB0` o `/dev/ttyACM0`),
  **excluyente** con `--tcp`.
- Lo lanza **el humano** (`guard-flash` bloquea al agente abrir el serial).

## 7. Diseño visual (pulidez clínica)

Requisito de primera clase. Dirección (el detalle fino se cierra en la
implementación con la guía `frontend-design`):

- Estética limpia y de **alto contraste**, tipografía legible a distancia de
  consulta, jerarquía clara (lo accionable resalta).
- **Color con significado**, no decorativo: verde acierto/subir, rojo error,
  ámbar precaución/bajar, neutro para mantener.
- El **panel de juego** puede usar fondo oscuro para que los LEDs blancos
  resalten (como el simulador), dentro de un marco general sobrio.
- Estados legibles de un vistazo (idle/running/paused/finished).
- **Nada en pantalla que no sirva al doctor** para decidir.

## 8. Pruebas (TDD; suite verde en cada paso)

- **Nuevos**: `test_fuente_serial.py` (loop:// — round-trip + tolerancia a
  no-JSON), test de `tendencia_ventana` (pura), `test_paneles.py` (headless:
  métricas reflejan `Sesion`; análisis deriva tendencia y "Aplicar" emite
  `set_level`).
- **Actualizar** (presupuestado): `test_app_smoke`, `test_analitica_widget`,
  `test_integracion` referencian atributos de la ventana; se ajustan a la nueva
  estructura. `./scripts/run_all_tests.sh` **TODO VERDE** antes de avanzar.

## 9. Fuera de alcance (YAGNI)

- IA/LLM para el análisis. WiFi/TCP para esta prueba (se conserva `FuenteTCP`).
- Cambios en `GameCore`/firmware o en el protocolo.
- Semilla visible; rediseño del histórico; parámetros del terapeuta por modo
  (ROADMAP §2); patrones de parpadeo (ROADMAP §2).

## 10. Riesgos

- **Romper tests por reestructurar la ventana** → mitigado presupuestando su
  actualización y corriendo la suite en cada paso.
- **HW no responde como se espera** (firmware no flasheado/umbral sin calibrar) →
  hedge: chequeo crudo de 5 min por monitor serial antes de A1 (skill `bring-up`).
- **matplotlib en el refresco** → prohibido en la vista en vivo; solo en histórico.

# SP1 — Lógica adaptable + instrumentación (diseño)

> ✅ **SP1 IMPLEMENTADO Y VALIDADO — 2026-06-22.** Diseño materializado por completo; los 5 criterios de aceptación de §6 se verificaron empíricamente (suite C++ 43/2134 + pytest 21 + firmware SUCCESS). Plan de implementación archivado en `../plans/archive/2026-06-04-sp1-logica-adaptable.md` (lleva el cuadro Task→commit→evidencia). Diseño histórico; trabajo activo: SP2.

- **Fecha:** 2026-06-04
- **Sub-proyecto:** SP1 de 4 (ver "Mapa de sub-proyectos" al final)
- **Estado de partida:** repositorio en verde (`./scripts/run_all_tests.sh` TODO
  VERDE; `pio run -e esp32dev` SUCCESS).
- **Objetivo de grado que refuerza:** Objetivo específico 2 — "desarrollar el
  firmware… implementando diferentes modos terapéuticos **adaptables** a las
  necesidades de los niños". Hoy los modos solo tienen niveles fijos; SP1 los
  vuelve realmente adaptables bajo un esquema **human-in-the-loop**.

## 1. Propósito

Dotar al sistema de una capa que **evalúa automáticamente el desempeño** del niño
y **recomienda** subir, mantener o bajar el nivel de dificultad, dejando la
**decisión final en el terapeuta**. Es un sistema de apoyo a la decisión clínica,
no un mecanismo que actúe por su cuenta sobre un niño. Esta distinción es
deliberada y se sostiene en la redacción académica (SP4).

## 2. Decisiones de diseño (tomadas y justificadas)

| # | Decisión | Justificación |
|---|----------|---------------|
| D1 | **Adaptación asistida** (human-in-the-loop): el sistema sugiere; el terapeuta aplica. | Máximo control clínico en población vulnerable; el sistema sí *calcula* la recomendación automáticamente, lo que satisface el espíritu del Objetivo 2 sin ceder el control. |
| D2 | **Evaluación en vivo, tras cada ronda**: se mantiene una "sugerencia actual" que cambia con el desempeño reciente. | Útil durante la sesión y demostrable; la última sugerencia sirve además como cierre. |
| D3 | **Regla: tasa de acierto en ventana móvil + histéresis.** | Estable frente a aciertos/fallos aislados, explicable ante el jurado y al terapeuta, uniforme en los 3 modos, determinista (golden-friendly). |
| D4 | **Aplicación desde la próxima ronda, sin reiniciar la sesión.** | Experiencia fluida; conserva los contadores; obliga a un refactor menor y prolijo (nivel dinámico por ronda) que de paso corrige un bug latente de `set_level`. |
| D5 | **Evento `suggest` con `rate` y `window`.** | Permite al terapeuta entender *por qué* se sugiere y deja traza para la evidencia (SP2). |
| D6 | **`W = 4` por defecto** (ventana). | Compromiso entre estabilidad y adaptación temprana en sesiones cortas; se calibrará empíricamente en SP2. |

## 3. Alcance de SP1

**Entra:**
- Lógica del `Recomendador` en `firmware/lib/GameCore/`.
- Refactor de "nivel dinámico por ronda" en los 3 modos y en `GameEngine`.
- Evento de protocolo `suggest` (documentación, serialización C++, parseo Python).
- Golden vectors nuevos y tests (doctest + pytest).
- Mínimo en simulador/dashboard: **reconocer** el evento `suggest` sin romperse.

**No entra (se difiere a SP2):**
- Vista en vivo de la sugerencia en el dashboard (resaltar, botón "aplicar").
- Analítica histórica entre sesiones y reportes.
- Persistencia enriquecida de las sugerencias en SQLite.

## 4. Diseño detallado

### 4.1 Componente nuevo: `Recomendador`
Clase pequeña con una sola responsabilidad: dado el flujo de resultados de ronda,
decidir la sugerencia. Vive en `firmware/lib/GameCore/` (portable, sin Arduino).

- **Estado interno:** ventana móvil (cola) de los últimos `W` resultados
  booleanos (acierto/fallo). **Nada más:** `evaluar()` es una función pura de
  `(ventana, nivelActual)`. (La validación movió la dedup de dirección a
  `GameEngine`; ver §4.4 y bitácora §10.)
- **Entrada:** `registrarResultado(bool acierto)`.
- **Consulta:** `Sugerencia evaluar(int nivelActual) const`, donde
  `Sugerencia { Direccion dir; int nivelSugerido; float tasa; int n; }` y
  `Direccion ∈ {SUBIR, MANTENER, BAJAR}`. `tasa` es float **interno** (0..1); se
  serializa como entero porcentaje en el evento (§4.3).
- **Regla:** solo decide con la ventana llena (`n == W`; si `n < W → MANTENER`).
  `tasa ≥ umbralAlto → SUBIR`; `tasa ≤ umbralBajo → BAJAR`; en medio `MANTENER`.
  `nivelSugerido = clamp(nivelActual ± 1, nivelMin, nivelMax)`. **Saturación:** si
  `nivelSugerido == nivelActual` (ya en el tope/piso), `dir` se fuerza a
  `MANTENER` (no hay cambio accionable).
- **Banda muerta = anti-oscilación:** la zona neutra `(umbralBajo, umbralAlto)`
  evita los flips por aciertos/fallos aislados; es pura y sin estado.
- **Ciclo de vida:** se reinicia al iniciar cada sesión.

*Alternativa descartada:* alojar este estado dentro de `GameEngine`. Una clase
aparte se prueba en aislamiento con secuencias de resultados y no engrosa el motor.

### 4.2 Refactor: nivel dinámico por ronda
Hoy cada modo congela sus parámetros en el constructor (`ventana_`, `rondas_`,
`k_`, `limite_`, longitudes, tiempos). Para que un cambio de nivel surta efecto en
la **próxima ronda** sin reiniciar:

- Se añade `int nivelActual() const` a `IMotor` (lo implementa `GameEngine`
  devolviendo `nivel_`).
- Cada modo recalcula **solo sus parámetros por ronda** desde `Config` con
  `m_.nivelActual()`, en el punto donde arranca una ronda. Los parámetros **de
  sesión** (los que definen cuándo termina) se congelan al `START` y no cambian a
  mitad, para no alargar/cortar la sesión de forma sorpresiva:

  | Modo | Por ronda (recalcula con el nivel actual) | De sesión (congelado al START) |
  |------|-------------------------------------------|--------------------------------|
  | Velocidad | `ventana` (en `nuevoObjetivo`) | `rondas` |
  | Equilibrio | `k`, `limite` (en `nuevoPatron`) | `rondas` |
  | Memoria | `onMs`, `gapMs` (en `iniciarExhibicion`) | `longitudInicial`, `longitudMax` |

  (Corrige el borrador previo de §4.2, que listaba `longitudMax` de Memoria como
  por-ronda: es de sesión — define el fin de la partida; ver bitácora §10.)
- `set_level` en `RUNNING` pasa a **solo actualizar `nivel_`** (ya no recrea el
  modo); en `IDLE`/`FINISHED` sigue recreándolo. Esto corrige el bug latente
  actual (recrear sin iniciar dejaba el modo inconsistente).

### 4.3 Protocolo: evento `suggest`
Cerebro → PC. Se emite **solo cuando la dirección sugerida cambia** respecto a la
última emitida (evita ruido; la dedup vive en `GameEngine`, §4.4). Esquema
canónico (orden de claves fijo, como el resto del protocolo):

```json
{"ev":"suggest","mode":2,"from":2,"level":3,"dir":"up","rate":75,"window":4}
```

(Ejemplo coherente con los defaults: 3 de 4 aciertos = tasa interna 0.75 ≥
`umbralAlto` 0.75 → `dir` `up`; `rate` se transmite como **entero porcentaje** 75.)

- `mode`: modo actual (1/2/3).
- `from`: nivel actual.
- `level`: nivel sugerido (`clamp(from ± 1, nivelMin, nivelMax)`).
- `dir`: `"up" | "down" | "keep"` (al saturar el nivel → `"keep"`, §4.1).
- `rate`: **entero porcentaje 0..100** = `round(tasa·100)`. El protocolo es
  entero-o-cadena (`protocol.md §2`); no se introducen floats por el cable. Por
  dentro el `Recomendador` usa float; el dashboard mostrará `rate %`.
- `window`: tamaño de ventana usado.

Orden de claves canónico a añadir en `shared/protocol.md §3`:
`suggest : ev, mode, from, level, dir, rate, window`.

Se documenta en `shared/protocol.md`, se serializa en `Protocol.cpp` con el
mini-serializador existente (todo `int`/cadena; **sin tocar la gramática**) y se
parsea idéntico en Python. El round-trip C++ de §5 queda trivial porque `rate` es
entero (no hay que extender `leerEntero`/`Par`).

### 4.4 Flujo de datos en `GameEngine`
`GameEngine` ya centraliza todos los `score()` de los modos. Mantiene tres campos
nuevos: `prevHits_/prevMisses_` (para derivar el resultado) y `ultimaDirEmitida_`
(para la dedup de emisión). En cada `score(hits, misses, …)`:
1. `acierto = (hits - prevHits_) > 0` (≡ `Δmisses == 0`); luego actualiza
   `prevHits_/prevMisses_`. **No** se usa el campo `round`: en Memoria vale `len_`
   y no es monótono (verificado en `ModoMemoria.cpp:80-82,92-94`).
2. `recomendador.registrarResultado(acierto)`.
3. `s = recomendador.evaluar(nivel_)`.
4. Si `s.dir != ultimaDirEmitida_` → emite `suggest` y actualiza
   `ultimaDirEmitida_`. Esta dedup (no el `Recomendador`) es lo que evita repetir
   la misma dirección; `evaluar()` permanece puro.

`prevHits_/prevMisses_/ultimaDirEmitida_` se reinician junto con el `Recomendador`
al `START`. Los modos no se enteran: la mecánica de juego queda intacta y la
fuente única de verdad se conserva.

### 4.5 Configuración (`cfg::adaptacion`, todo ajustable)
Defaults de partida (se calibran con la evidencia de SP2):
`W = 4`, `umbralAlto = 0.75`, `umbralBajo = 0.25`, `nivelMin = 1`, `nivelMax = 4`.
Los umbrales son **float** (lógica interna); solo el campo `rate` del evento se
emite como entero porcentaje (§4.3). La narrativa académica "tasa ≥ 0.75" se
mantiene intacta en `Config`.

## 5. Estrategia de pruebas (TDD: test → fallar → mínimo)

- **Unitarios del `Recomendador`** (doctest, sobre la función pura `evaluar`):
  rachas de aciertos → `SUBIR`; rachas de fallos → `BAJAR`; mezclas/banda muerta →
  `MANTENER`; ventana incompleta (`n < W`) → `MANTENER`; saturación en
  `nivelMin/nivelMax` → `dir = MANTENER` (no hay cambio accionable).
- **Unitarios de la dedup en `GameEngine`** (doctest): una dirección repetida
  emite `suggest` **una sola vez**; vuelve a emitir solo cuando la dirección
  cambia.
- **Unitarios del refactor de modos** (doctest): cambiar nivel a mitad de sesión →
  la próxima ronda usa los parámetros nuevos; contadores intactos; los parámetros
  de sesión no cambian.
- **Golden vectors nuevos** (`shared/golden_vectors.json`, reproducidos contra
  `libgamecore.so`): (a) escenario que produce `suggest up`; (b) escenario que
  produce `suggest down`; (c) escenario que aplica `set_level` a mitad y verifica
  el stream exacto (`strict`).
- **Round-trip de `suggest`**: serializar → parsear → comparar, en C++ y Python.
- **No regresión:** los golden vectors y tests existentes deben seguir verdes; en
  particular, revisar que el nuevo comportamiento de `set_level` no rompa
  escenarios actuales.

## 6. Criterios de aceptación de SP1

1. `./scripts/run_all_tests.sh` → TODO VERDE (incluye los nuevos tests y golden).
2. `pio run -e esp32dev` → SUCCESS (el firmware sigue compilando con los cambios).
3. El `Recomendador` produce las sugerencias esperadas en sus tests unitarios.
4. Los 3 golden vectors nuevos reproducen exactamente contra el `.so`.
5. El simulador y el dashboard no se rompen al recibir `suggest`.

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| El refactor toca los 3 modos → regresión. | TDD; los golden vectors existentes deben permanecer verdes. |
| Cambiar `set_level` en RUNNING altera golden vectors actuales. | Revisar y, si aplica, versionar los escenarios afectados. |
| Sesiones cortas → adaptación poco visible. | Aceptado en SP1; calibración de `W`/umbrales con datos en SP2. |

## 8. Oportunidades de mejora y decisiones diferidas

> Capturado a propósito para no perder ninguna mejora. Se implementarán **paso a
> paso**, a su tiempo. Nada de esto bloquea SP1.

### 8.A Extensiones naturales de la lógica adaptable (futuros incrementos sobre SP1)
- **Regla compuesta (tasa + rapidez):** incorporar el tiempo de respuesta relativo
  a la ventana del nivel para distinguir "domina con holgura" de "acierta al
  límite". Hoy solo se usa la tasa de acierto.
- **Modo automático supervisado (opcional, configurable):** permitir que, si el
  terapeuta lo habilita, el sistema aplique la sugerencia por sí mismo, con tope
  de cambios y posibilidad de congelar. Hoy es estrictamente asistido (D1).
- **Recomendación de cierre de sesión:** además de la sugerencia en vivo, una
  recomendación consolidada de nivel para la próxima sesión, persistida por perfil.
- **Recomendación de cambio de modo**, no solo de nivel, cuando el desempeño lo
  sugiera.
- **Calibración empírica de `W` y umbrales** con datos reales (depende de SP2).
- **Persistir la calibración por dispositivo/perfil.**

### 8.B Mejoras de los modos (del ROADMAP; tocan la lógica de GameCore)
- **Patrones de parpadeo más ricos** (no bloqueantes, fijados con golden):
  barrido de inicio de ronda; error = 3 parpadeos rápidos; acierto = LED sólido.
  Hoy el feedback es encender/apagar + sonido.
- **Memoria — tolerancia de tiempo de entrada** (timeout por pisada configurable)
  y reintentos antes de bajar longitud.
- **Velocidad — ventana adaptativa** según desempeño reciente (encaja con 8.A).
- **Equilibrio — subnivel "orden específico"** (hoy es "cualquier orden").
- **Parámetros configurables por el terapeuta** desde el dashboard (tiempos,
  longitudes), no solo niveles fijos en `Config.h`.

### 8.C Pertenecen a sub-proyectos posteriores (referenciadas para no perderlas)
- **SP2 — Evidencia + analítica + CI:** vista en vivo de la sugerencia; analítica
  de evolución por perfil (matplotlib); vista de historial filtrable; reconexión
  TCP automática; CI en GitHub Actions; ampliar golden vectors `strict` a Memoria
  y Equilibrio; unir simulador y dashboard por TCP.
- **SP3 — Prototipo físico + caracterización:** conseguir **6 resistencias de
  10 kΩ** (pull-down de los FSR; las 12 de 110 Ω son para los LEDs); montaje de los
  6 botones; alimentación de LEDs a 5 V (transistor/ULN2803) para brillo pleno;
  microSD con `/mp3/000X.mp3`; calibración de `UMBRAL_PISADA`; caracterización
  (latencia pisada→respuesta, % de detección, curva fuerza→ADC, estabilidad TCP).
- **SP4 — Reescritura académica integradora:** corregir Objetivo 1 a **LED blanco
  justificado** (accesibilidad sin color, costo, PWM robusto); reescribir
  Metodología y Resultados **en tiempo honesto** con la evidencia real; incorporar
  la arquitectura de software (fuente única, validación en software antes del
  hardware, golden vectors) como contribución; trazabilidad objetivo→evidencia;
  actualizar anteproyecto V3 y artículo.

## 9. Mapa de sub-proyectos (contexto)

| # | Sub-proyecto | Depende de hardware |
|---|--------------|:---:|
| **SP1** | **Lógica adaptable + instrumentación (este documento)** | No |
| SP2 | Evidencia funcional + analítica + CI | No |
| SP3 | Prototipo físico + caracterización | Sí |
| SP4 | Reescritura académica integradora | No |

Secuencia acordada: **SP1 → SP2 → SP3 → SP4**. Cada uno tiene su propio ciclo
diseño → plan → implementación con TDD.

## 10. Bitácora de validación (2026-06-04)

Validación profunda de esta spec contra el código real **antes** de escribir el
plan de implementación. Veredicto: diseño sólido y bien anclado; 12 afirmaciones
verificadas, 1 amienda material y varias precisiones. Decisiones del usuario y
correcciones aplicadas a este documento:

- **`rate` = entero porcentaje 0..100** (no float). El protocolo es entero-o-cadena
  (`protocol.md §2`; `Protocol.cpp:9-14,44-52`); un float rompería el `strict`
  byte-a-byte de los golden (`std::to_string(0.75)` → `"0.750000"`) y obligaría a
  extender el mini-parser. Float por dentro, entero por el cable. (§4.3, §4.5)
- **Saturación → `dir:"keep"`**: al estar ya en el tope/piso no hay cambio
  accionable; evita el evento contradictorio `from=4/level=4/dir=up`. (§4.1, §4.3)
- **Histéresis = banda muerta (pura, en `evaluar`) + dedup de emisión (en
  `GameEngine`, `ultimaDirEmitida_`).** Se eliminó el estado "última dirección" del
  `Recomendador` (la §4.1 original lo ubicaba mal y duplicaba la §4.4). (§4.1, §4.4)
- **`acierto = Δhits>0`** derivado de los acumuladores `(hits,misses)`, **no** del
  campo `round` (en Memoria `round = len_`, no monótono). Válido en los 3 modos.
  (§4.4)
- **Split sesión/por-ronda de Memoria corregido**: `longitudInicial/longitudMax`
  son de sesión (definen el fin), no por-ronda. (§4.2)

Evidencias que de-riesgan el plan:

- **Ningún golden vector ni doctest ejercita `set_level` en RUNNING** (`grep`
  confirmado) → el refactor de `set_level` (corrige el bug latente de
  `GameEngine.cpp:57-60`, que recrea el modo sin iniciarlo) es **aditivo**: no
  rompe la suite ni obliga a re-versionar goldens.
- Ambos parsers Python (`sesion.py:73-94`, `tapete_sim.py:76-87`) **ya** ignoran
  `ev` desconocido → "el dashboard/simulador no se rompe con `suggest`" se cumple
  hoy con cero cambios. El alcance en SP1 se limita a capturar `ultimo_suggest`
  (espejo de `ultimo_score`) + un test de no-regresión; **sin UI** (la vista en
  vivo es SP2).
- `score()` está centralizado en `GameEngine` (`GameEngine.cpp:121-123`) y los
  modos solo usan `IMotor` → el `Recomendador` se engancha en un único punto sin
  tocar la mecánica de los modos.

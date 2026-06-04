# SP1 — Lógica adaptable + instrumentación (diseño)

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
  booleanos (acierto/fallo); última dirección emitida (para la histéresis).
- **Entrada:** `registrarResultado(bool acierto)`.
- **Consulta:** `Sugerencia evaluar(int nivelActual) const`, donde
  `Sugerencia { Direccion dir; int nivelSugerido; float tasa; int n; }` y
  `Direccion ∈ {SUBIR, MANTENER, BAJAR}`.
- **Regla:** solo decide con la ventana llena (`n == W`).
  `tasa ≥ umbralAlto → SUBIR`; `tasa ≤ umbralBajo → BAJAR`; en medio `MANTENER`.
  `nivelSugerido` satura en `[nivelMin, nivelMax]`.
- **Histéresis:** no vuelve a proponer una dirección ya emitida hasta que la
  tendencia cambie (evita repetir/oscilar).
- **Ciclo de vida:** se reinicia al iniciar cada sesión.

*Alternativa descartada:* alojar este estado dentro de `GameEngine`. Una clase
aparte se prueba en aislamiento con secuencias de resultados y no engrosa el motor.

### 4.2 Refactor: nivel dinámico por ronda
Hoy cada modo congela sus parámetros en el constructor (`ventana_`, `rondas_`,
`k_`, `limite_`, longitudes, tiempos). Para que un cambio de nivel surta efecto en
la **próxima ronda** sin reiniciar:

- Se añade `int nivelActual() const` a `IMotor`.
- Cada modo recalcula sus parámetros **por ronda** desde `Config` con el nivel
  actual, en el punto donde arranca una ronda:
  - Velocidad → en `nuevoObjetivo` (ventana de reacción).
  - Equilibrio → en `nuevoPatron` (número de casillas `k` y tiempo límite).
  - Memoria → en la próxima exhibición (velocidad de exhibición y longitud máxima).
- Los parámetros **de sesión** (número total de rondas) se fijan al `START` y no
  cambian a mitad, para no alargar/cortar la sesión de forma sorpresiva.
- `set_level` en `RUNNING` pasa a **solo actualizar `nivel_`** (ya no recrea el
  modo); en `IDLE`/`FINISHED` sigue recreándolo. Esto corrige el bug latente
  actual (recrear sin iniciar dejaba el modo inconsistente).

### 4.3 Protocolo: evento `suggest`
Cerebro → PC. Se emite **solo cuando la dirección sugerida cambia** respecto a la
última emitida (evita ruido). Esquema canónico (orden de claves fijo, como el
resto del protocolo):

```json
{"ev":"suggest","mode":2,"from":2,"level":3,"dir":"up","rate":0.75,"window":4}
```

(Ejemplo coherente con los defaults: 3 de 4 aciertos = `rate` 0.75 ≥ `umbralAlto`
0.75 → `dir` `up`.)

- `mode`: modo actual (1/2/3).
- `from`: nivel actual.
- `level`: nivel sugerido (`from ± 1`, saturado).
- `dir`: `"up" | "down" | "keep"`.
- `rate`: tasa de acierto observada en la ventana (0..1).
- `window`: tamaño de ventana usado.

Se documenta en `shared/protocol.md`, se serializa en `Protocol.cpp` siguiendo el
mini-serializador existente y se parsea idéntico en Python.

### 4.4 Flujo de datos en `GameEngine`
`GameEngine` ya centraliza todos los `score()` de los modos. En cada `score()`:
1. Deriva `Δhits/Δmisses` respecto al `score` anterior → resultado de la ronda.
2. `recomendador.registrarResultado(acierto)`.
3. `s = recomendador.evaluar(nivel_)`.
4. Si `s.dir` cambió respecto a la última emitida → emite `suggest`.

Los modos no se enteran: la mecánica de juego queda intacta y la fuente única de
verdad se conserva.

### 4.5 Configuración (`cfg::adaptacion`, todo ajustable)
Defaults de partida (se calibran con la evidencia de SP2):
`W = 4`, `umbralAlto = 0.75`, `umbralBajo = 0.25`, `nivelMin = 1`, `nivelMax = 4`.

## 5. Estrategia de pruebas (TDD: test → fallar → mínimo)

- **Unitarios del `Recomendador`** (doctest): rachas de aciertos → `SUBIR`;
  rachas de fallos → `BAJAR`; mezclas → `MANTENER`; histéresis (no repite);
  saturación en `nivelMin/nivelMax`; ventana incompleta → `MANTENER`.
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

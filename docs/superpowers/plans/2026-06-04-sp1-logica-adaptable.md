# SP1 — Lógica adaptable + instrumentación: Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dotar al GameCore de una capa que evalúa el desempeño del niño tras cada ronda y **recomienda** (no aplica) subir/mantener/bajar el nivel, emitiendo un evento `suggest`; refactorizar los modos a "nivel dinámico por ronda" y corregir el bug latente de `set_level` en RUNNING.

**Architecture:** Una sola fuente de verdad en `firmware/lib/GameCore/`. Clase pura `adapt::Recomendador` (ventana móvil + banda muerta) consultada por `GameEngine` en cada `score()`; la de-dup de dirección vive en `GameEngine`. Evento de protocolo `suggest` con `rate` entero-porcentaje (el protocolo es entero-o-cadena, sin floats). Los modos recalculan sus parámetros por-ronda desde `Config` con `m_.nivelActual()`; los parámetros de sesión quedan congelados al START. Validación por doctest + golden vectors (reproducidos contra `build/libgamecore.so`) + pytest.

**Tech Stack:** C++17 portable (sin Arduino), doctest (vendored), `g++` para `.so` + tests, Python 3.12 (.venv), pytest, ctypes.

**Fuente del diseño:** `docs/superpowers/specs/2026-06-04-sp1-logica-adaptable-design.md` (validada; ver bitácora §10 de esa spec).

**Antes de ejecutar:** crear una rama de trabajo (`git switch -c sp1-logica-adaptable`). No commitear en `main`. Todos los comandos se ejecutan **desde la raíz del proyecto**. Las rutas `-I` son **relativas** (sin espacios), aunque la ruta absoluta del proyecto tenga un espacio: no se rompe el word-splitting.

---

## Estructura de archivos

**Crear:**
- `firmware/lib/GameCore/Recomendador.h` — clase pura `adapt::Recomendador`, `adapt::Direccion`, `adapt::Sugerencia`, `adapt::aTexto`.
- `firmware/lib/GameCore/Recomendador.cpp` — implementación de la regla (ventana móvil + umbrales + saturación).
- `firmware/test/test_recomendador/test_recomendador.cpp` — unitarios de la lógica pura.
- `firmware/test/test_adaptacion/test_adaptacion.cpp` — integración en `GameEngine` (nivelActual, suggest up/down, de-dup, saturación).

**Modificar:**
- `firmware/lib/GameCore/Config.h` — añadir `cfg::adaptacion`.
- `firmware/lib/GameCore/Protocol.h` / `.cpp` — evento `suggest` (tipo, campos, factory, serializar, parsear, `operator==`).
- `firmware/lib/GameCore/Motor.h` — añadir `virtual int nivelActual() const = 0;` a `IMotor`.
- `firmware/lib/GameCore/GameEngine.h` / `.cpp` — override `nivelActual()`, miembros de la capa adaptable, `SET_LEVEL` en RUNNING, derivación + emisión de `suggest` en `score()`, reset al START.
- `firmware/lib/GameCore/modes/ModoVelocidad.cpp` — recalcular `ventana_` por ronda en `nuevoObjetivo`.
- `firmware/lib/GameCore/modes/ModoEquilibrio.cpp` — recalcular `k_`/`limite_` por ronda en `nuevoPatron`.
- `firmware/lib/GameCore/modes/ModoMemoria.cpp` — recalcular `onMs_`/`gapMs_` por exhibición en `iniciarExhibicion`.
- `firmware/test/test_modo_velocidad/test_modo_velocidad.cpp` — set_level en RUNNING + ventana por ronda + sesión congelada.
- `firmware/test/test_modo_equilibrio/test_modo_equilibrio.cpp` — `k` por ronda.
- `firmware/test/test_protocolo/test_protocolo.cpp` — serialización canónica + round-trip de `suggest`.
- `shared/golden_vectors.json` — 3 escenarios nuevos (suggest up, suggest down, set_level strict).
- `shared/protocol.md` — documentar `suggest` + orden canónico de claves.
- `simulator/tapete_sim.py` — capturar `ultima_sugerencia`.
- `dashboard/sesion.py` — capturar `ultima_sugerencia`.
- `simulator/test_sim_smoke.py` — el simulador no se rompe con `suggest`.
- `dashboard/test_integracion.py` — `suggest up` de punta a punta (C++ → JSON → Python).

**No se modifican (se verifica que siguen verdes):** `run_all_tests.sh` (auto-descubre `test_*/` y `*.cpp`), `core_bridge.py`, `golden_runner.py`, `simulator/test_golden.py` (parametrizado sobre los escenarios → cubre los nuevos automáticamente).

**Comando de compilación C++ (plantilla para el inner-loop de doctest):**

```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/<DIR>/<FILE>.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/<BIN> && ./build/<BIN>
```

---

## Task 1: Configuración `cfg::adaptacion`

**Files:**
- Modify: `firmware/lib/GameCore/Config.h:112-114`

- [ ] **Step 1: Añadir el namespace `adaptacion` antes del cierre de `cfg`**

En `firmware/lib/GameCore/Config.h`, justo **después** de la línea `}  // namespace equilibrio` (línea 112) y **antes** de `}  // namespace cfg` (línea 114), insertar:

```cpp

// --- Logica adaptable (SP1): recomendacion de nivel asistida ----------------
// El sistema SUGIERE subir/mantener/bajar segun la tasa de acierto en una
// ventana movil; el terapeuta decide. Todo ajustable (se calibra en SP2).
namespace adaptacion {
constexpr int   W          = 4;      // tamano de la ventana movil de resultados
constexpr float umbralAlto = 0.75f;  // tasa >= umbralAlto -> sugerir SUBIR
constexpr float umbralBajo = 0.25f;  // tasa <= umbralBajo -> sugerir BAJAR
constexpr int   nivelMin   = 1;
constexpr int   nivelMax   = 4;
}  // namespace adaptacion
```

- [ ] **Step 2: Verificar que el header compila**

Run:
```bash
g++ -std=c++17 -fsyntax-only -I firmware/lib/GameCore firmware/lib/GameCore/GameEngine.cpp
```
Expected: sin salida (exit 0). El header es válido y no rompe el build existente.

- [ ] **Step 3: Commit**

```bash
git add firmware/lib/GameCore/Config.h
git commit -m "SP1: anade cfg::adaptacion (W, umbrales, nivelMin/Max)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Clase `adapt::Recomendador` (lógica pura)

**Files:**
- Create: `firmware/lib/GameCore/Recomendador.h`
- Create: `firmware/lib/GameCore/Recomendador.cpp`
- Test: `firmware/test/test_recomendador/test_recomendador.cpp`

- [ ] **Step 1: Escribir el test que falla**

Crear `firmware/test/test_recomendador/test_recomendador.cpp`:

```cpp
// Tests unitarios del Recomendador (capa adaptable, logica pura).
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "Recomendador.h"

using namespace adapt;

TEST_CASE("racha de aciertos con ventana llena sugiere SUBIR") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);
    Sugerencia s = r.evaluar(2);
    CHECK(s.dir == Direccion::SUBIR);
    CHECK(s.nivelSugerido == 3);
    CHECK(s.n == 4);
    CHECK(s.tasa == doctest::Approx(1.0));
}

TEST_CASE("racha de fallos con ventana llena sugiere BAJAR") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(false);
    Sugerencia s = r.evaluar(3);
    CHECK(s.dir == Direccion::BAJAR);
    CHECK(s.nivelSugerido == 2);
    CHECK(s.tasa == doctest::Approx(0.0));
}

TEST_CASE("desempeno intermedio (banda muerta) sugiere MANTENER") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    r.registrarResultado(true);  r.registrarResultado(false);
    r.registrarResultado(true);  r.registrarResultado(false);  // 2/4 = 0.5
    Sugerencia s = r.evaluar(2);
    CHECK(s.dir == Direccion::MANTENER);
    CHECK(s.nivelSugerido == 2);
}

TEST_CASE("ventana incompleta siempre sugiere MANTENER") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    r.registrarResultado(true);
    r.registrarResultado(true);
    r.registrarResultado(true);  // n=3 < W=4
    Sugerencia s = r.evaluar(2);
    CHECK(s.dir == Direccion::MANTENER);
    CHECK(s.n == 3);
}

TEST_CASE("saturacion en el nivel maximo fuerza MANTENER (no SUBIR)") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);
    Sugerencia s = r.evaluar(4);  // ya en el tope
    CHECK(s.nivelSugerido == 4);
    CHECK(s.dir == Direccion::MANTENER);
}

TEST_CASE("saturacion en el nivel minimo fuerza MANTENER (no BAJAR)") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(false);
    Sugerencia s = r.evaluar(1);  // ya en el piso
    CHECK(s.nivelSugerido == 1);
    CHECK(s.dir == Direccion::MANTENER);
}

TEST_CASE("la ventana movil descarta los resultados antiguos") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);   // SUBIR
    CHECK(r.evaluar(2).dir == Direccion::SUBIR);
    for (int i = 0; i < 4; ++i) r.registrarResultado(false);  // ya todo fallos
    CHECK(r.evaluar(2).dir == Direccion::BAJAR);
}

TEST_CASE("reiniciar vacia la ventana") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);
    r.reiniciar();
    Sugerencia s = r.evaluar(2);
    CHECK(s.n == 0);
    CHECK(s.dir == Direccion::MANTENER);
}
```

- [ ] **Step 2: Ejecutar el test para verlo fallar (no compila: falta Recomendador.h)**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_recomendador/test_recomendador.cpp \
  firmware/lib/GameCore/Recomendador.cpp \
  -o build/test_recomendador && ./build/test_recomendador
```
Expected: FALLA en compilación — `fatal error: Recomendador.h: No such file or directory`.

- [ ] **Step 3: Escribir el header `Recomendador.h`**

Crear `firmware/lib/GameCore/Recomendador.h`:

```cpp
#ifndef TAPETE_RECOMENDADOR_H
#define TAPETE_RECOMENDADOR_H

#include "Config.h"

// Capa adaptable (SP1): a partir del flujo de resultados de ronda (acierto/fallo)
// en una ventana movil, RECOMIENDA subir/mantener/bajar el nivel. No actua: la
// decision final es del terapeuta (adaptacion asistida, human-in-the-loop).
// Logica PURA y portable: sin Arduino, sin protocolo, sin hardware.
namespace adapt {

enum class Direccion { BAJAR, MANTENER, SUBIR };

// Texto canonico del campo "dir" del evento suggest del protocolo.
inline const char* aTexto(Direccion d) {
    switch (d) {
        case Direccion::SUBIR:    return "up";
        case Direccion::BAJAR:    return "down";
        case Direccion::MANTENER: return "keep";
    }
    return "keep";
}

struct Sugerencia {
    Direccion dir = Direccion::MANTENER;
    int   nivelSugerido = 0;  // clamp(nivelActual +/- 1) en [nivelMin, nivelMax]
    float tasa = 0.0f;        // tasa de acierto en la ventana (0..1), uso INTERNO
    int   n = 0;              // numero de resultados en la ventana (hasta W)
};

// Ventana movil de resultados booleanos + regla con banda muerta. evaluar() es
// una FUNCION PURA de (ventana, nivelActual): no guarda "ultima direccion"
// (esa de-dup vive en GameEngine).
class Recomendador {
public:
    explicit Recomendador(int W           = cfg::adaptacion::W,
                          float umbralAlto = cfg::adaptacion::umbralAlto,
                          float umbralBajo = cfg::adaptacion::umbralBajo,
                          int nivelMin     = cfg::adaptacion::nivelMin,
                          int nivelMax     = cfg::adaptacion::nivelMax);

    void reiniciar();
    void registrarResultado(bool acierto);
    Sugerencia evaluar(int nivelActual) const;

private:
    static constexpr int kMax = 32;  // tope de capacidad de la ventana
    int   W_;
    float umbralAlto_;
    float umbralBajo_;
    int   nivelMin_;
    int   nivelMax_;

    bool ventana_[kMax];
    int  n_ = 0;        // resultados validos en la ventana (hasta W_)
    int  cabeza_ = 0;   // indice circular: proxima escritura / mas antiguo
    int  aciertos_ = 0; // numero de 'true' en la ventana (tasa en O(1))
};

}  // namespace adapt

#endif  // TAPETE_RECOMENDADOR_H
```

- [ ] **Step 4: Escribir la implementación `Recomendador.cpp`**

Crear `firmware/lib/GameCore/Recomendador.cpp`:

```cpp
#include "Recomendador.h"

namespace adapt {

Recomendador::Recomendador(int W, float umbralAlto, float umbralBajo,
                           int nivelMin, int nivelMax)
    : W_(W < 1 ? 1 : (W > kMax ? kMax : W)),
      umbralAlto_(umbralAlto),
      umbralBajo_(umbralBajo),
      nivelMin_(nivelMin),
      nivelMax_(nivelMax) {
    reiniciar();
}

void Recomendador::reiniciar() {
    n_ = 0;
    cabeza_ = 0;
    aciertos_ = 0;
}

void Recomendador::registrarResultado(bool acierto) {
    if (n_ < W_) {
        ventana_[cabeza_] = acierto;
        if (acierto) ++aciertos_;
        cabeza_ = (cabeza_ + 1) % W_;
        ++n_;
    } else {
        // Ventana llena: 'cabeza_' apunta al mas antiguo; se reemplaza.
        if (ventana_[cabeza_]) --aciertos_;
        ventana_[cabeza_] = acierto;
        if (acierto) ++aciertos_;
        cabeza_ = (cabeza_ + 1) % W_;
    }
}

Sugerencia Recomendador::evaluar(int nivelActual) const {
    Sugerencia s;
    s.n = n_;
    s.tasa = (n_ > 0) ? static_cast<float>(aciertos_) / static_cast<float>(n_)
                      : 0.0f;
    s.nivelSugerido = nivelActual;
    s.dir = Direccion::MANTENER;

    if (n_ < W_) return s;  // ventana incompleta -> MANTENER

    if (s.tasa >= umbralAlto_) {
        s.dir = Direccion::SUBIR;
        s.nivelSugerido = nivelActual + 1;
    } else if (s.tasa <= umbralBajo_) {
        s.dir = Direccion::BAJAR;
        s.nivelSugerido = nivelActual - 1;
    }

    if (s.nivelSugerido > nivelMax_) s.nivelSugerido = nivelMax_;
    if (s.nivelSugerido < nivelMin_) s.nivelSugerido = nivelMin_;

    // Saturacion: ya en el tope/piso -> no hay cambio accionable -> keep.
    if (s.nivelSugerido == nivelActual) s.dir = Direccion::MANTENER;

    return s;
}

}  // namespace adapt
```

- [ ] **Step 5: Ejecutar el test para verlo pasar**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_recomendador/test_recomendador.cpp \
  firmware/lib/GameCore/Recomendador.cpp \
  -o build/test_recomendador && ./build/test_recomendador
```
Expected: `[doctest] test cases: 8 | 8 passed` (Status: SUCCESS).

- [ ] **Step 6: Commit**

```bash
git add firmware/lib/GameCore/Recomendador.h firmware/lib/GameCore/Recomendador.cpp firmware/test/test_recomendador/
git commit -m "SP1: Recomendador (ventana movil + banda muerta + saturacion)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Evento de protocolo `suggest`

**Files:**
- Modify: `firmware/lib/GameCore/Protocol.h:16-45`
- Modify: `firmware/lib/GameCore/Protocol.cpp` (Evento: factories, serializar, parsear, operator==)
- Test: `firmware/test/test_protocolo/test_protocolo.cpp`

- [ ] **Step 1: Escribir los tests que fallan (serialización canónica + round-trip)**

En `firmware/test/test_protocolo/test_protocolo.cpp`, **dentro** del `TEST_CASE("eventos se serializan en la forma canonica del protocolo")`, añadir tras la línea del `state` (línea 23, antes del `}` que cierra el case):

```cpp
    CHECK(Evento::suggest(2, 2, 3, "up", 75, 4).serializar() ==
          R"({"ev":"suggest","mode":2,"from":2,"level":3,"dir":"up","rate":75,"window":4})");
```

Y en el `TEST_CASE("round-trip de eventos: parsear(serializar(e)) == e")`, añadir un elemento al arreglo `ev[]` (tras `Evento::state(3, "finished"),`):

```cpp
        Evento::suggest(2, 2, 3, "up", 75, 4),
```

- [ ] **Step 2: Ejecutar para ver el fallo (no compila: falta Evento::suggest)**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_protocolo/test_protocolo.cpp \
  firmware/lib/GameCore/Protocol.cpp \
  -o build/test_protocolo && ./build/test_protocolo
```
Expected: FALLA en compilación — `'suggest' is not a member of 'proto::Evento'`.

- [ ] **Step 3: Añadir el tipo y los campos en `Protocol.h`**

En `firmware/lib/GameCore/Protocol.h`:

1. Cambiar el enum de tipos (línea 17) para añadir `SUGGEST`:
```cpp
    enum class Tipo { HELLO, LED, PRESS, SOUND, SCORE, STATE, SUGGEST, INVALIDO };
```

2. Tras la línea `std::string status;    // state` (línea 31), añadir los campos nuevos:
```cpp
    int from = 0;          // suggest (nivel actual)
    std::string dir;       // suggest ("up" | "down" | "keep")
    int rate = 0;          // suggest (tasa de acierto en %, 0..100)
    int window = 0;        // suggest (tamano de la ventana)
```

3. Tras la línea de la factory `state` (línea 38), añadir la factory `suggest`:
```cpp
    static Evento suggest(int mode, int from, int level,
                          const std::string& dir, int rate, int window);
```

- [ ] **Step 4: Implementar factory, serialización, parseo y `operator==` en `Protocol.cpp`**

En `firmware/lib/GameCore/Protocol.cpp`:

1. Tras la factory `Evento::state(...)` (línea 131-133), añadir:
```cpp
Evento Evento::suggest(int mode, int from, int level,
                       const std::string& dir, int rate, int window) {
    Evento e; e.tipo = Tipo::SUGGEST; e.mode = mode; e.from = from;
    e.level = level; e.dir = dir; e.rate = rate; e.window = window; return e;
}
```

2. En `Evento::serializar()`, tras el `case Tipo::STATE:` (línea 154-156), añadir antes del `default:`:
```cpp
        case Tipo::SUGGEST:
            return "{\"ev\":\"suggest\",\"mode\":" + std::to_string(mode) +
                   ",\"from\":" + std::to_string(from) +
                   ",\"level\":" + std::to_string(level) +
                   ",\"dir\":\"" + escapar(dir) + "\"" +
                   ",\"rate\":" + std::to_string(rate) +
                   ",\"window\":" + std::to_string(window) + "}";
```

3. En `Evento::parsear(...)`, tras el bloque `else if (ev == "state")` (línea 184-186), añadir:
```cpp
    } else if (ev == "suggest") {
        e.tipo = Tipo::SUGGEST;
        e.mode = static_cast<int>(entero(v, "mode"));
        e.from = static_cast<int>(entero(v, "from"));
        e.level = static_cast<int>(entero(v, "level"));
        e.dir = cadena(v, "dir");
        e.rate = static_cast<int>(entero(v, "rate"));
        e.window = static_cast<int>(entero(v, "window"));
```

4. En `Evento::operator==` (línea 191-196), añadir los campos nuevos a la comparación (antes del `;` final):
```cpp
bool Evento::operator==(const Evento& o) const {
    return tipo == o.tipo && fw == o.fw && cells == o.cells && cell == o.cell &&
           level == o.level && ms == o.ms && id == o.id && mode == o.mode &&
           hits == o.hits && misses == o.misses && rt_ms == o.rt_ms &&
           round == o.round && status == o.status &&
           from == o.from && dir == o.dir && rate == o.rate && window == o.window;
}
```

- [ ] **Step 5: Ejecutar para ver pasar**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_protocolo/test_protocolo.cpp \
  firmware/lib/GameCore/Protocol.cpp \
  -o build/test_protocolo && ./build/test_protocolo
```
Expected: todos los TEST_CASE pasan (Status: SUCCESS), incluida la serialización canónica y el round-trip de `suggest`.

- [ ] **Step 6: Commit**

```bash
git add firmware/lib/GameCore/Protocol.h firmware/lib/GameCore/Protocol.cpp firmware/test/test_protocolo/
git commit -m "SP1: evento de protocolo suggest (rate entero %, sin floats)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `IMotor::nivelActual()` + override en `GameEngine`

**Files:**
- Modify: `firmware/lib/GameCore/Motor.h:20-23`
- Modify: `firmware/lib/GameCore/GameEngine.h:41-45`
- Test: `firmware/test/test_adaptacion/test_adaptacion.cpp`

- [ ] **Step 1: Escribir el test que falla**

Crear `firmware/test/test_adaptacion/test_adaptacion.cpp`:

```cpp
// Integracion de la capa adaptable en GameEngine.
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "soporte_test.h"

using namespace proto;

TEST_CASE("IMotor::nivelActual refleja el nivel actual del motor") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":2})"));
    CHECK(motor.nivelActual() == 2);
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":4})"));
    CHECK(motor.nivelActual() == 4);
}
```

- [ ] **Step 2: Ejecutar para ver el fallo (no compila: falta nivelActual)**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_adaptacion/test_adaptacion.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/test_adaptacion && ./build/test_adaptacion
```
Expected: FALLA en compilación — `'class GameEngine' has no member named 'nivelActual'`.

- [ ] **Step 3: Añadir el método puro a `IMotor` y el override a `GameEngine`**

En `firmware/lib/GameCore/Motor.h`, dentro de `struct IMotor`, tras el método `score(...)` (línea 20) y antes de `rng()` (línea 23), añadir:

```cpp
    // Nivel actual de dificultad (1..CELDAS de niveles). Lo usan los modos para
    // recalcular sus parametros POR-RONDA sin recrearse.
    virtual int nivelActual() const = 0;
```

En `firmware/lib/GameCore/GameEngine.h`, en la sección `// --- IMotor (usado por los modos) ---`, tras `Rng& rng() override { return rng_; }` (línea 45), añadir:

```cpp
    int nivelActual() const override { return nivel_; }
```

- [ ] **Step 4: Ejecutar para ver pasar**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_adaptacion/test_adaptacion.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/test_adaptacion && ./build/test_adaptacion
```
Expected: 1 test case, 2 CHECK, pasan (Status: SUCCESS).

- [ ] **Step 5: Commit**

```bash
git add firmware/lib/GameCore/Motor.h firmware/lib/GameCore/GameEngine.h firmware/test/test_adaptacion/
git commit -m "SP1: IMotor::nivelActual() + override en GameEngine

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Cableado adaptable en `GameEngine` (suggest + de-dup)

**Files:**
- Modify: `firmware/lib/GameCore/GameEngine.h:8-12,47-63`
- Modify: `firmware/lib/GameCore/GameEngine.cpp:64-71,121-123`
- Test: `firmware/test/test_adaptacion/test_adaptacion.cpp`

- [ ] **Step 1: Añadir los tests de integración que fallan**

En `firmware/test/test_adaptacion/test_adaptacion.cpp`, añadir al final (antes de nada — son TEST_CASE independientes). Primero, un helper local tras `using namespace proto;`:

```cpp
// Arranca Velocidad con semilla 12345 -> objetivos [3,4,5,3,6,...].
static void arrancarVel(GameEngine& m, int nivel) {
    m.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":12345})"));
    m.procesar(Comando::parsear(
        std::string(R"({"cmd":"set_mode","mode":2,"level":)") +
        std::to_string(nivel) + "}"));
    m.procesar(Comando::parsear(R"({"cmd":"start"})"));
}
```

Y al final del archivo, los casos:

```cpp
TEST_CASE("adaptacion: 4 aciertos seguidos emiten suggest up (rate 100)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 1);                 // nivel 1: ventana 3000, 5 rondas
    const int obj[4] = {3, 4, 5, 3};
    uint32_t t = 100;
    for (int i = 0; i < 4; ++i) { hw.reloj = t; motor.pisar(obj[i]); t += 300; }
    CHECK(contiene(col.eventos, Evento::suggest(2, 1, 2, "up", 100, 4)));
    CHECK(cuenta(col.eventos, Evento::Tipo::SUGGEST) == 1);  // solo una vez
}

TEST_CASE("adaptacion: 4 fallos seguidos emiten suggest down (rate 0)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 2);                 // nivel 2: 8 rondas (no termina)
    uint32_t t = 100;
    for (int i = 0; i < 4; ++i) { hw.reloj = t; motor.pisar(1); t += 100; } // 1 != obj
    CHECK(contiene(col.eventos, Evento::suggest(2, 2, 1, "down", 0, 4)));
}

TEST_CASE("adaptacion: no repite la misma direccion (de-dup)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 1);
    const int obj[5] = {3, 4, 5, 3, 6};
    uint32_t t = 100;
    for (int i = 0; i < 5; ++i) { hw.reloj = t; motor.pisar(obj[i]); t += 300; }
    CHECK(cuenta(col.eventos, Evento::Tipo::SUGGEST) == 1);  // 5 aciertos -> 1 suggest
}

TEST_CASE("adaptacion: en el nivel maximo dominar no emite suggest (keep)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 4);                 // tope: SUBIR satura a keep
    const int obj[4] = {3, 4, 5, 3};
    uint32_t t = 100;
    for (int i = 0; i < 4; ++i) { hw.reloj = t; motor.pisar(obj[i]); t += 300; }
    CHECK(cuenta(col.eventos, Evento::Tipo::SUGGEST) == 0);
}
```

- [ ] **Step 2: Ejecutar para ver el fallo (compila, pero no se emite suggest)**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_adaptacion/test_adaptacion.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/test_adaptacion && ./build/test_adaptacion
```
Expected: FALLAN los 3 casos nuevos que esperan `suggest` (el de "keep" pasa por casualidad: 0==0). `contiene(... suggest ...)` es falso porque aún no se emite.

- [ ] **Step 3: Añadir miembros de la capa adaptable a `GameEngine.h`**

En `firmware/lib/GameCore/GameEngine.h`:

1. Tras `#include "Protocol.h"` (línea 11), añadir:
```cpp
#include "Recomendador.h"
```

2. En la sección `private:`, tras `uint32_t inicio_ = 0;` (línea 62), añadir:
```cpp
    // --- Capa adaptable (SP1) ---
    adapt::Recomendador recomendador_;
    int prevHits_ = 0;
    int prevMisses_ = 0;
    adapt::Direccion ultimaDirEmitida_ = adapt::Direccion::MANTENER;
```

- [ ] **Step 4: Resetear al START y emitir `suggest` en `score()` (`GameEngine.cpp`)**

En `firmware/lib/GameCore/GameEngine.cpp`:

1. En `procesar(...)`, en el `case T::START:` (líneas 64-71), añadir el reset de la capa adaptable tras `inicio_ = hw_.millis();`:
```cpp
        case T::START:
            if (modo_) {
                inicio_ = hw_.millis();
                recomendador_.reiniciar();
                prevHits_ = 0;
                prevMisses_ = 0;
                ultimaDirEmitida_ = adapt::Direccion::MANTENER;
                cambiarEstado(Estado::RUNNING);
                modo_->iniciar(0);
                revisarFin();
            }
            break;
```

2. Reemplazar `GameEngine::score(...)` (líneas 121-123) por:
```cpp
void GameEngine::score(int hits, int misses, int rt_ms, int round) {
    emitir(proto::Evento::score(modoId_, hits, misses, rt_ms, round));

    // --- Capa adaptable (SP1) ---------------------------------------------
    // Deriva el resultado de la ronda de los acumuladores (NO del campo round:
    // en Memoria 'round' = len_, no es monotono). Cada score sube exactamente
    // uno de hits/misses en +1.
    bool acierto = (hits - prevHits_) > 0;
    prevHits_ = hits;
    prevMisses_ = misses;
    recomendador_.registrarResultado(acierto);

    adapt::Sugerencia s = recomendador_.evaluar(nivel_);
    if (s.dir != ultimaDirEmitida_) {            // de-dup: solo al cambiar
        ultimaDirEmitida_ = s.dir;
        int ratePct = static_cast<int>(s.tasa * 100.0f + 0.5f);
        emitir(proto::Evento::suggest(modoId_, nivel_, s.nivelSugerido,
                                      adapt::aTexto(s.dir), ratePct,
                                      cfg::adaptacion::W));
    }
}
```

- [ ] **Step 5: Ejecutar el test de adaptación para verlo pasar**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_adaptacion/test_adaptacion.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/test_adaptacion && ./build/test_adaptacion
```
Expected: 5 test cases, todos pasan (Status: SUCCESS).

- [ ] **Step 6: Verificar que NO hay regresión en toda la suite**

Run:
```bash
./scripts/run_all_tests.sh
```
Expected: TODO VERDE (los 26 casos C++ existentes + los nuevos + pytest). Los golden/doctests previos siguen verdes: con `W=4` no emiten `suggest` espurios (≤2 scores antes de llenar la ventana; los de ≥4 scores son `subsequence` y toleran el evento extra).

- [ ] **Step 7: Commit**

```bash
git add firmware/lib/GameCore/GameEngine.h firmware/lib/GameCore/GameEngine.cpp firmware/test/test_adaptacion/
git commit -m "SP1: GameEngine consulta al Recomendador y emite suggest (de-dup)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Refactor de `set_level` en RUNNING (corrige el bug latente)

**Files:**
- Modify: `firmware/lib/GameCore/GameEngine.cpp:57-60`
- Test: `firmware/test/test_modo_velocidad/test_modo_velocidad.cpp`

- [ ] **Step 1: Escribir el test que falla**

En `firmware/test/test_modo_velocidad/test_modo_velocidad.cpp`, añadir al final del archivo:

```cpp
TEST_CASE("set_level en RUNNING no recrea el modo (conserva la ronda en curso)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);                       // modo 2, nivel 1, objetivo ronda1 = 3

    hw.reloj = 100;
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":3})"));
    CHECK(motor.estado() == Estado::RUNNING);   // sigue corriendo (no reinicia)
    CHECK(motor.nivel() == 3);

    hw.reloj = 200; motor.pisar(3);        // si el modo sigue vivo, es un acierto
    CHECK(contieneScore(col.eventos, 2, 1, 0, 1));  // hit de la ronda 1
}
```

- [ ] **Step 2: Ejecutar para ver el fallo (comportamiento viejo: recrea el modo)**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_modo_velocidad/test_modo_velocidad.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/test_modo_velocidad && ./build/test_modo_velocidad
```
Expected: FALLA el caso nuevo. Con el código actual, `set_level` recrea el modo (objetivo_=0, sin `iniciar`), por lo que `pisar(3)` se ignora y no hay score `(2,1,0,1)`.

- [ ] **Step 3: Cambiar el `case T::SET_LEVEL` para no recrear en sesión activa**

En `firmware/lib/GameCore/GameEngine.cpp`, reemplazar el `case T::SET_LEVEL:` (líneas 57-60) por:

```cpp
        case T::SET_LEVEL:
            nivel_ = c.level;
            // Solo recrea el modo FUERA de una sesion activa. En RUNNING/PAUSED
            // el modo sigue vivo y la proxima ronda recalcula sus parametros
            // por-ronda con el nuevo nivel (corrige el bug de recrear sin iniciar).
            if (estado_ == Estado::IDLE || estado_ == Estado::FINISHED)
                crearModo(modoId_);
            break;
```

- [ ] **Step 4: Ejecutar para ver pasar**

Run:
```bash
g++ -std=c++17 -Wall -Wextra -O1 \
  -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
  firmware/test/test_modo_velocidad/test_modo_velocidad.cpp \
  firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
  -o build/test_modo_velocidad && ./build/test_modo_velocidad
```
Expected: todos los TEST_CASE (incluido el nuevo) pasan (Status: SUCCESS).

- [ ] **Step 5: Commit**

```bash
git add firmware/lib/GameCore/GameEngine.cpp firmware/test/test_modo_velocidad/
git commit -m "SP1: set_level en RUNNING no recrea el modo (fix bug latente)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Nivel dinámico por ronda (refactor de los 3 modos)

**Files:**
- Modify: `firmware/lib/GameCore/modes/ModoVelocidad.cpp:18-27`
- Modify: `firmware/lib/GameCore/modes/ModoEquilibrio.cpp:17-34`
- Modify: `firmware/lib/GameCore/modes/ModoMemoria.cpp:24-32`
- Test: `firmware/test/test_modo_velocidad/test_modo_velocidad.cpp`
- Test: `firmware/test/test_modo_equilibrio/test_modo_equilibrio.cpp`

- [ ] **Step 1: Escribir los tests que fallan (velocidad: ventana por ronda + sesión congelada)**

En `firmware/test/test_modo_velocidad/test_modo_velocidad.cpp`, añadir al final:

```cpp
TEST_CASE("velocidad: la ronda siguiente usa la ventana del nuevo nivel") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);                       // nivel 1: ventana 3000 ms
    hw.reloj = 100;
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":3})")); // ventana 1200
    hw.reloj = 200; motor.pisar(3);        // acierto ronda1 -> ronda2 con ventana(3)=1200

    size_t antes = col.eventos.size();
    hw.reloj = 200 + 1199; motor.actualizar();
    CHECK(col.eventos.size() == antes);    // aun no expira (ventana 1200)
    hw.reloj = 200 + 1200; motor.actualizar();
    CHECK(contieneScore(col.eventos, 2, 1, 1, 2));  // timeout con la ventana nueva
}

TEST_CASE("velocidad: cambiar el nivel a mitad NO cambia el numero de rondas") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);                       // nivel 1: 5 rondas; objetivos [3,4,5,3,6]
    const int obj[5] = {3, 4, 5, 3, 6};
    for (int i = 0; i < 5; ++i) {
        if (i == 1) motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":4})"));
        hw.reloj = 100 * (i + 1); motor.pisar(obj[i]);
    }
    CHECK(motor.estado() == Estado::FINISHED);  // termina en 5 rondas (nivel 1), no 12
}
```

En `firmware/test/test_modo_equilibrio/test_modo_equilibrio.cpp`, añadir al final:

```cpp
TEST_CASE("equilibrio: la ronda siguiente usa el k del nuevo nivel") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":2024})"));
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":3,"level":1})")); // k=2
    motor.procesar(Comando::parsear(R"({"cmd":"start"})"));
    // patron ronda1 (k=2) = [3,6]. Subir a nivel 2 (k=3) en RUNNING.
    hw.reloj = 100;
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":2})"));
    size_t base = col.eventos.size();
    hw.reloj = 150; motor.pisar(3);
    hw.reloj = 200; motor.pisar(6);        // completa ronda1 -> nuevoPatron ronda2 (k=3)
    int encendidos = 0;
    for (size_t i = base; i < col.eventos.size(); ++i)
        if (col.eventos[i].tipo == Evento::Tipo::LED && col.eventos[i].level == 255)
            ++encendidos;
    CHECK(encendidos == 3);                // 3 casillas = k del nivel 2
}
```

- [ ] **Step 2: Ejecutar ambos para ver el fallo (los parámetros aún vienen del constructor)**

Run:
```bash
for d in test_modo_velocidad test_modo_equilibrio; do
  g++ -std=c++17 -Wall -Wextra -O1 \
    -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
    firmware/test/$d/$d.cpp \
    firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
    -o build/$d && ./build/$d
done
```
Expected: FALLAN los dos casos *driver* — velocidad "ventana del nuevo nivel" (la ventana sigue en 3000, sin timeout a 1400) y equilibrio "k del nuevo nivel" (la ronda 2 enciende 2 LEDs, no 3). El caso "cambiar el nivel a mitad NO cambia el numero de rondas" es un *guard* y ya PASA (los `rondas_` siempre estuvieron congelados en el constructor); protege contra mover `rondas_` a por-ronda por error.

- [ ] **Step 3: Recalcular la ventana por ronda en `ModoVelocidad.cpp`**

En `firmware/lib/GameCore/modes/ModoVelocidad.cpp`, en `nuevoObjetivo(...)`, tras el bloque `if (ronda_ > rondas_) {...}` (línea 23), añadir como primera línea operativa:

```cpp
void ModoVelocidad::nuevoObjetivo(uint32_t ms) {
    if (ronda_ > rondas_) {
        fin_ = true;
        objetivo_ = 0;
        return;
    }
    ventana_ = cfg::velocidad::ventanaMs(m_.nivelActual());  // nivel dinamico por ronda
    objetivo_ = m_.rng().casilla(cfg::CELDAS);
    inicioVentana_ = ms;
    m_.led(objetivo_, cfg::LED_ENCENDIDO);
}
```

- [ ] **Step 4: Recalcular `k_` y `limite_` por ronda en `ModoEquilibrio.cpp`**

En `firmware/lib/GameCore/modes/ModoEquilibrio.cpp`, en `nuevoPatron(...)`, tras el bloque `if (ronda_ > rondas_) {...}` (línea 21), añadir:

```cpp
void ModoEquilibrio::nuevoPatron(uint32_t ms) {
    if (ronda_ > rondas_) {
        fin_ = true;
        return;
    }
    k_ = cfg::equilibrio::casillasPatron(m_.nivelActual());  // nivel dinamico por ronda
    limite_ = cfg::equilibrio::limiteMs(m_.nivelActual());
    for (int c = 0; c <= cfg::CELDAS; ++c) { enPatron_[c] = false; yaPisada_[c] = false; }
    pisadasOk_ = 0;
    int puestos = 0;
    while (puestos < k_) {
        int c = m_.rng().casilla(cfg::CELDAS);
        if (!enPatron_[c]) {
            enPatron_[c] = true;
            patron_[puestos++] = c;
        }
    }
    for (int i = 0; i < k_; ++i) m_.led(patron_[i], cfg::LED_ENCENDIDO);
    tInicio_ = ms;
}
```

- [ ] **Step 5: Recalcular `onMs_`/`gapMs_` por exhibición en `ModoMemoria.cpp`**

En `firmware/lib/GameCore/modes/ModoMemoria.cpp`, en `iniciarExhibicion(...)` (líneas 24-32), añadir como primeras líneas (la longitud de la secuencia es parámetro de SESIÓN y NO se recalcula aquí):

```cpp
void ModoMemoria::iniciarExhibicion(uint32_t ms) {
    onMs_ = cfg::memoria::exhibicionOnMs(m_.nivelActual());   // nivel dinamico por ronda
    gapMs_ = cfg::memoria::exhibicionGapMs(m_.nivelActual());
    apagarTodo();
    fase_ = Fase::EXHIBIENDO;
    idxShow_ = 0;
    ledEncendido_ = true;
    m_.led(seq_[0], cfg::LED_ENCENDIDO);
    m_.sonido(cfg::SONIDO_INSTRUCCION);
    tTrans_ = ms + static_cast<uint32_t>(onMs_);
}
```

- [ ] **Step 6: Ejecutar los tests de los modos para verlos pasar**

Run:
```bash
for d in test_modo_velocidad test_modo_equilibrio test_modo_memoria; do
  g++ -std=c++17 -Wall -Wextra -O1 \
    -I firmware/lib/GameCore -I firmware/test -I firmware/test/vendor \
    firmware/test/$d/$d.cpp \
    firmware/lib/GameCore/*.cpp firmware/lib/GameCore/modes/*.cpp \
    -o build/$d && ./build/$d
done
```
Expected: los 3 binarios pasan todos sus TEST_CASE (incluidos los nuevos de velocidad y equilibrio; memoria sin cambios de test, debe seguir verde).

- [ ] **Step 7: Verificar la suite completa (no regresión de golden ni modos)**

Run:
```bash
./scripts/run_all_tests.sh
```
Expected: TODO VERDE. Los golden `subsequence` de memoria/equilibrio siguen verdes (los parámetros de sesión no cambiaron; el comportamiento por defecto en cada nivel es idéntico al previo).

- [ ] **Step 8: Commit**

```bash
git add firmware/lib/GameCore/modes/ firmware/test/test_modo_velocidad/ firmware/test/test_modo_equilibrio/
git commit -m "SP1: nivel dinamico por ronda en los 3 modos (sesion congelada)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Golden vectors (suggest up, suggest down, set_level strict)

**Files:**
- Modify: `shared/golden_vectors.json:111-120`

> Los golden vectors son cerrojos de regresión capturados de comportamiento ya
> implementado (Tasks 5-7). Deben pasar a la primera. El `subsequence` de up/down
> ancla solo `state` + `suggest` (robusto al timing). El `strict` fija el stream
> exacto del refactor de `set_level`. El runner compara **dicts** (json.loads), así
> que el orden de claves del `expected` no importa, solo los valores.

- [ ] **Step 1: Añadir los 3 escenarios a `shared/golden_vectors.json`**

Reemplazar el final del escenario `equilibrio_juego_completo` y el cierre del arreglo (líneas 111-120):

```json
      "expected": [
        { "ev": "state", "mode": 3, "status": "running" },
        { "ev": "led", "cell": 3, "level": 255 },
        { "ev": "led", "cell": 6, "level": 255 },
        { "ev": "sound", "id": 4 },
        { "ev": "state", "mode": 3, "status": "finished" }
      ]
    }
  ]
}
```

por:

```json
      "expected": [
        { "ev": "state", "mode": 3, "status": "running" },
        { "ev": "led", "cell": 3, "level": 255 },
        { "ev": "led", "cell": 6, "level": 255 },
        { "ev": "sound", "id": 4 },
        { "ev": "state", "mode": 3, "status": "finished" }
      ]
    },
    {
      "name": "velocidad_suggest_up",
      "match": "subsequence",
      "config": { "mode": 2, "level": 1, "seed": 12345 },
      "_nota": "4 aciertos llenan la ventana (W=4); tasa 1.0 -> sugiere subir a nivel 2 (rate 100). objetivos seed 12345 = [3,4,5,3].",
      "timeline": [
        { "t": 0,    "cmd": { "cmd": "set_mode", "mode": 2, "level": 1 } },
        { "t": 0,    "cmd": { "cmd": "start" } },
        { "t": 400,  "press": 3 },
        { "t": 800,  "press": 4 },
        { "t": 1200, "press": 5 },
        { "t": 1600, "press": 3 }
      ],
      "expected": [
        { "ev": "state", "mode": 2, "status": "running" },
        { "ev": "suggest", "mode": 2, "from": 1, "level": 2, "dir": "up", "rate": 100, "window": 4 }
      ]
    },
    {
      "name": "velocidad_suggest_down",
      "match": "subsequence",
      "config": { "mode": 2, "level": 2, "seed": 12345 },
      "_nota": "4 fallos (pisar siempre la casilla 1, nunca objetivo) -> tasa 0 -> bajar a nivel 1.",
      "timeline": [
        { "t": 0,   "cmd": { "cmd": "set_mode", "mode": 2, "level": 2 } },
        { "t": 0,   "cmd": { "cmd": "start" } },
        { "t": 100, "press": 1 },
        { "t": 200, "press": 1 },
        { "t": 300, "press": 1 },
        { "t": 400, "press": 1 }
      ],
      "expected": [
        { "ev": "state", "mode": 2, "status": "running" },
        { "ev": "suggest", "mode": 2, "from": 2, "level": 1, "dir": "down", "rate": 0, "window": 4 }
      ]
    },
    {
      "name": "velocidad_set_level_strict",
      "match": "strict",
      "config": { "mode": 2, "level": 1, "seed": 12345 },
      "_nota": "set_level a nivel 3 en RUNNING: NO recrea el modo; la ronda 2 usa ventana(3)=1200 (timeout a t=1400), contadores intactos. Sin suggest (solo 2 scores < W).",
      "timeline": [
        { "t": 0,    "cmd": { "cmd": "set_mode", "mode": 2, "level": 1 } },
        { "t": 0,    "cmd": { "cmd": "start" } },
        { "t": 100,  "cmd": { "cmd": "set_level", "level": 3 } },
        { "t": 200,  "press": 3 },
        { "t": 1400 }
      ],
      "expected": [
        { "ev": "state", "mode": 2, "status": "running" },
        { "ev": "led", "cell": 3, "level": 255 },
        { "ev": "press", "cell": 3, "ms": 200 },
        { "ev": "led", "cell": 3, "level": 0 },
        { "ev": "sound", "id": 2 },
        { "ev": "score", "mode": 2, "hits": 1, "misses": 0, "rt_ms": 200, "round": 1 },
        { "ev": "led", "cell": 4, "level": 255 },
        { "ev": "led", "cell": 4, "level": 0 },
        { "ev": "sound", "id": 3 },
        { "ev": "score", "mode": 2, "hits": 1, "misses": 1, "rt_ms": 0, "round": 2 },
        { "ev": "led", "cell": 5, "level": 255 }
      ]
    }
  ]
}
```

- [ ] **Step 2: Reconstruir el `.so` y correr los golden vectors**

Run:
```bash
rm -f build/libgamecore.so
.venv/bin/python -m pytest simulator/test_golden.py -q
```
Expected: todos los escenarios (los 5 previos + los 3 nuevos) en verde.

Si `velocidad_set_level_strict` falla, capturar el stream real para reconciliar (indica un error de derivación o un bug):
```bash
.venv/bin/python -c "import sys; sys.path.insert(0,'simulator'); from golden_runner import reproducir, cargar_vectores; import json; sc=[s for s in cargar_vectores()['scenarios'] if s['name']=='velocidad_set_level_strict'][0]; print(json.dumps(reproducir(sc), indent=1))"
```
Verificar el stream contra el diseño (§4.2/§4.4 de la spec) antes de ajustar el `expected`.

- [ ] **Step 3: Commit**

```bash
git add shared/golden_vectors.json
git commit -m "SP1: golden vectors de suggest (up/down) y set_level strict

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Reconocer `suggest` en simulador y dashboard (sin UI)

**Files:**
- Modify: `simulator/tapete_sim.py:66,84-87`
- Modify: `dashboard/sesion.py:28,90-93`
- Test: `simulator/test_sim_smoke.py`
- Test: `dashboard/test_integracion.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `simulator/test_sim_smoke.py`, añadir al final:

```python
def test_suggest_no_rompe_el_sim():
    from tapete_sim import Simulador
    sim = Simulador(headless=True)
    sim.comando({"cmd": "set_seed", "seed": 12345})
    sim.comando({"cmd": "set_mode", "mode": 2, "level": 1})
    sim.comando({"cmd": "start"})
    sim._drenar()
    for obj in [3, 4, 5, 3]:                  # 4 aciertos -> suggest up
        sim.core.actualizar(); sim._drenar()
        encendida = next((c for c in range(1, 7) if sim.leds[c] > 0), None)
        sim.pisar(encendida if encendida else obj)
    sim.core.cerrar(); sim.pygame.quit()
    assert sim.ultima_sugerencia.get("dir") == "up"
    assert sim.ultima_sugerencia.get("rate") == 100
```

En `dashboard/test_integracion.py`, añadir al final:

```python
def test_suggest_up_tras_cuatro_aciertos():
    almacen = Almacen(":memory:")
    reloj = Reloj()
    fuente = FuenteCore(reloj=reloj)
    ses = Sesion(almacen, fuente)
    ses.sembrar(12345)                        # objetivos [3,4,5,3,6]
    ses.configurar(modo=2, nivel=1)
    ses.iniciar()
    for _ in range(4):                        # 4 de 5 rondas: sigue corriendo
        ses.bombear()
        encendida = next((c for c in range(1, 7) if ses.leds[c] > 0), None)
        assert encendida is not None
        reloj.avanzar(500)
        fuente.pisar(encendida)
        ses.bombear()
    assert ses.estado == "running"
    assert ses.ultima_sugerencia == {
        "ev": "suggest", "mode": 2, "from": 1, "level": 2,
        "dir": "up", "rate": 100, "window": 4,
    }
```

- [ ] **Step 2: Ejecutar para ver el fallo (no existe `ultima_sugerencia`)**

Run:
```bash
rm -f build/libgamecore.so
.venv/bin/python -m pytest simulator/test_sim_smoke.py::test_suggest_no_rompe_el_sim dashboard/test_integracion.py::test_suggest_up_tras_cuatro_aciertos -q
```
Expected: FALLAN con `AttributeError: 'Simulador'/'Sesion' object has no attribute 'ultima_sugerencia'`.

- [ ] **Step 3: Capturar `suggest` en el simulador (`tapete_sim.py`)**

En `simulator/tapete_sim.py`:

1. En `__init__`, tras `self.ultimo_score = {}` (línea 66), añadir:
```python
        self.ultima_sugerencia = {}
```

2. En `_drenar`, tras el bloque `elif t == "score": self.ultimo_score = ev` (líneas 84-85), añadir:
```python
            elif t == "suggest":
                self.ultima_sugerencia = ev
```

- [ ] **Step 4: Capturar `suggest` en el dashboard (`sesion.py`)**

En `dashboard/sesion.py`:

1. En `__init__`, tras `self._rts: list[int] = []    # tiempos de reaccion (>0) para el promedio` (línea 28), añadir:
```python
        self.ultima_sugerencia: dict = {}   # ultima recomendacion (SP1; UI en SP2)
```

2. En `_procesar`, tras el bloque `elif tipo == "state": ...` (líneas 90-93), añadir:
```python
        elif tipo == "suggest":
            self.ultima_sugerencia = ev   # se reconoce; la vista en vivo es SP2
```

- [ ] **Step 5: Ejecutar para ver pasar**

Run:
```bash
rm -f build/libgamecore.so
.venv/bin/python -m pytest simulator/test_sim_smoke.py dashboard/test_integracion.py -q
```
Expected: todos los tests pasan (incluidos los previos de smoke e integración, sin regresión).

- [ ] **Step 6: Commit**

```bash
git add simulator/tapete_sim.py dashboard/sesion.py simulator/test_sim_smoke.py dashboard/test_integracion.py
git commit -m "SP1: simulador y dashboard reconocen suggest (captura, sin UI)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Documentación del protocolo + verificación final

**Files:**
- Modify: `shared/protocol.md:55-66`

- [ ] **Step 1: Documentar `suggest` en `shared/protocol.md`**

1. En la tabla de eventos (sección 3), tras la fila de `state` (línea 55), añadir:
```
| `suggest` | `{"ev":"suggest","mode":2,"from":2,"level":3,"dir":"up","rate":75,"window":4}` | Recomendación de nivel (asistida, SP1). `from`=nivel actual, `level`=sugerido, `dir`∈`up\|down\|keep`, `rate`=acierto % (0..100) en la ventana, `window`=tamaño de ventana. Se emite solo al cambiar la dirección. |
```

2. En el bloque "Orden de claves canónico (al escribir)" (sección 3), tras `state : ev, mode, status` (línea 65), añadir:
```
suggest : ev, mode, from, level, dir, rate, window
```

- [ ] **Step 2: Verificación completa de la suite (C++ + .so + pytest)**

Run:
```bash
./scripts/run_all_tests.sh
```
Expected: **TODO VERDE** — los casos C++ doctest (incluidos `test_recomendador`, `test_adaptacion` y los añadidos a los modos/protocolo) + el build del `.so` + los pytest (golden, smoke, integración).

- [ ] **Step 3: Verificación del firmware ESP32 (compila con los cambios)**

Run:
```bash
cd firmware && pio run -e esp32dev
```
Expected: **SUCCESS** (Flash ~60%, RAM ~14%). `Recomendador.cpp` y el override `nivelActual()` compilan en el target real; `EspHardware` (implementa `IHardware`, no `IMotor`) no se ve afectado.

- [ ] **Step 4: Commit final**

```bash
git add shared/protocol.md
git commit -m "SP1: documenta el evento suggest en protocol.md

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Cierre — verificar criterios de aceptación de la spec (§6)**

Confirmar manualmente contra `docs/superpowers/specs/2026-06-04-sp1-logica-adaptable-design.md` §6:
1. `./scripts/run_all_tests.sh` → TODO VERDE. ✓ (Task 10 Step 2)
2. `pio run -e esp32dev` → SUCCESS. ✓ (Task 10 Step 3)
3. El `Recomendador` produce las sugerencias esperadas. ✓ (Task 2)
4. Los 3 golden vectors nuevos reproducen contra el `.so`. ✓ (Task 8)
5. Simulador y dashboard no se rompen con `suggest`. ✓ (Task 9)

---

## Notas de cierre

- **Pendiente para SP2 (no en este plan):** vista en vivo de la sugerencia (resaltar + botón "aplicar"), persistencia enriquecida del `suggest` en SQLite (`_log`), calibración empírica de `W`/umbrales, golden `strict` para Memoria/Equilibrio. Ver §8 de la spec.
- **Memoria — refactor sin doctest dedicado:** sus parámetros por-ronda son tiempos de exhibición (difíciles de aislar en el stream sin fragilidad). Quedan cubiertos por la no-recreación de `set_level` (Task 6) + el golden `subsequence` de memoria, que sigue verde.
- **Al terminar:** usar la skill `superpowers:finishing-a-development-branch` para decidir merge/PR.

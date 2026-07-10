# Correcciones de modos + sistema de audio — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secuencias variables por partida, pausas claras en Memoria, y 4 tonos de audio bien mapeados; dejar el bug de LEDs de Equilibrio como diagnóstico de hardware.

**Architecture:** La lógica vive solo en `firmware/lib/GameCore/` (fuente única, compilada para ESP32 y para el `.so` del simulador). La entropía de la semilla se inyecta desde el dashboard (capa externa) vía el `set_seed` ya existente. El audio se dispara desde el motor (S1/S4, transversal) y desde los modos (S2/S3). Los tonos se generan por script determinista.

**Tech Stack:** C++17 (GameCore, doctest), Python 3.12 (PyQt6 dashboard, pygame simulador, pytest), numpy + ffmpeg (audio).

## Global Constraints

- **TDD**: test primero, verlo fallar, mínimo para pasar. No avanzar con tests en rojo.
- **GameCore sin Arduino**: nada de `analogRead`/`millis()` de Arduino en `lib/GameCore/`; el tiempo entra por `ms`. Motor no bloqueante (nunca `delay()`).
- **Determinismo**: RNG xorshift32 seedable; los golden y doctests fijan `set_seed` explícito.
- **El agente NUNCA flashea ni abre el serial** (lo bloquea `guard-flash.sh`). El firmware lo prueba el humano.
- **Suite verde**: `./scripts/run_all_tests.sh` debe quedar en verde al cerrar cada tarea que toque tests.
- **MP3 para DFPlayer**: mono, 44.1 kHz, 128 kbps, en `audio/0001.mp3`..`0004.mp3`.
- **Mapa de sonidos final**: `SONIDO_INICIO=1`, `SONIDO_ACIERTO=2`, `SONIDO_RONDA=3`, `SONIDO_FIN=4`. Error mudo.
- **Regla de fin de sesión (los 3 modos)**: el evento que dispara el fin NO suena su sonido normal; el motor emite `SONIDO_FIN` al pasar a FINISHED.
- **Commits pequeños por tarea**, trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **No tocar la evidencia del artículo** (`docs/evidencia/`): es un snapshot entregado; ningún test la valida y los números no cambian.

---

### Task 1: Bug 1 — semilla aleatoria por partida (dashboard)

**Files:**
- Modify: `dashboard/app.py` (añadir `import random`, función `semilla_efectiva`, `self.semilla = None`, uso en `_start_interno`)
- Test: `dashboard/test_semilla.py` (crear)

**Interfaces:**
- Produces: `app.semilla_efectiva(preferida: int | None) -> int` — devuelve `preferida` si no es None; si no, un entero aleatorio en `[1, 0xFFFFFFFF]`.

- [ ] **Step 1: Write the failing test**

```python
# dashboard/test_semilla.py
"""La semilla de cada partida es aleatoria salvo que se fije (smoke/tests)."""
from app import semilla_efectiva


def test_respeta_la_semilla_fijada():
    assert semilla_efectiva(12345) == 12345


def test_none_da_semilla_aleatoria_no_nula_en_rango():
    vals = {semilla_efectiva(None) for _ in range(64)}
    assert len(vals) > 1                                  # varía entre partidas
    assert all(1 <= v <= 0xFFFFFFFF for v in vals)        # rango xorshift válido (!=0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest dashboard/test_semilla.py -q`
Expected: FAIL con `ImportError: cannot import name 'semilla_efectiva'`

- [ ] **Step 3: Implement**

En `dashboard/app.py`, añadir cerca de los imports (`import random` arriba) y a nivel de módulo (junto a `SEMILLA_DEFECTO`):

```python
def semilla_efectiva(preferida):
    """Semilla de la partida: la fijada (smoke/tests reproducibles) o, si no se
    fijó, una aleatoria no nula por partida — cada juego, una secuencia distinta."""
    return preferida if preferida is not None else random.randint(1, 0xFFFFFFFF)
```

Cambiar la línea 234 `self.semilla = SEMILLA_DEFECTO` → `self.semilla = None` y en `_start_interno` (línea 392) `self.ses.sembrar(self.semilla)` → `self.ses.sembrar(semilla_efectiva(self.semilla))`. Eliminar `SEMILLA_DEFECTO` (línea 34) si queda sin uso (el smoke en `main` ya fija `v.semilla = 12345` explícito).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest dashboard/test_semilla.py dashboard/test_app_smoke.py dashboard/test_integracion.py -q`
Expected: PASS (el smoke sigue determinista porque fija `v.semilla=12345`).

- [ ] **Step 5: Commit**

```bash
git add dashboard/app.py dashboard/test_semilla.py
git commit -m "fix(dashboard): semilla aleatoria por partida (secuencias distintas)"
```

---

### Task 2: Bug 1 — tecla R de re-siembra en el simulador

**Files:**
- Modify: `simulator/tapete_sim.py` (`import random`, método `resembrar`, tecla `K_r`)
- Test: `simulator/test_sim_smoke.py` (añadir un caso)

**Interfaces:**
- Produces: `Simulador.resembrar()` — envía `set_seed` con semilla aleatoria no nula al core.

- [ ] **Step 1: Write the failing test** (añadir a `simulator/test_sim_smoke.py`)

```python
def test_resembrar_no_falla_headless():
    from tapete_sim import Simulador
    sim = Simulador(headless=True)
    sim.resembrar()          # no debe lanzar; envía set_seed al core
    sim.comando({"cmd": "set_mode", "mode": 1, "level": 1})
    sim.comando({"cmd": "start"})
    assert sim.estado == "running"
    sim.core.cerrar()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest simulator/test_sim_smoke.py::test_resembrar_no_falla_headless -q`
Expected: FAIL con `AttributeError: 'Simulador' object has no attribute 'resembrar'`

- [ ] **Step 3: Implement**

En `simulator/tapete_sim.py`: `import random` arriba. Añadir método:

```python
    def resembrar(self):
        """Re-siembra el RNG del core con una semilla aleatoria (tecla R)."""
        self.comando({"cmd": "set_seed", "seed": random.randint(1, 0xFFFFFFFF)})
```

En `procesar_teclado`, añadir rama:

```python
        elif ev.key == pg.K_r:
            self.resembrar()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest simulator/test_sim_smoke.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add simulator/tapete_sim.py simulator/test_sim_smoke.py
git commit -m "feat(sim): tecla R re-siembra el RNG (cierra desfase doc/codigo)"
```

---

### Task 3: Config.h — constantes de sonido nuevas + pausa de Memoria

**Files:**
- Modify: `firmware/lib/GameCore/Config.h`

**Interfaces:**
- Produces: `cfg::SONIDO_INICIO=1`, `cfg::SONIDO_ACIERTO=2`, `cfg::SONIDO_RONDA=3`, `cfg::SONIDO_FIN=4`; `cfg::memoria::pausaMs(int nivel) -> 1200`.

Nota: se **añaden** las nuevas y se conservan temporalmente las viejas (`SONIDO_INSTRUCCION/ERROR/EXITO`, mismos valores) para no romper la compilación; se eliminan en la Task 8, tras migrar todos los consumidores.

- [ ] **Step 1: Edit `Config.h`** — bloque de sonidos:

```cpp
// --- Sonidos (archivos 000X.mp3 en el DFPlayer) -----------------------------
constexpr int SONIDO_INICIO  = 1;  // aviso de inicio de sesion (START)
constexpr int SONIDO_ACIERTO = 2;  // pisada correcta / cada LED de la exhibicion
constexpr int SONIDO_RONDA   = 3;  // serie/patron completado (pase de ronda)
constexpr int SONIDO_FIN     = 4;  // fin de sesion (FINISHED)
// Alias transitorios (se eliminan en la Task 8, tras migrar los modos/tests):
constexpr int SONIDO_INSTRUCCION = 1;
constexpr int SONIDO_ERROR       = 3;
constexpr int SONIDO_EXITO       = 4;
```

En `namespace memoria`, añadir tras `exhibicionGapMs`:

```cpp
// Pausa clara entre fases (inicio, entre rondas, tras error) para una experiencia
// amigable: da tiempo a ver el primer LED. No bloqueante (via actualizar()).
inline int pausaMs(int nivel) { (void)nivel; return 1200; }
```

- [ ] **Step 2: Verify it compiles** (los tests actuales aún usan los alias)

Run: `./scripts/run_all_tests.sh`
Expected: TODO VERDE (nada cambió de comportamiento todavía).

- [ ] **Step 3: Commit**

```bash
git add firmware/lib/GameCore/Config.h
git commit -m "feat(core): constantes de sonido (inicio/acierto/ronda/fin) + pausa de memoria"
```

---

### Task 4: GameEngine — S1 al START, S4 al FINISHED

**Files:**
- Modify: `firmware/lib/GameCore/GameEngine.cpp` (`procesar` caso START; `revisarFin`)
- Test: `firmware/test/test_core/test_gameengine.cpp` (añadir casos)

**Interfaces:**
- Consumes: `cfg::SONIDO_INICIO`, `cfg::SONIDO_FIN` (Task 3).

- [ ] **Step 1: Write the failing tests** (añadir a `test_gameengine.cpp`)

```cpp
TEST_CASE("el motor suena INICIO al arrancar la sesion") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"start"})"));
    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_INICIO)));
}

TEST_CASE("el motor suena FIN al terminar la sesion") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":12345})"));
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"start"})"));
    const int obj[5] = {3, 4, 5, 3, 6};                 // seed 12345, nivel 1 = 5 rondas
    for (int i = 0; i < 5; ++i) { hw.reloj = 100 * (i + 1); motor.pisar(obj[i]); }
    REQUIRE(motor.estado() == Estado::FINISHED);
    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_FIN)));
}
```

- [ ] **Step 2: Run to verify they fail**

Run: `./scripts/run_all_tests.sh` (o compilar solo `test_core`)
Expected: FAIL (no se emite SONIDO_INICIO/FIN todavía).

- [ ] **Step 3: Implement** en `GameEngine.cpp`

En `procesar`, caso `T::START`, tras `cambiarEstado(Estado::RUNNING);` y ANTES de `modo_->iniciar(0);`:

```cpp
                sonido(cfg::SONIDO_INICIO);
```

En `revisarFin`, tras `cambiarEstado(Estado::FINISHED);` y ANTES de `apagarTodos();`:

```cpp
        sonido(cfg::SONIDO_FIN);
```

- [ ] **Step 4: Run to verify pass**

Run: `./scripts/run_all_tests.sh`
Expected: `test_core` PASS. Otros modos aún usan alias → siguen verdes.

- [ ] **Step 5: Commit**

```bash
git add firmware/lib/GameCore/GameEngine.cpp firmware/test/test_core/test_gameengine.cpp
git commit -m "feat(core): suena INICIO al START y FIN al FINISHED (transversal)"
```

---

### Task 5: ModoVelocidad — S2 en acierto, sin sonido de error

**Files:**
- Modify: `firmware/lib/GameCore/modes/ModoVelocidad.cpp`
- Test: `firmware/test/test_modo_velocidad/test_modo_velocidad.cpp`

- [ ] **Step 1: Update the tests** (reflejan el nuevo audio; escríbelos antes de tocar el modo)

En `test_modo_velocidad.cpp`, sustituir las aserciones de sonido:
- El caso "pisar la casilla equivocada es un error" (líneas 51-61): **quitar** cualquier expectativa de sonido de error (no la hay hoy explícita, pero añadir): `CHECK(!contiene(col.eventos, Evento::sound(cfg::SONIDO_ERROR)));` → tras la Task 8 `SONIDO_ERROR` desaparece; usar en su lugar un aserto por id: `CHECK(cuenta(col.eventos, Evento::Tipo::SOUND) == 1);` (solo el INICIO del start; el error no suena).
- Añadir un caso nuevo:

```cpp
TEST_CASE("velocidad: cada acierto suena ACIERTO; el error no suena") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);                       // seed 12345, objetivo ronda1 = 3
    hw.reloj = 300; motor.pisar(3);        // acierto
    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_ACIERTO)));
    hw.reloj = 600; motor.pisar(1);        // error (objetivo era 4)
    // No hay sonido de error: el unico ACIERTO es el de la ronda 1.
    CHECK(cuenta(col.eventos, Evento::Tipo::SOUND) == 2);  // INICIO + 1 ACIERTO
}
```

- [ ] **Step 2: Run to verify it fails**

Run: `./scripts/run_all_tests.sh`
Expected: FAIL (hoy `fallar()` suena `SONIDO_ERROR`).

- [ ] **Step 3: Implement** en `ModoVelocidad.cpp`

En `fallar`, eliminar la línea `m_.sonido(cfg::SONIDO_ERROR);`.

En `pisar` (rama acierto), reordenar para no sonar en la ronda final:

```cpp
    if (celda == objetivo_) {
        int rt = static_cast<int>(ms - inicioVentana_);
        hits_++;
        m_.led(objetivo_, cfg::LED_APAGADO);
        m_.score(hits_, misses_, rt, ronda_);
        ronda_++;
        if (ronda_ <= rondas_) m_.sonido(cfg::SONIDO_ACIERTO);  // no suena en la ronda final (suena FIN)
        nuevoObjetivo(ms);
    } else {
        fallar(ms);
    }
```

- [ ] **Step 4: Run to verify pass**

Run: `./scripts/run_all_tests.sh`
Expected: `test_modo_velocidad` PASS.

- [ ] **Step 5: Commit**

```bash
git add firmware/lib/GameCore/modes/ModoVelocidad.cpp firmware/test/test_modo_velocidad/test_modo_velocidad.cpp
git commit -m "feat(velocidad): ACIERTO por pisada correcta, error mudo"
```

---

### Task 6: ModoEquilibrio — S2 parcial, S3 al completar, sin error

**Files:**
- Modify: `firmware/lib/GameCore/modes/ModoEquilibrio.cpp`
- Test: `firmware/test/test_modo_equilibrio/test_modo_equilibrio.cpp`

- [ ] **Step 1: Update the tests**

En `test_modo_equilibrio.cpp`:
- Caso "completar el patron es acierto..." (líneas 24-36): `Evento::sound(cfg::SONIDO_EXITO)` → `Evento::sound(cfg::SONIDO_RONDA)`.
- Caso "pisar fuera del patron es error" (38-47): `CHECK(contiene(..., Evento::sound(cfg::SONIDO_ERROR)))` → `CHECK(cuenta(col.eventos, Evento::Tipo::SOUND) == 1);` (solo INICIO; el error no suena).
- Caso "agotar el tiempo limite es error" (49-58): igual, quitar el `sound(SONIDO_ERROR)`; el timeout no suena: `CHECK(cuenta(col.eventos, Evento::Tipo::SOUND) == 1);`.
- Añadir:

```cpp
TEST_CASE("equilibrio: cada casilla parcial suena ACIERTO; completar suena RONDA") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);                          // patron ronda1 = [3,6]
    hw.reloj = 500; motor.pisar(3);           // parcial
    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_ACIERTO)));
    hw.reloj = 900; motor.pisar(6);           // completa
    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_RONDA)));
}
```

- [ ] **Step 2: Run to verify it fails**

Run: `./scripts/run_all_tests.sh`
Expected: FAIL.

- [ ] **Step 3: Implement** en `ModoEquilibrio.cpp`

En `fallar`, eliminar `m_.sonido(cfg::SONIDO_ERROR);`.

Reescribir `pisar` (rama acierto parcial y compleción):

```cpp
void ModoEquilibrio::pisar(int celda, uint32_t ms) {
    if (fin_) return;
    if (celda >= 1 && celda <= cfg::CELDAS && enPatron_[celda]) {
        if (!yaPisada_[celda]) {
            yaPisada_[celda] = true;
            pisadasOk_++;
            if (pisadasOk_ >= k_) {
                // Patron completo.
                hits_++;
                m_.score(hits_, misses_, static_cast<int>(ms - tInicio_), ronda_);
                apagarPatron();
                ronda_++;
                if (ronda_ > rondas_) { fin_ = true; return; }   // fin: suena FIN (motor)
                m_.sonido(cfg::SONIDO_RONDA);
                nuevoPatron(ms);
            } else {
                m_.sonido(cfg::SONIDO_ACIERTO);                   // acierto parcial
            }
        }
    } else {
        fallar(ms);  // pisada fuera del patron (mudo)
    }
}
```

Nota: `nuevoPatron` conserva su guarda `if (ronda_ > rondas_) { fin_ = true; return; }` (defensa; ya no se alcanza desde `pisar`, pero sí desde `fallar`).

- [ ] **Step 4: Run to verify pass**

Run: `./scripts/run_all_tests.sh`
Expected: `test_modo_equilibrio` PASS.

- [ ] **Step 5: Commit**

```bash
git add firmware/lib/GameCore/modes/ModoEquilibrio.cpp firmware/test/test_modo_equilibrio/test_modo_equilibrio.cpp
git commit -m "feat(equilibrio): ACIERTO por casilla, RONDA al completar, error mudo"
```

---

### Task 7: ModoMemoria — fase PAUSA + audio (exhibición/confirmación S2, S3, sin error)

**Files:**
- Modify: `firmware/lib/GameCore/modes/ModoMemoria.h` (enum `Fase` + `iniciarPausa`)
- Modify: `firmware/lib/GameCore/modes/ModoMemoria.cpp`
- Test: `firmware/test/test_modo_memoria/test_modo_memoria.cpp`

**Interfaces:**
- Consumes: `cfg::memoria::pausaMs`, `cfg::SONIDO_ACIERTO`, `cfg::SONIDO_RONDA` (Tasks 3).

- [ ] **Step 1: Update/extend the tests**

En `test_modo_memoria.cpp`:
- `terminarExhibicion` avanza `+10000`, que ya absorbe la pausa (1,2 s) + exhibición. No cambia.
- Caso "exhibe la secuencia inicial": la aserción `cuenta(SOUND) >= 2` sigue válida (2 LEDs de exhibición × S2). Mantener.
- Caso "repetir la secuencia correcta sube la longitud": `Evento::sound(cfg::SONIDO_EXITO)` → `Evento::sound(cfg::SONIDO_RONDA)`.
- Caso "pisar mal cuenta error y repite": `CHECK(contiene(..., Evento::sound(cfg::SONIDO_ERROR)))` → **quitar** (error mudo). Mantener el `contieneScore(...misses 1...)` y `estado()==RUNNING`.
- Añadir dos casos:

```cpp
TEST_CASE("memoria: hay pausa entre completar y re-exhibir (no instantaneo)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);
    hw.reloj += 300; motor.pisar(4);
    hw.reloj += 300; motor.pisar(5);           // completa [4,5]
    size_t tras_completar = col.eventos.size();
    // Sin avanzar el reloj, la nueva exhibicion NO arranca (esta en PAUSA).
    motor.actualizar();
    CHECK(col.eventos.size() == tras_completar);          // nada aun: pausa
    // Avanzada la pausa, arranca la exhibicion (aparece el LED de la nueva casilla 2).
    hw.reloj += cfg::memoria::pausaMs(1) + 1; motor.actualizar();
    CHECK(contiene(col.eventos, Evento::led(2, 255)));
}

TEST_CASE("memoria: la pisada correcta intermedia suena ACIERTO") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);
    size_t base = col.eventos.size();
    hw.reloj += 300; motor.pisar(4);           // primer paso de [4,5]: acierto intermedio
    CHECK(contiene({col.eventos.begin() + base, col.eventos.end()},
                   Evento::sound(cfg::SONIDO_ACIERTO)));
}
```

Nota: si `contiene` no acepta un sub-rango por iteradores, reemplazar por un bucle inline que recorra `col.eventos` desde `base`.

- [ ] **Step 2: Run to verify they fail**

Run: `./scripts/run_all_tests.sh`
Expected: FAIL (no hay fase PAUSA ni S3; hoy re-exhibe instantáneo y suena EXITO).

- [ ] **Step 3: Implement — `ModoMemoria.h`**

Cambiar el enum y declarar el helper:

```cpp
    enum class Fase { PAUSA, EXHIBIENDO, ENTRADA };
    ...
    void iniciarPausa(uint32_t ms);   // pausa clara antes de (re)exhibir
```

Cambiar el valor inicial de `fase_`:

```cpp
    Fase fase_ = Fase::PAUSA;
```

- [ ] **Step 4: Implement — `ModoMemoria.cpp`**

`iniciar` arranca con pausa (deja ver el sonido de inicio antes de exhibir):

```cpp
void ModoMemoria::iniciar(uint32_t ms) {
    hits_ = 0;
    misses_ = 0;
    fin_ = false;
    iniciarPausa(ms);
}

void ModoMemoria::iniciarPausa(uint32_t ms) {
    apagarTodo();
    fase_ = Fase::PAUSA;
    tTrans_ = ms + static_cast<uint32_t>(cfg::memoria::pausaMs(m_.nivelActual()));
}
```

`iniciarExhibicion`: el primer LED lleva S2 (antes INSTRUCCION); el resto igual:

```cpp
    m_.led(seq_[0], cfg::LED_ENCENDIDO);
    m_.sonido(cfg::SONIDO_ACIERTO);
```

`actualizar`: manejar PAUSA y quitar el sonido viejo del bucle:

```cpp
void ModoMemoria::actualizar(uint32_t ms) {
    if (fin_) return;
    if (fase_ == Fase::PAUSA) {
        if (ms >= tTrans_) iniciarExhibicion(ms);
        return;
    }
    if (fase_ != Fase::EXHIBIENDO) return;
    while (fase_ == Fase::EXHIBIENDO && ms >= tTrans_) {
        if (ledEncendido_) {
            m_.led(seq_[idxShow_], cfg::LED_APAGADO);
            ledEncendido_ = false;
            ++idxShow_;
            if (idxShow_ >= len_) { iniciarEntrada(tTrans_); return; }
            tTrans_ += static_cast<uint32_t>(gapMs_);
        } else {
            m_.led(seq_[idxShow_], cfg::LED_ENCENDIDO);
            m_.sonido(cfg::SONIDO_ACIERTO);          // tono por LED de la exhibicion
            ledEncendido_ = true;
            tTrans_ += static_cast<uint32_t>(onMs_);
        }
    }
}
```

`pisar`: S2 en acierto intermedio, S3 al completar (o fin), pausa tras completar y tras error, error mudo:

```cpp
void ModoMemoria::pisar(int celda, uint32_t ms) {
    if (fin_ || fase_ != Fase::ENTRADA) return;

    if (celda == seq_[inputIndex_]) {
        m_.led(celda, cfg::LED_ENCENDIDO);
        tUltimaPisada_ = ms;
        ++inputIndex_;
        if (inputIndex_ >= len_) {
            // Secuencia completa.
            ++hits_;
            m_.score(hits_, misses_, static_cast<int>(ms - tInicioInput_), len_);
            if (len_ >= longitudMax_) { fin_ = true; return; }   // fin: suena FIN (motor)
            m_.sonido(cfg::SONIDO_RONDA);
            crecer();
            iniciarPausa(ms);
        } else {
            m_.sonido(cfg::SONIDO_ACIERTO);                       // acierto intermedio
        }
    } else {
        // Pisada incorrecta: error mudo; pausa y se repite la MISMA secuencia.
        ++misses_;
        m_.score(hits_, misses_, 0, len_);
        iniciarPausa(ms);
    }
}
```

- [ ] **Step 5: Run to verify pass**

Run: `./scripts/run_all_tests.sh`
Expected: `test_modo_memoria` PASS (los golden Python pueden fallar aún → Task 10).

- [ ] **Step 6: Commit**

```bash
git add firmware/lib/GameCore/modes/ModoMemoria.h firmware/lib/GameCore/modes/ModoMemoria.cpp firmware/test/test_modo_memoria/test_modo_memoria.cpp
git commit -m "feat(memoria): fase PAUSA (~1.2s) + audio por LED/acierto/ronda, error mudo"
```

---

### Task 8: Limpieza — eliminar alias de sonido viejos

**Files:**
- Modify: `firmware/lib/GameCore/Config.h`

- [ ] **Step 1: Grep para confirmar que no quedan usos**

Run: `grep -rn "SONIDO_INSTRUCCION\|SONIDO_ERROR\|SONIDO_EXITO" firmware/`
Expected: sin coincidencias (todo migrado en Tasks 4-7).

- [ ] **Step 2: Eliminar los alias transitorios de `Config.h`** (las 3 líneas `constexpr int SONIDO_INSTRUCCION/ERROR/EXITO`).

- [ ] **Step 3: Run full suite**

Run: `./scripts/run_all_tests.sh`
Expected: C++ verde; Python puede fallar en golden (Task 10) y jugador_modos (Task 9).

- [ ] **Step 4: Commit**

```bash
git add firmware/lib/GameCore/Config.h
git commit -m "refactor(core): eliminar alias de sonido viejos (mapa final inicio/acierto/ronda/fin)"
```

---

### Task 9: Adaptar `jugador_modos.py` (detección de exhibición por fase)

**Files:**
- Modify: `simulator/jugador_modos.py`
- Test: `simulator/test_jugador_modos.py` (debe seguir verde; los valores no cambian)

**Interfaces:**
- Consumes: el nuevo audio (exhibición y confirmación suenan `SONIDO_ACIERTO=2`).

Contexto: hoy el jugador construye `secuencia` con `sound id==1` durante la exhibición y confía en que la confirmación de pisada no suena. Ahora ambas suenan S2. Solución robusta: construir la secuencia por **fase** — un `led`>0 recibido mientras el jugador aún no está en modo `entrada` es un paso de la exhibición.

- [ ] **Step 1: Run the existing tests to see them fail with the new core**

Run: `./scripts/run_all_tests.sh` (o `.venv/bin/python -m pytest simulator/test_jugador_modos.py -q`)
Expected: FAIL en los casos de Memoria (el jugador ya no arma la secuencia).

- [ ] **Step 2: Rewrite the Memoria player's event drain** en `jugador_modos.py`

Reemplazar el bloque `drenar` de `jugar_memoria` para no depender del sonido:

```python
    def drenar(t: int) -> None:
        nonlocal entrada, idx, t_ultimo_led, finished, secuencia
        for linea in b.drenar_eventos():
            e = json.loads(linea)
            ev = e.get("ev")
            if ev == "led":
                t_ultimo_led = t
                if e["level"] > 0:
                    encendidas.add(e["cell"])
                    if not entrada:
                        secuencia.append(e["cell"])   # LED de exhibicion (aun no se pisa)
                else:
                    encendidas.discard(e["cell"])
            elif ev == "score":
                scores.append(e)
                secuencia = []       # el motor reexhibe: acierto (crece) o error (repite)
                entrada = False
                idx = 0
            elif ev == "suggest":
                suggests.append(e)
            elif ev == "state" and e.get("status") == "finished":
                finished = True
```

Eliminar la variable `pendiente` (ya no se usa) de la firma `nonlocal` y de su declaración arriba (`pendiente: int | None = None`). Eliminar la constante `SONIDO_INSTRUCCION` y su comentario. La condición de fin de exhibición (`SILENCIO_FIN_EXHIBICION_MS`) sigue igual: cuando hay `secuencia`, nada encendido y silencio ≥300 ms tras el último LED, pasa a `entrada=True`.

Nota sobre la pausa: durante la pausa inicial/entre rondas todo está apagado y `secuencia` está vacía → la guarda `secuencia and not encendidas` no dispara `entrada`; correcto. `max_t=120000` absorbe las pausas de 1,2 s.

- [ ] **Step 3: Run tests to verify pass**

Run: `.venv/bin/python -m pytest simulator/test_jugador_modos.py simulator/test_montecarlo.py simulator/test_evidencia_modos.py -q`
Expected: PASS (mismos hits/misses: la lógica de aciertos no cambió).

- [ ] **Step 4: Commit**

```bash
git add simulator/jugador_modos.py
git commit -m "fix(sim): jugador de memoria detecta la exhibicion por fase, no por sonido"
```

---

### Task 10: Regenerar `shared/golden_vectors.json`

**Files:**
- Modify: `shared/golden_vectors.json`
- Test: `simulator/test_golden.py` (verde tras regenerar)

Cambios de `sound` por el nuevo mapeo (validación por subsecuencia; `SONIDO_INICIO=1` al start no rompe subsecuencias que no lo mencionan):
- `velocidad_strict_dos_aciertos` (match strict): el stream ahora incluye `{"ev":"sound","id":1}` tras `state running`, y los `sound id:2` de acierto se mantienen. Regenerar el `expected` completo del stream real.
- `velocidad_set_level_strict` (match strict): `{"ev":"sound","id":3}` (error) desaparece; añadir `sound id:1` al inicio. Regenerar el stream real.
- `memoria_juego_completo`: `{"ev":"sound","id":4}` (completar 1ª serie) → `{"ev":"sound","id":3}`; el `state finished` final va acompañado de `sound id:4`. Ajustar el `expected` (subsecuencia).
- `equilibrio_juego_completo`: `{"ev":"sound","id":4}` (completar 1er patrón) → `{"ev":"sound","id":3}`.

- [ ] **Step 1: Generate the real streams** con un script de apoyo temporal:

```bash
.venv/bin/python - <<'PY'
import json, sys, os
sys.path.insert(0, "simulator")
from golden_runner import reproducir, cargar_vectores
d = cargar_vectores()
for esc in d["scenarios"]:
    emit = reproducir(esc)
    print("===", esc["name"], "(match:", esc["match"], ")")
    for e in emit: print("  ", json.dumps(e, ensure_ascii=False))
PY
```

- [ ] **Step 2: Update `expected`** para cada escenario:
  - Escenarios `strict`: copiar el stream emitido **completo** (tal cual lo imprimió el paso 1) al `expected`.
  - Escenarios `subsequence`: ajustar solo los ids de `sound` cambiados; conservar el estilo de subsecuencia curada (eventos clave, en orden). Para memoria/equilibrio, verificar que el `sound id` del "completar" es 3 y que el fin lleva `sound id` 4.

- [ ] **Step 3: Run the golden tests**

Run: `.venv/bin/python -m pytest simulator/test_golden.py -q`
Expected: PASS (los 8 escenarios reproducen exactamente/como subsecuencia).

- [ ] **Step 4: Full suite green**

Run: `./scripts/run_all_tests.sh`
Expected: TODO VERDE.

- [ ] **Step 5: Commit**

```bash
git add shared/golden_vectors.json
git commit -m "test(golden): regenerar vectores con el nuevo mapa de sonidos"
```

---

### Task 11: Generar los 4 tonos MP3

**Files:**
- Create: `scripts/gen_audio.py`
- Create: `audio/0001.mp3`..`audio/0004.mp3`
- Modify: `audio/README.md`

**Interfaces:**
- Produces: 4 MP3 mono 44.1 kHz 128 kbps: 1=inicio (arpegio asc.), 2=acierto (tono corto), 3=ronda (melodía de logro), 4=fin (fanfarria).

- [ ] **Step 1: Write `scripts/gen_audio.py`**

```python
"""Genera los 4 tonos del Tapete (audio/000X.mp3) de forma determinista.

numpy sintetiza ondas -> WAV temporal -> ffmpeg a MP3 mono 44.1k/128k (perfil que
el DFPlayer Mini reproduce con fiabilidad). Los mismos archivos sirven al simulador
(audio/) y a la microSD del ESP32 (/mp3/).
"""
import os
import struct
import subprocess
import wave

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(RAIZ, "audio")
SR = 44100


def _tono(freqs, dur, vol=0.6, fade=0.01):
    """Suma de senos (acorde/nota) de duracion dur (s) con fade in/out anti-click."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    onda = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    n = int(SR * fade)
    env = np.ones_like(onda)
    env[:n] = np.linspace(0, 1, n)
    env[-n:] = np.linspace(1, 0, n)
    return onda * env * vol


def _secuencia(notas):
    """notas = [(freqs, dur), ...] concatenadas."""
    return np.concatenate([_tono(f, d) for f, d in notas])


# Escala alegre (Do mayor) para sonidos amables.
DO, MI, SOL, DO2, SOL2 = 523.25, 659.25, 783.99, 1046.5, 1568.0

SONIDOS = {
    1: _secuencia([([DO], .12), ([MI], .12), ([SOL], .12), ([DO2], .18)]),      # inicio: arpegio asc.
    2: _tono([SOL2], .12),                                                       # acierto: tono corto claro
    3: _secuencia([([MI], .10), ([SOL], .10), ([DO2], .22)]),                    # ronda: pequeño logro
    4: _secuencia([([DO2], .14), ([SOL], .14), ([DO2], .14), ([MI, SOL, DO2], .35)]),  # fin: fanfarria
}


def _escribir_wav(path, onda):
    data = (np.clip(onda, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    os.makedirs(AUDIO, exist_ok=True)
    for sid, onda in SONIDOS.items():
        wav = os.path.join(AUDIO, f"{sid:04d}.wav")
        mp3 = os.path.join(AUDIO, f"{sid:04d}.mp3")
        _escribir_wav(wav, onda)
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-ac", "1", "-ar", "44100",
                        "-b:a", "128k", mp3], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(wav)
        print(f"audio/{sid:04d}.mp3 ({os.path.getsize(mp3)} bytes)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the assets**

Run: `.venv/bin/python scripts/gen_audio.py`
Expected: imprime 4 rutas; `audio/0001.mp3`..`0004.mp3` existen y pesan > 0.

- [ ] **Step 3: Verify with the simulator** (headless: comprueba que carga sin error)

Run: `.venv/bin/python -c "import pygame; pygame.mixer.init(); [pygame.mixer.Sound(f'audio/{i:04d}.mp3') for i in range(1,5)]; print('4 MP3 OK')"`
Expected: `4 MP3 OK` (si no hay dispositivo de audio, saltar; el sim los ignora sin fallar).

- [ ] **Step 4: Update `audio/README.md`** — tabla nueva:

```markdown
| Archivo | id | Cuándo suena |
|---|---|---|
| `0001.mp3` | 1 | Inicio de sesión (Start) |
| `0002.mp3` | 2 | Pisada correcta / cada LED de la exhibición (Memoria) |
| `0003.mp3` | 3 | Serie/patrón completado (pase de ronda) |
| `0004.mp3` | 4 | Fin de la sesión |

Se generan con `scripts/gen_audio.py` (numpy → ffmpeg, MP3 mono 44.1k/128k).
El error no lleva sonido.
```

- [ ] **Step 5: Commit**

```bash
git add scripts/gen_audio.py audio/0001.mp3 audio/0002.mp3 audio/0003.mp3 audio/0004.mp3 audio/README.md
git commit -m "feat(audio): generador determinista + 4 tonos (inicio/acierto/ronda/fin)"
```

---

### Task 12: Bug 3 — checklist de diagnóstico eléctrico de Equilibrio (no código)

**Files:**
- Create: `docs/hardware/diagnostico-leds-equilibrio.md`

Confirmado por evidencia: GameCore emite exactamente `k` LEDs por patrón (repro headless) y la pantalla del dashboard los muestra bien; el tapete enciende de más → causa **eléctrica**. El agente no flashea ni mide: se entrega un procedimiento para el autor.

- [ ] **Step 1: Write the checklist** con estos pasos (multímetro + `esp32dev` normal):
  1. Con un patrón fijo encendido (p. ej. Equilibrio n1 → 2 casillas), anotar qué celdas marca la **pantalla** y qué LEDs físicos encienden. Listar los "de más".
  2. Medir tensión en el ánodo/cátodo de cada LED del grupo que enciende de más; comparar con los del patrón. Un LED que enciende sin señal de su GPIO indica **retorno de tierra compartido** (ghosting) o un canal del driver puenteado.
  3. Verificar el cableado LED↔celda contra `firmware/lib/GameCore/Config.h` (`PIN_LED = {4,5,18,19,21,23}`) y `docs/hardware/cableado.md`: confirmar continuidad GPIO→driver→LED de cada celda por separado.
  4. Con solo un LED encendido a la vez (Velocidad/Memoria), confirmar que no hay ghosting; si aparece solo con varios simultáneos (Equilibrio), sospechar **caída de tensión/alimentación** compartida del riel de LEDs.
  5. Regla: si un pin del mapa resulta mal cableado, se corrige el **cableado** para casar con `Config.h` (fuente de verdad de pines); no se “inventa” un pin.

- [ ] **Step 2: Commit**

```bash
git add docs/hardware/diagnostico-leds-equilibrio.md
git commit -m "docs(hardware): checklist de diagnostico del ghosting de LEDs en Equilibrio"
```

---

## Self-Review

- **Spec coverage:** Frente 1 → Tasks 1-2; Frente 2 → Tasks 3,7; Frente 4 (audio) → Tasks 3-7,9,11; Frente 3 → Task 12; impacto suite → Tasks 8-10. Cubierto.
- **Orden y verdes intermedios:** Config coexiste con alias (Task 3) hasta migrar todos los consumidores; se limpian en Task 8. El C++ queda verde tras Task 8; el Python (golden/jugador) tras Tasks 9-10.
- **Tipos/nombres:** `SONIDO_INICIO/ACIERTO/RONDA/FIN`, `memoria::pausaMs`, `Fase::{PAUSA,EXHIBIENDO,ENTRADA}`, `iniciarPausa`, `semilla_efectiva`, `Simulador.resembrar` — consistentes entre tareas.
- **Riesgo:** la regeneración de golden `strict` requiere copiar el stream real (Task 10, paso 1). Verificar tras Task 8 (core estable) para no regenerar dos veces.
- **Evidencia del artículo:** intacta por diseño (ningún test la valida; números sin cambio).

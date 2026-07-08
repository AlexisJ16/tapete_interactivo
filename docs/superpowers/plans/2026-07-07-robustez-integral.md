# Robustez Integral del Software — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. La **Fase 1 (crash) usa superpowers:systematic-debugging**; toda tarea de código usa **superpowers:test-driven-development**.

**Goal:** Que ningún dato inesperado, uso intensivo ni fallo de E/S pueda tumbar el dashboard ni colgar el firmware, demostrado con tests deterministas — y cerrar el crash reportado con una regresión.

**Architecture:** Endurecer boundaries (validar al entrar, confiar dentro) sobre la base ya existente (FuenteTCP reconecta, parseo no-JSON tolerado). Añadir una red de seguridad global en la GUI (excepción→log, no propaga) y generadores de caos deterministas (monkey de GUI + fuzz de protocolo Py/C++) a la suite y CI.

**Tech Stack:** Python 3.12 + PyQt6 + matplotlib + pyserial (dashboard/simulator); C++17 + doctest + g++ (GameCore/firmware). pytest. CI GitHub Actions.

## Global Constraints

- **venv obligatorio** (PEP 668): correr Python con `.venv/bin/python` / `.venv/bin/pytest`. Nunca el pip del sistema.
- **Tests C++ con g++ + doctest** vía `./scripts/run_all_tests.sh` (sin PlatformIO). GameCore permanece **sin Arduino** (nada de `analogRead`/`millis()` de Arduino en `lib/GameCore/`).
- **Determinismo:** todo generador de caos usa una `seed` fija y explícita (reproducible).
- **TDD:** cada cambio nace de un test que falla antes y pasa después. Al cerrar cada tarea, `./scripts/run_all_tests.sh` queda **verde**.
- **Sin secretos** en código/commits. Commits pequeños con trailer `Co-Authored-By: Claude...`.
- **Andamiaje:** este plan vive en `docs/superpowers/` y se purga del snapshot de entrega.
- **No romper lo nominal:** los 2134 asserts C++ + golden vectors + 56 pytest deben seguir verdes.

## File Structure

**Nuevos:**
- `dashboard/test_robustez_gui.py` — monkey de GUI determinista + test de regresión del crash.
- `dashboard/test_defensivo.py` — tests de parseo/estado/storage/reports ante entrada basura.
- `dashboard/robustez.py` — utilidades de tolerancia (instalar excepthook, `logging`, `ejecutar_seguro`).
- `firmware/test/test_protocolo_fuzz.cpp` — fuzz del parser de protocolo C++ (doctest).

**Modificados (en ejecución, según diagnóstico/TDD):**
- `dashboard/app.py` — fix del crash; `tick()`/handlers envueltos; instalar red de seguridad.
- `dashboard/sesion.py` — parseo defensivo (campos/tipos/rangos/líneas gigantes).
- `dashboard/fuente.py` — endurecer `FuenteSerial`/`FuenteCore` en frontera.
- `dashboard/storage.py`, `dashboard/reports.py` — errores de DB/disco/export no propagan.
- `firmware/lib/GameCore/Protocol.h` — parser sin lecturas fuera de rango ante línea malformada.
- `firmware/lib/GameCore/GameEngine.*` — rangos de `set_level`/`set_mode`/`pisar` (verificar/endurecer).
- `firmware/src/main.cpp` — cota de tamaño del buffer de línea (serial/TCP).

---

## FASE 1 — El crash (P0)  ·  skill: systematic-debugging

### Task 1.1: Mapear la superficie de UI y escribir el monkey reproductor

**Files:**
- Read: `dashboard/app.py` (widgets, handlers, `tick`), `dashboard/paneles.py`, `dashboard/sesion.py`
- Create: `dashboard/test_robustez_gui.py`

**Interfaces:**
- Produces: `construir_ventana(fuente)` helper de test (o reutiliza el de `test_app_smoke.py`/`test_integracion.py`); `monkey(ventana, seed, n_eventos)` que dispara acciones aleatorias.

- [ ] **Step 1: Leer `app.py`, `paneles.py`, `test_app_smoke.py`, `test_integracion.py`** y listar: widgets clickeables (botones start/stop/pause/aplicar/exportar), combos (modo/nivel/perfil), pestañas, y cómo los tests headless ya construyen la ventana (`QT_QPA_PLATFORM=offscreen`, referencia fuerte al `QApplication`).
- [ ] **Step 2: Escribir el monkey determinista** en `dashboard/test_robustez_gui.py`: con `random.Random(seed)`, en cada iteración elige una acción de la lista mapeada (click botón, cambiar combo, cambiar pestaña, inyectar pisada vía `FuenteCore.pisar`, disparar `tick`), la aplica y llama `QApplication.processEvents()`. Aserción: completa `n_eventos` sin excepción ni abort.
- [ ] **Step 3: Correr el monkey con varias seeds** para intentar reproducir el crash.

Run: `.venv/bin/python -m pytest dashboard/test_robustez_gui.py -v`
Expected: idealmente **reproduce el crash/abort** (o una excepción). Si no reproduce, subir `n_eventos`, ampliar el set de acciones (clicks rápidos repetidos, cambio de pestaña durante juego, exportar sin sesión) y variar seeds hasta provocarlo.

- [ ] **Step 4: Commit** (el reproductor, aunque aún falle/crashee, es la base de la regresión).

```bash
git add dashboard/test_robustez_gui.py
git commit -m "test(dashboard): monkey determinista de GUI para reproducir el crash"
```

### Task 1.2: Aislar la causa raíz (systematic-debugging)

**Files:** Read según hipótesis: `dashboard/app.py` (`tick`, matplotlib canvas), `dashboard/paneles.py`, `dashboard/analitica.py`.

- [ ] **Step 1: Reducir el caso mínimo** — a partir de la seed que crashea, recortar la secuencia de acciones al mínimo que reproduce (bisección de la lista de eventos).
- [ ] **Step 2: Descartar hipótesis en orden**, con evidencia: (a) **reentrada del `tick`** mientras procesa eventos/diálogos; (b) **`FigureCanvas`/figuras matplotlib** recreadas sin referencia fuerte (la trampa conocida: el canvas aborta sin ref al QApplication) — buscar dónde se crean/destruyen canvases al refrescar o cambiar de pestaña; (c) **objeto Qt accedido tras `deleteLater`/cierre**; (d) diálogo modal reentrante. Ejecutar bajo `faulthandler` (`python -X faulthandler`) para capturar el traceback nativo del segfault.
- [ ] **Step 3: Escribir la causa raíz** (1-2 frases con evidencia: qué acción, qué objeto, por qué). No proponer fix hasta aquí.

(No hay commit: es investigación. El hallazgo alimenta 1.3.)

### Task 1.3: Fix mínimo + test de regresión

**Files:** Modify: el archivo de la causa (probablemente `dashboard/app.py` o `dashboard/paneles.py`). Test: `dashboard/test_robustez_gui.py`.

- [ ] **Step 1: Escribir el test de regresión** — la secuencia mínima de la Task 1.2 como test explícito que reproduce el crash de forma determinista (seed fija). Debe **fallar/crashear** antes del fix.
- [ ] **Step 2: Verificar que falla.** Run: `.venv/bin/python -m pytest dashboard/test_robustez_gui.py::test_regresion_crash -v` → FAIL/abort.
- [ ] **Step 3: Aplicar el fix mínimo** en la causa raíz (p. ej. mantener referencia fuerte al canvas; guardar contra reentrada del `tick` con un flag; no acceder a widget tras cierre). Código determinado por la Task 1.2.
- [ ] **Step 4: Verificar que pasa** el test de regresión y el monkey con varias seeds. Run: `.venv/bin/python -m pytest dashboard/test_robustez_gui.py -v` → PASS.
- [ ] **Step 5: Suite verde.** Run: `./scripts/run_all_tests.sh` → TODO VERDE.
- [ ] **Step 6: Commit.**

```bash
git add dashboard/app.py dashboard/test_robustez_gui.py
git commit -m "fix(dashboard): cierra el crash de Qt bajo uso intensivo + test de regresion"
```

---

## FASE 2 — Programación defensiva en boundaries  ·  skill: test-driven-development

> Cada tarea: leer el archivo, escribir un test que le meta la entrada basura concreta (falla), endurecer la frontera (pasa), suite verde, commit. El endurecimiento **valida al entrar y no re-valida dentro**.

### Task 2.1: Parseo de protocolo defensivo (`sesion.py`)

**Files:** Read/Modify: `dashboard/sesion.py`. Test: `dashboard/test_defensivo.py` (Create).

**Interfaces:** Consumes: el método de `sesion.py` que ingiere una línea de evento (identificarlo al leer). Produces: ese método nunca lanza ante entrada malformada.

- [ ] **Step 1:** Leer `sesion.py`; identificar dónde se parsea la línea/JSON y qué campos consume (`tipo`, `celda`, `rate`, etc.).
- [ ] **Step 2: Test que falla** en `test_defensivo.py`: alimentar a ese método (i) JSON válido pero con **campo faltante**, (ii) **tipo inesperado** (p. ej. `celda:"x"`), (iii) **valor fuera de rango** (celda 99), (iv) **línea gigante** (1 MB). Aserción: no lanza; ignora/registra la línea inválida y sigue procesando las válidas.
- [ ] **Step 3: Verificar que falla.** Run: `.venv/bin/python -m pytest dashboard/test_defensivo.py -k sesion -v` → FAIL.
- [ ] **Step 4: Endurecer** `sesion.py`: validar presencia/tipo/rango de campos en la frontera de parseo; descartar la línea inválida (con `logging.debug`) sin propagar.
- [ ] **Step 5: Verificar que pasa** + `./scripts/run_all_tests.sh` verde.
- [ ] **Step 6: Commit** `feat(dashboard): parseo de protocolo defensivo en sesion.py`.

### Task 2.2: Fuentes robustas (`fuente.py`)

**Files:** Read/Modify: `dashboard/fuente.py`. Test: `dashboard/test_defensivo.py`.

- [ ] **Step 1:** Test que falla: `FuenteSerial` con `loop://` (ya soportado) recibiendo **bytes no-UTF8**, **línea sin `\n` que crece** y **fragmentos parciales**; `FuenteCore.enviar` con **comando basura**. Aserción: `recibir()` nunca lanza; el buffer no crece sin cota.
- [ ] **Step 2: Verificar falla** → **Step 3: Endurecer** (cota de tamaño del buffer interno; `decode(..., "replace")` ya presente — verificar; comando inválido al core no rompe) → **Step 4: verde** → **Step 5: Commit** `feat(dashboard): fuentes toleran bytes basura y lineas sin fin`.

### Task 2.3: Estado de sesión / comandos reentrantes (`app.py`, `sesion.py`)

**Files:** Read/Modify: `dashboard/app.py`, `dashboard/sesion.py`. Test: `dashboard/test_defensivo.py`.

- [ ] **Step 1:** Test que falla: secuencias inválidas de control — `stop` sin `start`, doble `start`, `pause` sin sesión, cambiar modo/nivel a mitad de juego, "Aplicar" sin datos, exportar sin sesión. Aserción: ninguna lanza; el estado queda coherente.
- [ ] **Step 2–5:** verificar falla → endurecer guardas de estado en los handlers (idempotencia/orden) → verde → **Commit** `feat(dashboard): guardas de estado ante comandos fuera de orden`.

### Task 2.4: Storage y export tolerantes (`storage.py`, `reports.py`)

**Files:** Read/Modify: `dashboard/storage.py`, `dashboard/reports.py`. Test: `dashboard/test_defensivo.py`.

- [ ] **Step 1:** Test que falla: `storage` con ruta a directorio inexistente / DB corrupta; `reports` export a **ruta sin permiso** / sin datos. Aserción: error controlado (excepción propia o retorno), **nunca** un crash que suba a la GUI.
- [ ] **Step 2–5:** verificar → envolver E/S de DB/disco en la frontera → verde → **Commit** `feat(dashboard): storage/export degradan sin tumbar la GUI`.

### Task 2.5: Parser de protocolo C++ defensivo (`Protocol.h`)

**Files:** Read/Modify: `firmware/lib/GameCore/Protocol.h`. Test: `firmware/test/test_protocolo.cpp` (extender).

- [ ] **Step 1:** Leer `Protocol.h` y su mini-parser. Test doctest que falla: parsear líneas malformadas — **clave sin valor**, **comilla sin cerrar**, **número desbordado**, **cadena vacía**, **solo `{`**, **1000 comas**. Aserción: no hay lectura fuera de rango; devuelve evento inválido/vacío, nunca UB.
- [ ] **Step 2: Verificar falla.** Run: `./scripts/run_all_tests.sh` (o compilar `test_protocolo` a mano con g++). 
- [ ] **Step 3: Endurecer** el parser (chequear límites de índice antes de leer; longitudes acotadas).
- [ ] **Step 4: Verde** (idealmente recompilar una vez con `-fsanitize=address,undefined` y correr el test → sin hallazgos).
- [ ] **Step 5: Commit** `feat(gamecore): parser de protocolo sin lecturas fuera de rango`.

### Task 2.6: Rangos en el motor (`GameEngine`)

**Files:** Read/Modify: `firmware/lib/GameCore/GameEngine.*`. Test: `firmware/test/test_core.cpp` (extender).

- [ ] **Step 1:** Test que falla: `set_level` fuera de rango, `set_mode` desconocido, `pisar(0)`/`pisar(99)`. Aserción: se ignora con seguridad, sin cambiar a estado inválido.
- [ ] **Step 2–4:** verificar (puede que ya esté cubierto → confirmar) → endurecer si falta → verde.
- [ ] **Step 5: Commit** `feat(gamecore): rangos seguros en set_level/set_mode/pisar`.

### Task 2.7: Cota del buffer de línea del firmware (`main.cpp`)

**Files:** Read/Modify: `firmware/src/main.cpp` (`procesarLineasSerial`/`procesarLineasDe`). Test: extraer la lógica de acumulación a una función testeable o test en `firmware/test/`.

- [ ] **Step 1:** Test que falla: alimentar bytes **sin `\n`** indefinidamente. Aserción: el buffer no supera una cota (p. ej. 512 B); al excederla, se descarta hasta el próximo `\n`.
- [ ] **Step 2–4:** verificar → añadir la cota en la acumulación → verde (sin romper el smoke Wokwi ni `pio run -e esp32dev`).
- [ ] **Step 5: Commit** `feat(fw): cota de tamano del buffer de linea serial/TCP`.

---

## FASE 3 — Fuzzing / monkey testing determinista  ·  skill: test-driven-development

### Task 3.1: Endurecer el monkey de GUI como test permanente

**Files:** Modify: `dashboard/test_robustez_gui.py`.

- [ ] **Step 1:** Generalizar el monkey de la Fase 1 a un test parametrizado por varias seeds fijas que ejecute **≥5000 eventos** cada una. Aserción: 0 crashes, 0 excepciones no capturadas.
- [ ] **Step 2:** Verde. Run: `.venv/bin/python -m pytest dashboard/test_robustez_gui.py -v`.
- [ ] **Step 3: Commit** `test(dashboard): monkey de GUI multi-seed en la suite`.

### Task 3.2: Fuzz del protocolo (Python)

**Files:** Create/Modify: `dashboard/test_defensivo.py`.

- [ ] **Step 1:** Test que genera con `random.Random(seed)` **≥5000 líneas** (bytes/JSON basura, campos/tipos aleatorios) y las pasa por el parser de `sesion.py`. Aserción: nunca lanza.
- [ ] **Step 2:** Verde → **Step 3: Commit** `test(dashboard): fuzz determinista del parser de protocolo`.

### Task 3.3: Fuzz del parser de protocolo (C++)

**Files:** Create: `firmware/test/test_protocolo_fuzz.cpp`. Modify: `scripts/run_all_tests.sh` (registrar el binario nuevo).

- [ ] **Step 1:** Leer cómo `run_all_tests.sh` compila y lista los binarios de test. Escribir `test_protocolo_fuzz.cpp`: LCG seedado genera **≥5000 líneas** de longitud/bytes aleatorios y las parsea; aserción doctest: no crashea (el valor de retorno se ignora, importa que no haya UB).
- [ ] **Step 2:** Registrar el binario en `run_all_tests.sh`.
- [ ] **Step 3:** Verificar falla si el parser aún es frágil (o pasa si 2.5 ya lo endureció) → **Step 4:** correr una vez con `-fsanitize=address,undefined` → **Step 5: verde**.
- [ ] **Step 6: Commit** `test(gamecore): fuzz determinista del parser + registro en run_all_tests`.

---

## FASE 4 — Tolerancia a fallos / degradación  ·  skill: test-driven-development

### Task 4.1: Red de seguridad de la GUI (`robustez.py`, `app.py`)

**Files:** Create: `dashboard/robustez.py`. Modify: `dashboard/app.py`. Test: `dashboard/test_defensivo.py`.

**Interfaces:** Produces: `instalar_excepthook(logger)` (registra excepciones no capturadas sin abortar); `ejecutar_seguro(fn, logger)` (envuelve una llamada; loguea y no propaga).

- [ ] **Step 1:** Test que falla: un handler/`tick` que lanza una excepción **no** debe abortar la app; `ejecutar_seguro` la captura y registra. Aserción: la app sigue viva; se registró el error.
- [ ] **Step 2: Verificar falla** → **Step 3:** implementar `robustez.py` y envolver `tick()` y los handlers de `app.py` con `ejecutar_seguro`; instalar el excepthook al arrancar.
- [ ] **Step 4: Verde** (incluido el monkey de 3.1, que ahora tolera incluso bugs internos) → **Step 5: Commit** `feat(dashboard): red de seguridad global — la GUI nunca muere`.

### Task 4.2: Degradación visible ante caída de fuente/DB

**Files:** Modify: `dashboard/app.py`, `dashboard/robustez.py`. Test: `dashboard/test_defensivo.py`.

- [ ] **Step 1:** Test que falla: si `Fuente.recibir()` empieza a fallar o la DB cae, la UI muestra un estado "desconectado/degradado" y sigue viva (FuenteTCP ya reconecta; aquí se refleja en la UI). Aserción: no crash; hay señal de degradación.
- [ ] **Step 2–4:** verificar → reflejar el estado degradado en la UI (etiqueta/indicador) → verde → **Step 5: Commit** `feat(dashboard): degradacion visible ante caida de fuente/DB`.

### Task 4.3: Lazo del firmware acotado

**Files:** Read/Modify: `firmware/src/main.cpp`. 

- [ ] **Step 1:** Revisar el `loop()`: cada iteración hace trabajo **acotado** (cliente TCP caído se maneja — ya parcial; entrada basura no bloquea — cubierto por 2.7). Documentar/endurecer lo que falte.
- [ ] **Step 2:** `pio run -e esp32dev` SUCCESS + smoke Wokwi verde → **Step 3: Commit** `feat(fw): lazo acotado y tolerante a cliente/entrada`.

---

## Cierre

- [ ] `./scripts/run_all_tests.sh` **verde** con todos los tests nuevos.
- [ ] Monkey de GUI y fuzz (Py/C++) corren miles de eventos/líneas sin crash.
- [ ] Crash original **cerrado** con test de regresión.
- [ ] CI (`.github/workflows/ci.yml`) corre los generadores con seed fija (añadir si hace falta).
- [ ] Actualizar `CLAUDE.md`/handoff con el estado; commits pequeños por tarea.

## Self-Review (cobertura de la spec)

- Fase 1 crash → Tasks 1.1–1.3. ✔
- Defensiva Python (protocolo, fuentes, estado, storage, export) → 2.1–2.4. ✔
- Defensiva C++ (parser, motor, buffer firmware) → 2.5–2.7. ✔
- Fuzzing (GUI, protocolo Py, protocolo C++) → 3.1–3.3. ✔
- Tolerancia (GUI nunca muere, degradación, firmware) → 4.1–4.3. ✔
- Verificación/CI → Cierre. ✔
Sin placeholders de intención (cada tarea nombra archivo, modo de fallo y aserción objetivo). El código literal de endurecimiento se produce en ejecución TDD por depender del contenido vigente de cada archivo (leído en el Step 1 de cada tarea).

# Diseño — Robustez integral del software del Tapete Interactivo

**Fecha:** 2026-07-07 · **Estado:** aprobado (brainstorming) · **Andamiaje:** este
documento vive en `docs/superpowers/` y se purga del snapshot de entrega.

## Contexto y disparador

El hardware está validado end-to-end (6 FSR + 3 juegos por USB/Serial). Al probar el
dashboard, el usuario reportó que **con "muchos clicks" o "en ciertos casos" el programa
crashea** ("Python 3.12 dejó de funcionar" = **segfault nativo de Qt**, no una excepción
Python). El dashboard es **single-thread**: un `QTimer` hace polling de la fuente
(`app.py:tick`), así que el crash NO es cross-thread; las causas típicas en ese modelo son
reentrada del event loop, el `FigureCanvas` de matplotlib sin referencia fuerte (trampa ya
conocida en el proyecto), o acceso a un objeto Qt destruido.

El usuario pide robustecer el proyecto de forma **profesional, completa e integral**,
aceptando pedir prórroga si el deadline (8-jul 18:00) aprieta. Pilares nombrados:
tolerancia a fallos/resiliencia, monkey testing/fuzzing, programación defensiva.

## Objetivo

Que el sistema **no se caiga jamás** por entrada inesperada, uso intensivo o fallos de
E/S, y que ese comportamiento esté **demostrado con tests** (incluidos generadores de
caos deterministas). Cerrar el crash reportado con una regresión que lo fije.

## Alcance (superficie)

Todo el software del proyecto:
- **PC:** `dashboard/` (Qt, matplotlib, I/O, estado de UI) y `simulator/`.
- **C++:** `firmware/lib/GameCore/` (parser de protocolo, motor, bridge C ABI) y
  `firmware/src/` (buffers de línea, lazo del ESP32).

GameCore ya tiene 2134 aserciones + golden vectors (comportamiento nominal sólido); el
trabajo aquí es **el eje adversarial** (entradas malformadas, límites, caos), no re-probar
lo nominal.

## Principios rectores

1. **Validar en las fronteras, confiar dentro.** Todo dato externo (serial, TCP, usuario,
   SQLite, archivos, ctypes) se valida al entrar; el código interno no re-valida. Sin
   duplicar checks (regla `code-quality`).
2. **La GUI nunca muere.** Ninguna excepción ni dato basura debe tumbar el dashboard: peor
   caso, se registra (`logging`) y se continúa; la UI avisa si algo se degrada.
3. **El firmware no se cuelga.** Basura por serial/TCP, líneas sin fin o clientes caídos
   no deben bloquear ni reventar el ESP32.
4. **TDD siempre.** Cada endurecimiento nace de un test que falla antes y pasa después. La
   suite (`run_all_tests.sh`) queda verde.
5. **YAGNI.** Se endurece lo que tiene una vía de fallo real, no defensas hipotéticas.

## Fase 1 — El crash (P0)

Con la skill `systematic-debugging` (no parchear sin causa raíz):
1. **Reproducir** de forma determinista: lanzar el dashboard con `FuenteCore` en modo
   `offscreen` y un mini-monkey que inyecta clics/pisadas/cambios de pestaña a alta
   frecuencia hasta provocar el crash (hay display real; también sirve headless).
2. **Aislar la causa raíz** (hipótesis a descartar en orden): reentrada del `tick` mientras
   procesa; `FigureCanvas`/figuras matplotlib recreadas sin referencia fuerte; widget o
   `QObject` accedido tras `deleteLater`; reentrada por diálogos modales.
3. **Fix mínimo** en la causa + **test de regresión** que falle antes y pase después.

**Entregable:** crash reproducido, causa documentada, fix + test. Es prerequisito de las
demás fases (la Fase 3 generaliza este monkey).

## Fase 2 — Programación defensiva en los boundaries

Cada frontera valida su entrada; cada endurecimiento con test.

**Python (dashboard/simulator):**
- **Parseo de protocolo** (`sesion.py`): línea no-JSON (ya via `JSONDecodeError`), pero
  además campos faltantes, tipos inesperados, valores fuera de rango, líneas gigantes.
- **Fuentes** (`fuente.py`): bytes basura, UTF-8 inválido (ya usa `replace`), líneas
  parciales/sin fin, socket/serial a media escritura. Revisar `FuenteSerial` (silencia
  I/O) y `FuenteCore` (comandos inválidos vía bridge).
- **Estado de sesión / comandos** (`app.py`, `sesion.py`, `paneles.py`): clics en estado
  inconsistente (start/stop/pause reentrantes o fuera de orden), cambio de modo/nivel a
  mitad de sesión, "Aplicar" sin datos, exportar sin sesión.
- **Storage** (`storage.py`): errores de SQLite/disco no deben propagar a la UI.
- **Export** (`reports.py`): rutas inválidas, permisos, fallo de matplotlib/PDF.

**C++ (firmware/GameCore):**
- **Parser de protocolo** (`Protocol.h`): líneas malformadas, claves ausentes, números
  desbordados, comillas sin cerrar → sin lecturas fuera de rango ni UB; devolver evento
  inválido, nunca crashear.
- **Motor** (`GameEngine`): `set_level` fuera de rango, `set_mode` desconocido, `pisar`
  celda ∉ 1..CELDAS → ignorar con seguridad (verificar que ya lo hace; si no, endurecer).
- **Buffers de línea del firmware** (`main.cpp` `procesarLineasSerial/TCP`): una línea sin
  `\n` no debe crecer sin límite → **cota de tamaño** (descartar/rotar al excederla).

## Fase 3 — Harness de fuzzing / monkey testing

Generadores **deterministas** (con `seed`, reproducibles) integrados a pytest/doctest y CI:
- **Monkey de GUI** (Python, `offscreen`): secuencias aleatorias de clics/pisadas/cambios
  de pestaña/entradas a alta frecuencia; aserción: la app sobrevive N miles de eventos sin
  crash ni excepción no capturada. Generaliza el reproductor de la Fase 1.
- **Fuzz del protocolo (Python)**: miles de líneas malformadas a `sesion.py`; nunca lanza.
- **Fuzz del parser de protocolo (C++)**: g++/doctest alimenta líneas aleatorias a
  `Protocol.h`; nunca UB ni crash (idealmente correr una vez bajo ASan/UBSan).
- **Opcional documentado:** fuzz del firmware completo por Wokwi (costoso; se deja como
  nota, no se implementa en esta ronda salvo que sobre presupuesto).

## Fase 4 — Tolerancia a fallos / degradación

Red de seguridad global:
- **Dashboard:** envolver `tick()` y los handlers de forma que una excepción **se registre
  y no propague** (la app sigue viva); `sys.excepthook` / hook de Qt que loguea en vez de
  abortar; degradación limpia si cae serial/TCP o SQLite (avisar en la UI, reconectar donde
  aplique — `FuenteTCP` ya reconecta). `logging` configurable para diagnóstico en campo.
- **Firmware:** cliente TCP caído y basura de entrada ya no deben colgar el lazo (verificar
  y endurecer); el `loop()` nunca hace trabajo no acotado por iteración.

## Verificación / criterios de aceptación

- El crash original **reproducido y cerrado** con test de regresión.
- `./scripts/run_all_tests.sh` **verde** (C++ doctest + `.so` + pytest), con los nuevos
  tests defensivos y de fuzzing incluidos.
- El monkey de GUI corre **N miles de eventos sin crash**; el fuzz de protocolo (Py y C++)
  corre **N miles de líneas malformadas sin excepción/UB**.
- CI (`.github/workflows/ci.yml`) ejecuta los generadores con seed fijo.

## Fuera de alcance (YAGNI)

- Reescribir GameCore/firmware más allá de endurecer boundaries.
- Re-sincronización de estado de juego tras reconexión TCP (ya documentado como límite en
  `fuente.py`).
- Fuzz del firmware completo en hardware/Wokwi (solo nota).
- Refactors no relacionados con la robustez.

## Notas

- Deadline 8-jul 18:00; si aprieta, se pide prórroga (decisión del usuario, no recortar).
- Orden de ejecución: Fase 1 (crash) primero; luego 2/3/4 pueden entrelazarse por boundary
  (defensiva → su fuzz → su tolerancia) siguiendo TDD.
- Este spec se purga del snapshot de entrega (andamiaje `docs/superpowers/`).

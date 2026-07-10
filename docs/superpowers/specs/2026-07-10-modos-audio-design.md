# Diseño — Correcciones de modos de juego + sistema de audio

Fecha: 2026-07-10. Origen: prueba E2E sin acrílico OK; el autor reporta 3 detalles
en los modos y define el comportamiento de audio deseado.

Principio rector intacto: la lógica vive solo en `firmware/lib/GameCore/` (fuente
única, compilada para ESP32 y para el `.so` del simulador). TDD: test primero.

## Resumen de los cuatro frentes

| # | Frente | Capa | Naturaleza |
|---|---|---|---|
| 1 | Secuencias siempre iguales | Dashboard/Sim (fuera de GameCore) | Bug de configuración |
| 2 | Transición de ronda instantánea en Memoria | GameCore (`ModoMemoria`) | Falta fase de pausa |
| 3 | Equilibrio enciende LEDs de más en el tapete | Hardware/eléctrico | Fuera de código |
| 4 | Sistema de audio (4 tonos) | GameCore + assets | Feature |

Evidencia empírica (repro headless contra el mismo `GameCore.so`):
- Equilibrio nivel 3 emite **exactamente k=4** eventos `led`>0 por patrón y queda en 4 al
  pasar de patrón → **GameCore limpio**.
- Memoria: al completar la serie, el 1er `led` del nuevo patrón y el `sound` se emiten en
  el **mismo ms** que la última pisada → transición instantánea confirmada.
- Dashboard manda `set_seed` con semilla **fija** (`SEMILLA_DEFECTO=12345`) en cada Start.

---

## Frente 1 — Semilla aleatoria por partida (NO toca GameCore)

Causa: `app.py` envía siempre `set_seed:12345`. GameCore es determinista por diseño
(base de los golden vectors); la entropía es una **entrada externa** que se inyecta por
`set_seed`, el mecanismo ya existente. Flujo actual `set_seed → set_mode → start`: la
secuencia de Memoria se construye en `set_mode` (constructor del modo) **después** del
`set_seed`, así que basta variar la semilla. No hay que mover la generación.

Cambios:
- `dashboard/app.py`: `self.semilla = None` por defecto. En `_start_interno`, si
  `self.semilla is None` usar `random.randint(1, 2**32-1)` (evita 0, que xorshift
  normaliza); si tiene valor, respetarlo (smoke/tests reproducibles). El smoke
  (`v.semilla = 12345`) queda determinista.
- `simulator/tapete_sim.py`: implementar la tecla **R** (documentada pero ausente) →
  envía `set_seed` con valor aleatorio. El `--smoke` sigue con seed fijo explícito.

Alcance: la variabilidad aplica a los **tres** modos (deseable). Sin impacto en golden ni
en los doctests (todos mandan `set_seed` explícito).

## Frente 2 — Pausas claras en Memoria (~1.2 s, todo apagado)

Nueva fase no bloqueante `Fase::PAUSA` en `ModoMemoria`. Durante la pausa: todo LED
apagado; al vencer `tTrans_`, arranca la exhibición pendiente. Se aplica en los **tres**
momentos aprobados:
1. **Antes de la 1ª exhibición** (`iniciar()` → pausa → exhibición). El sonido de inicio
   (S1) lo emite el motor al `START`; la pausa deja verlo antes de la secuencia.
2. **Entre rondas** (al completar la serie, antes de exhibir la nueva, más larga).
3. **Tras un error** (antes de repetir la misma secuencia).

Config: `cfg::memoria::pausaMs(nivel)` → 1200 ms (fijo; `nivel` ignorado por ahora).

Detalle de máquina de estados:
```
iniciar(ms):        hits=misses=0; fin=false; iniciarPausa(ms)
iniciarPausa(ms):   apagarTodo(); fase=PAUSA; tTrans = ms + pausaMs
actualizar(ms):     if fin: return
                    if fase==PAUSA: if ms>=tTrans: iniciarExhibicion(ms); return
                    if fase==EXHIBIENDO: <bucle de exhibición: S2 al encender cada LED>
pisar correcto no-final:   S2; ++inputIndex
pisar que completa serie:  ++hits; score; si len>=max → fin (motor suena S4)
                           si no → S3; crecer(); iniciarPausa(ms)
pisar incorrecto:          ++misses; score; iniciarPausa(ms)   // sin sonido de error
```

## Frente 4 — Audio: 4 tonos sintéticos

Mapa de sonidos (reemplaza el actual; se **elimina** el sonido de error). Cuatro archivos:

| id | Constante | Evento | Memoria | Velocidad | Equilibrio |
|----|-----------|--------|---------|-----------|------------|
| 1 | `SONIDO_INICIO` | Inicio de sesión (START) | ✓ | ✓ | ✓ |
| 2 | `SONIDO_ACIERTO` | Pisada correcta individual **y** cada LED de la exhibición | cada botón / exhibición | cada objetivo | — (parciales mudas) |
| 3 | `SONIDO_RONDA` | Serie/patrón completado | al completar la serie | — | al completar el patrón |
| 4 | `SONIDO_FIN` | Fin de sesión (FINISHED) | ✓ | ✓ | ✓ |

Reglas para no encimar sonidos:
- El botón que **completa** una serie/patrón suena **S3**, no S2.
- Si esa ronda es la **última** (fin de sesión), no suena S3: el motor emite **S4** al
  pasar a FINISHED.
- Velocidad no tiene S3 (cada acierto ya es una ronda de un botón → solo S2).
- Equilibrio suena **solo al completar** el patrón (S3); las pisadas parciales van mudas
  (decisión del autor: "un sonido cuando se pulsaron TODOS los botones iluminados").
- La **exhibición** de la secuencia en Memoria suena **S2 por cada LED mostrado** (el mismo
  tono que el niño oirá al pisar ese botón: asocia luz+sonido, refuerza la memoria).

Ubicación de los disparos (DRY):
- **S1** en `GameEngine::procesar(START)` antes de `modo_->iniciar()` (transversal).
- **S4** en `GameEngine::revisarFin()` al entrar en FINISHED (transversal), antes de
  `apagarTodos()`.
- **S2/S3** dentro de cada modo, en `pisar()`.

Generación de assets (`scripts/gen_audio.py`, determinista):
- numpy sintetiza los tonos → WAV → `ffmpeg` a **MP3 mono, 44.1 kHz, 128 kbps** (perfil
  compatible con DFPlayer Mini). Salida: `audio/0001.mp3`..`0004.mp3`.
- Carácter: S1 arpegio ascendente; S2 tono corto claro; S3 melodía breve de logro; S4
  fanfarria de cierre. Cortos (0,3–1 s), amables.
- El autor copia `audio/000X.mp3` a `/mp3/` de la microSD FAT32 (mismos archivos que usa
  el simulador). Actualizar `audio/README.md`.

## Frente 3 — Equilibrio: diagnóstico eléctrico (fuera de código)

La pantalla muestra solo los botones correctos mientras el tapete enciende de más →
GameCore y el mapeo LEDC (`EspHardware`, canal=celda-1) están bien; la divergencia es
física. Procedimiento para el autor (multímetro, sin flashear del agente):
1. En modo juego, con un patrón fijo encendido, medir tensión en cada LED y confirmar qué
   celdas físicas se activan frente a las que marca la pantalla.
2. Verificar el cableado LED↔celda contra `Config.h` (`PIN_LED = {4,5,18,19,21,23}`) y el
   ruteo del driver en `docs/hardware/cableado.md`.
3. Sospechas ordenadas por probabilidad: retorno de tierra compartido que causa ghosting,
   canal del driver puenteado, o alimentación insuficiente con varios LEDs simultáneos.

Se entrega como checklist; no genera cambios de firmware salvo que el hallazgo obligue a
corregir el mapa de pines (que es fuente de verdad y solo se toca conciliando cableado).

## Impacto en la suite (TDD)

- Doctests a reescribir: `test_modo_memoria` (exhibición con S2, S3 en vez de EXITO, pausa),
  `test_modo_velocidad` (S2/sin error), `test_modo_equilibrio` (S2 parcial, S3, sin error).
  `test_core/test_gameengine` no arranca sesión con éxito/fin, pero captura `antes` tras el
  START (S1 ya emitido) → sigue válido; verificar.
- `shared/golden_vectors.json`: los 6 eventos `sound` cambian de id según el nuevo mapeo
  (id 2 se mantiene = acierto; id 4 EXITO→ahora id 3 al completar y id 4 solo al fin; id 3
  ERROR desaparece). Los timelines de Memoria usan t≫ (20000, 40000…): la pausa de 1,2 s no
  los altera. Regenerar a mano los `expected` y validar con `golden_runner`.
- **`simulator/jugador_modos.py` (impacto crítico):** el jugador de Memoria detecta la
  exhibición por `sound id==SONIDO_INSTRUCCION(1)` y distingue exhibición de confirmación
  porque hoy la confirmación **no** suena. Con el nuevo audio (exhibición y confirmación
  suenan S2) esa heurística falla. Adaptar: construir la secuencia por **fase** (LED>0
  mientras `not entrada`), no por el sonido. El jugador de Equilibrio no usa sonidos → sin
  cambios. Así juega idéntico y `test_jugador_modos`/`test_montecarlo`/`test_evidencia_modos`
  siguen verdes.
- **Evidencia del artículo — NO se regenera.** `docs/evidencia/resultados.json` y las trazas
  de `docs/evidencia/ejecucion/` son un snapshot entregado al redactor externo. Ningún test
  las valida; los números (convergencia, IC 95 %, aciertos) no cambian (la lógica de aciertos
  no cambia). Quedan intactas; sus trazas conservan los ids de sonido previos (histórico).
- Dashboard: sin cambios de comportamiento observable (los tests usan modo 2, sin pausa; el
  dashboard ignora `sound`).

## Fuera de alcance (YAGNI)

- Patrones de parpadeo más ricos, subniveles nuevos, reconexión TCP, etc. (backlog §4 del
  ROADMAP): no se tocan.
- Auto-siembra por entropía de hardware en el firmware: innecesaria (siempre hay dashboard).
- Pausas configurables por nivel/terapeuta: fijo 1200 ms por ahora.

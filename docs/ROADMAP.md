# Roadmap — estado vigente y próximos pasos

Fuente única del **estado del proyecto** (software, hardware, CI, artículo) y del trabajo
pendiente. `CLAUDE.md` recoge las reglas durables; este documento, lo que cambia.

Mantener siempre la disciplina del proyecto: **TDD**, **una sola fuente de verdad**
(`GameCore`), tests en verde antes de avanzar.

> **PUNTO DE CONTINUACIÓN (2026-07-09).** **No hay deadline externo:** el cliente aprobó el
> trabajo y la fecha queda a criterio del autor (lo antes posible, sin recortar calidad).
>
> **Prioridad total y exclusiva: el artículo (§1).** Debe enviarse a revisión. Nada más se
> toca hasta que esté terminado.
>
> El **CI está roto** (§2) y el **hardware está bloqueado y pausado** (§3). Ambos se
> retoman *después* del artículo, en ese orden.

**Línea base del software:** `./scripts/run_all_tests.sh` → TODO VERDE (52 casos /
2174 aserciones C++ + 119 pytest); `.venv/bin/pio run -e esp32dev` → SUCCESS. Si algo
está en rojo al empezar, arreglarlo antes de añadir nada. Esta máquina tiene display real
(`DISPLAY=:0` / Wayland): se pueden lanzar el simulador y el dashboard, y generar capturas
con `scripts/demo_visual.py`.

---

## 1. El artículo — PRIORIDAD ACTUAL

Entregable académico del proyecto de grado. El **anteproyecto V3 es el documento guía del
profesor y NO se edita**; el artículo es el único entregable editable, y es donde se
justifican las desviaciones respecto de la guía.

**Regla de integridad, no negociable:** no hubo pruebas con niños ni comité de ética. El
artículo reporta **validación funcional** (simulación determinista + banco), y lo clínico
se enuncia como trabajo futuro. Nunca en pasado lo que no ocurrió.

**Materiales en `docs/articulo/`:**

| Archivo | Qué es |
|---|---|
| `Articulo_Mejorado.docx` | Base de partida. **Incompleta:** 4323 palabras, termina en el título «4. Metodología» y salta a Referencias. Aporta marco teórico y estado del arte revisados, y un juego propio de referencias. |
| `Articulo_Tapete_Interactivo.md` / `.docx` | Versión previa, **completa**. Ya trae el reencuadre honesto: resumen sin pruebas clínicas, objetivo (iii) aterrizado, §4.1 justifica LED blanco frente a RGB, §5.5 marcada «pendiente de datos de banco», §5.6 trazabilidad objetivo→evidencia. |
| `...V3.docx` | Anteproyecto guía del profesor. **Solo lectura.** |

**Trabajo pendiente:**

- [ ] **Unificar en un solo documento** (Markdown versionable como fuente; exportación a
      `.docx` al final), partiendo del `Mejorado` y desarrollándolo hasta un artículo
      completo, profesional y con excelencia académica.
- [ ] Reconciliar las divergencias entre versiones: «juegos didácticos» vs «juegos serios»
      (el término también aparece en palabras clave); §3.4 PLAYTEK vs juguetes para
      parálisis cerebral; numeración (§3.6 debe ser §3.5).
- [ ] **Verificar todas las referencias.** Varias del `Mejorado` no son de calidad
      académica (Scribd, ScienceDirect Topics, Emooti, Mayo Clinic) y una cita al CDC
      lleva fecha «2026, 8 de enero» sin comprobar.
- [ ] Apoyar Resultados en la evidencia funcional **real y reproducible**: golden vectors,
      dashboard/SQLite/CSV, figuras `docs/evidencia/E2_adaptacion.png`, `E3_niveles.png`,
      `E4_trayectoria.png`.
- [ ] Figura del circuito: `docs/hardware/kicad/tapete.pdf` existe pero tiene **etiquetas
      solapadas** — falta un *tidy* en eeschema antes de incluirla.

## 2. CI — ROTO, pendiente de revisión exhaustiva (después del artículo)

`.github/workflows/ci.yml` existe con 5 jobs, pero **no entrega lo que debe entregar**: el
ZIP del Release nunca se ha producido. No darlo por hecho.

**Evidencia medida (2026-07-09), no inferida:**

- Run `28985648809` (commit `5c4dcb5`): `windows-smoke` arrancó a las 00:44:42Z y GitHub lo
  **mató a las 06:44:56Z** — exactamente 6 h, el límite duro de un job. Conclusión del run:
  `failure`. `firmware-wokwi` falló aparte por un flake de red al bajar el Wokwi CLI.
- Run `29037127207` (commit `ab69ba6`): `tests`, `firmware-wokwi` y `windows-build` (7m10s)
  en verde; `windows-smoke` volvió a colgarse y acabó `cancelled`.
- `windows-smoke` **no declara `timeout-minutes`** (solo `windows-build` lo hace, con 30).
  Por eso consume las 6 h enteras del runner en cada intento.
- `windows-release` depende de `windows-smoke`, así que el entregable queda bloqueado
  aguas abajo.

**Hipótesis a verificar (NO confirmada):** el `.exe` se empaqueta con `console=False`; al
correr `--smoke` sin fuente serie, `construir_fuente_segura` (introducida en `fcf1f1e`)
degrada y abre un `QMessageBox` **modal** que en CI nunca recibe un clic → el proceso no
termina. Confirmar antes de tocar nada.

**Alcance de la revisión:** el workflow entero, no solo el smoke. Duración, timeouts en
todos los jobs, condiciones de disparo, y validar de punta a punta que un tag produce el
ZIP descargable.

## 3. Hardware físico — BLOQUEADO y pausado

**Síntoma:** con el hardware montado en la caja (protoboard pegado, 6 FSR + LEDs, acrílico
atornillado), **ninguna pisada llega al dashboard**, en ningún modo, pisando con fuerza.

**Evidencia medida (2026-07-08):**

- Con `UMBRAL_PISADA = 2000`: sesiones 15–18 de `dashboard/tapete.sqlite` → **0 eventos `press`**.
- Con `UMBRAL_PISADA = 700`: sesiones 19–22 → **0 `press` y 0 pisadas fantasma**. El reposo
  está por debajo de 700 y el pico al pisar tampoco lo alcanza.
- Modo calibración (`esp32dev_calib`), **en reposo**: los 6 canales dan `act=0 reposo=0
  pico=0 rango=0`.
- El enlace serie, el firmware y el motor **funcionan**: durante esas sesiones sí llegaron
  eventos `score`. El fallo está aislado en la detección del FSR.

`reposo=0` es compatible con un FSR sano y sin fuerza (R de megaohmios + pull-down de
10 kΩ → nodo ~0 V), así que ese bloque **no discrimina por sí solo**.

**Primer paso al retomar:** el bloque de calibración **mientras se mantiene pisado** un
botón, mirando `act` en vivo (no `pico`).

- Si `act` sube → sensores vivos, es puramente umbral: fijarlo con los picos reales.
- Si `act` sigue en 0 pisando a fondo → **no llega tensión al nodo**. Sospechoso: el riel
  **3V3** de los FSR (Dupont suelto al atornillar, o **ESP32 mal asentado**). Ningún umbral
  lo arregla: se va al multímetro (`cableado.md` §5).
- Hacerlo también con el botón 5 (GPIO32) para separar «falla del riel» de «falla de un ADC».

**Estado físico de la placa:** el ESP32 quedó flasheado con **`esp32dev_calib`**, que no
corre el juego ni WiFi (solo imprime el ADC por serial). Para volver a jugar hay que
reflashear `esp32dev`. `UMBRAL_PISADA` está **revertido a 2000**; ningún valor está
validado con el acrílico puesto.

**El agente nunca flashea ni abre el serial** (lo bloquea el hook `guard-flash.sh`). Lo hace
el humano, con el skill `/bring-up`.

**Herramientas y notas:**

- `scripts/verificar_pisadas.py` da veredicto por celda leyendo los eventos de una sesión en
  SQLite, distinguiendo sensor **mudo** de **stuck-high**. La GUI no pinta las pisadas y
  `GameEngine::pisar` solo emite `press` en RUNNING: el único rastro es la base de datos.
- **LEDs:** no hay prueba determinista (no existe comando manual de LED). Cobertura máxima =
  Modo 3 Equilibrio nivel 3 (4 celdas por patrón, 8 rondas); la comprobación es visual.
- Pendientes de puesta en marcha: grabar la microSD en FAT32 con `/mp3/0001.mp3`..`0004.mp3`
  (ver `audio/README.md`) y `cp firmware/src/secrets.h.example firmware/src/secrets.h`.

## 4. Backlog de funcionalidad (siempre con tests/golden primero)

- [ ] **Patrones de parpadeo** más ricos: barrido de inicio de ronda; error = 3 parpadeos
      rápidos; acierto = LED sólido. No bloqueante en el motor, fijado con golden vectors.
- [ ] **Modo Equilibrio — subnivel «orden específico»** (hoy es «cualquier orden»).
- [ ] **Modo Memoria — tolerancia de tiempo** por pisada y reintentos antes de acortar.
- [ ] **Modo Velocidad — ventana adaptativa** según desempeño reciente.
- [ ] **Parámetros configurables por el terapeuta** desde el dashboard, no solo niveles
      fijos en `Config.h`.
- [ ] **Gráficas de evolución** por perfil y **vista de historial** de sesiones.
- [ ] **Reconexión TCP automática** si el ESP32 se cae (hoy `FuenteTCP` no reintenta).
- [ ] **Sim pygame como cliente TCP**: hoy `servidor.py` existe pero la ventana pygame usa su
      propio core embebido; unirlos cierra el bucle simulador↔dashboard en red.
- [ ] **Golden vectors**: ampliar a más niveles y añadir escenarios `strict` para Memoria y
      Equilibrio (hoy strict solo en Velocidad).
- [ ] Persistir la **calibración del umbral** por dispositivo.

## 5. Cierre — preparación de la entrega

`scripts/preparar-entrega.sh`, pendiente de escribir: snapshot sin historial git (un único
commit inicial) **más** depuración de rastros de IA (`docs/superpowers/`, `CLAUDE.md`, y
cualquier mención a Claude/superpowers), verificando que la suite siga verde sobre el árbol
depurado.

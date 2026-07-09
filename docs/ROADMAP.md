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
2174 aserciones C++ + 135 pytest); `.venv/bin/pio run -e esp32dev` → SUCCESS. Si algo
está en rojo al empezar, arreglarlo antes de añadir nada. Esta máquina tiene display real
(`DISPLAY=:0` / Wayland): se pueden lanzar el simulador y el dashboard, y generar capturas
con `scripts/demo_visual.py`.

---

## 1. El artículo — PRIORIDAD ACTUAL

Entregable académico del proyecto de grado. El **anteproyecto V3 es el documento guía del
profesor y NO se edita**; el artículo es el único entregable editable, y es donde se
justifican las desviaciones respecto de la guía.

**Regla de integridad, no negociable:** no hubo pruebas con niños ni comité de ética. El
artículo reporta **validación funcional** (simulación determinista + banco de software), y
lo clínico se enuncia como trabajo futuro. Nunca en pasado lo que no ocurrió. Corolario
operativo: **ninguna cifra del artículo se escribe a mano**; todas salen de
`scripts/experimentos.py` → `docs/evidencia/resultados.json`.

**Fuente única:** `docs/articulo/articulo.md` (Markdown versionable). Se construye con
`./scripts/build_articulo.sh` → `.docx` (para revisión) y `.pdf`, con citas APA 7 resueltas
por citeproc contra `referencias.bib`. El guion **falla si queda una cita sin resolver**.
El anteproyecto `...V3.docx` es solo lectura. Los dos borradores previos se absorbieron y
se borraron (recuperables en `ab69ba6`).

**Hecho (2026-07-09):**

- [x] Unificación en un solo documento (~11 900 palabras, 30 páginas, 4 figuras, 5 tablas).
- [x] Bibliografía: 29 referencias **verificadas una a una en línea**. Detectada una cita
      **fabricada** (IEEE Access 2023 con autores y páginas que no corresponden a su DOI);
      corregidos el apellido de Rodríguez-Timaná y el DOI de Bausela. Descartadas las
      fuentes de divulgación (Scribd, Emooti, Mayo Clinic, Physiopedia, ScienceDirect Topics)
      y toda referencia sin lista de autores confirmada.
- [x] Evidencia nueva medida: jugadores simulados de Memoria y Equilibrio (el borrador solo
      validaba Velocidad), convergencia en los tres modos, verificación estadística Monte
      Carlo (11/11 puntos dentro del IC 95 %), robustez, coste computacional y huella.
- [x] Corregido el hardware inventado del borrador: no hay batería de litio ni tapete de
      material suave (alimentación **solo USB**, caja de acrílico).

- [x] **Figuras de ingeniería (2026-07-09).** Esquemático KiCad rehecho (bloques
      funcionales, cajetín, etiquetas hacia afuera; **netlist idéntico**: 47 nets nodo a
      nodo, verificado, y cotejado con `Config.h` por `circuit-reviewer`). Diagrama de
      bloques con graphviz, leyendo los GPIO de `Config.h`. Simulación ngspice del divisor
      del FSR = **evidencia E9**. Artículo: 33 páginas, 8 figuras, 6 tablas, Anexo A con el
      esquemático completo. Todo regenerable: `scripts/gen_esquematico.py`,
      `scripts/gen_diagrama_bloques.py`, `scripts/experimentos.py`.

**Pendiente:**

- [ ] **Revisión profunda del documento** por el usuario, en varias sesiones, antes del envío.
- [ ] **Wokwi**: no se pudo ejecutar (el token vive en `~/.secrets`, de lectura bloqueada
      para el agente). Su aporte real es limitado: `firmware/diagram.json` solo instancia el
      ESP32, sin periféricos, así que sirve de *smoke* del firmware, no de validación del
      circuito. Si se quiere una figura, hay que ejecutarlo con el token en el entorno.
- [ ] Esquemático **de calidad de publicación** (hilos dibujados, buses, hojas jerárquicas):
      hoy la conectividad se expresa por etiquetas de red, lo cual es correcto y pasa ERC,
      pero un plano con hilos exigiría reescribir `kisch.py`. Decidido dejarlo como anexo.

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

`reposo=0` es compatible con un FSR sano y sin fuerza (R del sensor ≫ 10 kΩ del pull-down
→ nodo ~0 V), así que ese bloque **no discrimina por sí solo**. El valor de reposo del FSR
**no está medido** y no hay datasheet del sensor en `docs/hardware/datasheets/`: no se cite
una magnitud concreta hasta caracterizarlo.

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

**Ojo al depurar:** el `.docx` y el `.pdf` generados del artículo también llevan metadatos.
Y **no** se purgan los generadores de figuras (`kisch.py`, `gen_tapete.py`,
`scripts/gen_*.py`): el artículo afirma que el esquemático y el diagrama se generan con
guiones deterministas, y esa afirmación debe poder comprobarse en el árbol entregado.

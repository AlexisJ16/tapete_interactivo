# Roadmap — estado vigente y próximos pasos

Fuente única del **estado del proyecto** (software, hardware, CI, artículo) y del trabajo
pendiente. `CLAUDE.md` recoge las reglas durables; este documento, lo que cambia.

Mantener siempre la disciplina del proyecto: **TDD**, **una sola fuente de verdad**
(`GameCore`), tests en verde antes de avanzar.

> **PUNTO DE CONTINUACIÓN (2026-07-10).** **No hay deadline externo:** el cliente aprobó el
> trabajo y la fecha queda a criterio del autor.
>
> **Foco actual: HARDWARE.** El artículo (§1) quedó **delegado a un redactor externo**: se le
> entregó todo el material y un paquete de evidencia del software (`docs/evidencia/`). Ya no es
> trabajo nuestro.
>
> **Diagnóstico del hardware RESUELTO (§3):** los 6 sensores FSR están **sanos**; la falla era
> **mecánica** (el acrílico rígido no transmitía la fuerza al FSR). Sin acrílico detectan de
> inmediato (pico ≈4068–4095, reposo 0). **En curso: prueba end-to-end sin acrílico de los 3
> modos** (sensores + LEDs + audio + comunicación). El **CI** (§2) sigue roto y en espera.

**Línea base del software:** `./scripts/run_all_tests.sh` → TODO VERDE (52 casos /
2174 aserciones C++ + 137 pytest); `.venv/bin/pio run -e esp32dev` → SUCCESS. Si algo
está en rojo al empezar, arreglarlo antes de añadir nada. Esta máquina tiene display real
(`DISPLAY=:0` / Wayland): se pueden lanzar el simulador y el dashboard, y generar capturas
con `scripts/demo_visual.py`.

---

## 1. El artículo — DELEGADO A UN REDACTOR EXTERNO

> **Delegado (2026-07-10).** El artículo ya **no es trabajo nuestro**: lo redacta un tercero, a
> quien se le entregó todo el material y un **paquete de evidencia del software** —
> `docs/evidencia/GUIA_EVIDENCIA.md` (índice que responde su pedido punto por punto),
> `docs/articulo/stack-tecnologico.md` (tecnologías y versiones) y `docs/evidencia/ejecucion/`
> (logs, traza del protocolo de los 3 modos, golden vectors 8/8, capturas rotuladas del
> dashboard/simulador, export CSV/PDF, código). Integridad sostenida: toda captura va rotulada
> como software/simulador; no hay evidencia de hardware físico "funcionando". El detalle
> histórico de la auditoría se conserva abajo como referencia para el redactor.

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

- [x] Unificación en un solo documento fuente (`docs/articulo/articulo.md`).
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
      del FSR = **evidencia E9**. Artículo: 8 figuras, 6 tablas, Anexo A con el esquemático
      completo. Todo regenerable: `scripts/gen_esquematico.py`,
      `scripts/gen_diagrama_bloques.py`, `scripts/experimentos.py`.

      > No se anotan aquí páginas ni palabras del `.docx`/`.pdf`: cambian en cada build y
      > su fuente es el documento construido, no este roadmap.

- [x] **Evidencia con un solo generador (2026-07-09).** Se retiraron `generar_evidencia.py`
      y `simulator/evidencia.py` (duplicaban `evidencia_modos.py` con el modo fijo en
      Velocidad, y recomputaban por su cuenta el barrido que ya iba a `resultados.json`).
      La figura de adaptación se dibuja ahora **del mismo dict** que se serializa, así que
      no puede divergir del número publicado; se renombró `E2_adaptacion.png` →
      `E3_adaptacion.png` para casar con la etiqueta E3 del artículo. Retirados los PNG
      huérfanos `E3_niveles.png` y `E4_trayectoria.png` (el artículo no los usaba: los
      sustituyen la Tabla 4 y la Figura 5). Citadas las Tablas 3 y 6, que no se
      referenciaban por número en el cuerpo.

- [x] **Sondeo profundo del artículo (2026-07-09).** Auditoría de punta a punta antes de
      enviarlo a revisión: veracidad, cifras, bibliografía, redacción y rastros de IA.
      Hallazgos corregidos:
      - **Integridad.** El artículo afirmaba que *todas* sus cifras salían de un solo guion:
        falso para los conteos de robustez (salen del código de los tests), la huella de
        recursos (la da el compilador) y la cobertura de la suite. Afirmación acotada a lo
        que es cierto, en Resultados y en «Disponibilidad de la evidencia».
      - **E8 desincronizado.** El texto citaba medianas concretas (≈5 ns, 450–500 ns, ≈6 µs)
        que ya no coincidían con `resultados.json` (6,0 / 669,6 / 8,04). Se **eliminaron** los
        valores puntuales: el bench no es determinista y solo se enuncia como orden de
        magnitud. Además «más de seis órdenes de magnitud» es falso con el máximo observado
        (1059,8 ns → 9,4·10⁵): se rebajó a **cinco**, robusto en todo el rango.
      - **Cobertura.** «135 pruebas en Python» → **137** (medido).
      - **Bibliografía.** Verificadas las 29 entradas contra Crossref/editor. **Ninguna
        fabricada.** Corregidos: `grieco2015down` (Seligsohn *Karen*, no Kate; Schwartz
        *Alison*, no Allison), `degraaf2026latam` (año 2025→**2026**: vol. 28(1) es enero de
        2026), `wibowo2020fsr` (Khoeron *Slamet*, no Sahrul) y `latash2008hypotonia` (su DOI
        `10.3104/reviews.2074` da **404** en doi.org y Crossref → sustituido por la URL del
        editor, que sí resuelve).
      - **Formato APA.** citeproc desplazaba las partículas: «Graaf, G. de», «(Fels et al.)».
        Apellidos protegidos con llaves en el `.bib` → «de Graaf», «van der Fels», «te
        Wierike», «de Mello», «Da Luz». Ojo: la prosa ya decía «van der Fels» y la cita decía
        «Fels» — incoherencia visible solo en el PDF.
      - **Rastros de IA.** Eliminadas las 10 flechas `→` de la prosa, 43 negritas markdown de
        énfasis (se conservan solo los rótulos de entrada de párrafo y las celdas de tabla) y
        las construcciones características: «conviene…», «merece…», «Ahora bien», «Dicho de
        otro modo», «lejos de ser», «aparentemente modesto», antítesis del tipo «no solo
        parece X: hace Y» y «el algoritmo recomienda, el terapeuta decide».
      - **Maquetación.** El esquemático (Figura 8, `height=82%`) flotaba hasta el interior
        de la bibliografía; y el Anexo A estaba antes de las Referencias. Movido el Anexo
        detrás de Referencias y fijada la figura con `float`/`fig-pos="H"` (paquete añadido
        al preámbulo). Orden final: Referencias → Anexo A en página propia.
      - Verificado: 8 figuras y 6 tablas, **todas citadas** por número; E1–E11 coherentes;
        29/29 referencias citadas, ninguna huérfana; sin metadatos ni texto de IA en
        `.docx`/`.pdf`.

**Pendiente antes de someterlo (decisión humana):**

- **Front/back matter que exigen muchas revistas:** declaración de **conflicto de
  intereses**, de **financiación** y **autor de correspondencia** designado. Hoy el artículo
  no los trae. Añadir según pida la revista destino.
- **Las 52 rayas (—):** son incisos legítimos del español, pero es la única simbología que
  un lector escéptico podría asociar a IA por densidad. Pendiente decidir si se hace una
  pasada dirigida (muchas se convierten en comas/paréntesis sin perder nada).
- **Aviso de fondo, no editable:** E10/E11 pendientes → objetivo (iii) parcial; dos fuentes
  MDPI y una de cuartil medio (JASE). Un revisor probablemente preguntará por la validación
  física ausente. Es el estado del proyecto, no un defecto.

**Pendiente:**
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

## 3. Hardware físico — DIAGNÓSTICO RESUELTO; prueba end-to-end en curso

**Estado (2026-07-10): los 6 sensores están sanos; la falla era mecánica, no eléctrica.**

Antecedente (2026-07-08): con el acrílico atornillado, ninguna pisada llegaba al dashboard
(0 `press` con umbral 2000 y 700; en modo calibración los 6 canales daban `act=0` en reposo).
El enlace serie, el firmware y el motor sí funcionaban (llegaban eventos `score`).

**Diagnóstico (2026-07-10), medido en modo calibración `esp32dev_calib`:**

- **Sin el acrílico, los 6 FSR responden de inmediato.** Pisando a fondo: `reposo=0` y `pico`
  entre **4068 y 4095** (≈ fondo de escala del ADC de 4095) en los seis canales. El salto
  reposo→pico es casi total: detección binaria robusta.
- **El riel 3V3 estaba sano** (responden los seis): se descarta el Dupont suelto / ESP32
  desasentado que se sospechaba por el "todos-cero".
- **Causa confirmada: MECÁNICA.** El acrílico rígido atornillado reparte la fuerza en vez de
  concentrarla en la zona activa (~1 cm) del FSR. Con acrílico no detecta; sin acrílico, sí
  (verificado por el autor).
- Umbral sugerido por el firmware: común ~1423, por canal ~1630. `UMBRAL_PISADA` sigue en
  2000, que **ya detecta sin acrílico**; el definitivo se fija con la mecánica final.

**Próxima acción (retomar aquí): prueba end-to-end SIN acrílico**, ya decidida con el autor.
El humano flashea el firmware normal y juega los 3 modos con el dashboard por serial:

```
cd firmware && pio run -e esp32dev -t upload        # firmware del juego (no calib)
.venv/bin/python dashboard/app.py --serial /dev/ttyUSB0
```

- **Velocidad n1**: recorrer los 6 botones (sensor + LED correcto + audio, celda por celda).
- **Equilibrio n3**: coordinación de varios LEDs simultáneos (hasta 4 por patrón).
- **Memoria n1**: secuencia (exhibición de LED + audio + orden).
- Verificar el **mapeo LED↔celda** (que encienda la celda que se pisa) y el audio.

**Pendiente tras la prueba:**
1. **Decidir el acrílico final** (lo decide el autor con la evidencia): mantenerlo con un
   **concentrador de fuerza** (disco/domo rígido centrado sobre cada FSR, entre FSR y acrílico)
   + **recalibrar**, o prescindir de él. Elección declarada: *decidir tras la prueba*.
2. **Fijar `UMBRAL_PISADA` definitivo** con esa mecánica (pisada suave de niño → probablemente
   ~1500 o menos). Editar `Config.h`, reflashear.
3. **Audio:** microSD FAT32 con `/mp3/0001.mp3`..`0004.mp3` (ver `audio/README.md`).
4. **WiFi (opcional):** `cp firmware/src/secrets.h.example firmware/src/secrets.h` para usar
   `--tcp <IP>` en vez de `--serial`.

**El agente nunca flashea ni abre el serial** (lo bloquea `guard-flash.sh`); lo hace el humano
con el skill `/bring-up`. Instrumentos reales: solo multímetro + PC.

**Herramientas:** `scripts/verificar_pisadas.py` da veredicto por celda desde la sesión SQLite
(distingue sensor **mudo** de **stuck-high**). LEDs: sin comando manual; cobertura máxima =
Equilibrio n3 (comprobación visual).

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

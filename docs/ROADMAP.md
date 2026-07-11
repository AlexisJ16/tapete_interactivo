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
> **EL TAPETE FUNCIONA DE PUNTA A PUNTA (2026-07-11).** Los 3 modos corren en hardware real
> —**incluidas las luces de Equilibrio**— y **el audio suena**. La **mecánica quedó decidida**
> (§3): **el acrílico NO va sobre los sensores**; los FSR van arriba del todo y encima solo
> lleva el **vinilo translúcido** del gráfico. Con esa pila, `UMBRAL_PISADA = 2000` detecta.
>
> **Tonos normalizados (2026-07-11):** +3,2–4,0 dB de RMS y energía llevada a 3,1–4,2 kHz,
> **sin subir el volumen del módulo** (que topa en 15 por brownout). Ver §3.
>
> **PRÓXIMA ACCIÓN — la única abierta del hardware: el veredicto del autor en el tapete.**
> Copiar `audio/000X.mp3` a `/mp3/` de la microSD y jugar una sesión de cada modo. Criterio:
> suenan **más fuertes** y **siguen sonando** (sin cortes ni mudez). Si aparecieran cortes o
> silencio, es brownout: bajar `PICO`/`COMPRESION` en `scripts/gen_audio.py` y regenerar —
> **no hay que reflashear**, los tonos viven en la SD.
>
> Después de eso, del proyecto solo quedan el **CI** (§2, roto y en espera) y la **entrega**
> (§5).

**Línea base del software:** `./scripts/run_all_tests.sh` → TODO VERDE (58 casos /
2186 aserciones C++ + 144 pytest); `.venv/bin/pio run -e esp32dev` → SUCCESS. Si algo
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

## 3. Hardware físico — mecánica decidida; los 3 modos y el audio funcionan

> **CIERRE DE LA MECÁNICA (2026-07-11, decidido y probado por el autor).** **El acrílico no
> va sobre los sensores:** la lámina se montó **encima de la tapa plástica** de la caja, y los
> **FSR quedan arriba del todo**; lo único que los cubre es el **vinilo translúcido delgado**
> del gráfico. Probado con un papel encima: **los 3 modos funcionan, incluidas las luces de
> Equilibrio**. Con esta pila, `UMBRAL_PISADA = 2000` detecta bien y **se queda como está**
> (si un niño pisara demasiado flojo, bajarlo a ~1500 en `Config.h` y reflashear).
>
> Queda cerrado, por tanto, todo lo que este apartado listaba como pendiente: la decisión del
> acrílico, el umbral y el **ghosting de LEDs de Equilibrio** (no reaparece; el checklist de
> `docs/hardware/diagnostico-leds-equilibrio.md` se conserva por si volviera).

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

**E2E sin acrílico HECHA (2026-07-10): los 3 modos corren.** La prueba reveló tres detalles de
juego, ya **corregidos en software** (todo en `GameCore`, fuente única; suite verde + firmware
compila). Diseño y plan: `docs/superpowers/specs/2026-07-10-modos-audio-design.md` y
`docs/superpowers/plans/2026-07-10-modos-audio.md`.

1. **Secuencias siempre iguales → variables por partida.** El dashboard enviaba `set_seed` con
   una semilla fija; ahora siembra aleatorio por partida (los tests/golden fijan semilla).
2. **Memoria sin pausa → pausa clara (~1,2 s).** Fase no bloqueante `PAUSA` antes de la 1ª
   exhibición, entre rondas y tras error, para que se vea el primer botón.
3. **Equilibrio "LEDs de más" → aislado como ELÉCTRICO.** La pantalla muestra el patrón correcto
   y GameCore emite exactamente *k* LEDs (verificado en el simulador); la divergencia está por
   debajo de GameCore. Procedimiento de multímetro en `docs/hardware/diagnostico-leds-equilibrio.md`.

**Sistema de audio — FUNCIONA EN HARDWARE (2026-07-11).** 4 tonos de `scripts/gen_audio.py`
(numpy→ffmpeg, MP3 mono 44,1k/128k) en `audio/000X.mp3`: `1` inicio, `2` pisada correcta / cada
LED de la exhibición de Memoria, `3` serie/patrón completado, `4` fin. **La pisada incorrecta no
suena.** En Equilibrio suena **solo al completar** el patrón.

**El silencio tenía DOS causas encadenadas (ambas resueltas):**

1. **HARDWARE — faltaba el desacople.** Sin condensadores, el amplificador (parlante de 4 Ω)
   pide un pico que **hunde el riel de 5 V del USB**: el DFPlayer **se reiniciaba en bucle** al
   reproducir (repetía `microSD ONLINE`), acababa colgado (`TimeOut`; **no revive con el botón
   EN — hay que cortar la alimentación**) y no sonaba nada. Montados **100 µF + 100 nF**
   (VCC-GND del módulo) y **1000 µF** (rieles de 5 V): **0 reinicios** y suena. Síntoma
   documentado en `cableado.md` §7.
2. **FIRMWARE — `begin()` demasiado pronto.** Se llamaba a los 50 ms con timeout de 500 ms, pero
   el módulo tarda **1–3 s** en montar la SD → `audioOk_=false` y el tapete quedaba **mudo toda
   la sesión sin reintentar**. Ahora espera 1,5 s, timeout 1 s y reintenta 3 veces.

**Límite de volumen (verificado en banco):** `cfg::VOLUMEN_AUDIO = 15`. A **30 (máximo) vuelve el
brownout y DEJA DE SONAR** — el parlante de 4 Ω sobre USB no sostiene el pico ni con el desacople.
Para subirlo, ir de a poco (18/20/22) verificando con el entorno **`esp32dev_audio`** (firmware de
diagnóstico: prueba UART → microSD → reproducción y **cuenta los reinicios del módulo**).

### Tonos normalizados (2026-07-11) — HECHO en software, PENDIENTE el veredicto en el tapete

Los tonos sonaban flojos y el volumen del módulo ya topaba, así que la ganancia se buscó **en el
archivo** (`scripts/gen_audio.py`). Diseño:
`docs/superpowers/specs/2026-07-11-normalizacion-audio-design.md`.

**Medido sobre el MP3 decodificado (lo que oye el DFPlayer):**

| id | Antes | Ahora | Ganancia |
|---|---|---|---|
| 1 inicio | 0,54 s · RMS 0,403 · 783 Hz | 0,63 s · RMS 0,590 · 3137 Hz | **+3,3 dB** |
| 2 acierto | 0,12 s · RMS 0,400 · 1567 Hz | 0,25 s · RMS 0,576 · 3136 Hz | **+3,2 dB** |
| 3 ronda | 0,42 s · RMS 0,404 · 1048 Hz | 0,53 s · RMS 0,589 · 4187 Hz | **+3,3 dB** |
| 4 fin | 0,77 s · RMS 0,339 · 1049 Hz | 0,93 s · RMS 0,540 · 4187 Hz | **+4,0 dB** |

Cómo: melodías **transpuestas dos octavas** (2–4 kHz: pico de sensibilidad del oído y mejor
rendimiento del altavoz pequeño; **la única palanca gratis en corriente**), **armónicos** 2f/3f
(brillo), **compresión** `tanh` (sube el RMS sin subir el pico) y **silencio inicial** de 30 ms
(el DFPlayer se come el ataque).

**Dos hallazgos que fijaron el diseño (y que son ahora tests):**

- **El pico se fija midiendo el MP3, no la onda.** A 0,95 el MP3 decodificado llegaba a **1,018**
  (crujido), y el *overshoot* del codificador **no es monótono** (a 0,92 se dispara a 1,107): el
  margen se mide, no se deduce. **`PICO = 0,86`** → decodifican ≤ 0,945.
- **El tono de acierto NO se alarga a 0,5 s** (como pedía el plan viejo): suena en cada pisada y
  en cada LED de la exhibición, y la cadencia mínima de `Config.h` es de **550 ms**
  (`exhibicionOnMs` 300 + `gap` 250). Como el DFPlayer corta la pista en curso, se truncaría y
  sonaría a chasquido. Se queda en **0,22 s** y gana fuerza por frecuencia, no por duración.

**Ojo — "sin más corriente" es solo medio cierto:** gratis es la **frecuencia**; subir pico y RMS
sí pide más potencia (de pico y media). El desacople amortigua picos, no consumo medio. **Por eso
falta el veredicto en el tapete.**

**PENDIENTE (autor):** copiar `audio/000X.mp3` a `/mp3/` de la microSD y jugar una sesión de cada
modo. **No hace falta reflashear** (los tonos viven en la SD). Criterio: suenan más fuertes **y
siguen sonando**. Si aparecen cortes o mudez → es brownout → bajar `PICO`/`COMPRESION` y
regenerar (se conserva la ganancia de frecuencia); si hay duda, `esp32dev_audio` cuenta reinicios
del módulo (0 = sano).

**WiFi (opcional):** `cp firmware/src/secrets.h.example firmware/src/secrets.h` para usar
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

# Diseño: Setup profesional de ingeniería electrónica + planos completos

- **Fecha:** 2026-07-02
- **Proyecto:** Tapete Interactivo Terapéutico (ESP32 · FSR · ULN2803A · DFPlayer)
- **Origen:** triage crítico de los dos documentos de investigación en la raíz
  (`Orden de trabajo…`, `Setup profesional de Claude Code…`) generados por Claude AI
  (chat) a partir de un prompt previo. Este spec es la **decisión final de Claude
  Code** sobre qué implementar y cómo, tras filtrar incoherencias contra la realidad.

## 1. Objetivo

Dejar el proyecto con un **setup profesional de ingeniería electrónica** dentro de
Claude Code y producir los **planos completos del circuito** (esquemático autorado +
validación analógica + simulación de firmware), para **materializar el armado físico**
y **enriquecer el artículo/documento de grado**. Alcance completo, a fondo, sin
recortes. **La calidad manda sobre el tiempo** (orden mandatoria del autor: no se
re-litiga tiempo-vs-alcance).

## 2. Decisiones bloqueadas (no re-litigar)

| Tema | Decisión |
|---|---|
| Alcance | **Todo**: gobernanza CC + ngspice + KiCad autorado + Wokwi + CI + MCP + subagentes + skills + armado + artículo |
| Fuente de verdad de materiales | **`docs/hardware/materiales.md`** (lo que hay es lo que dice) |
| Resistencia de grupos LED | **2.2 kΩ** (6 de las 9× de reserva); ngspice + multímetro fijan la corriente real |
| Compilación firmware | **`.venv/bin/pio`** (PlatformIO Core 6.1.19). Tests GameCore = `g++` directo. Canonizar `pio` para el proyecto (PATH/wrapper) |
| Token Wokwi | `WOKWI_CLI_TOKEN` existe en `~/.secrets`; hay que **relanzar Claude Code desde un shell que lo sourcee** para la Fase 4 |
| KiCad | **10.0.4**, PPA oficial `ppa:kicad/kicad-10.0-releases` |
| SoT eléctrica (corregida) | **`cableado.md`** (geometría/net list/checklist §6/secuencia §7) + **`Config.h`** (pines canónicos). `00_diseno_circuito.md` = diseño/decisiones |

## 3. Incoherencias a podar (Fase 0) — con su origen

Los dos documentos se generaron contra un **snapshot anterior a la reorg del 29-jun**;
por eso varias referencias apuntan a la estructura vieja.

1. **Refs stale al "maestro §8/§9" / `00_diseno_circuito.md` como net list.** Hoy el
   net list, mapa de pines, checklist (§6) y secuencia (§7) viven en **`cableado.md`**.
   → Re-apuntar toda regla/subagente a `cableado.md` + `Config.h`.
2. **Regla de CLAUDE.md invertida.** El doc propone "gana el maestro sobre el código".
   En este proyecto **`Config.h` es la fuente canónica de pines**. → Regla correcta:
   SoT = `cableado.md` (geometría/net) + `Config.h` (pines); en conflicto se **concilia**.
3. **Recomendación "1 R por LED, 110 Ω, comprar 8 más" — RECHAZADA.** No tenemos 110 Ω,
   la premisa "tienes 10" es falsa, y comprar más contradice la decisión del autor. Se
   conserva la **física** (current-hogging, V_CE(sat) Darlington) como comprensión.
4. **Contradicción de cantidad de resistencias (nuestra, no del doc).** `cableado.md`
   §4.3 pedía 6× 1 kΩ para LEDs; `materiales.md` solo tiene 2× 1 kΩ (asignadas). →
   Resuelto: grupos LED = **2.2 kΩ**. Actualizar `cableado.md` §4.3 y textos derivados.
5. **Índice de memoria stale** (`MEMORY.md`): deadline "1-jul" (real 4-jul) y "110 Ω".
   → Corregir punteros.
6. **Componentes inexistentes en el doc** (op-amp MCP6002, analizador lógico): quedan
   como conocimiento de fondo, **no** entran al BOM ni al armado.

> Los **dos documentos de investigación** en la raíz **no se editan** (son insumo del
> autor). Se **consumen** aquí y luego se **archivan** fuera del snapshot de entrega.

## 4. Descomposición en fases (orden por dependencia)

Cada fase habilita a la siguiente y aprovecha lo ya construido.

### Fase 0 — Poda y alineación  [fundacional]
Ejecutar las correcciones §3 (1–6). Editar: `cableado.md` (§4.3 → 2.2 kΩ, y textos de
brillo/corriente), `00_diseno_circuito.md` (§2.1 valor R), `README.md`/`docs/hardware/README.md`
(si citan valor), `MEMORY.md` (punteros). No tocar `Config.h` (pines OK) ni los docs de
investigación.
- **Aceptación:** `grep` no encuentra "1 kΩ" en el contexto de grupos LED ni "§8/§9"
  del maestro; docs internamente consistentes con `materiales.md`; suite sigue verde.

### Fase 1 — Gobernanza y seguridad de Claude Code  [protege el ESP32 único]
- `.claude/settings.json` — **permitir**: `run_all_tests.sh`, `pio run -e esp32dev`
  (compilar), `g++`, `.venv/bin/pytest`, `ngspice -b`, `kicad-cli`, `wokwi-cli`.
  **denegar**: `rm -rf`, cualquier `pio … -t upload`, `esptool`, acceso a
  `/dev/ttyUSB*`/`/dev/ttyACM*`, `pio device monitor`. (Sintaxis del matcher verificada
  contra doc oficial antes de aplicar.)
- `.claude/hooks/guard-flash.sh` (ejecutable) + registro `PreToolUse`/`Bash`: bloquea
  flasheo/serial (exit 2). **Probado**: `pio … -t upload` → bloqueado; `pio run` → pasa.
- Bloque **"Disciplina de hardware"** en `CLAUDE.md` con la SoT **corregida** (§3.2).
- Canonizar `pio` para el proyecto (wrapper/PATH que apunte a `.venv/bin/pio`).
- **Aceptación:** hook demostrado (bloquea upload, permite compilar); permisos activos;
  `pio` invocable sin ruta completa.

### Fase 2 — ngspice  [fija los números antes de soldar]
- Instalar `ngspice`.
- Netlists en `docs/hardware/spice/` con valores **reales**:
  - **Divisor FSR:** `3V3 ─[R_FSR]─ nodo ─[10 kΩ]─ GND`; barrer R_FSR (~250 Ω…10 MΩ);
    tabular V_nodo; confirmar ventana ADC (~150–2450 mV) reposo→pisada.
  - **Grupo LED:** `5V ─[2.2 kΩ]─ (3 LED ‖) ─ [V_CE(sat)≈0.9 V] ─ GND`; corriente por
    grupo y por LED; comparativa informativa 1-R-por-grupo vs 1-por-LED (solo análisis).
- **Aceptación:** ambas corren en batch (`ngspice -b`) y producen tablas numéricas que
  se documentan (informan valor final de R y umbral).

### Fase 3 — KiCad 10 + esquemático autorado COMPLETO  [entregable de planos]
- Instalar KiCad 10.0.4 (PPA oficial). Verificar `kicad-cli version` = 10.0.x y `sch erc -h`.
- Proyecto en `docs/hardware/kicad/` (`tapete.kicad_pro`, `tapete.kicad_sch`).
- **Autorar el esquemático completo** desde el net list de `cableado.md`: ESP32 DevKit,
  6× (FSR + pull-down 10 kΩ) a ADC1, ULN2803A + 6 grupos LED (2.2 kΩ + 3 LED ‖) a 5 V,
  DFPlayer Mini + parlante 4 Ω + serie 1 kΩ + divisor contingente GPIO16, energía 4
  rieles (3V3 arriba / 5V abajo, GND común), desacoples (1000 µF/100 µF/100 nF).
- ERC limpio (`kicad-cli sch erc --exit-code-violations`). Export: **PDF** (figura para
  el artículo), **BOM**, **netlist SPICE**.
- **PCB layout:** decisión al llegar (opcional; el entregable primario es esquemático +
  protoboard).
- **Aceptación:** ERC sin violaciones; PDF/BOM/netlist generados; esquemático coincide
  net-por-net con `cableado.md` y `Config.h`.

### Fase 4 — Wokwi CLI + smoke test + CI
- Instalar `wokwi-cli` (script oficial); verificar `WOKWI_CLI_TOKEN` y `--version`.
- `firmware/wokwi.toml` → `.pio/build/esp32dev/firmware.{bin,elf}`; `diagram.json` mínimo
  (placa ESP32 para humo; periféricos después).
- Smoke test: `pio run -e esp32dev` → `wokwi-cli . --timeout 20000 --expect-text
  "Tapete Interactivo — firmware 1.0.0"` (banner en main.cpp:106; ojo: sale **tras**
  `hw.begin()` que hace ~2 s de timeout del DFPlayer no simulado).
- **CI** (GitHub Actions): `run_all_tests.sh` + `pio run -e esp32dev` + Wokwi CI en push.
- **Aceptación:** smoke test verde; workflow CI verde.

### Fase 5 — MCP + subagentes + skills + registro
- **MCP:** Wokwi (`wokwi-cli mcp`, stdio, hereda token); KiCad (`lamaalrajih/kicad-mcp`,
  uv, `KICAD_SEARCH_PATHS` → `docs/hardware/kicad/`). Verificados con `claude mcp list`.
- **Subagentes** (`.claude/agents/`): `circuit-reviewer` (net vs `Config.h`; cortos
  3V3↔5V; strapping GPIO0/2/5/12/15; ADC en pin correcto), `datasheet-reader`,
  `test-runner` (solo fallos), `firmware-reviewer` (convenciones GameCore).
- **Skills** (`.claude/skills/`): `design-review` (checklist §3.2 del doc), `bring-up`
  (secuencia segura = `cableado.md` §7).
- `docs/hardware/TOOLING.md` — registro del entorno (versiones, comandos, rutas de config).
- **Aceptación:** MCP conectados; subagentes invocables; `TOOLING.md` commiteado.

### Fase 6 — Materialización  [cosecha]
- Guía de armado apoyada en el esquemático KiCad + tablas ngspice + Wokwi.
- Enriquecer el artículo: método (modelo en V, design-review, FMEA ligero, WCCA), nota
  IEC 60601 (uso clínico futuro), figuras del esquemático y tablas de validación.
- **Aceptación:** armado físico verificado con el checklist; artículo con las figuras y
  el marco metodológico integrados.

## 5. Criterios de aceptación globales

- `./scripts/run_all_tests.sh` verde y `pio run -e esp32dev` SUCCESS en todo momento.
- Cero incoherencias entre `materiales.md`, `cableado.md`, `00_diseno_circuito.md`,
  `Config.h` y el esquemático KiCad.
- Toda herramienta responde a su comando de verificación y queda registrada en `TOOLING.md`.
- Solo fuentes oficiales para instalación/sintaxis; nada inventado.

## 6. Riesgos y notas

- **Token no sourceado** en el proceso actual de Claude Code → Fase 4 requiere relanzar
  desde shell con `~/.secrets`. No bloquea Fases 0–3.
- **Wokwi no modela** fuerza del FSR (potenciómetro stand-in) ni el DFPlayer (audio):
  sirve para lógica/protocolo/WiFi-TCP/timing, no para el lazo analógico ni audio.
- **KiCad MCP** es de terceros: se instala con supervisión; el de análisis primero.
- El **snapshot de entrega** ("sin rastros de IA") purga `docs/superpowers/` y limpia
  trazas; el tooling en `.claude/`, `wokwi.toml`, `docs/hardware/kicad|spice/`,
  `TOOLING.md` se conserva por ser infraestructura legítima del proyecto.

## 7. Fuera de alcance (por ahora)

- Op-amp seguidor (MCP6002) y analizador lógico: no están en inventario.
- Certificación IEC 60601 real (solo se cita el marco en el documento).
- Migración a PCB fabricada: opcional, se decide en Fase 3.

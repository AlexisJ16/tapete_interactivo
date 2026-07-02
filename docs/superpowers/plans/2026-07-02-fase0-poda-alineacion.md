# Fase 0 — Poda y alineación · Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (o
> subagent-driven-development). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Dejar los docs del repo y la memoria internamente consistentes con
`materiales.md`, con los grupos LED a **2.2 kΩ**, antes de construir tooling encima.

**Architecture:** Ediciones quirúrgicas sobre los docs de hardware (solo las `1 kΩ`
de grupos LED → `2.2 kΩ`; las `1 kΩ` del DFPlayer intactas) + higiene de la memoria
del proyecto. Sin cambios de código; la suite debe seguir verde.

**Tech Stack:** Markdown; verificación con `grep`; `./scripts/run_all_tests.sh`.

## Global Constraints (verbatim del spec)

- Fuente de verdad de materiales: `docs/hardware/materiales.md`.
- SoT eléctrica: `cableado.md` (geometría/net/checklist §6/secuencia §7) + `Config.h` (pines).
- Grupos LED = **2.2 kΩ** (6 de las 9× de reserva). Corriente exacta → ngspice + multímetro.
- Las `1 kΩ` del DFPlayer (serie RX + divisor GPIO16) **no se tocan**.
- Los dos documentos de investigación en la raíz **no se editan**.
- `./scripts/run_all_tests.sh` y `pio run -e esp32dev` deben seguir verdes.

---

### Task 1: Grupos LED → 2.2 kΩ en todos los docs de hardware del repo

**Files:**
- Modify: `docs/hardware/cableado.md` (L139, L144, L154-156, L203, L217)
- Modify: `docs/hardware/00_diseno_circuito.md` (L19, L26)
- Modify: `docs/hardware/materiales.md` (L24, L78, L80-81)
- Modify: `docs/ROADMAP.md` (L25)
- Modify: `README.md` (L116)

**Interfaces:**
- Produces: docs con "grupo LED = 2.2 kΩ" consistente; base para el net list del
  esquemático KiCad (Fase 3) y las netlists ngspice (Fase 2).

- [ ] **Step 1: `cableado.md` — texto del grupo (L139)**
  - Old: `Por grupo (3 LEDs en paralelo): `5V ─[1 kΩ]─ ánodo` y `cátodo ─ OUTk del ULN`. La`
  - New: `Por grupo (3 LEDs en paralelo): `5V ─[2.2 kΩ]─ ánodo` y `cátodo ─ OUTk del ULN`. La`

- [ ] **Step 2: `cableado.md` — fila de tabla LED1 (L144)**
  - Old: `| LED1 | D4 (c29) | IN1 (pin 1) | 5V→[1 kΩ]→ánodo | OUT1 (pin 18) |`
  - New: `| LED1 | D4 (c29) | IN1 (pin 1) | 5V→[2.2 kΩ]→ánodo | OUT1 (pin 18) |`
  - (Las filas LED2–LED6 dicen "idem": no requieren cambio.)

- [ ] **Step 3: `cableado.md` — nota de brillo (L154-156)**
  - Old: `> **Brillo esperado = tenue pero visible.** Con 1 kΩ desde 5 V vía el ULN, cada LED`
    `> recibe ~0.9 mA (no hay resistencias de valor bajo para más corriente; ver`
    `> `materiales.md` §3). Es lo máximo alcanzable con el inventario. Los LEDs van`
  - New: `> **Brillo esperado = tenue pero visible.** Los 6 grupos usan **2.2 kΩ** (las`
    `> 2× 1 kΩ del inventario van al DFPlayer y al divisor GPIO16; ver `materiales.md` §3).`
    `> Con 2.2 kΩ desde 5 V vía el ULN cada LED recibe **<1 mA** (corriente exacta`
    `> validada en `../spice/`, fase ngspice). Es lo máximo con el inventario. Los LEDs van`

- [ ] **Step 4: `cableado.md` — checklist (L203)**
  - Old: `- [ ] LEDs: polaridad (ánodo a 1 kΩ/5 V, cátodo a OUT del ULN).`
  - New: `- [ ] LEDs: polaridad (ánodo a 2.2 kΩ/5 V, cátodo a OUT del ULN).`

- [ ] **Step 5: `cableado.md` — secuencia (L217)**
  - Old: `   1 kΩ, ánodo, cátodo→OUT, IN←GPIO por puente lateral. Probar encendido (brillo`
  - New: `   2.2 kΩ, ánodo, cátodo→OUT, IN←GPIO por puente lateral. Probar encendido (brillo`

- [ ] **Step 6: `00_diseno_circuito.md` — tabla de subsistemas (L19)**
  - Old: `| Iluminación | 18× LED blanco (6 grupos de 3) + 6× 1 kΩ + **1× ULN2803A** | Conmutación a 5 V |`
  - New: `| Iluminación | 18× LED blanco (6 grupos de 3) + 6× 2.2 kΩ + **1× ULN2803A** | Conmutación a 5 V |`

- [ ] **Step 7: `00_diseno_circuito.md` — decisión congelada #1 (L26)**
  - Old: `1. **LEDs con ULN2803A a 5 V**, un grupo de 3 en paralelo por botón, **1 kΩ** en`
  - New: `1. **LEDs con ULN2803A a 5 V**, un grupo de 3 en paralelo por botón, **2.2 kΩ** en`

- [ ] **Step 8: `materiales.md` — destino de la fila 2.2 kΩ (L24)**
  - Old: `| 12 | R 2.2 kΩ | 1/4 W | 9 | comprado | Reserva / uso libre |`
  - New: `| 12 | R 2.2 kΩ | 1/4 W | 9 | comprado | **6× serie de grupo LED** (1 por grupo) + 3 reserva |`

- [ ] **Step 9: `materiales.md` — bullet de asignación (L78)**
  - Old: `  - **9 × 2.2 kΩ** → reserva.`
  - New: `  - **6 × 2.2 kΩ** → serie de los 6 grupos LED (1 por grupo); **3 × 2.2 kΩ** de reserva.`

- [ ] **Step 10: `materiales.md` — nota de brillo (L80-81)**
  - Old: `  bajo (~15–47 Ω) para llevar los LEDs a corriente plena. Con la resistencia más`
    `  baja disponible (1 kΩ) en serie desde 5 V vía el ULN, cada LED recibe ~0.9 mA:`
  - New: `  bajo (~15–47 Ω) para llevar los LEDs a corriente plena. Las 2× 1 kΩ están`
    `  asignadas al DFPlayer y al divisor GPIO16, así que los 6 grupos LED usan **2.2 kΩ**`
    `  (6 de las 9 de reserva). Cada LED recibe **<1 mA** (exacto: ngspice + multímetro):`

- [ ] **Step 11: `ROADMAP.md` — checklist LED (L25)**
  - Old: `      pero visible** con 1 kΩ (máximo alcanzable con el inventario; `materiales.md` §3).`
  - New: `      pero visible** con 2.2 kΩ (máximo alcanzable con el inventario; `materiales.md` §3).`

- [ ] **Step 12: `README.md` — descripción de hardware (L116)**
  - Old: `(3 por botón, a 5 V vía 1× ULN2803A; brillo tenue con 1 kΩ) · DFPlayer Mini +`
  - New: `(3 por botón, a 5 V vía 1× ULN2803A; brillo tenue con 2.2 kΩ) · DFPlayer Mini +`

- [ ] **Step 13: Verificar que NO queda `1 kΩ` en contexto LED y SÍ en DFPlayer**

  Run: `grep -rniE "1 ?kΩ" docs/ README.md | grep -viE "DFPlayer|GPIO16|divisor|serie|TX2|RX|spec"`
  Expected: **sin resultados** (todas las `1 kΩ` restantes son del DFPlayer/divisor).

  Run: `grep -rniE "2\.2 ?kΩ" docs/hardware/cableado.md docs/hardware/00_diseno_circuito.md`
  Expected: aparece en la sección de grupos LED de ambos.

- [ ] **Step 14: Verificar suite verde (los docs no afectan tests, es sanity)**

  Run: `./scripts/run_all_tests.sh`
  Expected: TODO VERDE (43 casos C++ + 36 pytest).

- [ ] **Step 15: Commit**

  ```bash
  git add docs/hardware/cableado.md docs/hardware/00_diseno_circuito.md docs/hardware/materiales.md docs/ROADMAP.md README.md docs/superpowers/
  git commit -m "docs(hw): alinea grupos LED a 2.2 kΩ (materiales.md como fuente de verdad) + spec/plan setup"
  ```

---

### Task 2: Higiene de memoria (LED 2.2 kΩ, deadline 4-jul, mandato full-scope)

**Files:** (memoria del proyecto — fuera del repo git, sin commit)
- Modify: `MEMORY.md` (índice, L1-L2)
- Modify: `tapete-interactivo-estado.md` (L32, L99, y sección de próxima acción)
- Modify: `tapete-materiales-hw.md` (razonamiento LED, ~L52-57)
- Modify: `tapete-protoboard-fuente-verdad.md` (L71-72)
- Create: `tapete-setup-ingenieria.md` (mandato full-scope + spec/plan + 6 fases)

**Interfaces:**
- Produces: memoria coherente con el estado real; puntero al spec/plan de este epic.

- [ ] **Step 1: `MEMORY.md` L1 — deadline y alcance**
  - Old hook: `DEADLINE 1-jul ... se entrega 2026-07-01; el plazo domina el alcance, recortar SP2 al mínimo demostrable`
  - New hook: `DEADLINE 4-jul (prórroga); MANDATO 2026-07-02: alcance COMPLETO a fondo, la calidad manda sobre el tiempo (no recortar)`

- [ ] **Step 2: `MEMORY.md` L2 — valor LED**
  - Old: `LEDs decididos (1×110Ω/grupo + ULN2803A)`
  - New: `LEDs decididos (1×2.2 kΩ/grupo + ULN2803A)`

- [ ] **Step 3: `MEMORY.md` — añadir puntero al nuevo epic**
  - Add line: `- [Tapete — setup ingeniería + planos](tapete-setup-ingenieria.md) — mandato full-scope: gobernanza CC + ngspice + KiCad autorado + Wokwi/CI + MCP/subagentes; spec/plan en docs/superpowers/`

- [ ] **Step 4: `tapete-interactivo-estado.md` — L32 valor LED**
  - Old: `LEDs a 5 V vía ULN con **1 kΩ → brillo tenue pero visible**`
  - New: `LEDs a 5 V vía ULN con **2.2 kΩ → brillo tenue** (las 2× 1 kΩ van al DFPlayer; ngspice fija la corriente)`

- [ ] **Step 5: `tapete-interactivo-estado.md` — L99 nota histórica**
  - Old fragment: `10× 110 Ω = 1 por grupo`
  - New fragment: `grupos LED a 2.2 kΩ (1 por grupo)`

- [ ] **Step 6: `tapete-interactivo-estado.md` — reescribir "PRÓXIMA ACCIÓN"**
  - Reemplazar el bloque de próxima acción por: epic de setup de ingeniería en curso
    (spec `docs/superpowers/specs/2026-07-02-...`; plan Fase 0 en `plans/`); Fase 0 =
    poda/alineación (LED 2.2 kΩ); siguen Fases 1–6 (gobernanza → ngspice → KiCad → Wokwi/CI → MCP → armado/artículo).

- [ ] **Step 7: `tapete-materiales-hw.md` — razonamiento de brillo (~L52-57)**
  - Actualizar de "1 kΩ → ~0.9 mA/LED" a "grupos LED = 2.2 kΩ (las 1 kΩ van al
    DFPlayer); <1 mA/LED, exacto por ngspice+multímetro". Mantener L34-35 (DFPlayer 1 kΩ).

- [ ] **Step 8: `tapete-protoboard-fuente-verdad.md` — L71-72**
  - Old: `el brillo se fija por prueba empírica con 1 kΩ`
  - New: `el brillo se fija con 2.2 kΩ (ngspice + multímetro)`

- [ ] **Step 9: Crear `tapete-setup-ingenieria.md`**
  - Frontmatter `type: project`, `volatility: volatile`, `review_after: 2026-08-15`.
  - Cuerpo: mandato full-scope (no re-litigar tiempo); spec+plan en `docs/superpowers/`;
    LED=2.2 kΩ; `pio` = `.venv/bin/pio` 6.1.19; KiCad 10.0.4; token en `~/.secrets`;
    6 fases por dependencia. Enlazar `[[tapete-interactivo-estado]]`, `[[tapete-materiales-hw]]`.

- [ ] **Step 10: Verificar coherencia de memoria**
  - Run: `grep -rniE "110|1-jul|1 ?kΩ.*LED|LED.*1 ?kΩ" ~/.claude/projects/-home-alexis-code-tapete-interactivo/memory/*.md`
  - Expected: sin `110`/`1-jul` como valor vigente (solo notas históricas explícitas); LED = 2.2 kΩ.

---

## Self-Review

- **Cobertura del spec §3:** item 4 (resistencias) → Task 1; item 5 (memoria) → Task 2;
  items 1/3/6 (refs §8/§9, 110Ω, componentes inexistentes) → sin edición (verificado: no
  hay refs stale en nuestros docs; el resto son decisiones capturadas en el spec); item 2
  (regla CLAUDE.md) → Fase 1 (se crea correcta allí).
- **Placeholders:** ninguno; cada step trae old/new exacto.
- **Consistencia:** "2.2 kΩ" uniforme; "1 kΩ" solo persiste en contexto DFPlayer (Step 13 lo verifica).

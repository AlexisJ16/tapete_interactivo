# Fase 1 — Gobernanza y seguridad de Claude Code · Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Checkbox (`- [ ]`) steps.

**Goal:** Proteger el ESP32 único (bloqueo real de flasheo/serial desde el agente) y dejar el
proyecto con permisos, disciplina de hardware y `pio` canónico, antes de instalar más tooling.

**Architecture:** `.claude/settings.json` (permisos allow/deny + registro del hook) + hook bash
`guard-flash.sh` que inspecciona el comando por regex y bloquea con exit 2 + bloque de disciplina
de hardware en `CLAUDE.md` (SoT corregida) + `pio` canónico (`.venv/bin/pio`).

**Tech Stack:** Claude Code hooks/permissions (sintaxis verificada en code.claude.com/docs), bash, jq.

## Global Constraints (verbatim del spec)

- SoT eléctrica: `cableado.md` (geometría/net/§6 checklist/§7 secuencia) + `Config.h` (pines canónicos).
- Regla correcta (NO la del doc de investigación): en conflicto se **concilia**; Config.h es fuente de pines.
- Un solo ESP32, solo por USB: el agente **nunca** flashea ni abre serial (lo hace el humano).
- Compilación: `.venv/bin/pio` (PlatformIO 6.1.19); tests GameCore = g++.
- Solo fuentes oficiales; sintaxis de hooks/permisos verificada contra doc oficial (2026-07-02).

## Sintaxis verificada (fuente: code.claude.com/docs/en/{permissions,hooks,settings})

- `permissions`: `allow`/`deny`/`ask`; matcher `Bash(cmd)` exacto, `Bash(cmd *)` prefijo con word
  boundary, `Bash(cmd*)` sin boundary. Precedencia **deny → ask → allow**, primer match gana; los
  `deny` se **mergen** entre niveles y ganan sobre cualquier `allow`.
- Hook: `hooks.PreToolUse[] = {matcher, hooks:[{type:"command", command, args, timeout}]}`.
  Input por stdin JSON; comando en `.tool_input.command`. **Exit 2 = bloquea** y stderr → Claude.
  Ruta con `${CLAUDE_PROJECT_DIR}` en exec form (`args:[]`).

---

### Task 1: Hook `guard-flash.sh` (bloqueo real, unit-testeado)

**Files:** Create: `.claude/hooks/guard-flash.sh`

- [ ] **Step 1: Crear el script** (regex que cubre upload/esptool/serial/`/dev/tty`/monitor;
  bloquea con exit 2, permite con exit 0).
- [ ] **Step 2: `chmod +x .claude/hooks/guard-flash.sh`**
- [ ] **Step 3: Unit test — comandos SEGUROS deben dar exit 0**
  ```bash
  for c in "pio run -e esp32dev" ".venv/bin/pio run -e esp32dev" "git status" "ls" \
           "./scripts/run_all_tests.sh" "pio device list" "ngspice -b x.cir"; do
    printf '{"tool_input":{"command":"%s"}}' "$c" | .claude/hooks/guard-flash.sh; \
    echo "exit=$? <- $c"; done
  ```
  Expected: `exit=0` en todos.
- [ ] **Step 4: Unit test — comandos de FLASHEO/SERIAL deben dar exit 2**
  ```bash
  for c in "pio run -e esp32dev -t upload" "pio run && pio run -t upload" \
           "esptool.py --port /dev/ttyUSB0 write_flash 0x0 fw.bin" \
           "pio device monitor -b 115200" "cat /dev/ttyACM0"; do
    printf '{"tool_input":{"command":"%s"}}' "$c" | .claude/hooks/guard-flash.sh >/dev/null 2>&1; \
    echo "exit=$? <- $c"; done
  ```
  Expected: `exit=2` en todos.

### Task 2: `.claude/settings.json` (permisos + registro del hook)

**Files:** Create: `.claude/settings.json`
- [ ] **Step 1: Crear** con `permissions.allow` (compilar/tests/ngspice/kicad-cli/wokwi-cli),
  `permissions.deny` (upload/esptool/rm -rf), y `hooks.PreToolUse` matcher `Bash` → guard-flash.
- [ ] **Step 2: Validar JSON:** `jq . .claude/settings.json` → sin error.
- [ ] Nota: el hook se activa en la **próxima sesión** de Claude Code (los hooks cargan al inicio);
  el script ya quedó unit-testeado en Task 1.

### Task 3: Bloque "Disciplina de hardware" en `CLAUDE.md`

**Files:** Modify: `CLAUDE.md` (nueva sección tras "Convenciones (respetar)")
- [ ] **Step 1:** Insertar el bloque con la SoT **corregida** (`cableado.md` + `Config.h`; conciliar
  en conflicto), prohibición de inventar hardware, unidades, frontera 3V3/5V, ESP32 único + hook,
  instrumentos (multímetro/ngspice/Wokwi), compilación con `.venv/bin/pio`.

### Task 4: `pio` canónico para el proyecto

**Files:** Create: `scripts/pio` (wrapper) ; documentar en CLAUDE.md/TOOLING
- [ ] **Step 1:** Wrapper `scripts/pio` → `exec "$(dirname "$0")/../.venv/bin/pio" "$@"` + chmod +x.
- [ ] **Step 2:** Verificar `scripts/pio --version` → PlatformIO Core 6.1.19.
- [ ] (PATH interactivo: ofrecer al usuario alias/direnv; no tocar ~/.zshrc sin su OK.)

### Task 5: Verificar + commit

- [ ] **Step 1:** `./scripts/run_all_tests.sh` → TODO VERDE.
- [ ] **Step 2:** Commit `.claude/`, `CLAUDE.md`, `scripts/pio`, `docs/superpowers/`.

## Self-Review
- Cubre spec Fase 1 (permisos, hook, CLAUDE.md hw, pio). Hook unit-testeado antes de registrar.
- Sin placeholders; sintaxis verificada contra doc oficial. SoT corregida (no la regla invertida del doc).

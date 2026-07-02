# TOOLING — Entorno de ingeniería del Tapete Interactivo

Fuente de verdad del **tooling de hardware/firmware**: versiones, comandos de uso,
rutas de config y registro de los MCP/subagentes. Complementa las fuentes eléctricas
(`cableado.md` + `Config.h`), no las reemplaza.

## Versiones instaladas (2026-07-02)

| Herramienta | Versión | Notas |
|---|---|---|
| PlatformIO (`pio`) | 6.1.19 | En el venv del proyecto: `.venv/bin/pio` (wrapper `scripts/pio`). |
| wokwi-cli | 0.26.1 | En `~/bin`. Simulador ESP32 + smoke/CI. Token `WOKWI_CLI_TOKEN` en `~/.secrets`. |
| kicad-cli | 10.0.4 | PPA `ppa:kicad/kicad-10.0-releases`. ERC + exports. |
| ngspice | 42 | apt. Validación analógica en batch. |
| uv | 0.11.8 | Gestor Python para el KiCad MCP. |
| Node.js | v24.14.1 | NVM. Runtime de wokwi-cli y de los MCP npx. |

## Comandos de uso

```bash
# TODOS los tests (C++ doctest + libgamecore.so + pytest) — fuente de verdad
./scripts/run_all_tests.sh

# Firmware ESP32 (solo compila; NO flashea — el flasheo lo hace el humano)
.venv/bin/pio run -e esp32dev

# Wokwi: smoke test del firmware (banner de boot por serial)
source ~/.secrets && wokwi-cli firmware --timeout 20000 --expect-text "Tapete Interactivo"

# KiCad: ERC significativo (exit != 0 si hay violaciones) + exports
kicad-cli sch erc --severity-all --exit-code-violations \
  -o docs/hardware/kicad/erc.rpt docs/hardware/kicad/tapete.kicad_sch
kicad-cli sch export netlist --format spice \
  -o docs/hardware/kicad/tapete.cir docs/hardware/kicad/tapete.kicad_sch
kicad-cli sch export pdf -o docs/hardware/kicad/tapete.pdf docs/hardware/kicad/tapete.kicad_sch
kicad-cli sch export bom  -o docs/hardware/kicad/tapete-bom.csv docs/hardware/kicad/tapete.kicad_sch

# ngspice: validación analógica en batch
ngspice -b docs/hardware/spice/divisor_fsr.cir
ngspice -b docs/hardware/spice/grupo_led.cir
```

## Rutas de config

| Config | Ruta | Qué es |
|---|---|---|
| Wokwi | `firmware/wokwi.toml` + `firmware/diagram.json` | apunta a `.pio/build/esp32dev/` + placa devkit-v1 |
| KiCad | `docs/hardware/kicad/` | `tapete.kicad_sch/pro`, exports (`tapete.pdf/-bom.csv/.cir`), `erc.rpt` |
| ngspice | `docs/hardware/spice/` | `divisor_fsr.cir`, `grupo_led.cir` |
| Datasheets | `docs/hardware/datasheets/` | PDFs de componentes (destino del subagente `datasheet-reader`) |

> Los `docs/hardware/kicad/{kisch.py,gen_tapete.py,__pycache__}` son andamiaje de
> autoría del esquemático (se purgan del snapshot de entrega).

## MCP servers (Claude Code)

Registrados con `claude mcp add`. Verificar con `claude mcp list`.

### Wokwi MCP — scope `local` (wrapper; registro no commiteado)
```bash
claude mcp add wokwi -s local -- /home/alexis/code/tapete_interactivo/scripts/wokwi-mcp.sh
```
- `scripts/wokwi-mcp.sh` (commiteado) sourcea `~/.secrets` y ejecuta `wokwi-cli mcp`,
  así **el token está garantizado** sin depender de cómo se lanzó CC. WHY: se verificó que
  el proceso de CC a menudo **NO** hereda `WOKWI_CLI_TOKEN` aunque el humano lo sourceara
  antes (por eso NO se usa `.mcp.json` project con `${WOKWI_CLI_TOKEN}`: avisaba `Missing
  environment variables` y quedaba `Pending approval`). Scope local = sin aprobación.
- Verificado `✔ Connected` **sin** warning de env. El pin IPv4 (abajo) cubre su red.

### KiCad MCP — scope `local` (no commiteado; máquina-específico)
```bash
# Instalación (una vez): repo en ~/code/tools/kicad-mcp
git clone https://github.com/lamaalrajih/kicad-mcp.git ~/code/tools/kicad-mcp
make -C ~/code/tools/kicad-mcp install          # uv sync --group dev → .venv
# Registro:
claude mcp add kicad -s local \
  -e KICAD_SEARCH_PATHS=/home/alexis/code/tapete_interactivo/docs/hardware/kicad \
  -- /home/alexis/code/tools/kicad-mcp/.venv/bin/python /home/alexis/code/tools/kicad-mcp/main.py
```
- Servidor de análisis de KiCad (usa `kicad-cli`). Verificado `✔ Connected`.

## Subagentes y skills (`.claude/`)

| Tipo | Nombre | Función |
|---|---|---|
| agente | `circuit-reviewer` | netlist (`cableado.md`) vs `Config.h`; cortos 3V3/5V, strapping, ADC |
| agente | `datasheet-reader` | extrae specs de `docs/hardware/datasheets/*.pdf` a tablas |
| agente | `test-runner` | corre `run_all_tests.sh`, devuelve solo fallos |
| skill | `design-review` | checklist de revisión eléctrica (despacha `circuit-reviewer`) |
| skill | `bring-up` | secuencia segura de encendido + calibración umbral FSR |

## Red — fix IPv4 para Wokwi (config LOCAL de máquina)

La ruta IPv6 de esta máquina a los endpoints anycast de wokwi.com hace **black-hole
de PMTU** (paquetes >~1448 B se descartan; el ICMPv6 PTB está filtrado) → wokwi-cli se
cuelga subiendo el firmware. **Fix persistente:** pin de wokwi.com→IPv4 en `/etc/hosts`
(bloque `# BEGIN/END wokwi-ipv4-pin`). El resto del IPv6 queda intacto. Refrescar IPs si
cambian: `getent ahostsv4 wokwi.com`. **CI en GitHub Actions no lo necesita** (red limpia).

## CI

`.github/workflows/ci.yml` en cada push/PR: job de tests (`run_all_tests.sh`) ‖ job de
firmware (`pio run -e esp32dev`) + smoke Wokwi (Secret `WOKWI_CLI_TOKEN`). Ver run verde
`28613746034`.

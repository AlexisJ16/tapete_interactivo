# Esquemático KiCad — Tapete Interactivo

Esquemático eléctrico completo del Tapete (KiCad 10.0.4), con ERC **significativo**
en verde y exports para el artículo. Cruza net-por-net con las fuentes de verdad:
`docs/hardware/cableado.md` §1/§4 + `firmware/lib/GameCore/Config.h`.

## Archivos

| Archivo | Qué es |
|---|---|
| `tapete.kicad_sch` | Esquemático (abrir con `eeschema`). Auto-layout: reordenar en la GUI si se desea. |
| `tapete.kicad_sym` | Librería de símbolos custom (ESP32 DevKit 30-pin, DFPlayer Mini), tipados. |
| `sym-lib-table`, `tapete.kicad_pro` | Proyecto KiCad (registran la lib `tapete`). |
| `tapete.pdf` | Plano exportado (para el artículo). |
| `tapete-bom.csv` | Lista de materiales. |
| `tapete.cir` | Netlist SPICE (artefacto; requiere modelos para simular). |
| `kisch.py`, `gen_tapete.py` | **Andamiaje**: generador que autora el `.kicad_sch`. Ver abajo. |

## Regenerar

```bash
# Proyecto + esquemático completo:
.venv/bin/python docs/hardware/kicad/gen_tapete.py --stage all --project
# Etapas intermedias (build incremental): esp32 | fsr | uln | dfplayer
```

Exports y verificación:

```bash
cd docs/hardware/kicad
kicad-cli sch erc --severity-all --exit-code-violations tapete.kicad_sch   # 0 infracciones
kicad-cli sch export pdf     -o tapete.pdf      tapete.kicad_sch
kicad-cli sch export bom     -o tapete-bom.csv  tapete.kicad_sch
kicad-cli sch export netlist --format spice -o tapete.cir tapete.kicad_sch
```

## Método (por qué es fiable)

- **Símbolos tipados**, no conectores genéricos: `power_in` (3V3/5V/GND), `input`
  (GPIO34-39 solo-entrada de los FSR), `bidirectional` (GPIO de LED/UART),
  `open_collector` (salidas del ULN2803A). El ESP32 y el DFPlayer son símbolos custom
  con esos tipos; ULN2803A/R/LED/C son stock de KiCad.
- **ERC significativo, no trivial:** power symbols `+5V/+3V3/GND` + `PWR_FLAG` en cada
  riel → el ERC detecta cortos 3V3↔5V, pines flotantes y nets sin fuente. Se validó
  que el ERC se pone **rojo** ante una falla deliberada (corto 3V3↔5V) antes de
  aceptar el verde (TDD del esquemático).
- **Conectividad por net labels** (los nombres = net list de `cableado.md`).
- **Autoría programática** (no hay API oficial de Python para esquemáticos): el
  generador emite el S-expression y se valida con `kicad-cli`. Punto clave:
  el espacio del símbolo es Y-arriba y el del esquemático Y-abajo → el punto de
  conexión absoluto de un pin es `(Sx + px, Sy − py)`. UUIDs deterministas
  (salida reproducible byte a byte).

## Notas

- **Brillo LED (gate arrastrado de Fase 2):** ~0.19 mA/LED con 2.2 kΩ es marginal; la
  prueba empírica de brillo (`cableado.md` §7 paso 4) es un gate real antes del armado.
- **GPIO16 (contingencia):** si el TX del DFPlayer mide ~5 V, intercalar divisor 1k+2k
  en `DF_TX` (`cableado.md` §4.4). El esquemático representa el caso nominal (3.3 V, directo).
- **Andamiaje:** `kisch.py`/`gen_tapete.py` son la herramienta de autoría, no el entregable
  final; se purgan del snapshot de entrega (como `docs/superpowers/`).

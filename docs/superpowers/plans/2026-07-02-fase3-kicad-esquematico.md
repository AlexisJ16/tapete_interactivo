# Fase 3 — Esquemático KiCad autorado · Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Construir
> INCREMENTAL: ERC + PDF tras cada subsistema (TDD del esquemático). No autorar todo y
> validar al final.

**Goal:** Producir `docs/hardware/kicad/tapete.kicad_sch` — esquemático completo, con ERC
**significativo** en verde, y exports PDF (plano para el artículo) + BOM + netlist SPICE.

**Architecture:** Autoría programática de un `.kicad_sch` (KiCad 10, formato v20260101).
Símbolos **tipados** (no conectores genéricos) para que el ERC valide de verdad; conectividad
por **net labels** (los nombres = net list de `cableado.md`); power symbols + PWR_FLAG para el
árbol de potencia. Layout auto (funcional, no hand-tidy; se puede reordenar en GUI después).

**Tech Stack:** kicad-cli 10.0.4 (erc/export), símbolos de `/usr/share/kicad/symbols/`,
generador en Python (`.venv/bin/python`).

## Global Constraints

- Net list y valores = `docs/hardware/cableado.md` + `Config.h` (FSR pull-down 10k; grupos LED
  **2.2k**; DFPlayer serie 1k; divisor GPIO16 1k+2k contingente). El esquemático **cruza** con
  esas fuentes; si algo no cuadra, se detiene y concilia (no se inventa).
- **ERC significativo, no trivial**: power symbols (+5V/+3V3/GND) + PWR_FLAG; tipos de pin
  correctos. Un ERC que pasa "por vacío" (símbolos passive) es una señal de que los símbolos
  son demasiado genéricos → corregir.
- Fronteras: 3V3 (sensores) y 5V (LED/audio) separados; ERC debe poder gritar si se tocan.

## Decisiones de símbolo (tipos eléctricos)

- **ESP32 DevKit (custom, si no hay stock):** `power_in` para 3V3/5V(VIN)/GND; `input` para
  GPIO34-39 (solo-entrada, los 6 FSR usan estos vía ADC1); `bidirectional` para los GPIO de
  LED (4,5,18,19,21,23) y UART (16,17); marcar `no_connect` los pines sin usar del header.
- **ULN2803A:** `Transistor_Array:ULN2803A` (stock, pines tipados). IN1-6 ← GPIO LED; OUT1-6 →
  cátodos de grupo; pin 9 GND, pin 10 COM→+5V.
- **LED blanco:** `Device:LED` ×3 por grupo (o 1 con nota "×3 ‖"); **R serie 2.2k** `Device:R`.
- **FSR:** `Device:R_Potentiometer`/`Device:R_Variable` (2-3 pines) o custom 2-pin; **pull-down
  10k** `Device:R` a GND; nodo → GPIO ADC.
- **DFPlayer (custom 8-16 pin tipado):** VCC(power_in 5V), GND, RX(input)←1k←TX2(17), TX(output)
  →RX2(16), SPK1/SPK2(passive)→`Device:Speaker` 4Ω. microSD nota.
- **Desacoples:** `Device:C_Polarized` 1000µF/100µF + `Device:C` 100nF en los buses.
- **Power symbols:** `power:+5V`, `power:+3V3`, `power:GND` + `power:PWR_FLAG` en fuentes.

## Tasks (incremental — ERC + PDF tras cada una)

### Task 0: Pre-flight
- [ ] Confirmar con grep si existe símbolo ESP32 **WROOM-32 / DevKitC** en `RF_Module.kicad_sym`
  y `MCU_Espressif.kicad_sym` (nombres completos). Si existe uno con los 30 pines y tipos
  correctos, usarlo; si no, autorar símbolo custom.
- [ ] Crear `docs/hardware/kicad/` con `sym-lib-table` (custom lib) y `tapete.kicad_pro`.

### Task 1: ESP32 + rieles de potencia (esqueleto ERC)
- [ ] Símbolo ESP32 (stock o custom) + power symbols +5V/+3V3/GND + PWR_FLAG.
- [ ] `kicad-cli sch erc` → limpio; `export pdf` → abre. (Prueba de formato antes de escalar.)

### Task 2: Banco de 6 FSR
- [ ] 6× (FSR + 10k pull-down) a GPIO36/39/34/35/32/33 vía net labels; verificar que son los
  `input`-only. ERC + PDF.

### Task 3: ULN2803A + 6 grupos LED
- [ ] ULN2803A; 6× (2.2k + LED(s)) 5V→OUT; IN←GPIO4/5/18/19/21/23. ERC + PDF.

### Task 4: DFPlayer + parlante + desacoples
- [ ] DFPlayer (VCC 5V, GND, RX←1k←TX2/17, TX→RX2/16, SPK→parlante 4Ω) + caps 1000µF/100µF/100nF.
  ERC + PDF.

### Task 5: Exports finales + commit
- [ ] `kicad-cli sch erc --exit-code-violations` → 0 infracciones.
- [ ] `kicad-cli sch export pdf/bom` + `export netlist --format spice`.
- [ ] Cruzar net-por-net contra `cableado.md` §1/§4 y `Config.h`. Commit.

## Notas
- Layout auto será funcional, no hand-tidy; el usuario puede reordenar en la GUI de KiCad.
- **Gate de brillo (arrastrado de Fase 2):** ~0.19 mA/LED es marginal; la prueba empírica de
  brillo (`cableado.md` §7 paso 4) es un **gate real** antes del armado final, no un trámite.

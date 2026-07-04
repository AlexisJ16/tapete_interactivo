---
name: design-review
description: Checklist de revisión eléctrica del Tapete Interactivo. Úsalo antes de energizar, tras cambiar el cableado, o al preparar la figura del circuito para el artículo. Coteja net list vs Config.h y busca cortos 3V3/5V, pines strapping y ADC mal asignados.
user-invocable: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
---

# design-review — Revisión eléctrica del Tapete

Revisión sistemática del circuito contra las **fuentes de verdad**. No inventes
pines ni valores; si un dato no está, márcalo **DESCONOCIDO** y pregunta.

## Fuentes de verdad
- `firmware/lib/GameCore/Config.h` — mapa de pines **canónico** (fuente de pines).
- `docs/hardware/cableado.md` — geometría (§1), net list (§4.2), ruteo Fila J (§3, Paso 1.3),
  arquitectura de potencia (§1.3 y §3, Paso 2), checklist multímetro (§5), armado paso a paso (§3).
- `docs/hardware/00_diseno_circuito.md` — decisiones congeladas (§2).
- `docs/hardware/materiales.md` — BOM y valores.

## Cómo ejecutar la revisión
Para una pasada exhaustiva y aislada, **despacha el subagente `circuit-reviewer`**
(Task) — devuelve hallazgos por severidad sin cargar este hilo. Si la haces inline,
sigue este checklist:

1. **Coherencia de pines:** cada pin de la net list de `cableado.md` coincide con
   `Config.h`. Si discrepan → HALLAZGO alto; **Config.h es la fuente**, se concilia.
2. **Frontera 3V3/5V:** los dos rieles `+` NUNCA puenteados (§1.3). Todo cruce del
   canal central justificado. Corto 3V3↔5V = CRÍTICO.
3. **FSR en ADC1** (GPIO32–39): ADC2 se cae con WiFi. FSR en ADC2 = HALLAZGO.
4. **Strapping** (GPIO0/2/5/12/15): sin cargas que alteren el boot (contingencia
   conocida: LED2→GPIO22 por GPIO5).
5. **Input-only** (GPIO34/35/36/39): válidos para FSR, no para manejar LED/ULN.
6. **Prohibidos** GPIO6–11 (flash). **DFPlayer:** medir TX antes de GPIO16.
7. **GND común:** rieles `−` unidos.

## Salida
Hallazgos ordenados por severidad con archivo:línea y corrección citando la fuente,
o "revisión limpia" + qué se verificó. Unidades siempre explícitas (V, mA, Ω).

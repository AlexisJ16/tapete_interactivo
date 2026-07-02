# Datasheets de componentes

Directorio para los **PDFs de datasheets** de los componentes del BOM
(`docs/hardware/materiales.md`). El subagente `datasheet-reader`
(`.claude/agents/datasheet-reader.md`) extrae pinouts/specs de aquí.

Presentes (verificados contra el diseño en la validación 2026-07-02):

- **`uln2803a.pdf`** ✓ — ULN2803APG array Darlington (Toshiba): IN1–8=p1–8, GND=p9,
  COM=p10, OUT8–1=p11–18; Vce(sat), I_c máx por canal, diodos de clamp.
- **`dfplayer-mini.pdf`** ✓ — DFPlayer Mini (DFRobot DFR0299): pinout de 16 pines,
  **serie 3.3V TTL** (1 kΩ en RX recomendado), VCC 3.2–5.0 V, comandos.

Faltantes (sugeridos; dejar el PDF oficial nombrado por componente):

- `fsr-40x.pdf` — sensor de fuerza resistivo (curva R vs fuerza).
- LED blanco 5 mm — Vf típica/máx e I_F máx (del proveedor).
- ESP32 DevKit V1: **no hay datasheet canónico único** (placa de comunidad con
  variación entre clones) → el pinout VIN/3V3 se **confirma contra la placa física**
  (ver el pre-flight de `cableado.md` §1).

Regla del proyecto: si un dato no está en un datasheet aquí, se marca
**DESCONOCIDO** y se pregunta — no se rellena de memoria.

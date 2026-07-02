# Datasheets de componentes

Directorio para los **PDFs de datasheets** de los componentes del BOM
(`docs/hardware/materiales.md`). El subagente `datasheet-reader`
(`.claude/agents/datasheet-reader.md`) extrae pinouts/specs de aquí.

Sugerido (dejar el PDF oficial del fabricante, nombrado por componente):

- `esp32-devkit-v1.pdf` — ESP32 DevKit V1 (pinout, strapping, ADC1/ADC2).
- `uln2803a.pdf` — array Darlington (Vce(sat), I_c máx por canal, diodos de clamp).
- `dfplayer-mini.pdf` — reproductor MP3 (pinout, niveles lógicos, comandos).
- `fsr-40x.pdf` — sensor de fuerza resistivo (curva R vs fuerza).
- LED blanco 5 mm — Vf típica/máx e I_F máx (del proveedor).

Regla del proyecto: si un dato no está en un datasheet aquí, se marca
**DESCONOCIDO** y se pregunta — no se rellena de memoria.

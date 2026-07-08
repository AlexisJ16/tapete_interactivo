# Documentación del hardware — Tapete Interactivo

Paquete para materializar el circuito y el prototipo físico. Tres fuentes de verdad,
una por tema:

| Archivo | Qué es |
|---|---|
| `materiales.md` | **Inventario real + presupuesto** (fuente única de materiales). |
| `cableado.md` | **Mapa de armado**: geometría del protoboard, net list, ruteo de la Fila J, leyenda y checklist con multímetro (fuente única del armado). |
| `00_diseno_circuito.md` | **Diseño**: decisiones, arquitectura de potencia y prototipo físico (caja/tapa). |
| `flashing.md` | Flasheo del ESP32, credenciales WiFi y conexión del dashboard. |
| `validation.md` | Validación por software (simulador, dashboard y tests). |
| `spice/` | Validación analógica con **ngspice** (divisor FSR, grupo LED). |
| `kicad/` | **Esquemático eléctrico** KiCad 10 (ERC significativo en verde + PDF/BOM/netlist). Cruza net-por-net con `cableado.md` y `Config.h`. |
| `grafico/` | **Plantilla imprimible a escala real** de la tapa (acetato A3); ver `grafico/README.md`. |

## Impresión del gráfico de la tapa (`grafico/`)

Plantilla vectorial **a escala real** para imprimir en **acetato A3** y montar sobre la
tapa. Instrucciones completas en `grafico/README.md`. Resumen:

- **Tamaño:** cuadro interior **32.8 × 19.5 cm**; tapa completa a cubrir **39 × 26 cm**;
  6 botones **Ø 5.6 cm**. Imprimir **al 100%** (la hoja trae regla de 100 mm y marcas de corte).
- **Ventanas de los botones:** relleno translúcido de color + número al centro; el LED
  blanco enciende teñido de ese tono (los LEDs se ven directo por los huecos).
- **Paleta (hex):** B1 `#E63946` · B2 `#FFD60A` · B3 `#2A9D8F` · B4 `#0077B6` ·
  B5 `#F77F00` · B6 `#7B2CBF` · números/contornos `#1D3557`.
- **Accesibilidad:** cada botón se distingue por **color + número** (no depende solo del color).

## Antes de energizar

Sigue el **checklist con multímetro** (`cableado.md` §5). La regla que evita el
corto: **3V3 y 5V nunca con continuidad entre sí ni a GND**; los dos rieles `−` sí
van unidos (GND común).

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
| `grafico-tapete.svg` | Arte de la tapa (6 ventanas, paleta accesible). |

## Impresión del gráfico de la tapa (`grafico-tapete.svg`)

- **Tamaño:** **32.5 × 19.5 cm (horizontal)**. Imprimir a tamaño real.
- **Ventanas de los botones:** como los LEDs se ven **directo por los huecos** del
  acrílico, el gráfico solo necesita dejar una ventana sobre cada botón (no requiere
  material translúcido en toda la lámina).
- **Paleta (hex):** B1 `#E63946` · B2 `#FFD60A` · B3 `#2A9D8F` · B4 `#0077B6` ·
  B5 `#F77F00` · B6 `#7B2CBF` · fondo `#FFF8E7` · contornos/números `#1D3557`.
- **Accesibilidad:** cada botón se distingue por **color + número + forma** (estrella,
  corazón, círculo, cuadrado, triángulo, rombo) → no depende solo del color.

> El gráfico será rediseñado a nivel profesional a este tamaño (tarea aparte).

## Antes de energizar

Sigue el **checklist con multímetro** (`cableado.md` §6). La regla que evita el
corto: **3V3 y 5V nunca con continuidad entre sí ni a GND**; los dos rieles `−` sí
van unidos (GND común).

# Planos del hardware — Tapete Interactivo

Paquete de diseño para materializar el circuito y el prototipo físico.

> **Para MONTAR el circuito, la fuente AUTORITATIVA es la hoja de cálculo
> `mapa_armado_protoboard.xlsx`** (cada celda = un hueco real; geometría exacta
> validada con el autor: ESP32 cols 22–41, pines 25–39, USB-C col 21). El documento
> maestro `00_diseno_circuito.md` aporta la intención eléctrica y el net list lógico;
> sus columnas absolutas y los SVG están **desactualizados** (reconciliación pendiente).

| Archivo | Qué es |
|---|---|
| `mapa_armado_protoboard.xlsx` | **MAPA DE ARMADO (plano para montar)**: hoja 1 = protoboard hueco-por-hueco; hoja 2 = cableado, leyenda, ⚠ seguridad y pendientes. |
| `generar_mapa_armado.py` | Generador reproducible del mapa (Python + `openpyxl`), derivado de la geometría real + `Config.h`. |
| `00_diseno_circuito.md` | **Documento maestro**: net list, zonificación, receta mecánica, secuencia de armado, checklist con multímetro, materiales. |
| `plano-A-esquematico.svg` | Esquema eléctrico (lógico) — para el documento final. |
| `plano-A-protoboard.svg` | Mapa de armado hueco-por-hueco sobre el protoboard. |
| `plano-B-fisico.svg` | Prototipo físico: planta de la tapa, corte lateral, detalle del botón. |
| `grafico-tapete.svg` | Arte para la tapa (6 ventanas translúcidas, paleta accesible). |
| `guia-fritzing.md` | Cómo rehacer el protoboard en Fritzing (opcional, "sello" de tesis). |

## Ver / editar / imprimir los SVG

- **Ver:** se abren en cualquier navegador (vectorial, escala sin pixelarse).
- **Editar:** Inkscape (gratis) — texto, colores y posiciones son editables.
- **Exportar a PDF/PNG** para el documento: Inkscape → *Archivo → Exportar*.
- **Reproducir** desde código: los SVG se generan con scripts Python + `cairosvg`
  (los generadores quedaron en el scratchpad de la sesión; se pueden versionar
  aquí si se quiere reproducibilidad).

## Impresión del gráfico de la tapa (`grafico-tapete.svg`)

- **Material:** film translúcido / backlit, acetato o papel vellum. Las 6 ventanas
  deben dejar pasar la luz del LED blanco (si el material es opaco, no se ve el LED).
- **Tamaño:** 40 × 28 cm (a sangre del tapa). Imprimir a tamaño real.
- **Paleta (hex):** B1 `#E63946` · B2 `#FFD60A` · B3 `#2A9D8F` · B4 `#0077B6` ·
  B5 `#F77F00` · B6 `#7B2CBF` · fondo `#FFF8E7` · contornos/números `#1D3557`.
- **Accesibilidad:** cada botón se distingue por **color + número + forma**
  (estrella, corazón, círculo, cuadrado, triángulo, rombo) → no depende solo del
  color (apto para daltonismo).

## Antes de energizar

Sigue el **checklist con multímetro** (§9 del documento maestro). La regla que
evita el corto: **3V3 y 5V nunca con continuidad entre sí ni a GND**; los dos
rieles `−` sí van unidos (GND común).

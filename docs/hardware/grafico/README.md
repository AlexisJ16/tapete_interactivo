# Gráfico de la tapa — plantilla a escala real (acetato)

Plantilla imprimible del gráfico del tapete, **a tamaño real**, para imprimir en
**acetato** y montar sobre la tapa de la caja.

| Archivo | Uso |
|---|---|
| `grafico_tapete_A3.pdf` | **El que se lleva a imprimir** (página A3). |
| `grafico_tapete_A3.svg` | Fuente vectorial editable. |
| `../../../scripts/gen_grafico_tapete.py` | Generador (regenera ambos + una prueba PNG). |

## Cómo imprimir (crítico para el calce)

> **Prueba primero en papel.** Antes de gastar el acetato: imprime una vez en
> **papel normal a escala 100%**, recorta y **ponla sobre la tapa montada**.
> Confirma que los **6 círculos caen sobre los 6 grupos de LED**. Recién entonces
> imprime la versión definitiva en acetato.

1. Imprimir `grafico_tapete_A3.pdf` en **A3**, a **escala 100% / tamaño real**.
   **NO** usar "ajustar a página" / "fit to page" (escala y rompe el calce).
2. **Medir con una regla la barra de calibración** del margen inferior: debe dar
   **100 mm exactos**. Si no, la escala está mal — reimprimir.
3. **Recortar por las marcas** de las esquinas → queda **39 × 26 cm**.
4. Montar: **alinear cada círculo sobre su grupo de LEDs**. El borde (confeti) es
   decorativo y tolera unos milímetros; el calce lo mandan los círculos.

## Geometría exacta (fuente de verdad de esta plantilla)

Medidas tomadas del prototipo real. El interior va **centrado** en el arte.

| Elemento | Medida |
|---|---|
| Página del PDF | A3 (420 × 297 mm) |
| Arte (tapa completa a cubrir) | **390 × 260 mm** (39 × 26 cm) |
| Cuadro interior (zona de juego) | **328 × 195 mm** (32.8 × 19.5 cm), centrado |
| Margen arte→interior | 31 mm horizontal · 32.5 mm vertical |
| Botones | 6, en 2 filas × 3 columnas, **Ø 56 mm** (radio 2.8 cm) |
| Centros X (desde borde izq. del interior) | 82 · 164 · 246 mm (separación 8.2 cm) |
| Centros Y (desde borde sup. del interior) | 65 · 130 mm (separación 6.5 cm) |

> El borde exterior real (39 × 26) y el interior (32.8 × 19.5) se midieron por
> separado en el prototipo; ambos mandan. El "margen 3.5 cm" anotado a mano es un
> valor derivado aproximado — el margen exacto es 31 / 32.5 mm (interior centrado).

## Regenerar / ajustar

```bash
.venv/bin/python scripts/gen_grafico_tapete.py     # reescribe SVG + PDF + proof.png
```

Todo (colores, confeti, números, tamaños) se edita en el generador; las cotas en
milímetros del bloque de geometría son la única fuente de las posiciones.

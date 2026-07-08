#!/usr/bin/env python3
"""Genera la plantilla imprimible del gráfico del tapete, a escala real.

Salida:
  docs/hardware/grafico/grafico_tapete_A3.svg   (fuente vectorial editable)
  docs/hardware/grafico/grafico_tapete_A3.pdf   (imprimir al 100% en A3)
  /tmp/.../proof.png                             (prueba visual, no se versiona)

Todas las coordenadas están en MILÍMETROS (1 unidad SVG = 1 mm). La página es
A3 (420×297 mm); el arte del tapete mide EXACTAMENTE 390×260 mm (39×26 cm) y va
centrado. El interior (328×195 mm) queda centrado dentro del arte, con los 6
botones según las medidas medidas en el prototipo real.
"""
import math
import os
import random
import sys

import cairosvg

# --- Geometría de la página y del arte (todo en mm) ---------------------------
PAGE_W, PAGE_H = 420.0, 297.0          # A3 apaisado
ART_W, ART_H = 390.0, 260.0            # 39 × 26 cm (tapa completa a cubrir)
INT_W, INT_H = 328.0, 195.0            # 32.8 × 19.5 cm (cuadro interior, calce LEDs)

ART_X = (PAGE_W - ART_W) / 2.0         # 15.0
ART_Y = (PAGE_H - ART_H) / 2.0         # 18.5
INT_X = ART_X + (ART_W - INT_W) / 2.0  # 46.0  -> margen 3.1 cm al arte
INT_Y = ART_Y + (ART_H - INT_H) / 2.0  # 51.0  -> margen 3.25 cm al arte

R = 28.0                               # radio del botón = 2.8 cm
# Centros de los botones (medidas del prototipo: 8.2/16.4/24.6 x 6.5/13.0 desde el interior)
COLX = [INT_X + 82.0, INT_X + 164.0, INT_X + 246.0]   # 128, 210, 292
ROWY = [INT_Y + 65.0, INT_Y + 130.0]                  # 116, 181

# Paleta de identidad por botón (1..6), coherente con el diseño del proyecto
PAL = ["#E63946", "#FFD60A", "#2A9D8F", "#0077B6", "#F77F00", "#7B2CBF"]
NAVY = "#1D3557"

CENTERS = []  # (n, cx, cy, color)
n = 0
for cy in ROWY:
    for cx in COLX:
        CENTERS.append((n + 1, cx, cy, PAL[n]))
        n += 1


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def star(cx, cy, r, color, op):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append(f"{cx + rad*math.cos(a):.2f},{cy + rad*math.sin(a):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="{op}"/>'


def heart(cx, cy, r, color, op):
    # corazón simple centrado en (cx,cy), "radio" ~ r
    d = (f"M {cx:.2f} {cy + r*0.9:.2f} "
         f"C {cx - r*1.3:.2f} {cy - r*0.2:.2f} {cx - r*0.55:.2f} {cy - r*1.1:.2f} {cx:.2f} {cy - r*0.35:.2f} "
         f"C {cx + r*0.55:.2f} {cy - r*1.1:.2f} {cx + r*1.3:.2f} {cy - r*0.2:.2f} {cx:.2f} {cy + r*0.9:.2f} Z")
    return f'<path d="{d}" fill="{color}" fill-opacity="{op}"/>'


def dot(cx, cy, r, color, op):
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{color}" fill-opacity="{op}"/>'


def rsquare(cx, cy, r, color, op):
    return (f'<rect x="{cx-r:.2f}" y="{cy-r:.2f}" width="{2*r:.2f}" height="{2*r:.2f}" '
            f'rx="{r*0.35:.2f}" fill="{color}" fill-opacity="{op}"/>')


def in_interior(x, y, pad):
    return (INT_X - pad) <= x <= (INT_X + INT_W + pad) and (INT_Y - pad) <= y <= (INT_Y + INT_H + pad)


def confetti():
    """Formas alegres suaves, repartidas por bandas (arriba/abajo/lados) para un
    borde equilibrado y calmado, sin invadir la zona de juego."""
    rng = random.Random(7)
    makers = [dot, star, heart, rsquare]

    def shape(x, y):
        return rng.choice(makers)(x, y, rng.uniform(2.4, 5.0), rng.choice(PAL), rng.uniform(0.5, 0.72))

    out = []
    # Banda superior e inferior (recorren todo el ancho)
    top_cy, bot_cy = (ART_Y + INT_Y) / 2.0, (ART_Y + ART_H + INT_Y + INT_H) / 2.0
    for i in range(23):
        x = ART_X + 18.0 + i * (ART_W - 36.0) / 22.0
        out.append(shape(x + rng.uniform(-7, 7), top_cy + rng.uniform(-8, 8)))
        out.append(shape(x + rng.uniform(-7, 7), bot_cy + rng.uniform(-8, 8)))
    # Bandas laterales (solo el tramo central, las esquinas ya las cubren arriba/abajo)
    left_cx, right_cx = (ART_X + INT_X) / 2.0, (ART_X + ART_W + INT_X + INT_W) / 2.0
    for i in range(12):
        y = INT_Y + 8.0 + i * (INT_H - 16.0) / 11.0
        out.append(shape(left_cx + rng.uniform(-7, 7), y + rng.uniform(-9, 9)))
        out.append(shape(right_cx + rng.uniform(-7, 7), y + rng.uniform(-9, 9)))
    return "\n".join(out)


def button(nnum, cx, cy, color):
    parts = []
    # halo suave
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="30" fill="{color}" fill-opacity="0.10"/>')
    # disco translúcido (el LED enciende teñido de este color) + anillo de color
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{color}" fill-opacity="0.45" '
                 f'stroke="{color}" stroke-width="3"/>')
    # número en el centro
    parts.append(f'<text x="{cx}" y="{cy + 9.2:.2f}" font-family="DejaVu Sans, Arial, sans-serif" '
                 f'font-size="26" font-weight="bold" fill="{NAVY}" text-anchor="middle">{nnum}</text>')
    return "\n".join(parts)


def crop_marks():
    out = []
    L, g, w = 6.0, 1.0, 0.3
    corners = [(ART_X, ART_Y, -1, -1), (ART_X + ART_W, ART_Y, 1, -1),
               (ART_X, ART_Y + ART_H, -1, 1), (ART_X + ART_W, ART_Y + ART_H, 1, 1)]
    for x, y, sx, sy in corners:
        # tick horizontal (en el margen izq/der)
        out.append(f'<line x1="{x + sx*g:.2f}" y1="{y:.2f}" x2="{x + sx*(g+L):.2f}" y2="{y:.2f}" '
                   f'stroke="{NAVY}" stroke-width="{w}"/>')
        # tick vertical (en el margen sup/inf)
        out.append(f'<line x1="{x:.2f}" y1="{y + sy*g:.2f}" x2="{x:.2f}" y2="{y + sy*(g+L):.2f}" '
                   f'stroke="{NAVY}" stroke-width="{w}"/>')
    return "\n".join(out)


def ruler():
    """Regla de calibración de 100 mm en el margen inferior (se recorta)."""
    x0 = (PAGE_W - 100.0) / 2.0   # 160
    x1 = x0 + 100.0
    y = 285.0                     # separada del borde para que no la recorte la impresora
    out = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{NAVY}" stroke-width="0.4"/>']
    for i in range(11):
        xx = x0 + i * 10.0
        h = 2.6 if i in (0, 10) else 1.4
        out.append(f'<line x1="{xx:.1f}" y1="{y-h:.1f}" x2="{xx:.1f}" y2="{y+h:.1f}" '
                   f'stroke="{NAVY}" stroke-width="0.4"/>')
    out.append(f'<text x="{PAGE_W/2:.1f}" y="{y-3.2:.1f}" font-family="DejaVu Sans, Arial, sans-serif" '
               f'font-size="3.2" fill="{NAVY}" text-anchor="middle">CALIBRACIÓN 100 mm — medir con regla; debe dar 100 mm exactos</text>')
    return "\n".join(out)


def build_svg():
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" '
             f'viewBox="0 0 {PAGE_W} {PAGE_H}">')
    # fondo de página (blanco de referencia; en acetato no se imprime tinta blanca)
    p.append(f'<rect x="0" y="0" width="{PAGE_W}" height="{PAGE_H}" fill="#FFFFFF"/>')

    # marco decorativo exterior (dentro del arte) y zona de juego (borde 32.8×19.5 exacto)
    p.append(f'<rect x="{ART_X+5:.1f}" y="{ART_Y+5:.1f}" width="{ART_W-10:.1f}" height="{ART_H-10:.1f}" '
             f'rx="10" fill="none" stroke="{NAVY}" stroke-opacity="0.22" stroke-width="0.8"/>')
    p.append(f'<rect x="{INT_X}" y="{INT_Y}" width="{INT_W}" height="{INT_H}" rx="8" '
             f'fill="none" stroke="{NAVY}" stroke-opacity="0.30" stroke-width="0.6" stroke-dasharray="3 2"/>')

    # confeti del borde
    p.append(confetti())

    # botones
    for nnum, cx, cy, color in CENTERS:
        p.append(button(nnum, cx, cy, color))

    # marcas de corte + regla + textos de control (en los márgenes de la página, se recortan)
    p.append(crop_marks())
    p.append(ruler())
    title = ("TAPETE INTERACTIVO — plantilla a escala real 39 × 26 cm.  "
             "IMPRIMIR AL 100% / TAMAÑO REAL — NO usar “ajustar a página”.  Recortar por las marcas.")
    sub = ("Acetato A3 · alinear cada círculo sobre su grupo de LEDs (el borde es decorativo) · "
           "verificar la regla de 100 mm antes de montar.")
    p.append(f'<text x="{PAGE_W/2:.1f}" y="9.5" font-family="DejaVu Sans, Arial, sans-serif" '
             f'font-size="3.4" font-weight="bold" fill="{NAVY}" text-anchor="middle">{esc(title)}</text>')
    p.append(f'<text x="{PAGE_W/2:.1f}" y="14.2" font-family="DejaVu Sans, Arial, sans-serif" '
             f'font-size="3.0" fill="{NAVY}" text-anchor="middle">{esc(sub)}</text>')

    p.append('</svg>')
    return "\n".join(p)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    outdir = os.path.join(root, "docs", "hardware", "grafico")
    os.makedirs(outdir, exist_ok=True)
    svg = build_svg()
    svg_path = os.path.join(outdir, "grafico_tapete_A3.svg")
    pdf_path = os.path.join(outdir, "grafico_tapete_A3.pdf")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=pdf_path)
    proof = sys.argv[1] if len(sys.argv) > 1 else os.path.join(outdir, "proof.png")
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=proof, dpi=150)
    print("SVG:", svg_path)
    print("PDF:", pdf_path)
    print("PNG:", proof)


if __name__ == "__main__":
    main()

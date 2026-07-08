"""Exportacion de reportes de sesion: CSV y PDF.

CSV: resumen de la sesion + log de eventos. PDF: una pagina con el resumen y un
grafico de aciertos/errores (matplotlib, backend Agg, sin pantalla).
"""
from __future__ import annotations

import csv

from storage import Almacen

CAMPOS_RESUMEN = [
    "id", "perfil_id", "modo", "nivel", "hits", "misses",
    "rt_prom_ms", "rondas", "estado_final", "inicio", "fin",
]


class ReporteError(Exception):
    """Fallo controlado al exportar (sesion inexistente, ruta sin permiso u
    otro error de E/S). La frontera GUI la captura en vez de propagar."""


def exportar_csv(almacen: Almacen, sesion_id: int, ruta: str) -> str:
    """Escribe un CSV con el resumen de la sesion y su log de eventos."""
    s = almacen.sesion(sesion_id)
    if s is None:
        raise ReporteError(f"sesion {sesion_id} inexistente")
    eventos = almacen.eventos(sesion_id)

    try:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["campo", "valor"])
            for c in CAMPOS_RESUMEN:
                w.writerow([c, s.get(c)])
            w.writerow([])
            w.writerow(["ms", "tipo", "datos"])
            for e in eventos:
                w.writerow([e["ms"], e["tipo"], e["datos"]])
    except OSError as e:
        raise ReporteError(f"no se pudo escribir '{ruta}': {e}") from e
    return ruta


def exportar_pdf(almacen: Almacen, sesion_id: int, ruta: str) -> str:
    """Escribe un PDF de una pagina con el resumen y un grafico simple."""
    import matplotlib
    matplotlib.use("Agg")  # sin pantalla
    import matplotlib.pyplot as plt

    s = almacen.sesion(sesion_id)
    if s is None:
        raise ReporteError(f"sesion {sesion_id} inexistente")

    fig, (ax_txt, ax_bar) = plt.subplots(2, 1, figsize=(8.27, 11.69),
                                         gridspec_kw={"height_ratios": [1, 1]})
    fig.suptitle("Tapete Interactivo — Reporte de sesion", fontsize=16, fontweight="bold")

    lineas = [
        f"Sesion: {s['id']}        Perfil: {s.get('perfil_id') or '-'}",
        f"Modo: {s['modo']}        Nivel: {s['nivel']}",
        f"Inicio: {s.get('inicio')}",
        f"Fin: {s.get('fin') or '-'}        Estado: {s.get('estado_final') or '-'}",
        "",
        f"Aciertos (hits): {s['hits']}",
        f"Errores (misses): {s['misses']}",
        f"Tiempo de reaccion promedio: {s['rt_prom_ms']} ms",
        f"Rondas / longitud: {s['rondas']}",
    ]
    ax_txt.axis("off")
    ax_txt.text(0.02, 0.95, "\n".join(lineas), va="top", ha="left",
                fontsize=12, family="monospace")

    ax_bar.bar(["aciertos", "errores"], [s["hits"], s["misses"]],
               color=["#3a8", "#c44"])
    ax_bar.set_ylabel("conteo")
    ax_bar.set_title("Desempeno")

    try:
        fig.savefig(ruta, format="pdf")
    except OSError as e:
        raise ReporteError(f"no se pudo escribir '{ruta}': {e}") from e
    finally:
        plt.close(fig)
    return ruta

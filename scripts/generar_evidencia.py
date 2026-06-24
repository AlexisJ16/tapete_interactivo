"""Genera figuras de evidencia (E2/E3/E4) de la lógica adaptable del Tapete.

Las figuras representan el COMPORTAMIENTO DEL SISTEMA EN SIMULACIÓN DETERMINISTA
(no resultados con pacientes ni datos de campo). Esa etiqueta se hornea en cada
figura para evitar lecturas indebidas. Backend Agg: no requiere pantalla.
"""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))
from evidencia import (  # noqa: E402
    barrido_habilidad, barrido_niveles, trayectoria_adaptativa,
)

SEED = 777
NOTA = ("Simulación determinista del sistema (mismo GameCore que el ESP32) — "
        "no son datos de usuarios reales.")


def _pie(fig) -> None:
    fig.text(0.5, 0.005, NOTA, ha="center", fontsize=7, style="italic", color="gray")


def _fig_adaptacion(salida: str) -> str:
    habs = [i / 10 for i in range(0, 11)]
    filas = barrido_habilidad(nivel=2, seed=SEED, habilidades=habs)
    x = [f["habilidad"] * 100 for f in filas]
    tasa = [100 * f["hits"] / max(1, f["rondas"]) for f in filas]
    color = {"up": "tab:green", "down": "tab:red", "keep": "tab:gray"}
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, tasa, "-", color="tab:blue", zorder=1, label="tasa de acierto")
    for f, xi, yi in zip(filas, x, tasa):
        ax.scatter([xi], [yi], color=color[f["dir"]], zorder=3, s=45)
    for dir_, col in color.items():
        ax.scatter([], [], color=col, label=f"sugiere: {dir_}")
    ax.set_xlabel("habilidad simulada del jugador (%)")
    ax.set_ylabel("tasa de acierto en la sesión (%)")
    ax.set_title("E2 — Recomendación adaptativa vs desempeño\n(Velocidad nivel 2, simulación)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    _pie(fig)
    ruta = os.path.join(salida, "E2_adaptacion.png")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(ruta, dpi=120); plt.close(fig)
    return ruta


def _fig_niveles(salida: str) -> str:
    filas = barrido_niveles(seed=SEED, habilidad=0.8, niveles=[1, 2, 3, 4])
    x = [f["nivel"] for f in filas]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([n - 0.2 for n in x], [f["hits"] for f in filas], width=0.4, label="hits")
    ax.bar([n + 0.2 for n in x], [f["misses"] for f in filas], width=0.4, label="misses")
    ax.set_xlabel("nivel"); ax.set_ylabel("conteo por sesión")
    ax.set_title("E3 — Desempeño por nivel\n(Velocidad, habilidad simulada 80%)")
    ax.set_xticks(x); ax.legend(); ax.grid(True, axis="y", alpha=0.3)
    _pie(fig)
    ruta = os.path.join(salida, "E3_niveles.png")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(ruta, dpi=120); plt.close(fig)
    return ruta


def _fig_trayectoria(salida: str) -> str:
    buena = trayectoria_adaptativa(seed=SEED, habilidad=0.95, nivel_inicial=1, n_sesiones=8)
    mala = trayectoria_adaptativa(seed=SEED, habilidad=0.1, nivel_inicial=4, n_sesiones=8)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([f["sesion"] for f in buena], [f["nivel"] for f in buena], "-o",
            color="tab:green", label="jugador hábil (95%)")
    ax.plot([f["sesion"] for f in mala], [f["nivel"] for f in mala], "-o",
            color="tab:red", label="jugador con dificultad (10%)")
    ax.set_xlabel("sesión"); ax.set_ylabel("nivel")
    ax.set_yticks([1, 2, 3, 4])
    ax.set_title("E4 — Trayectoria de nivel entre sesiones\n(adaptación, simulación)")
    ax.legend(); ax.grid(True, alpha=0.3)
    _pie(fig)
    ruta = os.path.join(salida, "E4_trayectoria.png")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(ruta, dpi=120); plt.close(fig)
    return ruta


def main(salida: str = os.path.join(RAIZ, "docs", "evidencia")) -> list[str]:
    os.makedirs(salida, exist_ok=True)
    return [_fig_adaptacion(salida), _fig_niveles(salida), _fig_trayectoria(salida)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera figuras de evidencia (E2/E3/E4).")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "docs", "evidencia"))
    args = ap.parse_args()
    for r in main(args.salida):
        print("escrita:", r)

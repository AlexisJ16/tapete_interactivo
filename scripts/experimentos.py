"""Genera TODA la evidencia cuantitativa del articulo, de forma reproducible.

Escribe `docs/evidencia/resultados.json` (las cifras que se citan en el texto) y
las figuras nuevas. Ninguna cifra del articulo debe escribirse a mano: sale de aqui.

    .venv/bin/python scripts/experimentos.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))

from evidencia_modos import (MODOS, NOMBRE_MODO, barrido_habilidad_modo,  # noqa: E402
                             barrido_niveles_modo, jugar, trayectoria_modo)
from montecarlo import resumen, tasa_por_longitud_memoria  # noqa: E402

SEED = 777
SEMILLAS_MC = range(200)
SALIDA = os.path.join(RAIZ, "docs", "evidencia")

COLOR = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c"}
PIE = "Simulación determinista del sistema (mismo GameCore que el ESP32) — no son datos de usuarios reales."


def huella_determinismo() -> dict:
    """E1: dos ejecuciones de la misma configuracion producen la MISMA traza."""
    out = {}
    for modo in MODOS:
        trazas = []
        for _ in range(2):
            r = jugar(modo, nivel=2, seed=SEED, habilidad=0.8)
            crudo = json.dumps(r["scores"], sort_keys=True).encode()
            trazas.append(hashlib.sha256(crudo).hexdigest())
        out[NOMBRE_MODO[modo]] = {"sha256": trazas[0], "identicas": trazas[0] == trazas[1]}
    return out


def golden() -> dict:
    """E2: cuantos escenarios de referencia hay y cuantos exigen traza exacta."""
    with open(os.path.join(RAIZ, "shared", "golden_vectors.json"), encoding="utf-8") as f:
        escenarios = json.load(f)["scenarios"]
    estrictos = sum(1 for e in escenarios if e.get("match") == "strict")
    return {"escenarios": len(escenarios), "estrictos": estrictos,
            "subsecuencia": len(escenarios) - estrictos}


def adaptacion() -> dict:
    habilidades = [round(0.1 * i, 1) for i in range(11)]
    return {NOMBRE_MODO[m]: barrido_habilidad_modo(m, 2, SEED, habilidades) for m in MODOS}


def escalado_niveles() -> dict:
    return {NOMBRE_MODO[m]: barrido_niveles_modo(m, SEED, 0.8, [1, 2, 3, 4]) for m in MODOS}


def convergencia() -> dict:
    out = {}
    for m in MODOS:
        out[NOMBRE_MODO[m]] = {
            "habil": trayectoria_modo(m, SEED, 1.0, nivel_inicial=1, n_sesiones=8),
            "con_dificultad": trayectoria_modo(m, SEED, 0.0, nivel_inicial=4, n_sesiones=8),
        }
    return out


def montecarlo() -> dict:
    velocidad = [resumen(2, 2, h, SEMILLAS_MC) for h in (0.3, 0.5, 0.7, 0.9)]
    equilibrio = [resumen(3, 2, h, SEMILLAS_MC) for h in (0.5, 0.7, 0.9)]
    memoria = []
    for longitud, (medido, n) in tasa_por_longitud_memoria(2, 0.85, SEMILLAS_MC).items():
        margen = 1.96 * (medido * (1 - medido) / n) ** 0.5
        teorico = 0.85 ** longitud
        memoria.append({"longitud": longitud, "rondas": n, "medido": medido,
                        "ic95": margen, "teorico": teorico,
                        "coincide": abs(medido - teorico) <= margen})
    return {"Velocidad": velocidad, "Equilibrio": equilibrio,
            "Memoria": {"habilidad": 0.85, "por_longitud": memoria}}


def figura_convergencia(datos: dict, salida: str) -> str:
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for eje, modo in zip(ejes, MODOS):
        d = datos[NOMBRE_MODO[modo]]
        eje.plot([f["sesion"] for f in d["habil"]], [f["nivel"] for f in d["habil"]],
                 "o-", color="#2ca02c", label="jugador hábil (h=1,0)")
        eje.plot([f["sesion"] for f in d["con_dificultad"]],
                 [f["nivel"] for f in d["con_dificultad"]],
                 "s--", color="#d62728", label="jugador con dificultad (h=0,0)")
        eje.set_title(NOMBRE_MODO[modo])
        eje.set_xlabel("sesión")
        eje.set_yticks([1, 2, 3, 4])
        eje.grid(alpha=0.3)
    ejes[0].set_ylabel("nivel")
    ejes[0].legend(fontsize=7, loc="center right")
    fig.suptitle("Convergencia del nivel de dificultad al desempeño, por modo", y=1.02)
    fig.text(0.5, -0.10, PIE, ha="center", fontsize=7, style="italic")
    ruta = os.path.join(salida, "E5_convergencia_modos.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def figura_montecarlo(datos: dict, salida: str) -> str:
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.4))

    def panel(eje, filas, xs, teoricas, titulo, xlabel):
        medidos = [f["med" if "med" in f else "medido"] for f in filas]
        errores = [f["ic95"] for f in filas]
        eje.errorbar(xs, medidos, yerr=errores, fmt="o", capsize=4,
                     color="#1f77b4", label="medido (IC 95 %)")
        eje.plot(xs, teoricas, "--", color="#d62728", label="predicción teórica")
        eje.set_title(titulo)
        eje.set_xlabel(xlabel)
        eje.grid(alpha=0.3)
        eje.legend(fontsize=7)

    v = datos["Velocidad"]
    panel(ejes[0], v, [f["habilidad"] for f in v], [f["teorico"] for f in v],
          "Velocidad:  P = h", "habilidad h")
    e = datos["Equilibrio"]
    panel(ejes[1], e, [f["habilidad"] for f in e], [f["teorico"] for f in e],
          "Equilibrio:  P = h³  (k=3)", "habilidad h")
    m = datos["Memoria"]["por_longitud"]
    panel(ejes[2], m, [f["longitud"] for f in m], [f["teorico"] for f in m],
          "Memoria:  P = h^L  (h=0,85)", "longitud L de la secuencia")
    ejes[0].set_ylabel("prob. de ganar la ronda")
    fig.suptitle("Verificación estadística de la regla del motor (200 semillas)", y=1.02)
    fig.text(0.5, -0.10, PIE, ha="center", fontsize=7, style="italic")
    ruta = os.path.join(salida, "E6_montecarlo.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def coste_computacional() -> dict:
    """Compila y corre el benchmark C++ del nucleo. Cifras en ns/us, no inventadas."""
    import re
    import subprocess

    binario = os.path.join(RAIZ, "build", "bench_nucleo")
    fuentes = [os.path.join(RAIZ, "scripts", "bench_nucleo.cpp")]
    for patron in ("*.cpp", "modes/*.cpp"):
        import glob
        fuentes += sorted(glob.glob(os.path.join(RAIZ, "firmware", "lib", "GameCore", patron)))
    subprocess.run(["g++", "-std=c++17", "-O2",
                    f"-I{os.path.join(RAIZ, 'firmware', 'lib', 'GameCore')}",
                    *fuentes, "-o", binario], check=True)
    salida = subprocess.run([binario], check=True, capture_output=True, text=True).stdout
    numeros = [float(x) for x in re.findall(r"([\d.]+) (?:ns|us)/", salida)]
    return {"tick_ns": numeros[0], "pisada_ns": numeros[1], "sesion_us": numeros[2],
            "cpu": "Intel Core i7-1355U", "salida_cruda": salida.strip().splitlines()}


def main(salida: str = SALIDA) -> int:
    os.makedirs(salida, exist_ok=True)
    datos = {
        "seed": SEED,
        "semillas_montecarlo": len(list(SEMILLAS_MC)),
        "determinismo": huella_determinismo(),
        "golden": golden(),
        "adaptacion": adaptacion(),
        "escalado_niveles": escalado_niveles(),
        "convergencia": convergencia(),
        "montecarlo": montecarlo(),
        "coste_computacional": coste_computacional(),
    }
    figura_convergencia(datos["convergencia"], salida)
    figura_montecarlo(datos["montecarlo"], salida)

    ruta = os.path.join(salida, "resultados.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print(f"OK: {ruta}")

    fallos = [k for k, v in datos["determinismo"].items() if not v["identicas"]]
    if fallos:
        print(f"ERROR: trazas no deterministas en {fallos}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

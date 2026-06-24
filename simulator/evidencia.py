"""Agrega evidencia de la lógica adaptable corriendo el jugador simulado.
Determinista: solo depende de (seed, habilidad, nivel)."""
from __future__ import annotations

from jugador_sim import jugar_sesion


def _dir_final(r: dict) -> str:
    return r["suggests"][-1]["dir"] if r["suggests"] else "keep"


def _nivel_sugerido(r: dict, nivel_actual: int) -> int:
    if r["suggests"]:
        return max(1, min(4, r["suggests"][-1]["level"]))
    return nivel_actual


def barrido_habilidad(nivel: int, seed: int, habilidades: list[float]) -> list[dict]:
    filas = []
    for h in habilidades:
        r = jugar_sesion(modo=2, nivel=nivel, seed=seed, habilidad=h)
        filas.append({"habilidad": h, "hits": r["hits"], "misses": r["misses"],
                      "rt_ms": r["rt_ms"], "rondas": r["rondas"], "dir": _dir_final(r)})
    return filas


def barrido_niveles(seed: int, habilidad: float, niveles: list[int]) -> list[dict]:
    filas = []
    for n in niveles:
        r = jugar_sesion(modo=2, nivel=n, seed=seed, habilidad=habilidad)
        filas.append({"nivel": n, "hits": r["hits"], "misses": r["misses"],
                      "rt_ms": r["rt_ms"], "rondas": r["rondas"]})
    return filas


def trayectoria_adaptativa(seed: int, habilidad: float, nivel_inicial: int,
                           n_sesiones: int) -> list[dict]:
    filas = []
    nivel = nivel_inicial
    for i in range(n_sesiones):
        r = jugar_sesion(modo=2, nivel=nivel, seed=seed + i, habilidad=habilidad)
        filas.append({"sesion": i + 1, "nivel": nivel,
                      "hits": r["hits"], "misses": r["misses"]})
        nivel = _nivel_sugerido(r, nivel)
    return filas

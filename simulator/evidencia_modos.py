"""Evidencia de la logica adaptativa para los TRES modos de juego.

`evidencia.py` cubre solo el modo Velocidad (y no se toca: sus figuras estan
publicadas y son byte-reproducibles). Este modulo generaliza los tres experimentos
a Memoria y Equilibrio usando los jugadores de `jugador_modos.py`.

Determinista: todo depende solo de (modo, nivel, seed, habilidad).
"""
from __future__ import annotations

from jugador_modos import jugar_equilibrio, jugar_memoria
from jugador_sim import jugar_sesion

MODOS = (1, 2, 3)
NOMBRE_MODO = {1: "Memoria", 2: "Velocidad", 3: "Equilibrio"}

NIVEL_MIN, NIVEL_MAX = 1, 4


def jugar(modo: int, nivel: int, seed: int, habilidad: float) -> dict:
    if modo == 1:
        return jugar_memoria(nivel=nivel, seed=seed, habilidad=habilidad)
    if modo == 3:
        return jugar_equilibrio(nivel=nivel, seed=seed, habilidad=habilidad)
    r = jugar_sesion(modo=2, nivel=nivel, seed=seed, habilidad=habilidad)
    r.setdefault("finished", True)
    return r


def _tasa(r: dict) -> float:
    total = r["hits"] + r["misses"]
    return round(100.0 * r["hits"] / total, 1) if total else 0.0


def _dir_final(r: dict) -> str:
    return r["suggests"][-1]["dir"] if r["suggests"] else "keep"


def _nivel_sugerido(r: dict, nivel_actual: int) -> int:
    if r["suggests"]:
        return max(NIVEL_MIN, min(NIVEL_MAX, r["suggests"][-1]["level"]))
    return nivel_actual


def _fila(r: dict) -> dict:
    return {"hits": r["hits"], "misses": r["misses"], "tasa": _tasa(r),
            "rondas": r["rondas"], "dir": _dir_final(r)}


def barrido_habilidad_modo(modo: int, nivel: int, seed: int,
                           habilidades: list[float]) -> list[dict]:
    """Tasa de acierto y direccion sugerida frente a la habilidad del jugador."""
    return [{"habilidad": h, **_fila(jugar(modo, nivel, seed, h))} for h in habilidades]


def barrido_niveles_modo(modo: int, seed: int, habilidad: float,
                         niveles: list[int]) -> list[dict]:
    """Como escala la exigencia de la sesion con el nivel, a habilidad fija."""
    return [{"nivel": n, **_fila(jugar(modo, n, seed, habilidad))} for n in niveles]


def trayectoria_modo(modo: int, seed: int, habilidad: float, nivel_inicial: int,
                     n_sesiones: int) -> list[dict]:
    """Encadena sesiones aplicando en cada una la recomendacion de nivel."""
    filas = []
    nivel = nivel_inicial
    for i in range(n_sesiones):
        r = jugar(modo, nivel, seed + i, habilidad)
        filas.append({"sesion": i + 1, "nivel": nivel,
                      "hits": r["hits"], "misses": r["misses"], "tasa": _tasa(r)})
        nivel = _nivel_sugerido(r, nivel)
    return filas

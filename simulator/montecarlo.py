"""Monte Carlo determinista sobre el motor: contrasta lo medido con la teoria.

El jugador simulado acierta cada pisada con probabilidad `h`. Una ronda se gana
solo encadenando aciertos, asi que la probabilidad teorica de ganarla es:

    Velocidad   P = h        (una casilla)
    Equilibrio  P = h^k      (k casillas simultaneas del patron)
    Memoria     P = h^L      (secuencia de longitud L)

Reproducible: solo depende de (modo, nivel, habilidad, semillas).
"""
from __future__ import annotations

from evidencia_modos import jugar
from jugador_modos import jugar_memoria


def rondas(scores: list[dict]) -> list[tuple[bool, int]]:
    """(acierto, round) por ronda. Cada `score` sube en 1 los hits o los misses."""
    hits_previos = 0
    out = []
    for s in scores:
        out.append((s["hits"] > hits_previos, s["round"]))
        hits_previos = s["hits"]
    return out


def predecir_velocidad(h: float) -> float:
    return h


def predecir_equilibrio(h: float, k: int) -> float:
    return h ** k


def predecir_memoria(h: float, longitud: int) -> float:
    return h ** longitud


def tasa_montecarlo(modo: int, nivel: int, habilidad: float, semillas) -> float:
    """Fraccion de rondas ganadas, agregando todas las semillas."""
    ganadas, total = _conteo(modo, nivel, habilidad, semillas)
    return ganadas / total if total else 0.0


def _conteo(modo: int, nivel: int, habilidad: float, semillas) -> tuple[int, int]:
    ganadas = total = 0
    for seed in semillas:
        for acierto, _ in rondas(jugar(modo, nivel, seed, habilidad)["scores"]):
            ganadas += acierto
            total += 1
    return ganadas, total


def ic95(p: float, n: int) -> float:
    """Semiancho del intervalo de confianza al 95 % de una proporcion (Wald)."""
    return 1.96 * (p * (1 - p) / n) ** 0.5 if n else 0.0


def resumen(modo: int, nivel: int, habilidad: float, semillas) -> dict:
    """Medicion contrastada con la prediccion teorica, con su intervalo."""
    ganadas, total = _conteo(modo, nivel, habilidad, semillas)
    medido = ganadas / total if total else 0.0
    margen = ic95(medido, total)
    teorico = _prediccion(modo, nivel, habilidad)
    return {"habilidad": habilidad, "rondas": total, "medido": medido,
            "ic95": margen, "teorico": teorico,
            "coincide": abs(medido - teorico) <= margen}


def _prediccion(modo: int, nivel: int, h: float) -> float:
    if modo == 2:
        return predecir_velocidad(h)
    if modo == 3:
        return predecir_equilibrio(h, _k_equilibrio(nivel))
    raise ValueError("Memoria varia la longitud por ronda: usa tasa_por_longitud_memoria")


def _k_equilibrio(nivel: int) -> int:
    """Casillas simultaneas del patron (Config.h: 1+nivel, acotado a [2,4])."""
    return max(2, min(4, 1 + nivel))


def tasa_por_longitud_memoria(nivel: int, habilidad: float,
                              semillas) -> dict[int, tuple[float, int]]:
    """{longitud de la secuencia: (fraccion ganada, nº de rondas observadas)}."""
    ganadas: dict[int, int] = {}
    totales: dict[int, int] = {}
    for seed in semillas:
        r = jugar_memoria(nivel=nivel, seed=seed, habilidad=habilidad)
        for acierto, longitud in rondas(r["scores"]):
            totales[longitud] = totales.get(longitud, 0) + 1
            ganadas[longitud] = ganadas.get(longitud, 0) + int(acierto)
    return {L: (ganadas[L] / totales[L], totales[L]) for L in sorted(totales)}

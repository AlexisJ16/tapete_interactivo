"""Verificacion estadistica del motor: lo medido debe coincidir con la teoria.

Una ronda se gana solo encadenando aciertos: 1 en Velocidad, k casillas en
Equilibrio, L pasos de secuencia en Memoria. Con un jugador que acierta cada
pisada con probabilidad h, la probabilidad de ganar una ronda es h, h^k y h^L
respectivamente. Si el motor implementa la regla que dice implementar, la tasa
medida sobre muchas semillas debe converger a ese valor.
"""
from __future__ import annotations

from montecarlo import (predecir_velocidad, tasa_montecarlo,
                        tasa_por_longitud_memoria)

# Tolerancia absoluta sobre una proporcion, holgada frente al error de muestreo.
TOL = 0.05


def test_velocidad_converge_a_h():
    for h in (0.5, 0.8):
        medido = tasa_montecarlo(modo=2, nivel=2, habilidad=h, semillas=range(120))
        assert abs(medido - predecir_velocidad(h)) < TOL, (h, medido)


def test_equilibrio_converge_a_h_elevado_a_k():
    # Nivel 2 -> k = 3 casillas simultaneas (Config.h).
    for h in (0.7, 0.9):
        medido = tasa_montecarlo(modo=3, nivel=2, habilidad=h, semillas=range(120))
        assert abs(medido - h ** 3) < TOL, (h, medido)


def test_memoria_converge_a_h_elevado_a_la_longitud():
    # Nivel 2 -> longitudes 3..6. Cada ronda de longitud L exige L aciertos.
    por_l = tasa_por_longitud_memoria(nivel=2, habilidad=0.85, semillas=range(120))
    assert por_l, "no se registro ninguna ronda"
    for longitud, (medido, n) in sorted(por_l.items()):
        if n < 30:
            continue          # muestra insuficiente para afirmar nada
        assert abs(medido - 0.85 ** longitud) < TOL, (longitud, medido, n)


def test_es_determinista():
    a = tasa_montecarlo(modo=2, nivel=1, habilidad=0.6, semillas=range(20))
    b = tasa_montecarlo(modo=2, nivel=1, habilidad=0.6, semillas=range(20))
    assert a == b

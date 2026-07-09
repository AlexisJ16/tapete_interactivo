"""Jugadores simulados para los modos Memoria y Equilibrio.

El jugador de `jugador_sim.py` solo sabe reaccionar al unico LED encendido (modo
Velocidad). Memoria exige memorizar una secuencia exhibida y repetirla; Equilibrio
exige pisar k casillas simultaneas. Sin estos jugadores no hay evidencia por
simulacion de los modos 1 y 3.
"""
from __future__ import annotations

from jugador_modos import jugar_equilibrio, jugar_memoria


def test_memoria_habilidad_perfecta_completa_la_sesion():
    r = jugar_memoria(nivel=1, seed=777, habilidad=1.0)
    # Nivel 1: longitud inicial 2, maxima 5 -> se superan las longitudes 2,3,4,5.
    assert r["finished"] is True
    assert r["hits"] == 4
    assert r["misses"] == 0


def test_memoria_habilidad_nula_solo_falla_y_no_termina():
    r = jugar_memoria(nivel=1, seed=777, habilidad=0.0)
    assert r["hits"] == 0
    assert r["misses"] > 0
    assert r["finished"] is False


def test_memoria_es_determinista():
    a = jugar_memoria(nivel=2, seed=2024, habilidad=0.6)
    b = jugar_memoria(nivel=2, seed=2024, habilidad=0.6)
    assert a["scores"] == b["scores"]


def test_equilibrio_habilidad_perfecta_acierta_todas_las_rondas():
    r = jugar_equilibrio(nivel=1, seed=777, habilidad=1.0)
    # Nivel 1: 4 rondas, patron de 2 casillas.
    assert r["finished"] is True
    assert r["hits"] == 4
    assert r["misses"] == 0


def test_equilibrio_habilidad_nula_falla_todas_las_rondas():
    r = jugar_equilibrio(nivel=1, seed=777, habilidad=0.0)
    assert r["hits"] == 0
    assert r["misses"] == 4
    assert r["finished"] is True


def test_equilibrio_es_determinista():
    a = jugar_equilibrio(nivel=3, seed=99, habilidad=0.7)
    b = jugar_equilibrio(nivel=3, seed=99, habilidad=0.7)
    assert a["scores"] == b["scores"]

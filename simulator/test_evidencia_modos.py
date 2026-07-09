"""Evidencia de la logica adaptativa en los TRES modos, no solo Velocidad."""
from __future__ import annotations

from evidencia_modos import (MODOS, barrido_habilidad_modo, barrido_niveles_modo,
                             jugar, trayectoria_modo)


def test_jugar_despacha_los_tres_modos():
    for modo in MODOS:
        r = jugar(modo=modo, nivel=1, seed=777, habilidad=1.0)
        assert r["modo"] == modo
        assert r["hits"] > 0


def test_barrido_habilidad_la_tasa_de_acierto_crece_con_la_habilidad():
    for modo in MODOS:
        filas = barrido_habilidad_modo(modo, nivel=2, seed=777,
                                       habilidades=[0.0, 0.5, 1.0])
        tasas = [f["tasa"] for f in filas]
        assert tasas == sorted(tasas), f"modo {modo}: {tasas}"
        assert tasas[0] == 0.0 and tasas[-1] == 100.0


def test_barrido_habilidad_la_direccion_sugerida_es_coherente():
    for modo in MODOS:
        filas = barrido_habilidad_modo(modo, nivel=2, seed=777,
                                       habilidades=[0.0, 1.0])
        assert filas[0]["dir"] == "down"   # falla todo -> bajar
        assert filas[-1]["dir"] == "up"    # acierta todo -> subir


def test_barrido_niveles_devuelve_una_fila_por_nivel():
    for modo in MODOS:
        filas = barrido_niveles_modo(modo, seed=777, habilidad=0.8, niveles=[1, 2, 3, 4])
        assert [f["nivel"] for f in filas] == [1, 2, 3, 4]


def test_trayectoria_el_jugador_habil_sube_y_satura():
    for modo in MODOS:
        filas = trayectoria_modo(modo, seed=777, habilidad=1.0,
                                 nivel_inicial=1, n_sesiones=6)
        niveles = [f["nivel"] for f in filas]
        assert niveles == sorted(niveles), f"modo {modo}: {niveles}"
        assert niveles[-1] == 4


def test_trayectoria_el_jugador_con_dificultad_baja_y_satura():
    for modo in MODOS:
        filas = trayectoria_modo(modo, seed=777, habilidad=0.0,
                                 nivel_inicial=4, n_sesiones=6)
        niveles = [f["nivel"] for f in filas]
        assert niveles == sorted(niveles, reverse=True), f"modo {modo}: {niveles}"
        assert niveles[-1] == 1

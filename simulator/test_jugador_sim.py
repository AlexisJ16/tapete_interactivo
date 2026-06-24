import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jugador_sim import jugar_sesion


def test_determinismo_misma_entrada_misma_salida():
    a = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=1.0)
    b = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=1.0)
    assert a["scores"] == b["scores"]
    assert a["suggests"] == b["suggests"]


def test_jugador_perfecto_acierta_todo_y_sube():
    r = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=1.0)
    assert r["misses"] == 0
    assert r["hits"] == r["rondas"] > 0
    assert any(s["dir"] == "up" for s in r["suggests"])


def test_jugador_pesimo_falla_todo_y_baja():
    r = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=0.0)
    assert r["hits"] == 0
    assert r["misses"] == r["rondas"] > 0
    assert any(s["dir"] == "down" for s in r["suggests"])

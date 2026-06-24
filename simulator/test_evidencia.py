import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evidencia import barrido_habilidad, barrido_niveles, trayectoria_adaptativa


def test_barrido_habilidad_monotonia_direccion():
    filas = barrido_habilidad(nivel=2, seed=777, habilidades=[0.0, 1.0])
    por_hab = {f["habilidad"]: f for f in filas}
    assert por_hab[1.0]["dir"] == "up"
    assert por_hab[0.0]["dir"] == "down"
    assert por_hab[1.0]["hits"] > por_hab[0.0]["hits"]


def test_barrido_niveles_devuelve_fila_por_nivel():
    filas = barrido_niveles(seed=777, habilidad=1.0, niveles=[1, 2, 3])
    assert [f["nivel"] for f in filas] == [1, 2, 3]
    assert all(f["misses"] == 0 for f in filas)  # jugador perfecto


def test_trayectoria_perfecta_sube_hasta_saturar():
    filas = trayectoria_adaptativa(seed=777, habilidad=1.0, nivel_inicial=1, n_sesiones=6)
    niveles = [f["nivel"] for f in filas]
    assert niveles[0] == 1
    assert niveles[-1] >= niveles[0]
    assert max(niveles) <= 4

"""Integracion de punta a punta (§10.3): dashboard <-> simulador (GameCore.so).

Inicia una sesion, simula una serie de pisadas, y verifica que las metricas se
calculan, se PERSISTEN en SQLite y se exportan a CSV. Headless (sin GUI).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fuente import FuenteCore
from reports import exportar_csv
from sesion import Sesion
from storage import Almacen


class Reloj:
    """Reloj controlable (ms) para que las pisadas caigan en instantes conocidos."""
    def __init__(self):
        self.ms = 0
    def __call__(self):
        return self.ms
    def avanzar(self, d):
        self.ms += d


def test_sesion_velocidad_persiste_metricas_y_csv(tmp_path):
    almacen = Almacen(str(tmp_path / "tapete.sqlite"))
    reloj = Reloj()
    fuente = FuenteCore(reloj=reloj)
    ses = Sesion(almacen, fuente)

    ses.set_perfil("p001", "Juan")
    ses.sembrar(12345)               # objetivos deterministas [3,4,5,3,6]
    ses.configurar(modo=2, nivel=1)
    ses.iniciar()

    # Juega las 5 rondas pisando siempre el LED encendido.
    for _ in range(5):
        ses.bombear()
        encendida = next((c for c in range(1, 7) if ses.leds[c] > 0), None)
        assert encendida is not None
        reloj.avanzar(500)
        fuente.pisar(encendida)
        ses.bombear()

    assert ses.estado == "finished"

    # Persistencia en SQLite.
    s = almacen.sesion(ses.sesion_id)
    assert s["hits"] == 5
    assert s["misses"] == 0
    assert s["rondas"] == 5
    assert s["estado_final"] == "finished"
    assert s["rt_prom_ms"] == 500.0
    assert s["perfil_id"] == "p001"

    evs = almacen.eventos(ses.sesion_id)
    assert any(e["tipo"] == "press" for e in evs)
    assert any(e["tipo"] == "score" for e in evs)

    # Export CSV.
    csv_path = tmp_path / "reporte.csv"
    exportar_csv(almacen, ses.sesion_id, str(csv_path))
    assert csv_path.exists()
    texto = csv_path.read_text(encoding="utf-8")
    assert "hits" in texto and "5" in texto


def test_metricas_con_errores():
    almacen = Almacen(":memory:")
    reloj = Reloj()
    fuente = FuenteCore(reloj=reloj)
    ses = Sesion(almacen, fuente)
    ses.sembrar(12345)               # objetivo inicial = 3
    ses.configurar(modo=2, nivel=1)
    ses.iniciar()
    ses.bombear()

    reloj.avanzar(300)
    fuente.pisar(1)                  # casilla equivocada (objetivo era 3)
    ses.bombear()

    s = almacen.sesion(ses.sesion_id)
    assert s["misses"] == 1
    assert s["hits"] == 0


def test_sesion_acumula_resultados_por_ronda():
    # La vista en vivo necesita saber, ronda a ronda, si fue acierto o error.
    # Sesion lo deriva de los deltas de hits/misses de cada evento score.
    almacen = Almacen(":memory:")
    reloj = Reloj()
    fuente = FuenteCore(reloj=reloj)
    ses = Sesion(almacen, fuente)
    ses.sembrar(12345)               # objetivos [3,4,5,3,6]
    ses.configurar(modo=2, nivel=1)
    ses.iniciar()

    # Ronda 1: acierto (pisa la encendida).
    ses.bombear()
    encendida = next((c for c in range(1, 7) if ses.leds[c] > 0), None)
    assert encendida is not None
    reloj.avanzar(400)
    fuente.pisar(encendida)
    ses.bombear()

    # Ronda 2: error (pisa una casilla que NO es la encendida).
    ses.bombear()
    encendida = next((c for c in range(1, 7) if ses.leds[c] > 0), None)
    assert encendida is not None
    equivocada = 1 if encendida != 1 else 2
    reloj.avanzar(400)
    fuente.pisar(equivocada)
    ses.bombear()

    assert ses.resultados == [True, False]


def test_resultados_se_reinician_al_iniciar():
    almacen = Almacen(":memory:")
    fuente = FuenteCore(reloj=Reloj())
    ses = Sesion(almacen, fuente)
    ses.resultados = [True, False, True]   # residuo de una sesion anterior
    ses.sembrar(12345)
    ses.configurar(modo=2, nivel=1)
    ses.iniciar()
    assert ses.resultados == []


def test_suggest_up_tras_cuatro_aciertos():
    almacen = Almacen(":memory:")
    reloj = Reloj()
    fuente = FuenteCore(reloj=reloj)
    ses = Sesion(almacen, fuente)
    ses.sembrar(12345)                        # objetivos [3,4,5,3,6]
    ses.configurar(modo=2, nivel=1)
    ses.iniciar()
    for _ in range(4):                        # 4 de 5 rondas: sigue corriendo
        ses.bombear()
        encendida = next((c for c in range(1, 7) if ses.leds[c] > 0), None)
        assert encendida is not None
        reloj.avanzar(500)
        fuente.pisar(encendida)
        ses.bombear()
    assert ses.estado == "running"
    assert ses.ultima_sugerencia == {
        "ev": "suggest", "mode": 2, "from": 1, "level": 2,
        "dir": "up", "rate": 100, "window": 4,
    }

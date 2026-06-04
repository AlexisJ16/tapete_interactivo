"""Tests de exportacion de reportes (CSV y PDF)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reports import exportar_csv, exportar_pdf
from storage import Almacen


def _sesion_demo(a: Almacen) -> int:
    a.upsert_perfil("p001", "Juan")
    sid = a.iniciar_sesion("p001", modo=2, nivel=1)
    a.registrar_evento(sid, 400, "press", {"cell": 3})
    a.registrar_evento(sid, 0, "score", {"hits": 1, "misses": 0, "rt_ms": 400, "round": 1})
    a.actualizar_metricas(sid, hits=3, misses=1, rt_prom_ms=420.0, rondas=3)
    a.cerrar_sesion(sid, "finished")
    return sid


def test_exportar_csv(tmp_path):
    a = Almacen(":memory:")
    sid = _sesion_demo(a)
    ruta = str(tmp_path / "rep.csv")
    exportar_csv(a, sid, ruta)
    texto = open(ruta, encoding="utf-8").read()
    assert "hits" in texto
    assert "3" in texto            # hits=3
    assert "press" in texto        # log de eventos
    assert "finished" in texto


def test_exportar_pdf(tmp_path):
    a = Almacen(":memory:")
    sid = _sesion_demo(a)
    ruta = str(tmp_path / "rep.pdf")
    exportar_pdf(a, sid, ruta)
    assert os.path.exists(ruta)
    with open(ruta, "rb") as f:
        cabecera = f.read(5)
    assert cabecera == b"%PDF-"   # PDF valido

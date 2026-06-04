"""Tests de la persistencia SQLite (storage.Almacen)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from storage import Almacen


def test_perfiles_crear_y_listar():
    a = Almacen(":memory:")
    a.upsert_perfil("p001", "Juan")
    a.upsert_perfil("p002", "Ana")
    a.upsert_perfil("p001", "Juan Perez")  # actualiza el nombre
    perfiles = {p["id"]: p["nombre"] for p in a.perfiles()}
    assert perfiles == {"p001": "Juan Perez", "p002": "Ana"}


def test_sesion_ciclo_completo():
    a = Almacen(":memory:")
    a.upsert_perfil("p001", "Juan")
    sid = a.iniciar_sesion("p001", modo=2, nivel=1)
    assert isinstance(sid, int)

    a.registrar_evento(sid, ms=400, tipo="press", datos={"cell": 3})
    a.registrar_evento(sid, ms=400, tipo="score",
                       datos={"hits": 1, "misses": 0, "rt_ms": 400, "round": 1})
    a.actualizar_metricas(sid, hits=1, misses=0, rt_prom_ms=400.0, rondas=1)
    a.cerrar_sesion(sid, estado_final="finished")

    s = a.sesion(sid)
    assert s["modo"] == 2 and s["nivel"] == 1
    assert s["hits"] == 1 and s["misses"] == 0
    assert s["rt_prom_ms"] == 400.0 and s["rondas"] == 1
    assert s["estado_final"] == "finished"
    assert s["fin"] is not None

    evs = a.eventos(sid)
    assert len(evs) == 2
    assert evs[0]["tipo"] == "press" and evs[0]["datos"]["cell"] == 3


def test_listar_sesiones_por_perfil():
    a = Almacen(":memory:")
    a.upsert_perfil("p001", "Juan")
    a.upsert_perfil("p002", "Ana")
    s1 = a.iniciar_sesion("p001", 1, 1)
    a.cerrar_sesion(s1, "finished")
    a.iniciar_sesion("p002", 2, 1)
    assert len(a.sesiones("p001")) == 1
    assert len(a.sesiones()) == 2


def test_persistencia_en_archivo(tmp_path):
    ruta = str(tmp_path / "tapete.sqlite")
    a = Almacen(ruta)
    a.upsert_perfil("p001", "Juan")
    sid = a.iniciar_sesion("p001", 3, 2)
    a.actualizar_metricas(sid, 4, 1, 250.5, 4)
    a.cerrar_sesion(sid, "finished")
    a.cerrar()

    b = Almacen(ruta)  # reabrir
    s = b.sesion(sid)
    assert s["hits"] == 4 and s["rt_prom_ms"] == 250.5 and s["nivel"] == 2

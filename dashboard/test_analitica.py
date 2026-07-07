"""TDD de la agregacion analitica (logica pura, sin Qt).

La analitica LEE del Almacen y devuelve series para graficar; no duplica
logica de GameCore. Es el *dato* de las figuras del dashboard (E2/E4 sobre el
historico real de sesiones), testeable headless.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analitica import serie_evolucion, tasa_acierto, tendencia_ventana  # noqa: E402
from storage import Almacen  # noqa: E402


def test_tasa_acierto():
    assert tasa_acierto({"hits": 3, "misses": 2}) == 60.0
    assert tasa_acierto({"hits": 0, "misses": 0}) == 0.0  # sesion sin jugar
    assert tasa_acierto({"hits": 9, "misses": 1}) == 90.0


def test_serie_evolucion_mapea_solo_las_sesiones_del_perfil():
    a = Almacen(":memory:")
    a.upsert_perfil("p001", "Juan")
    a.upsert_perfil("p002", "Ana")
    # Tres sesiones de Juan con desempeno creciente.
    s1 = a.iniciar_sesion("p001", modo=2, nivel=1)
    a.actualizar_metricas(s1, hits=3, misses=2, rt_prom_ms=800.0, rondas=5)
    a.cerrar_sesion(s1, "finished")
    s2 = a.iniciar_sesion("p001", modo=2, nivel=2)
    a.actualizar_metricas(s2, hits=6, misses=2, rt_prom_ms=600.0, rondas=8)
    a.cerrar_sesion(s2, "finished")
    s3 = a.iniciar_sesion("p001", modo=2, nivel=3)
    a.actualizar_metricas(s3, hits=9, misses=1, rt_prom_ms=500.0, rondas=10)
    a.cerrar_sesion(s3, "finished")
    # Una sesion de Ana que NO debe aparecer en la serie de Juan.
    sa = a.iniciar_sesion("p002", modo=2, nivel=1)
    a.actualizar_metricas(sa, hits=1, misses=4, rt_prom_ms=900.0, rondas=5)

    serie = serie_evolucion(a, "p001")
    assert serie["indices"] == [1, 2, 3]
    assert serie["hits"] == [3, 6, 9]
    assert serie["misses"] == [2, 2, 1]
    assert serie["rt_prom_ms"] == [800.0, 600.0, 500.0]
    assert serie["niveles"] == [1, 2, 3]
    assert serie["tasas"] == [60.0, 75.0, 90.0]


def test_serie_evolucion_perfil_sin_sesiones_es_vacia():
    a = Almacen(":memory:")
    serie = serie_evolucion(a, "fantasma")
    assert serie["indices"] == []
    assert serie["hits"] == []
    assert serie["tasas"] == []


def test_tendencia_ventana_toma_las_ultimas_w():
    # 6 rondas; con W=4 la tendencia mira solo las 4 ultimas (3 aciertos = 75%,
    # el mismo umbral 'subir' que usa el motor).
    res = [True, False, True, True, False, True]
    t = tendencia_ventana(res, w=4)
    assert t["recientes"] == [True, True, False, True]
    assert t["aciertos"] == 3
    assert t["total"] == 4
    assert t["pct"] == 75.0


def test_tendencia_ventana_incompleta_usa_lo_disponible():
    # Menos rondas que la ventana: se muestra lo que hay (aun no comparable al
    # 'rate' del motor, que exige ventana llena).
    t = tendencia_ventana([True, False], w=4)
    assert t["recientes"] == [True, False]
    assert t["aciertos"] == 1
    assert t["total"] == 2
    assert t["pct"] == 50.0


def test_tendencia_ventana_vacia():
    t = tendencia_ventana([], w=4)
    assert t["recientes"] == []
    assert t["aciertos"] == 0
    assert t["total"] == 0
    assert t["pct"] == 0.0

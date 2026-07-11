"""Smoke headless del widget de analitica (PyQt6 + matplotlib, offscreen).

Verifica que el panel construye, grafica el historico de un perfil sin crashear
y exporta la figura a PNG. El *dato* de las series se prueba aparte en
test_analitica.py; aqui solo se valida que la GUI lo dibuja y exporta.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analitica import serie_evolucion  # noqa: E402
from app import PanelAnalitica, VentanaDashboard  # noqa: E402
from fuente import FuenteCore  # noqa: E402
from storage import Almacen  # noqa: E402


def _almacen_con_datos():
    a = Almacen(":memory:")
    a.upsert_perfil("p001", "Juan")
    for i, (h, m, lvl) in enumerate([(3, 2, 1), (6, 2, 2), (9, 1, 3)], 1):
        s = a.iniciar_sesion("p001", modo=2, nivel=lvl)
        a.actualizar_metricas(s, hits=h, misses=m, rt_prom_ms=900.0 - 100 * i, rondas=h + m)
        a.cerrar_sesion(s, "finished")
    return a


_QAPP = None


def _app():
    # Mantener una referencia FUERTE y unica al QApplication: sin ella el
    # wrapper Python se vuelve inestable y crear el FigureCanvas aborta.
    global _QAPP
    from PyQt6 import QtWidgets
    if _QAPP is None:
        _QAPP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    return _QAPP


def test_panel_analitica_grafica_y_exporta(tmp_path):
    _app()
    a = _almacen_con_datos()
    panel = PanelAnalitica(a)
    panel.refrescar()          # llena el combo con los perfiles del almacen
    panel.graficar("p001")     # dibuja sin crashear
    ruta = str(tmp_path / "evolucion.png")
    panel.exportar(ruta)
    assert os.path.exists(ruta) and os.path.getsize(ruta) > 0


def test_panel_analitica_perfil_sin_datos_no_crashea():
    _app()
    panel = PanelAnalitica(Almacen(":memory:"))
    panel.graficar("fantasma")  # sin sesiones: no debe lanzar


def test_dashboard_registra_y_su_analitica_lo_muestra():
    """Integracion end-to-end: una sesion jugada en el dashboard queda en el
    historico que la propia pestaña de analitica grafica (una sola fuente)."""
    _app()
    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.almacen.upsert_perfil("p001", "Juan")     # el niño se elige de la lista, ya no se teclea
    v.recargar_pacientes()
    v.cb_paciente.setCurrentIndex(v.cb_paciente.findData("p001"))
    v.semilla = 12345
    v.cb_modo.setCurrentIndex(1)  # Velocidad
    v.sp_nivel.setValue(1)
    v._start()
    for _ in range(5):
        v.tick()
        enc = next((c for c in range(1, 7) if v.ses.leds[c] > 0), None)
        if enc is None:
            break
        v.fuente.pisar(enc)
        v.tick()

    v.panel.refrescar()  # la pestaña de analitica recarga el historico
    serie = serie_evolucion(v.almacen, "p001")
    assert len(serie["indices"]) == 1
    assert serie["hits"][0] == 5
    assert serie["tasas"][0] == 100.0


def test_ventana_muestra_recomendacion_en_vivo_y_aplica_nivel():
    """Cableado end-to-end: al jugar, el panel de analisis recibe la sugerencia
    del motor y 'Aplicar' manda set_level (el motor nunca cambia el nivel solo)."""
    _app()
    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.semilla = 12345               # objetivos [3,4,5,3,6]
    v.cb_modo.setCurrentIndex(1)    # Velocidad
    v.sp_nivel.setValue(1)
    v._start()
    for _ in range(4):              # 4 aciertos: el motor sugiere subir a nivel 2
        v.tick()
        enc = next((c for c in range(1, 7) if v.ses.leds[c] > 0), None)
        assert enc is not None
        v.fuente.pisar(enc)
        v.tick()

    assert v.ses.ultima_sugerencia.get("dir") == "up"
    assert v.pa.btn_aplicar.isEnabled()          # el panel refleja la sugerencia

    v.pa.btn_aplicar.click()                     # el terapeuta la aplica
    assert v.ses.nivel == 2                       # se mando set_level
    assert v.sp_nivel.value() == 2                # el control se sincronizo

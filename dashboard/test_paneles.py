"""TDD de los paneles de la pantalla del doctor (PyQt6, offscreen).

Cada panel LEE datos ya calculados por Sesion y los muestra; no reimplementa
logica de juego. Se prueban headless: que reflejen los datos, que la tendencia
se derive con la ventana del motor (W=4) y que "Aplicar" emita el nivel sugerido.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paneles import PanelAnalisis, PanelJuego, PanelMetricas  # noqa: E402

_QAPP = None


def _app():
    global _QAPP
    from PyQt6 import QtWidgets
    if _QAPP is None:
        _QAPP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    return _QAPP


# --- PanelJuego -------------------------------------------------------------

def test_panel_juego_refleja_leds_estado_y_ronda():
    _app()
    pj = PanelJuego(on_click=lambda c: None)
    leds = [0, 255, 0, 0, 120, 0, 0]     # indices 1..6; enciende 1 (255) y 4 (120)
    pj.actualizar(leds, estado="running", ronda=6)
    assert pj.celdas[1].nivel == 255
    assert pj.celdas[4].nivel == 120
    assert pj.celdas[2].nivel == 0
    assert "running" in pj.lbl_estado.text().lower()
    assert "6" in pj.lbl_ronda.text()


def test_panel_juego_click_invoca_callback():
    _app()
    pisadas = []
    pj = PanelJuego(on_click=pisadas.append)
    pj.celdas[3].mousePressEvent(None)
    assert pisadas == [3]


# --- PanelMetricas ----------------------------------------------------------

def test_panel_metricas_muestra_valores():
    _app()
    pm = PanelMetricas()
    pm.actualizar(hits=5, misses=1, tasa_pct=83.3, rt_ms=620, ronda=6)
    assert pm.val_aciertos.text() == "5"
    assert pm.val_errores.text() == "1"
    assert "83.3" in pm.val_tasa.text()
    assert "620" in pm.val_rt.text()
    assert pm.val_ronda.text() == "6"


# --- PanelAnalisis ----------------------------------------------------------

def test_panel_analisis_muestra_tendencia_sin_sugerencia():
    _app()
    pa = PanelAnalisis(on_aplicar=lambda n: None)
    pa.actualizar([True, True, False, True], sugerencia={})
    txt = pa.lbl_tendencia.text()
    assert "3" in txt and "4" in txt          # 3/4
    assert not pa.btn_aplicar.isEnabled()      # sin sugerencia: nada que aplicar


def test_panel_analisis_sugerencia_subir_habilita_aplicar():
    _app()
    pa = PanelAnalisis(on_aplicar=lambda n: None)
    sug = {"ev": "suggest", "mode": 2, "from": 2, "level": 3,
           "dir": "up", "rate": 75, "window": 4}
    pa.actualizar([True, True, False, True], sugerencia=sug)
    assert pa.btn_aplicar.isEnabled()
    t = pa.lbl_recom.text().lower()
    assert "sub" in t and "3" in t             # sube a nivel 3


def test_panel_analisis_aplicar_emite_nivel_sugerido():
    _app()
    aplicados = []
    pa = PanelAnalisis(on_aplicar=aplicados.append)
    sug = {"ev": "suggest", "mode": 2, "from": 3, "level": 2,
           "dir": "down", "rate": 25, "window": 4}
    pa.actualizar([False, True, False, False], sugerencia=sug)
    pa.btn_aplicar.click()
    assert aplicados == [2]


def test_panel_analisis_mantener_deshabilita_aplicar():
    _app()
    pa = PanelAnalisis(on_aplicar=lambda n: None)
    sug = {"ev": "suggest", "mode": 2, "from": 2, "level": 2,
           "dir": "keep", "rate": 50, "window": 4}
    pa.actualizar([True, False, True, False], sugerencia=sug)
    assert not pa.btn_aplicar.isEnabled()

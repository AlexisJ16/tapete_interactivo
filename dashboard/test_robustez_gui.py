"""Monkey determinista de la GUI (regresion de robustez).

Bombardea la ventana del dashboard con secuencias aleatorias de acciones
(iniciar/detener/pausar, cambiar modo/nivel, pisar celdas, cambiar de pestana,
tick) y verifica que SOBREVIVE sin crash ni excepcion no capturada.

Regresion concreta: cambiar de modo a mitad de sesion dejaba al GameEngine en
RUNNING con un modo sin iniciar, que emitia `led` con celda corrupta; en el slot
de Qt ese IndexError se convertia en abort ("Python dejo de funcionar").

Test permanente (Fase 3, Task 3.1): parametrizado por varias seeds fijas, cada
una con >= 5000 eventos, para regresion continua en la suite.
"""
import os
import sys
import random

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402
from PyQt6 import QtWidgets  # noqa: E402
from app import VentanaDashboard  # noqa: E402
from fuente import FuenteCore  # noqa: E402
from storage import Almacen  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _monkey(seed, n, fallos):
    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.timer.stop()  # control total del avance (determinismo)
    rng = random.Random(seed)
    acciones = [
        lambda: v.b_start.click(),
        lambda: v.b_stop.click(),
        lambda: v.b_pause.click(),
        lambda: v.cb_modo.setCurrentIndex(rng.randint(0, 2)),
        lambda: v.sp_nivel.setValue(rng.randint(1, 4)),
        lambda: v._click_celda(rng.randint(1, 6)),
        lambda: v.pa.btn_aplicar.click(),
        lambda: v.tabs.setCurrentIndex(rng.randint(0, 1)),
        lambda: v.tick(),
    ]
    for _ in range(n):
        try:
            rng.choice(acciones)()
            _app.processEvents()
        except Exception as e:  # noqa: BLE001
            fallos.append(repr(e))
            break
    v.win.close()


N_EVENTOS = 5000


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_monkey_gui_sobrevive(seed):
    fallos = []

    def hook(t, val, tb):
        fallos.append(repr(val))

    prev = sys.excepthook
    sys.excepthook = hook
    try:
        _monkey(seed, N_EVENTOS, fallos)
    finally:
        sys.excepthook = prev
    assert not fallos, f"la GUI no sobrevivio al monkey (seed={seed}): {fallos[:3]}"

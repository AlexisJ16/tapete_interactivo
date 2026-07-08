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
import logging
import os
import sys
import random
from contextlib import contextmanager

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402
from PyQt6 import QtWidgets  # noqa: E402
from app import VentanaDashboard  # noqa: E402
from fuente import FuenteCore  # noqa: E402
from storage import Almacen  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class _ColectorErroresLogger(logging.Handler):
    """Handler minimo: acumula el mensaje de cada registro ERROR del logger
    'app' -- el mismo logger que usa ejecutar_seguro (robustez.py, ver LOGGER
    en app.py) para registrar cualquier excepcion interna que absorbe SIN
    propagarla. Sin este handler, el monkey solo detecta fallos via
    sys.excepthook (abort real) o su propio try/except externo -- ambos ciegos
    a una excepcion ya atrapada dentro de ejecutar_seguro."""

    def __init__(self, destino):
        super().__init__(level=logging.ERROR)
        self._destino = destino

    def emit(self, record):
        self._destino.append(record.getMessage())


@contextmanager
def _capturar_errores_absorbidos(fallos):
    handler = _ColectorErroresLogger(fallos)
    logger = logging.getLogger("app")
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)


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
        with _capturar_errores_absorbidos(fallos):
            _monkey(seed, N_EVENTOS, fallos)
    finally:
        sys.excepthook = prev
    assert not fallos, f"la GUI no sobrevivio al monkey (seed={seed}): {fallos[:3]}"


def test_monkey_detecta_excepcion_absorbida_por_red_de_seguridad(monkeypatch):
    """Meta-test (cierre de hallazgo Importante, revision de rama sp2): ejecutar_seguro
    (robustez.py) atrapa y loguea CUALQUIER excepcion interna sin propagarla --
    por eso el monkey, que solo veia sys.excepthook + su propio try/except
    externo, se habia vuelto ciego a fallos internos y solo detectaria un
    segfault/abort real (no la regresion original: IndexError en un slot Qt).
    Inyecta una excepcion real en un handler que el monkey ejerce
    (_click_celda_interno) y confirma que SI se detecta."""
    monkeypatch.setattr(
        VentanaDashboard,
        "_click_celda_interno",
        lambda self, celda: (_ for _ in ()).throw(
            IndexError("fallo interno inyectado (regresion 2026)")
        ),
    )
    fallos = []
    with _capturar_errores_absorbidos(fallos):
        _monkey(0, 200, fallos)
    assert fallos, "el monkey deberia detectar la excepcion interna absorbida por ejecutar_seguro"

"""Red de seguridad: ningun test puede quedarse esperando un dialogo modal.

Desde que exportar pregunta DONDE guardar (QFileDialog), un test que pulse "Exportar"
sin parchear el dialogo se quedaria colgado para siempre — headless no hay nadie que
haga clic. Paso de verdad (2026-07-11): colgo la suite entera, y habria colgado el CI
igual que colgo el smoke del .exe.

Por defecto, el dialogo devuelve "" (= el medico pulso Cancelar). El test que quiera
exportar de verdad parchea `_pedir_ruta_guardado` de la ventana o del panel.
"""
import pytest


@pytest.fixture(autouse=True)
def sin_dialogos_modales(monkeypatch):
    from PyQt6 import QtWidgets
    monkeypatch.setattr(QtWidgets.QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: ("", "")))
    monkeypatch.setattr(QtWidgets.QInputDialog, "getText",
                        staticmethod(lambda *a, **k: ("", False)))

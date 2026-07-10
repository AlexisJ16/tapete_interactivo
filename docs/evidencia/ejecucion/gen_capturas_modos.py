"""Captura el dashboard del terapeuta en los TRES modos de juego (Memoria,
Velocidad, Equilibrio), con rotulo quemado en la imagen. Headless (offscreen).

    python docs/evidencia/ejecucion/gen_capturas_modos.py
"""
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CAP = os.path.join(os.path.dirname(__file__), "capturas")
sys.path.insert(0, os.path.dirname(__file__))          # rotular_capturas
sys.path.insert(0, os.path.join(RAIZ, "dashboard"))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PIL import Image                       # noqa: E402
from PyQt6 import QtWidgets                 # noqa: E402
from app import VentanaDashboard           # noqa: E402
from fuente import FuenteCore              # noqa: E402
from storage import Almacen               # noqa: E402
import estilo                              # noqa: E402
from rotular_capturas import poner_banda  # noqa: E402

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
app.setStyleSheet(estilo.QSS)


def captura_modo(idx):
    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.win.resize(980, 680)
    v.win.show()
    v.semilla = 12345
    v.cb_modo.setCurrentIndex(idx)
    etiqueta = v.cb_modo.currentText()                 # p.ej. "2 - Velocidad"
    slug = etiqueta.split("-")[-1].strip().lower().replace(" ", "")
    v.sp_nivel.setValue(1)
    v.in_perfil_nombre.setText("Demo")
    v._start()
    v.tick()
    app.processEvents()
    for _ in range(4):
        enc = next((c for c in range(1, 7) if v.ses.leds[c] > 0), None)
        if enc is None:
            break
        v.fuente.pisar(enc)
        v.tick()
        app.processEvents()

    tmp = os.path.join(CAP, "_tmp_modo.png")
    v.win.grab().save(tmp)
    texto = (f"Dashboard (SOFTWARE) — modo {etiqueta} — conectado al SIMULADOR, "
             f"no al tapete fisico")
    salida = os.path.join(CAP, f"dashboard_modo_{slug}.png")
    poner_banda(Image.open(tmp).convert("RGB"), texto).save(salida)
    os.remove(tmp)
    v.win.close()
    print(f"[modo {etiqueta}] hits={v.ses.hits} -> {os.path.basename(salida)}")


def main():
    for idx in (0, 1, 2):
        captura_modo(idx)


if __name__ == "__main__":
    main()

"""Dashboard del terapeuta (PyQt6).

Vista en vivo del tapete (LEDs blancos, pisadas, puntajes), control de
modo/nivel y perfiles, persistencia en SQLite y exportacion de reportes.

Por defecto embebe el simulador (FuenteCore): el dashboard ES el tapete en
software y se puede "pisar" con el raton. Con --tcp HOST se conecta a un ESP32
real (o a un simulador en red) por el puerto 3333: misma logica, otra IP.

Uso:
  python app.py                 # modo embebido (simulador en proceso)
  python app.py --tcp 192.168.1.50   # conectar a un ESP32 real
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)

from fuente import FuenteCore, FuenteTCP  # noqa: E402
from reports import exportar_csv, exportar_pdf  # noqa: E402
from sesion import Sesion  # noqa: E402
from storage import Almacen  # noqa: E402

NOMBRES_MODO = {1: "Memoria", 2: "Velocidad", 3: "Equilibrio"}


def _qt():
    from PyQt6 import QtCore, QtGui, QtWidgets
    return QtCore, QtGui, QtWidgets


class CeldaLed:
    """Fabrica del widget de una casilla (LED blanco clicable)."""

    @staticmethod
    def crear(celda, on_click):
        QtCore, QtGui, QtWidgets = _qt()

        class _Celda(QtWidgets.QWidget):
            def __init__(self):
                super().__init__()
                self.celda = celda
                self.nivel = 0
                self.setMinimumSize(120, 120)

            def set_nivel(self, n):
                if n != self.nivel:
                    self.nivel = n
                    self.update()

            def paintEvent(self, _):
                p = QtGui.QPainter(self)
                p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
                base = 35
                v = int(base + (255 - base) * (self.nivel / 255.0))
                p.setBrush(QtGui.QColor(v, v, v))           # LED BLANCO: escala de gris
                p.setPen(QtGui.QPen(QtGui.QColor(90, 90, 110), 2))
                r = self.rect().adjusted(6, 6, -6, -6)
                p.drawRoundedRect(r, 16, 16)
                p.setPen(QtGui.QColor(10, 10, 10) if self.nivel > 128 else QtGui.QColor(200, 200, 210))
                f = p.font(); f.setPointSize(26); f.setBold(True); p.setFont(f)
                p.drawText(r, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.celda))

            def mousePressEvent(self, _):
                on_click(self.celda)

        return _Celda()


class VentanaDashboard:
    """Encapsula la ventana principal (sin heredar de Qt para facilitar el smoke)."""

    def __init__(self, fuente=None, almacen=None):
        QtCore, QtGui, QtWidgets = _qt()
        self.QtCore = QtCore
        self.QtWidgets = QtWidgets

        self.almacen = almacen or Almacen(os.path.join(DIR, "tapete.sqlite"))
        self.fuente = fuente or FuenteCore()
        self.ses = Sesion(self.almacen, self.fuente)

        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Tapete Interactivo — Dashboard del terapeuta")
        central = QtWidgets.QWidget()
        self.win.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # --- barra de controles ---
        ctrl = QtWidgets.QHBoxLayout()
        self.in_perfil_id = QtWidgets.QLineEdit("p001")
        self.in_perfil_nombre = QtWidgets.QLineEdit("Juan")
        self.cb_modo = QtWidgets.QComboBox()
        for i in (1, 2, 3):
            self.cb_modo.addItem(f"{i} - {NOMBRES_MODO[i]}", i)
        self.cb_modo.setCurrentIndex(1)  # Velocidad
        self.sp_nivel = QtWidgets.QSpinBox(); self.sp_nivel.setRange(1, 4); self.sp_nivel.setValue(1)
        self.sp_seed = QtWidgets.QSpinBox(); self.sp_seed.setRange(1, 2_000_000_000); self.sp_seed.setValue(12345)
        b_start = QtWidgets.QPushButton("Start")
        b_stop = QtWidgets.QPushButton("Stop")
        b_pause = QtWidgets.QPushButton("Pausa")
        for w, etq in [(self.in_perfil_id, "ID"), (self.in_perfil_nombre, "Nombre")]:
            ctrl.addWidget(QtWidgets.QLabel(etq)); ctrl.addWidget(w)
        ctrl.addWidget(QtWidgets.QLabel("Modo")); ctrl.addWidget(self.cb_modo)
        ctrl.addWidget(QtWidgets.QLabel("Nivel")); ctrl.addWidget(self.sp_nivel)
        ctrl.addWidget(QtWidgets.QLabel("Semilla")); ctrl.addWidget(self.sp_seed)
        ctrl.addWidget(b_start); ctrl.addWidget(b_pause); ctrl.addWidget(b_stop)
        layout.addLayout(ctrl)

        # --- rejilla de LEDs 2x3 ---
        grid = QtWidgets.QGridLayout()
        self.celdas = {}
        for c in range(1, 7):
            w = CeldaLed.crear(c, self._click_celda)
            self.celdas[c] = w
            fila, col = divmod(c - 1, 3)
            grid.addWidget(w, fila, col)
        layout.addLayout(grid)

        # --- HUD de metricas + reportes ---
        self.lbl_estado = QtWidgets.QLabel("Estado: idle")
        self.lbl_score = QtWidgets.QLabel("hits=0  misses=0  rt=0ms  ronda=0")
        b_csv = QtWidgets.QPushButton("Exportar CSV")
        b_pdf = QtWidgets.QPushButton("Exportar PDF")
        hud = QtWidgets.QHBoxLayout()
        hud.addWidget(self.lbl_estado); hud.addWidget(self.lbl_score)
        hud.addStretch(1); hud.addWidget(b_csv); hud.addWidget(b_pdf)
        layout.addLayout(hud)

        # --- conexiones ---
        b_start.clicked.connect(self._start)
        b_stop.clicked.connect(self.ses.detener)
        b_pause.clicked.connect(self.ses.pausar)
        self.cb_modo.currentIndexChanged.connect(self._configurar)
        self.sp_nivel.valueChanged.connect(self._configurar)
        b_csv.clicked.connect(lambda: self._exportar("csv"))
        b_pdf.clicked.connect(lambda: self._exportar("pdf"))

        self._configurar()

        # --- temporizador de sondeo ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(40)

    # --- acciones ---
    def _modo(self):
        return self.cb_modo.currentData()

    def _configurar(self):
        self.ses.configurar(self._modo(), self.sp_nivel.value())

    def _start(self):
        self.ses.set_perfil(self.in_perfil_id.text() or "anon", self.in_perfil_nombre.text() or "")
        self.ses.sembrar(int(self.sp_seed.value()))
        self.ses.configurar(self._modo(), self.sp_nivel.value())
        self.ses.iniciar()

    def _click_celda(self, celda):
        # Solo tiene efecto en modo embebido (FuenteCore): "pisar" con el raton.
        if hasattr(self.fuente, "pisar"):
            self.fuente.pisar(celda)
            self.tick()

    def _exportar(self, fmt):
        if self.ses.sesion_id is None:
            return
        os.makedirs(os.path.join(DIR, "reportes"), exist_ok=True)
        ruta = os.path.join(DIR, "reportes", f"sesion_{self.ses.sesion_id}.{fmt}")
        (exportar_csv if fmt == "csv" else exportar_pdf)(self.almacen, self.ses.sesion_id, ruta)
        self.lbl_estado.setText(f"Exportado: {ruta}")

    def tick(self):
        self.ses.bombear()
        self._refrescar()

    def _refrescar(self):
        for c in range(1, 7):
            self.celdas[c].set_nivel(self.ses.leds[c])
        self.lbl_estado.setText(f"Estado: {self.ses.estado}")
        self.lbl_score.setText(
            f"hits={self.ses.hits}  misses={self.ses.misses}  "
            f"rt={self.ses.ultimo_rt}ms  ronda={self.ses.rondas}"
        )

    def mostrar(self):
        self.win.show()


def smoke() -> int:
    """Valida la GUI sin pantalla (QT_QPA_PLATFORM=offscreen): construye la
    ventana, juega una sesion de Velocidad inyectando pisadas y comprueba que el
    estado se refleja en los widgets."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtCore, QtGui, QtWidgets = _qt()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.sp_seed.setValue(12345)
    v.cb_modo.setCurrentIndex(1)  # Velocidad
    v.sp_nivel.setValue(1)
    v._start()

    for _ in range(5):
        v.tick()
        encendida = next((c for c in range(1, 7) if v.ses.leds[c] > 0), None)
        if encendida is None:
            break
        v.fuente.pisar(encendida)
        v.tick()

    ok = v.ses.estado == "finished" and v.ses.hits == 5
    # El HUD debe reflejar el estado final.
    refleja = "finished" in v.lbl_estado.text()
    print(f"[smoke-app] estado={v.ses.estado} hits={v.ses.hits} hud='{v.lbl_estado.text()}'")
    print("[smoke-app] OK" if (ok and refleja) else "[smoke-app] FALLO")
    del app
    return 0 if (ok and refleja) else 1


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Dashboard del terapeuta")
    p.add_argument("--tcp", metavar="HOST", default=None, help="conectar a un ESP32/simulador por TCP")
    p.add_argument("--puerto", type=int, default=3333)
    args = p.parse_args()

    QtCore, QtGui, QtWidgets = _qt()
    app = QtWidgets.QApplication(sys.argv)
    fuente = FuenteTCP(args.tcp, args.puerto) if args.tcp else FuenteCore()
    v = VentanaDashboard(fuente=fuente)
    v.mostrar()
    return app.exec()


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        sys.exit(smoke())
    sys.exit(main())

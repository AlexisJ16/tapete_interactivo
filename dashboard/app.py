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

from analitica import serie_evolucion  # noqa: E402
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


class PanelAnalitica:
    """Vista de evidencia/historial: evolucion del desempeno por perfil con
    matplotlib embebido. LEE del Almacen via analitica.serie_evolucion (no
    duplica logica de juego). Encapsula el widget para poder probarla headless."""

    def __init__(self, almacen):
        QtCore, QtGui, QtWidgets = _qt()
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure

        self.almacen = almacen
        self.widget = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(self.widget)

        barra = QtWidgets.QHBoxLayout()
        self.cb_perfil = QtWidgets.QComboBox()
        b_refrescar = QtWidgets.QPushButton("Refrescar")
        b_png = QtWidgets.QPushButton("Exportar PNG")
        barra.addWidget(QtWidgets.QLabel("Perfil")); barra.addWidget(self.cb_perfil)
        barra.addWidget(b_refrescar); barra.addStretch(1); barra.addWidget(b_png)
        lay.addLayout(barra)

        self.fig = Figure(figsize=(7, 7.5))
        self.canvas = FigureCanvasQTAgg(self.fig)
        lay.addWidget(self.canvas)
        self.lbl = QtWidgets.QLabel("")
        lay.addWidget(self.lbl)

        b_refrescar.clicked.connect(self.refrescar)
        b_png.clicked.connect(self._exportar_dialogo)
        self.cb_perfil.currentIndexChanged.connect(self._graficar_actual)
        self.refrescar()

    def refrescar(self):
        """Recarga el combo de perfiles desde el almacen y redibuja."""
        actual = self.cb_perfil.currentData()
        self.cb_perfil.blockSignals(True)
        self.cb_perfil.clear()
        for p in self.almacen.perfiles():
            self.cb_perfil.addItem(f"{p['id']} - {p['nombre']}", p["id"])
        if self.cb_perfil.count():
            idx = self.cb_perfil.findData(actual)
            self.cb_perfil.setCurrentIndex(idx if idx >= 0 else 0)
        self.cb_perfil.blockSignals(False)
        self._graficar_actual()

    def _graficar_actual(self):
        pid = self.cb_perfil.currentData()
        if pid:
            self.graficar(pid)

    def graficar(self, perfil_id):
        serie = serie_evolucion(self.almacen, perfil_id)
        self.fig.clear()
        ax1 = self.fig.add_subplot(3, 1, 1)
        ax2 = self.fig.add_subplot(3, 1, 2)
        ax3 = self.fig.add_subplot(3, 1, 3)
        x = serie["indices"]
        if x:
            ax1.plot(x, serie["hits"], "-o", color="tab:green", label="aciertos")
            ax1.plot(x, serie["misses"], "-o", color="tab:red", label="errores")
            ax1.set_ylabel("conteo"); ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.3)
            ax1.set_title(f"Evolucion por sesion — perfil {perfil_id}")

            ax2.plot(x, serie["rt_prom_ms"], "-o", color="tab:purple")
            ax2.set_ylabel("t. respuesta (ms)")
            ax2.grid(True, alpha=0.3)
            ax2.set_title("Tiempo de respuesta promedio")

            ax3.plot(x, serie["tasas"], "-o", color="tab:blue", label="acierto (%)")
            ax3b = ax3.twinx()
            ax3b.plot(x, serie["niveles"], "--s", color="tab:orange", label="nivel")
            ax3.set_xlabel("sesion"); ax3.set_ylabel("acierto (%)")
            ax3b.set_ylabel("nivel")
            ax3.set_ylim(0, 105); ax3b.set_ylim(0.5, 4.5); ax3b.set_yticks([1, 2, 3, 4])
            ax3.grid(True, alpha=0.3)
            ax3.set_title("Adaptacion: acierto vs nivel sugerido")
        else:
            for ax in (ax1, ax2, ax3):
                ax.set_axis_off()
            ax1.text(0.5, 0.5, "Sin sesiones para este perfil",
                     ha="center", va="center")
        self.fig.tight_layout()
        self.canvas.draw()

    def exportar(self, ruta):
        self.fig.savefig(ruta, dpi=120)

    def _exportar_dialogo(self):
        os.makedirs(os.path.join(DIR, "reportes"), exist_ok=True)
        pid = self.cb_perfil.currentData() or "perfil"
        ruta = os.path.join(DIR, "reportes", f"evolucion_{pid}.png")
        self.exportar(ruta)
        self.lbl.setText(f"Exportado: {ruta}")


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
        self.tabs = QtWidgets.QTabWidget()
        self.win.setCentralWidget(self.tabs)
        en_vivo = QtWidgets.QWidget()
        self.tabs.addTab(en_vivo, "En vivo")
        layout = QtWidgets.QVBoxLayout(en_vivo)

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

        # --- pestaña de analitica (historico por perfil) ---
        self.panel = PanelAnalitica(self.almacen)
        self.tabs.addTab(self.panel.widget, "Analitica")
        # al entrar a la pestaña, recarga con las sesiones nuevas
        self.tabs.currentChanged.connect(
            lambda i: self.panel.refrescar() if self.tabs.tabText(i) == "Analitica" else None
        )

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

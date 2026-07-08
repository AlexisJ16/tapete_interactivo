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

import logging
import os
import sqlite3
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)

from analitica import serie_evolucion, tasa_acierto  # noqa: E402
from estilo import QSS, GRAFICO  # noqa: E402
from fuente import FuenteCore, construir_fuente  # noqa: E402
from paneles import PanelAnalisis, PanelJuego, PanelMetricas  # noqa: E402
from reports import ReporteError, exportar_csv, exportar_pdf  # noqa: E402
from robustez import ejecutar_seguro, instalar_excepthook  # noqa: E402
from sesion import Sesion  # noqa: E402
from storage import Almacen, AlmacenError  # noqa: E402

NOMBRES_MODO = {1: "Memoria", 2: "Velocidad", 3: "Equilibrio"}
SEMILLA_DEFECTO = 12345   # reproducibilidad del RNG; no es un control clinico
LOGGER = logging.getLogger(__name__)


def _qt():
    from PyQt6 import QtCore, QtGui, QtWidgets
    return QtCore, QtGui, QtWidgets


def _abrir_almacen(ruta: str, on_degradado=None) -> Almacen:
    """Abre el almacen SQLite en 'ruta'. Si falla (DB corrupta, directorio
    inexistente), degrada a un almacen en memoria con un aviso visible en vez
    de abortar el arranque de la GUI (sin persistencia entre sesiones, pero el
    terapeuta puede seguir usando el tapete). 'on_degradado', si se pasa, se
    llama con el mensaje de error para que el llamador refleje la degradacion
    en la UI (Task 4.2), ademas del aviso por stderr (ya cubierto en 2.4)."""
    try:
        return Almacen(ruta)
    except AlmacenError as e:
        print(f"AVISO: {e} — se usara un almacen en memoria (sin persistencia)",
              file=sys.stderr)
        if on_degradado is not None:
            on_degradado(str(e))
        return Almacen(":memory:")


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
        ejecutar_seguro(self._refrescar_interno, LOGGER)

    def _refrescar_interno(self):
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
        ejecutar_seguro(self._graficar_actual_interno, LOGGER)

    def _graficar_actual_interno(self):
        pid = self.cb_perfil.currentData()
        if pid:
            self.graficar(pid)

    def graficar(self, perfil_id):
        serie = serie_evolucion(self.almacen, perfil_id)
        self.fig.clear()
        self.fig.patch.set_facecolor(GRAFICO["fondo"])   # integra la figura con el fondo del tab
        ax1 = self.fig.add_subplot(3, 1, 1)
        ax2 = self.fig.add_subplot(3, 1, 2)
        ax3 = self.fig.add_subplot(3, 1, 3)
        x = serie["indices"]
        if x:
            ax1.plot(x, serie["hits"], "-o", color=GRAFICO["aciertos"], label="aciertos")
            ax1.plot(x, serie["misses"], "-o", color=GRAFICO["errores"], label="errores")
            ax1.set_ylabel("conteo"); ax1.legend(loc="upper left")
            ax1.set_title(f"Evolucion por sesion — perfil {perfil_id}")

            ax2.plot(x, serie["rt_prom_ms"], "-o", color=GRAFICO["rt"])
            ax2.set_ylabel("t. respuesta (ms)")
            ax2.set_title("Tiempo de respuesta promedio")

            ax3.plot(x, serie["tasas"], "-o", color=GRAFICO["tasa"], label="acierto (%)")
            ax3b = ax3.twinx()
            ax3b.plot(x, serie["niveles"], "--s", color=GRAFICO["nivel"], label="nivel")
            ax3.set_xlabel("sesion"); ax3.set_ylabel("acierto (%)")
            ax3b.set_ylabel("nivel")
            ax3.set_ylim(0, 105); ax3b.set_ylim(0.5, 4.5); ax3b.set_yticks([1, 2, 3, 4])
            ax3.set_title("Adaptacion: acierto vs nivel sugerido")
            # Mismos ejes claros y grid tenue en las tres graficas (paleta clinica).
            for ax in (ax1, ax2, ax3):
                ax.set_facecolor("#FFFFFF")
                ax.grid(True, alpha=0.3, color=GRAFICO["grid"])
                ax.title.set_color(GRAFICO["tinta"])
        else:
            for ax in (ax1, ax2, ax3):
                ax.set_axis_off()
            ax1.text(0.5, 0.5, "Sin sesiones para este perfil",
                     ha="center", va="center", color=GRAFICO["tinta"])
        self.fig.tight_layout()
        self.canvas.draw()

    def exportar(self, ruta):
        self.fig.savefig(ruta, dpi=120)

    def _exportar_dialogo(self):
        ejecutar_seguro(self._exportar_dialogo_interno, LOGGER)

    def _exportar_dialogo_interno(self):
        os.makedirs(os.path.join(DIR, "reportes"), exist_ok=True)
        pid = self.cb_perfil.currentData() or "perfil"
        ruta = os.path.join(DIR, "reportes", f"evolucion_{pid}.png")
        self.exportar(ruta)
        self.lbl.setText(f"Exportado: {ruta}")


class _AlmacenSesion:
    """Envuelve el almacen real solo para las escrituras que hace Sesion
    (actualizar_metricas/registrar_evento): reenvia todo lo demas via
    __getattr__ (duck typing, igual que Fuente) y avisa con 'marcar(ok)' si
    cada escritura tuvo exito o fallo. Necesario porque, entre eventos
    score/press, bombear() no escribe nada -- "el tick no lanzo" no implica
    "la DB esta sana" (Finding 1, Task 4.2: la degradacion de almacen debe
    ser pegajoso hasta la proxima escritura exitosa, no hasta el proximo tick
    cualquiera). Busca el metodo real con getattr() en cada llamada (no lo
    ata en el constructor) para seguir funcionando si un test monkeypatchea
    el metodo despues de crear la ventana."""

    def __init__(self, real, marcar):
        self._real = real
        self._marcar = marcar

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)

    def actualizar_metricas(self, *a, **kw):
        return self._escribir("actualizar_metricas", a, kw)

    def registrar_evento(self, *a, **kw):
        return self._escribir("registrar_evento", a, kw)

    def _escribir(self, nombre, a, kw):
        try:
            resultado = getattr(self._real, nombre)(*a, **kw)
        except sqlite3.Error:
            self._marcar(False)
            raise
        self._marcar(True)
        return resultado


class VentanaDashboard:
    """Encapsula la ventana principal (sin heredar de Qt para facilitar el smoke)."""

    def __init__(self, fuente=None, almacen=None):
        QtCore, QtGui, QtWidgets = _qt()
        self.QtCore = QtCore
        self.QtWidgets = QtWidgets

        # --- estado de degradacion (Task 4.2): cuatro motivos independientes
        # que el indicador de conexion combina. '_degradado_almacen' (fallo al
        # ABRIR el archivo de DB) y '_degradado_almacen_escritura' (fallo al
        # ESCRIBIR ya con la sesion en curso) son pegajosos cada uno por su
        # lado -- el primero no se limpia nunca (la apertura ya cayo a
        # memoria toda la sesion); el segundo se limpia solo cuando una
        # escritura vuelve a tener exito (Finding 1: un tick ocioso sin
        # escrituras no cuenta como "recuperado"). Los otros dos se
        # recalculan en cada tick.
        self._degradado_almacen = False
        if almacen is not None:
            self.almacen = almacen
        else:
            self.almacen = _abrir_almacen(
                os.path.join(DIR, "tapete.sqlite"),
                on_degradado=lambda motivo: setattr(self, "_degradado_almacen", True),
            )
        self._degradado_almacen_escritura = False
        self._degradado_error = False
        self._degradado_transporte = False
        self.fuente = fuente or FuenteCore()
        self.ses = Sesion(_AlmacenSesion(self.almacen, self._marcar_escritura_almacen), self.fuente)
        self.semilla = SEMILLA_DEFECTO   # fuera de la vista del doctor

        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Tapete Interactivo — Pantalla del terapeuta")
        self.tabs = QtWidgets.QTabWidget()
        self.win.setCentralWidget(self.tabs)

        # ===== Pestaña "En vivo": controles + juego | metricas / analisis =====
        en_vivo = QtWidgets.QWidget()
        self.tabs.addTab(en_vivo, "En vivo")
        raiz = QtWidgets.QVBoxLayout(en_vivo)
        raiz.setContentsMargins(18, 16, 18, 14)   # aire deliberado alrededor del contenido
        raiz.setSpacing(14)

        # --- barra de controles (sin semilla: no es clinica) ---
        ctrl = QtWidgets.QHBoxLayout()
        ctrl.setSpacing(8)
        self.in_perfil_id = QtWidgets.QLineEdit("p001"); self.in_perfil_id.setMaximumWidth(90)
        self.in_perfil_nombre = QtWidgets.QLineEdit("Juan"); self.in_perfil_nombre.setMaximumWidth(150)
        self.cb_modo = QtWidgets.QComboBox()
        for i in (1, 2, 3):
            self.cb_modo.addItem(f"{i} - {NOMBRES_MODO[i]}", i)
        self.cb_modo.setCurrentIndex(1)  # Velocidad
        self.sp_nivel = QtWidgets.QSpinBox(); self.sp_nivel.setRange(1, 4); self.sp_nivel.setValue(1)
        self.b_start = QtWidgets.QPushButton("Iniciar"); self.b_start.setObjectName("start")
        self.b_pause = QtWidgets.QPushButton("Pausa")
        self.b_stop = QtWidgets.QPushButton("Detener"); self.b_stop.setObjectName("stop")
        for w, etq in [(self.in_perfil_id, "Niño (ID)"), (self.in_perfil_nombre, "Nombre")]:
            ctrl.addWidget(QtWidgets.QLabel(etq)); ctrl.addWidget(w)
        ctrl.addWidget(QtWidgets.QLabel("Modo")); ctrl.addWidget(self.cb_modo)
        ctrl.addWidget(QtWidgets.QLabel("Nivel")); ctrl.addWidget(self.sp_nivel)
        ctrl.addStretch(1)
        ctrl.addWidget(self.b_start); ctrl.addWidget(self.b_pause); ctrl.addWidget(self.b_stop)
        raiz.addLayout(ctrl)

        # --- cuerpo: juego (izq, grande) | metricas (arriba) + analisis (abajo) ---
        self.pj = PanelJuego(on_click=self._click_celda)
        self.pm = PanelMetricas()
        self.pa = PanelAnalisis(on_aplicar=self._aplicar_nivel)

        derecha = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        derecha.addWidget(self.pm.widget)
        derecha.addWidget(self.pa.widget)
        derecha.setSizes([300, 300])          # dos partes iguales

        cuerpo = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        cuerpo.addWidget(self.pj.widget)
        cuerpo.addWidget(derecha)
        cuerpo.setStretchFactor(0, 3)          # el juego, mas grande
        cuerpo.setStretchFactor(1, 2)
        cuerpo.setSizes([640, 420])
        raiz.addWidget(cuerpo, 1)

        # --- franja inferior: estado de conexion + export discreto ---
        pie = QtWidgets.QHBoxLayout()
        pie.setSpacing(8)
        self.lbl_estado_conexion = QtWidgets.QLabel("")
        self.lbl_estado_conexion.setObjectName("estadoConexion")
        self.lbl_export = QtWidgets.QLabel("")
        self.lbl_export.setObjectName("export")
        b_csv = QtWidgets.QPushButton("Exportar CSV")
        b_pdf = QtWidgets.QPushButton("Exportar PDF")
        pie.addWidget(self.lbl_estado_conexion)
        pie.addWidget(self.lbl_export); pie.addStretch(1)
        pie.addWidget(b_csv); pie.addWidget(b_pdf)
        raiz.addLayout(pie)

        # ===== Pestaña "Historico" (evolucion por perfil) =====
        self.panel = PanelAnalitica(self.almacen)
        self.tabs.addTab(self.panel.widget, "Historico")
        self.tabs.currentChanged.connect(
            lambda i: self.panel.refrescar() if self.tabs.tabText(i) == "Historico" else None
        )

        # --- conexiones ---
        self.b_start.clicked.connect(self._start)
        # ses.detener/pausar viven en sesion.py (fuera de alcance de esta tarea):
        # se envuelven en el punto de conexion, no se puede tocar su cuerpo.
        self.b_stop.clicked.connect(lambda: ejecutar_seguro(self.ses.detener, LOGGER))
        self.b_pause.clicked.connect(lambda: ejecutar_seguro(self.ses.pausar, LOGGER))
        self.cb_modo.currentIndexChanged.connect(self._configurar)
        self.sp_nivel.valueChanged.connect(self._configurar)
        b_csv.clicked.connect(lambda: self._exportar("csv"))
        b_pdf.clicked.connect(lambda: self._exportar("pdf"))
        self._configurar()
        self._actualizar_estado_conexion()   # refleja desde ya un almacen degradado al abrir

        # --- temporizador de sondeo (25 Hz) ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(40)

    # --- indicador de conexion/degradacion (Task 4.2) ---
    def _fuente_conectada(self) -> bool:
        # FuenteTCP expone 'sock' (None mientras reconecta tras una caida del
        # ESP32); FuenteCore/FuenteSerial no tienen esa nocion de transporte y
        # se asumen conectadas siempre (de ahi el default True).
        return getattr(self.fuente, "sock", True) is not None

    def _marcar_escritura_almacen(self, ok: bool) -> None:
        # No llama a _actualizar_estado_conexion() aqui: el tick que dispara la
        # escritura ya la llama al final (via _tick_interno o, si la escritura
        # lanzo y aborto el tick, via _marcar_error_tick).
        self._degradado_almacen_escritura = not ok

    def _actualizar_estado_conexion(self) -> None:
        motivos = []
        if self._degradado_error:
            motivos.append("error en tick")
        if self._degradado_transporte:
            motivos.append("fuente desconectada")
        if self._degradado_almacen:
            motivos.append("almacen en memoria")
        if self._degradado_almacen_escritura:
            motivos.append("fallo de escritura en almacen")
        if motivos:
            self.lbl_estado_conexion.setText("Degradado: " + ", ".join(motivos))
            estado = "degradado"
        else:
            self.lbl_estado_conexion.setText("Conectado")
            estado = "ok"
        # El color sale del QSS (chip [estado]); re-polish solo al cambiar de estado
        # (no en cada tick), mismo patron que el chip del panel de juego.
        if estado != getattr(self, "_estado_conexion_pintado", None):
            self._estado_conexion_pintado = estado
            self.lbl_estado_conexion.setProperty("estado", estado)
            st = self.lbl_estado_conexion.style()
            st.unpolish(self.lbl_estado_conexion); st.polish(self.lbl_estado_conexion)

    def _marcar_error_tick(self, exc) -> None:
        self._degradado_error = True
        self._actualizar_estado_conexion()

    # --- acciones ---
    def _modo(self):
        return self.cb_modo.currentData()

    def _configurar(self):
        ejecutar_seguro(self._configurar_interno, LOGGER)

    def _configurar_interno(self):
        self.ses.configurar(self._modo(), self.sp_nivel.value())

    def _start(self):
        ejecutar_seguro(self._start_interno, LOGGER)

    def _start_interno(self):
        # Doble start (sesion ya en curso): ignorar. Sin esta guarda, set_perfil/
        # sembrar/configurar reenviarian set_seed/set_mode a mitad de partida (la
        # segunda reinicia el RNG y el modo) y ses.iniciar() crearia una fila
        # SQLite huerfana ademas de resetear las metricas en curso.
        # bombear() drena antes de decidir: el "state":"running" del primer start
        # ya esta encolado en el core aunque el timer de 25 Hz no haya corrido
        # todavia (dos clics sin tick de por medio no deben burlar la guarda).
        self.ses.bombear()
        if self.ses.estado in ("running", "paused"):
            return
        self.ses.set_perfil(self.in_perfil_id.text() or "anon", self.in_perfil_nombre.text() or "")
        self.ses.sembrar(self.semilla)
        self.ses.configurar(self._modo(), self.sp_nivel.value())
        self.ses.iniciar()

    def _aplicar_nivel(self, nivel):
        ejecutar_seguro(lambda: self._aplicar_nivel_interno(nivel), LOGGER)

    def _aplicar_nivel_interno(self, nivel):
        # Aplica la recomendacion del motor con set_level (efectivo la ronda
        # siguiente, sin recrear el modo). No re-disparar _configurar (set_mode).
        self.ses.set_nivel(nivel)
        self.sp_nivel.blockSignals(True)
        self.sp_nivel.setValue(nivel)
        self.sp_nivel.blockSignals(False)

    def _click_celda(self, celda):
        ejecutar_seguro(lambda: self._click_celda_interno(celda), LOGGER)

    def _click_celda_interno(self, celda):
        # Solo tiene efecto en modo embebido (FuenteCore): "pisar" con el raton.
        if hasattr(self.fuente, "pisar"):
            self.fuente.pisar(celda)
            self.tick()

    def _exportar(self, fmt):
        ejecutar_seguro(lambda: self._exportar_interno(fmt), LOGGER)

    def _exportar_interno(self, fmt):
        if self.ses.sesion_id is None:
            return
        ruta = os.path.join(DIR, "reportes", f"sesion_{self.ses.sesion_id}.{fmt}")
        try:
            os.makedirs(os.path.join(DIR, "reportes"), exist_ok=True)
            (exportar_csv if fmt == "csv" else exportar_pdf)(self.almacen, self.ses.sesion_id, ruta)
        except (OSError, ReporteError) as e:
            # Frontera GUI: un fallo de E/S (makedirs o export) degrada a mensaje, no crashea.
            self.lbl_export.setText(f"Error al exportar: {e}")
            return
        self.lbl_export.setText(f"Exportado: {ruta}")

    def tick(self):
        ejecutar_seguro(self._tick_interno, LOGGER, on_error=self._marcar_error_tick)

    def _tick_interno(self):
        self.ses.bombear()
        # Si bombear() no lanzo (fuente y almacen respondieron), el tick esta
        # sano: limpia el error previo y recalcula el estado del transporte.
        self._degradado_error = False
        self._degradado_transporte = not self._fuente_conectada()
        self._actualizar_estado_conexion()
        self._refrescar()

    def _refrescar(self):
        self.pj.actualizar(self.ses.leds, self.ses.estado, self.ses.rondas)
        tasa = tasa_acierto({"hits": self.ses.hits, "misses": self.ses.misses})
        self.pm.actualizar(self.ses.hits, self.ses.misses, tasa,
                           self.ses.ultimo_rt, self.ses.rondas)
        self.pa.actualizar(self.ses.resultados, self.ses.ultima_sugerencia)

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
    v.semilla = 12345
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
    # El panel de juego debe reflejar el estado final.
    refleja = "finished" in v.pj.lbl_estado.text()
    print(f"[smoke-app] estado={v.ses.estado} hits={v.ses.hits} juego='{v.pj.lbl_estado.text()}'")
    print("[smoke-app] OK" if (ok and refleja) else "[smoke-app] FALLO")
    del app
    return 0 if (ok and refleja) else 1


def _elegir_puerto_com(puertos):
    """Selector minimo cuando hay varios CP210x (raro). GUI, no se testea."""
    QtCore, QtGui, QtWidgets = _qt()
    elegido, ok = QtWidgets.QInputDialog.getItem(
        None, "Tapete", "Elige el puerto del tapete:", puertos, 0, False)
    return elegido if ok else puertos[0]


def main() -> int:
    import argparse

    from puertos import resolver_puerto_serial
    p = argparse.ArgumentParser(description="Dashboard del terapeuta")
    p.add_argument("--tcp", metavar="HOST", default=None, help="conectar a un ESP32/simulador por TCP")
    p.add_argument("--serial", metavar="PUERTO", default=None,
                   help="conectar por USB/Serial: un puerto (COM3) o 'auto' (detecta el tapete)")
    p.add_argument("--puerto", type=int, default=3333)
    args = p.parse_args()

    instalar_excepthook(LOGGER)
    QtCore, QtGui, QtWidgets = _qt()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(QSS)
    if args.serial is not None:
        pedido = args.serial
        args.serial = resolver_puerto_serial(args.serial, elegir=_elegir_puerto_com)
        if pedido == "auto" and args.serial is None:
            QtWidgets.QMessageBox.information(
                None, "Tapete",
                "No se detecto el tapete por USB. Se abre en modo practica.\n"
                "Conecta el tapete y vuelve a abrir; si Windows no lo reconoce, "
                "instala el driver incluido (CP210x).")
    fuente = construir_fuente(tcp=args.tcp, serial=args.serial, puerto=args.puerto)
    v = VentanaDashboard(fuente=fuente)
    v.mostrar()
    return app.exec()


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        sys.exit(smoke())
    sys.exit(main())

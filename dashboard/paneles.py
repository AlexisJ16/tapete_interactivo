"""Paneles de la pantalla del doctor (PyQt6).

Cada panel es un widget enfocado que LEE datos ya calculados por Sesion y los
muestra; no reimplementa logica de juego. Se ensamblan en app.py. Los nombres de
objeto (objectName) los usa la hoja de estilos para el pulido visual.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analitica import tendencia_ventana  # noqa: E402


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
                base = 44                                    # ficha apagada, sobre tablero oscuro
                v = int(base + (255 - base) * (self.nivel / 255.0))
                p.setBrush(QtGui.QColor(v, v, v))            # LED BLANCO: escala de gris
                # Borde teal claro cuando esta encendida (acento de marca); neutro si no.
                borde = QtGui.QColor(120, 205, 195) if self.nivel > 60 else QtGui.QColor(74, 86, 104)
                p.setPen(QtGui.QPen(borde, 3 if self.nivel > 60 else 2))
                r = self.rect().adjusted(7, 7, -7, -7)
                p.drawRoundedRect(r, 18, 18)
                p.setPen(QtGui.QColor(20, 24, 30) if self.nivel > 128 else QtGui.QColor(150, 160, 172))
                f = p.font(); f.setPointSize(26); f.setBold(True); p.setFont(f)
                p.drawText(r, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.celda))

            def mousePressEvent(self, _):
                on_click(self.celda)

        return _Celda()


class PanelJuego:
    """El juego en vivo: rejilla 2x3 de LEDs + estado y ronda. Con FuenteCore es
    'pisable' con el raton (on_click)."""

    def __init__(self, on_click):
        QtCore, QtGui, QtWidgets = _qt()
        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName("panelJuego")
        lay = QtWidgets.QVBoxLayout(self.widget)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(14)
        self.celdas = {}
        for c in range(1, 7):
            w = CeldaLed.crear(c, on_click)
            self.celdas[c] = w
            fila, col = divmod(c - 1, 3)
            grid.addWidget(w, fila, col)
        lay.addLayout(grid, 1)

        info = QtWidgets.QHBoxLayout()
        self.lbl_estado = QtWidgets.QLabel("Estado: idle")
        self.lbl_estado.setObjectName("estadoJuego")
        self.lbl_estado.setProperty("estado", "idle")   # color inicial coincide con el 1er render
        self._estado_pintado = "idle"
        self.lbl_ronda = QtWidgets.QLabel("Ronda 0")
        self.lbl_ronda.setObjectName("rondaJuego")
        info.addWidget(self.lbl_estado); info.addStretch(1); info.addWidget(self.lbl_ronda)
        lay.addLayout(info)

    def actualizar(self, leds, estado, ronda):
        for c in range(1, 7):
            self.celdas[c].set_nivel(leds[c])
        # El texto conserva la palabra de estado en minuscula (la leen los tests).
        self.lbl_estado.setText(f"Estado: {estado}")
        self.lbl_ronda.setText(f"Ronda {ronda}")
        if estado != self._estado_pintado:
            # Color del chip via propiedad [estado]; re-polish solo al cambiar
            # (no en cada refresco de 25 Hz), igual que PanelAnalisis._pintar_dir.
            self._estado_pintado = estado
            self.lbl_estado.setProperty("estado", estado)
            st = self.lbl_estado.style()
            st.unpolish(self.lbl_estado); st.polish(self.lbl_estado)


class PanelMetricas:
    """Tarjetas de metricas de la sesion en curso (widgets Qt, sin matplotlib:
    se refresca a 25 Hz)."""

    def __init__(self):
        QtCore, QtGui, QtWidgets = _qt()
        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName("panelMetricas")
        lay = QtWidgets.QGridLayout(self.widget)
        lay.setSpacing(12)
        self.val_aciertos = self._tarjeta(lay, 0, 0, "Aciertos", "aciertos")
        self.val_errores = self._tarjeta(lay, 0, 1, "Errores", "errores")
        self.val_tasa = self._tarjeta(lay, 1, 0, "Tasa de acierto", "tasa")
        self.val_rt = self._tarjeta(lay, 1, 1, "Reaccion (ms)", "rt")
        self.val_ronda = self._tarjeta(lay, 2, 0, "Ronda", "ronda", colspan=2)

    def _tarjeta(self, lay, r, c, rotulo, nombre, colspan=1):
        QtCore, QtGui, QtWidgets = _qt()
        caja = QtWidgets.QFrame()
        caja.setObjectName("tarjeta")
        caja.setProperty("clase", nombre)
        v = QtWidgets.QVBoxLayout(caja)
        val = QtWidgets.QLabel("0")
        val.setObjectName("valor")
        val.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        rot = QtWidgets.QLabel(rotulo.upper())
        rot.setObjectName("rotulo")
        rot.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        v.addWidget(val); v.addWidget(rot)
        lay.addWidget(caja, r, c, 1, colspan)
        return val

    def actualizar(self, hits, misses, tasa_pct, rt_ms, ronda):
        self.val_aciertos.setText(str(hits))
        self.val_errores.setText(str(misses))
        self.val_tasa.setText(f"{tasa_pct:.1f}%")
        self.val_rt.setText(str(rt_ms))
        self.val_ronda.setText(str(ronda))


class PanelAnalisis:
    """Apoyo a la decision: tendencia reciente (ventana W=4, igual que el motor)
    y la recomendacion de nivel del motor (evento suggest). El terapeuta la
    aplica con un clic; el motor nunca cambia el nivel solo."""

    def __init__(self, on_aplicar):
        QtCore, QtGui, QtWidgets = _qt()
        self._on_aplicar = on_aplicar
        self._nivel_sugerido = None
        self._dir = None          # ultima direccion pintada (evita re-polish por frame)
        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName("panelAnalisis")
        lay = QtWidgets.QVBoxLayout(self.widget)

        self.lbl_tendencia = QtWidgets.QLabel("Aciertos recientes: — (sin rondas aun)")
        self.lbl_tendencia.setObjectName("tendencia")
        self.lbl_recom = QtWidgets.QLabel("Sin recomendacion todavia")
        self.lbl_recom.setObjectName("recomendacion")
        self.lbl_recom.setWordWrap(True)
        self.btn_aplicar = QtWidgets.QPushButton("Aplicar")
        self.btn_aplicar.setObjectName("aplicar")
        self.btn_aplicar.setEnabled(False)
        self.btn_aplicar.clicked.connect(self._aplicar)

        lay.addWidget(self.lbl_tendencia)
        lay.addWidget(self.lbl_recom)
        lay.addWidget(self.btn_aplicar)
        lay.addStretch(1)

    def _aplicar(self):
        if self._nivel_sugerido is not None:
            self._on_aplicar(self._nivel_sugerido)

    def actualizar(self, resultados, sugerencia):
        t = tendencia_ventana(resultados)
        if t["total"]:
            puntos = "".join("●" if r else "○" for r in t["recientes"])
            self.lbl_tendencia.setText(
                f"Aciertos recientes: {puntos}  ({t['aciertos']}/{t['total']} = {t['pct']:.0f}%)"
            )
        else:
            self.lbl_tendencia.setText("Aciertos recientes: — (sin rondas aun)")

        sug = sugerencia if isinstance(sugerencia, dict) else {}
        direccion = sug.get("dir")
        nivel = sug.get("level")
        if direccion in ("up", "down") and isinstance(nivel, int) and not isinstance(nivel, bool):
            verbo = "Subir" if direccion == "up" else "Bajar"
            rate, ventana = sug.get("rate", "?"), sug.get("window", "?")
            self._nivel_sugerido = nivel
            self.lbl_recom.setText(
                f"Sugerencia: {verbo} a nivel {nivel}  "
                f"(acierto {rate}% en {ventana} rondas)"
            )
            self.btn_aplicar.setText(f"Aplicar: {verbo.lower()} a nivel {nivel}")
            self.btn_aplicar.setEnabled(True)
            self._pintar_dir(direccion)
        else:
            self._nivel_sugerido = None
            if direccion == "keep":
                self.lbl_recom.setText("Recomendacion: mantener el nivel actual")
            self.btn_aplicar.setText("Aplicar")
            self.btn_aplicar.setEnabled(False)
            self._pintar_dir("keep")

    def _pintar_dir(self, direccion):
        # El color de la recomendacion y del boton salen del selector [dir=...]
        # de la hoja; solo re-polish al cambiar (no en cada frame del temporizador).
        if direccion == self._dir:
            return
        self._dir = direccion
        for w in (self.lbl_recom, self.btn_aplicar):
            w.setProperty("dir", direccion)
            w.style().unpolish(w)
            w.style().polish(w)

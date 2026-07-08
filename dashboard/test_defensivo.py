"""Programación defensiva en los boundaries del dashboard.

Todo dato externo (eventos del protocolo, líneas crudas del serial/TCP) se valida
al entrar: una entrada malformada NUNCA debe lanzar ni corromper el estado. La
fuente puede ser el ESP32 real, cuyo serial mezcla ruido/basura con los eventos.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6 import QtWidgets  # noqa: E402
from app import VentanaDashboard  # noqa: E402
from fuente import FuenteCore  # noqa: E402
from sesion import Sesion  # noqa: E402
from storage import Almacen  # noqa: E402

# Referencia fuerte al QApplication: sin ella, destruir widgets Qt en el teardown
# segfaultea (misma razon por la que los smokes headless mantienen un global).
_APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _ses():
    return Sesion(Almacen(":memory:"), FuenteCore())


def _ventana():
    """Ventana headless con control total del avance (sin timer de fondo),
    igual patron que test_robustez_gui.py."""
    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.timer.stop()
    return v


def test_led_con_celda_fuera_de_rango_no_lanza_ni_corrompe():
    ses = _ses()
    for cell in (0, 7, 999, -5, "x", None, 1.5):
        ses._procesar({"ev": "led", "cell": cell, "level": 100})
    assert ses.leds == [0] * 7          # las lecturas inválidas se descartan
    ses._procesar({"ev": "led", "cell": 3, "level": 200})
    assert ses.leds[3] == 200           # un led válido sí aplica


def test_eventos_con_campos_faltantes_o_tipos_malos_no_lanzan():
    ses = _ses()
    malos = [
        {"ev": "led"}, {"ev": "led", "cell": 3},
        {"ev": "led", "cell": 3, "level": "x"},
        {"ev": "press"}, {"ev": "press", "cell": "y"},
        {"ev": "score"}, {"ev": "score", "hits": 1},
        {"ev": "score", "hits": "a", "misses": 0, "round": 1, "rt_ms": 0},
        {"ev": "state"}, {"ev": "state", "status": 5},
        {"ev": "suggest"}, {}, {"ev": "desconocido"},
        {"ev": "led", "cell": None, "level": None},
    ]
    for ev in malos:
        ses._procesar(ev)               # ninguno debe lanzar


def test_bombear_descarta_lineas_basura_y_aplica_las_validas():
    class FuenteBasura(FuenteCore):
        def __init__(self):
            super().__init__()
            self._cola = [
                "no es json", "", "{",
                '{"ev":"led","cell":99,"level":1}',   # celda inválida
                '{"ev":"score"}',                      # campos faltantes
                "\x00\xff bytes",
                '{"ev":"led","cell":2,"level":9}',     # válida
            ]

        def recibir(self):
            c, self._cola = self._cola, []
            return c

    ses = Sesion(Almacen(":memory:"), FuenteBasura())
    ses.bombear()                        # no debe lanzar
    assert ses.leds[2] == 9              # la única línea válida se aplicó


def test_fuente_serial_acota_buffer_ante_lineas_sin_fin():
    from fuente import FuenteSerial
    f = FuenteSerial("loop://")

    class SerBasura:
        def read(self, n):
            return b"x" * n              # bytes sin '\n', indefinidamente
        def write(self, b):
            pass
        def close(self):
            pass

    f.ser = SerBasura()
    for _ in range(100):
        assert f.recibir() == []         # sin '\n' no hay líneas completas
    assert len(f._buf) <= (1 << 16) + 4096   # el buffer no crece sin cota
    f.cerrar()


def test_panel_analisis_tolera_suggest_malformado():
    from paneles import PanelAnalisis
    p = PanelAnalisis(on_aplicar=lambda n: None)
    for sug in ({"dir": "up"}, {"dir": "down", "level": "x"},
                {"dir": "up", "level": None}, {}, {"dir": 5}, None,
                {"dir": "up", "level": 3}):   # el último es válido
        p.actualizar([], sug)            # ninguno debe lanzar


# --- Task 2.3: comandos de control fuera de orden (handlers de app.py) ---
# El terapeuta puede pulsar los botones en cualquier secuencia; ninguna debe
# lanzar ni dejar el estado incoherente (sesion_id, metricas, filas en SQLite).


def test_stop_sin_start_no_lanza_ni_cambia_estado():
    v = _ventana()
    assert v.ses.sesion_id is None
    v.b_stop.click()
    v.tick()
    assert v.ses.sesion_id is None
    assert v.ses.estado == "idle"


def test_pause_sin_sesion_no_lanza_ni_cambia_estado():
    v = _ventana()
    v.b_pause.click()
    v.tick()
    assert v.ses.sesion_id is None
    assert v.ses.estado == "idle"


def test_doble_start_no_duplica_sesion_ni_reinicia_metricas():
    v = _ventana()
    v.b_start.click()
    v.tick()
    assert v.ses.estado == "running"
    sid1 = v.ses.sesion_id

    # juega una ronda para tener metricas != 0 y exponer si un doble start las resetea
    encendida = next(c for c in range(1, 7) if v.ses.leds[c] > 0)
    v.fuente.pisar(encendida)
    v.tick()
    hits_tras_ronda = v.ses.hits
    assert hits_tras_ronda >= 1

    v.b_start.click()   # doble start: la sesion ya esta corriendo
    v.tick()

    assert v.ses.sesion_id == sid1            # no crea una segunda fila
    assert v.ses.hits == hits_tras_ronda       # no reinicia las metricas en curso
    assert len(v.almacen.sesiones()) == 1      # ninguna fila huerfana en SQLite


def test_doble_start_sin_tick_intermedio_no_duplica_sesion():
    # El doble clic real: dos start() antes de que el timer de 25 Hz alcance a
    # correr entre medias. La guarda no puede depender de un tick previo para
    # ver ses.estado == "running" (el evento ya esta encolado en el core).
    v = _ventana()
    v.b_start.click()
    v.b_start.click()   # sin tick entre los dos clics
    v.tick()
    assert len(v.almacen.sesiones()) == 1


def test_cambiar_modo_a_mitad_de_juego_no_lanza_y_queda_coherente():
    v = _ventana()
    v.b_start.click()
    v.tick()
    assert v.ses.estado == "running"

    v.cb_modo.setCurrentIndex(2)   # cambia de modo a mitad de partida
    v.tick()

    assert v.ses.estado == "idle"              # el motor la detiene de forma segura
    assert all(0 <= led <= 255 for led in v.ses.leds)   # sin corrupcion de LEDs


def test_cambiar_nivel_a_mitad_de_juego_no_lanza_y_queda_coherente():
    # sp_nivel.valueChanged tambien dispara _configurar() -> set_mode (no es el
    # set_level de "Aplicar"), mismo handler que cb_modo: misma guarda del motor.
    v = _ventana()
    v.b_start.click()
    v.tick()
    assert v.ses.estado == "running"

    v.sp_nivel.setValue(3)   # cambia de nivel a mitad de partida
    v.tick()

    assert v.ses.estado == "idle"
    assert all(0 <= led <= 255 for led in v.ses.leds)


def test_aplicar_sin_datos_no_lanza_ni_cambia_nivel():
    v = _ventana()
    nivel_antes = v.sp_nivel.value()
    v.pa.btn_aplicar.click()       # sin sugerencia: el boton esta deshabilitado
    assert v.sp_nivel.value() == nivel_antes


def test_exportar_sin_sesion_no_lanza_ni_crea_archivo():
    v = _ventana()
    assert v.ses.sesion_id is None
    v._exportar("csv")
    v._exportar("pdf")
    assert v.lbl_export.text() == ""

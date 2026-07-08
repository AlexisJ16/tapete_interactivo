"""Programación defensiva en los boundaries del dashboard.

Todo dato externo (eventos del protocolo, líneas crudas del serial/TCP) se valida
al entrar: una entrada malformada NUNCA debe lanzar ni corromper el estado. La
fuente puede ser el ESP32 real, cuyo serial mezcla ruido/basura con los eventos.
"""
import json
import os
import random
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6 import QtWidgets  # noqa: E402
from app import VentanaDashboard  # noqa: E402
from fuente import Fuente, FuenteCore  # noqa: E402
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


# --- Task 2.4: storage y export degradan sin tumbar la GUI ---
# Errores de E/S de disco/DB (ruta inexistente, DB corrupta, sin permiso, sin
# datos) deben llegar a la frontera como una excepcion propia (AlmacenError /
# ReporteError), nunca como un crash sin control ni una corrupcion silenciosa.


def test_almacen_ruta_a_directorio_inexistente_lanza_error_controlado():
    from storage import AlmacenError
    with pytest.raises(AlmacenError):
        Almacen("/ruta/que/no/existe/tapete.sqlite")


def test_almacen_db_corrupta_lanza_error_controlado(tmp_path):
    from storage import AlmacenError
    ruta = tmp_path / "corrupta.sqlite"
    ruta.write_bytes(b"esto no es una base de datos sqlite")
    with pytest.raises(AlmacenError):
        Almacen(str(ruta))


def test_exportar_csv_a_ruta_sin_permiso_lanza_error_controlado(tmp_path):
    from reports import ReporteError, exportar_csv
    a = Almacen(":memory:")
    sid = a.iniciar_sesion(None, 1, 1)
    sin_permiso = tmp_path / "sin_permiso"
    sin_permiso.mkdir()
    sin_permiso.chmod(0o000)
    try:
        with pytest.raises(ReporteError):
            exportar_csv(a, sid, str(sin_permiso / "reporte.csv"))
    finally:
        sin_permiso.chmod(0o755)   # permitir que pytest limpie tmp_path


def test_exportar_pdf_a_ruta_sin_permiso_lanza_error_controlado(tmp_path):
    from reports import ReporteError, exportar_pdf
    a = Almacen(":memory:")
    sid = a.iniciar_sesion(None, 1, 1)
    sin_permiso = tmp_path / "sin_permiso"
    sin_permiso.mkdir()
    sin_permiso.chmod(0o000)
    try:
        with pytest.raises(ReporteError):
            exportar_pdf(a, sid, str(sin_permiso / "reporte.pdf"))
    finally:
        sin_permiso.chmod(0o755)


def test_exportar_csv_sin_datos_lanza_error_controlado(tmp_path):
    from reports import ReporteError, exportar_csv
    a = Almacen(":memory:")
    with pytest.raises(ReporteError):
        exportar_csv(a, 9999, str(tmp_path / "no_deberia_crearse.csv"))
    assert not (tmp_path / "no_deberia_crearse.csv").exists()


def test_exportar_pdf_sin_datos_lanza_error_controlado(tmp_path):
    from reports import ReporteError, exportar_pdf
    a = Almacen(":memory:")
    with pytest.raises(ReporteError):
        exportar_pdf(a, 9999, str(tmp_path / "no_deberia_crearse.pdf"))
    assert not (tmp_path / "no_deberia_crearse.pdf").exists()


def test_exportar_csv_sesion_valida_sin_eventos_exporta_igual(tmp_path):
    # Otra lectura de "sin datos": una sesion que SI existe pero no acumulo
    # eventos (0 rondas). No es un error; debe exportar el resumen igual.
    from reports import exportar_csv
    a = Almacen(":memory:")
    sid = a.iniciar_sesion(None, 1, 1)
    ruta = str(tmp_path / "sin_eventos.csv")
    exportar_csv(a, sid, ruta)
    assert os.path.exists(ruta)


def test_exportar_gui_con_sesion_invalida_no_crashea_y_muestra_error():
    # Simula una sesion cuyo id no esta en el almacen (equivalente, desde la
    # frontera, a que storage/reports fallen): _exportar no debe propagar.
    v = _ventana()
    v.ses.sesion_id = 9999
    v._exportar("csv")
    assert "Error" in v.lbl_export.text()
    v._exportar("pdf")
    assert "Error" in v.lbl_export.text()


def test_exportar_gui_makedirs_falla_no_crashea_y_muestra_error(tmp_path, monkeypatch):
    # Si "reportes" ya existe como archivo plano (no directorio), os.makedirs(...,
    # exist_ok=True) lanza FileExistsError pese a exist_ok=True (exist_ok solo
    # perdona si el target YA es un directorio). Esa excepcion no debe propagar
    # fuera del slot de Qt (hoy vive fuera del try/except de _exportar).
    import app
    monkeypatch.setattr(app, "DIR", str(tmp_path))
    (tmp_path / "reportes").write_text("no soy un directorio")

    v = _ventana()
    sid = v.almacen.iniciar_sesion(None, 1, 1)
    v.ses.sesion_id = sid

    v._exportar("csv")   # no debe lanzar

    assert "Error" in v.lbl_export.text()


def test_abrir_almacen_con_db_corrupta_degrada_a_memoria_sin_abortar_la_gui(tmp_path, capsys):
    # Almacen(ruta) real (Task 2.4, arriba) SI lanza AlmacenError con una DB
    # corrupta; pero eso solo se prueba en el aislamiento del unit test. La
    # ventana se construye una unica vez al arrancar, con una ruta fija: si
    # esa apertura fallara sin capturarse, la GUI ni siquiera llegaria a
    # mostrarse. _abrir_almacen es la frontera que evita ese aborto.
    from app import _abrir_almacen
    ruta = tmp_path / "corrupta.sqlite"
    ruta.write_bytes(b"esto no es una base de datos sqlite")

    a = _abrir_almacen(str(ruta))          # no debe lanzar

    a.upsert_perfil("p001", "Juan")        # el almacen de respaldo (memoria) funciona
    assert a.perfiles()[0]["id"] == "p001"
    assert "AVISO" in capsys.readouterr().err   # la degradacion es visible, no silenciosa


# --- Task 3.2: fuzz determinista del parser de protocolo (bombear/_procesar) ---
# bombear() es el ingreso real de una linea cruda: json.loads() + _procesar().
# Un fuzzer determinista (random.Random(seed) fija) genera lineas basura muy
# variadas y las hace pasar por bombear(); ninguna debe propagar una excepcion.

_ALFABETO_FUZZ = "{}[]\":,0123456789-+.eE abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_\t\\ /"
_CAMPOS_EV_FUZZ = ["led", "press", "sound", "score", "suggest", "state",
                   "", "desconocido", None, 42, True]
_VALORES_FUZZ = [0, 1, -1, 999999999, -999999999, 10**30, -10**30, 3.14,
                 float("nan"), float("inf"), -float("inf"), True, False, None,
                 "texto", "", [], {}, [1, 2, 3], {"x": 1}, "9" * 10000]


def _linea_fuzz(rng: random.Random) -> str:
    """Genera una linea 'de protocolo' al azar: basura estructural, vacia,
    gigante (numero de miles de digitos o texto enorme), JSON valido truncado
    a medias, JSON anidado en extremo, JSON valido pero no-dict en el tope,
    evento JSON con campos/tipos al azar, o bytes no-UTF8 (decodificados con
    'replace', igual que hace fuente.py antes de que la linea llegue aqui)."""
    categoria = rng.random()
    if categoria < 0.15:                       # basura estructural (alfabeto tipo JSON)
        n = rng.randrange(0, 200)
        return "".join(rng.choice(_ALFABETO_FUZZ) for _ in range(n))
    if categoria < 0.20:                       # vacia / solo espacios
        return rng.choice(["", " ", "\n", "\t", "   "])
    if categoria < 0.30:                       # gigante: numero enorme o basura enorme
        n = rng.randrange(2000, 60000)
        if rng.random() < 0.5:
            return str(rng.choice([1, 8, 9])) * n
        return "".join(rng.choice(_ALFABETO_FUZZ) for _ in range(n))
    if categoria < 0.40:                       # JSON valido truncado en un punto al azar
        base = json.dumps({"ev": rng.choice(_CAMPOS_EV_FUZZ),
                            "cell": rng.choice(_VALORES_FUZZ),
                            "level": rng.choice(_VALORES_FUZZ)})
        return base[:rng.randrange(0, len(base) + 1)]
    if categoria < 0.55:                       # anidamiento extremo: "[[[..." / {"a":{"a":...
        n = rng.randrange(200, 20000)
        abre, cierra = rng.choice([("[", "]"), ('{"a":', "}")])
        return abre * n + "1" + cierra * n
    if categoria < 0.70:                       # JSON valido, top-level no es dict
        return json.dumps(rng.choice([[1, 2, 3], "hola", 42, 3.14, True, None, []]))
    if categoria < 0.90:                       # evento JSON con campos/tipos al azar
        ev = {}
        if rng.random() < 0.9:
            ev["ev"] = rng.choice(_CAMPOS_EV_FUZZ)
        for campo in ("cell", "level", "hits", "misses", "round", "rt_ms",
                      "ms", "status", "seed"):
            if rng.random() < 0.6:
                ev[campo] = rng.choice(_VALORES_FUZZ)
        return json.dumps(ev)
    n = rng.randrange(0, 300)                  # bytes no-UTF8 (decodificados con replace)
    crudos = bytes(rng.randrange(0, 256) for _ in range(n))
    return crudos.decode("utf-8", "replace")


class _FuenteFuzz(Fuente):
    """Fuente minima que entrega, de una vez, un lote fijo de lineas ya generadas."""
    def __init__(self, lineas: list) -> None:
        self._lineas = lineas

    def enviar(self, linea: str) -> None:
        pass

    def recibir(self) -> list:
        return self._lineas


def test_fuzz_bombear_lineas_basura_variadas_no_lanza():
    # 3 seeds fijas x 6000 lineas (>=5000 cada una) = 18000 lineas reproducibles.
    for seed in (12345, 67890, 999983):
        rng = random.Random(seed)
        lineas = [_linea_fuzz(rng) for _ in range(6000)]
        ses = Sesion(Almacen(":memory:"), _FuenteFuzz(lineas))
        ses.bombear()   # ninguna linea debe propagar una excepcion


def test_fuzz_casos_conocidos_no_lanzan():
    # Regresion explicita de lo que encontro el fuzz (RED antes de endurecer
    # bombear() en sesion.py): json.loads() puede lanzar ValueError (no
    # JSONDecodeError) ante un entero de miles de digitos -- limite de
    # conversion de Python -- y RecursionError ante un anidamiento extremo.
    entero_gigante = "9" * 50000
    anidado_extremo = "[" * 20000 + "1" + "]" * 20000
    ses = Sesion(Almacen(":memory:"), _FuenteFuzz([entero_gigante, anidado_extremo]))
    ses.bombear()   # no debe lanzar

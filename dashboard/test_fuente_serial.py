"""TDD de FuenteSerial (USB/Serial), sin hardware real.

Usa el puerto de loopback en memoria de pyserial (`loop://`): lo que se escribe
en el puerto se puede leer de vuelta, asi que se prueba el *framing* (lineas
JSON \\n, acumulacion de trozos, tolerancia a basura) sin la placa.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest  # noqa: E402

from fuente import FuenteCore, FuenteSerial, construir_fuente  # noqa: E402


def test_parsea_lineas_entrantes_completas():
    f = FuenteSerial("loop://")
    # Simula al ESP32 emitiendo dos eventos.
    f.ser.write(b'{"ev":"hello","fw":"1.0.0","cells":6}\n{"ev":"led","cell":1,"level":255}\n')
    assert f.recibir() == [
        '{"ev":"hello","fw":"1.0.0","cells":6}',
        '{"ev":"led","cell":1,"level":255}',
    ]
    f.cerrar()


def test_acumula_trozos_hasta_el_salto_de_linea():
    f = FuenteSerial("loop://")
    f.ser.write(b'{"ev":"score",')     # linea a medias: aun no hay \n
    assert f.recibir() == []
    f.ser.write(b'"hits":1}\n')        # llega el resto
    assert f.recibir() == ['{"ev":"score","hits":1}']
    f.cerrar()


def test_ignora_vacias_y_no_filtra_basura():
    # El serial mezcla el banner de arranque (no-JSON) con los eventos. La
    # fuente NO juzga: entrega la basura como linea (sesion.py ya la descarta);
    # solo se saltan las lineas vacias.
    f = FuenteSerial("loop://")
    f.ser.write(b"\n\nTapete Interactivo - firmware 1.0.0\n")
    assert f.recibir() == ["Tapete Interactivo - firmware 1.0.0"]
    f.cerrar()


def test_enviar_agrega_salto_de_linea():
    f = FuenteSerial("loop://")
    f.enviar('{"cmd":"start"}')        # sin \n: la fuente lo agrega
    assert f.recibir() == ['{"cmd":"start"}']
    f.cerrar()


def test_construir_fuente_serial():
    f = construir_fuente(serial="loop://")
    assert isinstance(f, FuenteSerial)
    f.cerrar()


def test_construir_fuente_core_por_defecto():
    f = construir_fuente()
    assert isinstance(f, FuenteCore)
    f.cerrar()


def test_construir_fuente_rechaza_tcp_y_serial_juntos():
    with pytest.raises(ValueError):
        construir_fuente(tcp="192.168.1.5", serial="/dev/ttyUSB0")

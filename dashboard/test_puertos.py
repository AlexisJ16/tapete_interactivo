import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puertos import (CP210X_PID, CP210X_VID, puertos_tapete,
                     resolver_puerto_serial, serial_por_defecto)


def _p(device, vid, pid):
    return SimpleNamespace(device=device, vid=vid, pid=pid)


def test_puertos_tapete_filtra_por_vid_pid():
    ports = [
        _p("COM1", 0x1234, 0x0001),           # otro dispositivo
        _p("COM3", CP210X_VID, CP210X_PID),   # el tapete
        _p("COM4", CP210X_VID, 0x0000),       # mismo vendor, otro pid
    ]
    assert puertos_tapete(ports) == ["COM3"]


def test_resolver_valor_explicito_pasa_igual():
    assert resolver_puerto_serial("/dev/ttyUSB0", detectar=lambda: []) == "/dev/ttyUSB0"


def test_resolver_auto_un_puerto():
    assert resolver_puerto_serial("auto", detectar=lambda: ["COM3"]) == "COM3"


def test_resolver_auto_sin_puertos_da_none():
    assert resolver_puerto_serial("auto", detectar=lambda: []) is None


def test_resolver_auto_varios_usa_elegir():
    r = resolver_puerto_serial("auto", detectar=lambda: ["COM3", "COM5"],
                               elegir=lambda ps: ps[1])
    assert r == "COM5"


def test_resolver_auto_varios_sin_elegir_toma_primero():
    assert resolver_puerto_serial("auto", detectar=lambda: ["COM3", "COM5"]) == "COM3"


def test_serial_por_defecto_frozen_sin_args_da_auto():
    assert serial_por_defecto(None, None, True) == "auto"


def test_serial_por_defecto_dev_sin_args_da_none():
    assert serial_por_defecto(None, None, False) is None


def test_serial_por_defecto_explicito_manda():
    assert serial_por_defecto("COM3", None, True) == "COM3"


def test_serial_por_defecto_con_tcp_no_fuerza_auto():
    assert serial_por_defecto(None, "192.168.1.5", True) is None

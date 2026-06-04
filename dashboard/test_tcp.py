"""Integracion por TCP: el dashboard (FuenteTCP) habla con el servidor del
simulador EXACTAMENTE como hablara con el ESP32. Prueba el criterio 5: pasar al
hardware es solo cambiar la IP, sin cambios de logica.
"""
import os
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(os.path.dirname(DIR), "simulator"))

from fuente import FuenteTCP          # noqa: E402
from sesion import Sesion             # noqa: E402
from storage import Almacen           # noqa: E402
from servidor import ServidorTapete   # noqa: E402


def _esperar(ses: Sesion, cond, timeout=4.0) -> bool:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        ses.bombear()
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_sesion_sobre_tcp():
    srv = ServidorTapete(host="127.0.0.1", puerto=0)  # puerto efimero
    srv.iniciar()
    try:
        fuente = FuenteTCP("127.0.0.1", srv.puerto)
        almacen = Almacen(":memory:")
        ses = Sesion(almacen, fuente)

        ses.sembrar(12345)                # objetivo inicial = 3
        ses.configurar(modo=2, nivel=1)
        ses.iniciar()

        # Espera a que el motor encienda el LED objetivo.
        assert _esperar(ses, lambda: any(ses.leds[c] > 0 for c in range(1, 7))), \
            "no se recibio el LED objetivo por TCP"
        objetivo = next(c for c in range(1, 7) if ses.leds[c] > 0)

        # Inyecta la pisada en el servidor (equivale al FSR del ESP32).
        srv.pisar(objetivo)

        # El dashboard debe recibir el acierto por TCP y persistirlo.
        assert _esperar(ses, lambda: ses.hits >= 1), "no llego el acierto por TCP"
        s = almacen.sesion(ses.sesion_id)
        assert s["hits"] >= 1
        fuente.cerrar()
    finally:
        srv.detener()

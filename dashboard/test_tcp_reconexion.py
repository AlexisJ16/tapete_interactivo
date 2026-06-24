"""Reconexion automatica de FuenteTCP (componente C del SP2).

Si el ESP32 cae estando conectado, el dashboard no debe quedar muerto: FuenteTCP
reconecta sola (backoff acotado, no bloqueante) y retoma la recepcion de datos.
Sin cambiar el contrato Fuente (enviar/recibir).
"""
import os
import socket
import sys
import threading
import time

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(os.path.dirname(DIR), "simulator"))

from fuente import FuenteTCP  # noqa: E402


class _ServidorFalible:
    """Servidor TCP de prueba que acepta, envia y puede 'caer' (cerrar la
    conexion del cliente) para simular un ESP32 que se cae y revive."""

    def __init__(self):
        self.ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ls.bind(("127.0.0.1", 0))
        self.ls.listen(1)
        self.puerto = self.ls.getsockname()[1]
        self.conn = None

    def aceptar(self):
        self.conn, _ = self.ls.accept()

    def enviar(self, s):
        self.conn.sendall(s.encode("utf-8"))

    def caer(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def cerrar(self):
        self.caer()
        self.ls.close()


def _recibir_hasta(fuente, cond, timeout=3.0):
    acc = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        acc += fuente.recibir()
        if cond(acc):
            return True
        time.sleep(0.02)
    return False


def test_fuente_tcp_reconecta_tras_caida():
    srv = _ServidorFalible()
    h = threading.Thread(target=srv.aceptar, daemon=True)  # create_connection bloquea hasta accept
    h.start()
    fuente = FuenteTCP("127.0.0.1", srv.puerto, backoff=0.01)
    h.join(2.0)

    srv.enviar('{"ev":"hola"}\n')
    assert _recibir_hasta(fuente, lambda L: any("hola" in x for x in L)), \
        "no llego el primer mensaje"

    # El ESP32 cae.
    srv.caer()
    fuente.recibir()  # la fuente detecta la caida

    # El ESP32 revive: el servidor vuelve a aceptar y envia.
    def _revivir():
        srv.aceptar()
        srv.enviar('{"ev":"otra"}\n')

    h2 = threading.Thread(target=_revivir, daemon=True)
    h2.start()
    ok = _recibir_hasta(fuente, lambda L: any("otra" in x for x in L), timeout=3.0)
    h2.join(2.0)
    assert ok, "FuenteTCP no reconecto ni recibio datos tras la caida"

    fuente.cerrar()
    srv.cerrar()


def test_enviar_tras_caida_no_lanza():
    srv = _ServidorFalible()
    h = threading.Thread(target=srv.aceptar, daemon=True)
    h.start()
    fuente = FuenteTCP("127.0.0.1", srv.puerto, backoff=0.01)
    h.join(2.0)

    srv.caer()
    # enviar sobre un socket muerto no debe propagar excepcion (se traga y reintenta).
    fuente.enviar('{"cmd":"start"}')
    fuente.enviar('{"cmd":"start"}')

    fuente.cerrar()
    srv.cerrar()

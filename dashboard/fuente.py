"""Fuentes de datos del dashboard.

El dashboard habla SIEMPRE el mismo protocolo de lineas JSON, venga del
simulador o del ESP32 real. Hay dos implementaciones:

  - FuenteCore: embebe GameCore.so en proceso (el dashboard ES el simulador).
                Ideal para uso autonomo y para los tests headless.
  - FuenteTCP : cliente TCP hacia un ESP32 (o un simulador en red) en el
                puerto 3333. Cambiar del simulador al hardware es solo esto:
                usar FuenteTCP con la IP del ESP32. Cero cambios de logica.
"""
from __future__ import annotations

import os
import socket
import sys
import time
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simulator"))
from core_bridge import CoreBridge  # noqa: E402


class Fuente(ABC):
    """Frontera comun: el dashboard envia comandos y recibe lineas de evento."""

    @abstractmethod
    def enviar(self, linea: str) -> None: ...

    @abstractmethod
    def recibir(self) -> list[str]: ...

    def cerrar(self) -> None:  # opcional
        pass


class FuenteCore(Fuente):
    """Embebe GameCore.so en proceso. El reloj puede inyectarse (tests)."""

    def __init__(self, libpath: str | None = None, reloj=None):
        self.core = CoreBridge(libpath)
        # reloj() -> ms. Por defecto, reloj monotonico real en ms.
        self._reloj = reloj or (lambda: int(time.monotonic() * 1000))

    def _sync(self) -> None:
        self.core.set_millis(self._reloj() & 0xFFFFFFFF)

    def enviar(self, linea: str) -> None:
        self._sync()
        self.core.comando(linea)

    def recibir(self) -> list[str]:
        self._sync()
        self.core.actualizar()
        return self.core.drenar_eventos()

    def pisar(self, celda: int) -> None:
        """Inyecta una pisada (la usa la UI del simulador o los tests)."""
        self._sync()
        self.core.pisar(celda)

    def cerrar(self) -> None:
        self.core.cerrar()


class FuenteTCP(Fuente):
    """Cliente TCP line-JSON hacia el ESP32 (o un simulador en red).

    Si el ESP32 cae estando conectado, reconecta sola: el socket caido se marca
    y los siguientes enviar()/recibir() reintentan con backoff exponencial
    acotado (no bloqueante). El primer intento, en cambio, propaga el error: si
    al arrancar no hay nada en la IP/puerto, conviene fallar ruidoso.

    Limitacion conocida: la reconexion es solo de transporte. Al reconectar NO
    re-sincroniza el estado de juego (modo/nivel), asi que tras una caida real
    el ESP32 arranca en su estado por defecto mientras el dashboard cree que la
    sesion sigue. Re-emitir set_mode/start tras reconectar queda fuera de alcance.
    """

    def __init__(self, host: str, puerto: int = 3333, timeout: float = 2.0,
                 backoff: float = 0.5, backoff_max: float = 5.0):
        self.host = host
        self.puerto = puerto
        self.timeout = timeout
        self._backoff = backoff
        self._backoff_max = backoff_max
        self._espera = backoff
        self.sock: socket.socket | None = None
        self._buf = b""
        self._proximo = 0.0  # instante monotonico a partir del cual reintentar
        self._conectar(propagar=True)

    def _conectar(self, propagar: bool = False) -> bool:
        try:
            self.sock = socket.create_connection((self.host, self.puerto), timeout=self.timeout)
            self.sock.setblocking(False)
            self._espera = self._backoff  # exito: resetea el backoff
            return True
        except OSError:
            self.sock = None
            self._programar_reintento()
            if propagar:
                raise
            return False

    def _programar_reintento(self) -> None:
        self._proximo = time.monotonic() + self._espera
        self._espera = min(self._espera * 2, self._backoff_max)

    def _asegurar(self) -> bool:
        if self.sock is not None:
            return True
        if time.monotonic() < self._proximo:
            return False  # aun en backoff: no martillar el socket
        return self._conectar()

    def _caer(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self._buf = b""
        self._programar_reintento()

    def enviar(self, linea: str) -> None:
        if not self._asegurar():
            return
        if not linea.endswith("\n"):
            linea += "\n"
        try:
            self.sock.sendall(linea.encode("utf-8"))
        except OSError:
            self._caer()

    def recibir(self) -> list[str]:
        if not self._asegurar():
            return []
        try:
            while True:
                trozo = self.sock.recv(4096)
                if not trozo:
                    self._caer()  # el peer cerro la conexion
                    break
                self._buf += trozo
        except BlockingIOError:
            pass
        except OSError:
            self._caer()
        lineas: list[str] = []
        while b"\n" in self._buf:
            linea, self._buf = self._buf.split(b"\n", 1)
            s = linea.decode("utf-8", "replace").strip()
            if s:
                lineas.append(s)
        return lineas

    def cerrar(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

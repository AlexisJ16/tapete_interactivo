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
    """Cliente TCP line-JSON hacia el ESP32 (o un simulador en red)."""

    def __init__(self, host: str, puerto: int = 3333, timeout: float = 2.0):
        self.sock = socket.create_connection((host, puerto), timeout=timeout)
        self.sock.setblocking(False)
        self._buf = b""

    def enviar(self, linea: str) -> None:
        if not linea.endswith("\n"):
            linea += "\n"
        self.sock.sendall(linea.encode("utf-8"))

    def recibir(self) -> list[str]:
        try:
            while True:
                trozo = self.sock.recv(4096)
                if not trozo:
                    break
                self._buf += trozo
        except (BlockingIOError, socket.timeout):
            pass
        lineas: list[str] = []
        while b"\n" in self._buf:
            linea, self._buf = self._buf.split(b"\n", 1)
            s = linea.decode("utf-8", "replace").strip()
            if s:
                lineas.append(s)
        return lineas

    def cerrar(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

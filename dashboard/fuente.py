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

# Cota del buffer de recepcion: una linea de protocolo real ronda los 100 bytes.
# Si se acumulan >64 KiB sin '\n' es ruido/linea patologica -> se descarta el
# residuo (evita crecimiento sin fin ante un serial que escupe basura sin newline).
_MAX_BUF = 1 << 16


def _extraer_lineas(buf: bytes) -> "tuple[list[str], bytes]":
    """Parte 'buf' en lineas completas (por '\\n') y devuelve (lineas, residuo).
    Las lineas se decodifican con 'replace' (bytes no-UTF8 no rompen). El residuo
    se descarta si excede la cota."""
    lineas: list[str] = []
    while b"\n" in buf:
        linea, buf = buf.split(b"\n", 1)
        s = linea.decode("utf-8", "replace").strip()
        if s:
            lineas.append(s)
    if len(buf) > _MAX_BUF:
        buf = b""
    return lineas, buf


def construir_fuente(tcp: str | None = None, serial: str | None = None,
                     puerto: int = 3333) -> "Fuente":
    """Elige la fuente segun los argumentos de arranque. `tcp` y `serial` son
    excluyentes; sin ninguno se embebe el simulador (FuenteCore)."""
    if tcp and serial:
        raise ValueError("--tcp y --serial son excluyentes: elige una sola conexion")
    if serial:
        return FuenteSerial(serial)
    if tcp:
        return FuenteTCP(tcp, puerto)
    return FuenteCore()


def construir_fuente_segura(tcp=None, serial=None, puerto=3333, on_error=None):
    """Como construir_fuente pero NUNCA propaga: si la fuente elegida no arranca
    (p. ej. el puerto serie detectado esta ocupado, o falta un backend en el
    ejecutable congelado), degrada a FuenteCore (modo practica) y llama
    on_error(msg) con el motivo. Garantiza que la GUI siempre tiene una fuente
    (invariante: la GUI nunca muere al arrancar)."""
    try:
        return construir_fuente(tcp=tcp, serial=serial, puerto=puerto)
    except Exception as e:  # frontera de arranque: cualquier fallo degrada
        if on_error is not None:
            on_error(str(e))
        return FuenteCore()


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
        lineas, self._buf = _extraer_lineas(self._buf)
        return lineas

    def cerrar(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None


class FuenteSerial(Fuente):
    """Cliente line-JSON hacia el ESP32 por USB/Serial (mismo protocolo que TCP).

    El cable USB alimenta y transporta a 115200 baudios; no depende de WiFi. La
    lectura es no bloqueante (timeout=0) y NO filtra: el serial mezcla el banner
    de arranque del ESP32 (no-JSON) con los eventos, y quien descarta las lineas
    no-JSON es sesion.py (via except JSONDecodeError). Fallar al abrir el puerto
    propaga (ruidoso); los errores de E/S posteriores se silencian para no tumbar
    la GUI si el cable se desconecta.
    """

    def __init__(self, puerto: str, baud: int = 115200, timeout: float = 0):
        import serial  # dependencia solo de esta fuente (pyserial)
        # serial_for_url acepta tanto un puerto ("/dev/ttyUSB0") como una URL de
        # test ("loop://"), lo que permite probar el framing sin hardware.
        self.ser = serial.serial_for_url(puerto, baudrate=baud, timeout=timeout)
        self._buf = b""

    def enviar(self, linea: str) -> None:
        if not linea.endswith("\n"):
            linea += "\n"
        try:
            self.ser.write(linea.encode("utf-8"))
        except OSError:
            pass

    def recibir(self) -> list[str]:
        try:
            trozo = self.ser.read(4096)   # no bloqueante: lo disponible ya
        except OSError:
            return []
        if trozo:
            self._buf += trozo
        lineas, self._buf = _extraer_lineas(self._buf)
        return lineas

    def cerrar(self) -> None:
        try:
            self.ser.close()
        except OSError:
            pass

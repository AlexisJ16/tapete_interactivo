"""Servidor TCP del simulador (puerto 3333 por defecto).

Expone GameCore.so por TCP con el MISMO protocolo de lineas JSON que usara el
ESP32. Asi, el dashboard puede conectarse por red al simulador EXACTAMENTE igual
que al hardware real: pasar del simulador al ESP32 es solo cambiar la IP.

- Acepta clientes (dashboard) y les reenvia los eventos del motor.
- Recibe comandos de los clientes y los aplica al motor.
- pisar(celda): inyecta una pisada (la llama la UI del simulador o los tests),
  equivalente a la deteccion del FSR en el ESP32.

Toda la interaccion con el motor ocurre en UN solo hilo (el bucle del servidor),
de modo que no hace falta bloquear el acceso al core: las pisadas/comandos
externos se encolan y el bucle los aplica.
"""
from __future__ import annotations

import os
import queue
import selectors
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_bridge import CoreBridge


class ServidorTapete:
    def __init__(self, host: str = "127.0.0.1", puerto: int = 3333, reloj=None):
        self.core = CoreBridge()
        self._reloj = reloj or (lambda: int(time.monotonic() * 1000))
        self._cola = queue.Queue()        # ("press", celda) | ("cmd", linea)
        self._sel = selectors.DefaultSelector()
        self._buffers: dict[socket.socket, bytes] = {}

        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((host, puerto))
        self._srv.listen()
        self._srv.setblocking(False)
        self._sel.register(self._srv, selectors.EVENT_READ, data="srv")
        self.puerto = self._srv.getsockname()[1]

        self._run = False
        self._hilo: threading.Thread | None = None

    # --- ciclo de vida ---
    def iniciar(self) -> None:
        self._run = True
        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._run = False
        if self._hilo:
            self._hilo.join(timeout=2.0)
        for s in list(self._buffers):
            self._cerrar_cliente(s)
        try:
            self._sel.unregister(self._srv)
        except KeyError:
            pass
        self._srv.close()
        self.core.cerrar()

    # --- inyeccion externa (UI / tests) ---
    def pisar(self, celda: int) -> None:
        self._cola.put(("press", celda))

    def comando(self, linea: str) -> None:
        self._cola.put(("cmd", linea))

    # --- internos ---
    def _broadcast(self, linea: str) -> None:
        datos = (linea + "\n").encode("utf-8")
        for s in list(self._buffers):
            try:
                s.sendall(datos)
            except OSError:
                self._cerrar_cliente(s)

    def _aceptar(self) -> None:
        try:
            cli, _ = self._srv.accept()
        except OSError:
            return
        cli.setblocking(False)
        self._sel.register(cli, selectors.EVENT_READ, data="cli")
        self._buffers[cli] = b""

    def _cerrar_cliente(self, s: socket.socket) -> None:
        try:
            self._sel.unregister(s)
        except KeyError:
            pass
        self._buffers.pop(s, None)
        try:
            s.close()
        except OSError:
            pass

    def _leer_cliente(self, s: socket.socket) -> None:
        try:
            datos = s.recv(4096)
        except (BlockingIOError, OSError):
            return
        if not datos:
            self._cerrar_cliente(s)
            return
        self._buffers[s] += datos
        while b"\n" in self._buffers[s]:
            linea, self._buffers[s] = self._buffers[s].split(b"\n", 1)
            txt = linea.decode("utf-8", "replace").strip()
            if txt:
                self.core.comando(txt)

    def _loop(self) -> None:
        while self._run:
            self.core.set_millis(self._reloj() & 0xFFFFFFFF)

            for key, _ in self._sel.select(timeout=0.02):
                if key.data == "srv":
                    self._aceptar()
                else:
                    self._leer_cliente(key.fileobj)

            while not self._cola.empty():
                tipo, val = self._cola.get()
                if tipo == "press":
                    self.core.pisar(int(val))
                elif tipo == "cmd":
                    self.core.comando(val)

            self.core.actualizar()
            for linea in self.core.drenar_eventos():
                self._broadcast(linea)


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Servidor TCP del simulador del tapete")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--puerto", type=int, default=3333)
    args = p.parse_args()
    srv = ServidorTapete(args.host, args.puerto)
    srv.iniciar()
    print(f"Servidor del tapete escuchando en {args.host}:{srv.puerto} (Ctrl-C para salir)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.detener()
    return 0


if __name__ == "__main__":
    sys.exit(main())

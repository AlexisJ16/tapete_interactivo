"""Red de seguridad global de la GUI: ningun bug interno no anticipado debe
abortar el proceso.

Verificado empiricamente (Task 4.1): en PyQt6, una excepcion que escapa de un
slot invocado por Qt (C++ -> Python, p. ej. un boton conectado con .connect())
aborta el proceso (SIGABRT) si no hay un sys.excepthook propio instalado; con
uno instalado que solo registra (sin relanzar/salir), el proceso sigue vivo.
Una llamada Python directa (sin pasar por Qt, p. ej. un test invocando el
handler) no pasa por sys.excepthook en absoluto -- por eso se necesitan las
dos utilidades: ejecutar_seguro cubre ambos casos envolviendo la llamada en su
origen; instalar_excepthook es la red de respaldo para lo que quede sin
envolver.
"""
from __future__ import annotations

import sys


def instalar_excepthook(logger):
    """Instala un sys.excepthook que registra la excepcion no capturada con
    'logger' y no aborta el proceso."""
    def _hook(tipo, valor, tb):
        logger.error("Excepcion no capturada", exc_info=(tipo, valor, tb))

    sys.excepthook = _hook


def ejecutar_seguro(fn, logger):
    """Ejecuta fn() (sin argumentos); si lanza, la registra con 'logger' y no
    propaga (retorna None). Para envolver tick() y los handlers de la GUI."""
    try:
        return fn()
    except Exception:
        logger.error("Excepcion capturada en un handler/tick", exc_info=True)
        return None

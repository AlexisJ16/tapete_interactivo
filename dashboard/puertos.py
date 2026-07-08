"""Deteccion del puerto serie del tapete (ESP32 con puente USB CP210x).

El medico no escribe "COM3": el lanzador arranca con --serial auto y esto resuelve
el puerto por el VID/PID del CP210x. Sin Qt, para poder probarlo headless."""
from __future__ import annotations

# Silicon Labs CP210x UART Bridge (confirmado en la placa: lsusb 10c4:ea60).
CP210X_VID = 0x10C4
CP210X_PID = 0xEA60


def puertos_tapete(comports=None) -> "list[str]":
    """Nombres de puerto (p. ej. 'COM3' o '/dev/ttyUSB0') cuyo VID/PID es el CP210x
    del ESP32. 'comports' es inyectable para tests; por defecto usa
    serial.tools.list_ports.comports()."""
    if comports is None:
        from serial.tools import list_ports
        comports = list_ports.comports()
    return [p.device for p in comports
            if getattr(p, "vid", None) == CP210X_VID
            and getattr(p, "pid", None) == CP210X_PID]


def resolver_puerto_serial(valor, detectar=puertos_tapete, elegir=None):
    """Traduce el valor de --serial a un puerto concreto (o None).

    - 'auto': detecta los CP210x. 1 -> ese puerto; 0 -> None (sin tapete);
      N -> elegir(puertos) si se pasa, si no el primero.
    - cualquier otro valor: se devuelve tal cual (puerto explicito)."""
    if valor != "auto":
        return valor
    encontrados = detectar()
    if len(encontrados) == 1:
        return encontrados[0]
    if not encontrados:
        return None
    if elegir is None:
        return encontrados[0]
    return elegir(encontrados)

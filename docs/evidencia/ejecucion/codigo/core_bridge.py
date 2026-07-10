"""Puente ctypes hacia GameCore.so.

El simulador NO reimplementa la logica de juego: carga la MISMA biblioteca C++
(GameCore) compilada como .so y la maneja como si fuera el ESP32 en software.
Asi se garantiza que simulador y firmware ejecutan exactamente el mismo codigo.

API C expuesta por firmware/lib/GameCore/bridge.cpp:
    void*       tapete_crear();
    void        tapete_destruir(void*);
    void        tapete_set_millis(void*, uint32_t);
    void        tapete_comando(void*, const char* linea_json);
    void        tapete_actualizar(void*);
    void        tapete_pisar(void*, int celda);
    const char* tapete_siguiente_evento(void*);   # NULL si no hay; valido hasta la sgte. llamada
"""
from __future__ import annotations

import ctypes
import glob
import os
import subprocess
import sys

# Rutas del proyecto.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMECORE = os.path.join(RAIZ, "firmware", "lib", "GameCore")
BUILD = os.path.join(RAIZ, "build")


def fuentes_core() -> list[str]:
    """Lista de .cpp portables que componen GameCore."""
    return sorted(glob.glob(os.path.join(GAMECORE, "*.cpp"))) + sorted(
        glob.glob(os.path.join(GAMECORE, "modes", "*.cpp"))
    )


def _lib_nombre() -> str:
    """Nombre de la biblioteca nativa segun la plataforma."""
    return "libgamecore.dll" if sys.platform.startswith("win") else "libgamecore.so"


def _empaquetado() -> bool:
    """True si corremos dentro de un ejecutable congelado (PyInstaller)."""
    return getattr(sys, "frozen", False)


# Ruta de build (dev). El nombre depende de la plataforma.
SO_PATH = os.path.join(BUILD, _lib_nombre())


def _comando_build() -> list[str]:
    """Comando g++ para compilar GameCore como biblioteca compartida. En Windows
    se enlaza estatico (-static*) para que el .dll NO dependa del runtime de MinGW
    (libstdc++/libgcc/winpthread), ausente en el equipo del medico."""
    flags = ["-std=c++17", "-O2", "-fPIC", "-shared"]
    if sys.platform.startswith("win"):
        flags += ["-static", "-static-libgcc", "-static-libstdc++"]
    return [os.environ.get("CXX", "g++"), *flags, f"-I{GAMECORE}",
            *fuentes_core(), "-o", SO_PATH]


def construir_so(forzar: bool = False) -> str:
    """Compila GameCore (.so/.dll) con g++ si falta (o si se fuerza). Devuelve la
    ruta. Solo en DESARROLLO: la app congelada nunca llega aqui (ver ruta_lib)."""
    os.makedirs(BUILD, exist_ok=True)
    if forzar or not os.path.exists(SO_PATH):
        subprocess.run(_comando_build(), check=True)
    return SO_PATH


def ruta_lib() -> str:
    """Ruta a la biblioteca nativa lista para cargar.

    - App congelada (PyInstaller): la lib va empaquetada junto al ejecutable
      (sys._MEIPASS) y NUNCA se compila (el equipo del medico no tiene g++); si
      falta, error claro.
    - Desarrollo: se compila con g++ si falta."""
    if _empaquetado():
        p = os.path.join(getattr(sys, "_MEIPASS", RAIZ), _lib_nombre())
        if not os.path.exists(p):
            raise RuntimeError(f"biblioteca nativa no encontrada en el paquete: {p}")
        return p
    return construir_so()


class CoreBridge:
    """Envuelve una instancia del motor dentro de GameCore.so."""

    def __init__(self, libpath: str | None = None):
        if libpath is None:
            libpath = ruta_lib()
        self._lib = ctypes.CDLL(libpath)
        self._declarar_firmas()
        self._h = self._lib.tapete_crear()
        if not self._h:
            raise RuntimeError("tapete_crear() devolvio NULL")

    def _declarar_firmas(self) -> None:
        L = self._lib
        L.tapete_crear.restype = ctypes.c_void_p
        L.tapete_destruir.argtypes = [ctypes.c_void_p]
        L.tapete_set_millis.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        L.tapete_comando.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        L.tapete_actualizar.argtypes = [ctypes.c_void_p]
        L.tapete_pisar.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.tapete_siguiente_evento.argtypes = [ctypes.c_void_p]
        L.tapete_siguiente_evento.restype = ctypes.c_char_p

    # --- API de alto nivel ---
    def set_millis(self, ms: int) -> None:
        self._lib.tapete_set_millis(self._h, ctypes.c_uint32(ms))

    def comando(self, linea: str) -> None:
        self._lib.tapete_comando(self._h, linea.encode("utf-8"))

    def actualizar(self) -> None:
        self._lib.tapete_actualizar(self._h)

    def pisar(self, celda: int) -> None:
        self._lib.tapete_pisar(self._h, ctypes.c_int(celda))

    def drenar_eventos(self) -> list[str]:
        """Devuelve todas las lineas de evento pendientes (FIFO) y vacia la cola."""
        out: list[str] = []
        while True:
            p = self._lib.tapete_siguiente_evento(self._h)
            if not p:
                break
            out.append(p.decode("utf-8"))
        return out

    def cerrar(self) -> None:
        if getattr(self, "_h", None):
            self._lib.tapete_destruir(self._h)
            self._h = None

    def __del__(self):
        try:
            self.cerrar()
        except Exception:
            pass


if __name__ == "__main__":
    # Smoke test rapido por linea de comandos.
    b = CoreBridge()
    b.comando('{"cmd":"ping"}')
    print("eventos:", b.drenar_eventos(), file=sys.stderr)

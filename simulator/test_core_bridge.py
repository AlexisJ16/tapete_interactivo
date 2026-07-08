import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core_bridge as cb


def test_lib_nombre_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert cb._lib_nombre() == "libgamecore.dll"


def test_lib_nombre_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert cb._lib_nombre() == "libgamecore.so"


def test_comando_build_windows_es_estatico(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    cmd = cb._comando_build()
    assert "-static-libstdc++" in cmd
    assert "-static-libgcc" in cmd
    assert "-static" in cmd


def test_comando_build_linux_no_estatico(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert "-static" not in cb._comando_build()


def test_ruta_lib_congelado_usa_meipass_sin_compilar(monkeypatch, tmp_path):
    lib = tmp_path / cb._lib_nombre()
    lib.write_bytes(b"\x00")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    llamado = {"construir": False}
    monkeypatch.setattr(cb, "construir_so",
                        lambda *a, **k: llamado.__setitem__("construir", True))
    assert cb.ruta_lib() == str(lib)
    assert llamado["construir"] is False  # jamas compila en app congelada


def test_ruta_lib_congelado_sin_lib_falla(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    with pytest.raises(RuntimeError):
        cb.ruta_lib()

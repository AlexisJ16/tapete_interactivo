"""Test headless del simulador: arranca pygame en modo 'dummy' y valida que el
flujo simulador<->GameCore.so funciona de punta a punta (sin pantalla ni audio)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapete_sim import smoke


def test_smoke_velocidad():
    assert smoke() == 0

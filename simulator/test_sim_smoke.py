"""Test headless del simulador: arranca pygame en modo 'dummy' y valida que el
flujo simulador<->GameCore.so funciona de punta a punta (sin pantalla ni audio)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapete_sim import smoke


def test_smoke_velocidad():
    assert smoke() == 0


def test_suggest_no_rompe_el_sim():
    from tapete_sim import Simulador
    sim = Simulador(headless=True)
    sim.comando({"cmd": "set_seed", "seed": 12345})
    sim.comando({"cmd": "set_mode", "mode": 2, "level": 1})
    sim.comando({"cmd": "start"})
    sim._drenar()
    for obj in [3, 4, 5, 3]:                  # 4 aciertos -> suggest up
        sim.core.actualizar(); sim._drenar()
        encendida = next((c for c in range(1, 7) if sim.leds[c] > 0), None)
        sim.pisar(encendida if encendida else obj)
    sim.core.cerrar(); sim.pygame.quit()
    assert sim.ultima_sugerencia.get("dir") == "up"
    assert sim.ultima_sugerencia.get("rate") == 100


def test_resembrar_no_falla_headless():
    from tapete_sim import Simulador
    sim = Simulador(headless=True)
    sim.resembrar()          # no debe lanzar; envia set_seed al core
    sim.comando({"cmd": "set_mode", "mode": 1, "level": 1})
    sim.comando({"cmd": "start"})
    assert sim.estado == "running"
    sim.core.cerrar()

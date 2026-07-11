"""La simulacion analogica (ngspice) debe coincidir con la teoria del circuito.

El divisor del FSR tiene solucion cerrada: V_nodo = 3,3 * R_M / (R_FSR + R_M).
Si ngspice y la formula discrepan, uno de los dos esta mal.
"""
from __future__ import annotations

import shutil

import pytest

from spice import (VREF, R_PULLDOWN, UMBRAL_CUENTAS, r_fsr_en_umbral,
                   simular_divisor, simular_grupo_led, v_nodo_teorico)

pytestmark = pytest.mark.skipif(shutil.which("ngspice") is None,
                                reason="ngspice no instalado")


def test_el_divisor_simulado_coincide_con_la_formula():
    for fila in simular_divisor():
        esperado = v_nodo_teorico(fila["r_fsr"])
        assert abs(fila["v_nodo"] - esperado) < 1e-3, fila


def test_la_tension_del_nodo_baja_al_crecer_la_resistencia_del_fsr():
    filas = simular_divisor()
    tensiones = [f["v_nodo"] for f in filas]
    assert tensiones == sorted(tensiones, reverse=True)


def test_el_umbral_corresponde_a_una_resistencia_de_fsr_concreta():
    # UMBRAL_PISADA = 2000 cuentas de 4095 sobre 3,3 V.
    r = r_fsr_en_umbral()
    assert abs(v_nodo_teorico(r) - VREF * UMBRAL_CUENTAS / 4095) < 1e-6
    # Con pull-down de 10 kOhm, el umbral cae cerca de la propia R_M.
    assert 0.5 * R_PULLDOWN < r < 1.5 * R_PULLDOWN


def test_el_grupo_led_no_exige_mas_de_lo_que_el_uln_soporta():
    # El unico limite CITABLE es el del ULN2803A (uln2803a.pdf): 500 mA/canal de maximo
    # absoluto y ~100 mA/canal con los 8 canales activos a duty continuo. El maximo del
    # LED es DESCONOCIDO: no hay datasheet del LED blanco en el repo.
    r = simular_grupo_led()
    assert r["i_grupo_a"] < 50e-3, "el grupo se acerca al limite continuo del ULN2803A"
    assert r["i_grupo_a"] == pytest.approx(3 * r["i_led_a"], rel=1e-6)


def test_las_r_de_110_ohm_iluminan_de_verdad():
    # Las 2.2 kOhm originales daban < 1 mA por LED: "tenue pero visible", y el autor las
    # sustituyo por 110 Ohm el 2026-07-11 justo por eso. Si alguien vuelve a subir la R,
    # que falle aqui y no en la mesa de terapia.
    assert simular_grupo_led()["i_led_a"] > 2e-3

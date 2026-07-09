"""Ejecuta las simulaciones analogicas (ngspice) y devuelve sus cifras.

Los netlists son la fuente de verdad del circuito analogico y viven en
`docs/hardware/spice/`. Este modulo los corre, parsea la salida y expone los
resultados para el articulo. Ninguna cifra se transcribe a mano.

Peso epistemico DISTINTO de las dos simulaciones (no mezclarlas):
- `divisor_fsr.cir` es un divisor resistivo puro: exacto dadas las resistencias.
- `grupo_led.cir` usa un modelo de diodo ajustado a mano y un V_CE(sat) fijo del
  Darlington: es una ESTIMACION de orden de magnitud, pendiente de confirmar con
  multimetro sobre el circuito armado (ver el encabezado del propio netlist).
"""
from __future__ import annotations

import os
import re
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPICE = os.path.join(RAIZ, "docs", "hardware", "spice")

VREF = 3.3              # tension del riel de sensado (V)
R_PULLDOWN = 10_000.0   # resistencia fija a masa del divisor (ohm)
UMBRAL_CUENTAS = 2000   # cfg::UMBRAL_PISADA, sobre 4095 cuentas
ADC_MAX = 4095


def _correr(netlist: str) -> str:
    salida = subprocess.run(["ngspice", "-b", netlist], cwd=SPICE,
                            capture_output=True, text=True, timeout=120)
    if salida.returncode != 0:
        raise RuntimeError(f"ngspice fallo en {netlist}:\n{salida.stderr}")
    return salida.stdout


def v_nodo_teorico(r_fsr: float) -> float:
    """V_nodo = Vref * R_M / (R_FSR + R_M)."""
    return VREF * R_PULLDOWN / (r_fsr + R_PULLDOWN)


def cuentas_adc(v: float) -> float:
    return v / VREF * ADC_MAX


def r_fsr_en_umbral() -> float:
    """Resistencia del FSR a la que el nodo alcanza justo UMBRAL_PISADA."""
    v = VREF * UMBRAL_CUENTAS / ADC_MAX
    return R_PULLDOWN * (VREF / v - 1.0)


# Filas "R_FSR   V_nodo   ADC" que emite el bloque .control del netlist.
_FILA = re.compile(r"^\s*([\d.]+(?:e\d+)?)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*$")


def simular_divisor() -> list[dict]:
    filas = []
    for linea in _correr("divisor_fsr.cir").splitlines():
        m = _FILA.match(linea)
        if not m:
            continue
        r, v, adc = (float(x) for x in m.groups())
        filas.append({"r_fsr": r, "v_nodo": v, "adc": adc})
    if not filas:
        raise RuntimeError("no se pudo parsear la salida de divisor_fsr.cir")
    return filas


def simular_grupo_led() -> dict:
    salida = _correr("grupo_led.cir")

    def valor(clave: str) -> float:
        m = re.search(rf"^{re.escape(clave)}\s*=\s*([\d.eE+-]+)", salida, re.M)
        if not m:
            raise RuntimeError(f"no se encontro '{clave}' en la salida de grupo_led.cir")
        return float(m.group(1))

    return {"v_anodo": valor("v(anodo)"), "v_catodo": valor("v(catodo)"),
            "i_grupo_a": valor("irg"), "i_led_a": valor("iled"),
            "nota": "estimacion de orden de magnitud; modelo de diodo y V_CE(sat) "
                    "asumidos, pendientes de confirmar con multimetro"}

"""Agregacion analitica del historico de sesiones (logica pura, sin Qt).

LEE del Almacen y arma series para las graficas del dashboard. No reimplementa
logica de juego: el dato ya esta persistido por sesion.py. El widget de la GUI
(app.py) consume estas series y las dibuja con matplotlib embebido.
"""
from __future__ import annotations

from storage import Almacen


def tasa_acierto(s: dict) -> float:
    """Porcentaje de aciertos de una sesion (0.0 si no se jugo)."""
    hits = s.get("hits") or 0
    total = hits + (s.get("misses") or 0)
    return round(100.0 * hits / total, 1) if total else 0.0


def serie_evolucion(almacen: Almacen, perfil_id: str) -> dict:
    """Series por sesion de un perfil, en orden cronologico, para graficar la
    evolucion (E4) y la adaptacion nivel-desempeno (E2)."""
    ses = almacen.sesiones(perfil_id)
    return {
        "indices": list(range(1, len(ses) + 1)),
        "ids": [s["id"] for s in ses],
        "hits": [s["hits"] or 0 for s in ses],
        "misses": [s["misses"] or 0 for s in ses],
        "rt_prom_ms": [s["rt_prom_ms"] or 0.0 for s in ses],
        "niveles": [s["nivel"] for s in ses],
        "tasas": [tasa_acierto(s) for s in ses],
    }

"""Jugador simulado determinista para el modo Velocidad.

Corre una sesión completa contra el MISMO GameCore (.so) que el ESP32 y el
dashboard. No reimplementa la lógica: reacciona a los eventos `led` pisando la
celda encendida con probabilidad = habilidad. El 'dado' es un xorshift32 propio
seed-dependiente (determinista, reproducible; nunca random()).
"""
from __future__ import annotations

import json

from core_bridge import CoreBridge


def _xorshift32(estado: int):
    s = estado & 0xFFFFFFFF
    if s == 0:
        s = 0x1234567
    while True:
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        # Rango [0, 1): se divide por 2^24 para que nunca alcance 1.0 exacto.
        yield (s & 0xFFFFFF) / float(0x1000000)


def jugar_sesion(modo: int, nivel: int, seed: int, habilidad: float,
                 latencia: int = 300, paso: int = 50, max_t: int = 120000) -> dict:
    b = CoreBridge()
    dado = _xorshift32(seed * 2654435761)
    objetivo = None
    reaccion_en = None
    finished = False
    scores: list[dict] = []
    suggests: list[dict] = []

    def drenar(t: int) -> None:
        nonlocal objetivo, reaccion_en, finished
        for linea in b.drenar_eventos():
            e = json.loads(linea)
            ev = e.get("ev")
            if ev == "led" and e["level"] > 0:
                objetivo = e["cell"]
                reaccion_en = t + latencia
            elif ev == "score":
                scores.append(e)
            elif ev == "suggest":
                suggests.append(e)
            elif ev == "state" and e.get("status") == "finished":
                finished = True

    b.comando(json.dumps({"cmd": "set_seed", "seed": seed}))
    b.comando(json.dumps({"cmd": "set_mode", "mode": modo, "level": nivel}))
    b.comando(json.dumps({"cmd": "start"}))
    drenar(0)

    t = 0
    while t < max_t and not finished:
        t += paso
        b.set_millis(t)
        b.actualizar()
        drenar(t)
        if objetivo is not None and reaccion_en is not None and t >= reaccion_en:
            if next(dado) < habilidad:
                b.pisar(objetivo)
            elif next(dado) < 0.5:
                b.pisar((objetivo % 6) + 1)
            objetivo = None
            reaccion_en = None
            drenar(t)

    b.cerrar()
    ultimo = scores[-1] if scores else {"hits": 0, "misses": 0, "rt_ms": 0, "round": 0}
    return {
        "modo": modo, "nivel": nivel, "seed": seed, "habilidad": habilidad,
        "hits": ultimo["hits"], "misses": ultimo["misses"],
        "rt_ms": ultimo["rt_ms"], "rondas": ultimo["round"],
        "suggests": suggests, "scores": scores,
    }

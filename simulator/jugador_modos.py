"""Jugadores simulados deterministas para los modos Memoria y Equilibrio.

Como `jugador_sim.py` (modo Velocidad), no reimplementan nada: corren contra el
MISMO GameCore (.so) que el ESP32 y reaccionan a los eventos del protocolo. La
`habilidad` es la probabilidad de ejecutar la accion correcta en cada pisada.

Memoria y Equilibrio necesitan politicas propias: el jugador de Velocidad solo
sabe reaccionar a la unica casilla encendida.
"""
from __future__ import annotations

import json

from core_bridge import CoreBridge
from jugador_sim import _xorshift32

CELDAS = 6

# La exhibicion de Memoria separa dos LEDs por `gap` = 250 ms (Config.h). Con todas
# las casillas apagadas, un silencio mayor significa que la exhibicion termino y el
# motor espera la entrada. La condicion "apagadas" es imprescindible: mientras un LED
# esta encendido (hasta 600 ms) tampoco se emiten eventos.
SILENCIO_FIN_EXHIBICION_MS = 300


def _celda_distinta(celda: int) -> int:
    return (celda % CELDAS) + 1


def _arrancar(b: CoreBridge, modo: int, nivel: int, seed: int) -> None:
    b.comando(json.dumps({"cmd": "set_seed", "seed": seed}))
    b.comando(json.dumps({"cmd": "set_mode", "mode": modo, "level": nivel}))
    b.comando(json.dumps({"cmd": "start"}))


def jugar_memoria(nivel: int, seed: int, habilidad: float,
                  latencia: int = 300, paso: int = 50, max_t: int = 120000) -> dict:
    """Memoriza la secuencia exhibida y la repite, acertando con prob. `habilidad`."""
    b = CoreBridge()
    dado = _xorshift32(seed * 2654435761)
    scores: list[dict] = []
    suggests: list[dict] = []

    secuencia: list[int] = []
    encendidas: set[int] = set()
    entrada = False                # ¿el motor ya espera las pisadas?
    idx = 0
    t_ultimo_led = 0
    prox_pisada = 0
    finished = False

    def drenar(t: int) -> None:
        nonlocal entrada, idx, t_ultimo_led, finished, secuencia
        for linea in b.drenar_eventos():
            e = json.loads(linea)
            ev = e.get("ev")
            if ev == "led":
                t_ultimo_led = t
                if e["level"] > 0:
                    encendidas.add(e["cell"])
                    # Un LED que se enciende mientras aun no toca pisar (fase de
                    # exhibicion) es un paso de la secuencia. Los LEDs que confirman
                    # una pisada (fase de entrada) no cuentan.
                    if not entrada:
                        secuencia.append(e["cell"])
                else:
                    encendidas.discard(e["cell"])
            elif ev == "score":
                scores.append(e)
                secuencia = []       # el motor reexhibe: acierto (crece) o error (repite)
                entrada = False
                idx = 0
            elif ev == "suggest":
                suggests.append(e)
            elif ev == "state" and e.get("status") == "finished":
                finished = True

    _arrancar(b, 1, nivel, seed)
    drenar(0)

    t = 0
    while t < max_t and not finished:
        t += paso
        b.set_millis(t)
        b.actualizar()
        drenar(t)
        if finished:
            break

        if (not entrada and secuencia and not encendidas
                and (t - t_ultimo_led) >= SILENCIO_FIN_EXHIBICION_MS):
            entrada = True
            idx = 0
            prox_pisada = t + latencia

        if entrada and t >= prox_pisada and idx < len(secuencia):
            correcta = secuencia[idx]
            if next(dado) < habilidad:
                b.pisar(correcta)
                idx += 1
            else:
                b.pisar(_celda_distinta(correcta))  # error: el motor reexhibe
            prox_pisada = t + latencia
            drenar(t)

    b.cerrar()
    ultimo = scores[-1] if scores else {"hits": 0, "misses": 0, "rt_ms": 0, "round": 0}
    return {
        "modo": 1, "nivel": nivel, "seed": seed, "habilidad": habilidad,
        "hits": ultimo["hits"], "misses": ultimo["misses"],
        "rt_ms": ultimo["rt_ms"], "rondas": ultimo["round"],
        "finished": finished, "suggests": suggests, "scores": scores,
    }


def jugar_equilibrio(nivel: int, seed: int, habilidad: float,
                     latencia: int = 300, paso: int = 50, max_t: int = 120000) -> dict:
    """Pisa las k casillas simultaneas del patron, acertando con prob. `habilidad`."""
    b = CoreBridge()
    dado = _xorshift32(seed * 2654435761)
    scores: list[dict] = []
    suggests: list[dict] = []

    encendidas: set[int] = set()
    pisadas: set[int] = set()
    prox_pisada = 0
    finished = False

    def drenar() -> None:
        nonlocal finished, pisadas
        for linea in b.drenar_eventos():
            e = json.loads(linea)
            ev = e.get("ev")
            if ev == "led":
                if e["level"] > 0:
                    encendidas.add(e["cell"])
                else:
                    encendidas.discard(e["cell"])
            elif ev == "score":
                scores.append(e)
                pisadas = set()      # patron nuevo (acierto o fallo)
            elif ev == "suggest":
                suggests.append(e)
            elif ev == "state" and e.get("status") == "finished":
                finished = True

    _arrancar(b, 3, nivel, seed)
    drenar()

    t = 0
    while t < max_t and not finished:
        t += paso
        b.set_millis(t)
        b.actualizar()
        drenar()
        if finished:
            break

        faltan = sorted(encendidas - pisadas)
        if faltan and t >= prox_pisada:
            if next(dado) < habilidad:
                celda = faltan[0]
                b.pisar(celda)
                pisadas.add(celda)
            else:
                fuera = next((c for c in range(1, CELDAS + 1) if c not in encendidas), 1)
                b.pisar(fuera)       # error: el motor pasa a la ronda siguiente
            prox_pisada = t + latencia
            drenar()

    b.cerrar()
    ultimo = scores[-1] if scores else {"hits": 0, "misses": 0, "rt_ms": 0, "round": 0}
    return {
        "modo": 3, "nivel": nivel, "seed": seed, "habilidad": habilidad,
        "hits": ultimo["hits"], "misses": ultimo["misses"],
        "rt_ms": ultimo["rt_ms"], "rondas": ultimo["round"],
        "finished": finished, "suggests": suggests, "scores": scores,
    }

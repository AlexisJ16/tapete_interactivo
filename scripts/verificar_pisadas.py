#!/usr/bin/env python3
"""Veredicto de los 6 FSR a partir de los eventos 'press' de una sesion.

El firmware normal no imprime el ADC, y la GUI no pinta las pisadas: el unico
rastro de cada pisada es el evento 'press' que sesion.py escribe en SQLite.
Este script lo lee y dice, por celda, si el sensor respondio.

Distingue el fallo silencioso que importa tras atornillar el acrilico: un sensor
"stuck-high" (reposo por encima del umbral) emite UN press al arrancar y luego
calla, porque detectarPisadas() enclava pisada[c] hasta que el ADC vuelve a bajar.
Eso NO es un sensor sano: se delata porque dispara sin que nadie lo pise.

Uso:  .venv/bin/python scripts/verificar_pisadas.py [--sesion N] [--reposo-s 5]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

CELDAS = 6
BD = Path(__file__).resolve().parent.parent / "dashboard" / "tapete.sqlite"


def presses(db: sqlite3.Connection, sesion: int) -> list[tuple[int, int]]:
    """[(ms, celda)] ordenados por ms."""
    filas = db.execute(
        "SELECT ms, datos FROM eventos WHERE sesion_id=? AND tipo='press' ORDER BY ms",
        (sesion,),
    ).fetchall()
    out = []
    for ms, datos in filas:
        try:
            celda = json.loads(datos).get("cell")
        except (ValueError, TypeError):
            continue
        if isinstance(celda, int) and 1 <= celda <= CELDAS:
            out.append((ms, celda))
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sesion", type=int, help="id de sesion (por defecto: la ultima)")
    p.add_argument("--reposo-s", type=float, default=5.0,
                   help="ventana inicial en la que NADIE debe pisar (delata stuck-high)")
    args = p.parse_args()

    if not BD.exists():
        print(f"No existe la base de datos: {BD}")
        return 2
    db = sqlite3.connect(BD)

    sesion = args.sesion
    if sesion is None:
        fila = db.execute("SELECT MAX(id) FROM sesiones").fetchone()
        sesion = fila[0] if fila else None
    if sesion is None:
        print("No hay sesiones registradas.")
        return 2

    modo, nivel = db.execute(
        "SELECT modo, nivel FROM sesiones WHERE id=?", (sesion,)
    ).fetchone()
    eventos = presses(db, sesion)

    print(f"Sesion {sesion} (modo {modo}, nivel {nivel}) — {len(eventos)} pisadas registradas\n")
    if not eventos:
        print("NINGUNA pisada llego al dashboard.")
        print("-> Revisa que la sesion estuviera en RUNNING (boton Iniciar) y el cable USB.")
        return 1

    ventana_ms = int(args.reposo_s * 1000)
    fantasmas = [(ms, c) for ms, c in eventos if ms <= ventana_ms]

    conteo = {c: 0 for c in range(1, CELDAS + 1)}
    for _, c in eventos:
        conteo[c] += 1

    print(f"{'Celda':<7}{'Pisadas':<10}{'Veredicto'}")
    print("-" * 52)
    fallos = []
    for c in range(1, CELDAS + 1):
        n = conteo[c]
        sospechosa = any(cc == c for _, cc in fantasmas)
        if n == 0:
            v, ok = "MUDO — no registro ninguna pisada", False
        elif sospechosa and n == 1:
            v, ok = "STUCK-HIGH — disparo en reposo y callo", False
        elif sospechosa:
            v, ok = "disparo en reposo (revisar)", False
        elif n == 1:
            v, ok = "solo 1 pisada (pisa de nuevo para confirmar)", False
        else:
            v, ok = "OK", True
        if not ok:
            fallos.append(c)
        print(f"{c:<7}{n:<10}{v}")

    print()
    if fantasmas:
        print(f"AVISO: {len(fantasmas)} pisada(s) en los primeros {args.reposo_s:g} s "
              f"(nadie debia pisar): {sorted({c for _, c in fantasmas})}")
        print("-> Sensor(es) con reposo por encima de UMBRAL_PISADA=2000 (presion del acrilico).\n")

    if fallos:
        print(f"VEREDICTO: FALLAN las celdas {fallos}")
        print("-> Siguiente paso: flashear esp32dev_calib y medir reposo/pico CON el acrilico puesto")
        print("   (docs/hardware/flashing.md §6). Lo hace el humano; el agente no flashea.")
        return 1

    print("VEREDICTO: los 6 FSR responden. El acrilico NO desplazo el umbral. Listo para grabar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

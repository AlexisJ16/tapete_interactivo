"""Ejecuta shared/golden_vectors.json contra GameCore.so y verifica la salida.

Como el simulador carga el MISMO GameCore.so que se compila para el ESP32,
correr los golden vectors aqui valida a la vez 'C++' y 'simulador': hay una
sola implementacion de la logica. Es headless (no necesita pantalla ni audio).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

from core_bridge import RAIZ, CoreBridge, construir_so

GOLDEN = os.path.join(RAIZ, "shared", "golden_vectors.json")


def cargar_vectores(path: str = GOLDEN) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _es_subsecuencia(emitidos: list[dict], esperado: list[dict]) -> bool:
    """¿'esperado' aparece, en orden, como subsecuencia de 'emitidos'?"""
    j = 0
    for ev in emitidos:
        if j < len(esperado) and ev == esperado[j]:
            j += 1
    return j == len(esperado)


def reproducir(escenario: dict, libpath: str | None = None) -> list[dict]:
    """Reproduce el timeline de un escenario y devuelve los eventos emitidos."""
    b = CoreBridge(libpath)
    emitidos: list[dict] = []

    def drenar():
        for linea in b.drenar_eventos():
            emitidos.append(json.loads(linea))

    # Semilla inicial opcional desde config (ademas de la del timeline).
    cfg = escenario.get("config", {})
    if "seed" in cfg:
        b.comando(json.dumps({"cmd": "set_seed", "seed": cfg["seed"]}))
        drenar()

    for paso in escenario.get("timeline", []):
        t = paso.get("t", 0)
        b.set_millis(t)
        b.actualizar()
        drenar()
        if "cmd" in paso:
            b.comando(json.dumps(paso["cmd"]))
            drenar()
        elif "press" in paso:
            b.pisar(int(paso["press"]))
            drenar()
    b.cerrar()
    return emitidos


@dataclass
class Resultado:
    nombre: str
    ok: bool
    detalle: str = ""


def verificar_escenario(escenario: dict, libpath: str | None = None) -> Resultado:
    nombre = escenario.get("name", "<sin nombre>")
    esperado = escenario.get("expected", [])
    match = escenario.get("match", "subsequence")
    emitidos = reproducir(escenario, libpath)

    if match == "strict":
        ok = emitidos == esperado
    else:
        ok = _es_subsecuencia(emitidos, esperado)

    detalle = "" if ok else (
        f"\n  esperado ({match}): {json.dumps(esperado)}"
        f"\n  emitido:            {json.dumps(emitidos)}"
    )
    return Resultado(nombre, ok, detalle)


def correr_todos(path: str = GOLDEN) -> list[Resultado]:
    libpath = construir_so()
    datos = cargar_vectores(path)
    return [verificar_escenario(e, libpath) for e in datos.get("scenarios", [])]


def main() -> int:
    resultados = correr_todos()
    fallidos = 0
    for r in resultados:
        marca = "OK " if r.ok else "XX "
        print(f"{marca} {r.nombre}{r.detalle}")
        if not r.ok:
            fallidos += 1
    print(f"\n{len(resultados) - fallidos}/{len(resultados)} escenarios en verde")
    return 0 if fallidos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

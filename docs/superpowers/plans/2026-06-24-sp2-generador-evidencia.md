# Generador de evidencia (Velocidad) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un jugador simulado determinista corre sesiones del modo Velocidad contra el mismo GameCore (`.so`) y produce evidencia reproducible (E1–E4) y figuras PNG para el documento de grado.

**Architecture:** `simulator/jugador_sim.py` envuelve `CoreBridge` y simula un jugador parametrizado por *habilidad* (probabilidad de acertar a tiempo); reacciona a los eventos `led` y devuelve métricas + `suggest`. `scripts/generar_evidencia.py` barre habilidades/niveles, agrega y emite figuras con matplotlib (Agg). El jugador NO duplica lógica de juego: lee del `.so`.

**Tech Stack:** Python 3.12, ctypes (vía `core_bridge`), pytest, matplotlib (Agg, ya es dependencia de `dashboard/`).

## Global Constraints

- **Determinismo:** mismas (modo, nivel, seed, habilidad) → mismos eventos. El "dado" del jugador es un xorshift32 propio seed-dependiente, **nunca** `random`/`Math.random`.
- **Una sola fuente de verdad:** el jugador consume el `.so` de GameCore; no reimplementa modos.
- **Mecánica de Velocidad (verificada empíricamente):** nivel 1 = 5 rondas, nivel 2 = 8 rondas; ventana por nivel = 3000/2000/1200/1000 ms; cada ronda enciende una celda (`led` level>0), `score` por ronda (`hits,misses,rt_ms,round`), `state status:"finished"` al terminar. `suggest` se emite al cambiar de dirección (`window`=4): habilidad alta → `dir:"up"`, baja → `dir:"down"`.
- **Figuras:** matplotlib backend **Agg** (sin pantalla), PNG en `docs/evidencia/`.
- **Suite verde:** `./scripts/run_all_tests.sh` debe terminar en TODO VERDE; los tests del jugador van en `simulator/` (pytest los recoge).
- **Plazo corto:** incremento mínimo; solo Velocidad en esta iteración.

---

### Task 1: Jugador simulado determinista (`jugar_sesion`)

**Files:**
- Create: `simulator/jugador_sim.py`
- Test: `simulator/test_jugador_sim.py`

**Interfaces:**
- Consumes: `core_bridge.CoreBridge`, `core_bridge.construir_so`.
- Produces:
  - `jugar_sesion(modo:int, nivel:int, seed:int, habilidad:float, latencia:int=300, paso:int=50) -> dict`
    devuelve `{"modo","nivel","seed","habilidad","hits","misses","rt_ms","rondas","suggests":list[dict],"scores":list[dict]}`.

- [ ] **Step 1: Write the failing test** — `simulator/test_jugador_sim.py`

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jugador_sim import jugar_sesion


def test_determinismo_misma_entrada_misma_salida():
    a = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=1.0)
    b = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=1.0)
    assert a["scores"] == b["scores"]
    assert a["suggests"] == b["suggests"]


def test_jugador_perfecto_acierta_todo_y_sube():
    r = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=1.0)
    assert r["misses"] == 0
    assert r["hits"] == r["rondas"] > 0
    assert any(s["dir"] == "up" for s in r["suggests"])


def test_jugador_pesimo_falla_todo_y_baja():
    r = jugar_sesion(modo=2, nivel=2, seed=777, habilidad=0.0)
    assert r["hits"] == 0
    assert r["misses"] == r["rondas"] > 0
    assert any(s["dir"] == "down" for s in r["suggests"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest simulator/test_jugador_sim.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'jugador_sim'`).

- [ ] **Step 3: Write minimal implementation** — `simulator/jugador_sim.py`

```python
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
        yield (s & 0xFFFFFF) / float(0xFFFFFF)


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest simulator/test_jugador_sim.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add simulator/jugador_sim.py simulator/test_jugador_sim.py
git commit -m "SP2: jugador simulado determinista para Velocidad (E1/E2)"
```

---

### Task 2: Agregación de evidencia (barridos E2/E3/E4)

**Files:**
- Create: `simulator/evidencia.py`
- Test: `simulator/test_evidencia.py`

**Interfaces:**
- Consumes: `jugador_sim.jugar_sesion`.
- Produces:
  - `barrido_habilidad(nivel:int, seed:int, habilidades:list[float]) -> list[dict]` — una fila por habilidad con `{"habilidad","hits","misses","rt_ms","rondas","dir"}` (dir = última dirección sugerida o "keep").
  - `barrido_niveles(seed:int, habilidad:float, niveles:list[int]) -> list[dict]` — una fila por nivel.
  - `trayectoria_adaptativa(seed:int, habilidad:float, nivel_inicial:int, n_sesiones:int) -> list[dict]` — encadena sesiones aplicando el `suggest` (sube/baja nivel, saturado a 1..4); fila por sesión con `{"sesion","nivel","hits","misses"}`.

- [ ] **Step 1: Write the failing test** — `simulator/test_evidencia.py`

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evidencia import barrido_habilidad, barrido_niveles, trayectoria_adaptativa


def test_barrido_habilidad_monotonia_direccion():
    filas = barrido_habilidad(nivel=2, seed=777, habilidades=[0.0, 1.0])
    por_hab = {f["habilidad"]: f for f in filas}
    assert por_hab[1.0]["dir"] == "up"
    assert por_hab[0.0]["dir"] == "down"
    assert por_hab[1.0]["hits"] > por_hab[0.0]["hits"]


def test_barrido_niveles_devuelve_fila_por_nivel():
    filas = barrido_niveles(seed=777, habilidad=1.0, niveles=[1, 2, 3])
    assert [f["nivel"] for f in filas] == [1, 2, 3]
    assert all(f["misses"] == 0 for f in filas)  # jugador perfecto


def test_trayectoria_perfecta_sube_hasta_saturar():
    filas = trayectoria_adaptativa(seed=777, habilidad=1.0, nivel_inicial=1, n_sesiones=6)
    niveles = [f["nivel"] for f in filas]
    assert niveles[0] == 1
    assert niveles[-1] >= niveles[0]
    assert max(niveles) <= 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest simulator/test_evidencia.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'evidencia'`).

- [ ] **Step 3: Write minimal implementation** — `simulator/evidencia.py`

```python
"""Agrega evidencia de la lógica adaptable corriendo el jugador simulado.
Determinista: solo depende de (seed, habilidad, nivel)."""
from __future__ import annotations

from jugador_sim import jugar_sesion


def _dir_final(r: dict) -> str:
    return r["suggests"][-1]["dir"] if r["suggests"] else "keep"


def _nivel_sugerido(r: dict, nivel_actual: int) -> int:
    if r["suggests"]:
        return max(1, min(4, r["suggests"][-1]["level"]))
    return nivel_actual


def barrido_habilidad(nivel: int, seed: int, habilidades: list[float]) -> list[dict]:
    filas = []
    for h in habilidades:
        r = jugar_sesion(modo=2, nivel=nivel, seed=seed, habilidad=h)
        filas.append({"habilidad": h, "hits": r["hits"], "misses": r["misses"],
                      "rt_ms": r["rt_ms"], "rondas": r["rondas"], "dir": _dir_final(r)})
    return filas


def barrido_niveles(seed: int, habilidad: float, niveles: list[int]) -> list[dict]:
    filas = []
    for n in niveles:
        r = jugar_sesion(modo=2, nivel=n, seed=seed, habilidad=habilidad)
        filas.append({"nivel": n, "hits": r["hits"], "misses": r["misses"],
                      "rt_ms": r["rt_ms"], "rondas": r["rondas"]})
    return filas


def trayectoria_adaptativa(seed: int, habilidad: float, nivel_inicial: int,
                           n_sesiones: int) -> list[dict]:
    filas = []
    nivel = nivel_inicial
    for i in range(n_sesiones):
        r = jugar_sesion(modo=2, nivel=nivel, seed=seed + i, habilidad=habilidad)
        filas.append({"sesion": i + 1, "nivel": nivel,
                      "hits": r["hits"], "misses": r["misses"]})
        nivel = _nivel_sugerido(r, nivel)
    return filas
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest simulator/test_evidencia.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add simulator/evidencia.py simulator/test_evidencia.py
git commit -m "SP2: agregación de evidencia (barridos habilidad/nivel + trayectoria)"
```

---

### Task 3: Figuras PNG + CLI (`generar_evidencia.py`)

**Files:**
- Create: `scripts/generar_evidencia.py`
- Test: `simulator/test_generar_evidencia_smoke.py`

**Interfaces:**
- Consumes: `evidencia.barrido_habilidad`, `evidencia.barrido_niveles`, `evidencia.trayectoria_adaptativa`.
- Produces: `main(salida:str) -> list[str]` (rutas PNG escritas); figuras E2 (adaptación), E3 (desempeño por nivel), E4 (trayectoria).

- [ ] **Step 1: Write the failing smoke test** — `simulator/test_generar_evidencia_smoke.py`

```python
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))
import generar_evidencia  # noqa: E402


def test_genera_pngs(tmp_path):
    rutas = generar_evidencia.main(salida=str(tmp_path))
    assert len(rutas) >= 3
    for r in rutas:
        assert os.path.exists(r) and os.path.getsize(r) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest simulator/test_generar_evidencia_smoke.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'generar_evidencia'`).

- [ ] **Step 3: Write minimal implementation** — `scripts/generar_evidencia.py`

```python
"""Genera figuras de evidencia (E2/E3/E4) de la lógica adaptable del Tapete.
Las figuras representan el COMPORTAMIENTO DEL SISTEMA EN SIMULACIÓN determinista
(no resultados con pacientes). Backend Agg: no requiere pantalla."""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))
from evidencia import (  # noqa: E402
    barrido_habilidad, barrido_niveles, trayectoria_adaptativa,
)

SEED = 777


def _fig_adaptacion(salida: str) -> str:
    habs = [i / 10 for i in range(0, 11)]
    filas = barrido_habilidad(nivel=2, seed=SEED, habilidades=habs)
    x = [f["habilidad"] * 100 for f in filas]
    tasa = [100 * f["hits"] / max(1, f["rondas"]) for f in filas]
    color = {"up": "tab:green", "down": "tab:red", "keep": "tab:gray"}
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, tasa, "-o", color="tab:blue", label="tasa de acierto")
    for f, xi, yi in zip(filas, x, tasa):
        ax.scatter([xi], [yi], color=color[f["dir"]], zorder=3)
    ax.set_xlabel("habilidad del jugador (%)")
    ax.set_ylabel("tasa de acierto en la sesión (%)")
    ax.set_title("E2 — Recomendación adaptativa vs desempeño (Velocidad, nivel 2)")
    ax.grid(True, alpha=0.3)
    ruta = os.path.join(salida, "E2_adaptacion.png")
    fig.tight_layout(); fig.savefig(ruta, dpi=120); plt.close(fig)
    return ruta


def _fig_niveles(salida: str) -> str:
    filas = barrido_niveles(seed=SEED, habilidad=0.8, niveles=[1, 2, 3, 4])
    x = [f["nivel"] for f in filas]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([n - 0.2 for n in x], [f["hits"] for f in filas], width=0.4, label="hits")
    ax.bar([n + 0.2 for n in x], [f["misses"] for f in filas], width=0.4, label="misses")
    ax.set_xlabel("nivel"); ax.set_ylabel("conteo")
    ax.set_title("E3 — Desempeño por nivel (Velocidad, habilidad 80%)")
    ax.set_xticks(x); ax.legend(); ax.grid(True, axis="y", alpha=0.3)
    ruta = os.path.join(salida, "E3_niveles.png")
    fig.tight_layout(); fig.savefig(ruta, dpi=120); plt.close(fig)
    return ruta


def _fig_trayectoria(salida: str) -> str:
    buena = trayectoria_adaptativa(seed=SEED, habilidad=0.95, nivel_inicial=1, n_sesiones=8)
    mala = trayectoria_adaptativa(seed=SEED, habilidad=0.1, nivel_inicial=4, n_sesiones=8)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([f["sesion"] for f in buena], [f["nivel"] for f in buena], "-o",
            color="tab:green", label="jugador hábil")
    ax.plot([f["sesion"] for f in mala], [f["nivel"] for f in mala], "-o",
            color="tab:red", label="jugador con dificultad")
    ax.set_xlabel("sesión"); ax.set_ylabel("nivel")
    ax.set_yticks([1, 2, 3, 4])
    ax.set_title("E4 — Trayectoria de nivel entre sesiones (adaptación)")
    ax.legend(); ax.grid(True, alpha=0.3)
    ruta = os.path.join(salida, "E4_trayectoria.png")
    fig.tight_layout(); fig.savefig(ruta, dpi=120); plt.close(fig)
    return ruta


def main(salida: str = os.path.join(RAIZ, "docs", "evidencia")) -> list[str]:
    os.makedirs(salida, exist_ok=True)
    return [_fig_adaptacion(salida), _fig_niveles(salida), _fig_trayectoria(salida)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera figuras de evidencia (E2/E3/E4).")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "docs", "evidencia"))
    args = ap.parse_args()
    for r in main(args.salida):
        print("escrita:", r)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest simulator/test_generar_evidencia_smoke.py -v`
Expected: 1 passed.

- [ ] **Step 5: Generate the real figures and eyeball them**

Run: `.venv/bin/python scripts/generar_evidencia.py`
Expected: tres PNG en `docs/evidencia/` (E2/E3/E4). Abrir y verificar visualmente que E2 sube de rojo→verde con la habilidad, E3 muestra hits altos, E4 converge.

- [ ] **Step 6: Run the full suite**

Run: `./scripts/run_all_tests.sh`
Expected: TODO VERDE (C++ + pytest, ahora con los nuevos tests del jugador/evidencia).

- [ ] **Step 7: Commit**

```bash
git add scripts/generar_evidencia.py simulator/test_generar_evidencia_smoke.py docs/evidencia/
git commit -m "SP2: figuras de evidencia E2/E3/E4 (generador CLI)"
```

---

## Self-Review

**1. Spec coverage:** E1 (determinismo) → Task 1 `test_determinismo...`. E2 (adaptación) → Task 1 (suggest up/down) + Task 3 `_fig_adaptacion`. E3 (desempeño por nivel) → Task 2 `barrido_niveles` + `_fig_niveles`. E4 (evolución/trayectoria) → Task 2 `trayectoria_adaptativa` + `_fig_trayectoria`. Componente A del spec (generador) cubierto para Velocidad. Memoria/Equilibrio y E5/E6 (banco) quedan fuera de este incremento por diseño (plazo).

**2. Placeholder scan:** sin TBD/TODO; todo el código está completo y proviene de un spike verificado.

**3. Type consistency:** `jugar_sesion` devuelve dict con `suggests`/`scores`; `evidencia.py` lee `r["suggests"][-1]["dir"]`/`["level"]` (coincide con el protocolo `suggest`); las figuras consumen las claves que producen los barridos (`habilidad,hits,misses,rondas,dir,nivel,sesion`). Consistente.

## Fuera de alcance (próximos incrementos)

- Jugador para Memoria (fase exhibición vs repetición) y Equilibrio (celdas simultáneas).
- Analítica embebida en el dashboard (vista de evidencia/historial) — componente B del spec.
- Reconexión TCP — componente C del spec.
- Captura de banco E5/E6 — al flashear el hardware.

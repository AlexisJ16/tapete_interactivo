"""Diagrama de bloques del sistema (figura del articulo).

Fuente de verdad de la conectividad: `firmware/lib/GameCore/Config.h` (pines) y
`docs/hardware/cableado.md`. Los pines NO se escriben a mano aqui: se leen de Config.h,
de modo que el diagrama no puede divergir del firmware.

    .venv/bin/python scripts/gen_diagrama_bloques.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RAIZ, "firmware", "lib", "GameCore", "Config.h")
SALIDA = os.path.join(RAIZ, "docs", "evidencia")


def _lista(nombre: str) -> list[int]:
    """Lee un array de enteros de Config.h, p.ej. PIN_FSR / PIN_LED."""
    with open(CONFIG, encoding="utf-8") as f:
        texto = f.read()
    m = re.search(rf"{nombre}\s*\[[^\]]*\]\s*=\s*\{{([^}}]*)\}}", texto)
    if not m:
        raise RuntimeError(f"no se encontro {nombre} en Config.h")
    return [int(x) for x in re.findall(r"\d+", m.group(1))]


def _entero(nombre: str) -> int:
    with open(CONFIG, encoding="utf-8") as f:
        m = re.search(rf"{nombre}\s*=\s*(\d+)", f.read())
    if not m:
        raise RuntimeError(f"no se encontro {nombre} en Config.h")
    return int(m.group(1))


def dot() -> str:
    fsr = _lista("PIN_FSR")
    led = _lista("PIN_LED")
    tx = _entero("PIN_DFPLAYER_TX")
    rx = _entero("PIN_DFPLAYER_RX")
    puerto = _entero("PUERTO_TCP")

    fsr_txt = ", ".join(f"GPIO{p}" for p in fsr)
    led_txt = ", ".join(f"GPIO{p}" for p in led)

    # splines=ortho NO dibuja las etiquetas de las aristas; se usan splines normales.
    # rankdir=TB: con solo cuatro etapas, la disposicion horizontal daba una franja de 8:1.
    return f"""digraph tapete {{
  rankdir=TB;
  splines=spline;
  nodesep=0.5;
  ranksep=0.7;
  compound=true;
  fontname="DejaVu Sans";
  node [fontname="DejaVu Sans", fontsize=10, shape=box, style="rounded,filled", fillcolor=white];
  edge [fontname="DejaVu Sans", fontsize=8.5, color="#444444"];

  subgraph cluster_33 {{
    label="Dominio 3,3 V — sensado";
    style="rounded,dashed"; color="#1f77b4"; fontcolor="#1f77b4"; fontsize=10;
    FSR [label="6 × sensor FSR 402\\ndivisor con 10 kΩ a masa", fillcolor="#eaf2fb"];
  }}

  subgraph cluster_esp {{
    label="Cómputo";
    style="rounded,dashed"; color="#555555"; fontsize=10;
    ESP [label="ESP32 DevKit\\nGameCore: 3 modos + recomendador\\n(motor no bloqueante)",
         fillcolor="#fdf6e3", height=1.1];
  }}

  subgraph cluster_5 {{
    label="Dominio 5 V — actuación";
    style="rounded,dashed"; color="#d62728"; fontcolor="#d62728"; fontsize=10;
    ULN [label="ULN2803A\\ndriver Darlington", fillcolor="#fdeaea"];
    LED [label="6 grupos × 3 LED blancos\\n(2,2 kΩ en serie por grupo)", fillcolor="#fdeaea"];
    DF  [label="DFPlayer Mini\\n+ microSD", fillcolor="#fdeaea"];
    SPK [label="parlante 4 Ω / 3 W", shape=box, fillcolor="#fdeaea"];
  }}

  PC [label="PC del terapeuta\\ndashboard PyQt6 + SQLite\\nexportación CSV / PDF",
      fillcolor="#eafaea", height=0.9];

  PC  -> ESP [label="  protocolo JSON por líneas\\l  USB serie 115 200 bd\\l  o TCP {puerto} por WiFi\\l", dir=both];
  ESP -> FSR [label="  6 × ADC1\\l  {fsr_txt}\\l", dir=back];
  ESP -> ULN [label="  6 × PWM\\l  {led_txt}\\l"];
  ESP -> DF  [label="  UART2\\l  TX=GPIO{tx}, RX=GPIO{rx}\\l"];
  ULN -> LED [label="  conmutación a 5 V"];
  DF  -> SPK [label="  audio diferencial"];
}}
"""


def main(salida: str = SALIDA) -> list[str]:
    os.makedirs(salida, exist_ok=True)
    fuente = os.path.join(salida, "diagrama_bloques.dot")
    with open(fuente, "w", encoding="utf-8") as f:
        f.write(dot())
    rutas = []
    for fmt in ("png", "pdf"):
        ruta = os.path.join(salida, f"diagrama_bloques.{fmt}")
        subprocess.run(["dot", f"-T{fmt}", "-Gdpi=140", fuente, "-o", ruta], check=True)
        rutas.append(ruta)
    return rutas


if __name__ == "__main__":
    for r in main():
        print(f"OK: {r}")
    sys.exit(0)

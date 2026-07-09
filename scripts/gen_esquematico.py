"""Regenera el esquematico, lo valida con ERC y exporta las figuras del articulo.

Cadena completa y reproducible:
    gen_tapete.py  ->  tapete.kicad_sch
    kicad-cli erc  ->  0 infracciones (si no, aborta)
    kicad-cli pdf/svg -> plano vectorial
    pdftoppm + rotacion -> docs/evidencia/esquematico.png (anexo del articulo)

La rotacion es deliberada: el plano es A3 apaisado y el articulo, vertical; sin
rotar, la figura ocupa un tercio de la pagina y no se puede leer.

    .venv/bin/python scripts/gen_esquematico.py
"""
from __future__ import annotations

import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KICAD = os.path.join(RAIZ, "docs", "hardware", "kicad")
EVID = os.path.join(RAIZ, "docs", "evidencia")
SCH = os.path.join(KICAD, "tapete.kicad_sch")


def _run(cmd: list[str], cwd: str | None = None) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"fallo {' '.join(cmd[:2])}:\n{r.stdout}\n{r.stderr}")
    return r.stdout


def main() -> int:
    py = sys.executable
    _run([py, os.path.join(KICAD, "gen_tapete.py"), "all"], cwd=KICAD)

    # ERC: --exit-code-violations hace que kicad-cli devuelva != 0 si hay infracciones.
    _run(["kicad-cli", "sch", "erc", "--exit-code-violations",
          "-o", os.path.join(KICAD, "erc.rpt"), SCH], cwd=KICAD)

    _run(["kicad-cli", "sch", "export", "pdf", "-o",
          os.path.join(KICAD, "tapete.pdf"), SCH], cwd=KICAD)
    _run(["kicad-cli", "sch", "export", "svg", "-o", KICAD, SCH], cwd=KICAD)

    os.makedirs(EVID, exist_ok=True)
    tmp = os.path.join(EVID, "_sch")
    _run(["pdftoppm", "-png", "-r", "200", "-f", "1", "-l", "1",
          os.path.join(KICAD, "tapete.pdf"), tmp])

    from PIL import Image
    origen = f"{tmp}-1.png"
    destino = os.path.join(EVID, "esquematico.png")
    with Image.open(origen) as im:
        im.rotate(90, expand=True).save(destino)   # A3 apaisado -> pagina vertical
    os.remove(origen)

    print(f"OK: ERC sin infracciones\nOK: {os.path.join(KICAD, 'tapete.pdf')}\nOK: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

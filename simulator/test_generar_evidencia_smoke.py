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

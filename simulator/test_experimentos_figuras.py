"""La figura de adaptacion (E3) se dibuja del MISMO dict que va a resultados.json.

Calcular y dibujar no pueden ser dos caminos de codigo: una figura que recomputa el
barrido por su cuenta puede divergir en silencio de la cifra publicada en el articulo.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))
import experimentos  # noqa: E402


def test_figura_adaptacion_escribe_el_png(tmp_path):
    ruta = experimentos.figura_adaptacion(experimentos.adaptacion(), str(tmp_path))
    assert os.path.basename(ruta) == "E3_adaptacion.png"
    assert os.path.getsize(ruta) > 0


def test_figura_adaptacion_no_recomputa_el_barrido(tmp_path):
    """Se le pasan datos arbitrarios y los dibuja: no vuelve a llamar al jugador."""
    datos = {"Velocidad": [{"habilidad": h / 10, "tasa": 10.0 * h, "hits": h,
                            "misses": 10 - h, "rondas": 10, "dir": "keep"}
                           for h in range(11)]}
    ruta = experimentos.figura_adaptacion(datos, str(tmp_path))
    assert os.path.getsize(ruta) > 0

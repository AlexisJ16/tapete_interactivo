"""Test pytest: todos los golden vectors deben pasar contra GameCore.so."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from golden_runner import cargar_vectores, correr_todos


def _nombres():
    return [e.get("name", f"escenario_{i}")
            for i, e in enumerate(cargar_vectores()["scenarios"])]


@pytest.fixture(scope="module")
def resultados():
    return {r.nombre: r for r in correr_todos()}


@pytest.mark.parametrize("nombre", _nombres())
def test_golden_vector(resultados, nombre):
    r = resultados[nombre]
    assert r.ok, f"Golden vector '{nombre}' fallo:{r.detalle}"

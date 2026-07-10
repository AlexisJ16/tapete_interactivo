"""La semilla de cada partida es aleatoria salvo que se fije (smoke/tests)."""
from app import semilla_efectiva


def test_respeta_la_semilla_fijada():
    assert semilla_efectiva(12345) == 12345


def test_none_da_semilla_aleatoria_no_nula_en_rango():
    vals = {semilla_efectiva(None) for _ in range(64)}
    assert len(vals) > 1                                  # varía entre partidas
    assert all(1 <= v <= 0xFFFFFFFF for v in vals)        # rango xorshift válido (!=0)

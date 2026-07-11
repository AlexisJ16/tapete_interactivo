"""Lo que el terapeuta necesita para trabajar: exportar de verdad y consultar el pasado.

Los tres fallos que el autor encontro usando la aplicacion (2026-07-11):
  1. Pulsar "Exportar" sin una sesion no hacia NADA, ni un mensaje: parecia rota.
  2. Cuando exportaba, el archivo caia en una carpeta interna del programa que el
     medico nunca ve (y dentro del .exe, enterrada en el bundle).
  3. No habia forma de consultar ni exportar una terapia pasada: los datos estaban en
     SQLite, pero la pantalla no los mostraba.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simulator"))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import app as A  # noqa: E402
from fuente import FuenteCore  # noqa: E402
from storage import Almacen  # noqa: E402


@pytest.fixture
def qapp():
    from PyQt6 import QtWidgets
    yield QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def ventana(qapp):
    return A.VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))


def _jugar(v, modo_idx=1, nivel=1):
    v.semilla = 123
    v.cb_modo.setCurrentIndex(modo_idx)
    v.sp_nivel.setValue(nivel)
    v._start()
    for _ in range(8):
        v.tick()
        celda = next((i for i in range(1, 7) if v.ses.leds[i] > 0), None)
        if celda is None:
            break
        v.fuente.pisar(celda)
        v.tick()
    return v.ses.sesion_id


def test_exportar_sin_sesion_avisa_en_vez_de_no_hacer_nada(ventana):
    ventana._exportar("csv")
    assert ventana.lbl_export.text(), "el boton no dijo nada: el medico cree que esta roto"
    assert "sesion" in ventana.lbl_export.text().lower()


def test_exportar_pregunta_donde_guardar_y_escribe_ahi(ventana, tmp_path, monkeypatch):
    sid = _jugar(ventana)
    destino = str(tmp_path / "reporte_del_medico.csv")
    monkeypatch.setattr(ventana, "_pedir_ruta_guardado", lambda sugerido, filtro: destino)

    ventana._exportar("csv")

    assert os.path.exists(destino), "no escribio donde el medico eligio"
    assert destino in ventana.lbl_export.text()
    assert sid is not None


def test_si_el_medico_cancela_el_dialogo_no_se_exporta(ventana, monkeypatch):
    _jugar(ventana)
    monkeypatch.setattr(ventana, "_pedir_ruta_guardado", lambda sugerido, filtro: "")
    ventana._exportar("pdf")
    assert "cancel" in ventana.lbl_export.text().lower()


def test_el_nombre_sugerido_identifica_al_paciente_y_la_fecha(ventana):
    sid = _jugar(ventana)
    sugerido = ventana._nombre_sugerido(sid, "csv")
    assert sugerido.endswith(".csv")
    assert str(sid) in sugerido


def test_el_historico_lista_las_sesiones_del_paciente(ventana):
    ventana.almacen.upsert_perfil("juan", "Juan Perez")
    for modo in (1, 2):
        ventana.almacen.iniciar_sesion("juan", modo, 1)
    ventana.almacen.upsert_perfil("ana", "Ana Ruiz")
    ventana.almacen.iniciar_sesion("ana", 3, 2)

    ventana.panel.refrescar()
    ventana.panel.seleccionar_perfil("juan")

    assert ventana.panel.tabla.rowCount() == 2, "el medico no ve las terapias de su paciente"
    ventana.panel.seleccionar_perfil("ana")
    assert ventana.panel.tabla.rowCount() == 1


def test_el_medico_exporta_una_terapia_PASADA_desde_el_historico(ventana, tmp_path, monkeypatch):
    sid = _jugar(ventana)                      # una sesion que ya termino
    ventana.panel.refrescar()
    ventana.panel.seleccionar_perfil(ventana.ses.perfil_id)
    ventana.panel.tabla.selectRow(0)

    destino = str(tmp_path / "terapia_pasada.pdf")
    monkeypatch.setattr(ventana.panel, "_pedir_ruta_guardado", lambda sugerido, filtro: destino)
    ventana.panel.exportar_seleccionada("pdf")

    assert os.path.exists(destino), "no se puede exportar una terapia de hace semanas"
    assert sid is not None


def test_el_selector_de_pacientes_ofrece_los_ya_creados(ventana):
    ventana.almacen.upsert_perfil("juan", "Juan Perez")
    ventana.almacen.upsert_perfil("ana", "Ana Ruiz")
    ventana.recargar_pacientes()

    ids = [ventana.cb_paciente.itemData(i) for i in range(ventana.cb_paciente.count())]
    assert "juan" in ids and "ana" in ids, "el medico tiene que teclear el id a mano y se duplican los casos"

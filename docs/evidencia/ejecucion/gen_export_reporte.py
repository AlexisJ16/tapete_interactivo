"""Ejercita la exportacion de reportes del dashboard (CSV y PDF) con datos de una
partida REAL simulada sobre GameCore. Evidencia de storage.py (SQLite) + reports.py.

Corre el escenario de Velocidad, persiste la sesion y sus eventos en una base SQLite
y exporta el resumen a CSV y a PDF (una pagina con grafico de aciertos/errores).

    python docs/evidencia/ejecucion/gen_export_reporte.py
"""
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SALIDA = os.path.join(os.path.dirname(__file__), "reportes")
os.makedirs(SALIDA, exist_ok=True)
sys.path.insert(0, os.path.join(RAIZ, "simulator"))
sys.path.insert(0, os.path.join(RAIZ, "dashboard"))

from golden_runner import cargar_vectores, reproducir   # noqa: E402
from storage import Almacen                              # noqa: E402
from reports import exportar_csv, exportar_pdf           # noqa: E402


def main():
    escenarios = cargar_vectores()["scenarios"]
    esc = next(e for e in escenarios if e["name"] == "velocidad_strict_dos_aciertos")
    eventos = reproducir(esc)   # eventos reales emitidos por GameCore

    db = os.path.join(SALIDA, "tapete_demo.sqlite")
    if os.path.exists(db):
        os.remove(db)
    alm = Almacen(db)
    alm.upsert_perfil("p001", "Demo")
    sid = alm.iniciar_sesion("p001", esc["config"]["mode"], esc["config"]["level"])

    hits = misses = rt = rondas = 0
    for ev in eventos:
        ms = ev.get("ms", 0)
        alm.registrar_evento(sid, ms, ev.get("ev", "?"), ev)
        if ev.get("ev") == "score":
            hits, misses, rondas = ev["hits"], ev["misses"], ev["round"]
            rt = ev["rt_ms"]
    alm.actualizar_metricas(sid, hits, misses, float(rt), rondas)
    alm.cerrar_sesion(sid, "finished")

    csv_path = exportar_csv(alm, sid, os.path.join(SALIDA, "sesion_ejemplo.csv"))
    pdf_path = exportar_pdf(alm, sid, os.path.join(SALIDA, "sesion_ejemplo.pdf"))
    alm.cerrar()

    print(f"sesion {sid}: hits={hits} misses={misses} rondas={rondas}")
    print(f"eventos persistidos: {len(eventos)}")
    print(f"CSV -> {csv_path}")
    print(f"PDF -> {pdf_path}")
    print("\n--- contenido del CSV ---")
    with open(csv_path, encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    main()

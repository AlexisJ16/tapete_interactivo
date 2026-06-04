"""Persistencia SQLite: perfiles, sesiones y eventos.

Capa de almacenamiento "tonta": solo guarda y consulta. El calculo de metricas
lo hace el controlador de sesion (sesion.py); aqui se persiste el resumen y el
log de eventos para poder exportar y auditar.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime

ESQUEMA = """
CREATE TABLE IF NOT EXISTS perfiles (
    id      TEXT PRIMARY KEY,
    nombre  TEXT NOT NULL,
    creado  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sesiones (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil_id    TEXT,
    modo         INTEGER NOT NULL,
    nivel        INTEGER NOT NULL,
    inicio       TEXT NOT NULL,
    fin          TEXT,
    hits         INTEGER DEFAULT 0,
    misses       INTEGER DEFAULT 0,
    rt_prom_ms   REAL DEFAULT 0,
    rondas       INTEGER DEFAULT 0,
    estado_final TEXT,
    FOREIGN KEY (perfil_id) REFERENCES perfiles (id)
);
CREATE TABLE IF NOT EXISTS eventos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id INTEGER NOT NULL,
    ms        INTEGER,
    tipo      TEXT,
    datos     TEXT,
    FOREIGN KEY (sesion_id) REFERENCES sesiones (id)
);
"""


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Almacen:
    def __init__(self, ruta: str = "tapete.sqlite"):
        self.ruta = ruta
        self.con = sqlite3.connect(ruta)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.executescript(ESQUEMA)
        self.con.commit()

    # --- perfiles ---
    def upsert_perfil(self, id: str, nombre: str) -> None:
        self.con.execute(
            "INSERT INTO perfiles (id, nombre, creado) VALUES (?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET nombre = excluded.nombre",
            (id, nombre, _ahora()),
        )
        self.con.commit()

    def perfiles(self) -> list[dict]:
        cur = self.con.execute("SELECT * FROM perfiles ORDER BY id")
        return [dict(r) for r in cur.fetchall()]

    # --- sesiones ---
    def iniciar_sesion(self, perfil_id: str | None, modo: int, nivel: int) -> int:
        cur = self.con.execute(
            "INSERT INTO sesiones (perfil_id, modo, nivel, inicio) VALUES (?, ?, ?, ?)",
            (perfil_id, modo, nivel, _ahora()),
        )
        self.con.commit()
        return int(cur.lastrowid)

    def actualizar_metricas(self, sesion_id: int, hits: int, misses: int,
                            rt_prom_ms: float, rondas: int) -> None:
        self.con.execute(
            "UPDATE sesiones SET hits = ?, misses = ?, rt_prom_ms = ?, rondas = ? WHERE id = ?",
            (hits, misses, rt_prom_ms, rondas, sesion_id),
        )
        self.con.commit()

    def cerrar_sesion(self, sesion_id: int, estado_final: str) -> None:
        self.con.execute(
            "UPDATE sesiones SET fin = ?, estado_final = ? WHERE id = ?",
            (_ahora(), estado_final, sesion_id),
        )
        self.con.commit()

    def sesion(self, sesion_id: int) -> dict | None:
        cur = self.con.execute("SELECT * FROM sesiones WHERE id = ?", (sesion_id,))
        r = cur.fetchone()
        return dict(r) if r else None

    def sesiones(self, perfil_id: str | None = None) -> list[dict]:
        if perfil_id is None:
            cur = self.con.execute("SELECT * FROM sesiones ORDER BY id")
        else:
            cur = self.con.execute(
                "SELECT * FROM sesiones WHERE perfil_id = ? ORDER BY id", (perfil_id,)
            )
        return [dict(r) for r in cur.fetchall()]

    # --- eventos ---
    def registrar_evento(self, sesion_id: int, ms: int, tipo: str, datos: dict) -> None:
        self.con.execute(
            "INSERT INTO eventos (sesion_id, ms, tipo, datos) VALUES (?, ?, ?, ?)",
            (sesion_id, ms, tipo, json.dumps(datos)),
        )
        self.con.commit()

    def eventos(self, sesion_id: int) -> list[dict]:
        cur = self.con.execute(
            "SELECT * FROM eventos WHERE sesion_id = ? ORDER BY id", (sesion_id,)
        )
        out = []
        for r in cur.fetchall():
            d = dict(r)
            d["datos"] = json.loads(d["datos"]) if d["datos"] else {}
            out.append(d)
        return out

    def cerrar(self) -> None:
        self.con.close()

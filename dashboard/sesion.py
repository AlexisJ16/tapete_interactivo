"""Controlador de sesion: consume eventos del tapete, calcula metricas y persiste.

Es la logica del dashboard SIN interfaz grafica (para poder probarla headless).
La GUI (app.py) solo lo envuelve y dibuja el estado.
"""
from __future__ import annotations

import json

from fuente import Fuente
from storage import Almacen


class Sesion:
    def __init__(self, almacen: Almacen, fuente: Fuente):
        self.almacen = almacen
        self.fuente = fuente
        self.sesion_id: int | None = None
        self.perfil_id: str | None = None
        self.modo = 2
        self.nivel = 1
        self.estado = "idle"
        self.leds = [0] * 7          # brillo por casilla (1..6)
        self.hits = 0
        self.misses = 0
        self.rondas = 0
        self.ultimo_rt = 0
        self._rts: list[int] = []    # tiempos de reaccion (>0) para el promedio

    # --- configuracion / control ---
    def set_perfil(self, id: str, nombre: str) -> None:
        self.almacen.upsert_perfil(id, nombre)
        self.perfil_id = id

    def sembrar(self, seed: int) -> None:
        self.fuente.enviar(json.dumps({"cmd": "set_seed", "seed": seed}))

    def configurar(self, modo: int, nivel: int) -> None:
        self.modo, self.nivel = modo, nivel
        self.fuente.enviar(json.dumps({"cmd": "set_mode", "mode": modo, "level": nivel}))

    def set_nivel(self, nivel: int) -> None:
        self.nivel = nivel
        self.fuente.enviar(json.dumps({"cmd": "set_level", "level": nivel}))

    def iniciar(self) -> int:
        self._reset_metricas()
        self.sesion_id = self.almacen.iniciar_sesion(self.perfil_id, self.modo, self.nivel)
        self.fuente.enviar(json.dumps({"cmd": "start"}))
        return self.sesion_id

    def detener(self) -> None:
        self.fuente.enviar(json.dumps({"cmd": "stop"}))

    def pausar(self) -> None:
        self.fuente.enviar(json.dumps({"cmd": "pause"}))

    def _reset_metricas(self) -> None:
        self.hits = self.misses = self.rondas = self.ultimo_rt = 0
        self._rts = []
        self.leds = [0] * 7

    # --- bucle de eventos ---
    def bombear(self) -> None:
        """Procesa todos los eventos pendientes de la fuente."""
        for linea in self.fuente.recibir():
            try:
                ev = json.loads(linea)
            except json.JSONDecodeError:
                continue
            self._procesar(ev)

    def _procesar(self, ev: dict) -> None:
        tipo = ev.get("ev")
        if tipo == "led":
            self.leds[ev["cell"]] = ev["level"]
        elif tipo == "press":
            self._log(ev.get("ms", 0), "press", {"cell": ev["cell"]})
        elif tipo == "sound":
            pass  # el sonido lo gestiona el simulador/ESP32, no el dashboard
        elif tipo == "score":
            self.hits = ev["hits"]
            self.misses = ev["misses"]
            self.rondas = ev["round"]
            self.ultimo_rt = ev["rt_ms"]
            if ev["rt_ms"] > 0:
                self._rts.append(ev["rt_ms"])
            self._log(0, "score", ev)
            self._persistir_metricas()
        elif tipo == "state":
            self.estado = ev["status"]
            if self.estado == "finished":
                self._cerrar()

    def _log(self, ms: int, tipo: str, datos: dict) -> None:
        if self.sesion_id is not None:
            self.almacen.registrar_evento(self.sesion_id, ms, tipo, datos)

    @property
    def rt_prom(self) -> float:
        return round(sum(self._rts) / len(self._rts), 1) if self._rts else 0.0

    def _persistir_metricas(self) -> None:
        if self.sesion_id is not None:
            self.almacen.actualizar_metricas(
                self.sesion_id, self.hits, self.misses, self.rt_prom, self.rondas
            )

    def _cerrar(self) -> None:
        if self.sesion_id is not None:
            self._persistir_metricas()
            self.almacen.cerrar_sesion(self.sesion_id, self.estado)

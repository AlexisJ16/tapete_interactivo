"""Controlador de sesion: consume eventos del tapete, calcula metricas y persiste.

Es la logica del dashboard SIN interfaz grafica (para poder probarla headless).
La GUI (app.py) solo lo envuelve y dibuja el estado.
"""
from __future__ import annotations

import json

from fuente import Fuente
from storage import Almacen


def _es_int(x) -> bool:
    """int de verdad (excluye bool, que es subclase de int)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _como_int(x, defecto: int = 0) -> int:
    return x if _es_int(x) else defecto


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
        self.resultados: list[bool] = []    # acierto/error por ronda (para la tendencia en vivo)
        self.ultima_sugerencia: dict = {}   # ultima recomendacion (SP1; UI en SP2)

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
        self.resultados = []
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

    def _celda_valida(self, c) -> bool:
        # 1..6 (leds tiene 7 slots: 0 no se usa). Excluye bool y fuera de rango.
        return _es_int(c) and 1 <= c < len(self.leds)

    def _procesar(self, ev: dict) -> None:
        # Frontera: el evento viene de una fuente externa (core, o el ESP32 por
        # serial/TCP, que puede mezclar ruido). Se valida aqui; una entrada
        # malformada se descarta sin lanzar ni corromper estado.
        if not isinstance(ev, dict):
            return
        tipo = ev.get("ev")
        if tipo == "led":
            cell, level = ev.get("cell"), ev.get("level")
            if self._celda_valida(cell) and _es_int(level):
                self.leds[cell] = level
        elif tipo == "press":
            cell = ev.get("cell")
            if self._celda_valida(cell):
                self._log(_como_int(ev.get("ms")), "press", {"cell": cell})
        elif tipo == "sound":
            pass  # el sonido lo gestiona el simulador/ESP32, no el dashboard
        elif tipo == "score":
            hits, misses = ev.get("hits"), ev.get("misses")
            ronda, rt = ev.get("round"), ev.get("rt_ms")
            if not all(_es_int(x) for x in (hits, misses, ronda, rt)):
                return
            # Cada score resuelve una ronda subiendo +1 hits o +1 misses; el
            # delta dice si fue acierto o error (base de la tendencia en vivo).
            if hits > self.hits:
                self.resultados.append(True)
            elif misses > self.misses:
                self.resultados.append(False)
            self.hits, self.misses, self.rondas, self.ultimo_rt = hits, misses, ronda, rt
            if rt > 0:
                self._rts.append(rt)
            self._log(0, "score", ev)
            self._persistir_metricas()
        elif tipo == "suggest":
            self.ultima_sugerencia = ev   # se reconoce; la vista en vivo es SP2
        elif tipo == "state":
            status = ev.get("status")
            if isinstance(status, str):
                self.estado = status
                if status == "finished":
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

"""Simulador visual del Tapete Interactivo (Pygame).

Reemplaza al ESP32 en software: ejecuta el MISMO GameCore.so vvia core_bridge.
- Clic en una casilla = pisada.
- Los LEDs son BLANCOS: se dibujan apagados / encendidos / con brillo (PWM 0..255),
  nunca con color (el hardware real no es RGB).
- Los sonidos se reproducen desde audio/000X.mp3 (si el archivo existe).

Controles de teclado:
  1 / 2 / 3 : elegir modo (Memoria / Velocidad / Equilibrio)
  + / -     : subir / bajar nivel
  S         : start    X : stop    P : pausa/reanudar    R : re-sembrar aleatorio

Uso:
  python tapete_sim.py            # ventana interactiva
  python tapete_sim.py --smoke    # prueba headless (sin pantalla), valida el flujo
"""
from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_bridge import RAIZ, CoreBridge  # noqa: E402

AUDIO_DIR = os.path.join(RAIZ, "audio")

CELDAS = 6
FILAS, COLUMNAS = 2, 3
ANCHO, ALTO = 720, 560
MARGEN = 40
HUD_ALTO = 120

NOMBRES_MODO = {1: "Memoria", 2: "Velocidad", 3: "Equilibrio"}


class Simulador:
    def __init__(self, headless: bool = False):
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        import pygame  # import diferido: permite usar el bridge sin pygame
        self.pygame = pygame
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Tapete Interactivo — Simulador")
        self.fuente = pygame.font.SysFont("monospace", 18)
        self.fuente_grande = pygame.font.SysFont("monospace", 28, bold=True)
        self.reloj = pygame.time.Clock()

        # Audio: opcional; si no hay dispositivo, se desactiva sin romper.
        self.sonidos: dict[int, object] = {}
        self.audio_ok = False
        try:
            pygame.mixer.init()
            self.audio_ok = True
        except Exception:
            self.audio_ok = False

        self.core = CoreBridge()
        self.leds = [0] * (CELDAS + 1)          # brillo 0..255 por casilla (1..6)
        self.modo = 2
        self.nivel = 1
        self.estado = "idle"
        self.ultimo_score = {}
        self.ultima_sugerencia = {}
        self.core.comando(json.dumps({"cmd": "set_mode", "mode": self.modo, "level": self.nivel}))

    # --- comunicacion con el motor ---
    def _ahora(self) -> int:
        return self.pygame.time.get_ticks()

    def _sincronizar_reloj(self):
        self.core.set_millis(self._ahora())

    def _drenar(self):
        for linea in self.core.drenar_eventos():
            ev = json.loads(linea)
            t = ev.get("ev")
            if t == "led":
                self.leds[ev["cell"]] = ev["level"]
            elif t == "sound":
                self._reproducir(ev["id"])
            elif t == "score":
                self.ultimo_score = ev
            elif t == "suggest":
                self.ultima_sugerencia = ev
            elif t == "state":
                self.estado = ev["status"]

    def _reproducir(self, sonido_id: int):
        if not self.audio_ok:
            return
        snd = self.sonidos.get(sonido_id)
        if snd is None:
            ruta = os.path.join(AUDIO_DIR, f"{sonido_id:04d}.mp3")
            if not os.path.exists(ruta):
                return  # falta el MP3: se ignora silenciosamente
            try:
                snd = self.pygame.mixer.Sound(ruta)
            except Exception:
                return
            self.sonidos[sonido_id] = snd
        snd.play()

    def comando(self, d: dict):
        self._sincronizar_reloj()
        self.core.comando(json.dumps(d))
        self._drenar()

    def pisar(self, celda: int):
        self._sincronizar_reloj()
        self.core.pisar(celda)
        self._drenar()

    def resembrar(self):
        """Re-siembra el RNG del core con una semilla aleatoria (tecla R)."""
        self.comando({"cmd": "set_seed", "seed": random.randint(1, 0xFFFFFFFF)})

    # --- geometria ---
    def _rect_celda(self, celda: int):
        idx = celda - 1
        fila, col = divmod(idx, COLUMNAS)
        ancho_zona = ANCHO - 2 * MARGEN
        alto_zona = ALTO - HUD_ALTO - 2 * MARGEN
        cw = ancho_zona / COLUMNAS
        ch = alto_zona / FILAS
        x = MARGEN + col * cw
        y = MARGEN + fila * ch
        pad = 12
        return self.pygame.Rect(int(x + pad), int(y + pad), int(cw - 2 * pad), int(ch - 2 * pad))

    def _celda_en(self, pos):
        for c in range(1, CELDAS + 1):
            if self._rect_celda(c).collidepoint(pos):
                return c
        return None

    # --- dibujo ---
    def dibujar(self):
        pg = self.pygame
        self.pantalla.fill((18, 18, 22))
        for c in range(1, CELDAS + 1):
            rect = self._rect_celda(c)
            nivel = self.leds[c]
            # LED BLANCO: el brillo mapea a una escala de gris (apagado=gris oscuro).
            base = 35
            v = base + int((255 - base) * (nivel / 255.0))
            pg.draw.rect(self.pantalla, (v, v, v), rect, border_radius=16)
            pg.draw.rect(self.pantalla, (90, 90, 110), rect, width=2, border_radius=16)
            etq = self.fuente_grande.render(str(c), True,
                                            (10, 10, 10) if nivel > 128 else (200, 200, 210))
            self.pantalla.blit(etq, etq.get_rect(center=rect.center))
        self._dibujar_hud()
        pg.display.flip()

    def _dibujar_hud(self):
        pg = self.pygame
        y0 = ALTO - HUD_ALTO + 8
        s = self.ultimo_score
        lineas = [
            f"Modo {self.modo} ({NOMBRES_MODO.get(self.modo,'?')})   Nivel {self.nivel}   Estado: {self.estado}",
            f"Score  hits={s.get('hits',0)}  misses={s.get('misses',0)}  rt={s.get('rt_ms',0)}ms  ronda={s.get('round',0)}",
            "Teclas: [1/2/3] modo   [+/-] nivel   [S]tart  [X]stop  [P]ausa  |  clic = pisada",
        ]
        for i, txt in enumerate(lineas):
            self.pantalla.blit(self.fuente.render(txt, True, (210, 210, 220)), (MARGEN, y0 + i * 26))

    # --- bucle principal ---
    def procesar_teclado(self, ev):
        pg = self.pygame
        if ev.key in (pg.K_1, pg.K_2, pg.K_3):
            self.modo = {pg.K_1: 1, pg.K_2: 2, pg.K_3: 3}[ev.key]
            self.comando({"cmd": "set_mode", "mode": self.modo, "level": self.nivel})
        elif ev.key in (pg.K_PLUS, pg.K_EQUALS, pg.K_KP_PLUS):
            self.nivel = min(4, self.nivel + 1)
            self.comando({"cmd": "set_level", "level": self.nivel})
        elif ev.key in (pg.K_MINUS, pg.K_KP_MINUS):
            self.nivel = max(1, self.nivel - 1)
            self.comando({"cmd": "set_level", "level": self.nivel})
        elif ev.key == pg.K_s:
            self.comando({"cmd": "start"})
        elif ev.key == pg.K_x:
            self.comando({"cmd": "stop"})
        elif ev.key == pg.K_p:
            self.comando({"cmd": "pause"})
        elif ev.key == pg.K_r:
            self.resembrar()

    def correr(self):
        pg = self.pygame
        corriendo = True
        while corriendo:
            self._sincronizar_reloj()
            self.core.actualizar()
            self._drenar()
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    corriendo = False
                elif ev.type == pg.KEYDOWN:
                    if ev.key == pg.K_ESCAPE:
                        corriendo = False
                    else:
                        self.procesar_teclado(ev)
                elif ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                    c = self._celda_en(ev.pos)
                    if c:
                        self.pisar(c)
            self.dibujar()
            self.reloj.tick(60)
        self.core.cerrar()
        pg.quit()


def smoke() -> int:
    """Prueba headless: arranca una sesion de Velocidad y simula pisadas.

    Valida de punta a punta: pygame init + bridge + flujo de eventos, sin pantalla.
    """
    sim = Simulador(headless=True)
    sim.comando({"cmd": "set_seed", "seed": 12345})
    sim.comando({"cmd": "set_mode", "mode": 2, "level": 1})
    sim.comando({"cmd": "start"})
    sim._drenar()
    # seed 12345 -> objetivos [3,4,5,...]; pisa el LED encendido.
    objetivos = [3, 4, 5]
    aciertos = 0
    for obj in objetivos:
        sim.core.actualizar()
        sim._drenar()
        encendida = next((c for c in range(1, CELDAS + 1) if sim.leds[c] > 0), None)
        sim.pisar(encendida if encendida else obj)
        if sim.ultimo_score.get("hits", 0) > aciertos:
            aciertos = sim.ultimo_score["hits"]
    sim.core.cerrar()
    sim.pygame.quit()
    print(f"[smoke] estado={sim.estado} aciertos={aciertos} leds={sim.leds[1:]}")
    ok = aciertos == 3
    print("[smoke] OK" if ok else "[smoke] FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        sys.exit(smoke())
    Simulador().correr()

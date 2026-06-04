"""Genera evidencia visual de que el simulador y el dashboard funcionan.

Renderiza estados reales de juego a PNG (headless) y arma un GIF del simulador.
No necesita pantalla (usa los drivers 'dummy'/'offscreen'), asi que sirve tanto
para CI como para inspeccion. Las capturas van a /tmp/tapete_demo/.
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = "/tmp/tapete_demo"
os.makedirs(SALIDA, exist_ok=True)


def capturar_simulador():
    """Juega una ronda de Velocidad y guarda frames PNG del tapete."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    sys.path.insert(0, os.path.join(RAIZ, "simulator"))
    import pygame
    from tapete_sim import Simulador

    sim = Simulador(headless=True)
    sim.comando({"cmd": "set_seed", "seed": 12345})
    sim.comando({"cmd": "set_mode", "mode": 2, "level": 1})
    sim.comando({"cmd": "start"})
    sim._drenar()

    frames = []
    n = 0

    def frame():
        nonlocal n
        sim.dibujar()
        ruta = os.path.join(SALIDA, f"sim_{n:03d}.png")
        pygame.image.save(sim.pantalla, ruta)
        frames.append(ruta)
        n += 1

    frame()  # objetivo inicial encendido
    for _ in range(4):
        encendida = next((c for c in range(1, 7) if sim.leds[c] > 0), None)
        if encendida is None:
            break
        sim.pisar(encendida)
        frame()  # tras el acierto: siguiente objetivo + score actualizado
    sim.core.cerrar()
    pygame.quit()

    # Construye un GIF con ffmpeg (2 fps). subprocess con lista de argumentos
    # (no shell): evita cualquier inyeccion; las rutas son constantes ademas.
    gif = os.path.join(SALIDA, "simulador.gif")
    subprocess.run(
        ["ffmpeg", "-y", "-framerate", "2", "-i", os.path.join(SALIDA, "sim_%03d.png"),
         "-vf", "scale=480:-1:flags=lanczos", gif],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    print(f"[simulador] {len(frames)} frames + {gif}")
    return frames[0], gif


def capturar_dashboard():
    """Renderiza la GUI del dashboard a PNG en una sesion de Velocidad."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    sys.path.insert(0, os.path.join(RAIZ, "dashboard"))
    from PyQt6 import QtWidgets
    from app import VentanaDashboard
    from fuente import FuenteCore
    from storage import Almacen

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    v = VentanaDashboard(fuente=FuenteCore(), almacen=Almacen(":memory:"))
    v.win.resize(780, 640)
    v.win.show()
    v.sp_seed.setValue(12345)
    v.cb_modo.setCurrentIndex(1)  # Velocidad
    v.sp_nivel.setValue(1)
    v.in_perfil_nombre.setText("Demo")
    v._start()
    v.tick()
    app.processEvents()

    # Objetivo encendido: captura inicial.
    png_inicio = os.path.join(SALIDA, "dashboard_inicio.png")
    v.win.grab().save(png_inicio)

    # Juega 3 aciertos y captura el estado con metricas.
    for _ in range(3):
        enc = next((c for c in range(1, 7) if v.ses.leds[c] > 0), None)
        if enc is None:
            break
        v.fuente.pisar(enc)
        v.tick()
        app.processEvents()
    png_juego = os.path.join(SALIDA, "dashboard_juego.png")
    v.win.grab().save(png_juego)
    print(f"[dashboard] {png_inicio} | {png_juego}  (hits={v.ses.hits})")
    return png_inicio, png_juego


if __name__ == "__main__":
    capturar_simulador()
    capturar_dashboard()
    print("Listo. Capturas en", SALIDA)

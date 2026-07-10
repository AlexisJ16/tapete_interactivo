"""Quema un rotulo dentro de cada captura para que su naturaleza (software /
simulador, no hardware fisico) no se pierda si alguien extrae solo el PNG.

    python docs/evidencia/ejecucion/rotular_capturas.py
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

CAP = os.path.join(os.path.dirname(__file__), "capturas")
FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ROTULOS = {
    "dashboard_inicio.png": "Dashboard del terapeuta (SOFTWARE), conectado al SIMULADOR — no es el tapete fisico",
    "dashboard_juego.png":  "Dashboard (SOFTWARE) en ejecucion, conectado al SIMULADOR — no es el tapete fisico",
    "sim_000.png": "Simulador de software del tapete — mismo GameCore que el ESP32 (no hardware fisico)",
    "sim_001.png": "Simulador de software del tapete — mismo GameCore que el ESP32 (no hardware fisico)",
    "sim_002.png": "Simulador de software del tapete — mismo GameCore que el ESP32 (no hardware fisico)",
    "sim_003.png": "Simulador de software del tapete — mismo GameCore que el ESP32 (no hardware fisico)",
    "sim_004.png": "Simulador de software del tapete — mismo GameCore que el ESP32 (no hardware fisico)",
}


def fuente_que_quepa(texto, ancho_max):
    for tam in range(18, 9, -1):
        f = ImageFont.truetype(FUENTE, tam)
        if f.getlength(texto) <= ancho_max:
            return f
    return ImageFont.truetype(FUENTE, 10)


def poner_banda(img, texto):
    """Devuelve una copia de la imagen con una banda inferior rotulada."""
    w, h = img.size
    banda = 34
    f = fuente_que_quepa(texto, w - 16)
    nueva = Image.new("RGB", (w, h + banda), (17, 24, 39))   # franja azul oscuro
    nueva.paste(img, (0, 0))
    d = ImageDraw.Draw(nueva)
    tw = f.getlength(texto)
    ty = h + (banda - (f.size + 2)) // 2
    d.text(((w - tw) / 2, ty), texto, fill=(255, 214, 10), font=f)   # ambar
    return nueva


def rotular(nombre, texto):
    ruta = os.path.join(CAP, nombre)
    img = Image.open(ruta).convert("RGB")
    nueva = poner_banda(img, texto)
    nueva.save(ruta)
    return nueva.size


def main():
    for nombre, texto in ROTULOS.items():
        size = rotular(nombre, texto)
        print(f"rotulada {nombre} -> {size}")
    # Regenerar el GIF a partir de los frames ya rotulados.
    gif = os.path.join(CAP, "simulador.gif")
    subprocess.run(
        ["ffmpeg", "-y", "-framerate", "2", "-i", os.path.join(CAP, "sim_%03d.png"),
         "-vf", "scale=480:-1:flags=lanczos", gif],
        check=True, capture_output=True,
    )
    print(f"GIF regenerado con frames rotulados -> {gif}")


if __name__ == "__main__":
    main()

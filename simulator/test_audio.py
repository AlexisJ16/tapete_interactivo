"""Los tonos deben sonar FUERTE, sin truncarse y sin distorsionar.

Dos invariantes cazaron bugs reales al escribirlos (2026-07-11):

- El tono de acierto suena en cada pisada correcta y en cada LED de la exhibicion de
  Memoria, y el DFPlayer CORTA la pista en curso al recibir una orden nueva. Si dura
  mas que la cadencia del motor, el nino oye un chasquido en vez de un acierto. La
  cadencia se lee de Config.h (fuente de verdad), no se copia aqui.
- El pico hay que medirlo en el MP3 DECODIFICADO, no en la onda: el codificador anade
  un overshoot que llevaba a clipping (1,018) unas ondas normalizadas a 0,95.
"""
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import gen_audio  # noqa: E402

CONFIG_H = os.path.join(RAIZ, "firmware", "lib", "GameCore", "Config.h")

SONIDO_ACIERTO = 2
LATENCIA_DFPLAYER_S = 0.05  # margen para que el comando llegue y arranque la pista


def _cadencia_minima_ms():
    """min(exhibicionOnMs) + exhibicionGapMs de Config.h: el hueco mas corto entre
    dos sonidos consecutivos que puede pedir el motor."""
    fuente = open(CONFIG_H, encoding="utf-8").read()
    bloque_on = re.search(r"exhibicionOnMs\(int nivel\) \{(.+?)\n\}", fuente, re.S).group(1)
    on_ms = min(int(n) for n in re.findall(r"return (\d+);", bloque_on))
    gap_ms = int(re.search(r"exhibicionGapMs\(int nivel\) \{[^}]*?return (\d+);",
                           fuente, re.S).group(1))
    return on_ms + gap_ms


def _mp3_decodificado(sid, destino):
    """Codifica el tono a MP3 y lo decodifica en FLOAT: revela el overshoot real."""
    wav, mp3 = os.path.join(destino, "t.wav"), os.path.join(destino, "t.mp3")
    gen_audio._escribir_wav(wav, gen_audio.SONIDOS[sid])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-ac", "1", "-ar", "44100",
                    "-b:a", "128k", mp3], check=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1",
                          "-ar", "44100", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)


def test_el_tono_de_acierto_cabe_en_la_cadencia_mas_rapida_del_motor():
    cadencia_s = _cadencia_minima_ms() / 1000.0
    dur = len(gen_audio.SONIDOS[SONIDO_ACIERTO]) / gen_audio.SR
    assert dur + LATENCIA_DFPLAYER_S < cadencia_s, (
        f"el acierto dura {dur:.3f} s y el motor puede pedir otro a los {cadencia_s:.3f} s")


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no instalado")
def test_el_mp3_no_clipea_al_decodificarse(tmp_path):
    for sid in gen_audio.SONIDOS:
        pico = float(np.max(np.abs(_mp3_decodificado(sid, str(tmp_path)))))
        assert pico <= 0.99, f"sonido {sid} clipea en el MP3 (pico {pico:.3f}): sonaria a crujido"


def test_todos_los_tonos_estan_normalizados_al_pico():
    for sid, onda in gen_audio.SONIDOS.items():
        assert abs(np.max(np.abs(onda)) - gen_audio.PICO) < 0.01, f"sonido {sid} sin normalizar"


def test_los_tonos_suenan_fuerte():
    # El RMS es el loudness percibido. Los tonos flojos de antes daban 0,34; estos dan
    # 0,57-0,62. El umbral deja margen a un back-off de PICO/COMPRESION si el tapete
    # entrara en brownout, pero NO a volver a unos tonos apagados.
    for sid, onda in gen_audio.SONIDOS.items():
        rms = float(np.sqrt(np.mean(onda ** 2)))
        assert rms > 0.50, f"sonido {sid} suena flojo (RMS {rms:.3f})"

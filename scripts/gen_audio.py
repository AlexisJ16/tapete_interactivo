"""Genera los 4 tonos del Tapete (audio/000X.mp3) de forma determinista.

numpy sintetiza ondas -> WAV temporal -> ffmpeg a MP3 mono 44.1k/128k (perfil que
el DFPlayer Mini reproduce con fiabilidad). Los mismos archivos sirven al simulador
(audio/) y a la microSD del ESP32 (/mp3/).

Mapa de sonidos (ver audio/README.md y firmware/lib/GameCore/Config.h):
  1 inicio de sesion   2 pisada correcta / exhibicion   3 pase de ronda   4 fin
"""
import os
import subprocess
import wave

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(RAIZ, "audio")
SR = 44100


def _tono(freqs, dur, vol=0.6, fade=0.01):
    """Suma de senos (acorde/nota) de duracion dur (s) con fade in/out anti-click."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    onda = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    n = max(1, int(SR * fade))
    env = np.ones_like(onda)
    env[:n] = np.linspace(0, 1, n)
    env[-n:] = np.linspace(1, 0, n)
    return onda * env * vol


def _secuencia(notas):
    """notas = [(freqs, dur), ...] concatenadas."""
    return np.concatenate([_tono(f, d) for f, d in notas])


# Escala alegre (Do mayor) para sonidos amables.
DO, MI, SOL, DO2, SOL2 = 523.25, 659.25, 783.99, 1046.5, 1568.0

SONIDOS = {
    1: _secuencia([([DO], .12), ([MI], .12), ([SOL], .12), ([DO2], .18)]),                  # inicio: arpegio asc.
    2: _tono([SOL2], .12),                                                                   # acierto: tono corto claro
    3: _secuencia([([MI], .10), ([SOL], .10), ([DO2], .22)]),                                # ronda: pequeno logro
    4: _secuencia([([DO2], .14), ([SOL], .14), ([DO2], .14), ([MI, SOL, DO2], .35)]),        # fin: fanfarria
}


def _escribir_wav(path, onda):
    data = (np.clip(onda, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    os.makedirs(AUDIO, exist_ok=True)
    for sid, onda in SONIDOS.items():
        wav = os.path.join(AUDIO, f"{sid:04d}.wav")
        mp3 = os.path.join(AUDIO, f"{sid:04d}.mp3")
        _escribir_wav(wav, onda)
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-ac", "1", "-ar", "44100",
                        "-b:a", "128k", mp3], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(wav)
        print(f"audio/{sid:04d}.mp3 ({os.path.getsize(mp3)} bytes)")


if __name__ == "__main__":
    main()

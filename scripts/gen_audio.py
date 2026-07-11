"""Genera los 4 tonos del Tapete (audio/000X.mp3) de forma determinista.

numpy sintetiza ondas -> WAV temporal -> ffmpeg a MP3 mono 44.1k/128k (perfil que
el DFPlayer Mini reproduce con fiabilidad). Los mismos archivos sirven al simulador
(audio/) y a la microSD del ESP32 (/mp3/).

Los tonos se generan lo mas FUERTES y NITIDOS posible, porque el volumen del modulo
ya topa: a VOLUMEN_AUDIO=30 el parlante de 4 Ohm sobre USB provoca brownout y el
DFPlayer deja de sonar (Config.h). De las palancas de este guion, la unica gratis en
corriente es la FRECUENCIA (2-4 kHz = pico de sensibilidad del oido y mejor
rendimiento de un altavoz pequeno); subir PICO y COMPRESION si pide mas potencia (de
pico y media). Si en el tapete reaparecen cortes o mudez, es brownout: bajar PICO y
COMPRESION y regenerar, conservando la frecuencia. Diseno:
docs/superpowers/specs/2026-07-11-normalizacion-audio-design.md

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

PICO = 0.86            # normalizacion final. Deja margen al overshoot del codificador MP3:
                       # MEDIDO (2026-07-11), a 0,95 el MP3 decodificado llega a 1,018 y el
                       # DFPlayer lo oye como crujido. El overshoot NO es monotono (a 0,92
                       # dispara a 1,107), asi que el margen se fija por medicion, no por
                       # teoria: a 0,86 los cuatro decodifican <= 0,945. Cuesta 0,9 dB.
COMPRESION = 2.5       # k del waveshaper tanh: sube el RMS (loudness) sin subir el pico.
SILENCIO_INICIAL = 0.03  # s. El DFPlayer se come el ataque de la pista.
ARMONICOS = (1.0, 0.5, 0.25)  # pesos de f, 2f, 3f: dan el brillo de campanita.

# Do mayor DOS OCTAVAS por encima del original: zona de maxima sensibilidad del oido
# (~2-4 kHz), donde el mismo vatio suena mucho mas fuerte. El 3er armonico del mas
# agudo (4186*3 = 12,6 kHz) sigue por debajo de Nyquist (22,05 kHz): no hay aliasing.
DO, MI, SOL, DO2 = 2093.0, 2637.0, 3136.0, 4186.0


def _nota(freqs, dur, fade_in=0.005, fade_out=0.02):
    """Suma de notas (acorde), cada una con sus armonicos. Envolvente casi plana:
    maximiza la energia (un decay de campana sonaria bonito pero bajaria el loudness,
    que es justo lo que se persigue)."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    onda = sum(peso * np.sin(2 * np.pi * (f * k) * t)
               for f in freqs
               for k, peso in enumerate(ARMONICOS, start=1)) / len(freqs)
    env = np.ones_like(onda)
    n_in, n_out = max(1, int(SR * fade_in)), max(1, int(SR * fade_out))
    env[:n_in] = np.linspace(0, 1, n_in)
    env[-n_out:] = np.linspace(1, 0, n_out)
    return onda * env


def _acabado(onda):
    """Comprime (sube el RMS sin subir el pico), normaliza a PICO y antepone el silencio."""
    onda = onda / np.max(np.abs(onda))
    onda = np.tanh(COMPRESION * onda) / np.tanh(COMPRESION)
    onda = onda / np.max(np.abs(onda)) * PICO
    return np.concatenate([np.zeros(int(SR * SILENCIO_INICIAL)), onda])


def _secuencia(notas):
    """notas = [(freqs, dur), ...] concatenadas, con el acabado comun."""
    return _acabado(np.concatenate([_nota(f, d) for f, d in notas]))


# Duraciones: el ACIERTO es el unico que se repite en cadencia rapida (cada pisada
# correcta y cada LED de la exhibicion de Memoria, que en nivel 4 van cada 550 ms) y
# el DFPlayer corta la pista en curso al recibir otra orden -> se queda corto a
# proposito, para no truncarse nunca. Su fuerza viene de la frecuencia y los armonicos.
SONIDOS = {
    1: _secuencia([([DO], .13), ([MI], .13), ([SOL], .13), ([DO2], .21)]),               # inicio: arpegio asc.
    2: _secuencia([([SOL], .22)]),                                                        # acierto: campanada corta
    3: _secuencia([([MI], .12), ([SOL], .12), ([DO2], .26)]),                             # ronda: pequeno logro
    4: _secuencia([([DO2], .16), ([SOL], .16), ([DO2], .16), ([MI, SOL, DO2], .42)]),     # fin: fanfarria
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
        rms = float(np.sqrt(np.mean(onda ** 2)))
        print(f"audio/{sid:04d}.mp3  {len(onda)/SR:.3f} s  pico {np.max(np.abs(onda)):.2f}  "
              f"RMS {rms:.3f} ({20*np.log10(rms):+.1f} dBFS)  {os.path.getsize(mp3)} bytes")


if __name__ == "__main__":
    main()

# Audios del DFPlayer Mini

Los pide el firmware/simulador por `id` (evento `{"ev":"sound","id":N}`).

- **ESP32 (microSD FAT32):** crea una carpeta `/mp3` en la raíz de la SD y pon
  los archivos ahí: `/mp3/0001.mp3` … `/mp3/0004.mp3`. El firmware usa
  `playMp3Folder(id)`, que los reproduce **por número** de forma fiable (no
  depende del orden de copiado, a diferencia de `play()`).
- **Simulador:** los archivos van en esta misma carpeta `audio/` (`0001.mp3`…).

| Archivo | id | Cuándo suena |
|---|---|---|
| `0001.mp3` | 1 | Inicio de sesión (Start) |
| `0002.mp3` | 2 | Pisada correcta / cada LED de la exhibición (Memoria) |
| `0003.mp3` | 3 | Serie/patrón completado (pase de ronda) |
| `0004.mp3` | 4 | Fin de la sesión |

La pisada incorrecta **no** lleva sonido.

Notas:

- Se generan con `scripts/gen_audio.py` (numpy → ffmpeg): MP3 mono 44,1 kHz /
  128 kbps, perfil que el DFPlayer Mini reproduce con fiabilidad. Regenerarlos:
  `.venv/bin/python scripts/gen_audio.py`.
- Numéralos con 4 dígitos (`0001.mp3`, `0002.mp3`, …).
- En el **simulador**, si faltan los archivos no pasa nada: simplemente no
  reproduce sonido (no falla).

# Audios del DFPlayer Mini

Coloca estos archivos MP3 en la **raíz** de la microSD (FAT32) del DFPlayer.
El firmware/simulador los pide por `id` (evento `{"ev":"sound","id":N}`):

| Archivo | id | Cuándo suena |
|---|---|---|
| `0001.mp3` | 1 | Instrucción / muestra de secuencia / inicio de ronda |
| `0002.mp3` | 2 | **Acierto** (tono ascendente alegre) |
| `0003.mp3` | 3 | **Error** (tono grave) |
| `0004.mp3` | 4 | **Éxito** (secuencia/sesión completada) |

Notas:

- Numéralos con 4 dígitos (`0001.mp3`, `0002.mp3`, …). El DFPlayer reproduce por
  índice de pista (`play(id)`).
- En el **simulador**, los archivos van en esta misma carpeta `audio/`. Si faltan,
  el simulador no falla: simplemente no reproduce sonido.
- Sonidos sugeridos: cortos (0,3–1 s), claros y amables para niños.

# Audios del DFPlayer Mini

Los pide el firmware/simulador por `id` (evento `{"ev":"sound","id":N}`).

- **ESP32 (microSD FAT32):** crea una carpeta `/mp3` en la raíz de la SD y pon
  los archivos ahí: `/mp3/0001.mp3` … `/mp3/0004.mp3`. El firmware usa
  `playMp3Folder(id)`, que los reproduce **por número** de forma fiable (no
  depende del orden de copiado, a diferencia de `play()`).
- **Simulador:** los archivos van en esta misma carpeta `audio/` (`0001.mp3`…).

| Archivo | id | Cuándo suena |
|---|---|---|
| `0001.mp3` | 1 | Instrucción / muestra de secuencia / inicio de ronda |
| `0002.mp3` | 2 | **Acierto** (tono ascendente alegre) |
| `0003.mp3` | 3 | **Error** (tono grave) |
| `0004.mp3` | 4 | **Éxito** (secuencia/sesión completada) |

Notas:

- Numéralos con 4 dígitos (`0001.mp3`, `0002.mp3`, …).
- En el **simulador**, si faltan los archivos no pasa nada: simplemente no
  reproduce sonido (no falla).
- Sonidos sugeridos: cortos (0,3–1 s), claros y amables para niños.

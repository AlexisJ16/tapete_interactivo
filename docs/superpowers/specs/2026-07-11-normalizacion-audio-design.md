# Normalización de los tonos del Tapete — diseño (2026-07-11)

Los 4 tonos suenan **débiles** en el hardware. El volumen del módulo ya topa: `VOLUMEN_AUDIO
= 15` es el techo verificado (a 30 el parlante de 4 Ω sobre USB provoca brownout y el
DFPlayer deja de sonar). La ganancia hay que buscarla, entonces, **en el archivo**:
`scripts/gen_audio.py`.

## Qué es gratis y qué cuesta corriente

La premisa del ROADMAP ("subir el archivo en vez del volumen, sin pedir más corriente") es
**solo medio cierta**, y de ahí sale el riesgo del trabajo:

| Palanca | Efecto | Coste eléctrico |
|---|---|---|
| Frecuencia a 2–4 kHz | mucho más volumen percibido (pico de sensibilidad del oído + mejor rendimiento del altavoz pequeño) | **ninguno** — la única palanca gratis |
| Armónicos (2f, 3f) | brillo y nitidez; timbre de campanita | despreciable (redistribuye energía) |
| Pico 0,6 → 0,95 | +4 dB de pico | **sí**: ~1,6× de tensión ≈ 2,5× de potencia de pico |
| Compresión (sube el RMS) | más *loudness* percibido | **sí**: sube la potencia **media** |

Los condensadores de desacople amortiguan **picos transitorios**; no sostienen un consumo
**medio** mayor. Un archivo más caliente a volumen 15 puede reproducir el mismo brownout que
causó el volumen 30. Por eso el criterio de éxito **no** es "suena más fuerte en el PC", sino
**"suena más fuerte en el tapete y sigue sonando, sin cortes ni mudez"**.

## Síntesis

- **Timbre:** cada nota = fundamental + armónicos 2f y 3f (pesos 1 / 0,5 / 0,25) → campanita
  de juguete, brillante. Se conserva la escala (Do mayor) y las 4 melodías, para que los
  avisos sigan distinguiéndose entre sí (el niño debe saber si acertó o si pasó de ronda) y
  no suenen a alarma.
- **Transposición dos octavas** al rango óptimo: DO 2093, MI 2637, SOL 3136, DO2 4186 Hz.
- **Compresión suave** (waveshaper `tanh`): sube el RMS sin subir el pico.
- **Pico normalizado a 0,86** (medido, ver abajo), no a 1,0: deja margen al *overshoot* que
  introduce el codificador MP3.
- **Envolvente casi plana** (fade in 5 ms, fade out 20 ms): maximiza la energía. Un decay de
  campana sonaría bonito pero bajaría el *loudness*, que es justo lo que se persigue.
- **Silencio inicial de 30 ms** para que el DFPlayer no se coma el ataque.
- Salida igual que hoy: MP3 mono 44,1 kHz / 128 kbps (perfil fiable del módulo).

## El pico se fija midiendo el MP3, no la onda (hallazgo)

El diseño partía de normalizar a 0,95. **Medido sobre el MP3 decodificado, no vale:** el
codificador añade *overshoot* y tres de los cuatro tonos llegaban a **1,005–1,018**, que el
DFPlayer oiría como crujido. Y el *overshoot* **no es monótono** — a un pico de 0,92 se
dispara a **1,107**, peor que a 0,95 —, así que el margen no se puede deducir: hay que
medirlo. Barrido:

| Pico de la onda | Pico del MP3 decodificado | |
|---|---|---|
| 0,95 | 0,973 – 1,018 | clipea |
| 0,92 | 0,946 – 1,107 | clipea |
| **0,86** | **0,910 – 0,945** | **sin clipping, con holgura** |

`PICO = 0,86`. Cuesta 0,9 dB frente a 0,95, irrelevante junto a los +3–4 dB de RMS y a la
ganancia de frecuencia. **Corolario para el test: el clipping se comprueba en el MP3
decodificado**, nunca en la onda en memoria — ahí es invisible.

## Duraciones — restricción de cadencia (hallazgo)

El ROADMAP pedía "alargar los tonos a ~0,5 s". **Para el tono de acierto eso es un error** y
no se hace: el acierto (id 2) suena en **cada** pisada correcta y en **cada** LED de la
exhibición de Memoria. La cadencia más rápida que fija `Config.h` es la exhibición en nivel 4
(`exhibicionOnMs`=300 + `exhibicionGapMs`=250 = **550 ms**), y en Velocidad un niño puede
encadenar dos aciertos en menos de medio segundo. El DFPlayer **corta la pista en curso** al
recibir una nueva orden, así que un tono de 0,5 s se truncaría y se oiría como un chasquido.

| id | Tono | Duración | Por qué |
|---|---|---|---|
| 1 | inicio | ~0,60 s | no se repite |
| 2 | **acierto** | **0,22 s** | **debe caber en la cadencia de 550 ms** |
| 3 | ronda | ~0,50 s | no se repite |
| 4 | fin | ~0,90 s | no se repite |

El acierto gana audibilidad por **frecuencia, pico y armónicos**, no por duración.

## Test — `simulator/test_audio.py`

Sigue el precedente de `test_spice.py` / `test_experimentos_figuras.py` (tests de los
generadores de `scripts/`). Cuatro aserciones, cada una protege una decisión:

1. **La duración del acierto queda por debajo de la cadencia mínima de `Config.h`** —
   el invariante que impide el truncado. Lee los 550 ms del propio `Config.h`, no una
   constante copiada, para que un cambio de `exhibicionOnMs`/`GapMs` rompa el test.
2. **El MP3 decodificado no clipea** (pico ≤ 0,99) — el invariante que impide el crujido.
   Codifica y decodifica de verdad con ffmpeg: en la onda en memoria este fallo no se ve.
3. **Pico normalizado** a `PICO` (± tolerancia).
4. **RMS por encima de un mínimo** — que la compresión efectivamente subió el *loudness*.

## Validación

1. Métricas antes/después (pico, RMS, dBFS, duración) — evidencia, no impresión.
2. Escucha en el PC: juicio del **carácter** (que no suene a alarma).
3. **El tapete es el juez real** (el autor copia los MP3 a la microSD y prueba). Criterio:
   suena más fuerte **y** sin cortes ni silencios en una sesión completa de cada modo.

**Si aparecen cortes o mudez → es brownout.** Remedio, por este orden: bajar `PICO` y
`COMPRESION` en `gen_audio.py` y regenerar (**se conserva la ganancia de frecuencia, que es
la gratis**); no hace falta reflashear, los tonos viven en la SD. Si hubiera duda, el entorno
`esp32dev_audio` da el veredicto objetivo: **0 reinicios del módulo**.

## Fuera de alcance

- **No se toca el firmware ni `Config.h`** (ni `VOLUMEN_AUDIO` ni los tiempos de juego, ya
  validados en hardware) → **no hay que reflashear**.
- **No se toca la microSD:** los archivos se dejan en `audio/`; el autor los copia.
- La suite no cambia: golden vectors y tests de GameCore dependen del **id** del evento
  `sound`, nunca de la forma de onda.

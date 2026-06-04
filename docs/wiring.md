# Cableado y montaje en protoboard

Tapete de **6 botones** en disposición 2 filas × 3 columnas:

```
[1] [2] [3]
[4] [5] [6]
```

Cada botón = **1 sensor FSR** (pisada) + **3 LEDs blancos** en grupo (un solo
pin PWM por grupo). **Los LEDs son BLANCOS, no RGB**: no hay color; la
retroalimentación es por **patrón de parpadeo + sonido**.

## 1. Mapa de pines (coincide con `firmware/lib/GameCore/Config.h`)

| Señal | Pin ESP32 | Notas |
|---|---|---|
| FSR 1 | GPIO 36 (VP) | ADC1, solo entrada |
| FSR 2 | GPIO 39 (VN) | ADC1, solo entrada |
| FSR 3 | GPIO 34 | ADC1, solo entrada |
| FSR 4 | GPIO 35 | ADC1, solo entrada |
| FSR 5 | GPIO 32 | ADC1 (pull interno disponible) |
| FSR 6 | GPIO 33 | ADC1 (pull interno disponible) |
| LED grupo 1 | GPIO 4 | salida, canal LEDC (PWM) |
| LED grupo 2 | GPIO 5 | salida, canal LEDC (PWM) |
| LED grupo 3 | GPIO 18 | salida, canal LEDC (PWM) |
| LED grupo 4 | GPIO 19 | salida, canal LEDC (PWM) |
| LED grupo 5 | GPIO 21 | salida, canal LEDC (PWM) |
| LED grupo 6 | GPIO 23 | salida, canal LEDC (PWM) |
| DFPlayer RX (módulo) | GPIO 17 (TX2) | TX del ESP32 → RX DFPlayer (1 kΩ en serie recomendado) |
| DFPlayer TX (módulo) | GPIO 16 (RX2) | RX del ESP32 ← TX DFPlayer |

> Se usa **ADC1** para todos los FSR porque **ADC2 entra en conflicto con el
> WiFi** en el ESP32. Los GPIO 34–39 son **solo entrada** (perfectos para sensores).

## 2. Sensores FSR — divisor de voltaje (CRÍTICO)

Cada FSR forma un **divisor de voltaje** con una resistencia **pull-down de
~10 kΩ** que se lee con el ADC:

```
3V3 ──[ FSR ]──┬── GPIO (entrada ADC1)
               │
            [ 10 kΩ ]
               │
              GND
```

- **Importante:** las resistencias de **110 Ω son para los LEDs**, NO para los
  FSR. Con 110 Ω el rango de lectura del FSR queda muy comprimido y la detección
  es poco fiable.
- **Acción para la fase física:** conseguir **6 resistencias de 10 kΩ** (una por
  FSR; son muy económicas). Como respaldo, los **GPIO 32 y 33** tienen pull-down
  interno (~45 kΩ) utilizable para 2 sensores, pero lo correcto es la resistencia
  externa de 10 kΩ.
- El firmware define un **umbral de pisada** calibrable: `cfg::UMBRAL_PISADA`
  (lectura ADC 0..4095) en `Config.h`. Ajústalo observando los valores que
  imprime el Serial al pisar.

## 3. LEDs blancos — brillo pleno (recomendado)

El voltaje directo de un LED blanco (~3,0–3,4 V) está muy cerca de los 3,3 V del
GPIO, así que **encenderlos directo desde el pin a 3,3 V dará poco brillo**.

- **Para empezar / probar:** se puede encender tenue directo desde el GPIO con su
  resistencia de **110 Ω** en serie por LED.
- **Para brillo pleno (dispositivo final):** alimentar los LEDs desde **5 V** y
  conmutar cada grupo con un transistor (p. ej. **2N2222**) o un único
  **ULN2803** (8 canales) controlado por los GPIO PWM. El GPIO controla la base/
  entrada; la corriente de los LEDs viene de 5 V, no del pin.

```
5V ──[ 110Ω ]──[ LED ]──┐
5V ──[ 110Ω ]──[ LED ]──┤ (3 LEDs del grupo en paralelo)
5V ──[ 110Ω ]──[ LED ]──┘
                         └── Colector/salida del transistor (o ULN2803)
GPIO PWM ──[ 1kΩ ]── Base (2N2222)   |  o directo a la entrada del ULN2803
                         Emisor ── GND  (GND común con el ESP32)
```

Cada **grupo de 3 LEDs** se controla con **un solo pin PWM** (encienden/atenúan
juntos). El brillo lo fija el firmware vía LEDC (0..255).

## 4. DFPlayer Mini + parlante

- Alimentación: **5 V** y GND.
- `RX` del DFPlayer ← **GPIO 17 (TX2)** del ESP32, con **1 kΩ en serie**
  recomendada (protege la entrada del módulo).
- `TX` del DFPlayer → **GPIO 16 (RX2)** del ESP32.
- Parlante a `SPK_1`/`SPK_2` (3 W) o salida `DAC` a un amplificador.
- **microSD** (FAT32) con los audios en la carpeta `/mp3/`: `/mp3/0001.mp3` …
  `/mp3/0004.mp3` (ver `audio/README.md`).

## 5. Alimentación

- **Desarrollo:** basta con alimentar el ESP32 por **USB-C**.
- **GND común:** todos los GND (ESP32, LEDs/5 V, DFPlayer) deben ir juntos.
- **Dispositivo portátil final:** añadir batería de litio + cargador
  (no incluido en esta compra).

## 6. Lista de verificación antes de energizar

- [ ] FSR con su pull-down de 10 kΩ a GND (no 110 Ω).
- [ ] LEDs con 110 Ω en serie; si van a 5 V, transistor/ULN2803 por grupo.
- [ ] DFPlayer: TX/RX cruzados (17→RX, 16←TX) y 1 kΩ en la línea a su RX.
- [ ] GND común entre ESP32, etapa de LEDs y DFPlayer.
- [ ] microSD FAT32 con `/mp3/0001.mp3`..`/mp3/0004.mp3`.
- [ ] Nada conectado a ADC2/ pines de WiFi.

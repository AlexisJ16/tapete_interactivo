# Cableado y armado del protoboard — Tapete Interactivo

> **Fuente única de verdad del armado** (reemplaza al antiguo
> `mapa_armado_protoboard.xlsx`). Geometría del protoboard **validada con el autor
> (2026-06-29) y bloqueada**: no re-inventar. El diseño conceptual (decisiones,
> arquitectura de potencia, mecánica del botón, caja) vive en
> `00_diseno_circuito.md`; los materiales, en `materiales.md`.

Tapete de **6 botones** (2 filas × 3 columnas):

```
[1] [2] [3]
[4] [5] [6]
```

Cada botón = **1 FSR** (pisada) + **3 LEDs blancos** en paralelo (un pin PWM por
grupo). Los LEDs son **blancos** (no RGB): el feedback es patrón de parpadeo + sonido.

## 1. Geometría del protoboard (bloqueada)

- Protoboard de **830 puntos**. Filas **A–E / canal central / F–J**. Columnas
  **1–64**. Rieles `+/−` arriba y abajo.
- **ESP32 (30 pines):** el cuerpo cubre **columnas 22–41, filas B–J**. La **Fila A
  es la única libre** de esa franja (expone el header superior). Los pines quedan en
  **columnas 25–39** (15 por lado).
- **USB-C:** columna **21** (filas F–G).
- **Zonas libres para componentes:** **columnas 1–21** (izquierda) y **42–64**
  (derecha).

### Mapa de pines del ESP32

**Header superior — Fila A (accesible directo, arriba):**

| Col | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **VIN** | GND | D13 | D12 | D14 | D27 | D26 | D25 | D33 | D32 | D35 | D34 | **VN** | **VP** | EN |
| Uso | **5 V** | GND | — | — | — | — | — | — | FSR6 | FSR5 | FSR4 | FSR3 | FSR2 | FSR1 | — |

> ⚠️ **El doble "VN":** el de la **col 25** (esquina) es **VIN = 5 V (potencia)**;
> el de la **col 37** (junto a VP/EN) es **GPIO39 = FSR2 (entrada ADC)**.
> Confundirlos mete 5 V a un ADC.

**Header inferior — Fila J (contra el borde inferior):**

| Col | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **3V3** | GND | D15 | D2 | **D4** | **RX2** | **TX2** | **D5** | **D18** | **D19** | **D21** | RX0 | TX0 | D22 | **D23** |
| Uso | 3V3 | GND | — | — | LED1 | DF-TX→ | DF←RX | LED2 | LED3 | LED4 | LED5 | — | — | — | LED6 |

`RX2 = GPIO16`, `TX2 = GPIO17`. Convención DFPlayer: ESP32 **TX2(17) → RX** del
módulo; ESP32 **RX2(16) ← TX** del módulo.

**Mapa lógico (coincide con `firmware/lib/GameCore/Config.h`):**

| Señal | GPIO | Col (Fila) |
|---|---|---|
| FSR1 | 36 (VP) | 38 (A) |
| FSR2 | 39 (VN) | 37 (A) |
| FSR3 | 34 | 36 (A) |
| FSR4 | 35 | 35 (A) |
| FSR5 | 32 | 34 (A) |
| FSR6 | 33 | 33 (A) |
| LED1 | 4 | 29 (J) |
| LED2 | 5 | 32 (J) |
| LED3 | 18 | 33 (J) |
| LED4 | 19 | 34 (J) |
| LED5 | 21 | 35 (J) |
| LED6 | 23 | 39 (J) |
| DFPlayer RX2 (←TX) | 16 | 30 (J) |
| DFPlayer TX2 (→RX) | 17 | 31 (J) |

> Se usa **ADC1** para todos los FSR (ADC2 choca con el WiFi). Los GPIO 34–39 son
> **solo entrada** (perfectos para sensores).

## 2. Ruteo de la Fila J (detalle crítico del montaje)

Los pines del **header inferior están en la Fila J**, y las filas **F–I de esas
columnas quedan tapadas por el cuerpo del ESP32** → no hay huecos accesibles
justo debajo para conectar componentes.

**Solución:** desde cada pin del header inferior se **sacan puentes/cables hacia
las zonas laterales libres** (columnas **1–21** y **42–64**) y ahí se hacen las
conexiones de forma limpia. En concreto: **LEDs, ULN2803A y DFPlayer se montan en
la zona inferior-derecha (cols 42–64)**; los GPIO de LED (Fila J, cols 29–39) y las
líneas del DFPlayer (Fila J, cols 30–31) llegan a esa zona por puentes laterales.
El header superior (Fila A) no tiene este problema: se conecta directo hacia arriba.

## 3. Arquitectura de potencia — 4 rieles (seguridad anti-corto)

| Riel | Bus | Se alimenta desde |
|---|---|---|
| Superior `−` | **GND** | ESP32 GND (Fila A, col 26) |
| Superior `+` | **3V3** | ESP32 3V3 (Fila J, col 25) → 1 puente cruza al riel superior |
| Inferior `+` | **5 V** | ESP32 VIN (Fila A, col 25) → 1 puente cruza al riel inferior |
| Inferior `−` | **GND** | ESP32 GND (Fila J, col 26) |

**Reglas invariables:**
- Se **puentean los dos rieles `−`** (GND común): 1 jumper en un extremo.
- **NUNCA** se puentean los dos `+` (uno es 3V3, otro 5V → cortocircuito).
- El **mundo 3V3 vive arriba** (sensores); el **mundo 5V abajo** (LEDs/audio). El
  canal central los separa: esa es la frontera que evita el corto.
- Muchos protoboards traen los rieles **partidos a la mitad** → verifica
  continuidad de cada riel de extremo a extremo y puentea si hace falta.

## 4. Net list por subsistema

### 4.1 Energía

| # | Desde | Hasta | Nota |
|---|---|---|---|
| P1 | ESP32 3V3 (J, c25) | Riel **superior +** | bus 3V3 |
| P2 | ESP32 VIN (A, c25) | Riel **inferior +** | bus 5V |
| P3 | ESP32 GND (A, c26) | Riel **superior −** | GND |
| P4 | ESP32 GND (J, c26) | Riel **inferior −** | GND |
| P5 | Riel **superior −** | Riel **inferior −** | puente GND común |

Alimentación: **solo el PC al ESP32 por cable USB** (5 V). Sin power bank ni red.

### 4.2 Sensores FSR (mitad superior-izquierda, cols 1–21)

Topología por canal: `3V3 ─[FSR]─┬─ ADC ; nodo ─[10 kΩ]─ GND`. El **nodo** vive en
una columna libre de la zona superior-izquierda.

| Canal | ADC (Fila A) | 10 kΩ | FSR | 
|---|---|---|---|
| FSR1 | VP/GPIO36 (c38) | nodo → GND | 3V3 → FSR → nodo → ADC |
| FSR2 | VN/GPIO39 (c37) | nodo → GND | idem |
| FSR3 | D34/GPIO34 (c36) | nodo → GND | idem |
| FSR4 | D35/GPIO35 (c35) | nodo → GND | idem |
| FSR5 | D32/GPIO32 (c34) | nodo → GND | idem |
| FSR6 | D33/GPIO33 (c33) | nodo → GND | idem |

Por canal: 1 jumper nodo→ADC, 1 resistencia 10 kΩ nodo→GND, el hilo **FSR_alto**
del tapete a 3V3 y el **FSR_bajo** al nodo. **Trenza cada par de hilos FSR** (alto
+ bajo) para inmunizar el ruido a ~25–30 cm.

### 4.3 LEDs vía ULN2803A (mitad inferior-derecha, cols 42–64)

Por grupo (3 LEDs en paralelo): `5V ─[1 kΩ]─ ánodo` y `cátodo ─ OUTk del ULN`. La
entrada `INk` llega del GPIO de LED (Fila J) por puente lateral.

| Grupo | GPIO (Fila J) | Entrada ULN | R serie | Salida ULN |
|---|---|---|---|---|
| LED1 | D4 (c29) | IN1 (pin 1) | 5V→[1 kΩ]→ánodo | OUT1 (pin 18) |
| LED2 | D5 (c32) | IN2 (pin 2) | idem | OUT2 (pin 17) |
| LED3 | D18 (c33) | IN3 (pin 3) | idem | OUT3 (pin 16) |
| LED4 | D19 (c34) | IN4 (pin 4) | idem | OUT4 (pin 15) |
| LED5 | D21 (c35) | IN5 (pin 5) | idem | OUT5 (pin 14) |
| LED6 | D23 (c39) | IN6 (pin 6) | idem | OUT6 (pin 13) |

ULN2803A: **pin 9 = GND** (riel inf −), **pin 10 = COM** (riel inf +, 5 V). Muesca
hacia el pin 1.

> **Brillo esperado = tenue pero visible.** Con 1 kΩ desde 5 V vía el ULN, cada LED
> recibe ~0.9 mA (no hay resistencias de valor bajo para más corriente; ver
> `materiales.md` §3). Es lo máximo alcanzable con el inventario. Los LEDs van
> **directo en la superficie** (huecos en el acrílico), sin difusor, así que a esa
> corriente se ven.
>
> ⚠️ **GPIO5 (LED2) es strapping pin.** Si tras cablear LED2 el ESP32 no arranca,
> reasigna **LED2 → GPIO22** (D22, col 38, libre y no strapping): una línea en
> `Config.h` (`PIN_LED`) y mover un cable.

### 4.4 DFPlayer Mini + parlante (mitad inferior-izquierda/derecha, cols 42–64)

| Pin módulo | Conexión |
|---|---|
| VCC | riel **inferior +** (5 V) |
| GND | riel **inferior −** |
| RX | ← **1 kΩ** en serie ← ESP32 **TX2/GPIO17** (J, c31) por puente lateral |
| TX | → ESP32 **RX2/GPIO16** (J, c30) por puente lateral |
| SPK1 / SPK2 | **parlante 4 Ω** (par diferencial, **NO aterrizar** ninguno) |

microSD FAT32 con `/mp3/0001.mp3` … `/mp3/0004.mp3` (ver `audio/README.md`).

> ⚠️ **Protege el ESP32 — línea DFPlayer TX → GPIO16.** GPIO16 **no es
> 5V-tolerante**. Antes de conectar, **mide el nivel alto del TX del módulo**: si
> ~3.3 V → directo; si ~5 V → intercala un divisor con **1 kΩ + 2 kΩ**.
>
> **Desacople del audio:** con el parlante activo el amplificador tira picos → pon
> un electrolítico (1000 µF y/o 100 µF) entre VCC y GND del DFPlayer + un 100 nF
> cerámico. Mantén el **volumen moderado** (parlante de 4 Ω sobre puerto USB del PC).

## 5. Leyenda de señales (colores sugeridos para el montaje)

| Color | Señal |
|---|---|
| Negro | GND |
| Naranja | 3V3 |
| Rojo | 5 V |
| Azul | señal FSR (nodo → ADC) |
| Verde | GPIO → IN del ULN |
| Violeta | OUT del ULN → cátodo del grupo LED |
| Marrón | línea UART del DFPlayer |

## 6. Checklist con multímetro (ANTES de energizar cada vez)

- [ ] Rieles `−` con continuidad entre sí y con GND del ESP32.
- [ ] Riel 3V3 y riel 5V **sin** continuidad entre ellos ni con GND.
- [ ] Cada riel continuo de extremo a extremo (puentear si está partido).
- [ ] Ningún FSR a 5 V (solo a 3V3); ningún ADC a 5 V (¡el doble "VN": c25 vs c37!).
- [ ] ULN: pin 9 a GND, pin 10 a 5 V, muesca correcta.
- [ ] LEDs: polaridad (ánodo a 1 kΩ/5 V, cátodo a OUT del ULN).
- [ ] Nada en ADC2 / pines de WiFi. GPIO12 libre (no cablear).
- [ ] **DFPlayer TX medido ≤ 3.3 V** antes de conectarlo a GPIO16 (si 5 V → divisor).
- [ ] Tras cablear LED2, el ESP32 **arranca** (GPIO5 strapping; si no, LED2→GPIO22).
- [ ] microSD FAT32 con `/mp3/0001.mp3`…`/mp3/0004.mp3`.

## 7. Secuencia de armado (orden seguro)

1. **Rieles primero.** Montar P1–P5 y verificar con el multímetro (checklist §6).
2. **Energizar en vacío** (solo ESP32): medir **VIN→GND ≈ 5 V** y **3V3→GND ≈ 3.3 V**;
   confirmar que arranca (Serial 115200).
3. **FSR uno por uno.** Montar el divisor; ver en el Serial la lectura ADC en reposo
   y al pisar. Ajustar `cfg::UMBRAL_PISADA`. Repetir los 6.
4. **ULN + LEDs por grupo.** Montar el ULN (pin 9→GND, pin 10→5 V). Un grupo:
   1 kΩ, ánodo, cátodo→OUT, IN←GPIO por puente lateral. Probar encendido (brillo
   tenue esperado). *(GPIO5 strapping: confirmar que el ESP32 sigue arrancando tras LED2.)*
5. **DFPlayer + parlante.** VCC/GND, TX2→(1 kΩ)→RX, RX2←TX, microSD, SPK a parlante.
   Verificar `audioOk`. Volumen moderado.
6. **Tapa.** Módulos bajo-tapa, rutear arneses, pegar el gráfico.

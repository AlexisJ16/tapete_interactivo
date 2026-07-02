# Cableado y armado del protoboard — Tapete Interactivo

> **Fuente única de verdad del armado.** Geometría del protoboard **validada con el
> autor (2026-06-29) y bloqueada**: no re-inventar. Aquí está **todo lo necesario
> para montar el circuito de una sola vez**: el plano hueco por hueco, el net list
> con columnas exactas, la leyenda de colores, el checklist con multímetro y la
> secuencia de armado. El diseño conceptual (decisiones, mecánica del botón, caja)
> vive en `00_diseno_circuito.md`; los materiales, en `materiales.md`; el mapa de
> pines canónico, en `firmware/lib/GameCore/Config.h`.

Tapete de **6 botones** (2 filas × 3 columnas):

```
[1] [2] [3]
[4] [5] [6]
```

Cada botón = **1 FSR** (pisada) + **3 LEDs blancos en paralelo** (un pin PWM por
grupo). Los LEDs son **blancos** (no RGB): el feedback es patrón de parpadeo + sonido.
Los 18 LEDs y los 6 FSR viven **en la tapa**; al protoboard llegan solo **4 hilos por
botón** (FSR_alto, FSR_bajo, LED_ánodo común, LED_cátodo común) — ver §6 y
`00_diseno_circuito.md §4`.

---

## 1. Geometría del protoboard (bloqueada)

> **Cómo funciona un protoboard (regla base — léela primero).** Los **5 huecos de una
> misma columna en la mitad superior** (A, B, C, D, E) están **unidos por dentro = 1 solo
> nodo eléctrico**; lo mismo los 5 de la mitad inferior (F, G, H, I, J) = **otro** nodo. El
> **canal central separa** las dos mitades (A–E y F–J de la misma columna **no** se tocan,
> salvo por un componente que cruce el canal). Los **rieles `+` y `−` corren horizontales**
> a lo largo de todo el borde (toda la línea es el mismo nodo). Por eso, cuando el doc dice
> *"conecta en la col 20"*, da igual en cuál de A20/B20/C20/D20/E20 pinches: es el mismo
> nodo. Una **resistencia o un LED** ocupa **dos** nodos (una pata en cada columna); un
> **jumper** copia un nodo a otro.

- Protoboard de **830 puntos**. Filas **A–E** (mitad superior) / **canal central** /
  **F–J** (mitad inferior). Columnas **1–64**. Rieles `+/−` arriba y abajo.
- **ESP32 (DevKit 30 pines):** el módulo se monta **a caballo del canal central**,
  cubriendo **columnas 22–41**, y está **corrido hacia el borde inferior**: sus **pines
  inferiores ocupan la Fila J** (la última fila — debajo solo están los rieles) y por
  arriba **deja libre la Fila A**. Los pines están en las **columnas 25–39** (15 por
  lado); el cuerpo tapa las filas intermedias. **Cada header se conecta de forma distinta
  (¡importa!):**
  - **Header superior:** la **Fila A queda libre** → el cable entra **directo en la Fila
    A** de la columna del pin (mismo nodo).
  - **Header inferior:** la **Fila J está OCUPADA por el pin y NO hay hueco libre** ahí (ni
    debajo, que son solo rieles). Se conecta tomando los **huecos de las Filas F–I** de esa
    misma columna (bajo el módulo, mismo nodo eléctrico que el pin) y **sacando un puente
    lateral hacia la derecha** (cols 42–64); ver §5.
- **USB-C:** columna **21** (filas F–G).
- **Zonas libres para componentes:** **columnas 1–21** (izquierda) y **42–64** (derecha).

> ⚠️ **La Fila J NO tiene huecos libres** en las columnas 25–39: el pin del ESP32 la
> ocupa y debajo solo hay rieles. **No busques dónde "enchufar" en la Fila J** — los
> pines inferiores se toman por las **Filas F–I** (bajo el módulo, mismo nodo) y se sacan
> por **puente lateral a la derecha** (§5). Solo la **Fila A** (header superior) queda
> libre para conexión directa. Las dos mitades **A–E** (mundo 3V3, arriba) y **F–J**
> (mundo 5V, abajo) están separadas por el canal central.

### Orientación del ESP32 (CRÍTICA — hazla antes de nada)

> 🛑 **Coloca el ESP32 con el conector USB apuntando a la IZQUIERDA** (sobresaliendo hacia
> la col 21). Con esa orientación, leyendo la **serigrafía** (los textos impresos en la
> placa), el pin **VIN** queda en la **columna 25 del header superior** (arriba-izquierda; se conecta
> por el **hueco libre de la Fila A25**, mismo nodo que el pin — ver §1) y el **3V3** en la
> **columna 25 del header inferior** (abajo, Fila J). **Verifícalo con los ojos en tu módulo:** si "VIN" no queda arriba a
> la izquierda (col 25), el módulo está **girado 180°** → gíralo antes de continuar. Un
> ESP32 al revés mete **5 V al mundo 3V3** y quema el regulador de la placa (§3, el cruce de
> la col 25).

> ✅ **Confirma también que la Fila A queda con huecos LIBRES por encima de los pines
> superiores** del ESP32 (ahí se conecta todo el header superior: VIN, GND y los 6 ADC de los
> FSR). En casi todos los módulos así es. **Si en tu placa los pines superiores ocupan la
> propia Fila A** (no hay hueco libre encima), **detente**: entonces el header superior
> necesita el **mismo pre-cableado por debajo del módulo** (por las Filas B–E, antes de
> asentarlo) que la Fila J en §5.

### Mapa de pines del ESP32

**Header superior — Fila A (accesible directo, hacia arriba):**

| Col | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **VIN** | GND | D13 | D12 | D14 | D27 | D26 | D25 | D33 | D32 | D35 | D34 | **VN** | **VP** | EN |
| Uso | **5 V** | GND | — | — | — | — | — | — | FSR6 | FSR5 | FSR4 | FSR3 | FSR2 | FSR1 | — |

> ⚠️ **No confundas "VIN" con "VN":** **VIN** (col 25, esquina) es **5 V (potencia)**;
> **VN** (col 37, junto a VP/EN) es **GPIO39 = FSR2 (entrada ADC)**.
> Confundirlos mete 5 V a un ADC.

**Header inferior — Fila J (contra el borde inferior):**

| Col | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **3V3** | GND | D15 | D2 | **D4** | **RX2** | **TX2** | **D5** | **D18** | **D19** | **D21** | RX0 | TX0 | D22 | **D23** |
| Uso | 3V3 | GND | — | — | LED1 | DF-TX→ | DF←RX | LED2 | LED3 | LED4 | LED5 | — | — | (LED2 alt) | LED6 |

`RX2 = GPIO16`, `TX2 = GPIO17`. Convención DFPlayer: ESP32 **TX2(17) → RX** del
módulo; ESP32 **RX2(16) ← TX** del módulo.

**Mapa lógico (coincide con `firmware/lib/GameCore/Config.h`):**

| Señal | GPIO | Col (Fila) | Nodo/destino en zona libre |
|---|---|---|---|
| FSR1 | 36 (VP) | 38 (A) | nodo **col 20** |
| FSR2 | 39 (VN) | 37 (A) | nodo **col 18** |
| FSR3 | 34 | 36 (A) | nodo **col 16** |
| FSR4 | 35 | 35 (A) | nodo **col 14** |
| FSR5 | 32 | 34 (A) | nodo **col 12** |
| FSR6 | 33 | 33 (A) | nodo **col 10** |
| LED1 | 4 | 29 (J) | IN1 del ULN (**col 58**, Fila E) |
| LED2 | 5 | 32 (J) | IN2 del ULN (**col 57**, Fila E) |
| LED3 | 18 | 33 (J) | IN3 del ULN (**col 56**, Fila E) |
| LED4 | 19 | 34 (J) | IN4 del ULN (**col 55**, Fila E) |
| LED5 | 21 | 35 (J) | IN5 del ULN (**col 54**, Fila E) |
| LED6 | 23 | 39 (J) | IN6 del ULN (**col 53**, Fila E) |
| DFPlayer RX2 (←TX) | 16 | 30 (J) | DFPlayer TX (por serigrafía) |
| DFPlayer TX2 (→RX) | 17 | 31 (J) | DFPlayer RX (por serigrafía, 1 kΩ serie) |

> Se usa **ADC1** para todos los FSR (ADC2 choca con el WiFi). Los GPIO 34–39 son
> **solo entrada** (perfectos para sensores).

---

## 2. Mapa de botones (índice ↔ posición ↔ arnés)

El firmware numera los botones **1..6**; esa numeración es la que ves en el gráfico
de la tapa y la que usa cada FSR y cada grupo LED. **Rotula cada arnés B1..B6** antes
de bajarlo al protoboard; un arnés cruzado hace que el juego lea/encienda la casilla
equivocada.

| Botón | Posición en la tapa | FSR (ADC) | Grupo LED (GPIO) | Arnés |
|---|---|---|---|---|
| 1 | superior izquierda | FSR1 · GPIO36 | LED1 · GPIO4 | **B1** |
| 2 | superior centro | FSR2 · GPIO39 | LED2 · GPIO5 | **B2** |
| 3 | superior derecha | FSR3 · GPIO34 | LED3 · GPIO18 | **B3** |
| 4 | inferior izquierda | FSR4 · GPIO35 | LED4 · GPIO19 | **B4** |
| 5 | inferior centro | FSR5 · GPIO32 | LED5 · GPIO21 | **B5** |
| 6 | inferior derecha | FSR6 · GPIO33 | LED6 · GPIO23 | **B6** |

Cada arnés Bk lleva **4 hilos**: FSR_alto, FSR_bajo, LED_ánodo común, LED_cátodo común.

---

## 3. Arquitectura de potencia — 4 rieles (seguridad anti-corto)

| Riel | Bus | Se alimenta desde |
|---|---|---|
| Superior `−` | **GND** | ESP32 GND (Fila A, col 26) |
| Superior `+` | **3V3** | ESP32 3V3 (Fila **J**, col 25) → **1 cable SUBE** al riel superior |
| Inferior `+` | **5 V** | ESP32 VIN (Fila **A**, col 25) → **1 cable BAJA** al riel inferior |
| Inferior `−` | **GND** | ESP32 GND (Fila J, col 26) |

**Reglas invariables:**
- Se **puentean los dos rieles `−`** (GND común): 1 jumper en un extremo (p. ej. col 1 o col 64).
- **NUNCA** se puentean los dos `+` (uno es 3V3, otro 5V → cortocircuito).
- El **mundo 3V3 vive arriba** (sensores); el **mundo 5V abajo** (LEDs/audio). El
  canal central los separa. Los módulos DIP (ESP32, ULN, DFPlayer) cruzan el canal por
  construcción: es normal, no crea corto mientras su potencia se tome del riel correcto.
- Muchos protoboards traen los rieles **partidos a la mitad** → verifica continuidad de
  cada riel de extremo a extremo y puentea si hace falta.

> 🛑 **EL ERROR QUE FRÍE EL ESP32 — el cruce de la columna 25.** En la **columna 25**
> conviven **VIN = 5 V** (Fila A, arriba) y **3V3** (Fila J, abajo). Los dos buses `+`
> **se cruzan**: el 3V3 (que sale del pin de **abajo**, J25) alimenta el riel de
> **arriba**; el 5 V (que sale del pin de **arriba**, A25) alimenta el riel de **abajo**.
> El error natural del primerizo es "conectar el pin `+` más cercano al riel de arriba"
> → mete **5 V al mundo 3V3** y quema el regulador 3V3 del ESP32 (y, con un FSR pisado,
> ~5 V sobre un ADC no tolerante a 5 V). **Regla mnemónica:** *3V3 vive abajo (J25) y
> sube; 5 V vive arriba (A25) y baja.* La única prueba que detecta este error es
> **medir el voltaje en los propios rieles** (§8), no la aislación entre ellos.

---

## 4. Plano hueco por hueco (rejilla del protoboard)

Vista de arriba. `═══` = riel; `·` = hueco libre; el **canal central** separa A–E de
F–J. Coordenada = **columna + fila** (p. ej. `C20` = fila C, columna 20).

### 4.1 Mitad superior izquierda — divisores FSR (cols 8–21)

Los **dos rieles de arriba** (3V3 `+` y GND `−`) están AMBOS **sobre la Fila A**. **No
hay riel bajo la Fila E**: ahí está el canal central.

> Diagrama **esquemático** (no es la posición literal hueco por hueco; las columnas exactas
> están en la tabla §6.2). `[R]` = **una** resistencia de 10 kΩ; hay **6**, una por canal.

```
 Riel + (3V3) ══●═══●═══●═══●═══●═══●══   FSR_alto de los 6 botones → aquí (naranja)
 Riel − (GND) ══●═══●═══●═══●═══●═══●══   pata GND de cada 10 kΩ → aquí (negro)
        col:    10    12    14    16    18    20
       botón:  FSR6  FSR5  FSR4  FSR3  FSR2  FSR1
   ┌───────────────────────────────────────────
 A │  [R]   [R]   [R]   [R]   [R]   [R]    una pata en el nodo, la otra SUBE al riel −
 B │   n     n     n     n     n     n     ← nodo: aquí llega el FSR_bajo del botón (azul)
 C │   ↗     ↗     ↗     ↗     ↗     ↗     jumper AZUL: del nodo a la Fila A del ADC…
   └───────────────────────────────────────────
   … destino del jumper (Fila A de OTRA columna): FSR6→A33 · FSR5→A34 · FSR4→A35 ·
     FSR3→A36 · FSR2→A37 · FSR1→A38
      ═══ canal central ═══  (mitad inferior / mundo 5V → §4.3)
```

Cada columna-nodo (10,12,14,16,18,20) reúne **tres** conexiones en su grupo A–E: una pata
de la **10 kΩ**, el **FSR_bajo** (del botón) y el **jumper al ADC** (a la Fila A de la
columna del ADC). La **otra** pata de la 10 kΩ va al **riel − (GND)** de arriba — la
resistencia NO puede tener sus dos patas en la misma columna-nodo (se anularía). El
**FSR_alto** va al riel + (3V3), no al nodo. *(Opcional antirruido: 100 nF del nodo a GND.)*

### 4.2 El ESP32 (cols 22–41)

Header superior por la **Fila A** (libre, conexión directa). Header inferior: la Fila J
está ocupada por el pin, así que se toma por las **Filas F–I** de la columna del pin y se
saca por **puente lateral a la derecha** (ver §1 y §5). El cuerpo tapa las filas
intermedias.

### 4.3 Mitad inferior derecha — ULN2803A, grupos LED y DFPlayer (cols 42–64)

```
        DFPlayer (cols 42–49)      ULN2803A (cols 50–58)     Grupos LED (cols 59–64)
                                  ┌ notch a la DERECHA ┐
        col: 42 .. 49         50   51  52  53  54  55  56  57  58   59 60 61 62 63 64
 A–D │  (libre / caps)        ·    ·   ·   ·   ·   ·   ·   ·   ·    ·  ·  ·  ·  ·  ·
 E   │  ┌ DFPlayer ┐  hilera  GND  IN8 IN7 IN6 IN5 IN4 IN3 IN2 IN1  ·  ·  ·  ·  ·  ·
     │  │ (silk)   │  sup.    (p9) ← IN6..IN1 reciben GPIO LEDk por puente lateral (§5)
 ════╪══ canal ════════════════════════════════════════════════════════════════════
 F   │  └ DFPlayer ┘  hilera  COM  O8  O7 OUT6 O5  O4 OUT3 O2 OUT1  R  R  R  R  R  R
     │     inf.             (p10)          c53         c56    c58  2.2kΩ desde riel 5V
 G–J │  100µF/100nF          ·    ·   ·   ·   ·   ·   ·   ·   ·    a → ánodo común (tapa)
     │  (VCC→GND DF)         cátodo común (tapa) baja por la col del OUT: c58=LED1..c53=LED6
   ──┴────────────────────────────────────────────────────────────────────────────
 Riel + (5 V) ═══════════ VCC(DFPlayer) · COM(ULN,c50) · las 6× 2.2kΩ ══════════════
 Riel − (GND) ═══════════ GND(DFPlayer) · GND(ULN,p9→arriba) ════════════════════════
```

**ULN2803A (DIP-18) — se monta A CABALLO del canal central** (una hilera en Fila E,
otra en Fila F). Si lo montas en un solo lado, sus dos hileras se cortocircuitan.
**Muesca (notch) hacia la derecha** — la muesca es la **hendidura semicircular** en un
extremo del chip; el **pin 1** es el más cercano a ella (a veces marcado con un punto) y
debe quedar **arriba-derecha**, para que las **salidas queden en la Fila F** (mitad
inferior, junto a los LEDs). *(En la hilera inferior del diagrama, las salidas usadas son
`OUT1..OUT6` = cols 58..53; `O7`/`O8` = pines 12/11 quedan sin usar; las columnas exactas
están en la tabla de abajo.)*

| Pin ULN | Señal | Hueco | Conexión |
|---|---|---|---|
| 1 | IN1 | **E58** | ← LED1 (GPIO4, Fila J c29) por puente |
| 2 | IN2 | **E57** | ← LED2 (GPIO5, Fila J c32) por puente |
| 3 | IN3 | **E56** | ← LED3 (GPIO18, Fila J c33) por puente |
| 4 | IN4 | **E55** | ← LED4 (GPIO19, Fila J c34) por puente |
| 5 | IN5 | **E54** | ← LED5 (GPIO21, Fila J c35) por puente |
| 6 | IN6 | **E53** | ← LED6 (GPIO23, Fila J c39) por puente |
| 9 | GND | **E50** | → riel − (GND) |
| 10 | COM | **F50** | → riel + (5 V) |
| 18 | OUT1 | **F58** | → cátodo LED1 (col 58, baja a G–J) |
| 17 | OUT2 | **F57** | → cátodo LED2 (col 57) |
| 16 | OUT3 | **F56** | → cátodo LED3 (col 56) |
| 15 | OUT4 | **F55** | → cátodo LED4 (col 55) |
| 14 | OUT5 | **F54** | → cátodo LED5 (col 54) |
| 13 | OUT6 | **F53** | → cátodo LED6 (col 53) |

*(IN7/IN8 = pines 7,8 y OUT7/OUT8 = pines 11,12 quedan sin usar.)* Los puentes IN
llevan **señal lógica 3.3 V** (no potencia), por eso pueden cruzar a la Fila E sin
violar la frontera de rieles.

---

## 5. Ruteo de la Fila J (detalle crítico del montaje)

La **Fila J (cols 25–39) está ocupada por los pines inferiores del ESP32 y NO tiene
huecos libres** (debajo solo están los rieles). Para conectar cada pin inferior se toma
un **hueco de las Filas F–I de su misma columna** (bajo el módulo, mismo nodo eléctrico
que el pin) y se **saca un puente/cable lateral hacia la derecha** (**cols 42–64**), donde
viven el ULN, los LEDs y el DFPlayer. **Excepción — P1 y P4** (energía): no van a la
derecha sino a los **rieles** — P1 (3V3) **sube** al riel superior, P4 (GND) **baja** al
inferior (ver las dos primeras filas de la tabla).

> ⚠️ **Cablea la mitad inferior con el ESP32 LEVANTADO (o antes de asentarlo a fondo).**
> Los huecos F–I quedan bajo el cuerpo del módulo: inserta ahí los puentes de los pines
> inferiores **antes de prensar el ESP32**, o retíralo para cablear esa mitad y vuelve a
> asentarlo. Con el módulo ya prensado no entra un cable en F–I.

En concreto:

| Pin (Fila J) | Sale hacia | Señal |
|---|---|---|
| **3V3 · c25 (P1)** | riel **superior +** — tómalo en **I25** (bajo el módulo) y SUBE | 3V3 (naranja) |
| **GND · c26 (P4)** | riel **inferior −** — tómalo en **I26** (bajo el módulo) | GND (negro) |
| LED1 · c29 | IN1 del ULN (**E58**) | GPIO → IN (verde) |
| LED2 · c32 | IN2 del ULN (**E57**) | GPIO → IN (verde) |
| LED3 · c33 | IN3 del ULN (**E56**) | GPIO → IN (verde) |
| LED4 · c34 | IN4 del ULN (**E55**) | GPIO → IN (verde) |
| LED5 · c35 | IN5 del ULN (**E54**) | GPIO → IN (verde) |
| LED6 · c39 | IN6 del ULN (**E53**) | GPIO → IN (verde) |
| DF-RX2 · c30 (GPIO16) | DFPlayer **TX** (silk) | UART (marrón) |
| DF-TX2 · c31 (GPIO17) | DFPlayer **RX** (silk), vía 1 kΩ | UART (marrón) |

El header superior (Fila A: **VIN/5 V** c25, GND c26, los 6 ADC c33–38) **no** tiene
este problema: la Fila A está libre y se conecta directo hacia arriba. *(El 3V3 del riel
superior viene del header inferior J25 y **sube** —P1, §6.1—; no está en la Fila A.)*

---

## 6. Net list por subsistema (con columnas exactas)

### 6.1 Energía

| # | Desde | Hasta | Nota |
|---|---|---|---|
| P1 | ESP32 3V3 (Fila **J**, c25) | Riel **superior +** | bus 3V3 — **SUBE** (cruce, §3) |
| P2 | ESP32 VIN (Fila **A**, c25) | Riel **inferior +** | bus 5V — **BAJA** (cruce, §3) |
| P3 | ESP32 GND (Fila A, c26) | Riel **superior −** | GND |
| P4 | ESP32 GND (Fila J, c26) | Riel **inferior −** | GND |
| P5 | Riel **superior −** | Riel **inferior −** | puente GND común (1 jumper, un extremo) |

Alimentación: **solo el PC al ESP32 por cable USB** (5 V). Sin power bank ni red.
**Cap de bus:** **1×** **1000 µF / 16 V** entre riel **inferior +** (5 V) y riel inferior −
(colócalo sobre los rieles inferiores, cerca de donde entra el 5 V; el inventario trae 2,
usa 1, el otro es reserva); la **pata `+` (larga, lado sin banda) al 5 V**, la banda `−` a
GND. Invertirlo lo revienta.

### 6.2 Sensores FSR (mitad superior-izquierda, cols 8–21)

Topología por canal: `3V3 ─[FSR]─ nodo ─→ ADC ; nodo ─[10 kΩ]─ GND`.

| Canal | Nodo (col) | ADC (Fila A) | Conexiones en el nodo |
|---|---|---|---|
| FSR1 | **col 20** | VP/GPIO36 (c38) | 10 kΩ→GND · FSR_bajo(B1) · jumper→A38 |
| FSR2 | **col 18** | VN/GPIO39 (c37) | 10 kΩ→GND · FSR_bajo(B2) · jumper→A37 |
| FSR3 | **col 16** | GPIO34 (c36) | 10 kΩ→GND · FSR_bajo(B3) · jumper→A36 |
| FSR4 | **col 14** | GPIO35 (c35) | 10 kΩ→GND · FSR_bajo(B4) · jumper→A35 |
| FSR5 | **col 12** | GPIO32 (c34) | 10 kΩ→GND · FSR_bajo(B5) · jumper→A34 |
| FSR6 | **col 10** | GPIO33 (c33) | 10 kΩ→GND · FSR_bajo(B6) · jumper→A33 |

El hilo **FSR_alto** de cada botón va al **riel + (3V3)**; el **FSR_bajo** al nodo.
**El FSR no tiene polaridad:** sus dos patas son iguales — elige una como "FSR_alto" (irá a
3V3) y la otra como "FSR_bajo" (irá al nodo); da igual cuál sea cuál, pero **rotúlalas al
soldar el arnés** para no confundirlas después.
**Trenza cada par de hilos FSR** (alto + bajo) a lo largo de los ~25–30 cm para
inmunizar el ruido.

### 6.3 LEDs vía ULN2803A (mitad inferior-derecha, cols 50–64)

Por grupo (3 LEDs en paralelo, en la tapa): `5V ─[2.2 kΩ]─ ánodo` (columnas 59–64) y
`cátodo ─ OUTk del ULN`. La entrada `INk` llega del GPIO por puente lateral (§5).
El ULN (pines, huecos y orientación) está en **§4.3**.

> **Cómo se arma cada grupo LED (en la tapa).** Un grupo = **3 LEDs blancos en paralelo**.
> En un LED, la **pata larga es el ánodo (+)** y la corta (del lado con el borde plano del
> encapsulado) es el **cátodo (−)**. Une las **3 patas largas** entre sí → un solo hilo =
> **ánodo común**; une las **3 patas cortas** → **cátodo común**. Rotula ambos hilos por
> botón (B1..B6). El **ánodo común** va a la 2.2 kΩ (a 5 V) y el **cátodo común** a la salida
> OUTk del ULN.

| Grupo | 2.2 kΩ (desde 5V) → ánodo | Ánodo común (tapa) | Cátodo común (tapa) → OUT |
|---|---|---|---|
| LED1 | col **59** | → col 59 | → **col 58** (OUT1) |
| LED2 | col **60** | → col 60 | → **col 57** (OUT2) |
| LED3 | col **61** | → col 61 | → **col 56** (OUT3) |
| LED4 | col **62** | → col 62 | → **col 55** (OUT4) |
| LED5 | col **63** | → col 63 | → **col 54** (OUT5) |
| LED6 | col **64** | → col 64 | → **col 53** (OUT6) |

**Cuidado con los 2 hilos de cada grupo:** el **ánodo** cae en cols 59–64 y el **cátodo**
en cols 53–58 (columnas no adyacentes). Rotula ambos por grupo (Bk) y sigue la tabla fila
por fila para no cruzarlos.

> **Brillo esperado = tenue pero visible.** Los 6 grupos usan **2.2 kΩ** (las 2× 1 kΩ
> del inventario van al DFPlayer; ver `materiales.md §3`). Con 2.2 kΩ desde 5 V vía el
> ULN, cada LED recibe **~0.19 mA** (≈ 3.5 mA los 6 grupos) según ngspice
> (`spice/`); **confirmar con multímetro al energizar**. Es el máximo alcanzable
> con el inventario; los LEDs van directo en la superficie (huecos en el acrílico), así
> que a esa corriente se ven.
>
> ⚠️ **GPIO5 (LED2) es un strapping pin** (un pin que el ESP32 lee al encender para decidir
> cómo arranca; una carga puede alterarlo). Si tras cablear LED2 el ESP32 **no arranca**,
> reasigna **LED2 → GPIO22** (D22, Fila J **col 38**, libre y no strapping): (1) edita
> `firmware/lib/GameCore/Config.h` → `PIN_LED[1]` de `5` a `22`, (2) **recompila y
> reflashea**, (3) mueve el puente de IN2 desde la col 32 a la **col 38** (Fila J).

### 6.4 DFPlayer Mini + parlante (cols 42–49)

El DFPlayer Mini se monta **a caballo del canal** (cols 42–49), orientado con la
**columna izquierda (VCC/RX/TX/GND/SPK) del lado de la Fila F** (mitad inferior, mundo
5V) para que VCC y GND caigan junto a los rieles inferiores. Se conecta por las
**etiquetas serigrafiadas** del módulo. Pinout confirmado de tu placa (mirándola con el
**Micro USB hacia abajo**):

```
   columna izquierda        columna derecha
   (1) VCC                  BUSY    (1)
   (2) RX                   USB −   (2)
   (3) TX                   USB +   (3)
   (4) DAC_R                ADKEY_2 (4)
   (5) DAC_L                ADKEY_1 (5)
   (6) SPK_1                IO_2    (6)
   (7) GND                  GND     (7)
   (8) SPK_2                IO_1    (8)
```

Solo se usan **VCC, RX, TX, SPK_1, SPK_2 y GND** (todos en la columna izquierda):

| Etiqueta (silk) | Conexión |
|---|---|
| VCC (izq-1) | riel **inferior +** (5 V) |
| GND (izq-7) | riel **inferior −** |
| RX (izq-2) | ← **1 kΩ** en serie ← ESP32 **TX2/GPIO17** (pin inferior c31, por puente lateral) |
| TX (izq-3) | → ESP32 **RX2/GPIO16** (pin inferior c30, por puente lateral) — **medir antes** (abajo) |
| SPK_1 (izq-6) / SPK_2 (izq-8) | **parlante 4 Ω** (par diferencial = los dos hilos llevan la señal **entre sí**; **NO aterrizar** ninguno a GND; ojo: **GND (izq-7) va EN MEDIO** de ambos) |

**Desacople (junto al módulo, cols 42–44, mitad inferior):** **1×** **100 µF / 16 V**
electrolítico entre VCC y GND (**pata `+` larga al VCC**, banda `−` a GND; trae 2, usa 1)
+ 1× **100 nF** cerámico ("104", sin polaridad) entre VCC y GND. microSD **FAT32** con
`/mp3/0001.mp3` … `/mp3/0004.mp3` (ver `audio/README.md`).

> ⚠️ **Protege el ESP32 — línea DFPlayer TX → GPIO16.** GPIO16 **no es 5V-tolerante**.
> Antes de conectar, **mide el nivel alto del TX del módulo**: si **~3.3 V** → directo;
> si **~5 V** → intercala un divisor: **1 kΩ en serie** desde el TX al nodo, **2 kΩ del
> nodo a GND**, y el **nodo → GPIO16** (da 5 V × 2k/(1k+2k) ≈ **3.33 V**).
>
> **Volumen moderado** (parlante de 4 Ω sobre puerto USB del PC); los caps de desacople
> absorben los picos del amplificador.

---

## 7. Leyenda de señales (colores sugeridos para el montaje)

| Color | Señal |
|---|---|
| Negro | GND |
| Naranja | 3V3 |
| Rojo | 5 V |
| Azul | señal FSR (FSR_bajo / nodo → ADC) |
| Verde | GPIO → IN del ULN |
| Violeta | OUT del ULN → cátodo del grupo LED |
| Amarillo | ánodo común del grupo LED (a 2.2 kΩ / 5 V) |
| Marrón | línea UART del DFPlayer |

---

## 8. Checklist con multímetro

> 🛑 **La PRIMERA vez se energiza con la placa DESNUDA: solo el ESP32 y los rieles, nada
> más conectado.** No conectes FSR, LEDs ni DFPlayer hasta pasar el **Bloque B en vacío**.
> El orden completo de armado está en **§9 — síguelo paso a paso; no uses esta lista suelta
> como secuencia.** El **Bloque A** se corre cada vez que vayas a energizar (placa sin
> corriente); el **Bloque B** es la medición inmediatamente **después** de dar corriente.

### Bloque A — con la placa SIN energizar (multímetro en continuidad)

- [ ] Rieles `−` con continuidad entre sí y con GND del ESP32.
- [ ] Riel 3V3 y riel 5V **sin** continuidad entre ellos ni con GND (aislación).
- [ ] Cada riel continuo de extremo a extremo (puentear si está partido).
- [ ] Ningún FSR a 5 V (solo a 3V3); ningún ADC a 5 V (ojo: **VIN**=5 V en c25 ≠ **VN**=GPIO39/ADC en c37).
- [ ] ULN **a caballo del canal**, muesca a la derecha; pin 9 (E50) a GND (**riel superior −**),
      pin 10 (F50) a 5 V.
- [ ] LEDs: polaridad (ánodo a 2.2 kΩ/5 V en cols 59–64, cátodo a OUT del ULN cols 53–58).
- [ ] Electrolíticos (1000 µF, 100 µF) con la **polaridad correcta** (banda `−` a GND).
- [ ] Nada en ADC2 / pines de WiFi. GPIO12 libre (no cablear).
- [ ] **DFPlayer TX medido ≤ 3.3 V** antes de conectarlo a GPIO16 (si 5 V → divisor).
- [ ] Arneses rotulados **B1..B6** sin cruzar (§2). microSD FAT32 con los 4 MP3.

### Bloque B — recién energizada (multímetro en tensión, en los rieles)

- [ ] **Voltaje EN LOS RIELES tras energizar** (la prueba que caza el cruce de la col 25):
      **riel superior + ≈ 3.3 V** y **riel inferior + ≈ 4.6–5.0 V** (muchos DevKit meten
      VIN por un diodo Schottky → el riel de 5 V puede leer ~4.6–4.7 V; es normal). Lo que
      **NUNCA** debe pasar: el **riel superior marcando ~5 V** → estaría alimentado con VIN
      por error: **desconecta YA** y corrige P1/P2 (§3).
- [ ] Tras cablear LED2, el ESP32 **arranca** (GPIO5 es un *strapping pin* — un pin que el
      chip lee al encender para decidir cómo arranca; si no arranca, LED2→GPIO22).

---

## 9. Secuencia de armado (orden seguro)

1. **Rieles primero.** Montar P1–P5 (§6.1) y el cap de bus 1000 µF. **Ojo:** **P1 (3V3,
   J25) y P4 (GND, J26) salen de pines del ESP32 en la Fila J**, que quedan bajo el módulo →
   se toman por las **Filas F–I con el ESP32 LEVANTADO**, antes de prensarlo (ver §5); si ya
   lo prensaste, no entrará el cable. **P2 (VIN, A25) y P3 (GND, A26)** salen del header
   superior (Fila A libre): directos. Verificar continuidad y **aislación** con el multímetro
   (§8, Bloque A).
2. **Energizar en vacío** (solo ESP32, por USB). **(a)** Con el multímetro, medir **en los
   rieles**: superior + ≈ **3.3 V**, inferior + ≈ **4.6–5.0 V** (§8, Bloque B) — esto **no
   necesita firmware**. *Si el riel superior marca ~5 V, desconecta y corrige el cruce de la
   col 25 antes de seguir.* **(b)** Para confirmar el arranque por **Serial (115200)**
   necesitas el **firmware flasheado**: ver `flashing.md`.
3. **FSR uno por uno.** Montar el divisor del canal (nodo en su columna, 10 kΩ a GND,
   FSR_alto a 3V3, jumper a la Fila A). Ver la lectura ADC en el Serial en reposo y al
   pisar. **Ajustar `cfg::UMBRAL_PISADA`** = editar `firmware/lib/GameCore/Config.h`,
   recompilar y reflashear (ver `flashing.md`). Repetir los 6 (B1..B6).
4. **ULN + LEDs por grupo.** Montar el ULN a caballo del canal (cols 50–58, muesca
   derecha; pin 9→GND, pin 10→5 V). Por grupo: 2.2 kΩ (5V→ánodo), ánodo y cátodo de la
   tapa, IN←GPIO por puente lateral. Probar encendido (brillo tenue esperado).
   *(GPIO5 strapping: confirmar que el ESP32 sigue arrancando tras LED2.)*
5. **DFPlayer + parlante.** VCC/GND por serigrafía; caps de desacople; TX2→(1 kΩ)→RX;
   **medir TX del módulo** antes de RX2←TX; microSD; parlante a SPK1/SPK2. Verificar
   `audioOk`. Volumen moderado.
6. **Tapa.** Módulos bajo-tapa, rutear arneses B1..B6, dejar bucle de servicio, pegar
   el gráfico con ventana sobre cada botón.

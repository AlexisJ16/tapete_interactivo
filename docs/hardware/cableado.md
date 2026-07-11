# Guía de armado del protoboard — Tapete Interactivo (paso a paso, hueco por hueco)

> **Fuente única de verdad del armado.** Guía **hueco por hueco** para montar el
> circuito **de una sola vez**, pensada para quien arma por primera vez: cada paso
> dice **qué componente**, **en qué huecos** y **cada puente de dónde a dónde**, con
> **coordenadas exactas, color de cable y verificación**. Geometría del protoboard
> **validada con el autor y bloqueada** (2026-06-29; esquema de energía actualizado
> 2026-07-03): no re-inventar.
>
> El **mapa de pines canónico** vive en `firmware/lib/GameCore/Config.h` (si esta guía
> y `Config.h` discrepan, se detiene el trabajo y se concilia — `Config.h` manda en
> pines). El **diseño conceptual** (decisiones, mecánica del botón, caja) está en
> `00_diseno_circuito.md`; los **materiales y valores** en `materiales.md`; las
> **corrientes simuladas** en `spice/`.

Tapete de **6 botones** (2 filas × 3 columnas):

```
[1] [2] [3]
[4] [5] [6]
```

Cada botón = **1 FSR** (pisada) + **3 LEDs blancos en paralelo** (un pin PWM por
grupo). Los LEDs son **blancos** (no RGB): el feedback es patrón de parpadeo + sonido.
Los 18 LEDs y los 6 FSR viven **en la tapa**; al protoboard llegan solo **4 hilos por
botón** (FSR_alto, FSR_bajo, LED_ánodo común, LED_cátodo común) — ver Paso 8 y
`00_diseno_circuito.md §4`.

---

## 1. Antes de empezar (léelo primero — no te saltes esto)

### 1.1 Cómo funciona el protoboard y cómo se leen las coordenadas

- Protoboard de **830 puntos**. Filas **A–E** (mitad superior) · **canal central** ·
  **F–J** (mitad inferior). Columnas **1–64**. Rieles `+/−` horizontales arriba y abajo.
- **Los 5 huecos de una misma columna en la mitad superior** (A, B, C, D, E) están
  **unidos por dentro = 1 solo nodo eléctrico**; lo mismo los 5 de la mitad inferior
  (F, G, H, I, J) = **otro** nodo. El **canal central separa** las dos mitades: A–E y
  F–J de la misma columna **no se tocan**, salvo por un componente que cruce el canal.
- Los **rieles `+` y `−`** corren horizontales por el borde: **toda la línea es el mismo
  nodo**. Por eso, cuando la guía dice *"conecta en la col 20"*, da igual en cuál de
  A20/B20/C20/D20/E20 pinches: es el mismo nodo.
- Una **resistencia o un LED** ocupa **dos** nodos (una pata en cada columna); un
  **jumper** copia un nodo a otro.
- **Sistema de coordenadas de esta guía: `FilaColumna`.** `C20` = fila C, columna 20.
  `A25` = fila A, columna 25. `riel superior +` / `riel inferior −` para los rieles.
- Muchos protoboards traen los rieles **partidos a la mitad** → verifica continuidad de
  cada riel de extremo a extremo con el multímetro y puentea si hace falta.

### 1.2 Leyenda de colores de cable (úsala en todo el armado)

| Color | Señal |
|---|---|
| Negro | GND |
| Naranja | 3V3 |
| Rojo | 5 V |
| Azul | señal FSR (FSR_bajo / nodo → ADC) |
| Verde | GPIO → IN del ULN |
| Violeta | OUT del ULN → cátodo del grupo LED |
| Amarillo | ánodo común del grupo LED (a 110 Ω / 5 V) |
| Marrón | línea UART del DFPlayer |

### 1.3 Los peligros que fríen (resumen — el detalle está en cada paso)

Cuatro cosas rompen hardware. Ténlas presentes de principio a fin:

1. **Orientación del ESP32 (lo más peligroso).** Con el USB a la **izquierda**, el pin
   **VIN = 5 V** queda **arriba-izquierda** (`A25`) y el **3V3** queda **abajo** (`J25`).
   Si el módulo se coloca **girado 180°**, el 5 V y el 3V3 se **invierten** → el 5 V
   entra al **mundo 3V3** (sensores/ADC) y lo quema. La **única** prueba que lo caza es
   **medir el voltaje en los rieles con la placa energizada en vacío** (Paso 3).
2. **Los dos rieles `+` van SEPARADOS y por extremos opuestos.** El **riel superior +**
   es **3V3** y entra por la **izquierda** (col 1); el **riel inferior +** es **5 V** y
   entra por la **derecha** (col 64). **NUNCA** se puentean entre sí (sería 3V3 contra
   5 V = cortocircuito). El mundo 3V3 vive arriba (sensores); el mundo 5 V abajo
   (LEDs/audio); el canal central los separa.
3. **5 V a un ADC.** No confundas **VIN** (col 25, esquina = 5 V de potencia) con **VN**
   (col 37 = GPIO39 = entrada ADC del FSR2). Confundirlos mete 5 V a un ADC no tolerante.
4. **Pares `+`/`−` adyacentes en los waypoints de energía.** El esquema nuevo deja el
   3V3 pegado a un GND (`F1`/`F2`) y el 5 V pegado a un GND (`A64`/`A63`). Un puente
   corrido una columna = corto `+`↔`−`. Sigue las coordenadas al pie y verifica aislación
   antes de energizar (Paso 3 / Checklist Bloque A).

---

## 2. Mapa general de zonas (qué bloque va en qué columnas)

Vista de arriba. Antes de pinchar hueco por hueco, ten claro el reparto del tablero:

```
 columnas:  1–2      8–20     21      22–41       42–49      50–58      59–64
            energía   FSR×6    USB     ESP32       DFPlayer   ULN2803A   LEDs
            (izq)     (divis.)         (a caballo) (caballo)  (caballo)  (grupos)
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │ riel superior +  =  3V3   ← entra por la IZQUIERDA (P1/P4 suben desde F1/F2, col 1–2)
 │                                                                                     │
 │ A–E (arriba):   nodos FSR · header sup del ESP32 (Fila A) · IN(E58–E53)/GND(E50) del
 │                 ULN · waypoints de energía A64=5V y A63=GND                         │
 │ ═══════════ canal central: mundo 3V3 (arriba) separado de mundo 5V (abajo) ════════ │
 │ F–J (abajo):    header inf del ESP32 (Fila J) · DFPlayer (Fila F) · OUT(F58–F53)/    │
 │                 COM(F50) del ULN · ánodos+110 Ω (cols 59–64) y cátodos (a OUT, 53–58) │
 │                                                                                     │
 │ riel inferior +  =  5 V   ← entra por la DERECHA (P2/P3 bajan desde A64/A63, col 63–64)
 └──────────────────────────────────────────────────────────────────────────────────┘
```

- **Energía por los extremos:** el **3V3** sube al **riel superior +** desde la
  **izquierda** (cols 1–2); el **5 V** baja al **riel inferior +** desde la **derecha**
  (cols 63–64). Así los dos `+` nunca se acercan.
- **Zonas libres para componentes:** FSR en cols **8–20**, DFPlayer **42–49**, ULN
  **50–58**, LEDs **59–64**. El **USB-C** sale por la col **21**.

---

## 3. Armado PASO A PASO (en orden seguro)

> Arma en este orden. No conectes FSR, LEDs ni DFPlayer hasta pasar el **Paso 3
> (checkpoint en vacío)**. Cada paso termina con su verificación; no avances con una
> verificación en rojo.

### Paso 1 — ESP32: orientar, pre-cablear la Fila J, asentar

El ESP32 (DevKit 30 pines) se monta **a caballo del canal central**, cubriendo
**columnas 22–41**, **corrido hacia el borde inferior**: sus **pines inferiores ocupan
la Fila J** y por arriba **deja libre la Fila A**. Los pines están en las **columnas
25–39** (15 por lado); el cuerpo tapa las filas intermedias.

**1.1 Orienta el módulo (CRÍTICO — hazlo antes de nada).**
Coloca el ESP32 con el **conector USB apuntando a la IZQUIERDA** (sobresaliendo hacia
la col 21). Con esa orientación, leyendo la **serigrafía**, el pin **VIN** queda en
**`A25`** (arriba-izquierda, header superior) y el **3V3** en **`J25`** (abajo, header
inferior). **Verifícalo con los ojos en tu módulo:** si "VIN" no queda arriba-izquierda
(col 25), el módulo está **girado 180°** → gíralo antes de continuar. Un ESP32 al revés
mete **5 V al mundo 3V3** (ver §1.3, peligro 1).

**1.2 Confirma que la Fila A queda LIBRE** por encima de los pines superiores (ahí se
conecta todo el header superior: VIN, GND y los 6 ADC de los FSR). En casi todos los
módulos así es. **Si en tu placa los pines superiores ocupan la propia Fila A** (no hay
hueco libre encima), **detente**: entonces el header superior necesita el **mismo
pre-cableado por debajo** (Filas B–E, antes de asentar) que la Fila J en el paso 1.3.

**1.3 Pre-cablea los pines inferiores (Fila J) — con el ESP32 LEVANTADO.**
La **Fila J (cols 25–39) está ocupada por los pines y NO tiene huecos libres** (debajo
solo hay rieles). Cada pin inferior se toma por un **hueco de las Filas F–I de su misma
columna** (bajo el módulo, mismo nodo eléctrico) y se saca un **puente lateral**. Estos
huecos quedan **bajo el cuerpo del módulo**: inserta estos puentes **antes de prensar el
ESP32** (o retíralo para cablearlos y vuelve a asentarlo). Con el módulo prensado no
entra un cable en F–I.

| Pin (Fila J) | Toma en | Puente hasta | Color | Nota |
|---|---|---|---|---|
| 3V3 · c25 (P1) | **I25** | **F1** | naranja | 1er puente de P1; el 2º (F1→riel) va en Paso 2 |
| GND · c26 (P4) | **I26** | **F2** | negro | 1er puente de P4; el 2º (F2→riel) va en Paso 2 |
| LED1 · c29 (GPIO4) | **I29** | **A58** (nodo de IN1) | verde | deja libre **E58** para el pin del ULN |
| LED2 · c32 (GPIO5) | **I32** | **A57** (nodo de IN2) | verde | GPIO5 = strapping (ver Paso 6) |
| LED3 · c33 (GPIO18) | **I33** | **A56** (nodo de IN3) | verde | |
| LED4 · c34 (GPIO19) | **I34** | **A55** (nodo de IN4) | verde | |
| LED5 · c35 (GPIO21) | **I35** | **A54** (nodo de IN5) | verde | |
| LED6 · c39 (GPIO23) | **I39** | **A53** (nodo de IN6) | verde | |
| DF-RX2 · c30 (GPIO16) | **I30** | aparca la punta en **A45** (hueco inerte) | marrón | se remata en Paso 7 → TX del DFPlayer |
| DF-TX2 · c31 (GPIO17) | **I31** | aparca la punta en **A46** (hueco inerte) | marrón | se remata en Paso 7 → RX (vía 1 kΩ) |

Los puentes de LED terminan en la **Fila A de las cols 58–53** — el **mismo nodo** que los
pines IN del ULN (que irán en la Fila E, Paso 5), pero en un **hueco distinto**: así el pin
del ULN entra sin pelear el hueco (simétrico al cátodo, que "baja a G–J" en el Paso 5). Las
dos puntas UART del DFPlayer se **aparcan en huecos inertes** (`A45`, `A46`, vacíos) hasta
el **Paso 7**, cuando el DFPlayer ya esté asentado y se conozcan las columnas de sus pines
RX/TX por serigrafía. Todos estos puentes llevan **señal lógica 3.3 V** (no potencia), por
eso pueden cruzar a la mitad superior sin violar la frontera de rieles.

> **Nota de nodo (aplica a toda la tabla):** las tomas bajo el módulo (`I25`, `I29`, …) se
> indican en la **Fila I**, pero **cualquier hueco libre F–I de esa misma columna es el
> mismo nodo** del pin — usa el que te resulte cómodo bajo el cuerpo del módulo.

**1.4 Asienta el ESP32** (prénsalo). El header superior (Fila A) queda libre para
conectar directo hacia arriba en los pasos siguientes.

**Verificación Paso 1:** USB a la izquierda; VIN visible arriba-izquierda; los 10
puentes de la Fila J insertados **antes** de prensar; nada aún en los rieles.

### Paso 2 — Rieles de energía (esquema P1–P5)

Cada bus va del pin a su riel en **2 puentes**: pin → **waypoint** (columna extrema) →
riel. El 3V3 sube por la **izquierda**; el 5 V baja por la **derecha**; así los dos rieles
`+` entran por **extremos opuestos** del tablero y nunca se acercan.

| # | Bus | Puente 1 (pin → waypoint) | Puente 2 (waypoint → riel) | Color |
|---|---|---|---|---|
| **P1** | 3V3 | `I25` → **`F1`** (col 1, mitad **inferior**) *(hecho en Paso 1.3)* | `F1` → **riel superior +** | naranja |
| **P4** | GND | `I26` → **`F2`** (col 2, mitad **inferior**) *(hecho en Paso 1.3)* | `F2` → **riel superior −** | negro |
| **P2** | 5 V | `A25` → **`A64`** (col 64, mitad **superior**) | `A64` → **riel inferior +** | rojo |
| **P3** | GND | `A26` → **`A63`** (col 63, mitad **superior**) | `A63` → **riel inferior −** | negro |
| **P5** | GND común | puente **riel superior − ↔ riel inferior −** (1 jumper, en **cualquier extremo** del tablero, p. ej. col 1 o col 64) | — | negro |

**Precisiones obligatorias (esto lo hace seguro):**
- **`J25` (3V3) y `J26` (GND)** están en la Fila J ocupada → se toman por **`I25`/`I26`**
  (bajo el módulo, mismo nodo); por eso su 1er puente se **pre-cabló en el Paso 1.3**.
  **`A25`/`A26`** están en la Fila A libre → son directos, se hacen ahora.
- **Waypoints:** izquierda en la **mitad INFERIOR** (`F1`,`F2`, libres); derecha en la
  **mitad SUPERIOR** (`A64`,`A63`, libres).
- 🛑 **El 5 V (P2) NUNCA en la mitad inferior de la col 64:** ahí está el **ánodo de
  LED6** con su 110 Ω, y le saltaría la resistencia (lo quemaría). Su waypoint va en la
  mitad **superior** (`A64`), separada del ánodo por el canal central. Igual `A63` (GND,
  mitad superior) no toca el ánodo de LED5 que está en la col 63 mitad inferior.
- ⚠️ **Pares `+`/`−` adyacentes:** `A64` (5 V) queda junto a `A63` (GND); `F1` (3V3)
  junto a `F2` (GND). No corras un puente una columna: sería corto `+`↔`−`.
- ⚠️ **Ruteo del puente P2** (`A25`→`A64`): corre 5 V a lo largo de la Fila A, **pasando
  por encima de los pines ADC** `A33`–`A38`. Tiéndelo **despejado** (cable aéreo, sin
  pinchar esos huecos) para que el 5 V no roce un ADC.

**Cap de bus:** **1×** **1000 µF / 16 V** entre riel **inferior +** (5 V) y riel inferior
`−`, cerca de donde entra el 5 V; **pata `+` (larga) al 5 V**, banda `−` a GND.
Invertirlo lo revienta. (El inventario trae 2; usa 1, el otro es reserva.)

Alimentación: **solo el PC al ESP32 por cable USB** (5 V). Sin power bank ni red.

**Verificación Paso 2 (multímetro, sin energía — Checklist Bloque A):** rieles `−` con
continuidad entre sí (P5); riel 3V3 y riel 5V **sin** continuidad entre ellos ni con GND
(aislación); cada riel continuo de extremo a extremo.

### Paso 3 — CHECKPOINT de seguridad (energizar en vacío)

> 🛑 **La primera energización es con la placa DESNUDA: solo el ESP32 y los rieles.** Los
> puentes de señal pre-cableados terminan en nodos aislados (los de LED en las cols 58–53;
> las puntas UART aparcadas en `A45`/`A46`): sin carga, no afectan la medición. No conectes
> FSR, LEDs ni DFPlayer hasta pasar este paso.

1. Conecta el ESP32 al PC por USB (esto **no necesita firmware**).
2. Con el multímetro en tensión, mide **en los propios rieles**:
   - **riel superior + ≈ 3.3 V** y **riel inferior + ≈ 4.6–5.0 V** (muchos DevKit meten
     VIN por un diodo Schottky → el riel de 5 V puede leer ~4.6–4.7 V; es normal).
3. 🛑 **Lo que NUNCA debe pasar:** el **riel superior + marcando ~5 V**. Significaría que
   el módulo está **girado** (3V3/5V invertidos) o que P1/P2 se cruzaron → **desconecta
   YA** y corrige la orientación / los waypoints antes de seguir.

**No avances si esta medición falla.** Es la única prueba que caza el error de orientación.

### Paso 4 — Sensores FSR (×6, uno por uno)

Topología por canal: `3V3 ─[FSR]─ nodo ─→ ADC ; nodo ─[10 kΩ]─ GND`.
Cada columna-nodo reúne **tres** conexiones en su grupo A–E: una pata de la **10 kΩ**, el
**FSR_bajo** (del botón) y el **jumper al ADC**. La **otra** pata de la 10 kΩ va al **riel
superior − (GND)** (no puede tener las dos patas en el mismo nodo: se anularía). El
**FSR_alto** va al **riel superior + (3V3)**, no al nodo.

Monta un canal completo, verifica su lectura, y repite los 6:

| Canal | Nodo (col) | 10 kΩ | FSR_bajo | Jumper nodo→ADC (Fila A) | ADC (pin) |
|---|---|---|---|---|---|
| FSR1 (B1) | **col 20** | nodo → riel superior − | del botón → nodo | → **A38** | VP/GPIO36 |
| FSR2 (B2) | **col 18** | nodo → riel superior − | del botón → nodo | → **A37** | VN/GPIO39 |
| FSR3 (B3) | **col 16** | nodo → riel superior − | del botón → nodo | → **A36** | GPIO34 |
| FSR4 (B4) | **col 14** | nodo → riel superior − | del botón → nodo | → **A35** | GPIO35 |
| FSR5 (B5) | **col 12** | nodo → riel superior − | del botón → nodo | → **A34** | GPIO32 |
| FSR6 (B6) | **col 10** | nodo → riel superior − | del botón → nodo | → **A33** | GPIO33 |

- Colores: **FSR_alto → naranja** (3V3), **FSR_bajo/nodo→ADC → azul**, **10 kΩ→riel** = la
  pata al riel superior − (GND, negro).
- **El FSR no tiene polaridad:** sus dos patas son iguales — elige una como "FSR_alto"
  (a 3V3) y otra como "FSR_bajo" (al nodo); **rotúlalas al soldar el arnés** para no
  confundirlas. **Trenza cada par** (alto+bajo) a lo largo de los ~25–30 cm (antirruido).
  *(Opcional: 100 nF del nodo a GND.)*
- **Calibra `cfg::UMBRAL_PISADA` en la puesta en marcha (no en el armado):** requiere el
  **firmware ya cargado** — observa la lectura ADC en el Serial en reposo y al pisar, edita
  `firmware/lib/GameCore/Config.h`, recompila y reflashea. Es un paso de **bring-up**, no de
  cableado (ver `flashing.md` y el skill `bring-up`).

**Verificación Paso 4:** cada FS_alto a **3V3** (nunca a 5 V); cada jumper al ADC correcto
(ojo: **VIN**=5 V en c25 ≠ **VN**=GPIO39/ADC en c37); lectura ADC cambia al pisar.

### Paso 5 — Driver ULN2803A (cols 50–58)

**El ULN2803A (DIP-18) se monta A CABALLO del canal central** (una hilera en Fila E, otra
en Fila F). Si lo montas en un solo lado, sus dos hileras se cortocircuitan. **Muesca
(notch) hacia la DERECHA** — la muesca es la hendidura semicircular en un extremo; el
**pin 1 = IN1** es el más cercano a ella (a veces con un punto) y queda en **`E58`**, para
que las **salidas queden en la Fila F** (mitad inferior, junto a los LEDs).

| Pin ULN | Señal | Hueco | Conexión |
|---|---|---|---|
| 1 | IN1 | **E58** | ← LED1 (ya pre-cableado, Paso 1.3) |
| 2 | IN2 | **E57** | ← LED2 (Paso 1.3) |
| 3 | IN3 | **E56** | ← LED3 (Paso 1.3) |
| 4 | IN4 | **E55** | ← LED4 (Paso 1.3) |
| 5 | IN5 | **E54** | ← LED5 (Paso 1.3) |
| 6 | IN6 | **E53** | ← LED6 (Paso 1.3) |
| 9 | GND | **E50** | → **riel superior −** (GND, negro) |
| 10 | COM | **F50** | → **riel inferior +** (5 V, rojo) |
| 18 | OUT1 | **F58** | → cátodo LED1 (baja a G–J, violeta) |
| 17 | OUT2 | **F57** | → cátodo LED2 |
| 16 | OUT3 | **F56** | → cátodo LED3 |
| 15 | OUT4 | **F55** | → cátodo LED4 |
| 14 | OUT5 | **F54** | → cátodo LED5 |
| 13 | OUT6 | **F53** | → cátodo LED6 |

*(IN7/IN8 = pines 7,8 y OUT7/OUT8 = pines 11,12 quedan sin usar.)*

**Verificación Paso 5:** ULN a caballo del canal, muesca a la derecha; **pin 9 (E50) a
riel superior −** y **pin 10 (F50) a riel inferior + (5 V)** — no los inviertas.

### Paso 6 — Grupos de LED (×6)

**Cómo se arma cada grupo (en la tapa):** un grupo = **3 LEDs blancos en paralelo**. En un
LED, la **pata larga es el ánodo (+)** y la corta (lado con el borde plano) es el **cátodo
(−)**. Une las **3 patas largas** → un solo hilo = **ánodo común**; une las **3 patas
cortas** → **cátodo común**. Rotula ambos hilos por botón (B1..B6). El **ánodo común** va a
la 110 Ω (a 5 V); el **cátodo común** a la salida OUTk del ULN.

Por grupo: `5V ─[110 Ω]─ ánodo` (cols 59–64) y `cátodo ─ OUTk del ULN` (cols 53–58):

| Grupo | 110 Ω (riel inferior + → ánodo) | Ánodo común (tapa) | Cátodo común (tapa) → OUT |
|---|---|---|---|
| LED1 | col **59** | → col 59 (amarillo) | → **col 58** (OUT1, violeta) |
| LED2 | col **60** | → col 60 | → **col 57** (OUT2) |
| LED3 | col **61** | → col 61 | → **col 56** (OUT3) |
| LED4 | col **62** | → col 62 | → **col 55** (OUT4) |
| LED5 | col **63** | → col 63 | → **col 54** (OUT5) |
| LED6 | col **64** | → col 64 | → **col 53** (OUT6) |

⚠️ **Cuidado con los 2 hilos de cada grupo:** el **ánodo** cae en cols 59–64 y el
**cátodo** en cols 53–58 (columnas no adyacentes). Rotula ambos por grupo (Bk) y sigue la
tabla fila por fila para no cruzarlos.

> **Brillo (actualizado 2026-07-11): los 6 grupos usan 110 Ω.** Con las **2.2 kΩ** originales
> cada LED recibía **~0.19 mA** y quedaba **demasiado tenue**, así que el autor las sustituyó
> por **110 Ω**. Según ngspice (`spice/grupo_led.cir`), cada grupo pasa a **10,1 mA** (**3,4 mA
> por LED**, ánodo a 3,89 V) — unos **61 mA** con los 6 grupos encendidos.
>
> **Sigue muy dentro de los límites del ULN2803A** (500 mA/canal de máximo absoluto;
> `datasheets/uln2803a.pdf`) y **no provoca brownout del DFPlayer**: verificado en hardware el
> 2026-07-11, los 3 modos × 3 niveles con audio, incluido Equilibrio n3 (4 grupos a la vez).
> El máximo del LED es **DESCONOCIDO** (no hay datasheet del LED en el repo), pero 3,4 mA está
> un orden de magnitud por debajo de los ~20 mA nominales de un LED de 5 mm corriente.
>
> ⚠️ **No cambies componentes con el circuito energizado.** Al sustituir estas resistencias con
> el USB conectado, el glitch de alimentación **colgó el DFPlayer**: enmudeció del todo y **no
> revivió con EN ni reseteando el ESP32** — hubo que **desconectar el USB** y volver a
> conectarlo (mismo modo de fallo que el brownout, §7). Desconecta antes de tocar el protoboard.
>
> ⚠️ **GPIO5 (LED2) es un strapping pin** (el ESP32 lo lee al encender para decidir cómo
> arranca; una carga puede alterarlo). Si tras cablear LED2 el ESP32 **no arranca**,
> reasigna **LED2 → GPIO22** (D22, Fila J **col 38**, libre y no strapping): (1) edita
> `Config.h` → `PIN_LED[1]` de `5` a `22`, (2) **recompila y reflashea**, (3) mueve la
> **toma del puente en el lado ESP32** de la col 32 a la **col 38** (ambas Fila J); el otro
> extremo del puente sigue en el nodo de IN2 (col 57).

**Verificación Paso 6:** polaridad de cada grupo (ánodo a 110 Ω/5 V en cols 59–64,
cátodo a OUT del ULN en cols 53–58); el ESP32 **sigue arrancando** tras cablear LED2.

### Paso 7 — DFPlayer Mini + parlante (cols 42–49)

El DFPlayer se monta **a caballo del canal** (cols 42–49), con la **columna izquierda
(VCC/RX/TX/GND/SPK) del lado de la Fila F** (mitad inferior, mundo 5 V) para que VCC y GND
caigan junto a los rieles inferiores. **Oriéntalo con VCC hacia la izquierda (col 42)**, de
modo que RX/TX queden frente a las puntas UART del ESP32 (acorta los puentes). **Conecta
cada pin por su etiqueta serigrafiada, no por su número de columna** — la tabla de abajo
dice a dónde va cada etiqueta y el pinout te dice cuál es cuál. Pinout confirmado de tu
placa (mirándola con el **Micro USB hacia abajo**):

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
| VCC (izq-1) | **riel inferior +** (5 V, rojo) |
| GND (izq-7) | **riel inferior −** (negro) |
| RX (izq-2) | ← **1 kΩ** en serie ← ESP32 **TX2/GPIO17** (punta pre-cableada de c31, Paso 1.3) *(marrón)* |
| TX (izq-3) | → ESP32 **RX2/GPIO16** (punta pre-cableada de c30) — **medir antes** (abajo) *(marrón)* |
| SPK_1 (izq-6) / SPK_2 (izq-8) | **parlante 4 Ω** (par diferencial: la señal va **entre** los dos hilos; **NO aterrizar** ninguno a GND; ojo: **GND (izq-7) va EN MEDIO**) |

- **Remata las dos puntas UART** que dejaste en el Paso 1.3: la de **c31 (GPIO17/TX2)** va
  al **RX** del DFPlayer **con la 1 kΩ en serie**; la de **c30 (GPIO16/RX2)** va al **TX**
  del DFPlayer. Convención: ESP32 **TX2(17) → RX** del módulo; ESP32 **RX2(16) ← TX**.
- **Desacople (cols 42–44, mitad inferior):** **1×** **100 µF / 16 V** entre VCC y GND
  (**pata `+` larga al VCC**, banda `−` a GND) **+ 1× 100 nF** ("104", sin polaridad).
  Añade además el **1000 µF / 16 V** entre los **rieles de 5 V** (`+` y `−`): es la reserva
  de carga del bus (BOM ítem 13).

> ⚠️ **Los caps NO son opcionales — verificado en banco (2026-07-11).** Sin ellos, el
> amplificador (parlante de 4 Ω) pide un pico que **hunde el riel de 5 V del USB**: el
> DFPlayer **se reinicia en bucle** en cuanto se le pide reproducir (repite `microSD
> ONLINE`), acaba **colgado** (`TimeOut`, y ya no revive con el botón EN: hay que **cortar
> la alimentación**) y **no suena nada**. Montados los tres caps, el módulo quedó estable
> (**0 reinicios**) y el parlante sonó. Para diagnosticar esto hay un firmware dedicado:
> `pio run -e esp32dev_audio -t upload` (prueba UART → microSD → reproducción y cuenta los
> reinicios).
- **microSD FAT32** con `/mp3/0001.mp3` … `/mp3/0004.mp3` (ver `audio/README.md`).

> ⚠️ **Protege el ESP32 — línea DFPlayer TX → GPIO16.** GPIO16 **no es 5V-tolerante**.
> Antes de conectar, **mide el nivel alto del TX del módulo**: si **~3.3 V** → directo; si
> **~5 V** → intercala un divisor: **1 kΩ en serie** desde el TX al nodo, **2 kΩ del nodo a
> GND**, y el **nodo → GPIO16** (da 5 V × 2k/(1k+2k) ≈ **3.33 V**).
>
> **Volumen moderado** (parlante de 4 Ω sobre puerto USB del PC); los caps de desacople
> absorben los picos del amplificador.

**Verificación Paso 7:** **TX del DFPlayer medido ≤ 3.3 V** antes de tocar GPIO16; VCC/GND
al riel inferior; caps con polaridad correcta; `audioOk` en el firmware.

### Paso 8 — Tapa y arneses

Baja los módulos bajo la tapa, **rotula cada arnés B1..B6** (§tabla de botones, abajo) y
rutéalos sin cruzar — un arnés cruzado hace que el juego lea/encienda la casilla
equivocada. Cada arnés Bk lleva **4 hilos**: FSR_alto, FSR_bajo, LED_ánodo común,
LED_cátodo común. Deja un **bucle de servicio** y pega el gráfico con una ventana sobre
cada botón.

**Mapa de botones (índice ↔ posición ↔ arnés):**

| Botón | Posición en la tapa | FSR (ADC) | Grupo LED (GPIO) | Arnés |
|---|---|---|---|---|
| 1 | superior izquierda | FSR1 · GPIO36 | LED1 · GPIO4 | **B1** |
| 2 | superior centro | FSR2 · GPIO39 | LED2 · GPIO5 | **B2** |
| 3 | superior derecha | FSR3 · GPIO34 | LED3 · GPIO18 | **B3** |
| 4 | inferior izquierda | FSR4 · GPIO35 | LED4 · GPIO19 | **B4** |
| 5 | inferior centro | FSR5 · GPIO32 | LED5 · GPIO21 | **B5** |
| 6 | inferior derecha | FSR6 · GPIO33 | LED6 · GPIO23 | **B6** |

---

## 4. Tablas de referencia (para consulta)

### 4.1 Mapa de pines del ESP32

**Header superior — Fila A (accesible directo, hacia arriba):**

| Col | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **VIN** | GND | D13 | D12 | D14 | D27 | D26 | D25 | D33 | D32 | D35 | D34 | **VN** | **VP** | EN |
| Uso | **5 V** | GND | — | — | — | — | — | — | FSR6 | FSR5 | FSR4 | FSR3 | FSR2 | FSR1 | — |

> ⚠️ **No confundas "VIN" con "VN":** **VIN** (col 25, esquina) es **5 V (potencia)**;
> **VN** (col 37, junto a VP/EN) es **GPIO39 = FSR2 (entrada ADC)**. Confundirlos mete 5 V
> a un ADC.

**Header inferior — Fila J (contra el borde inferior):**

| Col | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **3V3** | GND | D15 | D2 | **D4** | **RX2** | **TX2** | **D5** | **D18** | **D19** | **D21** | RX0 | TX0 | D22 | **D23** |
| Uso | 3V3 | GND | — | — | LED1 | DF-TX→ | DF←RX | LED2 | LED3 | LED4 | LED5 | — | — | (LED2 alt) | LED6 |

`RX2 = GPIO16`, `TX2 = GPIO17`. Convención DFPlayer: ESP32 **TX2(17) → RX** del módulo;
ESP32 **RX2(16) ← TX** del módulo.

**Mapa lógico (coincide con `firmware/lib/GameCore/Config.h`):**

| Señal | GPIO | Col (Fila) | Nodo/destino en zona libre |
|---|---|---|---|
| FSR1 | 36 (VP) | 38 (A) | nodo **col 20** |
| FSR2 | 39 (VN) | 37 (A) | nodo **col 18** |
| FSR3 | 34 | 36 (A) | nodo **col 16** |
| FSR4 | 35 | 35 (A) | nodo **col 14** |
| FSR5 | 32 | 34 (A) | nodo **col 12** |
| FSR6 | 33 | 33 (A) | nodo **col 10** |
| LED1 | 4 | 29 (J) | nodo de IN1 (**col 58**; el puente aterriza en **Fila A**, ver Paso 1.3) |
| LED2 | 5 | 32 (J) | nodo de IN2 (**col 57**; puente por Fila A, Paso 1.3) |
| LED3 | 18 | 33 (J) | nodo de IN3 (**col 56**; puente por Fila A, Paso 1.3) |
| LED4 | 19 | 34 (J) | nodo de IN4 (**col 55**; puente por Fila A, Paso 1.3) |
| LED5 | 21 | 35 (J) | nodo de IN5 (**col 54**; puente por Fila A, Paso 1.3) |
| LED6 | 23 | 39 (J) | nodo de IN6 (**col 53**; puente por Fila A, Paso 1.3) |
| DFPlayer RX2 (←TX) | 16 | 30 (J) | DFPlayer TX (por serigrafía) |
| DFPlayer TX2 (→RX) | 17 | 31 (J) | DFPlayer RX (por serigrafía, 1 kΩ serie) |

> Se usa **ADC1** para todos los FSR (ADC2 choca con el WiFi). Los GPIO 34–39 son **solo
> entrada** (perfectos para sensores). GPIO12 libre (no cablear).

### 4.2 Net list por subsistema

**Energía (rieles):**

| # | Bus | Desde | Waypoint | Hasta |
|---|---|---|---|---|
| P1 | 3V3 | ESP32 3V3 (`I25`, Fila J) | `F1` | Riel **superior +** |
| P4 | GND | ESP32 GND (`I26`, Fila J) | `F2` | Riel **superior −** |
| P2 | 5 V | ESP32 VIN (`A25`, Fila A) | `A64` | Riel **inferior +** |
| P3 | GND | ESP32 GND (`A26`, Fila A) | `A63` | Riel **inferior −** |
| P5 | GND común | Riel superior − | — | Riel inferior − (1 jumper, un extremo) |

- **Arquitectura de rieles:** superior + = **3V3** (desde la izquierda, col 1) · superior
  − = **GND** · inferior + = **5 V** (desde la derecha, col 64) · inferior − = **GND**.
- **NUNCA** se puentean los dos `+` (3V3 vs 5 V = cortocircuito). Los dos `−` sí (P5).
- Cap de bus: **1× 1000 µF / 16 V** entre riel inferior + y −.

**FSR (cols 8–20):** ver Paso 4. Topología `3V3 ─[FSR]─ nodo ─[10 kΩ]─ GND ; nodo → ADC`.
Nodos 20/18/16/14/12/10 → ADC A38/A37/A36/A35/A34/A33.

**ULN2803A + LEDs (cols 50–64):** ver Pasos 5–6. IN1..IN6 = E58..E53; OUT1..OUT6 =
F58..F53; GND(p9)=E50→sup −; COM(p10)=F50→inf +; 110 Ω (inf +) → ánodos cols 59–64;
cátodos → OUT en cols 58–53.

**DFPlayer (cols 42–49):** ver Paso 7. VCC→inf +, GND→inf −, RX←1 kΩ←GPIO17(c31),
TX→GPIO16(c30, medir ≤3.3 V), SPK1/SPK2→parlante 4 Ω, caps 100 µF+100 nF.

---

## 5. Checklist con multímetro

> El **Bloque A** se corre **cada vez** que vayas a energizar (placa sin corriente); el
> **Bloque B** es la medición inmediatamente **después** de dar corriente. La primera vez,
> Bloque B se hace en vacío (Paso 3) antes de conectar FSR/LEDs/DFPlayer.

### Bloque A — con la placa SIN energizar (multímetro en continuidad)

- [ ] Rieles `−` con continuidad entre sí y con GND del ESP32 (P5).
- [ ] Riel 3V3 (superior +) y riel 5V (inferior +) **sin** continuidad entre ellos ni con
      GND (aislación). Revisa los pares adyacentes `A64`/`A63` y `F1`/`F2`.
- [ ] Cada riel continuo de extremo a extremo (puentear si está partido).
- [ ] Ningún FSR a 5 V (solo a 3V3); ningún ADC a 5 V (ojo: **VIN**=5 V en c25 ≠
      **VN**=GPIO39/ADC en c37).
- [ ] ULN **a caballo del canal**, muesca a la derecha; pin 9 (E50) a **riel superior −**,
      pin 10 (F50) a **riel inferior + (5 V)**.
- [ ] LEDs: polaridad (ánodo a 110 Ω/5 V en cols 59–64, cátodo a OUT del ULN cols 53–58).
- [ ] Electrolíticos (1000 µF, 100 µF) con la **polaridad correcta** (banda `−` a GND).
- [ ] Nada en ADC2 / pines de WiFi. GPIO12 libre (no cablear).
- [ ] **DFPlayer TX medido ≤ 3.3 V** antes de conectarlo a GPIO16 (si 5 V → divisor).
- [ ] Arneses rotulados **B1..B6** sin cruzar. microSD FAT32 con los 4 MP3.

### Bloque B — recién energizada (multímetro en tensión, en los rieles)

- [ ] **Voltaje EN LOS RIELES tras energizar** (la prueba que caza el módulo girado):
      **riel superior + ≈ 3.3 V** y **riel inferior + ≈ 4.6–5.0 V** (muchos DevKit meten
      VIN por un diodo Schottky → el riel de 5 V puede leer ~4.6–4.7 V; es normal). Lo que
      **NUNCA** debe pasar: el **riel superior marcando ~5 V** → el ESP32 está girado o
      P1/P2 se cruzaron: **desconecta YA** y corrige (Paso 1.1 / Paso 2).
- [ ] Tras cablear LED2, el ESP32 **arranca** (GPIO5 es un *strapping pin*; si no arranca,
      LED2→GPIO22, ver Paso 6).

# Tapete Interactivo — Diseño del circuito y del prototipo físico

> **Documento de diseño (decisiones e intención).** El detalle operativo vive en:
> - **`materiales.md`** — inventario real + presupuesto (fuente única de materiales).
> - **`cableado.md`** — geometría del protoboard, net list, ruteo de la Fila J,
>   leyenda y checklist con multímetro (fuente única del armado).
> - **`flashing.md`** — flasheo del ESP32 y conexión del dashboard.
>
> Cruza con `firmware/lib/GameCore/Config.h` (mapa de pines).

## 1. Resumen del sistema

6 botones (FSR + 3 LEDs blancos c/u) sobre la tapa de una caja transparente; un
ESP32 al centro del piso corre la lógica y se comunica con el dashboard de PC.

| Subsistema | Componentes | Etapa |
|---|---|---|
| Sensado | 6× FSR 402 + 6× 10 kΩ (pull-down) | Divisores de voltaje, 3V3 |
| Iluminación | 18× LED blanco (6 grupos de 3) + 6× 2.2 kΩ + **1× ULN2803A** | Conmutación a 5 V |
| Audio | DFPlayer Mini + microSD + **parlante 4 Ω** | UART, 5 V |
| Cómputo/red | ESP32 DevKit 30 pines | — |
| Energía | **PC → ESP32 por USB** (5 V), regulador interno (3V3) | 4 rieles |

## 2. Decisiones congeladas (con el autor)

1. **LEDs con ULN2803A a 5 V**, un grupo de 3 en paralelo por botón, **2.2 kΩ** en
   serie. El brillo resultante es **tenue pero visible** (no hay resistencias de
   valor bajo para más corriente; es el máximo alcanzable con el inventario —
   decisión de no comprar más). Detalle en `cableado.md` §4.3 y `materiales.md` §3.
2. **DFPlayer con parlante 4 Ω** a SPK1/SPK2 (el amplificador del módulo lo maneja).
   El firmware degrada con gracia si el audio no inicializa (`audioOk_`).
3. **Alimentación: solo el PC al ESP32 por USB** (5 V). Sin power bank ni toma de
   red. Con LEDs tenues + volumen moderado, el puerto USB del PC alcanza.
4. **24 hilos** tapa→protoboard (4 por botón). Cables largos por **encadenado
   M-F + M-M soldado + termorretráctil**.
5. Caja transparente **40 × 28 × 13 cm**; protoboard al centro del piso; 6 botones
   en la tapa en cuadrícula **2×3**. Gráfico de la tapa **32.5 × 19.5 cm (horizontal)**.

## 3. Arquitectura de potencia — 4 rieles (anti-corto)

El principio que evita el cortocircuito: **el mundo 3V3 (sensores) vive en la mitad
superior y el mundo 5V (LEDs/audio) en la inferior**, separados por el canal central.

- Los **dos rieles `−`** se puentean entre sí (GND común).
- Los **dos `+` NUNCA** se puentean (uno es 3V3, otro 5V → corto).

El net list exacto de energía (P1–P5) y las columnas están en `cableado.md` §6.1.

## 4. Prototipo físico (caja + tapa)

### 4.1 Distribución de botones en la tapa
Cuadrícula **2×3** respetando `[1][2][3] / [4][5][6]`, sobre un área de gráfico de
**32.5 (ancho) × 19.5 (alto) cm**. Separación ~10 cm; hueco para el USB en una
pared lateral, alineado con el puerto del ESP32.

### 4.2 Módulo bajo-tapa por botón (construcción real con acrílico)
Para que la tapa no flexe y el FSR lea con precisión, la tapa se **rigidiza con dos
láminas de acrílico transparente** recortadas al calce (fotos en
`../evidencia/caja/tapa_con_refuerzo.jpeg` y `tapa_y_refuerzos.jpeg`). Sándwich, de
arriba hacia abajo:

1. **Lámina de acrílico superior** (superficie que se presiona, rígida).
2. **FSR 402** (sensor de pisada).
3. **Tapa plástica original** de la caja.
4. **Lámina de acrílico inferior**.
5. **Los 3 LEDs del botón**, ubicados **abajo del todo** (bajo el acrílico
   inferior), acomodados **alrededor del sensor**. Se hacen **huecos en las capas
   de plástico/acrílico** para que la luz del LED salga **directa**, sin tener que
   atravesar el material (esto compensa el brillo tenue).

El conjunto (acrílico superior → FSR → tapa plástica → acrílico inferior) debe
quedar **plano, rígido y firme**: así la pisada carga el FSR de forma uniforme y la
lectura es limpia. El **cableado de los FSR** sale por un **pequeño doblez hacia
abajo de las patas** del sensor, a través de huecos en la tapa y en la lámina
inferior, y baja organizado hacia el protoboard.

> Si aparecen falsos disparos o no registra, ajusta `cfg::UMBRAL_PISADA` viendo el
> Serial; un anillo de espuma perimetral da retorno elástico si hiciera falta.

### 4.3 Difusión / gráfico
La tapa es transparente y los LEDs son **blancos**. Como los LEDs se ven **directo
por los huecos**, no dependen de que el material sea translúcido. El gráfico que va
encima debe dejar una **ventana** sobre cada botón para que se vea el LED. Cada
ventana de color hace que el LED blanco encienda en ese tono (ver `grafico-tapete.svg`).

### 4.4 Cableado tapa→protoboard
24 hilos = 6 botones × 4 (FSR_alto, FSR_bajo, LED_ánodo común, LED_cátodo común).
Recorridos ~25–30 cm (los de esquina) → **encadenar M-F + M-M, soldar +
termorretráctil**. Etiquetar cada arnés B1..B6. Dejar **bucle de servicio** (~20 cm)
para levantar la tapa. Protoboard fijada al piso con doble faz / velcro.

> **Ruido en los FSR:** son entradas de alta impedancia a ~25–30 cm. **Trenza cada
> par de hilos FSR** (alto+bajo). El firmware ya filtra (umbral + antirrebote); si
> aún hay falsos, un cap 10–100 nF del nodo a GND lo limpia.

## 5. Armado y verificación

El **orden de armado** (rieles → energizar en vacío → FSR → ULN+LEDs → DFPlayer →
tapa) y el **checklist con multímetro** están en `cableado.md` §8 (checklist) y §9
(secuencia). La regla que
evita el corto: **3V3 y 5V nunca con continuidad entre sí ni a GND**; los dos rieles
`−` sí van unidos.

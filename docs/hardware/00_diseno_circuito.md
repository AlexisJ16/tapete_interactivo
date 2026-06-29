# Tapete Interactivo — Diseño del circuito y del prototipo físico

> **Documento maestro (fuente única de verdad).** Todos los planos
> (`plano-A-esquematico.svg`, `plano-A-protoboard.svg`, `plano-B-fisico.svg`,
> `grafico-tapete.svg`) y la guía Fritzing derivan de aquí. Si algo cambia, se
> cambia primero acá.
>
> Cruza con: `firmware/lib/GameCore/Config.h` (mapa de pines), `docs/wiring.md`
> (intención eléctrica), `docs/DiseñoProtoboard.html` (geometría del protoboard
> diseñada por el autor).

## 1. Resumen del sistema

6 botones (FSR + 3 LEDs blancos c/u) sobre la tapa de una caja transparente; un
ESP32 al centro del piso corre la lógica y se comunica con el dashboard de PC.

| Subsistema | Componentes | Etapa en el protoboard |
|---|---|---|
| Sensado | 6× FSR 402 + 6× 10 kΩ (pull-down) | Divisores de voltaje, 3V3 |
| Iluminación | 18× LED blanco (6 grupos de 3) + 6× 110 Ω + **1× ULN2803A** | Driver de corriente, 5V |
| Audio | DFPlayer Mini + microSD (sin parlante) | UART, 5V |
| Cómputo/red | ESP32 DevKit 30 pines | — |
| Energía | USB-C (5V), regulador interno (3V3) | 4 rieles |

## 2. Decisiones congeladas (con el autor)

1. **LEDs con ULN2803A** a 5 V (brillo pleno; los 6 GPIO entran directo al chip).
2. **DFPlayer se monta** aunque no haya parlante (el firmware lo detecta;
   degradación elegante si no).
3. **Alimentación solo por USB-C** (5 V desde el pin VIN). Techo ~500 mA, holgado.
4. **24 hilos** tapa→protoboard (arnés de 4 por botón). Cables largos por
   **encadenado M-F + M-M soldado + termorretráctil**.
5. Caja transparente **40 cm (ancho) × 28 cm (largo) × 13 cm (alto)**; protoboard
   al centro del piso; 6 botones en la tapa en cuadrícula **2×3**.

## 3. Mapa de pines (verificado contra el plano físico del autor)

El ESP32 DevKit (30 pines) está montado a caballo sobre el canal central,
ocupando las columnas ~24–38. **El header izquierdo se accede por la Fila A**
(arriba) y **el derecho por la Fila J** (abajo). Asignación columna→pin:

### Header izquierdo — Fila A (accesible directo)
| Col | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **VIN** | GND | D13 | D12 | D14 | D27 | D26 | D25 | D33 | D32 | D35 | D34 | **VN** | **VP** | EN |
| Uso | **5V** | GND | — | — | — | — | — | — | FSR6 | FSR5 | FSR4 | FSR3 | FSR2 | FSR1 | — |

> ⚠️ **El doble "VN" del plano:** el de la **col 24** (esquina, junto a GND) es
> **VIN = 5 V (potencia)**. El de la **col 36** (junto a VP/EN) es **GPIO39 =
> FSR2 (entrada ADC)**. Confundirlos mete 5 V a un ADC. En los planos van
> rotulados sin ambigüedad.

### Header derecho — Fila J (contra el borde; sale a columnas externas)
| Col | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pin | **3V3** | GND | D15 | D2 | **D4** | **RX2** | **TX2** | **D5** | **D18** | **D19** | **D21** | RX0 | TX0 | D22 | **D23** |
| Uso | **3V3** | GND | — | — | LED1 | DF-TX→ | DF←RX | LED2 | LED3 | LED4 | LED5 | — | — | — | LED6 |

`RX2 = GPIO16`, `TX2 = GPIO17`. Convención DFPlayer: ESP32 **TX2(17)→RX** del
módulo, ESP32 **RX2(16)←TX** del módulo.

## 4. Arquitectura de potencia — los 4 rieles (seguridad anti-corto)

| Riel | Bus | Se alimenta desde |
|---|---|---|
| Superior `−` | **GND** | ESP32 GND (Fila A, col 25) |
| Superior `+` | **3V3** | ESP32 3V3 (Fila J, col 24) → 1 jumper cruza al riel superior |
| Inferior `+` | **5V** | ESP32 VIN (Fila A, col 24) → 1 jumper cruza al riel inferior |
| Inferior `−` | **GND** | ESP32 GND (Fila J, col 25) |

**Reglas invariables:**
- Se **puentean los dos rieles `−`** entre sí (GND común): 1 jumper en un extremo.
- **NUNCA** se puentean los dos `+` (uno es 3V3, otro 5V → cortocircuito).
- El **mundo 3V3 vive en la mitad superior** (sensores); el **mundo 5V en la
  mitad inferior** (LEDs/audio). El canal central del protoboard los separa
  físicamente. Esa es la frontera que evita el corto.
- ⚠️ Muchos protoboards traen los rieles **partidos a la mitad**. Verifica con el
  multímetro la continuidad de cada riel de extremo a extremo; si está partido,
  puentea las dos mitades.

## 5. Net list completo (cada conexión)

### 5.1 Energía
| # | Desde | Hasta | Nota |
|---|---|---|---|
| P1 | ESP32 3V3 (J, c24) | Riel **superior +** | bus 3V3 |
| P2 | ESP32 VIN (A, c24) | Riel **inferior +** | bus 5V |
| P3 | ESP32 GND (A, c25) | Riel **superior −** | GND |
| P4 | ESP32 GND (J, c25) | Riel **inferior −** | GND |
| P5 | Riel **superior −** | Riel **inferior −** | puente GND común |

### 5.2 Sensores FSR (i = 1..6) — mitad superior, zona izquierda
Topología por canal: `3V3 ─[FSR]─┬─ ADC ; nodo ─[10kΩ]─ GND`.
El **nodo de unión** vive en una columna libre de la mitad superior izquierda.

| Canal | ADC (Fila A) | Nodo (col, mitad sup.) | 10 kΩ | FSR_alto | FSR_bajo |
|---|---|---|---|---|---|
| FSR1 | VP / GPIO36 (c37) | col 4 | nodo→riel sup. − | →riel sup. + (3V3) | →nodo |
| FSR2 | VN / GPIO39 (c36) | col 7 | nodo→riel sup. − | →riel sup. + | →nodo |
| FSR3 | D34 / GPIO34 (c35) | col 10 | nodo→riel sup. − | →riel sup. + | →nodo |
| FSR4 | D35 / GPIO35 (c34) | col 13 | nodo→riel sup. − | →riel sup. + | →nodo |
| FSR5 | D32 / GPIO32 (c33) | col 16 | nodo→riel sup. − | →riel sup. + | →nodo |
| FSR6 | D33 / GPIO33 (c32) | col 19 | nodo→riel sup. − | →riel sup. + | →nodo |

Por canal: 1 jumper nodo→ADC, 1 resistencia 10 kΩ nodo→GND, el cable
**FSR_alto** del tapete a 3V3 y el **FSR_bajo** del tapete al nodo. (6 nodos en
la mitad superior izquierda; sobra espacio.)

### 5.3 LEDs (k = 1..6) vía ULN2803A — mitad inferior, zona derecha
El ULN2803A se monta **a caballo sobre el canal central** en la zona derecha
(p. ej. cuerpo en columnas 44–52). Pines:

| Pin ULN | Función | Conexión |
|---|---|---|
| 1..6 (IN1..IN6) | entradas lógicas | ← GPIO LED (ver tabla) |
| 7, 8 | IN7, IN8 | sin uso |
| 9 | GND | → riel **inferior −** |
| 10 | COM | → riel **inferior +** (5V) — clamp de los diodos internos |
| 18,17,16,15,14,13 (OUT1..OUT6) | salidas (sink) | → cátodo de cada grupo |

Por grupo: `5V ─[110Ω]─ nodo_ánodo ─(LED_ánodo del tapete)` y
`LED_cátodo del tapete ─ nodo_cátodo ─ OUTk`.

| Grupo | GPIO (Fila J) | Entrada ULN | 110 Ω | Salida ULN |
|---|---|---|---|---|
| LED1 | D4 / GPIO4 (c28) | IN1 (pin 1) | 5V→ánodo1 | OUT1 (pin 18) |
| LED2 | D5 / GPIO5 (c31) | IN2 (pin 2) | 5V→ánodo2 | OUT2 (pin 17) |
| LED3 | D18 / GPIO18 (c32) | IN3 (pin 3) | 5V→ánodo3 | OUT3 (pin 16) |
| LED4 | D19 / GPIO19 (c33) | IN4 (pin 4) | 5V→ánodo4 | OUT4 (pin 15) |
| LED5 | D21 / GPIO21 (c34) | IN5 (pin 5) | 5V→ánodo5 | OUT5 (pin 14) |
| LED6 | D23 / GPIO23 (c38) | IN6 (pin 6) | 5V→ánodo6 | OUT6 (pin 13) |

> Los 3 LEDs de cada grupo van en **paralelo** (ánodos juntos, cátodos juntos)
> compartiendo un 110 Ω. **Cuenta realista** (el ULN es Darlington, cae
> V_CE(sat)≈0.8–1 V): corriente ≈ (5 − 0.9 − Vf) / 110. Con Vf≈2.9 V da ~4 mA
> por rama → tenue y algo disparejo (current-hogging entre LEDs en paralelo con un
> solo resistor). **Calíbralo con el multímetro**; 110 Ω es punto de partida.
>
> **Mejora de calidad (opcional, si el reloj lo permite):** un **resistor en serie
> por LED** (~100–150 Ω) soldado en el tapete (ánodo+resistor de los 3 → 5V;
> cátodos → OUT). Elimina el hogging, uniformiza el brillo y **saca los resistores
> del protoboard**. Mantiene los 24 hilos. Requiere comprar ~12–18 resistores más.
>
> ⚠️ **GPIO5 (LED2) es strapping pin.** La entrada del ULN (2.7 kΩ a base) puede
> dejar GPIO5 en zona indeterminada en el arranque. **Contingencia lista:** si tras
> cablear LED2 el ESP32 no arranca o arranca raro, reasigna **LED2 → GPIO22** (D22,
> col 37 del header derecho, libre y NO strapping): una línea en `Config.h`
> (`PIN_LED`) y mover un cable; no rompe el split derecho.

### 5.4 DFPlayer Mini — mitad inferior, zona izquierda
| Pin módulo | Conexión |
|---|---|
| VCC | riel **inferior +** (5V) |
| GND | riel **inferior −** |
| RX | ← **110 Ω** en serie ← ESP32 **TX2/GPIO17** (J, c30) |
| TX | → ESP32 **RX2/GPIO16** (J, c29) |
| SPK1 / SPK2 | sin conexión (no hay parlante) |

microSD FAT32 con `/mp3/0001.mp3` … `/mp3/0004.mp3` (ver `audio/README.md`).

> ⚠️ **Protege tu único ESP32 — línea DFPlayer TX → RX2/GPIO16.** GPIO16 **no es
> 5V-tolerante** y el módulo va a 5 V. La mayoría de DFPlayer emiten TX a 3.3 V
> (seguro), pero los clones varían. **Antes de conectar a GPIO16, mide con el
> multímetro el nivel alto de TX del módulo:** si ~3.3 V → directo; si ~5 V →
> intercala un divisor (o alimenta el DFPlayer desde 3V3, aunque a 5 V inicializa
> más fiable). El 110 Ω que ya pusimos está en la otra línea (ESP32 TX→RX), que no
> es la de riesgo.

## 6. Zonificación del protoboard (resumen visual)

```
 RIEL SUP −  (GND) ═══════════════════════════════════════════════════
 RIEL SUP +  (3V3) ═══════════════════════════════════════════════════
 Filas A–E   │ FSR1..FSR6 (divisores)  │   ESP32   │ (libre / ULN out) │
   (sup.)    │  cols 4..19 — IZQUIERDA  │ cols24-38 │   cols 44+ DER.   │
 ─ ─ ─ ─ ─ canal central ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
 Filas F–J   │ DFPlayer (cols 4..14)    │ ESP32 J   │ ULN2803 + LEDs    │
   (inf.)    │      IZQUIERDA           │           │  cols 44+ DER.    │
 RIEL INF +  (5V)  ═══════════════════════════════════════════════════
 RIEL INF −  (GND) ═══════════════════════════════════════════════════
```

- **Superior-izquierda:** 6 divisores FSR (3V3/GND de los rieles superiores).
- **Inferior-izquierda:** DFPlayer (5V/GND inferiores).
- **Derecha (cruza canal):** ULN2803 + 6 grupos LED (5V/GND inferiores).
- **Centro:** ESP32. Power entry junto a las cols 24–25.

## 7. Prototipo físico (caja + tapa)

### 7.1 Distribución de botones en la tapa (40×28)
Cuadrícula 2×3 respetando `[1][2][3] / [4][5][6]`:

| Botón | x (cm) | y (cm) |
|---|---|---|
| 1 | 10 | 19 | 2 | 20 | 19 | 3 | 30 | 19 |
| 4 | 10 | 9  | 5 | 20 | 9  | 6 | 30 | 9  |

Separación ~10 cm, márgenes ~9–10 cm. Hueco para USB-C en una pared lateral,
alineado con el puerto del ESP32.

### 7.2 Módulo bajo-tapa por botón (que la tapa no flexe y el FSR lea bien)
Sándwich, de arriba hacia abajo:
1. **Tapa-botón rígida** sobre la tapa (disco de acrílico/cartón con el gráfico)
   — localiza el dedo y evita flexión despareja.
2. **Tapa transparente** (superficie que se presiona).
3. **Anillo de espuma** (EVA / cinta doble faz de espuma, ~1–2 mm) al perímetro
   — retorno elástico, evita disparos falsos.
4. **Disco concentrador (puck)** ~8–10 mm centrado sobre el domo del FSR
   (moneda, recorte de acrílico, tapa de botella) — enfoca la fuerza.
5. **FSR 402** (cara arriba) pegado por su reverso a…
6. **Base rígida** ~3×3 cm (acrílico/PVC/MDF/baquela) — impide que el FSR flexe.

La base se fija bajo la tapa por el anillo de espuma. Al presionar, el puck
carga el FSR contra la base → lectura limpia. Si hay falsos/no-registra, fija la
base a un marco/standoff y calibra `cfg::UMBRAL_PISADA` viendo el Serial.

### 7.3 Difusión / gráfico
La tapa es transparente y los LEDs son **blancos**. El gráfico que va encima
debe ser **translúcido** o tener **ventanas difusoras** sobre cada botón; si es
opaco, el LED no se ve. Cada ventana de color hace que el LED blanco encienda en
ese tono (ver `grafico-tapete.svg` y §9).

### 7.4 Cableado tapa→protoboard
24 hilos = 6 botones × 4 (FSR_alto, FSR_bajo, LED_ánodo común, LED_cátodo común).
Recorridos ~25–30 cm (los de esquina) → **encadenar M-F + M-M, soldar +
termorretráctil**. Etiquetar cada arnés B1..B6. Dejar **bucle de servicio**
(~20 cm) para levantar la tapa y trabajar dentro. Protoboard fijada al piso con
cinta doble faz / velcro.

> **Ruido en los FSR:** son entradas de alta impedancia a ~25–30 cm. **Trenza cada
> par de hilos FSR** (alto+bajo) para inmunizar; el firmware ya filtra (umbral +
> antirrebote). Si aún hay falsos, un cap 10–100 nF del nodo a GND lo limpia.

## 8. Secuencia de armado (orden seguro)

1. **Rieles primero.** Montar P1–P5. Con el multímetro: continuidad de cada riel
   de extremo a extremo; **3V3 y 5V SIN continuidad entre sí ni a GND**; los dos
   GND unidos.
2. **Energizar en vacío** (solo ESP32, sin nada más): medir **VIN→GND ≈ 4.7–5 V**
   y **3V3→GND ≈ 3.3 V**. Confirmar que el ESP32 arranca (Serial 115200).
3. **FSR uno por uno.** Montar un divisor; en el Serial ver la lectura ADC en
   reposo (~baja) y al presionar (sube). Ajustar umbral. Repetir los 6.
4. **ULN + LEDs por grupo.** Montar ULN (GND pin9, COM pin10→5V). Un grupo:
   110Ω, ánodo, cátodo→OUT, IN←GPIO. Probar encendido desde el firmware/dashboard.
   Repetir los 6. *(GPIO5 es strapping pin: confirmar que el ESP32 sigue
   arrancando tras cablear LED2.)*
5. **DFPlayer.** VCC/GND, TX2→(110Ω)→RX, RX2←TX, microSD. Verificar `audioOk`.
6. **Tapa.** Montar módulos bajo-tapa, rutear arneses, pegar gráfico.

## 9. Checklist de verificación con multímetro (ANTES de energizar cada vez)

- [ ] Rieles `−` con continuidad entre sí y con GND del ESP32.
- [ ] Riel 3V3 y riel 5V **sin** continuidad entre ellos ni con GND.
- [ ] Cada riel continuo de extremo a extremo (puentear si está partido).
- [ ] Ningún FSR conectado a 5V (solo a 3V3); ningún ADC a 5V (¡el doble "VN"!).
- [ ] ULN: pin 9 a GND, pin 10 a 5V, orientación (muesca) correcta.
- [ ] LEDs: polaridad (ánodo a 110Ω/5V, cátodo a OUT del ULN).
- [ ] Nada en ADC2 / pines de WiFi. GPIO12 libre (no cablear).
- [ ] **DFPlayer TX medido ≤3.3 V** antes de conectarlo a GPIO16 (si 5 V → divisor).
- [ ] Tras cablear LED2, el ESP32 **arranca** (GPIO5 strapping; si no, LED2→GPIO22).
- [ ] microSD FAT32 con `/mp3/0001.mp3`…`/mp3/0004.mp3`.

## 10. Materiales (estado)

En mano: ESP32, 6× FSR402, 6× 10 kΩ, 18× LED blanco, 10× 110 Ω, DFPlayer + microSD,
protoboard, Dupont M-M y M-F, USB-C, soldador/estaño/termorretráctil.
**Comprar:** 1× **ULN2803A** (driver LED). Opcional: parlante 8Ω/3W (audio real).

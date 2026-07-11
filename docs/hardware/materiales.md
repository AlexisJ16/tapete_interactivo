# Materiales del Tapete Interactivo — inventario y presupuesto

> **Fuente única de verdad de los materiales.** Cualquier otro documento que
> mencione componentes o cantidades se refiere a esta lista. Validada contra el
> inventario físico real (foto `../evidencia/caja/materiales_completos.jpeg`,
> 2026-07-01).

## 1. Lista de componentes (BOM)

| # | Componente | Especificación | Cant. | Origen | Destino en el circuito |
|---|---|---|---|---|---|
| 1 | Módulo ESP32 | DevKit 30 pines (WiFi+BT) | 1 | en mano | Cómputo, red (TCP/serial), PWM de LEDs, ADC de FSR |
| 2 | Sensor FSR | Interlink FSR 402 | 6 | en mano | Un botón cada uno (pisada) |
| 3 | LED blanco | 5 mm through-hole difuso | 18 | en mano | 3 por botón (6 grupos de 3) |
| 4 | DFPlayer Mini | Módulo MP3 (amplificador integrado) | 1 | en mano | Audio |
| 5 | microSD | 2 GB, FAT32 | 1 | en mano | Audios `/mp3/000X.mp3` del DFPlayer |
| 6 | Driver de LEDs | **ULN2803APG** (Toshiba, DIP-18) | 1 | comprado | Conmuta los 6 grupos de LED a 5 V |
| 7 | Parlante | **4 Ω / 3 W** | 1 | comprado | A SPK1/SPK2 del DFPlayer |
| 8 | Protoboard | 830 puntos | 1 | en mano | Montaje |
| **Resistencias** | | | | | |
| 9 | R 10 kΩ | 1/4 W | 8 | en mano | 6 pull-down de FSR + 2 reserva |
| 10 | R 1 kΩ | 1/4 W | 2 | comprado | 1 línea serie DFPlayer + 1 divisor GPIO16 |
| 11 | R 2 kΩ | 1/4 W | 3 | comprado | Divisor GPIO16 (contingencia) + reserva |
| 12 | R 2.2 kΩ | 1/4 W | 9 | comprado | ~~6× serie de grupo LED~~ → **sustituidas el 2026-07-11** (brillo muy tenue). Hoy: **reserva** |
| 12b | **R 110 Ω** | 1/4 W | 6 en uso | añadido por el autor (2026-07-11) | **6× serie de grupo LED** (1 por grupo). Cantidad total en inventario: **no registrada** |
| **Capacitores** | | | | | |
| 13 | Electrolítico | 1000 µF / 16 V | 2 | comprado | Desacople del bus de 5 V |
| 14 | Electrolítico | 100 µF / 16 V | 2 | comprado | Desacople VCC del DFPlayer |
| 15 | Cerámico | 100 nF ("104") | 5 | comprado | Filtrado HF + antirruido de FSR |
| **Cableado y consumibles** | | | | | |
| 16 | Cables Dupont | M-M y M-H | varios | en mano | Jumpers y arneses |
| 17 | Cable de cobre | hilo suelto | de sobra | comprado | Puentes laterales de la Fila J |
| 18 | Cable USB | del PC al ESP32 (datos) | 1 | en mano | Alimentación + programación |
| 19 | Soldadura | soldador, estaño, termorretráctil | — | en mano | Arneses de la tapa |
| **Mecánico (caja)** | | | | | |
| 20 | Caja transparente | plástico, 40 × 28 × 13 cm | 1 | en mano | Enclosure |
| 21 | Láminas de acrílico | recortadas al calce de la tapa | 2 | comprado | Refuerzo/rigidez de la tapa (sándwich) |
| 22 | Gráfico de la tapa | impresión, 32.5 × 19.5 cm | 1 | pendiente | Arte de los 6 botones |

## 2. Presupuesto (a completar con los costos reales)

Rellena `Costo unit.` y `Costo total` con lo que pagaste. Los ítems "en mano"
(ya los tenías) pueden ir en 0 o con su costo previo, según cómo quieras
presentar el presupuesto.

| Ítem | Cant. | Origen | Costo unit. | Costo total |
|---|---|---|---|---|
| Módulo ESP32 DevKit 30 pines | 1 | en mano | | |
| Sensor FSR 402 | 6 | en mano | | |
| LED blanco 5 mm | 18 | en mano | | |
| DFPlayer Mini | 1 | en mano | | |
| microSD 2 GB | 1 | en mano | | |
| ULN2803APG | 1 | comprado | | |
| Parlante 4 Ω / 3 W | 1 | comprado | | |
| Protoboard 830 pts | 1 | en mano | | |
| Resistencia 10 kΩ | 8 | en mano | | |
| Resistencia 1 kΩ | 2 | comprado | | |
| Resistencia 2 kΩ | 3 | comprado | | |
| Resistencia 2.2 kΩ | 9 | comprado | | sustituidas en los grupos LED (2026-07-11) |
| **Resistencia 110 Ω** | 6 en uso | añadido por el autor | | serie de los 6 grupos LED |
| Cap. electrolítico 1000 µF 16 V | 2 | comprado | | |
| Cap. electrolítico 100 µF 16 V | 2 | comprado | | |
| Cap. cerámico 100 nF | 5 | comprado | | |
| Cables Dupont + cobre | — | mixto | | |
| Caja transparente 40×28×13 | 1 | en mano | | |
| Láminas de acrílico | 2 | comprado | | |
| Impresión del gráfico | 1 | pendiente | | |
| **TOTAL** | | | | |

## 3. Notas técnicas del inventario

- **Parlante 4 Ω / 3 W:** el DFPlayer Mini soporta 4 Ω u 8 Ω hasta 3 W. Con 4 Ω
  los picos de corriente son mayores → **volumen moderado**; los capacitores de
  desacople absorben esos picos.
- **Resistencias — asignación real:**
  - **6 × 10 kΩ** → pull-down de los 6 FSR (crítico); 2 × 10 kΩ de reserva.
  - **1 kΩ** → resistencia en serie de la línea DFPlayer `TX2 → RX`.
  - **1 kΩ + 2 kΩ** → divisor de tensión para `DFPlayer TX → GPIO16`, **solo si**
    el TX del módulo mide 5 V (medir con multímetro; la mayoría emite 3.3 V).
  - **6 × 110 Ω** → serie de los 6 grupos LED (1 por grupo). Las **9 × 2.2 kΩ** quedan de
    reserva.
- **Brillo de los LEDs — resuelto el 2026-07-11 (ya no es un límite aceptado).** El diseño
  original usaba **2.2 kΩ** (lo que había en el inventario): **<1 mA por LED**, un brillo
  demasiado tenue. El autor las sustituyó por **110 Ω**, con lo que cada grupo pide **10,1 mA**
  y cada LED **3,4 mA** (ngspice, `spice/grupo_led.cir`). Los 6 grupos suman **~61 mA**, muy
  dentro de los límites del ULN2803A (500 mA/canal de máximo absoluto) y **sin perturbar al
  DFPlayer** (verificado: 3 modos × 3 niveles con audio). El máximo del LED es **DESCONOCIDO**
  (no hay datasheet del LED en el repo). Ver `cableado.md` §3 (Paso 6).
- **Energía:** única fuente = **el PC al ESP32 por cable USB** (5 V). No se usa
  power bank ni toma de red. Con los 6 grupos de LED (~61 mA) y `VOLUMEN_AUDIO = 15`, el
  puerto USB del PC alcanza para todo el circuito — verificado en hardware.
- **No se compró** ESP32 ni ULN de repuesto (presupuesto).

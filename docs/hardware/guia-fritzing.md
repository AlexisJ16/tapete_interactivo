# Guía para replicar el protoboard en Fritzing

El SVG `plano-A-protoboard.svg` ya es preciso. Esta guía es para que, **opcionalmente**,
rehagas esa vista en **Fritzing** y obtengas el dibujo "realista" reconocido en
sustentaciones de ingeniería. El net list es el de `00_diseno_circuito.md` §5.

## 1. Instalar y preparar partes

- Descarga Fritzing (gratis): <https://fritzing.org/download/> (o `sudo apt install fritzing`).
- Vista a usar: **Protoboard** (la pestaña "Breadboard").
- Partes que **no** vienen por defecto — impórtalas (menú *Archivo → Abrir* el `.fzpz`):
  - **ESP32 DevKit 30 pines**: busca "ESP32 DevKitC" o "ESP32 DevKit v1" en el
    foro de Fritzing (parts) e importa el `.fzpz`.
  - **DFPlayer Mini**: hay `.fzpz` en el foro/GitHub ("DFPlayer Mini Fritzing part").
- Partes del **core** (panel derecho, ya incluidas):
  - **Full+ breadboard** (la protoboard grande).
  - **Force Sensitive Resistor** (FSR) ×6.
  - **LED** (5 mm) ×18 y **Resistor** ×(6×10k + 6×110 + 1×110 DFPlayer).
  - **IC** genérico de **18 pines (DIP)** para el **ULN2803A** (renómbralo en
    *Inspector → label* = "ULN2803A"; si encuentras el part exacto, mejor).

## 2. Colocar (sigue `plano-A-protoboard.svg`)

1. Pon la **protoboard Full+** y, encima, el **ESP32** a caballo del canal central
   (queda en las columnas centrales; header izquierdo arriba = Fila A, derecho
   abajo = Fila J — igual que en tu `DiseñoProtoboard.html`).
2. **Rieles:** asigna mentalmente *sup−=GND, sup+=3V3, inf+=5V, inf−=GND*. En
   Fritzing usa color de cable: **negro=GND, naranja=3V3, rojo=5V**.
3. **ULN2803A** (IC 18 pines) a la **derecha**, cruzando el canal. Orienta la
   muesca para identificar el pin 1.
4. **DFPlayer** en la zona **inferior izquierda**.
5. **6 FSR** + 6×**10 kΩ** en la zona **superior izquierda** (divisores).
6. **18 LED** en 6 grupos + 6×**110 Ω** a la **derecha**, hacia el ULN.

## 3. Cablear (net list resumido — detalle en §5 del doc maestro)

| Conexión | Color de cable en Fritzing |
|---|---|
| 3V3 (pin J col24) → riel +3V3; FSR_alto → +3V3 | naranja |
| VIN (pin A col24) → riel +5V; 110Ω LED → +5V; ULN COM, DFPlayer VCC → +5V | rojo |
| GND ×2 → rieles −; puente entre los dos − | negro |
| FSR: 3V3─FSR─nodo─ADC ; nodo─10kΩ─GND | azul (señal) |
| GPIO 4,5,18,19,21,23 → ULN IN1..IN6 | verde |
| ULN OUT1..6 → cátodo de cada grupo; 5V─110Ω─ánodo | violeta |
| ESP32 TX2/17 ─(110Ω)→ DFPlayer RX ; DFPlayer TX → RX2/16 | marrón |

> **Pin-pairing del ULN2803A:** IN1=pin1↔OUT1=pin18, IN2=pin2↔OUT2=pin17, …,
> IN6=pin6↔OUT6=pin13. GND=pin9, COM=pin10.

## 4. Limpieza y exportación

- *Routing → "Autorouter/Cleanup"* solo para ordenar; revisa a mano.
- Activa colores por net y evita cruces innecesarios.
- Exporta para la tesis: *Archivo → Exportar → como Imagen → PDF / SVG / PNG*
  (PDF/SVG = vectorial, nítido a cualquier tamaño).

## 5. Verificación

Antes de dar por buena la vista, contrasta cada cable contra la tabla §5 del
documento maestro y contra `plano-A-protoboard.svg`. Deben coincidir 1:1.

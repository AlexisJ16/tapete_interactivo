# Diseño: reescritura de `docs/hardware/cableado.md` como guía paso-a-paso hueco-por-hueco

**Fecha:** 2026-07-03. **Estado:** energía + GND común APROBADOS por el usuario; estructura
pendiente de su review. Andamiaje (se purga del snapshot de entrega, como el resto de
`docs/superpowers/`).

## Objetivo

Reescribir `docs/hardware/cableado.md` para que sea **máximamente clara, paso a paso, con
coordenadas exactas y sin ambigüedad ni libertad**, para un **armador primerizo**. El enfoque
es una **lista de armado hueco por hueco**: qué componente, en qué huecos, cada puente de dónde
a dónde. Incorpora el nuevo esquema de energía.

## Principio rector (ANTI-ERROR — no negociable)

1. **NO se cambia la topología validada.** Las coordenadas de **FSR, ULN2803A, LEDs y DFPlayer**
   se **preservan VERBATIM** del `cableado.md` actual (fuente de verdad en disco, ya validada:
   coteo vs `Config.h`, 2× `circuit-reviewer`, datasheets ULN/DFPlayer, re-derivación geométrica).
   Al reescribir se **re-leen del disco**, nunca de memoria del chat.
2. **Fuente de pines canónica:** `firmware/lib/GameCore/Config.h`
   (`PIN_FSR={36,39,34,35,32,33}`, `PIN_LED={4,5,18,19,21,23}`, TX=17, RX=16). Si algo discrepa,
   se DETIENE y concilia; no se improvisa.
3. **Único cambio de topología:** el esquema de energía (P1–P5), abajo.
4. Todo lo demás es **re-presentación** (misma información, mejor organizada). Prohibido inventar
   un pin, columna, valor o coordenada que no esté en las fuentes de verdad.

## Esquema de energía NUEVO (APROBADO 2026-07-03)

Coordenadas `FilaColumna` (p. ej. `A25` = Fila A, columna 25). Cada conexión = **2 puentes**:
pin → columna extrema (waypoint) → riel. Reemplaza el antiguo cruce de la columna 25.

| # | Bus | Puente 1 (pin → waypoint) | Puente 2 (waypoint → riel) |
|---|---|---|---|
| **P1** | 3V3 | `I25` → `F1` (col 1, mitad inferior) | `F1` → **riel superior +** |
| **P4** | GND | `I26` → `F2` (col 2, mitad inferior) | `F2` → **riel superior −** |
| **P2** | 5 V | `A25` → `A64` (col 64, mitad superior) | `A64` → **riel inferior +** |
| **P3** | GND | `A26` → `A63` (col 63, mitad superior) | `A63` → **riel inferior −** |
| **P5** | GND común | puente **riel superior − ↔ riel inferior −** (1 puente, un extremo) | — |

**Precisiones (obligatorias, hacen esto seguro):**
- `J25` (3V3) y `J26` (GND) están en la **Fila J ocupada** → se toman por `I25`/`I26` (bajo el
  módulo, mismo nodo eléctrico) → **pre-cablear antes de asentar el ESP32**. `A25`/`A26` (Fila A
  libre) son directos.
- **Waypoints:** izquierda en la **mitad INFERIOR** (`F1`,`F2`, libres); derecha en la **mitad
  SUPERIOR** (`A64`,`A63`). **El 5V NUNCA en la mitad inferior de col 64:** ahí está el ánodo de
  LED6 y le saltaría la resistencia de 2.2 kΩ (lo quemaría).
- **Orientación del ESP32 sigue siendo crítica:** `A25`=5V, `J25`=3V3. Si el módulo se gira, el
  5V iría al riel de 3V3. La medición de rieles en vacío lo caza.
- **Gana:** 3V3 aislado a la izquierda, 5V a la derecha; **el cruce de la columna 25 desaparece**;
  los dos rieles `+` nunca se tocan (superior+=3V3 desde col 1, inferior+=5V desde col 64).
- El resto (FSR, ULN, LEDs, DFPlayer) **no cambia**: solo cambia cómo se alimentan los rieles.

## Coordenadas PRESERVADAS (re-leer del `cableado.md` actual — NO re-derivar)

Del `cableado.md` actual en disco (secciones a preservar verbatim):
- **ESP32 pinout:** tablas header superior (Fila A) / header inferior (Fila J) + "Mapa lógico".
  Orientación (USB izq, VIN=col25 sup, 3V3=col25 inf) + confirmar Fila A libre.
- **FSR (×6):** nodos cols **20/18/16/14/12/10**; jumper a ADC **A38/A37/A36/A35/A34/A33**;
  10 kΩ nodo→riel superior − (GND); FSR_alto→riel superior + (3V3). Topología `3V3─FSR─nodo─10k─GND`.
- **ULN2803A:** a caballo del canal, **muesca a la DERECHA** (pin1=IN1 en **E58**); IN1..IN6 =
  **E58,E57,E56,E55,E54,E53**; OUT1..OUT6 = **F58,F57,F56,F55,F54,F53**; GND(p9)=**E50**→riel
  superior −; COM(p10)=**F50**→riel inferior + (5V). IN_k ← GPIO LED_k por puente lateral.
- **Puentes GPIO→IN del ULN (Fila J → E):** LED1 c29→E58, LED2 c32→E57, LED3 c33→E56,
  LED4 c34→E55, LED5 c35→E54, LED6 c39→E53. (GPIO5=LED2 strapping → contingencia GPIO22/col38.)
- **LEDs (×6 grupos):** 2.2 kΩ de riel inferior + a ánodo en cols **59,60,61,62,63,64**;
  cátodo común → OUT_k en cols **58,57,56,55,54,53**.
- **DFPlayer (cols 42–49):** pinout de la placa (Micro USB abajo; col izq VCC/RX/TX/DAC_R/DAC_L/
  SPK1/GND/SPK2). VCC→riel inferior +, GND→riel inferior −, RX←1 kΩ←GPIO17 (c31), TX→GPIO16 (c30,
  medir ≤3.3V antes), SPK1/SPK2→parlante 4Ω. Caps 100µF+100nF VCC↔GND.
- **Cap de bus:** 1000 µF entre riel inferior + y −.
- Valores/BOM: `materiales.md`. Corrientes: `spice/`.

## Estructura del documento reescrito (para review del usuario)

0. **Encabezado:** qué es, fuente de verdad, disposición 2×3 de botones.
1. **Antes de empezar (léelo primero):**
   - Cómo funciona el protoboard (columna A–E = 1 nodo, F–J = otro, canal separa, rieles
     horizontales). Sistema de coordenadas `FilaColumna`.
   - Leyenda de colores de cable.
   - Los peligros que fríen (orientación ESP32 / rieles + separados / 5V a ADC) — resumen corto.
2. **Mapa general de zonas** (un plano ASCII: qué bloque va en qué columnas):
   FSR 8–20 · USB 21 · ESP32 22–41 · DFPlayer 42–49 · ULN 50–58 · LEDs 59–64 · energía en extremos.
3. **Armado PASO A PASO (hueco por hueco), en orden seguro** — cada paso = micro-instrucciones
   numeradas con coordenadas exactas + color de cable + verificación:
   - **Paso 1 — ESP32:** orientar (USB izq), confirmar Fila A libre, pre-cablear los puentes de la
     Fila J (P1/P4 + los 6 IN de LED + DFPlayer TX/RX) por F–I, asentar.
   - **Paso 2 — Rieles de energía:** P1–P5 con las coordenadas exactas de arriba.
   - **Paso 3 — CHECKPOINT de seguridad:** energizar en vacío (solo ESP32) + medir rieles
     (sup+≈3.3V, inf+≈4.6–5.0V; sup+ nunca ~5V). No seguir si falla.
   - **Paso 4 — Sensores FSR (×6, uno por uno):** por canal, hueco por hueco (nodo, 10 kΩ,
     FSR_alto, jumper a ADC). Calibrar UMBRAL_PISADA (ver `flashing.md`).
   - **Paso 5 — Driver ULN2803A:** colocación (muesca derecha), GND/COM, IN por puentes, OUT.
   - **Paso 6 — Grupos de LED (×6):** 2.2 kΩ, ánodo/cátodo por grupo (armado del arnés + polaridad).
   - **Paso 7 — DFPlayer + parlante:** VCC/GND, UART (1 kΩ, medir TX), caps, SPK, microSD.
   - **Paso 8 — Tapa y arneses:** B1–B6, bucle de servicio, gráfico.
4. **Tablas de referencia** (para consulta): mapa de pines completo + net list por subsistema.
5. **Checklist con multímetro:** Bloque A (sin energía) / Bloque B (energizada).

## Verificación post-reescritura (obligatoria antes de cerrar)

1. `circuit-reviewer`: coteo pin/columna del doc reescrito vs `Config.h` → **sin regresiones**;
   + verificar que el nuevo esquema de energía no crea cruce 3V3↔5V.
2. Lente primerizo: ¿seguible sin ambigüedad? ¿algún paso atasca?
3. Verificar refs a archivos (`flashing.md`, `spice/`, `audio/README.md`, `materiales.md`).
4. Advisor de cierre. Commit.

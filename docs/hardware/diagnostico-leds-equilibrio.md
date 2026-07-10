# Diagnóstico — LEDs "de más" en el modo Equilibrio

## Qué se observó y qué se descartó

En el modo Equilibrio (varios LEDs simultáneos) el **tapete físico** enciende más
LEDs de los que corresponden al patrón, mientras la **pantalla del dashboard** muestra
solo los correctos.

Esto localiza la falla **por debajo de GameCore**, en la capa eléctrica:

- GameCore emite un único flujo de eventos `led` que alimenta **igual** a la pantalla y
  al hardware (`GameEngine::led` → `hw.setLed()` + evento al dashboard). Reproducido en el
  simulador (mismo `GameCore.so`), el modo Equilibrio enciende **exactamente k** LEDs por
  patrón (2/3/4 según nivel) y ni uno más. Si la pantalla está bien, la lógica está bien.
- El mapeo LEDC de `EspHardware::setLed` es correcto: un canal PWM por casilla
  (`canal = celda-1`), un pin por canal, misma frecuencia/resolución. Compartir *timer*
  entre canales no comparte *duty*, así que un canal no enciende a otro.

Conclusión: es **eléctrico** (cableado, driver o alimentación), no firmware. El síntoma
aparece solo en Equilibrio porque es el único modo con varios LEDs a la vez.

## Fuente de verdad de pines (no se improvisa)

`firmware/lib/GameCore/Config.h`:

```
PIN_LED[celda-1] = { 4, 5, 18, 19, 21, 23 }   // celdas 1..6
```

Cableado y ruteo del driver: `docs/hardware/cableado.md`. Si un pin real no coincide con
`Config.h`, se corrige el **cableado** para casar con `Config.h` (fuente de verdad); no se
cambia el pinout "de memoria".

## Procedimiento (multímetro + PC; el humano flashea)

Firmware normal (`esp32dev`), dashboard por serial. Instrumentos: solo multímetro y PC.

1. **Fijar un patrón y listar los "de más".** Arranca Equilibrio nivel 1 (2 casillas).
   Anota qué celdas marca la **pantalla** y qué LEDs físicos encienden. Lista los LEDs que
   encienden sin estar en el patrón.

2. **Confirmar que con UN LED no hay fantasma.** Juega Velocidad o Memoria (un LED a la
   vez). Si ahí no aparecen LEDs de más y en Equilibrio sí, el problema se manifiesta con
   **varios LEDs simultáneos** → sospecha primero de alimentación/retorno compartido.

3. **Medir el GPIO del LED fantasma.** Con el patrón encendido, mide la tensión del pin
   `PIN_LED` de la celda que enciende de más:
   - Si el **GPIO está en LOW/0 V** pero el LED enciende → el LED recibe corriente por otra
     vía: **retorno de tierra compartido** (ghosting) o un canal del driver puenteado.
   - Si el **GPIO está en HIGH** cuando no debería → revisar continuidad GPIO→driver (un
     cruce de cables entre canales del driver).

4. **Verificar el driver canal a canal.** Con el ESP32 apagado, comprueba continuidad de
   cada cadena por separado: `GPIO → entrada del driver → LED de esa celda → retorno`.
   Que no haya continuidad entre la salida de una celda y el LED de otra.

5. **Descartar caída de tensión.** Si el fantasma aparece solo al encender 3–4 LEDs a la
   vez, mide la tensión del riel de LEDs con esa carga: una caída marcada indica
   **alimentación insuficiente** o retorno común mal dimensionado.

## Salida esperada

- Si es cableado cruzado: recablear para casar con `Config.h` y re-verificar con el
  checklist eléctrico de `cableado.md` §5 antes de energizar.
- Si es ghosting por tierra/driver: separar retornos o revisar el driver (ver
  `docs/hardware/00_diseno_circuito.md` y `materiales.md`).
- No se cambia firmware salvo que el hallazgo obligue a corregir el mapa de pines, que es
  fuente de verdad y solo se toca conciliando con el cableado real.

# Protocolo de comunicación — Tapete Interactivo Terapéutico

**Versión:** `1.0.0`

Este protocolo es la **frontera única** entre el cerebro del tapete (ESP32 real
**o** simulador) y la PC (dashboard del terapeuta). El simulador expone
exactamente el mismo protocolo que el ESP32, de modo que el dashboard no
distingue entre uno y otro.

---

## 1. Transporte

- Mensajes en **líneas JSON terminadas en `\n`** (un objeto JSON por línea).
- Funciona idénticamente sobre:
  - **Serial (USB)** a `115200` baudios.
  - **WiFi (TCP)**: el **ESP32 actúa como servidor TCP en el puerto `3333`**;
    el dashboard (o el simulador en modo red) se conecta como **cliente**.
- Codificación **UTF-8**. Cada línea es un objeto JSON plano (sin anidamiento).

---

## 2. Formato de serialización (mini-JSON propio)

Para garantizar que **el parseo sea idéntico** en C++ (ESP32 + `.so` del
simulador) y en Python, se usa un subconjunto estricto de JSON, no una
librería externa:

- Objeto plano: `{"clave":valor,"clave":valor}`. **Sin** objetos ni arrays
  anidados como valores.
- **Claves**: siempre cadenas entre comillas dobles.
- **Valores**: o bien un **entero** (`-?[0-9]+`) o bien una **cadena** entre
  comillas dobles.
- **Orden de claves fijo** por tipo de mensaje (ver abajo). Esto hace que la
  serialización sea **determinista** y comparable byte a byte en los golden
  vectors.
- **Escape** dentro de cadenas: solo `\"` (comilla) y `\\` (barra). No se usan
  otros escapes; los textos de nombres deben evitar caracteres de control.
- Sin espacios fuera de las cadenas. Terminador de línea: `\n` (no `\r\n`).

> El parser tolera espacios alrededor de `:` y `,` al **leer** (robustez), pero
> al **escribir** produce siempre la forma canónica sin espacios.

---

## 3. Eventos: Cerebro (ESP32 / Simulador) → PC

| Evento  | Ejemplo                                                              | Significado |
|---------|----------------------------------------------------------------------|-------------|
| `hello` | `{"ev":"hello","fw":"1.0.0","cells":6}`                              | Saludo inicial / respuesta a `ping`. Anuncia versión de firmware y número de casillas. |
| `led`   | `{"ev":"led","cell":1,"level":255}`                                 | Estado de un LED. `cell` 1..6, `level` 0..255 (brillo PWM). |
| `press` | `{"ev":"press","cell":3,"ms":1820}`                                 | Pisada detectada. `ms` = timestamp relativo al inicio de la sesión. |
| `sound` | `{"ev":"sound","id":2}`                                              | Petición de reproducir el audio `000{id}.mp3`. |
| `score` | `{"ev":"score","mode":1,"hits":5,"misses":1,"rt_ms":820,"round":6}` | Actualización de métricas. `rt_ms` = último/promedio tiempo de reacción. |
| `state` | `{"ev":"state","mode":1,"status":"running"}`                        | Cambio de estado del motor. `status` ∈ `idle\|running\|paused\|finished`. |

**Orden de claves canónico (al escribir):**

```
hello : ev, fw, cells
led   : ev, cell, level
press : ev, cell, ms
sound : ev, id
score : ev, mode, hits, misses, rt_ms, round
state : ev, mode, status
```

---

## 4. Comandos: PC → Cerebro (ESP32 / Simulador)

| Comando      | Ejemplo                                       | Significado |
|--------------|-----------------------------------------------|-------------|
| `set_mode`   | `{"cmd":"set_mode","mode":1,"level":2}`       | Selecciona modo (1=Memoria, 2=Velocidad, 3=Equilibrio) y nivel. |
| `start`      | `{"cmd":"start"}`                             | Inicia la sesión/ronda. |
| `stop`       | `{"cmd":"stop"}`                              | Detiene y vuelve a `idle`. |
| `pause`      | `{"cmd":"pause"}`                             | Pausa/reanuda (toggle) → `paused`/`running`. |
| `set_level`  | `{"cmd":"set_level","level":3}`               | Cambia el nivel actual. |
| `set_player` | `{"cmd":"set_player","id":"p001","name":"Juan"}` | Asocia la sesión a un perfil. |
| `set_seed`   | `{"cmd":"set_seed","seed":12345}`             | Fija la semilla del RNG (reproducibilidad / golden vectors). |
| `ping`       | `{"cmd":"ping"}`                              | El cerebro responde con `hello`. |

**Orden de claves canónico (al escribir, para tests de round-trip):**

```
set_mode   : cmd, mode, level
start      : cmd
stop       : cmd
pause      : cmd
set_level  : cmd, level
set_player : cmd, id, name
set_seed   : cmd, seed
ping       : cmd
```

> `set_seed` no aparecía en la especificación original; se añade porque los
> modos Memoria y Velocidad usan aleatoriedad. Fijar la semilla hace que la
> secuencia generada sea **reproducible**, requisito de los golden vectors.

---

## 5. Modos y niveles

- **Modo 1 — Memoria** (Simón dice): secuencia creciente de casillas.
- **Modo 2 — Velocidad** (topo): una casilla al azar, ventana de tiempo.
- **Modo 3 — Equilibrio** (patrones): 2–4 casillas simultáneas.

El significado preciso de cada `level` se documenta en `Config.h` (longitudes,
ventanas de tiempo, número de rondas) y se valida con los golden vectors.

---

## 6. Aleatoriedad determinista (RNG)

El cerebro usa un **xorshift32** propio (no `rand()`), portable e idéntico en
C++ y en cualquier reimplementación:

```
uint32_t next(uint32_t &s) {       // s != 0
    s ^= s << 13;
    s ^= s >> 17;
    s ^= s << 5;
    return s;
}
// Casilla elegida: cell = (next(s) % CELLS) + 1   // 1..6
```

La semilla se fija con `set_seed`. Con la misma semilla, modo y nivel, la
secuencia de casillas es siempre la misma → salida reproducible.

---

## 7. Versionado

- El campo `fw` de `hello` indica la versión del firmware/lógica.
- Cambios incompatibles del protocolo incrementan la versión mayor de este
  documento y del `fw`.

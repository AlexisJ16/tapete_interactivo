# Flasheo del ESP32 y configuración WiFi

El firmware ya está validado en software (simulador + tests). Pasar al hardware
es: **flashear + poner credenciales WiFi + abrir el dashboard**. Cero cambios de
lógica.

## 1. Requisitos

- **PlatformIO Core** (CLI):
  ```bash
  pip install platformio        # o usar el venv del proyecto: .venv/bin/pip install platformio
  ```
- Cable **USB-C** del ESP32 a la PC.
- (Audio) microSD FAT32 con los MP3 en la carpeta `/mp3/`: `/mp3/0001.mp3`..
  `/mp3/0004.mp3` (ver `audio/README.md`).

## 2. Credenciales WiFi (sin secretos en git)

```bash
cd firmware
cp src/secrets.h.example src/secrets.h
# edita src/secrets.h con tu SSID y contraseña
```

`src/secrets.h` está en `.gitignore`: **nunca se commitea**. Si no creas el
archivo, el firmware igual compila (usa credenciales `CAMBIAME` y emite un
`#warning`), pero no se conectará a tu WiFi.

## 3. Compilar (sin flashear)

```bash
cd firmware
pio run -e esp32dev
```

Esto descarga el toolchain de Espressif la primera vez (varios cientos de MB) y
compila. Debe terminar **sin errores**.

## 4. Flashear y monitor serie

```bash
cd firmware
pio run -e esp32dev -t upload          # flashea por USB
pio device monitor -b 115200           # abre el monitor serie
```

Al arrancar verás en el Serial:

```
Tapete Interactivo — firmware 1.0.0
Conectando a WiFi....
WiFi OK. IP: 192.168.1.50
Servidor TCP en puerto 3333
```

Anota la **IP**: la usarás en el dashboard.

> Si el puerto no se detecta, revisa permisos del puerto serie
> (`sudo usermod -aG dialout $USER` y reinicia sesión) o instala el driver
> CP210x/CH340 según tu placa.

## 5. Conectar el dashboard al ESP32 (por USB/Serial)

El puerto serie es **exclusivo**: cierra antes el `pio device monitor` (y no
reflashees con el dashboard abierto). El ESP32 se reinicia al abrir el puerto;
espera el banner `firmware 1.0.0` antes de pulsar **Iniciar**.

```bash
.venv/bin/python dashboard/app.py --serial /dev/ttyUSB0   # o /dev/ttyACM0
```

El dashboard habla el **mismo protocolo** por Serial que por TCP (tolera el banner
de arranque no-JSON). Elige modo/nivel, pulsa **Iniciar** y el niño juega sobre el
tapete físico; las pisadas (FSR) llegan en vivo y las sesiones se guardan en
SQLite, exportables a CSV/PDF.

> **Permiso del puerto:** si da *permission denied*, falta el grupo dialout:
> `sudo usermod -aG dialout $USER` y reinicia sesión. El puerto aparece al
> conectar: `ls /dev/ttyUSB* /dev/ttyACM*` (CP2102/CH340 → `ttyUSB0`; USB nativo →
> `ttyACM0`).
>
> **Alternativa WiFi (TCP):** pon credenciales en `secrets.h` y usa
> `--tcp <IP>` con la IP que muestra el Serial. El firmware sirve por ambos a la vez.

## 6. Calibración del umbral de pisada (modo calibración)

El firmware normal **no** imprime el ADC. Para verlo, flashea el **modo
calibración** (entorno `esp32dev_calib`): imprime por serial, cada ~700 ms, el
reposo/pico/rango de los 6 FSR (promedia 16 lecturas para bajar el ruido) y no
corre el juego ni WiFi.

```bash
cd firmware
pio run -e esp32dev_calib -t upload    # flashea el modo calibración
pio device monitor -b 115200
```

Verás un bloque cada ~700 ms con, por cada FSR: valor **actual**, **reposo**
(mínimo visto), **pico** (máximo visto) y **rango** (pico−reposo). El `✓` es solo
una pista (aparece cuando el rango supera 150); **los números mandan**:

```
====== CALIBRACION FSR ======  (Enter=reiniciar)
  FSR1  act=8    reposo=6    pico=41    rango=35     ✗
  FSR2  act=380  reposo=352  pico=2180  rango=1828   ✓ umbral=1083
  ...
  -> UMBRAL comun sugerido: 1000   (canales con actividad: 1)
=============================================
```

Cómo leerlo:

- **Canal conectado** → `reposo` estable en una banda con sentido (p. ej. ~300–400
  con el nodo a ~0.19 V). Al pisar, el `pico` sube.
- **Canal al aire** (sin sensor) → `reposo` ~0 en GPIO36/39/34/35 (FSR1–4) o ruido
  en GPIO32/33 (FSR5–6). El rango queda pequeño → `✗`.
- Pisa **fuerte** (peso, no toque de dedo): un FSR 402 con pull-down de 10 kΩ solo
  da buen salto con carga real. Pulsa **Enter** para reiniciar reposo/pico.

Anota el `reposo` y el `pico` de cada sensor y fija `cfg::UMBRAL_PISADA` en
`firmware/lib/GameCore/Config.h` (0..4095) a un punto intermedio —el `umbral`
que sugiere cada línea (`reposo + 40 %` del rango) es un buen punto de partida—
que la pisada lo supere con holgura y el reposo quede debajo. Luego **cierra el
monitor** y reflashea el firmware normal:

```bash
pio run -e esp32dev -t upload
```

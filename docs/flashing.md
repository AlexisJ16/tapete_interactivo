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
- (Audio) microSD FAT32 con `0001.mp3`..`0004.mp3` en la raíz (ver `audio/README.md`).

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

## 5. Conectar el dashboard al ESP32

```bash
cd dashboard
../.venv/bin/python app.py --tcp 192.168.1.50      # IP que mostró el Serial
```

El dashboard se conecta por TCP (puerto 3333) **con el mismo protocolo** que usa
contra el simulador. Elige modo/nivel, pulsa **Start** y el niño juega sobre el
tapete físico; las pisadas (FSR) llegan en vivo y las sesiones se guardan en
SQLite, exportables a CSV/PDF.

## 6. Calibración del umbral de pisada

Las lecturas crudas del FSR se ven en el Serial. Ajusta `cfg::UMBRAL_PISADA` en
`firmware/lib/GameCore/Config.h` (0..4095) hasta que una pisada normal lo supere
con holgura y el reposo quede por debajo. Recompila y vuelve a flashear.

## 7. Sin WiFi (alternativa por Serial)

Si no hay WiFi, el firmware sigue funcionando: emite y recibe el **mismo
protocolo** por el puerto serie (115200). Un cliente que hable líneas JSON por
Serial puede controlarlo igual que por TCP.

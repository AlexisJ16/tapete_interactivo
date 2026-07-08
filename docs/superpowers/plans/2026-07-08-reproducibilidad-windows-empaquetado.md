# Reproducibilidad y empaquetado Windows 11 — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el cliente descargue un ZIP de release construido por CI y el médico opere el tapete en Windows 11 con doble clic, mientras el mantenedor reproduce todo (tests, compilación, firmware) desde el repo.

**Architecture:** Dos niveles. Nivel 1 (médico): dashboard congelado con PyInstaller (onedir) que auto-detecta el puerto COM del ESP32 (CP210x) y trae la `libgamecore.dll` para modo práctica. Nivel 2 (mantenedor): se reutiliza `scripts/run_all_tests.sh` en Windows vía Git Bash + MinGW, sin reescribirlo. GitHub Actions (runner `windows-latest`) construye y **verifica** los artefactos (el `.exe` se lanza en un job sin `pip install`).

**Tech Stack:** Python 3.12, PyQt6, matplotlib, pyserial; PyInstaller (empaquetado); MinGW-w64 g++ (compila `libgamecore.dll`); GitHub Actions; ctypes.

## Global Constraints

- **Plataforma destino:** Windows 11; construir/verificar artefactos Windows solo en GitHub Actions `windows-latest` (la máquina de dev es Linux).
- **Chip USB-serial:** Silicon Labs CP210x — **VID `0x10C4`, PID `0xEA60`** (confirmado por `lsusb` → `10c4:ea60`).
- **Versiones fijadas exactas:** `PyQt6==6.11.0`, `matplotlib==3.11.0`, `pyserial==3.5`, `pytest==9.1.1`, `platformio==6.1.19`, `pygame==2.6.1`.
- **No reescribir `scripts/run_all_tests.sh`:** en Windows se corre con `shell: bash`, `PYBIN=python`, `QT_QPA_PLATFORM=offscreen` y MinGW `g++` en el PATH.
- **App congelada NUNCA compila:** en el `.exe` no se invoca `g++`; se carga la lib empaquetada o se falla con mensaje claro.
- **Lib nativa entregada = `libgamecore.dll`** (linkeada estática: sin dependencias del runtime MinGW); `ctypes` la carga por ruta.
- **Baseline verde en Linux tras cada tarea:** `./scripts/run_all_tests.sh` → 52 casos / 2174 aserciones C++ + ~101 pytest. No avanzar con rojo.
- **Commits:** pequeños; cada uno termina con el trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Se commitea directo en `main`.
- **Entrega limpia:** este trabajo vive en el repo de desarrollo; el snapshot al cliente depura rastros de IA aparte. Scripts/CI/packaging son entregables legítimos.

---

## File Structure

- `requirements-dev.txt`, `dashboard/requirements.txt`, `simulator/requirements.txt` — **modificar**: fijar versiones.
- `simulator/core_bridge.py` — **modificar**: nombre de lib por plataforma, ruta segura en app congelada, flags estáticos en Windows.
- `simulator/test_core_bridge.py` — **crear**: tests de la lógica de plataforma/congelado.
- `dashboard/puertos.py` — **crear**: detección CP210x + resolución de `--serial auto` (sin Qt).
- `dashboard/test_puertos.py` — **crear**: tests de detección/resolución.
- `dashboard/app.py` — **modificar**: `--serial auto` + selector de puerto.
- `packaging/tapete_dashboard.spec` — **crear**: spec PyInstaller (onedir).
- `packaging/instalar.bat` — **crear**: instalador venv de respaldo.
- `packaging/GUIA_MEDICO.md` — **crear**: guía de una página para el médico.
- `docs/dev-windows.md` — **crear**: setup del mantenedor en Windows.
- `.github/workflows/ci.yml` — **modificar**: jobs `windows-build`, `windows-smoke`, `windows-release`.

---

### Task 1: Fijar versiones de dependencias

**Files:**
- Modify: `dashboard/requirements.txt`
- Modify: `simulator/requirements.txt`
- Modify: `requirements-dev.txt`

**Interfaces:**
- Consumes: nada.
- Produces: requirements con versiones `==` exactas que CI y el mantenedor instalan.

- [ ] **Step 1: Fijar `dashboard/requirements.txt`**

```
# Dashboard del terapeuta. Versiones fijadas para reproducibilidad (y hooks de PyInstaller).
PyQt6==6.11.0
matplotlib==3.11.0
pyserial==3.5   # FuenteSerial: conexion USB/Serial con el ESP32
```

- [ ] **Step 2: Fijar `simulator/requirements.txt`**

```
# Simulador visual del tapete.
pygame==2.6.1
```

- [ ] **Step 3: Fijar `requirements-dev.txt`**

```
# Dependencias de desarrollo/test (Python). Instalar en el venv del proyecto:
#   python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
pytest==9.1.1
platformio==6.1.19   # build/flash del firmware ESP32 (pio run -e esp32dev)
```

- [ ] **Step 4: Verificar que resuelve y la suite sigue verde**

Run: `.venv/bin/pip install -r requirements-dev.txt -r simulator/requirements.txt -r dashboard/requirements.txt && ./scripts/run_all_tests.sh`
Expected: instala sin conflictos y termina en `>>> TODO VERDE <<<`.

- [ ] **Step 5: Commit**

```bash
git add requirements-dev.txt simulator/requirements.txt dashboard/requirements.txt
git commit -m "build: fijar versiones exactas de dependencias (reproducibilidad)"
```

---

### Task 2: `core_bridge` multiplataforma y a prueba de congelado

**Files:**
- Create: `simulator/test_core_bridge.py`
- Modify: `simulator/core_bridge.py` (constantes ~L24-28, `construir_so` ~L38-50, `CoreBridge.__init__` ~L56-58)

**Interfaces:**
- Consumes: nada.
- Produces: `core_bridge._lib_nombre() -> str`, `core_bridge._comando_build() -> list[str]`, `core_bridge.ruta_lib() -> str`, `core_bridge.construir_so(forzar=False) -> str` (nombre de salida por plataforma). `CoreBridge()` sigue funcionando igual en dev.

- [ ] **Step 1: Escribir los tests que fallan** — crear `simulator/test_core_bridge.py`:

```python
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core_bridge as cb


def test_lib_nombre_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert cb._lib_nombre() == "libgamecore.dll"


def test_lib_nombre_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert cb._lib_nombre() == "libgamecore.so"


def test_comando_build_windows_es_estatico(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    cmd = cb._comando_build()
    assert "-static-libstdc++" in cmd
    assert "-static-libgcc" in cmd
    assert "-static" in cmd


def test_comando_build_linux_no_estatico(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert "-static" not in cb._comando_build()


def test_ruta_lib_congelado_usa_meipass_sin_compilar(monkeypatch, tmp_path):
    lib = tmp_path / cb._lib_nombre()
    lib.write_bytes(b"\x00")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    llamado = {"construir": False}
    monkeypatch.setattr(cb, "construir_so",
                        lambda *a, **k: llamado.__setitem__("construir", True))
    assert cb.ruta_lib() == str(lib)
    assert llamado["construir"] is False  # jamas compila en app congelada


def test_ruta_lib_congelado_sin_lib_falla(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    with pytest.raises(RuntimeError):
        cb.ruta_lib()
```

- [ ] **Step 2: Correr y verlos fallar**

Run: `.venv/bin/python -m pytest simulator/test_core_bridge.py -q`
Expected: FAIL (`AttributeError: module 'core_bridge' has no attribute '_lib_nombre'`).

- [ ] **Step 3: Implementar en `simulator/core_bridge.py`** — reemplazar la línea de `SO_PATH` (actual L28 `SO_PATH = os.path.join(BUILD, "libgamecore.so")`) por:

```python
def _lib_nombre() -> str:
    """Nombre de la biblioteca nativa segun la plataforma."""
    return "libgamecore.dll" if sys.platform.startswith("win") else "libgamecore.so"


def _empaquetado() -> bool:
    """True si corremos dentro de un ejecutable congelado (PyInstaller)."""
    return getattr(sys, "frozen", False)


# Ruta de build (dev). El nombre depende de la plataforma.
SO_PATH = os.path.join(BUILD, _lib_nombre())
```

  Reemplazar la función `construir_so` (actual L38-50) por:

```python
def _comando_build() -> list[str]:
    """Comando g++ para compilar GameCore como biblioteca compartida. En Windows
    se enlaza estatico (-static*) para que el .dll NO dependa del runtime de MinGW
    (libstdc++/libgcc/winpthread), ausente en el equipo del medico."""
    flags = ["-std=c++17", "-O2", "-fPIC", "-shared"]
    if sys.platform.startswith("win"):
        flags += ["-static", "-static-libgcc", "-static-libstdc++"]
    return [os.environ.get("CXX", "g++"), *flags, f"-I{GAMECORE}",
            *fuentes_core(), "-o", SO_PATH]


def construir_so(forzar: bool = False) -> str:
    """Compila GameCore (.so/.dll) con g++ si falta (o si se fuerza). Devuelve la
    ruta. Solo en DESARROLLO: la app congelada nunca llega aqui (ver ruta_lib)."""
    os.makedirs(BUILD, exist_ok=True)
    if forzar or not os.path.exists(SO_PATH):
        subprocess.run(_comando_build(), check=True)
    return SO_PATH


def ruta_lib() -> str:
    """Ruta a la biblioteca nativa lista para cargar.

    - App congelada (PyInstaller): la lib va empaquetada junto al ejecutable
      (sys._MEIPASS) y NUNCA se compila (el equipo del medico no tiene g++); si
      falta, error claro.
    - Desarrollo: se compila con g++ si falta."""
    if _empaquetado():
        p = os.path.join(getattr(sys, "_MEIPASS", RAIZ), _lib_nombre())
        if not os.path.exists(p):
            raise RuntimeError(f"biblioteca nativa no encontrada en el paquete: {p}")
        return p
    return construir_so()
```

  En `CoreBridge.__init__` (actual L56-58) cambiar `libpath = construir_so()` por `libpath = ruta_lib()`:

```python
    def __init__(self, libpath: str | None = None):
        if libpath is None:
            libpath = ruta_lib()
        self._lib = ctypes.CDLL(libpath)
```

- [ ] **Step 4: Correr los tests nuevos y la suite completa**

Run: `.venv/bin/python -m pytest simulator/test_core_bridge.py -q && ./scripts/run_all_tests.sh`
Expected: los 6 tests nuevos PASAN y la suite termina `>>> TODO VERDE <<<` (la construcción `.so` en Linux sigue igual).

- [ ] **Step 5: Commit**

```bash
git add simulator/core_bridge.py simulator/test_core_bridge.py
git commit -m "feat(core_bridge): lib por plataforma, ruta segura en app congelada, .dll estatico"
```

---

### Task 3: Auto-detección del puerto COM y `--serial auto`

**Files:**
- Create: `dashboard/puertos.py`
- Create: `dashboard/test_puertos.py`
- Modify: `dashboard/app.py` (`main()` ~L486-502)

**Interfaces:**
- Consumes: `pyserial` (`serial.tools.list_ports`).
- Produces: `puertos.puertos_tapete(comports=None) -> list[str]`; `puertos.resolver_puerto_serial(valor, detectar=puertos_tapete, elegir=None) -> str | None`; constantes `puertos.CP210X_VID`, `puertos.CP210X_PID`. `app.py` acepta `--serial auto`.

- [ ] **Step 1: Escribir los tests que fallan** — crear `dashboard/test_puertos.py`:

```python
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puertos import (CP210X_PID, CP210X_VID, puertos_tapete,
                     resolver_puerto_serial)


def _p(device, vid, pid):
    return SimpleNamespace(device=device, vid=vid, pid=pid)


def test_puertos_tapete_filtra_por_vid_pid():
    ports = [
        _p("COM1", 0x1234, 0x0001),           # otro dispositivo
        _p("COM3", CP210X_VID, CP210X_PID),   # el tapete
        _p("COM4", CP210X_VID, 0x0000),       # mismo vendor, otro pid
    ]
    assert puertos_tapete(ports) == ["COM3"]


def test_resolver_valor_explicito_pasa_igual():
    assert resolver_puerto_serial("/dev/ttyUSB0", detectar=lambda: []) == "/dev/ttyUSB0"


def test_resolver_auto_un_puerto():
    assert resolver_puerto_serial("auto", detectar=lambda: ["COM3"]) == "COM3"


def test_resolver_auto_sin_puertos_da_none():
    assert resolver_puerto_serial("auto", detectar=lambda: []) is None


def test_resolver_auto_varios_usa_elegir():
    r = resolver_puerto_serial("auto", detectar=lambda: ["COM3", "COM5"],
                               elegir=lambda ps: ps[1])
    assert r == "COM5"


def test_resolver_auto_varios_sin_elegir_toma_primero():
    assert resolver_puerto_serial("auto", detectar=lambda: ["COM3", "COM5"]) == "COM3"
```

- [ ] **Step 2: Correr y verlos fallar**

Run: `.venv/bin/python -m pytest dashboard/test_puertos.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'puertos'`).

- [ ] **Step 3: Implementar** — crear `dashboard/puertos.py`:

```python
"""Deteccion del puerto serie del tapete (ESP32 con puente USB CP210x).

El medico no escribe "COM3": el lanzador arranca con --serial auto y esto resuelve
el puerto por el VID/PID del CP210x. Sin Qt, para poder probarlo headless."""
from __future__ import annotations

# Silicon Labs CP210x UART Bridge (confirmado en la placa: lsusb 10c4:ea60).
CP210X_VID = 0x10C4
CP210X_PID = 0xEA60


def puertos_tapete(comports=None) -> "list[str]":
    """Nombres de puerto (p. ej. 'COM3' o '/dev/ttyUSB0') cuyo VID/PID es el CP210x
    del ESP32. 'comports' es inyectable para tests; por defecto usa
    serial.tools.list_ports.comports()."""
    if comports is None:
        from serial.tools import list_ports
        comports = list_ports.comports()
    return [p.device for p in comports
            if getattr(p, "vid", None) == CP210X_VID
            and getattr(p, "pid", None) == CP210X_PID]


def resolver_puerto_serial(valor, detectar=puertos_tapete, elegir=None):
    """Traduce el valor de --serial a un puerto concreto (o None).

    - 'auto': detecta los CP210x. 1 -> ese puerto; 0 -> None (sin tapete);
      N -> elegir(puertos) si se pasa, si no el primero.
    - cualquier otro valor: se devuelve tal cual (puerto explicito)."""
    if valor != "auto":
        return valor
    encontrados = detectar()
    if len(encontrados) == 1:
        return encontrados[0]
    if not encontrados:
        return None
    if elegir is None:
        return encontrados[0]
    return elegir(encontrados)
```

- [ ] **Step 4: Correr los tests nuevos y verlos pasar**

Run: `.venv/bin/python -m pytest dashboard/test_puertos.py -q`
Expected: PASS (6 tests).

- [ ] **Step 5: Cablear `app.py`** — reemplazar `main()` (L486-502) y añadir el selector; el bloque `smoke()`/`__main__` (L455-508) queda igual:

```python
def _elegir_puerto_com(puertos):
    """Selector minimo cuando hay varios CP210x (raro). GUI, no se testea."""
    QtCore, QtGui, QtWidgets = _qt()
    elegido, ok = QtWidgets.QInputDialog.getItem(
        None, "Tapete", "Elige el puerto del tapete:", puertos, 0, False)
    return elegido if ok else puertos[0]


def main() -> int:
    import argparse

    from puertos import resolver_puerto_serial
    p = argparse.ArgumentParser(description="Dashboard del terapeuta")
    p.add_argument("--tcp", metavar="HOST", default=None, help="conectar a un ESP32/simulador por TCP")
    p.add_argument("--serial", metavar="PUERTO", default=None,
                   help="conectar por USB/Serial: un puerto (COM3) o 'auto' (detecta el tapete)")
    p.add_argument("--puerto", type=int, default=3333)
    args = p.parse_args()

    instalar_excepthook(LOGGER)
    QtCore, QtGui, QtWidgets = _qt()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(QSS)
    if args.serial is not None:
        pedido = args.serial
        args.serial = resolver_puerto_serial(args.serial, elegir=_elegir_puerto_com)
        if pedido == "auto" and args.serial is None:
            QtWidgets.QMessageBox.information(
                None, "Tapete",
                "No se detecto el tapete por USB. Se abre en modo practica.\n"
                "Conecta el tapete y vuelve a abrir; si Windows no lo reconoce, "
                "instala el driver incluido (CP210x).")
    fuente = construir_fuente(tcp=args.tcp, serial=args.serial, puerto=args.puerto)
    v = VentanaDashboard(fuente=fuente)
    v.mostrar()
    return app.exec()
```

- [ ] **Step 6: Verificar que la suite completa sigue verde**

Run: `./scripts/run_all_tests.sh`
Expected: `>>> TODO VERDE <<<` (incluye `dashboard/test_puertos.py`).

- [ ] **Step 7: Commit**

```bash
git add dashboard/puertos.py dashboard/test_puertos.py dashboard/app.py
git commit -m "feat(dashboard): auto-deteccion del puerto COM (CP210x) y --serial auto"
```

---

### Task 4: Empaquetado — spec PyInstaller + `.bat` de respaldo

**Files:**
- Create: `packaging/tapete_dashboard.spec`
- Create: `packaging/instalar.bat`

**Interfaces:**
- Consumes: `build/libgamecore.dll` (lo produce CI con `core_bridge.construir_so(True)` antes de `pyinstaller`); `dashboard/app.py` y módulos hermanos.
- Produces: `dist/TapeteDashboard/` (onedir con `TapeteDashboard.exe` + `libgamecore.dll`).

> **Nota de verificación:** este task se **construye en Linux** pero solo se **verifica en Windows/CI** (Task 6). Su smoke real es el job `windows-smoke`. Puntos que pueden requerir un ajuste tras el primer run de CI: la ruta de MinGW y el flag `-static` (ver Task 6). Es bring-up de CI esperado, no placeholders.

- [ ] **Step 1: Crear `packaging/tapete_dashboard.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec del dashboard del terapeuta (onedir).
# Se construye en Windows (CI). build/libgamecore.dll debe existir antes de correr
# pyinstaller (CI: paso "Construir libgamecore.dll"). Correr desde la raiz del repo.
import os

raiz = os.path.abspath(os.getcwd())
dll = os.path.join(raiz, "build", "libgamecore.dll")

a = Analysis(
    ['dashboard/app.py'],
    pathex=['dashboard', 'simulator'],
    binaries=[],
    datas=[(dll, '.')] if os.path.exists(dll) else [],
    hiddenimports=['core_bridge', 'fuente', 'sesion', 'storage', 'reports',
                   'paneles', 'analitica', 'estilo', 'robustez', 'puertos'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
          name='TapeteDashboard', console=False)
coll = COLLECT(exe, a.binaries, a.datas, name='TapeteDashboard')
```

- [ ] **Step 2: Crear `packaging/instalar.bat` (respaldo si el `.exe` falla)**

```bat
@echo off
REM Instalador de respaldo del Dashboard del Tapete (alternativa al .exe).
REM Crea un entorno Python local e instala las dependencias fijadas.
setlocal
cd /d "%~dp0.."
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% -m venv .venv || goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip || goto :err
pip install -r dashboard\requirements.txt || goto :err
> abrir_tapete.bat echo @echo off
>> abrir_tapete.bat echo cd /d "%%~dp0"
>> abrir_tapete.bat echo call .venv\Scripts\activate.bat
>> abrir_tapete.bat echo python dashboard\app.py --serial auto
echo.
echo Listo. Doble clic en abrir_tapete.bat para usar el tapete.
pause
exit /b 0
:err
echo ERROR durante la instalacion.
pause
exit /b 1
```

- [ ] **Step 3: Chequeo de sintaxis del spec (Linux, no construye el exe)**

Run: `.venv/bin/python -c "compile(open('packaging/tapete_dashboard.spec').read(), 'spec', 'exec'); print('spec OK')"`
Expected: `spec OK` (valida que el spec es Python parseable).

- [ ] **Step 4: Commit**

```bash
git add packaging/tapete_dashboard.spec packaging/instalar.bat
git commit -m "build(packaging): spec PyInstaller (onedir) + instalador .bat de respaldo"
```

---

### Task 5: Documentación — guía del médico y setup del mantenedor

**Files:**
- Create: `packaging/GUIA_MEDICO.md`
- Create: `docs/dev-windows.md`

**Interfaces:**
- Consumes: nada.
- Produces: `packaging/GUIA_MEDICO.md` (va dentro del ZIP del release, Task 6); `docs/dev-windows.md`.

- [ ] **Step 1: Crear `packaging/GUIA_MEDICO.md`**

```markdown
# Tapete Interactivo — Guia rapida

## Para empezar (una sola vez)

1. Conecta el tapete al computador con el cable USB.
2. Espera unos segundos. Windows 11 suele reconocerlo solo.
   - Si mas adelante el programa avisa que no encuentra el tapete, abre la carpeta
     `driver_cp210x`, descomprime el archivo y ejecuta el instalador que trae.
     Luego desconecta y vuelve a conectar el tapete.

## Uso diario

1. Conecta el tapete por USB (si no lo esta).
2. Doble clic en **TapeteDashboard.exe**.
3. El programa busca el tapete y se conecta solo. No tienes que elegir puertos.
4. Elige el modo de juego y el nivel, escribe el nombre del nino y presiona
   **Iniciar**.

## Si el tapete no esta conectado

El programa abre igual en **modo practica**: puedes tocar los botones con el raton
para conocer la interfaz. Para jugar de verdad, conecta el tapete y vuelve a abrir.

## Al terminar

Exporta el reporte de la sesion (CSV/PDF) con el boton de exportar y cierra la
ventana normalmente.

## Problemas frecuentes

- **"No se detecto el tapete"**: revisa el cable USB y que este bien conectado. Si
  sigue, instala el driver de la carpeta `driver_cp210x` (ver arriba).
- **El programa no abre**: descomprime el ZIP completo en una carpeta antes de
  ejecutar (no lo abras desde dentro del ZIP).
```

- [ ] **Step 2: Crear `docs/dev-windows.md`**

```markdown
# Entorno de desarrollo en Windows 11

Para MANTENER el proyecto (correr tests, compilar la logica, flashear el firmware).
El medico NO necesita esto: usa el ZIP del release (ver packaging/GUIA_MEDICO.md).

## 1. Instalar herramientas (una vez, con winget)

En PowerShell:

    winget install --id Git.Git -e
    winget install --id Python.Python.3.12 -e
    winget install --id BrechtSanders.WinLibs.POSIX.UCRT.LLVM -e   # g++ (MinGW-w64)

Cierra y reabre PowerShell para refrescar el PATH. Verifica:

    python --version   # 3.12.x
    g++ --version      # MinGW-w64
    git --version

## 2. Clonar y crear el entorno

    git clone <URL-del-repo> tapete
    cd tapete
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements-dev.txt -r simulator\requirements.txt -r dashboard\requirements.txt

## 3. Correr TODA la suite

Se usa el mismo runner que en Linux/CI, via Git Bash:

    "C:\Program Files\Git\bin\bash.exe" -lc "PYBIN=python QT_QPA_PLATFORM=offscreen ./scripts/run_all_tests.sh"

Esperado: `>>> TODO VERDE <<<`.

## 4. Firmware (opcional; requiere el ESP32)

    cd firmware
    copy src\secrets.h.example src\secrets.h   REM y edita credenciales WiFi
    ..\.venv\Scripts\pio run -e esp32dev        REM compila (no flashea)

El flasheo lo hace un humano conscientemente (ver docs/hardware/flashing.md).
```

- [ ] **Step 3: Commit**

```bash
git add packaging/GUIA_MEDICO.md docs/dev-windows.md
git commit -m "docs: guia del medico (release) + setup dev en Windows"
```

---

### Task 6: CI — construir, verificar y publicar el ZIP de Windows

**Files:**
- Modify: `.github/workflows/ci.yml` (añadir 3 jobs al final; no tocar los jobs `tests` y `firmware-wokwi`).

**Interfaces:**
- Consumes: requirements fijados (Task 1), `core_bridge.construir_so` (Task 2), `packaging/tapete_dashboard.spec` (Task 4), `packaging/GUIA_MEDICO.md` (Task 5), `app.py --smoke` (ya existe).
- Produces: artefacto `TapeteDashboard-windows` (ZIP) y, en tags, un Release de GitHub con el ZIP adjunto.

- [ ] **Step 1: Añadir los jobs al final de `.github/workflows/ci.yml`**

```yaml
  windows-build:
    name: Windows — tests + empaquetado
    runs-on: windows-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/') || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Instalar MinGW (g++) y ponerlo en PATH
        shell: pwsh
        run: |
          choco install mingw --no-progress -y
          $cands = @(
            "C:\ProgramData\mingw64\mingw64\bin",
            "C:\ProgramData\chocolatey\lib\mingw\tools\install\mingw64\bin",
            "C:\mingw64\bin"
          )
          $bin = $cands | Where-Object { Test-Path (Join-Path $_ "g++.exe") } | Select-Object -First 1
          if (-not $bin) {
            $gpp = Get-Command g++ -ErrorAction SilentlyContinue
            if ($gpp) { $bin = Split-Path $gpp.Source }
          }
          if (-not $bin) { throw "no encontre g++ tras instalar mingw" }
          echo $bin >> $env:GITHUB_PATH

      - name: Instalar dependencias Python
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt -r simulator/requirements.txt -r dashboard/requirements.txt pyinstaller

      - name: Correr la suite (mismo runner, via bash, PYBIN=python)
        shell: bash
        env:
          PYBIN: python
          QT_QPA_PLATFORM: offscreen
          SDL_VIDEODRIVER: dummy
        run: ./scripts/run_all_tests.sh

      - name: Construir libgamecore.dll
        run: python -c "import sys; sys.path.insert(0, 'simulator'); import core_bridge; print(core_bridge.construir_so(True))"

      - name: Construir el ejecutable (PyInstaller)
        run: pyinstaller --noconfirm packaging/tapete_dashboard.spec

      - name: Descargar driver CP210x (offline en el ZIP; best-effort)
        shell: bash
        run: |
          mkdir -p dist/TapeteDashboard/driver_cp210x
          curl -fL -o dist/TapeteDashboard/driver_cp210x/CP210x_Universal_Windows_Driver.zip \
            https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip \
            || echo "::warning::No se pudo bajar el driver CP210x; el ZIP va sin el (la guia trae la referencia)."

      - name: Incluir la guia del medico
        shell: bash
        run: cp packaging/GUIA_MEDICO.md dist/TapeteDashboard/GUIA_MEDICO.md

      - name: Empaquetar ZIP
        shell: bash
        run: cd dist && 7z a -tzip TapeteDashboard-windows.zip TapeteDashboard >/dev/null

      - uses: actions/upload-artifact@v4
        with:
          name: TapeteDashboard-windows
          path: dist/TapeteDashboard-windows.zip

  windows-smoke:
    name: Windows — smoke del .exe SIN deps de dev (gate de evidencia)
    needs: windows-build
    runs-on: windows-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: TapeteDashboard-windows

      - name: Descomprimir
        shell: bash
        run: 7z x TapeteDashboard-windows.zip >/dev/null

      - name: Lanzar el .exe headless (sin pip install)
        shell: bash
        env:
          QT_QPA_PLATFORM: offscreen
        run: ./TapeteDashboard/TapeteDashboard.exe --smoke

  windows-release:
    name: Windows — adjuntar el ZIP al Release (solo tags)
    needs: [windows-build, windows-smoke]
    if: startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: TapeteDashboard-windows
      - uses: softprops/action-gh-release@v2
        with:
          files: TapeteDashboard-windows.zip
```

- [ ] **Step 2: Validar el YAML localmente**

Run: `.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml OK')"`
Expected: `yaml OK`. (Si falta PyYAML: `.venv/bin/pip install pyyaml`.)

- [ ] **Step 3: Commit y push (dispara CI en Windows)**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: job Windows — tests, empaquetado del .exe y smoke sin deps"
git push
```

- [ ] **Step 4: Observar CI y confirmar el gate de evidencia**

Run: `gh run watch $(gh run list --branch main --workflow CI --limit 1 --json databaseId --jq '.[0].databaseId')`
Expected: los jobs `windows-build` y `windows-smoke` en verde. El paso "Lanzar el .exe headless" debe salir con código 0 (el `.exe` arranca y auto-sale sin dependencias de dev). **Este es el gate: "listo" = el `.exe` corre en una máquina limpia.**
Si `windows-build` falla en MinGW o en `-static`, ajustar según el mensaje (candidatos de PATH / quitar `-static` dejando `-static-libgcc -static-libstdc++` en `core_bridge._comando_build`) y volver a pushear.

- [ ] **Step 5 (opcional, cuando todo esté verde): publicar un release de prueba**

```bash
git tag v0.1.0-rc1 && git push origin v0.1.0-rc1
```
Expected: el job `windows-release` adjunta `TapeteDashboard-windows.zip` al Release `v0.1.0-rc1`. Descargarlo, descomprimir y confirmar que `TapeteDashboard.exe` abre en un Windows real (validación humana final).

---

## Self-Review

**1. Spec coverage** (spec → task):
- §4/§5.1 dos niveles + contenido del ZIP → Task 4 (exe+dll), Task 6 (ZIP: exe+driver+guía).
- §5.2 auto-detección COM (CP210x VID/PID) → Task 3.
- §5.3 modo práctica + `.dll` empaquetada → Task 2 (dll/frozen) + Task 4 (datas).
- §5.4 driver CP210x offline → Task 6 (descarga best-effort) + Task 5 (guía).
- §5.6 PyInstaller onedir + `.bat` respaldo → Task 4.
- §6 Nivel 2 reutiliza `run_all_tests.sh` en Windows → Task 6 (job bash) + Task 5 (`dev-windows.md`).
- §7 CI (build/tests/dll/exe/smoke-sin-deps/release) → Task 6.
- §8 cambios de código (core_bridge, app.py `--serial auto`, pin deps) → Tasks 2, 3, 1.
- §9 gate de evidencia (exe sin deps) → Task 6 Step 4 (`windows-smoke`).
- §11 riesgo PyInstaller + fallback `.bat` → Task 4 Step 2.
No hay requisitos del spec sin task.

**2. Placeholder scan:** sin "TBD/TODO/etc." Los dos puntos de ajuste de CI (ruta MinGW, flag `-static`) están resueltos con código concreto + criterio de ajuste explícito, no son placeholders.

**3. Type consistency:** `_lib_nombre`, `_comando_build`, `ruta_lib`, `construir_so` (Task 2) coinciden con su uso en `CoreBridge.__init__` y en el paso CI "Construir libgamecore.dll". `puertos_tapete`/`resolver_puerto_serial` (Task 3) coinciden con su import en `app.py`. El spec PyInstaller referencia `build/libgamecore.dll`, que es lo que produce `construir_so` en Windows (`_lib_nombre()` → `libgamecore.dll`). `--smoke` usado en Task 6 ya existe en `app.py`. Consistente.

# Reproducibilidad y empaquetado para Windows 11 — Diseño

Fecha: 2026-07-08
Estado: aprobado (brainstorming); pendiente de plan de implementación.

## 1. Objetivo

Que el proyecto sea **altamente reproducible y trivial de operar en Windows 11**, con la
tecnología más simple posible, dado que el cliente y los médicos que lo usarán tienen bajo
nivel técnico. La meta operativa: un médico, con instrucciones claras, opera el tapete de
forma completa; el cliente pone todo en marcha con el mínimo esfuerzo.

## 2. Decisiones cerradas con el usuario

- **Alcance = dos niveles:** paquete "molido" para operar (médico) + entorno reproducible
  para mantener (quien herede el proyecto).
- **Actores:** el **cliente descarga el ZIP del release** (construido por CI), descomprime y
  listo — **no clona, no corre scripts, no instala Python**. El **médico** solo abre un
  lanzador. La ruta "clonar + correr scripts" es del **mantenedor** (Nivel 2).
- **Construcción y verificación de artefactos Windows = GitHub Actions (runner `windows-latest`).**
  La máquina de desarrollo es Linux y no puede construir ni probar `.exe`/COM/drivers de Windows.
- **Empaquetado:** `.exe` congelado (PyInstaller) como **única entrega al cliente**; el `.bat`
  (`packaging/instalar.bat`) es una **conveniencia de desarrollo** para correr desde el checkout,
  no un entregable. Si el freeze falla en CI, no se publica y se itera el build (ver §5.6/§11).
- **Tratamiento completo** (sin presión de deadline): empaquetado + CI + instrucciones + docs.
- **Chip USB-serial confirmado empíricamente = Silicon Labs CP210x** (`lsusb` → `10c4:ea60`).

## 3. Hecho técnico habilitante (verificado, no asumido)

Importar `simulator/core_bridge.py` **no** compila la biblioteca nativa: la compilación con
`g++` es perezosa dentro de `CoreBridge.__init__`, que solo instancia `FuenteCore`. Por tanto
el camino operativo del médico (`dashboard/app.py --serial <COM>` → `FuenteSerial`) **no toca
código nativo**: solo requiere `PyQt6`, `matplotlib` y `pyserial`. Ese es el pilar del paquete
liviano. La biblioteca nativa (`libgamecore`) solo hace falta para el **modo práctica**
(`FuenteCore`, ver §5.3).

## 4. Arquitectura: dos niveles

| | **Nivel 1 — Operar (médico)** | **Nivel 2 — Mantener (dev)** |
|---|---|---|
| Actor | Cliente instala 1 vez; médico opera a diario | Quien herede el proyecto |
| Obtención | Descarga ZIP del release + descomprime | Clona el repo |
| Puesta en marcha | Doble clic al lanzador | Corre scripts de setup |
| Python en la máquina | No (embebido en el `.exe`) | Sí (venv) |
| Compilador C++ | No | Sí (MinGW-w64) |
| Firmware / flasheo | No (recibe el ESP32 ya flasheado) | Sí (PlatformIO) |

## 5. Nivel 1 — Paquete del médico

### 5.1 Contenido del ZIP del release
- Carpeta del dashboard congelado (PyInstaller **onedir**): `TapeteDashboard.exe` + `_internal/`.
- `libgamecore.dll` empaquetada (para el modo práctica, §5.3).
- Instalador del **driver CP210x** de Silicon Labs (offline, §5.4).
- `LEEME.txt` / guía de una página con capturas (§5.5).
- Opcional: acceso directo `Tapete.lnk` apuntando al `.exe`.

### 5.2 Auto-detección del puerto COM
El médico **nunca escribe "COM3"**. Nueva función de detección basada en
`serial.tools.list_ports.comports()`, filtrando por **VID `0x10C4` / PID `0xEA60`** (CP210x):
- Exactamente un puerto CP210x → conecta sin preguntar.
- Cero → mensaje claro ("Conecta el tapete por USB; si Windows no lo reconoce, instala el
  driver incluido") + estado degradado visible (ya existe la infraestructura de degradación).
- Varios → selector simple (diálogo con la lista).

Interfaz: `app.py` acepta `--serial auto` (sentinela) además del puerto explícito. El lanzador
del médico invoca `--serial auto`. `--serial <COM>` y `--tcp` explícitos siguen igual.

### 5.3 Modo práctica sin tapete (función incluida, **severable**)
El dashboard ya trae el tapete en software (`FuenteCore`, se "pisa" con el ratón). Se conserva
para que el médico practique/aprenda la interfaz sin hardware. Es **lo único** que obliga a
empaquetar `libgamecore.dll`. Si PyInstaller se resiste con la lib nativa, esta función se puede
**recortar** y dejar un `.exe` solo-serial (trivial de congelar) sin afectar la operación real.

### 5.4 Driver CP210x en Windows 11
En Windows 11 el CP210x suele instalarse solo por Windows Update al conectar. Para no depender
de internet ni de que ocurra: **se incluye el "CP210x Universal Windows Driver" de Silicon Labs
en el ZIP**, con instrucción de "ejecutar solo si el tapete no aparece". La guía explica cómo
saber que ya funciona (aparece el puerto / el dashboard conecta).

### 5.5 Lanzador e instrucciones
- Lanzador = el propio `TapeteDashboard.exe` (arranca con `--serial auto`), o un acceso directo.
- Guía de una página (médico): conectar el tapete → abrir el lanzador → (si hace falta) driver →
  jugar. Con capturas. Lenguaje no técnico.

### 5.6 Empaquetado
- **PyInstaller onedir** (carpeta), entregada como ZIP. Onedir sobre onefile: arranca más rápido
  y da menos falsos positivos de antivirus, que en una máquina clínica pesa más que "un solo
  archivo".
- Spec de PyInstaller versionado en el repo (`packaging/`), con manejo de `datas` para
  `libgamecore.dll` y hooks de PyQt6/matplotlib.
- **Conveniencia dev:** `packaging/instalar.bat` corre el dashboard desde un checkout del repo
  (venv + deps fijadas + `abrir_tapete.bat`), equivalente a `docs/dev-windows.md` automatizado.
  NO es entregable del cliente (requiere el árbol de fuente).

## 6. Nivel 2 — Entorno de mantenimiento (dev en Windows)

**No se reescribe `scripts/run_all_tests.sh`.** Se reutiliza tal cual en Windows con `bash`
(Git Bash), que ya trae el runner de GitHub y cualquier instalación de Git para Windows:
- `PYBIN=python` (el override ya existe en el script; en Windows el venv es `Scripts\python.exe`).
- MinGW-w64 `g++` en el PATH (mismos flags GCC; `-fPIC` es inocuo/omitible en Windows).
- `ctypes` carga la lib por ruta, así que el nombre `libgamecore.so` no molesta en los **tests**
  (la `.dll` con nombre propio es solo para el paquete entregado, §8).

Setup documentado (`docs/dev-windows.md`) con `winget`:
`winget install` de Python 3.12, MinGW-w64 (o LLVM), Git; luego venv + `pip install -r` de los
requirements fijados; PlatformIO para firmware; `cp secrets.h.example secrets.h`.

## 7. CI: nuevo job de Windows (`.github/workflows/ci.yml`)

Se **añade** un job `windows` (los jobs Linux actuales se conservan):
1. `windows-latest`, Python 3.12.
2. Correr la suite completa con el runner existente: `shell: bash`, `PYBIN=python`, MinGW en PATH
   (`choco install mingw`). Evidencia de que C++ doctest + `.dll` + pytest pasan en Windows.
3. Construir `libgamecore.dll`.
4. Construir el `.exe` con PyInstaller.
5. **Smoke sin dependencias de dev:** lanzar el `.exe` en un paso/job que **NO** hizo
   `pip install`, con arranque headless auto-salida (`QT_QPA_PLATFORM=offscreen`, un tick,
   `exit 0`). Es la única forma de detectar fallos de empaquetado (plugin `qwindows`, backend de
   matplotlib) que el Python del sistema taparía. **Este paso es el gate de evidencia.**
6. Empaquetar el ZIP (exe + dll + driver + guía) como artefacto; en push de **tag**, adjuntarlo
   al **Release** de GitHub (de ahí lo baja el cliente).

## 8. Cambios de código (mínimos y justificados)

- `simulator/core_bridge.py`:
  - Elegir extensión por plataforma: `libgamecore.dll` en Windows, `.so` en Linux.
  - En app **congelada** (`getattr(sys, "frozen", False)` / `sys._MEIPASS`): **nunca** invocar
    `g++`; cargar la lib empaquetada, o fallar con mensaje claro (el médico no tiene compilador).
  - Resolver rutas robustas bajo PyInstaller (`RAIZ`/`SO_PATH` y el `sys.path.insert(...simulator)`
    de `fuente.py` hoy asumen árbol de repo y se rompen congelados).
- `dashboard/app.py`: soportar `--serial auto` + función de detección/selección de puerto COM.
- **Fijar versiones exactas** de dependencias (hoy `>=`) para reproducibilidad y compatibilidad
  con hooks de PyInstaller. Un archivo de lock/requirements fijados; la fuente de versiones sale
  de resolver en CI.

**Tests (TDD, obligatorio):**
- Detección de puerto: función pura testeable con `list_ports` mockeado (0/1/N puertos CP210x).
- `core_bridge`: selección de extensión y rama "congelada no compila" con `sys.platform`/`sys.frozen`
  mockeados. La suite existente (52c/2174a C++ + ~101 pytest) debe seguir verde en Linux **y**
  ahora también en Windows (CI).

## 9. Verificación y evidencia (gate de "listo")

"Listo" NO es "compiló". El gate es el **§7.5**: el `.exe` arranca en una máquina/paso sin las
dependencias de dev. Además: suite verde en el job Windows; ZIP adjunto al Release descargable.
Sin ese lanzamiento limpio, no se declara terminado (regla "no declarar listo sin evidencia").

## 10. Entrega limpia

Todo esto vive en el repo de desarrollo con normalidad (con `CLAUDE.md`/`superpowers`). El
snapshot de entrega al cliente depura rastros de IA como ya está previsto
(`preparar-entrega`), pero **los scripts, el CI y el empaquetado son entregables legítimos** y
se conservan. El ZIP del release que baja el cliente no contiene el árbol de desarrollo.

## 11. Riesgos y mitigaciones

- **PyInstaller + PyQt6 + matplotlib** es la parte genuinamente frágil y solo depurable por
  iteración en CI (no en Linux local). *Mitigación:* el `.exe` se **construye y smoke-testea en
  CI antes de publicar** el release; si el freeze falla, no se publica y se itera el build (no se
  entrega un fallback a medias).
- **Driver CP210x** no instalado → sin puerto COM. *Mitigación:* driver offline en el ZIP +
  mensaje claro del auto-detect.
- **Falso verde de empaquetado** (deps del sistema tapan un fallo del bundle). *Mitigación:* el
  smoke sin `pip install` del §7.5.

## 12. Fuera de alcance (YAGNI)

- El médico **no** flashea firmware ni compila nada (recibe el ESP32 ya flasheado).
- **No** se empaqueta el simulador pygame en el paquete del médico (el modo práctica del propio
  dashboard cubre "usar sin hardware").
- **No** onefile (se elige onedir por robustez).
- **No** se reescribe el runner de tests a Python (se reutiliza el bash existente).

## 13. Items abiertos

- Ninguno bloqueante. Chip (CP210x) y modelo del cliente (ZIP) confirmados. Las versiones exactas
  a fijar salen del primer resolve en CI durante la implementación.

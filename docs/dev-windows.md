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

#!/usr/bin/env bash
# ============================================================================
#  run_all_tests.sh — corre TODOS los tests del proyecto y reporta verde/rojo.
# ----------------------------------------------------------------------------
#  1. Tests unitarios de C++ (GameCore) con doctest, compilados con g++.
#  2. Construye GameCore.so (lo necesita el simulador y el golden_runner).
#  3. Golden vectors + integracion + protocolo en Python (pytest).
#
#  No requiere PlatformIO: la logica portable se compila directo con g++.
#  Salida: codigo 0 si TODO esta verde; != 0 si algo falla.
#
#  NOTA: se usan rutas RELATIVAS (tras cd al raiz) porque la ruta del proyecto
#  puede contener espacios ("Tapete Interactivo"), que romperian un -I sin comillas.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

GAMECORE="firmware/lib/GameCore"
VENDOR="firmware/test/vendor"
TESTDIR="firmware/test"
BUILD="build"
mkdir -p "$BUILD"

CXX="${CXX:-g++}"
INCLUDES=(-I"$GAMECORE" -I"$VENDOR" -I"$TESTDIR")
CXXFLAGS=(-std=c++17 -Wall -Wextra -O1 "${INCLUDES[@]}")

# En Windows (Git Bash/MSYS) los binarios de test se enlazan estaticos: si no,
# el .exe carga los DLL de runtime de MinGW (libstdc++/libgcc/winpthread) desde
# el PATH y Git-for-Windows trae una copia incompatible que lo hace crashear al
# arrancar. Estatico elimina esa busqueda. En Linux no se toca nada.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) CXXFLAGS+=(-static -static-libgcc -static-libstdc++) ;;
esac

shopt -s nullglob
CORE_SRCS=( "$GAMECORE"/*.cpp "$GAMECORE"/modes/*.cpp )

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YEL=$'\033[1;33m'; NC=$'\033[0m'
FAILED=0
ran_any=0

echo "=============================================================="
echo " 1) Tests unitarios C++ (doctest)"
echo "=============================================================="
if [ ! -f "$VENDOR/doctest.h" ]; then
  echo "${YEL}AVISO:${NC} falta $VENDOR/doctest.h"
fi
for d in "$TESTDIR"/test_*/; do
  srcs=( "$d"*.cpp )
  [ ${#srcs[@]} -eq 0 ] && continue
  ran_any=1
  name="$(basename "$d")"
  bin="$BUILD/$name"
  echo "--- compilando $name ---"
  if "$CXX" "${CXXFLAGS[@]}" "${srcs[@]}" "${CORE_SRCS[@]}" -o "$bin" 2>&1; then
    if "./$bin"; then
      echo "${GREEN}OK${NC} $name"
    else
      rc=$?
      echo "${RED}FALLO (runtime, rc=$rc)${NC} $name"; FAILED=1
    fi
  else
    echo "${RED}FALLO (compilacion)${NC} $name"; FAILED=1
  fi
done
[ "$ran_any" -eq 0 ] && echo "${YEL}(aun no hay tests C++)${NC}"

echo
echo "=============================================================="
echo " 2) Construir GameCore.so (para simulador / golden_runner)"
echo "=============================================================="
if [ -f "$GAMECORE/bridge.cpp" ]; then
  if "$CXX" -std=c++17 -O2 -fPIC -shared -I"$GAMECORE" "${CORE_SRCS[@]}" \
        -o "$BUILD/libgamecore.so" 2>&1; then
    echo "${GREEN}OK${NC} build/libgamecore.so"
  else
    echo "${RED}FALLO${NC} al construir libgamecore.so"; FAILED=1
  fi
else
  echo "${YEL}(GameCore aun no tiene bridge.cpp; se crea en la Fase 3)${NC}"
fi

echo
echo "=============================================================="
echo " 3) Tests Python (golden vectors + integracion + protocolo)"
echo "=============================================================="
# Se usa el python del venv del proyecto via "-m pytest"; NO se depende de
# 'activate' ni de los console scripts (.venv/bin/pytest): sus shebangs se
# rompen si el proyecto cambia de ruta. PYBIN es overridable (para tests).
PYBIN="${PYBIN:-}"
if [ -z "$PYBIN" ]; then
  if [ -x ".venv/bin/python" ]; then PYBIN=".venv/bin/python"; else PYBIN="python3"; fi
fi
if "$PYBIN" -m pytest --version >/dev/null 2>&1; then
  "$PYBIN" -m pytest -q . --ignore=.venv --rootdir=. 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "${GREEN}OK${NC} pytest"
  elif [ "$rc" -eq 5 ]; then
    echo "${YEL}(pytest no encontro tests todavia)${NC}"
  else
    echo "${RED}FALLO${NC} pytest (rc=$rc)"; FAILED=1
  fi
else
  # Falso-verde evitado: si los tests Python no corren, es ROJO, no un aviso.
  echo "${RED}FALLO:${NC} pytest no disponible (los tests Python NO se ejecutaron)."
  echo "  Recrea el venv: python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt -r simulator/requirements.txt -r dashboard/requirements.txt"
  FAILED=1
fi

echo
echo "=============================================================="
if [ "$FAILED" -eq 0 ]; then
  echo "${GREEN}>>> TODO VERDE <<<${NC}"
  exit 0
else
  echo "${RED}>>> HAY FALLOS <<<${NC}"
  exit 1
fi

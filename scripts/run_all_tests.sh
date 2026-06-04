#!/usr/bin/env bash
# ============================================================================
#  run_all_tests.sh — corre TODOS los tests del proyecto y reporta verde/rojo.
# ----------------------------------------------------------------------------
#  1. Tests unitarios de C++ (GameCore) con doctest, compilados con g++.
#  2. Golden vectors + integracion + protocolo en Python (pytest).
#  3. Construye GameCore.so (lo necesita el simulador y el golden_runner).
#
#  No requiere PlatformIO: la logica portable se compila directo con g++.
#  Salida: codigo 0 si TODO esta verde; != 0 si algo falla.
# ============================================================================
set -u

# Raiz del repo = carpeta padre de este script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

GAMECORE="$ROOT/firmware/lib/GameCore"
VENDOR="$ROOT/firmware/test/vendor"
TESTDIR="$ROOT/firmware/test"
BUILD="$ROOT/build"
mkdir -p "$BUILD"

CXX="${CXX:-g++}"
CXXFLAGS="-std=c++17 -Wall -Wextra -O1 -I$GAMECORE -I$VENDOR"

# Fuentes de la logica portable (se enlazan a cada binario de test).
shopt -s nullglob
CORE_SRCS=( "$GAMECORE"/*.cpp "$GAMECORE"/modes/*.cpp )

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YEL=$'\033[1;33m'; NC=$'\033[0m'
FAILED=0
ran_any=0

echo "=============================================================="
echo " 1) Tests unitarios C++ (doctest)"
echo "=============================================================="
if [ ! -f "$VENDOR/doctest.h" ]; then
  echo "${YEL}AVISO:${NC} falta $VENDOR/doctest.h (se descarga en la Fase 2)."
fi
for d in "$TESTDIR"/test_*/; do
  srcs=( "$d"*.cpp )
  [ ${#srcs[@]} -eq 0 ] && continue
  ran_any=1
  name="$(basename "$d")"
  bin="$BUILD/$name"
  echo "--- compilando $name ---"
  if $CXX $CXXFLAGS "${srcs[@]}" "${CORE_SRCS[@]}" -o "$bin" 2>&1; then
    if "$bin"; then
      echo "${GREEN}OK${NC} $name"
    else
      echo "${RED}FALLO (runtime)${NC} $name"; FAILED=1
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
if [ ${#CORE_SRCS[@]} -gt 0 ] && [ -f "$GAMECORE/bridge.cpp" ]; then
  if $CXX -std=c++17 -O2 -fPIC -shared -I"$GAMECORE" "${CORE_SRCS[@]}" \
        -o "$BUILD/libgamecore.so" 2>&1; then
    echo "${GREEN}OK${NC} build/libgamecore.so"
  else
    echo "${RED}FALLO${NC} al construir libgamecore.so"; FAILED=1
  fi
else
  echo "${YEL}(GameCore aun no tiene bridge.cpp; se crea en la Fase 2/3)${NC}"
fi

echo
echo "=============================================================="
echo " 3) Tests Python (golden vectors + integracion + protocolo)"
echo "=============================================================="
# Activa el venv del proyecto si existe.
if [ -f "$ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi
if command -v pytest >/dev/null 2>&1; then
  if pytest -q "$ROOT" \
        --ignore="$ROOT/.venv" \
        --rootdir="$ROOT" 2>&1; then
    echo "${GREEN}OK${NC} pytest"
  else
    rc=$?
    # pytest devuelve 5 cuando NO recolecta ningun test: no es un fallo real.
    if [ "$rc" -eq 5 ]; then
      echo "${YEL}(pytest no encontro tests todavia)${NC}"
    else
      echo "${RED}FALLO${NC} pytest (rc=$rc)"; FAILED=1
    fi
  fi
else
  echo "${YEL}AVISO:${NC} pytest no disponible. Crea el venv: python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt"
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

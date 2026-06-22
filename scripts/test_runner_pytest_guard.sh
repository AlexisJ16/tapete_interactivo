#!/usr/bin/env bash
# Regresion: run_all_tests.sh debe FALLAR (exit != 0) cuando pytest no esta
# disponible, en vez de imprimir "TODO VERDE" saltando los tests Python.
# (Antes del fix, pytest ausente -> solo un AVISO -> exit 0: falso verde.)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Stub: un "python" sin pytest (cualquier 'python -m pytest ...' falla).
STUB_DIR="$(mktemp -d)"
trap 'rm -rf "$STUB_DIR"' EXIT
cat > "$STUB_DIR/nopytest-python" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
chmod +x "$STUB_DIR/nopytest-python"

out="$(PYBIN="$STUB_DIR/nopytest-python" bash "$ROOT/scripts/run_all_tests.sh" 2>&1)"
rc=$?

if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q "pytest no disponible"; then
  echo "OK: el runner marca rojo (rc=$rc) cuando pytest no esta disponible"
  exit 0
fi
echo "FALLO: el runner NO marco rojo con pytest ausente (rc=$rc)"
printf '%s\n' "$out" | tail -5
exit 1

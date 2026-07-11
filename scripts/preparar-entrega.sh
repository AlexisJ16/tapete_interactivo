#!/usr/bin/env bash
# Prepara la ENTREGA del proyecto: un snapshot limpio, sin historial de git y sin
# rastros de las herramientas de IA con las que se desarrollo.
#
#   ./scripts/preparar-entrega.sh [destino]        (por defecto: ../tapete_entrega)
#
# Hace, en una pasada:
#   1. Snapshot del arbol versionado (git archive) -> el destino queda SIN .git.
#   2. Borra las rutas de herramientas y limpia las menciones que quedan dentro de
#      archivos que si se entregan.
#   3. VERIFICA que no queda ninguna mencion (si queda, aborta: no se entrega a medias).
#   4. Corre la suite completa SOBRE EL ARBOL DEPURADO (no sobre el original: la poda
#      podria haber roto algo).
#   5. git init + un unico commit inicial, a nombre de quien recibe el proyecto.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$(dirname "$REPO")/tapete_entrega}"
ROJO=$'\e[31m'; VERDE=$'\e[32m'; NC=$'\e[0m'

cd "$REPO"
if [ -n "$(git status --porcelain)" ]; then
    echo "${ROJO}ABORTA:${NC} hay cambios sin commitear. El snapshot sale de HEAD."
    exit 1
fi

if [ -e "$DEST" ]; then
    echo "${ROJO}ABORTA:${NC} '$DEST' ya existe. Borralo o elige otro destino."
    exit 1
fi

echo "== 1/5  Snapshot de HEAD ($(git rev-parse --short HEAD)) -> $DEST"
mkdir -p "$DEST"
git archive --format=tar HEAD | tar -x -C "$DEST"

echo "== 2/5  Depurando rastros de las herramientas de desarrollo"
cd "$DEST"
rm -rf docs/superpowers .claude CLAUDE.md scripts/wokwi-mcp.sh scripts/preparar-entrega.sh

# Menciones dentro de archivos que SI se entregan.
# El ROADMAP se entrega (decision del autor), pero su §5 explica como se purga esta
# misma entrega: eso no viaja con el producto.
sed -i '/^## 5\. Cierre/,$d' docs/ROADMAP.md
sed -i 's|`CLAUDE\.md` recoge las reglas durables; este documento, lo que cambia\.|Este documento recoge lo que cambia: estado y trabajo pendiente.|' docs/ROADMAP.md
sed -i '/^## MCP servers/,/^## [^M]/{ /^## [^M]/!d }' docs/hardware/TOOLING.md
sed -i '/^## Subagentes y skills/,$d' docs/hardware/TOOLING.md
python3 - <<'PY'
import pathlib
p = pathlib.Path("docs/hardware/datasheets/README.md")
p.write_text(p.read_text(encoding="utf-8").replace(
    "El subagente `datasheet-reader`\n(`.claude/agents/datasheet-reader.md`) extrae pinouts/specs de aquí.",
    "De aquí salen los pinouts y las especificaciones citadas en el diseño."),
    encoding="utf-8")
PY
sed -i 's|^// Task 2\.6 (docs/superpowers/plans/[^)]*): las|// Robustez: las|' firmware/test/test_core/test_gameengine.cpp
sed -i '/docs\/superpowers/d' docs/hardware/kicad/README.md scripts/gen_audio.py
# Restos genericos (rutas de specs/planes citadas en prosa).
grep -rlIiE "superpowers" . 2>/dev/null | while read -r f; do sed -i '/superpowers/d' "$f"; done

echo "== 3/5  Verificando que no queda ningun rastro"
# Se excluyen los binarios generados del articulo (.docx/.pdf): sus metadatos se
# revisan aparte; el grep de texto no los interpreta.
if SOBRAN=$(grep -rlIiE "claude|superpowers|anthropic" . 2>/dev/null); then
    echo "${ROJO}ABORTA:${NC} quedan menciones en:"; echo "$SOBRAN"
    exit 1
fi
echo "   sin menciones a las herramientas de desarrollo"

echo "== 4/5  Suite completa sobre el arbol DEPURADO"
ln -s "$REPO/.venv" .venv            # solo para correr los tests; .venv esta gitignored
if ! ./scripts/run_all_tests.sh >/tmp/entrega_tests.log 2>&1; then
    rm -f .venv
    echo "${ROJO}ABORTA:${NC} la suite falla sobre el arbol depurado. Log: /tmp/entrega_tests.log"
    exit 1
fi
rm -f .venv
echo "   $(grep -c "" /tmp/entrega_tests.log) lineas de salida; suite ${VERDE}VERDE${NC}"

echo "== 5/5  Repositorio nuevo, un unico commit"
git init -q -b main
git add -A
git -c user.name="Tapete Interactivo" -c user.email="entrega@local" \
    commit -q -m "Initial commit"

echo
echo "${VERDE}LISTO${NC}  $DEST"
echo "   $(git rev-list --count HEAD) commit · $(git ls-files | wc -l) archivos · sin historial previo"
echo
echo "Comprueba a mano antes de enviar:"
echo "   - metadatos de docs/articulo/*.docx y *.pdf (el grep de texto no los ve)"
echo "   - que el ZIP del dashboard para el medico va aparte (lo produce el CI en Windows)"

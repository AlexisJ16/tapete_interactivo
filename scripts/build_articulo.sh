#!/usr/bin/env bash
# Construye el articulo a partir de la fuente Markdown: .docx (para revision) y .pdf.
# Las citas se resuelven con citeproc contra referencias.bib, en estilo APA 7 (apa.csl).
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ART="$RAIZ/docs/articulo"
SRC="$ART/articulo.md"
BIB="$ART/referencias.bib"
CSL="$ART/apa.csl"
SALIDA="$ART/Articulo_Tapete_Interactivo"

for f in "$SRC" "$BIB" "$CSL"; do
  [[ -f "$f" ]] || { echo "FALTA: $f" >&2; exit 1; }
done

command -v pandoc >/dev/null || { echo "pandoc no esta instalado" >&2; exit 1; }

comun=(--citeproc --bibliography="$BIB" --csl="$CSL"
       --resource-path="$ART:$RAIZ/docs" --number-sections)

echo "==> .docx"
pandoc "$SRC" "${comun[@]}" -o "$SALIDA.docx"

# xelatex y no pdflatex: el texto lleva Unicode (Ω, µ) que pdflatex no compone.
echo "==> .pdf"
pandoc "$SRC" "${comun[@]}" --pdf-engine=xelatex \
  -V geometry:margin=2.5cm -V fontsize=11pt -V lang=es \
  -V mainfont="DejaVu Serif" -V sansfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" \
  -o "$SALIDA.pdf"

# Una cita sin resolver aparece como [@clave] en la salida: es un error silencioso
# que se coleria hasta el revisor.
echo "==> citas sin resolver"
if pandoc "$SALIDA.docx" -t plain | grep -n '\[@' ; then
  echo "ERROR: hay citas sin resolver (ver arriba)" >&2
  exit 1
fi
echo "ninguna"

echo
echo "OK: $SALIDA.docx"
echo "OK: $SALIDA.pdf"

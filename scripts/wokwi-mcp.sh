#!/usr/bin/env bash
# Wrapper del servidor MCP de Wokwi.
#
# WHY: el proceso de Claude Code a menudo NO hereda WOKWI_CLI_TOKEN aunque el
# humano crea haberlo sourceado antes de lanzar `claude` (verificado 2026-07-02:
# el proceso de CC no tenía el token). Este wrapper sourcea ~/.secrets él mismo,
# así el token está garantizado sin depender de cómo se lanzó CC.
#
# Registrar como MCP local (no se commitea; ruta de máquina):
#   claude mcp add wokwi -s local -- <repo>/scripts/wokwi-mcp.sh
export PATH="$HOME/bin:$PATH"                 # wokwi-cli vive en ~/bin
[ -f "$HOME/.secrets" ] && . "$HOME/.secrets" # exporta WOKWI_CLI_TOKEN
exec wokwi-cli mcp "$@"

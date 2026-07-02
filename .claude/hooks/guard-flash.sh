#!/usr/bin/env bash
# guard-flash — PreToolUse/Bash guard.
# Bloquea que el AGENTE flashee o abra el serial del ESP32 (hay UN solo ESP32,
# alimentado solo por USB del PC). El flasheo y el monitor serial se hacen a
# MANO, conscientemente. No hay decisión que tomar aquí salvo: ¿este comando
# toca el flasheo/serial? -> exit 2 (bloquea, stderr va a Claude). Si no -> exit 0.
#
# Sintaxis verificada: el input llega por stdin como JSON; el comando Bash está
# en .tool_input.command (code.claude.com/docs/en/hooks).

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"

# Formas peligrosas (case-insensitive): carga de firmware, esptool, apertura de
# serie del ESP32 (pio device monitor / acceso directo a /dev/ttyUSB|ACM).
if printf '%s' "$cmd" | grep -Eiq '(-t[[:space:]]+upload|--target[[:space:]]+upload|(^|[[:space:];&|(])esptool|/dev/tty(USB|ACM)|device[[:space:]]+monitor|pio[[:space:]].*[[:space:]]upload)'; then
  echo "BLOQUEADO por guard-flash: comando de flasheo/serial del ESP32 detectado -> \"$cmd\". Hay UN solo ESP32 alimentado solo por USB; el flasheo y el monitor serial se hacen MANUALMENTE (no desde el agente). Ver docs/hardware/flashing.md." >&2
  exit 2
fi
exit 0

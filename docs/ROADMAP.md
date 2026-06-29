# Roadmap — próximos pasos

El sistema está **completo y validado en software** (6 fases base + SP1 todo
verde, firmware compila para `esp32dev`). Este documento recoge el trabajo que
sigue, para retomarlo en una conversación nueva. Mantener siempre la disciplina
del proyecto: **TDD**, **una sola fuente de verdad** (`GameCore`), tests en
verde antes de avanzar (ver `CLAUDE.md`).

> **PUNTO DE CONTINUACIÓN:** SP1 está **mergeado a `main`** (commit `4cf3543`,
> 2026-06-24; rama `sp1-logica-adaptable` conservada y sincronizada). El
> **siguiente paso es SP2** — evidencia funcional + analítica + CI — en definición
> (brainstorming → spec → plan). Crear rama `sp2-evidencia-analitica` desde `main`
> al arrancar la implementación.

## 1. Puesta en marcha del hardware físico (lo único no validable en software)

- [x] **6 resistencias de 10 kΩ** (pull-down de los FSR — NO las de 110 Ω, que
      son para los LEDs) — **conseguidas (2026-06-22)**, junto con la microSD.
- [ ] Montar en protoboard según el paquete **`docs/hardware/`**: `00_diseno_circuito.md`
      (maestro — net list, zonificación, secuencia de armado, checklist con multímetro) y los
      planos `plano-A-protoboard.svg` / `plano-A-esquematico.svg`. Referencia textual adicional:
      `docs/hardware/wiring.md`.
- [ ] LEDs a brillo pleno: alimentar desde **5 V** con transistor por grupo
      (2N2222) o **ULN2803**; el GPIO solo controla.
- [ ] Grabar la **microSD** (ya en mano) en FAT32 con `/mp3/0001.mp3`..`/mp3/0004.mp3`
      (instrucción, acierto, error, éxito). Ver `audio/README.md`.
- [ ] `cp firmware/src/secrets.h.example firmware/src/secrets.h` + credenciales.
- [ ] Flashear y **calibrar `cfg::UMBRAL_PISADA`** observando el Serial al pisar
      (`docs/hardware/flashing.md`).
- [ ] Verificar end-to-end con el dashboard: `app.py --tcp <IP>`.

## 2. Mejoras de funcionalidad (lógica → siempre con tests/golden primero)

- [ ] **Patrones de parpadeo** más ricos (§3 de la spec): barrido de inicio de
      ronda; error = 3 parpadeos rápidos; acierto = LED sólido. Hoy el feedback
      es encender/apagar + sonido. Modelarlo no bloqueante en el motor y fijarlo
      con golden vectors.
- [ ] **Modo Equilibrio — subnivel "orden específico"** (hoy es "cualquier
      orden"). Añadir flag y tests.
- [ ] **Modo Memoria — tolerancia de tiempo** por pisada (timeout de entrada
      configurable) y reintentos antes de bajar longitud.
- [ ] **Modo Velocidad — ventana adaptativa** según desempeño reciente.
- [ ] **Parámetros configurables por el terapeuta** desde el dashboard (tiempos,
      longitudes), no solo niveles fijos en `Config.h`.

## 3. Dashboard / simulador

- [ ] **Gráficas de evolución** (matplotlib embebido) por perfil: histórico de
      hits/errores/rt entre sesiones.
- [ ] **Vista de historial** de sesiones (tabla filtrable por perfil) + abrir
      reportes guardados.
- [ ] **Reconexión TCP automática** si el ESP32 se cae (hoy `FuenteTCP` no
      reintenta).
- [ ] **Sim pygame como cliente/servidor TCP**: que el terapeuta vea en vivo lo
      que el niño juega en el simulador (hoy `servidor.py` existe pero la ventana
      pygame usa su propio core embebido; unirlos cierra el bucle simulador↔dashboard
      en red, idéntico al ESP32).

## 4. Calidad e infraestructura

- [ ] **CI** (GitHub Actions): correr `scripts/run_all_tests.sh` y `pio run -e
      esp32dev` en cada push.
- [ ] **Golden vectors**: ampliar a más niveles y añadir escenarios `strict`
      (stream exacto) para Memoria y Equilibrio (hoy strict solo en Velocidad).
- [ ] Persistir **calibración del umbral** por dispositivo.

## Notas de arranque para la próxima sesión

- Línea base: `./scripts/run_all_tests.sh` → TODO VERDE; `pio run -e esp32dev` →
  SUCCESS. Si algo está en rojo al empezar, arreglarlo antes de añadir nada.
- Esta máquina tiene **display real** (`DISPLAY=:0` / Wayland): se pueden lanzar
  el simulador y el dashboard en pantalla, y generar capturas con
  `scripts/demo_visual.py`.

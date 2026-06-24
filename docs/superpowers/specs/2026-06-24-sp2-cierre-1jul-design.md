# SP2 (recortado) + cierre del proyecto de grado — Diseño (1-jul)

> **Restricción dominante:** entrega del **proyecto de grado completo el 2026-07-01**
> (software + hardware de banco + documento honesto + demo). 7 días desde el 24-jun.
> SP2 software se recorta al **mínimo demostrable**. El cuello de botella es el
> montaje físico (manos de Alexis); el software sirve para **generar la evidencia y
> las figuras** que el documento necesita.

## 1. Alcance

**Dentro (mi carril, software + borrador):**
- Generador de evidencia determinista (simulador / `.so`) → dataset + figuras PNG.
- Analítica en el dashboard: vista de evidencia/historial con matplotlib embebido.
- Robustez de demo: reconexión TCP simple en `FuenteTCP`.
- Captura de banco cuando el HW esté flasheado (datos reales → figuras de banco).
- Borrador honesto del documento + figuras.

**Fuera (post 1-jul, salvo que sobre tiempo):**
- Unir la ventana pygame al servidor TCP (frente red completo).
- CI en GitHub Actions.
- Patrones de parpadeo ricos en GameCore; golden `strict` en los 3 modos.

## 2. Integridad académica (no negociable)

Las figuras representan **el comportamiento del sistema en simulación y en banco**,
NO resultados con pacientes. El documento se reencuadra de "evaluación clínica
realizada" (comité de ética, entrevistas — hoy afirmado en falso) a **validación
funcional de banco**. Corrección **RGB→blanco** justificada. Lo clínico pasa a
"trabajo futuro". Ver memoria `tapete-contexto-academico` y `tapete-deadline-entrega`.

## 3. Objetivos de evidencia (qué demuestran las figuras)

| # | Evidencia | Fuente | Depende de HW |
|---|---|---|---|
| E1 | Determinismo / reproducibilidad (mismo seed → mismo stream) | golden vectors | No |
| E2 | Lógica adaptable SP1: nivel sugerido sigue al desempeño | simulador (seeds) | No |
| E3 | Comportamiento por modo: rt, hits/errores por nivel | simulador (seeds) | No |
| E4 | Evolución entre sesiones por perfil | simulador (seeds) | No |
| E5 | Latencia del lazo pisada→feedback | ESP32 (banco) | Sí |
| E6 | Detección FSR (umbral, fiabilidad) | ESP32 (banco) | Sí |

E1–E4 se materializan **ya**, sin hardware. E5–E6 entran en el sync de banco.

## 4. Componentes de software

### A. Generador de evidencia — `scripts/generar_evidencia.py`
- Corre sesiones deterministas contra el `.so` (vía `core_bridge`) con seeds fijos,
  por modo y nivel; persiste a SQLite (reutiliza `storage.py`) y/o CSV.
- Emite figuras PNG en `docs/evidencia/` (matplotlib, backend Agg).
- Determinista y reproducible (mismos seeds → mismas figuras). Es la base de E1–E4.

### B. Analítica en el dashboard — vista de evidencia/historial
- Nueva vista/pestaña en `dashboard/app.py` (PyQt6) con matplotlib embebido.
- Lee el histórico de `storage.py` (sesiones/eventos ya persistidos).
- Gráficas: evolución hits/errores/rt por perfil (E4) y curva de adaptación nivel↔desempeño (E2).
- Botón "exportar figura" (PNG) para el documento.

### C. Robustez de demo — `dashboard/fuente.py`
- `FuenteTCP`: reconexión automática simple (reintento con backoff acotado) si el
  ESP32 cae. Sin cambiar el contrato de la fuente.

### D. Sync de banco (cuando el HW esté flasheado)
- Correr sesiones reales (`app.py --tcp <IP>`), capturar a SQLite, generar E5–E6.

## 5. Disciplina

- **TDD donde aplica**: lógica de agregación/generación con pytest (determinismo
  verificable). Las figuras se validan visualmente; su *dato* se testea.
- **Una sola fuente de verdad**: la analítica **lee** datos; NO duplica lógica de
  GameCore. El generador usa el mismo `.so`.
- **Determinismo**: seeds fijos → datasets y figuras reproducibles.

## 6. Plan de 7 días (dos carriles)

| Día | Tu carril (físico + documento) | Mi carril (código + borrador) | Sync |
|---|---|---|---|
| 24-jun | Iniciar montaje (`docs/diagrama-conexiones.html`) | Generador de evidencia + figuras E1–E3 | |
| 25-jun | Montaje | Figuras E2/E4 + analítica en dashboard | |
| 26-jun | Terminar montaje → flashear | Reconexión TCP + demo end-to-end; firmware/calibración listos | HW vivo |
| 27-jun | Calibrar umbral + sesiones de banco | Datos reales → figuras E5–E6 | Datos reales |
| 28-jun | Revisar documento | Borrador honesto (Metodología/Resultados) con figuras | |
| 29-jun | Cerrar documento + trazabilidad | Demo grabada (sim + banco) | |
| 30-jun | Repaso final | Snapshot limpio al cliente + suite verde sobre árbol depurado | Entrega lista |

**Riesgo principal:** atraso del montaje. **Mitigación:** E1–E4 y el borrador no
dependen del HW; el carril de software avanza igual y E5–E6 se integran al llegar.

## 7. Documento honesto (SP4 — borrador mío, cierre de Alexis)

- Reescribir Metodología/Resultados a validación de banco con E1–E6.
- Justificar RGB→blanco (accesibilidad sin color, costo, PWM robusto).
- Trazabilidad objetivo específico → evidencia (tabla E#).
- Eliminar/reencuadrar afirmaciones clínicas no realizadas → "trabajo futuro".

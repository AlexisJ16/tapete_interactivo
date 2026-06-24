# Artículo — reencuadre a validación honesta (nota de revisión)

Esta nota resume **qué cambió** entre el artículo original (`Articulo_Tapete_Interactivo.docx`)
y el borrador honesto (`articulo_honesto_borrador.docx` / `.md`), y **por qué**.
Es un documento de trabajo interno para sustentar la revisión; no forma parte del artículo.

## Motivo

El artículo original describía en tiempo pasado una **evaluación con pacientes en un
entorno terapéutico real** (fundación, cinco semanas, comité de ética, consentimiento
informado, entrevistas a docentes y padres) y una sección de Resultados con
**placeholders** (`[N]`, `[X]`, `[ ]`). Esa evaluación **no se realizó**: el aporte
verificable del proyecto es la **viabilidad técnica y funcional** del dispositivo y de su
lógica de dificultad adaptativa. Reportar lo no realizado es un riesgo de integridad
académica. El reencuadre reporta solo lo que existe y traslada lo clínico a trabajo futuro.

## Cambios por sección

| Sección | Original | Borrador honesto |
|---|---|---|
| Resumen / Abstract | "La evaluación se realizó en un entorno terapéutico real" | "La validación se realizó mediante simulación determinista de la lógica + pruebas de banco, sin pruebas con pacientes" |
| Objetivo específico (i) | "módulos de iluminación LED **RGB**" | "módulos de iluminación LED" (decisión RGB→blanco justificada en §4.1) |
| Objetivo específico (iii) | "evaluar el comportamiento funcional en un entorno terapéutico real" | "validar el comportamiento funcional mediante simulación determinista y pruebas de banco" |
| §4.1 Diseño electrónico | "tiras de LED **RGB WS2812B**" | LEDs de luz blanca por PWM, con justificación de ingeniería (accesibilidad sin color, robustez, costo) |
| §4.4 Protocolo | Evaluación con niños, 5 semanas, comité de ética, entrevistas (en pasado) | Protocolo de validación en dos niveles: simulación determinista (E1–E4) + banco (E5–E6); lo clínico → trabajo futuro |
| §5 Resultados | Prosa en pasado con placeholders `[N]/[X]/[ ]` | Resultados E1–E4 con cifras reales de simulación + E5–E6 marcadas como pendientes de banco + tabla de trazabilidad objetivo→evidencia |
| §6 Análisis | "participación activa de los niños", "contextos terapéuticos reales" | Análisis de la viabilidad técnica y la lógica adaptativa; limitaciones explícitas; lo clínico como trabajo futuro |

## Procedencia de las cifras (§5)

Todas las cifras del borrador provienen de la simulación determinista (semilla fija,
reproducible), no de pacientes:

- **E1 (reproducibilidad):** dos ejecuciones idénticas confirman el determinismo.
- **E2 (adaptación, nivel 2):** tasa de acierto 0 %→100 % según habilidad; recomendación
  baja/mantiene/sube en 0–10 % / 20–30 % / ≥40 %.
- **E3 (por nivel, habilidad 80 %):** rondas 5/8/10/12 y 1 error por sesión (niveles 1–4).
- **E4 (trayectoria):** hábil 1→2→3→4 (satura); con dificultad 4→3→2→1 (satura).

Regenerables con `scripts/generar_evidencia.py` (figuras) — mismos parámetros, semilla 777.

## Pendiente (de Alexis / al montar el hardware)

- **E5/E6 (banco):** latencia del lazo pisada→retroalimentación y fiabilidad de detección
  FSR. Capturar con el dashboard conectado al ESP32 e integrar en §5.5.
- **Modos memoria y equilibrio:** la evidencia de simulación cubre solo Velocidad;
  extender la validación análoga (o mantener el alcance declarado en §6).
- Revisión final de estilo y consistencia con el anteproyecto V3 (RGB→blanco también
  aparece allí).

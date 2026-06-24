# Trazabilidad: anteproyecto-guía → artículo (material de sustentación)

Documento de apoyo para defender el artículo frente a la guía del proyecto. **No
es un entregable**: es una ayuda interna para la sustentación.

## Marco

- El **anteproyecto V3** es el **documento guía** que entrega el director para iniciar
  el proyecto. Es prospectivo (describe lo planeado) y **se conserva sin cambios**.
- El **artículo** (`articulo_honesto_borrador`) es el **entregable** desarrollado. Es
  donde se reporta lo logrado y se justifican las desviaciones respecto a la guía.
- Prueba de coherencia: guía + artículo deben contar **una sola historia veraz** —
  "se planeó X; se logró la validación funcional; lo clínico quedó como trabajo futuro"—
  sin que el artículo afirme nada no realizado ni contradiga la guía sin justificar.

## Tabla de trazabilidad

| Elemento de la guía | Cómo lo aborda el artículo | Estado |
|---|---|---|
| **Pregunta de investigación**: elementos clave de un tapete interactivo eficaz como apoyo terapéutico | §6 los identifica: integración multisensorial coherente, retroalimentación inmediata, dificultad adaptativa y registro objetivo del desempeño | **Respondida** |
| **Objetivo general**: desarrollar el tapete (luces y sonidos) como apoyo terapéutico | Sistema completo (HW de banco + firmware + dashboard) descrito en §4 | **Cumplido** |
| **Obj. (i)**: diseñar el sistema electrónico (FSR + iluminación LED + audio) | §4.1: FSR, iluminación LED y DFPlayer. **Desviación: LED blanco PWM en vez de RGB**, justificada | **Cumplido con desviación justificada** |
| **Obj. (ii)**: firmware con modos terapéuticos adaptables | §4.3 (3 modos) + lógica de dificultad adaptativa, evidenciada en E1–E4 (modo velocidad) | **Cumplido** (memoria/equilibrio: validación análoga pendiente) |
| **Obj. (iii)**: evaluar el comportamiento funcional del prototipo **en un entorno terapéutico real** | §5: validación del **comportamiento funcional** por simulación determinista (E1–E4) + banco (E5–E6, pendiente de montaje). La evaluación **en entorno terapéutico real** NO se realizó → §6 trabajo futuro | **Parcial — desviación de alcance** |

## Las dos desviaciones (y cómo defenderlas)

### 1. Iluminación: RGB → blanco PWM (Obj. i)

- **Guía:** "módulos de iluminación LED RGB / tiras WS2812B".
- **Entregado:** LED de luz blanca por PWM.
- **Defensa (ya en §4.1 del artículo):** decisión de ingeniería justificada por (a)
  accesibilidad —la retroalimentación se basa en posición y estado, no en color, evitando
  excluir a usuarios con alteración de la percepción cromática—; (b) robustez del control
  PWM frente al protocolo temporizado de las tiras direccionables; (c) costo. La **función**
  del objetivo (i) —retroalimentación visual por casilla— se cumple; cambia la tecnología,
  no el propósito. La lógica es independiente del tipo de LED (abstracción de hardware).
- **Riesgo:** bajo. Es un hecho de hardware con justificación técnica sólida.

### 2. Evaluación: "entorno terapéutico real" → validación funcional (Obj. iii)

- **Guía:** evaluar el comportamiento funcional **en un entorno terapéutico real** (pruebas
  con niños en fundación, 5 semanas, comité de ética, entrevistas).
- **Entregado:** validación del **comportamiento funcional** por simulación determinista
  (E1–E4) y pruebas de banco (E5–E6, al completar el montaje). Sin pruebas con pacientes.
- **Defensa (ya en §4.4 y §6 del artículo):** el objetivo (iii) tiene dos componentes —
  *evaluar el comportamiento funcional* (logrado) y *en entorno terapéutico real* (no
  realizado)—. El trabajo se centró en la **viabilidad técnica y funcional**, que es lo
  verificable sin pacientes; la evaluación en entorno terapéutico real requiere protocolo
  clínico (comité de ética, consentimiento, seguimiento) y queda explícitamente como
  **trabajo futuro**. Esto es honesto: el artículo no afirma haber hecho pruebas con niños.
- **Riesgo:** este es el **punto más sensible de la sustentación**. Conviene anticiparlo:
  reconocer que el alcance de evaluación se ajustó respecto a la guía (por el tiempo de
  montaje físico y los requisitos éticos de las pruebas con menores), y que lo entregado —validación funcional
  reproducible— es un resultado sólido y defendible, con la evaluación en entorno real como
  continuación natural.

## Notas menores de consistencia

- La guía menciona análisis estadístico (ANOVA, regresión) para comparar modos: aplica a la
  fase de datos con usuarios reales, que es trabajo futuro. El artículo no lo reporta porque
  no realizó esa fase; coherente.
- La guía describe Wi-Fi/Bluetooth; el sistema entregado usa Wi-Fi/TCP. Sin contradicción
  (la guía dice "Wi-Fi o Bluetooth").

## Conclusión

Guía + artículo son **coherentes y honestos**: el artículo cumple los objetivos (i) y (ii),
aborda el (iii) en su componente funcional y declara lo terapéutico real como trabajo futuro,
y justifica las dos desviaciones. El único punto que exige defensa activa en la sustentación
es el alcance del objetivo (iii).

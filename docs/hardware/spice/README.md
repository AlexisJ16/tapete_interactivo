# Validación analógica con ngspice — Tapete Interactivo

Netlists SPICE que cierran la brecha analógica **antes de soldar**. Se corren en
batch y no necesitan hardware. Herramienta: `ngspice 42` (`sudo apt install ngspice`).

```bash
ngspice -b docs/hardware/spice/divisor_fsr.cir
ngspice -b docs/hardware/spice/grupo_led.cir
```

Los valores son los **reales del inventario** (`../materiales.md`) y del cableado
(`../cableado.md`): pull-down FSR **10 kΩ**, resistencia de grupo LED **2.2 kΩ**.

## 1. Divisor FSR (`divisor_fsr.cir`)

Topología: `3V3 ─[R_FSR]─ nodo(ADC) ─[10 kΩ]─ GND`. El FSR baja su resistencia con
la fuerza, así que `V_nodo` sube con la pisada: `V_nodo = 3.3·10k/(R_FSR+10k)`.

Barrido de `R_FSR` (resultado ngspice, ADC ≈ V_nodo/3.3·4095):

| R_FSR (Ω) | V_nodo (V) | ADC (~cuentas) | Interpretación |
|---|---|---|---|
| 250 | 3.220 | 3995 | pisada muy fuerte (satura arriba del ADC) |
| 500 | 3.143 | 3900 | pisada fuerte |
| 1 000 | 3.000 | 3723 | pisada firme |
| 2 200 | 2.705 | 3357 | pisada firme |
| 4 700 | 2.245 | 2786 | pisada media |
| **10 000** | **1.650** | **2048** | **≈ UMBRAL_PISADA (2000 cuentas)** |
| 22 000 | 1.031 | 1280 | toque leve → ignorado |
| 47 000 | 0.579 | 718 | roce → ignorado |
| 100 000 | 0.300 | 372 | roce → ignorado |
| 1 000 000 | 0.033 | 41 | reposo |
| 10 000 000 | 0.003 | 4 | reposo (sin carga) |

**Conclusiones:**
- Separación limpia **reposo (~4-40 cuentas) ↔ pisada (>2700 cuentas)**: la
  detección por umbral + antirrebote es robusta (no necesita linealidad del ADC).
- `cfg::UMBRAL_PISADA = 2000` corresponde a `R_FSR ≈ 10 kΩ`: una pisada firme
  (R_FSR de 1-5 kΩ) queda muy por encima; un roce (>22 kΩ) por debajo. Bien ubicado.
- El pull-down de **10 kΩ** desplaza la sensibilidad hacia fuerzas altas (detecta
  **pisada**, no roce) — decisión de ingeniería correcta para este uso.
- Acción en hardware: leer el ADC en reposo y al pisar por el Serial y **afinar
  `UMBRAL_PISADA`** al valor real de los 6 canales (`cableado.md` §7 paso 3).

## 2. Grupo LED (`grupo_led.cir`)

Topología: `5V ─[2.2 kΩ]─ ánodo ─(3× LED blanco ‖)─ cátodo ─[ULN V_CE(sat)≈0.9 V]─ GND`.
LED blanco modelado con Vf≈3.0 V a 5 mA; V_CE(sat) del Darlington fijo a 0.9 V (conservador).

Resultado ngspice:

| Magnitud | Valor |
|---|---|
| V(ánodo) | 3.731 V |
| V(cátodo) | 0.900 V (V_CE(sat) del ULN) |
| Vf por LED | ≈ 2.83 V |
| **I por grupo (por Rg)** | **≈ 0.58 mA** |
| **I por LED (≈ grupo/3)** | **≈ 0.19 mA** |
| I total 6 grupos | ≈ 3.5 mA (USB de sobra) |

**Conclusiones:**
- El **brillo es muy tenue** (0.19 mA/LED): es la consecuencia física de tener 2.2 kΩ
  (la R más baja con ≥6 unidades del inventario) compartida por 3 LEDs en paralelo.
  Es lo aceptado por el autor ("máximo con lo que hay, sin comprar").
- El **consumo NO es problema** (~3.5 mA los 6 grupos): el USB del PC sobra.
- **Current-hogging:** con 1 sola R por grupo los 3 LEDs no comparten por igual (el de
  menor Vf acapara); el promedio simulado (0.19 mA) es orden de magnitud, no reparto exacto.
- **Único lever real de brillo con el inventario** = menos LEDs por grupo (sube I/LED:
  1 LED con 2.2 kΩ ≈ 0.55 mA). Subir de verdad el brillo pediría R < 1 kΩ (no hay).
- **Prueba empírica pendiente** (`cableado.md` §7 paso 4): cablear un grupo, medir la
  corriente con multímetro y **mirar el brillo real** con los LEDs directo en los huecos;
  ahí se decide si es aceptable o se ajusta (nº de LEDs) dentro de lo disponible.

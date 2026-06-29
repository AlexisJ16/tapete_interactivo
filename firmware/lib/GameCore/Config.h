#ifndef TAPETE_CONFIG_H
#define TAPETE_CONFIG_H

#include <cstdint>

// Configuracion central: numero de casillas, mapa de pines (para el ESP32),
// niveles de cada modo, sonidos y tiempos. Todo lo "ajustable" vive aqui.
// Este header es PORTABLE: los pines son solo enteros; el ESP32 los usa,
// el simulador los ignora.
namespace cfg {

// --- Geometria del tapete ---------------------------------------------------
constexpr int CELDAS = 6;          // botones (2 filas x 3 columnas)
constexpr int LED_ENCENDIDO = 255; // brillo PWM maximo (0..255)
constexpr int LED_APAGADO = 0;

// --- Sonidos (archivos 000X.mp3 en el DFPlayer) -----------------------------
constexpr int SONIDO_INSTRUCCION = 1;  // muestra de secuencia / inicio de ronda
constexpr int SONIDO_ACIERTO     = 2;  // tono ascendente alegre
constexpr int SONIDO_ERROR       = 3;  // tono grave
constexpr int SONIDO_EXITO       = 4;  // secuencia/sesion completada

// --- Mapa de pines ESP32 (ver shared/protocol.md y docs/hardware/wiring.md) -
// FSR en ADC1 (GPIO 34-39 y 32-33). LEDs por LEDC/PWM.
constexpr int PIN_FSR[CELDAS]  = {36, 39, 34, 35, 32, 33};
constexpr int PIN_LED[CELDAS]  = {4, 5, 18, 19, 21, 23};
constexpr int PIN_DFPLAYER_TX  = 17;  // TX2 del ESP32 -> RX DFPlayer
constexpr int PIN_DFPLAYER_RX  = 16;  // RX2 del ESP32 <- TX DFPlayer
constexpr int UMBRAL_PISADA    = 2000;  // lectura ADC (0..4095) para considerar pisada

// --- Servidor TCP -----------------------------------------------------------
constexpr int PUERTO_TCP = 3333;
constexpr const char* VERSION_FW = "1.0.0";

// --- Modo 2: Velocidad de reaccion ------------------------------------------
namespace velocidad {
// Ventana de tiempo para reaccionar (ms). Mas corta = mas dificil.
inline int ventanaMs(int nivel) {
    switch (nivel) {
        case 1:  return 3000;
        case 2:  return 2000;
        case 3:  return 1200;
        default: return 1000;
    }
}
// Numero de rondas (objetivos) de la sesion.
inline int rondas(int nivel) {
    switch (nivel) {
        case 1:  return 5;
        case 2:  return 8;
        case 3:  return 10;
        default: return 12;
    }
}
}  // namespace velocidad

// --- Modo 1: Memoria de secuencias ------------------------------------------
namespace memoria {
// Longitud inicial de la secuencia (2..6 segun nivel).
inline int longitudInicial(int nivel) {
    int L = 1 + nivel;            // nivel 1 -> 2, nivel 2 -> 3, ...
    if (L < 2) L = 2;
    if (L > 6) L = 6;
    return L;
}
// Longitud que, al completarse, termina la sesion.
inline int longitudMaxima(int nivel) {
    int L = longitudInicial(nivel) + 3;
    if (L > 9) L = 9;
    return L;
}
// Tiempo que cada LED permanece encendido al exhibir la secuencia (ms).
inline int exhibicionOnMs(int nivel) {
    switch (nivel) {
        case 1:  return 600;
        case 2:  return 500;
        case 3:  return 400;
        default: return 300;
    }
}
// Pausa entre LEDs al exhibir (ms).
inline int exhibicionGapMs(int nivel) { (void)nivel; return 250; }
}  // namespace memoria

// --- Modo 3: Equilibrio y coordinacion --------------------------------------
namespace equilibrio {
// Numero de casillas simultaneas del patron (2/3/4 segun nivel).
inline int casillasPatron(int nivel) {
    int n = 1 + nivel;            // nivel 1 -> 2, nivel 2 -> 3, nivel 3 -> 4
    if (n < 2) n = 2;
    if (n > 4) n = 4;
    return n;
}
// Tiempo limite para completar el patron (ms).
inline int limiteMs(int nivel) {
    switch (nivel) {
        case 1:  return 5000;
        case 2:  return 4000;
        case 3:  return 3000;
        default: return 2500;
    }
}
// Numero de patrones de la sesion.
inline int rondas(int nivel) {
    switch (nivel) {
        case 1:  return 4;
        case 2:  return 6;
        case 3:  return 8;
        default: return 10;
    }
}
}  // namespace equilibrio

// --- Logica adaptable (SP1): recomendacion de nivel asistida ----------------
// El sistema SUGIERE subir/mantener/bajar segun la tasa de acierto en una
// ventana movil; el terapeuta decide. Todo ajustable (se calibra en SP2).
namespace adaptacion {
constexpr int   W          = 4;      // tamano de la ventana movil de resultados
constexpr float umbralAlto = 0.75f;  // tasa >= umbralAlto -> sugerir SUBIR
constexpr float umbralBajo = 0.25f;  // tasa <= umbralBajo -> sugerir BAJAR
constexpr int   nivelMin   = 1;
constexpr int   nivelMax   = 4;
}  // namespace adaptacion

}  // namespace cfg

#endif  // TAPETE_CONFIG_H

#include "modes/ModoVelocidad.h"

#include "Config.h"

ModoVelocidad::ModoVelocidad(IMotor& motor, int nivel)
    : m_(motor),
      ventana_(cfg::velocidad::ventanaMs(nivel)),
      rondas_(cfg::velocidad::rondas(nivel)) {}

void ModoVelocidad::iniciar(uint32_t ms) {
    hits_ = 0;
    misses_ = 0;
    ronda_ = 1;
    fin_ = false;
    nuevoObjetivo(ms);
}

void ModoVelocidad::nuevoObjetivo(uint32_t ms) {
    if (ronda_ > rondas_) {
        fin_ = true;
        objetivo_ = 0;
        return;
    }
    objetivo_ = m_.rng().casilla(cfg::CELDAS);
    inicioVentana_ = ms;
    m_.led(objetivo_, cfg::LED_ENCENDIDO);
}

void ModoVelocidad::fallar(uint32_t ms) {
    misses_++;
    if (objetivo_ != 0) m_.led(objetivo_, cfg::LED_APAGADO);
    m_.sonido(cfg::SONIDO_ERROR);
    m_.score(hits_, misses_, 0, ronda_);
    ronda_++;
    nuevoObjetivo(ms);
}

void ModoVelocidad::actualizar(uint32_t ms) {
    if (fin_ || objetivo_ == 0) return;
    if (ms - inicioVentana_ >= static_cast<uint32_t>(ventana_)) {
        fallar(ms);  // timeout
    }
}

void ModoVelocidad::pisar(int celda, uint32_t ms) {
    if (fin_ || objetivo_ == 0) return;
    if (celda == objetivo_) {
        int rt = static_cast<int>(ms - inicioVentana_);
        hits_++;
        m_.led(objetivo_, cfg::LED_APAGADO);
        m_.sonido(cfg::SONIDO_ACIERTO);
        m_.score(hits_, misses_, rt, ronda_);
        ronda_++;
        nuevoObjetivo(ms);
    } else {
        fallar(ms);  // casilla equivocada
    }
}

#include "modes/ModoEquilibrio.h"

ModoEquilibrio::ModoEquilibrio(IMotor& motor, int nivel)
    : m_(motor),
      k_(cfg::equilibrio::casillasPatron(nivel)),
      limite_(cfg::equilibrio::limiteMs(nivel)),
      rondas_(cfg::equilibrio::rondas(nivel)) {}

void ModoEquilibrio::iniciar(uint32_t ms) {
    hits_ = 0;
    misses_ = 0;
    ronda_ = 1;
    fin_ = false;
    nuevoPatron(ms);
}

void ModoEquilibrio::nuevoPatron(uint32_t ms) {
    if (ronda_ > rondas_) {
        fin_ = true;
        return;
    }
    k_ = cfg::equilibrio::casillasPatron(m_.nivelActual());  // nivel dinamico por ronda
    limite_ = cfg::equilibrio::limiteMs(m_.nivelActual());
    for (int c = 0; c <= cfg::CELDAS; ++c) { enPatron_[c] = false; yaPisada_[c] = false; }
    pisadasOk_ = 0;
    int puestos = 0;
    while (puestos < k_) {
        int c = m_.rng().casilla(cfg::CELDAS);
        if (!enPatron_[c]) {            // casillas distintas dentro del patron
            enPatron_[c] = true;
            patron_[puestos++] = c;
        }
    }
    for (int i = 0; i < k_; ++i) m_.led(patron_[i], cfg::LED_ENCENDIDO);
    tInicio_ = ms;
}

void ModoEquilibrio::apagarPatron() {
    for (int i = 0; i < k_; ++i) m_.led(patron_[i], cfg::LED_APAGADO);
}

void ModoEquilibrio::fallar(uint32_t ms) {
    misses_++;
    m_.score(hits_, misses_, 0, ronda_);   // error mudo
    apagarPatron();
    ronda_++;
    nuevoPatron(ms);
}

void ModoEquilibrio::actualizar(uint32_t ms) {
    if (fin_) return;
    if (ms - tInicio_ >= static_cast<uint32_t>(limite_)) {
        fallar(ms);  // tiempo agotado
    }
}

void ModoEquilibrio::pisar(int celda, uint32_t ms) {
    if (fin_) return;
    if (celda >= 1 && celda <= cfg::CELDAS && enPatron_[celda]) {
        if (!yaPisada_[celda]) {
            yaPisada_[celda] = true;
            pisadasOk_++;
            if (pisadasOk_ >= k_) {
                // Patron completo.
                hits_++;
                m_.score(hits_, misses_, static_cast<int>(ms - tInicio_), ronda_);
                apagarPatron();
                ronda_++;
                if (ronda_ > rondas_) { fin_ = true; return; }   // fin: suena FIN (motor)
                m_.sonido(cfg::SONIDO_RONDA);
                nuevoPatron(ms);
            } else {
                m_.sonido(cfg::SONIDO_ACIERTO);                   // acierto parcial
            }
        }
    } else {
        fallar(ms);  // pisada fuera del patron
    }
}

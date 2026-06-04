#include "modes/ModoMemoria.h"

ModoMemoria::ModoMemoria(IMotor& motor, int nivel)
    : m_(motor),
      onMs_(cfg::memoria::exhibicionOnMs(nivel)),
      gapMs_(cfg::memoria::exhibicionGapMs(nivel)),
      longitudMax_(cfg::memoria::longitudMaxima(nivel)) {
    int L0 = cfg::memoria::longitudInicial(nivel);
    len_ = 0;
    for (int i = 0; i < L0; ++i) seq_[len_++] = m_.rng().casilla(cfg::CELDAS);
}

void ModoMemoria::apagarTodo() {
    for (int c = 1; c <= cfg::CELDAS; ++c) m_.led(c, cfg::LED_APAGADO);
}

void ModoMemoria::iniciar(uint32_t ms) {
    hits_ = 0;
    misses_ = 0;
    fin_ = false;
    iniciarExhibicion(ms);
}

void ModoMemoria::iniciarExhibicion(uint32_t ms) {
    apagarTodo();
    fase_ = Fase::EXHIBIENDO;
    idxShow_ = 0;
    ledEncendido_ = true;
    m_.led(seq_[0], cfg::LED_ENCENDIDO);
    m_.sonido(cfg::SONIDO_INSTRUCCION);
    tTrans_ = ms + static_cast<uint32_t>(onMs_);
}

void ModoMemoria::iniciarEntrada(uint32_t ms) {
    fase_ = Fase::ENTRADA;
    inputIndex_ = 0;
    tInicioInput_ = ms;
    tUltimaPisada_ = ms;
}

void ModoMemoria::crecer() {
    if (len_ < static_cast<int>(sizeof(seq_) / sizeof(seq_[0]))) {
        seq_[len_++] = m_.rng().casilla(cfg::CELDAS);
    }
}

void ModoMemoria::actualizar(uint32_t ms) {
    if (fin_ || fase_ != Fase::EXHIBIENDO) return;
    // Procesa todas las transiciones de exhibicion ya vencidas (robusto frente a
    // la frecuencia con que se llame a actualizar).
    while (fase_ == Fase::EXHIBIENDO && ms >= tTrans_) {
        if (ledEncendido_) {
            m_.led(seq_[idxShow_], cfg::LED_APAGADO);
            ledEncendido_ = false;
            ++idxShow_;
            if (idxShow_ >= len_) {
                iniciarEntrada(tTrans_);
                return;
            }
            tTrans_ += static_cast<uint32_t>(gapMs_);
        } else {
            m_.led(seq_[idxShow_], cfg::LED_ENCENDIDO);
            m_.sonido(cfg::SONIDO_INSTRUCCION);
            ledEncendido_ = true;
            tTrans_ += static_cast<uint32_t>(onMs_);
        }
    }
}

void ModoMemoria::pisar(int celda, uint32_t ms) {
    if (fin_ || fase_ != Fase::ENTRADA) return;

    if (celda == seq_[inputIndex_]) {
        // Pisada correcta: confirma encendiendo la casilla.
        m_.led(celda, cfg::LED_ENCENDIDO);
        tUltimaPisada_ = ms;
        ++inputIndex_;
        if (inputIndex_ >= len_) {
            // Secuencia completa.
            ++hits_;
            m_.sonido(cfg::SONIDO_EXITO);
            m_.score(hits_, misses_, static_cast<int>(ms - tInicioInput_), len_);
            if (len_ >= longitudMax_) {
                fin_ = true;
                return;
            }
            crecer();
            iniciarExhibicion(ms);
        }
    } else {
        // Pisada incorrecta: error y se repite la MISMA secuencia.
        ++misses_;
        m_.sonido(cfg::SONIDO_ERROR);
        m_.score(hits_, misses_, 0, len_);
        iniciarExhibicion(ms);
    }
}

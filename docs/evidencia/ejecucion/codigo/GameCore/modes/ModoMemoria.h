#ifndef TAPETE_MODO_MEMORIA_H
#define TAPETE_MODO_MEMORIA_H

#include "Config.h"
#include "Motor.h"

// Modo 1 — Memoria de secuencias (tipo "Simon dice").
// El sistema genera y exhibe una secuencia de casillas (longitud inicial segun
// nivel). El nino la repite. Al completarla, la longitud crece (+1) y se exhibe
// de nuevo. Un error reproduce la MISMA secuencia. Termina al completar una
// secuencia de la longitud maxima del nivel.
//
// Maquina de estados NO bloqueante: la exhibicion avanza por timestamps
// programados en actualizar(ms); nunca usa delay().
class ModoMemoria : public IModo {
public:
    ModoMemoria(IMotor& motor, int nivel);

    void iniciar(uint32_t ms) override;
    void actualizar(uint32_t ms) override;
    void pisar(int celda, uint32_t ms) override;
    bool terminado() const override { return fin_; }

private:
    enum class Fase { EXHIBIENDO, ENTRADA };

    void apagarTodo();
    void iniciarExhibicion(uint32_t ms);
    void iniciarEntrada(uint32_t ms);
    void crecer();

    IMotor& m_;
    int onMs_;
    int gapMs_;
    int longitudMax_;

    int seq_[16];
    int len_ = 0;

    Fase fase_ = Fase::EXHIBIENDO;
    int idxShow_ = 0;
    bool ledEncendido_ = false;
    uint32_t tTrans_ = 0;     // instante de la proxima transicion de exhibicion

    int inputIndex_ = 0;
    uint32_t tInicioInput_ = 0;
    uint32_t tUltimaPisada_ = 0;

    int hits_ = 0;
    int misses_ = 0;
    bool fin_ = false;
};

#endif  // TAPETE_MODO_MEMORIA_H

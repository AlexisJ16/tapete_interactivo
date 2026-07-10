#ifndef TAPETE_MODO_VELOCIDAD_H
#define TAPETE_MODO_VELOCIDAD_H

#include "Motor.h"

// Modo 2 — Velocidad de reaccion (tipo "topo").
// Se enciende una casilla al azar; el nino debe pisarla antes de que expire la
// ventana de tiempo. Acierto -> registra rt_ms y pasa a la siguiente. Pisada
// equivocada o timeout -> error. Termina al completar todas las rondas.
class ModoVelocidad : public IModo {
public:
    ModoVelocidad(IMotor& motor, int nivel);

    void iniciar(uint32_t ms) override;
    void actualizar(uint32_t ms) override;
    void pisar(int celda, uint32_t ms) override;
    bool terminado() const override { return fin_; }

private:
    void nuevoObjetivo(uint32_t ms);
    void fallar(uint32_t ms);   // error (timeout o casilla equivocada)

    IMotor& m_;
    int ventana_;
    int rondas_;
    int objetivo_ = 0;
    uint32_t inicioVentana_ = 0;
    int ronda_ = 0;
    int hits_ = 0;
    int misses_ = 0;
    bool fin_ = false;
};

#endif  // TAPETE_MODO_VELOCIDAD_H

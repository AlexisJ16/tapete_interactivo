#ifndef TAPETE_MODO_EQUILIBRIO_H
#define TAPETE_MODO_EQUILIBRIO_H

#include "Config.h"
#include "Motor.h"

// Modo 3 — Equilibrio y coordinacion (patrones simultaneos).
// Se enciende un patron de 2-4 casillas a la vez (segun nivel). El nino debe
// pisarlas todas dentro de un tiempo limite. Patron completo -> exito. Tiempo
// agotado o pisada fuera del patron -> error. Termina al completar todas las
// rondas (patrones) del nivel.
class ModoEquilibrio : public IModo {
public:
    ModoEquilibrio(IMotor& motor, int nivel);

    void iniciar(uint32_t ms) override;
    void actualizar(uint32_t ms) override;
    void pisar(int celda, uint32_t ms) override;
    bool terminado() const override { return fin_; }

private:
    void nuevoPatron(uint32_t ms);
    void apagarPatron();
    void fallar(uint32_t ms);

    IMotor& m_;
    int k_;          // casillas simultaneas del patron
    int limite_;     // tiempo limite (ms)
    int rondas_;

    int patron_[4];
    bool enPatron_[cfg::CELDAS + 1];
    bool yaPisada_[cfg::CELDAS + 1];
    int pisadasOk_ = 0;

    uint32_t tInicio_ = 0;
    int ronda_ = 0;
    int hits_ = 0;
    int misses_ = 0;
    bool fin_ = false;
};

#endif  // TAPETE_MODO_EQUILIBRIO_H

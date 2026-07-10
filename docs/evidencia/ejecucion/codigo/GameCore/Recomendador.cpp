#include "Recomendador.h"

namespace adapt {

Recomendador::Recomendador(int W, float umbralAlto, float umbralBajo,
                           int nivelMin, int nivelMax)
    : W_(W < 1 ? 1 : (W > kMax ? kMax : W)),
      umbralAlto_(umbralAlto),
      umbralBajo_(umbralBajo),
      nivelMin_(nivelMin),
      nivelMax_(nivelMax) {
    reiniciar();
}

void Recomendador::reiniciar() {
    n_ = 0;
    cabeza_ = 0;
    aciertos_ = 0;
}

void Recomendador::registrarResultado(bool acierto) {
    if (n_ < W_) {
        ventana_[cabeza_] = acierto;
        if (acierto) ++aciertos_;
        cabeza_ = (cabeza_ + 1) % W_;
        ++n_;
    } else {
        // Ventana llena: 'cabeza_' apunta al mas antiguo; se reemplaza.
        if (ventana_[cabeza_]) --aciertos_;
        ventana_[cabeza_] = acierto;
        if (acierto) ++aciertos_;
        cabeza_ = (cabeza_ + 1) % W_;
    }
}

Sugerencia Recomendador::evaluar(int nivelActual) const {
    Sugerencia s;
    s.n = n_;
    s.tasa = (n_ > 0) ? static_cast<float>(aciertos_) / static_cast<float>(n_)
                      : 0.0f;
    s.nivelSugerido = nivelActual;
    s.dir = Direccion::MANTENER;

    if (n_ < W_) return s;  // ventana incompleta -> MANTENER

    if (s.tasa >= umbralAlto_) {
        s.dir = Direccion::SUBIR;
        s.nivelSugerido = nivelActual + 1;
    } else if (s.tasa <= umbralBajo_) {
        s.dir = Direccion::BAJAR;
        s.nivelSugerido = nivelActual - 1;
    }

    if (s.nivelSugerido > nivelMax_) s.nivelSugerido = nivelMax_;
    if (s.nivelSugerido < nivelMin_) s.nivelSugerido = nivelMin_;

    // Saturacion: ya en el tope/piso -> no hay cambio accionable -> keep.
    if (s.nivelSugerido == nivelActual) s.dir = Direccion::MANTENER;

    return s;
}

}  // namespace adapt

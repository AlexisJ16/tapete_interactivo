#ifndef TAPETE_RECOMENDADOR_H
#define TAPETE_RECOMENDADOR_H

#include "Config.h"

// Capa adaptable (SP1): a partir del flujo de resultados de ronda (acierto/fallo)
// en una ventana movil, RECOMIENDA subir/mantener/bajar el nivel. No actua: la
// decision final es del terapeuta (adaptacion asistida, human-in-the-loop).
// Logica PURA y portable: sin Arduino, sin protocolo, sin hardware.
namespace adapt {

enum class Direccion { BAJAR, MANTENER, SUBIR };

// Texto canonico del campo "dir" del evento suggest del protocolo.
inline const char* aTexto(Direccion d) {
    switch (d) {
        case Direccion::SUBIR:    return "up";
        case Direccion::BAJAR:    return "down";
        case Direccion::MANTENER: return "keep";
    }
    return "keep";
}

struct Sugerencia {
    Direccion dir = Direccion::MANTENER;
    int   nivelSugerido = 0;  // clamp(nivelActual +/- 1) en [nivelMin, nivelMax]
    float tasa = 0.0f;        // tasa de acierto en la ventana (0..1), uso INTERNO
    int   n = 0;              // numero de resultados en la ventana (hasta W)
};

// Ventana movil de resultados booleanos + regla con banda muerta. evaluar() es
// una FUNCION PURA de (ventana, nivelActual): no guarda "ultima direccion"
// (esa de-dup vive en GameEngine).
class Recomendador {
public:
    explicit Recomendador(int W           = cfg::adaptacion::W,
                          float umbralAlto = cfg::adaptacion::umbralAlto,
                          float umbralBajo = cfg::adaptacion::umbralBajo,
                          int nivelMin     = cfg::adaptacion::nivelMin,
                          int nivelMax     = cfg::adaptacion::nivelMax);

    void reiniciar();
    void registrarResultado(bool acierto);
    Sugerencia evaluar(int nivelActual) const;

private:
    static constexpr int kMax = 32;  // tope de capacidad de la ventana
    int   W_;
    float umbralAlto_;
    float umbralBajo_;
    int   nivelMin_;
    int   nivelMax_;

    bool ventana_[kMax];
    int  n_ = 0;        // resultados validos en la ventana (hasta W_)
    int  cabeza_ = 0;   // indice circular: proxima escritura / mas antiguo
    int  aciertos_ = 0; // numero de 'true' en la ventana (tasa en O(1))
};

}  // namespace adapt

#endif  // TAPETE_RECOMENDADOR_H

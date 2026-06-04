#ifndef SOPORTE_TEST_H
#define SOPORTE_TEST_H

// Infraestructura compartida por los tests de los modos:
//  - FakeHardware: doble de IHardware con reloj controlable y registro de I/O.
//  - Colector: captura los eventos del protocolo emitidos por el motor.
//  - helpers para verificar subsecuencias de eventos.

#include <functional>
#include <vector>
#include "IHardware.h"
#include "Protocol.h"
#include "GameEngine.h"

// Doble de hardware: el test controla el reloj y los sensores; registra LEDs y sonidos.
struct FakeHardware : IHardware {
    uint32_t reloj = 0;
    int sensores[8] = {0};  // indices 1..6
    std::vector<std::pair<int, int>> leds;  // (celda, nivel) en orden
    std::vector<int> sonidos;

    uint32_t millis() override { return reloj; }
    int leerSensor(int celda) override { return sensores[celda]; }
    void setLed(int celda, int nivel) override { leds.push_back({celda, nivel}); }
    void reproducirSonido(int id) override { sonidos.push_back(id); }
};

// Captura todos los eventos del protocolo emitidos por el motor.
struct Colector {
    std::vector<proto::Evento> eventos;
    Emisor sink() {
        return [this](const proto::Evento& e) { eventos.push_back(e); };
    }
};

// ¿'esperado' aparece, EN ORDEN, como subsecuencia de 'stream'?
inline bool subsecuencia(const std::vector<proto::Evento>& stream,
                         const std::vector<proto::Evento>& esperado) {
    size_t j = 0;
    for (const auto& e : stream) {
        if (j < esperado.size() && e == esperado[j]) ++j;
    }
    return j == esperado.size();
}

// ¿el stream contiene al menos un evento igual a 'e'?
inline bool contiene(const std::vector<proto::Evento>& stream, const proto::Evento& e) {
    for (const auto& x : stream) if (x == e) return true;
    return false;
}

// ¿el stream contiene un score con estos campos? (ignora rt_ms, que depende del timing)
inline bool contieneScore(const std::vector<proto::Evento>& stream,
                          int mode, int hits, int misses, int round) {
    for (const auto& x : stream) {
        if (x.tipo == proto::Evento::Tipo::SCORE && x.mode == mode &&
            x.hits == hits && x.misses == misses && x.round == round) {
            return true;
        }
    }
    return false;
}

// Cuenta eventos de un tipo dado.
inline int cuenta(const std::vector<proto::Evento>& stream, proto::Evento::Tipo t) {
    int n = 0;
    for (const auto& x : stream) if (x.tipo == t) ++n;
    return n;
}

#endif  // SOPORTE_TEST_H

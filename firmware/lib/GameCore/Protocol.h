#ifndef TAPETE_PROTOCOL_H
#define TAPETE_PROTOCOL_H

#include <cstdint>
#include <string>

// Protocolo de comunicacion v1.0.0 (ver shared/protocol.md).
// Mini-serializacion JSON propia: objetos planos, claves y orden fijos.
// El parseo es identico en ambos extremos (este codigo corre en ESP32 y en el
// .so del simulador). No depende de Arduino ni de librerias externas.
namespace proto {

// ----------------------------------------------------------------------------
//  Eventos: cerebro (ESP32 / Simulador) -> PC
// ----------------------------------------------------------------------------
struct Evento {
    enum class Tipo { HELLO, LED, PRESS, SOUND, SCORE, STATE, INVALIDO };
    Tipo tipo = Tipo::INVALIDO;

    std::string fw;        // hello
    int cells = 0;         // hello
    int cell = 0;          // led, press
    int level = 0;         // led
    uint32_t ms = 0;       // press
    int id = 0;            // sound
    int mode = 0;          // score, state
    int hits = 0;          // score
    int misses = 0;        // score
    int rt_ms = 0;         // score
    int round = 0;         // score
    std::string status;    // state

    static Evento hello(const std::string& fw, int cells);
    static Evento led(int cell, int level);
    static Evento press(int cell, uint32_t ms);
    static Evento sound(int id);
    static Evento score(int mode, int hits, int misses, int rt_ms, int round);
    static Evento state(int mode, const std::string& status);

    std::string serializar() const;
    static Evento parsear(const std::string& linea);

    bool operator==(const Evento& o) const;
    bool operator!=(const Evento& o) const { return !(*this == o); }
};

// ----------------------------------------------------------------------------
//  Comandos: PC -> cerebro (ESP32 / Simulador)
// ----------------------------------------------------------------------------
struct Comando {
    enum class Tipo {
        INVALIDO, SET_MODE, START, STOP, PAUSE,
        SET_LEVEL, SET_PLAYER, SET_SEED, PING
    };
    Tipo tipo = Tipo::INVALIDO;

    int mode = 0;
    int level = 0;
    uint32_t seed = 0;
    std::string id;
    std::string name;

    std::string serializar() const;
    static Comando parsear(const std::string& linea);

    bool operator==(const Comando& o) const;
    bool operator!=(const Comando& o) const { return !(*this == o); }
};

} // namespace proto

#endif // TAPETE_PROTOCOL_H

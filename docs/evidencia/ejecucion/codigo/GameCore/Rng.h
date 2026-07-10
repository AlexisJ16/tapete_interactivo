#ifndef TAPETE_RNG_H
#define TAPETE_RNG_H

#include <cstdint>

// Generador pseudoaleatorio xorshift32: determinista, rapido y portable.
// Identico en C++ nativo y en el ESP32. NO usar rand() (no reproducible).
// La reproducibilidad es la base de los golden vectors.
class Rng {
public:
    explicit Rng(uint32_t semilla = 0x2545F491u) { sembrar(semilla); }

    // Fija la semilla. El estado xorshift no puede ser 0 (se quedaria atascado),
    // por lo que una semilla 0 se normaliza a una constante no nula.
    void sembrar(uint32_t semilla) {
        estado_ = (semilla == 0u) ? 0x2545F491u : semilla;
    }

    // Siguiente valor de 32 bits.
    uint32_t next() {
        uint32_t s = estado_;
        s ^= s << 13;
        s ^= s >> 17;
        s ^= s << 5;
        estado_ = s;
        return s;
    }

    // Casilla en el rango 1..n (n = numero de casillas).
    int casilla(int n) {
        return static_cast<int>(next() % static_cast<uint32_t>(n)) + 1;
    }

private:
    uint32_t estado_;
};

#endif // TAPETE_RNG_H

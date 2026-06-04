// Tests del generador pseudoaleatorio xorshift32 (determinista y portable).
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "Rng.h"

TEST_CASE("xorshift32 es determinista con la misma semilla") {
    Rng a(12345), b(12345);
    for (int i = 0; i < 20; ++i) {
        CHECK(a.next() == b.next());
    }
}

TEST_CASE("casilla() produce la secuencia esperada para seed=12345") {
    // Calculado offline: cell = (next() % 6) + 1
    Rng r(12345);
    const int esperado[8] = {3, 4, 5, 3, 6, 1, 1, 3};
    for (int i = 0; i < 8; ++i) {
        CHECK(r.casilla(6) == esperado[i]);
    }
}

TEST_CASE("casilla() siempre cae en el rango 1..n") {
    Rng r(987654321u);
    for (int i = 0; i < 1000; ++i) {
        int c = r.casilla(6);
        CHECK(c >= 1);
        CHECK(c <= 6);
    }
}

TEST_CASE("semilla 0 se normaliza a un estado valido (no se queda atascada)") {
    Rng r(0);
    // xorshift con estado 0 produciria siempre 0; el constructor debe evitarlo.
    uint32_t v = r.next();
    CHECK(v != 0u);
}

TEST_CASE("sembrar() reinicia la secuencia") {
    Rng r(42);
    uint32_t primero = r.next();
    r.next(); r.next();
    r.sembrar(42);
    CHECK(r.next() == primero);
}

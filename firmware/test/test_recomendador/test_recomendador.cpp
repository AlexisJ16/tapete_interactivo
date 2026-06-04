// Tests unitarios del Recomendador (capa adaptable, logica pura).
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "Recomendador.h"

using namespace adapt;

TEST_CASE("racha de aciertos con ventana llena sugiere SUBIR") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);
    Sugerencia s = r.evaluar(2);
    CHECK(s.dir == Direccion::SUBIR);
    CHECK(s.nivelSugerido == 3);
    CHECK(s.n == 4);
    CHECK(s.tasa == doctest::Approx(1.0));
}

TEST_CASE("racha de fallos con ventana llena sugiere BAJAR") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(false);
    Sugerencia s = r.evaluar(3);
    CHECK(s.dir == Direccion::BAJAR);
    CHECK(s.nivelSugerido == 2);
    CHECK(s.tasa == doctest::Approx(0.0));
}

TEST_CASE("desempeno intermedio (banda muerta) sugiere MANTENER") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    r.registrarResultado(true);  r.registrarResultado(false);
    r.registrarResultado(true);  r.registrarResultado(false);  // 2/4 = 0.5
    Sugerencia s = r.evaluar(2);
    CHECK(s.dir == Direccion::MANTENER);
    CHECK(s.nivelSugerido == 2);
}

TEST_CASE("ventana incompleta siempre sugiere MANTENER") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    r.registrarResultado(true);
    r.registrarResultado(true);
    r.registrarResultado(true);  // n=3 < W=4
    Sugerencia s = r.evaluar(2);
    CHECK(s.dir == Direccion::MANTENER);
    CHECK(s.n == 3);
}

TEST_CASE("saturacion en el nivel maximo fuerza MANTENER (no SUBIR)") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);
    Sugerencia s = r.evaluar(4);  // ya en el tope
    CHECK(s.nivelSugerido == 4);
    CHECK(s.dir == Direccion::MANTENER);
}

TEST_CASE("saturacion en el nivel minimo fuerza MANTENER (no BAJAR)") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(false);
    Sugerencia s = r.evaluar(1);  // ya en el piso
    CHECK(s.nivelSugerido == 1);
    CHECK(s.dir == Direccion::MANTENER);
}

TEST_CASE("la ventana movil descarta los resultados antiguos") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);   // SUBIR
    CHECK(r.evaluar(2).dir == Direccion::SUBIR);
    for (int i = 0; i < 4; ++i) r.registrarResultado(false);  // ya todo fallos
    CHECK(r.evaluar(2).dir == Direccion::BAJAR);
}

TEST_CASE("reiniciar vacia la ventana") {
    Recomendador r(4, 0.75f, 0.25f, 1, 4);
    for (int i = 0; i < 4; ++i) r.registrarResultado(true);
    r.reiniciar();
    Sugerencia s = r.evaluar(2);
    CHECK(s.n == 0);
    CHECK(s.dir == Direccion::MANTENER);
}

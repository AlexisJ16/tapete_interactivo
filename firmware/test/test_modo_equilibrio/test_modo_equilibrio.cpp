// Tests del Modo 3 (Equilibrio y coordinacion, patrones simultaneos).
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "soporte_test.h"

using namespace proto;

// seed=2024 -> casillas [3,6,5,4,6,2,5,1].
// Nivel 1: patrones de 2 casillas -> [3,6], [5,4], [6,2], [5,1]. 4 rondas.
static void arrancar(GameEngine& m) {
    m.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":2024})"));
    m.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":3,"level":1})"));
    m.procesar(Comando::parsear(R"({"cmd":"start"})"));
}

TEST_CASE("equilibrio: enciende un patron de 2 casillas") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    CHECK(contiene(col.eventos, Evento::led(3, 255)));
    CHECK(contiene(col.eventos, Evento::led(6, 255)));
}

TEST_CASE("equilibrio: completar el patron es acierto y pasa al siguiente") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    hw.reloj = 500;  motor.pisar(3);
    hw.reloj = 900;  motor.pisar(6);  // patron [3,6] completo

    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_EXITO)));
    CHECK(contieneScore(col.eventos, /*mode*/ 3, /*hits*/ 1, /*misses*/ 0, /*round*/ 1));
    // Siguiente patron [5,4]: aparece un LED nuevo.
    CHECK(contiene(col.eventos, Evento::led(5, 255)));
}

TEST_CASE("equilibrio: pisar fuera del patron es error") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    hw.reloj = 500; motor.pisar(1);  // 1 no esta en [3,6]

    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_ERROR)));
    CHECK(contieneScore(col.eventos, 3, /*hits*/ 0, /*misses*/ 1, /*round*/ 1));
}

TEST_CASE("equilibrio: agotar el tiempo limite es error") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    hw.reloj = 6000; motor.actualizar();  // limite nivel 1 = 5000 ms

    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_ERROR)));
    CHECK(contieneScore(col.eventos, 3, 0, 1, 1));
}

TEST_CASE("equilibrio: termina tras completar todas las rondas (nivel 1 = 4)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    const int patrones[4][2] = {{3, 6}, {5, 4}, {6, 2}, {5, 1}};
    uint32_t t = 200;
    for (int r = 0; r < 4; ++r) {
        for (int i = 0; i < 2; ++i) {
            hw.reloj = t; motor.pisar(patrones[r][i]); t += 300;
        }
    }

    CHECK(motor.estado() == Estado::FINISHED);
    CHECK(contiene(col.eventos, Evento::state(3, "finished")));
}

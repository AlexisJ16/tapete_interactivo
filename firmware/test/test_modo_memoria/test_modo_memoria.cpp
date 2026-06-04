// Tests del Modo 1 (Memoria de secuencias, tipo "Simon dice").
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "soporte_test.h"

using namespace proto;

// seed=777 -> casillas [4,5,2,3,6,...]. Nivel 1: longitud inicial 2, maxima 5.
static void arrancar(GameEngine& m) {
    m.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":777})"));
    m.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":1,"level":1})"));
    m.procesar(Comando::parsear(R"({"cmd":"start"})"));
}

// Avanza el reloj lo suficiente para que termine la exhibicion de la secuencia.
static void terminarExhibicion(FakeHardware& hw, GameEngine& m) {
    hw.reloj += 10000;
    m.actualizar();
}

TEST_CASE("memoria: exhibe la secuencia inicial (longitud 2 en nivel 1)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);
    // La secuencia [4,5] se mostro encendiendo cada LED.
    CHECK(contiene(col.eventos, Evento::led(4, 255)));
    CHECK(contiene(col.eventos, Evento::led(5, 255)));
    // Cada paso de exhibicion lleva un sonido de instruccion.
    CHECK(cuenta(col.eventos, Evento::Tipo::SOUND) >= 2);
}

TEST_CASE("memoria: repetir la secuencia correcta sube la longitud") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);

    hw.reloj += 300; motor.pisar(4);
    hw.reloj += 300; motor.pisar(5);  // secuencia [4,5] completada

    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_EXITO)));
    CHECK(contieneScore(col.eventos, /*mode*/ 1, /*hits*/ 1, /*misses*/ 0, /*round=len*/ 2));
    // Crece a [4,5,2] y se vuelve a exhibir: aparece el LED de la nueva casilla (2).
    terminarExhibicion(hw, motor);
    CHECK(contiene(col.eventos, Evento::led(2, 255)));
}

TEST_CASE("memoria: pisar mal cuenta error y repite la misma secuencia") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);

    hw.reloj += 300; motor.pisar(5);  // se esperaba 4 -> error

    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_ERROR)));
    CHECK(contieneScore(col.eventos, 1, /*hits*/ 0, /*misses*/ 1, /*round*/ 2));
    CHECK(motor.estado() == Estado::RUNNING);  // no termina por un error
}

TEST_CASE("memoria: completar hasta la longitud maxima termina la sesion") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    const int seq[5] = {4, 5, 2, 3, 6};  // seed 777
    // Repite secuencias crecientes de longitud 2,3,4,5.
    for (int len = 2; len <= 5; ++len) {
        terminarExhibicion(hw, motor);
        for (int i = 0; i < len; ++i) {
            hw.reloj += 250;
            motor.pisar(seq[i]);
        }
    }

    CHECK(motor.estado() == Estado::FINISHED);
    CHECK(contiene(col.eventos, Evento::state(1, "finished")));
}

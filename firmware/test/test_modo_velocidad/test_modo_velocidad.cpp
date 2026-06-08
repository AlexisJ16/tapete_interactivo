// Tests del Modo 2 (Velocidad de reaccion, tipo "topo").
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "soporte_test.h"

using namespace proto;

// Arranca un motor en Modo Velocidad, nivel 1, semilla 12345.
// seed=12345 -> casillas objetivo [3,4,5,3,6,...].
static void arrancar(GameEngine& m) {
    m.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":12345})"));
    m.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":1})"));
    m.procesar(Comando::parsear(R"({"cmd":"start"})"));
}

TEST_CASE("velocidad: dos aciertos consecutivos (coincide con golden)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    hw.reloj = 400; motor.pisar(3);
    hw.reloj = 900; motor.pisar(4);

    CHECK(subsecuencia(col.eventos, {
        Evento::state(2, "running"),
        Evento::led(3, 255),
        Evento::press(3, 400),
        Evento::score(2, 1, 0, 400, 1),
        Evento::led(4, 255),
        Evento::press(4, 900),
        Evento::score(2, 2, 0, 500, 2),
        Evento::led(5, 255),
    }));
}

TEST_CASE("velocidad: timeout cuenta como error y avanza") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    hw.reloj = 5000; motor.actualizar();  // mas alla de la ventana (3000 ms en nivel 1)

    CHECK(subsecuencia(col.eventos, {
        Evento::state(2, "running"),
        Evento::led(3, 255),
        Evento::score(2, 0, 1, 0, 1),
        Evento::led(4, 255),
    }));
}

TEST_CASE("velocidad: pisar la casilla equivocada es un error") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    hw.reloj = 200; motor.pisar(5);  // objetivo era 3

    CHECK(contiene(col.eventos, Evento::press(5, 200)));
    CHECK(contiene(col.eventos, Evento::score(2, 0, 1, 0, 1)));
    CHECK(contiene(col.eventos, Evento::led(4, 255)));  // pasa al siguiente objetivo
}

TEST_CASE("velocidad: termina tras completar todas las rondas (nivel 1 = 5)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);

    const int objetivos[5] = {3, 4, 5, 3, 6};  // seed 12345
    uint32_t t = 100;
    for (int i = 0; i < 5; ++i) {
        hw.reloj = t; motor.pisar(objetivos[i]); t += 300;
    }

    CHECK(motor.estado() == Estado::FINISHED);
    CHECK(contiene(col.eventos, Evento::state(2, "finished")));
    CHECK(contiene(col.eventos, Evento::score(2, 5, 0, 300, 5)));
}

TEST_CASE("velocidad: ping responde con hello") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"ping"})"));
    CHECK(contiene(col.eventos, Evento::hello("1.0.0", 6)));
}

TEST_CASE("set_level en RUNNING no recrea el modo (conserva la ronda en curso)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);                       // modo 2, nivel 1, objetivo ronda1 = 3

    hw.reloj = 100;
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":3})"));
    CHECK(motor.estado() == Estado::RUNNING);   // sigue corriendo (no reinicia)
    CHECK(motor.nivel() == 3);

    hw.reloj = 200; motor.pisar(3);        // si el modo sigue vivo, es un acierto
    CHECK(contieneScore(col.eventos, 2, 1, 0, 1));  // hit de la ronda 1
}

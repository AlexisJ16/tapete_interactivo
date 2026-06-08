// Integracion de la capa adaptable en GameEngine.
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "soporte_test.h"

using namespace proto;

TEST_CASE("IMotor::nivelActual refleja el nivel actual del motor") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":2})"));
    CHECK(motor.nivelActual() == 2);
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":4})"));
    CHECK(motor.nivelActual() == 4);
}

// Arranca Velocidad con semilla 12345 -> objetivos [3,4,5,3,6,...].
static void arrancarVel(GameEngine& m, int nivel) {
    m.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":12345})"));
    m.procesar(Comando::parsear(
        std::string(R"({"cmd":"set_mode","mode":2,"level":)") +
        std::to_string(nivel) + "}"));
    m.procesar(Comando::parsear(R"({"cmd":"start"})"));
}

TEST_CASE("adaptacion: 4 aciertos seguidos emiten suggest up (rate 100)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 1);                 // nivel 1: ventana 3000, 5 rondas
    const int obj[4] = {3, 4, 5, 3};
    uint32_t t = 100;
    for (int i = 0; i < 4; ++i) { hw.reloj = t; motor.pisar(obj[i]); t += 300; }
    CHECK(contiene(col.eventos, Evento::suggest(2, 1, 2, "up", 100, 4)));
    CHECK(cuenta(col.eventos, Evento::Tipo::SUGGEST) == 1);  // solo una vez
}

TEST_CASE("adaptacion: 4 fallos seguidos emiten suggest down (rate 0)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 2);                 // nivel 2: 8 rondas (no termina)
    uint32_t t = 100;
    for (int i = 0; i < 4; ++i) { hw.reloj = t; motor.pisar(1); t += 100; } // 1 != obj
    CHECK(contiene(col.eventos, Evento::suggest(2, 2, 1, "down", 0, 4)));
}

TEST_CASE("adaptacion: no repite la misma direccion (de-dup)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 1);
    const int obj[5] = {3, 4, 5, 3, 6};
    uint32_t t = 100;
    for (int i = 0; i < 5; ++i) { hw.reloj = t; motor.pisar(obj[i]); t += 300; }
    CHECK(cuenta(col.eventos, Evento::Tipo::SUGGEST) == 1);  // 5 aciertos -> 1 suggest
}

TEST_CASE("adaptacion: en el nivel maximo dominar no emite suggest (keep)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancarVel(motor, 4);                 // tope: SUBIR satura a keep
    const int obj[4] = {3, 4, 5, 3};
    uint32_t t = 100;
    for (int i = 0; i < 4; ++i) { hw.reloj = t; motor.pisar(obj[i]); t += 300; }
    CHECK(cuenta(col.eventos, Evento::Tipo::SUGGEST) == 0);
}

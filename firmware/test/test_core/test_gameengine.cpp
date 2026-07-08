// Tests de frontera del motor (GameEngine): rangos seguros de la API publica.
// Task 2.6 (docs/superpowers/plans/2026-07-07-robustez-integral.md): las
// entradas fuera de rango a set_level/set_mode/pisar deben ignorarse sin dejar
// el motor en un estado invalido (nivel/modo corrupto, o un press con celda
// que no existe en el tapete).
#include "doctest.h"
#include "soporte_test.h"

using namespace proto;

TEST_CASE("set_level fuera de rango se ignora: el nivel actual no cambia") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":1,"level":2})"));
    REQUIRE(motor.nivel() == 2);

    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":0})"));
    CHECK(motor.nivel() == 2);
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":99})"));
    CHECK(motor.nivel() == 2);
    motor.procesar(Comando::parsear(R"({"cmd":"set_level","level":-5})"));
    CHECK(motor.nivel() == 2);
}

TEST_CASE("set_mode desconocido se ignora: no toca modo/nivel ni interrumpe la sesion") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":1,"level":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"start"})"));
    REQUIRE(motor.estado() == Estado::RUNNING);
    REQUIRE(motor.modoId() == 1);
    size_t antes = col.eventos.size();

    // Modo desconocido (no existe modo 99): debe ignorarse por completo, sin
    // efectos secundarios (nada de apagar LEDs / volver a IDLE).
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":99,"level":1})"));

    CHECK(motor.modoId() == 1);
    CHECK(motor.nivel() == 1);
    CHECK(motor.estado() == Estado::RUNNING);
    CHECK(col.eventos.size() == antes);  // ni state ni led: comando totalmente ignorado
}

TEST_CASE("set_mode con nivel fuera de rango se ignora por completo") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":1,"level":2})"));
    REQUIRE(motor.modoId() == 1);
    REQUIRE(motor.nivel() == 2);

    // Modo valido (2) pero nivel invalido (99): se ignora el comando completo,
    // no solo el nivel (evita un modo 2 con nivel corrupto).
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":99})"));

    CHECK(motor.modoId() == 1);
    CHECK(motor.nivel() == 2);
}

TEST_CASE("pisar(0) y pisar(99) se ignoran sin emitir eventos ni tocar el modo") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    motor.procesar(Comando::parsear(R"({"cmd":"set_seed","seed":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"set_mode","mode":2,"level":1})"));
    motor.procesar(Comando::parsear(R"({"cmd":"start"})"));
    REQUIRE(motor.estado() == Estado::RUNNING);
    size_t antes = col.eventos.size();

    hw.reloj = 100; motor.pisar(0);
    hw.reloj = 200; motor.pisar(99);

    CHECK(col.eventos.size() == antes);  // ningun press/score/sound generado
    CHECK(motor.estado() == Estado::RUNNING);

    // El modo sigue vivo (no quedo corrupto): una pisada valida despues sigue
    // generando eventos con normalidad.
    hw.reloj = 300; motor.pisar(1);
    CHECK(col.eventos.size() > antes);
}

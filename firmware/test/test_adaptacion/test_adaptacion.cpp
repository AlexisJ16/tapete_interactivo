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

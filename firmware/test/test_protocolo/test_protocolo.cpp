// Tests del protocolo: serializacion canonica y round-trip (serializar->parsear).
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "Protocol.h"

using namespace proto;

// ----------------------------------------------------------------------------
//  Serializacion canonica de EVENTOS (cerebro -> PC)
// ----------------------------------------------------------------------------
TEST_CASE("eventos se serializan en la forma canonica del protocolo") {
    CHECK(Evento::hello("1.0.0", 6).serializar() ==
          R"({"ev":"hello","fw":"1.0.0","cells":6})");
    CHECK(Evento::led(1, 255).serializar() ==
          R"({"ev":"led","cell":1,"level":255})");
    CHECK(Evento::press(3, 1820).serializar() ==
          R"({"ev":"press","cell":3,"ms":1820})");
    CHECK(Evento::sound(2).serializar() ==
          R"({"ev":"sound","id":2})");
    CHECK(Evento::score(1, 5, 1, 820, 6).serializar() ==
          R"({"ev":"score","mode":1,"hits":5,"misses":1,"rt_ms":820,"round":6})");
    CHECK(Evento::state(1, "running").serializar() ==
          R"({"ev":"state","mode":1,"status":"running"})");
    CHECK(Evento::suggest(2, 2, 3, "up", 75, 4).serializar() ==
          R"({"ev":"suggest","mode":2,"from":2,"level":3,"dir":"up","rate":75,"window":4})");
}

// ----------------------------------------------------------------------------
//  Parseo de COMANDOS (PC -> cerebro)
// ----------------------------------------------------------------------------
TEST_CASE("comandos se parsean correctamente") {
    Comando c1 = Comando::parsear(R"({"cmd":"set_mode","mode":1,"level":2})");
    CHECK(c1.tipo == Comando::Tipo::SET_MODE);
    CHECK(c1.mode == 1);
    CHECK(c1.level == 2);

    CHECK(Comando::parsear(R"({"cmd":"start"})").tipo == Comando::Tipo::START);
    CHECK(Comando::parsear(R"({"cmd":"stop"})").tipo == Comando::Tipo::STOP);
    CHECK(Comando::parsear(R"({"cmd":"pause"})").tipo == Comando::Tipo::PAUSE);
    CHECK(Comando::parsear(R"({"cmd":"ping"})").tipo == Comando::Tipo::PING);

    Comando c2 = Comando::parsear(R"({"cmd":"set_level","level":3})");
    CHECK(c2.tipo == Comando::Tipo::SET_LEVEL);
    CHECK(c2.level == 3);

    Comando c3 = Comando::parsear(R"({"cmd":"set_player","id":"p001","name":"Juan"})");
    CHECK(c3.tipo == Comando::Tipo::SET_PLAYER);
    CHECK(c3.id == "p001");
    CHECK(c3.name == "Juan");

    Comando c4 = Comando::parsear(R"({"cmd":"set_seed","seed":12345})");
    CHECK(c4.tipo == Comando::Tipo::SET_SEED);
    CHECK(c4.seed == 12345u);
}

TEST_CASE("comando invalido o desconocido devuelve INVALIDO") {
    CHECK(Comando::parsear("basura no json").tipo == Comando::Tipo::INVALIDO);
    CHECK(Comando::parsear(R"({"cmd":"despegar"})").tipo == Comando::Tipo::INVALIDO);
    CHECK(Comando::parsear("").tipo == Comando::Tipo::INVALIDO);
}

TEST_CASE("el parser tolera espacios alrededor de ':' y ','") {
    Comando c = Comando::parsear(R"({ "cmd" : "set_mode" , "mode" : 2 , "level" : 1 })");
    CHECK(c.tipo == Comando::Tipo::SET_MODE);
    CHECK(c.mode == 2);
    CHECK(c.level == 1);
}

// ----------------------------------------------------------------------------
//  Round-trip: serializar -> parsear -> comparar (§10.4)
// ----------------------------------------------------------------------------
TEST_CASE("round-trip de eventos: parsear(serializar(e)) == e") {
    Evento ev[] = {
        Evento::hello("1.0.0", 6),
        Evento::led(4, 128),
        Evento::press(2, 999),
        Evento::sound(3),
        Evento::score(2, 7, 2, 540, 9),
        Evento::state(3, "finished"),
        Evento::suggest(2, 2, 3, "up", 75, 4),
    };
    for (const auto& e : ev) {
        CHECK(Evento::parsear(e.serializar()) == e);
    }
}

TEST_CASE("round-trip de comandos: parsear(serializar(c)) == c") {
    Comando cmds[5];
    cmds[0].tipo = Comando::Tipo::SET_MODE; cmds[0].mode = 1; cmds[0].level = 2;
    cmds[1].tipo = Comando::Tipo::SET_LEVEL; cmds[1].level = 4;
    cmds[2].tipo = Comando::Tipo::SET_PLAYER; cmds[2].id = "p007"; cmds[2].name = "Ana";
    cmds[3].tipo = Comando::Tipo::SET_SEED; cmds[3].seed = 777u;
    cmds[4].tipo = Comando::Tipo::PING;
    for (const auto& c : cmds) {
        CHECK(Comando::parsear(c.serializar()) == c);
    }
}

TEST_CASE("cadenas con comillas se escapan y se recuperan") {
    Comando c;
    c.tipo = Comando::Tipo::SET_PLAYER;
    c.id = "p001";
    c.name = R"(Jo"se)";  // contiene una comilla
    Comando r = Comando::parsear(c.serializar());
    CHECK(r.name == R"(Jo"se)");
}

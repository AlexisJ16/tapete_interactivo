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

// Avanza el reloj en pasos y actualiza varias veces: cubre la PAUSA (~1,2 s) y deja
// transcurrir toda la exhibicion de la secuencia hasta la fase de ENTRADA. Una vez en
// ENTRADA, actualizar() ya no hace nada (Memoria no tiene timeout de entrada).
static void terminarExhibicion(FakeHardware& hw, GameEngine& m) {
    for (int i = 0; i < 30; ++i) { hw.reloj += 2000; m.actualizar(); }
}

// ¿aparece 'e' en el stream a partir del indice 'desde'?
static bool contieneDesde(const std::vector<Evento>& ev, size_t desde, const Evento& e) {
    for (size_t i = desde; i < ev.size(); ++i) if (ev[i] == e) return true;
    return false;
}

TEST_CASE("memoria: exhibe la secuencia inicial (longitud 2 en nivel 1)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);
    // La secuencia [4,5] se mostro encendiendo cada LED.
    CHECK(contiene(col.eventos, Evento::led(4, 255)));
    CHECK(contiene(col.eventos, Evento::led(5, 255)));
    // Cada LED de la exhibicion lleva un tono (ACIERTO), mas el INICIO del start.
    CHECK(cuenta(col.eventos, Evento::Tipo::SOUND) >= 2);
}

TEST_CASE("memoria: repetir la secuencia correcta sube la longitud") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);

    hw.reloj += 300; motor.pisar(4);
    hw.reloj += 300; motor.pisar(5);  // secuencia [4,5] completada

    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_RONDA)));
    CHECK(contieneScore(col.eventos, /*mode*/ 1, /*hits*/ 1, /*misses*/ 0, /*round=len*/ 2));
    // Crece a [4,5,2] y se vuelve a exhibir: aparece el LED de la nueva casilla (2).
    terminarExhibicion(hw, motor);
    CHECK(contiene(col.eventos, Evento::led(2, 255)));
}

TEST_CASE("memoria: la pisada correcta intermedia suena ACIERTO") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);

    size_t base = col.eventos.size();
    hw.reloj += 300; motor.pisar(4);  // primer paso de [4,5]: acierto intermedio
    CHECK(contieneDesde(col.eventos, base, Evento::sound(cfg::SONIDO_ACIERTO)));
}

TEST_CASE("memoria: hay pausa entre completar y re-exhibir (no instantaneo)") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);
    hw.reloj += 300; motor.pisar(4);
    hw.reloj += 300; motor.pisar(5);  // completa [4,5]

    // Justo tras completar (RONDA + apagado), la nueva exhibicion NO arranca: PAUSA.
    size_t tras = col.eventos.size();
    hw.reloj += 100; motor.actualizar();          // +100 < pausa(1200): sigue en pausa
    CHECK(col.eventos.size() == tras);            // nada nuevo: no es instantaneo
    // Tras la pausa completa, la exhibicion transcurre y aparece el nuevo LED (2).
    terminarExhibicion(hw, motor);
    CHECK(contiene(col.eventos, Evento::led(2, 255)));
}

TEST_CASE("memoria: pisar mal cuenta error (mudo) y repite la misma secuencia") {
    FakeHardware hw; Colector col;
    GameEngine motor(hw, col.sink());
    arrancar(motor);
    terminarExhibicion(hw, motor);

    size_t base = col.eventos.size();
    hw.reloj += 300; motor.pisar(5);  // se esperaba 4 -> error

    CHECK(contieneScore(col.eventos, 1, /*hits*/ 0, /*misses*/ 1, /*round*/ 2));
    CHECK(!contieneDesde(col.eventos, base, Evento::sound(cfg::SONIDO_ACIERTO)));  // error mudo
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
    CHECK(contiene(col.eventos, Evento::sound(cfg::SONIDO_FIN)));
}

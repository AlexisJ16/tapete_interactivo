// Fuzz determinista del parser de protocolo: miles de lineas aleatorias y
// fragmentos estructurales no deben crashear ni provocar UB. El parser corre en
// el ESP32 (que compila sin excepciones), asi que una lectura fuera de rango o un
// std::stoll desbordado seria un abort. Correr una vez bajo ASan/UBSan.
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "Protocol.h"

#include <cstdint>
#include <string>

using namespace proto;

// LCG simple y determinista (portable, sin <random>).
struct Lcg {
    uint32_t s;
    explicit Lcg(uint32_t seed) : s(seed) {}
    uint32_t next() { s = s * 1664525u + 1013904223u; return s; }
    int rango(int n) { return static_cast<int>(next() % static_cast<uint32_t>(n)); }
};

static std::string lineaAleatoria(Lcg& r) {
    // Alfabeto que incluye lo estructural del JSON, digitos, signos, letras y
    // espacios; longitud variable (incluye vacio).
    static const char alf[] =
        "{}[]\":,0123456789-+abcdefghijklmnopqrstuvwxyz_ \t\\evcmd";
    const int n = sizeof(alf) - 1;
    int len = r.rango(90);
    std::string s;
    s.reserve(static_cast<size_t>(len));
    for (int i = 0; i < len; ++i) s += alf[r.rango(n)];
    return s;
}

TEST_CASE("fuzz: el parser de comandos no crashea ante lineas aleatorias") {
    Lcg r(12345);
    for (int i = 0; i < 20000; ++i) {
        Comando c = Comando::parsear(lineaAleatoria(r));
        (void)c;
    }
    CHECK(true);
}

TEST_CASE("fuzz: el parser de eventos no crashea ante lineas aleatorias") {
    Lcg r(67890);
    for (int i = 0; i < 20000; ++i) {
        Evento e = Evento::parsear(lineaAleatoria(r));
        (void)e;
    }
    CHECK(true);
}

TEST_CASE("fuzz: fragmentos estructurales y valores extremos") {
    const char* casos[] = {
        "", "{", "}", "{}", "{\"", "{\"cmd", "{\"cmd\":", "{\"cmd\":\"",
        "{\"cmd\":\"set_level\",\"level\":", "{\"cmd\":\"set_level\",\"level\":-",
        "{\"level\":999999999999999999999999999999}", "[]", "\"\"", ":,:,:,",
        "{\"a\":1,\"a\":2,\"a\":3}", "{\"cmd\":\"set_seed\",\"seed\":4294967295}",
        "{\"mode\":-2147483648}", "{\"x\":\\\\\\\\}",
    };
    for (const char* s : casos) {
        Comando c = Comando::parsear(s); (void)c;
        Evento e = Evento::parsear(s); (void)e;
    }
    CHECK(true);
}

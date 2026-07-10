#include "Protocol.h"

#include <vector>

namespace proto {
namespace {

// --- Mini-parser de objetos JSON planos --------------------------------------
struct Par {
    std::string clave;
    bool esCadena = false;
    std::string s;
    long long ent = 0;
};

void saltarEspacios(const std::string& t, size_t& i) {
    while (i < t.size() && (t[i] == ' ' || t[i] == '\t' ||
                            t[i] == '\r' || t[i] == '\n')) {
        ++i;
    }
}

// Lee una cadena entre comillas dobles (i debe apuntar a la '"' de apertura).
// Soporta los escapes \" y \\. Avanza i mas alla de la comilla de cierre.
bool leerCadena(const std::string& t, size_t& i, std::string& out) {
    if (i >= t.size() || t[i] != '"') return false;
    ++i;
    out.clear();
    while (i < t.size()) {
        char c = t[i++];
        if (c == '\\') {
            if (i >= t.size()) return false;
            char e = t[i++];
            out += e;            // \" -> "  ;  \\ -> \  (cualquier otro: literal)
        } else if (c == '"') {
            return true;
        } else {
            out += c;
        }
    }
    return false;  // sin comilla de cierre
}

bool leerEntero(const std::string& t, size_t& i, long long& out) {
    bool neg = false;
    if (i < t.size() && (t[i] == '-' || t[i] == '+')) { neg = (t[i] == '-'); ++i; }
    size_t digitos = 0;
    long long val = 0;
    // Acumulacion manual con saturacion: evita std::stoll, que lanzaria
    // out_of_range con numeros de >19 digitos (abort en el ESP32, que compila sin
    // excepciones). Se toman a lo sumo 18 digitos (caben en long long); el resto se
    // ignora. Cualquier valor mayor es basura para el protocolo.
    while (i < t.size() && t[i] >= '0' && t[i] <= '9') {
        if (digitos < 18) val = val * 10 + (t[i] - '0');
        ++i; ++digitos;
    }
    if (digitos == 0) return false;
    out = neg ? -val : val;
    return true;
}

// Parsea un objeto plano "{...}" a una lista de pares clave/valor.
bool parsearObjeto(const std::string& t, std::vector<Par>& out) {
    size_t i = 0;
    saltarEspacios(t, i);
    if (i >= t.size() || t[i] != '{') return false;
    ++i;
    saltarEspacios(t, i);
    if (i < t.size() && t[i] == '}') return true;  // objeto vacio
    while (true) {
        saltarEspacios(t, i);
        Par p;
        if (!leerCadena(t, i, p.clave)) return false;
        saltarEspacios(t, i);
        if (i >= t.size() || t[i] != ':') return false;
        ++i;
        saltarEspacios(t, i);
        if (i >= t.size()) return false;
        if (t[i] == '"') {
            p.esCadena = true;
            if (!leerCadena(t, i, p.s)) return false;
        } else {
            p.esCadena = false;
            if (!leerEntero(t, i, p.ent)) return false;
        }
        out.push_back(p);
        saltarEspacios(t, i);
        if (i >= t.size()) return false;
        if (t[i] == ',') { ++i; continue; }
        if (t[i] == '}') return true;
        return false;
    }
}

const Par* buscar(const std::vector<Par>& v, const char* clave) {
    for (const auto& p : v) if (p.clave == clave) return &p;
    return nullptr;
}
std::string cadena(const std::vector<Par>& v, const char* clave) {
    const Par* p = buscar(v, clave);
    return (p && p->esCadena) ? p->s : std::string();
}
long long entero(const std::vector<Par>& v, const char* clave) {
    const Par* p = buscar(v, clave);
    return (p && !p->esCadena) ? p->ent : 0;
}

std::string escapar(const std::string& s) {
    std::string o;
    o.reserve(s.size() + 2);
    for (char c : s) {
        if (c == '\\' || c == '"') o += '\\';
        o += c;
    }
    return o;
}

}  // namespace

// ============================================================================
//  Evento
// ============================================================================
Evento Evento::hello(const std::string& fw, int cells) {
    Evento e; e.tipo = Tipo::HELLO; e.fw = fw; e.cells = cells; return e;
}
Evento Evento::led(int cell, int level) {
    Evento e; e.tipo = Tipo::LED; e.cell = cell; e.level = level; return e;
}
Evento Evento::press(int cell, uint32_t ms) {
    Evento e; e.tipo = Tipo::PRESS; e.cell = cell; e.ms = ms; return e;
}
Evento Evento::sound(int id) {
    Evento e; e.tipo = Tipo::SOUND; e.id = id; return e;
}
Evento Evento::score(int mode, int hits, int misses, int rt_ms, int round) {
    Evento e; e.tipo = Tipo::SCORE; e.mode = mode; e.hits = hits;
    e.misses = misses; e.rt_ms = rt_ms; e.round = round; return e;
}
Evento Evento::state(int mode, const std::string& status) {
    Evento e; e.tipo = Tipo::STATE; e.mode = mode; e.status = status; return e;
}
Evento Evento::suggest(int mode, int from, int level,
                       const std::string& dir, int rate, int window) {
    Evento e; e.tipo = Tipo::SUGGEST; e.mode = mode; e.from = from;
    e.level = level; e.dir = dir; e.rate = rate; e.window = window; return e;
}

std::string Evento::serializar() const {
    switch (tipo) {
        case Tipo::HELLO:
            return "{\"ev\":\"hello\",\"fw\":\"" + escapar(fw) +
                   "\",\"cells\":" + std::to_string(cells) + "}";
        case Tipo::LED:
            return "{\"ev\":\"led\",\"cell\":" + std::to_string(cell) +
                   ",\"level\":" + std::to_string(level) + "}";
        case Tipo::PRESS:
            return "{\"ev\":\"press\",\"cell\":" + std::to_string(cell) +
                   ",\"ms\":" + std::to_string(ms) + "}";
        case Tipo::SOUND:
            return "{\"ev\":\"sound\",\"id\":" + std::to_string(id) + "}";
        case Tipo::SCORE:
            return "{\"ev\":\"score\",\"mode\":" + std::to_string(mode) +
                   ",\"hits\":" + std::to_string(hits) +
                   ",\"misses\":" + std::to_string(misses) +
                   ",\"rt_ms\":" + std::to_string(rt_ms) +
                   ",\"round\":" + std::to_string(round) + "}";
        case Tipo::STATE:
            return "{\"ev\":\"state\",\"mode\":" + std::to_string(mode) +
                   ",\"status\":\"" + escapar(status) + "\"}";
        case Tipo::SUGGEST:
            return "{\"ev\":\"suggest\",\"mode\":" + std::to_string(mode) +
                   ",\"from\":" + std::to_string(from) +
                   ",\"level\":" + std::to_string(level) +
                   ",\"dir\":\"" + escapar(dir) + "\"" +
                   ",\"rate\":" + std::to_string(rate) +
                   ",\"window\":" + std::to_string(window) + "}";
        default:
            return "";
    }
}

Evento Evento::parsear(const std::string& linea) {
    std::vector<Par> v;
    Evento e;
    if (!parsearObjeto(linea, v)) return e;  // INVALIDO
    std::string ev = cadena(v, "ev");
    if (ev == "hello") {
        e.tipo = Tipo::HELLO; e.fw = cadena(v, "fw");
        e.cells = static_cast<int>(entero(v, "cells"));
    } else if (ev == "led") {
        e.tipo = Tipo::LED; e.cell = static_cast<int>(entero(v, "cell"));
        e.level = static_cast<int>(entero(v, "level"));
    } else if (ev == "press") {
        e.tipo = Tipo::PRESS; e.cell = static_cast<int>(entero(v, "cell"));
        e.ms = static_cast<uint32_t>(entero(v, "ms"));
    } else if (ev == "sound") {
        e.tipo = Tipo::SOUND; e.id = static_cast<int>(entero(v, "id"));
    } else if (ev == "score") {
        e.tipo = Tipo::SCORE; e.mode = static_cast<int>(entero(v, "mode"));
        e.hits = static_cast<int>(entero(v, "hits"));
        e.misses = static_cast<int>(entero(v, "misses"));
        e.rt_ms = static_cast<int>(entero(v, "rt_ms"));
        e.round = static_cast<int>(entero(v, "round"));
    } else if (ev == "state") {
        e.tipo = Tipo::STATE; e.mode = static_cast<int>(entero(v, "mode"));
        e.status = cadena(v, "status");
    } else if (ev == "suggest") {
        e.tipo = Tipo::SUGGEST;
        e.mode = static_cast<int>(entero(v, "mode"));
        e.from = static_cast<int>(entero(v, "from"));
        e.level = static_cast<int>(entero(v, "level"));
        e.dir = cadena(v, "dir");
        e.rate = static_cast<int>(entero(v, "rate"));
        e.window = static_cast<int>(entero(v, "window"));
    }
    return e;
}

bool Evento::operator==(const Evento& o) const {
    return tipo == o.tipo && fw == o.fw && cells == o.cells && cell == o.cell &&
           level == o.level && ms == o.ms && id == o.id && mode == o.mode &&
           hits == o.hits && misses == o.misses && rt_ms == o.rt_ms &&
           round == o.round && status == o.status &&
           from == o.from && dir == o.dir && rate == o.rate && window == o.window;
}

// ============================================================================
//  Comando
// ============================================================================
std::string Comando::serializar() const {
    switch (tipo) {
        case Tipo::SET_MODE:
            return "{\"cmd\":\"set_mode\",\"mode\":" + std::to_string(mode) +
                   ",\"level\":" + std::to_string(level) + "}";
        case Tipo::START:     return "{\"cmd\":\"start\"}";
        case Tipo::STOP:      return "{\"cmd\":\"stop\"}";
        case Tipo::PAUSE:     return "{\"cmd\":\"pause\"}";
        case Tipo::SET_LEVEL:
            return "{\"cmd\":\"set_level\",\"level\":" + std::to_string(level) + "}";
        case Tipo::SET_PLAYER:
            return "{\"cmd\":\"set_player\",\"id\":\"" + escapar(id) +
                   "\",\"name\":\"" + escapar(name) + "\"}";
        case Tipo::SET_SEED:
            return "{\"cmd\":\"set_seed\",\"seed\":" + std::to_string(seed) + "}";
        case Tipo::PING:      return "{\"cmd\":\"ping\"}";
        default:              return "";
    }
}

Comando Comando::parsear(const std::string& linea) {
    std::vector<Par> v;
    Comando c;
    if (!parsearObjeto(linea, v)) return c;  // INVALIDO
    std::string cmd = cadena(v, "cmd");
    if (cmd == "set_mode") {
        c.tipo = Tipo::SET_MODE; c.mode = static_cast<int>(entero(v, "mode"));
        c.level = static_cast<int>(entero(v, "level"));
    } else if (cmd == "start") {
        c.tipo = Tipo::START;
    } else if (cmd == "stop") {
        c.tipo = Tipo::STOP;
    } else if (cmd == "pause") {
        c.tipo = Tipo::PAUSE;
    } else if (cmd == "set_level") {
        c.tipo = Tipo::SET_LEVEL; c.level = static_cast<int>(entero(v, "level"));
    } else if (cmd == "set_player") {
        c.tipo = Tipo::SET_PLAYER; c.id = cadena(v, "id"); c.name = cadena(v, "name");
    } else if (cmd == "set_seed") {
        c.tipo = Tipo::SET_SEED; c.seed = static_cast<uint32_t>(entero(v, "seed"));
    } else if (cmd == "ping") {
        c.tipo = Tipo::PING;
    }
    return c;
}

bool Comando::operator==(const Comando& o) const {
    return tipo == o.tipo && mode == o.mode && level == o.level &&
           seed == o.seed && id == o.id && name == o.name;
}

}  // namespace proto

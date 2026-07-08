#include "GameEngine.h"

#include "modes/ModoEquilibrio.h"
#include "modes/ModoMemoria.h"
#include "modes/ModoVelocidad.h"

namespace {
// Unico lugar que decide que ids de modo existen (ver GameEngine::crearModo).
bool modoValido(int id) { return id >= 1 && id <= 3; }
bool nivelValido(int nivel) {
    return nivel >= cfg::adaptacion::nivelMin && nivel <= cfg::adaptacion::nivelMax;
}
}  // namespace

const char* nombreEstado(Estado e) {
    switch (e) {
        case Estado::IDLE:     return "idle";
        case Estado::RUNNING:  return "running";
        case Estado::PAUSED:   return "paused";
        case Estado::FINISHED: return "finished";
    }
    return "idle";
}

GameEngine::GameEngine(IHardware& hw, Emisor emisor)
    : hw_(hw), emisor_(std::move(emisor)) {}

uint32_t GameEngine::sesionMs() {
    return hw_.millis() - inicio_;
}

void GameEngine::cambiarEstado(Estado e) {
    estado_ = e;
    emitir(proto::Evento::state(modoId_, nombreEstado(e)));
}

void GameEngine::apagarTodos() {
    for (int c = 1; c <= cfg::CELDAS; ++c) led(c, cfg::LED_APAGADO);
}

void GameEngine::crearModo(int id) {
    switch (id) {
        case 1:  modo_.reset(new ModoMemoria(*this, nivel_)); break;
        case 2:  modo_.reset(new ModoVelocidad(*this, nivel_)); break;
        case 3:  modo_.reset(new ModoEquilibrio(*this, nivel_)); break;
        default: modo_.reset(); break;
    }
}

void GameEngine::revisarFin() {
    if (estado_ == Estado::RUNNING && modo_ && modo_->terminado()) {
        cambiarEstado(Estado::FINISHED);
        apagarTodos();
    }
}

void GameEngine::procesar(const proto::Comando& c) {
    using T = proto::Comando::Tipo;
    switch (c.tipo) {
        case T::SET_MODE:
            // Modo desconocido o nivel fuera de rango: se ignora el comando
            // completo (no deja el motor con un modoId_/nivel_ invalido).
            if (!modoValido(c.mode) || !nivelValido(c.level)) break;
            modoId_ = c.mode;
            nivel_ = c.level;
            crearModo(modoId_);
            // Cambiar de modo durante una sesion activa la detiene. El modo recien
            // creado aun NO esta iniciado (patron_/enPatron_ sin inicializar);
            // dejarlo en RUNNING/PAUSED haria que actualizar()/pisar() operen sobre
            // memoria basura y emitan LEDs con celda corrupta. Volver a IDLE (a la
            // espera de START) es el estado seguro y predecible.
            if (estado_ == Estado::RUNNING || estado_ == Estado::PAUSED) {
                apagarTodos();
                cambiarEstado(Estado::IDLE);
            }
            break;
        case T::SET_LEVEL:
            // Nivel fuera de rango: se ignora (el nivel actual no cambia).
            if (!nivelValido(c.level)) break;
            nivel_ = c.level;
            // Solo recrea el modo FUERA de una sesion activa. En RUNNING/PAUSED
            // el modo sigue vivo y la proxima ronda recalcula sus parametros
            // por-ronda con el nuevo nivel (corrige el bug de recrear sin iniciar).
            if (estado_ == Estado::IDLE || estado_ == Estado::FINISHED)
                crearModo(modoId_);
            break;
        case T::SET_SEED:
            rng_.sembrar(c.seed);
            break;
        case T::START:
            if (modo_) {
                inicio_ = hw_.millis();
                recomendador_.reiniciar();
                prevHits_ = 0;
                prevMisses_ = 0;
                ultimaDirEmitida_ = adapt::Direccion::MANTENER;
                cambiarEstado(Estado::RUNNING);
                modo_->iniciar(0);
                revisarFin();
            }
            break;
        case T::STOP:
            apagarTodos();
            cambiarEstado(Estado::IDLE);
            break;
        case T::PAUSE:
            if (estado_ == Estado::RUNNING)      cambiarEstado(Estado::PAUSED);
            else if (estado_ == Estado::PAUSED)  cambiarEstado(Estado::RUNNING);
            break;
        case T::PING:
            emitir(proto::Evento::hello(cfg::VERSION_FW, cfg::CELDAS));
            break;
        case T::SET_PLAYER:
            // El perfil lo gestiona el dashboard; la logica no necesita guardarlo.
            break;
        case T::INVALIDO:
        default:
            break;
    }
}

void GameEngine::procesarLinea(const std::string& linea) {
    procesar(proto::Comando::parsear(linea));
}

void GameEngine::actualizar() {
    if (estado_ == Estado::RUNNING && modo_) {
        modo_->actualizar(sesionMs());
        revisarFin();
    }
}

void GameEngine::pisar(int celda) {
    if (celda < 1 || celda > cfg::CELDAS) return;  // celda fuera del tapete: se ignora
    if (estado_ == Estado::RUNNING && modo_) {
        uint32_t ms = sesionMs();
        emitir(proto::Evento::press(celda, ms));
        modo_->pisar(celda, ms);
        revisarFin();
    }
}

// --- IMotor ---
void GameEngine::led(int celda, int nivel) {
    hw_.setLed(celda, nivel);
    emitir(proto::Evento::led(celda, nivel));
}
void GameEngine::sonido(int id) {
    hw_.reproducirSonido(id);
    emitir(proto::Evento::sound(id));
}
void GameEngine::score(int hits, int misses, int rt_ms, int round) {
    emitir(proto::Evento::score(modoId_, hits, misses, rt_ms, round));

    // --- Capa adaptable (SP1) -------------------------------------------------
    // Deriva el resultado de la ronda de los acumuladores (NO del campo round:
    // en Memoria 'round' = len_, no es monotono). Cada score sube exactamente
    // uno de hits/misses en +1.
    bool acierto = (hits - prevHits_) > 0;
    prevHits_ = hits;
    prevMisses_ = misses;
    recomendador_.registrarResultado(acierto);

    adapt::Sugerencia s = recomendador_.evaluar(nivel_);
    if (s.dir != ultimaDirEmitida_) {            // de-dup: solo al cambiar
        ultimaDirEmitida_ = s.dir;
        int ratePct = static_cast<int>(s.tasa * 100.0f + 0.5f);
        emitir(proto::Evento::suggest(modoId_, nivel_, s.nivelSugerido,
                                      adapt::aTexto(s.dir), ratePct,
                                      cfg::adaptacion::W));
    }
}

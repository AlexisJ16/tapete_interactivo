#include "GameEngine.h"

#include "modes/ModoEquilibrio.h"
#include "modes/ModoMemoria.h"
#include "modes/ModoVelocidad.h"

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
            modoId_ = c.mode;
            nivel_ = c.level;
            crearModo(modoId_);
            break;
        case T::SET_LEVEL:
            nivel_ = c.level;
            crearModo(modoId_);  // re-crea el modo con el nuevo nivel
            break;
        case T::SET_SEED:
            rng_.sembrar(c.seed);
            break;
        case T::START:
            if (modo_) {
                inicio_ = hw_.millis();
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
}

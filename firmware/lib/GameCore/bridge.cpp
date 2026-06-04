// Puente C (ABI estable) sobre GameEngine para cargarlo desde Python (ctypes).
// Convierte al .so en "el ESP32 en software": se le inyectan comandos y pisadas,
// y entrega los eventos del protocolo como lineas JSON. Reutiliza Protocol.cpp,
// de modo que la serializacion es identica a la del firmware real.
//
// Este archivo SOLO se usa en el build del .so; en el ESP32 la entrada/salida
// la maneja main.cpp (Serial/TCP). No contiene logica de juego.

#include <deque>
#include <string>

#include "Config.h"
#include "GameEngine.h"
#include "IHardware.h"
#include "Protocol.h"

namespace {

// Hardware virtual del simulador: reloj controlado desde Python; los LEDs y
// sonidos NO se actuan aqui (el lado Python los obtiene de los eventos del
// protocolo, que el motor emite junto con cada accion).
struct HardwarePuente : IHardware {
    uint32_t reloj = 0;
    uint32_t millis() override { return reloj; }
    int leerSensor(int) override { return 0; }
    void setLed(int, int) override {}
    void reproducirSonido(int) override {}
};

// Una instancia = un motor + su hardware + la cola de eventos emitidos.
struct Puente {
    HardwarePuente hw;
    std::deque<std::string> cola;
    std::string ultimo;  // mantiene vivo el c_str() devuelto hasta la sgte. llamada
    GameEngine motor;

    Puente()
        : motor(hw, [this](const proto::Evento& e) { cola.push_back(e.serializar()); }) {}
};

}  // namespace

extern "C" {

void* tapete_crear() {
    return new Puente();
}

void tapete_destruir(void* h) {
    delete static_cast<Puente*>(h);
}

void tapete_set_millis(void* h, uint32_t ms) {
    static_cast<Puente*>(h)->hw.reloj = ms;
}

void tapete_comando(void* h, const char* linea) {
    if (!linea) return;
    static_cast<Puente*>(h)->motor.procesarLinea(linea);
}

void tapete_actualizar(void* h) {
    static_cast<Puente*>(h)->motor.actualizar();
}

void tapete_pisar(void* h, int celda) {
    static_cast<Puente*>(h)->motor.pisar(celda);
}

// Devuelve la siguiente linea de evento (FIFO) o NULL si no hay. El puntero es
// valido hasta la proxima llamada a esta funcion (no hay malloc que liberar).
const char* tapete_siguiente_evento(void* h) {
    Puente* p = static_cast<Puente*>(h);
    if (p->cola.empty()) return nullptr;
    p->ultimo = p->cola.front();
    p->cola.pop_front();
    return p->ultimo.c_str();
}

}  // extern "C"

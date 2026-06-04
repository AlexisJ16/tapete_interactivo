#ifndef TAPETE_GAMEENGINE_H
#define TAPETE_GAMEENGINE_H

#include <functional>
#include <memory>
#include <string>

#include "Config.h"
#include "IHardware.h"
#include "Motor.h"
#include "Protocol.h"
#include "Rng.h"

// Sumidero de eventos: el motor emite eventos del protocolo a traves de este
// callback. En el ESP32 escribe lineas JSON al Serial/TCP; en el simulador las
// entrega al puente; en los tests las acumula un Colector.
using Emisor = std::function<void(const proto::Evento&)>;

enum class Estado { IDLE, RUNNING, PAUSED, FINISHED };
const char* nombreEstado(Estado e);

// Maquina de estados general. Es independiente del hardware (habla por IHardware)
// y del transporte (emite por Emisor). Esta MISMA clase corre en el ESP32 y,
// compilada como .so, dentro del simulador: una sola fuente de verdad.
class GameEngine : public IMotor {
public:
    GameEngine(IHardware& hw, Emisor emisor);

    // Comandos PC -> cerebro.
    void procesar(const proto::Comando& c);
    void procesarLinea(const std::string& linea);  // parsea y procesa (para el puente)

    // El reloj lo provee IHardware: el motor lee hw.millis() internamente.
    void actualizar();           // avance temporal (timeouts, exhibicion de secuencias)
    void pisar(int celda);       // pisada detectada en 'celda' (1..CELDAS)

    Estado estado() const { return estado_; }
    int modoId() const { return modoId_; }
    int nivel() const { return nivel_; }

    // --- IMotor (usado por los modos) ---
    void led(int celda, int nivel) override;
    void sonido(int id) override;
    void score(int hits, int misses, int rt_ms, int round) override;
    Rng& rng() override { return rng_; }

private:
    void emitir(const proto::Evento& e) { if (emisor_) emisor_(e); }
    void cambiarEstado(Estado e);
    void crearModo(int id);
    void revisarFin();
    void apagarTodos();
    uint32_t sesionMs();

    IHardware& hw_;
    Emisor emisor_;
    Rng rng_;
    std::unique_ptr<IModo> modo_;
    Estado estado_ = Estado::IDLE;
    int modoId_ = 0;
    int nivel_ = 1;
    uint32_t inicio_ = 0;
};

#endif  // TAPETE_GAMEENGINE_H

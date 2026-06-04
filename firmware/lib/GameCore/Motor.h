#ifndef TAPETE_MOTOR_H
#define TAPETE_MOTOR_H

#include <cstdint>
#include "Rng.h"

// Servicios que el motor (GameEngine) ofrece a los modos para producir efectos
// y eventos del protocolo. Cada metodo combina la accion fisica (hardware) con
// la emision del evento correspondiente hacia la PC. Los modos NO tocan el
// hardware ni el protocolo directamente: solo usan IMotor.
struct IMotor {
    // Enciende/atenua el LED de la casilla (1..CELDAS), nivel 0..255.
    // Emite tambien el evento {"ev":"led",...}.
    virtual void led(int celda, int nivel) = 0;

    // Reproduce el sonido 'id' y emite {"ev":"sound","id":...}.
    virtual void sonido(int id) = 0;

    // Emite {"ev":"score",...}. El motor anade el 'mode' actual.
    virtual void score(int hits, int misses, int rt_ms, int round) = 0;

    // Generador pseudoaleatorio determinista compartido (semilla via set_seed).
    virtual Rng& rng() = 0;

    virtual ~IMotor() = default;
};

// Interfaz comun de los tres modos de juego. Maquina de estados no bloqueante:
// el motor le pasa el tiempo de sesion (ms) en cada llamada; el modo nunca
// duerme ni bloquea.
struct IModo {
    // Inicia la sesion del modo en el instante 'ms' (tiempo de sesion).
    virtual void iniciar(uint32_t ms) = 0;

    // Avance temporal: procesa timeouts y transiciones programadas hasta 'ms'.
    virtual void actualizar(uint32_t ms) = 0;

    // Procesa la pisada de 'celda' (1..CELDAS) en el instante 'ms'.
    virtual void pisar(int celda, uint32_t ms) = 0;

    // ¿La sesion del modo termino?
    virtual bool terminado() const = 0;

    virtual ~IModo() = default;
};

#endif  // TAPETE_MOTOR_H

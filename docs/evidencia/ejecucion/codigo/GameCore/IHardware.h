#ifndef TAPETE_IHARDWARE_H
#define TAPETE_IHARDWARE_H

#include <cstdint>

// Interfaz de hardware abstracta. GameCore SOLO habla con el mundo a traves de
// esta interfaz; no contiene llamadas Arduino (analogRead/ledcWrite/etc.).
//  - EspHardware la implementa en el ESP32 (FSR via ADC, LEDs via LEDC/PWM, DFPlayer).
//  - El simulador la implementa en software (clics = pisadas, LEDs = dibujo, audio).
struct IHardware {
    // Milisegundos monotonicos desde el arranque (como Arduino millis()).
    virtual uint32_t millis() = 0;

    // Lectura cruda del sensor de presion de la casilla 'celda' (1..CELDAS).
    // En el ESP32 es el ADC (0..4095). La deteccion de pisada (umbral/antirrebote)
    // es responsabilidad de la capa de hardware, que llama a GameEngine::pisar().
    virtual int leerSensor(int celda) = 0;

    // Fija el brillo del grupo de LEDs de 'celda' (1..CELDAS), nivel 0..255.
    virtual void setLed(int celda, int nivel) = 0;

    // Reproduce el audio 000{id}.mp3.
    virtual void reproducirSonido(int id) = 0;

    virtual ~IHardware() = default;
};

#endif  // TAPETE_IHARDWARE_H

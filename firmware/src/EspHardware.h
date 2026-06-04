#ifndef TAPETE_ESP_HARDWARE_H
#define TAPETE_ESP_HARDWARE_H

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

#include "IHardware.h"

// Implementacion real de IHardware sobre el ESP32:
//   - FSR  -> ADC (analogRead, 0..4095)
//   - LEDs -> LEDC/PWM (ledcAttach/ledcWrite), NO LEDs direccionables
//   - Audio-> DFPlayer Mini por Serial2
//
// Solo aqui hay llamadas Arduino. La logica de juego (GameCore) no las conoce.
class EspHardware : public IHardware {
public:
    void begin();

    uint32_t millis() override;
    int leerSensor(int celda) override;       // celda 1..CELDAS
    void setLed(int celda, int nivel) override;  // nivel 0..255 (PWM 8 bits)
    void reproducirSonido(int id) override;

    bool audioDisponible() const { return audioOk_; }

private:
    DFRobotDFPlayerMini player_;
    bool audioOk_ = false;
};

#endif  // TAPETE_ESP_HARDWARE_H

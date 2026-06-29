#include "EspHardware.h"

#include "Config.h"

// Frecuencia y resolucion del PWM de los LEDs (LEDC). 8 bits => duty 0..255,
// que coincide con el rango de brillo del protocolo.
static constexpr uint32_t LEDC_FREQ = 5000;     // Hz
static constexpr uint8_t  LEDC_BITS = 8;         // resolucion -> 0..255

// La API de LEDC cambio entre Arduino-ESP32 2.x (por canal) y 3.x (por pin).
// Soportamos ambas: el canal del modo 2.x es (celda-1).
#define USA_LEDC_POR_PIN (ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0))

void EspHardware::begin() {
    // LEDs: un canal/grupo PWM por casilla.
    for (int i = 0; i < cfg::CELDAS; ++i) {
#if USA_LEDC_POR_PIN
        ledcAttach(cfg::PIN_LED[i], LEDC_FREQ, LEDC_BITS);
        ledcWrite(cfg::PIN_LED[i], 0);
#else
        ledcSetup(i, LEDC_FREQ, LEDC_BITS);        // canal i
        ledcAttachPin(cfg::PIN_LED[i], i);
        ledcWrite(i, 0);
#endif
    }

    // FSR: GPIO de solo entrada en ADC1. analogRead -> 0..4095 (12 bits).
    analogReadResolution(12);
    for (int i = 0; i < cfg::CELDAS; ++i) {
        pinMode(cfg::PIN_FSR[i], INPUT);
    }

    // DFPlayer Mini por Serial2 (RX=GPIO16, TX=GPIO17).
    Serial2.begin(9600, SERIAL_8N1, cfg::PIN_DFPLAYER_RX, cfg::PIN_DFPLAYER_TX);
    delay(50);
    audioOk_ = player_.begin(Serial2, /*isACK=*/true, /*doReset=*/true);
    if (audioOk_) {
        player_.volume(22);  // 0..30
    }
}

uint32_t EspHardware::millis() {
    return ::millis();
}

int EspHardware::leerSensor(int celda) {
    if (celda < 1 || celda > cfg::CELDAS) return 0;
    return analogRead(cfg::PIN_FSR[celda - 1]);
}

void EspHardware::setLed(int celda, int nivel) {
    if (celda < 1 || celda > cfg::CELDAS) return;
    if (nivel < 0) nivel = 0;
    if (nivel > 255) nivel = 255;
#if USA_LEDC_POR_PIN
    ledcWrite(cfg::PIN_LED[celda - 1], static_cast<uint32_t>(nivel));
#else
    ledcWrite(celda - 1, static_cast<uint32_t>(nivel));  // canal = celda-1
#endif
}

void EspHardware::reproducirSonido(int id) {
    if (audioOk_) {
        // playMp3Folder reproduce /mp3/000{id}.mp3 por NUMERO (fiable), a
        // diferencia de play(), que depende del orden en que se copiaron los
        // archivos a la SD. Ver audio/README.md y docs/hardware/flashing.md.
        player_.playMp3Folder(id);
    }
}

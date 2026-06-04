// Entrada del firmware ESP32: WiFi + servidor TCP (3333) + EspHardware + GameEngine.
//
// La LOGICA es la misma que se valido en el simulador (lib/GameCore). Aqui solo
// se conectan los drivers reales y el transporte. Pasar del simulador al ESP32
// es: flashear + poner credenciales WiFi + abrir el dashboard. Cero cambios de logica.

#include <Arduino.h>
#include <WiFi.h>

#include "Config.h"
#include "EspHardware.h"
#include "GameEngine.h"
#include "Protocol.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#warning "Sin src/secrets.h: usando credenciales placeholder. Copia src/secrets.h.example a src/secrets.h."
#define WIFI_SSID "CAMBIAME"
#define WIFI_PASS "CAMBIAME"
#endif

static EspHardware hw;
static WiFiServer servidor(cfg::PUERTO_TCP);
static WiFiClient cliente;
static GameEngine* motor = nullptr;
static String bufferCliente;
static String bufferSerial;

// Antirrebote de pisadas (la deteccion FSR vive en la capa de hardware, no en GameCore).
static bool pisada[cfg::CELDAS + 1] = {false};
static uint32_t ultimaPisada[cfg::CELDAS + 1] = {0};
static constexpr uint32_t ANTIRREBOTE_MS = 120;

// Emisor: cada evento del motor se manda al Serial y al cliente TCP conectado.
static void emitir(const proto::Evento& e) {
    String linea = String(e.serializar().c_str());
    Serial.println(linea);
    if (cliente && cliente.connected()) {
        cliente.print(linea);
        cliente.print('\n');
    }
}

static void conectarWiFi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print("Conectando a WiFi");
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
        delay(300);
        Serial.print('.');
    }
    Serial.println();
    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("WiFi OK. IP: ");
        Serial.println(WiFi.localIP());
        Serial.print("Servidor TCP en puerto ");
        Serial.println(cfg::PUERTO_TCP);
    } else {
        Serial.println("Sin WiFi: el dashboard puede usar el Serial (mismo protocolo).");
    }
}

static void procesarLineasDe(WiFiClient& c, String& buf) {
    while (c && c.available()) {
        char ch = (char)c.read();
        if (ch == '\n') {
            if (buf.length()) { motor->procesarLinea(buf.c_str()); buf = ""; }
        } else if (ch != '\r') {
            buf += ch;
        }
    }
}

static void procesarLineasSerial() {
    while (Serial.available()) {
        char ch = (char)Serial.read();
        if (ch == '\n') {
            if (bufferSerial.length()) { motor->procesarLinea(bufferSerial.c_str()); bufferSerial = ""; }
        } else if (ch != '\r') {
            bufferSerial += ch;
        }
    }
}

static void detectarPisadas() {
    uint32_t ahora = hw.millis();
    for (int c = 1; c <= cfg::CELDAS; ++c) {
        int v = hw.leerSensor(c);
        bool activo = v >= cfg::UMBRAL_PISADA;
        if (activo && !pisada[c] && (ahora - ultimaPisada[c] > ANTIRREBOTE_MS)) {
            pisada[c] = true;
            ultimaPisada[c] = ahora;
            motor->pisar(c);   // pisada detectada -> a la logica de juego
        } else if (!activo) {
            pisada[c] = false;
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(200);
    hw.begin();
    Serial.println("Tapete Interactivo — firmware 1.0.0");
    if (!hw.audioDisponible()) {
        Serial.println("AVISO: DFPlayer no detectado (revisa cableado/SD). Sigue sin audio.");
    }
    conectarWiFi();
    servidor.begin();
    servidor.setNoDelay(true);

    static GameEngine eng(hw, emitir);
    motor = &eng;
}

void loop() {
    // Aceptar/renovar cliente del dashboard.
    if (!cliente || !cliente.connected()) {
        WiFiClient nuevo = servidor.available();
        if (nuevo) {
            cliente = nuevo;
            emitir(proto::Evento::hello(cfg::VERSION_FW, cfg::CELDAS));
        }
    }

    procesarLineasDe(cliente, bufferCliente);
    procesarLineasSerial();
    detectarPisadas();
    motor->actualizar();   // avance temporal no bloqueante (timeouts, exhibicion)
}

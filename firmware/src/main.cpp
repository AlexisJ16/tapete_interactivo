// Entrada del firmware ESP32: WiFi + servidor TCP (3333) + EspHardware + GameEngine.
//
// La LOGICA es la misma que se valido en el simulador (lib/GameCore). Aqui solo
// se conectan los drivers reales y el transporte. Pasar del simulador al ESP32
// es: flashear + poner credenciales WiFi + abrir el dashboard. Cero cambios de logica.

#include <Arduino.h>
#include <WiFi.h>
#include <lwip/sockets.h>  // select()/fd_set: guarda de escritura no bloqueante (ver emitir())

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
// Cota del buffer de linea de entrada (serial/TCP): una linea de protocolo real
// ronda los 100 bytes; mas de esto sin '\n' es basura -> se descarta (protege la
// RAM del ESP32 de una linea patologica sin fin).
static constexpr unsigned MAX_LINEA = 256;
// Cota de bytes leidos por fuente en CADA vuelta del loop(): sin esto, un
// `while (available())` drena todo lo que ya llego al buffer de recepcion
// (WiFi o UART) de un tiron. Con un cliente/atacante que manda un flujo
// continuo eso puede acaparar la iteracion y postergar detectarPisadas() y
// motor->actualizar() (LEDs, timeouts) por tiempo indefinido. 512 bytes ~
// 2-5 lineas reales de protocolo por vuelta: rinde bien en uso normal y
// deja el resto para la(s) siguiente(s) vuelta(s) si llega una rafaga mayor.
static constexpr unsigned MAX_BYTES_POR_VUELTA = 512;

// ¿El socket del cliente admite escritura AHORA MISMO (sin esperar)? select()
// con timeout {0,0} es no bloqueante (devuelve al instante). Sirve para
// esquivar un cliente "vivo" a nivel TCP (connected()==true, no mando FIN/RST)
// pero que dejo de leer (app del dashboard colgada): su buffer de recepcion
// se llena y, sin esta guarda, WiFiClient::write() reintenta con select() de
// 1s hasta 10 veces (~10s) POR CADA print(). Como emitir() se llama en cada
// evento del motor, eso repetiria el bloqueo de ~20s en cada evento mientras
// el cliente siga atascado, congelando el loop() (LEDs/sensores/motor) de
// forma indefinida. Con la guarda, en cuanto el buffer se llena se detecta
// aqui y se salta el envio a ese cliente (el Serial igual recibe el evento);
// el loop() nunca se queda esperando a un cliente que no lee.
static bool clienteAceptaEscritura() {
    int fd = cliente.fd();
    if (fd < 0) return false;
    fd_set wfds;
    FD_ZERO(&wfds);
    FD_SET(fd, &wfds);
    struct timeval sinEspera{0, 0};
    return select(fd + 1, nullptr, &wfds, nullptr, &sinEspera) > 0;
}

// Emisor: cada evento del motor se manda al Serial y al cliente TCP conectado.
static void emitir(const proto::Evento& e) {
    String linea = String(e.serializar().c_str());
    Serial.println(linea);
    if (cliente && cliente.connected() && clienteAceptaEscritura()) {
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
    unsigned leidos = 0;
    while (c && c.available() && leidos < MAX_BYTES_POR_VUELTA) {
        char ch = (char)c.read();
        ++leidos;
        if (ch == '\n') {
            if (buf.length()) { motor->procesarLinea(buf.c_str()); buf = ""; }
        } else if (ch != '\r') {
            if (buf.length() >= MAX_LINEA) buf = "";  // linea sin fin: descartar
            buf += ch;
        }
    }
}

static void procesarLineasSerial() {
    unsigned leidos = 0;
    while (Serial.available() && leidos < MAX_BYTES_POR_VUELTA) {
        char ch = (char)Serial.read();
        ++leidos;
        if (ch == '\n') {
            if (bufferSerial.length()) { motor->procesarLinea(bufferSerial.c_str()); bufferSerial = ""; }
        } else if (ch != '\r') {
            if (bufferSerial.length() >= MAX_LINEA) bufferSerial = "";
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
#ifndef CALIBRACION
    conectarWiFi();
    servidor.begin();
    servidor.setNoDelay(true);
#endif

    static GameEngine eng(hw, emitir);
    motor = &eng;
}

void loop() {
#ifdef CALIBRACION
    // Modo calibracion (entorno esp32dev_calib, -DCALIBRACION). NO corre el juego
    // ni WiFi. Muestra SIEMPRE, por cada FSR: valor actual, reposo (min), pico
    // (max) y rango. El ✓ es solo una PISTA (rango >= UMBRAL_DET sobre el reposo);
    // los numeros mandan. Un canal conectado tiene reposo estable; uno al aire da
    // ~0 (GPIO36/39/34/35) o ruido (GPIO32/33). Enter = reiniciar min/max.
    static bool init = false;
    static uint32_t ultimo = 0;
    static int minv[cfg::CELDAS + 1];
    static int maxv[cfg::CELDAS + 1];
    static int act[cfg::CELDAS + 1];
    constexpr int UMBRAL_DET = 150;   // salto sobre el reposo que se marca como pisada
    if (!init) {
        for (int c = 1; c <= cfg::CELDAS; ++c) { minv[c] = 4095; maxv[c] = 0; }
        init = true;
    }
    if (Serial.available()) {                          // Enter -> reinicia
        while (Serial.available()) Serial.read();
        for (int c = 1; c <= cfg::CELDAS; ++c) { minv[c] = 4095; maxv[c] = 0; }
        Serial.println(">>> reiniciado (pisa UN sensor fuerte) <<<");
    }
    for (int c = 1; c <= cfg::CELDAS; ++c) {           // promedio de 16 -> menos ruido
        uint32_t suma = 0;
        for (int k = 0; k < 16; ++k) suma += hw.leerSensor(c);
        int v = suma / 16;
        act[c] = v;
        if (v < minv[c]) minv[c] = v;
        if (v > maxv[c]) maxv[c] = v;
    }
    if (hw.millis() - ultimo >= 700) {
        ultimo = hw.millis();
        int repMax = 0, picoMin = 4095, nOk = 0;
        Serial.println("====== CALIBRACION FSR ======  (Enter=reiniciar)");
        for (int c = 1; c <= cfg::CELDAS; ++c) {
            int rango = maxv[c] - minv[c];
            bool ok = rango >= UMBRAL_DET;
            String l = "  FSR" + String(c)
                     + "  act=" + String(act[c])
                     + "  reposo=" + String(minv[c])
                     + "  pico=" + String(maxv[c])
                     + "  rango=" + String(rango) + "  ";
            if (ok) {
                int umbral = minv[c] + rango * 2 / 5;     // reposo + 40% del rango
                l += "✓ umbral=" + String(umbral);
                if (minv[c] > repMax) repMax = minv[c];
                if (maxv[c] < picoMin) picoMin = maxv[c];
                nOk++;
            } else {
                l += "✗";
            }
            Serial.println(l);
        }
        if (nOk > 0) {
            int comun = repMax + (picoMin - repMax) * 35 / 100;
            Serial.println("  -> UMBRAL comun sugerido: " + String(comun)
                         + "   (canales con actividad: " + String(nOk) + ")");
        }
        Serial.println("=============================================");
    }
    return;
#endif
    // Aceptar/renovar cliente del dashboard. `cliente = nuevo` ya libera el
    // socket viejo (WiFiClient::operator= llama stop() antes de copiar), asi
    // que un cliente caido no deja el puerto colgado. Lo que SI hay que
    // limpiar a mano es bufferCliente: si el cliente anterior se cayo a mitad
    // de una linea (sin '\n'), esos bytes quedarian pegados al inicio de la
    // primera linea del cliente nuevo y se procesarian como si fueran suyos.
    if (!cliente || !cliente.connected()) {
        WiFiClient nuevo = servidor.available();
        if (nuevo) {
            cliente = nuevo;
            bufferCliente = "";  // nueva sesion: descarta el resto sin '\n' de la anterior
            emitir(proto::Evento::hello(cfg::VERSION_FW, cfg::CELDAS));
        }
    }

    procesarLineasDe(cliente, bufferCliente);
    procesarLineasSerial();
    detectarPisadas();
    motor->actualizar();   // avance temporal no bloqueante (timeouts, exhibicion)
}

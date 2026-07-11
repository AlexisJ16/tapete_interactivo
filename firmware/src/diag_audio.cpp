// Diagnostico del audio (DFPlayer Mini) — entorno `esp32dev_audio`.
//
//   cd firmware && pio run -e esp32dev_audio -t upload
//   pio device monitor -b 115200
//
// NO corre el juego ni WiFi. Prueba el DFPlayer capa por capa e imprime DONDE falla:
//   1) ¿responde por UART?            -> comunicacion (cableado / 5 V / cruce TX-RX)
//   2) ¿ve archivos en la microSD?    -> lectura de la SD (formato / insercion)
//   3) ¿reproduce sin error?          -> archivos (nombre/ubicacion) o parlante
//
// Test discriminante: copia ademas un MP3 NORMAL (una cancion, >5 s) como
// /mp3/0005.mp3. Si 0005 suena y 0001-0004 no, el problema son NUESTROS archivos
// (demasiado cortos), no el hardware.

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

#include "Config.h"

static DFRobotDFPlayerMini player;
static bool ok = false;

// Vacia la cola de mensajes del DFPlayer traduciendo los codigos a texto.
static void detalle() {
    while (player.available()) {
        uint8_t t = player.readType();
        uint16_t v = player.read();
        Serial.print("   [DFPlayer] ");
        switch (t) {
            case TimeOut:              Serial.println("TimeOut (no responde)"); break;
            case WrongStack:           Serial.println("WrongStack"); break;
            case DFPlayerCardInserted: Serial.println("microSD insertada"); break;
            case DFPlayerCardRemoved:  Serial.println("microSD retirada"); break;
            case DFPlayerCardOnline:   Serial.println("microSD ONLINE"); break;
            case DFPlayerPlayFinished: Serial.print("fin de pista "); Serial.println(v); break;
            case DFPlayerError:
                Serial.print("ERROR: ");
                switch (v) {
                    case Busy:            Serial.println("Busy (modulo ocupado / sin SD)"); break;
                    case Sleeping:        Serial.println("Sleeping"); break;
                    case SerialWrongStack:Serial.println("SerialWrongStack"); break;
                    case CheckSumNotMatch:Serial.println("CheckSumNotMatch (ruido en la UART)"); break;
                    case FileIndexOut:    Serial.println("FileIndexOut (indice fuera de rango)"); break;
                    case FileMismatch:    Serial.println("FileMismatch (NO encuentra el archivo)"); break;
                    case Advertise:       Serial.println("Advertise"); break;
                    default:              Serial.println(v); break;
                }
                break;
            default:
                Serial.print("tipo "); Serial.print(t);
                Serial.print(" valor "); Serial.println(v);
                break;
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println();
    Serial.println("========= DIAGNOSTICO DE AUDIO — DFPlayer Mini =========");
    Serial.print("UART2: RX=GPIO");
    Serial.print(cfg::PIN_DFPLAYER_RX);
    Serial.print(" (<- TX del DFPlayer)    TX=GPIO");
    Serial.print(cfg::PIN_DFPLAYER_TX);
    Serial.println(" (-> RX del DFPlayer, via 1k)");

    Serial2.begin(9600, SERIAL_8N1, cfg::PIN_DFPLAYER_RX, cfg::PIN_DFPLAYER_TX);

    // El DFPlayer tarda 1-3 s tras encender en montar la SD y contestar. El firmware
    // del juego solo esperaba 50 ms: si esa es la causa, aqui SI respondera.
    Serial.println("Esperando 3 s a que el DFPlayer arranque...");
    delay(3000);

    player.setTimeOut(2000);   // por defecto la libreria solo espera 500 ms

    for (int intento = 1; intento <= 5 && !ok; ++intento) {
        Serial.print("begin() intento ");
        Serial.print(intento);
        Serial.print(" ... ");
        ok = player.begin(Serial2, /*isACK=*/true, /*doReset=*/true);
        Serial.println(ok ? "OK" : "FALLO");
        if (!ok) { detalle(); delay(1500); }
    }

    if (!ok) {
        Serial.println();
        Serial.println(">>> CAPA 1 (UART): el DFPlayer NO responde. Revisa en este orden:");
        Serial.println("    1) VCC del DFPlayer a 5 V (NO 3V3) y GND COMUN con el ESP32.");
        Serial.println("    2) El cruce: ESP32 GPIO17 (TX) -> RX del DFPlayer (via 1 kOhm)");
        Serial.println("       y ESP32 GPIO16 (RX) <- TX del DFPlayer.");
        Serial.println("       Si van directos (TX->TX, RX->RX), el modulo nunca contesta.");
        Serial.println("    3) microSD insertada a fondo.");
        return;
    }

    Serial.println();
    Serial.println("--- CAPA 1 OK: el DFPlayer responde por UART. Interrogando la microSD ---");
    player.volume(30);              // volumen maximo (0..30)
    delay(200);
    Serial.print("volumen leido : "); Serial.println(player.readVolume());
    Serial.print("estado        : "); Serial.println(player.readState());
    int n = player.readFileCounts();
    Serial.print("archivos en SD: "); Serial.println(n);
    if (n <= 0) {
        Serial.println(">>> CAPA 2 (microSD): el DFPlayer NO ve archivos.");
        Serial.println("    Formatea la microSD en FAT32 y copia /mp3/0001.mp3 .. 0004.mp3");
    }
    detalle();

    Serial.println();
    Serial.println("--- CAPA 3: reproduciendo /mp3/000N.mp3 a volumen 30 ---");
    Serial.println("    NOTA: copia un MP3 NORMAL (cancion, >5 s) como /mp3/0005.mp3.");
    Serial.println("    Si 0005 SUENA y 0001-0004 no -> el problema son nuestros archivos");
    Serial.println("    (duran 0,16-0,81 s; el DFPlayer no reproduce bien pistas tan cortas).");
    Serial.println();
}

void loop() {
    if (!ok) { delay(3000); return; }
    for (int i = 1; i <= 5; ++i) {
        Serial.print(">> playMp3Folder(");
        Serial.print(i);
        Serial.println(")  --- ESCUCHA AHORA ---");
        player.playMp3Folder(i);
        uint32_t t0 = millis();
        while (millis() - t0 < 4000) {   // 4 s por pista: oirla y recoger sus eventos
            detalle();
            delay(50);
        }
        Serial.print("   estado tras la pista: ");
        Serial.println(player.readState());
    }
    Serial.println("--- ciclo completo; repitiendo ---");
    Serial.println();
}

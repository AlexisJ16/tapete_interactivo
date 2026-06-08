// Test de hardware: cada potenciometro (FSR simulado) enciende su grupo de LEDs.
// Girar el potenciometro > 50% hacia la derecha = boton pisado = LEDs encienden.

const int PIN_FSR[] = {36, 39, 34, 35, 32, 33};
const int PIN_LED[] = { 4,  5, 18, 19, 21, 23};
const int UMBRAL    = 2000;   // ADC 0..4095, coincide con Config.h

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  for (int i = 0; i < 6; i++) {
    pinMode(PIN_LED[i], OUTPUT);
    digitalWrite(PIN_LED[i], LOW);
  }
  Serial.println("Tapete TEST — gira un potenciometro para simular pisada");
}

void loop() {
  for (int i = 0; i < 6; i++) {
    int adc = analogRead(PIN_FSR[i]);
    bool pisado = adc >= UMBRAL;
    digitalWrite(PIN_LED[i], pisado ? HIGH : LOW);
    if (pisado) {
      Serial.print("Boton ");
      Serial.print(i + 1);
      Serial.print(" | ADC=");
      Serial.println(adc);
    }
  }
  delay(50);
}

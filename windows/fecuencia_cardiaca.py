#define USE_ARDUINO_INTERRUPTS true    
#include <PulseSensorPlayground.h>

const int PIN_PULSO = A0;     // Aquí va el cable azul del sensor de pulso
int limiteBPM = 550;

PulseSensorPlayground pulseSensor;

void setup() {
  Serial.begin(9600);
  pulseSensor.analogInput(PIN_PULSO);
  pulseSensor.setThreshold(limiteBPM);

  if (pulseSensor.begin()) {
    Serial.println("PulseSensor listo...");
  }
}

void loop() {
  int BPM = pulseSensor.getBeatsPerMinute();
  
  if (pulseSensor.sawStartOfBeat()) {
    Serial.print("BPM:");
    Serial.println(BPM);
  }
}

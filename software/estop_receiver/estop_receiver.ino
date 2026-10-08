// Wireless e-stop receiver: fail-safe watchdog between an RC receiver and the e-stop loop relay.
//
// Hardware: Arduino Nano (ATmega328P) or Pro Mini 5 V.
//   D2  <- PWM signal from a dedicated ELRS PWM receiver channel (the "RUN" switch on the transmitter)
//   D7  -> relay module input (active HIGH). The relay's NO contact is in series with the NC e-stop loop.
//   D13 -> onboard LED: solid = RUN, fast blink = stopped (no valid signal), slow blink = stopped (switch off)
//
// The relay is energised ONLY while valid pulses keep arriving AND the RUN switch is high.
// Anything else (transmitter off, out of range, receiver unplugged, broken wire, switch off,
// firmware hang) drops the relay and opens the e-stop loop.
//
// Receiver failsafe must be set to "No Pulses" (ELRS Lua -> Failsafe). This code also rejects
// stale signals on its own, but "No Pulses" makes the failure obvious.

#include <avr/wdt.h>

const uint8_t PIN_PWM = 2;     // INT0
const uint8_t PIN_RELAY = 7;
const uint8_t PIN_LED = 13;

const uint16_t PULSE_MIN_US = 900;    // outside this window = invalid
const uint16_t PULSE_MAX_US = 2100;
const uint16_t RUN_THRESHOLD_US = 1700;  // switch "up" ~2000 us
const uint32_t SIGNAL_TIMEOUT_MS = 100;  // RC frames arrive every ~20 ms; 5 missed frames = stop
const uint8_t RUN_CONFIRM_PULSES = 10;   // require ~0.2 s of steady RUN before closing the relay

volatile uint32_t riseMicros = 0;
volatile uint16_t lastPulseUs = 0;
volatile uint32_t lastPulseMillis = 0;
volatile bool newPulse = false;

void onEdge() {
  uint32_t now = micros();
  if (digitalRead(PIN_PWM)) {
    riseMicros = now;
  } else {
    lastPulseUs = (uint16_t)(now - riseMicros);
    lastPulseMillis = millis();
    newPulse = true;
  }
}

void setup() {
  MCUSR = 0;
  wdt_disable();
  // Relay OFF before anything else: the pin defaults to input (relay off) through reset.
  digitalWrite(PIN_RELAY, LOW);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_PWM, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_PWM), onEdge, CHANGE);
  wdt_enable(WDTO_250MS);  // a hung loop resets the MCU, which drops the relay
}

void loop() {
  static uint8_t runCount = 0;
  static bool run = false;

  noInterrupts();
  uint16_t pulse = lastPulseUs;
  uint32_t pulseAge = millis() - lastPulseMillis;
  bool fresh = newPulse;
  newPulse = false;
  interrupts();

  bool valid = pulseAge < SIGNAL_TIMEOUT_MS && pulse >= PULSE_MIN_US && pulse <= PULSE_MAX_US;
  bool runRequested = valid && pulse >= RUN_THRESHOLD_US;

  if (!runRequested) {
    runCount = 0;
    run = false;
  } else if (fresh && runCount < RUN_CONFIRM_PULSES) {
    runCount++;
  }
  if (runCount >= RUN_CONFIRM_PULSES) {
    run = true;
  }

  digitalWrite(PIN_RELAY, run ? HIGH : LOW);

  // LED status.
  uint32_t t = millis();
  if (run) {
    digitalWrite(PIN_LED, HIGH);
  } else if (!valid) {
    digitalWrite(PIN_LED, (t / 100) % 2);
  } else {
    digitalWrite(PIN_LED, (t / 500) % 2);
  }

  wdt_reset();
}

# Wireless e-stop receiver

A $5 microcontroller that turns a dedicated RC receiver channel into a **fail-safe** wireless e-stop. The relay closes only while a valid "RUN" signal keeps arriving. Transmitter off, out of range, a broken wire, the switch flipped down, or the firmware hanging all open the e-stop loop.

Why not a cheap RC relay switch? Most of them **hold their last state on signal loss**, which is the opposite of fail-safe.

## Hardware

| Part | Notes |
|---|---|
| Arduino Nano or Pro Mini (5 V, ATmega328P) | Flash with the current (Optiboot) bootloader. The old Nano bootloader can reset-loop with the watchdog, which still fails safe (relay off) but won't run. |
| ELRS **PWM** receiver (e.g. RadioMaster ER-series) | Dedicated to the e-stop, bound to the same transmitter. **Failsafe = "No Pulses".** |
| 1-channel relay module, 5 V coil, active-HIGH input | Contacts in series with the NC e-stop loop ([electrical design](../../hardware/electrical/README.md)) |

Wiring: receiver channel signal → **D2**; **D7** → relay module IN; 5 V and GND from the robot's 5 V rail to the Nano, receiver, and relay module.

Map a **2-position switch** on the transmitter to that channel: up (~2000 µs) = RUN, down = STOP.

## Build

```bash
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 software/estop_receiver
arduino-cli upload  --fqbn arduino:avr:nano:cpu=atmega328 -p /dev/cu.usbserial-XXXX software/estop_receiver
```

## Acceptance test (do it before every mowing season, and monthly)

Each test must drop the relay (you'll hear it click and see the LED blink):

1. Flip the RUN switch down → relay drops within 0.1 s.
2. Turn the transmitter off → relay drops (time how long it takes; should be ≤ 1 s).
3. Walk out of range (or shield the transmitter in a metal box) → relay drops.
4. Unplug the receiver signal wire → relay drops.
5. Power-cycle the Nano with the switch in RUN → relay stays off for ~0.2 s, then closes.

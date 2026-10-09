# Step 3: Autopilot, radios and e-stop receiver on the bench

*Links and prices checked 2026-10-08. Spend: about $350–400. Time: an evening or two.*

**Goal:** the flight controller running ArduPilot Rover with our parameter file and the blade-interlock script, talking to the rover GPS, both radios, the RC transmitter and the wireless e-stop receiver, all on the bench. By the end you can arm it, see RTK Fixed, trip the e-stop and watch the script disarm. Nothing moves yet.

## Buy

| ✓ | Item | Spec to check | Where | Price seen |
|---|---|---|---|---|
| ☐ | **Flight controller** | ArduPilot-supported H7 board with ≥ 8 PWM outputs, 2 GPS ports, 2 telemetry ports, SD card. With a **12S-rated power module** (our bus is 36 V nominal, 42 V max). | [Holybro Pixhawk 6C Mini, Model-A revision, with PM02 V3](https://holybro.com/products/pixhawk-6c-mini) ($149.98 with the power module) | $150 |
| ☐ | **RC transmitter** | ExpressLRS 2.4 GHz, ≥ 2 two-position switches (arm, e-stop RUN) and one 3-position (mode), EdgeTX | [RadioMaster Pocket, ELRS, FCC](https://www.radiomasterrc.com/products/pocket-radio-controller-m2) ($71.50) plus 2 × 18650 cells. A larger radio (TX12, Boxer) is fine too. | $72 + cells |
| ☐ | **Receiver for driving** (to the flight controller) | ELRS 2.4 GHz, CRSF serial output | [RadioMaster RP3 V2 ExpressLRS nano receiver, FCC](https://www.radiomasterrc.com/products/rp3-expresslrs-2-4ghz-nano-receiver) ($19.99) | $20 |
| ☐ | **Receiver for the wireless e-stop** (separate from the above) | ELRS 2.4 GHz with **PWM outputs** and configurable failsafe (set to **No Pulses**) | [RadioMaster ER6 6-channel ELRS PWM receiver](https://motionrc.com/products/radiomaster-er6-6-channel-elrs-pwm-receiver-hp0157-rx-er6) ($27.99) | $28 |
| ☐ | **E-stop receiver microcontroller** | Arduino Nano (ATmega328P, 5 V) + a 1-channel 5 V relay module (active-HIGH input) | Any Nano clone with the Optiboot bootloader; firmware in [`software/estop_receiver`](../../software/estop_receiver/README.md) | $10–15 |
| ☐ | **Telemetry radio pair** (robot ↔ laptop) | 915 MHz SiK, second pair, **different NETID** from the RTK pair | [Holybro SiK Telemetry Radio V3, 915 MHz](https://holybro.com/products/sik-telemetry-radio-v3) ($58.99) | $59 |
| ☐ | Bench odds and ends | 5 V 3 A USB supply for the bench (the PM02 needs the battery bus; on the bench power the FC from USB), JST-GH cable kit (usually included with the Pixhawk), microSD card ≥ 8 GB, a few 2.54 mm servo leads | — | $20 |

The rover ZED-F9P and its antenna come from step 2.

## Do

1. **Flash ArduPilot Rover 4.6.x** onto the Pixhawk with Mission Planner (Setup → Install Firmware → Rover). Create the SD card.
2. **Load our configuration:** Config → Full Parameter List → Load from file → [`software/ardupilot/params/orbitist-v1.param`](../../software/ardupilot/params/orbitist-v1.param) → Write Params → reboot. Copy [`blade_interlock.lua`](../../software/ardupilot/scripts/blade_interlock.lua) to the SD card under `APM/scripts/`, reboot, and confirm "Blade interlock loaded" in the Messages tab. The `BLD_*` parameters now exist.
3. **GPS:** rover F9P to the GPS1 port (UART1 on the F9P), antenna on a metal plate outdoors or on a windowsill. With the base running, the HUD should show *rtk Fixed* (GPS status 6). ROVER SiK radio into the F9P's UART2 header as in step 2.
4. **RC:** flash the Pocket and both receivers to the same ExpressLRS version and bind phrase (ELRS configurator, Wi-Fi). RP3 to the Pixhawk's RC IN (CRSF). In Mission Planner's Radio Calibration, check all channels move, map channel 7 to a two-position switch (`RC7_OPTION 153` = arm/disarm) and channel 8 to a three-position switch (mode: Manual / Hold / Auto).
5. **Wireless e-stop:** ER6 channel 1 ← a second two-position switch on the Pocket ("RUN"). In the ELRS Lua on the transmitter, set the ER6's **failsafe to No Pulses**. Flash the Nano with `software/estop_receiver` (`arduino-cli compile … && arduino-cli upload …`). Wire ER6 ch1 signal → Nano D2, Nano D7 → relay IN, 5 V and GND to all three. Run the acceptance test in that README: the relay must drop for a switch-down, transmitter off, out of range, unplugged signal, and must stay off for ~0.2 s after a power cycle.
6. **E-stop input to the autopilot:** on the bench, wire the relay's NO contact in series with 3.3 V to a spare AUX pin configured as GPIO, and set `BLD_ESTOP_SRC 1`, `BLD_ESTOP_PIN <that pin>`. Arm with the switch (Hold mode); flip RUN down; the script must report "ESTOP loop open: disarmed".
7. **Telemetry:** second SiK pair between TELEM1 and the laptop; Mission Planner connects over it at 57600.
8. **Simulation handshake:** run `software/sim/run_sitl.py` once more on the real lawn file from step 2 so the missions you'll load later have already passed the acceptance tests.

## Record

- The AUX pin used for ESTOP_OK and the relay output pin for the blade (`RELAY1_PIN`) in the parameter file; commit it.
- ELRS version and bind phrase (in a private note, not the repo).

## Done when

- [ ] HUD shows rtk Fixed, both radios link, all RC channels calibrated.
- [ ] Arm/disarm works only from the switch.
- [ ] The wireless e-stop passes all five acceptance tests, and tripping it disarms the autopilot via the script.
- [ ] `orbitist-v1.param` in the repo matches what is on the flight controller.

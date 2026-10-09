# Ordering plan: Platform v1

> The step-by-step version of this, with checked purchase links per step, is the [build tutorial](../../docs/build/README.md). This page stays as the one-screen summary.

Purchases are grouped into waves, so money goes out only when each part is needed and early parts can be tested before the next wave. Prices are rough estimates as of Oct 2026. Full list with costs: [`platform-v1-bom.csv`](platform-v1-bom.csv).

## Wave 0: de-risking tests (now, ~$350, all parts needed anyway)

See the [confidence plan](../../docs/design/confidence-plan.md). These measurements decide the battery, the drive motors, and the final plate DXFs **before** the main order.

| ✓ | Item | Why first | ~$ |
|---|---|---|---|
| ☐ | **Used Ryobi mower** (same voltage as the farm's batteries) | T1: measure blade power on the real lawn, deck geometry, and blade switching. Decides the battery. | 50–150 |
| ☐ | **One** 10" hub motor + **one** VESC | T3: bench test of torque constant, low-speed smoothness, 30 min thermal at mowing torque, timeout brake. Buy the second only if it passes. | 210 |
| ☐ | Current-limited bench supply (≥ 50 V, 5 A) | Safe first power-up for T1/T3, and later for commissioning | 60–100 |
| ☐ | One 10" plate caster | T4: bolt pattern and height for the caster-plate DXF | 35 |
| ☐ | DC clamp meter (optional) | T1 blade current; useful for the rest of the build | 40 |

## Wave 1: GPS + autopilot (order now, ~$700–900)

**Why first:** the base station needs a day of logging to fix its position. We can also **map the lawn boundaries this fall, before snow**, by putting the rover GPS on a wheelbarrow or garden cart and walking the edges. That map becomes our geofences and mowing zones, and it means navigation is proven before the robot exists.

| ✓ | Item | What to look for | ~$ |
|---|---|---|---|
| ☐ | 2× u-blox **ZED-F9P** boards (base + rover) | ArduSimple simpleRTK2B or SparkFun GPS-RTK2 class. A board with an XBee-style radio socket (ArduSimple) makes the radio link plug-in. | 2× 200–280 |
| ☐ | 2× multiband (L1/L2) GNSS antennas | u-blox ANN-MB class for the rover; a survey-style antenna (or another ANN-MB on a ground plate) for the base | 2× 60–150 |
| ☐ | Radio pair for corrections (base → rover) | 915 MHz SiK telemetry radio pair or an XBee-socket radio pair matching the F9P boards | 60 |
| ☐ | Flight controller | **Holybro Pixhawk 6C (mini)** for easy connectors, or Matek H743 class. Plus a power module rated for 12S. | 120–200 |
| ☐ | RC transmitter + receivers | ExpressLRS (ELRS) transmitter with switches + ELRS receiver for driving + **ELRS PWM receiver** for the wireless e-stop | 100–150 |
| ☐ | Telemetry radio pair (robot ↔ laptop) | Second SiK 915 MHz pair, or MAVLink over ELRS | 60 |
| ☐ | Base station mount | Rigid pole or roof bracket, weatherproof box, 5 V power supply, low-loss SMA cable | 60 |
| ☐ | Raspberry Pi for the base | Pi 4 / Pi 5 / Zero 2 W + SD card + PSU. Logs the 24 h survey and later serves NTRIP. See the [base station guide](../../docs/guides/rtk-base-station.md). | 60–90 |

**Wave 1 tasks:** set up the base station and log 24 h of raw data → submit to NOAA OPUS → enter the fixed base position. Walk the lawn edges with the rover GPS → save the polygons to `software/ardupilot/missions/`. Meanwhile, run ArduPilot SITL on a laptop with those polygons.

## Wave 2: drive and power (after T1–T4, ~$1,100)

| ✓ | Item | What to look for | ~$ |
|---|---|---|---|
| ☐ | Second 10" hub motor (first bought in Wave 0) | 36 V, 350–500 W, pneumatic 10×2.5"–10×3" tire, **Hall sensors (small 5-wire connector)**, **axle with flats on both sides**. Same listing as the Wave 0 motor, so they match. | 120 |
| ☐ | Second FOC motor controller | VESC-class (Flipsky FSESC 4.20 / 6.x, Makerbase 75100), **rated ≥ 50 V**, Hall sensor input, PWM/PPM input. Budget alternative: hoverboard mainboard + ST-Link. | 90 |
| ☐ | 2× 10" pneumatic plate-mount swivel casters | 4"×4.5" top plate, ~12" overall height, ≥ 150 kg rating, ball-bearing swivel. **Measure the bolt pattern and height on arrival** (they set `caster-plate.dxf`). | 2× 35 |
| ☐ | Battery | **Size set by T1** (blade power): 36 V 20 Ah if the deck stays on Ryobi packs; 30–40 Ah (or two 20 Ah) if the deck runs from the robot. BMS ≥ 30 A continuous, plus a matching charger. 10S Li-ion or 12S LiFePO4. | 300–450 |
| ☐ | Electrical | Per the [electrical parts list](../electrical/README.md#7-parts-list-electrical): 40 A MRBF main fuse, battery disconnect, 12 V-coil DC contactor, precharge relay + 47 Ω 10 W resistor, on-delay and off-delay timer modules, DPDT signal relay, 58 V fuses + block, power module, DC-DCs (input ≥ 60 V), XT90s, 10–12 AWG silicone wire | 220 |
| ☐ | Safety | NC mushroom e-stop, Arduino Nano + 5 V relay module (wireless e-stop, [firmware](../../software/estop_receiver/README.md)), 2 roller-lever NC microswitches, optocoupler module | 60 |
| ☐ | Bumper | Aluminium bar or 30x30 extrusion, 2 sliding arms + UHMW/printed guides, return springs, 50 mm closed-cell foam | 50 |
| ☐ | Frame | 30-series slot-8 aluminum extrusion per the [cut list](../cad/exports/cut-list.md): 30×30 3 × 1220 mm; 30×60 2 × 1150 mm + 2 × 1220 mm (buy ~4 m of 30×30 and ~5.2 m of 30×60). Corner brackets, T-nuts, stainless M6/M8 fasteners. | 230 |
| ☐ | Plates | From `hardware/cad/exports/*.dxf`: 4× fork side plates (6 mm steel), 4× **torque arms** (5 mm steel, required), 8× frame gussets (5 mm Al), plus fork top plates and saddle tabs. Send DXFs out for cutting once the motor axle is measured. | 80 |
| ☐ | Enclosure | IP65 polycarbonate box ~30×20×15 cm, cable glands | 70 |

## Wave 3: mower deck (whenever a good deal appears; off-season is cheapest)

| ✓ | Item | What to look for | ~$ |
|---|---|---|---|
| ☐ | Used Ryobi mower #1 | **Same voltage as the farm's existing Ryobi batteries** (check the battery label). Prefer a brushless 20–21" model. A bare tool (no battery) is fine. | 50–150 |
| ☐ | Used Ryobi mower #2 | Same model as #1, for the twin-deck upgrade (v1.5) | 50–150 |
| ☐ | Deck hanging hardware | Links/chain, anti-scalp rollers, a relay to switch the mower's start circuit | 50 |

## Wave 4: phase 2 (spring/summer 2027)

Charging dock, Raspberry Pi 5, OAK-D Lite, global-shutter camera. See the BOM. We'll order these once supervised mowing works.

## Tools to have on hand

- Soldering iron, crimpers (XT90/Anderson, ferrules), multimeter, **current-limited bench supply** (for first power-up of controllers)
- Chop/miter saw with a non-ferrous blade for extrusion, drill press, taps (M6/M8), files
- 3D printer (PETG/ASA filament)
- **ST-Link V2 programmer**, only if using the hoverboard-board option
- Laptop with Mission Planner (or QGroundControl), VESC Tool, and u-center (u-blox configuration)

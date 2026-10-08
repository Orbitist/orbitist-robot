# Ordering plan: Platform v1

Purchases are grouped into waves, so money goes out only when each part is needed and early parts can be tested before the next wave. Prices are rough estimates as of Oct 2026. Full list with costs: [`platform-v1-bom.csv`](platform-v1-bom.csv).

## Wave 1: GPS + autopilot (order now, ~$700–900)

**Why first:** the base station needs a day of logging to fix its position. We can also **map the lawn boundaries this fall, before snow**, by putting the rover GPS on a wheelbarrow or garden cart and walking the edges. That map becomes our geofences and mowing zones, and it means navigation is proven before the robot exists.

| ✓ | Item | What to look for | ~$ |
|---|---|---|---|
| ☐ | 2× u-blox **ZED-F9P** boards (base + rover) | ArduSimple simpleRTK2B or SparkFun GPS-RTK2 class. A board with an XBee-style radio socket (ArduSimple) makes the radio link plug-in. | 2× 200–280 |
| ☐ | 2× multiband (L1/L2) GNSS antennas | u-blox ANN-MB class for the rover; a survey-style antenna (or another ANN-MB on a ground plate) for the base | 2× 60–150 |
| ☐ | Radio pair for corrections (base → rover) | 915 MHz SiK telemetry radio pair or an XBee-socket radio pair matching the F9P boards | 60 |
| ☐ | Flight controller | **Holybro Pixhawk 6C (mini)** for easy connectors, or Matek H743 class. Plus a power module rated for 12S. | 120–200 |
| ☐ | RC transmitter + receiver | ExpressLRS (ELRS) transmitter with switches + 2 ELRS receivers (one for driving, one for the wireless e-stop) | 100–150 |
| ☐ | Telemetry radio pair (robot ↔ laptop) | Second SiK 915 MHz pair, or MAVLink over ELRS | 60 |
| ☐ | Base station mount | Pole or roof bracket, weatherproof box, 5 V power or a USB supply | 40 |

**Wave 1 tasks:** set up the base station and log 24 h of raw data → submit to NOAA OPUS → enter the fixed base position. Walk the lawn edges with the rover GPS → save the polygons to `software/ardupilot/missions/`. Meanwhile, run ArduPilot SITL on a laptop with those polygons.

## Wave 2: drive and power (Nov, ~$1,100)

| ✓ | Item | What to look for | ~$ |
|---|---|---|---|
| ☐ | 2× 10" hub motors | 36 V, 350–500 W, pneumatic 10×2.5"–10×3" tire, **Hall sensors (small 5-wire connector)**, **axle with flats on both sides**. Buy both from the same listing so they match. | 2× 120 |
| ☐ | 2× FOC motor controllers | VESC-class (Flipsky FSESC 4.20 / 6.x, Makerbase 75100), **rated ≥ 50 V**, Hall sensor input, PWM/PPM input. Budget alternative: hoverboard mainboard + ST-Link. | 2× 90 |
| ☐ | 2× zero-turn mower caster assemblies | 11×4 or 13×5 caster wheel + fork + yoke/spindle bearing (mower replacement parts) | 2× 55 |
| ☐ | Battery | 36 V e-bike pack, **20 Ah**, BMS ≥ 30 A continuous, plus a matching charger. 10S Li-ion or 12S LiFePO4. | 300 |
| ☐ | Electrical | Main fuse (40 A), key switch, precharge resistor, 36 V contactor (coil voltage to match the e-stop loop), DC-DCs 36→12 V 10 A and 36→5 V 5 A (input ≥ 50 V), XT90 connectors, 10–12 AWG silicone wire, fuse block | 150 |
| ☐ | Safety | NC mushroom e-stop, relay module for the wireless e-stop, bumper microswitches | 100 |
| ☐ | Frame | 30-series slot-8 aluminum extrusion per the [cut list](../cad/exports/cut-list.md): 30×30 4 × 1220 mm; 30×60 2 × 1165 mm + 1 × 1220 mm. Corner brackets, T-nuts, stainless M6/M8 fasteners. | 230 |
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

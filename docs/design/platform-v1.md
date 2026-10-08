# Orbitist Farm Robot — Platform v1 Design (Brainstorm)

*Status: draft for discussion · Started 2026-10-08 · Builds on the [Sept 2026 vineyard concept report](../concept/2026-09-vineyard-robot-design-report.pdf)*

## 1. What we're building this winter

A single, open-source, farm-buildable robot base that **mows our lawns autonomously by spring**. It should also be able to grow into the long-term jobs: towing small loads such as mulch, carrying sensors, and eventually carrying a light arm for weeding and pruning.

Design rules:

1. **Buy what's proven, build what's simple.** Use parts with large hobby or ag communities behind them, such as e-bike and scooter parts, mower replacement parts, ArduPilot autopilots, and u-blox RTK GPS. Only fabricate brackets, plates, and frame cuts.
2. **Salvage-friendly.** Every major subsystem has a "new part" path and a "salvaged part" path.
3. **One robot first.** Get one robot doing useful work before building a pair or a fleet.
4. **Safety is a subsystem, not a feature.** This robot carries a spinning blade, so the kill chain gets designed before the autonomy.

## 1a. Site parameters (our farm)

| Parameter | Value | Design impact |
|---|---|---|
| Lawn area | **~3 acres (~12,000 m²)**, growing as the farm expands | One 21" deck needs ~8–9 h per full pass, so the robot must **mow in daily zones from a charging dock** (§5) |
| Existing equipment | Ryobi electric push mower + several Ryobi batteries, in daily use | Mower module uses a **second, used Ryobi deck** of the same voltage line so batteries and charger are shared (§6.2) |
| Fabrication | Any tools needed | Extrusion for fast iteration; welded steel and outsourced laser/water-jet plates where they're stronger or cheaper |
| Connectivity | Cell coverage over the whole property; Wi-Fi can be extended | Telemetry and remote monitoring over Wi-Fi/LTE later; RTK corrections can travel over radio or network |
| RTK correction service | **None known nearby** | **Our own RTK base station** on a farm building is required in phase 1. It serves every future robot on the farm. |
| Terrain | **Generally flat** | Rear-wheel drive with front casters has plenty of grip; 4WD is only needed for hauling in mud later |
| Sky view | **Open sky; base station can go anywhere** | Ideal for RTK: expect a solid fix nearly everywhere. Put the base near the middle of the lawns. |
| Layout | **Mostly open lawns joined by ~8 ft (2.4 m) paths**; small paths touched up by hand | Robot can be up to ~1.4 m wide, so the frame is **built wide enough for twin decks from the start** (§4) |
| CAD | Open to anything | **Onshape** (§6.6) |
| License | Delegated to Claude | CERN-OHL-W-2.0 (hardware) · Apache-2.0 (software) · CC BY-SA 4.0 (docs). See [LICENSE.md](../../LICENSE.md). |

## 2. What changes from the vineyard concept, and why

The concept report is a good foundation. Its research on hub motors, the 36 V bus, e-bike packs, AprilTags, and the risk table carries over. Mowing as the first task and towing and arm work as later tasks change what matters most.

| Topic | Concept report | v1 proposal | Why |
|---|---|---|---|
| Number of robots | Identical pair with peer-to-peer docking | **One robot.** Peer docking becomes a later research track. | Mowing doesn't need two robots, and the dock latch was the highest-risk item (Risk #1 in the report). |
| Navigation | AprilTag + odometry; RTK GPS in phase 3 | **RTK GPS from day one** | Coverage mowing needs ~2–5 cm repeatable position across open lawn. Every DIY and commercial wire-free mower relies on this. |
| Low-level control | Pi 5 + ROS 2 + `ros2_control` | **ArduPilot Rover on a $60–150 flight controller**, with the Pi 5 + ROS 2 added as a companion in phase 2 | ArduPilot already provides skid-steer control, RTK/EKF fusion, waypoint and grid missions, geofences, failsafes, and logging, and people already run it on mowers. This replaces months of ROS 2 integration with days of parameter tuning. |
| Chassis layout | 2WD with front and rear casters, rear docking pin | **Zero-turn layout:** 2 driven rear wheels, 2 front casters, mid-mounted deck | This is the layout lawn mowers settled on. It pivots in place without scrubbing turf, unlike 4WD skid-steer. |
| Motor drivers | Hoverboard mainboard with EFeru FOC | **VESC-class FOC controller per wheel** by default; hoverboard board as the budget option | VESCs take RC-PWM or CAN straight from ArduPilot, handle low-speed hub-motor torque well with Hall sensors, and are documented on the ArduPilot forums. |
| Payload approach | Basket on the top deck | **Three mounting points:** belly (mower deck), rear hitch (towed cart), top deck (sensors/arm) | Towing a garden cart is easier on the robot than carrying a load: the cart's wheels hold the weight, and tongue weight adds traction. |
| Charging | Peer-to-peer bus sharing | **Swapped battery first, then a fixed charging dock** in phase 2 | Lawns sit near buildings. A fixed dock is how commercial mowers work and is much simpler. ArduPilot already has an AprilTag-guided [Dock mode](https://ardupilot.org/rover/docs/dock-mode.html). |
| Battery chemistry | "36 V (10S) LiFePO4" | **36 V means 10S Li-ion (NMC), or 12S LiFePO4 (38.4 V nominal)** | Correction: 10S LiFePO4 is only 32 V. Both 10S NMC and 12S LFP run 36 V-class motors and controllers. |

Ideas from the concept report that carry forward unchanged: the 36 V bus, 10" pneumatic hub motors, aluminum extrusion with T-slot mounting everywhere, the IP65 electronics box, the e-stop and contactor, the BNO085-class IMU, global-shutter camera + AprilTags (now for the charging dock), and OAK-D Lite for obstacle sensing in phase 2.

## 3. Chassis options considered

| Option | Description | Strengths | Weaknesses | Verdict |
|---|---|---|---|---|
| **A. Zero-turn rover** | 2 rear hub motors, 2 front mower-caster wheels, extrusion frame | Turf-friendly, simple, cheap, mirrors proven mower geometry | Only 2 wheels drive, so traction on wet slopes is limited (see §5) | **v1 recommended** |
| B. Salvaged power-wheelchair base | Used wheelchair ($100–300 on Marketplace) supplies frame, 24 V gearmotors **with electromagnetic brakes**, casters, and wheels | Very high torque, holds position on slopes, very cheap if found | Availability varies; needs a new motor controller (Sabertooth/RoboClaw, $90–130); heavy; 24 V | **Strong salvage alternative.** The frame will accept wheelchair motors as a drop-in "drive module." |
| C. 4WD skid-steer | 4 hub motors, no casters (Amiga-style) | Best traction and mud performance, good for hauling | Scrubs and tears turf when turning; +$250 | **v2 variant for hauling and fieldwork.** Same frame, casters swapped for driven wheels. |
| D. Docked pair (concept report) | Two robots that latch into one 4WD unit | Redundancy and shared range | Highest complexity; not needed for mowing | Research track after v1 works |
| E. Convert an existing riding or zero-turn mower | ArduPilot + actuators on a gas or electric ZTR | Big cutting width, proven by the ArduPilot community | Heavy, dangerous, less reusable as a general platform | Not pursued, but forum builds are a useful reference |

**Modularity choice:** design the frame around **swappable drive modules**. Each drive wheel bolts on through a pair of dropout plates, so Options A, B, and C share one frame.

## 4. v1 layout (top view)

```
              FRONT
     ┌─────────────────────────┐
     │ (caster)       (caster) │   ← 11" zero-turn mower caster wheels on forks
     │    ╔═══════════════╗    │   ← bump bar / bumper switches across the front
     │    ║               ║    │
     │    ║  MOWER DECK   ║    │   ← belly mount, hangs from 4 links, anti-scalp wheels
     │    ║  (mid-mount)  ║    │
     │    ╚═══════════════╝    │
  ███│  [ IP65 electronics ]   │███  ← 10" hub motors in dropout plates (drive axle)
  ███│  [ battery over axle ]  │███
     │        [hitch]          │   ← rear 2" receiver or pin hitch for the cart
     └─────────────────────────┘
              REAR
   RTK antenna(s) on a mast above the deck · e-stop mushroom at rear top
```

Target envelope, to be refined in CAD:

| Parameter | Target |
|---|---|
| Overall width | **~1.3–1.4 m**, frame sized for twin decks from day one (fits 2.4 m farm paths and vineyard aisles; too wide for a man-door, so store in a garage/barn bay) |
| Length | ~100–110 cm |
| Frame | 30×30 mm aluminum T-slot (axle and hitch rails 30×60 or steel plate) |
| Wheelbase (caster pivots to drive axle) | ~70 cm |
| Ground clearance under frame | ≥ 15 cm (deck hangs below) |
| Mass, mowing config | ~45–55 kg (one deck) · ~60–70 kg (twin decks) |
| Cut width | ~50 cm with one centered deck (v1) → **~1 m with twin decks** (v1.5) |
| Mowing speed | 0.5–1.0 m/s |
| Top speed (transit) | ~1.5–2 m/s (software limited) |

**Why build wide now:** on 3+ acres with 8 ft paths, the twin-deck upgrade roughly halves mowing time (§5). Cutting the extrusion 50 cm longer now costs ~$30. Rebuilding a narrow frame later would mean redoing the drive mounts, wiring, and CAD. v1 runs with one deck centered; the second deck bolts onto the same belly mount. The twin decks can sit side by side, or staggered front-left / rear-right with ~5 cm overlap. We'll decide in CAD based on how the Ryobi deck housing looks.

**Why the battery sits over the drive axle:** in a zero-turn layout the casters carry weight without providing traction. Every kilogram over the rear axle helps on slopes, as §5 shows.

## 5. Back-of-envelope sizing

Assumptions: 45 kg robot, 10" (0.254 m) wheels, rolling-resistance coefficient on turf ≈ 0.10, 65 % of mass on the drive wheels.

**Torque on a 15° slope:** grade force 45·9.81·sin15° ≈ 114 N, plus rolling resistance ≈ 44 N, gives ≈ 160 N total. That works out to **≈ 10 N·m per wheel**. A 36 V 350 W 10" hub motor is typically rated around 10–15 N·m continuous with higher peak, so torque is adequate.

**Traction is the real limit** (a general-user concern; our farm is flat): normal load on the drive wheels ≈ 287 N. With grass friction μ ≈ 0.35 (wet) to 0.6 (dry), the robot can push 100–170 N before slipping. That means **dry 15° slopes are marginal and wet 15° slopes will slip.** The v1 spec is therefore **10° slopes reliably, 15° in dry conditions**, with ballast over the axle as the first fix and the 4WD variant (Option C) as the real one.

**Towing a garden cart:** a 100 kg load in a 15 kg cart on flat grass needs ≈ 113 N, plus the robot's own ≈ 44 N, for ≈ 160 N. That's feasible on dry flat ground, especially with some tongue weight on the hitch. Mulch at roughly 250–400 kg per cubic yard means **partial loads, many trips**. That's fine for a robot that doesn't get tired.

**Wheel speed:** 1 m/s on a 10" wheel is ≈ 75 rpm. Scooter hub motors have a no-load speed around 600–700 rpm at 36 V, so the robot runs at ~10–15 % of motor speed. That's fine **only with Hall-sensored FOC**, which VESC and EFeru firmware both provide. Sensorless control will stutter at low speed.

**Mowing energy:**

| Load | Estimate |
|---|---|
| Drive on turf at 0.8 m/s | ~100–150 W |
| Blade (21" deck, maintained lawn, mowed weekly or more often) | ~150–400 W |
| Electronics (autopilot, GPS, radios, Pi later) | ~20–30 W |
| **Total** | **~300–550 W** |

Coverage at 0.45 m effective swath × 0.8 m/s ≈ **1,300 m²/hour ≈ 1/3 acre per hour**. A 36 V 20 Ah pack (720 Wh, ~575 Wh usable) gives **~1–1.5 h, or roughly 0.3–0.5 acre per charge**. Ways to extend that:

- Mow more often and cut less each time, as commercial robot mowers do. Blade power drops sharply.
- Run the blade from its own tool battery (see §6), which roughly doubles available energy.
- Use two packs: swap one while the other charges.
- Phase 2: add a charging dock and mow in daily chunks.

**Applied to our ~3 acres (12,000 m²):**

| Configuration | Effective swath × speed | Coverage | Time per full pass | Energy per pass |
|---|---|---|---|---|
| One 21" deck, 0.8 m/s | 0.45 m × 0.8 m/s | ~1,300 m²/h | **~9 h** | ~3.5 kWh |
| One 21" deck, 1.0 m/s | 0.45 m × 1.0 m/s | ~1,600 m²/h | ~7.5 h | ~3 kWh |
| Twin decks (~1 m cut), 1.0 m/s | 0.95 m × 1.0 m/s | ~3,400 m²/h | ~3.5 h | ~2.4 kWh |

So the operating model is **mowing a zone each day from a charging dock**, the way commercial robot mowers work. About 1.3–1.5 h of mowing per day covers all 3 acres roughly once a week with a single deck. That fits within one 720 Wh pack per day, keeps grass short so blade power stays low, and scales as the farm grows: add zones, then add a second deck or a second robot.

Consequences:
- **The charging dock moves up** to the first item in phase 2, right after supervised mowing works. Until then, swap batteries manually.
- **The twin-deck module** (~1 m cut) is the v1.5 upgrade, and the frame is built for it from day one (§4). With twin decks, about 30–40 min of mowing per day covers 3 acres weekly, which leaves room for the farm to grow.
- **Open sky** means RTK should hold a fixed solution almost everywhere. Narrow paths and tree edges get touched up by hand.

## 6. Subsystems

### 6.1 Drive

| | Default (new) | Budget | Salvage |
|---|---|---|---|
| Motors | 2× 10" pneumatic hub motor, 36 V 350–500 W, **Hall sensors**, double-sided axle | same | Power-wheelchair gearmotors with brakes (24 V) |
| Controller | 2× VESC-class FOC (e.g. Flipsky 4.20/6.x, Makerbase 75100 class), RC-PWM or CAN from ArduPilot | 1× hoverboard mainboard + [EFeru FOC firmware](https://github.com/EFeru/hoverboard-firmware-hack-FOC), PWM/PPM variant, **tank mixing off** | Sabertooth 2x32 or RoboClaw 2x30 |
| Casters | 2× 11×4 zero-turn mower caster wheels + forks + yokes (mower replacement parts) | same | Casters from a junked riding mower |

Mechanical notes from the e-bike world:

- **Torque arms.** Hub-motor axles spin out of plain slotted plates under load and shred the wires. Use 6 mm aluminum or 5 mm steel dropout plates with the axle flats in a snug slot, plus torque washers.
- **No parking brake.** Hub motors roll freely when unpowered. The VESC can hold position while armed, but on power loss a hub-motor robot will roll downhill. Park on the flat, or add a solenoid or caliper brake later. Wheelchair motors don't have this problem.

### 6.2 Mower module

The mower is a **module that bolts to the belly mount**, not part of the robot. Options:

| Option | How | Pros | Cons | Verdict |
|---|---|---|---|---|
| **M1. Salvaged cordless mower** (Greenworks/Ryobi/Kobalt "40 V max" class) | Remove handle and wheels, hang the deck from the robot, have the robot switch the mower's own start/bail circuit through a relay | Deck, blade, motor, **built-in blade brake**, and height adjust are all included; used units are cheap; 40 V-max tools are 10S, the same voltage class as our bus | Each brand's safety interlock is different; tool-battery data handshakes may complicate running from our pack | **v1 recommended.** Simplest path to cutting grass. |
| M2. Robot-mower-style blades | 1–3 small brushless motors with pivoting razor blades | Safest, quietest, lowest power | Needs frequent mowing; struggles in tall grass | Good later for areas near people |
| M3. Gas push-mower deck + brushless motor | Free curbside deck; replace the engine with a ~1–2 kW outrunner + VESC with brake | Strong cut, most salvage-y | Must build our own blade brake and guarding; keep blade tip speed under the ANSI 19,000 ft/min limit | Fallback / v2 heavy-grass deck |

**Our M1 plan, Ryobi:** buy a **second, used Ryobi mower** of the same voltage line as the one already in use, so the farm keeps its daily mower and the robot shares its batteries and charger. Used Ryobi 40 V mowers are common on Marketplace, often sold without a battery for $50–150. Prefer a brushless model with a mulching deck.
- *To confirm:* model number of the current mower. Ryobi sells 40 V, 80 V, and 18 V ONE+ (twin-battery) mowers, and the voltage decides compatibility. 40 V is the best match: it's 10S, the same class as our drive bus.
- *Bench test:* how the mower's start button and bail switch are wired, and whether it starts from a bench supply or 3D-printed battery adapter without a battery data handshake. This decides phase 2 below.

**Power for M1, phase 1:** the blade runs **from Ryobi batteries we already own**. That keeps the blade electrically isolated from the drive bus, avoids handshake problems, and adds energy. A 40 V 6 Ah pack (~216 Wh) runs a 21" deck for roughly 40–60 minutes. The robot only controls a relay that is part of the kill chain (§6.4).

**Phase 2, once the dock exists:** feed the deck from the robot's main bus through a Ryobi battery adapter so the dock recharges everything, removing the need to swap Ryobi packs every day. This depends on the bench test above. If the mower requires a battery handshake, keep a Ryobi pack on the deck and charge it on the dock with a Ryobi charger.

**Deck suspension:** hang the deck on four short links or chains with anti-scalp wheels, as mid-mount riding mowers do. The deck then follows the ground and doesn't scalp on bumps.

### 6.3 Navigation and control

```
                 ┌──────────── RTK corrections (NTRIP over Wi-Fi/LTE, or own base via radio) ─┐
                 ▼                                                                             │
 [u-blox ZED-F9P rover GPS] ──► [ArduPilot Rover flight controller] ──PWM/CAN──► [VESC L] [VESC R]
 [2nd F9P for GPS-yaw, opt.]─►        │  │  │                                     [blade relay]
                                      │  │  └── RC receiver (ELRS) ← manual drive + arm switch
                                      │  └───── telemetry radio ↔ Mission Planner / QGroundControl
                                      └── MAVLink/DDS ──► [Pi 5 + ROS 2] (phase 2: camera, obstacles, dock, arm)
```

- **Autopilot:** ArduPilot Rover 4.6.x on a Pixhawk-class or Matek H743-class board. Set it up as a skid-steer rover (`SERVO1_FUNCTION=73` throttle-left, `SERVO3_FUNCTION=74` throttle-right). Use a **switch** to arm, never stick arming. ArduPilot's built-in IMU covers tilt and lift detection.
- **GPS:** u-blox ZED-F9P board + survey-grade multiband antenna on a mast. **Heading:** compasses do poorly near hub-motor magnets and steel. ArduPilot supports **GPS-yaw (moving baseline)** with two F9Ps about 50 cm or more apart, which is the recommended upgrade if heading proves noisy.
- **RTK corrections: our own base station** (no known service nearby):
  - **Hardware:** a ZED-F9P + survey multiband antenna on a fixed mount with clear sky, on a barn or house roof or a post. Power and a small enclosure.
  - **Absolute position:** let the base "survey in," or better, log 24 h of raw data and submit it to the free **NOAA OPUS** service or a PPP service. That fixes the base's coordinates, so lawn maps and fences stay accurate even if the base is moved or replaced.
  - **Link to the robot, v1:** a 915 MHz telemetry radio straight from the base to the rover GPS. No network or internet needed. SiK-class radios cover typical farm distances easily.
  - **Link, later:** a Raspberry Pi at the base runs an NTRIP caster (e.g. RTKLIB `str2str`) over farm Wi-Fi or LTE. Any number of robots, a tractor, or survey gear can use the same corrections.
  - One base covers everything within ~10 km, so it serves the whole farm as it expands.
  - *Worth a 10-minute check:* look for a state DOT CORS station or community RTK2go base within ~20 km. If one exists, it's a free backup.
- **Mowing patterns:** Mission Planner's polygon "survey/grid" tool creates back-and-forth passes with overlap, and fences mark the hard boundary. Later, [Fields2Cover](https://github.com/Fields2Cover/Fields2Cover) (ROS 2) can produce better coverage paths with headland turns.
- **Simulation all winter:** ArduPilot SITL (optionally with Gazebo) lets us practice missions, geofences, and failsafes before the hardware exists.
- **Tree cover:** RTK degrades to "float" under trees and near buildings. v1 mows open areas only and pauses when the fix drops. Phase 2 adds wheel odometry and camera-based fallback for edges.

### 6.4 Safety and kill chain

This is designed first and tested on the bench before the blade is ever installed.

1. **Hardware e-stop loop (normally-closed, series):** mushroom button on the robot → wireless e-stop receiver relay → bumper switches. Any break opens the **main contactor** (drive power) and the **blade relay**.
2. **Wireless e-stop that fails safe:** losing the signal must stop the robot. Use a dedicated receiver (a separate ELRS receiver with failsafe = no pulses driving a relay module, or a commercial industrial wireless e-stop). A simple 433 MHz relay remote is *not* acceptable, because it doesn't fail safe.
3. **Blade interlocks, through the autopilot:** blade only runs when armed, in Auto or Mission mode, with RTK fix, inside the fence, level (tilt < ~25°), and not lifted. A relay output plus a Lua script, or `RELAY` + failsafe actions, cuts the blade the moment any condition fails.
4. **Blade brake:** the M1 mower deck has one built in. For M3 we'd need a VESC brake with a mechanical backup. Target: blade stops in under 3 s.
5. **Geofence** with action = Hold/disarm.
6. **Supervised operation only in v1:** someone is present with the e-stop and no people, kids, pets, or livestock are in the zone. Obstacle detection (OAK-D Lite or a cheap ToF/radar ring) comes in phase 2 before any unsupervised mowing.
7. Precharge resistor, main fuse, per-rail fuses, and fused battery leads, as in the concept report.

### 6.5 Electrical

| Item | Spec |
|---|---|
| Bus | 36 V class: 10S Li-ion (42 V max) **or** 12S LiFePO4 (43.8 V max). Check every controller and DC-DC is rated ≥ 50 V. |
| Battery | 36 V 20 Ah e-bike pack with BMS (≥ 30 A continuous), XT90 or Anderson connector, in a slide-in bay over the axle |
| Distribution | Main fuse → key switch → precharge → contactor (e-stop loop) → VESCs; unswitched fused feed → DC-DCs for electronics so logging survives an e-stop |
| Rails | 12 V 10 A (lights, payloads, Pi later via 5 V), 5 V 5 A (flight controller, GPS, receivers) |
| Sensing | Power module or INA226 for bus voltage/current to ArduPilot (battery failsafe) |
| Enclosure | IP65 polycarbonate box, cable glands, conformal-coated boards |

### 6.6 Frame and fabrication

- **30×30 aluminum T-slot extrusion** for the perimeter and top deck. Cut-to-length, corner brackets, no welding. Easy to change through many iterations.
- **Plate parts** (dropouts, caster yokes, hitch plate, deck hangers) from 6 mm aluminum or 3–5 mm steel. Hand-cut and drilled at first, then sent to an online cutting service (e.g. SendCutSend) once the design is stable.
- **3D-printed PETG/ASA** for sensor mounts, cable guides, bumper housings, and the antenna mast base. Avoid PLA outdoors.
- **CAD: Onshape.** It's browser-based, so the team and intern can co-edit with no install and no file merges. It has good frame (extrusion) and sheet-metal tools, and the free plan requires public documents, which fits an open-source project. At each milestone, export **STEP (whole assembly), DXF (plates for cutting), and STL (printed parts)** to `hardware/cad/` so the repo works without Onshape. *Alternatives considered:* FreeCAD 1.x (fully open with files in git, but steeper and slower for frames and assemblies); Fusion 360 (personal license is non-commercial only, so not appropriate for Orbitist).
- **Standard interfaces**, published as drawings so others can build compatible modules:
  - *Belly mount:* 4 hanger points on a fixed rectangle
  - *Rear hitch:* 2" receiver or 5/8" pin hitch at a fixed height
  - *Top deck:* T-slot rails at fixed spacing, plus a 12 V / 5 V / Ethernet / CAN payload connector

## 7. Roadmap

| Phase | Timeframe | Goal | Exit criterion |
|---|---|---|---|
| **0. Design + sim** | Oct–Nov 2026 | Finalize this doc, CAD in Onshape, order parts, **set up the RTK base and survey its position**, ArduPilot SITL missions | BOM ordered; base surveyed; SITL mows a polygon of our real lawn |
| **1a. Rolling chassis** | Dec 2026 | Frame, drive, battery, kill chain, RC driving | Drives under RC with a working e-stop; tested on snow/gravel |
| **1b. Autonomy without blade** | Jan–Feb 2027 | Autopilot, RTK, tuning, missions on dormant lawn or snow; **map lawn zones and fences** | Runs a 50×20 m grid, passes within ±5 cm |
| **1c. Mowing** | Apr–May 2027 | Install Ryobi deck module, blade interlocks, supervised mowing with battery swaps | Mows one zone, supervised, with no missed strips |
| **2. Unsupervised-capable** | Summer 2027 | **Charging dock first**, then Pi 5 + ROS 2, obstacle sensing, odometry fallback, deck on main bus | Mows all ~3 acres weekly in daily zones from the dock; stops for a dummy obstacle 10/10 times |
| **3. Hauling** | 2027 | Hitch + cart module, 4WD variant | Moves a cart of mulch along a mapped route |
| **4. Manipulation** | 2028+ | Top-deck arm, perception for weeding and pruning | — |

## 8. Open questions for us to decide

*Answered 2026-10-08:* ~3 acres and growing; Ryobi mower + batteries on hand; any tools available; cell coverage and extendable Wi-Fi; no known RTK service; CAD open to recommendation; flat terrain; open sky; lawns joined by ~8 ft paths; license delegated. See §1a.

Still open, none blocking:
1. **Ryobi voltage line:** check the label on the batteries already on hand (40 V, 80 V, or 18 V) and buy the used robot mower in the same line. If the batteries are 40 V, look for a used **Ryobi 40 V brushless 20–21" mower**, ideally two eventually for the twin deck.
2. **Number of separate lawn zones**, to plan the mowing schedule and choose the dock location. This can be mapped with the robot itself in phase 1b.

## 9. References

- Concept report: [`docs/concept/2026-09-vineyard-robot-design-report.pdf`](../concept/2026-09-vineyard-robot-design-report.pdf)
- ArduPilot Rover: [Dock mode](https://ardupilot.org/rover/docs/dock-mode.html) (AprilTag/ArUco docking via a companion computer); [KevinG's autonomous zero-turn mower](https://discuss.ardupilot.org/t/kevings-autonomous-zero-point-turn-lawn-mower/29178); [first run of a zero-turn mower implementation](https://discuss.ardupilot.org/t/first-run-of-a-nice-implementation-of-autonomous-zero-turn-mower/40501); [skid-steer with VESCs](https://discuss.ardupilot.org/t/three-wheeled-rover-with-skid-steering-and-servo-controlled-tailwheel/34696); [hoverboard boards with ArduPilot](https://discuss.ardupilot.org/t/using-the-boards-from-the-hoverboard-in-autopilot/87229)
- [OpenMower](https://github.com/ClemensElflein/OpenMower): open-source RTK robot mower (ROS, xESC motor control). Good reference for mower-specific software, though its hardware is tied to a donor mower.
- [Acorn (Twisted Fields)](https://github.com/Twisted-Fields/acorn-precision-farming-rover), [farm-ng Amiga](https://farm-ng.com/): open and commercial ag-rover references from the concept report
- [Fields2Cover](https://github.com/Fields2Cover/Fields2Cover): coverage path planning
- [EFeru hoverboard FOC firmware](https://github.com/EFeru/hoverboard-firmware-hack-FOC)

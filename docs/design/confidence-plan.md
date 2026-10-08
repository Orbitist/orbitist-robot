# Confidence plan: what's verified, what isn't, and how we close the gaps before buying

*Status 2026-10-08. Companion to [platform-v1.md](platform-v1.md). Update the status column as tests complete.*

The aim: spend the big money (motors, battery, frame, electronics ≈ $1,500) only after the riskiest assumptions are measured. Most risks can be retired with **about $350 of parts we need anyway**.

## 1. Where the design stands

| Area | How it was checked | Confidence | Evidence |
|---|---|---|---|
| Layout, clearances, weight distribution | Parametric CAD with automated clearance checks | ✅ High for geometry; masses are estimates | [`report.md`](../../hardware/cad/exports/report.md) |
| Frame and bracket strength | Hand calculations, 2.5 g bumps, side skid, motor torque | ✅ High, given catalog extrusion properties | [`strength-report.md`](../../hardware/cad/exports/strength-report.md) |
| Bumper stopping distance → 0.6 m/s mowing speed | Kinematics with an assumed 3 m/s² braking | 🟡 Medium: braking rate must be measured | strength report §bumper |
| Autopilot configuration, failsafes, blade interlock | **ArduPilot SITL**: 13/13 acceptance checks (mission, RC loss, e-stop, restart, GPS loss, fence) | ✅ High for logic; vehicle dynamics are generic | [`results/test-plot.md`](../../software/sim/results/test-plot.md) |
| Coverage pattern and mowing time | Planner + SITL. Full-size sample zone (4,100 m², tree + bed, 781 waypoints): **mission completed, 97.5 % cut vs 98.0 % planned, 6.13 h vs 6.1 h predicted** | ✅ High for the sample layout; the real lawns aren't mapped yet | [`results/sample-farm.md`](../../software/sim/results/sample-farm.md), [`plans/`](../../software/sim/plans) |
| Hub motors at mowing speed (45 rpm) | Operating-point model with uncertainty ranges | 🟡 OK in the typical case; **worst case overheats** | [`drive-energy-report.md`](../../hardware/cad/exports/drive-energy-report.md) |
| Daily energy and battery size | Energy model from coverage time × power | 🔴 **Blade power is a 150–400 W guess**, and it's the biggest energy term | drive-energy report §2 |
| RTK fix over the actual lawns | Not tested | 🟡 Open sky reported; untested near trees and buildings | — |
| Ryobi deck: mass, size, blade switching | Estimates (17 kg, 580 mm housing) | 🔴 Unknown model and wiring | — |

## 2. What simulation found and fixed

These were caught in software, with nothing bought, broken, or mown wrong. Details are in [software/sim/README.md](../../software/sim/README.md#what-simulation-found-and-what-changed-because-of-it).

1. **Fence avoidance stalls edge mowing.** ArduPilot's 2 m avoidance margin → avoidance limited to proximity sensors.
2. **Corner-cutting into trees.** Extra 0.25 m obstacle clearance; fences at the body-contact line; tighter waypoint radius.
3. **Waypoint hunting.** Stripe-end waypoints 3 cm apart made the robot pivot for minutes → the planner merges legs shorter than 0.3 m.
4. **Uncut strips.** With realistic tracking, the pass overlap needed to grow from 7.5 to 15 cm.
5. **Blind driving after GPS loss.** About 8 m of dead-reckoning → the robot now pauses after 2 s and resumes automatically.
6. **Fence storage limit.** A full zone's fence exceeded ArduPilot's 84 points → the planner now fits fences in 80 points.
7. **A planned route through a tree.** A planner bug, caught by a clearance check → replaced by a visibility-graph router; every leg is now verified ≥ 0.17 m from no-go zones.
8. **Operating time.** About 17 h/week with one deck at 0.6 m/s, 8 h/week with two, which changes the twin-deck priority (below).

## 3. Before buying the main parts: four de-risking tests

In this order. Each feeds a number back into `params.py`, `drive_energy.py`, or `coverage.py`, and the reports regenerate.

| # | Test | Buy | ~$ | Answers | Decides |
|---|---|---|---|---|---|
| **T1** | **Used Ryobi mower on the farm lawn.** Time one 6 Ah pack to empty while mowing normally (or log current with a DC clamp meter). Measure the deck with the handle and wheels off: housing outline, motor height, mass. Open the handle wiring: bail-switch current, start circuit, blade-brake stop time. Try powering it from a bench supply or a printed battery adapter. | Used Ryobi mower (same voltage as the farm's batteries) | 50–150 | **Blade power** (the biggest energy unknown), deck geometry, how the robot switches the blade, whether the deck can run from the robot pack | Battery size and chemistry; K5 relay vs contactor; deck hangers in CAD; whether phase 1 needs daily Ryobi pack swaps |
| **T2** | **RTK on a cart.** Set up the base station (guide), put the rover GPS + flight controller on a wheelbarrow, and walk every lawn edge, tree, and bed. | Wave 1 GNSS kit (needed anyway) | (700–900) | RTK fix availability across the real lawns; the **real lawn file** | Real mowing hours and coverage per zone; where the robot can't mow; dock location |
| **T3** | **One hub motor + one VESC on the bench.** Run VESC motor detection (torque constant, resistance), check the axle flats and dropout spacing, test smooth low-speed Hall FOC at 45 rpm, run **30 minutes at mowing torque** (≈ 4–6 N·m: drag a weighted tire or sled) and measure motor temperature, and test the VESC timeout brake. | 1 hub motor + 1 VESC + current-limited bench supply | 210 + 60 | Whether hub motors run cool at mowing speed; real torque constant; braking rate for the bumper calculation | Buy the second motor, or switch to geared or wheelchair motors; final fork-plate DXF; VESC current limits |
| **T4** | **One caster.** Measure the bolt pattern, height, and swivel offset. | 1 caster (need 2 anyway) | 35 | Caster geometry | Caster plate DXF and frame height |

**Then:** cut the plates and order Wave 2 (frame, second motor and VESC, electrical, battery), with every DXF and the battery choice based on measured parts.

## 4. Risk register

| Risk | Likelihood | Impact | Status | Retire by |
|---|---|---|---|---|
| Blade power higher than assumed → battery too small, too many pack swaps | Medium | High | 🔴 Open | **T1** |
| Hub motors overheat at mowing speed | Low–medium | High | 🟡 Open | **T3** (fallback: wheelchair or geared motors; frame accepts swappable drive modules) |
| Ryobi needs a battery handshake, so the deck can't run from the robot pack | Medium | Medium (daily swaps in phase 1) | 🔴 Open | **T1** (fallback: keep a Ryobi pack on the deck and charge it on the dock) |
| RTK float/no-fix near buildings and trees | Medium | Medium | 🟡 Open | **T2**; the robot pauses on fix loss (SITL-verified) |
| Path tracking on grass worse than ±10 cm → uncut strips | Medium | Low (one more overlap step) | 🟡 Open | Phase 1b field tuning; overlap is one planner parameter |
| Braking on wet grass < 3 m/s² → bumper speed limit < 0.6 m/s | Medium | Medium | 🟡 Open | T3 brake test, then commissioning step 7 |
| Single deck too slow for 3 acres weekly (≈17 h) | High | Medium | 🟡 Known | Twin decks (≈8 h), already designed in; buy the second used Ryobi early |
| Frame or joint failure | Low | High | ✅ Analysed | Gussets, saddle forks, torque arms; check bolt preload after the first hours |
| Autopilot logic error (blade on outside AUTO, no stop on faults) | Low | High | ✅ SITL 13/13 | Re-run `run_sitl.py` after every parameter or script change |
| Mission or fence too large for the flight controller | Low | Medium | ✅ Resolved | SD-card mission/fence storage + planner budget |
| Cost overrun | Medium | Medium | 🟡 | De-risking tests buy parts needed anyway; the battery waits for T1 |

## 5. Decision points

- **After T1:** battery choice (36 V 20 Ah, 30 Ah, or two packs), K5 type, deck hangers. If the blade draws ≥ 300 W, buy the second Ryobi deck for v1 and go twin straight away. It halves mowing hours, while blade energy per acre stays about the same.
- **After T2:** confirm 3 zones (or more) and the dock location; regenerate plans from the real lawn file.
- **After T3:** commit to hub motors, or switch drive modules before buying the second motor.

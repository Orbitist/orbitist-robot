# Simulation: plan and test mowing before the robot exists

Two tools, both using the robot's real geometry (`hardware/cad/params.py`) and its real autopilot configuration (`software/ardupilot/`):

| Tool | What it does |
|---|---|
| `coverage.py` | **Mowing planner.** Turns a lawn file into ArduPilot missions (one per zone, i.e. one day's job), geofences, a coverage map, and a time estimate. |
| `run_sitl.py` | **Acceptance tests.** Boots ArduPilot Rover 4.6.3 in software-in-the-loop (SITL) with our parameters and the blade-interlock Lua script, flies the planned mission, and injects faults. |

## Setup (once, ~10 min)

```bash
cd software/sim
./setup.sh
```

This creates a Python 3.12 environment and downloads and compiles ArduPilot SITL into `ardupilot/` (git-ignored).

## Plan mowing

```bash
.venv/bin/python coverage.py lawns/sample-farm.json                 # single deck
.venv/bin/python coverage.py lawns/sample-farm.json --config twin   # twin decks
```

Output goes to `plans/<lawn>-<config>/`:
- `<zone>.waypoints`: load in Mission Planner.
- `<zone>.plan`: load in QGroundControl. Includes the fence.
- `<zone>-fence.json`: the fence on its own.
- `<zone>.png`: map of the plan. Red marks area the robot can't reach.
- `report.md`: time and coverage per zone.

**The pattern:** the deck sits on the robot's right, so the robot first runs two laps with the deck facing the boundary: counter-clockwise around the lawn, clockwise around trees and beds. It then mows straight stripes at whichever angle needs the fewest turns. At each stripe end the offset deck makes the robot pivot 180° almost in place.

**Lawn files** (`lawns/*.json`) are in metres east/north of an origin. `sample-farm.json` is an invented ~3-acre layout. Replace it with the real lawns once the RTK rover has walked the boundaries; the planner accepts the same format.

## Run the acceptance tests

```bash
.venv/bin/python run_sitl.py                         # all scenarios, small test plot (~3 min)
.venv/bin/python run_sitl.py mission --lawn lawns/sample-farm.json --zone east --speedup 40
```

| Scenario | Pass criteria |
|---|---|
| `mission` | completes; tracking p95 ≤ 0.15 m while mowing; actual cut ≥ planned − 2 %; blade only on while armed in AUTO |
| `rc_loss` | transmitter lost → Hold and blade off within 2.5 s |
| `estop` | e-stop loop opens → disarmed and blade off within 0.5 s |
| `restart` | e-stop released → stays disarmed and still |
| `gps_loss` | GPS lost → blade off within 1 s, paused within 3 s, < 2 m travelled; resumes when the fix returns |
| `fence` | commanded outside the fence → stays within 1 m of it |

Results: [`results/test-plot.md`](results/test-plot.md). Per-run logs, ArduPilot `.BIN` logs, and track plots go in `runs/` (git-ignored).

## What simulation found (and what changed because of it)

| Found in SITL | Change |
|---|---|
| ArduPilot's **fence avoidance** keeps the robot 2 m (`AVOID_MARGIN`) from the fence, stalling the perimeter laps | `AVOID_ENABLE = 2` (proximity only); the fence still stops the robot on a breach |
| **Corner-cutting** with `WP_RADIUS 0.3` took the robot into the fence around a tree | Laps keep an extra 0.25 m from trees and beds; the fence sits where the body would touch; `WP_RADIUS 0.2` |
| **Waypoints a few cm apart** (stripe-end hops) made the robot pivot back and forth for minutes | Planner merges legs < 0.3 m into one pivot point |
| With ±0.14 m tracking, a 7.5 cm overlap left uncut strips (−5 % coverage) | Overlap 0.15 m (revisit with real tracking) |
| After **losing GPS**, the robot dead-reckoned ~8 m before ArduPilot's failsafe | Lua pauses (Hold) after 2 s without an RTK fix and resumes when it's back |
| A full-size zone's fence (119 points) exceeded ArduPilot's **84-point fence store** | Conservative fence simplification within an 80-point budget; `BRD_SD_FENCE` on hardware |
| Real pivot turns cost ~3 s more each than estimated | Planner time model calibrated (`PIVOT_OVERHEAD_S = 5`) |
| SITL reads "no PWM" as full reverse | SITL-only `MOT_SAFE_DISARM 0` (the real VESCs brake on missing pulses) |

## Limits of this simulation

- **Vehicle dynamics are generic.** ArduPilot's `rover-skid` model is a small, fast hobby rover (4 m/s, very high acceleration), not a 65 kg robot on grass. It validates mission logic, safety behaviour, failsafes, coverage geometry, and the planner, but **not** tuning, traction, or braking distances. Steering tuning (`ATC_*`, `PSC_*`) happens on the real robot; the SITL overlay's tuning is model-specific.
- **GPS is idealised:** RTK fixed everywhere with 2 cm noise. Tree-canopy dropouts are tested only as total GPS loss (`gps_loss`).
- **No grass, no blade load, no battery sag.**

Field tests in phase 1b/1c (see `docs/design/confidence-plan.md`) cover what the simulator can't.

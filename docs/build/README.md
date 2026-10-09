# Build tutorial: Orbitist platform v1, one step at a time

This is the hands-on path from an empty bench to a mowing robot. Each step is a separate page with:

- **Buy:** the exact parts for that step, with links checked on the date shown at the top of the page, prices as seen that day, and the specification to check if a listing has changed.
- **Do:** the work, in order, with what "done" looks like.
- **Record:** measurements to write into [`measurements.md`](measurements.md). They feed `hardware/cad/params.py`, so the model, cutting files and reports regenerate from real parts.

Work one step at a time. Finish a step's **Done when** checklist before buying the next step's parts; several later purchases depend on numbers measured earlier (the battery size on the blade test, the plate DXFs on the motor axle and caster).

| Step | What | Spend (approx.) | Depends on | Status |
|---|---|---|---|---|
| [1](step-01-de-risk.md) | De-risking tests: one razor disc + one solar panel on the lawn, one hub motor + VESC on the bench, caster measurements | $450–600 | — | links checked (disc motor and panel links pending) |
| [2](step-02-rtk-base.md) | RTK base station and rover GPS; survey the base; map the lawns | $700–900 | — (parallel with 1) | links checked |
| [3](step-03-autopilot-bench.md) | Flight controller, radios, e-stop receiver on the bench; load our parameters and script | $350–400 | 2 (for GPS) | links checked |
| [4](step-04-frame.md) | Frame: extrusion, brackets, gussets, cut plates | ~$500 | 1 (axle and caster dimensions) | outline |
| [5](step-05-drive-modules.md) | Second motor and VESC, forks, torque arms; drive modules on the frame | ~$350 | 1, 4 | outline |
| [6](step-06-casters-bumper.md) | Casters on corner plates, sprung bumper with switches | ~$150 | 4 | outline |
| [7](step-07-electrical.md) | Battery, contactor, fuses, DC-DCs, MPPT, e-stop loop; commissioning tests | ~$600 | 1 (pack size), 5, 6 | outline |
| [8](step-08-autopilot-on-robot.md) | Autopilot on the robot, RC driving, steering tuning, first missions without blade | — | 3, 7 | outline |
| [9](step-09-deck.md) | Razor deck module: four discs, plate, skirt, hangers, interlocks, supervised daily mowing | ~$400 | 1, 8 | outline |
| [9b](step-09b-solar-roof.md) | Solar roof: posts, roof frame, panels, MPPT; antenna and e-stop move up | ~$400 | 4, 7 | outline |
| [10](step-10-phase-2.md) | Phase 2: companion computer, obstacle sensing, unsupervised operation (no dock needed) | ~$400 | 9, 9b | outline |

Steps marked *outline* list the specification and the work; their purchase links get added (and checked) when we reach them, because listings and prices move.

## Conventions

- Prices are US retail as seen on the date in each page's header, before tax and shipping. Nothing here is sponsored; links are to the page I verified, usually the manufacturer's.
- **Spec first, link second.** If a link is dead or the price has jumped, buy anything that meets the spec line next to it.
- Used and salvaged parts are fine wherever a line says so. The battery can be a healthy used e-bike pack. The farm's existing Ryobi mower is the catch-up mower; it is not modified.
- Safety-critical items (fuses rated for 58 V DC, the fail-safe e-stop parts, the contactor) are marked **safety** and should not be substituted with cheaper parts that don't meet the rating.

## What you'll have at the end of each step

1. Measured numbers that settle the drive motor, battery and plate drawings, and a working one-wheel drive on the bench.
2. A base station on a post with its position fixed to ~2 cm, and a map file of the real lawns.
3. The autopilot talking to the GPS, radios and e-stop receiver on the bench, running our configuration.
4. A rolling frame you can push around.
5. A frame that drives under radio control (no autopilot yet).
6. The robot stops when the bumper is pushed.
7. The complete power and safety system, tested item by item.
8. The robot drives a planned mission across the lawn without a blade.
9. The robot mows a lawn zone, supervised, and keeps mowing daily on solar.
10. Daily unsupervised mowing.

Reference documents: [design](../design/platform-v1.md) · [electrical](../../hardware/electrical/README.md) · [CAD](../../hardware/cad/README.md) · [RTK base guide](../guides/rtk-base-station.md) · [simulation](../../software/sim/README.md) · [confidence plan](../design/confidence-plan.md)

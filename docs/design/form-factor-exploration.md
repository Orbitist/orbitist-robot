# Form factors for farm robots, from first principles

*2026-10-08. A step back before buying parts: is a 90 kg wheeled tool-carrier the right shape of robot for a farm that is heading toward polyculture? This document reasons from physics and economics rather than from existing products, scores the candidate form factors against the work a farm actually needs done, and ends with what it changes for Orbitist v1.*

## 1. What farm work is, physically

Every task on a farm is one of five physical operations, applied at a place and a time:

| Operation | Examples | What it costs physically |
|---|---|---|
| **Cut** | mow, prune, harvest, chop-and-drop | energy per unit of material severed; force scales with stem thickness² |
| **Move mass** | mulch, compost, water, harvest, amendments | energy ∝ mass × distance (plus rolling losses); throughput ∝ payload × speed / trip length |
| **Place** | seed, transplant, drip emitters, stakes | precision positioning of small items; low force |
| **Sense** | plant state, weeds, pests, soil moisture, growth | almost free: a camera is $20 and compute is cheaper every year |
| **Protect** | weed, deter pests, shade, cover, net | mostly small forces, high frequency, per-plant decisions |

Two things fall out immediately:

1. **Sensing has decoupled from actuation.** Nothing says the thing that looks at a plant must be the thing that acts on it. A fixed camera can watch 100 m² for years for $20; the actuator can be anything dispatched later. Most robot designs bundle both into one expensive mobile body because that's what a human is.
2. **Non-contact actuation avoids the hard problem.** Dexterous manipulation in clutter (picking a tomato among leaves, pulling one weed from a seedling row) is still unsolved at any price. Laser, flame, spray, water, light, sound and mowing need no grasping. Any form factor that relies on non-contact tools can work *now*; any that relies on hands is a research project.

## 2. Scaling laws that decide the body size

**Square-cube.** A robot half the size has ¼ the panel area and footprint but ⅛ the mass, payload and battery. Small robots are cheap, light on the soil, and carry almost no kinetic energy (a 5 kg robot at 0.5 m/s has 0.6 J; it cannot hurt anything). But their wheels are small, and **a wheel cannot climb an obstacle taller than roughly a third of its radius.** A 10 cm wheel is stopped by a 3 cm stick. Polyculture ground is nothing but sticks, stems and ruts. Small wheeled robots need either prepared ground (lawn, beds, paths), rails, cables, or legs.

**Mass-moving throughput.** A swarm versus one hauler, for 100 m trips at 0.5 m/s (400 s round trip):

| | Payload | Trips/hour each | Throughput |
|---|---|---|---|
| 20 ant-robots | 2 kg | 9 | 360 kg/h, if all 20 work |
| 1 robot towing a cart | 100 kg | 9 | 900 kg/h |

Energy per kg·m is similar for both; the hauler wins because payload scales with the cube of size while the swarm's cost scales with count. Ants win only because they are free. **Swarms are the wrong shape for moving mass.**

**Cutting energy depends on the regime, not the robot.** Mowing energy is set by how much plant material is severed per square metre, which depends on how often you cut:

| Regime | Blade power | Energy per m² | 3 acres per pass |
|---|---|---|---|
| Weekly cut, 21" rotary deck (our v1 plan) | 150–400 W at 0.27 m²/s | ~0.3 Wh/m² | ~3.7 kWh |
| Daily "increment" cut, razor-disc deck (how robot mowers work) | 25–60 W at ~0.1 m²/s | ~0.1 Wh/m², and the cut is 2 mm of regrowth instead of 50 mm | ~1.2 kWh |

This is the single most important number in this document: **cutting little and often needs 3–10× less energy than cutting a week's growth,** which is why a 10 kg Husqvarna with three razor blades mows what a 30 kg petrol mower mows. We adopted the daily-zone schedule but kept the heavy deck; §6 revisits that.

**Slow is cheap.** Power, force, structure, bumper energy and battery all scale with speed, and a robot that has all day can go slowly. The work in §1 mostly has no deadline measured in minutes. A robot that runs ten hours a day at 0.1 m/s does the same work as one that runs one hour at 1 m/s, with 1/10 the power, a fraction of the mass, and no collision risk worth the name. The commercial robots that actually work unattended (ecoRobotix AVO, Husqvarna/EPOS, FarmDroid) are all slow, light, and often solar.

**Solar closes the loop for slow robots.** A 1.3 × 1.5 m robot roof carries about 2 m² of panel, ~300 W peak, ~1.2–1.5 kWh on a summer day. That is more than the daily energy for mowing 3 acres weekly in the razor regime (1.2 kWh per pass ÷ 7 days). A slow solar robot needs **no charging dock and no daily battery handling**, which were two of the three hardest items in our phase 2.

## 3. Where autonomy's cost comes from: infrastructure versus intelligence

A robot knows where it is and what to do either because it is clever (RTK GPS, vision, planning) or because the environment is simple (a rail, a wire, a cable, a wall). Our v1 bought cleverness: ~$1,000 of RTK and autopilot, a visibility-graph planner, failsafes for lost fixes. That is the right trade for **open ground** (lawns, fields), where fixed infrastructure would be absurd.

For **structured ground** it is the wrong trade. A market-garden bed is a 30" wide strip with permanent paths either side; a vineyard is rows at fixed pitch; a food forest has paths. On structured ground the robot's problem collapses from 2-D (x, y, heading) to **1-D (distance along the bed or row)**, and 1-D needs a wheel encoder and an end stop, not $600 of GNSS. Infrastructure also solves terrain: a robot riding on the paths, on rails laid on the bed edges, or on a cable above, never meets a stick.

Rough cost of "infrastructure" autonomy per unit area on a small farm:

| Infrastructure | Cost | Covers | Notes |
|---|---|---|---|
| Permanent bed paths (you have them anyway) | $0 | all beds | the robot's wheels ride the paths; localization by encoder |
| Lightweight rails on bed edges (conduit, angle) | ~$2–4 per metre of bed | one bed per rail pair, or rails moved between beds | FarmBot-style precision at 1/10 the cost per m² |
| Cable-driven head over a plot (4 posts, 4 winches) | ~$1,500–3,000 per plot up to ~0.3 acre | the whole plot, 3-D | no ground contact at all; wind, sag and tension limit the span; proven in research and in camera systems, not yet in farms at scale |
| Trellis wire / irrigation main as a track | reuse | orchard and vineyard rows | the row's own infrastructure carries the robot |
| Boundary wire | ~$0.5 per metre | lawn perimeter | what cheap robot mowers use instead of RTK |

The pattern: **the smaller and more structured the farm, the more infrastructure wins; the larger and more open, the more intelligence wins.** A 3-acre lawn is open ground. A quarter-acre of intensive beds is not.

## 4. The candidate form factors, scored against the work

Scores are for a small, diverse farm like ours, with the honest state of the technology in 2026. ● good · ◐ workable · ○ poor.

| Form factor | Cut (grass) | Cut (woody / harvest) | Move mass | Place | Sense | Protect (weed / pest) | Terrain | Cost to start | Maturity |
|---|---|---|---|---|---|---|---|---|---|
| **A. Wheeled tool-carrier** (our v1: 60–90 kg, RTK) | ● | ◐ with an arm, later | ● towing | ◐ | ● | ◐ | ◐ lawns, paths; not among plants | $2–3k | high (ArduPilot) |
| **B. Slow solar groundskeeper** (20–30 kg, razor deck, 0.1–0.3 m/s) | ● on maintained turf; ○ on tall growth | ○ | ○ | ○ | ● (it's always out there) | ◐ | ◐ | $1.5–2.5k | high (robot mowers) |
| **C. Swarm of tiny ground robots** (≤ 5 kg, many) | ○ | ○ | ○ | ◐ | ● | ● per-plant, non-contact tools | ○ on anything but prepared ground | $0.5–1k each, fleet $10k+ | medium; maintenance of N units is the real cost |
| **D. 1-D bed/row gantry** (rides the paths or rails, straddles a bed) | ◐ paths only | ◐ pruning with a fixed tool head | ◐ along the bed | ● | ● | ● | ● (never leaves the path) | $1–2k | medium; FarmBot/FarmDroid lineage |
| **E. Cable-driven head** over a plot | ○ | ◐ | ○ | ● | ● | ● non-contact | ● (airborne) | $2–3k per plot | low-medium |
| **F. Aerial drone** | ○ | ○ | ○ (seed only) | ◐ seeding | ● | ◐ spot-spray | ● | $0.5–2k | high for sensing |
| **G. Legged (quadruped)** | ○ | ◐ as a platform | ◐ 5–10 kg | ◐ | ● | ◐ | ● | $1.6–3k | low outdoors (water, mud, upkeep) |
| **H. Tethered ground robot** (power cable to a field point) | ● unlimited runtime | ◐ | ◐ | ◐ | ● | ◐ | ◐ | cheapest electrically | medium; tether management |
| **I. Animals + virtual fence** (sheep/geese with GPS collars) | ● orchard floors, understory, zero energy, adds fertility | ○ | ○ | ○ | ○ | ◐ pests (geese, chickens) | ● | $300/collar + animals | high (Nofence, Halter) |
| **J. Human + assist** (follow-me cart, power tools, logging camera) | ● | ● | ● | ● | ● | ● | ● | $1–2k | high |
| **K. Fixed sensing network** (cameras, soil probes, weather) | — | — | — | — | ● continuous, per-plant | enables all of the above | — | $20–50 per node | high |

Reading the table: no single row is good at everything, and the rows that are good at *cut grass* and *move mass* (A, B, I, J) are poor at *place* and *protect*, where D, E, C and K are strong. **The farm needs a system of two or three form factors with shared electronics, not one robot.**

### What each one is really for

- **A, the tool-carrier,** is the mass mover: mulch, compost, harvest crates, water, towing. Its mowing role is the first job because it's the easiest, not because it's the best mower. Keep it.
- **B, the slow solar groundskeeper,** is the best *mower* for maintained turf and could be the same chassis as A with a lighter deck and a solar roof (see §6). It cannot catch up on neglected growth; that's what the Ryobi and the Swisher are for.
- **C, swarms,** make sense where the work is per-plant, non-contact, over a large open area with no infrastructure (a 40-acre arable field) and where losing a few units doesn't matter. Nothing on a small diverse farm looks like that. The *idea* behind swarms that does transfer is **graceful degradation and incremental purchase**: buy one, learn, buy the second.
- **D, the 1-D bed gantry,** is the strongest form for the polyculture future *if the layout has beds or rows.* It is FarmBot without FarmBot's cost per square metre, it never fights terrain, it localizes with an encoder, and its tool head can carry non-contact tools (seeder, water, flame or laser weeder, camera) that work today. It would reuse everything we've built: VESC drive, ArduPilot or a much simpler controller, the safety chain, the same extrusion frame language.
- **E, the cable robot,** is the "place and protect" machine for an intensive plot. It is the most outside-the-box option that could actually be built in a season; it is also the least proven. Worth a bench-scale prototype (4 m × 4 m) before believing in it.
- **F, a drone,** is the cheapest high-value purchase on this list: a weekly orthomosaic of the whole farm at 1 cm/pixel gives weed maps, growth, irrigation faults, and it needs no building. Off-the-shelf, today.
- **G, legs,** are now cheap enough ($1,600 for a Unitree Go2) to be a sensing platform for a food forest, but not reliable enough outdoors to depend on.
- **H, a tether,** is worth remembering for fixed areas: a corded robot mower on a reel has no battery, no dock and no range limit. It isn't absurd for a 1-acre lawn next to a barn.
- **I, animals,** are the zero-energy mower for orchard floors and understory, with fertility as a by-product. A virtual fence makes them "programmable". For a polyculture farm this may be the best mower there is, and it isn't a robot.
- **J, the assisted human,** wins every task that needs judgement (harvest, pruning, planting decisions) for the next several years. A follow-me cart that carries 100 kg and never gets tired is, quietly, the robot most small farms would buy first. It is also our v1 chassis in a different mode: following a person instead of a mission.
- **K, fixed sensing,** is the layer everything else depends on, and the cheapest. It's where "polyculture robotics" should start: knowing what every bed is doing, every day.

## 5. Designing the farm for the robots

The form factor that matters most is the farm's. Permaculture layouts (keyhole beds, guilds, curved swales) are designed for hands and feet. A layout designed for **both** adds three constraints, none of which hurts the ecology:

1. **A lattice of machine-accessible paths** at a fixed width (your 8 ft paths already are one), connecting every zone, so a wheeled carrier can reach anywhere with a load.
2. **Beds or rows at a fixed pitch** where intensive work happens, so a 1-D gantry fits them all.
3. **Edges that are either mowable or grazed,** with a decision per edge: robot B, animals I, or hand tools.

"Robot-ready" is a property of the layout, and it's cheaper to design in than to engineer around.

## 6. What this changes for Orbitist v1

Most of the v1 work survives this analysis untouched: the electronics and software kit (ArduPilot, VESC drive modules, the safety chain, the RTK base, the planner and simulation) is common to A, B, D and H, and the extrusion frame is the right construction method for all of them. Three things change.

**1. The cutting regime, and with it the deck, battery and dock.** We adopted little-and-often mowing but kept a deck built for weekly cuts. If the lawns are mown daily in zones, a **razor-disc deck** (three pivoting blades on a ~250 W brushless motor, running at 25–60 W) does the job at 3–10× less energy. Consequences, from the numbers in §2:

| | v1 as designed | v1 with razor decks + solar roof |
|---|---|---|
| Blade power | 150–400 W per deck | 25–60 W per deck |
| Robot mass | 73–91 kg | ~45–55 kg |
| Daily energy, 3 acres weekly | 0.9–2.1 kWh | ~0.35–0.5 kWh |
| Energy source | 36 V 20–40 Ah pack, **charging dock** (phase 2) | ~300 W solar roof + 36 V 10–15 Ah pack; **no dock**, parks anywhere |
| Catch-up on tall growth | the deck handles it | **cannot**: Ryobi or Swisher for catch-up and spring start |
| Hazard | 21" steel blade, 60 kg | small razor blades, 50 kg: materially safer |

The cost is a dependency: the robot must keep up, every day, in season, or someone mows with the Ryobi. That is exactly the operating model of every commercial robot mower, so it's a known trade. The Ryobi deck remains the right answer if the lawns are often left to grow; the razor deck is the right answer if the robot runs daily. **This is a question about how the farm will operate, not an engineering question, and it should be decided before buying the deck or the battery.**

**2. The order of purchases.** Two of the cheapest items on the list have the highest information value and no build: a **drone** for weekly maps, and a **fixed camera or two** on the beds. They cost less than step 1 of the build and start teaching us what the polyculture robot actually needs to do. They don't delay v1.

**3. The roadmap gains a second platform.** v2 for the polyculture future should not be "v1 with an arm"; it should be the **1-D bed gantry (D)** for whatever beds exist, with non-contact tools, sharing v1's electronics. The arm stays on the roadmap for later, when manipulation catches up.

What does *not* change: v1 remains the mass mover and the first mower; its chassis, drive modules, safety chain and navigation are the right shape for open ground, and nothing above replaces them for hauling mulch across 3 acres.

## 7. Questions only the farm can answer

1. **Will the lawns be mown by the robot daily in season**, or do they sometimes go two or three weeks? (Razor deck vs Ryobi deck.)
2. **What does "polyculture" look like here in five years:** beds at a fixed pitch, an orchard with rows, a food forest without rows, or all three? (Which of D, E, I apply.)
3. **Would animals be welcome** as mowers under trees and on margins? (I is the cheapest mower in the table.)
4. **Is a solar roof acceptable** on the robot (it makes it taller and wider in appearance, and it must park in the sun)?
5. **Is there a quarter-acre plot** where a bed gantry or a cable robot could be prototyped next year without disturbing anything?

## 8. Proposed next moves

1. Decide question 1. If "daily": design the razor deck + solar roof variant in CAD (one evening: it's a lighter deck module and a roof on the existing frame) and rerun the energy, strength and bumper numbers. Step 1 of the build changes: the Ryobi test is replaced by a razor-deck power test, and the bench supply, motor and caster purchases stay the same.
2. Buy a drone (any $500–1,000 camera drone with mapping software) and fly the farm weekly from now. Store the maps in the repo's lawn files.
3. Keep steps 2 and 3 (RTK base, autopilot bench) as planned: they are common to every ground form factor.
4. Sketch the 1-D bed gantry as a v2 design note once question 2 is answered.

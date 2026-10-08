# Decision log

A short record of design decisions, so future contributors can see *why* things are the way they are. Add a row when a decision is made or revisited. Write a longer note only when a row isn't enough.

| # | Date | Decision | Status | Rationale / link |
|---|---|---|---|---|
| D1 | 2026-10-08 | Build **one robot first**; peer-to-peer docking becomes a later research track | Proposed | Mowing doesn't need a pair; the latch was the top risk. [platform-v1 §2](../design/platform-v1.md#2-what-changes-from-the-vineyard-concept-and-why) |
| D2 | 2026-10-08 | **Zero-turn layout** (2 rear hub motors + 2 front casters) for v1; frame accepts swappable drive modules (wheelchair, 4WD) | Proposed | Turf-friendly pivot turns; proven mower geometry. [§3](../design/platform-v1.md#3-chassis-options-considered) |
| D3 | 2026-10-08 | **ArduPilot Rover** on a flight controller for low-level control and GPS navigation; Pi 5 + ROS 2 added as a companion in phase 2 | Proposed | Mature skid-steer, RTK, missions, failsafes; existing community mower builds. [§6.3](../design/platform-v1.md#63-navigation-and-control) |
| D4 | 2026-10-08 | **RTK GNSS (u-blox ZED-F9P) in phase 1** | Proposed | Coverage mowing needs cm-level repeatability |
| D5 | 2026-10-08 | **VESC-class FOC controllers** by default; hoverboard + EFeru FOC as budget option | Proposed | Direct RC-PWM/CAN from ArduPilot; Hall-sensored low-speed torque |
| D6 | 2026-10-08 | **Mower is a belly-mount module**; v1 uses a salvaged 40 V-max cordless mower deck on its own battery | Proposed | Includes blade brake and height adjust; isolates blade power. [§6.2](../design/platform-v1.md#62-mower-module) |
| D7 | 2026-10-08 | Haul loads by **towing a cart from a rear hitch** rather than carrying them on deck | Proposed | Cart's wheels carry the load; tongue weight adds traction |
| D8 | 2026-10-08 | Battery swap first, then a **fixed AprilTag charging dock** in phase 2 (replaces peer-to-peer charging for lawn use) | Proposed | Simpler; ArduPilot Dock mode exists |
| D10 | 2026-10-08 | Operating model for ~3 acres: **mow in daily zones from a charging dock**; dock is the first item in phase 2 | Proposed | One 21" deck needs ~8–9 h per full pass. [platform-v1 §5](../design/platform-v1.md#5-back-of-envelope-sizing) |
| D11 | 2026-10-08 | **Own RTK base station** (ZED-F9P, position fixed with NOAA OPUS), 915 MHz radio link to the robot; NTRIP caster later | Proposed | No known correction service nearby; one base serves the whole farm |
| D12 | 2026-10-08 | Mower module from a **second used Ryobi mower** sharing the farm's existing batteries and charger | Proposed | Keeps the daily mower in service; reuses the battery ecosystem. Pending model number. |
| D13 | 2026-10-08 | **Onshape** for CAD; STEP/DXF/STL exported to `hardware/cad/` at milestones | Proposed | Browser co-editing, good frame and sheet-metal tools, free public docs suit open source |
| D9 | 2026-10-08 | Correction: "36 V" means **10S Li-ion or 12S LiFePO4** (concept report said 10S LiFePO4, which is only 32 V) | Accepted | Cell chemistry math |

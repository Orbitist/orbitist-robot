# Software

Planned layout:

| Folder | Contents |
|---|---|
| `ardupilot/` | Rover parameter files (`.param`), Lua scripts (blade interlock), SITL setup notes, mission/fence files for our lawns |
| `ros2/` | *(phase 2)* Companion-computer workspace on the Pi 5: camera, obstacle detection, dock AprilTag → `LANDING_TARGET`, coverage planning |

See [`docs/design/platform-v1.md` §6.3](../docs/design/platform-v1.md#63-navigation-and-control) for the architecture.

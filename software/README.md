# Software

| Folder | Contents |
|---|---|
| [`ardupilot/`](ardupilot/README.md) | Rover 4.6 parameter files and the blade-interlock Lua script that run on the flight controller |
| [`sim/`](sim/README.md) | Coverage planner (lawn → missions + fences) and ArduPilot SITL acceptance tests |
| [`base-station/`](base-station/README.md) | RTK base station configuration (u-blox ZED-F9P) |
| [`estop_receiver/`](estop_receiver/README.md) | Fail-safe wireless e-stop firmware (Arduino Nano) |
| `ros2/` | *(phase 2)* Companion-computer workspace on the Pi 5: camera, obstacle detection, dock AprilTag |

Architecture: [`docs/design/platform-v1.md` §6.3](../docs/design/platform-v1.md#63-navigation-and-control).

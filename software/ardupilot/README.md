# ArduPilot configuration

| Path | What |
|---|---|
| `params/orbitist-v1.param` | Baseline Rover 4.6 parameters for the real robot: frame, speeds, arming, failsafes, fence, blade relay, scripting. Values marked TUNE are set during commissioning. |
| `params/sitl-overlay.param` | Simulation-only overrides (loaded by `software/sim`). **Never load on the robot.** |
| `scripts/blade_interlock.lua` | Blade interlock + GPS pause/resume + e-stop disarm. Copy to the flight controller's SD card under `APM/scripts/`. |

## Blade control

Missions don't switch the blade relay directly. They send `MAV_CMD_DO_SEND_SCRIPT_MESSAGE` (id 1, param2 = 1 on / 0 off), and the Lua script turns relay 1 (K5) on only while **all** of these hold:

armed · AUTO mode · GPS fix ≥ `BLD_MIN_FIX` (RTK fixed) · no fence breach · tilt < 25° · e-stop loop OK · blade requested

The script also:
- disarms if the e-stop loop opens (the hardware e-stop acts independently: see `hardware/electrical`);
- pauses the mission (Hold) if the RTK fix is lost for 2 s, and resumes once it's been back for 3 s;
- forces the blade off if the script itself errors.

Its parameters (`BLD_*`) appear after the first boot with the script installed. Set `BLD_ESTOP_SRC = 1` and `BLD_ESTOP_PIN` to the GPIO wired to the ESTOP_OK optocoupler. With the pin unset, the script treats the e-stop as tripped (fail safe).

## Installing on the flight controller

1. Flash ArduPilot **Rover 4.6.x** (the version the simulation uses).
2. Mission Planner → Config → Full Parameter List → **Load from file** → `orbitist-v1.param` → Write → reboot.
3. Copy `scripts/blade_interlock.lua` to the SD card at `APM/scripts/`, reboot, and check for "Blade interlock loaded" in Messages.
4. Commission in the order given in `hardware/electrical/README.md` §8, then tune steering and speed per the [ArduPilot Rover tuning guide](https://ardupilot.org/rover/docs/rover-tuning-process.html).
5. Commit any tuned values back to `orbitist-v1.param`.

Every behaviour above is exercised in simulation by `software/sim/run_sitl.py`.

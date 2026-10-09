# Step 8: Autopilot on the robot, first missions (no blade)

*Outline. No purchases beyond step 3.*

## Do

1. Move the bench setup (step 3) into the enclosure: Pixhawk, PM02 on the main bus, RP3, telemetry radio, Nano + relay, F9P with the RTK radio; GNSS antenna on the mast with its ground plane.
2. Confirm `orbitist-v1.param` is loaded and the ESTOP_OK and blade relay pins are set.
3. Compass and accelerometer calibration away from the barn; check heading against a known bearing. If heading is noisy near the motors, this is where the second F9P for GPS-yaw gets added.
4. **Steering and speed tuning** per the ArduPilot Rover tuning guide: `CRUISE_THROTTLE` so 0.6 m/s is reached, then `ATC_STR_RAT_*`, `ATC_SPEED_*`, `NAVL1`/`PSC` as needed. Record the values in the parameter file.
5. Load the real lawn's fence and a short mission from `coverage.py`; run it in Auto in the open, supervised, with the wireless e-stop in hand. Then a full zone.
6. Measure path-tracking error from the log (`mavlogdump` or Mission Planner's log viewer); set the planner's overlap accordingly.

## Done when

- [ ] A full zone mission completes without intervention; tracking p95 ≤ 10 cm.
- [ ] All failsafes re-tested on the lawn: RC off, e-stop, GPS antenna unplugged, fence breach by driving it in Manual.

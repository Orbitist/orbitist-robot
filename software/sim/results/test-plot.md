# SITL results: test-plot.json

ArduPilot Rover 4.6.3 SITL (rover-skid model), params `software/ardupilot/params`, Lua `blade_interlock.lua`. **13/13 checks passed.**

| Scenario | Check | Result | Detail |
|---|---|---|---|
| mission | mission completes | ✅ | 2562 s sim |
| mission | path tracking while mowing, p95 ≤ 0.15 m | ✅ | p95 0.135 m, median 0.035 m, max 0.198 m |
| mission | actual cut ≥ planned − 2 % | ✅ | actual 91.9%, planned 93.6% |
| mission | blade on only while armed in AUTO | ✅ | 0 violations |
| rc_loss | RC loss → Hold and blade off within 2.5 s | ✅ | 1.60 s |
| estop | e-stop → disarmed and blade off within 0.5 s | ✅ | 0.00 s |
| restart | e-stop → disarmed and blade off within 0.5 s | ✅ | 0.10 s |
| restart | after release: stays disarmed and still | ✅ | re-armed=False, moved 0.018 m |
| gps_loss | GPS loss → blade off within 1.0 s | ✅ | 0.20 s |
| gps_loss | GPS loss → paused (Hold) within 3 s, < 2 m travelled | ✅ | after 2.2 s; travelled ≤ 1.49 m (dead-reckoned estimate) |
| gps_loss | GPS back → mission resumes by itself | ✅ | after 3.2 s |
| fence | commanded outside the fence: stays within 1.0 m of it | ✅ | max excursion 0.24 m |
| fence | blade off outside AUTO | ✅ |  |

# SITL results: sample-farm.json

ArduPilot Rover 4.6.3 SITL (rover-skid model), params `software/ardupilot/params`, Lua `blade_interlock.lua`. **4/4 checks passed.**

| Scenario | Check | Result | Detail |
|---|---|---|---|
| mission | mission completes | ✅ | 22065 s sim |
| mission | path tracking while mowing, p95 ≤ 0.15 m | ✅ | p95 0.100 m, median 0.031 m, max 0.281 m |
| mission | actual cut ≥ planned − 2 % | ✅ | actual 97.5%, planned 98.0% |
| mission | blade on only while armed in AUTO | ✅ | 0 violations |

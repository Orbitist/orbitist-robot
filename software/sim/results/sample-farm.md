# SITL results: sample-farm.json

ArduPilot Rover 4.6.3 SITL (rover-skid model), params `software/ardupilot/params`, Lua `blade_interlock.lua`. **2/4 checks passed.**

| Scenario | Check | Result | Detail |
|---|---|---|---|
| mission | mission completes | ❌ | 584 s sim | last messages: Mission: 9 WP / Mission: 10 WP / Manual recovery started / Blade OFF: not AUTO |
| mission | path tracking while mowing, p95 ≤ 0.15 m | ✅ | p95 0.068 m, median 0.032 m, max 0.126 m |
| mission | actual cut ≥ planned − 2 % | ❌ | actual 4.0%, planned 98.0% |
| mission | blade on only while armed in AUTO | ✅ | 0 violations |

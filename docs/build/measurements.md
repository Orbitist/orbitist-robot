# Measurements record

Fill these in as parts arrive. Each entry names the `params.py` field it feeds; after updating the
field, run `build.py`, `strength.py` and `drive_energy.py` in `hardware/cad/` and commit the regenerated
exports with the measurement.

## Hub motor (step 1)

| Measurement | Value | `params.py` field |
|---|---|---|
| Listing / model | | (note in commit) |
| Tire outside diameter (inflated, mm) | | `wheel_diameter` |
| Tire width (mm) | | `tire_width` |
| Motor can diameter (mm) | | `hub_diameter` |
| Axle: shoulder-to-shoulder (mm) | | `dropout_spacing` |
| Axle: width across flats (mm) | | `axle_flats` |
| Axle: diameter (mm) | | (strength.py `AXLE_D`) |
| Axle: length past each shoulder (mm) | | (check vs fork plate + torque arm + nut) |
| Flats on both ends? | yes / no | (single-sided needs a different fork) |
| Hall connector type, phase wire gauge | | — |
| Mass with tire (kg) | | `masses["hub_motor"]` |
| VESC detection: flux linkage / Kt (N·m/A) | | `drive_energy.KT` |
| VESC detection: phase resistance (Ω) | | `drive_energy.R_PHASE` |
| Bench: 30 min at ~5 N·m, can temperature (°C) | | — (pass if < 70 °C) |
| Bench: timeout-brake stop from 0.6 m/s equivalent | | `strength.BRAKE_DECEL` |

## Caster (step 1)

| Measurement | Value | `params.py` field |
|---|---|---|
| Wheel outside diameter (mm) | | `caster_wheel_diameter` |
| Wheel width (mm) | | `caster_wheel_width` |
| Swivel offset, pivot to axle (mm) | | `caster_trail` |
| Height, ground to top of plate (mm) | | `caster_height` |
| Top plate size (mm × mm) | | `caster_plate` |
| Bolt pattern (mm × mm) and hole diameter | | `caster_bolts` |
| Mass (kg) | | `masses["caster"]` |

## Ryobi deck (step 1)

| Measurement | Value | `params.py` field |
|---|---|---|
| Model number (label under the deck) | | — |
| Battery line (40 V / 80 V / 18 V) and pack sizes on hand | | — |
| Housing outline: width × length (mm) and max diameter | | `deck_housing_diameter` |
| Height, ground to top of shell at the lowest cut setting (mm) | | `deck_shell_bottom_z`, `deck_shell_height` |
| Motor housing diameter and height above the shell (mm) | | `deck_motor_diameter`, `deck_motor_height` |
| Mass without handle, wheels, battery (kg) | | `deck_mass` |
| Good hanger points (4), relative to the blade centre (mm) | | `deck_hanger_spread` and tab positions |
| Blade power test: pack Wh ÷ runtime hours = W | | `drive_energy.BLADE_W` |
| Bail switch: signal or motor current? Start button wiring | | electrical §6 |
| Runs from a bench supply without a battery handshake? | | — |
| Blade stop time after releasing the bail (s) | | — (must be < 3 s) |

## Battery and enclosure (step 7)

| Measurement | Value | `params.py` field |
|---|---|---|
| Pack size (mm) and mass | | `battery_size`, `masses["battery"]` |
| Enclosure outside size (mm) | | `ebox_size` |

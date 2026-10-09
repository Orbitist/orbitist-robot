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

## Razor disc and solar panel (step 1)

| Measurement | Value | `params.py` field |
|---|---|---|
| Disc motor model, driver model | | — |
| Motor can diameter and height (mm), shaft diameter | | `razor_motor_d`, `razor_motor_h` |
| No-load rpm at 36 V, no-load current | | — |
| Cutting power, lawn mown yesterday (W) | | `drive_energy.RAZOR_W` |
| Cutting power, one week's growth (W) | | — (catch-up limit) |
| Spin-down time after power-off (s) | | — (brake needed if > 3 s) |
| Panel: size (mm), Voc, Isc flat at midday, Isc bright overcast | | `panel_size`, `panel_w_peak` |

## Battery and enclosure (step 7)

| Measurement | Value | `params.py` field |
|---|---|---|
| Pack size (mm) and mass | | `battery_size`, `masses["battery"]` |
| Enclosure outside size (mm) | | `ebox_size` |

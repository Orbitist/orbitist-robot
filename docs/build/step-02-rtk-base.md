# Step 2: RTK base station and lawn survey

*Links and prices checked 2026-10-08. Spend: about $700–900. Time: one afternoon to build, 24 h logging, a few days waiting for the position report, one afternoon walking the lawns.*

**Goal:** a permanent GPS base station on the farm with its position fixed to about 2 cm, a rover receiver that gets centimetre fixes from it, and a map of the real lawn edges. The base serves every robot you build later. Can run in parallel with step 1.

Full procedure: [RTK base station guide](../guides/rtk-base-station.md).

## Buy

| ✓ | Item | Spec to check | Where | Price seen |
|---|---|---|---|---|
| ☐ | **2× u-blox ZED-F9P receiver boards** (base + rover) | ZED-F9P, USB and UART2 broken out; an XBee socket is handy but not required (we use SiK radios) | [ArduSimple simpleRTK2B Budget](https://www.ardusimple.com/product/simplertk2b/) (€172 each, ships from Spain) | 2 × ~$190 |
| ☐ | **Base antenna** | Multiband (L1/L2) survey-style antenna with a ground plane, 5/8" mount thread, IP66+ | [ArduSimple Budget Survey Multiband GNSS Antenna](https://www.ardusimple.com/product/survey-gnss-multiband-antenna/) (€89, TNC + 2.5 m SMA pigtail, IP66) | ~$100 |
| ☐ | **Rover antenna** | Multiband, magnetic or screw mount, SMA, 5 m cable | [u-blox ANN-MB-00 at ArduSimple](https://www.ardusimple.com/product/u-blox-gnss-multiband-antenna-ann-mb-00-ip67-bulk/) (€53.80) or [SparkFun GPS-15192](https://www.sparkfun.com/products/15192) ($109.95, same antenna) | $60–110 |
| ☐ | **Radio pair for corrections** (base → rover) | 915 MHz, transparent serial, ≥ 100 mW | [Holybro SiK Telemetry Radio V3, 915 MHz 100 mW](https://holybro.com/products/sik-telemetry-radio-v3) ($58.99; confirm the listing is the pair) | $59 |
| ☐ | **Raspberry Pi** for the base (logs the 24 h survey; later an NTRIP caster) | Pi 4 (2 GB is plenty) or Pi 5, with power supply and a 32 GB microSD | [Raspberry Pi 4 Model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) via an approved reseller | $60–90 |
| ☐ | Mast and box | 1–1.5" galvanised pipe or a wall bracket, a weatherproof box for the F9P + Pi (IP65, ~20 × 15 × 10 cm), a 5 V supply, SMA bulkhead and 5 m low-loss SMA cable if the antenna pigtail is too short | hardware store / Amazon | $60–100 |
| ☐ | For the survey cart | A wheelbarrow or garden cart, a USB power bank, your laptop | — | $0 |

**Why ArduSimple over SparkFun for the boards:** the Budget board has UART2 on a header with the right default (38400 baud, RTCM in), so the radio plugs straight in on the rover with no configuration. The configuration script in `software/base-station/` works with any ZED-F9P board over USB.

## Do

1. **Site the base** (guide §2): clear sky, rigid mount, power, as central as practical. Mount the survey antenna on the mast, run its cable into the box.
2. **Pi setup** (guide §4): install Raspberry Pi OS, `rtklib`, clone the repo, create the venv, confirm the F9P shows as `/dev/ttyACM0`.
3. **Radios** (guide §5): configure both SiK radios to 38400 baud, MAVLink framing **off**, a NETID of your choosing. Label them BASE and ROVER.
4. **Log 24 h** (guide §6): `configure_f9p_base.py raw-log`, then `str2str` for a day. Convert with `convbin` and submit to CSRS-PPP. While waiting, run **survey-in** mode so you can test the rover.
5. **Rover on the cart:** rover F9P on USB to the laptop, ANN-MB antenna on the cart on a metal plate ≥ 10 cm, ROVER radio into the F9P's UART2 header. Confirm **RTK Fixed** in u-center or with `configure_f9p_base.py PORT status`.
6. **Walk the lawns.** Push the cart along every lawn edge, around every tree and bed, and along the paths between zones, logging positions (u-center or a short Python script using `pyubx2`). Note gate widths and anything under tree cover where the fix drops to Float.
7. **When the PPP report arrives:** set the base to `fixed` with the reported latitude, longitude and ellipsoidal height; record them in `docs/guides/base-station-position.md`. **Re-walk the edges** if you mapped them while the base was in survey-in mode (the map shifts by the survey-in error).
8. **Make the lawn file:** convert the walked polygons to a `software/sim/lawns/<farm>.json` (metres east/north of an origin; the file format is in `sample-farm.json`). Run `coverage.py` on it: you now have real missions, fences and mowing-time estimates for your farm.

## Record

- The base position and antenna details in `docs/guides/base-station-position.md`.
- The lawn file, committed to `software/sim/lawns/`.
- Where RTK dropped to Float during the walk (tree cover): a note in the lawn file's `_comment`.

## Done when

- [ ] Base runs `fixed` mode from the PPP position and resumes by itself after a power cut.
- [ ] Rover reaches RTK Fixed within 2 minutes under open sky and repeats a marked point to ±2 cm an hour apart.
- [ ] `coverage.py lawns/<farm>.json` runs and produces a plan for every zone.

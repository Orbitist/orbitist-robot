# Orbitist Robot

An open-source, general-purpose farm robot that farmers can build from off-the-shelf, salvaged, and used parts, plus 3D-printed pieces and lightly fabricated metal.

**First job:** autonomously mowing the lawns on our farm (prototype built winter 2026–27).
**Later jobs:** towing small loads (mulch), carrying sensors, and a light arm for weeding and pruning.

## Status

Design, analysis, and simulation, done before buying parts. Start with:
- **[Platform v1 design](docs/design/platform-v1.md)**: what we're building and why
- **[Confidence plan](docs/design/confidence-plan.md)**: what's verified, what isn't, and the tests to run before the main purchase
- **[Simulation](software/sim/README.md)**: plan mowing and run the autopilot in software
- **[Build tutorial](docs/build/README.md)**: step-by-step assembly with purchase links, one step at a time

## Repository layout

```
docs/
  concept/     Original concept work (Sept 2026 vineyard robot design report)
  design/      Current design documents (platform-v1.md)
  decisions/   Decision log: what we chose and why
  guides/      How-to guides (RTK base station setup)
  build/       Step-by-step build tutorial with purchase links and a measurements record
hardware/
  bom/         Bills of materials (CSV) and ordering plan
  cad/         Parametric CAD model, renders, cutting DXFs, strength check
  electrical/  Power distribution, e-stop safety chain, wiring, commissioning tests
software/
  ardupilot/       Autopilot parameters + blade-interlock Lua script
  sim/             Coverage planner + ArduPilot SITL acceptance tests
  base-station/    RTK base (u-blox ZED-F9P) configuration script
  estop_receiver/  Fail-safe wireless e-stop firmware (Arduino)
```

## License

Hardware: [CERN-OHL-W-2.0](LICENSES/CERN-OHL-W-2.0.txt) · Software: [Apache-2.0](LICENSES/Apache-2.0.txt) · Docs: [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt). See [LICENSE.md](LICENSE.md) for what applies where.

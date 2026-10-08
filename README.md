# Orbitist Robot

An open-source, general-purpose farm robot that farmers can build from off-the-shelf, salvaged, and used parts, plus 3D-printed pieces and lightly fabricated metal.

**First job:** autonomously mowing the lawns on our farm (prototype built winter 2026–27).
**Later jobs:** towing small loads (mulch), carrying sensors, and a light arm for weeding and pruning.

## Status

Design / brainstorm. Start with the **[Platform v1 design](docs/design/platform-v1.md)**.

## Repository layout

```
docs/
  concept/     Original concept work (Sept 2026 vineyard robot design report)
  design/      Current design documents (platform-v1.md)
  decisions/   Decision log: what we chose and why
  guides/      How-to guides (RTK base station setup)
hardware/
  bom/         Bills of materials (CSV) and ordering plan
  cad/         Parametric CAD model, renders, cutting DXFs, strength check
  electrical/  Power distribution, e-stop safety chain, wiring, commissioning tests
software/
  base-station/    RTK base (u-blox ZED-F9P) configuration script
  estop_receiver/  Fail-safe wireless e-stop firmware (Arduino)
```

## License

Hardware: [CERN-OHL-W-2.0](LICENSES/CERN-OHL-W-2.0.txt) · Software: [Apache-2.0](LICENSES/Apache-2.0.txt) · Docs: [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt). See [LICENSE.md](LICENSE.md) for what applies where.

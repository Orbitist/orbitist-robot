# Hardware

| Folder | Contents |
|---|---|
| `bom/` | Bills of materials as CSV (one file per platform version) and the [ordering plan](bom/ordering-plan.md) (what to buy when). Prices are rough estimates as of Oct 2026. |
| `cad/` | [Parametric build123d model](cad/README.md) of the frame: STEP, renders, DXF plates, cut list, mass/CG report |
| `electrical/` | *(planned)* Wiring diagram, kill-chain schematic, connector pinouts. |

Design rationale lives in [`docs/design/platform-v1.md`](../docs/design/platform-v1.md).

**v1 BOM rough totals (new parts):**
- Core mowing robot + RTK base station (phases 0–1c, without optional GPS-yaw): **~$2,420**
- Everything listed, including GPS-yaw, second deck, hitch, charging dock, and phase-2 compute and sensors: **~$3,300**

The RTK base (~$280) is a one-time farm asset shared by every future robot. The biggest savings come from salvaged parts: a hoverboard board instead of VESCs (−$135), a used e-bike pack, and mower casters from a junked rider. The Ryobi batteries and charger are already on hand.

Licensed under [CERN-OHL-W-2.0](../LICENSES/CERN-OHL-W-2.0.txt).

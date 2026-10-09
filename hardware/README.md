# Hardware

| Folder | Contents |
|---|---|
| `bom/` | Bills of materials as CSV (one file per platform version) and the [ordering plan](bom/ordering-plan.md) (what to buy when). Prices are rough estimates as of Oct 2026. |
| `cad/` | [Parametric build123d model](cad/README.md) of the frame: STEP, renders, DXF plates, cut list, mass/CG report |
| `electrical/` | [Power distribution, e-stop safety chain, signal wiring, fuses, commissioning tests](electrical/README.md) |

Design rationale lives in [`docs/design/platform-v1.md`](../docs/design/platform-v1.md).

**v1 BOM rough totals (new parts):**
- Core mowing robot (razor deck + solar roof) + RTK base station (phases 0–1c, without optional GPS-yaw): **~$3,400**
- Everything listed, including GPS-yaw, hitch, and phase-2 compute and sensors: **~$4,040**

Analyses that regenerate from the CAD parameters: [strength](cad/exports/strength-report.md), [drive & energy](cad/exports/drive-energy-report.md), [layout & clearances](cad/exports/report.md).

The RTK base (~$280) is a one-time farm asset shared by every future robot. There is no charging dock: the solar roof keeps the robot charged (D28). The biggest savings come from salvaged parts: a hoverboard board instead of VESCs (−$135), a used e-bike pack, and used rigid solar panels.

Licensed under [CERN-OHL-W-2.0](../LICENSES/CERN-OHL-W-2.0.txt).

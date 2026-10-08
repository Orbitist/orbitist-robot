# Hardware

| Folder | Contents |
|---|---|
| `bom/` | Bills of materials as CSV (one file per platform version). Prices are rough estimates as of Oct 2026. |
| `cad/` | *(planned)* Frame, dropout plates, mounts. Source files plus exported STEP/STL/DXF. |
| `electrical/` | *(planned)* Wiring diagram, kill-chain schematic, connector pinouts. |

Design rationale lives in [`docs/design/platform-v1.md`](../docs/design/platform-v1.md).

**v1 BOM rough totals (new parts):**
- Core mowing robot (phases 1a–1c, without optional GPS-yaw or RTK base): **~$2,070**
- Everything listed, including optional GNSS, hitch, and phase-2 compute and sensors: **~$3,000**

The biggest savings come from salvaged parts: a hoverboard board instead of VESCs (−$135), a used e-bike pack, mower casters from a junked rider, and free CORS corrections instead of our own base. These could bring the core to roughly $1,500.

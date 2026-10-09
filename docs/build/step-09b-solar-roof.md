# Step 9b: Solar roof

*Outline. Links added when we reach it. See D28.*

## Buy (spec)

| Item | Spec | Qty |
|---|---|---|
| Solar panels | semi-flexible, ~100–120 W, ~1.05 × 0.54 m, bypass diodes (one bought in step 1) | 1 more |
| MPPT charge controller | **boost** type for a 36 V-class battery from ~18–36 V panel input (Genasun GVB-8 class), Li-ion/LiFePO4 profile to suit the pack | 1 |
| Roof extrusion | 30x30: 4 posts + 4 rails per the [cut list](../../hardware/cad/exports/cut-list.md); corner brackets | kit |
| Backing sheet | 1.5 mm aluminium or 3 mm twin-wall polycarbonate, frame size | 1 |
| Hinges + gas strut or prop | so the roof lifts for access to the battery and electronics | 2 + 1 |
| Panel fixing | VHB tape or edge clips, MC4 extension, gland into the enclosure | — |

## Do

1. Bolt the posts to the side rails at the corners, the roof rails on top; square it; fit the backing sheet.
2. Mount the panels, wire them in series (or parallel, to suit the MPPT's input range) to the MPPT; MPPT output to the battery through its own 15 A fuse.
3. Move the GNSS antenna onto the stub on the rear roof rail (ground-plane disc under it) and the e-stop beside it; re-run the GPS and e-stop checks.
4. Log a full sunny day parked: the pack should reach full by early afternoon.

## Done when

- [ ] Panel output at midday within 20 % of the step-1 measurement; MPPT charging at 36–42 V.
- [ ] Antenna still reaches RTK Fixed on the roof; e-stop reachable from behind.

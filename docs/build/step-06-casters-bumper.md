# Step 6: Casters and bumper

*Outline. Links added when we reach it.*

## Buy (spec)

| Item | Spec | Qty |
|---|---|---|
| Second caster | identical to step 1's | 1 |
| Caster spacers | per the thickness in `report.md` ("Needs a N mm spacer"), steel or aluminium | 2 |
| Bumper bar | 30×60 extrusion offcut (length per CAD), or 25×50 aluminium tube | 1 |
| Bumper arms | Ø20 steel or aluminium tube, 2 pcs | 2 |
| Guide blocks | UHMW or Delrin block 60×50×50 bored Ø21, or 3D-printed PETG | 2 |
| Return springs | compression, ~Ø30 OD, free length per CAD, 2–4 N/mm | 2 |
| Microswitches | roller-lever, **NC contact**, IP67 if available | 2 |
| Closed-cell foam | 50 mm, bar length | 1 |

## Do

1. Bolt the caster plates to the front corners (rail bottom slot + front member bottom slot), then the casters with spacers, M8 from below.
2. Make the guide blocks, bolt them under the front member at y = ±300, fit the arms, collars, springs and the bar.
3. Mount the switches on the guide blocks so the collar presses the lever after ~8 mm of travel; wire them in series (NC) on a lead to the future e-stop loop.
4. Push test: the bar must move freely, return fully, and both switches open within the first 10 mm.

## Done when

- [ ] Robot rolls on all four wheels, casters swivel freely through 360° without touching the bumper hardware.
- [ ] Bumper trips both switches and returns.

# Step 4: Frame

*Outline. Purchase links get added and checked when step 1 is done (the plate drawings depend on the measured motor axle and caster).*

**Goal:** the bare frame, square and bolted, with gussets, the plates cut, standing on blocks.

## Buy (spec)

| Item | Spec | Qty | Notes |
|---|---|---|---|
| 30×30 T-slot extrusion, slot 8 | 6-series (Misumi HFS6-3030 class), cut to length | per [cut list](../../hardware/cad/exports/cut-list.md) | Misumi US cuts to length for free on configurable part numbers (HFS6-3030-[length]); their US pages were not reachable from here to verify pricing, so get a quote |
| 30×60 T-slot extrusion, slot 8 | HFS6-3060 class | per cut list | same |
| Cast inside corner brackets, 30-series | with M6 bolts and T-nuts | ~24 | 2 per cross-member end + battery rails |
| Slot-8 T-nuts and M6/M8 bolts | stainless, assorted 12–20 mm | 100+ | buy a kit |
| Cut plates | from [`hardware/cad/exports/*.dxf`](../../hardware/cad/exports): fork side plates (6 mm steel ×4), fork top plates (8 mm ×2), saddle tabs, torque arms (5 mm ×4), gussets (5 mm aluminium ×8), caster plates (8 mm steel ×2) | — | Upload the DXFs to SendCutSend or a local laser/water-jet shop. Order **only after** step 1's measurements are in `params.py` |
| Chop-saw blade for aluminium (if cutting at home) | non-ferrous, negative rake | 1 | or have Misumi cut everything |

## Do

1. Lay out the side rails and cross members per the [top view](../../hardware/cad/exports/platform-v1-single-top.png); member positions are in `params.py` (`cross_member_x`).
2. Square the frame on a flat floor (equal diagonals), fit corner brackets, then the gussets at the two drive-adjacent members, torque the bolts and mark them with paint.
3. Fit the battery support rails and the saddle-tab fork top plates (without motors) to check the plate fit against the real extrusion.
4. Deburr every cut; tap the caster plates M8.

## Done when

- [ ] Diagonals equal within 2 mm; all joints bolted, torque-striped.
- [ ] Every cut plate test-fits its location.

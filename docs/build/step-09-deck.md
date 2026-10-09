# Step 9: Razor deck module and supervised mowing

*Outline. Links added when we reach it. Revised 2026-10-09 for the razor-disc deck (D27).*

## Buy (spec)

| Item | Spec | Qty |
|---|---|---|
| Disc motors + drivers | identical to step 1's | 3 more (4 total) |
| Discs | `razor-disc.dxf`, 3 mm aluminium | 3 more |
| Razor blades + shoulder screws | robot-mower razor blades; M6 × 10 shoulder screws | 12 + spares |
| Deck plate | 3 mm aluminium per CAD outline (DXF to be exported once step 1 fixes the motor hole pattern) | 1 |
| Skirt | 6 mm HDPE strip, 70 mm tall, bent/joined around the plate | ~3.2 m |
| Hangers | M8 threaded rod, nuts, slot-8 drop-in T-nuts | 4 sets |
| Anti-scalp rollers | 60 mm wide, Ø60 | 2 |
| Blade enable wiring | all four drivers' enable/PWM lines switched together by K5; 2-core shielded cable | — |

## Do

1. Drill the plate for the motors, bolt the motors on top, discs underneath, blades on; fit the skirt and rollers.
2. Hang the deck from the members at x = 215 and x = 600 on the four rods; set the blade height to 50 mm with the rods, level front-to-back and side-to-side.
3. Wire the drivers: 36 V from the fused motor bus; enable lines through K5 (the blade relay) so the Lua interlock and the hardware e-stop both control all four discs. Set each driver's speed to ~3,000 rpm.
4. Electrical README §8 steps 6 and 7: disc stop time on every e-stop path, bumper push at 0.6 m/s.
5. **Catch-up cut first:** mow every zone once with the Ryobi so the razors only see regrowth.
6. First supervised mow: a small open zone, wireless e-stop in hand, nobody else in the zone. Then the full zone list, daily.

## Done when

- [ ] All four discs stop within 3 s on every e-stop path; discs never run outside AUTO (`BLADE` named value in the logs).
- [ ] Two weeks of daily mowing with no uncut strips and the battery never below 30 % at dawn (solar keeping up).

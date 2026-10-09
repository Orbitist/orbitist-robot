# Step 9: Deck module and supervised mowing

*Outline. Links added when we reach it.*

## Buy (spec)

| Item | Spec | Qty |
|---|---|---|
| Deck hanger hardware | M8 threaded rod, nuts, slot-8 drop-in T-nuts, anti-scalp rollers if the deck's own wheels can't be reused | kit |
| Blade relay / contactor | per step 1's T1 result | 1 |
| Ryobi battery adapter (if the deck runs from the robot pack) | printed/commercial 40 V adapter + 36→40 V boost or direct, per T1 | 1 |
| Deck interlock wiring | 2-core shielded cable, Deutsch or Anderson connector so the deck module unplugs | — |

## Do

1. Fit the four hanger tabs to the deck (positions per CAD and the T1 measurements), hang the deck from the cross members, set the cut height so the deck sits level ~ the Ryobi's middle setting with the rollers 15 mm off the ground.
2. Wire the bail/start circuit through the blade relay; wire the relay coil from the SAFE 12 V rail through the autopilot's relay output.
3. Electrical README §8 steps 6 and 7 (blade stop time, bumper push at speed).
4. First supervised mow: a small open zone, wireless e-stop in hand, nobody else in the zone. Then the full zone list.

## Done when

- [ ] Blade stops < 3 s on every e-stop path; blade never runs outside AUTO (check logs: `BLADE` named value).
- [ ] One full zone mown with no missed strips; twin-deck decision made from the measured hours.

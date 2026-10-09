# Step 7: Power and safety electrical

*Outline. Links added when we reach it. Battery size is decided by step 1's blade test.*

Design and parts list: [`hardware/electrical/README.md`](../../hardware/electrical/README.md). Everything marked **safety** must meet the stated rating.

## Buy (spec)

| Item | Spec | Qty |
|---|---|---|
| Battery | 36 V-class pack (10S Li-ion or 12S LiFePO4), **size per step 1 decision**, BMS ≥ 30 A continuous, with charger | 1 (or 2) |
| **safety** Main fuse + holder | MRBF or Class T, 40 A, ≥ 58 V DC | 1 |
| Battery disconnect switch | ≥ 48 V DC, ≥ 50 A | 1 |
| **safety** Main contactor | 12 V coil, ≥ 60 V DC, ≥ 50 A continuous (Albright SW60 / TE LEV100 class) | 1 |
| Precharge relay + resistor | 12 V automotive relay; 47 Ω 10 W wirewound | 1 + 1 |
| Timer relay modules | 12 V on-delay (1.5 s) and off-delay (1.0 s) | 1 + 1 |
| Signal relay | 12 V DPDT, gold contacts (K4) | 1 |
| Blade relay | per the T1 bench test (small relay or DC contactor) | 1 |
| DC-DC converters | 36→12 V 10 A and 36→5 V 5 A, input ≥ 60 V | 1 + 1 |
| **safety** Fuse block and fuses | 58 V DC rated, 2–25 A assortment | 1 |
| E-stop | 22 mm mushroom, twist-release, NC block | 1 |
| Optocoupler module | 12 V in → 3.3 V out (ESTOP_OK) | 1 |
| Enclosure | IP65 polycarbonate ~300×220×150, cable glands, DIN rail | 1 |
| Wire and connectors | 10/12 AWG silicone, XT90s, ferrules, heat-shrink, labels | kit |

## Do

Follow the electrical README: §1 power distribution, §2 safety chain, §3 signal wiring, then **§8 commissioning tests in order**, wheels off the ground and no blade.

## Done when

- [ ] All eight commissioning tests pass and are logged in the electrical README's test record.

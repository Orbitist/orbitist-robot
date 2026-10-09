# Step 5: Drive modules

*Outline. Links added when we reach it.*

**Goal:** both wheels on the frame, each driven by its own VESC, driving under radio control from the transmitter through the Pixhawk (Manual mode).

## Buy (spec)

| Item | Spec | Qty |
|---|---|---|
| Second hub motor | identical listing to step 1's | 1 |
| Second VESC | identical to step 1's | 1 |
| Torque-arm and fork fasteners | M8 × 20 class 8.8 (fork plates), M6 × 16 (torque arms, saddle tabs), nyloc nuts, torque washers | kit |
| Phase and Hall extension leads | 12 AWG silicone, 3 m; 6-pin Hall extension | 2 sets |
| 36 V test pack or bench supply at 36 V, 10 A | the real battery arrives in step 7; a used e-bike pack or the bench supply (current-limited) is enough to drive on blocks | — |

## Do

1. Assemble each fork: side plates, top plate, saddle tabs; slide the axle in with the flats seated, fit the torque arm on the outboard plate, nuts torqued.
2. Bolt the forks under the side rails at x = 0 (into the bottom slot and both side slots).
3. Mount both VESCs in the electronics position (the enclosure comes in step 7; a temporary plate is fine), set them up identically to step 1 (motor detection again for the second motor), set the PPM app to **PID speed** mode with ~2 m/s full scale.
4. Pixhawk outputs 1 and 3 → VESC PPM inputs (through the K4 relay later; direct for now). Set VESC PPM centre/endpoints from the Pixhawk's output range.
5. On blocks: Manual mode, arm, throttle: both wheels turn the same direction at the same speed, steering turns them opposite. Fix any reversed motor in VESC Tool (invert motor direction), never by swapping phase wires at random.
6. On the ground, in the barn: drive straight, pivot, stop. Check the `MOT_SAFE_DISARM` behaviour: disarming stops the pulses and the VESCs brake.

## Done when

- [ ] Robot drives straight at 0.6 m/s under RC with matched wheel speeds.
- [ ] Disarm brakes both wheels within 0.2 s.

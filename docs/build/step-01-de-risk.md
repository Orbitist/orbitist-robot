# Step 1: De-risking tests

*Links and prices checked 2026-10-08; revised 2026-10-09 for the razor-disc deck and solar roof (D27, D28). Spend: about $450–600. Time: a weekend, plus waiting for shipping.*

**Goal:** measure the three things the rest of the design depends on before the main purchase: how much power one razor disc draws cutting the farm's grass (and what a solar panel yields flat on the roof), whether a cheap hub motor can run at mowing speed without overheating, and the exact dimensions of the motor and caster that the cut plates are drawn around. Everything bought here is used in the final robot.

## Buy

| ✓ | Item | Spec to check | Where | Price seen |
|---|---|---|---|---|
| ☐ | **One razor-disc cutting unit** | Brushless motor, 36 V class (24–36 V nominal, no-load 2,500–3,500 rpm), ≥ 100 W, with a matching BLDC driver that takes a PWM/enable signal (robot-mower blade-motor replacements and generic "36 V 350 W BLDC driver" boards both work); one disc cut from [`razor-disc.dxf`](../../hardware/cad/exports/razor-disc.dxf) (3 mm aluminium, SendCutSend or hand-cut) with **three standard robot-mower razor blades** and M6 shoulder screws; a motor hub/shaft adapter to suit the motor | Links to be checked when ordering; blades: any "Automower-compatible razor blades" pack (~$10 per 9) | $60–120 |
| ☐ | **One solar panel** | Semi-flexible, ~100–120 W, ~1.05 × 0.54 m, with bypass diodes; plus a 36 V-battery **boost MPPT** charge controller later (step 7) | Links to be checked when ordering | $90–150 |
| ☐ | **One 10" hub motor** | Brushless, gearless, **Hall sensors** (5 thin wires + 3 thick), pneumatic 10×2.5–3" tire, **axle with flats on both sides** (two dropouts), 36–48 V winding, 350–1000 W. A 48 V motor is fine on our 36 V pack: it just runs slower and makes more torque per amp, which suits mowing. Avoid *geared* motors unless the listing confirms **no freewheel clutch** (the robot brakes and holds position with the motors). | [Wheelway eBay store](https://www.ebay.com/str/wheelway) (10" scooter motors; ask the seller for the axle drawing), or AliExpress search "10 inch hub motor 36V hall sensor". A US-stock but pricier option: [VXB 10" hub motor kit](https://vxb.com/products/10-inch-wheel-hub-motor-assembly-delivering-badass) ($329; confirm axle type first). | $100–240 |
| ☐ | **One VESC controller** | VESC 6 hardware, ≥ 60 V input, Hall sensor port, PPM input, CAN. | [Flipsky 75100 Pro](https://flipsky.net/products/flipsky-75100-pro-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller) ($89, 14–84 V, 100 A, Hall port, PPM/UART/CAN). Budget: the plain [Flipsky 75100](https://flipsky.net/products/flipsky-75100-75v-100a-single-esc-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller) ($65). Note Flipsky's warning: disable the phase filter in VESC Tool on firmware ≥ 5.3. | $65–89 |
| ☐ | **One 10" pneumatic swivel caster, plate mount** | ≥ 300 lb, plate ~4" × 4.5". | [Harbor Freight Haul-Master 10" pneumatic swivel caster, SKU 63799](https://www.harborfreight.com/10-in-pneumatic-swivel-caster-63799.html) ($19.99, 300 lb, bolt pattern 3" × 3-3/8"). | $20 |
| ☐ | **Bench power supply** | 0–60 V, ≥ 5 A, with **adjustable current limit** (constant-current mode). Used for every first power-up in this project. | [Vetco 60 V 5 A lab supply](https://vetco.net/products/vupn2187_60v_5a_adjustable_bench_top_lab_dc_power_supply) ($190; check stock). Cheaper generic 60 V 5 A units (~$70–100) are fine if they state CC mode. | $70–190 |
| ☐ | DC clamp meter (optional but useful) | Reads DC amps, ≥ 40 A | Any brand with "DC current" clamp (e.g. UNI-T UT210E class) | $30–60 |
| ☐ | 3-phase wiring bits | XT60 pair, 12 AWG silicone wire, JST-PH or the Hall connector your motor uses, crimper | Amazon / local | $20 |
| ☐ | Digital calipers (if the shop doesn't have them) | 150 mm | any | $15–25 |

Also needed, no purchase: a laptop with [VESC Tool](https://vesc-project.com/vesc_tool) (free), a bathroom scale, a stopwatch, a tape measure, something to load the motor (see T3), and the farm's existing Ryobi mower for the catch-up cut before the razor test.

## Do

### T1. One razor disc on the lawn, and one panel in the sun

1. **Build the test disc.** Cut the disc from `razor-disc.dxf`, fit three razor blades on M6 shoulder screws (they must swing freely), mount it on the motor with the hub adapter, mount the motor on a scrap board with a skirt of plywood around the disc for a guard, and set the blades 50 mm above the ground on two scrap wheels or runners. Wire the driver to the bench supply at 36 V, current limit 3 A at first.
2. **Spin-up check,** blades off: it should reach ~3,000 rpm; log the no-load current. Then with blades, in the air.
3. **Cut the lawn** (eye protection; nobody near): push the rig at walking pace over a lawn mown yesterday with the Ryobi, then over a strip left for a week. Log the current from the bench supply or clamp meter. Watts = 36 × amps. Expect 10–20 W on the daily strip; note what the weekly strip needs and whether the blades fold back.
4. **Stop time:** cut the power; time how long the disc spins. If more than 3 s, note it: the driver needs a brake input, or a small blade brake.
5. **Panel:** lay the panel flat in the sun at midday, short it through the clamp meter for the short-circuit current and read the open-circuit voltage; the product (× 0.75) approximates its real output flat on the roof. Repeat on a bright overcast day.

### T1b. The reel alternative (D31): one push reel mower on the same strips

Same afternoon, same lawn as T1. Borrow or buy one used 16–20" push reel mower (~$0–130).
1. Pick up sticks on a 100 m strip mown yesterday with the Ryobi, and leave a 100 m strip three days old.
2. Push the reel mower at 0.6 m/s (a slow walk; time 10 m in ~17 s) with a luggage scale hooked between your hand and the handle. Log the steady pull force on each strip.
3. Count jams and uncut stalks per 100 m. Note the cut quality against the razor-disc strip.
4. Weigh the mower, and the reel cartridge + wheels alone if you can strip it.

**Decision rule:** reel gang if pull force < 60 N per unit, fewer than one jam per 500 m after the stick pick-up, and a clean cut; otherwise razor discs. Either way, record the numbers in `measurements.md`.

### T3. One motor on the bench

1. **Measure the motor** before anything else: tire diameter and width, axle shoulder-to-shoulder, width across the flats, axle diameter, protrusion past each shoulder. These numbers set the fork plates and torque arms.
2. **Wire the VESC:** battery leads to the bench supply (set 36 V, current limit 2 A for the first power-up, raise later), three phase wires to the motor, the Hall connector to the sensor port. Install VESC Tool and connect over USB.
3. **Motor detection** (VESC Tool → FOC → Detect). Record flux linkage (→ torque constant), phase resistance, and the Hall table. Set **motor current max 50 A, battery current max 14 A**, timeout brake current 20 A, PPM timeout 100 ms.
4. **Low-speed check:** with the wheel off the ground, run at 45 rpm (our mowing speed) from VESC Tool's keyboard control. It should turn smoothly without cogging; that's what the Hall sensors are for.
5. **Thermal check:** load the motor to about 5 N·m for 30 minutes. Easiest rig: clamp the axle in a vise, wrap a strap around the tire with a known weight hanging from it (5 N·m ≈ 4 kg at the tire's 127 mm radius), and run at 45 rpm. Read the motor temperature every 5 minutes (VESC Tool shows it if the motor has a sensor; otherwise an IR thermometer on the can). **Pass:** under 70 °C and still rising slowly. **Fail:** climbs past 80 °C. A fail means we switch to a geared or wheelchair motor before buying the second one; the frame accepts either.
6. **Brake test:** spin the wheel to 45 rpm, then unplug the PPM signal (or stop sending it). The VESC must brake within its 100 ms timeout and hold the wheel.

### T4. Caster

Measure the top plate, bolt pattern and hole size, overall height, wheel diameter and width, and the swivel offset. Spin the swivel: it should be smooth with no lift.

## Record

Write everything into [`measurements.md`](measurements.md), then update `hardware/cad/params.py` and `drive_energy.py` and regenerate (`build.py`, `strength.py`, `drive_energy.py`). Commit the measurements and the regenerated exports together.

## Done when

- [ ] Disc cutting power and panel yield are measured numbers, not ranges; reel pull force and jam rate recorded (T1b).
- [ ] The motor ran 30 minutes at mowing load and stayed under 70 °C.
- [ ] The motor brakes and holds when the signal stops.
- [ ] `params.py` has the real axle, tire and caster dimensions, and the DXFs regenerated.
- [ ] Decision recorded in the [decision log](../decisions/README.md): drive motor type confirmed (or changed); pack size for step 7 (10 or 15 Ah); disc count (4, or 3 if power allows a bigger disc), or the reel gang instead (D31).

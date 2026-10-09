# Step 1: De-risking tests

*Links and prices checked 2026-10-08. Spend: about $450–600. Time: a weekend, plus waiting for shipping.*

**Goal:** measure the three things the rest of the design depends on before the main purchase: how much power the mower blade really draws, whether a cheap hub motor can run at mowing speed without overheating, and the exact dimensions of the motor and caster that the cut plates are drawn around. Everything bought here is used in the final robot.

## Buy

| ✓ | Item | Spec to check | Where | Price seen |
|---|---|---|---|---|
| ☐ | **Used Ryobi 40 V 21" mower** | Same battery line as the farm's batteries (check the label on a battery: *40V* or *40V HP*). Prefer a **brushless** 21" model. Bare tool is fine. Current new tool-only model for reference: [RY40HPLM01B at Home Depot](https://www.homedepot.com/p/RYOBI-40V-HP-Brushless-21-in-Cordless-Battery-Walk-Behind-Self-Propelled-Lawn-Mower-Tool-Only-RY40HPLM01B/332712843) ($409 new). | Facebook Marketplace / Craigslist, search "Ryobi 40V mower" | $50–150 used |
| ☐ | **One 10" hub motor** | Brushless, gearless, **Hall sensors** (5 thin wires + 3 thick), pneumatic 10×2.5–3" tire, **axle with flats on both sides** (two dropouts), 36–48 V winding, 350–1000 W. A 48 V motor is fine on our 36 V pack: it just runs slower and makes more torque per amp, which suits mowing. Avoid *geared* motors unless the listing confirms **no freewheel clutch** (the robot brakes and holds position with the motors). | [Wheelway eBay store](https://www.ebay.com/str/wheelway) (10" scooter motors; ask the seller for the axle drawing), or AliExpress search "10 inch hub motor 36V hall sensor". A US-stock but pricier option: [VXB 10" hub motor kit](https://vxb.com/products/10-inch-wheel-hub-motor-assembly-delivering-badass) ($329; confirm axle type first). | $100–240 |
| ☐ | **One VESC controller** | VESC 6 hardware, ≥ 60 V input, Hall sensor port, PPM input, CAN. | [Flipsky 75100 Pro](https://flipsky.net/products/flipsky-75100-pro-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller) ($89, 14–84 V, 100 A, Hall port, PPM/UART/CAN). Budget: the plain [Flipsky 75100](https://flipsky.net/products/flipsky-75100-75v-100a-single-esc-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller) ($65). Note Flipsky's warning: disable the phase filter in VESC Tool on firmware ≥ 5.3. | $65–89 |
| ☐ | **One 10" pneumatic swivel caster, plate mount** | ≥ 300 lb, plate ~4" × 4.5". | [Harbor Freight Haul-Master 10" pneumatic swivel caster, SKU 63799](https://www.harborfreight.com/10-in-pneumatic-swivel-caster-63799.html) ($19.99, 300 lb, bolt pattern 3" × 3-3/8"). | $20 |
| ☐ | **Bench power supply** | 0–60 V, ≥ 5 A, with **adjustable current limit** (constant-current mode). Used for every first power-up in this project. | [Vetco 60 V 5 A lab supply](https://vetco.net/products/vupn2187_60v_5a_adjustable_bench_top_lab_dc_power_supply) ($190; check stock). Cheaper generic 60 V 5 A units (~$70–100) are fine if they state CC mode. | $70–190 |
| ☐ | DC clamp meter (optional but useful) | Reads DC amps, ≥ 40 A | Any brand with "DC current" clamp (e.g. UNI-T UT210E class) | $30–60 |
| ☐ | 3-phase wiring bits | XT60 pair, 12 AWG silicone wire, JST-PH or the Hall connector your motor uses, crimper | Amazon / local | $20 |
| ☐ | Digital calipers (if the shop doesn't have them) | 150 mm | any | $15–25 |

Also needed, no purchase: a laptop with [VESC Tool](https://vesc-project.com/vesc_tool) (free), a bathroom scale, a stopwatch, a tape measure, something to load the motor (see T3).

## Do

### T1. Ryobi blade-power test and teardown

1. **Mow with it.** On a typical lawn on the farm, mow normally with a fully charged pack of known size (e.g. 6 Ah). Time it until the pack is empty. Blade power ≈ pack Wh ÷ hours (a 40 V 6 Ah pack is 216 Wh nominal, ~200 usable). Do this twice if you can: once on short grass, once on grass that's a week overgrown. If you bought the clamp meter, clip it around one battery lead instead and read the current while mowing: W = V × A.
2. **Strip it.** Remove the handle, wheels and bag. Weigh the deck. Measure the housing outline, the height from ground to the shell top at the lowest cut setting, and the motor housing. Photograph the underside.
3. **Find the switches.** Open the handle's switch housing. Identify the bail lever switch and the start button, and how they reach the mower's controller (a thin signal cable, or heavy wires carrying motor current). With the pack in and the blade *removed*, use the meter to measure the current through the bail switch while running.
4. **Battery handshake test.** With the blade removed and the deck on a bench, connect the bench supply to the battery terminals (observe polarity; 40 V, current limit 3 A) through a printed or cut adapter, and try to start it. If it runs, the deck can later run from the robot's pack. If it refuses, it needs the real pack present.
5. **Blade brake.** Refit the blade, guard the deck, run it, release the bail, and time the stop. Must be under 3 s.

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

- [ ] Blade power is a measured number (W), not a range.
- [ ] The motor ran 30 minutes at mowing load and stayed under 70 °C.
- [ ] The motor brakes and holds when the signal stops.
- [ ] `params.py` has the real axle, tire and caster dimensions, and the DXFs regenerated.
- [ ] Decision recorded in the [decision log](../decisions/README.md): motor type confirmed (or changed), and the battery size for step 7 (20 Ah if the deck stays on Ryobi packs; 30–40 Ah or two packs if it will run from the robot).

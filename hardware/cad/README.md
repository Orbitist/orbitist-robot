# CAD: platform v1 frame (code-based, build123d)

The robot is modelled in Python with [build123d](https://github.com/gumyr/build123d) (OpenCascade kernel). `params.py` holds every dimension in one place. `build.py` regenerates the STEP files, renders, flat-plate DXFs, cut list, and an engineering report.

![Twin-deck layout, isometric](exports/platform-v1-twin-iso.png)

## Files

| File | What it is |
|---|---|
| `params.py` | **All dimensions and masses.** Values marked `ESTIMATE` are typical sizes for parts we haven't bought; replace them with measurements. |
| `model.py` | Assembles the parts and re-exports the helpers the analyses use |
| `parts/common.py` | T-slot extrusion profile (30-series, slot 8), hex bolts and nuts, rods, colours by material |
| `parts/plates.py` | **2D outlines of every cut plate** (fork side plate, torque arm, gusset, caster plate). The 3D model extrudes them and the DXFs are exported from them, so they can't drift apart. |
| `parts/frame.py` | Rails and members with real T-slot sections, cast corner brackets, top-face gussets, battery support rails, all bolts |
| `parts/drive.py` | Hub motors (treaded tire, rim, can, side covers, flatted axle), bolt-on forks with saddle tabs, torque arms, axle nuts, motor cables |
| `parts/casters.py` | Plate-mount swivel casters (top plate with bolt pattern, raceway, yoke legs, axle, hub) on the steel corner plates |
| `parts/deck.py` | Ryobi-class deck shells (revolved pan with skirt and rib), blades with lift wings, finned motor housings, anti-scalp rollers, four threaded-rod hangers per deck with drop-in slot blocks |
| `parts/razor_deck.py` | Razor-disc deck: plate cut back to the caster swivel circle, skirt, four disc motors, discs from `razor-disc.dxf`, pivoting blades, rollers, hangers |
| `parts/roof.py` | Solar roof: posts, rails, panels, MPPT, GNSS antenna stub and e-stop on the rear rail |
| `parts/payload.py` | Battery with handle and connector on a lipped tray with strap, IP65 box with lid, glands and mounting feet, GNSS mast with ground plane and antenna, e-stop, 2" hitch receiver with pin, sprung bumper with guide blocks, trip collars and roller microswitches |
| `build.py` | Exports everything to `exports/` and runs clearance checks |
| `strength.py` | Hand-calculation strength check → `exports/strength-report.md` |
| `drive_energy.py` | Hub-motor operating points, heating, and the daily energy budget → `exports/drive-energy-report.md` |
| `exports/platform-v1-{single,twin}.step` | Full assembly. Open in Onshape (*Import*), FreeCAD, Fusion, or any STEP viewer. |
| `exports/*-{iso,top,side,front}.png` | Quick-look renders |
| `exports/platform-v1-detail-*.png` | Close-ups: drive module, front corner (caster + bumper), Ryobi deck hangers, rear, razor deck from below, solar roof |
| `exports/*.dxf` | Flat patterns: drive-fork side plate (6 mm steel ×4), torque arm (5 mm steel ×4), frame gusset (×8), caster plate (×2), razor disc (3 mm aluminium ×4) |
| `exports/strength-report.md` | Load cases, stresses and safety factors for forks, joints, and frame members |
| `exports/cut-list.md` | Extrusion lengths to cut |
| `exports/report.md` | Envelope, mass, CG, axle loads, tongue-weight limit, clearance checks |

## Configurations

- **razor** (v1 baseline, D27/D28): four Ø280 mm razor-blade discs on a 3 mm plate with an HDPE skirt, 1.06 m symmetric cut, plus the solar roof (posts, 30x30 roof frame, two panels, MPPT) carrying the GNSS antenna and e-stop.
- **single**: one Ryobi deck in the twin layout's **rear-right** slot (weekly-capable cutting, needs the dock), no roof.
- **twin**: v1.5, two decks **staggered** (rear-right, front-left) so their cuts overlap by 50 mm. Two decks side by side would leave an uncut strip, because the deck housing is wider than the blade. The frame is the same for both.

## Regenerate

```bash
cd hardware/cad
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python build.py
.venv/bin/python strength.py
.venv/bin/python drive_energy.py
```

`build.py --details` regenerates only the close-up renders (fast) while adjusting views. A full build takes about a minute, most of it in clearance checks and renders.

Commit the regenerated `exports/` together with the parameter change, so the repo stays readable without Python.

## What this model is (and isn't)

- **Detailed layout model (v1).** Every structural part is modelled the way it would be built: real T-slot sections, bolted joints with brackets and gussets, plates from the same outlines as the DXFs, fasteners at every joint. Purchased parts (hub motors, casters, the Ryobi deck, battery, enclosure) are modelled from typical catalog dimensions and will be replaced by measured ones (below). The STEP has ~350 solids and opens in Onshape or FreeCAD.
- **Clearance checks** run on the full model: decks (shell, blade, motor, rollers) against the frame, brackets, forks, wheels and casters; caster swivel sweep against the decks and bumper parts; hangers against everything they shouldn't touch; payload against the deck motors; bumper travel against the caster sweep. The detailed model caught one clash the block model missed: the right hub motor's cable exit ran into deck 1's skirt, which is only ~18 mm from the axle end. The cable now turns up at the axle.
- **Strength:** `strength.py` hand-checks the forks, joints, and members ([report](exports/strength-report.md)). It led to the torque arms, saddle-mounted forks, gussets, and the 30x60 member at x = 215. It's not FEA; the frame is simple enough that beam and plate checks catch the real risks.
- **Not modelled yet:** wiring beyond the motor cables, the belly pan, the VESCs inside the enclosure, the deck's blade-brake and switch wiring, and the charging-dock contacts (phase 2).

## Measure when parts arrive, then update `params.py`

1. Hub motor: tire OD and width, **dropout spacing** (shoulder to shoulder), **axle flats width**, axle length past each shoulder
2. Caster: wheel OD and width, trail, overall height from ground to the mounting plate
3. Ryobi deck (handle and wheels removed): housing outline, motor housing diameter and height, cutting height range, mass
4. Battery and enclosure dimensions

Licensed under [CERN-OHL-W-2.0](../../LICENSES/CERN-OHL-W-2.0.txt); the code in this folder is also available under [Apache-2.0](../../LICENSES/Apache-2.0.txt).

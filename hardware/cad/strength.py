"""Hand-calculation strength check for the platform v1 frame and drive forks.

Usage (from hardware/cad/):
    .venv/bin/python strength.py      -> exports/strength-report.md

These are classical beam/plate/bolt checks with explicit load cases and
assumptions, intended to catch under-sized parts before metal is cut. They are
not a finite-element analysis. Section properties of the aluminium extrusion
are typical catalog values for 30-series slot-8 profiles; check them against the
supplier's datasheet when the extrusion is chosen.
"""

from math import pi
from pathlib import Path

import numpy as np

from model import assembly, caster_plate_extent
from params import Params

OUT = Path(__file__).parent / "exports"
G = 9.81

# ----------------------------------------------------------- assumptions --
# Materials (MPa)
AL_YIELD = 145.0  # 6063-T5 extrusion (conservative; T6 is ~215)
AL_FATIGUE = 50.0  # guideline for >1e8 vibration cycles on bolted extrusion frames
STEEL_YIELD = 235.0  # mild steel plate (A36 / S235)
BOLT_M8_PROOF_N = 22_000  # class 8.8 M8 proof load
BOLT_M6_SHEAR_N = 20.1 * 0.6 * 640  # class 8.8 M6, shear through the shank area
TNUT_PULLOUT_N = 2_500  # conservative allowable per T-nut in a 30-series slot; verify

# Sections (mm^4, mm^3)
SEC = {
    "30x30": {"I": 2.6e4, "Z": 1.7e3},
    "30x60 strong": {"I": 1.5e5, "Z": 5.0e3},  # 60 mm side vertical
    "30x60 weak": {"I": 4.8e4, "Z": 3.2e3},
}
E_AL = 69_000.0

# Load cases
BUMP = 2.5  # vertical dynamic factor: driving over ruts/roots at ~1.5 m/s
LAT_MU = 0.7  # peak grass friction for a sideways skid
LAT_DYN = 1.5  # vertical factor acting with the skid
MOTOR_TORQUE_NM = 40.0  # peak hub-motor torque; set the VESC motor-current limit to keep below this
AXLE_D = 12.0  # mm, hub-motor axle (ESTIMATE)
AXLE_FLAT_FACE = 6.6  # mm, face width of each flat on a 12 mm axle with 10 mm flats
TONGUE_KG = 20.0  # cart tongue weight (below the tip-up limit in report.md)
DRAWBAR_N = 160.0  # pull for 100 kg in a cart on grass (design doc §5)
HITCH_DYN = 2.0


def sf(capacity, demand):
    return capacity / demand if demand > 0 else float("inf")


def verdict(s, limit=2.0):
    return "✅" if s >= limit else ("⚠️" if s >= 1.0 else "❌")


def static_loads(p: Params, config: str):
    parts = assembly(p, config)
    total = sum(r.mass for r in parts)
    cg = sum(np.array(tuple(r.shape.center())) * r.mass for r in parts) / total
    caster_x = p.caster_pivot_x - p.caster_trail
    r_caster = total * cg[0] / caster_x
    return parts, total, (total - r_caster) / 2 * G, r_caster / 2 * G  # N per drive wheel, per caster


def nearest_members(p: Params, x):
    xs = sorted(p.cross_member_x)
    behind = max((m for m in xs if m <= x), default=xs[0])
    ahead = min((m for m in xs if m > x), default=xs[-1])
    return behind, ahead


def member_loads(p: Params, parts, factor):
    """Distribute part weights (N) onto cross members as (member_x, y, load)."""
    loads = []
    for r in parts:
        if r.group in ("frame", "drive", "fork", "caster"):
            continue
        c = r.shape.center()
        w = r.mass * G * factor
        if r.group == "deck":
            x, y = r.meta["center"]
            a, b = nearest_members(p, x)
            fa = (b - x) / (b - a)
            for hy in (y - p.deck_hanger_spread, y + p.deck_hanger_spread):  # 4 hangers per deck
                loads += [(a, hy, w * fa / 2), (b, hy, w * (1 - fa) / 2)]
        elif r.name == "battery":
            continue  # sits directly over the drive fork on the side rail
        else:
            a, b = nearest_members(p, c.X)
            if c.X <= min(p.cross_member_x):
                loads.append((a, c.Y, w))
            else:
                fa = (b - c.X) / (b - a) if b != a else 1.0
                loads += [(a, c.Y, w * fa), (b, c.Y, w * (1 - fa))]
    return loads


def cross_member_check(p: Params, loads):
    """Worst cross member as a simply supported beam (corner brackets ~ pinned)."""
    span = p.frame_width - 2 * p.side_rail[0]
    worst = None
    for mx in p.cross_member_x:
        pts = [(span / 2 + y, w) for (x, y, w) in loads if x == mx]
        if not pts:
            continue
        xs = np.linspace(0, span, 400)
        rb = sum(a * w for a, w in pts) / span
        ra = sum(w for _, w in pts) - rb
        m = np.array([ra * xx - sum(w * (xx - a) for a, w in pts if xx > a) for xx in xs])
        mmax = abs(m).max()
        prof = p.cross_profile(mx)[2]
        stress = mmax / SEC["30x60 strong" if prof == "30x60" else "30x30"]["Z"]
        if worst is None or stress > worst[3]:
            worst = (mx, mmax, pts, stress)
    return worst, span


def side_rail_check(p: Params, loads):
    """Side rail: supported at the drive fork (x=0) and front cross member; rear overhang."""
    span = p.frame_width - 2 * p.side_rail[0]
    support_front = max(p.cross_member_x)
    worst = 0.0
    for sgn in (1, -1):
        pts = []
        for x, y, w in loads:
            if x == support_front:
                continue  # front member load goes straight into the caster below it
            share = (span / 2 + sgn * y) / span  # lever rule across the member
            pts.append((x, w * share))
        # Reactions at x=0 and x=support_front.
        r_front = sum(w * x for x, w in pts) / support_front
        r0 = sum(w for _, w in pts) - r_front
        for xx in np.linspace(p.frame_rear_x, support_front, 600):
            m = sum(-w * (xx - x) for x, w in pts if x < xx)
            if xx > 0:
                m += r0 * xx
            worst = max(worst, abs(m))
    return worst


BRAKE_DECEL = 3.0  # m/s^2: VESC timeout brake, traction-limited on grass (verify by test)
STOP_LATENCY = 0.12  # s: switch + relay (~20 ms) + VESC signal timeout (100 ms)
FOAM_USABLE = 0.7  # fraction of foam thickness that crushes usefully


def bumper_section(p: Params, total_kg: float) -> list[str]:
    avail = (p.bumper_travel + FOAM_USABLE * p.bumper_foam) / 1000
    t, a = STOP_LATENCY, BRAKE_DECEL
    v_max = a * (-t + (t * t + 2 * avail / a) ** 0.5)
    lines = [
        "",
        "## Bumper stopping distance",
        "",
        "When the bumper trips, the robot keeps moving through the e-stop latency, then brakes. "
        "The bumper's travel plus foam must absorb that distance, or the robot pushes the obstacle "
        "with its full weight.",
        "",
        f"- Available: {p.bumper_travel:.0f} mm travel + {FOAM_USABLE:.0%} of {p.bumper_foam:.0f} mm foam = **{avail * 1000:.0f} mm**",
        f"- Latency {STOP_LATENCY * 1000:.0f} ms (switch + relay + VESC 100 ms signal timeout); "
        f"braking {BRAKE_DECEL} m/s² (VESC timeout brake, limited by grass traction: verify by test)",
        "",
        "| Speed | Stopping distance | Fits in bumper? | Energy at contact |",
        "|---|---|---|---|",
    ]
    for v in (0.4, 0.5, 0.6, 0.8, 1.0, 1.5):
        d = v * t + v * v / (2 * a)
        lines.append(f"| {v} m/s | {d * 1000:.0f} mm | {'✅' if d <= avail else '❌'} | "
                     f"{0.5 * total_kg * v * v:.0f} J |")
    lines += [
        "",
        f"**Maximum speed the bumper can protect: {v_max:.2f} m/s.** v1 mows at **0.6 m/s** (ArduPilot "
        "`CRUISE_SPEED`, and `WP_SPEED` for missions). Faster transit needs phase-2 obstacle sensing that "
        "slows the robot before contact. The bumper is a last resort for objects, not a people-safety "
        "system: v1 runs **supervised only**.",
        "",
        "Shorter latency helps most: dropping the VESC timeout from 100 ms to 50 ms raises the protected "
        "speed by about 0.1 m/s. Test it on the bench (electrical README §8, step 7).",
    ]
    return lines


def main():
    p = Params()
    rows = []
    notes = []

    parts, total, wheel_n, caster_n = static_loads(p, "twin")  # heaviest configuration
    w_bump = BUMP * wheel_n
    f_lat = LAT_MU * LAT_DYN * wheel_n
    rail_w = p.side_rail[0]
    lever_ground_to_rail = p.frame_bottom_z

    # 1. Fork side plates, out-of-plane bending from a sideways skid.
    z_bot = p.wheel_diameter / 2 - 35
    plate_h = p.frame_bottom_z - p.fork_top_t - z_bot
    zs = p.fork_length_x * p.fork_plate_t**2 / 6
    sig = (f_lat / 2) * lever_ground_to_rail / zs
    s = sf(STEEL_YIELD, sig)
    rows.append(("Fork side plates (6 mm steel)", "Sideways skid",
                 f"{sig:.0f} MPa bending", f"{STEEL_YIELD:.0f} MPa yield", s, verdict(s), ""))

    # 2. Fork top plate, cantilever from the rail edge to the side plates (bump).
    arm = p.dropout_spacing / 2 + p.fork_plate_t / 2 - rail_w / 2
    zt = p.fork_length_x * p.fork_top_t**2 / 6
    sig = (w_bump / 2) * arm / zt
    s = sf(STEEL_YIELD, sig)
    rows.append(("Fork top plate (8 mm steel)", "Bump 2.5 g", f"{sig:.0f} MPa", f"{STEEL_YIELD:.0f} MPa", s,
                 verdict(s), ""))

    # 3. Dropout bearing on the axle (bump).
    sig = (w_bump / 2) / (AXLE_D * p.fork_plate_t)
    s = sf(STEEL_YIELD, sig)
    rows.append(("Dropout slot bearing", "Bump 2.5 g", f"{sig:.0f} MPa", f"{STEEL_YIELD:.0f} MPa", s, verdict(s), ""))

    # 4. Motor torque reaction through the axle flats.
    t_plate = MOTOR_TORQUE_NM * 1000 / 2
    f_flat = t_plate / AXLE_FLAT_FACE
    sig = f_flat / (p.fork_plate_t * 2.0)  # line contact ~2 mm wide along the plate thickness
    s = sf(STEEL_YIELD, sig)
    rows.append(("Axle flats in slot, **no torque arm**", f"{MOTOR_TORQUE_NM:.0f} N·m peak torque",
                 f"{sig:.0f} MPa contact", f"{STEEL_YIELD:.0f} MPa", s, verdict(s),
                 "Slot wallows out and the axle spins: the classic e-bike failure"))
    f_bolt = t_plate / 50.0
    s = sf(BOLT_M6_SHEAR_N, f_bolt)
    rows.append(("Torque arm (keyed plate + M6 at 50 mm)", f"{MOTOR_TORQUE_NM:.0f} N·m peak torque",
                 f"{f_bolt:.0f} N shear", f"{BOLT_M6_SHEAR_N:.0f} N", s, verdict(s), "Fix for the row above"))

    # 5. Fork-to-rail joint: bolts in the single bottom slot pry about the rail edge.
    m_joint = f_lat * lever_ground_to_rail
    n_nuts = 4
    t_per = m_joint / (rail_w / 2) / n_nuts
    s = sf(TNUT_PULLOUT_N, t_per)
    rows.append(("Fork → rail joint, **bottom slot only**", "Sideways skid",
                 f"{t_per:.0f} N per T-nut", f"{TNUT_PULLOUT_N} N pull-out", s, verdict(s),
                 f"{m_joint / 1000:.0f} N·m reacted over a {rail_w / 2:.0f} mm lever"))
    saddle_lever = p.side_rail[1] - 15  # upper side-slot centreline above the rail bottom
    t_per = m_joint / saddle_lever / 2
    s = sf(TNUT_PULLOUT_N, t_per)
    rows.append(("Fork → rail joint, **saddle tabs** into side slots", "Sideways skid",
                 f"{t_per:.0f} N per T-nut", f"{TNUT_PULLOUT_N} N pull-out", s, verdict(s), "Fix for the row above"))

    # 6. Cross members (decks hang from them), both configurations.
    for config in ("single", "twin"):
        parts_c, _, _, _ = static_loads(p, config)
        loads = member_loads(p, parts_c, BUMP)
        (mx, mmax, pts, _), span = cross_member_check(p, loads)
        prof = p.cross_profile(mx)[2]
        sec = SEC["30x60 strong" if prof == "30x60" else "30x30"]
        sig = mmax / sec["Z"]
        static_pts = [(a, w / BUMP) for a, w in pts]
        # Midspan deflection, superposition of point loads (simply supported).
        d = 0.0
        for a, w in static_pts:
            b = span - a
            xm = span / 2
            if xm >= a:
                a, b = b, a
            d += w * b * xm * (span**2 - b**2 - xm**2) / (6 * E_AL * sec["I"] * span)
        s = sf(AL_YIELD, sig)
        rows.append((f"Cross member at x={mx:.0f} ({prof}), {config} deck", "Bump 2.5 g",
                     f"{sig:.0f} MPa", f"{AL_YIELD:.0f} MPa yield / {AL_FATIGUE:.0f} fatigue", s,
                     verdict(s) if sig <= AL_FATIGUE else "⚠️",
                     f"static sag {d:.1f} mm over {span:.0f} mm"))

    # 7. Side rails.
    loads = member_loads(p, parts, BUMP)
    m_rail = side_rail_check(p, loads)
    sig = m_rail / SEC["30x60 strong"]["Z"]
    s = sf(AL_YIELD, sig)
    rows.append(("Side rails (30x60)", "Bump 2.5 g, twin deck", f"{sig:.0f} MPa", f"{AL_YIELD:.0f} MPa", s,
                 verdict(s) if sig <= AL_FATIGUE else "⚠️", ""))

    # 8. Rear cross member carrying the hitch at mid-span (towing case).
    span = p.frame_width - 2 * rail_w
    mv = TONGUE_KG * G * HITCH_DYN * span / 4
    mh = DRAWBAR_N * HITCH_DYN * span / 4
    sig = (mv + mh) / SEC["30x30"]["Z"]
    s = sf(AL_YIELD, sig)
    rows.append(("Rear cross member with hitch at mid-span (30x30)",
                 f"Towing: {TONGUE_KG:.0f} kg tongue + {DRAWBAR_N:.0f} N pull, ×{HITCH_DYN:.0f}",
                 f"{sig:.0f} MPa", f"{AL_YIELD:.0f} MPa", s, verdict(s),
                 "Fix: A-frame drawbar to both side rails (phase 3)"))

    # 9. Caster corner plate: bump load at the caster, reacted by the rail and front-member bolts.
    x0, x1, y_in, y_out = caster_plate_extent(p)
    f_c = BUMP * caster_n
    arm_c = min(p.side_rail_y - p.caster_pivot_y, max(p.cross_member_x) - p.caster_pivot_x)
    zp = (x1 - x0) * p.caster_mount_t**2 / 6
    sig = f_c * arm_c / zp
    s = sf(STEEL_YIELD, sig)
    rows.append(("Caster corner plate (8 mm steel)", "Bump 2.5 g", f"{sig:.0f} MPa", f"{STEEL_YIELD:.0f} MPa", s,
                 verdict(s), ""))
    m_c = 0.5 * f_c * p.caster_height  # rearward bump force at the tire
    lever = max(p.cross_member_x) - (x0 + 15)  # member bolts to rearmost rail bolt
    t_per = m_c / lever / 2
    s = sf(TNUT_PULLOUT_N, t_per)
    rows.append(("Caster plate bolts", "Bump: rearward force 0.5 × vertical at the tire",
                 f"{t_per:.0f} N per T-nut", f"{TNUT_PULLOUT_N} N pull-out", s, verdict(s), ""))

    # ---------------------------------------------------------- report --
    lines = [
        "# Strength check: platform v1 frame and drive forks",
        "",
        "*Generated by `strength.py`; do not edit by hand. Hand calculations, not FEA. "
        "All inputs are listed below and in `params.py`.*",
        "",
        "## Load cases and assumptions",
        "",
        f"- Heaviest configuration (twin deck): **{total:.1f} kg**, giving **{wheel_n / G:.1f} kg per drive wheel** and "
        f"{caster_n / G:.1f} kg per caster (static).",
        f"- **Bump:** {BUMP} × static, vertical (ruts and roots at ~1.5 m/s).",
        f"- **Sideways skid:** {LAT_MU} × {LAT_DYN} × static wheel load = **{f_lat:.0f} N** applied at the tire "
        "contact patch. Pure pivot turns don't skid the drive wheels sideways, so this covers sliding into "
        "a rut or bumping something side-on.",
        f"- **Motor torque:** {MOTOR_TORQUE_NM:.0f} N·m peak per wheel. Set the VESC motor-current limit so this "
        "isn't exceeded.",
        f"- **Towing (phase 3):** {TONGUE_KG:.0f} kg tongue weight and {DRAWBAR_N:.0f} N drawbar pull, × {HITCH_DYN:.0f} dynamic.",
        f"- **Materials:** 6063-T5 aluminium extrusion, yield {AL_YIELD:.0f} MPa, with a **fatigue guideline of "
        f"{AL_FATIGUE:.0f} MPa** for the bump case (aluminium has no endurance limit and the frame vibrates "
        f"for hours). Mild-steel plate, yield {STEEL_YIELD:.0f} MPa. T-nut pull-out allowable {TNUT_PULLOUT_N} N "
        "(conservative; check the supplier's figure).",
        "- **Extrusion sections** (typical 30-series catalog values): "
        + "; ".join(f"{k}: I = {v['I']:.1e} mm⁴, Z = {v['Z']:.1e} mm³" for k, v in SEC.items()) + ".",
        "- Corner-bracket joints are treated as **pinned** (conservative for member bending).",
        "",
        "## Results",
        "",
        "Target: safety factor ≥ 2 on yield in the worst case, and bump-case stress in aluminium below the "
        "fatigue guideline.",
        "",
        "| Part | Load case | Demand | Capacity | SF | | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    for part, case, demand, cap, s, v, note in rows:
        lines.append(f"| {part} | {case} | {demand} | {cap} | {s:.1f} | {v} | {note} |")
    lines += bumper_section(p, total)
    lines += [
        "",
        "## What has to change before cutting metal",
        "",
        "1. **Torque arms on both hub motors (required).** Without them, peak motor torque crushes the slot edges "
        "and the axle spins in the dropouts, tearing the motor wires. Use a steel plate keyed to the axle flats and "
        "bolted to the fork side plate at the two M6 holes already in the DXF (`torque-arm.dxf`). Also set the "
        f"VESC motor-current limit so peak torque stays under {MOTOR_TORQUE_NM:.0f} N·m.",
        "2. **Saddle-mount the drive forks.** Bolting the fork top plate only into the rail's bottom slot leaves a "
        "15 mm lever against sideways loads. Add two tabs that rise up both 60 mm faces of the side rail and bolt "
        "into the side slots. The model now includes them.",
        "3. **Gusset the four rail-to-cross-member joints next to the drive axle** (members at x = −120 and x = 215). "
        f"They carry the sideways-skid moment from the forks (~{m_joint / 2000:.0f} N·m each) as well as the deck "
        "loads. Plain cast corner brackets are the weakest, least stiff part of an extrusion frame. Use 5 mm "
        "aluminium or 3 mm steel gusset plates on the top face (`frame-gusset.dxf`), 3 M6 bolts per leg.",
        "4. **The cross member at x = 215 is 30x60** (was 30x30). It carries both decks in the twin layout, "
        "and as 30x30 it sat right at the aluminium fatigue guideline (~49 MPa). Hang the decks as close to the "
        "side rails as the deck allows, and re-run once the real hanger points are known.",
        "5. **Casters on 8 mm steel corner plates** that bolt to both the side rail and the (now 30x60) front "
        "cross member (`caster-plate.dxf`). The plate spreads the caster's bump loads into two members.",
        "6. **Towing (phase 3): A-frame drawbar.** A hitch at the middle of the rear 30x30 member is at "
        "SF ≈ 1 for a modest cart. Use a triangulated drawbar from the hitch pin to both side rails so the "
        "rails (SF > 20) carry the load. Until then, **don't tow from the current hitch.**",
        "",
        "## Not covered here",
        "",
        "- **Bumper arms and guides** under a full-speed impact after the travel is used up (they should "
        "yield before the frame does). Size them once the spring and switch hardware is chosen.",
        "- **Frame twist** when one wheel drops into a hole is accommodated by frame flexibility, and helps keep "
        "all four wheels on the ground. Check bolt preload after the first hours of running (use thread-locker "
        "or nyloc nuts and torque-stripe paint).",
    ]
    (OUT / "strength-report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

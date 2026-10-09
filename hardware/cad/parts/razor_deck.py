"""Razor-disc mower deck: four small brushless discs with pivoting razor blades on a 3 mm
aluminium plate with an HDPE skirt, hung from the cross members. Light-and-often cutting:
see docs/design/form-factor-exploration.md §2 and §6."""

import math

from build123d import Axis, Circle, Compound, Plane, Pos, Rectangle, Rot, extrude

from params import Params
from parts.common import PartRecord, box, hex_bolt, hex_nut, rod, y_cylinder, z_cylinder
from parts.frame import member_span
from parts.plates import razor_disc


def razor_deck(p: Params) -> list[PartRecord]:
    parts = []
    x0, x1, hw = p.razor_plate_extent()
    zp = p.razor_plate_z
    t = p.razor_plate_t
    # Deck plate: a rectangle with the front outer corners cut back to the caster swivel
    # circle (+5 mm), so the casters can spin through 360° without touching the deck.
    sweep_r = p.caster_trail + p.caster_wheel_diameter / 2 + 5
    def outline_at(z, inset=0.0):
        sk = Pos((x0 + x1) / 2, 0) * Rectangle(x1 - x0 - 2 * inset, 2 * hw - 2 * inset)
        for sy in (-1, 1):
            sk = sk - Pos(p.caster_pivot_x, sy * p.caster_pivot_y) * Circle(sweep_r + inset)
        return Plane(origin=(0, 0, z)) * sk
    plate = extrude(outline_at(zp), t)
    for x, y in p.razor_discs():
        plate = plate - z_cylinder(x, y, zp - 1, 12, t + 2)  # motor shaft hole
    # Skirt: HDPE strip around the plate edge, below it.
    skirt_t = 6.0
    skirt = extrude(outline_at(zp - p.razor_skirt_h), p.razor_skirt_h) - extrude(
        outline_at(zp - p.razor_skirt_h - 1, skirt_t), p.razor_skirt_h + 2)
    parts.append(PartRecord("razor_deck_plate", "deck", plate, 5.0, material="aluminium",
                            meta={"center": ((x0 + x1) / 2, 0.0), "motor_top_z": zp + t + p.razor_motor_h + 10}))
    parts.append(PartRecord("razor_deck_skirt", "deck", skirt, 1.5, material="black_plastic"))

    disc_sk, r_pivot = razor_disc(p)
    motors, discs, blades = [], [], []
    for i, (x, y) in enumerate(p.razor_discs()):
        motors.append(z_cylinder(x, y, zp + t, p.razor_motor_d / 2, p.razor_motor_h))
        motors.append(z_cylinder(x, y, zp + t + p.razor_motor_h, 10, 10))  # cable boss
        motors.append(z_cylinder(x, y, p.razor_cut_z + 4, 6, zp - p.razor_cut_z - 4))  # shaft
        disc = extrude(Plane(origin=(x, y, p.razor_cut_z + 4)) * disc_sk, 3)
        discs.append(disc)
        for k in range(3):  # blades swung out at a working angle
            a = math.radians(k * 120 + 15 * (i % 2))
            px, py = x + r_pivot * math.cos(a), y + r_pivot * math.sin(a)
            blade = Pos(px, py, p.razor_cut_z) * Rot(0, 0, math.degrees(a)) * box(-4, 30, -9, 9, 0, 1.2)
            blades.append(blade)
            blades.append(z_cylinder(px, py, p.razor_cut_z - 2, 3, 10))  # shoulder screw
    parts.append(PartRecord("razor_motors", "deck", Compound(children=motors), 2.0, material="black_plastic"))
    parts.append(PartRecord("razor_discs", "deck", Compound(children=discs), 1.0, material="aluminium"))
    parts.append(PartRecord("razor_blades", "deck", Compound(children=blades), 0.3, material="steel"))

    # Anti-scalp rollers at the front and rear centre line.
    rollers = []
    for rx in (x0 + 25, x1 - 25):
        rollers.append(y_cylinder(rx, 0, 36, 30, 60))
        rollers.append(box(rx - 8, rx + 8, -38, 38, 36, zp))
    parts.append(PartRecord("razor_rollers", "deck", Compound(children=rollers), 0.4, material="black_plastic"))

    # Four M8 threaded-rod hangers up to the cross members on either side of the deck.
    hangers = []
    xs = sorted(p.cross_member_x)
    behind = max(m for m in xs if m <= x0 + 60)
    ahead = min(m for m in xs if m >= x1 - 60)
    for mx in (behind, ahead):
        m0, m1, chh = member_span(p, mx)
        zb = p.frame_top_z - chh
        for sy in (-1, 1):
            hx, hy = (m0 + m1) / 2, sy * p.razor_hanger_y
            hangers.append(rod((hx, hy, zp - 6), (hx, hy, zb + 12), 4))
            hangers.append(box(hx - 12, hx + 12, hy - 10, hy + 10, zb - 10, zb))  # drop-in T block
            hangers.append(hex_nut((hx, hy, zp + t), (0, 0, 1), af=13, height=6.5, bore=4))
            hangers.append(hex_nut((hx, hy, zp), (0, 0, -1), af=13, height=6.5, bore=4))
    parts.append(PartRecord("razor_hangers", "hanger", Compound(children=hangers), 4 * p.masses["hanger"]))
    return parts
